#!/usr/bin/env python3
"""CLI for Godot Docs RAG."""

import argparse
import json
import sys
from pathlib import Path
from importlib import resources

from rag.diagnostics import run_diagnostics
from rag.store import (
    build_database,
    list_addons,
    search_database,
    search_database_with_metadata,
)


def default_db_path() -> Path:
    """Return the bundled database path for installed package usage."""
    return Path(resources.files("godot_rag.rag") / "godot_docs.sqlite")


def _db_path_from_args(args) -> Path:
    return Path(args.db) if args.db else default_db_path()


def _require_db(args) -> Path:
    db_path = _db_path_from_args(args)
    if not db_path.exists():
        print(f"Error: database not found: {db_path}", file=sys.stderr)
        sys.exit(1)
    return db_path


def cmd_build(args):
    """Build the RAG database."""
    docs_dir = Path(args.docs)
    db_path = Path(args.db)

    if not docs_dir.exists():
        print(f"Error: docs directory not found: {docs_dir}", file=sys.stderr)
        sys.exit(1)

    addons_dir = Path(args.addons) if args.addons else None
    build_database(docs_dir, db_path, addons_dir=addons_dir)
    print(f"Database built at {db_path}")


def _signal_to_dict(s):
    return {
        "name": s.name,
        "weight": s.weight,
        "value": s.value,
        "details": dict(s.details),
    }


def _result_to_dict(r):
    return {
        "score": r.score,
        "path": r.path,
        "start_line": r.start_line,
        "end_line": r.end_line,
        "doc_type": r.doc_type,
        "chunk_type": r.chunk_type,
        "addon": r.addon,
        "addon_name": r.addon_name,
        "symbol": r.symbol,
        "heading": r.heading,
        "breadcrumb": r.breadcrumb,
        "text": r.text,
        "relation_type": r.relation_type,
        "distance": r.distance,
        "ranking_signals": [_signal_to_dict(s) for s in r.ranking_signals],
    }


def _print_results(results, as_json: bool, metadata=None, debug_search: bool = False):
    """Print search results in text or JSON format."""
    if as_json:
        output = [_result_to_dict(r) for r in results]
        if debug_search and metadata is not None:
            output = {
                "metadata": {
                    "mode": metadata.mode,
                    "vector_available": metadata.vector_available,
                    "fallback_reason": metadata.fallback_reason,
                },
                "results": output,
            }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        if debug_search and metadata is not None:
            print(f"search_mode: {metadata.mode}")
            print(f"vector_available: {metadata.vector_available}")
            if metadata.fallback_reason:
                print(f"fallback_reason: {metadata.fallback_reason}")
            print("---")
        for i, r in enumerate(results):
            if i > 0:
                print("---")
            print(f"score: {r.score}")
            if r.relation_type:
                print(f"relation: {r.relation_type} (distance={r.distance})")
            if debug_search and r.ranking_signals:
                summary = ", ".join(f"{s.name}={s.weight:+g}" for s in r.ranking_signals)
                print(f"signals: {summary}")
            print(f"path: {r.path}:{r.start_line}-{r.end_line}")
            print(f"type: {r.chunk_type}")
            if r.addon:
                print(f"addon: {r.addon_name or r.addon}")
            print(f"symbol: {r.symbol}")
            print(f"heading: {r.heading}")
            print(f"breadcrumb: {r.breadcrumb}")
            print(f"text:\n{r.text}")


def _run_search(args, doc_types=None, addon=None, exclude_addons=False):
    db_path = _require_db(args)
    expand = not getattr(args, "no_expand", False)
    if args.debug_search:
        response = search_database_with_metadata(
            db_path,
            args.query,
            limit=args.limit,
            doc_types=doc_types,
            addon=addon,
            expand_graph=expand,
            exclude_addons=exclude_addons,
        )
        _print_results(response.results, args.json, response.metadata, debug_search=True)
        return

    results = search_database(
        db_path,
        args.query,
        limit=args.limit,
        doc_types=doc_types,
        addon=addon,
        expand_graph=expand,
        exclude_addons=exclude_addons,
    )
    _print_results(results, args.json)


def cmd_search(args):
    """Search the RAG database (all doc types)."""
    _run_search(args, exclude_addons=True)


def cmd_search_class(args):
    """Search class reference docs only."""
    _run_search(args, doc_types=["class"], exclude_addons=True)


def cmd_search_tutorial(args):
    """Search tutorial and getting-started docs only."""
    _run_search(args, doc_types=["tutorial", "getting_started"], exclude_addons=True)


def cmd_search_engine(args):
    """Search engine detail docs only."""
    _run_search(args, doc_types=["engine_detail"], exclude_addons=True)


def cmd_addons(args):
    """List all indexed addons."""
    db_path = _require_db(args)

    addons = list_addons(db_path)
    if not addons:
        print("No addons indexed in database.")
        return

    if args.json:
        print(json.dumps(addons, ensure_ascii=False, indent=2))
    else:
        total = sum(a["chunk_count"] for a in addons)
        for a in addons:
            print(f"{a['addon']:<20} {a['addon_name']:<25} {a['chunk_count']} chunks")
        print(f"\n{len(addons)} addons, {total} chunks total")


def cmd_search_addon(args):
    """Search addon docs and examples."""
    _run_search(args, doc_types=["addon"], addon=getattr(args, "addon", None))


def cmd_diagnostics(args):
    db_path = _db_path_from_args(args)
    report = run_diagnostics(db_path, check_model=not args.no_model)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"database: {report['db_path']}")
        print(f"ok: {report['ok']}")
        print(f"sqlite_vec_available: {report['sqlite_vec_available']}")
        print(f"vec_chunks: {report['vec_chunks_count']}")
        print(f"chunks: {report['chunks_count']}")
        print(f"row_parity: {report['row_parity']}")
        print(f"model_available: {report['model_available']}")
        if report["errors"]:
            print("errors: " + ", ".join(report["errors"]))
    if not report["ok"]:
        sys.exit(1)


def _add_search_args(parser):
    """Add common search arguments to a subparser."""
    parser.add_argument("query", help="Search query")
    parser.add_argument("--db", help="Path to SQLite database")
    parser.add_argument("--limit", type=int, default=8, help="Max results")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--debug-search", action="store_true", help="Include search-path metadata")
    parser.add_argument("--no-expand", action="store_true", help="Disable graph expansion")


def main():
    parser = argparse.ArgumentParser(description="Godot Docs RAG CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # build command
    build_parser = subparsers.add_parser("build", help="Build RAG database")
    build_parser.add_argument("--docs", required=True, help="Path to markdown docs directory")
    build_parser.add_argument("--db", required=True, help="Path to SQLite database")
    build_parser.add_argument("--addons", help="Path to addons directory (optional)")
    build_parser.set_defaults(func=cmd_build)

    # s command (all types)
    search_parser = subparsers.add_parser("s", aliases=["search"], help="Search all docs")
    _add_search_args(search_parser)
    search_parser.set_defaults(func=cmd_search)

    # s-class command
    class_parser = subparsers.add_parser("s-class", aliases=["search-class"], help="Search class reference docs")
    _add_search_args(class_parser)
    class_parser.set_defaults(func=cmd_search_class)

    # s-tutorial command
    tutorial_parser = subparsers.add_parser("s-tutorial", aliases=["search-tutorial"], help="Search tutorial and getting-started docs")
    _add_search_args(tutorial_parser)
    tutorial_parser.set_defaults(func=cmd_search_tutorial)

    # s-engine command
    engine_parser = subparsers.add_parser("s-engine", aliases=["search-engine"], help="Search engine detail docs")
    _add_search_args(engine_parser)
    engine_parser.set_defaults(func=cmd_search_engine)

    # addons command
    addons_parser = subparsers.add_parser("addons", help="List all indexed addons")
    addons_parser.add_argument("--db", help="Path to SQLite database")
    addons_parser.add_argument("--json", action="store_true", help="Output as JSON")
    addons_parser.set_defaults(func=cmd_addons)

    # s-addon command
    addon_parser = subparsers.add_parser("s-addon", aliases=["search-addon"], help="Search addon docs and examples")
    _add_search_args(addon_parser)
    addon_parser.add_argument("--addon", help="Filter by addon name (e.g. statecharts)")
    addon_parser.set_defaults(func=cmd_search_addon)

    # diagnostics command (used internally by build pipeline)
    diagnostics_parser = subparsers.add_parser("diagnostics", help="Validate semantic search readiness")
    diagnostics_parser.add_argument("--db", help="Path to SQLite database")
    diagnostics_parser.add_argument("--json", action="store_true", help="Output as JSON")
    diagnostics_parser.add_argument("--no-model", action="store_true", help="Skip embedding model availability check")
    diagnostics_parser.set_defaults(func=cmd_diagnostics)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
