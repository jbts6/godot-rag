from pathlib import Path

from godot_rag_build.cache import BuildCache, clean_cache
from godot_rag_build.fingerprints import fingerprint_file, fingerprint_items, fingerprint_tree
from godot_rag_build.runner import CommandRunner
from godot_rag_build.stages import StageContext


def test_file_fingerprint_changes_with_content(tmp_path):
    path = tmp_path / "input.txt"
    path.write_text("one", encoding="utf-8")
    first = fingerprint_file(path)

    path.write_text("two", encoding="utf-8")
    second = fingerprint_file(path)

    assert first != second


def test_tree_fingerprint_uses_stable_order(tmp_path):
    root = tmp_path / "tree"
    root.mkdir()
    (root / "b.py").write_text("b", encoding="utf-8")
    (root / "a.py").write_text("a", encoding="utf-8")

    first = fingerprint_tree(root, include_suffixes=(".py",))
    second = fingerprint_tree(root, include_suffixes=(".py",))

    assert first == second


def test_options_change_fingerprint():
    no_wiki = fingerprint_items({"with_wiki": "false", "godot_docs_head": "abc"})
    with_wiki = fingerprint_items({"with_wiki": "true", "godot_docs_head": "abc"})

    assert no_wiki != with_wiki


def test_cache_skips_only_when_fingerprint_and_outputs_match(tmp_path):
    cache_dir = tmp_path / ".cache/build-release"
    output = tmp_path / "dist/pkg.whl"
    output.parent.mkdir()
    output.write_text("wheel", encoding="utf-8")

    cache = BuildCache.load(cache_dir)
    cache.record_success("wheel", "abc", [str(output)])
    cache.save()
    loaded = BuildCache.load(cache_dir)
    ctx = StageContext(tmp_path, cache_dir, CommandRunner(), {}, {})

    decision = loaded.should_skip("wheel", "abc", ctx, lambda _ctx: output.exists())

    assert decision.skip is True
    assert decision.reason == "fingerprint match"
    assert decision.outputs == [str(output)]


def test_cache_miss_when_output_check_fails(tmp_path):
    cache_dir = tmp_path / ".cache/build-release"
    cache = BuildCache.load(cache_dir)
    cache.record_success("rag-db", "abc", [str(tmp_path / "missing.sqlite")])
    cache.save()
    ctx = StageContext(tmp_path, cache_dir, CommandRunner(), {}, {})

    decision = BuildCache.load(cache_dir).should_skip("rag-db", "abc", ctx, lambda _ctx: False)

    assert decision.skip is False
    assert decision.reason == "outputs missing"


def test_clean_cache_removes_cache_dir(tmp_path):
    cache_dir = tmp_path / ".cache/build-release"
    cache_dir.mkdir(parents=True)
    (cache_dir / "manifest.json").write_text("{}", encoding="utf-8")

    clean_cache(cache_dir)

    assert not cache_dir.exists()
