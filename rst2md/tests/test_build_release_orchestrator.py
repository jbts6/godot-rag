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
