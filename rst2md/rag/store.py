from pathlib import Path
from typing import List

from rag.db import clean_chunk_text, get_connection
from rag.indexer import build_database
from rag.searcher import (  # noqa: F401 — re-export for backward compat
    _FTS5_SPECIAL,
    _escape_fts5,
    _extract_snippet,
    _run_vector_query,
    _search_database_impl,
    _smart_tokenize,
    _vector_availability,
    rrf_fusion,
    search_database,
    search_database_with_metadata,
    vector_search,
)


def list_addons(db_path: Path) -> List[dict]:
    """List all addons indexed in the database.

    Returns a list of dicts with keys: addon, addon_name, chunk_count.
    """
    with get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT addon, addon_name, COUNT(*) as chunk_count "
            "FROM chunks WHERE addon != '' GROUP BY addon ORDER BY addon"
        ).fetchall()
        return [{"addon": r["addon"], "addon_name": r["addon_name"], "chunk_count": r["chunk_count"]} for r in rows]


def get_stats(db_path: Path) -> dict:
    """Get database statistics.

    Returns a dict with keys: chunks, symbols, relations, addons.
    """
    with get_connection(db_path) as conn:
        # Chunk stats
        chunk_total = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        chunk_by_type = {}
        for row in conn.execute("SELECT doc_type, COUNT(*) as cnt FROM chunks GROUP BY doc_type"):
            chunk_by_type[row["doc_type"]] = row["cnt"]

        # Symbol stats
        symbol_total = conn.execute("SELECT COUNT(*) FROM symbols").fetchone()[0]
        symbol_by_kind = {}
        for row in conn.execute("SELECT kind, COUNT(*) as cnt FROM symbols GROUP BY kind"):
            symbol_by_kind[row["kind"]] = row["cnt"]

        # Relation stats
        relation_total = conn.execute("SELECT COUNT(*) FROM chunk_relations").fetchone()[0]
        relation_by_type = {}
        for row in conn.execute("SELECT relation, COUNT(*) as cnt FROM chunk_relations GROUP BY relation"):
            relation_by_type[row["relation"]] = row["cnt"]

        # Addon stats
        addon_rows = conn.execute(
            "SELECT addon, addon_name, COUNT(*) as chunk_count "
            "FROM chunks WHERE addon != '' GROUP BY addon ORDER BY addon"
        ).fetchall()
        addons = [{"addon": r["addon"], "addon_name": r["addon_name"], "chunk_count": r["chunk_count"]} for r in addon_rows]

        return {
            "chunks": {"total": chunk_total, "by_type": chunk_by_type},
            "symbols": {"total": symbol_total, "by_kind": symbol_by_kind},
            "relations": {"total": relation_total, "by_type": relation_by_type},
            "addons": addons,
        }
