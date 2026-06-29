---
change: stabilize-search-quality-loop
design-doc: docs/superpowers/specs/2026-06-29-stabilize-search-quality-loop-design.md
base-ref: 8c531568f7c29f90992aaef8b14a02e5a5ec0680
archived-with: 2026-06-29-stabilize-search-quality-loop
---

# Stabilize Search Quality Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the search quality loop stable enough to reject invalid baselines and promote natural-language symbol queries through `QueryPlan`-driven recall and deterministic reranking.

**Architecture:** Keep the existing SQLite FTS5, sqlite-vec, RRF, and graph expansion pipeline. Add a focused evaluation metadata layer in `search_eval.py`, a small internal `QueryPlan` module, and deterministic reranking helpers consumed by `searcher.py`.

**Tech Stack:** Python 3.10+, pytest, SQLite, sqlite-vec, existing `rag` package modules.

## Global Constraints

- Use Chinese for user-facing progress and final reports.
- Do not add external runtime services, LLM rerankers, learned rerankers, or new model dependencies.
- Do not change public `search_database()` or `search_database_with_metadata()` signatures.
- Do not require committing generated database binaries.
- Keep addon queries report-only unless diagnostics prove expected addon rows exist in the canonical database.
- Use TDD unless the user explicitly chooses direct execution.

archived-with: 2026-06-29-stabilize-search-quality-loop
---

## File Structure

- Modify `rst2md/rag/search_eval.py`: baseline metadata, database fingerprint, query-suite hash, validation errors, category coverage warnings, promotion eligibility.
- Modify `rst2md/rag/cli.py`: surface baseline validation failures and metadata warnings through `eval-search`.
- Create `rst2md/rag/query_plan.py`: internal `QueryPlan` dataclass and `build_query_plan()`.
- Modify `rst2md/rag/query_rewrite.py`: keep `expand_query_variants()` and expose reusable alias/symbol intent helpers for `QueryPlan`.
- Modify `rst2md/rag/searcher.py`: build one `QueryPlan`, route symbol candidates through symbol recall, replace `_apply_intent_boost()` with deterministic reranking.
- Modify `rst2md/tests/test_search_eval.py`: metadata, invalid DB, category coverage, promotion tests.
- Modify `rst2md/tests/test_search_eval_cli.py`: CLI failure and JSON warning behavior.
- Modify `rst2md/tests/test_searcher_module.py`: `QueryPlan` and query rewrite unit tests.
- Modify `rst2md/tests/test_semantic_search.py` or `rst2md/tests/test_rag_search.py`: integration-style ranking tests using fixture databases.
- Modify `rst2md/rag/search_eval_queries.json`: promote only passing natural-language symbol queries after verification.
- Modify `docs/search-quality/baseline.json`: refresh after implementation passes.

## Task 1: Baseline Metadata and Database Validation

**Files:**
- Modify: `rst2md/rag/search_eval.py`
- Test: `rst2md/tests/test_search_eval.py`

**Interfaces:**
- Produces: `DatabaseFingerprint`, `query_suite_hash()`, `database_fingerprint()`, `validate_baseline_input()`.
- Consumes: existing `GoldenQuery`, `EvaluationReport`, `report_to_dict()`, `apply_baseline()`.

- [x] **Step 1: Write failing tests for query hash and invalid baseline database**

Add tests to `rst2md/tests/test_search_eval.py`:

```python
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
```

- [x] **Step 2: Run tests and verify they fail**

Run:

```bash
rtk uv run pytest rst2md/tests/test_search_eval.py -q
```

Expected: failures for missing `DatabaseFingerprint`, `query_suite_hash`, or `validate_baseline_input`.

- [x] **Step 3: Implement metadata helpers**

Add to `rst2md/rag/search_eval.py`:

```python
@dataclass(frozen=True)
class DatabaseFingerprint:
    path: str
    size_bytes: int
    documents: int
    chunks: int
    symbols: int
    vectors: int | None


def query_suite_hash(queries: Sequence[GoldenQuery]) -> str:
    payload = [
        {
            "id": query.id,
            "query": query.query,
            "category": query.category,
            "required_at": query.required_at,
            "expected_symbols": list(query.expected_symbols),
            "expected_paths": list(query.expected_paths),
            "expected_doc_types": list(query.expected_doc_types),
            "expected_addons": list(query.expected_addons),
            "tags": list(query.tags),
            "report_only": query.report_only,
        }
        for query in sorted(queries, key=lambda item: item.id)
    ]
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
```

Implement `database_fingerprint(db_path)` with SQLite `COUNT(*)` queries for `documents`, `chunks`, `symbols`, and optional `vec_chunks`. Implement `validate_baseline_input()` to return messages, not raise directly.

- [x] **Step 4: Run tests and verify they pass**

Run:

```bash
rtk uv run pytest rst2md/tests/test_search_eval.py -q
```

Expected: existing tests and the new metadata tests pass.

- [x] **Step 5: Commit Task 1**

```bash
rtk git add rst2md/rag/search_eval.py rst2md/tests/test_search_eval.py
rtk git commit -m "feat: add search baseline input metadata"
```

## Task 2: Baseline Write Guard, Drift Reporting, and Category Coverage

**Files:**
- Modify: `rst2md/rag/search_eval.py`
- Modify: `rst2md/rag/cli.py`
- Test: `rst2md/tests/test_search_eval.py`
- Test: `rst2md/tests/test_search_eval_cli.py`

**Interfaces:**
- Consumes: Task 1 metadata helpers.
- Produces: report metadata in `report_to_dict()`, baseline validation failure behavior, category coverage warnings.

- [x] **Step 1: Write failing tests for baseline metadata and validation**

Add tests:

```python
def test_apply_baseline_writes_metadata(tmp_path):
    from rag.search_eval import (
        DatabaseFingerprint,
        EvaluationReport,
        apply_baseline,
        report_to_dict,
    )

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


def test_baseline_write_rejects_invalid_database(tmp_path):
    from rag.search_eval import DatabaseFingerprint, EvaluationReport, apply_baseline

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
```

- [x] **Step 2: Write failing tests for category coverage warning**

Add a test that creates an `EvaluationReport` with no gating addon queries and asserts `report_to_dict(report)["category_warnings"]` contains `"addon"`.

- [x] **Step 3: Run focused tests and verify they fail**

```bash
rtk uv run pytest rst2md/tests/test_search_eval.py rst2md/tests/test_search_eval_cli.py -q
```

- [x] **Step 4: Implement report metadata and warning output**

Add fields to `EvaluationReport`:

```python
database: DatabaseFingerprint | None = None
query_suite_hash: str = ""
category_warnings: tuple[str, ...] = ()
baseline_warnings: tuple[str, ...] = ()
```

In `evaluate_database()`, compute `database_fingerprint(db_path)`, `query_suite_hash(queries)`, and category warnings. In `apply_baseline()`, reject invalid baseline writes before writing. In baseline compare, compare `baseline["metadata"]["query_suite_hash"]` with the current hash and append a baseline warning without setting `regression_failed`.

- [x] **Step 5: Update CLI error behavior**

In `rst2md/rag/cli.py`, let `ValueError` from baseline writing surface as a non-zero command with a clear message. If there is an existing CLI error pattern in the file, use it; otherwise print to stderr and raise `SystemExit(1)`.

- [x] **Step 6: Run tests and commit**

```bash
rtk uv run pytest rst2md/tests/test_search_eval.py rst2md/tests/test_search_eval_cli.py -q
rtk git add rst2md/rag/search_eval.py rst2md/rag/cli.py rst2md/tests/test_search_eval.py rst2md/tests/test_search_eval_cli.py
rtk git commit -m "feat: guard search quality baseline writes"
```

## Task 3: QueryPlan Construction

**Files:**
- Create: `rst2md/rag/query_plan.py`
- Modify: `rst2md/rag/query_rewrite.py`
- Modify: `rst2md/tests/test_searcher_module.py`

**Interfaces:**
- Produces: `QueryPlan`, `build_query_plan(query: str) -> QueryPlan`.
- Consumes: existing `expand_query_variants()` and alias rules.

- [x] **Step 1: Write failing QueryPlan unit tests**

Add to `rst2md/tests/test_searcher_module.py`:

```python
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
```

- [x] **Step 2: Run tests and verify they fail**

```bash
rtk uv run pytest rst2md/tests/test_search_eval.py -q
```

- [x] **Step 3: Implement `query_plan.py`**

Create `rst2md/rag/query_plan.py` with a frozen dataclass. Reuse `normalize_symbol()` from `rag.symbols` and `expand_query_variants()` from `rag.query_rewrite`. Keep intent detection conservative:

```python
def _doc_type_intent(query: str) -> str | None:
    lowered = query.lower()
    if "." in query or "_" in query:
        return None
    if lowered.startswith("how to ") or " tutorial" in lowered or " guide" in lowered or "learn " in lowered:
        return "tutorial"
    return None
```

For addon intent, return `"addon"` when tokens include `"addon"` or `"plugin"`.

- [x] **Step 4: Preserve existing query rewrite behavior**

Ensure these existing tests still pass:

```bash
rtk uv run pytest rst2md/tests/test_searcher_module.py::test_expand_query_variants_adds_node_add_child_alias rst2md/tests/test_searcher_module.py::test_expand_query_variants_deduplicates_exact_symbol_query -q
```

- [x] **Step 5: Run tests and commit**

```bash
rtk uv run pytest rst2md/tests/test_searcher_module.py -q
rtk git add rst2md/rag/query_plan.py rst2md/rag/query_rewrite.py rst2md/tests/test_searcher_module.py
rtk git commit -m "feat: add structured search query plan"
```

## Task 4: Wire QueryPlan Into Symbol Recall

**Files:**
- Modify: `rst2md/rag/searcher.py`
- Test: `rst2md/tests/test_semantic_search.py`
- Test: `rst2md/tests/test_rag_search.py` if the existing fixture is easier there

**Interfaces:**
- Consumes: `build_query_plan()`, `QueryPlan.symbol_candidates`.
- Produces: helper functions for symbol candidate recall inside `_search_database_impl()`.

- [x] **Step 1: Write failing integration test for alias symbol recall**

Use the existing fixture pattern in `rst2md/tests/test_semantic_search.py`. Add a test that builds or reuses a DB containing `Node.add_child`, searches `"attach node to scene tree"` with `expand_graph=False`, and asserts `Node.add_child` appears in top 5.

```python
def test_alias_query_uses_symbol_recall(db_path):
    from rag.searcher import search_database

    results = search_database(db_path, "attach node to scene tree", limit=5, expand_graph=False)

    assert any(result.symbol == "Node.add_child" for result in results)
```

If the file uses a different fixture name, adapt only the fixture argument, not the assertion.

- [x] **Step 2: Run the focused test and verify it fails**

```bash
rtk uv run pytest rst2md/tests/test_semantic_search.py -q
```

- [x] **Step 3: Implement symbol candidate recall**

In `rst2md/rag/searcher.py`:

1. Import `build_query_plan`.
2. Build `plan = build_query_plan(query)` at the start of `_search_database_impl()`.
3. Replace single `normalized = normalize_symbol(query)` symbol lookup with loops over `plan.symbol_candidates`.
4. Keep scoring tiers compatible with the current exact `100`, suffix `80`, prefix `40` behavior.
5. Deduplicate by chunk ID through the existing `results` dict.

- [x] **Step 4: Ensure FTS still uses variants and vector still uses original query**

Keep `_run_vector_query()` input as `query` or `plan.original`. Use `plan.fts_variants` in the FTS loop instead of calling `expand_query_variants(query)` directly.

- [x] **Step 5: Run tests and commit**

```bash
rtk uv run pytest rst2md/tests/test_semantic_search.py rst2md/tests/test_searcher_module.py -q
rtk git add rst2md/rag/searcher.py rst2md/tests/test_semantic_search.py
rtk git commit -m "feat: use query plan for symbol recall"
```

## Task 5: Deterministic Reranking Signals

**Files:**
- Modify: `rst2md/rag/searcher.py`
- Modify: `rst2md/rag/query_plan.py` if helper properties are useful
- Test: `rst2md/tests/test_searcher_module.py`
- Test: `rst2md/tests/test_semantic_search.py`

**Interfaces:**
- Produces: `rerank_results(plan: QueryPlan, results: list[SearchResult]) -> list[SearchResult]`.
- Replaces: `_apply_intent_boost(query, results)` call site.

- [x] **Step 1: Write failing unit tests for reranking**

Add tests with constructed `SearchResult` objects:

```python
def test_rerank_promotes_alias_symbol_match():
    from rag.models import SearchResult
    from rag.query_plan import build_query_plan
    from rag.searcher import rerank_results

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
```

Add a second test proving `build_query_plan("Node.add_child")` keeps symbol behavior and does not apply tutorial intent.

- [x] **Step 2: Run tests and verify they fail**

```bash
rtk uv run pytest rst2md/tests/test_searcher_module.py -q
```

- [x] **Step 3: Implement named reranking signals**

In `rst2md/rag/searcher.py`, add helpers:

```python
def _rerank_bonus(plan: QueryPlan, result: SearchResult) -> float:
    bonus = 0.0
    if result.symbol in plan.alias_symbol_candidates:
        bonus += 5.0
    elif result.symbol in plan.symbol_candidates:
        bonus += 2.0
    if plan.doc_type_intent and result.doc_type == plan.doc_type_intent and not plan.symbol_candidates:
        bonus += 0.05
    if plan.addon_intent and result.doc_type == "addon":
        bonus += 0.5
    return bonus
```

Use `replace(result, score=result.score + bonus)` and stable sort descending by score. Adjust values only if tests show existing exact symbol ranking is harmed; document any changed constants near the helper.

- [x] **Step 4: Replace `_apply_intent_boost()` call**

Change final ranking from:

```python
search_results = _apply_intent_boost(query, search_results)
```

to:

```python
search_results = rerank_results(plan, search_results)
```

Remove or keep `_apply_intent_boost()` only if tests still import it. If kept, make it a compatibility wrapper around `build_query_plan()` and `rerank_results()`.

- [x] **Step 5: Run tests and commit**

```bash
rtk uv run pytest rst2md/tests/test_searcher_module.py rst2md/tests/test_semantic_search.py -q
rtk git add rst2md/rag/searcher.py rst2md/rag/query_plan.py rst2md/tests/test_searcher_module.py rst2md/tests/test_semantic_search.py
rtk git commit -m "feat: rerank search results with query plan signals"
```

## Task 6: Promotion Checks, Query Fixture, and Baseline Refresh

**Files:**
- Modify: `rst2md/rag/search_eval.py`
- Modify: `rst2md/rag/search_eval_queries.json`
- Modify: `docs/search-quality/baseline.json`
- Test: `rst2md/tests/test_search_eval.py`

**Interfaces:**
- Consumes: failure diagnostics and `QueryResult`.
- Produces: promotion eligibility checks and refreshed baseline.

- [x] **Step 1: Write failing tests for promotion eligibility**

Add tests:

```python
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
```

If implementing promotion eligibility directly from `QueryResult` is cleaner, adjust the test to construct `QueryResult` and `FailureDiagnostics`, but keep the same assertions.

- [x] **Step 2: Run tests and verify they fail**

```bash
rtk uv run pytest rst2md/tests/test_searcher_module.py -q
```

- [x] **Step 3: Implement promotion status**

Add:

```python
@dataclass(frozen=True)
class PromotionStatus:
    eligible: bool
    reason: str
```

Implement promotion logic with explicit reasons: `not_report_only`, `expected_not_present`, `not_passing`, `rank_too_low`, `eligible`, `addon_data_unstable`.

- [x] **Step 4: Run canonical eval to decide promotions**

Run:

```bash
rtk uv run godot-rag eval-search --db godot_rag.db --baseline docs/search-quality/baseline.json --compare-graph --json
```

Inspect the JSON summary for natural-language symbol queries:

- `node-add-child-natural`
- `timer-stopped-natural`
- `signal-emit-natural`

Promote only the ones now passing within `required_at` and with expected targets present.

- [x] **Step 5: Update query fixture and refresh baseline**

Edit `rst2md/rag/search_eval_queries.json` by removing `"report_only": true` only from passing natural-language symbol queries. Do not promote addon queries in this task.

Refresh baseline:

```bash
rtk uv run godot-rag eval-search --db godot_rag.db --baseline docs/search-quality/baseline.json --write-baseline --compare-graph
```

Then verify:

```bash
rtk uv run godot-rag eval-search --db godot_rag.db --baseline docs/search-quality/baseline.json --compare-graph
```

Expected: non-report-only failures are zero, baseline comparison succeeds, and metadata is present in `docs/search-quality/baseline.json`.

- [x] **Step 6: Run final focused suite and commit**

```bash
rtk uv run pytest rst2md/tests/test_search_eval.py rst2md/tests/test_search_eval_cli.py rst2md/tests/test_searcher_module.py rst2md/tests/test_semantic_search.py -q
rtk git add rst2md/rag/search_eval.py rst2md/rag/search_eval_queries.json docs/search-quality/baseline.json rst2md/tests/test_search_eval.py
rtk git commit -m "feat: promote stable search quality queries"
```

## Final Verification

- [x] Run focused tests:

```bash
rtk uv run pytest rst2md/tests/test_search_eval.py rst2md/tests/test_search_eval_cli.py rst2md/tests/test_searcher_module.py rst2md/tests/test_semantic_search.py -q
```

- [x] Run baseline comparison:

```bash
rtk uv run godot-rag eval-search --db godot_rag.db --baseline docs/search-quality/baseline.json --compare-graph
```

- [x] Run build:

```bash
rtk uv build
```

- [x] Update OpenSpec task checkboxes in `openspec/changes/stabilize-search-quality-loop/tasks.md`.

- [x] Commit final task/status updates:

```bash
rtk git add openspec/changes/stabilize-search-quality-loop/tasks.md
rtk git commit -m "chore: complete search quality loop tasks"
```

## Execution Handoff

Plan complete. Before implementation starts, choose:

1. Subagent-Driven - one background worker per task with main-session review.
2. Inline Execution - execute tasks in this session with checkpoints.

Implementation must not start until the user explicitly confirms execution mode, isolation, TDD mode, and review mode.
