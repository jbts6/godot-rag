import argparse
import json
from argparse import Namespace
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest

from rag.cli import cmd_eval_search
from rag.search_eval import EvaluationReport, ReportOnlyTriage


def _report(regression_failed=False):
    return EvaluationReport(
        overall={"count": 1, "hit@1": 1.0, "hit@3": 1.0, "hit@5": 1.0, "mrr@5": 1.0},
        categories={"class": {"count": 1, "hit@1": 1.0, "hit@3": 1.0, "hit@5": 1.0, "mrr@5": 1.0}},
        failures=[],
        query_results=[],
        graph_changes=[],
        regression_failed=regression_failed,
    )


def test_eval_search_text_output(tmp_path, capsys):
    db_path = tmp_path / "db.sqlite"
    db_path.write_text("", encoding="utf-8")
    queries = tmp_path / "queries.json"
    queries.write_text("[]", encoding="utf-8")
    args = argparse.Namespace(
        db=str(db_path),
        queries=str(queries),
        baseline=None,
        write_baseline=False,
        json=False,
        limit=5,
        compare_graph=False,
        diagnostic_limit=None,
        hit5_drop_threshold=0.05,
        mrr5_relative_drop_threshold=0.10,
        p95_latency_threshold_ms=None,
    )

    with patch("rag.cli.load_queries", return_value=[]), patch("rag.cli.evaluate_database", return_value=_report()), patch("rag.cli.apply_baseline", side_effect=lambda report, *a, **k: report):
        cmd_eval_search(args)

    assert "Search Quality Evaluation" in capsys.readouterr().out


def test_eval_search_json_output(tmp_path, capsys):
    db_path = tmp_path / "db.sqlite"
    db_path.write_text("", encoding="utf-8")
    queries = tmp_path / "queries.json"
    queries.write_text("[]", encoding="utf-8")
    args = argparse.Namespace(
        db=str(db_path),
        queries=str(queries),
        baseline=None,
        write_baseline=False,
        json=True,
        limit=5,
        compare_graph=False,
        diagnostic_limit=None,
        hit5_drop_threshold=0.05,
        mrr5_relative_drop_threshold=0.10,
        p95_latency_threshold_ms=None,
    )

    with patch("rag.cli.load_queries", return_value=[]), patch("rag.cli.evaluate_database", return_value=_report()), patch("rag.cli.apply_baseline", side_effect=lambda report, *a, **k: report):
        cmd_eval_search(args)

    assert json.loads(capsys.readouterr().out)["overall"]["hit@5"] == 1.0


def test_eval_search_exits_nonzero_on_regression(tmp_path):
    db_path = tmp_path / "db.sqlite"
    db_path.write_text("", encoding="utf-8")
    queries = tmp_path / "queries.json"
    queries.write_text("[]", encoding="utf-8")
    args = argparse.Namespace(
        db=str(db_path),
        queries=str(queries),
        baseline=str(tmp_path / "baseline.json"),
        write_baseline=False,
        json=False,
        limit=5,
        compare_graph=False,
        diagnostic_limit=None,
        hit5_drop_threshold=0.05,
        mrr5_relative_drop_threshold=0.10,
        p95_latency_threshold_ms=None,
    )

    with patch("rag.cli.load_queries", return_value=[]), patch("rag.cli.evaluate_database", return_value=_report()), patch("rag.cli.apply_baseline", return_value=_report(regression_failed=True)):
        with pytest.raises(SystemExit) as exc:
            cmd_eval_search(args)

    assert exc.value.code == 1


def test_eval_search_exits_nonzero_on_baseline_write_value_error(tmp_path, capsys):
    db_path = tmp_path / "db.sqlite"
    db_path.write_text("", encoding="utf-8")
    queries = tmp_path / "queries.json"
    queries.write_text("[]", encoding="utf-8")
    args = argparse.Namespace(
        db=str(db_path),
        queries=str(queries),
        baseline=str(tmp_path / "baseline.json"),
        write_baseline=True,
        json=False,
        limit=5,
        compare_graph=False,
        diagnostic_limit=None,
        hit5_drop_threshold=0.05,
        mrr5_relative_drop_threshold=0.10,
        p95_latency_threshold_ms=None,
    )

    with patch("rag.cli.load_queries", return_value=[]), patch("rag.cli.evaluate_database", return_value=_report()), patch("rag.cli.apply_baseline", side_effect=ValueError("documents=0")):
        with pytest.raises(SystemExit) as exc:
            cmd_eval_search(args)

    assert exc.value.code == 1
    assert "documents=0" in capsys.readouterr().err


def test_eval_search_json_output_includes_latency(capsys, tmp_path):
    report = _report()
    report = replace(report, latency={"count": 1, "p50_ms": 1.0, "p95_ms": 1.0})
    db_path = tmp_path / "db.sqlite"
    db_path.write_text("", encoding="utf-8")
    queries = tmp_path / "queries.json"
    queries.write_text("[]", encoding="utf-8")
    args = Namespace(
        db=str(db_path),
        queries=str(queries),
        limit=5,
        compare_graph=False,
        baseline=None,
        write_baseline=False,
        json=True,
        hit5_drop_threshold=0.05,
        mrr5_relative_drop_threshold=0.10,
        diagnostic_limit=None,
        p95_latency_threshold_ms=None,
    )

    with patch("rag.cli.load_queries", return_value=[]), patch("rag.cli.evaluate_database", return_value=report), patch("rag.cli.apply_baseline", side_effect=lambda report, *a, **k: report):
        cmd_eval_search(args)

    output = json.loads(capsys.readouterr().out)
    assert output["latency"] == {"count": 1, "p50_ms": 1.0, "p95_ms": 1.0}


def test_eval_search_text_output_includes_latency(capsys, tmp_path):
    report = _report()
    report = replace(report, latency={"count": 5, "p50_ms": 12.345, "p95_ms": 23.456})
    db_path = tmp_path / "db.sqlite"
    db_path.write_text("", encoding="utf-8")
    queries = tmp_path / "queries.json"
    queries.write_text("[]", encoding="utf-8")
    args = Namespace(
        db=str(db_path),
        queries=str(queries),
        limit=5,
        compare_graph=False,
        baseline=None,
        write_baseline=False,
        json=False,
        hit5_drop_threshold=0.05,
        mrr5_relative_drop_threshold=0.10,
        diagnostic_limit=None,
        p95_latency_threshold_ms=None,
    )

    with patch("rag.cli.load_queries", return_value=[]), patch("rag.cli.evaluate_database", return_value=report), patch("rag.cli.apply_baseline", side_effect=lambda report, *a, **k: report):
        cmd_eval_search(args)

    output = capsys.readouterr().out
    assert "latency:" in output
    assert "count=5" in output
    assert "p50=12.345ms" in output
    assert "p95=23.456ms" in output


def test_eval_search_passes_diagnostic_and_latency_threshold_args(capsys, tmp_path):
    report = _report()
    db_path = tmp_path / "db.sqlite"
    db_path.write_text("", encoding="utf-8")
    queries = tmp_path / "queries.json"
    queries.write_text("[]", encoding="utf-8")
    args = Namespace(
        db=str(db_path),
        queries=str(queries),
        limit=5,
        compare_graph=False,
        diagnostic_limit=25,
        baseline=str(tmp_path / "baseline.json"),
        write_baseline=False,
        json=True,
        hit5_drop_threshold=0.05,
        mrr5_relative_drop_threshold=0.10,
        p95_latency_threshold_ms=100.0,
    )

    with (
        patch("rag.cli.load_queries", return_value=[]),
        patch("rag.cli.evaluate_database", return_value=report) as evaluate_database,
        patch("rag.cli.apply_baseline", side_effect=lambda report, *a, **k: report) as apply_baseline,
    ):
        cmd_eval_search(args)

    evaluate_database.assert_called_once_with(
        db_path,
        [],
        limit=5,
        compare_graph=False,
        diagnostic_limit=25,
    )
    assert apply_baseline.call_args.kwargs["p95_latency_threshold_ms"] == 100.0
    capsys.readouterr()


def test_project_script_targets_importable_rag_cli():
    import importlib
    import re

    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")
    script_match = re.search(r'^godot-rag = "([^"]+)"$', pyproject, re.MULTILINE)
    assert script_match is not None
    assert script_match.group(1) == "rag.cli:main"

    package_match = re.search(r'^packages = \[(.+)\]$', pyproject, re.MULTILINE)
    assert package_match is not None
    assert '"rst2md/rag"' in package_match.group(1)

    module_name, _, attr_name = script_match.group(1).partition(":")
    module = importlib.import_module(module_name)
    assert callable(getattr(module, attr_name))


def _triage():
    return (
        ReportOnlyTriage(
            query_id="report-only-node",
            classification="promotion_ready",
            promotion_candidate=True,
            recommended_followup="promotion",
            evidence={"matched_rank": 1, "required_at": 5, "observed": []},
        ),
    )


def test_eval_search_json_output_includes_report_only_triage(capsys, tmp_path):
    report = replace(_report(), report_only_triage=_triage())
    db_path = tmp_path / "db.sqlite"
    db_path.write_text("", encoding="utf-8")
    queries = tmp_path / "queries.json"
    queries.write_text("[]", encoding="utf-8")
    args = Namespace(
        db=str(db_path),
        queries=str(queries),
        limit=5,
        compare_graph=False,
        baseline=None,
        write_baseline=False,
        json=True,
        hit5_drop_threshold=0.05,
        mrr5_relative_drop_threshold=0.10,
        diagnostic_limit=50,
        p95_latency_threshold_ms=None,
    )

    with patch("rag.cli.load_queries", return_value=[]), patch("rag.cli.evaluate_database", return_value=report), patch("rag.cli.apply_baseline", side_effect=lambda report, *a, **k: report):
        cmd_eval_search(args)

    output = json.loads(capsys.readouterr().out)
    assert output["report_only_triage"][0]["query_id"] == "report-only-node"
    assert output["report_only_triage"][0]["promotion_candidate"] is True


def test_eval_search_text_output_includes_report_only_triage(capsys, tmp_path):
    report = replace(_report(), report_only_triage=_triage())
    db_path = tmp_path / "db.sqlite"
    db_path.write_text("", encoding="utf-8")
    queries = tmp_path / "queries.json"
    queries.write_text("[]", encoding="utf-8")
    args = Namespace(
        db=str(db_path),
        queries=str(queries),
        limit=5,
        compare_graph=False,
        baseline=None,
        write_baseline=False,
        json=False,
        hit5_drop_threshold=0.05,
        mrr5_relative_drop_threshold=0.10,
        diagnostic_limit=50,
        p95_latency_threshold_ms=None,
    )

    with patch("rag.cli.load_queries", return_value=[]), patch("rag.cli.evaluate_database", return_value=report), patch("rag.cli.apply_baseline", side_effect=lambda report, *a, **k: report):
        cmd_eval_search(args)

    assert "report_only_triage:" in capsys.readouterr().out
