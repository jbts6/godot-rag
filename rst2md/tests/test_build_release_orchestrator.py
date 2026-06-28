from pathlib import Path

from godot_rag_build.orchestrator import BuildOptions, assemble_package_tree, create_build_stages, run_build
from godot_rag_build.runner import CommandResult
from godot_rag_build.stages import StageContext


class FakeRunner:
    def __init__(self):
        self.calls = []

    def run(self, args, *, cwd=None, env=None, check=True, capture_output=False):
        self.calls.append(tuple(args))
        if tuple(args) == ("uv", "build", "--wheel") and cwd is not None:
            dist = Path(cwd) / "dist"
            dist.mkdir(exist_ok=True)
            (dist / "godot_rag-4.7.0.post10-py3-none-any.whl").write_text("wheel", encoding="utf-8")
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
    (root / "addons/example/docs").mkdir(parents=True)
    (root / "addons/example/docs/index.md").write_text("# Addon\n", encoding="utf-8")
    (root / ".cache/addon-wikis/scene_manager").mkdir(parents=True)
    (root / ".cache/addon-wikis/scene_manager/Home.md").write_text("# Wiki\n", encoding="utf-8")
    (root / "build.sh").write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    (root / "uv.lock").write_text("", encoding="utf-8")
    (root / "pyproject.toml").write_text(
        '[project]\nname = "godot-rag"\nversion = "4.7.0.post10"\n',
        encoding="utf-8",
    )


def stage_fingerprint(root: Path, stage_name: str, *, with_wiki: bool = False, runner=None) -> str:
    runner = runner or FakeRunner()
    options = BuildOptions(no_bump=True, with_wiki=with_wiki, cache_dir=root / ".cache/build-release", root=root, runner=runner)
    ctx = StageContext(root, root / ".cache/build-release", runner, {"no_bump": True, "with_wiki": with_wiki}, {})
    spec = next(stage for stage in create_build_stages(options) if stage.name == stage_name)
    assert spec.fingerprint is not None
    return spec.fingerprint(ctx)


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


def test_stage_fingerprints_include_relevant_build_inputs(tmp_path):
    write_minimal_build_tree(tmp_path)

    rag_before = stage_fingerprint(tmp_path, "rag-db")
    (tmp_path / "rst2md/rag/store.py").write_text("VALUE = 2\n", encoding="utf-8")
    assert stage_fingerprint(tmp_path, "rag-db") != rag_before

    readme_before = stage_fingerprint(tmp_path, "readme")
    (tmp_path / "README.md").write_text("# Changed\n", encoding="utf-8")
    assert stage_fingerprint(tmp_path, "readme") != readme_before

    addon_before = stage_fingerprint(tmp_path, "rag-db")
    (tmp_path / "addons/example/docs/index.md").write_text("# Changed addon\n", encoding="utf-8")
    assert stage_fingerprint(tmp_path, "rag-db") != addon_before

    wiki_before = stage_fingerprint(tmp_path, "wiki", with_wiki=True)
    (tmp_path / ".cache/addon-wikis/scene_manager/Home.md").write_text("# Changed wiki\n", encoding="utf-8")
    assert stage_fingerprint(tmp_path, "wiki", with_wiki=True) != wiki_before


def test_stage_fingerprints_include_tool_versions(tmp_path):
    write_minimal_build_tree(tmp_path)

    class NewerToolsRunner(FakeRunner):
        def run(self, args, *, cwd=None, env=None, check=True, capture_output=False):
            if tuple(args[:2]) == ("uv", "--version"):
                return CommandResult(tuple(args), 0, stdout="uv 0.8.0\n")
            return super().run(args, cwd=cwd, env=env, check=check, capture_output=capture_output)

    assert stage_fingerprint(tmp_path, "docs-md", runner=FakeRunner()) != stage_fingerprint(tmp_path, "docs-md", runner=NewerToolsRunner())


def test_wheel_stage_fails_when_expected_artifact_is_missing(tmp_path):
    write_minimal_build_tree(tmp_path)

    class MissingWheelRunner(FakeRunner):
        def run(self, args, *, cwd=None, env=None, check=True, capture_output=False):
            if tuple(args) == ("uv", "build", "--wheel"):
                self.calls.append(tuple(args))
                return CommandResult(tuple(args), 0)
            return super().run(args, cwd=cwd, env=env, check=check, capture_output=capture_output)

    report = run_build(BuildOptions(no_bump=True, with_wiki=False, cache_dir=tmp_path / ".cache/build-release", root=tmp_path, runner=MissingWheelRunner()))

    wheel_stage = next(stage for stage in report.stages if stage.name == "wheel")

    assert report.overall_status == "FAIL"
    assert wheel_stage.status.value == "FAIL"
    assert "expected wheel not found" in wheel_stage.reason
    assert not (tmp_path / "dist/godot_rag-4.7.0.post10-py3-none-any.whl").exists()
