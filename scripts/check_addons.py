#!/usr/bin/env python3
"""Smoke test: verify addon discovery and key query hits."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "rst2md"))

from rag.addon_configs import all_smoke_queries  # noqa: E402
from rag.addon_docs import (
    collect_api_files,
    collect_doc_files,
    collect_example_files,
    discover_addon,
)
from rag.store import search_database  # noqa: E402

ADDONS_DIR = ROOT / "addons"
DB_PATH = ROOT / "godot_rag" / "rag" / "godot_docs.sqlite"


def _count_files(addon_dir: Path) -> tuple[int, int, int]:
    """Return (doc_count, example_count, api_count) for an addon."""
    layout = discover_addon(addon_dir)
    return (
        len(collect_doc_files(layout)),
        len(collect_example_files(layout)),
        len(collect_api_files(layout)),
    )


def _display_name(addon_dir: Path) -> str:
    layout = discover_addon(addon_dir)
    return layout.display_name


def _smoke_hit(query: str, addon: str) -> str:
    """Return '✅' if the query hits the addon, '❌' otherwise."""
    if not DB_PATH.is_file():
        return "⏭️"
    results = search_database(DB_PATH, query, limit=3, doc_types=["addon"], addon=addon)
    return "✅" if results else "❌"


def main() -> int:
    if not ADDONS_DIR.is_dir():
        print(f"Addons directory not found: {ADDONS_DIR}", file=sys.stderr)
        return 1

    addons = sorted(p for p in ADDONS_DIR.iterdir() if p.is_dir())
    smoke_queries = all_smoke_queries()
    smoke_map = {name: [] for _, name in smoke_queries}
    for query, addon_name in smoke_queries:
        smoke_map[addon_name].append(query)

    # Header
    print("| Addon | Display Name | Docs | Examples | API | Smoke |")
    print("|---|---|---|---|---|---|")

    for addon_dir in addons:
        name = addon_dir.name
        display = _display_name(addon_dir)
        docs, examples, apis = _count_files(addon_dir)

        # Find smoke queries for this addon
        smoke = ""
        if name in smoke_map:
            hits = []
            for query in smoke_map[name]:
                hits.append(f"{_smoke_hit(query, name)} `{query}`")
            smoke = " · ".join(hits)

        doc_s = str(docs) if docs else "—"
        ex_s = str(examples) if examples else "—"
        api_s = str(apis) if apis else "—"
        print(f"| {name} | {display} | {doc_s} | {ex_s} | {api_s} | {smoke} |")

    # Summary
    print()
    db_ok = "✅" if DB_PATH.is_file() else "❌ (run ./build.sh --no-bump first)"
    print(f"Database: {db_ok}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
