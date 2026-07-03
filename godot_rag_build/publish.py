from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from urllib.error import HTTPError
from urllib.request import urlopen

from godot_rag_build.orchestrator import BuildOptions, run_build
from godot_rag_build.reporting import BuildReport, print_summary, write_last_run
from godot_rag_build.runner import CommandRunner


@dataclass(frozen=True)
class PublishOptions:
    target: Literal["pypi", "testpypi"]
    no_bump: bool = False
    with_wiki: bool = True
    cache_dir: Path = Path(".cache/build-release")
    root: Path = Path(".")
    runner: CommandRunner | None = None


def check_worktree_clean(root: Path, runner: CommandRunner) -> None:
    result = runner.run(["git", "status", "--porcelain"], cwd=root, capture_output=True)
    if result.stdout.strip():
        raise RuntimeError("publish requires a clean worktree before build")


def package_version_exists(package: str, version: str, target: str, opener=urlopen) -> bool:
    host = "test.pypi.org" if target == "testpypi" else "pypi.org"
    url = f"https://{host}/pypi/{package}/{version}/json"
    try:
        with opener(url, timeout=15):
            return True
    except HTTPError as exc:
        if exc.code == 404:
            return False
        raise


def _failed_publish_report(options: PublishOptions, build_report: BuildReport, reason: str) -> BuildReport:
    return BuildReport(
        command="publish",
        options={"target": options.target, "no_bump": options.no_bump, "with_wiki": options.with_wiki},
        overall_status="FAIL",
        started_at=build_report.started_at,
        ended_at=build_report.ended_at,
        stages=build_report.stages,
        artifacts={**build_report.artifacts, "publish_error": reason},
    )


def run_publish(options: PublishOptions) -> BuildReport:
    root = options.root.resolve()
    runner = options.runner or CommandRunner()
    cache_dir = options.cache_dir if options.cache_dir.is_absolute() else root / options.cache_dir

    try:
        check_worktree_clean(root, runner)
    except RuntimeError as exc:
        empty = BuildReport("publish", {"target": options.target}, "FAIL", "", "", [], {"publish_error": str(exc)})
        write_last_run(empty, cache_dir)
        print_summary(empty)
        return empty

    build_report = run_build(BuildOptions(options.no_bump, options.with_wiki, cache_dir, root, runner))
    if build_report.overall_status != "OK":
        report = _failed_publish_report(options, build_report, "build failed")
        write_last_run(report, cache_dir)
        print_summary(report)
        return report

    try:
        runner.run(["uv", "run", "pytest", "-q"], cwd=root)
        env = dict(os.environ)
        env["PYTHONPATH"] = "rst2md"
        runner.run(["uv", "run", "python3", "-m", "rag.cli", "diagnostics", "--db", "godot_rag/rag/godot_docs.sqlite"], cwd=root, env=env)

        version = str(build_report.artifacts["package_version"])
        wheel = str(build_report.artifacts["wheel"])
        version_exists = package_version_exists("godot-rag", version, options.target)
    except (RuntimeError, OSError, KeyError) as exc:
        report = _failed_publish_report(options, build_report, str(exc))
        write_last_run(report, cache_dir)
        print_summary(report)
        return report

    if version_exists:
        report = _failed_publish_report(options, build_report, f"version {version} already exists on {options.target}")
        write_last_run(report, cache_dir)
        print_summary(report)
        return report

    upload = ["uv", "run", "--with", "twine", "python", "-m", "twine", "upload"]
    if options.target == "testpypi":
        upload += ["--repository", "testpypi"]
    upload.append(wheel)
    try:
        runner.run(upload, cwd=root)
    except (RuntimeError, OSError) as exc:
        report = _failed_publish_report(options, build_report, str(exc))
        write_last_run(report, cache_dir)
        print_summary(report)
        return report

    report = BuildReport(
        command="publish",
        options={"target": options.target, "no_bump": options.no_bump, "with_wiki": options.with_wiki},
        overall_status="OK",
        started_at=build_report.started_at,
        ended_at=build_report.ended_at,
        stages=build_report.stages,
        artifacts={**build_report.artifacts, "publish_target": options.target},
    )
    write_last_run(report, cache_dir)
    print_summary(report)
    return report
