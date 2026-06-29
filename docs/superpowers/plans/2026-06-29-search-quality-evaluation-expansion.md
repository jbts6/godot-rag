---
change: search-quality-evaluation-expansion
design-doc: docs/superpowers/specs/2026-06-29-search-quality-evaluation-expansion-design.md
base-ref: 5c9010127c71f7dac05c8130de6a3b75a7d8ff96
archived-with: 2026-06-29-search-quality-evaluation-expansion
---

# Search Quality Evaluation Expansion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand the search quality evaluation loop so query coverage, latency, fallback/degraded state, and refactor safety are visible before ranking changes.

**Architecture:** Keep public search behavior stable. Extend the existing `rag.search_eval` evaluator and query fixture first, then thread additive search metadata from `search_database_with_metadata` into diagnostics where needed. Documentation changes should describe deterministic local validation and conditional real-database baseline validation.

**Tech Stack:** Python 3.10+, stdlib `time`, `statistics`, `dataclasses`, `json`, existing `rag.search_eval`, `rag.searcher`, `pytest`, OpenSpec/Comet docs.

archived-with: 2026-06-29-search-quality-evaluation-expansion
---

## File Structure

- Modify `rst2md/rag/search_eval_queries.json`
  - Owns packaged real-database query coverage.
- Modify `rst2md/rag/search_eval.py`
  - Owns evaluation timing, latency summaries, report serialization, baseline comparison, diagnostics, and report-only promotion logic.
- Modify `rst2md/rag/searcher.py`
  - Exposes search mode and fallback/degraded metadata through existing `SearchMetadata`; no ranking changes.
- Modify `rst2md/rag/models.py`
  - Add additive metadata fields only if existing `SearchMetadata` is insufficient.
- Modify `rst2md/rag/cli.py`
  - Print new evaluator fields in text/JSON output while preserving existing fields.
- Modify `rst2md/tests/test_search_eval.py`
  - Add expanded fixture/query-suite assertions and evaluator metric/diagnostic tests.
- Modify `rst2md/tests/test_search_eval_cli.py`
  - Add CLI output coverage for new text/JSON fields.
- Modify `README.md`
  - Document routine deterministic validation and real-database baseline validation.
- Modify `WIP.md`
  - Mark this change as opened or update next-step notes after implementation.

## Task 1: Audit And Expand Query Suite

**Files:**
- Modify: `rst2md/rag/search_eval_queries.json`
- Modify: `rst2md/tests/test_search_eval.py`
- Reference: `docs/search-quality/baseline.json`

- [x] **Step 1: Inspect current query distribution**

Run:

```bash
rtk uv run python -c "import json; from collections import Counter; q=json.load(open('rst2md/rag/search_eval_queries.json')); print('total', len(q)); print('gating', sum(not x.get('report_only') for x in q)); print('report_only', sum(bool(x.get('report_only')) for x in q)); print('categories', sorted(Counter(x['category'] for x in q).items())); print('tags', sorted(Counter(t for x in q for t in x.get('tags', [])).items()))"
```

Expected: output shows current totals and highlights missing coverage relative to the OpenSpec delta.

- [x] **Step 2: Write failing test for expanded suite thresholds**

Add or update a test in `rst2md/tests/test_search_eval.py`:

```python
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
```

- [x] **Step 3: Run the failing test**

Run:

```bash
rtk uv run pytest -q rst2md/tests/test_search_eval.py::test_packaged_eval_queries_meet_expanded_coverage_requirements
```

Expected: FAIL because current packaged query coverage is below the new threshold or lacks the new filter precision assertion.

- [x] **Step 4: Add stable packaged queries**

Edit `rst2md/rag/search_eval_queries.json` and add enough stable entries to satisfy the test. Prefer queries whose expected path/symbol/doc_type/addon already exists in `godot_rag.db`. Use `report_only: true` for uncertain cases.

Use this shape for each new entry:

```json
{
  "id": "unique-kebab-case-id",
  "query": "user-facing search phrase",
  "category": "symbol",
  "required_at": 5,
  "expected_paths": ["classes/class_node.md"],
  "expected_symbols": ["Node.add_child"],
  "expected_doc_types": ["class"],
  "tags": ["normalization"]
}
```

- [x] **Step 5: Verify expanded query suite test passes**

Run:

```bash
rtk uv run pytest -q rst2md/tests/test_search_eval.py::test_packaged_eval_queries_meet_expanded_coverage_requirements
```

Expected: PASS.

- [x] **Step 6: Commit query suite expansion**

Run:

```bash
rtk git add rst2md/rag/search_eval_queries.json rst2md/tests/test_search_eval.py
rtk git commit -m "test: expand search quality query coverage"
```

## Task 2: Add Latency Metrics To Evaluation Reports

**Files:**
- Modify: `rst2md/rag/search_eval.py`
- Modify: `rst2md/tests/test_search_eval.py`

- [x] **Step 1: Write failing unit test for latency summary calculation**

Add to `rst2md/tests/test_search_eval.py`:

```python
def test_latency_summary_reports_p50_and_p95():
    from rag.search_eval import latency_summary

    summary = latency_summary([0.010, 0.020, 0.030, 0.040])

    assert summary["count"] == 4
    assert summary["p50_ms"] == 25.0
    assert summary["p95_ms"] == 40.0
```

- [x] **Step 2: Run failing latency summary test**

Run:

```bash
rtk uv run pytest -q rst2md/tests/test_search_eval.py::test_latency_summary_reports_p50_and_p95
```

Expected: FAIL because `latency_summary` does not exist yet.

- [x] **Step 3: Implement deterministic latency summary helper**

Add to `rst2md/rag/search_eval.py`:

```python
def _percentile(values: Sequence[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((len(ordered) - 1) * percentile)))
    return ordered[index]


def latency_summary(elapsed_seconds: Sequence[float]) -> dict:
    return {
        "count": len(elapsed_seconds),
        "p50_ms": round(_percentile(elapsed_seconds, 0.50) * 1000, 3),
        "p95_ms": round(_percentile(elapsed_seconds, 0.95) * 1000, 3),
    }
```

- [x] **Step 4: Run latency summary test**

Run:

```bash
rtk uv run pytest -q rst2md/tests/test_search_eval.py::test_latency_summary_reports_p50_and_p95
```

Expected: PASS.

- [x] **Step 5: Add elapsed time to `EvaluationReport`**

Update `EvaluationReport` in `rst2md/rag/search_eval.py` with an additive field:

```python
latency: dict | None = None
```

Update call sites that instantiate `EvaluationReport` to pass through existing latency data or leave `None`.

- [x] **Step 6: Measure per-query elapsed time in `evaluate_database`**

In `evaluate_database`, wrap each graph-enabled search call:

```python
started = time.perf_counter()
results = search_database(db_path, query.query, limit=diagnostic_window, expand_graph=True)
elapsed_seconds.append(time.perf_counter() - started)
```

Import `time` at the top of `rst2md/rag/search_eval.py`. Set `latency=latency_summary(elapsed_seconds)` on the returned report.

- [x] **Step 7: Add report serialization test for latency**

Add to `rst2md/tests/test_search_eval.py`:

```python
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
```

- [x] **Step 8: Run evaluator tests**

Run:

```bash
rtk uv run pytest -q rst2md/tests/test_search_eval.py
```

Expected: PASS.

- [x] **Step 9: Commit latency metrics**

Run:

```bash
rtk git add rst2md/rag/search_eval.py rst2md/tests/test_search_eval.py
rtk git commit -m "feat: report search evaluation latency"
```

## Task 3: Surface Search Mode And Fallback Diagnostics

**Files:**
- Modify: `rst2md/rag/search_eval.py`
- Modify: `rst2md/rag/searcher.py`
- Modify: `rst2md/rag/models.py`
- Modify: `rst2md/tests/test_search_eval.py`
- Modify: `rst2md/tests/test_semantic_search.py`

- [x] **Step 1: Audit existing `SearchMetadata` fields**

Run:

```bash
rtk rg -n "class SearchMetadata|fallback_reason|mode|vector_available|SearchResponse" rst2md/rag rst2md/tests
```

Expected: locate all instantiations and assertions before adding fields.

- [x] **Step 2: Write failing diagnostics test for search execution metadata**

Add to `rst2md/tests/test_search_eval.py`:

```python
def test_failure_diagnostics_include_search_execution_metadata():
    from rag.search_eval import FailureDiagnostics, _query_result_to_dict

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
```

- [x] **Step 3: Run failing diagnostics test**

Run:

```bash
rtk uv run pytest -q rst2md/tests/test_search_eval.py::test_failure_diagnostics_include_search_execution_metadata
```

Expected: FAIL because diagnostics do not yet expose these fields.

- [x] **Step 4: Extend `FailureDiagnostics` additively**

In `rst2md/rag/search_eval.py`, add fields with defaults:

```python
search_mode: str = ""
fallback_reason: str = ""
```

Update `_query_result_to_dict` diagnostics serialization to include both fields.

- [x] **Step 5: Thread metadata from search response where possible**

Change `evaluate_database` to use `search_database_with_metadata` for graph-enabled search. Preserve `search_database` public behavior. Use `response.results` for existing evaluation logic and `response.metadata` for diagnostics.

Keep no-graph comparison behavior equivalent. If no-graph metadata is not needed for first implementation, do not add it.

- [x] **Step 6: Preserve existing semantic search metadata tests**

Run:

```bash
rtk uv run pytest -q rst2md/tests/test_semantic_search.py rst2md/tests/test_search_eval.py
```

Expected: PASS.

- [x] **Step 7: Commit fallback diagnostics**

Run:

```bash
rtk git add rst2md/rag/search_eval.py rst2md/rag/searcher.py rst2md/rag/models.py rst2md/tests/test_search_eval.py rst2md/tests/test_semantic_search.py
rtk git commit -m "feat: include search execution metadata in evaluation diagnostics"
```

## Task 4: Update CLI Output And Validation Documentation

**Files:**
- Modify: `rst2md/rag/cli.py`
- Modify: `rst2md/tests/test_search_eval_cli.py`
- Modify: `README.md`
- Modify: `WIP.md`

- [x] **Step 1: Write failing CLI JSON output test**

Add to `rst2md/tests/test_search_eval_cli.py`:

```python
def test_eval_search_json_output_includes_latency(capsys, tmp_path):
    report = _report()
    report = replace(report, latency={"count": 1, "p50_ms": 1.0, "p95_ms": 1.0})
    db_path = tmp_path / "db.sqlite"
    db_path.write_text("", encoding="utf-8")
    queries = tmp_path / "queries.json"
    queries.write_text("[]", encoding="utf-8")
    args = Namespace(
        db=db_path,
        queries=queries,
        limit=5,
        compare_graph=False,
        baseline=None,
        write_baseline=False,
        json=True,
    )

    with patch("rag.cli.load_queries", return_value=[]), patch("rag.cli.evaluate_database", return_value=report), patch("rag.cli.apply_baseline", side_effect=lambda report, *a, **k: report):
        assert cmd_eval_search(args) == 0

    output = json.loads(capsys.readouterr().out)
    assert output["latency"] == {"count": 1, "p50_ms": 1.0, "p95_ms": 1.0}
```

Adjust imports in the test file as needed:

```python
import json
from dataclasses import replace
from argparse import Namespace
from unittest.mock import patch
```

- [x] **Step 2: Run failing CLI test**

Run:

```bash
rtk uv run pytest -q rst2md/tests/test_search_eval_cli.py::test_eval_search_json_output_includes_latency
```

Expected: FAIL until report serialization and CLI output include latency.

- [x] **Step 3: Update CLI text output**

In `rst2md/rag/cli.py`, ensure text report includes a concise line when `report.latency` is present:

```text
latency: count=<count> p50=<p50_ms>ms p95=<p95_ms>ms
```

Keep existing text report lines unchanged.

- [x] **Step 4: Update README search quality section**

In `README.md`, update "Search Quality Evaluation" with:

```markdown
Run deterministic evaluator tests during development:

```bash
rtk uv run pytest -q rst2md/tests/test_search_eval.py rst2md/tests/test_search_eval_cli.py
```

Run the real-database gate when `godot_rag.db` is available:

```bash
rtk uv run godot-rag eval-search --db godot_rag.db --baseline docs/search-quality/baseline.json --compare-graph
```

Reports include ranking metrics, failed-query diagnostics, and latency summaries.
```
```

- [x] **Step 5: Update WIP current change note**

In `WIP.md`, mark `search-quality-evaluation-expansion` as opened and keep remaining ranking/alias work as future work.

- [x] **Step 6: Run CLI tests**

Run:

```bash
rtk uv run pytest -q rst2md/tests/test_search_eval_cli.py
```

Expected: PASS.

- [x] **Step 7: Commit CLI and docs**

Run:

```bash
rtk git add rst2md/rag/cli.py rst2md/tests/test_search_eval_cli.py README.md WIP.md
rtk git commit -m "docs: document expanded search quality validation"
```

## Task 5: Refactor Safety Tests And Verification

**Files:**
- Modify: `rst2md/tests/test_searcher_module.py`
- Modify: `openspec/changes/search-quality-evaluation-expansion/tasks.md`
- Modify: `docs/search-quality/baseline.json` only if baseline refresh is explicitly needed after verified intentional output additions.

- [x] **Step 1: Add metadata stability test for searcher boundary**

Add to `rst2md/tests/test_searcher_module.py`:

```python
def test_search_response_metadata_shape_is_stable():
    from rag.models import SearchMetadata

    metadata = SearchMetadata(mode="fts_only", vector_available=False, fallback_reason="missing_vec_chunks")

    assert metadata.mode == "fts_only"
    assert metadata.vector_available is False
    assert metadata.fallback_reason == "missing_vec_chunks"
```

- [x] **Step 2: Run focused searcher module test**

Run:

```bash
rtk uv run pytest -q rst2md/tests/test_searcher_module.py::test_search_response_metadata_shape_is_stable
```

Expected: PASS.

- [x] **Step 3: Run focused evaluator and semantic tests**

Run:

```bash
rtk uv run pytest -q rst2md/tests/test_search_eval.py rst2md/tests/test_search_eval_cli.py rst2md/tests/test_semantic_search.py rst2md/tests/test_searcher_module.py
```

Expected: PASS.

- [x] **Step 4: Run full project tests**

Run:

```bash
rtk uv run pytest -q
```

Expected: PASS.

- [x] **Step 5: Run real-database evaluation if available**

Run:

```bash
rtk bash -lc 'if [ -f godot_rag.db ]; then rtk uv run godot-rag eval-search --db godot_rag.db --baseline docs/search-quality/baseline.json --compare-graph; else echo "SKIP: godot_rag.db not available"; fi'
```

Expected: PASS or explicit SKIP.

- [x] **Step 6: Mark OpenSpec tasks complete**

After implementation and verification, update `openspec/changes/search-quality-evaluation-expansion/tasks.md` so completed tasks use `- [x]`.

- [x] **Step 7: Commit final task status**

Run:

```bash
rtk git add openspec/changes/search-quality-evaluation-expansion/tasks.md
rtk git commit -m "chore: complete search quality evaluation expansion tasks"
```

## Self-Review

- Spec coverage: query expansion, latency reporting, fallback/degraded diagnostics, validation workflow, and refactor safety all map to tasks above.
- Placeholder scan: no `TBD` or unspecified implementation step remains.
- Type consistency: the plan consistently uses `latency_summary`, `EvaluationReport.latency`, `FailureDiagnostics.search_mode`, and `FailureDiagnostics.fallback_reason`.
