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
