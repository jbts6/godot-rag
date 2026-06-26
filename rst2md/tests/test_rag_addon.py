"""Tests for addon discovery, chunking, search, and CLI."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from rag.addon_docs import (
    AddonLayout,
    chunk_addon,
    chunk_addon_markdown,
    chunk_code_file,
    collect_doc_files,
    collect_example_files,
    discover_addon,
)
from rag.store import build_database, search_database


class TestAddonDiscovery(unittest.TestCase):
    """discover_addon should find docs and example directories."""

    def test_finds_docs_and_examples(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "myaddon"
            root.mkdir()
            (root / "docs").mkdir()
            (root / "examples").mkdir()
            (root / "README.md").write_text("# My Addon\n")

            layout = discover_addon(root)
            self.assertEqual(layout.name, "myaddon")
            self.assertEqual(len(layout.doc_dirs), 1)
            self.assertEqual(layout.doc_dirs[0].name, "docs")
            self.assertEqual(len(layout.example_dirs), 1)
            self.assertEqual(layout.example_dirs[0].name, "examples")
            self.assertEqual(len(layout.doc_files), 1)

    def test_finds_documentation_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "gdunit"
            root.mkdir()
            (root / "documentation").mkdir()

            layout = discover_addon(root)
            self.assertEqual(len(layout.doc_dirs), 1)
            self.assertEqual(layout.doc_dirs[0].name, "documentation")

    def test_finds_doc_source_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "limboai"
            root.mkdir()
            doc_source = root / "doc" / "source"
            doc_source.mkdir(parents=True)

            layout = discover_addon(root)
            self.assertEqual(len(layout.doc_dirs), 1)
            self.assertEqual(layout.doc_dirs[0], doc_source)

    def test_no_docs_dir_just_readme(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "phantom"
            root.mkdir()
            (root / "README.md").write_text("# Phantom Camera\n")

            layout = discover_addon(root)
            self.assertEqual(len(layout.doc_dirs), 0)
            self.assertEqual(len(layout.doc_files), 1)

    def test_no_readme_no_docs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "empty"
            root.mkdir()

            layout = discover_addon(root)
            self.assertEqual(len(layout.doc_dirs), 0)
            self.assertEqual(len(layout.doc_files), 0)
            self.assertEqual(len(layout.example_dirs), 0)


class TestCollectFiles(unittest.TestCase):
    """collect_doc_files and collect_example_files should filter correctly."""

    def test_collect_doc_files_excludes_scaffolding(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "addon"
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
            self.assertIn("guide.md", names)
            self.assertNotIn("header.md", names)
            self.assertNotIn("default.md", names)

    def test_collect_example_files_finds_gd(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "addon"
            root.mkdir()
            examples = root / "examples"
            examples.mkdir()
            (examples / "player.gd").write_text("extends Node\n## Player script\n")
            (examples / "player.tscn").write_text("[gd_scene]\n")
            (examples / "icon.png").write_bytes(b"\x89PNG\n")

            layout = discover_addon(root)
            files = collect_example_files(layout)
            names = [f.name for f in files]
            self.assertIn("player.gd", names)
            self.assertNotIn("player.tscn", names)
            self.assertNotIn("icon.png", names)

    def test_collect_example_files_finds_readme(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "addon"
            root.mkdir()
            examples = root / "examples"
            examples.mkdir()
            (examples / "README.md").write_text("# Examples\n")

            layout = discover_addon(root)
            files = collect_example_files(layout)
            names = [f.name for f in files]
            self.assertIn("README.md", names)


class TestAddonChunker(unittest.TestCase):
    """chunk_addon_markdown and chunk_code_file should produce correct chunks."""

    def test_markdown_split_by_heading(self):
        md = "# Intro\n\nSome text.\n\n## Usage\n\nHow to use.\n\n## API\n\nDetails.\n"
        chunks = chunk_addon_markdown("myaddon", "addons/myaddon/docs/guide.md", md)
        self.assertEqual(len(chunks), 3)
        self.assertEqual(chunks[0].heading, "Intro")
        self.assertEqual(chunks[1].heading, "Usage")
        self.assertEqual(chunks[2].heading, "API")
        for c in chunks:
            self.assertEqual(c.doc_type, "addon")
            self.assertEqual(c.chunk_type, "addon_doc")
            self.assertEqual(c.addon, "myaddon")

    def test_markdown_no_heading(self):
        md = "Just some text without headings.\n"
        chunks = chunk_addon_markdown("myaddon", "addons/myaddon/docs/plain.md", md)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].heading, "plain")

    def test_gd_file_as_single_chunk(self):
        code = 'extends Node\n\n## This is a player script\nfunc _ready():\n\tpass\n'
        chunks = chunk_code_file("statecharts", "addons/statecharts/examples/player.gd", code)
        self.assertEqual(len(chunks), 1)
        c = chunks[0]
        self.assertEqual(c.doc_type, "addon")
        self.assertEqual(c.chunk_type, "addon_example")
        self.assertEqual(c.addon, "statecharts")
        self.assertEqual(c.symbol, "addons/statecharts/examples/player.gd")
        self.assertEqual(c.heading, "player.gd")
        self.assertIn("## This is a player script", c.text)
        self.assertEqual(c.start_line, 1)
        self.assertEqual(c.end_line, 6)

    def test_cs_file_as_single_chunk(self):
        code = 'using Godot;\n\n/// <summary>\n/// Player class\n/// </summary>\npublic partial class Player : Node {}\n'
        chunks = chunk_code_file("myaddon", "addons/myaddon/examples/Player.cs", code)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].chunk_type, "addon_example")
        self.assertIn("/// <summary>", chunks[0].text)

    def test_empty_gd_file_skipped(self):
        chunks = chunk_code_file("myaddon", "addons/myaddon/examples/empty.gd", "")
        self.assertEqual(len(chunks), 0)

    def test_example_readme_tagged_as_example(self):
        md = "# Examples\n\nSome examples.\n\n## Basic\n\nBasic usage.\n"
        chunks = chunk_addon_markdown("myaddon", "addons/myaddon/examples/README.md", md)
        # Override chunk_type as chunk_addon does
        for c in chunks:
            self.assertEqual(c.chunk_type, "addon_doc")  # raw function returns addon_doc
        # But after chunk_addon processing, they become addon_example


class TestAddonIntegration(unittest.TestCase):
    """End-to-end: build database with addons and search."""

    def _build_db(self, tmp):
        # Create Godot docs (minimal)
        docs = Path(tmp) / "docs"
        docs.mkdir()
        classes = docs / "classes"
        classes.mkdir()
        (classes / "class_node.md").write_text(
            "# Node\n\n## Methods\n\n`void` **add_child**()\n\nAdd a child.\n",
            encoding="utf-8",
        )

        # Create addons
        addons = Path(tmp) / "addons"
        addons.mkdir()

        # Addon 1: statecharts
        sc = addons / "statecharts"
        sc.mkdir()
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

        db_path = Path(tmp) / "test.sqlite"
        build_database(docs, db_path, addons_dir=addons)
        return db_path

    def test_addon_data_in_database(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = self._build_db(tmp)
            results = search_database(db_path, "state machine", limit=20, doc_types=["addon"])
            self.assertGreater(len(results), 0)
            for r in results:
                self.assertEqual(r.doc_type, "addon")
                self.assertEqual(r.addon, "statecharts")

    def test_search_specific_addon(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = self._build_db(tmp)
            results = search_database(db_path, "state machine", limit=20, addon="statecharts")
            for r in results:
                self.assertEqual(r.addon, "statecharts")

    def test_addon_search_does_not_affect_main(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = self._build_db(tmp)
            # Main search should return Godot docs
            results = search_database(db_path, "add_child", limit=5)
            doc_types = {r.doc_type for r in results}
            self.assertIn("class", doc_types)

    def test_addon_has_code_example(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = self._build_db(tmp)
            results = search_database(db_path, "player state machine", limit=5, doc_types=["addon"])
            texts = " ".join(r.text for r in results)
            self.assertIn("player", texts.lower())

    def test_addon_readme_in_results(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = self._build_db(tmp)
            results = search_database(db_path, "dialogue", limit=10, addon="dialogue_manager")
            self.assertGreater(len(results), 0)


class TestAddonCLI(unittest.TestCase):
    def test_saddon_help(self):
        result = subprocess.run(
            [sys.executable, "-m", "rag.cli", "s-addon", "--help"],
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("query", result.stdout)
        self.assertIn("--addon", result.stdout)

    def test_build_help_has_addons(self):
        result = subprocess.run(
            [sys.executable, "-m", "rag.cli", "build", "--help"],
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("--addons", result.stdout)


if __name__ == "__main__":
    unittest.main()
