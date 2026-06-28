from pathlib import Path
import json
from urllib.error import HTTPError

import pytest

from godot_rag_build.publish import PublishOptions, package_version_exists, run_publish
from godot_rag_build.runner import CommandResult


class FakeRunner:
    def __init__(self):
        self.calls = []

    def run(self, args, *, cwd=None, env=None, check=True, capture_output=False):
        self.calls.append(tuple(args))
        if tuple(args) == ("uv", "build", "--wheel") and cwd is not None:
            dist = Path(cwd) / "dist"
            dist.mkdir(exist_ok=True)
            (dist / "godot_rag-4.7.0.post10-py3-none-any.whl").write_text("wheel", encoding="utf-8")
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


def test_publish_test_failure_writes_publish_failure_report(tmp_path, monkeypatch):
    write_tree(tmp_path)

    class FailingTestsRunner(FakeRunner):
        def run(self, args, *, cwd=None, env=None, check=True, capture_output=False):
            if tuple(args) == ("uv", "run", "pytest", "-q"):
                raise RuntimeError("tests failed")
            return super().run(args, cwd=cwd, env=env, check=check, capture_output=capture_output)

    monkeypatch.setattr("godot_rag_build.publish.package_version_exists", lambda package, version, target: False)

    cache_dir = tmp_path / ".cache/build-release"
    report = run_publish(PublishOptions(target="testpypi", no_bump=True, cache_dir=cache_dir, root=tmp_path, runner=FailingTestsRunner()))
    last_run = json.loads((cache_dir / "last-run.json").read_text(encoding="utf-8"))

    assert report.overall_status == "FAIL"
    assert report.command == "publish"
    assert report.artifacts["publish_error"] == "tests failed"
    assert last_run["command"] == "publish"
    assert last_run["overall_status"] == "FAIL"
    assert last_run["artifacts"]["publish_error"] == "tests failed"
