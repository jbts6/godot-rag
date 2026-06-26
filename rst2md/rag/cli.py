#!/usr/bin/env python3
"""CLI for Godot Docs RAG."""

import argparse
import json
import sys
from pathlib import Path
from importlib import resources

from rag.store import build_database, search_database


def default_db_path() -> Path:
    """Return the bundled database path for installed package usage."""
    return Path(resources.files("godot_rag.rag") / "godot_docs.sqlite")


def _db_path_from_args(args) -> Path:
    return Path(args.db) if args.db else default_db_path()


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


def _print_results(results, as_json: bool):
    """Print search results in text or JSON format."""
    if as_json:
        output = [
            {
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
            }
            for r in results
        ]
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        for i, r in enumerate(results):
            if i > 0:
                print("---")
            print(f"score: {r.score}")
            print(f"path: {r.path}:{r.start_line}-{r.end_line}")
            print(f"type: {r.chunk_type}")
            if r.addon:
                print(f"addon: {r.addon_name or r.addon}")
            print(f"symbol: {r.symbol}")
            print(f"heading: {r.heading}")
            print(f"breadcrumb: {r.breadcrumb}")
            print(f"text:\n{r.text}")


def cmd_search(args):
    """Search the RAG database (all doc types)."""
    db_path = _db_path_from_args(args)

    if not db_path.exists():
        print(f"Error: database not found: {db_path}", file=sys.stderr)
        sys.exit(1)

    results = search_database(db_path, args.query, limit=args.limit)
    _print_results(results, args.json)


def cmd_search_class(args):
    """Search class reference docs only."""
    db_path = _db_path_from_args(args)

    if not db_path.exists():
        print(f"Error: database not found: {db_path}", file=sys.stderr)
        sys.exit(1)

    results = search_database(db_path, args.query, limit=args.limit, doc_types=["class"])
    _print_results(results, args.json)


def cmd_search_tutorial(args):
    """Search tutorial and getting-started docs only."""
    db_path = _db_path_from_args(args)

    if not db_path.exists():
        print(f"Error: database not found: {db_path}", file=sys.stderr)
        sys.exit(1)

    results = search_database(
        db_path, args.query, limit=args.limit, doc_types=["tutorial", "getting_started"]
    )
    _print_results(results, args.json)


def cmd_search_engine(args):
    """Search engine detail docs only."""
    db_path = _db_path_from_args(args)

    if not db_path.exists():
        print(f"Error: database not found: {db_path}", file=sys.stderr)
        sys.exit(1)

    results = search_database(
        db_path, args.query, limit=args.limit, doc_types=["engine_detail"]
    )
    _print_results(results, args.json)


def cmd_search_addon(args):
    """Search addon docs and examples."""
    db_path = _db_path_from_args(args)

    if not db_path.exists():
        print(f"Error: database not found: {db_path}", file=sys.stderr)
        sys.exit(1)

    results = search_database(
        db_path, args.query, limit=args.limit,
        doc_types=["addon"], addon=getattr(args, 'addon', None),
    )
    _print_results(results, args.json)


def _add_search_args(parser):
    """Add common search arguments to a subparser."""
    parser.add_argument("query", help="Search query")
    parser.add_argument("--db", help="Path to SQLite database")
    parser.add_argument("--limit", type=int, default=8, help="Max results")
    parser.add_argument("--json", action="store_true", help="Output as JSON")


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
    search_parser = subparsers.add_parser("s", help="Search all docs")
    _add_search_args(search_parser)
    search_parser.set_defaults(func=cmd_search)

    # s-class command
    class_parser = subparsers.add_parser("s-class", help="Search class reference docs")
    _add_search_args(class_parser)
    class_parser.set_defaults(func=cmd_search_class)

    # s-tutorial command
    tutorial_parser = subparsers.add_parser("s-tutorial", help="Search tutorial and getting-started docs")
    _add_search_args(tutorial_parser)
    tutorial_parser.set_defaults(func=cmd_search_tutorial)

    # s-engine command
    engine_parser = subparsers.add_parser("s-engine", help="Search engine detail docs")
    _add_search_args(engine_parser)
    engine_parser.set_defaults(func=cmd_search_engine)

    # s-addon command
    addon_parser = subparsers.add_parser("s-addon", help="Search addon docs and examples")
    _add_search_args(addon_parser)
    addon_parser.add_argument("--addon", help="Filter by addon name (e.g. statecharts)")
    addon_parser.set_defaults(func=cmd_search_addon)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
