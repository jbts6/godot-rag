import argparse
import json
from argparse import Namespace
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest

from rag.cli import cmd_eval_search
from rag.search_eval import EvaluationReport


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
        hit5_drop_threshold=0.05,
        mrr5_relative_drop_threshold=0.10,
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
        hit5_drop_threshold=0.05,
        mrr5_relative_drop_threshold=0.10,
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
        hit5_drop_threshold=0.05,
        mrr5_relative_drop_threshold=0.10,
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
        hit5_drop_threshold=0.05,
        mrr5_relative_drop_threshold=0.10,
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
    )

    with patch("rag.cli.load_queries", return_value=[]), patch("rag.cli.evaluate_database", return_value=report), patch("rag.cli.apply_baseline", side_effect=lambda report, *a, **k: report):
        cmd_eval_search(args)

    output = capsys.readouterr().out
    assert "latency:" in output
    assert "count=5" in output
    assert "p50=12.345ms" in output
    assert "p95=23.456ms" in output


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
