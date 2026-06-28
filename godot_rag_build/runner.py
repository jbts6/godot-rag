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
