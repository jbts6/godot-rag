---
change: search-quality-evaluation
design-doc: openspec/changes/search-quality-evaluation/design.md
base-ref: 30eaba0f87effcba5204857dc416f4cf05f284fd
---

# Search Quality Evaluation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a two-layer search quality evaluation harness with deterministic fixture checks and manual real-database regression gates.

**Architecture:** Add a focused `rag.search_eval` module for query fixtures, matching, metrics, baseline comparison, and report formatting. Keep `rag.searcher` ranking behavior unchanged; wire the new evaluator through a `godot-rag eval-search` CLI command and small fixture tests. Use JSON fixtures to avoid adding dependencies.

**Tech Stack:** Python 3.10+, stdlib `dataclasses`, `json`, `pathlib`, `argparse`; existing `rag.search_database`; existing `pytest` setup via `rtk uv run pytest`.

## Global Constraints

- Public search behavior remains unchanged.
- No ranking algorithm changes.
- No embedding model changes.
- No database schema changes.
- No mandatory full release-database evaluation in default CI.
- No new runtime dependency for the first version.
- Generated SQLite database files remain untracked.
- Real-database quality gates fail only on clear regressions.

---

## File Structure

- Create `rst2md/rag/search_eval.py`
  - Owns golden-query loading, expected-result matching, metric calculation, failure classification, graph comparison, baseline comparison, and report serialization.
- Create `rst2md/rag/search_eval_queries.json`
  - Packaged default real-database query set for `godot-rag eval-search`.
- Create `rst2md/tests/fixtures/search_eval_fixture_queries.json`
  - Deterministic fixture query set used by CI tests.
- Create `rst2md/tests/test_search_eval.py`
  - Unit tests for metrics, matching, failure classification, baseline comparison, and fixture evaluation.
- Create `rst2md/tests/test_search_eval_cli.py`
  - CLI tests for text output, JSON output, first-run baseline creation, and regression failure.
- Modify `rst2md/rag/cli.py`
  - Add `eval-search` command; preserve existing command behavior.
- Modify `godot_rag_build/orchestrator.py`
  - Ensure non-Python top-level RAG fixture data such as `search_eval_queries.json` is copied into `godot_rag/rag`.
- Modify `rst2md/tests/test_build_release_orchestrator.py`
  - Add package-tree coverage for copied RAG JSON data.
- Modify `README.md`
  - Document fixture evaluation, real-database evaluation, JSON output, baseline refresh, and regression gate.

## Task 1: Evaluation Model, Matching, Metrics, And Baselines

**Files:**
- Create: `rst2md/rag/search_eval.py`
- Test: `rst2md/tests/test_search_eval.py`

**Interfaces:**
- Produces:
  - `GoldenQuery(id: str, query: str, category: str, required_at: int = 5, expected_paths: tuple[str, ...] = (), expected_symbols: tuple[str, ...] = (), expected_doc_types: tuple[str, ...] = (), expected_addons: tuple[str, ...] = (), report_only: bool = False, tags: tuple[str, ...] = ())`
  - `QueryResult(query: GoldenQuery, matched_rank: int | None, passed: bool, failure_classification: str, observed: list[dict], graph_changed: bool = False)`
  - `EvaluationReport(overall: dict, categories: dict, failures: list[QueryResult], query_results: list[QueryResult])`
  - `load_queries(path: Path) -> list[GoldenQuery]`
  - `evaluate_results(query: GoldenQuery, results: Sequence[SearchResult], *, required_window: int = 10) -> QueryResult`
  - `calculate_metrics(query_results: Sequence[QueryResult]) -> tuple[dict, dict]`
  - `compare_with_baseline(current: dict, baseline: dict, *, hit5_drop_threshold: float = 0.05, mrr5_relative_drop_threshold: float = 0.10) -> tuple[bool, list[str]]`
- Consumes:
  - `rag.models.SearchResult`

- [x] **Step 1: Write failing tests for query loading and expected-result matching**

Add this to `rst2md/tests/test_search_eval.py`:

```python
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
```

Run: `rtk uv run pytest -q rst2md/tests/test_search_eval.py::test_load_queries_from_json rst2md/tests/test_search_eval.py::test_evaluate_results_passes_when_expected_path_is_in_top_k`

Expected: FAIL because `rag.search_eval` does not exist and fixture file does not exist.

- [x] **Step 2: Create minimal fixture file required by the failing test**

Create `rst2md/tests/fixtures/search_eval_fixture_queries.json`:

```json
[
  {
    "id": "node-add-child",
    "query": "attach node to scene tree",
    "category": "class",
    "required_at": 5,
    "expected_paths": ["classes/class_node.md"],
    "expected_symbols": ["Node.add_child"],
    "tags": ["symbol_variant"]
  }
]
```

- [x] **Step 3: Implement query dataclass, loader, matching, and result serialization**

Create `rst2md/rag/search_eval.py` with this initial content:

```python
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from rag.models import SearchResult


@dataclass(frozen=True)
class GoldenQuery:
    id: str
    query: str
    category: str
    required_at: int = 5
    expected_paths: tuple[str, ...] = ()
    expected_symbols: tuple[str, ...] = ()
    expected_doc_types: tuple[str, ...] = ()
    expected_addons: tuple[str, ...] = ()
    report_only: bool = False
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class QueryResult:
    query: GoldenQuery
    matched_rank: int | None
    passed: bool
    failure_classification: str
    observed: list[dict]
    graph_changed: bool = False


def _as_tuple(data: dict, key: str) -> tuple[str, ...]:
    value = data.get(key) or []
    return tuple(str(item) for item in value)


def load_queries(path: Path) -> list[GoldenQuery]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    queries = []
    for item in raw:
        queries.append(
            GoldenQuery(
                id=str(item["id"]),
                query=str(item["query"]),
                category=str(item["category"]),
                required_at=int(item.get("required_at", 5)),
                expected_paths=_as_tuple(item, "expected_paths"),
                expected_symbols=_as_tuple(item, "expected_symbols"),
                expected_doc_types=_as_tuple(item, "expected_doc_types"),
                expected_addons=_as_tuple(item, "expected_addons"),
                report_only=bool(item.get("report_only", False)),
                tags=_as_tuple(item, "tags"),
            )
        )
    return queries


def _result_to_observed(result: SearchResult, rank: int) -> dict:
    return {
        "rank": rank,
        "score": result.score,
        "path": result.path,
        "symbol": result.symbol,
        "doc_type": result.doc_type,
        "addon": result.addon,
        "heading": result.heading,
    }


def _matches_any(value: str, expected: tuple[str, ...]) -> bool:
    return not expected or value in expected


def result_matches(query: GoldenQuery, result: SearchResult) -> bool:
    return (
        _matches_any(result.path, query.expected_paths)
        and _matches_any(result.symbol, query.expected_symbols)
        and _matches_any(result.doc_type, query.expected_doc_types)
        and _matches_any(result.addon, query.expected_addons)
    )


def _classify_failure(query: GoldenQuery, results: Sequence[SearchResult], matched_rank: int | None) -> str:
    if matched_rank is not None and matched_rank > query.required_at:
        return "low_ranking"
    if query.expected_doc_types and any(r.doc_type not in query.expected_doc_types for r in results[: query.required_at]):
        return "filter_mismatch"
    if query.expected_addons and any(r.addon not in query.expected_addons for r in results[: query.required_at]):
        return "filter_mismatch"
    if "normalization" in query.tags or "symbol_variant" in query.tags:
        return "query_normalization"
    return "missing_recall"


def evaluate_results(query: GoldenQuery, results: Sequence[SearchResult], *, required_window: int = 10) -> QueryResult:
    matched_rank = None
    for rank, result in enumerate(results[:required_window], start=1):
        if result_matches(query, result):
            matched_rank = rank
            break
    passed = matched_rank is not None and matched_rank <= query.required_at
    observed = [_result_to_observed(result, rank) for rank, result in enumerate(results[:required_window], start=1)]
    return QueryResult(
        query=query,
        matched_rank=matched_rank,
        passed=passed,
        failure_classification="" if passed else _classify_failure(query, results, matched_rank),
        observed=observed,
    )
```

- [x] **Step 4: Run the first tests to verify green**

Run: `rtk uv run pytest -q rst2md/tests/test_search_eval.py::test_load_queries_from_json rst2md/tests/test_search_eval.py::test_evaluate_results_passes_when_expected_path_is_in_top_k`

Expected: PASS.

- [x] **Step 5: Add failing metric and baseline tests**

Append to `rst2md/tests/test_search_eval.py`:

```python
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
```

Run: `rtk uv run pytest -q rst2md/tests/test_search_eval.py::test_calculate_metrics_overall_and_by_category rst2md/tests/test_search_eval.py::test_compare_with_baseline_reports_hit5_regression`

Expected: FAIL because metrics and baseline comparison are not implemented.

- [x] **Step 6: Implement metrics and baseline comparison**

Add to `rst2md/rag/search_eval.py`:

```python
def _metric_summary(results: Sequence[QueryResult]) -> dict:
    gating = [result for result in results if not result.query.report_only]
    if not gating:
        return {"count": 0, "hit@1": 0.0, "hit@3": 0.0, "hit@5": 0.0, "mrr@5": 0.0}

    def hit_at(k: int) -> float:
        return sum(1 for result in gating if result.matched_rank is not None and result.matched_rank <= k) / len(gating)

    mrr_total = 0.0
    for result in gating:
        if result.matched_rank is not None and result.matched_rank <= 5:
            mrr_total += 1.0 / result.matched_rank

    return {
        "count": len(gating),
        "hit@1": hit_at(1),
        "hit@3": hit_at(3),
        "hit@5": hit_at(5),
        "mrr@5": mrr_total / len(gating),
    }


def calculate_metrics(query_results: Sequence[QueryResult]) -> tuple[dict, dict]:
    overall = _metric_summary(query_results)
    categories = {}
    for result in query_results:
        categories.setdefault(result.query.category, []).append(result)
    return overall, {category: _metric_summary(results) for category, results in sorted(categories.items())}


def compare_with_baseline(
    current: dict,
    baseline: dict,
    *,
    hit5_drop_threshold: float = 0.05,
    mrr5_relative_drop_threshold: float = 0.10,
) -> tuple[bool, list[str]]:
    messages = []
    baseline_hit5 = float(baseline.get("hit@5", 0.0))
    current_hit5 = float(current.get("hit@5", 0.0))
    hit5_drop = baseline_hit5 - current_hit5
    if hit5_drop > hit5_drop_threshold:
        messages.append(
            f"hit@5 regressed from {baseline_hit5:.4f} to {current_hit5:.4f}; "
            f"drop {hit5_drop:.4f} exceeds threshold {hit5_drop_threshold:.4f}"
        )

    baseline_mrr = float(baseline.get("mrr@5", 0.0))
    current_mrr = float(current.get("mrr@5", 0.0))
    if baseline_mrr > 0:
        relative_drop = (baseline_mrr - current_mrr) / baseline_mrr
        if relative_drop > mrr5_relative_drop_threshold:
            messages.append(
                f"mrr@5 regressed from {baseline_mrr:.4f} to {current_mrr:.4f}; "
                f"relative drop {relative_drop:.4f} exceeds threshold {mrr5_relative_drop_threshold:.4f}"
            )

    return bool(messages), messages
```

- [x] **Step 7: Run Task 1 tests**

Run: `rtk uv run pytest -q rst2md/tests/test_search_eval.py`

Expected: PASS.

- [x] **Step 8: Commit Task 1**

```bash
rtk git add rst2md/rag/search_eval.py rst2md/tests/test_search_eval.py rst2md/tests/fixtures/search_eval_fixture_queries.json
rtk git commit -m "feat: add search quality evaluation metrics"
```

## Task 2: Deterministic Fixture Evaluation

**Files:**
- Modify: `rst2md/rag/search_eval.py`
- Modify: `rst2md/tests/fixtures/search_eval_fixture_queries.json`
- Modify: `rst2md/tests/test_search_eval.py`

**Interfaces:**
- Consumes:
  - `load_queries(path: Path) -> list[GoldenQuery]`
  - `evaluate_results(query: GoldenQuery, results: Sequence[SearchResult]) -> QueryResult`
- Produces:
  - `EvaluationReport`
  - `evaluate_database(db_path: Path, queries: Sequence[GoldenQuery], *, limit: int = 5, compare_graph: bool = False) -> EvaluationReport`
  - `report_to_dict(report: EvaluationReport) -> dict`

- [ ] **Step 1: Write failing tests for fixture database evaluation and graph comparison**

Append to `rst2md/tests/test_search_eval.py`:

```python
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
```

Run: `rtk uv run pytest -q rst2md/tests/test_search_eval.py::test_evaluate_database_returns_metrics_and_failures rst2md/tests/test_search_eval.py::test_graph_comparison_marks_changed_query_status`

Expected: FAIL because `EvaluationReport`, `evaluate_database`, and `report_to_dict` are not implemented.

- [ ] **Step 2: Expand deterministic fixture query set**

Replace `rst2md/tests/fixtures/search_eval_fixture_queries.json` with at least these entries. Keep the full fixture between 30 and 50 entries by adding variants after this initial set; use `report_only: true` for experimental cases if needed.

```json
[
  {
    "id": "node-add-child",
    "query": "attach node to scene tree",
    "category": "class",
    "required_at": 5,
    "expected_paths": ["classes/class_node.md"],
    "tags": ["symbol_variant"]
  },
  {
    "id": "node-add-child-symbol",
    "query": "Node.add_child",
    "category": "symbol",
    "required_at": 3,
    "expected_symbols": ["Node.add_child"],
    "tags": ["normalization"]
  },
  {
    "id": "timer-start",
    "query": "start countdown timer",
    "category": "class",
    "required_at": 5,
    "expected_paths": ["classes/class_timer.md"]
  },
  {
    "id": "timer-stopped",
    "query": "check if timer is stopped",
    "category": "class",
    "required_at": 5,
    "expected_paths": ["classes/class_timer.md"]
  },
  {
    "id": "scene-tree-tutorial",
    "query": "scene tree attach nodes tutorial",
    "category": "tutorial",
    "required_at": 5,
    "expected_paths": ["tutorials/scene_tree.md"]
  }
]
```

- [ ] **Step 3: Implement `EvaluationReport`, database evaluation, graph comparison, and report dict**

Add to `rst2md/rag/search_eval.py`:

```python
@dataclass(frozen=True)
class EvaluationReport:
    overall: dict
    categories: dict
    failures: list[QueryResult]
    query_results: list[QueryResult]
    graph_changes: list[QueryResult]
    regression_failed: bool = False
    regression_messages: tuple[str, ...] = ()
    baseline_written: bool = False
    baseline_compared: bool = False


def evaluate_database(
    db_path: Path,
    queries: Sequence[GoldenQuery],
    *,
    limit: int = 5,
    compare_graph: bool = False,
) -> EvaluationReport:
    from rag.searcher import search_database

    query_results = []
    graph_changes = []
    required_window = max(10, limit)
    for query in queries:
        results = search_database(db_path, query.query, limit=required_window, expand_graph=True)
        evaluated = evaluate_results(query, results, required_window=required_window)
        if compare_graph:
            no_graph_results = search_database(db_path, query.query, limit=required_window, expand_graph=False)
            no_graph = evaluate_results(query, no_graph_results, required_window=required_window)
            if no_graph.passed != evaluated.passed:
                evaluated = QueryResult(
                    query=evaluated.query,
                    matched_rank=evaluated.matched_rank,
                    passed=evaluated.passed,
                    failure_classification=evaluated.failure_classification,
                    observed=evaluated.observed,
                    graph_changed=True,
                )
                graph_changes.append(evaluated)
        query_results.append(evaluated)

    overall, categories = calculate_metrics(query_results)
    failures = [result for result in query_results if not result.passed]
    return EvaluationReport(
        overall=overall,
        categories=categories,
        failures=failures,
        query_results=query_results,
        graph_changes=graph_changes,
    )


def _query_result_to_dict(result: QueryResult) -> dict:
    return {
        "id": result.query.id,
        "query": result.query.query,
        "category": result.query.category,
        "required_at": result.query.required_at,
        "matched_rank": result.matched_rank,
        "passed": result.passed,
        "failure_classification": result.failure_classification,
        "report_only": result.query.report_only,
        "graph_changed": result.graph_changed,
        "expected": {
            "paths": list(result.query.expected_paths),
            "symbols": list(result.query.expected_symbols),
            "doc_types": list(result.query.expected_doc_types),
            "addons": list(result.query.expected_addons),
        },
        "observed": result.observed,
    }


def report_to_dict(report: EvaluationReport) -> dict:
    return {
        "overall": report.overall,
        "categories": report.categories,
        "failures": [_query_result_to_dict(result) for result in report.failures],
        "queries": [_query_result_to_dict(result) for result in report.query_results],
        "graph_changes": [_query_result_to_dict(result) for result in report.graph_changes],
        "regression_failed": report.regression_failed,
        "regression_messages": list(report.regression_messages),
        "baseline_written": report.baseline_written,
        "baseline_compared": report.baseline_compared,
    }
```

- [ ] **Step 4: Run fixture evaluation tests**

Run: `rtk uv run pytest -q rst2md/tests/test_search_eval.py`

Expected: PASS.

- [ ] **Step 5: Commit Task 2**

```bash
rtk git add rst2md/rag/search_eval.py rst2md/tests/test_search_eval.py rst2md/tests/fixtures/search_eval_fixture_queries.json
rtk git commit -m "test: add deterministic search quality evaluation"
```

## Task 3: CLI Command, Packaged Queries, Reports, And Regression Gate

**Files:**
- Modify: `rst2md/rag/search_eval.py`
- Modify: `rst2md/rag/cli.py`
- Create: `rst2md/rag/search_eval_queries.json`
- Create: `rst2md/tests/test_search_eval_cli.py`

**Interfaces:**
- Consumes:
  - `evaluate_database(db_path, queries, limit=5, compare_graph=False) -> EvaluationReport`
  - `report_to_dict(report) -> dict`
- Produces:
  - `apply_baseline(report: EvaluationReport, baseline_path: Path | None, *, write_baseline: bool, hit5_drop_threshold: float, mrr5_relative_drop_threshold: float) -> EvaluationReport`
  - `format_text_report(report: EvaluationReport) -> str`
  - CLI command: `godot-rag eval-search --db PATH [--queries PATH] [--baseline PATH] [--write-baseline] [--json] [--compare-graph]`

- [ ] **Step 1: Write failing tests for baseline creation and regression failure**

Append to `rst2md/tests/test_search_eval.py`:

```python
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
```

Run: `rtk uv run pytest -q rst2md/tests/test_search_eval.py::test_apply_baseline_writes_first_run_baseline rst2md/tests/test_search_eval.py::test_apply_baseline_marks_regression_failure`

Expected: FAIL because `apply_baseline` is missing.

- [ ] **Step 2: Implement baseline read/write and text report**

Add to `rst2md/rag/search_eval.py`:

```python
def apply_baseline(
    report: EvaluationReport,
    baseline_path: Path | None,
    *,
    write_baseline: bool = False,
    hit5_drop_threshold: float = 0.05,
    mrr5_relative_drop_threshold: float = 0.10,
) -> EvaluationReport:
    if baseline_path is None:
        return report

    if write_baseline:
        baseline_path.parent.mkdir(parents=True, exist_ok=True)
        baseline_path.write_text(json.dumps(report_to_dict(report), ensure_ascii=False, indent=2), encoding="utf-8")
        return EvaluationReport(
            overall=report.overall,
            categories=report.categories,
            failures=report.failures,
            query_results=report.query_results,
            graph_changes=report.graph_changes,
            regression_failed=False,
            regression_messages=(),
            baseline_written=True,
            baseline_compared=False,
        )

    if not baseline_path.exists():
        return report

    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    failed, messages = compare_with_baseline(
        report.overall,
        baseline.get("overall", {}),
        hit5_drop_threshold=hit5_drop_threshold,
        mrr5_relative_drop_threshold=mrr5_relative_drop_threshold,
    )
    return EvaluationReport(
        overall=report.overall,
        categories=report.categories,
        failures=report.failures,
        query_results=report.query_results,
        graph_changes=report.graph_changes,
        regression_failed=failed,
        regression_messages=tuple(messages),
        baseline_written=False,
        baseline_compared=True,
    )


def format_text_report(report: EvaluationReport) -> str:
    lines = ["=== Search Quality Evaluation ==="]
    lines.append(
        "overall: "
        f"count={report.overall['count']} "
        f"hit@1={report.overall['hit@1']:.3f} "
        f"hit@3={report.overall['hit@3']:.3f} "
        f"hit@5={report.overall['hit@5']:.3f} "
        f"mrr@5={report.overall['mrr@5']:.3f}"
    )
    for category, metrics in report.categories.items():
        lines.append(
            f"{category}: count={metrics['count']} "
            f"hit@5={metrics['hit@5']:.3f} mrr@5={metrics['mrr@5']:.3f}"
        )
    if report.baseline_written:
        lines.append("baseline: written")
    if report.baseline_compared:
        lines.append("baseline: compared")
    for message in report.regression_messages:
        lines.append(f"regression: {message}")
    if report.failures:
        lines.append("failures:")
        for failure in report.failures:
            lines.append(f"- {failure.query.id}: {failure.failure_classification}")
    return "\n".join(lines)
```

- [ ] **Step 3: Add packaged default real-database queries**

Create `rst2md/rag/search_eval_queries.json`:

```json
[
  {
    "id": "node-add-child",
    "query": "attach node to scene tree",
    "category": "class",
    "required_at": 5,
    "expected_symbols": ["Node.add_child"],
    "tags": ["symbol_variant"]
  },
  {
    "id": "timer-stopped",
    "query": "check if timer is stopped",
    "category": "class",
    "required_at": 5,
    "expected_symbols": ["Timer.is_stopped"]
  },
  {
    "id": "signal-emit",
    "query": "emit a signal from code",
    "category": "class",
    "required_at": 5,
    "expected_symbols": ["Signal.emit"]
  },
  {
    "id": "scene-tree-tutorial",
    "query": "how to use scene tree nodes",
    "category": "tutorial",
    "required_at": 5,
    "expected_doc_types": ["tutorial"]
  },
  {
    "id": "addon-state-machine",
    "query": "state machine addon",
    "category": "addon",
    "required_at": 5,
    "expected_doc_types": ["addon"],
    "report_only": true
  }
]
```

The first version can start with this small packaged set, then expand toward 30-50 entries before marking the change complete.

- [ ] **Step 4: Write failing CLI tests**

Create `rst2md/tests/test_search_eval_cli.py`:

```python
import argparse
import json
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
```

Run: `rtk uv run pytest -q rst2md/tests/test_search_eval_cli.py`

Expected: FAIL because `cmd_eval_search` and CLI imports are missing.

- [ ] **Step 5: Wire `eval-search` into `rst2md/rag/cli.py`**

Modify imports in `rst2md/rag/cli.py`:

```python
from rag.search_eval import (
    apply_baseline,
    evaluate_database,
    format_text_report,
    load_queries,
    report_to_dict,
)
```

Add command function:

```python
def _default_eval_queries_path() -> Path:
    return Path(__file__).with_name("search_eval_queries.json")


def cmd_eval_search(args):
    """Evaluate search quality against golden queries."""
    db_path = _require_db(args)
    queries_path = Path(args.queries) if args.queries else _default_eval_queries_path()
    queries = load_queries(queries_path)
    report = evaluate_database(db_path, queries, limit=args.limit, compare_graph=args.compare_graph)
    baseline_path = Path(args.baseline) if args.baseline else None
    report = apply_baseline(
        report,
        baseline_path,
        write_baseline=args.write_baseline,
        hit5_drop_threshold=args.hit5_drop_threshold,
        mrr5_relative_drop_threshold=args.mrr5_relative_drop_threshold,
    )
    if args.json:
        print(json.dumps(report_to_dict(report), ensure_ascii=False, indent=2))
    else:
        print(format_text_report(report))
    if report.regression_failed:
        sys.exit(1)
```

Add parser in `main()` before diagnostics or after stats:

```python
    eval_parser = subparsers.add_parser("eval-search", help="Evaluate search quality")
    eval_parser.add_argument("--db", help="Path to SQLite database")
    eval_parser.add_argument("--queries", help="Path to golden query JSON file")
    eval_parser.add_argument("--baseline", help="Path to baseline JSON file")
    eval_parser.add_argument("--write-baseline", action="store_true", help="Write baseline JSON and skip comparison")
    eval_parser.add_argument("--json", action="store_true", help="Output as JSON")
    eval_parser.add_argument("--limit", type=int, default=5, help="Max results per query")
    eval_parser.add_argument("--compare-graph", action="store_true", help="Compare graph expansion enabled and disabled")
    eval_parser.add_argument("--hit5-drop-threshold", type=float, default=0.05, help="Allowed hit@5 drop before failing")
    eval_parser.add_argument("--mrr5-relative-drop-threshold", type=float, default=0.10, help="Allowed relative MRR@5 drop before failing")
    eval_parser.set_defaults(func=cmd_eval_search)
```

- [ ] **Step 6: Run CLI tests**

Run: `rtk uv run pytest -q rst2md/tests/test_search_eval.py rst2md/tests/test_search_eval_cli.py`

Expected: PASS.

- [ ] **Step 7: Commit Task 3**

```bash
rtk git add rst2md/rag/search_eval.py rst2md/rag/cli.py rst2md/rag/search_eval_queries.json rst2md/tests/test_search_eval.py rst2md/tests/test_search_eval_cli.py
rtk git commit -m "feat: add search quality evaluation CLI"
```

## Task 4: Package Data, Documentation, And Verification

**Files:**
- Modify: `godot_rag_build/orchestrator.py`
- Modify: `rst2md/tests/test_build_release_orchestrator.py`
- Modify: `README.md`
- Modify: `openspec/changes/search-quality-evaluation/tasks.md`

**Interfaces:**
- Consumes:
  - `assemble_package_tree(root: Path) -> list[str]`
  - `godot-rag eval-search`
- Produces:
  - Package tree includes `godot_rag/rag/search_eval_queries.json`.
  - README documents evaluation and baseline workflow.

- [ ] **Step 1: Write failing package-tree test for RAG JSON data**

Modify `write_minimal_build_tree` in `rst2md/tests/test_build_release_orchestrator.py` to add:

```python
    (root / "rst2md/rag/search_eval_queries.json").write_text("[]\n", encoding="utf-8")
```

Add to `test_assemble_package_tree_rewrites_imports`:

```python
    assert (tmp_path / "godot_rag/rag/search_eval_queries.json").exists()
    assert "godot_rag/rag/search_eval_queries.json" in outputs
```

Run: `rtk uv run pytest -q rst2md/tests/test_build_release_orchestrator.py::test_assemble_package_tree_rewrites_imports`

Expected: FAIL because package tree currently copies only top-level `*.py` and `addon_configs`.

- [ ] **Step 2: Copy top-level RAG JSON files into package tree**

Modify `assemble_package_tree` in `godot_rag_build/orchestrator.py`:

```python
    for source in sorted((root / "rst2md/rag").glob("*.json")):
        target = rag_out / source.name
        shutil.copy2(source, target)
```

Place this after the existing `*.py` copy loop and before `addon_configs`.

- [ ] **Step 3: Run package-tree tests**

Run: `rtk uv run pytest -q rst2md/tests/test_build_release_orchestrator.py`

Expected: PASS.

- [ ] **Step 4: Document evaluation workflow in README**

Add a compact section near the existing diagnostics/debug search documentation:

```markdown
## Search Quality Evaluation

Run the deterministic fixture tests during development:

```bash
uv run pytest -q rst2md/tests/test_search_eval.py rst2md/tests/test_search_eval_cli.py
```

Evaluate a generated release database manually:

```bash
godot-rag eval-search --db godot_rag/rag/godot_docs.sqlite
```

Write or refresh a baseline:

```bash
godot-rag eval-search \
  --db godot_rag/rag/godot_docs.sqlite \
  --baseline docs/search-quality/baseline.json \
  --write-baseline
```

Compare against a baseline and fail only on clear regressions:

```bash
godot-rag eval-search \
  --db godot_rag/rag/godot_docs.sqlite \
  --baseline docs/search-quality/baseline.json \
  --compare-graph
```

Use `--json` for machine-readable reports.
```
```

- [ ] **Step 5: Run focused and relevant verification**

Run:

```bash
rtk uv run pytest -q rst2md/tests/test_search_eval.py rst2md/tests/test_search_eval_cli.py
rtk uv run pytest -q rst2md/tests/test_rag_search.py rst2md/tests/test_semantic_search.py rst2md/tests/test_searcher_module.py
rtk uv run pytest -q rst2md/tests/test_build_release_orchestrator.py
rtk uv run openspec validate search-quality-evaluation --strict
```

Expected: all pass.

- [ ] **Step 6: Mark OpenSpec tasks complete after verification**

Update `openspec/changes/search-quality-evaluation/tasks.md` only after the implementation and tests pass. Check off each completed task.

- [ ] **Step 7: Commit Task 4**

```bash
rtk git add godot_rag_build/orchestrator.py rst2md/tests/test_build_release_orchestrator.py README.md openspec/changes/search-quality-evaluation/tasks.md
rtk git commit -m "docs: document search quality evaluation workflow"
```

## Self-Review

Spec coverage:
- Categorized golden queries: Task 1 and Task 2.
- Fixture tests without generated DB state: Task 2.
- Real database explicit path: Task 3 CLI.
- Query constraints for path/symbol/doc type/addon: Task 1.
- Metrics overall and by category: Task 1.
- Failed query diagnostics and JSON output: Task 2 and Task 3.
- Baseline creation and clear regression failure: Task 3.
- Report-only queries: Task 1 metrics and Task 3 baseline gate.
- Failure modes and graph comparison: Task 1 and Task 2.

Placeholder scan:
- No placeholder markers remain in the plan.

Type consistency:
- `GoldenQuery`, `QueryResult`, and `EvaluationReport` are introduced in Task 1/2 before CLI use.
- `evaluate_database`, `report_to_dict`, `apply_baseline`, and `format_text_report` are introduced before CLI wiring.
