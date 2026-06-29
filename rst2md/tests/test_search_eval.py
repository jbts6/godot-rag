from pathlib import Path

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
from rag.search_eval import evaluate_database, report_to_dict


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
                "queries": [
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
