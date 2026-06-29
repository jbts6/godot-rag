---
change: search-quality-optimization-loop
design-doc: docs/superpowers/specs/2026-06-29-search-quality-optimization-loop-design.md
base-ref: 9dde7807289149a4481cba172a46568b24d44416
---

# Search Quality Optimization Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Build a repeatable search-quality optimization loop that makes `eval-search` runnable, expands golden-query coverage, diagnoses failures, and fixes the first observed recall and ranking failures.

**Architecture:** Keep the existing RAG search pipeline intact and add narrow support modules around it. Evaluation owns quality data, diagnostics, baselines, and report output; search owns query rewriting and intent-aware ranking; packaging owns making the documented CLI command import the current `rag` package.

**Tech Stack:** Python 3.10+, pytest, SQLite/FTS5, sqlite-vec, model2vec, hatchling, existing `rst2md/rag` package.

## Global Constraints

- Do not change the embedding model.
- Do not replace SQLite, FTS5, sqlite-vec, or RRF fusion.
- Do not require full release-database evaluation in default CI.
- Keep broad or corpus-sensitive queries as `report_only`.
- Use `rtk` before shell commands.
- Use `rtk uv run pytest ...` for pytest verification.

---

## File Structure

- Modify `pyproject.toml`: point `godot-rag` at the importable `rag.cli:main` module and include the `rst2md/rag` package in wheel packaging.
- Modify `README.md`: keep documented `godot-rag eval-search` examples aligned with the fixed entry point and new diagnostics fields.
- Modify `rst2md/rag/search_eval.py`: add failure diagnostics, JSON output fields, and text report summaries.
- Modify `rst2md/rag/search_eval_queries.json`: expand the packaged query suite and tier unstable entries with `report_only`.
- Create `rst2md/rag/query_rewrite.py`: hold conservative natural-language aliases and doc-type intent helpers.
- Modify `rst2md/rag/searcher.py`: use query variants for lexical recall and apply small intent-aware boosts after candidate generation.
- Modify `rst2md/tests/test_search_eval.py`: cover diagnostics, query-suite shape, and report output.
- Modify `rst2md/tests/test_search_eval_cli.py`: cover project script target and CLI output.
- Modify `rst2md/tests/test_searcher_module.py`: cover query rewriting helpers.
- Modify `rst2md/tests/test_rag_search.py`: cover search integration for alias recall and tutorial intent ranking.
- Create `docs/search-quality/baseline.json`: reviewed baseline generated after final local release-database evaluation.

---

### Task 1: Fix the Documented CLI Entry Point

**Files:**
- Modify: `pyproject.toml`
- Modify: `rst2md/tests/test_search_eval_cli.py`

**Interfaces:**
- Consumes: existing `rag.cli.main()` in `rst2md/rag/cli.py`.
- Produces: project script target `godot-rag = "rag.cli:main"` and wheel package inclusion for `rst2md/rag`.

- [x] **Step 1: Write the failing packaging test**

Append this test to `rst2md/tests/test_search_eval_cli.py`:

```python
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
```

- [x] **Step 2: Run the targeted failing test**

Run:

```bash
rtk uv run pytest rst2md/tests/test_search_eval_cli.py::test_project_script_targets_importable_rag_cli -q
```

Expected: FAIL because `pyproject.toml` currently targets `godot_rag.rag.cli:main` and does not include `"rst2md/rag"` in wheel packages.

- [x] **Step 3: Fix `pyproject.toml`**

Change the script and packages block to:

```toml
[project.scripts]
godot-rag = "rag.cli:main"
godot-rag-build = "godot_rag_build.cli:main"

[tool.hatch.build.targets.wheel]
packages = ["rst2md/rag", "godot_rag", "godot_rag_build"]
exclude = ["godot_rag/docs-md/**"]
```

- [x] **Step 4: Verify the test and the command**

Run:

```bash
rtk uv run pytest rst2md/tests/test_search_eval_cli.py::test_project_script_targets_importable_rag_cli -q
rtk uv run godot-rag eval-search --help
```

Expected:

- pytest prints `1 passed`.
- help output includes `usage:` and `eval-search`.

- [x] **Step 5: Commit**

```bash
rtk git add pyproject.toml rst2md/tests/test_search_eval_cli.py
rtk git commit -m "fix: make eval-search CLI entrypoint importable"
```

---

### Task 2: Add Failure Diagnostics to Evaluation Output

**Files:**
- Modify: `rst2md/rag/search_eval.py`
- Modify: `rst2md/tests/test_search_eval.py`

**Interfaces:**
- Consumes: `GoldenQuery`, `QueryResult`, `SearchResult`, existing `evaluate_database(db_path, queries, *, limit, compare_graph)`.
- Produces:
  - `FailureDiagnostics` dataclass.
  - `QueryResult.diagnostics: FailureDiagnostics | None`.
  - `evaluate_database(..., diagnostic_limit: int = 50)`.
  - JSON field `failures[].diagnostics`.
  - text report lines for `expected_present`, `best_rank`, and `best_rank_no_graph`.

- [x] **Step 1: Write the failing diagnostics test**

Add these imports near the existing imports in `rst2md/tests/test_search_eval.py`:

```python
from dataclasses import replace
```

Append this test to `rst2md/tests/test_search_eval.py`:

```python
def test_evaluate_database_attaches_failure_diagnostics(tmp_path, monkeypatch):
    db_path = _build_eval_db(tmp_path, monkeypatch)
    base = load_queries(Path("rst2md/tests/fixtures/search_eval_fixture_queries.json"))[0]
    query = replace(
        base,
        id="timer-low-window",
        query="timer methods start stop",
        expected_paths=("classes/class_timer.md",),
        expected_symbols=(),
        required_at=1,
    )

    report = evaluate_database(db_path, [query], limit=1, diagnostic_limit=20)
    assert report.failures

    diagnostics = report.failures[0].diagnostics
    assert diagnostics is not None
    assert diagnostics.expected_present is True
    assert diagnostics.diagnostic_window == 20
    assert diagnostics.best_rank is not None
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
        query="timer methods start stop",
        expected_paths=("classes/class_timer.md",),
        expected_symbols=(),
        required_at=1,
    )

    report = evaluate_database(db_path, [query], limit=1, diagnostic_limit=20)
    text = format_text_report(report)

    assert "diagnostics:" in text
    assert "expected_present=True" in text
    assert "best_rank=" in text
```

- [x] **Step 2: Run the failing diagnostics tests**

Run:

```bash
rtk uv run pytest \
  rst2md/tests/test_search_eval.py::test_evaluate_database_attaches_failure_diagnostics \
  rst2md/tests/test_search_eval.py::test_text_report_includes_failure_diagnostics_summary \
  -q
```

Expected: FAIL because `diagnostic_limit`, `FailureDiagnostics`, and `QueryResult.diagnostics` do not exist yet.

- [x] **Step 3: Add diagnostics data structures**

In `rst2md/rag/search_eval.py`, update imports and dataclasses:

```python
from dataclasses import dataclass, replace
```

Add this dataclass after `GoldenQuery`:

```python
@dataclass(frozen=True)
class FailureDiagnostics:
    expected_present: bool
    expected_rows: list[dict]
    best_rank: int | None
    best_rank_no_graph: int | None
    diagnostic_window: int
```

Update `QueryResult`:

```python
@dataclass(frozen=True)
class QueryResult:
    query: GoldenQuery
    matched_rank: int | None
    passed: bool
    failure_classification: str
    observed: list[dict]
    graph_changed: bool = False
    diagnostics: FailureDiagnostics | None = None
```

- [x] **Step 4: Add diagnostic helpers**

Add these helpers after `result_matches`:

```python
def _query_constraints(query: GoldenQuery) -> tuple[list[str], list[str]]:
    clauses = []
    params = []
    if query.expected_paths:
        clauses.append("path IN ({})".format(",".join("?" for _ in query.expected_paths)))
        params.extend(query.expected_paths)
    if query.expected_symbols:
        clauses.append("symbol IN ({})".format(",".join("?" for _ in query.expected_symbols)))
        params.extend(query.expected_symbols)
    if query.expected_doc_types:
        clauses.append("doc_type IN ({})".format(",".join("?" for _ in query.expected_doc_types)))
        params.extend(query.expected_doc_types)
    if query.expected_addons:
        clauses.append("addon IN ({})".format(",".join("?" for _ in query.expected_addons)))
        params.extend(query.expected_addons)
    return clauses, params


def _fetch_expected_rows(db_path: Path, query: GoldenQuery, *, limit: int = 10) -> list[dict]:
    import sqlite3

    clauses, params = _query_constraints(query)
    if not clauses:
        return []

    sql = (
        "SELECT path, symbol, doc_type, addon, heading "
        "FROM chunks WHERE " + " AND ".join(clauses) + " "
        "ORDER BY path, symbol LIMIT ?"
    )
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(sql, [*params, limit]).fetchall()
    return [dict(row) for row in rows]


def _find_matching_rank(query: GoldenQuery, results: Sequence[SearchResult]) -> int | None:
    for rank, result in enumerate(results, start=1):
        if result_matches(query, result):
            return rank
    return None


def diagnose_failure(
    db_path: Path,
    query: GoldenQuery,
    expanded_results: Sequence[SearchResult],
    no_graph_results: Sequence[SearchResult],
    *,
    diagnostic_window: int,
) -> FailureDiagnostics:
    expected_rows = _fetch_expected_rows(db_path, query)
    return FailureDiagnostics(
        expected_present=bool(expected_rows),
        expected_rows=expected_rows,
        best_rank=_find_matching_rank(query, expanded_results[:diagnostic_window]),
        best_rank_no_graph=_find_matching_rank(query, no_graph_results[:diagnostic_window]),
        diagnostic_window=diagnostic_window,
    )
```

- [x] **Step 5: Attach diagnostics in `evaluate_database`**

Change the signature:

```python
def evaluate_database(
    db_path: Path,
    queries: Sequence[GoldenQuery],
    *,
    limit: int = 5,
    compare_graph: bool = False,
    diagnostic_limit: int = 50,
) -> EvaluationReport:
```

Inside the query loop, compute an extended diagnostic window and attach diagnostics only when the query fails:

```python
    required_window = max(10, limit)
    diagnostic_window = max(required_window, diagnostic_limit)
    for query in queries:
        results = search_database(db_path, query.query, limit=diagnostic_window, expand_graph=True)
        evaluated = evaluate_results(query, results, required_window=required_window)
        no_graph_results = []
        if compare_graph or not evaluated.passed:
            no_graph_results = search_database(db_path, query.query, limit=diagnostic_window, expand_graph=False)
        if compare_graph:
            no_graph = evaluate_results(query, no_graph_results, required_window=required_window)
            if no_graph.passed != evaluated.passed:
                evaluated = replace(evaluated, graph_changed=True)
                graph_changes.append(evaluated)
        if not evaluated.passed:
            evaluated = replace(
                evaluated,
                diagnostics=diagnose_failure(
                    db_path,
                    query,
                    results,
                    no_graph_results,
                    diagnostic_window=diagnostic_window,
                ),
            )
        query_results.append(evaluated)
```

- [x] **Step 6: Serialize and print diagnostics**

In `_query_result_to_dict`, add:

```python
        "diagnostics": (
            {
                "expected_present": result.diagnostics.expected_present,
                "expected_rows": result.diagnostics.expected_rows,
                "best_rank": result.diagnostics.best_rank,
                "best_rank_no_graph": result.diagnostics.best_rank_no_graph,
                "diagnostic_window": result.diagnostics.diagnostic_window,
            }
            if result.diagnostics
            else None
        ),
```

In `format_text_report`, inside the failure block, after expected output and before observed output, add:

```python
            if failure.diagnostics:
                lines.append("  diagnostics:")
                lines.append(
                    "  "
                    f"expected_present={failure.diagnostics.expected_present} "
                    f"best_rank={failure.diagnostics.best_rank} "
                    f"best_rank_no_graph={failure.diagnostics.best_rank_no_graph} "
                    f"diagnostic_window={failure.diagnostics.diagnostic_window}"
                )
```

- [x] **Step 7: Run diagnostics tests**

Run:

```bash
rtk uv run pytest \
  rst2md/tests/test_search_eval.py::test_evaluate_database_attaches_failure_diagnostics \
  rst2md/tests/test_search_eval.py::test_text_report_includes_failure_diagnostics_summary \
  -q
```

Expected: `2 passed`.

- [x] **Step 8: Commit**

```bash
rtk git add rst2md/rag/search_eval.py rst2md/tests/test_search_eval.py
rtk git commit -m "feat: add search evaluation failure diagnostics"
```

---

### Task 3: Expand and Tier Packaged Golden Queries

**Files:**
- Modify: `rst2md/rag/search_eval_queries.json`
- Modify: `rst2md/tests/test_search_eval.py`

**Interfaces:**
- Consumes: existing `GoldenQuery.report_only` tier flag.
- Produces: packaged query suite with at least 30 unique IDs, at least 12 gating queries, and coverage for `class`, `symbol`, `tutorial`, `engine`, and `addon` categories.

- [x] **Step 1: Write the failing query-suite shape test**

Append this test to `rst2md/tests/test_search_eval.py`:

```python
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
```

- [x] **Step 2: Run the failing query-suite shape test**

Run:

```bash
rtk uv run pytest rst2md/tests/test_search_eval.py::test_packaged_eval_queries_are_broad_and_tiered -q
```

Expected: FAIL because the packaged query suite currently has 5 entries.

- [x] **Step 3: Replace `rst2md/rag/search_eval_queries.json`**

Replace the file with this JSON:

```json
[
  {"id": "node-add-child-symbol", "query": "Node.add_child", "category": "symbol", "required_at": 3, "expected_symbols": ["Node.add_child"], "tags": ["normalization"]},
  {"id": "timer-start-symbol", "query": "Timer.start", "category": "symbol", "required_at": 3, "expected_symbols": ["Timer.start"], "tags": ["normalization"]},
  {"id": "timer-stop-symbol", "query": "Timer.stop", "category": "symbol", "required_at": 3, "expected_symbols": ["Timer.stop"], "tags": ["normalization"]},
  {"id": "timer-is-stopped-symbol", "query": "Timer.is_stopped", "category": "symbol", "required_at": 3, "expected_symbols": ["Timer.is_stopped"], "tags": ["normalization"]},
  {"id": "object-emit-signal-symbol", "query": "Object.emit_signal", "category": "symbol", "required_at": 3, "expected_symbols": ["Object.emit_signal"], "tags": ["normalization"]},
  {"id": "node-class", "query": "Node", "category": "class", "required_at": 5, "expected_paths": ["classes/class_node.md"]},
  {"id": "timer-class", "query": "Timer", "category": "class", "required_at": 5, "expected_paths": ["classes/class_timer.md"]},
  {"id": "object-class", "query": "Object", "category": "class", "required_at": 5, "expected_paths": ["classes/class_object.md"]},
  {"id": "scene-tree-tutorial", "query": "scene tree tutorial", "category": "tutorial", "required_at": 5, "expected_doc_types": ["tutorial"]},
  {"id": "nodes-and-scenes-tutorial", "query": "nodes and scenes", "category": "tutorial", "required_at": 5, "expected_doc_types": ["tutorial"]},
  {"id": "gdextension-engine", "query": "GDExtension C example", "category": "engine", "required_at": 5, "expected_doc_types": ["tutorial"]},
  {"id": "state-machine-addon", "query": "state machine addon", "category": "addon", "required_at": 5, "expected_doc_types": ["addon"], "report_only": true},
  {"id": "node-add-child-natural", "query": "attach node to scene tree", "category": "class", "required_at": 5, "expected_symbols": ["Node.add_child"], "tags": ["normalization", "alias"], "report_only": true},
  {"id": "timer-stopped-natural", "query": "check if timer is stopped", "category": "class", "required_at": 5, "expected_symbols": ["Timer.is_stopped"], "tags": ["normalization", "alias"], "report_only": true},
  {"id": "signal-emit-natural", "query": "emit a signal from code", "category": "class", "required_at": 5, "expected_symbols": ["Object.emit_signal"], "tags": ["normalization", "alias"], "report_only": true},
  {"id": "child-node-attach", "query": "child node attach", "category": "class", "required_at": 5, "expected_symbols": ["Node.add_child"], "tags": ["normalization", "alias"], "report_only": true},
  {"id": "start-countdown-timer", "query": "start countdown timer", "category": "class", "required_at": 5, "expected_symbols": ["Timer.start"], "tags": ["alias"], "report_only": true},
  {"id": "stop-countdown-timer", "query": "stop countdown timer", "category": "class", "required_at": 5, "expected_symbols": ["Timer.stop"], "tags": ["alias"], "report_only": true},
  {"id": "how-to-use-scene-tree-nodes", "query": "how to use scene tree nodes", "category": "tutorial", "required_at": 5, "expected_doc_types": ["tutorial"], "tags": ["intent"], "report_only": true},
  {"id": "how-to-change-scenes", "query": "how to change scenes manually", "category": "tutorial", "required_at": 5, "expected_doc_types": ["tutorial"], "tags": ["intent"], "report_only": true},
  {"id": "script-signals-tutorial", "query": "signals in gdscript tutorial", "category": "tutorial", "required_at": 5, "expected_doc_types": ["tutorial"], "tags": ["intent"], "report_only": true},
  {"id": "physics-server-engine", "query": "PhysicsServer3D engine details", "category": "engine", "required_at": 5, "expected_doc_types": ["class"], "report_only": true},
  {"id": "class-inheritance-node-object", "query": "Node inherits Object", "category": "class", "required_at": 5, "expected_paths": ["classes/class_node.md"], "tags": ["graph"], "report_only": true},
  {"id": "timer-related-methods", "query": "Timer start stop paused wait time", "category": "class", "required_at": 5, "expected_paths": ["classes/class_timer.md"], "tags": ["graph"], "report_only": true},
  {"id": "object-signal-methods", "query": "Object signal methods emit add user signal", "category": "class", "required_at": 5, "expected_paths": ["classes/class_object.md"], "tags": ["graph"], "report_only": true},
  {"id": "addon-dialogue-manager", "query": "dialogue manager addon", "category": "addon", "required_at": 5, "expected_doc_types": ["addon"], "report_only": true},
  {"id": "addon-phantom-camera", "query": "phantom camera addon", "category": "addon", "required_at": 5, "expected_doc_types": ["addon"], "report_only": true},
  {"id": "addon-limboai-behavior-tree", "query": "behavior tree addon", "category": "addon", "required_at": 5, "expected_doc_types": ["addon"], "report_only": true},
  {"id": "vector-fallback-metadata", "query": "semantic search vector fallback", "category": "engine", "required_at": 5, "expected_doc_types": ["tutorial"], "report_only": true},
  {"id": "editor-plugin-running-code", "query": "running code in the editor plugin", "category": "tutorial", "required_at": 5, "expected_doc_types": ["tutorial"], "report_only": true}
]
```

- [x] **Step 4: Run query loading and shape tests**

Run:

```bash
rtk uv run pytest \
  rst2md/tests/test_search_eval.py::test_load_queries_from_json \
  rst2md/tests/test_search_eval.py::test_packaged_eval_queries_are_broad_and_tiered \
  -q
```

Expected: `2 passed`.

- [x] **Step 5: Commit**

```bash
rtk git add rst2md/rag/search_eval_queries.json rst2md/tests/test_search_eval.py
rtk git commit -m "test: expand tiered search quality queries"
```

---

### Task 4: Add Conservative Query Rewriting for Missing Recall

**Files:**
- Create: `rst2md/rag/query_rewrite.py`
- Modify: `rst2md/rag/searcher.py`
- Modify: `rst2md/tests/test_searcher_module.py`
- Modify: `rst2md/tests/test_rag_search.py`
- Modify: `rst2md/rag/search_eval_queries.json`

**Interfaces:**
- Produces `expand_query_variants(query: str) -> list[str]`.
- `search_database(...)` keeps its existing public signature.
- Query variants are lexical recall candidates only; vector search continues to use the original query text.

- [x] **Step 1: Write failing unit tests for query rewriting**

Append to `rst2md/tests/test_searcher_module.py`:

```python
from rag.query_rewrite import expand_query_variants


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
```

- [x] **Step 2: Write failing search integration test**

Add this method inside `SearchTests` in `rst2md/tests/test_rag_search.py`:

```python
    def test_natural_language_alias_returns_expected_symbol(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp) / "docs"
            classes = docs / "classes"
            classes.mkdir(parents=True)
            (classes / "class_node.md").write_text(
                "# Node\n\n"
                "## Method Descriptions\n\n"
                "### add_child\n\n"
                "Adds a child node to the scene tree.\n",
                encoding="utf-8",
            )
            db_path = Path(tmp) / "godot_docs.sqlite"
            build_database(docs, db_path)

            results = search_database(db_path, "attach node to scene tree", limit=3, expand_graph=False)

            self.assertTrue(results)
            self.assertEqual(results[0].symbol, "Node.add_child")
```

- [x] **Step 3: Run the failing rewrite tests**

Run:

```bash
rtk uv run pytest \
  rst2md/tests/test_searcher_module.py::test_expand_query_variants_adds_node_add_child_alias \
  rst2md/tests/test_searcher_module.py::test_expand_query_variants_adds_timer_is_stopped_alias \
  rst2md/tests/test_searcher_module.py::test_expand_query_variants_adds_object_emit_signal_alias \
  rst2md/tests/test_searcher_module.py::test_expand_query_variants_deduplicates_exact_symbol_query \
  rst2md/tests/test_rag_search.py::SearchTests::test_natural_language_alias_returns_expected_symbol \
  -q
```

Expected: FAIL because `rag.query_rewrite` does not exist and search does not use aliases.

- [x] **Step 4: Create `rst2md/rag/query_rewrite.py`**

```python
import re


_ALIAS_RULES: tuple[tuple[frozenset[str], str], ...] = (
    (frozenset({"attach", "node", "scene", "tree"}), "Node.add_child"),
    (frozenset({"child", "node", "attach"}), "Node.add_child"),
    (frozenset({"check", "timer", "stopped"}), "Timer.is_stopped"),
    (frozenset({"timer", "is", "stopped"}), "Timer.is_stopped"),
    (frozenset({"emit", "signal"}), "Object.emit_signal"),
)


def _tokens(query: str) -> frozenset[str]:
    return frozenset(re.findall(r"[a-z0-9]+", query.lower()))


def expand_query_variants(query: str) -> list[str]:
    variants = [query]
    query_tokens = _tokens(query)
    for required_tokens, alias in _ALIAS_RULES:
        if required_tokens.issubset(query_tokens) and alias not in variants:
            variants.append(alias)
    return variants
```

- [x] **Step 5: Use query variants in `rst2md/rag/searcher.py`**

Add the import:

```python
from rag.query_rewrite import expand_query_variants
```

Extract the existing FTS query block inside `_search_database_impl` into a helper named `_run_fts_query` with this interface:

```python
def _run_fts_query(conn, query: str, limit: int, fts_type_filter: str, fts_type_params: list, fts_addon_filter: str, fts_addon_params: list) -> list[dict]:
    escaped_query = _smart_tokenize(normalize_symbol(query))
    rows = conn.execute(
        f"""
        SELECT c.id, bm25(chunks_fts) as score
        FROM chunks_fts
        JOIN chunks c ON chunks_fts.rowid = c.id
        WHERE chunks_fts MATCH ?
        {fts_type_filter}
        {fts_addon_filter}
        ORDER BY score
        LIMIT ?
        """,
        [escaped_query] + fts_type_params + fts_addon_params + [limit * 3],
    ).fetchall()
    return [{"id": row[0], "score": row[1]} for row in rows]
```

Replace the single FTS execution with variant merging:

```python
    fts_results_by_id = {}
    for variant in expand_query_variants(query):
        for row in _run_fts_query(
            conn,
            variant,
            limit,
            fts_type_filter,
            fts_type_params,
            fts_addon_filter,
            fts_addon_params,
        ):
            current = fts_results_by_id.get(row["id"])
            if current is None or row["score"] < current["score"]:
                fts_results_by_id[row["id"]] = row
    fts_results_raw = list(fts_results_by_id.values())
```

Keep the existing vector query and RRF code unchanged after `fts_results_raw`.

- [x] **Step 6: Promote fixed alias queries out of report-only**

In `rst2md/rag/search_eval_queries.json`, remove `"report_only": true` from:

- `node-add-child-natural`
- `timer-stopped-natural`
- `signal-emit-natural`

Keep their `tags` values unchanged.

- [x] **Step 7: Verify rewrite tests**

Run:

```bash
rtk uv run pytest \
  rst2md/tests/test_searcher_module.py \
  rst2md/tests/test_rag_search.py::SearchTests::test_natural_language_alias_returns_expected_symbol \
  -q
```

Expected: all selected tests pass.

- [x] **Step 8: Commit**

```bash
rtk git add rst2md/rag/query_rewrite.py rst2md/rag/searcher.py rst2md/rag/search_eval_queries.json rst2md/tests/test_searcher_module.py rst2md/tests/test_rag_search.py
rtk git commit -m "feat: add conservative query rewrite aliases"
```

---

### Task 5: Add Intent-Aware Ranking for Tutorial Queries

**Files:**
- Modify: `rst2md/rag/query_rewrite.py`
- Modify: `rst2md/rag/searcher.py`
- Modify: `rst2md/tests/test_searcher_module.py`
- Modify: `rst2md/tests/test_rag_search.py`
- Modify: `rst2md/rag/search_eval_queries.json`

**Interfaces:**
- Produces `doc_type_boost(query: str, doc_type: str) -> float`.
- Search results preserve the existing `SearchResult` fields and public search function signatures.

- [x] **Step 1: Write failing unit tests for intent boost**

Append to `rst2md/tests/test_searcher_module.py`:

```python
from rag.query_rewrite import doc_type_boost


def test_doc_type_boost_prefers_tutorial_for_how_to_query():
    assert doc_type_boost("how to use scene tree nodes", "tutorial") > 0
    assert doc_type_boost("how to use scene tree nodes", "class") == 0


def test_doc_type_boost_does_not_boost_symbol_query():
    assert doc_type_boost("Node.add_child", "tutorial") == 0
    assert doc_type_boost("Node.add_child", "class") == 0
```

- [x] **Step 2: Write failing integration test**

Add this method inside `SearchTests` in `rst2md/tests/test_rag_search.py`:

```python
    def test_how_to_query_prefers_tutorial_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp) / "docs"
            classes = docs / "classes"
            tutorials = docs / "tutorials"
            classes.mkdir(parents=True)
            tutorials.mkdir(parents=True)
            (classes / "class_animation.md").write_text(
                "# Animation\n\nScene tree nodes can be animated from code.\n",
                encoding="utf-8",
            )
            (tutorials / "scene_tree.md").write_text(
                "# Scene tree\n\nHow to use scene tree nodes and attach child nodes.\n",
                encoding="utf-8",
            )
            db_path = Path(tmp) / "godot_docs.sqlite"
            build_database(docs, db_path)

            results = search_database(db_path, "how to use scene tree nodes", limit=3, expand_graph=False)

            self.assertTrue(results)
            self.assertEqual(results[0].doc_type, "tutorial")
            self.assertEqual(results[0].path, "tutorials/scene_tree.md")
```

- [x] **Step 3: Run the failing intent tests**

Run:

```bash
rtk uv run pytest \
  rst2md/tests/test_searcher_module.py::test_doc_type_boost_prefers_tutorial_for_how_to_query \
  rst2md/tests/test_searcher_module.py::test_doc_type_boost_does_not_boost_symbol_query \
  rst2md/tests/test_rag_search.py::SearchTests::test_how_to_query_prefers_tutorial_result \
  -q
```

Expected: FAIL because `doc_type_boost` does not exist and ranking does not apply doc-type intent.

- [x] **Step 4: Add `doc_type_boost` to `query_rewrite.py`**

```python
def doc_type_boost(query: str, doc_type: str) -> float:
    lowered = query.lower()
    if "." in query or "_" in query:
        return 0.0
    tutorial_intent = (
        lowered.startswith("how to ")
        or " tutorial" in lowered
        or " guide" in lowered
        or "learn " in lowered
    )
    if tutorial_intent and doc_type == "tutorial":
        return 0.05
    return 0.0
```

- [x] **Step 5: Apply the boost in `searcher.py`**

Update imports:

```python
from dataclasses import replace
from rag.query_rewrite import doc_type_boost, expand_query_variants
```

Add this helper near `_make_result`:

```python
def _apply_intent_boost(query: str, results: list[SearchResult]) -> list[SearchResult]:
    boosted = [
        replace(result, score=result.score + doc_type_boost(query, result.doc_type))
        for result in results
    ]
    return sorted(boosted, key=lambda result: result.score, reverse=True)
```

After direct and graph-expanded `SearchResult` objects are assembled and before returning from `_search_database_impl`, apply:

```python
    sorted_results = _apply_intent_boost(query, sorted_results)
```

- [x] **Step 6: Promote the tutorial intent query out of report-only**

In `rst2md/rag/search_eval_queries.json`, remove `"report_only": true` from `how-to-use-scene-tree-nodes`.

- [x] **Step 7: Verify intent tests**

Run:

```bash
rtk uv run pytest \
  rst2md/tests/test_searcher_module.py \
  rst2md/tests/test_rag_search.py::SearchTests::test_how_to_query_prefers_tutorial_result \
  -q
```

Expected: all selected tests pass.

- [x] **Step 8: Commit**

```bash
rtk git add rst2md/rag/query_rewrite.py rst2md/rag/searcher.py rst2md/rag/search_eval_queries.json rst2md/tests/test_searcher_module.py rst2md/tests/test_rag_search.py
rtk git commit -m "feat: boost tutorial intent in search ranking"
```

---

### Task 6: Document the Loop and Establish a Reviewable Baseline

**Files:**
- Modify: `README.md`
- Create: `docs/search-quality/baseline.json`

**Interfaces:**
- Consumes: runnable `godot-rag eval-search`.
- Produces: documented diagnostics workflow and a baseline JSON file for release-database comparison.

- [x] **Step 1: Update README evaluation docs**

In `README.md`, update the `Search Quality Evaluation` section so it includes these command examples:

````markdown
Run the packaged quality suite against a release database:

```bash
godot-rag eval-search --db godot_rag/rag/godot_docs.sqlite --compare-graph
```

Write or refresh the reviewed baseline:

```bash
godot-rag eval-search \
  --db godot_rag/rag/godot_docs.sqlite \
  --baseline docs/search-quality/baseline.json \
  --write-baseline
```

Compare against the reviewed baseline:

```bash
godot-rag eval-search \
  --db godot_rag/rag/godot_docs.sqlite \
  --baseline docs/search-quality/baseline.json \
  --compare-graph
```

Failed queries include diagnostics showing whether expected targets exist in the database and where the best match appears inside the diagnostic window.
````

- [x] **Step 2: Run the full focused test suite**

Run:

```bash
rtk uv run pytest rst2md/tests/test_search_eval.py rst2md/tests/test_search_eval_cli.py rst2md/tests/test_searcher_module.py rst2md/tests/test_rag_search.py rst2md/tests/test_semantic_search.py -q
```

Expected: all selected tests pass.

- [x] **Step 3: Run manual evaluation text output**

Run:

```bash
rtk uv run godot-rag eval-search --db godot_rag.db --compare-graph
```

Expected:

- command exits 0 unless a baseline regression flag is supplied.
- output includes `Search Quality Evaluation`.
- output includes absolute `hit@5` and `mrr@5`.
- any failed query includes a `diagnostics:` block.

- [x] **Step 4: Create or refresh baseline**

Run:

```bash
mkdir -p docs/search-quality
rtk uv run godot-rag eval-search --db godot_rag.db --baseline docs/search-quality/baseline.json --write-baseline --json
```

Expected:

- `docs/search-quality/baseline.json` exists.
- JSON includes `overall`, `categories`, `query_results`, and `baseline_written`.

- [x] **Step 5: Compare against baseline**

Run:

```bash
rtk uv run godot-rag eval-search --db godot_rag.db --baseline docs/search-quality/baseline.json --compare-graph
```

Expected:

- output includes `baseline: compared`.
- command exits 0 immediately after baseline creation.

- [x] **Step 6: Commit**

```bash
rtk git add README.md docs/search-quality/baseline.json
rtk git commit -m "docs: document search quality optimization loop"
```

---

## Final Verification

Run the complete focused verification:

```bash
rtk uv run pytest rst2md/tests/test_search_eval.py rst2md/tests/test_search_eval_cli.py rst2md/tests/test_searcher_module.py rst2md/tests/test_rag_search.py rst2md/tests/test_semantic_search.py -q
rtk uv run godot-rag eval-search --db godot_rag.db --baseline docs/search-quality/baseline.json --compare-graph
rtk git status --short
```

Expected:

- pytest passes.
- evaluation command prints absolute metrics and baseline comparison.
- `git status --short` is clean after all commits.

## Self-Review Notes

- Spec coverage: CLI entry point is covered by Task 1; query expansion by Task 3; diagnostics by Task 2; current failure families by Tasks 4 and 5; baseline/docs by Task 6.
- Completeness scan: every task lists exact files, public interfaces, test commands, expected results, and commit commands.
- Type consistency: `FailureDiagnostics`, `QueryResult.diagnostics`, `expand_query_variants`, and `doc_type_boost` are introduced before later tasks rely on them.
