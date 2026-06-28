# Task 2: Stage Model And Run Reporting

## Task Description

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

## Steps

### Step 1: Write failing stage/report tests

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

### Step 2: Run tests to verify they fail

```bash
rtk uv run pytest rst2md/tests/test_build_release_stages.py -q
```

Expected: FAIL because stage and reporting modules do not exist.

### Step 3: Implement stage primitives

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

### Step 4: Implement report serialization and summary

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

### Step 5: Run stage/report tests

```bash
rtk uv run pytest rst2md/tests/test_build_release_stages.py -q
```

Expected: PASS.

### Step 6: Commit Task 2

```bash
rtk git status --short
rtk git add godot_rag_build/stages.py godot_rag_build/reporting.py rst2md/tests/test_build_release_stages.py
rtk git commit -m "feat: add release build stage reporting"
```

## Global Constraints

- `godot-rag-build` 必须提供 `build`、`publish`、`diagnostics`、`clean-cache` 四个 subcommands。
- 缓存只在 manifest 指纹完全匹配、影响选项匹配、期望输出存在且 output check 通过时使用；任何不确定都必须运行阶段。
- `.cache/build-release/manifest.json` 保存可复用缓存状态；`.cache/build-release/last-run.json` 保存最近一次运行报告。
- report 不得记录 token、password、credential 或完整环境变量。
- 每个实现任务完成后运行该任务列出的测试命令并提交；提交前用 `rtk git status --short` 检查生成物没有进入 git 跟踪。
