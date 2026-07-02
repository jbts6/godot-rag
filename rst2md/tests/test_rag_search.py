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

    def test_natural_language_alias_returns_expected_symbol(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp) / "docs"
            classes = docs / "classes"
            classes.mkdir(parents=True)
            (classes / "class_node.md").write_text(
                "# Node\n\n"
                "## Methods\n\n"
                "`void` **add_child**(`Node` node)\n\n"
                "Adds a child node to the scene tree.\n",
                encoding="utf-8",
            )
            db_path = Path(tmp) / "godot_docs.sqlite"
            build_database(docs, db_path)

            results = search_database(db_path, "attach node to scene tree", limit=3, expand_graph=False)

            self.assertTrue(results)
            self.assertEqual(results[0].symbol, "Node.add_child")


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


class RankingSignalTests(unittest.TestCase):
    """RankingSignal model and SearchResult additive field."""

    def test_ranking_signal_defaults(self):
        from rag.models import RankingSignal

        signal = RankingSignal(name="symbol_recall.exact", weight=100.0)
        self.assertEqual(signal.name, "symbol_recall.exact")
        self.assertEqual(signal.weight, 100.0)
        self.assertIsNone(signal.value)
        self.assertEqual(signal.details, {})

    def test_ranking_signal_details_not_shared_across_instances(self):
        from rag.models import RankingSignal

        a = RankingSignal(name="x", weight=1.0)
        b = RankingSignal(name="y", weight=2.0)
        a.details["k"] = "v"
        self.assertNotIn("k", b.details, "details dict must not be shared across instances")

    def test_search_result_ranking_signals_default_empty(self):
        from rag.models import SearchResult

        result = SearchResult(
            score=1.0, path="p", start_line=1, end_line=2,
            doc_type="class", chunk_type="method", addon="", addon_name="",
            symbol="X", heading="h", breadcrumb="b", text="t",
        )
        self.assertEqual(result.ranking_signals, [])

    def test_search_result_positional_construction_still_works(self):
        """Existing positional construction must stay source-compatible."""
        from rag.models import SearchResult

        result = SearchResult(
            1.0, "p", 1, 2, "class", "method", "", "", "X", "h", "b", "t",
        )
        self.assertEqual(result.score, 1.0)
        self.assertEqual(result.snippet, "")
        self.assertEqual(result.ranking_signals, [])


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

    def test_cli_search_debug_json_includes_ranking_signals(self):
        from rag import embeddings
        from rag.cli import cmd_search
        from unittest.mock import MagicMock

        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp) / "docs"
            classes = docs / "classes"
            classes.mkdir(parents=True)
            (classes / "class_timer.md").write_text(
                "# Timer\n\n## Methods\n\n"
                "`bool` **is_stopped**() `const`\n\nReturns true if the timer is stopped.\n",
                encoding="utf-8",
            )
            with patch.object(embeddings, "generate_embeddings", return_value=[[0.0] * 256]):
                db_path = Path(tmp) / "test.db"
                build_database(docs, db_path)
                args = MagicMock()
                args.db = str(db_path)
                args.query = "Timer.is_stopped"
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

            self.assertIn("results", output)
            self.assertTrue(output["results"], "should have at least one result")
            top = output["results"][0]
            self.assertIn("ranking_signals", top)
            self.assertIsInstance(top["ranking_signals"], list)
            self.assertTrue(top["ranking_signals"], "top result should have ranking signals")
            sig = top["ranking_signals"][0]
            self.assertIn("name", sig)
            self.assertIn("weight", sig)
            self.assertIn("details", sig)

    def test_cli_search_debug_text_includes_signal_summary(self):
        from rag.cli import cmd_search
        from unittest.mock import MagicMock

        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp) / "docs"
            classes = docs / "classes"
            classes.mkdir(parents=True)
            (classes / "class_timer.md").write_text(
                "# Timer\n\n## Methods\n\n"
                "`bool` **is_stopped**() `const`\n\nReturns true.\n",
                encoding="utf-8",
            )
            db_path = Path(tmp) / "test.db"
            build_database(docs, db_path)
            args = MagicMock()
            args.db = str(db_path)
            args.query = "Timer.is_stopped"
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

            self.assertIn("signals:", output, "debug text output should include a signals summary line")

    def test_cli_search_default_text_omits_signals(self):
        """OpenSpec 4.2: default (non-debug) text output must not print signals."""
        from rag.cli import cmd_search
        from unittest.mock import MagicMock

        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp) / "docs"
            classes = docs / "classes"
            classes.mkdir(parents=True)
            (classes / "class_timer.md").write_text(
                "# Timer\n\n## Methods\n\n"
                "`bool` **is_stopped**() `const`\n\nReturns true.\n",
                encoding="utf-8",
            )
            db_path = Path(tmp) / "test.db"
            build_database(docs, db_path)
            args = MagicMock()
            args.db = str(db_path)
            args.query = "Timer.is_stopped"
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

            self.assertNotIn("signals:", output, "default text output must not print signal payload")


class IntentBoostTests(unittest.TestCase):
    """Tutorial-intent queries should boost tutorial doc_type results."""

    def test_how_to_query_prefers_tutorial_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp) / "docs"
            classes = docs / "classes"
            tutorials = docs / "tutorials"
            classes.mkdir(parents=True)
            tutorials.mkdir(parents=True)
            (classes / "class_animation.md").write_text(
                "# Animation\n\nScene tree nodes can be animated from code.\n",
                encoding="utf-8",
            )
            (tutorials / "scene_tree.md").write_text(
                "# Scene tree\n\nHow to use scene tree nodes and attach child nodes.\n",
                encoding="utf-8",
            )
            db_path = Path(tmp) / "godot_docs.sqlite"
            build_database(docs, db_path)

            results = search_database(db_path, "how to use scene tree nodes", limit=3, expand_graph=False)

            self.assertTrue(results)
            self.assertEqual(results[0].doc_type, "tutorial")
            self.assertEqual(results[0].path, "tutorials/scene_tree.md")


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


class SymbolRecallSignalTests(unittest.TestCase):
    """Symbol recall stages should record named ranking signals."""

    def _build_db(self, tmp):
        docs = Path(tmp) / "docs"
        classes = docs / "classes"
        classes.mkdir(parents=True)
        (classes / "class_node.md").write_text(
            "# Node\n\nBase class.\n\n## Methods\n\n"
            "`void` **add_child**(`Node` node)\n\nAdds a child node.\n",
            encoding="utf-8",
        )
        db_path = Path(tmp) / "test.sqlite"
        build_database(docs, db_path)
        return db_path

    def test_exact_symbol_match_records_signal(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = self._build_db(tmp)
            results = search_database(db_path, "Node.add_child", limit=3, expand_graph=False)
            self.assertTrue(results)
            top = results[0]
            self.assertEqual(top.symbol, "Node.add_child")
            names = [s.name for s in top.ranking_signals]
            self.assertIn("symbol_recall.exact", names)
            exact = next(s for s in top.ranking_signals if s.name == "symbol_recall.exact")
            self.assertEqual(exact.weight, 100.0)

    def test_suffix_symbol_match_records_signal(self):
        """Suffix-recall tier fires for dot-notation symbols.

        _canonical_form (rst2md/rag/symbols.py) preserves the dot boundary, so
        an indexed `Node.add_child` symbol has normalized form `node.addchild`.
        Querying `add_child` (normalized `addchild`) hits the suffix LIKE
        pattern `%.addchild`, which matches `node.addchild` — the suffix tier
        fires and records a `symbol_recall.suffix` signal.
        """
        with tempfile.TemporaryDirectory() as tmp:
            db_path = self._build_db(tmp)
            results = search_database(db_path, "add_child", limit=3, expand_graph=False)
            self.assertTrue(results)
            top = results[0]
            self.assertEqual(top.symbol, "Node.add_child")
            names = [s.name for s in top.ranking_signals]
            self.assertIn("symbol_recall.suffix", names)
            suffix = next(s for s in top.ranking_signals if s.name == "symbol_recall.suffix")
            self.assertEqual(suffix.weight, 80.0)

    def test_prefix_symbol_match_records_signal(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = self._build_db(tmp)
            results = search_database(db_path, "Node", limit=10, expand_graph=False)
            method = next((r for r in results if r.symbol == "Node.add_child"), None)
            self.assertIsNotNone(method, "Node.add_child should be found via prefix symbol match")
            names = [s.name for s in method.ranking_signals]
            self.assertIn("symbol_recall.prefix", names)
            prefix = next(s for s in method.ranking_signals if s.name == "symbol_recall.prefix")
            self.assertEqual(prefix.weight, 40.0)

    def test_alias_derived_match_sets_alias_detail(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = self._build_db(tmp)
            results = search_database(
                db_path, "attach node to scene tree", limit=3, expand_graph=False
            )
            self.assertTrue(results)
            top = results[0]
            self.assertEqual(top.symbol, "Node.add_child")
            exact = next(
                (s for s in top.ranking_signals if s.name == "symbol_recall.exact"), None
            )
            self.assertIsNotNone(
                exact, "alias-derived exact match should still record symbol_recall.exact"
            )
            self.assertTrue(
                exact.details.get("alias_derived"),
                "alias-derived match should set details.alias_derived=True",
            )


class HybridRrfSignalTests(unittest.TestCase):
    """Hybrid RRF and FTS fallback stages should record signals."""

    def test_fts_fallback_records_bm25_signal(self):
        from rag import embeddings
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp) / "docs"
            classes = docs / "classes"
            classes.mkdir(parents=True)
            (classes / "class_timer.md").write_text(
                "# Timer\n\n## Methods\n\n"
                "`bool` **is_stopped**() `const`\n\nReturns true if the timer is stopped.\n",
                encoding="utf-8",
            )
            db_path = Path(tmp) / "test.sqlite"
            # Disable vector support (empty vec_chunks) so FTS is the scoring
            # path that introduces the candidate, regardless of whether the
            # embedding model / sqlite-vec happen to be installed locally.
            with patch.object(embeddings, "generate_embeddings", lambda texts: []):
                build_database(docs, db_path)
                results = search_database(db_path, "stopped timer", limit=3, expand_graph=False)
            self.assertTrue(results)
            has_fts = any(
                s.name == "fts.bm25" for r in results for s in r.ranking_signals
            )
            self.assertTrue(has_fts, "FTS fallback should record fts.bm25 signal")

    def test_hybrid_rrf_records_signal_when_vector_available(self):
        from rag import embeddings
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp) / "docs"
            classes = docs / "classes"
            classes.mkdir(parents=True)
            (classes / "class_timer.md").write_text(
                "# Timer\n\n## Methods\n\n"
                "`bool` **is_stopped**() `const`\n\nReturns true if the timer is stopped.\n",
                encoding="utf-8",
            )
            db_path = Path(tmp) / "test.sqlite"
            # Return one zero-vector per input text so vec_chunks row count
            # matches chunks (parity required for _vector_availability=True).
            with patch.object(
                embeddings, "generate_embeddings",
                lambda texts: [[0.0] * 256 for _ in texts],
            ):
                build_database(docs, db_path)
                results = search_database(db_path, "timer stopped", limit=3, expand_graph=False)
            self.assertTrue(results)
            has_rrf = any(
                s.name == "hybrid.rrf" for r in results for s in r.ranking_signals
            )
            self.assertTrue(has_rrf, "Hybrid mode should record hybrid.rrf signal")

    def test_symbol_recall_preserves_prior_rrf_signal(self):
        """OpenSpec 2.4: when symbol recall improves an RRF-found candidate,
        the prior hybrid.rrf signal must survive the replacement."""
        import sqlite3
        from rag import embeddings
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp) / "docs"
            classes = docs / "classes"
            classes.mkdir(parents=True)
            (classes / "class_timer.md").write_text(
                "# Timer\n\n## Methods\n\n"
                "`bool` **is_stopped**() `const`\n\nReturns true.\n",
                encoding="utf-8",
            )
            db_path = Path(tmp) / "test.sqlite"
            # Return one zero-vector per input text so vec_chunks row count
            # matches chunks (parity required for _vector_availability=True).
            with patch.object(
                embeddings, "generate_embeddings",
                lambda texts: [[0.0] * 256 for _ in texts],
            ):
                build_database(docs, db_path)
                conn = sqlite3.connect(str(db_path))
                cid = conn.execute(
                    "SELECT id FROM chunks WHERE symbol='Timer.is_stopped'"
                ).fetchone()[0]
                conn.close()
                # Force RRF to surface the Timer.is_stopped chunk; symbol recall
                # will then promote it from a low RRF score to exact (100).
                with patch("rag.searcher.rrf_fusion", return_value=[{"id": cid, "rrf_score": 0.5}]):
                    results = search_database(
                        db_path, "Timer.is_stopped", limit=3, expand_graph=False
                    )
            top = results[0]
            self.assertEqual(top.symbol, "Timer.is_stopped")
            names = {s.name for s in top.ranking_signals}
            self.assertIn("hybrid.rrf", names, "prior RRF signal must survive symbol-recall replacement")
            self.assertIn("symbol_recall.exact", names)


class GraphExpansionSignalTests(unittest.TestCase):
    """Graph expansion should record signals and preserve prior signals."""

    def test_new_graph_chunk_records_expansion_signal(self):
        from rag import embeddings
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp) / "docs"
            classes = docs / "classes"
            classes.mkdir(parents=True)
            # The Node class_summary text contains the query term "node" so FTS
            # (and exact symbol recall) finds it; its `inherits` edge targets
            # Object, whose text does NOT contain the query term, so Object is
            # only reached via graph expansion (new-chunk branch). Timer and
            # Sprite are unrelated filler so the doc set has >=4 chunks.
            (classes / "class_node.md").write_text(
                "# Node\n\nBase class for scene nodes.\n\n**Inherits:** `Object`\n\n"
                "## Methods\n\n`void` **add_child**(`Node` node)\n\nAdds a child.\n",
                encoding="utf-8",
            )
            (classes / "class_object.md").write_text(
                "# Object\n\nRoot of all things.\n",
                encoding="utf-8",
            )
            (classes / "class_timer.md").write_text(
                "# Timer\n\nA countdown timer.\n",
                encoding="utf-8",
            )
            (classes / "class_sprite.md").write_text(
                "# Sprite\n\nA 2D texture.\n",
                encoding="utf-8",
            )
            db_path = Path(tmp) / "test.sqlite"
            # Disable vectors so RRF does not surface every chunk at distance=0;
            # FTS-only mode keeps Object out of results until graph expansion.
            with patch.object(embeddings, "generate_embeddings", lambda texts: []):
                build_database(docs, db_path)
                results = search_database(db_path, "node", limit=10, expand_graph=True)
            # Object class_summary is reached only via graph expansion (inherits).
            obj = next((r for r in results if r.symbol == "Object"), None)
            self.assertIsNotNone(obj, "Object should be reached via graph expansion")
            names = [s.name for s in obj.ranking_signals]
            self.assertIn("graph.expansion", names)
            graph_sig = next(s for s in obj.ranking_signals if s.name == "graph.expansion")
            self.assertEqual(graph_sig.details.get("relation"), "inherits")
            self.assertEqual(graph_sig.details.get("distance"), 1)

    def test_graph_expansion_preserves_prior_fts_signal(self):
        """OpenSpec 2.4: a chunk found by FTS and then reached via graph
        expansion must carry both its fts.bm25 signal and graph.expansion."""
        from rag import embeddings
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp) / "docs"
            classes = docs / "classes"
            classes.mkdir(parents=True)
            # The alias rule {child, node, attach} -> "Node.add_child" makes the
            # method an exact symbol match (score 100, in top_k). The
            # class_summaries FTS-match "attach child node" (fts.bm25, ~40);
            # the short Node summary is the strongest bm25 match so its
            # inverted fts_score is lowest, landing it OUTSIDE top_k=3 (the
            # method + Timer + Sprite occupy top_k). The method's `parent`
            # edge -> Node summary then hits the existing-chunk branch:
            # graph.expansion (metadata_only=True) is appended while fts.bm25
            # is preserved.
            (classes / "class_node.md").write_text(
                "# Node\n\nAttach child node.\n\n"
                "## Methods\n\n`void` **add_child**(`Node` node)\n\n"
                "Adds a child node to the parent.\n",
                encoding="utf-8",
            )
            (classes / "class_timer.md").write_text(
                "# Timer\n\nA countdown timer that can attach a child node "
                "for scheduling nested timer callbacks within the scene tree "
                "management system.\n",
                encoding="utf-8",
            )
            (classes / "class_sprite.md").write_text(
                "# Sprite\n\nA two dimensional texture that can attach a child "
                "node for rendering nested sprites within the scene graph "
                "hierarchy.\n",
                encoding="utf-8",
            )
            db_path = Path(tmp) / "test.sqlite"
            # Disable vectors so the summaries get fts.bm25 (not hybrid.rrf).
            with patch.object(embeddings, "generate_embeddings", lambda texts: []):
                build_database(docs, db_path)
                results = search_database(db_path, "attach child node", limit=10, expand_graph=True)
            summary = next((r for r in results if r.symbol == "Node"), None)
            self.assertIsNotNone(summary, "Node class_summary should be in results")
            names = {s.name for s in summary.ranking_signals}
            self.assertIn("fts.bm25", names, "prior FTS signal must survive graph expansion")
            self.assertIn("graph.expansion", names, "graph expansion should append its own signal")
            graph_sig = next(s for s in summary.ranking_signals if s.name == "graph.expansion")
            self.assertTrue(graph_sig.details.get("metadata_only"), "existing-chunk branch should set metadata_only=True")


class RankingSignalCoverageTests(unittest.TestCase):
    """OpenSpec 5.1: ranking-signal family coverage guards.

    Each family must be observable somewhere in the suite. The core families
    reachable via search_database() are checked in
    test_core_signal_families_observable_via_search_database; families that
    require a direct rerank_results() call (or are dead code) are verified in
    their own tests and documented there.
    """

    def _build_db(self, tmp, with_vectors=False):
        from rag import embeddings
        docs = Path(tmp) / "docs"
        classes = docs / "classes"
        classes.mkdir(parents=True, exist_ok=True)
        (classes / "class_node.md").write_text(
            "# Node\n\nBase class. Node has an add_child method.\n\n"
            "**Inherits:** `Object`\n\n"
            "## Methods\n\n"
            "`void` **add_child**(`Node` node)\n\nAdds a child.\n",
            encoding="utf-8",
        )
        (classes / "class_object.md").write_text(
            "# Object\n\nBase of all classes.\n",
            encoding="utf-8",
        )
        # Empty embeddings (with_vectors=False) → FTS-only mode: fts.bm25
        # (FTS section-4 fallback) and graph.expansion (new-chunk branch)
        # are observable. With vectors populated, hybrid.rrf returns every
        # fixture chunk, which (a) makes FTS section-4 exclude them and (b)
        # puts all chunks in the graph top-K so no new chunk is discovered.
        # Zero-vector embeddings (with_vectors=True) populate vec_chunks so
        # _vector_availability is True and hybrid.rrf fires. A separate
        # filename avoids clobbering the FTS-only DB. Matches
        # test_graph_expansion_preserves_prior_fts_signal for determinism.
        db_path = Path(tmp) / ("test_hybrid.sqlite" if with_vectors else "test.sqlite")
        emb_fn = (lambda texts: [[0.0] * 256 for _ in texts]) if with_vectors else (lambda texts: [])
        with patch.object(embeddings, "generate_embeddings", emb_fn):
            build_database(docs, db_path)
        return db_path

    def test_core_signal_families_observable_via_search_database(self):
        """Coverage guard: signal families reachable via search_database() on
        this fixture must all appear in the observed set.

        Families in `required` (verified here via search_database):
          - symbol_recall.exact / .prefix  (symbol-candidate queries)
          - fts.bm25                        (FTS fallback, FTS-only DB)
          - graph.expansion                 (expand_graph=True)
          - rerank.direct_symbol            (query "Node.add_child")
          - rerank.alias_symbol             (query "attach node to scene tree"
                                             → _ALIAS_RULE → Node.add_child)
          - hybrid.rrf                      (separate DB built with vectors)

        Families verified elsewhere (not in `required`):
          - rerank.doc_type_intent: not exercised by this test's query set
            (no "how to..." / tutorial-intent queries here). Verified directly
            via test_rerank_appends_doc_type_intent_signal and
            test_rerank_bonus_equals_signal_weight_sum_doc_type_intent
            (test_searcher_module.py).
          - rerank.addon_intent: the bare fixture has no addon docs, so the
            addon-intent rerank path is not reachable via search_database()
            here. Verified via direct rerank_results() in
            test_addon_intent_signal_observable_via_rerank.
          - symbol_recall.suffix: fires for the `add_child` query against the
            indexed `Node.add_child` symbol (normalized `node.addchild` matches
            the suffix LIKE `%.addchild`); see
            test_suffix_symbol_match_records_signal.
        """
        observed: set[str] = set()
        with tempfile.TemporaryDirectory() as tmp:
            # FTS-only DB: symbol recall, FTS fallback, graph expansion,
            # rerank.direct_symbol + rerank.alias_symbol.
            db_path = self._build_db(tmp)
            for q in ("Node.add_child", "add_child", "Node"):
                for r in search_database(db_path, q, limit=10, expand_graph=False):
                    observed.update(s.name for s in r.ranking_signals)
            # Alias-derived symbol match → rerank.alias_symbol.
            for r in search_database(db_path, "attach node to scene tree", limit=10, expand_graph=False):
                observed.update(s.name for s in r.ranking_signals)
            # FTS fallback.
            for r in search_database(db_path, "base class", limit=10, expand_graph=False):
                observed.update(s.name for s in r.ranking_signals)
            # Graph expansion (new + existing chunk branches).
            for r in search_database(db_path, "add child", limit=10, expand_graph=True):
                observed.update(s.name for s in r.ranking_signals)
            # Hybrid RRF — needs a DB with vec_chunks populated. The FTS-only
            # DB above has empty vec_chunks, so _vector_availability is False
            # and RRF never fires regardless of any search-time embedding patch
            # (the build-time embedding is what populates vec_chunks).
            hybrid_db = self._build_db(tmp, with_vectors=True)
            for r in search_database(hybrid_db, "node add_child", limit=10, expand_graph=False):
                observed.update(s.name for s in r.ranking_signals)

        required = {
            "symbol_recall.exact",
            "symbol_recall.prefix",
            "symbol_recall.suffix",
            "fts.bm25",
            "graph.expansion",
            "rerank.direct_symbol",
            "rerank.alias_symbol",
            "hybrid.rrf",
        }
        missing = required - observed
        self.assertFalse(missing, f"missing signal families: {sorted(missing)}")

    def test_addon_intent_signal_observable_via_rerank(self):
        """Verify rerank.addon_intent via a direct rerank_results() call.

        The bare fixture has no addon docs, so the addon-intent rerank path is
        not reachable via search_database() here. This exercises the signal
        directly via rerank_results() (the production rerank entry point) with
        a synthetic addon SearchResult.
        """
        from rag.models import SearchResult
        from rag.query_plan import build_query_plan
        from rag.fusion import rerank_results

        plan = build_query_plan("dialogue manager addon")
        addon_result = SearchResult(
            score=1.0, path="addons/dm/docs.md", start_line=1, end_line=2,
            doc_type="addon", chunk_type="section", addon="dm", addon_name="DM",
            symbol="", heading="Dialogue", breadcrumb="Addon",
            text="A dialogue addon.",
        )
        ranked = rerank_results(plan, [addon_result])
        names = {s.name for s in ranked[0].ranking_signals}
        self.assertIn("rerank.addon_intent", names)


class BuildChunkRelationsCoverageTests(unittest.TestCase):
    """Direct unit coverage for rag.relations.build_chunk_relations.

    Existing ChunkRelationTests exercise build_chunk_relations indirectly via
    build_database; this class calls it directly on a hand-built DB to pin the
    exact inherits row (source, target, relation, weight=0.8).
    """

    def _build_db(self, docs_text_map):
        import sqlite3
        import tempfile
        from rag.db import SCHEMA
        tmp = tempfile.mkdtemp()
        db_path = os.path.join(tmp, "t.sqlite")
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        conn.executescript(SCHEMA)
        for path, (doc_type, chunk_type, symbol, parent_symbol, text) in docs_text_map.items():
            cur = conn.execute(
                "INSERT INTO documents (path, doc_type, title) VALUES (?, ?, ?)",
                (path, doc_type, symbol or path),
            )
            doc_id = cur.lastrowid
            conn.execute(
                "INSERT INTO chunks (document_id, path, doc_type, chunk_type, symbol, parent_symbol, text, start_line, end_line) "
                "VALUES (?,?,?,?,?,?,?,1,10)",
                (doc_id, path, doc_type, chunk_type, symbol, parent_symbol, text),
            )
        conn.commit()
        return conn

    def test_inherits_relation_created_for_class_summary(self):
        from rag.relations import build_chunk_relations
        conn = self._build_db({
            "classes/class_node.md": ("class", "class_summary", "Node", "", "**Inherits:** `Object`"),
            "classes/class_object.md": ("class", "class_summary", "Object", "", "Root of all things."),
        })
        build_chunk_relations(conn)
        row = conn.execute(
            "SELECT source_id, target_id, relation, weight FROM chunk_relations WHERE relation='inherits'"
        ).fetchone()
        self.assertIsNotNone(row, "inherits relation should exist")
        self.assertEqual(row["relation"], "inherits")
        self.assertAlmostEqual(row["weight"], 0.8)


class InheritsGraphTraversalTests(unittest.TestCase):
    def test_node_inherits_object_reaches_object_class_summary(self):
        from rag import embeddings
        from unittest.mock import patch
        from rag.indexer import build_database
        from rag.searcher import search_database

        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp) / "docs"
            classes = docs / "classes"
            classes.mkdir(parents=True)
            (classes / "class_node.md").write_text(
                "# Node\n\nBase class.\n\n**Inherits:** `Object`\n\n",
                encoding="utf-8",
            )
            (classes / "class_object.md").write_text(
                "# Object\n\nRoot of all things.\n\n",
                encoding="utf-8",
            )
            (classes / "class_timer.md").write_text(
                "# Timer\n\nA countdown timer.\n", encoding="utf-8",
            )
            db_path = Path(tmp) / "t.sqlite"
            with patch.object(embeddings, "generate_embeddings", lambda texts: []):
                build_database(docs, db_path)
                results = search_database(db_path, "Node inherits Object", limit=10, expand_graph=True)
            obj = next((r for r in results if r.symbol == "Object"), None)
            self.assertIsNotNone(obj, "Object class_summary should be reached via inherits traversal")
            rank = results.index(obj) + 1
            self.assertLessEqual(rank, 5, f"Object rank {rank} should be <= 5")
            names = [s.name for s in obj.ranking_signals]
            self.assertIn("graph.inherits", names)


class InheritanceRecallTests(unittest.TestCase):
    """Step 3.5 inheritance-directed class_summary recall.

    Reproduces the production gap: query ``Node inherits Object`` floods FTS
    top_k with noise class_summary chunks (each inheritance chain mentions
    Node and Object), leaving Node's class_summary out of the candidate set
    so the inherits traversal at searcher.py:384 never fires and Object is
    never recalled. Step 3.5 recalls Node's class_summary directly so it
    enters top_k and the traversal can pull Object via the inherits edge.
    """

    def _build_db_with_noise(self, tmp):
        from rag import embeddings
        from unittest.mock import patch
        from rag.indexer import build_database

        docs = Path(tmp) / "docs"
        classes = docs / "classes"
        classes.mkdir(parents=True)
        (classes / "class_node.md").write_text(
            "# Node\n\nBase class for scene nodes.\n\n**Inherits:** `Object`\n\n",
            encoding="utf-8",
        )
        (classes / "class_object.md").write_text(
            "# Object\n\nRoot of all things.\n\n",
            encoding="utf-8",
        )
        # Noise class_summary chunks whose inheritance-chain text mentions both
        # Node and Object, so they match the FTS query "Node inherits Object"
        # and flood top_k=3, reproducing the production gap.
        (classes / "class_scrollbar.md").write_text(
            "# ScrollBar\n\nA scrollbar control.\n\n"
            "**Inherits:** `Range` **<** `Control` **<** `CanvasItem` **<** `Node` **<** `Object`\n\n",
            encoding="utf-8",
        )
        (classes / "class_slider.md").write_text(
            "# Slider\n\nA slider control.\n\n"
            "**Inherits:** `Range` **<** `Control` **<** `CanvasItem` **<** `Node` **<** `Object`\n\n",
            encoding="utf-8",
        )
        (classes / "class_popuppanel.md").write_text(
            "# PopupPanel\n\nA popup container.\n\n"
            "**Inherits:** `Window` **<** `Viewport` **<** `Node` **<** `Object`\n\n",
            encoding="utf-8",
        )
        db_path = Path(tmp) / "t.sqlite"
        # Disable vectors (empty embeddings list) so the search runs in
        # FTS-only mode and the FTS-cap-at-40 tie dynamics match the gap.
        with patch.object(embeddings, "generate_embeddings", lambda texts: []):
            build_database(docs, db_path)
        return db_path

    def test_inheritance_recall_pulls_class_summary_into_top_k(self):
        from rag.searcher import search_database

        with tempfile.TemporaryDirectory() as tmp:
            db_path = self._build_db_with_noise(tmp)
            results = search_database(
                db_path, "Node inherits Object", limit=5, expand_graph=True,
            )
        symbols = [r.symbol for r in results]
        self.assertIn(
            "Node", symbols,
            "Node class_summary should be recalled into top-5 by step 3.5",
        )
        self.assertIn(
            "Object", symbols,
            "Object class_summary should be reached (via step 3.5 recall or inherits traversal)",
        )
        node = next(r for r in results if r.symbol == "Node")
        names = [s.name for s in node.ranking_signals]
        self.assertIn(
            "inheritance_recall.class_summary", names,
            "Node must carry the inheritance_recall.class_summary signal (D3)",
        )


if __name__ == "__main__":
    unittest.main()
