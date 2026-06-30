"""Candidate retrieval: vector + FTS5 query construction and execution.

Focused sub-module split from searcher.py (change: split-searcher-modules).
Behavior is byte-for-byte identical to the previous searcher.py implementation.
"""
import re
import sqlite3
from typing import List

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


def _run_fts_query(
    conn, query: str, limit: int,
    fts_type_filter: str, fts_type_params: list,
    fts_addon_filter: str, fts_addon_params: list,
    fused_exclude: str = "", fused_exclude_params: list | None = None,
) -> list[dict]:
    if fused_exclude_params is None:
        fused_exclude_params = []
    escaped_query = _smart_tokenize(query)
    rows = conn.execute(
        f"""
        SELECT c.id, c.path, c.start_line, c.end_line, c.doc_type,
               c.chunk_type, c.addon, c.addon_name, c.symbol, c.heading,
               c.breadcrumb, c.text,
               bm25(chunks_fts) as score
        FROM chunks_fts
        JOIN chunks c ON chunks_fts.rowid = c.id
        WHERE chunks_fts MATCH ?
        {fts_type_filter}
        {fts_addon_filter}
        {fused_exclude}
        ORDER BY score
        LIMIT ?
        """,
        [escaped_query] + fts_type_params + fts_addon_params + fused_exclude_params + [limit * 3],
    ).fetchall()
    return [{"id": row["id"], "score": row["score"], "row": row} for row in rows]
