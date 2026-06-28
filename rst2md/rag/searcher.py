import re
import sqlite3
from pathlib import Path
from typing import List, Optional

from rag.db import clean_chunk_text, get_connection
from rag.models import SearchMetadata, SearchResponse, SearchResult
from rag.symbols import normalize_symbol


_FTS5_SPECIAL = set('"*+-:()^')

def _smart_tokenize(query: str) -> str:
    """Split dotted/snake_case symbols into separate tokens for FTS5.

    "Node.add_child" → '"Node" AND "add" AND "child"'
    Plain queries pass through unchanged.
    """
    # Only split if query contains . or _ (likely a symbol)
    if '.' not in query and '_' not in query:
        return _escape_fts5(query)

    tokens = re.split(r'[._]', query)
    fts_tokens = []
    for t in tokens:
        if not t:
            continue
        if any(c in _FTS5_SPECIAL for c in t):
            escaped = t.replace('"', '""')
            fts_tokens.append(f'"{escaped}"')
        else:
            fts_tokens.append(t)
    return " AND ".join(fts_tokens) if fts_tokens else _escape_fts5(query)


def _escape_fts5(query: str) -> str:
    """Escape FTS5 special characters so the query is treated as literal text.

    FTS5 does not support backslash escaping. Tokens containing special
    characters are wrapped in double quotes (phrase matching). Plain tokens
    are left as-is so multi-word queries retain implicit AND semantics.
    """
    tokens = []
    for token in query.split():
        if any(c in _FTS5_SPECIAL for c in token):
            escaped = token.replace('"', '""')
            tokens.append(f'"{escaped}"')
        else:
            tokens.append(token)
    return ' '.join(tokens)


def vector_search(conn, query_embedding: List[float], limit: int = 10) -> List[dict]:
    """Search for similar chunks using vector embeddings.

    Args:
        conn: SQLite connection.
        query_embedding: Query vector (256 dimensions).
        limit: Maximum number of results.

    Returns:
        List of dicts with 'id' and 'distance' keys.
    """
    results = conn.execute(
        "SELECT chunk_id, distance FROM vec_chunks WHERE embedding MATCH ? AND k = ?",
        (str(query_embedding), limit)
    ).fetchall()

    return [{'id': row[0], 'distance': row[1]} for row in results]


def rrf_fusion(fts_results: List[dict], vec_results: List[dict], k: int = 60) -> List[dict]:
    """Fuse FTS5 and vector search results using Reciprocal Rank Fusion.

    Args:
        fts_results: FTS5 results with 'id' key.
        vec_results: Vector results with 'id' and 'distance' keys.
        k: RRF parameter (default 60).

    Returns:
        Fused results sorted by RRF score, with 'rrf_score' key added.
    """
    scores = {}

    for rank, result in enumerate(fts_results):
        chunk_id = result['id']
        scores[chunk_id] = scores.get(chunk_id, 0) + 1.0 / (k + rank)

    for rank, result in enumerate(vec_results):
        chunk_id = result['id']
        scores[chunk_id] = scores.get(chunk_id, 0) + 1.0 / (k + rank)

    sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

    results = []
    for chunk_id in sorted_ids:
        result = next((r for r in fts_results if r['id'] == chunk_id), None)
        if result is None:
            result = next((r for r in vec_results if r['id'] == chunk_id), None)
        if result:
            result = dict(result)
            result['rrf_score'] = scores[chunk_id]
            results.append(result)

    return results


def _extract_snippet(text: str, query: str, context_lines: int = 3) -> str:
    """Extract a snippet from text around the first line containing query keywords."""
    lines = text.split('\n')
    query_lower = query.lower()
    keywords = query_lower.split()

    # Find first line containing any keyword
    match_idx = None
    for i, line in enumerate(lines):
        line_lower = line.lower()
        if any(kw in line_lower for kw in keywords):
            match_idx = i
            break

    if match_idx is None:
        # No match found, return first few lines
        return '\n'.join(lines[:context_lines * 2 + 1])

    # Extract context around match
    start = max(0, match_idx - context_lines)
    end = min(len(lines), match_idx + context_lines + 1)

    snippet_lines = []
    if start > 0:
        snippet_lines.append('...')
    snippet_lines.extend(lines[start:end])
    if end < len(lines):
        snippet_lines.append('...')

    return '\n'.join(snippet_lines)


def _vector_availability(conn) -> tuple[bool, str]:
    try:
        # Check if vec_chunks table exists and is queryable
        vec_count = conn.execute("SELECT COUNT(*) FROM vec_chunks").fetchone()[0]
    except sqlite3.OperationalError as exc:
        message = str(exc).lower()
        if "no such table" in message or "no such module" in message:
            return False, "missing_vec_chunks"
        return False, "vector_query_failed"

    # Check if vec_chunks is empty
    if vec_count == 0:
        return False, "empty_vec_chunks"

    # Check row count parity with chunks table
    try:
        chunks_count = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        if vec_count != chunks_count:
            return False, "vector_row_count_mismatch"
    except sqlite3.OperationalError:
        return False, "vector_query_failed"

    return True, ""


def _run_vector_query(conn, query_embedding, limit, type_filter, type_params, addon_filter, addon_params):
    vec_query = (
        "SELECT vc.chunk_id, vc.distance FROM vec_chunks vc "
        "JOIN chunks c ON vc.chunk_id = c.id "
        "WHERE vc.embedding MATCH ? AND k = ?"
        + type_filter + addon_filter
    )
    vec_rows = conn.execute(
        vec_query,
        [str(query_embedding), limit * 3] + type_params + addon_params,
    ).fetchall()
    return [{'id': row[0], 'distance': row[1]} for row in vec_rows]


def search_database_with_metadata(
    db_path: Path, query: str, limit: int = 8,
    doc_types: Optional[List[str]] = None, addon: Optional[str] = None,
    expand_graph: bool = True,
) -> SearchResponse:
    results, metadata = _search_database_impl(
        db_path=db_path,
        query=query,
        limit=limit,
        doc_types=doc_types,
        addon=addon,
        expand_graph=expand_graph,
    )
    return SearchResponse(results=results, metadata=metadata)


def search_database(
    db_path: Path, query: str, limit: int = 8,
    doc_types: Optional[List[str]] = None, addon: Optional[str] = None,
    expand_graph: bool = True,
) -> List[SearchResult]:
    return search_database_with_metadata(
        db_path,
        query,
        limit=limit,
        doc_types=doc_types,
        addon=addon,
        expand_graph=expand_graph,
    ).results


def _search_database_impl(
    db_path: Path, query: str, limit: int = 8,
    doc_types: Optional[List[str]] = None, addon: Optional[str] = None,
    expand_graph: bool = True,
) -> tuple[List[SearchResult], SearchMetadata]:
    """Search the RAG database.

    Args:
        db_path: Path to the SQLite database.
        query: Search query string.
        limit: Maximum number of results to return.
        doc_types: If provided, only search chunks whose doc_type is in this list.
        addon: If provided, only search chunks belonging to this addon.
        expand_graph: If True, expand top results via chunk_relations graph.
        doc_types: If provided, only search chunks whose doc_type is in this list.
                   Common values: "class", "tutorial", "getting_started", "engine_detail", "addon".
        addon: If provided, only search chunks belonging to this addon (e.g. "statecharts").
    """
    with get_connection(db_path) as conn:
        normalized = normalize_symbol(query)
        results = {}
        vector_available, fallback_reason = _vector_availability(conn)
        metadata = SearchMetadata(
            mode="fts_only",
            vector_available=False,
            fallback_reason=fallback_reason,
        )

        # Build optional doc_type filter
        type_filter = ""
        type_params: list = []
        if doc_types:
            placeholders = ",".join("?" for _ in doc_types)
            type_filter = f" AND c.doc_type IN ({placeholders})"
            type_params = list(doc_types)

        # Build optional addon filter
        addon_filter = ""
        addon_params: list = []
        if addon:
            addon_filter = " AND c.addon = ?"
            addon_params = [addon]

        def _make_result(row, score):
            return {
                "id": row["id"],
                "score": score,
                "path": row["path"],
                "start_line": row["start_line"],
                "end_line": row["end_line"],
                "doc_type": row["doc_type"],
                "chunk_type": row["chunk_type"],
                "addon": row["addon"],
                "addon_name": row["addon_name"],
                "symbol": row["symbol"],
                "heading": row["heading"],
                "breadcrumb": row["breadcrumb"],
                "text": clean_chunk_text(row["text"]),
                "relation_type": "",
                "distance": 0,
            }

        # 0. Vector search + RRF fusion (respects doc_type and addon filters)
        fused_ids = set()
        if vector_available:
            try:
                from rag.embeddings import generate_embeddings
                query_embedding = generate_embeddings([query])[0]

                vec_results_raw = _run_vector_query(
                    conn, query_embedding, limit,
                    type_filter, type_params, addon_filter, addon_params,
                )

                # FTS5 search for RRF fusion (with doc_type/addon filters)
                fts_results_raw = []
                try:
                    escaped_query = _smart_tokenize(query)
                    fts_rows = conn.execute(
                        "SELECT c.id, bm25(chunks_fts) as rank FROM chunks_fts fts JOIN chunks c ON fts.rowid = c.id WHERE chunks_fts MATCH ?"
                        + type_filter + addon_filter
                        + " ORDER BY rank LIMIT ?",
                        [escaped_query] + type_params + addon_params + [limit * 3]
                    ).fetchall()
                    for row in fts_rows:
                        fts_results_raw.append({'id': row['id'], 'rank': row['rank']})
                except sqlite3.OperationalError:
                    pass

                # RRF fusion
                fused_results = rrf_fusion(fts_results_raw, vec_results_raw)
                fused_ids = {r['id'] for r in fused_results[:limit * 3]}
                metadata = SearchMetadata(mode="hybrid", vector_available=True)

                # Add fused results to results dict with RRF scores
                for rank, fused in enumerate(fused_results[:limit * 3]):
                    cid = fused['id']
                    rrf_score = fused['rrf_score'] * 40.0  # Scale RRF to 0-40 range
                    if cid not in results or results[cid]["score"] < rrf_score:
                        row = conn.execute("SELECT * FROM chunks WHERE id = ?", (cid,)).fetchone()
                        if row:
                            results[cid] = _make_result(row, rrf_score)
            except Exception:
                metadata = SearchMetadata(
                    mode="fts_only",
                    vector_available=False,
                    fallback_reason="vector_query_failed",
                )

        # 1. Exact symbol match (+100)
        rows = conn.execute(
            "SELECT s.name, c.* FROM symbols s JOIN chunks c ON s.chunk_id = c.id WHERE s.normalized_name = ?"
            + type_filter + addon_filter,
            [normalized] + type_params + addon_params,
        ).fetchall()
        for row in rows:
            cid = row["id"]
            if cid not in results or results[cid]["score"] < 100:
                results[cid] = _make_result(row, 100.0)

        # 2. Suffix symbol match (+80)
        rows = conn.execute(
            "SELECT s.name, c.* FROM symbols s JOIN chunks c ON s.chunk_id = c.id WHERE s.normalized_name LIKE ?"
            + type_filter + addon_filter,
            [f"%.{normalized}"] + type_params + addon_params,
        ).fetchall()
        for row in rows:
            cid = row["id"]
            if cid not in results or results[cid]["score"] < 80:
                results[cid] = _make_result(row, 80.0)

        # 3. Prefix symbol match (+40)
        rows = conn.execute(
            "SELECT s.name, c.* FROM symbols s JOIN chunks c ON s.chunk_id = c.id WHERE s.normalized_name LIKE ?"
            + type_filter + addon_filter,
            [f"{normalized}%"] + type_params + addon_params,
        ).fetchall()
        for row in rows:
            cid = row["id"]
            if cid not in results or results[cid]["score"] < 40:
                results[cid] = _make_result(row, 40.0)

        # 4. FTS5 search (bm25 → 0-40 score, skip chunks already in fused results)
        try:
            escaped_query = _smart_tokenize(query)
            fts_type_filter = ""
            fts_type_params: list = []
            if doc_types:
                placeholders = ",".join("?" for _ in doc_types)
                fts_type_filter = f" AND c.doc_type IN ({placeholders})"
                fts_type_params = list(doc_types)

            fts_addon_filter = ""
            fts_addon_params: list = []
            if addon:
                fts_addon_filter = " AND c.addon = ?"
                fts_addon_params = [addon]

            # Exclude chunks already in fused results
            fused_exclude = ""
            fused_exclude_params: list = []
            if fused_ids:
                placeholders = ",".join("?" for _ in fused_ids)
                fused_exclude = f" AND c.id NOT IN ({placeholders})"
                fused_exclude_params = list(fused_ids)

            fts_rows = conn.execute(
                "SELECT c.*, bm25(chunks_fts) as rank FROM chunks_fts fts JOIN chunks c ON fts.rowid = c.id WHERE chunks_fts MATCH ?"
                + fts_type_filter + fts_addon_filter + fused_exclude
                + " ORDER BY rank LIMIT ?",
                [escaped_query] + fts_type_params + fts_addon_params + fused_exclude_params + [limit * 3],
            ).fetchall()
            for row in fts_rows:
                cid = row["id"]
                bm25 = abs(row["rank"])
                fts_score = min(40.0, max(0.0, 40.0 / (1.0 + bm25 * 0.01)))
                if cid not in results or results[cid]["score"] < fts_score:
                    results[cid] = _make_result(row, fts_score)
        except sqlite3.OperationalError:
            # FTS match syntax error, skip
            pass

        # Sort by score descending
        sorted_results = sorted(results.values(), key=lambda r: r["score"], reverse=True)

        # Graph expansion: expand top-K results via chunk_relations
        if expand_graph:
            top_k = min(3, len(sorted_results))
            expanded_ids = {r["id"] for r in sorted_results[:top_k]}

            for result in sorted_results[:top_k]:
                graph_query = (
                    "SELECT c.*, r.relation, r.weight FROM chunk_relations r "
                    "JOIN chunks c ON c.id = r.target_id "
                    "WHERE r.source_id = ?"
                    + type_filter + addon_filter
                    + " ORDER BY r.weight DESC LIMIT 5"
                )
                related_rows = conn.execute(
                    graph_query,
                    [result["id"]] + type_params + addon_params
                ).fetchall()
                for rel_row in related_rows:
                    rel_id = rel_row["id"]
                    if rel_id not in expanded_ids:
                        expanded_ids.add(rel_id)
                        if rel_id in results:
                            # Chunk already found by vector/FTS search, update relation metadata
                            results[rel_id]["relation_type"] = rel_row["relation"]
                            results[rel_id]["distance"] = 1
                        else:
                            # New chunk from graph expansion
                            rel_score = result["score"] * rel_row["weight"] * 0.5
                            results[rel_id] = {
                                "id": rel_id,
                                "score": rel_score,
                                "path": rel_row["path"],
                                "start_line": rel_row["start_line"],
                                "end_line": rel_row["end_line"],
                                "doc_type": rel_row["doc_type"],
                                "chunk_type": rel_row["chunk_type"],
                                "addon": rel_row["addon"],
                                "addon_name": rel_row["addon_name"],
                                "symbol": rel_row["symbol"],
                                "heading": rel_row["heading"],
                                "breadcrumb": rel_row["breadcrumb"],
                                "text": clean_chunk_text(rel_row["text"]),
                                "relation_type": rel_row["relation"],
                                "distance": 1,
                            }

            # Re-sort after expansion
            sorted_results = sorted(results.values(), key=lambda r: r["score"], reverse=True)

        return ([
            SearchResult(
                score=r["score"],
                path=r["path"],
                start_line=r["start_line"],
                end_line=r["end_line"],
                doc_type=r["doc_type"],
                chunk_type=r["chunk_type"],
                addon=r["addon"],
                addon_name=r["addon_name"],
                symbol=r["symbol"],
                heading=r["heading"],
                breadcrumb=r["breadcrumb"],
                text=r["text"],
                relation_type=r.get("relation_type", ""),
                distance=r.get("distance", 0),
                snippet=_extract_snippet(r["text"], query),
            )
            for r in sorted_results[:limit]
        ], metadata)
