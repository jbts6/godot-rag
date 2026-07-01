"""TDD test: search functions are importable from focused modules and facade."""

import unittest


class SearcherModuleImportTests(unittest.TestCase):
    """Verify search functions are importable from focused modules and legacy facade."""

    def test_import_smart_tokenize(self):
        from rag.retrieval import _smart_tokenize
        self.assertTrue(callable(_smart_tokenize))

    def test_import_escape_fts5(self):
        from rag.retrieval import _escape_fts5
        self.assertTrue(callable(_escape_fts5))

    def test_import_vector_search(self):
        from rag.retrieval import vector_search
        self.assertTrue(callable(vector_search))

    def test_import_rrf_fusion(self):
        from rag.fusion import rrf_fusion
        self.assertTrue(callable(rrf_fusion))

    def test_import_search_database(self):
        from rag.searcher import search_database
        self.assertTrue(callable(search_database))

    def test_import_search_database_with_metadata(self):
        from rag.searcher import search_database_with_metadata
        self.assertTrue(callable(search_database_with_metadata))

    def test_import_extract_snippet(self):
        from rag.snippet import _extract_snippet
        self.assertTrue(callable(_extract_snippet))

    def test_import_vector_availability(self):
        from rag.retrieval import _vector_availability
        self.assertTrue(callable(_vector_availability))

    def test_import_run_vector_query(self):
        from rag.retrieval import _run_vector_query
        self.assertTrue(callable(_run_vector_query))

    def test_import_fts5_special(self):
        from rag.retrieval import _FTS5_SPECIAL
        self.assertIsInstance(_FTS5_SPECIAL, set)

    def test_import_search_database_impl(self):
        from rag.searcher import _search_database_impl
        self.assertTrue(callable(_search_database_impl))

    def test_import_rerank_results(self):
        from rag.fusion import rerank_results
        self.assertTrue(callable(rerank_results))

    def test_searcher_reexports_legacy_helper_imports(self):
        from rag import fusion, retrieval, snippet
        from rag.searcher import (
            _FTS5_SPECIAL,
            _escape_fts5,
            _extract_snippet,
            _run_fts_query,
            _run_vector_query,
            _smart_tokenize,
            _vector_availability,
            rerank_results,
            rrf_fusion,
            vector_search,
        )

        self.assertIs(_FTS5_SPECIAL, retrieval._FTS5_SPECIAL)
        self.assertIs(_escape_fts5, retrieval._escape_fts5)
        self.assertIs(_run_fts_query, retrieval._run_fts_query)
        self.assertIs(_run_vector_query, retrieval._run_vector_query)
        self.assertIs(_smart_tokenize, retrieval._smart_tokenize)
        self.assertIs(_vector_availability, retrieval._vector_availability)
        self.assertIs(vector_search, retrieval.vector_search)
        self.assertIs(rerank_results, fusion.rerank_results)
        self.assertIs(rrf_fusion, fusion.rrf_fusion)
        self.assertIs(_extract_snippet, snippet._extract_snippet)

    def test_rrf_fusion_basic(self):
        from rag.fusion import rrf_fusion
        fts = [{'id': 1}, {'id': 2}]
        vec = [{'id': 2, 'distance': 0.1}, {'id': 3, 'distance': 0.2}]
        fused = rrf_fusion(fts, vec, k=60)
        self.assertEqual(len(fused), 3)
        self.assertEqual(fused[0]['id'], 2)
        self.assertIn('rrf_score', fused[0])


from rag.query_rewrite import expand_query_variants


def test_expand_query_variants_adds_node_add_child_alias():
    assert expand_query_variants("attach node to scene tree") == [
        "attach node to scene tree",
        "Node.add_child",
    ]


def test_expand_query_variants_adds_timer_is_stopped_alias():
    assert expand_query_variants("check if timer is stopped") == [
        "check if timer is stopped",
        "Timer.is_stopped",
    ]


def test_expand_query_variants_adds_object_emit_signal_alias():
    assert expand_query_variants("emit a signal from code") == [
        "emit a signal from code",
        "Object.emit_signal",
    ]


def test_expand_query_variants_deduplicates_exact_symbol_query():
    assert expand_query_variants("Node.add_child") == ["Node.add_child"]


from rag.query_rewrite import doc_type_boost


def test_doc_type_boost_prefers_tutorial_for_how_to_query():
    assert doc_type_boost("how to use scene tree nodes", "tutorial") > 0
    assert doc_type_boost("how to use scene tree nodes", "class") == 0


def test_doc_type_boost_does_not_boost_symbol_query():
    assert doc_type_boost("Node.add_child", "tutorial") == 0
    assert doc_type_boost("Node.add_child", "class") == 0


def test_query_plan_exposes_alias_symbol_candidate():
    from rag.query_plan import build_query_plan

    plan = build_query_plan("attach node to scene tree")

    assert plan.original == "attach node to scene tree"
    assert "attach node to scene tree" in plan.fts_variants
    assert "Node.add_child" in plan.alias_symbol_candidates
    assert "Node.add_child" in plan.symbol_candidates


def test_query_plan_deduplicates_exact_symbol_query():
    from rag.query_plan import build_query_plan

    plan = build_query_plan("Node.add_child")

    assert plan.symbol_candidates == ("Node.add_child",)
    assert plan.alias_symbol_candidates == ()
    assert plan.fts_variants == ("Node.add_child",)


def test_query_plan_detects_tutorial_and_addon_intent():
    from rag.query_plan import build_query_plan

    tutorial = build_query_plan("how to use scene tree nodes")
    addon = build_query_plan("dialogue manager addon")

    assert tutorial.doc_type_intent == "tutorial"
    assert addon.addon_intent == "addon"


def test_rerank_promotes_alias_symbol_match():
    from rag.models import SearchResult
    from rag.query_plan import build_query_plan
    from rag.fusion import rerank_results

    plan = build_query_plan("attach node to scene tree")
    weak_alias = SearchResult(
        score=1.0,
        path="classes/class_node.md",
        start_line=1,
        end_line=2,
        doc_type="class",
        chunk_type="method",
        addon="",
        addon_name="",
        symbol="Node.add_child",
        heading="add_child",
        breadcrumb="Node",
        text="Adds a child node.",
    )
    lexical = SearchResult(
        score=2.0,
        path="tutorials/scripting/change_scenes_manually.md",
        start_line=1,
        end_line=2,
        doc_type="tutorial",
        chunk_type="section",
        addon="",
        addon_name="",
        symbol="",
        heading="Scene tree",
        breadcrumb="Tutorial",
        text="Attach scripts to scene nodes.",
    )

    ranked = rerank_results(plan, [lexical, weak_alias])

    assert ranked[0].symbol == "Node.add_child"


def test_rerank_symbol_query_does_not_apply_tutorial_intent():
    from rag.models import SearchResult
    from rag.query_plan import build_query_plan
    from rag.fusion import rerank_results

    plan = build_query_plan("Node.add_child")
    class_result = SearchResult(
        score=1.0,
        path="classes/class_node.md",
        start_line=1,
        end_line=2,
        doc_type="class",
        chunk_type="method",
        addon="",
        addon_name="",
        symbol="Node.add_child",
        heading="add_child",
        breadcrumb="Node",
        text="Adds a child node.",
    )
    tutorial_result = SearchResult(
        score=2.0,
        path="tutorials/scripting/change_scenes_manually.md",
        start_line=1,
        end_line=2,
        doc_type="tutorial",
        chunk_type="section",
        addon="",
        addon_name="",
        symbol="",
        heading="Scene tree",
        breadcrumb="Tutorial",
        text="Attach scripts to scene nodes.",
    )

    ranked = rerank_results(plan, [tutorial_result, class_result])

    assert ranked[0].symbol == "Node.add_child"


def test_rerank_appends_alias_symbol_signal():
    from rag.models import SearchResult
    from rag.query_plan import build_query_plan
    from rag.fusion import rerank_results

    plan = build_query_plan("attach node to scene tree")
    weak_alias = SearchResult(
        score=1.0, path="classes/class_node.md", start_line=1, end_line=2,
        doc_type="class", chunk_type="method", addon="", addon_name="",
        symbol="Node.add_child", heading="add_child", breadcrumb="Node",
        text="Adds a child node.",
    )
    ranked = rerank_results(plan, [weak_alias])
    assert ranked[0].symbol == "Node.add_child"
    names = [s.name for s in ranked[0].ranking_signals]
    assert "rerank.alias_symbol" in names
    alias_sig = next(s for s in ranked[0].ranking_signals if s.name == "rerank.alias_symbol")
    assert alias_sig.weight == 5.0


def test_rerank_appends_direct_symbol_signal():
    from rag.models import SearchResult
    from rag.query_plan import build_query_plan
    from rag.fusion import rerank_results

    plan = build_query_plan("Node.add_child")
    result = SearchResult(
        score=1.0, path="classes/class_node.md", start_line=1, end_line=2,
        doc_type="class", chunk_type="method", addon="", addon_name="",
        symbol="Node.add_child", heading="add_child", breadcrumb="Node",
        text="Adds a child node.",
    )
    ranked = rerank_results(plan, [result])
    names = [s.name for s in ranked[0].ranking_signals]
    assert "rerank.direct_symbol" in names
    sig = next(s for s in ranked[0].ranking_signals if s.name == "rerank.direct_symbol")
    assert sig.weight == 2.0


def test_rerank_appends_doc_type_intent_signal():
    from rag.models import SearchResult
    from rag.query_plan import QueryPlan
    from rag.fusion import rerank_results

    # Construct plan directly: build_query_plan always puts the original query
    # in symbol_candidates (per QueryPlan docstring), which would block the
    # doc_type_intent bonus (the `not plan.symbol_candidates` guard). Empty
    # symbol_candidates exercises the doc_type_intent branch in isolation.
    plan = QueryPlan(
        original="how to use scene tree nodes",
        fts_variants=("how to use scene tree nodes",),
        symbol_candidates=(),
        alias_symbol_candidates=(),
        doc_type_intent="tutorial",
        addon_intent=None,
    )
    tutorial = SearchResult(
        score=1.0, path="tutorials/scene_tree.md", start_line=1, end_line=2,
        doc_type="tutorial", chunk_type="section", addon="", addon_name="",
        symbol="", heading="Scene tree", breadcrumb="Tutorial",
        text="How to use the scene tree.",
    )
    ranked = rerank_results(plan, [tutorial])
    names = [s.name for s in ranked[0].ranking_signals]
    assert "rerank.doc_type_intent" in names
    sig = next(s for s in ranked[0].ranking_signals if s.name == "rerank.doc_type_intent")
    assert sig.weight == 0.05


def test_rerank_appends_addon_intent_signal():
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
    names = [s.name for s in ranked[0].ranking_signals]
    assert "rerank.addon_intent" in names
    sig = next(s for s in ranked[0].ranking_signals if s.name == "rerank.addon_intent")
    assert sig.weight == 0.5


def test_rerank_preserves_prior_signals_without_mutating_original():
    """OpenSpec 2.4 / 3.2: rerank must copy ranking_signals (not share the
    list) and preserve ordering."""
    from rag.models import RankingSignal, SearchResult
    from rag.query_plan import build_query_plan
    from rag.fusion import rerank_results

    plan = build_query_plan("attach node to scene tree")
    prior = RankingSignal(name="symbol_recall.exact", weight=100.0, value="Node.add_child")
    original = SearchResult(
        score=1.0, path="classes/class_node.md", start_line=1, end_line=2,
        doc_type="class", chunk_type="method", addon="", addon_name="",
        symbol="Node.add_child", heading="add_child", breadcrumb="Node",
        text="Adds a child node.", ranking_signals=[prior],
    )
    ranked = rerank_results(plan, [original])
    names = [s.name for s in ranked[0].ranking_signals]
    assert "symbol_recall.exact" in names, "prior signal must survive rerank"
    assert "rerank.alias_symbol" in names, "rerank bonus signal must be appended"
    # Original must not be mutated (list not shared across replace()).
    assert len(original.ranking_signals) == 1, (
        "original result's signal list must not be mutated by rerank"
    )


def test_rerank_bonus_equals_signal_weight_sum():
    """Guard against drift between _rerank_bonus and _rerank_signals."""
    from rag.models import SearchResult
    from rag.query_plan import build_query_plan
    from rag.fusion import _rerank_bonus, _rerank_signals

    plan = build_query_plan("dialogue manager addon how to")
    addon_tutorial = SearchResult(
        score=1.0, path="p", start_line=1, end_line=2, doc_type="addon",
        chunk_type="section", addon="dm", addon_name="DM", symbol="",
        heading="h", breadcrumb="b", text="t",
    )
    assert _rerank_bonus(plan, addon_tutorial) == sum(
        s.weight for s in _rerank_signals(plan, addon_tutorial)
    )


def test_rerank_ordering_unchanged_with_signals():
    """OpenSpec 3.2: final ordering must match the pre-change order."""
    from rag.models import SearchResult
    from rag.query_plan import build_query_plan
    from rag.fusion import rerank_results

    plan = build_query_plan("attach node to scene tree")
    weak_alias = SearchResult(
        score=1.0, path="classes/class_node.md", start_line=1, end_line=2,
        doc_type="class", chunk_type="method", addon="", addon_name="",
        symbol="Node.add_child", heading="add_child", breadcrumb="Node",
        text="Adds a child node.",
    )
    lexical = SearchResult(
        score=2.0, path="tutorials/scripting/change_scenes_manually.md",
        start_line=1, end_line=2, doc_type="tutorial", chunk_type="section",
        addon="", addon_name="", symbol="", heading="Scene tree",
        breadcrumb="Tutorial", text="Attach scripts to scene nodes.",
    )
    ranked = rerank_results(plan, [lexical, weak_alias])
    assert ranked[0].symbol == "Node.add_child", "alias bonus must still promote the alias match"


def test_search_response_metadata_shape_is_stable():
    from rag.models import SearchMetadata

    metadata = SearchMetadata(mode="fts_only", vector_available=False, fallback_reason="missing_vec_chunks")

    assert metadata.mode == "fts_only"
    assert metadata.vector_available is False
    assert metadata.fallback_reason == "missing_vec_chunks"


if __name__ == "__main__":
    unittest.main()
