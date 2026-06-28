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
