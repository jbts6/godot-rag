#!/usr/bin/env python3
"""Print README benchmark tables from a built Godot RAG database."""

from __future__ import annotations

import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "rst2md"))

from rag.store import search_database  # noqa: E402

DB_PATH = ROOT / "godot_rag" / "rag" / "godot_docs.sqlite"
QUERIES = [
    ("change_scene", "scene_manager"),
    ("SceneManager", "scene_manager"),
    ("SceneManager.change_scene", "scene_manager"),
    ("BehaviorTree", "limboai"),
    ("DialogueManager", "dialogue_manager"),
    ("state machine transitions", None),
    ("scene transition animation", None),
    ("input helper gamepad", "input_helper"),
    ("input action mapping", None),
]


def _fmt_count(value: int) -> str:
    return f"{value:,}"


def _timed_search(db_path: Path, query: str, addon: str | None) -> tuple[int, float]:
    start = time.perf_counter()
    results = search_database(db_path, query, limit=3, doc_types=["addon"], addon=addon)
    elapsed_ms = (time.perf_counter() - start) * 1000
    return len(results), elapsed_ms


def main() -> int:
    if not DB_PATH.is_file():
        print(f"Database not found: {DB_PATH}", file=sys.stderr)
        print("Run ./build.sh --no-bump first.", file=sys.stderr)
        return 1

    conn = sqlite3.connect(DB_PATH)
    total_chunks = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    addon_chunks = conn.execute("SELECT COUNT(*) FROM chunks WHERE doc_type = 'addon'").fetchone()[0]
    godot_chunks = total_chunks - addon_chunks
    addon_count = conn.execute(
        "SELECT COUNT(DISTINCT addon) FROM chunks WHERE doc_type = 'addon' AND addon != ''"
    ).fetchone()[0]
    coverage = conn.execute(
        """
        SELECT
            addon,
            SUM(CASE WHEN chunk_type = 'addon_doc' THEN 1 ELSE 0 END) AS docs,
            SUM(CASE WHEN chunk_type = 'addon_example' THEN 1 ELSE 0 END) AS examples,
            SUM(CASE WHEN chunk_type = 'addon_api' THEN 1 ELSE 0 END) AS api,
            COUNT(*) AS total
        FROM chunks
        WHERE doc_type = 'addon'
        GROUP BY addon
        ORDER BY addon
        """
    ).fetchall()
    conn.close()

    print("### Benchmark Summary")
    print()
    print(
        f"Tested on a database of **{_fmt_count(total_chunks)} chunks** "
        f"({_fmt_count(godot_chunks)} Godot docs + {_fmt_count(addon_chunks)} addon chunks "
        f"across {addon_count} addons)."
    )
    print()
    print("### Query Hit Rate")
    print()
    print("| Query | RAG Results | Notes |")
    print("|---|---|---|")
    for query, addon in QUERIES:
        count, elapsed_ms = _timed_search(DB_PATH, query, addon)
        addon_note = f" `{addon}`" if addon else ""
        print(f"| `{query}` | ✅ {count} hits ({elapsed_ms:.1f}ms) | addon filter:{addon_note or ' none'} |")
    print()
    print("### Database Coverage")
    print()
    print("| Addon | Docs | Examples | API | Total |")
    print("|---|---|---|---|---|")
    totals = [0, 0, 0, 0]
    for addon, docs, examples, api, total in coverage:
        values = [docs or 0, examples or 0, api or 0, total or 0]
        totals = [left + right for left, right in zip(totals, values)]
        print(
            f"| {addon} | {_fmt_count(values[0]) if values[0] else '—'} | "
            f"{_fmt_count(values[1]) if values[1] else '—'} | "
            f"{_fmt_count(values[2]) if values[2] else '—'} | {_fmt_count(values[3])} |"
        )
    print(
        f"| **Total** | **{_fmt_count(totals[0])}** | **{_fmt_count(totals[1])}** | "
        f"**{_fmt_count(totals[2])}** | **{_fmt_count(totals[3])}** |"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
