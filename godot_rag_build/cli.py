from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Godot RAG release build tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build = subparsers.add_parser("build", help="Build local release artifacts")
    build.add_argument("--no-bump", action="store_true", help="Use the current pyproject.toml version")
    build.add_argument("--with-wiki", action="store_true", help="Include Scene Manager wiki input")
    build.add_argument("--cache-dir", default=".cache/build-release", help="Build cache directory")
    build.set_defaults(func=_cmd_build)

    publish = subparsers.add_parser("publish", help="Build and publish after required gates")
    publish.add_argument("--target", choices=["pypi", "testpypi"], required=True)
    publish.add_argument("--no-bump", action="store_true", help="Use the current pyproject.toml version")
    publish.add_argument("--with-wiki", action="store_true", help="Include Scene Manager wiki input")
    publish.add_argument("--cache-dir", default=".cache/build-release", help="Build cache directory")
    publish.set_defaults(func=_cmd_publish)

    diagnostics = subparsers.add_parser("diagnostics", help="Run release database diagnostics")
    diagnostics.add_argument("--db", default="godot_rag/rag/godot_docs.sqlite", help="SQLite database path")
    diagnostics.set_defaults(func=_cmd_diagnostics)

    clean_cache = subparsers.add_parser("clean-cache", help="Remove local release build cache")
    clean_cache.add_argument("--cache-dir", default=".cache/build-release", help="Build cache directory")
    clean_cache.set_defaults(func=_cmd_clean_cache)

    return parser


def _cmd_build(args: argparse.Namespace) -> int:
    from godot_rag_build.orchestrator import BuildOptions, run_build

    report = run_build(
        BuildOptions(no_bump=args.no_bump, with_wiki=args.with_wiki, cache_dir=Path(args.cache_dir))
    )
    return 0 if report.overall_status == "OK" else 1


def _cmd_publish(args: argparse.Namespace) -> int:
    from godot_rag_build.publish import PublishOptions, run_publish

    report = run_publish(
        PublishOptions(
            target=args.target,
            no_bump=args.no_bump,
            with_wiki=args.with_wiki,
            cache_dir=Path(args.cache_dir),
        )
    )
    return 0 if report.overall_status == "OK" else 1


def _cmd_diagnostics(args: argparse.Namespace) -> int:
    from godot_rag_build.orchestrator import run_release_diagnostics

    return run_release_diagnostics(Path(args.db))


def _cmd_clean_cache(args: argparse.Namespace) -> int:
    from godot_rag_build.cache import clean_cache

    clean_cache(Path(args.cache_dir))
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = create_parser()
    args = parser.parse_args(argv)
    return args.func(args)
