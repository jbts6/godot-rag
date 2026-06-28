# Task 1: Packaged CLI Entrypoint

## Task Description

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

## Steps

### Step 1: Write failing CLI tests

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

### Step 2: Run tests to verify they fail

```bash
rtk uv run pytest rst2md/tests/test_build_release_cli.py -q
```

Expected: FAIL because `godot_rag_build` and the project script do not exist.

### Step 3: Add package marker and runner shell

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

### Step 4: Add CLI parser skeleton

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

### Step 5: Wire project script and package inclusion

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

### Step 6: Run CLI tests

```bash
rtk uv run pytest rst2md/tests/test_build_release_cli.py -q
```

Expected: PASS for CLI parser and pyproject assertions. Handler imports may remain unexecuted because these tests only parse help and config.

### Step 7: Commit Task 1

```bash
rtk git status --short
rtk git add pyproject.toml godot_rag_build/__init__.py godot_rag_build/cli.py godot_rag_build/runner.py rst2md/tests/test_build_release_cli.py
rtk git commit -m "feat: add release build CLI entrypoint"
```

## Global Constraints

- 本 change 只优化本地 release build；CI 不作为速度优化目标，只保持现有 workflow 可用。
- `godot-rag-build` 必须提供 `build`、`publish`、`diagnostics`、`clean-cache` 四个 subcommands。
- Design Doc 中的 `scripts.build_release:main` 入口在当前 wheel package 配置下不可导入；实现必须改为 `godot_rag_build.cli:main`，并把 `godot_rag_build` 加入 hatch wheel packages。
- `publish` 不得提供 `--skip-tests` 或同义跳过测试参数。
- report 不得记录 token、password、credential 或完整环境变量。
- 每个实现任务完成后运行该任务列出的测试命令并提交；提交前用 `rtk git status --short` 检查生成物没有进入 git 跟踪。
