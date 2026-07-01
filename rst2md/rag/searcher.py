import sqlite3
from pathlib import Path
from typing import List, Optional

from rag.db import clean_chunk_text, get_connection
from rag.models import RankingSignal, SearchMetadata, SearchResponse, SearchResult
from rag.query_plan import build_query_plan
from rag.symbols import normalize_symbol
from rag.fusion import (  # noqa: F401 — rrf_fusion re-exported for store.py facade; rerank_results used by _search_database_impl
    rerank_results,
    rrf_fusion,
)
from rag.snippet import _extract_snippet  # noqa: F401 — re-export for store.py facade backward compat
# _run_fts_query/_run_vector_query/_smart_tokenize/_vector_availability: used by _search_database_impl.
# _FTS5_SPECIAL/_escape_fts5/vector_search: re-exported for store.py facade (noqa: F401).
from rag.retrieval import (  # noqa: F401
    _FTS5_SPECIAL,
    _escape_fts5,
    _run_fts_query,
    _run_vector_query,
    _smart_tokenize,
    _vector_availability,
    vector_search,
)


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
    """
    with get_connection(db_path) as conn:
        plan = build_query_plan(query)
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

        def _make_result(row, score, ranking_signals=None):
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
                "ranking_signals": list(ranking_signals or []),
            }

        def _record_signal(candidate: dict, signal: RankingSignal) -> None:
            """Append a ranking signal to a candidate dict, preserving prior signals."""
            candidate.setdefault("ranking_signals", []).append(signal)


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
                            prior = results[cid].get("ranking_signals", []) if cid in results else []
                            results[cid] = _make_result(row, rrf_score, ranking_signals=prior)
                            _record_signal(
                                results[cid],
                                RankingSignal(
                                    name="hybrid.rrf",
                                    weight=rrf_score,
                                    value=fused['rrf_score'],
                                    details={"scale": 40.0},
                                ),
                            )
            except Exception:
                metadata = SearchMetadata(
                    mode="fts_only",
                    vector_available=False,
                    fallback_reason="vector_query_failed",
                )

        # 1-3. Symbol recall: iterate over plan.symbol_candidates and alias_symbol_candidates
        for candidate in plan.symbol_candidates + plan.alias_symbol_candidates:
            normalized = normalize_symbol(candidate)
            alias_derived = candidate in plan.alias_symbol_candidates

            # Exact symbol match (+100)
            rows = conn.execute(
                "SELECT s.name, c.* FROM symbols s JOIN chunks c ON s.chunk_id = c.id WHERE s.normalized_name = ?"
                + type_filter + addon_filter,
                [normalized] + type_params + addon_params,
            ).fetchall()
            for row in rows:
                cid = row["id"]
                if cid not in results or results[cid]["score"] < 100:
                    prior = results[cid].get("ranking_signals", []) if cid in results else []
                    results[cid] = _make_result(row, 100.0, ranking_signals=prior)
                    _record_signal(
                        results[cid],
                        RankingSignal(
                            name="symbol_recall.exact",
                            weight=100.0,
                            value=candidate,
                            details={"alias_derived": alias_derived},
                        ),
                    )

            # Suffix symbol match (+80)
            rows = conn.execute(
                "SELECT s.name, c.* FROM symbols s JOIN chunks c ON s.chunk_id = c.id WHERE s.normalized_name LIKE ?"
                + type_filter + addon_filter,
                [f"%.{normalized}"] + type_params + addon_params,
            ).fetchall()
            for row in rows:
                cid = row["id"]
                if cid not in results or results[cid]["score"] < 80:
                    prior = results[cid].get("ranking_signals", []) if cid in results else []
                    results[cid] = _make_result(row, 80.0, ranking_signals=prior)
                    _record_signal(
                        results[cid],
                        RankingSignal(
                            name="symbol_recall.suffix",
                            weight=80.0,
                            value=candidate,
                            details={"alias_derived": alias_derived},
                        ),
                    )

            # Prefix symbol match (+40)
            rows = conn.execute(
                "SELECT s.name, c.* FROM symbols s JOIN chunks c ON s.chunk_id = c.id WHERE s.normalized_name LIKE ?"
                + type_filter + addon_filter,
                [f"{normalized}%"] + type_params + addon_params,
            ).fetchall()
            for row in rows:
                cid = row["id"]
                if cid not in results or results[cid]["score"] < 40:
                    prior = results[cid].get("ranking_signals", []) if cid in results else []
                    results[cid] = _make_result(row, 40.0, ranking_signals=prior)
                    _record_signal(
                        results[cid],
                        RankingSignal(
                            name="symbol_recall.prefix",
                            weight=40.0,
                            value=candidate,
                            details={"alias_derived": alias_derived},
                        ),
                    )

        # 4. FTS5 search (bm25 → 0-40 score, skip chunks already in fused results)
        try:
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

            fts_results_by_id: dict = {}
            for variant in plan.fts_variants:
                for row in _run_fts_query(
                    conn,
                    variant,
                    limit,
                    fts_type_filter,
                    fts_type_params,
                    fts_addon_filter,
                    fts_addon_params,
                    fused_exclude,
                    fused_exclude_params,
                ):
                    current = fts_results_by_id.get(row["id"])
                    if current is None or row["score"] < current["score"]:
                        fts_results_by_id[row["id"]] = row
            for cid, row in fts_results_by_id.items():
                bm25 = abs(row["score"])
                fts_score = min(40.0, max(0.0, 40.0 / (1.0 + bm25 * 0.01)))
                if cid not in results or results[cid]["score"] < fts_score:
                    prior = results[cid].get("ranking_signals", []) if cid in results else []
                    results[cid] = _make_result(row["row"], fts_score, ranking_signals=prior)
                    _record_signal(
                        results[cid],
                        RankingSignal(
                            name="fts.bm25",
                            weight=fts_score,
                            value=bm25,
                            details={},
                        ),
                    )
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
                            _record_signal(
                                results[rel_id],
                                RankingSignal(
                                    name="graph.expansion",
                                    weight=0.0,
                                    value=rel_row["relation"],
                                    details={
                                        "relation": rel_row["relation"],
                                        "distance": 1,
                                        "metadata_only": True,
                                    },
                                ),
                            )
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
                                "ranking_signals": [
                                    RankingSignal(
                                        name="graph.expansion",
                                        weight=rel_score,
                                        value=rel_row["relation"],
                                        details={
                                            "relation": rel_row["relation"],
                                            "distance": 1,
                                            "source_score": result["score"],
                                            "weight": rel_row["weight"],
                                        },
                                    )
                                ],
                            }

            # Inheritance-directed traversal: when query signals inheritance
            # intent, pull parent class_summary chunks via 'inherits' edges.
            if plan.inheritance_intent:
                for result in sorted_results[:top_k]:
                    if result.get("chunk_type") != "class_summary":
                        continue
                    inh_rows = conn.execute(
                        "SELECT c.*, r.weight FROM chunk_relations r "
                        "JOIN chunks c ON c.id = r.target_id "
                        "WHERE r.source_id = ? AND r.relation = 'inherits'",
                        [result["id"]],
                    ).fetchall()
                    for rel_row in inh_rows:
                        rel_id = rel_row["id"]
                        rel_score = result["score"] * 0.7
                        if rel_id in expanded_ids:
                            if rel_id in results:
                                _record_signal(
                                    results[rel_id],
                                    RankingSignal(
                                        name="graph.inherits",
                                        weight=rel_score,
                                        value="inherits",
                                        details={
                                            "relation": "inherits",
                                            "distance": 1,
                                            "source_score": result["score"],
                                        },
                                    ),
                                )
                            continue
                        expanded_ids.add(rel_id)
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
                            "relation_type": "inherits",
                            "distance": 1,
                            "ranking_signals": [
                                RankingSignal(
                                    name="graph.inherits",
                                    weight=rel_score,
                                    value="inherits",
                                    details={
                                        "relation": "inherits",
                                        "distance": 1,
                                        "source_score": result["score"],
                                    },
                                )
                            ],
                        }

            # Re-sort after expansion
            sorted_results = sorted(results.values(), key=lambda r: r["score"], reverse=True)

        search_results = [
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
                ranking_signals=r.get("ranking_signals", []),
            )
            for r in sorted_results
        ]
        search_results = rerank_results(plan, search_results)
        return (search_results[:limit], metadata)
