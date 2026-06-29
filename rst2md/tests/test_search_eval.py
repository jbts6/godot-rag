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

from rag.search_eval import calculate_metrics, compare_with_baseline


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


import tempfile

from rag.indexer import build_database
from rag.search_eval import evaluate_database, report_to_dict


def _build_eval_db(tmp_path, monkeypatch):
    from rag import embeddings

    docs = tmp_path / "docs"
    classes = docs / "classes"
    tutorials = docs / "tutorials"
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
    monkeypatch.setattr(embeddings, "generate_embeddings", lambda texts: [[0.0] * 256 for _ in texts])
    db_path = tmp_path / "eval.db"
    build_database(docs, db_path)
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
