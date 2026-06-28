"""TDD test: search functions should be importable from rag.searcher."""

import unittest


class SearcherModuleImportTests(unittest.TestCase):
    """Verify that search functions are importable from rag.searcher."""

    def test_import_smart_tokenize(self):
        from rag.searcher import _smart_tokenize
        self.assertTrue(callable(_smart_tokenize))

    def test_import_escape_fts5(self):
        from rag.searcher import _escape_fts5
        self.assertTrue(callable(_escape_fts5))

    def test_import_vector_search(self):
        from rag.searcher import vector_search
        self.assertTrue(callable(vector_search))

    def test_import_rrf_fusion(self):
        from rag.searcher import rrf_fusion
        self.assertTrue(callable(rrf_fusion))

    def test_import_search_database(self):
        from rag.searcher import search_database
        self.assertTrue(callable(search_database))

    def test_import_search_database_with_metadata(self):
        from rag.searcher import search_database_with_metadata
        self.assertTrue(callable(search_database_with_metadata))

    def test_import_extract_snippet(self):
        from rag.searcher import _extract_snippet
        self.assertTrue(callable(_extract_snippet))

    def test_import_vector_availability(self):
        from rag.searcher import _vector_availability
        self.assertTrue(callable(_vector_availability))

    def test_import_run_vector_query(self):
        from rag.searcher import _run_vector_query
        self.assertTrue(callable(_run_vector_query))

    def test_import_fts5_special(self):
        from rag.searcher import _FTS5_SPECIAL
        self.assertIsInstance(_FTS5_SPECIAL, set)

    def test_import_search_database_impl(self):
        from rag.searcher import _search_database_impl
        self.assertTrue(callable(_search_database_impl))

    def test_rrf_fusion_basic(self):
        from rag.searcher import rrf_fusion
        fts = [{'id': 1}, {'id': 2}]
        vec = [{'id': 2, 'distance': 0.1}, {'id': 3, 'distance': 0.2}]
        fused = rrf_fusion(fts, vec, k=60)
        self.assertEqual(len(fused), 3)
        self.assertEqual(fused[0]['id'], 2)
        self.assertIn('rrf_score', fused[0])


if __name__ == "__main__":
    unittest.main()
