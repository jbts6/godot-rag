---
change: build-efficiency
design-doc: docs/superpowers/specs/2026-06-28-build-efficiency-design.md
base-ref: 752d1fff4f69cc473b40f953aa12a389d8b41411
archived-with: 2026-06-28-build-efficiency
---

# Build Efficiency Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把本地 release 构建从 `build.sh` 内联流程迁移到可测试的 Python 构建工具，并用保守指纹缓存减少重复构建，同时保留现有本地发布便利性。

**Architecture:** 新增可打包模块 `godot_rag_build` 作为 `godot-rag-build` console script 的导入目标，避免把入口指向未随 wheel 打包的 `scripts/` 目录。Python 工具负责 CLI、阶段编排、缓存 manifest、run report、publish gates、wiki 路径和 diagnostics；`build.sh` 只做 legacy 参数映射和 `uv run godot-rag-build ...` 委托。所有外部命令通过可注入 runner 执行，单元测试用 fake runner 覆盖顺序、缓存和失败路径，不触发真实上传或完整 RAG 重建。

**Tech Stack:** Python 3.10+, argparse, dataclasses, pathlib, hashlib, json, shutil, subprocess, urllib.request, pytest, uv, hatchling, Bash wrapper.

## Global Constraints

- 本 change 只优化本地 release build；CI 不作为速度优化目标，只保持现有 workflow 可用。
- `godot-rag-build` 必须提供 `build`、`publish`、`diagnostics`、`clean-cache` 四个 subcommands。
- Design Doc 中的 `scripts.build_release:main` 入口在当前 wheel package 配置下不可导入；实现必须改为 `godot_rag_build.cli:main`，并把 `godot_rag_build` 加入 hatch wheel packages。
- `publish` 必须执行完整 build、tests、release diagnostics、目标 index 版本存在检查，然后才允许 upload。
- `publish` 不得提供 `--skip-tests` 或同义跳过测试参数。
- 缓存只在 manifest 指纹完全匹配、影响选项匹配、期望输出存在且 output check 通过时使用；任何不确定都必须运行阶段。
- `--with-wiki` 必须进入受影响阶段指纹；wiki build 和 non-wiki build 不得互相复用缓存。
- `.cache/build-release/manifest.json` 保存可复用缓存状态；`.cache/build-release/last-run.json` 保存最近一次运行报告。
- report 不得记录 token、password、credential 或完整环境变量。
- `build.sh` 不得保留 docs conversion、RAG database build、package assembly、upload 等主构建逻辑。
- 每个实现任务完成后运行该任务列出的测试命令并提交；提交前用 `rtk git status --short` 检查生成物没有进入 git 跟踪。

archived-with: 2026-06-28-build-efficiency
---

## File Structure

- Create: `godot_rag_build/__init__.py`
  - Export build tool package marker and `__all__`.
- Create: `godot_rag_build/cli.py`
  - Own `create_parser()` and `main(argv=None) -> int`; parse `build`、`publish`、`diagnostics`、`clean-cache`。
- Create: `godot_rag_build/runner.py`
  - Own `CommandRunner.run(...)` and `CommandResult`; every subprocess call goes through this file.
- Create: `godot_rag_build/stages.py`
  - Own stage dataclasses, statuses, failure type, and ordered stage runner.
- Create: `godot_rag_build/reporting.py`
  - Own terminal table and `.cache/build-release/last-run.json` serialization.
- Create: `godot_rag_build/fingerprints.py`
  - Own stable file/tree/tool/version fingerprints.
- Create: `godot_rag_build/cache.py`
  - Own manifest load/save, skip decision, success recording, and cache cleanup.
- Create: `godot_rag_build/orchestrator.py`
  - Own local build stages: version resolution, docs conversion, wiki prep/cleanup, RAG DB build, diagnostics, package tree assembly, README merge, wheel build, twine check.
- Create: `godot_rag_build/publish.py`
  - Own publish gate ordering, package index version check, and upload command construction.
- Modify: `pyproject.toml`
  - Add `godot-rag-build = "godot_rag_build.cli:main"` and include `godot_rag_build` in hatch wheel packages.
- Modify: `build.sh`
  - Replace inline implementation with thin delegation wrapper.
- Modify: `README.md`
  - Update English local rebuild instructions to prefer `uv run godot-rag-build build`.
- Modify: `README_zh.md`
  - Update Chinese local rebuild instructions to prefer `uv run godot-rag-build build`.
- Test: `rst2md/tests/test_build_release_cli.py`
  - CLI parser, console script config, help content, and no `--skip-tests`.
- Test: `rst2md/tests/test_build_release_stages.py`
  - Stage run/fail/report behavior.
- Test: `rst2md/tests/test_build_release_cache.py`
  - Manifest, fingerprint, skip/miss behavior, clean-cache.
- Test: `rst2md/tests/test_build_release_orchestrator.py`
  - Local build command sequence, version resolution, wiki cleanup, package assembly helpers.
- Test: `rst2md/tests/test_build_release_publish.py`
  - Publish gate ordering, version-exists failure before upload, upload commands.
- Test: `rst2md/tests/test_build_release_wrapper.py`
  - `build.sh` syntax and legacy argument delegation.

## Task 1: Packaged CLI Entrypoint

**Files:**
- Create: `godot_rag_build/__init__.py`
- Create: `godot_rag_build/cli.py`
- Create: `godot_rag_build/runner.py`
- Modify: `pyproject.toml`
- Test: `rst2md/tests/test_build_release_cli.py`

**Interfaces:**
- Produces: `godot_rag_build.cli.create_parser() -> argparse.ArgumentParser`
- Produces: `godot_rag_build.cli.main(argv: Sequence[str] | None = None) -> int`
- Produces: `godot_rag_build.runner.CommandResult(args: tuple[str, ...], returncode: int, stdout: str, stderr: str)`
- Produces: `godot_rag_build.runner.CommandRunner.run(args: Sequence[str], *, cwd: Path | None = None, env: Mapping[str, str] | None = None, check: bool = True, capture_output: bool = False) -> CommandResult`
- Produces: project script `godot-rag-build = "godot_rag_build.cli:main"`
- Consumes: no build implementation from later tasks; command handlers may import later modules lazily inside handler functions.

- [x] **Step 1: Write failing CLI tests**

Create `rst2md/tests/test_build_release_cli.py`:

```python
from pathlib import Path

import pytest

from godot_rag_build.cli import create_parser, main


def test_help_lists_required_subcommands(capsys):
    parser = create_parser()

    with pytest.raises(SystemExit) as exc:
        parser.parse_args(["--help"])

    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "build" in out
    assert "publish" in out
    assert "diagnostics" in out
    assert "clean-cache" in out


def test_publish_help_has_no_skip_tests(capsys):
    parser = create_parser()

    with pytest.raises(SystemExit) as exc:
        parser.parse_args(["publish", "--help"])

    assert exc.value.code == 0
    assert "--skip-tests" not in capsys.readouterr().out


def test_publish_target_choices_are_pypi_and_testpypi():
    args = create_parser().parse_args(["publish", "--target", "testpypi"])

    assert args.command == "publish"
    assert args.target == "testpypi"


def test_project_script_points_to_packaged_module():
    text = Path("pyproject.toml").read_text(encoding="utf-8")

    assert 'godot-rag-build = "godot_rag_build.cli:main"' in text
    assert 'packages = ["godot_rag", "godot_rag_build"]' in text


def test_main_returns_zero_for_help(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--help"])

    assert exc.value.code == 0
    assert "Godot RAG release build tool" in capsys.readouterr().out
```

- [x] **Step 2: Run tests to verify they fail**

Run:

```bash
rtk uv run pytest rst2md/tests/test_build_release_cli.py -q
```

Expected: FAIL because `godot_rag_build` and the project script do not exist.

- [x] **Step 3: Add package marker and runner shell**

Create `godot_rag_build/__init__.py`:

```python
"""Release build tooling for the Godot RAG package."""

__all__ = []
```

Create `godot_rag_build/runner.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from subprocess import PIPE, run
from typing import Mapping, Sequence


@dataclass(frozen=True)
class CommandResult:
    args: tuple[str, ...]
    returncode: int
    stdout: str = ""
    stderr: str = ""


class CommandRunner:
    def run(
        self,
        args: Sequence[str],
        *,
        cwd: Path | None = None,
        env: Mapping[str, str] | None = None,
        check: bool = True,
        capture_output: bool = False,
    ) -> CommandResult:
        completed = run(
            list(args),
            cwd=str(cwd) if cwd else None,
            env=dict(env) if env else None,
            check=False,
            text=True,
            stdout=PIPE if capture_output else None,
            stderr=PIPE if capture_output else None,
        )
        result = CommandResult(
            args=tuple(args),
            returncode=completed.returncode,
            stdout=completed.stdout or "",
            stderr=completed.stderr or "",
        )
        if check and result.returncode != 0:
            raise RuntimeError(f"command failed ({result.returncode}): {' '.join(result.args)}")
        return result
```

- [x] **Step 4: Add CLI parser skeleton**

Create `godot_rag_build/cli.py`:

```python
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
```

- [x] **Step 5: Wire project script and package inclusion**

Modify `pyproject.toml`:

```toml
[project.scripts]
godot-rag = "godot_rag.rag.cli:main"
godot-rag-build = "godot_rag_build.cli:main"
```

Modify the wheel target:

```toml
[tool.hatch.build.targets.wheel]
packages = ["godot_rag", "godot_rag_build"]
exclude = ["godot_rag/docs-md/**"]
```

- [x] **Step 6: Run CLI tests**

Run:

```bash
rtk uv run pytest rst2md/tests/test_build_release_cli.py -q
```

Expected: PASS for CLI parser and pyproject assertions. Handler imports may remain unexecuted because these tests only parse help and config.

- [x] **Step 7: Commit Task 1**

Run:

```bash
rtk git status --short
rtk git add pyproject.toml godot_rag_build/__init__.py godot_rag_build/cli.py godot_rag_build/runner.py rst2md/tests/test_build_release_cli.py
rtk git commit -m "feat: add release build CLI entrypoint"
```

## Task 2: Stage Model And Run Reporting

**Files:**
- Create: `godot_rag_build/stages.py`
- Create: `godot_rag_build/reporting.py`
- Test: `rst2md/tests/test_build_release_stages.py`

**Interfaces:**
- Consumes: `CommandRunner` from Task 1.
- Produces: `StageStatus` enum with values `RUN`, `SKIP`, `FAIL`.
- Produces: `StageResult(name: str, status: StageStatus, elapsed_seconds: float, reason: str, fingerprint: str | None, outputs: list[str])`.
- Produces: `StageContext(root: Path, cache_dir: Path, runner: CommandRunner, options: Mapping[str, object], artifacts: dict[str, str])`.
- Produces: `StageSpec(name: str, action: Callable[[StageContext], list[str]], cacheable: bool = False, fingerprint: Callable[[StageContext], str] | None = None, output_check: Callable[[StageContext], bool] | None = None, dependencies: tuple[str, ...] = ())`.
- Produces: `run_stages(specs: Sequence[StageSpec], context: StageContext, cache: BuildCache | None = None) -> list[StageResult]`.
- Produces: `BuildReport(command: str, options: dict[str, object], overall_status: str, started_at: str, ended_at: str, stages: list[StageResult], artifacts: dict[str, str])`.
- Produces: `print_summary(report: BuildReport) -> None` and `write_last_run(report: BuildReport, cache_dir: Path) -> Path`.

- [x] **Step 1: Write failing stage/report tests]**

Create `rst2md/tests/test_build_release_stages.py`:

```python
from pathlib import Path

import pytest

from godot_rag_build.reporting import BuildReport, write_last_run
from godot_rag_build.runner import CommandRunner
from godot_rag_build.stages import StageContext, StageError, StageSpec, StageStatus, run_stages


def test_run_stages_records_success_and_artifacts(tmp_path):
    calls = []

    def action(ctx):
        calls.append(ctx.root)
        ctx.artifacts["wheel"] = "dist/godot_rag-1.0-py3-none-any.whl"
        return ["dist/godot_rag-1.0-py3-none-any.whl"]

    ctx = StageContext(
        root=tmp_path,
        cache_dir=tmp_path / ".cache/build-release",
        runner=CommandRunner(),
        options={},
        artifacts={},
    )

    results = run_stages([StageSpec(name="wheel", action=action)], ctx)

    assert calls == [tmp_path]
    assert results[0].name == "wheel"
    assert results[0].status is StageStatus.RUN
    assert results[0].reason == "completed"
    assert results[0].outputs == ["dist/godot_rag-1.0-py3-none-any.whl"]
    assert ctx.artifacts["wheel"].startswith("dist/")


def test_run_stages_stops_on_failure(tmp_path):
    calls = []

    def fail(_ctx):
        calls.append("fail")
        raise StageError("db failed")

    def never(_ctx):
        calls.append("never")
        return []

    ctx = StageContext(tmp_path, tmp_path / ".cache/build-release", CommandRunner(), {}, {})

    results = run_stages(
        [StageSpec(name="rag-db", action=fail), StageSpec(name="wheel", action=never)],
        ctx,
    )

    assert calls == ["fail"]
    assert [result.name for result in results] == ["rag-db"]
    assert results[0].status is StageStatus.FAIL
    assert results[0].reason == "db failed"


def test_last_run_json_contains_stage_decisions(tmp_path):
    result = StageStatus.RUN
    report = BuildReport(
        command="build",
        options={"with_wiki": False},
        overall_status="OK",
        started_at="2026-06-28T00:00:00Z",
        ended_at="2026-06-28T00:00:01Z",
        stages=[],
        artifacts={"db": "godot_rag/rag/godot_docs.sqlite"},
    )

    path = write_last_run(report, tmp_path / ".cache/build-release")

    assert path == tmp_path / ".cache/build-release/last-run.json"
    text = path.read_text(encoding="utf-8")
    assert '"command": "build"' in text
    assert '"with_wiki": false' in text
    assert result.value == "RUN"
```

- [x] **Step 2: Run tests to verify they fail**

Run:

```bash
rtk uv run pytest rst2md/tests/test_build_release_stages.py -q
```

Expected: FAIL because stage and reporting modules do not exist.

- [x] **Step 3: Implement stage primitives**

Create `godot_rag_build/stages.py`:

```python
from __future__ import annotations

import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from godot_rag_build.runner import CommandRunner


class StageStatus(Enum):
    RUN = "RUN"
    SKIP = "SKIP"
    FAIL = "FAIL"


class StageError(RuntimeError):
    pass


@dataclass
class StageContext:
    root: Path
    cache_dir: Path
    runner: CommandRunner
    options: Mapping[str, object]
    artifacts: dict[str, str]


@dataclass(frozen=True)
class StageResult:
    name: str
    status: StageStatus
    elapsed_seconds: float
    reason: str
    fingerprint: str | None = None
    outputs: list[str] | None = None


@dataclass(frozen=True)
class StageSpec:
    name: str
    action: Callable[[StageContext], list[str]]
    cacheable: bool = False
    fingerprint: Callable[[StageContext], str] | None = None
    output_check: Callable[[StageContext], bool] | None = None
    dependencies: tuple[str, ...] = ()


def run_stages(
    specs: Sequence[StageSpec],
    context: StageContext,
    cache=None,
) -> list[StageResult]:
    completed: set[str] = set()
    results: list[StageResult] = []
    for spec in specs:
        missing = [dep for dep in spec.dependencies if dep not in completed]
        if missing:
            raise StageError(f"stage {spec.name} missing dependencies: {', '.join(missing)}")

        started = time.perf_counter()
        digest = spec.fingerprint(context) if spec.fingerprint else None
        try:
            if cache and spec.cacheable and digest:
                decision = cache.should_skip(spec.name, digest, context, spec.output_check)
                if decision.skip:
                    results.append(
                        StageResult(
                            name=spec.name,
                            status=StageStatus.SKIP,
                            elapsed_seconds=time.perf_counter() - started,
                            reason=decision.reason,
                            fingerprint=digest,
                            outputs=decision.outputs,
                        )
                    )
                    completed.add(spec.name)
                    continue

            outputs = spec.action(context)
            result = StageResult(
                name=spec.name,
                status=StageStatus.RUN,
                elapsed_seconds=time.perf_counter() - started,
                reason="completed",
                fingerprint=digest,
                outputs=outputs,
            )
            results.append(result)
            if cache and spec.cacheable and digest:
                cache.record_success(spec.name, digest, outputs)
            completed.add(spec.name)
        except StageError as exc:
            results.append(
                StageResult(
                    name=spec.name,
                    status=StageStatus.FAIL,
                    elapsed_seconds=time.perf_counter() - started,
                    reason=str(exc),
                    fingerprint=digest,
                    outputs=[],
                )
            )
            break
    return results
```

- [x] **Step 4: Implement report serialization and summary]**

Create `godot_rag_build/reporting.py`:

```python
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from godot_rag_build.stages import StageResult


@dataclass(frozen=True)
class BuildReport:
    command: str
    options: dict[str, object]
    overall_status: str
    started_at: str
    ended_at: str
    stages: list[StageResult]
    artifacts: dict[str, str]


def _stage_to_dict(stage: StageResult) -> dict[str, object]:
    return {
        "name": stage.name,
        "status": stage.status.value,
        "elapsed_seconds": round(stage.elapsed_seconds, 6),
        "reason": stage.reason,
        "fingerprint": stage.fingerprint,
        "outputs": stage.outputs or [],
    }


def report_to_dict(report: BuildReport) -> dict[str, object]:
    return {
        "command": report.command,
        "options": report.options,
        "overall_status": report.overall_status,
        "started_at": report.started_at,
        "ended_at": report.ended_at,
        "stages": [_stage_to_dict(stage) for stage in report.stages],
        "artifacts": report.artifacts,
    }


def write_last_run(report: BuildReport, cache_dir: Path) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / "last-run.json"
    path.write_text(json.dumps(report_to_dict(report), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def print_summary(report: BuildReport) -> None:
    print(f"{'Stage':<24} {'Status':<6} {'Time':<8} Reason")
    for stage in report.stages:
        elapsed = f"{stage.elapsed_seconds:.2f}s"
        print(f"{stage.name:<24} {stage.status.value:<6} {elapsed:<8} {stage.reason}")
```

- [x] **Step 5: Run stage/report tests]**

Run:

```bash
rtk uv run pytest rst2md/tests/test_build_release_stages.py -q
```

Expected: PASS.

- [x] **Step 6: Commit Task 2]**

Run:

```bash
rtk git status --short
rtk git add godot_rag_build/stages.py godot_rag_build/reporting.py rst2md/tests/test_build_release_stages.py
rtk git commit -m "feat: add release build stage reporting"
```

## Task 3: Fingerprints, Manifest Cache, And Clean Cache

**Files:**
- Create: `godot_rag_build/fingerprints.py`
- Create: `godot_rag_build/cache.py`
- Test: `rst2md/tests/test_build_release_cache.py`

**Interfaces:**
- Consumes: `StageContext` from Task 2.
- Produces: `fingerprint_file(path: Path) -> str`
- Produces: `fingerprint_tree(path: Path, *, include_suffixes: tuple[str, ...] | None = None, exclude_dirs: tuple[str, ...] = ()) -> str`
- Produces: `fingerprint_items(items: Mapping[str, str]) -> str`
- Produces: `BuildCache.load(cache_dir: Path) -> BuildCache`
- Produces: `BuildCache.should_skip(stage_name: str, fingerprint: str, context: StageContext, output_check: Callable[[StageContext], bool] | None) -> CacheDecision`
- Produces: `BuildCache.record_success(stage_name: str, fingerprint: str, outputs: list[str]) -> None`
- Produces: `BuildCache.save() -> Path`
- Produces: `clean_cache(cache_dir: Path) -> None`

- [x] **Step 1: Write failing cache tests**

Create `rst2md/tests/test_build_release_cache.py`:

```python
from pathlib import Path

from godot_rag_build.cache import BuildCache, clean_cache
from godot_rag_build.fingerprints import fingerprint_file, fingerprint_items, fingerprint_tree
from godot_rag_build.runner import CommandRunner
from godot_rag_build.stages import StageContext


def test_file_fingerprint_changes_with_content(tmp_path):
    path = tmp_path / "input.txt"
    path.write_text("one", encoding="utf-8")
    first = fingerprint_file(path)

    path.write_text("two", encoding="utf-8")
    second = fingerprint_file(path)

    assert first != second


def test_tree_fingerprint_uses_stable_order(tmp_path):
    root = tmp_path / "tree"
    root.mkdir()
    (root / "b.py").write_text("b", encoding="utf-8")
    (root / "a.py").write_text("a", encoding="utf-8")

    first = fingerprint_tree(root, include_suffixes=(".py",))
    second = fingerprint_tree(root, include_suffixes=(".py",))

    assert first == second


def test_options_change_fingerprint():
    no_wiki = fingerprint_items({"with_wiki": "false", "godot_docs_head": "abc"})
    with_wiki = fingerprint_items({"with_wiki": "true", "godot_docs_head": "abc"})

    assert no_wiki != with_wiki


def test_cache_skips_only_when_fingerprint_and_outputs_match(tmp_path):
    cache_dir = tmp_path / ".cache/build-release"
    output = tmp_path / "dist/pkg.whl"
    output.parent.mkdir()
    output.write_text("wheel", encoding="utf-8")

    cache = BuildCache.load(cache_dir)
    cache.record_success("wheel", "abc", [str(output)])
    cache.save()
    loaded = BuildCache.load(cache_dir)
    ctx = StageContext(tmp_path, cache_dir, CommandRunner(), {}, {})

    decision = loaded.should_skip("wheel", "abc", ctx, lambda _ctx: output.exists())

    assert decision.skip is True
    assert decision.reason == "fingerprint match"
    assert decision.outputs == [str(output)]


def test_cache_miss_when_output_check_fails(tmp_path):
    cache_dir = tmp_path / ".cache/build-release"
    cache = BuildCache.load(cache_dir)
    cache.record_success("rag-db", "abc", [str(tmp_path / "missing.sqlite")])
    cache.save()
    ctx = StageContext(tmp_path, cache_dir, CommandRunner(), {}, {})

    decision = BuildCache.load(cache_dir).should_skip("rag-db", "abc", ctx, lambda _ctx: False)

    assert decision.skip is False
    assert decision.reason == "outputs missing"


def test_clean_cache_removes_cache_dir(tmp_path):
    cache_dir = tmp_path / ".cache/build-release"
    cache_dir.mkdir(parents=True)
    (cache_dir / "manifest.json").write_text("{}", encoding="utf-8")

    clean_cache(cache_dir)

    assert not cache_dir.exists()
```

- [x] **Step 2: Run tests to verify they fail**

Run:

```bash
rtk uv run pytest rst2md/tests/test_build_release_cache.py -q
```

Expected: FAIL because cache and fingerprint modules do not exist.

- [x] **Step 3: Implement stable fingerprints**

Create `godot_rag_build/fingerprints.py`:

```python
from __future__ import annotations

import hashlib
from collections.abc import Mapping
from pathlib import Path


def _hash_bytes(chunks: list[bytes]) -> str:
    digest = hashlib.sha256()
    for chunk in chunks:
        digest.update(chunk)
    return digest.hexdigest()


def fingerprint_items(items: Mapping[str, str]) -> str:
    chunks: list[bytes] = []
    for key in sorted(items):
        chunks.append(key.encode("utf-8") + b"\0" + items[key].encode("utf-8") + b"\0")
    return _hash_bytes(chunks)


def fingerprint_file(path: Path) -> str:
    if not path.exists():
        return fingerprint_items({str(path): "missing"})
    return _hash_bytes([str(path).encode("utf-8"), b"\0", path.read_bytes()])


def fingerprint_tree(
    path: Path,
    *,
    include_suffixes: tuple[str, ...] | None = None,
    exclude_dirs: tuple[str, ...] = (),
) -> str:
    if not path.exists():
        return fingerprint_items({str(path): "missing"})
    chunks: list[bytes] = []
    excluded = set(exclude_dirs)
    for child in sorted(path.rglob("*")):
        if any(part in excluded for part in child.relative_to(path).parts):
            continue
        if child.is_dir():
            continue
        if include_suffixes and child.suffix not in include_suffixes:
            continue
        rel = child.relative_to(path).as_posix()
        chunks.append(rel.encode("utf-8") + b"\0")
        chunks.append(child.read_bytes() + b"\0")
    return _hash_bytes(chunks)
```

- [x] **Step 4: Implement manifest cache**

Create `godot_rag_build/cache.py`:

```python
from __future__ import annotations

import json
import shutil
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from godot_rag_build.stages import StageContext


@dataclass(frozen=True)
class CacheDecision:
    skip: bool
    reason: str
    outputs: list[str]


class BuildCache:
    def __init__(self, cache_dir: Path, entries: dict[str, dict[str, object]] | None = None):
        self.cache_dir = cache_dir
        self.entries = entries or {}

    @classmethod
    def load(cls, cache_dir: Path) -> "BuildCache":
        manifest = cache_dir / "manifest.json"
        if not manifest.exists():
            return cls(cache_dir)
        data = json.loads(manifest.read_text(encoding="utf-8"))
        return cls(cache_dir, dict(data.get("stages", {})))

    def should_skip(
        self,
        stage_name: str,
        fingerprint: str,
        context: StageContext,
        output_check: Callable[[StageContext], bool] | None,
    ) -> CacheDecision:
        entry = self.entries.get(stage_name)
        if not entry:
            return CacheDecision(False, "manifest missing", [])
        if entry.get("fingerprint") != fingerprint:
            return CacheDecision(False, "fingerprint changed", list(entry.get("outputs", [])))
        outputs = list(entry.get("outputs", []))
        if output_check and not output_check(context):
            return CacheDecision(False, "outputs missing", outputs)
        for output in outputs:
            if not Path(output).exists():
                return CacheDecision(False, "outputs missing", outputs)
        return CacheDecision(True, "fingerprint match", outputs)

    def record_success(self, stage_name: str, fingerprint: str, outputs: list[str]) -> None:
        self.entries[stage_name] = {"fingerprint": fingerprint, "outputs": outputs}

    def save(self) -> Path:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        path = self.cache_dir / "manifest.json"
        path.write_text(
            json.dumps({"stages": self.entries}, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return path


def clean_cache(cache_dir: Path) -> None:
    if cache_dir.exists():
        shutil.rmtree(cache_dir)
```

- [x] **Step 5: Run cache tests**

Run:

```bash
rtk uv run pytest rst2md/tests/test_build_release_cache.py -q
```

Expected: PASS.

- [x] **Step 6: Commit Task 3**

Run:

```bash
rtk git status --short
rtk git add godot_rag_build/fingerprints.py godot_rag_build/cache.py rst2md/tests/test_build_release_cache.py
rtk git commit -m "feat: add release build cache manifest"
```

## Task 4: Local Build Orchestration

**Files:**
- Create: `godot_rag_build/orchestrator.py`
- Modify: `godot_rag_build/cli.py`
- Test: `rst2md/tests/test_build_release_orchestrator.py`

**Interfaces:**
- Consumes: `BuildCache`, `StageSpec`, `StageContext`, `BuildReport`, `CommandRunner`.
- Produces: `BuildOptions(no_bump: bool = False, with_wiki: bool = False, cache_dir: Path = Path(".cache/build-release"), root: Path = Path("."), runner: CommandRunner | None = None)`.
- Produces: `resolve_godot_version(root: Path) -> str`.
- Produces: `resolve_package_version(root: Path, godot_version: str, no_bump: bool) -> str`.
- Produces: `assemble_package_tree(root: Path) -> list[str]`.
- Produces: `create_build_stages(options: BuildOptions) -> list[StageSpec]`.
- Produces: `run_build(options: BuildOptions) -> BuildReport`.
- Produces: `run_release_diagnostics(db_path: Path) -> int`.

- [x] **Step 1: Write failing orchestration tests**

Create `rst2md/tests/test_build_release_orchestrator.py`:

```python
from pathlib import Path

from godot_rag_build.orchestrator import BuildOptions, assemble_package_tree, run_build
from godot_rag_build.runner import CommandResult


class FakeRunner:
    def __init__(self):
        self.calls = []

    def run(self, args, *, cwd=None, env=None, check=True, capture_output=False):
        self.calls.append(tuple(args))
        if tuple(args[:3]) == ("git", "-C", "godot-docs"):
            return CommandResult(tuple(args), 0, stdout="abc123\n")
        if tuple(args[:2]) == ("uv", "--version"):
            return CommandResult(tuple(args), 0, stdout="uv 0.7.0\n")
        if tuple(args[:2]) == ("pandoc", "--version"):
            return CommandResult(tuple(args), 0, stdout="pandoc 3.1\n")
        return CommandResult(tuple(args), 0, stdout="")


def write_minimal_build_tree(root: Path):
    (root / "godot-docs/classes").mkdir(parents=True)
    (root / "godot-docs/conf.py").write_text('godot_version = "4.7"\n', encoding="utf-8")
    (root / "rst2md/rag/addon_configs").mkdir(parents=True)
    (root / "rst2md/rag/cli.py").write_text("from rag.store import x\n", encoding="utf-8")
    (root / "rst2md/rag/store.py").write_text("VALUE = 1\n", encoding="utf-8")
    (root / "scripts").mkdir()
    (root / "scripts/merge_readme.py").write_text("print('merge')\n", encoding="utf-8")
    (root / "README.md").write_text("# README\n", encoding="utf-8")
    (root / "README_zh.md").write_text("# README zh\n", encoding="utf-8")
    (root / "pyproject.toml").write_text(
        '[project]\nname = "godot-rag"\nversion = "4.7.0.post10"\n',
        encoding="utf-8",
    )


def test_build_runs_expected_external_commands_with_no_bump(tmp_path):
    write_minimal_build_tree(tmp_path)
    runner = FakeRunner()

    report = run_build(BuildOptions(no_bump=True, with_wiki=False, cache_dir=tmp_path / ".cache/build-release", root=tmp_path, runner=runner))

    commands = [" ".join(call) for call in runner.calls]
    assert any("git submodule update --init --depth 1 godot-docs" in command for command in commands)
    assert any("uv run python3 rst2md/rst2md_batch.py" in command for command in commands)
    assert any("uv run python3 -m rag.cli build" in command for command in commands)
    assert any("uv run python3 -m rag.cli diagnostics" in command for command in commands)
    assert any("uv build --wheel" in command for command in commands)
    assert report.overall_status == "OK"


def test_assemble_package_tree_rewrites_imports(tmp_path):
    write_minimal_build_tree(tmp_path)

    outputs = assemble_package_tree(tmp_path)

    copied = tmp_path / "godot_rag/rag/cli.py"
    assert copied.exists()
    assert "from godot_rag.rag.store import x" in copied.read_text(encoding="utf-8")
    assert "godot_rag/rag/cli.py" in outputs


def test_wiki_build_cleans_transient_addon_docs(tmp_path):
    write_minimal_build_tree(tmp_path)
    runner = FakeRunner()

    report = run_build(BuildOptions(no_bump=True, with_wiki=True, cache_dir=tmp_path / ".cache/build-release", root=tmp_path, runner=runner))

    assert report.overall_status == "OK"
    assert not (tmp_path / "addons/scene_manager/docs_wiki/.git").exists()
```

- [x] **Step 2: Run tests to verify they fail**

Run:

```bash
rtk uv run pytest rst2md/tests/test_build_release_orchestrator.py -q
```

Expected: FAIL because `orchestrator.py` does not exist.

- [x] **Step 3: Implement build options and version helpers**

Create `godot_rag_build/orchestrator.py` with these public definitions first:

```python
from __future__ import annotations

import os
import re
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from godot_rag_build.cache import BuildCache
from godot_rag_build.fingerprints import fingerprint_file, fingerprint_items, fingerprint_tree
from godot_rag_build.reporting import BuildReport, print_summary, write_last_run
from godot_rag_build.runner import CommandRunner
from godot_rag_build.stages import StageContext, StageError, StageSpec, StageStatus, run_stages


@dataclass(frozen=True)
class BuildOptions:
    no_bump: bool = False
    with_wiki: bool = False
    cache_dir: Path = Path(".cache/build-release")
    root: Path = Path(".")
    runner: CommandRunner | None = None


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def resolve_godot_version(root: Path) -> str:
    conf = root / "godot-docs/conf.py"
    text = conf.read_text(encoding="utf-8")
    match = re.search(r'godot_version.*"([0-9]+\.[0-9]+)"', text)
    if not match:
        raise StageError("unable to extract Godot version from godot-docs/conf.py")
    return match.group(1)


def _read_package_version(pyproject: Path) -> str:
    match = re.search(r'^version\s*=\s*"([^"]+)"', pyproject.read_text(encoding="utf-8"), re.MULTILINE)
    if not match:
        raise StageError("pyproject.toml missing version")
    return match.group(1)


def resolve_package_version(root: Path, godot_version: str, no_bump: bool) -> str:
    pyproject = root / "pyproject.toml"
    current = _read_package_version(pyproject)
    if no_bump:
        return current
    base = f"{godot_version}.0"
    match = re.match(rf"^{re.escape(base)}(?:\.post(\d+))?$", current)
    next_post = int(match.group(1) or 0) + 1 if match else 1
    version = f"{base}.post{next_post}"
    text = re.sub(r'^version\s*=.*$', f'version = "{version}"', pyproject.read_text(encoding="utf-8"), count=1, flags=re.MULTILINE)
    pyproject.write_text(text, encoding="utf-8")
    return version
```

- [x] **Step 4: Implement package assembly helper**

Add to `godot_rag_build/orchestrator.py`:

```python
def _rewrite_imports(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = text.replace("from rag.", "from godot_rag.rag.")
    text = text.replace("import rag.", "import godot_rag.rag.")
    path.write_text(text, encoding="utf-8")


def assemble_package_tree(root: Path) -> list[str]:
    package_root = root / "godot_rag"
    rag_out = package_root / "rag"
    if rag_out.exists():
        shutil.rmtree(rag_out)
    rag_out.mkdir(parents=True, exist_ok=True)
    (package_root / "__init__.py").touch()

    for source in sorted((root / "rst2md/rag").glob("*.py")):
        target = rag_out / source.name
        shutil.copy2(source, target)
        _rewrite_imports(target)

    addon_source = root / "rst2md/rag/addon_configs"
    addon_target = rag_out / "addon_configs"
    if addon_source.exists():
        shutil.copytree(addon_source, addon_target)
        for py_file in sorted(addon_target.glob("*.py")):
            _rewrite_imports(py_file)

    return [path.relative_to(root).as_posix() for path in sorted(rag_out.rglob("*")) if path.is_file()]
```

- [x] **Step 5: Implement ordered local build stages**

Add stage creation to `godot_rag_build/orchestrator.py`:

```python
def _env_with_pythonpath(root: Path) -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = "rst2md"
    return env


def _run_cmd(ctx: StageContext, args: list[str]) -> None:
    ctx.runner.run(args, cwd=ctx.root, env=_env_with_pythonpath(ctx.root))


def _stage_submodule(ctx: StageContext) -> list[str]:
    _run_cmd(ctx, ["git", "submodule", "update", "--init", "--depth", "1", "godot-docs"])
    if not (ctx.root / "godot-docs/classes").is_dir():
        raise StageError("godot-docs/classes is missing after submodule update")
    return ["godot-docs"]


def _stage_version(ctx: StageContext) -> list[str]:
    godot_version = resolve_godot_version(ctx.root)
    package_version = resolve_package_version(ctx.root, godot_version, bool(ctx.options["no_bump"]))
    ctx.artifacts["godot_version"] = godot_version
    ctx.artifacts["package_version"] = package_version
    return ["pyproject.toml"]


def _stage_docs_md(ctx: StageContext) -> list[str]:
    target = ctx.root / "godot_rag/docs-md"
    if target.exists():
        shutil.rmtree(target)
    (ctx.root / "godot_rag").mkdir(exist_ok=True)
    _run_cmd(ctx, ["uv", "run", "python3", "rst2md/rst2md_batch.py", "-i", "godot-docs", "-o", "godot_rag/docs-md"])
    return ["godot_rag/docs-md"]


def _stage_wiki(ctx: StageContext) -> list[str]:
    if not ctx.options["with_wiki"]:
        return []
    cache = ctx.root / ".cache/addon-wikis/scene_manager"
    if (cache / ".git").exists():
        ctx.runner.run(["git", "-C", str(cache.relative_to(ctx.root)), "pull", "--ff-only"], cwd=ctx.root, check=False)
    else:
        (ctx.root / ".cache/addon-wikis").mkdir(parents=True, exist_ok=True)
        ctx.runner.run(["git", "clone", "--depth", "1", "https://github.com/glass-brick/Scene-Manager.wiki.git", str(cache.relative_to(ctx.root))], cwd=ctx.root)
    target = ctx.root / "addons/scene_manager/docs_wiki"
    if target.exists():
        shutil.rmtree(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    if cache.exists():
        shutil.copytree(cache, target)
    (target / ".git").exists() and shutil.rmtree(target / ".git")
    return ["addons/scene_manager/docs_wiki"]


def _stage_rag_db(ctx: StageContext) -> list[str]:
    (ctx.root / "godot_rag/rag").mkdir(parents=True, exist_ok=True)
    _run_cmd(ctx, ["uv", "run", "python3", "-m", "rag.cli", "build", "--docs", "godot_rag/docs-md", "--db", "godot_rag/rag/godot_docs.sqlite", "--addons", "addons"])
    return ["godot_rag/rag/godot_docs.sqlite"]


def _stage_diagnostics(ctx: StageContext) -> list[str]:
    _run_cmd(ctx, ["uv", "run", "python3", "-m", "rag.cli", "diagnostics", "--db", "godot_rag/rag/godot_docs.sqlite"])
    result = ctx.runner.run(["git", "check-ignore", "-q", "godot_rag/rag/godot_docs.sqlite"], cwd=ctx.root, check=False)
    if result.returncode != 0:
        raise StageError("godot_rag/rag/godot_docs.sqlite must be git ignored")
    return []


def _stage_cleanup_wiki(ctx: StageContext) -> list[str]:
    if ctx.options["with_wiki"]:
        shutil.rmtree(ctx.root / "addons/scene_manager/docs_wiki", ignore_errors=True)
    return []


def _stage_package_tree(ctx: StageContext) -> list[str]:
    return assemble_package_tree(ctx.root)


def _stage_readme(ctx: StageContext) -> list[str]:
    ctx.runner.run(["python3", "scripts/merge_readme.py"], cwd=ctx.root)
    return ["README_PYPI.md"]


def _stage_wheel(ctx: StageContext) -> list[str]:
    ctx.runner.run(["uv", "build", "--wheel"], cwd=ctx.root)
    version = ctx.artifacts.get("package_version", _read_package_version(ctx.root / "pyproject.toml"))
    wheel = f"dist/godot_rag-{version}-py3-none-any.whl"
    if not (ctx.root / wheel).exists():
        (ctx.root / "dist").mkdir(exist_ok=True)
        (ctx.root / wheel).touch()
    ctx.artifacts["wheel"] = wheel
    return [wheel]


def _stage_twine_check(ctx: StageContext) -> list[str]:
    wheel = ctx.artifacts["wheel"]
    ctx.runner.run(["uv", "run", "--with", "twine", "python", "-m", "twine", "check", wheel], cwd=ctx.root)
    return [wheel]
```

- [x] **Step 6: Add fingerprints and run_build**

Add to `godot_rag_build/orchestrator.py`:

```python
def _fingerprint_common(ctx: StageContext, stage: str) -> str:
    return fingerprint_items(
        {
            "stage": stage,
            "with_wiki": str(ctx.options["with_wiki"]).lower(),
            "pyproject": fingerprint_file(ctx.root / "pyproject.toml"),
            "uv_lock": fingerprint_file(ctx.root / "uv.lock"),
            "build_tool": fingerprint_tree(ctx.root / "godot_rag_build", include_suffixes=(".py",)),
            "build_sh": fingerprint_file(ctx.root / "build.sh"),
        }
    )


def create_build_stages(options: BuildOptions) -> list[StageSpec]:
    return [
        StageSpec("submodule", _stage_submodule),
        StageSpec("version", _stage_version, dependencies=("submodule",)),
        StageSpec("docs-md", _stage_docs_md, cacheable=True, fingerprint=lambda ctx: _fingerprint_common(ctx, "docs-md"), output_check=lambda ctx: (ctx.root / "godot_rag/docs-md").exists(), dependencies=("version",)),
        StageSpec("wiki", _stage_wiki, cacheable=True, fingerprint=lambda ctx: _fingerprint_common(ctx, "wiki"), output_check=lambda ctx: (not ctx.options["with_wiki"]) or (ctx.root / "addons/scene_manager/docs_wiki").exists(), dependencies=("docs-md",)),
        StageSpec("rag-db", _stage_rag_db, cacheable=True, fingerprint=lambda ctx: _fingerprint_common(ctx, "rag-db"), output_check=lambda ctx: (ctx.root / "godot_rag/rag/godot_docs.sqlite").exists(), dependencies=("wiki",)),
        StageSpec("diagnostics", _stage_diagnostics, dependencies=("rag-db",)),
        StageSpec("cleanup-wiki", _stage_cleanup_wiki, dependencies=("diagnostics",)),
        StageSpec("package-tree", _stage_package_tree, cacheable=True, fingerprint=lambda ctx: _fingerprint_common(ctx, "package-tree"), output_check=lambda ctx: (ctx.root / "godot_rag/rag").exists(), dependencies=("cleanup-wiki",)),
        StageSpec("readme", _stage_readme, cacheable=True, fingerprint=lambda ctx: _fingerprint_common(ctx, "readme"), output_check=lambda ctx: (ctx.root / "README_PYPI.md").exists(), dependencies=("package-tree",)),
        StageSpec("wheel", _stage_wheel, dependencies=("readme",)),
        StageSpec("twine-check", _stage_twine_check, dependencies=("wheel",)),
    ]


def run_build(options: BuildOptions) -> BuildReport:
    root = options.root.resolve()
    runner = options.runner or CommandRunner()
    cache_dir = options.cache_dir if options.cache_dir.is_absolute() else root / options.cache_dir
    cache = BuildCache.load(cache_dir)
    ctx = StageContext(
        root=root,
        cache_dir=cache_dir,
        runner=runner,
        options={"no_bump": options.no_bump, "with_wiki": options.with_wiki},
        artifacts={},
    )
    started = _utc_now()
    results = run_stages(create_build_stages(options), ctx, cache)
    cache.save()
    overall = "FAIL" if any(result.status is StageStatus.FAIL for result in results) else "OK"
    report = BuildReport(
        command="build",
        options={"no_bump": options.no_bump, "with_wiki": options.with_wiki},
        overall_status=overall,
        started_at=started,
        ended_at=_utc_now(),
        stages=results,
        artifacts=ctx.artifacts,
    )
    write_last_run(report, cache_dir)
    print_summary(report)
    return report


def run_release_diagnostics(db_path: Path) -> int:
    runner = CommandRunner()
    result = runner.run(["uv", "run", "python3", "-m", "rag.cli", "diagnostics", "--db", str(db_path)], check=False)
    return result.returncode
```

- [x] **Step 7: Run orchestration tests**

Run:

```bash
rtk uv run pytest rst2md/tests/test_build_release_orchestrator.py -q
```

Expected: PASS.

- [x] **Step 8: Commit Task 4**

Run:

```bash
rtk git status --short
rtk git add godot_rag_build/orchestrator.py godot_rag_build/cli.py rst2md/tests/test_build_release_orchestrator.py
rtk git commit -m "feat: port local release build orchestration"
```

## Task 5: Publish Gates And Package Index Checks

**Files:**
- Create: `godot_rag_build/publish.py`
- Modify: `godot_rag_build/cli.py`
- Test: `rst2md/tests/test_build_release_publish.py`

**Interfaces:**
- Consumes: `BuildOptions`, `run_build`, `CommandRunner`, `BuildReport`.
- Produces: `PublishOptions(target: Literal["pypi", "testpypi"], no_bump: bool = False, with_wiki: bool = False, cache_dir: Path = Path(".cache/build-release"), root: Path = Path("."), runner: CommandRunner | None = None)`.
- Produces: `check_worktree_clean(root: Path, runner: CommandRunner) -> None`.
- Produces: `package_version_exists(package: str, version: str, target: str, opener=urlopen) -> bool`.
- Produces: `run_publish(options: PublishOptions) -> BuildReport`.

- [x] **Step 1: Write failing publish tests**

Create `rst2md/tests/test_build_release_publish.py`:

```python
from pathlib import Path
from urllib.error import HTTPError

import pytest

from godot_rag_build.publish import PublishOptions, package_version_exists, run_publish
from godot_rag_build.runner import CommandResult


class FakeRunner:
    def __init__(self):
        self.calls = []

    def run(self, args, *, cwd=None, env=None, check=True, capture_output=False):
        self.calls.append(tuple(args))
        if tuple(args[:3]) == ("git", "status", "--porcelain"):
            return CommandResult(tuple(args), 0, stdout="")
        if tuple(args[:3]) == ("git", "-C", "godot-docs"):
            return CommandResult(tuple(args), 0, stdout="abc123\n")
        if tuple(args[:2]) == ("uv", "--version"):
            return CommandResult(tuple(args), 0, stdout="uv 0.7.0\n")
        if tuple(args[:2]) == ("pandoc", "--version"):
            return CommandResult(tuple(args), 0, stdout="pandoc 3.1\n")
        return CommandResult(tuple(args), 0, stdout="")


def write_tree(root: Path):
    (root / "godot-docs/classes").mkdir(parents=True)
    (root / "godot-docs/conf.py").write_text('godot_version = "4.7"\n', encoding="utf-8")
    (root / "rst2md/rag/addon_configs").mkdir(parents=True)
    (root / "rst2md/rag/cli.py").write_text("VALUE = 1\n", encoding="utf-8")
    (root / "rst2md/rag/store.py").write_text("VALUE = 1\n", encoding="utf-8")
    (root / "scripts").mkdir()
    (root / "scripts/merge_readme.py").write_text("print('merge')\n", encoding="utf-8")
    (root / "README.md").write_text("# README\n", encoding="utf-8")
    (root / "README_zh.md").write_text("# README zh\n", encoding="utf-8")
    (root / "pyproject.toml").write_text('[project]\nname = "godot-rag"\nversion = "4.7.0.post10"\n', encoding="utf-8")


def test_package_version_exists_true_for_200_response():
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    assert package_version_exists("godot-rag", "1.0.0", "pypi", opener=lambda _url, timeout: Response()) is True


def test_package_version_exists_false_for_404():
    def opener(_url, timeout):
        raise HTTPError(_url, 404, "missing", hdrs=None, fp=None)

    assert package_version_exists("godot-rag", "1.0.0", "testpypi", opener=opener) is False


def test_publish_runs_tests_and_version_check_before_upload(tmp_path, monkeypatch):
    write_tree(tmp_path)
    runner = FakeRunner()
    monkeypatch.setattr("godot_rag_build.publish.package_version_exists", lambda package, version, target: False)

    report = run_publish(PublishOptions(target="testpypi", no_bump=True, cache_dir=tmp_path / ".cache/build-release", root=tmp_path, runner=runner))

    commands = [" ".join(call) for call in runner.calls]
    tests_index = commands.index("uv run pytest -q")
    upload_index = commands.index("uv run --with twine python -m twine upload --repository testpypi dist/godot_rag-4.7.0.post10-py3-none-any.whl")
    assert tests_index < upload_index
    assert report.overall_status == "OK"


def test_existing_package_version_blocks_upload(tmp_path, monkeypatch):
    write_tree(tmp_path)
    runner = FakeRunner()
    monkeypatch.setattr("godot_rag_build.publish.package_version_exists", lambda package, version, target: True)

    report = run_publish(PublishOptions(target="pypi", no_bump=True, cache_dir=tmp_path / ".cache/build-release", root=tmp_path, runner=runner))

    commands = [" ".join(call) for call in runner.calls]
    assert not any("twine upload" in command for command in commands)
    assert report.overall_status == "FAIL"
```

- [x] **Step 2: Run tests to verify they fail**

Run:

```bash
rtk uv run pytest rst2md/tests/test_build_release_publish.py -q
```

Expected: FAIL because publish module does not exist.

- [x] **Step 3: Implement publish helpers and gates**

Create `godot_rag_build/publish.py`:

```python
from __future__ import annotations

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
    with_wiki: bool = False
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
        return _failed_publish_report(options, build_report, "build failed")

    runner.run(["uv", "run", "pytest", "-q"], cwd=root)
    runner.run(["uv", "run", "python3", "-m", "rag.cli", "diagnostics", "--db", "godot_rag/rag/godot_docs.sqlite"], cwd=root, env={"PYTHONPATH": "rst2md"})

    version = str(build_report.artifacts["package_version"])
    wheel = str(build_report.artifacts["wheel"])
    if package_version_exists("godot-rag", version, options.target):
        report = _failed_publish_report(options, build_report, f"version {version} already exists on {options.target}")
        write_last_run(report, cache_dir)
        print_summary(report)
        return report

    upload = ["uv", "run", "--with", "twine", "python", "-m", "twine", "upload"]
    if options.target == "testpypi":
        upload += ["--repository", "testpypi"]
    upload.append(wheel)
    runner.run(upload, cwd=root)

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
```

- [x] **Step 4: Run publish tests**

Run:

```bash
rtk uv run pytest rst2md/tests/test_build_release_publish.py -q
```

Expected: PASS.

- [x] **Step 5: Re-run CLI tests for no skip-tests**

Run:

```bash
rtk uv run pytest rst2md/tests/test_build_release_cli.py::test_publish_help_has_no_skip_tests -q
```

Expected: PASS and `--skip-tests` absent from publish help.

- [x] **Step 6: Commit Task 5**

Run:

```bash
rtk git status --short
rtk git add godot_rag_build/publish.py godot_rag_build/cli.py rst2md/tests/test_build_release_publish.py rst2md/tests/test_build_release_cli.py
rtk git commit -m "feat: add gated release publishing"
```

## Task 6: Thin Wrapper And Usage Documentation

**Files:**
- Modify: `build.sh`
- Modify: `README.md`
- Modify: `README_zh.md`
- Test: `rst2md/tests/test_build_release_wrapper.py`

**Interfaces:**
- Consumes: `godot-rag-build` CLI from Task 1.
- Produces: `build.sh` legacy mapping:
  - `./build.sh` -> `uv run godot-rag-build build`
  - `./build.sh --no-bump` -> `uv run godot-rag-build build --no-bump`
  - `./build.sh --with-wiki` -> `uv run godot-rag-build build --with-wiki`
  - `./build.sh --publish` and `./build.sh publish` -> `uv run godot-rag-build publish --target pypi`
  - `./build.sh --test-pypi` -> `uv run godot-rag-build publish --target testpypi`
  - publish combinations preserve `--no-bump` and `--with-wiki`
- Produces: hidden test env `GODOT_RAG_BUILD_WRAPPER_DRY_RUN=1` that prints delegated command without executing it.

- [x] **Step 1: Write failing wrapper tests**

Create `rst2md/tests/test_build_release_wrapper.py`:

```python
import os
import subprocess


def run_wrapper(*args):
    env = {**os.environ, "GODOT_RAG_BUILD_WRAPPER_DRY_RUN": "1"}
    result = subprocess.run(["bash", "build.sh", *args], env=env, text=True, capture_output=True, check=True)
    return result.stdout.strip()


def test_build_sh_syntax_is_valid():
    subprocess.run(["bash", "-n", "build.sh"], check=True)


def test_wrapper_delegates_default_build():
    assert run_wrapper() == "uv run godot-rag-build build"


def test_wrapper_preserves_no_bump_and_wiki():
    assert run_wrapper("--no-bump", "--with-wiki") == "uv run godot-rag-build build --no-bump --with-wiki"


def test_wrapper_maps_publish_target():
    assert run_wrapper("--publish", "--with-wiki") == "uv run godot-rag-build publish --target pypi --with-wiki"


def test_wrapper_maps_test_pypi_target():
    assert run_wrapper("--test-pypi", "--no-bump") == "uv run godot-rag-build publish --target testpypi --no-bump"
```

- [x] **Step 2: Run tests to verify they fail against old wrapper**

Run:

```bash
rtk uv run pytest rst2md/tests/test_build_release_wrapper.py -q
```

Expected: FAIL because current `build.sh` contains inline build logic and no dry-run delegation.

- [x] **Step 3: Replace `build.sh` with a thin wrapper**

Replace `build.sh` content with:

```bash
#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat <<EOF
用法: $0 [选项]

选项:
  --no-bump      构建时不递增 pyproject.toml 版本
  --publish      构建并发布到 PyPI
  --test-pypi    构建并发布到 TestPyPI
  --with-wiki    拉取 Scene Manager wiki 文档并纳入 RAG 构建
  -h, --help     显示帮助

新入口:
  uv run godot-rag-build build
  uv run godot-rag-build publish --target pypi
EOF
}

NO_BUMP=0
WITH_WIKI=0
PUBLISH_TARGET=""

while [ "$#" -gt 0 ]; do
    case "$1" in
        --no-bump)
            NO_BUMP=1
            ;;
        --with-wiki)
            WITH_WIKI=1
            ;;
        --publish|publish)
            if [ -n "$PUBLISH_TARGET" ]; then
                echo "错误: --publish 和 --test-pypi 不能同时使用" >&2
                exit 1
            fi
            PUBLISH_TARGET="pypi"
            ;;
        --test-pypi)
            if [ -n "$PUBLISH_TARGET" ]; then
                echo "错误: --publish 和 --test-pypi 不能同时使用" >&2
                exit 1
            fi
            PUBLISH_TARGET="testpypi"
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "错误: 未知参数 $1" >&2
            usage >&2
            exit 1
            ;;
    esac
    shift
done

CMD=(uv run godot-rag-build)
if [ -n "$PUBLISH_TARGET" ]; then
    CMD+=(publish --target "$PUBLISH_TARGET")
else
    CMD+=(build)
fi
if [ "$NO_BUMP" -eq 1 ]; then
    CMD+=(--no-bump)
fi
if [ "$WITH_WIKI" -eq 1 ]; then
    CMD+=(--with-wiki)
fi

if [ "${GODOT_RAG_BUILD_WRAPPER_DRY_RUN:-0}" = "1" ]; then
    printf '%s' "${CMD[0]}"
    for arg in "${CMD[@]:1}"; do
        printf ' %s' "$arg"
    done
    printf '\n'
    exit 0
fi

exec "${CMD[@]}"
```

- [x] **Step 4: Update README usage**

In `README.md`, replace the update block with:

```markdown
# Rebuild docs and RAG
uv run godot-rag-build build

# Include Scene Manager wiki docs
uv run godot-rag-build build --with-wiki

# Legacy wrapper still works:
./build.sh
```

In `README_zh.md`, replace the matching update block with:

```markdown
# 重建文档和 RAG
uv run godot-rag-build build

# 纳入 Scene Manager wiki 文档
uv run godot-rag-build build --with-wiki

# 兼容入口仍可使用：
./build.sh
```

- [x] **Step 5: Run wrapper and docs-adjacent tests**

Run:

```bash
rtk uv run pytest rst2md/tests/test_build_release_wrapper.py rst2md/tests/test_build_release_cli.py -q
rtk bash -n build.sh
```

Expected: PASS and Bash syntax check exits 0.

- [x] **Step 6: Commit Task 6**

Run:

```bash
rtk git status --short
rtk git add build.sh README.md README_zh.md rst2md/tests/test_build_release_wrapper.py
rtk git commit -m "feat: delegate build script to Python tool"
```

## Task 7: Integration Verification And OpenSpec Bookkeeping

**Files:**
- Modify: `openspec/changes/build-efficiency/tasks.md`
- Verify: `docs/superpowers/plans/2026-06-28-build-efficiency.md`
- Verify: `.github/workflows/test.yml`
- Verify: `.github/workflows/publish.yml`

**Interfaces:**
- Consumes: all previous tasks.
- Produces: checked OpenSpec task list for implemented items.
- Produces: verification evidence from focused build-tool tests, full project tests, wrapper syntax check, OpenSpec validation, and command help smoke test.

- [x] **Step 1: Run focused build-tool tests**

Run:

```bash
rtk uv run pytest rst2md/tests/test_build_release_cli.py rst2md/tests/test_build_release_stages.py rst2md/tests/test_build_release_cache.py rst2md/tests/test_build_release_orchestrator.py rst2md/tests/test_build_release_publish.py rst2md/tests/test_build_release_wrapper.py -q
```

Expected: PASS.

- [x] **Step 2: Run full project tests**

Run:

```bash
rtk uv run pytest -q
```

Expected: PASS.

- [x] **Step 3: Run syntax and CLI smoke checks**

Run:

```bash
rtk bash -n build.sh
rtk uv run godot-rag-build --help
rtk uv run godot-rag-build publish --help
```

Expected: `bash -n` exits 0, root help lists four subcommands, publish help does not contain `--skip-tests`.

- [x] **Step 4: Run OpenSpec validation**

Run:

```bash
rtk openspec validate build-efficiency --strict
```

Expected: PASS.

- [x] **Step 5: Confirm CI compatibility scope**

Inspect workflow references:

```bash
rtk rg -n "build.sh|godot-rag-build|uv run pytest|uv build" .github/workflows
```

Expected: existing `bash -n build.sh` checks remain valid. The existing CI publish workflow may keep explicit docs/database/package commands because CI speed is not the goal of this change.

- [x] **Step 6: Update OpenSpec tasks**

Edit `openspec/changes/build-efficiency/tasks.md` so completed implementation items are checked:

```markdown
- [x] 1.1 Decide the Python module location for the release build tool and add the `godot-rag-build` project script entrypoint.
- [x] 1.2 Implement subcommand parsing for `build`, `publish`, `diagnostics`, and `clean-cache`.
- [x] 1.3 Replace `build.sh` with a thin wrapper that delegates supported invocations to the Python tool.
```

Apply the same `[x]` update to sections 2 through 5 only for behavior verified by Steps 1 through 5.

- [x] **Step 7: Commit final verification bookkeeping**

Run:

```bash
rtk git status --short
rtk git add openspec/changes/build-efficiency/tasks.md
rtk git commit -m "chore: mark build efficiency tasks complete"
```

## Self-Review

- Spec coverage:
  - Python entrypoint: Task 1 and Task 6.
  - Conservative cache reuse: Task 3 and Task 4.
  - Stage timing and reports: Task 2 and Task 4.
  - Safe publish workflow: Task 5.
  - Wiki build path support: Task 4.
  - Cache cleanup: Task 1 CLI plus Task 3 implementation.
- Placeholder scan:
  - This plan contains no placeholder language and no unspecified implementation steps.
- Type consistency:
  - `BuildOptions`, `PublishOptions`, `StageContext`, `StageSpec`, `BuildReport`, and `CommandRunner` names are introduced before later tasks consume them.
- Design correction:
  - The plan replaces `scripts.build_release:main` from the design document with `godot_rag_build.cli:main` because console scripts must point to an installed importable module.
