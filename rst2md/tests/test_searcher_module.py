"""TDD test: search functions are importable from focused modules and facade."""

import pytest

from rag.query_rewrite import expand_query_variants, doc_type_boost


def test_searcher_reexports_legacy_helper_imports():
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

    assert _FTS5_SPECIAL is retrieval._FTS5_SPECIAL
    assert _escape_fts5 is retrieval._escape_fts5
    assert _run_fts_query is retrieval._run_fts_query
    assert _run_vector_query is retrieval._run_vector_query
    assert _smart_tokenize is retrieval._smart_tokenize
    assert _vector_availability is retrieval._vector_availability
    assert vector_search is retrieval.vector_search
    assert rerank_results is fusion.rerank_results
    assert rrf_fusion is fusion.rrf_fusion
    assert _extract_snippet is snippet._extract_snippet


def test_rrf_fusion_basic():
    from rag.fusion import rrf_fusion
    fts = [{'id': 1}, {'id': 2}]
    vec = [{'id': 2, 'distance': 0.1}, {'id': 3, 'distance': 0.2}]
    fused = rrf_fusion(fts, vec, k=60)
    assert len(fused) == 3
    assert fused[0]['id'] == 2
    assert 'rrf_score' in fused[0]


# --- Query rewrite tests ---

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


def test_doc_type_boost_prefers_tutorial_for_how_to_query():
    assert doc_type_boost("how to use scene tree nodes", "tutorial") == 0.0
    assert doc_type_boost("how to use scene tree nodes", "class") == 0.0


def test_doc_type_boost_does_not_boost_symbol_query():
    assert doc_type_boost("Node.add_child", "tutorial") == 0
    assert doc_type_boost("Node.add_child", "class") == 0


# --- Query plan tests ---

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


# --- Rerank tests ---

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
    from rag.fusion import rerank_results, TUTORIAL_SCORE_FLOOR, TUTORIAL_BOOST_FACTOR

    plan = QueryPlan(
        original="how to use scene tree nodes",
        fts_variants=("how to use scene tree nodes",),
        symbol_candidates=(),
        alias_symbol_candidates=(),
        doc_type_intent="tutorial",
        addon_intent=None,
        inheritance_intent=False,
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
    expected_weight = max(tutorial.score, TUTORIAL_SCORE_FLOOR) * (TUTORIAL_BOOST_FACTOR - 1)
    assert sig.weight == expected_weight


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
    assert len(original.ranking_signals) == 1, (
        "original result's signal list must not be mutated by rerank"
    )


def test_rerank_bonus_equals_signal_weight_sum_alias_symbol():
    from rag.models import SearchResult
    from rag.query_plan import build_query_plan
    from rag.fusion import _rerank_bonus, _rerank_signals

    plan = build_query_plan("attach node to scene tree")
    result = SearchResult(
        score=1.0, path="classes/class_node.md", start_line=1, end_line=2,
        doc_type="class", chunk_type="method", addon="", addon_name="",
        symbol="Node.add_child", heading="add_child", breadcrumb="Node",
        text="Adds a child node.",
    )
    signals = _rerank_signals(plan, result)
    assert _rerank_bonus(plan, result) == sum(s.weight for s in signals)
    names = [s.name for s in signals]
    assert "rerank.alias_symbol" in names
    assert next(s for s in signals if s.name == "rerank.alias_symbol").weight == 5.0


def test_rerank_bonus_equals_signal_weight_sum_direct_symbol():
    from rag.models import SearchResult
    from rag.query_plan import build_query_plan
    from rag.fusion import _rerank_bonus, _rerank_signals

    plan = build_query_plan("Node.add_child")
    result = SearchResult(
        score=1.0, path="classes/class_node.md", start_line=1, end_line=2,
        doc_type="class", chunk_type="method", addon="", addon_name="",
        symbol="Node.add_child", heading="add_child", breadcrumb="Node",
        text="Adds a child node.",
    )
    signals = _rerank_signals(plan, result)
    assert _rerank_bonus(plan, result) == sum(s.weight for s in signals)
    names = [s.name for s in signals]
    assert "rerank.direct_symbol" in names
    assert next(s for s in signals if s.name == "rerank.direct_symbol").weight == 2.0


def test_rerank_bonus_equals_signal_weight_sum_doc_type_intent():
    from rag.models import SearchResult
    from rag.query_plan import QueryPlan
    from rag.fusion import _rerank_bonus, _rerank_signals, TUTORIAL_SCORE_FLOOR, TUTORIAL_BOOST_FACTOR

    plan = QueryPlan(
        original="how to use scene tree nodes",
        fts_variants=("how to use scene tree nodes",),
        symbol_candidates=(),
        alias_symbol_candidates=(),
        doc_type_intent="tutorial",
        addon_intent=None,
        inheritance_intent=False,
    )
    result = SearchResult(
        score=1.0, path="tutorials/scene_tree.md", start_line=1, end_line=2,
        doc_type="tutorial", chunk_type="section", addon="", addon_name="",
        symbol="", heading="Scene tree", breadcrumb="Tutorial",
        text="How to use the scene tree.",
    )
    signals = _rerank_signals(plan, result)
    assert _rerank_bonus(plan, result) == sum(s.weight for s in signals)
    names = [s.name for s in signals]
    assert "rerank.doc_type_intent" in names
    expected_weight = max(result.score, TUTORIAL_SCORE_FLOOR) * (TUTORIAL_BOOST_FACTOR - 1)
    assert next(s for s in signals if s.name == "rerank.doc_type_intent").weight == expected_weight


def test_rerank_bonus_equals_signal_weight_sum_addon_intent():
    from rag.models import SearchResult
    from rag.query_plan import build_query_plan
    from rag.fusion import _rerank_bonus, _rerank_signals

    plan = build_query_plan("dialogue manager addon")
    result = SearchResult(
        score=1.0, path="addons/dm/docs.md", start_line=1, end_line=2,
        doc_type="addon", chunk_type="section", addon="dm", addon_name="DM",
        symbol="", heading="Dialogue", breadcrumb="Addon",
        text="A dialogue addon.",
    )
    signals = _rerank_signals(plan, result)
    assert _rerank_bonus(plan, result) == sum(s.weight for s in signals)
    names = [s.name for s in signals]
    assert "rerank.addon_intent" in names
    assert next(s for s in signals if s.name == "rerank.addon_intent").weight == 0.5


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


# --- Dot notation split tests ---

def test_class_method_splits_to_method_suffix():
    assert expand_query_variants("Node.connect") == ["Node.connect", "connect"]


def test_class_method_parens_strips_parens():
    assert expand_query_variants("ResourceLoader.load()") == ["ResourceLoader.load()", "load"]


def test_lowercase_dot_not_split():
    # scene_tree.tutorial — 前段非大写开头，不拆
    assert expand_query_variants("scene_tree.tutorial") == ["scene_tree.tutorial"]


def test_numeric_dot_not_split():
    # v2.1 — 前段非大写开头，不拆
    assert expand_query_variants("v2.1") == ["v2.1"]


def test_symbol_candidates_dedup_dot_split():
    from rag.query_plan import build_query_plan
    plan = build_query_plan("Node.connect")
    assert "Node.connect" in plan.symbol_candidates
    assert "connect" in plan.symbol_candidates


# --- Tutorial floor boost tests ---

def test_doc_type_boost_returns_zero_for_tutorial():
    assert doc_type_boost("how to use scene tree nodes", "tutorial") == 0.0


def test_rerank_bonus_floors_low_tutorial_score():
    # score=0.66 < FLOOR=3.0 → bonus = 3.0 * 4 = 12.0
    from rag.fusion import _rerank_bonus, TUTORIAL_SCORE_FLOOR, TUTORIAL_BOOST_FACTOR
    from rag.models import SearchResult
    from rag.query_plan import build_query_plan
    plan = build_query_plan("how to use scene tree nodes")
    result = SearchResult(
        score=0.66, path="tut.md", start_line=1, end_line=10,
        doc_type="tutorial", chunk_type="section", addon="", addon_name="",
        symbol="", heading="", breadcrumb="", text="", relation_type="",
        distance=0, snippet="", ranking_signals=[],
    )
    expected = max(0.66, TUTORIAL_SCORE_FLOOR) * (TUTORIAL_BOOST_FACTOR - 1)
    assert _rerank_bonus(plan, result) == pytest.approx(expected, abs=1e-6)


def test_rerank_bonus_multiplicative_high_tutorial_score():
    # score=5.0 >= FLOOR=3.0 → bonus = 5.0 * 4 = 20.0
    from rag.fusion import _rerank_bonus, TUTORIAL_SCORE_FLOOR, TUTORIAL_BOOST_FACTOR
    from rag.models import SearchResult
    from rag.query_plan import build_query_plan
    plan = build_query_plan("how to use scene tree nodes")
    result = SearchResult(
        score=5.0, path="tut.md", start_line=1, end_line=10,
        doc_type="tutorial", chunk_type="section", addon="", addon_name="",
        symbol="", heading="", breadcrumb="", text="", relation_type="",
        distance=0, snippet="", ranking_signals=[],
    )
    expected = max(5.0, TUTORIAL_SCORE_FLOOR) * (TUTORIAL_BOOST_FACTOR - 1)
    assert _rerank_bonus(plan, result) == pytest.approx(expected, abs=1e-6)


def test_rerank_bonus_no_tutorial_boost_for_dotted_symbol_query():
    # "Node.add_child" 含点号 → _doc_type_intent 返回 None → tutorial boost 不触发
    from rag.fusion import _rerank_bonus
    from rag.models import SearchResult
    from rag.query_plan import build_query_plan
    plan = build_query_plan("Node.add_child")
    result = SearchResult(
        score=0.66, path="tut.md", start_line=1, end_line=10,
        doc_type="tutorial", chunk_type="section", addon="", addon_name="",
        symbol="", heading="", breadcrumb="", text="", relation_type="",
        distance=0, snippet="", ranking_signals=[],
    )
    assert _rerank_bonus(plan, result) == 0.0


# --- Inheritance intent tests ---

def test_inherits_keyword_triggers():
    from rag.query_plan import _inheritance_intent
    assert _inheritance_intent("Node inherits Object")


def test_subclass_of_keyword_triggers():
    from rag.query_plan import _inheritance_intent
    assert _inheritance_intent("what is subclass of Node")


def test_parent_class_keyword_triggers():
    from rag.query_plan import _inheritance_intent
    assert _inheritance_intent("parent class of Timer")


def test_derived_from_keyword_triggers():
    from rag.query_plan import _inheritance_intent
    assert _inheritance_intent("classes derived from Object")


def test_extends_does_not_trigger():
    # 修订：去掉 extends，避免 "how to extend Node functionality" 误判
    from rag.query_plan import _inheritance_intent
    assert not _inheritance_intent("how to extend Node functionality")


def test_plain_query_does_not_trigger():
    from rag.query_plan import _inheritance_intent
    assert not _inheritance_intent("Node connect")
    assert not _inheritance_intent("tutorial scene tree")
