#!/usr/bin/env python3
"""Print or verify README benchmark tables from a built Godot RAG database."""

from __future__ import annotations

import re
import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "rst2md"))

from rag.store import search_database  # noqa: E402

DB_PATH = ROOT / "godot_rag" / "rag" / "godot_docs.sqlite"
README_PATH = ROOT / "README.md"
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


def _db_stats(db_path: Path) -> tuple[int, int, int, list[tuple[str, int, int, int, int]]]:
    """Return (total, godot, addon, addon_count, coverage_rows)."""
    conn = sqlite3.connect(db_path)
    total = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    addon_chunks = conn.execute("SELECT COUNT(*) FROM chunks WHERE doc_type = 'addon'").fetchone()[0]
    godot = total - addon_chunks
    addon_count = conn.execute(
        "SELECT COUNT(DISTINCT addon) FROM chunks WHERE doc_type = 'addon' AND addon != ''"
    ).fetchone()[0]
    coverage = conn.execute(
        """
        SELECT
            addon,
            SUM(CASE WHEN chunk_type = 'addon_doc' THEN 1 ELSE 0 END),
            SUM(CASE WHEN chunk_type = 'addon_example' THEN 1 ELSE 0 END),
            SUM(CASE WHEN chunk_type = 'addon_api' THEN 1 ELSE 0 END),
            COUNT(*)
        FROM chunks WHERE doc_type = 'addon'
        GROUP BY addon ORDER BY addon
        """
    ).fetchall()
    conn.close()
    return total, godot, addon_chunks, addon_count, coverage


def _print_report(total: int, godot: int, addon_chunks: int, addon_count: int,
                  coverage: list[tuple], db_path: Path) -> None:
    print("### Benchmark Summary")
    print()
    print(
        f"Tested on a database of **{_fmt_count(total)} chunks** "
        f"({_fmt_count(godot)} Godot docs + {_fmt_count(addon_chunks)} addon chunks "
        f"across {addon_count} addons)."
    )
    print()
    print("### Query Hit Rate")
    print()
    print("| Query | RAG Results | Notes |")
    print("|---|---|---|")
    for query, addon in QUERIES:
        count, elapsed_ms = _timed_search(db_path, query, addon)
        addon_note = f" `{addon}`" if addon else ""
        print(f"| `{query}` | ✅ {count} hits ({elapsed_ms:.1f}ms) | addon filter:{addon_note or ' none'} |")
    print()
    print("### Database Coverage")
    print()
    print("| Addon | Docs | Examples | API | Total |")
    print("|---|---|---|---|---|")
    totals = [0, 0, 0, 0]
    for addon, docs, examples, api, cnt in coverage:
        values = [docs or 0, examples or 0, api or 0, cnt or 0]
        totals = [a + b for a, b in zip(totals, values)]
        print(
            f"| {addon} | {_fmt_count(values[0]) if values[0] else '—'} | "
            f"{_fmt_count(values[1]) if values[1] else '—'} | "
            f"{_fmt_count(values[2]) if values[2] else '—'} | {_fmt_count(values[3])} |"
        )
    print(
        f"| **Total** | **{_fmt_count(totals[0])}** | **{_fmt_count(totals[1])}** | "
        f"**{_fmt_count(totals[2])}** | **{_fmt_count(totals[3])}** |"
    )


# -- Check mode: compare README with actual database --

_NUM_RE = re.compile(r"[\d,]+")


def _parse_readme_coverage(readme: str) -> dict[str, tuple[int, int, int, int]]:
    """Parse the coverage table from README. Returns {addon: (docs, examples, api, total)}."""
    result = {}
    in_table = False
    for line in readme.splitlines():
        if "| Addon | Docs | Examples | API | Total |" in line:
            in_table = True
            continue
        if in_table and line.startswith("|---"):
            continue
        if in_table and line.startswith("|"):
            cells = [c.strip() for c in line.split("|")]
            # cells: ['', addon, docs, examples, api, total, '']
            if len(cells) < 7 or cells[1].startswith("**"):
                if "**Total**" in line:
                    break
                continue
            addon = cells[1]
            nums = []
            for c in cells[2:6]:
                m = _NUM_RE.search(c)
                nums.append(int(m.group().replace(",", "")) if m else 0)
            result[addon] = tuple(nums)  # type: ignore[assignment]
        elif in_table and not line.startswith("|"):
            break
    return result


def _parse_readme_summary(readme: str) -> tuple[int, int, int]:
    """Parse the summary line 'X chunks (Y Godot docs + Z addon chunks)'."""
    m = re.search(
        r"\*\*([\d,]+)\s+chunks\*\*\s*\(([\d,]+)\s+Godot\s+docs\s+\+\s+([\d,]+)\s+addon",
        readme,
    )
    if not m:
        return 0, 0, 0
    return (
        int(m.group(1).replace(",", "")),
        int(m.group(2).replace(",", "")),
        int(m.group(3).replace(",", "")),
    )


def check_mode(db_path: Path) -> int:
    """Compare README numbers with actual database. Returns 0 if up-to-date, 1 if stale."""
    if not db_path.is_file():
        print(f"Database not found: {db_path}", file=sys.stderr)
        return 1
    if not README_PATH.is_file():
        print(f"README not found: {README_PATH}", file=sys.stderr)
        return 1

    total, godot, addon_chunks, _addon_count, coverage = _db_stats(db_path)
    readme = README_PATH.read_text(encoding="utf-8")

    errors = []

    # Check summary line
    r_total, r_godot, r_addon = _parse_readme_summary(readme)
    if r_total and r_total != total:
        errors.append(f"Total chunks: README={r_total}, actual={total}")
    if r_godot and r_godot != godot:
        errors.append(f"Godot docs: README={r_godot}, actual={godot}")
    if r_addon and r_addon != addon_chunks:
        errors.append(f"Addon chunks: README={r_addon}, actual={addon_chunks}")

    # Check coverage table
    readme_cov = _parse_readme_coverage(readme)
    actual_cov = {}
    for addon, docs, examples, api, cnt in coverage:
        actual_cov[addon] = (docs or 0, examples or 0, api or 0, cnt or 0)

    for addon, actual in actual_cov.items():
        if addon in readme_cov:
            readme_vals = readme_cov[addon]
            for i, label in enumerate(["docs", "examples", "api", "total"]):
                if readme_vals[i] != actual[i]:
                    errors.append(
                        f"{addon} {label}: README={readme_vals[i]}, actual={actual[i]}"
                    )

    if errors:
        print("README benchmark data is stale:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        print("\nRun: PYTHONPATH=rst2md uv run python3 scripts/benchmark_readme.py", file=sys.stderr)
        print("Then update README.md and README_zh.md with the output.", file=sys.stderr)
        return 1

    print("README benchmark data is up-to-date.")
    return 0


# -- Main --

def main() -> int:
    if "--check" in sys.argv:
        return check_mode(DB_PATH)

    if not DB_PATH.is_file():
        print(f"Database not found: {DB_PATH}", file=sys.stderr)
        print("Run ./build.sh --no-bump first.", file=sys.stderr)
        return 1

    total, godot, addon_chunks, addon_count, coverage = _db_stats(DB_PATH)
    _print_report(total, godot, addon_chunks, addon_count, coverage, DB_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
