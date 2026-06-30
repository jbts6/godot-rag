from pathlib import Path

import pytest

from rag.models import SearchResult
from rag.search_eval import evaluate_results, load_queries


def _result(path="classes/class_node.md", symbol="Node.add_child", doc_type="class", addon=""):
    return SearchResult(
        score=100.0,
        path=path,
        start_line=1,
        end_line=10,
        doc_type=doc_type,
        chunk_type="section",
        addon=addon,
        addon_name=addon,
        symbol=symbol,
        heading="Methods",
        breadcrumb="Node > Methods",
        text="Adds a child node.",
    )


def test_load_queries_from_json(tmp_path):
    query_file = tmp_path / "queries.json"
    query_file.write_text(
        """[
          {
            "id": "node-add-child",
            "query": "attach node to scene tree",
            "category": "class",
            "required_at": 5,
            "expected_paths": ["classes/class_node.md"],
            "expected_symbols": ["Node.add_child"]
          }
        ]""",
        encoding="utf-8",
    )

    queries = load_queries(query_file)

    assert queries[0].id == "node-add-child"
    assert queries[0].expected_paths == ("classes/class_node.md",)
    assert queries[0].expected_symbols == ("Node.add_child",)


def test_evaluate_results_passes_when_expected_path_is_in_top_k():
    query = load_queries(Path("rst2md/tests/fixtures/search_eval_fixture_queries.json"))[0]

    result = evaluate_results(query, [_result(path=query.expected_paths[0])])

    assert result.passed is True
    assert result.matched_rank == 1
    assert result.failure_classification == ""


from dataclasses import replace

from rag.search_eval import calculate_metrics, compare_with_baseline, format_text_report


def test_calculate_metrics_overall_and_by_category():
    base = load_queries(Path("rst2md/tests/fixtures/search_eval_fixture_queries.json"))[0]
    passed_at_1 = evaluate_results(base, [_result(path=base.expected_paths[0])])
    passed_at_3 = evaluate_results(replace(base, id="tutorial", category="tutorial"), [
        _result(path="wrong.md", symbol="Wrong"),
        _result(path="other.md", symbol="Other"),
        _result(path=base.expected_paths[0]),
    ])
    failed = evaluate_results(replace(base, id="miss", category="tutorial"), [_result(path="wrong.md", symbol="Wrong")])

    overall, categories = calculate_metrics([passed_at_1, passed_at_3, failed])

    assert overall["count"] == 3
    assert overall["hit@1"] == 1 / 3
    assert overall["hit@3"] == 2 / 3
    assert overall["hit@5"] == 2 / 3
    assert overall["mrr@5"] == (1.0 + (1 / 3) + 0.0) / 3
    assert categories["tutorial"]["count"] == 2


def test_compare_with_baseline_reports_hit5_regression():
    failed, messages = compare_with_baseline(
        {"hit@5": 0.80, "mrr@5": 0.70},
        {"hit@5": 0.90, "mrr@5": 0.72},
        hit5_drop_threshold=0.05,
        mrr5_relative_drop_threshold=0.10,
    )

    assert failed is True
    assert any("hit@5" in message for message in messages)


def test_apply_baseline_marks_latency_regression_when_p95_threshold_exceeded(tmp_path):
    baseline = tmp_path / "baseline.json"
    baseline.write_text(
        json.dumps(
            {
                "overall": {"count": 1, "hit@1": 1.0, "hit@3": 1.0, "hit@5": 1.0, "mrr@5": 1.0},
                "latency": {"count": 1, "p50_ms": 20.0, "p95_ms": 100.0},
            }
        ),
        encoding="utf-8",
    )
    report = EvaluationReport(
        overall={"count": 1, "hit@1": 1.0, "hit@3": 1.0, "hit@5": 1.0, "mrr@5": 1.0},
        categories={},
        failures=[],
        query_results=[],
        graph_changes=[],
        latency={"count": 1, "p50_ms": 30.0, "p95_ms": 225.0},
    )

    updated = apply_baseline(
        report,
        baseline,
        write_baseline=False,
        p95_latency_threshold_ms=100.0,
    )

    assert updated.regression_failed is True
    assert any("p95 latency" in message for message in updated.regression_messages)
    assert any("threshold 100.000ms" in message for message in updated.regression_messages)


def test_text_report_includes_failed_query_diagnostic_detail():
    base = load_queries(Path("rst2md/tests/fixtures/search_eval_fixture_queries.json"))[0]
    query = replace(
        base,
        id="missing-node-add-child",
        query="missing node add_child",
        category="class",
        expected_paths=("classes/class_node.md",),
        expected_symbols=("Node.add_child",),
        expected_doc_types=("class",),
    )
    failed = evaluate_results(
        query,
        [_result(path="classes/class_timer.md", symbol="Timer.start", doc_type="class")],
    )
    overall, categories = calculate_metrics([failed])
    report = EvaluationReport(
        overall=overall,
        categories=categories,
        failures=[failed],
        query_results=[failed],
        graph_changes=[],
    )

    text = format_text_report(report)

    assert "missing-node-add-child" in text
    assert "missing node add_child" in text
    assert "category=class" in text
    assert "classes/class_node.md" in text
    assert "Node.add_child" in text
    assert "classes/class_timer.md" in text


from rag.indexer import build_database
from rag.db import get_connection
from rag.search_eval import evaluate_database, report_to_dict, database_fingerprint, DatabaseFingerprint


def _build_eval_db(tmp_path, monkeypatch):
    from rag import embeddings

    docs = tmp_path / "docs"
    classes = docs / "classes"
    tutorials = docs / "tutorials"
    addons = tmp_path / "addons"
    classes.mkdir(parents=True)
    tutorials.mkdir(parents=True)

    (classes / "class_node.md").write_text(
        "# Node\n\n"
        "Scene tree node.\n\n"
        "## Methods\n\n"
        "`void` **add_child**(`Node` node)\n\nAttach a child node to the scene tree.\n",
        encoding="utf-8",
    )
    (classes / "class_timer.md").write_text(
        "# Timer\n\n"
        "Countdown timer node.\n\n"
        "## Methods\n\n"
        "`void` **start**()\n\nStarts the timer.\n\n"
        "`bool` **is_stopped**()\n\nReturns true when the timer is stopped.\n",
        encoding="utf-8",
    )
    (tutorials / "scene_tree.md").write_text(
        "# Scene Tree\n\nUse add_child to attach nodes to the scene tree.\n",
        encoding="utf-8",
    )
    (tutorials / "graph_links.md").write_text(
        "# Graph Links\n\nGraph expansion seed. See also `Node.add_child`.\n",
        encoding="utf-8",
    )
    statecharts = addons / "statecharts"
    statecharts_docs = statecharts / "docs"
    statecharts_addon = statecharts / "addons" / "godot_state_charts"
    statecharts_docs.mkdir(parents=True)
    statecharts_addon.mkdir(parents=True)
    (statecharts_addon / "plugin.cfg").write_text(
        '[plugin]\nname="Godot State Charts"\n',
        encoding="utf-8",
    )
    (statecharts / "README.md").write_text(
        "# Statecharts\n\nState machine addon for Godot.\n",
        encoding="utf-8",
    )
    (statecharts_docs / "usage.md").write_text(
        "# Usage\n\nCreate a state machine and add transitions.\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(embeddings, "generate_embeddings", lambda texts: [[0.0] * 256 for _ in texts])
    db_path = tmp_path / "eval.db"
    build_database(docs, db_path, addons_dir=addons)
    with get_connection(db_path) as conn:
        try:
            conn.execute("DELETE FROM vec_chunks")
            conn.commit()
        except Exception:
            pass
    return db_path


def test_evaluate_database_returns_metrics_and_failures(tmp_path, monkeypatch):
    db_path = _build_eval_db(tmp_path, monkeypatch)
    queries = load_queries(Path("rst2md/tests/fixtures/search_eval_fixture_queries.json"))

    report = evaluate_database(db_path, queries, limit=5)
    data = report_to_dict(report)

    assert data["overall"]["count"] >= 3
    assert "hit@5" in data["overall"]
    assert "class" in data["categories"]
    assert isinstance(data["failures"], list)


def test_graph_comparison_marks_changed_query_status(tmp_path, monkeypatch):
    db_path = _build_eval_db(tmp_path, monkeypatch)
    queries = load_queries(Path("rst2md/tests/fixtures/search_eval_fixture_queries.json"))

    report = evaluate_database(db_path, queries, limit=5, compare_graph=True)

    assert all(hasattr(result, "graph_changed") for result in report.query_results)


def test_fixture_evaluation_covers_addon_doc_type_and_graph_expansion(tmp_path, monkeypatch):
    db_path = _build_eval_db(tmp_path, monkeypatch)
    queries = load_queries(Path("rst2md/tests/fixtures/search_eval_fixture_queries.json"))

    assert any(query.expected_doc_types for query in queries)
    assert any(query.expected_addons for query in queries)

    report = evaluate_database(db_path, queries, limit=5, compare_graph=True)
    data = report_to_dict(report)

    assert "addon" in data["categories"]
    assert any(result.query.expected_addons and result.passed for result in report.query_results)
    assert any(result.graph_changed for result in report.graph_changes)


import json

from rag.search_eval import EvaluationReport, apply_baseline


def test_apply_baseline_writes_first_run_baseline(tmp_path):
    report = EvaluationReport(
        overall={"count": 1, "hit@1": 1.0, "hit@3": 1.0, "hit@5": 1.0, "mrr@5": 1.0},
        categories={},
        failures=[],
        query_results=[],
        graph_changes=[],
    )
    baseline = tmp_path / "baseline.json"

    updated = apply_baseline(report, baseline, write_baseline=True)

    assert updated.baseline_written is True
    assert json.loads(baseline.read_text(encoding="utf-8"))["overall"]["hit@5"] == 1.0


def test_apply_baseline_marks_regression_failure(tmp_path):
    baseline = tmp_path / "baseline.json"
    baseline.write_text(json.dumps({"overall": {"hit@5": 1.0, "mrr@5": 1.0}}), encoding="utf-8")
    report = EvaluationReport(
        overall={"count": 1, "hit@1": 0.0, "hit@3": 0.0, "hit@5": 0.0, "mrr@5": 0.0},
        categories={},
        failures=[],
        query_results=[],
        graph_changes=[],
    )

    updated = apply_baseline(report, baseline, write_baseline=False)

    assert updated.regression_failed is True
    assert updated.baseline_compared is True
    assert updated.regression_messages


def test_apply_baseline_ignores_new_queries_outside_baseline_gate(tmp_path):
    baseline = tmp_path / "baseline.json"
    baseline.write_text(
        json.dumps(
            {
                "overall": {"count": 1, "hit@1": 1.0, "hit@3": 1.0, "hit@5": 1.0, "mrr@5": 1.0},
                "query_results": [
                    {
                        "id": "existing",
                        "query": "existing query",
                        "category": "class",
                        "required_at": 5,
                        "matched_rank": 1,
                        "passed": True,
                        "failure_classification": "",
                        "report_only": False,
                        "graph_changed": False,
                        "expected": {"paths": [], "symbols": [], "doc_types": [], "addons": []},
                        "observed": [],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    existing_query = load_queries(Path("rst2md/tests/fixtures/search_eval_fixture_queries.json"))[0]
    existing = evaluate_results(replace(existing_query, id="existing"), [_result(path=existing_query.expected_paths[0])])
    new_query = replace(existing_query, id="new-query")
    new_failure = evaluate_results(new_query, [_result(path="classes/class_timer.md", symbol="Timer.start")])
    overall, categories = calculate_metrics([existing, new_failure])
    report = EvaluationReport(
        overall=overall,
        categories=categories,
        failures=[new_failure],
        query_results=[existing, new_failure],
        graph_changes=[],
    )

    updated = apply_baseline(report, baseline, write_baseline=False)

    assert updated.baseline_compared is True
    assert updated.regression_failed is False


def test_evaluate_database_attaches_failure_diagnostics(tmp_path, monkeypatch):
    db_path = _build_eval_db(tmp_path, monkeypatch)
    base = load_queries(Path("rst2md/tests/fixtures/search_eval_fixture_queries.json"))[0]
    query = replace(
        base,
        id="timer-low-window",
        query="timer start",
        expected_paths=("classes/class_timer.md",),
        expected_symbols=("Timer.is_stopped",),
        required_at=1,
    )

    report = evaluate_database(db_path, [query], limit=1, diagnostic_limit=20)
    assert report.failures

    diagnostics = report.failures[0].diagnostics
    assert diagnostics is not None
    assert diagnostics.expected_present is True
    assert diagnostics.diagnostic_window == 20
    assert diagnostics.expected_rows[0]["path"] == "classes/class_timer.md"

    data = report_to_dict(report)
    assert data["failures"][0]["diagnostics"]["expected_present"] is True
    assert "best_rank" in data["failures"][0]["diagnostics"]


def test_evaluate_database_skips_failure_diagnostics_by_default(tmp_path, monkeypatch):
    db_path = _build_eval_db(tmp_path, monkeypatch)
    base = load_queries(Path("rst2md/tests/fixtures/search_eval_fixture_queries.json"))[0]
    query = replace(
        base,
        id="timer-default-no-diagnostics",
        query="timer start",
        expected_paths=("classes/class_timer.md",),
        expected_symbols=("Timer.is_stopped",),
        required_at=1,
    )

    report = evaluate_database(db_path, [query], limit=1)

    assert report.failures
    assert report.failures[0].diagnostics is None


def test_text_report_includes_failure_diagnostics_summary(tmp_path, monkeypatch):
    db_path = _build_eval_db(tmp_path, monkeypatch)
    base = load_queries(Path("rst2md/tests/fixtures/search_eval_fixture_queries.json"))[0]
    query = replace(
        base,
        id="timer-diagnostic-text",
        query="timer start",
        expected_paths=("classes/class_timer.md",),
        expected_symbols=("Timer.is_stopped",),
        required_at=1,
    )

    report = evaluate_database(db_path, [query], limit=1, diagnostic_limit=20)
    text = format_text_report(report)

    assert "diagnostics:" in text
    assert "expected_present=True" in text
    assert "best_rank=" in text


def test_query_suite_hash_is_stable_for_same_queries():
    from rag.search_eval import GoldenQuery, query_suite_hash

    queries = [
        GoldenQuery(
            id="node-add-child",
            query="attach node to scene tree",
            category="class",
            required_at=5,
            expected_symbols=("Node.add_child",),
            tags=("normalization", "alias"),
        )
    ]

    assert query_suite_hash(queries) == query_suite_hash(list(queries))


def test_query_suite_hash_changes_when_query_definition_changes():
    from rag.search_eval import GoldenQuery, query_suite_hash

    original = [
        GoldenQuery(
            id="node-add-child",
            query="attach node to scene tree",
            category="class",
            required_at=5,
            expected_symbols=("Node.add_child",),
        )
    ]
    changed = [
        GoldenQuery(
            id="node-add-child",
            query="attach child node",
            category="class",
            required_at=5,
            expected_symbols=("Node.add_child",),
        )
    ]

    assert query_suite_hash(original) != query_suite_hash(changed)


def test_validate_baseline_input_rejects_empty_counts():
    from rag.search_eval import DatabaseFingerprint, validate_baseline_input

    fingerprint = DatabaseFingerprint(
        path="empty.sqlite",
        size_bytes=0,
        documents=0,
        chunks=0,
        symbols=0,
        vectors=0,
    )

    messages = validate_baseline_input(fingerprint)

    assert "documents=0" in messages
    assert "chunks=0" in messages
    assert "symbols=0" in messages


def test_packaged_eval_queries_are_broad_and_tiered():
    queries = load_queries(Path("rst2md/rag/search_eval_queries.json"))
    ids = [query.id for query in queries]
    categories = {query.category for query in queries}
    gating = [query for query in queries if not query.report_only]
    report_only = [query for query in queries if query.report_only]

    assert len(queries) >= 30
    assert len(ids) == len(set(ids))
    assert len(gating) >= 12
    assert len(report_only) >= 8
    assert {"class", "symbol", "tutorial", "engine", "addon"}.issubset(categories)
    assert any("normalization" in query.tags for query in queries)
    assert any("graph" in query.tags for query in queries)


def test_packaged_eval_queries_meet_expanded_coverage_requirements():
    queries = load_queries(Path("rst2md/rag/search_eval_queries.json"))
    gating = [query for query in queries if not query.report_only]
    report_only = [query for query in queries if query.report_only]
    categories = {query.category for query in queries}
    tags = {tag for query in queries for tag in query.tags}

    assert len({query.id for query in queries}) == len(queries)
    assert len(queries) >= 40
    assert len(gating) >= 25
    assert len(report_only) >= 10
    assert {"class", "symbol", "tutorial", "engine", "addon"} <= categories
    assert "normalization" in tags
    assert "graph" in tags
    assert any(
        not query.report_only and (query.expected_doc_types or query.expected_addons)
        for query in queries
    )


def test_report_only_query_with_missing_expected_rows_is_not_promotable():
    from rag.search_eval import PromotionStatus, promotion_eligibility

    status = promotion_eligibility(
        passed=False,
        report_only=True,
        expected_present=False,
        matched_rank=None,
        required_at=5,
        category="addon",
    )

    assert status.eligible is False
    assert status.reason == "expected_not_present"


def test_report_only_query_that_passes_with_present_expected_rows_is_promotable():
    from rag.search_eval import promotion_eligibility

    status = promotion_eligibility(
        passed=True,
        report_only=True,
        expected_present=True,
        matched_rank=3,
        required_at=5,
        category="class",
    )

    assert status.eligible is True
    assert status.reason == "eligible"


def test_not_report_only_query_is_not_promotable():
    from rag.search_eval import promotion_eligibility

    status = promotion_eligibility(
        passed=True,
        report_only=False,
        expected_present=True,
        matched_rank=1,
        required_at=5,
        category="class",
    )

    assert status.eligible is False
    assert status.reason == "not_report_only"


def test_report_only_query_that_fails_is_not_promotable():
    from rag.search_eval import promotion_eligibility

    status = promotion_eligibility(
        passed=False,
        report_only=True,
        expected_present=True,
        matched_rank=None,
        required_at=5,
        category="class",
    )

    assert status.eligible is False
    assert status.reason == "not_passing"


def test_report_only_query_with_rank_above_required_is_not_promotable():
    from rag.search_eval import promotion_eligibility

    status = promotion_eligibility(
        passed=False,
        report_only=True,
        expected_present=True,
        matched_rank=7,
        required_at=5,
        category="class",
    )

    assert status.eligible is False
    assert status.reason == "rank_too_low"


def test_report_only_addon_query_is_not_promotable():
    from rag.search_eval import promotion_eligibility

    status = promotion_eligibility(
        passed=True,
        report_only=True,
        expected_present=True,
        matched_rank=2,
        required_at=5,
        category="addon",
    )

    assert status.eligible is False
    assert status.reason == "addon_data_unstable"


def test_database_fingerprint_returns_nonzero_counts(tmp_path, monkeypatch):
    db_path = _build_eval_db(tmp_path, monkeypatch)

    fp = database_fingerprint(str(db_path))

    assert isinstance(fp, DatabaseFingerprint)
    assert fp.path == str(db_path)
    assert fp.size_bytes > 0
    assert fp.documents > 0
    assert fp.chunks > 0
    assert fp.symbols > 0


def test_apply_baseline_writes_metadata(tmp_path):
    report = EvaluationReport(
        overall={"count": 1, "hit@1": 1.0, "hit@3": 1.0, "hit@5": 1.0, "mrr@5": 1.0},
        categories={},
        failures=[],
        query_results=[],
        graph_changes=[],
        database=DatabaseFingerprint("godot_rag.db", 123, 10, 20, 30, 20),
        query_suite_hash="abc123",
    )
    baseline = tmp_path / "baseline.json"

    updated = apply_baseline(report, baseline, write_baseline=True)
    payload = json.loads(baseline.read_text(encoding="utf-8"))

    assert updated.baseline_written is True
    assert payload["metadata"]["query_suite_hash"] == "abc123"
    assert payload["metadata"]["database"]["chunks"] == 20


def test_report_to_dict_includes_version_metadata():
    report = EvaluationReport(
        overall={"count": 1, "hit@1": 1.0, "hit@3": 1.0, "hit@5": 1.0, "mrr@5": 1.0},
        categories={},
        failures=[],
        query_results=[],
        graph_changes=[],
        database=DatabaseFingerprint("godot_rag.db", 123, 10, 20, 30, 20),
        query_suite_hash="abc123",
    )

    data = report_to_dict(report)

    versions = data["metadata"]["versions"]
    assert isinstance(versions["evaluator"], str) and versions["evaluator"]
    assert isinstance(versions["search"], str) and versions["search"]
    assert versions["evaluator"] == versions["search"]


def test_apply_baseline_write_includes_version_metadata(tmp_path):
    report = EvaluationReport(
        overall={"count": 1, "hit@1": 1.0, "hit@3": 1.0, "hit@5": 1.0, "mrr@5": 1.0},
        categories={},
        failures=[],
        query_results=[],
        graph_changes=[],
        database=DatabaseFingerprint("godot_rag.db", 123, 10, 20, 30, 20),
        query_suite_hash="abc123",
    )
    baseline = tmp_path / "baseline.json"

    apply_baseline(report, baseline, write_baseline=True)
    payload = json.loads(baseline.read_text(encoding="utf-8"))

    versions = payload["metadata"]["versions"]
    assert versions["evaluator"]
    assert versions["search"]
    assert versions["evaluator"] == versions["search"]


def test_baseline_write_rejects_invalid_database(tmp_path):
    report = EvaluationReport(
        overall={"count": 0, "hit@1": 0.0, "hit@3": 0.0, "hit@5": 0.0, "mrr@5": 0.0},
        categories={},
        failures=[],
        query_results=[],
        graph_changes=[],
        database=DatabaseFingerprint("empty.sqlite", 0, 0, 0, 0, 0),
        query_suite_hash="abc123",
    )

    with pytest.raises(ValueError, match="documents=0"):
        apply_baseline(report, tmp_path / "baseline.json", write_baseline=True)


def test_category_coverage_warns_missing_addon_category():
    from rag.search_eval import GoldenQuery, evaluate_results, calculate_metrics

    query = GoldenQuery(
        id="q1",
        query="test query",
        category="class",
        required_at=5,
        expected_paths=("classes/class_node.md",),
    )
    result = evaluate_results(query, [_result(path="classes/class_node.md")])
    overall, categories = calculate_metrics([result])
    report = EvaluationReport(
        overall=overall,
        categories=categories,
        failures=[],
        query_results=[result],
        graph_changes=[],
    )

    data = report_to_dict(report)

    assert "addon" in data["category_warnings"]


def test_latency_summary_reports_p50_and_p95():
    from rag.search_eval import latency_summary

    summary = latency_summary([0.010, 0.020, 0.030, 0.040])

    assert summary["count"] == 4
    assert summary["p50_ms"] == 25.0
    assert summary["p95_ms"] == 40.0


def test_report_to_dict_includes_latency_summary():
    from rag.search_eval import EvaluationReport, report_to_dict

    report = EvaluationReport(
        overall={"count": 0, "hit@1": 0.0, "hit@3": 0.0, "hit@5": 0.0, "mrr@5": 0.0},
        categories={},
        failures=[],
        query_results=[],
        graph_changes=[],
        latency={"count": 2, "p50_ms": 1.0, "p95_ms": 2.0},
    )

    assert report_to_dict(report)["latency"] == {"count": 2, "p50_ms": 1.0, "p95_ms": 2.0}


def test_failure_diagnostics_include_search_execution_metadata():
    from rag.search_eval import FailureDiagnostics, GoldenQuery, QueryResult, _query_result_to_dict

    query = GoldenQuery(
        id="missing",
        query="missing",
        category="symbol",
        expected_symbols=("Missing.symbol",),
    )
    result = QueryResult(
        query=query,
        matched_rank=None,
        passed=False,
        failure_classification="missing_recall",
        observed=[],
        diagnostics=FailureDiagnostics(
            expected_present=False,
            expected_rows=(),
            best_rank=None,
            best_rank_no_graph=None,
            diagnostic_window=50,
            search_mode="fts_only",
            fallback_reason="missing_vec_chunks",
        ),
    )

    data = _query_result_to_dict(result)

    assert data["diagnostics"]["search_mode"] == "fts_only"
    assert data["diagnostics"]["fallback_reason"] == "missing_vec_chunks"


def _report_only_query(**overrides):
    from rag.search_eval import GoldenQuery

    values = {
        "id": "report-only-node",
        "query": "attach node to scene tree",
        "category": "class",
        "required_at": 5,
        "expected_paths": ("classes/class_node.md",),
        "expected_symbols": ("Node.add_child",),
        "expected_doc_types": (),
        "expected_addons": (),
        "report_only": True,
        "tags": (),
    }
    values.update(overrides)
    return GoldenQuery(**values)


def _query_result(query, *, matched_rank=None, passed=False, failure_classification="", observed=None, diagnostics=None):
    from rag.search_eval import QueryResult

    return QueryResult(
        query=query,
        matched_rank=matched_rank,
        passed=passed,
        failure_classification=failure_classification,
        observed=observed or [],
        diagnostics=diagnostics,
    )


def _diagnostics(**overrides):
    from rag.search_eval import FailureDiagnostics

    values = {
        "expected_present": True,
        "expected_rows": ({"path": "classes/class_node.md", "symbol": "Node.add_child", "doc_type": "class", "addon": "", "heading": "Methods"},),
        "best_rank": None,
        "best_rank_no_graph": None,
        "diagnostic_window": 50,
        "search_mode": "hybrid",
        "fallback_reason": "",
    }
    values.update(overrides)
    return FailureDiagnostics(**values)


def test_report_only_triage_marks_promotion_ready():
    from rag.search_eval import _classify_report_only_triage

    result = _query_result(_report_only_query(), matched_rank=3, passed=True)

    triage = _classify_report_only_triage(result)

    assert triage.classification == "promotion_ready"
    assert triage.promotion_candidate is True
    assert triage.recommended_followup == "promotion"
    assert triage.evidence["matched_rank"] == 3


def test_report_only_triage_marks_missing_expected_data():
    from rag.search_eval import _classify_report_only_triage

    result = _query_result(
        _report_only_query(),
        failure_classification="missing_recall",
        diagnostics=_diagnostics(expected_present=False, expected_rows=(), best_rank=None),
    )

    triage = _classify_report_only_triage(result)

    assert triage.classification == "missing_expected_data"
    assert triage.promotion_candidate is False
    assert triage.recommended_followup == "data"
    assert triage.evidence["expected_present"] is False


def test_report_only_triage_marks_low_ranking():
    from rag.search_eval import _classify_report_only_triage

    result = _query_result(
        _report_only_query(required_at=5),
        matched_rank=None,
        failure_classification="low_ranking",
        diagnostics=_diagnostics(best_rank=12),
    )

    triage = _classify_report_only_triage(result)

    assert triage.classification == "low_ranking"
    assert triage.recommended_followup == "ranking"
    assert triage.evidence["best_rank"] == 12
    assert triage.evidence["required_at"] == 5


def test_report_only_triage_marks_filter_mismatch():
    from rag.search_eval import _classify_report_only_triage

    result = _query_result(
        _report_only_query(expected_doc_types=("class",)),
        failure_classification="filter_mismatch",
        observed=[{"rank": 1, "path": "tutorials/nodes.md", "symbol": "", "doc_type": "tutorial", "addon": "", "heading": "Nodes"}],
        diagnostics=_diagnostics(best_rank=None),
    )

    triage = _classify_report_only_triage(result)

    assert triage.classification == "filter_mismatch"
    assert triage.recommended_followup == "filter"
    assert triage.evidence["observed"][0]["doc_type"] == "tutorial"


def test_report_only_triage_marks_degraded_search_before_other_causes():
    from rag.search_eval import _classify_report_only_triage

    result = _query_result(
        _report_only_query(),
        matched_rank=1,
        passed=True,
        failure_classification="missing_recall",
        diagnostics=_diagnostics(best_rank=1, fallback_reason="vector_query_failed"),
    )

    triage = _classify_report_only_triage(result)

    assert triage.classification == "degraded_search"
    assert triage.promotion_candidate is False
    assert triage.recommended_followup == "degraded_search"
    assert triage.evidence["fallback_reason"] == "vector_query_failed"


def test_report_only_triage_marks_missing_recall():
    from rag.search_eval import _classify_report_only_triage

    result = _query_result(
        _report_only_query(),
        failure_classification="missing_recall",
        diagnostics=_diagnostics(expected_present=True, best_rank=None),
    )

    triage = _classify_report_only_triage(result)

    assert triage.classification == "missing_recall"
    assert triage.recommended_followup == "recall"


def test_report_to_dict_includes_report_only_triage():
    from rag.search_eval import EvaluationReport, ReportOnlyTriage, report_to_dict

    report = EvaluationReport(
        overall={"count": 0, "hit@1": 0.0, "hit@3": 0.0, "hit@5": 0.0, "mrr@5": 0.0},
        categories={},
        failures=[],
        query_results=[],
        graph_changes=[],
        report_only_triage=(
            ReportOnlyTriage(
                query_id="report-only-node",
                classification="promotion_ready",
                promotion_candidate=True,
                recommended_followup="promotion",
                evidence={"matched_rank": 1, "required_at": 5, "observed": []},
            ),
        ),
    )

    data = report_to_dict(report)

    assert data["report_only_triage"] == [
        {
            "query_id": "report-only-node",
            "classification": "promotion_ready",
            "promotion_candidate": True,
            "recommended_followup": "promotion",
            "evidence": {"matched_rank": 1, "required_at": 5, "observed": []},
        }
    ]


def test_evaluate_database_builds_report_only_triage_when_diagnostics_enabled(tmp_path, monkeypatch):
    db_path = _build_eval_db(tmp_path, monkeypatch)
    query = _report_only_query(
        id="fixture-report-only",
        query="Node add_child",
        expected_paths=("classes/class_node.md",),
        expected_symbols=("Node.add_child",),
    )

    report = evaluate_database(db_path, [query], limit=5, diagnostic_limit=10)

    assert len(report.report_only_triage) == 1
    assert report.report_only_triage[0].query_id == "fixture-report-only"
    assert report.report_only_triage[0].classification == "degraded_search"
    assert report.report_only_triage[0].promotion_candidate is False


def test_evaluate_database_triages_passing_report_only_with_diagnostics(tmp_path, monkeypatch):
    db_path = _build_eval_db(tmp_path, monkeypatch)
    query = _report_only_query(
        id="passing-report-only",
        query="Node",
        expected_paths=("classes/class_node.md",),
        expected_symbols=(),
    )

    report = evaluate_database(db_path, [query], limit=5, diagnostic_limit=10)

    triage = report.report_only_triage[0]
    assert triage.classification == "degraded_search"
    assert triage.promotion_candidate is False
    assert triage.evidence["expected_present"] is True
    assert triage.evidence["search_mode"] == "fts_only"
    assert triage.evidence["fallback_reason"] == "empty_vec_chunks"


def test_text_report_includes_report_only_triage_summary():
    from rag.search_eval import EvaluationReport, ReportOnlyTriage, format_text_report

    report = EvaluationReport(
        overall={"count": 0, "hit@1": 0.0, "hit@3": 0.0, "hit@5": 0.0, "mrr@5": 0.0},
        categories={},
        failures=[],
        query_results=[],
        graph_changes=[],
        report_only_triage=(
            ReportOnlyTriage(
                query_id="addon-dialogue-manager",
                classification="low_ranking",
                promotion_candidate=False,
                recommended_followup="ranking",
                evidence={
                    "expected_present": True,
                    "best_rank": 12,
                    "required_at": 5,
                    "search_mode": "hybrid",
                    "fallback_reason": "",
                    "observed": [],
                },
            ),
        ),
    )

    text = format_text_report(report)

    assert "report_only_triage:" in text
    assert "- addon-dialogue-manager: low_ranking followup=ranking promotion_candidate=False" in text
    assert "expected_present=True best_rank=12 required_at=5 search_mode=hybrid fallback_reason=" in text


def test_evaluate_database_omits_report_only_triage_without_diagnostics(tmp_path, monkeypatch):
    db_path = _build_eval_db(tmp_path, monkeypatch)
    query = _report_only_query(
        id="fixture-report-only",
        query="Node add_child",
        expected_paths=("classes/class_node.md",),
        expected_symbols=("Node.add_child",),
    )

    report = evaluate_database(db_path, [query], limit=5, diagnostic_limit=None)

    assert report.report_only_triage == ()
