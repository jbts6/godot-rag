from pathlib import Path

import pytest

from godot_rag_build.cli import create_parser, main
from godot_rag_build.runner import CommandResult


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


def test_diagnostics_command_uses_rst2md_pythonpath(monkeypatch):
    calls = []

    def fake_run(self, args, *, cwd=None, env=None, check=True, capture_output=False):
        calls.append((tuple(args), env))
        return CommandResult(tuple(args), 0)

    monkeypatch.setattr("godot_rag_build.runner.CommandRunner.run", fake_run)

    assert main(["diagnostics", "--db", "missing.sqlite"]) == 0
    assert calls[0][0] == ("uv", "run", "python3", "-m", "rag.cli", "diagnostics", "--db", "missing.sqlite")
    assert calls[0][1] is not None
    assert calls[0][1]["PYTHONPATH"] == "rst2md"
