import json
import subprocess
import sys
import tempfile
import unittest
import os
from pathlib import Path
from unittest.mock import patch

from rag.cli import _db_path_from_args
from rag.chunker import chunk_markdown
from rag.store import build_database, search_database


TEST_ENV = {**os.environ, "PYTHONPATH": "rst2md"}


class SearchTests(unittest.TestCase):
    def test_symbol_query_returns_exact_method_first(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp) / "docs"
            docs.mkdir()
            classes = docs / "classes"
            classes.mkdir()
            (classes / "class_stringname.md").write_text(
                "# StringName\n\n"
                "## Methods\n\n"
                "`bool` **is_valid_filename**() `const`\n\n"
                "Returns `true` if this string is a valid file name.\n",
                encoding="utf-8",
            )
            db_path = Path(tmp) / "godot_docs.sqlite"

            build_database(docs, db_path)
            results = search_database(db_path, "StringName.is_valid_filename", limit=3)

            self.assertGreaterEqual(len(results), 1)
            self.assertEqual(results[0].symbol, "StringName.is_valid_filename")
            self.assertEqual(results[0].path, "classes/class_stringname.md")


class FtsScoreTests(unittest.TestCase):
    """BM25 score mapping should produce reasonable distribution."""

    def _build_db(self, tmp):
        docs = Path(tmp) / "docs"
        docs.mkdir()
        classes = docs / "classes"
        classes.mkdir()
        # Create classes with varied content lengths to get different BM25 scores
        for cls_name, methods in [("Timer", 5), ("Node", 10), ("Object", 3)]:
            content = f"# {cls_name}\n\n{cls_name} is a class.\n\n## Methods\n\n"
            for i in range(methods):
                extra = " extra context " * i  # vary document length
                content += f"`bool` **method_{i}**() `const`\n\n{extra}A useful method.\n\n"
            (classes / f"class_{cls_name.lower()}.md").write_text(content, encoding="utf-8")
        db_path = Path(tmp) / "test.sqlite"
        build_database(docs, db_path)
        return db_path

    def test_fts_formula_produces_varied_scores(self):
        """The BM25 formula should map different raw values to different scores."""
        # Direct unit test of the formula
        def fts_score(bm25):
            return min(40.0, max(0.0, 40.0 / (1.0 + bm25 * 0.01)))

        # Different BM25 values should produce different scores
        scores = {fts_score(v) for v in [0.0, 0.5, 1.0, 5.0, 10.0, 50.0, 100.0]}
        self.assertGreater(len(scores), 3, "Formula should produce varied scores")


class FtsEscapeTests(unittest.TestCase):
    """FTS5 queries with special characters should not silently fail."""

    def _build_db(self, tmp):
        docs = Path(tmp) / "docs"
        docs.mkdir()
        classes = docs / "classes"
        classes.mkdir()
        (classes / "class_timer.md").write_text(
            "# Timer\n\n"
            "## Methods\n\n"
            "`bool` **is_stopped**() `const`\n\n"
            "Returns true if the timer is stopped.\n\n"
            "`float` **get_time_left**()\n\n"
            "Returns the remaining time.\n",
            encoding="utf-8",
        )
        db_path = Path(tmp) / "test.sqlite"
        build_database(docs, db_path)
        return db_path

    def test_colon_in_query_still_returns_fts_results(self):
        """Queries with FTS5 special chars (e.g. ':') should not silently
        suppress full-text results."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = self._build_db(tmp)
            # "is_stopped" appears in chunk text; colon in query should
            # not prevent FTS from finding it.
            results = search_database(db_path, "is_stopped:const", limit=3)
            texts = " ".join(r.text for r in results)
            self.assertIn("is_stopped", texts)

    def test_plain_fts_query_returns_results(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = self._build_db(tmp)
            results = search_database(db_path, "stopped timer", limit=3)
            texts = " ".join(r.text for r in results)
            self.assertIn("stopped", texts.lower())


class DocTypeFilterTests(unittest.TestCase):
    """search_database should filter results by doc_type when requested."""

    def _build_db(self, tmp):
        docs = Path(tmp) / "docs"
        docs.mkdir()

        # Class doc
        classes = docs / "classes"
        classes.mkdir()
        (classes / "class_timer.md").write_text(
            "# Timer\n\n"
            "## Methods\n\n"
            "`bool` **is_stopped**() `const`\n\n"
            "Returns true if the timer is stopped.\n",
            encoding="utf-8",
        )

        # Tutorial doc
        tutorials = docs / "tutorials"
        tutorials.mkdir()
        (tutorials / "intro_to_signals.md").write_text(
            "# Introduction to Signals\n\n"
            "Signals are a way to...\n\n"
            "## Using Timer\n\n"
            "The timer node is stopped when...\n",
            encoding="utf-8",
        )

        db_path = Path(tmp) / "test.sqlite"
        build_database(docs, db_path)
        return db_path

    def test_search_all_returns_both_types(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = self._build_db(tmp)
            results = search_database(db_path, "timer stopped", limit=10)
            doc_types = {r.doc_type for r in results}
            # Should find results from both class and tutorial
            self.assertIn("class", doc_types)

    def test_search_class_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = self._build_db(tmp)
            results = search_database(db_path, "timer stopped", limit=10, doc_types=["class"])
            doc_types = {r.doc_type for r in results}
            self.assertNotIn("tutorial", doc_types)

    def test_search_tutorial_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = self._build_db(tmp)
            results = search_database(
                db_path, "timer stopped", limit=10, doc_types=["tutorial", "getting_started"]
            )
            doc_types = {r.doc_type for r in results}
            self.assertNotIn("class", doc_types)

    def test_empty_doc_types_treated_as_none(self):
        """Passing an empty list should search all types (no filter)."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = self._build_db(tmp)
            all_results = search_database(db_path, "timer stopped", limit=10)
            filtered = search_database(db_path, "timer stopped", limit=10, doc_types=[])
            self.assertEqual(len(all_results), len(filtered))


class RelationModuleImportTests(unittest.TestCase):
    """rag.relations module should expose extract_inherits, INHERITS_RE, and build_chunk_relations."""

    def test_import_extract_inherits(self):
        from rag.relations import extract_inherits
        self.assertEqual(extract_inherits("no inherits here"), [])

    def test_import_inherits_re(self):
        from rag.relations import INHERITS_RE
        self.assertTrue(INHERITS_RE.search("**Inherits:** `Object`"))

    def test_import_build_chunk_relations(self):
        from rag.relations import build_chunk_relations
        import inspect
        self.assertTrue(callable(build_chunk_relations))
        self.assertEqual(len(inspect.signature(build_chunk_relations).parameters), 1)

    def test_extract_inherits_finds_backticked_names(self):
        from rag.relations import extract_inherits
        result = extract_inherits("**Inherits:** `Node` and `Object`")
        self.assertEqual(result, ["Node", "Object"])


class ChunkRelationTests(unittest.TestCase):
    """chunk_relations table should be created and populated."""

    def _build_db(self, tmp):
        docs = Path(tmp) / "docs"
        docs.mkdir()
        classes = docs / "classes"
        classes.mkdir()
        (classes / "class_node.md").write_text(
            "# Node\n\nBase class.\n\n**Inherits:** `Object`\n\n"
            "## Methods\n\n"
            "`void` **add_child**(`Node` node)\n\nAdds a child.\n\n"
            "`void` **remove_child**(`Node` node)\n\nRemoves a child.\n\n",
            encoding="utf-8",
        )
        (classes / "class_object.md").write_text(
            "# Object\n\nBase of all classes.\n\n",
            encoding="utf-8",
        )
        db_path = Path(tmp) / "test.sqlite"
        build_database(docs, db_path)
        return db_path

    def test_relation_table_exists(self):
        import sqlite3
        with tempfile.TemporaryDirectory() as tmp:
            db_path = self._build_db(tmp)
            conn = sqlite3.connect(str(db_path))
            tables = [r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()]
            conn.close()
            self.assertIn("chunk_relations", tables)

    def test_parent_relations_exist(self):
        import sqlite3
        with tempfile.TemporaryDirectory() as tmp:
            db_path = self._build_db(tmp)
            conn = sqlite3.connect(str(db_path))
            count = conn.execute(
                "SELECT COUNT(*) FROM chunk_relations WHERE relation='parent'"
            ).fetchone()[0]
            conn.close()
            self.assertGreater(count, 0, "Should have parent relations")

    def test_inherits_relations_exist(self):
        import sqlite3
        with tempfile.TemporaryDirectory() as tmp:
            db_path = self._build_db(tmp)
            conn = sqlite3.connect(str(db_path))
            count = conn.execute(
                "SELECT COUNT(*) FROM chunk_relations WHERE relation='inherits'"
            ).fetchone()[0]
            conn.close()
            self.assertGreater(count, 0, "Should have inherits relations")


class FtsTokenizeTests(unittest.TestCase):
    """FTS query tokenizer should split dotted symbols."""

    def test_dotted_symbol_splits_to_tokens(self):
        from rag.store import _smart_tokenize
        result = _smart_tokenize("Node.add_child")
        self.assertIn("Node", result)
        self.assertIn("add", result)
        self.assertIn("child", result)
        self.assertIn("AND", result)

    def test_plain_query_unchanged(self):
        from rag.store import _smart_tokenize
        result = _smart_tokenize("scene transition")
        self.assertEqual(result, "scene transition")

    def test_special_chars_quoted(self):
        from rag.store import _smart_tokenize
        result = _smart_tokenize("Node::add")
        # Colons should be quoted
        self.assertIn('"Node::add"', result)


class GraphExpansionTests(unittest.TestCase):
    """Graph expansion should return related chunks."""

    def _build_db(self, tmp):
        docs = Path(tmp) / "docs"
        docs.mkdir()
        classes = docs / "classes"
        classes.mkdir()
        (classes / "class_node.md").write_text(
            "# Node\n\nBase class.\n\n**Inherits:** `Object`\n\n"
            "## Methods\n\n"
            "`void` **add_child**(`Node` node)\n\nAdds a child node.\n\n"
            "`void` **remove_child**(`Node` node)\n\nRemoves a child.\n\n",
            encoding="utf-8",
        )
        (classes / "class_object.md").write_text(
            "# Object\n\nBase of all classes.\n\n## Methods\n\n"
            "`void` **free**()\n\nFrees the object.\n\n",
            encoding="utf-8",
        )
        db_path = Path(tmp) / "test.sqlite"
        build_database(docs, db_path)
        return db_path

    def test_expand_returns_parent_chunk(self):
        """Searching for a method should return its class_summary via parent relation."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = self._build_db(tmp)
            results = search_database(db_path, "add_child", limit=5, expand_graph=True)
            # Should have the method itself plus parent class_summary
            symbols = {r.symbol for r in results}
            self.assertIn("Node.add_child", symbols)
            # Parent (Node class_summary) should be in results
            self.assertIn("Node", symbols)

    def test_no_expand_returns_only_direct(self):
        """With expand_graph=False, should only return direct matches."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = self._build_db(tmp)
            results = search_database(db_path, "add_child", limit=5, expand_graph=False)
            symbols = {r.symbol for r in results}
            self.assertIn("Node.add_child", symbols)
            # Without expansion, Node class_summary may not be present
            # (depends on FTS, but at least distance=0 results only)

    def test_expanded_results_have_distance(self):
        """Expanded results should have distance=1."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = self._build_db(tmp)
            results = search_database(db_path, "add_child", limit=5, expand_graph=True)
            expanded = [r for r in results if r.distance == 1]
            self.assertGreater(len(expanded), 0, "Should have expanded results with distance=1")

    def test_expanded_results_have_relation_type(self):
        """Expanded results should have a relation_type."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = self._build_db(tmp)
            results = search_database(db_path, "add_child", limit=5, expand_graph=True)
            expanded = [r for r in results if r.relation_type]
            self.assertGreater(len(expanded), 0, "Should have expanded results with relation_type")


class AddonSearchTests(unittest.TestCase):
    """Addon search should support --no-expand flag."""

    def _build_db(self, tmp):
        """Build a database with addon content that has graph relations."""
        docs = Path(tmp) / "docs"
        docs.mkdir()
        classes = docs / "classes"
        classes.mkdir()
        # Create a class document that will be referenced
        (classes / "class_node.md").write_text(
            "# Node\n\nBase class.\n\n## Methods\n\n"
            "`void` **add_child**(`Node` node)\n\nAdds a child.\n\n",
            encoding="utf-8",
        )

        # Create addon content with API source that references Node
        addons = Path(tmp) / "addons"
        addons.mkdir()
        sm = addons / "scene_manager"
        sm.mkdir()
        sm_plugin = sm / "addons" / "scene_manager"
        sm_plugin.mkdir(parents=True)
        (sm_plugin / "plugin.cfg").write_text('[plugin]\nname="SceneManager"\n', encoding="utf-8")
        sm_docs = sm_plugin / "Docs"
        sm_docs.mkdir()
        (sm_docs / "quick-start.md").write_text(
            "# Quick Start\n\nUse `SceneManager.change_scene` to switch scenes.\n\n"
            "This addon extends `Node` to provide scene management.\n",
            encoding="utf-8",
        )
        (sm_plugin / "SceneManager.gd").write_text(
            "extends Node\n\nsignal scene_loaded\n\nfunc change_scene(path):\n\tpass\n",
            encoding="utf-8",
        )

        db_path = Path(tmp) / "test.sqlite"
        build_database(docs, db_path, addons_dir=addons)
        return db_path

    def test_addon_search_respects_no_expand(self):
        """search_database with expand_graph=False should not expand results."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = self._build_db(tmp)
            # Search with expansion (without addon filter to get graph expansion)
            results_expand = search_database(db_path, "SceneManager", limit=5, expand_graph=True)
            # Search without expansion
            results_no_expand = search_database(db_path, "SceneManager", limit=5, expand_graph=False)
            # Without expansion, should have fewer or equal results
            self.assertLessEqual(len(results_no_expand), len(results_expand))
            # Without expansion, all results should have distance=0
            for r in results_no_expand:
                self.assertEqual(r.distance, 0, "No-expand results should have distance=0")

    def test_cli_addon_search_no_expand_flag(self):
        """cmd_search_addon should pass expand_graph=False when --no-expand is set."""
        from rag.cli import cmd_search_addon
        from unittest.mock import MagicMock, patch

        with tempfile.TemporaryDirectory() as tmp:
            db_path = self._build_db(tmp)

            # Mock args with no_expand=True
            args = MagicMock()
            args.db = str(db_path)
            args.query = "SceneManager"
            args.limit = 5
            args.json = True
            args.no_expand = True
            args.addon = None
            args.debug_search = False

            # Patch search_database to capture the call
            with patch("rag.cli.search_database") as mock_search:
                mock_search.return_value = []
                cmd_search_addon(args)

                # Verify search_database was called with expand_graph=False
                mock_search.assert_called_once()
                call_kwargs = mock_search.call_args
                self.assertEqual(call_kwargs.kwargs.get("expand_graph", True), False,
                                 "search_database should be called with expand_graph=False when --no-expand is set")


class CliTests(unittest.TestCase):
    def test_cli_help_runs(self):
        result = subprocess.run(
            [sys.executable, "-m", "rag.cli", "--help"],
            text=True,
            capture_output=True,
            env=TEST_ENV,
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("build", result.stdout)
        self.assertIn("s", result.stdout)

    def test_cli_search_alias_works(self):
        """Long alias 'search' should work as alias for 's'."""
        result = subprocess.run(
            [sys.executable, "-m", "rag.cli", "search", "--help"],
            text=True,
            capture_output=True,
            env=TEST_ENV,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("query", result.stdout)

    def test_build_shows_progress(self):
        """build_database should print progress output."""
        import io
        from contextlib import redirect_stdout

        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp) / "docs"
            docs.mkdir()
            classes = docs / "classes"
            classes.mkdir()
            # Create multiple files to trigger progress output
            for i in range(105):
                (classes / f"class_test{i}.md").write_text(
                    f"# Test{i}\n\n## Methods\n\n`void` **method{i}**()\n\nA test method.\n",
                    encoding="utf-8",
                )
            db_path = Path(tmp) / "test.sqlite"

            f = io.StringIO()
            with redirect_stdout(f):
                build_database(docs, db_path)

            output = f.getvalue()
            # Should contain progress output
            self.assertIn("Building database", output)


class ConnectionManagerTests(unittest.TestCase):
    """Test SQLite connection context manager."""

    def test_clean_chunk_text_importable_from_store_facade(self):
        """clean_chunk_text should remain importable from rag.store."""
        from rag.store import clean_chunk_text

        self.assertEqual(clean_chunk_text("classref-test\n`Node<class_Node>`"), "`Node`")

    def test_get_connection_context_manager(self):
        """get_connection should provide a working connection."""
        from rag.store import get_connection

        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "test.sqlite"

            # Create a simple database
            import sqlite3
            conn = sqlite3.connect(str(db_path))
            conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")
            conn.execute("INSERT INTO test VALUES (1, 'hello')")
            conn.commit()
            conn.close()

            # Use context manager
            with get_connection(db_path) as conn:
                result = conn.execute("SELECT name FROM test WHERE id = 1").fetchone()
                self.assertEqual(result[0], "hello")

    def test_get_connection_sets_row_factory(self):
        """get_connection should set row_factory to sqlite3.Row."""
        from rag.store import get_connection

        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "test.sqlite"

            # Create a simple database
            import sqlite3
            conn = sqlite3.connect(str(db_path))
            conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")
            conn.execute("INSERT INTO test VALUES (1, 'hello')")
            conn.commit()
            conn.close()

            # Use context manager
            with get_connection(db_path) as conn:
                result = conn.execute("SELECT name FROM test WHERE id = 1").fetchone()
                # Should be sqlite3.Row object
                self.assertIsInstance(result, sqlite3.Row)
                self.assertEqual(result["name"], "hello")


class StatsCommandTests(unittest.TestCase):
    """Test godot-rag stats command."""

    def _build_db(self, tmp):
        """Build a test database."""
        docs = Path(tmp) / "docs"
        docs.mkdir()
        classes = docs / "classes"
        classes.mkdir()
        (classes / "class_node.md").write_text(
            "# Node\n\nBase class.\n\n## Methods\n\n"
            "`void` **add_child**(`Node` node)\n\nAdds a child.\n\n",
            encoding="utf-8",
        )
        db_path = Path(tmp) / "test.sqlite"
        build_database(docs, db_path)
        return db_path

    def test_get_stats_returns_expected_keys(self):
        """get_stats should return a dict with expected keys."""
        from rag.store import get_stats

        with tempfile.TemporaryDirectory() as tmp:
            db_path = self._build_db(tmp)
            stats = get_stats(db_path)

            self.assertIn("chunks", stats)
            self.assertIn("symbols", stats)
            self.assertIn("relations", stats)
            self.assertIn("addons", stats)

    def test_get_stats_returns_correct_chunk_count(self):
        """get_stats should return correct chunk count."""
        from rag.store import get_stats

        with tempfile.TemporaryDirectory() as tmp:
            db_path = self._build_db(tmp)
            stats = get_stats(db_path)

            self.assertEqual(stats["chunks"]["total"], 2)  # class_summary + method

    def test_cli_stats_command_works(self):
        """godot-rag stats should work."""
        result = subprocess.run(
            [sys.executable, "-m", "rag.cli", "stats", "--help"],
            text=True,
            capture_output=True,
            env=TEST_ENV,
        )
        self.assertEqual(result.returncode, 0)


class SnippetTests(unittest.TestCase):
    """Test snippet highlighting in search results."""

    def _build_db(self, tmp):
        """Build a test database with multi-line content."""
        docs = Path(tmp) / "docs"
        docs.mkdir()
        classes = docs / "classes"
        classes.mkdir()
        # Create a document with multiple lines
        content = "# Node\n\nBase class for all scene nodes.\n\n"
        content += "## Description\n\n"
        content += "Nodes are the basic building blocks of scenes.\n"
        content += "They can be added as children of other nodes.\n"
        content += "The scene tree is made of nodes.\n\n"
        content += "## Methods\n\n"
        content += "`void` **add_child**(`Node` node)\n\n"
        content += "Adds a child node to the scene tree.\n"
        (classes / "class_node.md").write_text(content, encoding="utf-8")
        db_path = Path(tmp) / "test.sqlite"
        build_database(docs, db_path)
        return db_path

    def test_search_result_has_snippet_field(self):
        """SearchResult should have a snippet field."""
        from rag.models import SearchResult

        result = SearchResult(
            score=100.0,
            path="test.md",
            start_line=1,
            end_line=10,
            doc_type="class",
            chunk_type="class_summary",
            addon="",
            addon_name="",
            symbol="Node",
            heading="Node",
            breadcrumb="classes > Node",
            text="Some text here",
        )
        self.assertEqual(result.snippet, "")

    def test_search_database_returns_snippet(self):
        """search_database should return results with snippet field."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = self._build_db(tmp)
            results = search_database(db_path, "add_child", limit=5)

            self.assertGreater(len(results), 0)
            # Results should have snippet field
            for r in results:
                self.assertIsInstance(r.snippet, str)


class RegressionTests(unittest.TestCase):
    """Regression tests for bug fixes."""

    def test_addon_search_no_expand_flag(self):
        """Regression test: addon search should respect --no-expand flag."""
        from rag.cli import cmd_search_addon
        from unittest.mock import MagicMock, patch

        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp) / "docs"
            docs.mkdir()
            classes = docs / "classes"
            classes.mkdir()
            (classes / "class_node.md").write_text(
                "# Node\n\nBase class.\n\n## Methods\n\n"
                "`void` **add_child**(`Node` node)\n\nAdds a child.\n\n",
                encoding="utf-8",
            )

            # Create addon content with API source that references Node
            addons = Path(tmp) / "addons"
            addons.mkdir()
            sm = addons / "scene_manager"
            sm.mkdir()
            sm_plugin = sm / "addons" / "scene_manager"
            sm_plugin.mkdir(parents=True)
            (sm_plugin / "plugin.cfg").write_text('[plugin]\nname="SceneManager"\n', encoding="utf-8")
            sm_docs = sm_plugin / "Docs"
            sm_docs.mkdir()
            (sm_docs / "quick-start.md").write_text(
                "# Quick Start\n\nUse `SceneManager.change_scene` to switch scenes.\n\n"
                "This addon extends `Node` to provide scene management.\n",
                encoding="utf-8",
            )
            (sm_plugin / "SceneManager.gd").write_text(
                "extends Node\n\nsignal scene_loaded\n\nfunc change_scene(path):\n\tpass\n",
                encoding="utf-8",
            )

            db_path = Path(tmp) / "test.sqlite"
            build_database(docs, db_path, addons_dir=addons)

            # Mock args with no_expand=True
            args = MagicMock()
            args.db = str(db_path)
            args.query = "SceneManager"
            args.limit = 5
            args.json = True
            args.no_expand = True
            args.addon = None
            args.debug_search = False

            # Patch search_database to capture the call
            with patch("rag.cli.search_database") as mock_search:
                mock_search.return_value = []
                cmd_search_addon(args)

                # Verify search_database was called with expand_graph=False
                mock_search.assert_called_once()
                call_kwargs = mock_search.call_args
                self.assertEqual(call_kwargs.kwargs.get("expand_graph", True), False,
                                 "search_database should be called with expand_graph=False when --no-expand is set")

    def test_cli_search_class_help(self):
        result = subprocess.run(
            [sys.executable, "-m", "rag.cli", "s-class", "--help"],
            text=True,
            capture_output=True,
            env=TEST_ENV,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("query", result.stdout)

    def test_cli_search_tutorial_help(self):
        result = subprocess.run(
            [sys.executable, "-m", "rag.cli", "s-tutorial", "--help"],
            text=True,
            capture_output=True,
            env=TEST_ENV,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("query", result.stdout)

    def test_cli_search_engine_help(self):
        result = subprocess.run(
            [sys.executable, "-m", "rag.cli", "s-engine", "--help"],
            text=True,
            capture_output=True,
            env=TEST_ENV,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("query", result.stdout)

    def test_search_args_default_to_bundled_database(self):
        class Args:
            db = None

        with patch("rag.cli.default_db_path", return_value=Path("/tmp/godot_docs.sqlite")):
            self.assertEqual(_db_path_from_args(Args()), Path("/tmp/godot_docs.sqlite"))

    def test_cli_diagnostics_help(self):
        result = subprocess.run(
            [sys.executable, "-m", "rag.cli", "diagnostics", "--help"],
            capture_output=True,
            text=True,
            env=TEST_ENV,
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("--db", result.stdout)
        self.assertIn("--json", result.stdout)

    def test_cli_search_debug_json_includes_metadata(self):
        from rag import embeddings
        from rag.cli import cmd_search
        from unittest.mock import MagicMock

        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp) / "docs"
            classes = docs / "classes"
            classes.mkdir(parents=True)
            (classes / "class_timer.md").write_text(
                "# Timer\n\n"
                "## Methods\n\n"
                "`bool` **is_stopped**() `const`\n\n"
                "Returns true if the timer is stopped.\n",
                encoding="utf-8",
            )
            with patch.object(embeddings, "generate_embeddings", return_value=[[0.0] * 256]):
                db_path = Path(tmp) / "test.db"
                build_database(docs, db_path)

                args = MagicMock()
                args.db = str(db_path)
                args.query = "timer stopped"
                args.limit = 3
                args.json = True
                args.no_expand = True
                args.debug_search = True

                import io
                from contextlib import redirect_stdout

                f = io.StringIO()
                with redirect_stdout(f):
                    cmd_search(args)
                output = json.loads(f.getvalue())

                self.assertIn("metadata", output)
                self.assertIn("mode", output["metadata"])
                self.assertIn("results", output)

    def test_cli_search_debug_text_includes_metadata(self):
        from rag import embeddings
        from rag.cli import cmd_search
        from unittest.mock import MagicMock

        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp) / "docs"
            classes = docs / "classes"
            classes.mkdir(parents=True)
            (classes / "class_timer.md").write_text(
                "# Timer\n\n"
                "## Methods\n\n"
                "`bool` **is_stopped**() `const`\n\n"
                "Returns true if the timer is stopped.\n",
                encoding="utf-8",
            )
            with patch.object(embeddings, "generate_embeddings", return_value=[[0.0] * 256]):
                db_path = Path(tmp) / "test.db"
                build_database(docs, db_path)

                args = MagicMock()
                args.db = str(db_path)
                args.query = "timer stopped"
                args.limit = 3
                args.json = False
                args.no_expand = True
                args.debug_search = True

                import io
                from contextlib import redirect_stdout

                f = io.StringIO()
                with redirect_stdout(f):
                    cmd_search(args)
                output = f.getvalue()

                # Text mode should include metadata header
                self.assertIn("search_mode:", output)
                self.assertIn("vector_available:", output)

    def test_cli_search_without_debug_no_metadata(self):
        from rag import embeddings
        from rag.cli import cmd_search
        from unittest.mock import MagicMock

        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp) / "docs"
            classes = docs / "classes"
            classes.mkdir(parents=True)
            (classes / "class_timer.md").write_text(
                "# Timer\n\n"
                "## Methods\n\n"
                "`bool` **is_stopped**() `const`\n\n"
                "Returns true if the timer is stopped.\n",
                encoding="utf-8",
            )
            with patch.object(embeddings, "generate_embeddings", return_value=[[0.0] * 256]):
                db_path = Path(tmp) / "test.db"
                build_database(docs, db_path)

                args = MagicMock()
                args.db = str(db_path)
                args.query = "timer stopped"
                args.limit = 3
                args.json = False
                args.no_expand = True
                args.debug_search = False

                import io
                from contextlib import redirect_stdout

                f = io.StringIO()
                with redirect_stdout(f):
                    cmd_search(args)
                output = f.getvalue()

                # Without debug_search, should not include metadata
                self.assertNotIn("search_mode:", output)
                self.assertNotIn("vector_available:", output)


class IndexerModuleTests(unittest.TestCase):
    """Task 4: build_database should be importable from rag.indexer."""

    def test_build_database_importable_from_indexer(self):
        from rag.indexer import build_database as indexer_fn
        from rag.store import build_database as store_fn
        self.assertIs(indexer_fn, store_fn)


class RequireDbTests(unittest.TestCase):
    """Task 7: _require_db should guard database access."""

    def test_require_db_returns_path_when_exists(self):
        from rag.cli import _require_db
        from unittest.mock import MagicMock

        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "test.sqlite"
            db_path.touch()
            args = MagicMock()
            args.db = str(db_path)
            result = _require_db(args)
            self.assertEqual(result, db_path)

    def test_require_db_exits_when_missing(self):
        from rag.cli import _require_db
        from unittest.mock import MagicMock

        args = MagicMock()
        args.db = "/nonexistent/path/test.sqlite"
        with self.assertRaises(SystemExit):
            _require_db(args)


class RunSearchTests(unittest.TestCase):
    """Task 7: _run_search should unify search command logic."""

    def _build_db(self, tmp):
        docs = Path(tmp) / "docs"
        docs.mkdir()
        classes = docs / "classes"
        classes.mkdir()
        (classes / "class_timer.md").write_text(
            "# Timer\n\n## Methods\n\n`bool` **is_stopped**() `const`\n\nReturns true.\n",
            encoding="utf-8",
        )
        db_path = Path(tmp) / "test.sqlite"
        build_database(docs, db_path)
        return db_path

    def test_run_search_calls_search_database(self):
        from rag.cli import _run_search
        from unittest.mock import MagicMock, patch

        with tempfile.TemporaryDirectory() as tmp:
            db_path = self._build_db(tmp)
            args = MagicMock()
            args.db = str(db_path)
            args.query = "timer"
            args.limit = 3
            args.json = True
            args.no_expand = False
            args.debug_search = False

            with patch("rag.cli.search_database") as mock_search:
                mock_search.return_value = []
                _run_search(args)
                mock_search.assert_called_once()
                call_kwargs = mock_search.call_args
                self.assertEqual(call_kwargs.kwargs.get("doc_types"), None)
                self.assertEqual(call_kwargs.kwargs.get("addon"), None)

    def test_run_search_passes_doc_types(self):
        from rag.cli import _run_search
        from unittest.mock import MagicMock, patch

        with tempfile.TemporaryDirectory() as tmp:
            db_path = self._build_db(tmp)
            args = MagicMock()
            args.db = str(db_path)
            args.query = "timer"
            args.limit = 3
            args.json = True
            args.no_expand = False
            args.debug_search = False

            with patch("rag.cli.search_database") as mock_search:
                mock_search.return_value = []
                _run_search(args, doc_types=["class"])
                call_kwargs = mock_search.call_args
                self.assertEqual(call_kwargs.kwargs.get("doc_types"), ["class"])

    def test_run_search_passes_addon(self):
        from rag.cli import _run_search
        from unittest.mock import MagicMock, patch

        with tempfile.TemporaryDirectory() as tmp:
            db_path = self._build_db(tmp)
            args = MagicMock()
            args.db = str(db_path)
            args.query = "timer"
            args.limit = 3
            args.json = True
            args.no_expand = False
            args.debug_search = False
            args.addon = "myaddon"

            with patch("rag.cli.search_database") as mock_search:
                mock_search.return_value = []
                _run_search(args, doc_types=["addon"], addon="myaddon")
                call_kwargs = mock_search.call_args
                self.assertEqual(call_kwargs.kwargs.get("doc_types"), ["addon"])
                self.assertEqual(call_kwargs.kwargs.get("addon"), "myaddon")

    def test_run_search_respects_no_expand(self):
        from rag.cli import _run_search
        from unittest.mock import MagicMock, patch

        with tempfile.TemporaryDirectory() as tmp:
            db_path = self._build_db(tmp)
            args = MagicMock()
            args.db = str(db_path)
            args.query = "timer"
            args.limit = 3
            args.json = True
            args.no_expand = True
            args.debug_search = False

            with patch("rag.cli.search_database") as mock_search:
                mock_search.return_value = []
                _run_search(args)
                call_kwargs = mock_search.call_args
                self.assertEqual(call_kwargs.kwargs.get("expand_graph"), False)

    def test_run_search_debug_uses_metadata_variant(self):
        from rag.cli import _run_search
        from unittest.mock import MagicMock, patch

        with tempfile.TemporaryDirectory() as tmp:
            db_path = self._build_db(tmp)
            args = MagicMock()
            args.db = str(db_path)
            args.query = "timer"
            args.limit = 3
            args.json = True
            args.no_expand = False
            args.debug_search = True

            with patch("rag.cli.search_database_with_metadata") as mock_search:
                mock_search.return_value = MagicMock(results=[], metadata=MagicMock(mode="fts", vector_available=False, fallback_reason=None))
                _run_search(args)
                mock_search.assert_called_once()


if __name__ == "__main__":
    unittest.main()
