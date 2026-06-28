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
    cache: object = None,
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
        except (StageError, RuntimeError, OSError) as exc:
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
