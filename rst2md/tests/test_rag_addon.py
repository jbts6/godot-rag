"""Tests for addon discovery, chunking, search, and CLI."""

import subprocess
import sys
import tempfile
import os
from pathlib import Path

import pytest

from rag.addon_docs import (
    chunk_api_file,
    chunk_addon,
    chunk_addon_markdown,
    chunk_code_file,
)
from rag.addon_discovery import (
    AddonLayout,
    collect_api_files,
    collect_doc_files,
    collect_example_files,
    discover_addon,
)
from rag.store import build_database, search_database


TEST_ENV = {**os.environ, "PYTHONPATH": "rst2md"}


# --- Addon discovery tests ---

def test_finds_docs_and_examples(tmp_path):
    root = tmp_path / "myaddon"
    root.mkdir()
    (root / "docs").mkdir()
    (root / "examples").mkdir()
    (root / "README.md").write_text("# My Addon\n")

    layout = discover_addon(root)
    assert layout.name == "myaddon"
    assert len(layout.doc_dirs) == 1
    assert layout.doc_dirs[0].name == "docs"
    assert len(layout.example_dirs) == 1
    assert layout.example_dirs[0].name == "examples"
    assert len(layout.doc_files) == 1


def test_finds_documentation_dir(tmp_path):
    root = tmp_path / "gdunit"
    root.mkdir()
    (root / "documentation").mkdir()

    layout = discover_addon(root)
    assert len(layout.doc_dirs) == 1
    assert layout.doc_dirs[0].name == "documentation"


def test_finds_doc_source_dir(tmp_path):
    root = tmp_path / "limboai"
    root.mkdir()
    doc_source = root / "doc" / "source"
    doc_source.mkdir(parents=True)

    layout = discover_addon(root)
    assert len(layout.doc_dirs) == 1
    assert layout.doc_dirs[0] == doc_source


def test_no_docs_dir_just_readme(tmp_path):
    root = tmp_path / "phantom"
    root.mkdir()
    (root / "README.md").write_text("# Phantom Camera\n")

    layout = discover_addon(root)
    assert len(layout.doc_dirs) == 0
    assert len(layout.doc_files) == 1


def test_no_readme_no_docs(tmp_path):
    root = tmp_path / "empty"
    root.mkdir()

    layout = discover_addon(root)
    assert len(layout.doc_dirs) == 0
    assert len(layout.doc_files) == 0
    assert len(layout.example_dirs) == 0


def test_display_name_from_plugin_cfg(tmp_path):
    root = tmp_path / "statecharts"
    root.mkdir()
    addons = root / "addons" / "godot_state_charts"
    addons.mkdir(parents=True)
    (addons / "plugin.cfg").write_text(
        '[plugin]\nname="Godot State Charts"\nauthor="test"\nversion="1.0"\n',
        encoding="utf-8",
    )

    layout = discover_addon(root)
    assert layout.name == "statecharts"
    assert layout.display_name == "Godot State Charts"


def test_display_name_fallback_to_folder(tmp_path):
    root = tmp_path / "myaddon"
    root.mkdir()

    layout = discover_addon(root)
    assert layout.display_name == "myaddon"


def test_display_name_skips_gut(tmp_path):
    root = tmp_path / "statecharts"
    root.mkdir()
    gut = root / "addons" / "gut"
    gut.mkdir(parents=True)
    (gut / "plugin.cfg").write_text(
        '[plugin]\nname="Gut"\nauthor="test"\n',
        encoding="utf-8",
    )
    real = root / "addons" / "godot_state_charts"
    real.mkdir(parents=True)
    (real / "plugin.cfg").write_text(
        '[plugin]\nname="Godot State Charts"\nauthor="test"\n',
        encoding="utf-8",
    )

    layout = discover_addon(root)
    assert layout.display_name == "Godot State Charts"


def test_nested_plugin_docs_examples_and_api_dirs(tmp_path):
    root = tmp_path / "scene_manager"
    root.mkdir()
    plugin_dir = root / "addons" / "scene_manager"
    docs = plugin_dir / "Docs"
    docs.mkdir(parents=True)
    demo = root / "demo"
    demo.mkdir()
    (plugin_dir / "plugin.cfg").write_text('[plugin]\nname="SceneManager"\n', encoding="utf-8")
    (docs / "quick-start.md").write_text("# Quick Start\n", encoding="utf-8")
    (demo / "Menu.gd").write_text("extends Node\n", encoding="utf-8")
    (plugin_dir / "SceneManager.gd").write_text("extends Node\nclass_name SceneManager\n", encoding="utf-8")

    layout = discover_addon(root)

    assert docs in layout.doc_dirs
    assert demo in layout.example_dirs
    assert plugin_dir in layout.api_dirs
    assert len(collect_doc_files(layout)) == 1
    assert len(collect_example_files(layout)) == 1
    assert len(collect_api_files(layout)) == 1


def test_discovers_named_examples_directory(tmp_path):
    root = tmp_path / "statecharts"
    root.mkdir()
    examples = root / "godot_state_charts_examples"
    examples.mkdir()
    (examples / "ant.gd").write_text("extends Node\n", encoding="utf-8")

    layout = discover_addon(root)

    assert examples in layout.example_dirs


# --- Collect files tests ---

def test_collect_doc_files_excludes_scaffolding(tmp_path):
    root = tmp_path / "addon"
    root.mkdir()
    docs = root / "docs"
    docs.mkdir()
    (docs / "guide.md").write_text("# Guide\n")
    (docs / "_includes").mkdir()
    (docs / "_includes" / "header.md").write_text("header\n")
    (docs / "_layouts").mkdir()
    (docs / "_layouts" / "default.md").write_text("layout\n")
    (docs / "assets").mkdir()
    (docs / "assets" / "style.css").write_text("body{}\n")

    layout = discover_addon(root)
    files = collect_doc_files(layout)
    names = [f.name for f in files]
    assert "guide.md" in names
    assert "header.md" not in names
    assert "default.md" not in names


def test_collect_example_files_finds_gd(tmp_path):
    root = tmp_path / "addon"
    root.mkdir()
    examples = root / "examples"
    examples.mkdir()
    (examples / "player.gd").write_text("extends Node\n## Player script\n")
    (examples / "player.tscn").write_text("[gd_scene]\n")
    (examples / "icon.png").write_bytes(b"\x89PNG\n")

    layout = discover_addon(root)
    files = collect_example_files(layout)
    names = [f.name for f in files]
    assert "player.gd" in names
    assert "player.tscn" not in names
    assert "icon.png" not in names


def test_collect_example_files_finds_readme(tmp_path):
    root = tmp_path / "addon"
    root.mkdir()
    examples = root / "examples"
    examples.mkdir()
    (examples / "README.md").write_text("# Examples\n")

    layout = discover_addon(root)
    files = collect_example_files(layout)
    names = [f.name for f in files]
    assert "README.md" in names


def test_collect_doc_files_finds_rst(tmp_path):
    root = tmp_path / "limboai"
    root.mkdir()
    docs = root / "doc" / "source"
    docs.mkdir(parents=True)
    (docs / "index.rst").write_text("LimboAI\n=======\n\nBehavior trees.\n", encoding="utf-8")

    layout = discover_addon(root)
    files = collect_doc_files(layout)

    assert len(files) == 1
    assert files[0].suffix == ".rst"


# --- Addon chunker tests ---

def test_markdown_split_by_heading():
    md = "# Intro\n\nSome text.\n\n## Usage\n\nHow to use.\n\n## API\n\nDetails.\n"
    chunks = chunk_addon_markdown("myaddon", "My Addon", "addons/myaddon/docs/guide.md", md)
    assert len(chunks) == 3
    assert chunks[0].heading == "Intro"
    assert chunks[1].heading == "Usage"
    assert chunks[2].heading == "API"
    for c in chunks:
        assert c.doc_type == "addon"
        assert c.chunk_type == "addon_doc"
        assert c.addon == "myaddon"
        assert c.addon_name == "My Addon"


def test_markdown_no_heading():
    md = "Just some text without headings.\n"
    chunks = chunk_addon_markdown("myaddon", "My Addon", "addons/myaddon/docs/plain.md", md)
    assert len(chunks) == 1
    assert chunks[0].heading == "plain"


def test_gd_file_as_single_chunk():
    code = 'extends Node\n\n## This is a player script\nfunc _ready():\n\tpass\n'
    chunks = chunk_code_file("statecharts", "Godot State Charts", "addons/statecharts/examples/player.gd", code)
    assert len(chunks) == 1
    c = chunks[0]
    assert c.doc_type == "addon"
    assert c.chunk_type == "addon_example"
    assert c.addon == "statecharts"
    assert c.addon_name == "Godot State Charts"
    assert c.symbol == "addons/statecharts/examples/player.gd"
    assert c.heading == "player.gd"
    assert "## This is a player script" in c.text
    assert c.start_line == 1
    assert c.end_line == 6


def test_cs_file_as_single_chunk():
    code = 'using Godot;\n\n/// <summary>\n/// Player class\n/// </summary>\npublic partial class Player : Node {}\n'
    chunks = chunk_code_file("myaddon", "My Addon", "addons/myaddon/examples/Player.cs", code)
    assert len(chunks) == 1
    assert chunks[0].chunk_type == "addon_example"
    assert "/// <summary>" in chunks[0].text


def test_empty_gd_file_skipped():
    chunks = chunk_code_file("myaddon", "My Addon", "addons/myaddon/examples/empty.gd", "")
    assert len(chunks) == 0


def test_api_file_extracts_public_declarations_only():
    code = """extends Node2D

signal scene_loaded
signal transition_finished

var is_transitioning := false

func change_scene(path: Variant, setted_options: Dictionary = {}) -> void:
\tpass

func _load_scene_resource(path: Variant) -> Resource:
\tpass
"""
    chunks = chunk_api_file(
        "scene_manager",
        "SceneManager",
        "addons/scene_manager/addons/scene_manager/SceneManager.gd",
        code,
    )

    assert len(chunks) == 1
    assert chunks[0].chunk_type == "addon_api"
    assert chunks[0].symbol == "SceneManager"
    assert "SceneManager.change_scene" in chunks[0].symbols
    assert "SceneManager.scene_loaded" in chunks[0].symbols
    assert "SceneManager.is_transitioning" in chunks[0].symbols
    assert "_load_scene_resource" not in chunks[0].symbols
    assert "signal scene_loaded" in chunks[0].text
    assert "func change_scene" in chunks[0].text
    assert "_load_scene_resource" not in chunks[0].text


def test_example_readme_tagged_as_example():
    md = "# Examples\n\nSome examples.\n\n## Basic\n\nBasic usage.\n"
    chunks = chunk_addon_markdown("myaddon", "My Addon", "addons/myaddon/examples/README.md", md)
    for c in chunks:
        assert c.chunk_type == "addon_doc"


def test_chunk_addon_readme_in_examples_becomes_addon_example(tmp_path):
    """End-to-end: README.md inside examples/ gets chunk_type='addon_example'."""
    addon = tmp_path / "myaddon"
    addon.mkdir()
    examples = addon / "examples"
    examples.mkdir()
    (examples / "README.md").write_text(
        "# Examples\n\nSome examples.\n\n## Basic\n\nBasic usage.\n",
        encoding="utf-8",
    )
    (examples / "demo.gd").write_text("func _ready():\n    pass\n", encoding="utf-8")

    chunks = chunk_addon(addon)
    readme_chunks = [c for c in chunks if "README" in c.heading]
    assert len(readme_chunks) > 0, "Should find README chunks"
    for c in readme_chunks:
        assert c.chunk_type == "addon_example", f"README in examples/ should be addon_example, got {c.chunk_type}"


# --- Addon integration tests ---

def _build_addon_db(tmp_path):
    """Build a test database with addons."""
    docs = tmp_path / "docs"
    docs.mkdir()
    classes = docs / "classes"
    classes.mkdir()
    (classes / "class_node.md").write_text(
        "# Node\n\n## Methods\n\n`void` **add_child**()\n\nAdd a child.\n",
        encoding="utf-8",
    )

    addons = tmp_path / "addons"
    addons.mkdir()

    # Addon 1: statecharts
    sc = addons / "statecharts"
    sc.mkdir()
    sc_addons = sc / "addons" / "godot_state_charts"
    sc_addons.mkdir(parents=True)
    (sc_addons / "plugin.cfg").write_text(
        '[plugin]\nname="Godot State Charts"\nauthor="test"\n',
        encoding="utf-8",
    )
    (sc / "README.md").write_text("# Statecharts\n\nState machine for Godot.\n", encoding="utf-8")
    docs_dir = sc / "docs"
    docs_dir.mkdir()
    (docs_dir / "usage.md").write_text(
        "# Usage\n\nCreate a state machine.\n\n## Transitions\n\nAdd transitions.\n",
        encoding="utf-8",
    )
    examples = sc / "examples"
    examples.mkdir()
    (examples / "player.gd").write_text(
        "extends Node\n\n## Player with state machine\nvar state = 'idle'\n",
        encoding="utf-8",
    )

    # Addon 2: dialogue_manager
    dm = addons / "dialogue_manager"
    dm.mkdir()
    (dm / "README.md").write_text("# Dialogue Manager\n\nManage dialogues.\n", encoding="utf-8")
    dm_docs = dm / "docs"
    dm_docs.mkdir()
    (dm_docs / "api.md").write_text("# API\n\nUse `DialogueManager`.\n", encoding="utf-8")

    # Addon 3: scene_manager with nested plugin docs and API source
    sm = addons / "scene_manager"
    sm.mkdir()
    sm_plugin = sm / "addons" / "scene_manager"
    sm_plugin.mkdir(parents=True)
    (sm_plugin / "plugin.cfg").write_text('[plugin]\nname="SceneManager"\n', encoding="utf-8")
    sm_docs = sm_plugin / "Docs"
    sm_docs.mkdir()
    (sm_docs / "quick-start.md").write_text("# Quick Start\n\nUse change_scene.\n", encoding="utf-8")
    (sm_plugin / "SceneManager.gd").write_text(
        "extends Node2D\n\nsignal scene_loaded\n\nfunc change_scene(path):\n\tpass\n",
        encoding="utf-8",
    )

    db_path = tmp_path / "test.sqlite"
    build_database(docs, db_path, addons_dir=addons)
    return db_path


def test_addon_data_in_database(tmp_path):
    db_path = _build_addon_db(tmp_path)
    results = search_database(db_path, "state machine", limit=20, doc_types=["addon"])
    assert len(results) > 0
    for r in results:
        assert r.doc_type == "addon"
    addons_found = {r.addon for r in results}
    assert "statecharts" in addons_found


def test_search_specific_addon(tmp_path):
    db_path = _build_addon_db(tmp_path)
    results = search_database(db_path, "state machine", limit=20, addon="statecharts")
    for r in results:
        assert r.addon == "statecharts"


def test_addon_search_does_not_affect_main(tmp_path):
    db_path = _build_addon_db(tmp_path)
    results = search_database(db_path, "add_child", limit=5)
    doc_types = {r.doc_type for r in results}
    assert "class" in doc_types


def test_addon_has_code_example(tmp_path):
    db_path = _build_addon_db(tmp_path)
    results = search_database(db_path, "player state machine", limit=5, doc_types=["addon"])
    texts = " ".join(r.text for r in results)
    assert "player" in texts.lower()


def test_addon_readme_in_results(tmp_path):
    db_path = _build_addon_db(tmp_path)
    results = search_database(db_path, "dialogue", limit=10, addon="dialogue_manager")
    assert len(results) > 0


def test_nested_addon_docs_and_api_are_searchable(tmp_path):
    db_path = _build_addon_db(tmp_path)
    results = search_database(db_path, "change_scene", limit=10, addon="scene_manager")
    chunk_types = {r.chunk_type for r in results}
    assert "addon_doc" in chunk_types
    assert "addon_api" in chunk_types


def test_nested_addon_api_alias_is_searchable(tmp_path):
    db_path = _build_addon_db(tmp_path)
    results = search_database(
        db_path,
        "SceneManager.change_scene",
        limit=3,
        addon="scene_manager",
    )
    assert len(results) > 0
    assert results[0].chunk_type == "addon_api"
    assert results[0].symbol == "SceneManager"


def test_addon_example_symbol_points_to_own_chunk(tmp_path):
    db_path = _build_addon_db(tmp_path)
    results = search_database(
        db_path,
        "addons/statecharts/examples/player.gd",
        limit=3,
        addon="statecharts",
    )
    assert len(results) > 0
    assert results[0].chunk_type == "addon_example"
    assert results[0].path == "addons/statecharts/examples/player.gd"


# --- Addon CLI tests ---

def test_saddon_help():
    result = subprocess.run(
        [sys.executable, "-m", "rag.cli", "s-addon", "--help"],
        text=True,
        capture_output=True,
        env=TEST_ENV,
    )
    assert result.returncode == 0
    assert "query" in result.stdout
    assert "--addon" in result.stdout


def test_build_help_has_addons():
    result = subprocess.run(
        [sys.executable, "-m", "rag.cli", "build", "--help"],
        text=True,
        capture_output=True,
        env=TEST_ENV,
    )
    assert result.returncode == 0
    assert "--addons" in result.stdout
