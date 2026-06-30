---
change: search-ranking-report-only-triage
design-doc: docs/superpowers/specs/2026-06-30-search-ranking-report-only-triage-design.md
base-ref: 5cecde7cb751a762fe725fa7759c57ee91144a7f
---

# Search Ranking Report-Only Triage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在搜索质量评估诊断输出中为 report-only 查询生成结构化 triage，总结 promotion 候选和后续工作归属。

**Architecture:** 变更只落在评估层。`evaluate_database()` 在 diagnostic evaluation 时基于现有 `QueryResult`、`FailureDiagnostics`、搜索 metadata 和 observed results 生成 `ReportOnlyTriage`；`report_to_dict()` 和 `format_text_report()` 负责序列化，不修改搜索排序、数据库 schema 或 query suite。

**Tech Stack:** Python 3.10+ dataclasses, pytest, SQLite-backed existing fixtures, existing `rag.search_eval` evaluator APIs.

## Global Constraints

- 不修改 `rst2md/rag/searcher.py`、`rst2md/rag/query_plan.py`、数据库 schema、索引流程或 `search_database` public API。
- 不自动修改 `rst2md/rag/search_eval_queries.json` 来 promote 查询。
- triage 仅在 diagnostics 被请求时生成；默认 evaluation 不做额外数据库工作。
- JSON 输出是权威机器可读格式；text 输出只给简洁摘要。
- baseline comparison 继续只基于现有 gating metrics、metadata 和 latency 阈值，不因 triage 缺失或变化失败。
- 每个实现任务先写失败测试，再写最小实现，再跑 focused tests。

---

## File Structure

- Modify `rst2md/rag/search_eval.py`: add `ReportOnlyTriage`, classification helper, evidence builder, `EvaluationReport.report_only_triage`, JSON/text serialization, and baseline-copy preservation.
- Modify `rst2md/tests/test_search_eval.py`: add triage classification unit tests, JSON serialization tests, text report tests, and baseline regression safety checks.
- Modify `rst2md/tests/test_search_eval_cli.py`: add CLI JSON/text output coverage using mocked `EvaluationReport` objects with triage.
- Modify `openspec/changes/search-ranking-report-only-triage/tasks.md`: check off completed OpenSpec tasks as implementation progresses.
- Optional documentation update after real evaluation: update an existing WIP/search-quality doc only if the run produces a concrete next-step candidate list worth recording.

## Task 1: Record Current Evaluation Baseline

**Files:**
- Modify: `openspec/changes/search-ranking-report-only-triage/tasks.md`

**Interfaces:**
- Consumes: existing CLI command `uv run godot-rag eval-search --db godot_rag.db --diagnostic-limit 50 --json`
- Produces: command output summary for later verification; no code interface.

- [x] **Step 1: Run current evaluator against the local database**

Run:

```bash
rtk uv run godot-rag eval-search --db godot_rag.db --diagnostic-limit 50 --json
```

Expected: command completes or exits with current evaluation status. Record these facts from the JSON output in the task notes or final task summary:

```text
total query count: 45
gating query count: 25
report_only query count: 20
whether report_only_triage exists before implementation: no
```

- [x] **Step 2: Verify query-suite counts directly**

Run:

```bash
rtk uv run python -c "import json; q=json.load(open('rst2md/rag/search_eval_queries.json')); print(len(q), sum(1 for x in q if not x.get('report_only')), sum(1 for x in q if x.get('report_only')))"
```

Expected:

```text
45 25 20
```

- [x] **Step 3: Update OpenSpec task checklist**

In `openspec/changes/search-ranking-report-only-triage/tasks.md`, change:

```markdown
- [ ] 1.1 Run the current search evaluation and record the 25 gating / 20 report-only baseline behavior.
```

to:

```markdown
- [x] 1.1 Run the current search evaluation and record the 25 gating / 20 report-only baseline behavior.
```

- [x] **Step 4: Commit**

```bash
rtk git add openspec/changes/search-ranking-report-only-triage/tasks.md
rtk git commit -m "test: record report-only triage baseline"
```

## Task 2: Add Triage Model and Classification Tests

**Files:**
- Modify: `rst2md/tests/test_search_eval.py`
- Modify: `rst2md/rag/search_eval.py`
- Modify: `openspec/changes/search-ranking-report-only-triage/tasks.md`

**Interfaces:**
- Produces: `ReportOnlyTriage` dataclass with fields `query_id: str`, `classification: str`, `promotion_candidate: bool`, `recommended_followup: str`, `evidence: dict`
- Produces: `_classify_report_only_triage(result: QueryResult) -> ReportOnlyTriage | None`
- Consumes: existing `GoldenQuery`, `QueryResult`, `FailureDiagnostics`, and `_result()` test helper.

- [ ] **Step 1: Add failing tests for triage classification**

Append these tests to `rst2md/tests/test_search_eval.py` near the existing diagnostics tests:

```python
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
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
rtk uv run pytest -q rst2md/tests/test_search_eval.py -k "report_only_triage"
```

Expected: FAIL because `_classify_report_only_triage` does not exist.

- [ ] **Step 3: Add minimal triage model and classifier**

In `rst2md/rag/search_eval.py`, add this dataclass after `QueryResult`:

```python
@dataclass(frozen=True)
class ReportOnlyTriage:
    query_id: str
    classification: str
    promotion_candidate: bool
    recommended_followup: str
    evidence: dict
```

Add these helpers near `_classify_failure()`:

```python
def _triage_evidence(result: QueryResult) -> dict:
    diagnostics = result.diagnostics
    return {
        "expected_present": diagnostics.expected_present if diagnostics else None,
        "matched_rank": result.matched_rank,
        "best_rank": diagnostics.best_rank if diagnostics else result.matched_rank,
        "best_rank_no_graph": diagnostics.best_rank_no_graph if diagnostics else None,
        "required_at": result.query.required_at,
        "search_mode": diagnostics.search_mode if diagnostics else "",
        "fallback_reason": diagnostics.fallback_reason if diagnostics else "",
        "observed": result.observed,
    }


def _report_only_triage_result(
    result: QueryResult,
    classification: str,
    recommended_followup: str,
    *,
    promotion_candidate: bool = False,
) -> ReportOnlyTriage:
    return ReportOnlyTriage(
        query_id=result.query.id,
        classification=classification,
        promotion_candidate=promotion_candidate,
        recommended_followup=recommended_followup,
        evidence=_triage_evidence(result),
    )


def _classify_report_only_triage(result: QueryResult) -> ReportOnlyTriage | None:
    if not result.query.report_only:
        return None

    evidence = _triage_evidence(result)
    if evidence["fallback_reason"]:
        return _report_only_triage_result(result, "degraded_search", "degraded_search")
    if result.passed and result.matched_rank is not None and result.matched_rank <= result.query.required_at:
        return _report_only_triage_result(
            result,
            "promotion_ready",
            "promotion",
            promotion_candidate=True,
        )
    if evidence["expected_present"] is False:
        return _report_only_triage_result(result, "missing_expected_data", "data")
    if result.failure_classification == "filter_mismatch":
        return _report_only_triage_result(result, "filter_mismatch", "filter")
    best_rank = evidence["best_rank"]
    if best_rank is not None and best_rank > result.query.required_at:
        return _report_only_triage_result(result, "low_ranking", "ranking")
    return _report_only_triage_result(result, "missing_recall", "recall")
```

- [ ] **Step 4: Run focused tests and verify GREEN**

Run:

```bash
rtk uv run pytest -q rst2md/tests/test_search_eval.py -k "report_only_triage"
```

Expected: PASS.

- [ ] **Step 5: Update OpenSpec task checklist**

In `openspec/changes/search-ranking-report-only-triage/tasks.md`, check off:

```markdown
- [x] 1.2 Add focused failing tests for report-only triage classifications and promotion recommendations.
- [x] 2.1 Add a structured triage result model for report-only queries.
- [x] 2.2 Classify report-only queries as `promotion_ready`, `missing_expected_data`, `missing_recall`, `low_ranking`, `filter_mismatch`, or `degraded_search`.
```

- [ ] **Step 6: Commit**

```bash
rtk git add rst2md/rag/search_eval.py rst2md/tests/test_search_eval.py openspec/changes/search-ranking-report-only-triage/tasks.md
rtk git commit -m "feat: classify report-only search eval triage"
```

## Task 3: Integrate Triage Into Evaluation and JSON Reports

**Files:**
- Modify: `rst2md/tests/test_search_eval.py`
- Modify: `rst2md/rag/search_eval.py`
- Modify: `openspec/changes/search-ranking-report-only-triage/tasks.md`

**Interfaces:**
- Consumes: `_classify_report_only_triage(result: QueryResult) -> ReportOnlyTriage | None`
- Produces: `EvaluationReport.report_only_triage: tuple[ReportOnlyTriage, ...]`
- Produces: `_report_only_triage_to_dict(triage: ReportOnlyTriage) -> dict`
- Updates: `report_to_dict(report)["report_only_triage"]`

- [ ] **Step 1: Add failing JSON/evaluation tests**

Append these tests to `rst2md/tests/test_search_eval.py`:

```python
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
    assert report.report_only_triage[0].classification == "promotion_ready"
    assert report.report_only_triage[0].promotion_candidate is True


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
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
rtk uv run pytest -q rst2md/tests/test_search_eval.py -k "report_only_triage or report_to_dict_includes_report_only"
```

Expected: FAIL because `EvaluationReport` has no `report_only_triage` field and report serialization is missing.

- [ ] **Step 3: Add report field and JSON serialization**

In `EvaluationReport`, add:

```python
    report_only_triage: tuple[ReportOnlyTriage, ...] = ()
```

Add this helper near `_query_result_to_dict()`:

```python
def _report_only_triage_to_dict(triage: ReportOnlyTriage) -> dict:
    return {
        "query_id": triage.query_id,
        "classification": triage.classification,
        "promotion_candidate": triage.promotion_candidate,
        "recommended_followup": triage.recommended_followup,
        "evidence": triage.evidence,
    }
```

In `report_to_dict()`, add:

```python
        "report_only_triage": [_report_only_triage_to_dict(triage) for triage in report.report_only_triage],
```

In `apply_baseline()`, preserve `report_only_triage` in both `baseline_report` and the returned comparison report:

```python
            report_only_triage=report.report_only_triage,
```

- [ ] **Step 4: Build triage in `evaluate_database()`**

In `evaluate_database()`, initialize:

```python
    report_only_triage = []
```

After diagnostics may have been attached and before `query_results.append(evaluated)`, add:

```python
        if diagnostics_enabled and query.report_only:
            triage = _classify_report_only_triage(evaluated)
            if triage:
                report_only_triage.append(triage)
```

In the returned `EvaluationReport`, add:

```python
        report_only_triage=tuple(report_only_triage),
```

- [ ] **Step 5: Run focused tests and verify GREEN**

Run:

```bash
rtk uv run pytest -q rst2md/tests/test_search_eval.py -k "report_only_triage or report_to_dict_includes_report_only"
```

Expected: PASS.

- [ ] **Step 6: Run baseline safety tests**

Run:

```bash
rtk uv run pytest -q rst2md/tests/test_search_eval.py -k "baseline or latency or category_warnings"
```

Expected: PASS.

- [ ] **Step 7: Update OpenSpec task checklist**

In `openspec/changes/search-ranking-report-only-triage/tasks.md`, check off:

```markdown
- [x] 2.3 Attach evidence to each triage result: expected target presence, best rank, search mode, fallback reason, and observed top results.
- [x] 3.1 Include report-only triage summaries in JSON evaluation output.
```

- [ ] **Step 8: Commit**

```bash
rtk git add rst2md/rag/search_eval.py rst2md/tests/test_search_eval.py openspec/changes/search-ranking-report-only-triage/tasks.md
rtk git commit -m "feat: report search eval report-only triage"
```

## Task 4: Add Text and CLI Output Coverage

**Files:**
- Modify: `rst2md/tests/test_search_eval.py`
- Modify: `rst2md/tests/test_search_eval_cli.py`
- Modify: `rst2md/rag/search_eval.py`
- Modify: `openspec/changes/search-ranking-report-only-triage/tasks.md`

**Interfaces:**
- Consumes: `EvaluationReport.report_only_triage`
- Updates: `format_text_report(report) -> str`
- Verifies: `cmd_eval_search()` emits JSON/text triage through existing report formatters.

- [ ] **Step 1: Add failing text report test**

Append this test to `rst2md/tests/test_search_eval.py`:

```python
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
```

- [ ] **Step 2: Add failing CLI JSON/text tests**

In `rst2md/tests/test_search_eval_cli.py`, update imports:

```python
from rag.search_eval import EvaluationReport, ReportOnlyTriage
```

Add helper:

```python
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
```

Add tests:

```python
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
```

- [ ] **Step 3: Run tests and verify RED**

Run:

```bash
rtk uv run pytest -q rst2md/tests/test_search_eval.py::test_text_report_includes_report_only_triage_summary rst2md/tests/test_search_eval_cli.py -k "report_only_triage"
```

Expected: text report test FAILS before formatter implementation.

- [ ] **Step 4: Add text report section**

In `format_text_report()`, after latency output and before failures, add:

```python
    if report.report_only_triage:
        lines.append("report_only_triage:")
        for triage in report.report_only_triage:
            evidence = triage.evidence
            lines.append(
                f"- {triage.query_id}: {triage.classification} "
                f"followup={triage.recommended_followup} "
                f"promotion_candidate={triage.promotion_candidate}"
            )
            lines.append(
                "  evidence: "
                f"expected_present={evidence.get('expected_present')} "
                f"best_rank={evidence.get('best_rank')} "
                f"required_at={evidence.get('required_at')} "
                f"search_mode={evidence.get('search_mode')} "
                f"fallback_reason={evidence.get('fallback_reason')}"
            )
```

- [ ] **Step 5: Run focused output tests and verify GREEN**

Run:

```bash
rtk uv run pytest -q rst2md/tests/test_search_eval.py::test_text_report_includes_report_only_triage_summary rst2md/tests/test_search_eval_cli.py -k "report_only_triage"
```

Expected: PASS.

- [ ] **Step 6: Update OpenSpec task checklist**

In `openspec/changes/search-ranking-report-only-triage/tasks.md`, check off:

```markdown
- [x] 1.3 Add CLI/report tests for the triage summary in JSON and text output.
- [x] 3.2 Include concise report-only triage summaries in text evaluation output.
- [x] 3.3 Emit advisory follow-up ownership for each non-promotion-ready query: data/fixture, recall, ranking, filter, or degraded search investigation.
```

- [ ] **Step 7: Commit**

```bash
rtk git add rst2md/rag/search_eval.py rst2md/tests/test_search_eval.py rst2md/tests/test_search_eval_cli.py openspec/changes/search-ranking-report-only-triage/tasks.md
rtk git commit -m "feat: expose report-only triage in eval output"
```

## Task 5: Verification and Follow-Up Candidate Documentation

**Files:**
- Modify: `openspec/changes/search-ranking-report-only-triage/tasks.md`
- Optional Modify: an existing WIP/search-quality markdown document if a concrete candidate list is produced by the real evaluation.

**Interfaces:**
- Consumes: full implementation from Tasks 2-4.
- Produces: verified test/run evidence and checked-off OpenSpec verification tasks.

- [ ] **Step 1: Run focused search evaluation tests**

Run:

```bash
rtk uv run pytest -q rst2md/tests/test_search_eval.py rst2md/tests/test_search_eval_cli.py
```

Expected: PASS.

- [ ] **Step 2: Run broader impacted tests**

Run:

```bash
rtk uv run pytest -q rst2md/tests/test_rag_search.py rst2md/tests/test_semantic_search.py
```

Expected: PASS.

- [ ] **Step 3: Run full test suite**

Run:

```bash
rtk uv run pytest -q
```

Expected: PASS.

- [ ] **Step 4: Run real evaluator with diagnostics**

Run:

```bash
rtk uv run godot-rag eval-search --db godot_rag.db --diagnostic-limit 50 --json
```

Expected: JSON output includes a top-level `report_only_triage` array. The command may still report search-quality failures according to the current corpus; do not treat report-only triage itself as a regression gate.

- [ ] **Step 5: Extract promotion and follow-up candidates**

Run:

```bash
rtk uv run godot-rag eval-search --db godot_rag.db --diagnostic-limit 50 --json > /tmp/search-triage.json
rtk uv run python -c "import json; d=json.load(open('/tmp/search-triage.json')); print('\\n'.join(f\"{x['query_id']}: {x['classification']} -> {x['recommended_followup']}\" for x in d.get('report_only_triage', [])))"
```

Expected: prints one line per report-only triage entry.

- [ ] **Step 6: Update documentation only if there is a concrete next-step list**

If Step 5 produces actionable candidates, update the relevant existing WIP/search-quality document with a short section like:

```markdown
## Report-Only Triage Candidates

- `<query-id>`: `<classification>` -> `<recommended_followup>`
```

If no existing document clearly owns this list, skip the doc update and record the candidate list in the final implementation summary instead.

- [ ] **Step 7: Update OpenSpec task checklist**

In `openspec/changes/search-ranking-report-only-triage/tasks.md`, check off:

```markdown
- [x] 4.1 Verify existing gating evaluation and baseline comparison behavior remains unchanged.
- [x] 4.2 Run focused and full test suites.
- [x] 4.3 Update WIP or related docs with the resulting next-step candidate list.
```

If Step 6 intentionally skipped documentation because no owning document existed, append this HTML comment below task 4.3:

```markdown
<!-- 4.3 candidate list captured in implementation summary; no owning WIP doc updated -->
```

- [ ] **Step 8: Commit**

```bash
rtk git add openspec/changes/search-ranking-report-only-triage/tasks.md
rtk git add docs || true
rtk git commit -m "test: verify report-only triage workflow"
```

## Self-Review Notes

- Spec coverage: Tasks 2-4 cover classification, evidence, JSON output, text output, promotion advisory behavior, and follow-up ownership. Task 5 covers gating/baseline preservation and verification.
- Scope control: no task modifies ranking, query planning, database schema, or query promotion.
- Type consistency: `ReportOnlyTriage`, `_classify_report_only_triage`, `_report_only_triage_to_dict`, and `EvaluationReport.report_only_triage` names are consistent across tasks.
