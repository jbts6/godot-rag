import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from rag.chunker import chunk_markdown
from rag.store import build_database, search_database


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


class CliTests(unittest.TestCase):
    def test_cli_help_runs(self):
        result = subprocess.run(
            [sys.executable, "-m", "rag.cli", "--help"],
            text=True,
            capture_output=True,
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("build", result.stdout)
        self.assertIn("s", result.stdout)

    def test_cli_search_class_help(self):
        result = subprocess.run(
            [sys.executable, "-m", "rag.cli", "s-class", "--help"],
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("query", result.stdout)

    def test_cli_search_tutorial_help(self):
        result = subprocess.run(
            [sys.executable, "-m", "rag.cli", "s-tutorial", "--help"],
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("query", result.stdout)

    def test_cli_search_engine_help(self):
        result = subprocess.run(
            [sys.executable, "-m", "rag.cli", "s-engine", "--help"],
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("query", result.stdout)


if __name__ == "__main__":
    unittest.main()
