from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Godot RAG release build tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build = subparsers.add_parser("build", help="Build local release artifacts")
    build.add_argument("--no-bump", action="store_true", help="Use the current pyproject.toml version")
    build.add_argument("--no-wiki", action="store_false", dest="with_wiki", help="Exclude Scene Manager wiki input")
    build.add_argument("--cache-dir", default=".cache/build-release", help="Build cache directory")
    build.set_defaults(func=_cmd_build)

    publish = subparsers.add_parser("publish", help="Build and publish after required gates")
    publish.add_argument("--target", choices=["pypi", "testpypi"], required=True)
    publish.add_argument("--no-bump", action="store_true", help="Use the current pyproject.toml version")
    publish.add_argument("--no-wiki", action="store_false", dest="with_wiki", help="Exclude Scene Manager wiki input")
    publish.add_argument("--cache-dir", default=".cache/build-release", help="Build cache directory")
    publish.set_defaults(func=_cmd_publish)

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


def main(argv: Sequence[str] | None = None) -> int:
    parser = create_parser()
    args = parser.parse_args(argv)
    return args.func(args)
