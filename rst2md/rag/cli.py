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
    get_stats,
    list_addons,
    search_database,
    search_database_with_metadata,
)


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

    expand = not getattr(args, 'no_expand', False)
    if args.debug_search:
        response = search_database_with_metadata(
            db_path, args.query, limit=args.limit, expand_graph=expand
        )
        _print_results(response.results, args.json, response.metadata, debug_search=True)
    else:
        results = search_database(db_path, args.query, limit=args.limit, expand_graph=expand)
        _print_results(results, args.json)


def cmd_search_class(args):
    """Search class reference docs only."""
    db_path = _db_path_from_args(args)

    if not db_path.exists():
        print(f"Error: database not found: {db_path}", file=sys.stderr)
        sys.exit(1)

    expand = not getattr(args, 'no_expand', False)
    if args.debug_search:
        response = search_database_with_metadata(
            db_path, args.query, limit=args.limit, doc_types=["class"], expand_graph=expand
        )
        _print_results(response.results, args.json, response.metadata, debug_search=True)
    else:
        results = search_database(db_path, args.query, limit=args.limit, doc_types=["class"], expand_graph=expand)
        _print_results(results, args.json)


def cmd_search_tutorial(args):
    """Search tutorial and getting-started docs only."""
    db_path = _db_path_from_args(args)

    if not db_path.exists():
        print(f"Error: database not found: {db_path}", file=sys.stderr)
        sys.exit(1)

    expand = not getattr(args, 'no_expand', False)
    if args.debug_search:
        response = search_database_with_metadata(
            db_path,
            args.query,
            limit=args.limit,
            doc_types=["tutorial", "getting_started"],
            expand_graph=expand,
        )
        _print_results(response.results, args.json, response.metadata, debug_search=True)
    else:
        results = search_database(
            db_path, args.query, limit=args.limit, doc_types=["tutorial", "getting_started"], expand_graph=expand
        )
        _print_results(results, args.json)


def cmd_search_engine(args):
    """Search engine detail docs only."""
    db_path = _db_path_from_args(args)

    if not db_path.exists():
        print(f"Error: database not found: {db_path}", file=sys.stderr)
        sys.exit(1)

    expand = not getattr(args, 'no_expand', False)
    if args.debug_search:
        response = search_database_with_metadata(
            db_path, args.query, limit=args.limit, doc_types=["engine_detail"], expand_graph=expand
        )
        _print_results(response.results, args.json, response.metadata, debug_search=True)
    else:
        results = search_database(
            db_path, args.query, limit=args.limit, doc_types=["engine_detail"], expand_graph=expand
        )
        _print_results(results, args.json)


def cmd_addons(args):
    """List all indexed addons."""
    db_path = _db_path_from_args(args)

    if not db_path.exists():
        print(f"Error: database not found: {db_path}", file=sys.stderr)
        sys.exit(1)

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


def cmd_stats(args):
    """Show database statistics."""
    db_path = _db_path_from_args(args)

    if not db_path.exists():
        print(f"Error: database not found: {db_path}", file=sys.stderr)
        sys.exit(1)

    stats = get_stats(db_path)

    if args.json:
        print(json.dumps(stats, ensure_ascii=False, indent=2))
    else:
        print("=== Database Statistics ===")
        print(f"\nChunks: {stats['chunks']['total']}")
        for doc_type, count in stats['chunks']['by_type'].items():
            print(f"  {doc_type}: {count}")

        print(f"\nSymbols: {stats['symbols']['total']}")
        for kind, count in stats['symbols']['by_kind'].items():
            print(f"  {kind}: {count}")

        print(f"\nRelations: {stats['relations']['total']}")
        for relation, count in stats['relations']['by_type'].items():
            print(f"  {relation}: {count}")

        if stats['addons']:
            print(f"\nAddons: {len(stats['addons'])}")
            for a in stats['addons']:
                print(f"  {a['addon']}: {a['chunk_count']} chunks")


def cmd_search_addon(args):
    """Search addon docs and examples."""
    db_path = _db_path_from_args(args)

    if not db_path.exists():
        print(f"Error: database not found: {db_path}", file=sys.stderr)
        sys.exit(1)

    expand = not getattr(args, 'no_expand', False)
    if args.debug_search:
        response = search_database_with_metadata(
            db_path,
            args.query,
            limit=args.limit,
            doc_types=["addon"],
            addon=getattr(args, 'addon', None),
            expand_graph=expand,
        )
        _print_results(response.results, args.json, response.metadata, debug_search=True)
    else:
        results = search_database(
            db_path, args.query, limit=args.limit,
            doc_types=["addon"], addon=getattr(args, 'addon', None),
            expand_graph=expand,
        )
        _print_results(results, args.json)


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

    # stats command
    stats_parser = subparsers.add_parser("stats", help="Show database statistics")
    stats_parser.add_argument("--db", help="Path to SQLite database")
    stats_parser.add_argument("--json", action="store_true", help="Output as JSON")
    stats_parser.set_defaults(func=cmd_stats)

    # s-addon command
    addon_parser = subparsers.add_parser("s-addon", aliases=["search-addon"], help="Search addon docs and examples")
    _add_search_args(addon_parser)
    addon_parser.add_argument("--addon", help="Filter by addon name (e.g. statecharts)")
    addon_parser.set_defaults(func=cmd_search_addon)

    diagnostics_parser = subparsers.add_parser("diagnostics", help="Validate semantic search readiness")
    diagnostics_parser.add_argument("--db", help="Path to SQLite database")
    diagnostics_parser.add_argument("--json", action="store_true", help="Output as JSON")
    diagnostics_parser.add_argument("--no-model", action="store_true", help="Skip embedding model availability check")
    diagnostics_parser.set_defaults(func=cmd_diagnostics)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
