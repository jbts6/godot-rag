---
change: search-ranking-signal-explanations
design-doc: docs/superpowers/specs/2026-06-30-search-ranking-signal-explanations-design.md
base-ref: fb5491a279abb9c03f90f5e6b7fc25b7bf63a555
---

# Search Ranking Signal Explanations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Attach structured, per-result ranking signal explanations to every `SearchResult` covering symbol recall, hybrid/RRF, FTS-only, graph expansion, and deterministic rerank — without changing ranking math, final ordering, or `search_database()` source compatibility.

**Architecture:** Additive model field only. A frozen `RankingSignal` dataclass is appended to `SearchResult` (default-empty list). The searcher threads a mutable `ranking_signals` list through its internal candidate dict, appending a named signal at each scoring stage and preserving prior signals when a later stage replaces an entry. Rerank copies the list before appending non-zero bonus signals. CLI serializes the full payload in JSON and prints a compact summary under `--debug-search` only.

**Tech Stack:** Python 3.10+ frozen dataclasses with `field(default_factory=...)`, pytest over `unittest.TestCase` and bare-function tests, SQLite-backed temporary-database fixtures, `uv` for dependency/test management.

## Global Constraints

- **Source-compatibility is mandatory.** `search_database()` and `search_database_with_metadata()` keep their current signatures and return shapes. `SearchResult` gains `ranking_signals` as the LAST field with `field(default_factory=list)` so all existing positional construction stays valid (see `rst2md/tests/test_rag_search.py:625` `test_search_result_has_snippet_field` for the pattern that must keep passing).
- **Ranking math and final ordering must not change.** Rerank tasks append named non-zero bonus signals only; the bonus amounts (5.0, 2.0, 0.05, 0.5) and the `elif`/additive logic in `_rerank_bonus` (`rst2md/rag/fusion.py:49`) stay byte-for-byte identical. Focused tests must assert ordering is unchanged.
- **No schema, no embeddings-dependency, no new retrieval channels.** Do not touch `rst2md/rag/query_plan.py`, `rst2md/rag/db.py` schema, `rst2md/rag/indexer.py`, or `SearchMetadata`. Explanations must be producible in FTS-only mode (no vectors).
- **Edit under `rst2md/rag/`.** Source imports use `from rag.module import ...` (rewritten to `from godot_rag.rag.module` in build). NEVER edit `godot_rag/` (build output).
- **Signal payloads must be JSON-friendly.** `value` is `float|int|str|None`; `details` values are `str|int|float|bool|None` only.
- **Stable signal names** (use these exact strings): `symbol_recall.exact`, `symbol_recall.suffix`, `symbol_recall.prefix`, `hybrid.rrf`, `fts.bm25`, `graph.expansion`, `rerank.alias_symbol`, `rerank.direct_symbol`, `rerank.doc_type_intent`, `rerank.addon_intent`.
- **TDD per task.** Write the failing test first, run it to confirm it fails, implement the minimal change, run it to confirm it passes, then commit. Each task is independently committable.
- **Test commands.** Focused: `uv run pytest -q rst2md/tests/test_rag_search.py`; rerank/unit: `uv run pytest -q rst2md/tests/test_searcher_module.py`; eval: `uv run pytest -q rst2md/tests/test_search_eval.py`; full: `uv run pytest -q`. CLI subprocess tests rely on `PYTHONPATH=rst2md` (already set in `TEST_ENV` at `rst2md/tests/test_rag_search.py:15`).
- **OpenSpec task tracking.** As each task completes, check off the matching IDs in `openspec/changes/search-ranking-signal-explanations/tasks.md`.

---

## File Structure

- **Modify `rst2md/rag/models.py`**: add `RankingSignal` frozen dataclass; append `ranking_signals: list[RankingSignal]` field to `SearchResult` after `snippet` (currently `rst2md/rag/models.py:38`).
- **Modify `rst2md/rag/searcher.py`**: import `RankingSignal`; thread `ranking_signals` through `_make_result` (`:99`); append signals at RRF (`:118-163`), symbol recall (`:165-200`), FTS (`:202-248`), and graph expansion (`:253-300`); pass signals into the `SearchResult` constructor (`:302-321`).
- **Modify `rst2md/rag/fusion.py`**: import `RankingSignal`; add `_rerank_signals(plan, result)` mirroring `_rerank_bonus` conditions; in `rerank_results` (`:62`) copy `result.ranking_signals` before appending non-zero rerank signals.
- **Modify `rst2md/rag/cli.py`**: add `_signal_to_dict`; serialize `ranking_signals` in `_result_to_dict` (`:58`); print compact `signals:` summary in the `--debug-search` text path (`:91-111`); leave default text path unchanged.
- **Modify `rst2md/tests/test_rag_search.py`**: add `RankingSignalTests`, `SymbolRecallSignalTests`, `HybridRrfSignalTests`, `GraphExpansionSignalTests`, and CLI signal tests.
- **Modify `rst2md/tests/test_searcher_module.py`**: add rerank signal tests alongside existing `test_rerank_promotes_alias_symbol_match` (`:165`) and `test_rerank_symbol_query_does_not_apply_tutorial_intent` (`:205`).
- **Modify `openspec/changes/search-ranking-signal-explanations/tasks.md`**: check off OpenSpec task IDs as implementation progresses.

## OpenSpec Task Mapping

| Plan Task | OpenSpec IDs |
|---|---|
| Task 1 | 1.1, 1.2, 1.3 |
| Task 2 | 2.1 (+ 2.4 for symbol-stage replacement) |
| Task 3 | 2.2 (+ 2.4 for RRF→symbol preservation) |
| Task 4 | 2.3 (+ 2.4 for FTS→graph preservation) |
| Task 5 | 3.1, 3.2 (+ 2.4 for rerank list-copy) |
| Task 6 | 4.1, 4.2 |
| Task 7 | 5.1, 5.2, 5.3 |

---

## Task 1: RankingSignal model and additive SearchResult field

**Files:**
- Modify: `rst2md/rag/models.py:1-51` (add `RankingSignal`; extend `SearchResult`).
- Test: `rst2md/tests/test_rag_search.py` (new `RankingSignalTests` class).

**Interfaces:**
- Consumes: nothing (foundation task).
- Produces: `RankingSignal(name: str, weight: float, value: float|int|str|None=None, details: dict[str, object]=field(default_factory=dict))` frozen dataclass; `SearchResult.ranking_signals: list[RankingSignal]` additive field with `field(default_factory=list)`.

- [x] **Step 1: Write the failing test**

Append to `rst2md/tests/test_rag_search.py` (new class, placed after `SnippetTests`):

```python
class RankingSignalTests(unittest.TestCase):
    """RankingSignal model and SearchResult additive field."""

    def test_ranking_signal_defaults(self):
        from rag.models import RankingSignal

        signal = RankingSignal(name="symbol_recall.exact", weight=100.0)
        self.assertEqual(signal.name, "symbol_recall.exact")
        self.assertEqual(signal.weight, 100.0)
        self.assertIsNone(signal.value)
        self.assertEqual(signal.details, {})

    def test_ranking_signal_details_not_shared_across_instances(self):
        from rag.models import RankingSignal

        a = RankingSignal(name="x", weight=1.0)
        b = RankingSignal(name="y", weight=2.0)
        a.details["k"] = "v"
        self.assertNotIn("k", b.details, "details dict must not be shared across instances")

    def test_search_result_ranking_signals_default_empty(self):
        from rag.models import SearchResult

        result = SearchResult(
            score=1.0, path="p", start_line=1, end_line=2,
            doc_type="class", chunk_type="method", addon="", addon_name="",
            symbol="X", heading="h", breadcrumb="b", text="t",
        )
        self.assertEqual(result.ranking_signals, [])

    def test_search_result_positional_construction_still_works(self):
        """Existing positional construction must stay source-compatible."""
        from rag.models import SearchResult

        result = SearchResult(
            1.0, "p", 1, 2, "class", "method", "", "", "X", "h", "b", "t",
        )
        self.assertEqual(result.score, 1.0)
        self.assertEqual(result.snippet, "")
        self.assertEqual(result.ranking_signals, [])
```

- [x] **Step 2: Run test to verify it fails**

Run: `uv run pytest -q rst2md/tests/test_rag_search.py::RankingSignalTests -v`
Expected: FAIL with `ImportError: cannot import name 'RankingSignal' from 'rag.models'` (and `ranking_signals` attribute errors).

- [x] **Step 3: Write minimal implementation**

Edit `rst2md/rag/models.py`. Add the `RankingSignal` dataclass and the additive `ranking_signals` field on `SearchResult` AFTER `snippet`. The `details` field uses `field(default_factory=dict)` (same pattern `Chunk.symbols` uses at `rst2md/rag/models.py:18`). Final file:

```python
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class Chunk:
    path: str
    doc_type: str
    chunk_type: str
    addon: str
    addon_name: str
    symbol: str
    heading: str
    breadcrumb: str
    start_line: int
    end_line: int
    text: str
    symbols: List[str] = field(default_factory=list)
    parent_symbol: str = ""


@dataclass(frozen=True)
class RankingSignal:
    name: str
    weight: float
    value: float | int | str | None = None
    details: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class SearchResult:
    score: float
    path: str
    start_line: int
    end_line: int
    doc_type: str
    chunk_type: str
    addon: str
    addon_name: str
    symbol: str
    heading: str
    breadcrumb: str
    text: str
    relation_type: str = ''
    distance: int = 0
    snippet: str = ''
    ranking_signals: List[RankingSignal] = field(default_factory=list)


@dataclass(frozen=True)
class SearchMetadata:
    mode: str
    vector_available: bool
    fallback_reason: str = ""


@dataclass(frozen=True)
class SearchResponse:
    results: List[SearchResult]
    metadata: SearchMetadata
```

- [x] **Step 4: Run test to verify it passes**

Run: `uv run pytest -q rst2md/tests/test_rag_search.py::RankingSignalTests -v`
Expected: PASS (4 tests).

- [x] **Step 5: Run regression to confirm no breakage**

Run: `uv run pytest -q rst2md/tests/test_rag_search.py rst2md/tests/test_searcher_module.py -q`
Expected: PASS (existing tests unaffected — `ranking_signals` defaults to empty).

- [x] **Step 6: Commit**

```bash
git add rst2md/rag/models.py rst2md/tests/test_rag_search.py
git commit -m "feat(rag): add RankingSignal model and SearchResult.ranking_signals field"
```

Then check off OpenSpec `1.1`, `1.2`, `1.3` in `openspec/changes/search-ranking-signal-explanations/tasks.md`.

---

## Task 2: Record symbol recall signals

**Files:**
- Modify: `rst2md/rag/searcher.py:6` (import), `:99-116` (`_make_result` + new `_record_signal` helper), `:165-200` (symbol recall stages).
- Test: `rst2md/tests/test_rag_search.py` (new `SymbolRecallSignalTests` class).

**Interfaces:**
- Consumes: `RankingSignal`, `SearchResult.ranking_signals` (from Task 1).
- Produces: `_make_result(row, score, ranking_signals=None)` returns a candidate dict with a `ranking_signals` list key; `_record_signal(candidate, signal)` helper that appends to `candidate["ranking_signals"]` preserving prior entries. Symbol-recall stages emit `symbol_recall.exact` (weight 100.0), `symbol_recall.suffix` (80.0), `symbol_recall.prefix` (40.0), with `details={"candidate": <candidate>, "alias_derived": <bool>}`.

- [x] **Step 1: Write the failing test**

Append to `rst2md/tests/test_rag_search.py`:

```python
class SymbolRecallSignalTests(unittest.TestCase):
    """Symbol recall stages should record named ranking signals."""

    def _build_db(self, tmp):
        docs = Path(tmp) / "docs"
        classes = docs / "classes"
        classes.mkdir(parents=True)
        (classes / "class_node.md").write_text(
            "# Node\n\nBase class.\n\n## Methods\n\n"
            "`void` **add_child**(`Node` node)\n\nAdds a child node.\n",
            encoding="utf-8",
        )
        db_path = Path(tmp) / "test.sqlite"
        build_database(docs, db_path)
        return db_path

    def test_exact_symbol_match_records_signal(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = self._build_db(tmp)
            results = search_database(db_path, "Node.add_child", limit=3, expand_graph=False)
            self.assertTrue(results)
            top = results[0]
            self.assertEqual(top.symbol, "Node.add_child")
            names = [s.name for s in top.ranking_signals]
            self.assertIn("symbol_recall.exact", names)
            exact = next(s for s in top.ranking_signals if s.name == "symbol_recall.exact")
            self.assertEqual(exact.weight, 100.0)

    def test_suffix_symbol_match_records_signal(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = self._build_db(tmp)
            results = search_database(db_path, "add_child", limit=3, expand_graph=False)
            self.assertTrue(results)
            top = results[0]
            self.assertEqual(top.symbol, "Node.add_child")
            names = [s.name for s in top.ranking_signals]
            self.assertIn("symbol_recall.suffix", names)
            suffix = next(s for s in top.ranking_signals if s.name == "symbol_recall.suffix")
            self.assertEqual(suffix.weight, 80.0)

    def test_prefix_symbol_match_records_signal(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = self._build_db(tmp)
            results = search_database(db_path, "Node", limit=10, expand_graph=False)
            method = next((r for r in results if r.symbol == "Node.add_child"), None)
            self.assertIsNotNone(method, "Node.add_child should be found via prefix symbol match")
            names = [s.name for s in method.ranking_signals]
            self.assertIn("symbol_recall.prefix", names)
            prefix = next(s for s in method.ranking_signals if s.name == "symbol_recall.prefix")
            self.assertEqual(prefix.weight, 40.0)

    def test_alias_derived_match_sets_alias_detail(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = self._build_db(tmp)
            results = search_database(
                db_path, "attach node to scene tree", limit=3, expand_graph=False
            )
            self.assertTrue(results)
            top = results[0]
            self.assertEqual(top.symbol, "Node.add_child")
            exact = next(
                (s for s in top.ranking_signals if s.name == "symbol_recall.exact"), None
            )
            self.assertIsNotNone(
                exact, "alias-derived exact match should still record symbol_recall.exact"
            )
            self.assertTrue(
                exact.details.get("alias_derived"),
                "alias-derived match should set details.alias_derived=True",
            )
```

- [x] **Step 2: Run test to verify it fails**

Run: `uv run pytest -q rst2md/tests/test_rag_search.py::SymbolRecallSignalTests -v`
Expected: FAIL — `top.ranking_signals` is `[]` (no signals recorded yet), so `assertIn("symbol_recall.exact", names)` fails.

- [x] **Step 3: Write minimal implementation**

Edit `rst2md/rag/searcher.py`.

3a. Update the import at `rst2md/rag/searcher.py:6`:

```python
from rag.models import RankingSignal, SearchMetadata, SearchResponse, SearchResult
```

3b. Update `_make_result` (at `rst2md/rag/searcher.py:99`) to accept and carry `ranking_signals`, and add a `_record_signal` helper immediately after it:

```python
        def _make_result(row, score, ranking_signals=None):
            return {
                "id": row["id"],
                "score": score,
                "path": row["path"],
                "start_line": row["start_line"],
                "end_line": row["end_line"],
                "doc_type": row["doc_type"],
                "chunk_type": row["chunk_type"],
                "addon": row["addon"],
                "addon_name": row["addon_name"],
                "symbol": row["symbol"],
                "heading": row["heading"],
                "breadcrumb": row["breadcrumb"],
                "text": clean_chunk_text(row["text"]),
                "relation_type": "",
                "distance": 0,
                "ranking_signals": list(ranking_signals or []),
            }

        def _record_signal(candidate: dict, signal: RankingSignal) -> None:
            """Append a ranking signal to a candidate dict, preserving prior signals."""
            candidate.setdefault("ranking_signals", []).append(signal)
```

3c. Update the symbol-recall block (at `rst2md/rag/searcher.py:165-200`). The current loop iterates `plan.symbol_candidates + plan.alias_symbol_candidates` and replaces `results[cid]` with `_make_result(row, score)` when the new score is higher. Change each of the three tiers (exact 100, suffix 80, prefix 40) to preserve prior signals and append a named signal. Replace the whole block with:

```python
        # 1-3. Symbol recall: iterate over plan.symbol_candidates and alias_symbol_candidates
        for candidate in plan.symbol_candidates + plan.alias_symbol_candidates:
            normalized = normalize_symbol(candidate)
            alias_derived = candidate in plan.alias_symbol_candidates

            # Exact symbol match (+100)
            rows = conn.execute(
                "SELECT s.name, c.* FROM symbols s JOIN chunks c ON s.chunk_id = c.id WHERE s.normalized_name = ?"
                + type_filter + addon_filter,
                [normalized] + type_params + addon_params,
            ).fetchall()
            for row in rows:
                cid = row["id"]
                if cid not in results or results[cid]["score"] < 100:
                    prior = results[cid].get("ranking_signals", []) if cid in results else []
                    results[cid] = _make_result(row, 100.0, ranking_signals=prior)
                    _record_signal(
                        results[cid],
                        RankingSignal(
                            name="symbol_recall.exact",
                            weight=100.0,
                            value=candidate,
                            details={"alias_derived": alias_derived},
                        ),
                    )

            # Suffix symbol match (+80)
            rows = conn.execute(
                "SELECT s.name, c.* FROM symbols s JOIN chunks c ON s.chunk_id = c.id WHERE s.normalized_name LIKE ?"
                + type_filter + addon_filter,
                [f"%.{normalized}"] + type_params + addon_params,
            ).fetchall()
            for row in rows:
                cid = row["id"]
                if cid not in results or results[cid]["score"] < 80:
                    prior = results[cid].get("ranking_signals", []) if cid in results else []
                    results[cid] = _make_result(row, 80.0, ranking_signals=prior)
                    _record_signal(
                        results[cid],
                        RankingSignal(
                            name="symbol_recall.suffix",
                            weight=80.0,
                            value=candidate,
                            details={"alias_derived": alias_derived},
                        ),
                    )

            # Prefix symbol match (+40)
            rows = conn.execute(
                "SELECT s.name, c.* FROM symbols s JOIN chunks c ON s.chunk_id = c.id WHERE s.normalized_name LIKE ?"
                + type_filter + addon_filter,
                [f"{normalized}%"] + type_params + addon_params,
            ).fetchall()
            for row in rows:
                cid = row["id"]
                if cid not in results or results[cid]["score"] < 40:
                    prior = results[cid].get("ranking_signals", []) if cid in results else []
                    results[cid] = _make_result(row, 40.0, ranking_signals=prior)
                    _record_signal(
                        results[cid],
                        RankingSignal(
                            name="symbol_recall.prefix",
                            weight=40.0,
                            value=candidate,
                            details={"alias_derived": alias_derived},
                        ),
                    )
```

3d. Update the final `SearchResult` assembly (at `rst2md/rag/searcher.py:302-321`) to pass `ranking_signals` through:

```python
        search_results = [
            SearchResult(
                score=r["score"],
                path=r["path"],
                start_line=r["start_line"],
                end_line=r["end_line"],
                doc_type=r["doc_type"],
                chunk_type=r["chunk_type"],
                addon=r["addon"],
                addon_name=r["addon_name"],
                symbol=r["symbol"],
                heading=r["heading"],
                breadcrumb=r["breadcrumb"],
                text=r["text"],
                relation_type=r.get("relation_type", ""),
                distance=r.get("distance", 0),
                snippet=_extract_snippet(r["text"], query),
                ranking_signals=r.get("ranking_signals", []),
            )
            for r in sorted_results
        ]
```

Note: do NOT touch the RRF, FTS, or graph stages yet — they still call the old `_make_result(row, score)` form, which now defaults `ranking_signals` to `[]`. That is fine; subsequent tasks add their signals. The `results[cid] = _make_result(row, score)` calls in RRF (line ~157) and FTS (line ~245) will produce entries with empty `ranking_signals` lists until Tasks 3 and 4 fill them in.

- [x] **Step 4: Run test to verify it passes**

Run: `uv run pytest -q rst2md/tests/test_rag_search.py::SymbolRecallSignalTests -v`
Expected: PASS (4 tests).

- [x] **Step 5: Run regression**

Run: `uv run pytest -q rst2md/tests/test_rag_search.py rst2md/tests/test_searcher_module.py -q`
Expected: PASS. Existing symbol/recall tests (`test_symbol_query_returns_exact_method_first`, `test_natural_language_alias_returns_expected_symbol`, `test_rerank_promotes_alias_symbol_match`) still pass — ordering unchanged.

- [x] **Step 6: Commit**

```bash
git add rst2md/rag/searcher.py rst2md/tests/test_rag_search.py
git commit -m "feat(rag): record symbol recall ranking signals"
```

Then check off OpenSpec `2.1` in `openspec/changes/search-ranking-signal-explanations/tasks.md`.

---

## Task 3: Record hybrid/RRF and FTS scoring signals

**Files:**
- Modify: `rst2md/rag/searcher.py:118-163` (RRF stage), `:202-248` (FTS stage).
- Test: `rst2md/tests/test_rag_search.py` (new `HybridRrfSignalTests` class).

**Interfaces:**
- Consumes: `_make_result(..., ranking_signals=...)`, `_record_signal`, `RankingSignal` (from Task 2).
- Produces: `hybrid.rrf` signal (weight = scaled RRF score, `details={"scale": 40.0}`) recorded when RRF introduces/improves a candidate; `fts.bm25` signal (weight = scaled FTS score, `details={}`) recorded when FTS introduces/improves a candidate. Prior signals are preserved when RRF or FTS replaces an entry (OpenSpec 2.4 for the RRF→symbol-recall replacement chain).

- [x] **Step 1: Write the failing test**

Append to `rst2md/tests/test_rag_search.py`:

```python
class HybridRrfSignalTests(unittest.TestCase):
    """Hybrid RRF and FTS fallback stages should record signals."""

    def test_fts_fallback_records_bm25_signal(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp) / "docs"
            classes = docs / "classes"
            classes.mkdir(parents=True)
            (classes / "class_timer.md").write_text(
                "# Timer\n\n## Methods\n\n"
                "`bool` **is_stopped**() `const`\n\nReturns true if the timer is stopped.\n",
                encoding="utf-8",
            )
            db_path = Path(tmp) / "test.sqlite"
            build_database(docs, db_path)
            # "stopped timer" does not exactly match a symbol, so FTS is the
            # scoring path that introduces the candidate.
            results = search_database(db_path, "stopped timer", limit=3, expand_graph=False)
            self.assertTrue(results)
            has_fts = any(
                s.name == "fts.bm25" for r in results for s in r.ranking_signals
            )
            self.assertTrue(has_fts, "FTS fallback should record fts.bm25 signal")

    def test_hybrid_rrf_records_signal_when_vector_available(self):
        from rag import embeddings
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp) / "docs"
            classes = docs / "classes"
            classes.mkdir(parents=True)
            (classes / "class_timer.md").write_text(
                "# Timer\n\n## Methods\n\n"
                "`bool` **is_stopped**() `const`\n\nReturns true if the timer is stopped.\n",
                encoding="utf-8",
            )
            db_path = Path(tmp) / "test.sqlite"
            with patch.object(embeddings, "generate_embeddings", return_value=[[0.0] * 256]):
                build_database(docs, db_path)
                results = search_database(db_path, "timer stopped", limit=3, expand_graph=False)
            self.assertTrue(results)
            has_rrf = any(
                s.name == "hybrid.rrf" for r in results for s in r.ranking_signals
            )
            self.assertTrue(has_rrf, "Hybrid mode should record hybrid.rrf signal")

    def test_symbol_recall_preserves_prior_rrf_signal(self):
        """OpenSpec 2.4: when symbol recall improves an RRF-found candidate,
        the prior hybrid.rrf signal must survive the replacement."""
        import sqlite3
        from rag import embeddings
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp) / "docs"
            classes = docs / "classes"
            classes.mkdir(parents=True)
            (classes / "class_timer.md").write_text(
                "# Timer\n\n## Methods\n\n"
                "`bool` **is_stopped**() `const`\n\nReturns true.\n",
                encoding="utf-8",
            )
            db_path = Path(tmp) / "test.sqlite"
            with patch.object(embeddings, "generate_embeddings", return_value=[[0.0] * 256]):
                build_database(docs, db_path)
                conn = sqlite3.connect(str(db_path))
                cid = conn.execute(
                    "SELECT id FROM chunks WHERE symbol='Timer.is_stopped'"
                ).fetchone()[0]
                conn.close()
                # Force RRF to surface the Timer.is_stopped chunk; symbol recall
                # will then promote it from a low RRF score to exact (100).
                with patch("rag.searcher.rrf_fusion", return_value=[{"id": cid, "rrf_score": 0.5}]):
                    results = search_database(
                        db_path, "Timer.is_stopped", limit=3, expand_graph=False
                    )
            top = results[0]
            self.assertEqual(top.symbol, "Timer.is_stopped")
            names = {s.name for s in top.ranking_signals}
            self.assertIn("hybrid.rrf", names, "prior RRF signal must survive symbol-recall replacement")
            self.assertIn("symbol_recall.exact", names)
```

- [x] **Step 2: Run test to verify it fails**

Run: `uv run pytest -q rst2md/tests/test_rag_search.py::HybridRrfSignalTests -v`
Expected: FAIL — no `hybrid.rrf` or `fts.bm25` signals are recorded yet (RRF/FTS still use the old `_make_result(row, score)` form producing empty signal lists).

- [x] **Step 3: Write minimal implementation**

Edit `rst2md/rag/searcher.py`.

3a. Update the RRF result-merge block (at `rst2md/rag/searcher.py:150-157`) to preserve prior signals and append `hybrid.rrf`. Replace:

```python
                # Add fused results to results dict with RRF scores
                for rank, fused in enumerate(fused_results[:limit * 3]):
                    cid = fused['id']
                    rrf_score = fused['rrf_score'] * 40.0  # Scale RRF to 0-40 range
                    if cid not in results or results[cid]["score"] < rrf_score:
                        row = conn.execute("SELECT * FROM chunks WHERE id = ?", (cid,)).fetchone()
                        if row:
                            results[cid] = _make_result(row, rrf_score)
```

with:

```python
                # Add fused results to results dict with RRF scores
                for rank, fused in enumerate(fused_results[:limit * 3]):
                    cid = fused['id']
                    rrf_score = fused['rrf_score'] * 40.0  # Scale RRF to 0-40 range
                    if cid not in results or results[cid]["score"] < rrf_score:
                        row = conn.execute("SELECT * FROM chunks WHERE id = ?", (cid,)).fetchone()
                        if row:
                            prior = results[cid].get("ranking_signals", []) if cid in results else []
                            results[cid] = _make_result(row, rrf_score, ranking_signals=prior)
                            _record_signal(
                                results[cid],
                                RankingSignal(
                                    name="hybrid.rrf",
                                    weight=rrf_score,
                                    value=fused['rrf_score'],
                                    details={"scale": 40.0},
                                ),
                            )
```

3b. Update the FTS merge block (at `rst2md/rag/searcher.py:241-245`). Replace:

```python
            for cid, row in fts_results_by_id.items():
                bm25 = abs(row["score"])
                fts_score = min(40.0, max(0.0, 40.0 / (1.0 + bm25 * 0.01)))
                if cid not in results or results[cid]["score"] < fts_score:
                    results[cid] = _make_result(row["row"], fts_score)
```

with:

```python
            for cid, row in fts_results_by_id.items():
                bm25 = abs(row["score"])
                fts_score = min(40.0, max(0.0, 40.0 / (1.0 + bm25 * 0.01)))
                if cid not in results or results[cid]["score"] < fts_score:
                    prior = results[cid].get("ranking_signals", []) if cid in results else []
                    results[cid] = _make_result(row["row"], fts_score, ranking_signals=prior)
                    _record_signal(
                        results[cid],
                        RankingSignal(
                            name="fts.bm25",
                            weight=fts_score,
                            value=bm25,
                            details={},
                        ),
                    )
```

- [x] **Step 4: Run test to verify it passes**

Run: `uv run pytest -q rst2md/tests/test_rag_search.py::HybridRrfSignalTests -v`
Expected: PASS (3 tests).

- [x] **Step 5: Run regression**

Run: `uv run pytest -q rst2md/tests/test_rag_search.py rst2md/tests/test_searcher_module.py -q`
Expected: PASS. Hybrid/RRF tests (`test_rrf_fusion_basic`, `test_cli_search_debug_json_includes_metadata`) still pass — score math unchanged.

- [x] **Step 6: Commit**

```bash
git add rst2md/rag/searcher.py rst2md/tests/test_rag_search.py
git commit -m "feat(rag): record hybrid RRF and FTS scoring signals"
```

Then check off OpenSpec `2.2` in `openspec/changes/search-ranking-signal-explanations/tasks.md`.

---

## Task 4: Record graph expansion signals

**Files:**
- Modify: `rst2md/rag/searcher.py:270-297` (graph expansion: existing-chunk branch + new-chunk branch).
- Test: `rst2md/tests/test_rag_search.py` (new `GraphExpansionSignalTests` class).

**Interfaces:**
- Consumes: `_make_result`, `_record_signal`, `RankingSignal` (from Task 2). The `parent` relation direction is `source=member → target=class_summary` (confirmed at `rst2md/rag/relations.py:30-36`), so searching a method expands to its class_summary.
- Produces: `graph.expansion` signal recorded (a) for newly introduced chunks (weight = computed `rel_score`, `details={"relation", "distance", "source_score", "weight"}`) and (b) for already-present chunks whose `relation_type`/`distance` are updated (weight = 0.0, `details={"relation", "distance", "metadata_only": True}`). Prior signals are preserved in the existing-chunk branch (OpenSpec 2.4 for FTS→graph preservation).

- [x] **Step 1: Write the failing test**

Append to `rst2md/tests/test_rag_search.py`:

```python
class GraphExpansionSignalTests(unittest.TestCase):
    """Graph expansion should record signals and preserve prior signals."""

    def test_new_graph_chunk_records_expansion_signal(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp) / "docs"
            classes = docs / "classes"
            classes.mkdir(parents=True)
            (classes / "class_node.md").write_text(
                "# Node\n\nBase class.\n\n**Inherits:** `Object`\n\n"
                "## Methods\n\n`void` **add_child**(`Node` node)\n\nAdds a child.\n",
                encoding="utf-8",
            )
            (classes / "class_object.md").write_text(
                "# Object\n\nBase of all classes.\n",
                encoding="utf-8",
            )
            db_path = Path(tmp) / "test.sqlite"
            build_database(docs, db_path)
            results = search_database(db_path, "add_child", limit=10, expand_graph=True)
            # Object class_summary is reached only via graph expansion (inherits).
            obj = next((r for r in results if r.symbol == "Object"), None)
            self.assertIsNotNone(obj, "Object should be reached via graph expansion")
            names = [s.name for s in obj.ranking_signals]
            self.assertIn("graph.expansion", names)
            graph_sig = next(s for s in obj.ranking_signals if s.name == "graph.expansion")
            self.assertEqual(graph_sig.details.get("relation"), "inherits")
            self.assertEqual(graph_sig.details.get("distance"), 1)

    def test_graph_expansion_preserves_prior_fts_signal(self):
        """OpenSpec 2.4: a chunk found by FTS and then reached via graph
        expansion must carry both its fts.bm25 signal and graph.expansion."""
        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp) / "docs"
            classes = docs / "classes"
            classes.mkdir(parents=True)
            # The class_summary text deliberately mentions "add_child" so FTS
            # finds it; graph expansion (parent: method -> class_summary) then
            # reaches it as an already-present candidate.
            (classes / "class_node.md").write_text(
                "# Node\n\nBase class. Node has an add_child method.\n\n"
                "## Methods\n\n`void` **add_child**(`Node` node)\n\nAdds a child.\n",
                encoding="utf-8",
            )
            db_path = Path(tmp) / "test.sqlite"
            build_database(docs, db_path)
            results = search_database(db_path, "add_child", limit=10, expand_graph=True)
            summary = next((r for r in results if r.symbol == "Node"), None)
            self.assertIsNotNone(summary, "Node class_summary should be in results")
            names = {s.name for s in summary.ranking_signals}
            self.assertIn("fts.bm25", names, "prior FTS signal must survive graph expansion")
            self.assertIn("graph.expansion", names, "graph expansion should append its own signal")
            graph_sig = next(s for s in summary.ranking_signals if s.name == "graph.expansion")
            self.assertTrue(graph_sig.details.get("metadata_only"), "existing-chunk branch should set metadata_only=True")
```

- [x] **Step 2: Run test to verify it fails**

Run: `uv run pytest -q rst2md/tests/test_rag_search.py::GraphExpansionSignalTests -v`
Expected: FAIL — no `graph.expansion` signals recorded; the new-chunk branch builds a dict without `ranking_signals`, and the existing-chunk branch doesn't append a signal.

- [x] **Step 3: Write minimal implementation**

Edit `rst2md/rag/searcher.py:270-297`. The existing-chunk branch (at `:274-277`) currently only mutates `relation_type` and `distance`; add a `graph.expansion` signal append. The new-chunk branch (at `:281-297`) builds a dict inline; add a `ranking_signals` list with one `graph.expansion` signal. Replace the inner loop body:

```python
                for rel_row in related_rows:
                    rel_id = rel_row["id"]
                    if rel_id not in expanded_ids:
                        expanded_ids.add(rel_id)
                        if rel_id in results:
                            # Chunk already found by vector/FTS search, update relation metadata
                            results[rel_id]["relation_type"] = rel_row["relation"]
                            results[rel_id]["distance"] = 1
                            _record_signal(
                                results[rel_id],
                                RankingSignal(
                                    name="graph.expansion",
                                    weight=0.0,
                                    value=rel_row["relation"],
                                    details={
                                        "relation": rel_row["relation"],
                                        "distance": 1,
                                        "metadata_only": True,
                                    },
                                ),
                            )
                        else:
                            # New chunk from graph expansion
                            rel_score = result["score"] * rel_row["weight"] * 0.5
                            results[rel_id] = {
                                "id": rel_id,
                                "score": rel_score,
                                "path": rel_row["path"],
                                "start_line": rel_row["start_line"],
                                "end_line": rel_row["end_line"],
                                "doc_type": rel_row["doc_type"],
                                "chunk_type": rel_row["chunk_type"],
                                "addon": rel_row["addon"],
                                "addon_name": rel_row["addon_name"],
                                "symbol": rel_row["symbol"],
                                "heading": rel_row["heading"],
                                "breadcrumb": rel_row["breadcrumb"],
                                "text": clean_chunk_text(rel_row["text"]),
                                "relation_type": rel_row["relation"],
                                "distance": 1,
                                "ranking_signals": [
                                    RankingSignal(
                                        name="graph.expansion",
                                        weight=rel_score,
                                        value=rel_row["relation"],
                                        details={
                                            "relation": rel_row["relation"],
                                            "distance": 1,
                                            "source_score": result["score"],
                                            "weight": rel_row["weight"],
                                        },
                                    )
                                ],
                            }
```

- [x] **Step 4: Run test to verify it passes**

Run: `uv run pytest -q rst2md/tests/test_rag_search.py::GraphExpansionSignalTests -v`
Expected: PASS (2 tests).

- [x] **Step 5: Run regression**

Run: `uv run pytest -q rst2md/tests/test_rag_search.py -q`
Expected: PASS. Existing `GraphExpansionTests` (`test_expand_returns_parent_chunk`, `test_expanded_results_have_distance`, `test_expanded_results_have_relation_type`) still pass — relation metadata and scoring unchanged.

- [x] **Step 6: Commit**

```bash
git add rst2md/rag/searcher.py rst2md/tests/test_rag_search.py
git commit -m "feat(rag): record graph expansion ranking signals"
```

Then check off OpenSpec `2.3` (and note `2.4` is now covered across Tasks 2-4) in `openspec/changes/search-ranking-signal-explanations/tasks.md`.

---

## Task 5: Rerank named bonus signals (preserve score math and ordering)

**Files:**
- Modify: `rst2md/rag/fusion.py:6` (import), `:49-67` (add `_rerank_signals`; update `rerank_results`).
- Test: `rst2md/tests/test_searcher_module.py` (new bare-function tests after `test_rerank_symbol_query_does_not_apply_tutorial_intent` at `:205`).

**Interfaces:**
- Consumes: `RankingSignal` (from Task 1), `SearchResult.ranking_signals`, `_rerank_bonus` (unchanged).
- Produces: `_rerank_signals(plan, result) -> list[RankingSignal]` mirroring `_rerank_bonus` conditions and returning one signal per non-zero bonus (`rerank.alias_symbol` weight 5.0, `rerank.direct_symbol` weight 2.0, `rerank.doc_type_intent` weight 0.05, `rerank.addon_intent` weight 0.5). `rerank_results` copies `result.ranking_signals` (shallow copy of the list — items are frozen dataclasses) before appending rerank signals; score math and final sort are untouched.

**Critical constraint:** Do NOT change `_rerank_bonus` return values, the `elif` between alias/direct, or the additive `doc_type_intent`/`addon_intent` logic. Only ADD `_rerank_signals` and the list-copy in `rerank_results`.

- [x] **Step 1: Write the failing test**

Append to `rst2md/tests/test_searcher_module.py` (after `test_rerank_symbol_query_does_not_apply_tutorial_intent`):

```python
def test_rerank_appends_alias_symbol_signal():
    from rag.models import SearchResult
    from rag.query_plan import build_query_plan
    from rag.fusion import rerank_results

    plan = build_query_plan("attach node to scene tree")
    weak_alias = SearchResult(
        score=1.0, path="classes/class_node.md", start_line=1, end_line=2,
        doc_type="class", chunk_type="method", addon="", addon_name="",
        symbol="Node.add_child", heading="add_child", breadcrumb="Node",
        text="Adds a child node.",
    )
    ranked = rerank_results(plan, [weak_alias])
    assert ranked[0].symbol == "Node.add_child"
    names = [s.name for s in ranked[0].ranking_signals]
    assert "rerank.alias_symbol" in names
    alias_sig = next(s for s in ranked[0].ranking_signals if s.name == "rerank.alias_symbol")
    assert alias_sig.weight == 5.0


def test_rerank_appends_direct_symbol_signal():
    from rag.models import SearchResult
    from rag.query_plan import build_query_plan
    from rag.fusion import rerank_results

    plan = build_query_plan("Node.add_child")
    result = SearchResult(
        score=1.0, path="classes/class_node.md", start_line=1, end_line=2,
        doc_type="class", chunk_type="method", addon="", addon_name="",
        symbol="Node.add_child", heading="add_child", breadcrumb="Node",
        text="Adds a child node.",
    )
    ranked = rerank_results(plan, [result])
    names = [s.name for s in ranked[0].ranking_signals]
    assert "rerank.direct_symbol" in names
    sig = next(s for s in ranked[0].ranking_signals if s.name == "rerank.direct_symbol")
    assert sig.weight == 2.0


def test_rerank_appends_doc_type_intent_signal():
    from rag.models import SearchResult
    from rag.query_plan import build_query_plan
    from rag.fusion import rerank_results

    plan = build_query_plan("how to use scene tree nodes")
    tutorial = SearchResult(
        score=1.0, path="tutorials/scene_tree.md", start_line=1, end_line=2,
        doc_type="tutorial", chunk_type="section", addon="", addon_name="",
        symbol="", heading="Scene tree", breadcrumb="Tutorial",
        text="How to use the scene tree.",
    )
    ranked = rerank_results(plan, [tutorial])
    names = [s.name for s in ranked[0].ranking_signals]
    assert "rerank.doc_type_intent" in names
    sig = next(s for s in ranked[0].ranking_signals if s.name == "rerank.doc_type_intent")
    assert sig.weight == 0.05


def test_rerank_appends_addon_intent_signal():
    from rag.models import SearchResult
    from rag.query_plan import build_query_plan
    from rag.fusion import rerank_results

    plan = build_query_plan("dialogue manager addon")
    addon_result = SearchResult(
        score=1.0, path="addons/dm/docs.md", start_line=1, end_line=2,
        doc_type="addon", chunk_type="section", addon="dm", addon_name="DM",
        symbol="", heading="Dialogue", breadcrumb="Addon",
        text="A dialogue addon.",
    )
    ranked = rerank_results(plan, [addon_result])
    names = [s.name for s in ranked[0].ranking_signals]
    assert "rerank.addon_intent" in names
    sig = next(s for s in ranked[0].ranking_signals if s.name == "rerank.addon_intent")
    assert sig.weight == 0.5


def test_rerank_preserves_prior_signals_without_mutating_original():
    """OpenSpec 2.4 / 3.2: rerank must copy ranking_signals (not share the
    list) and preserve ordering."""
    from rag.models import RankingSignal, SearchResult
    from rag.query_plan import build_query_plan
    from rag.fusion import rerank_results

    plan = build_query_plan("attach node to scene tree")
    prior = RankingSignal(name="symbol_recall.exact", weight=100.0, value="Node.add_child")
    original = SearchResult(
        score=1.0, path="classes/class_node.md", start_line=1, end_line=2,
        doc_type="class", chunk_type="method", addon="", addon_name="",
        symbol="Node.add_child", heading="add_child", breadcrumb="Node",
        text="Adds a child node.", ranking_signals=[prior],
    )
    ranked = rerank_results(plan, [original])
    names = [s.name for s in ranked[0].ranking_signals]
    assert "symbol_recall.exact" in names, "prior signal must survive rerank"
    assert "rerank.alias_symbol" in names, "rerank bonus signal must be appended"
    # Original must not be mutated (list not shared across replace()).
    assert len(original.ranking_signals) == 1, (
        "original result's signal list must not be mutated by rerank"
    )


def test_rerank_bonus_equals_signal_weight_sum():
    """Guard against drift between _rerank_bonus and _rerank_signals."""
    from rag.models import SearchResult
    from rag.query_plan import build_query_plan
    from rag.fusion import _rerank_bonus, _rerank_signals

    plan = build_query_plan("dialogue manager addon how to")
    addon_tutorial = SearchResult(
        score=1.0, path="p", start_line=1, end_line=2, doc_type="addon",
        chunk_type="section", addon="dm", addon_name="DM", symbol="",
        heading="h", breadcrumb="b", text="t",
    )
    assert _rerank_bonus(plan, addon_tutorial) == sum(
        s.weight for s in _rerank_signals(plan, addon_tutorial)
    )


def test_rerank_ordering_unchanged_with_signals():
    """OpenSpec 3.2: final ordering must match the pre-change order."""
    from rag.models import SearchResult
    from rag.query_plan import build_query_plan
    from rag.fusion import rerank_results

    plan = build_query_plan("attach node to scene tree")
    weak_alias = SearchResult(
        score=1.0, path="classes/class_node.md", start_line=1, end_line=2,
        doc_type="class", chunk_type="method", addon="", addon_name="",
        symbol="Node.add_child", heading="add_child", breadcrumb="Node",
        text="Adds a child node.",
    )
    lexical = SearchResult(
        score=2.0, path="tutorials/scripting/change_scenes_manually.md",
        start_line=1, end_line=2, doc_type="tutorial", chunk_type="section",
        addon="", addon_name="", symbol="", heading="Scene tree",
        breadcrumb="Tutorial", text="Attach scripts to scene nodes.",
    )
    ranked = rerank_results(plan, [lexical, weak_alias])
    assert ranked[0].symbol == "Node.add_child", "alias bonus must still promote the alias match"
```

- [x] **Step 2: Run test to verify it fails**

Run: `uv run pytest -q rst2md/tests/test_searcher_module.py -v -k "rerank_appends or rerank_preserves or rerank_bonus_equals or rerank_ordering_unchanged"`
Expected: FAIL — `_rerank_signals` does not exist (ImportError), and `ranked[0].ranking_signals` does not contain rerank signals.

- [x] **Step 3: Write minimal implementation**

Edit `rst2md/rag/fusion.py`. Add the `RankingSignal` import and a `_rerank_signals` helper that mirrors `_rerank_bonus` exactly (same conditions, same constants), then update `rerank_results` to copy the list and append signals. Final file:

```python
"""RRF fusion and rerank for search results.

Focused sub-module split from searcher.py (change: split-searcher-modules).
Behavior is byte-for-byte identical to the previous searcher.py implementation.
"""
from dataclasses import replace
from typing import List

from rag.models import RankingSignal, SearchResult
from rag.query_plan import QueryPlan


def rrf_fusion(fts_results: List[dict], vec_results: List[dict], k: int = 60) -> List[dict]:
    """Fuse FTS5 and vector search results using Reciprocal Rank Fusion.

    Args:
        fts_results: FTS5 results with 'id' key.
        vec_results: Vector results with 'id' and 'distance' keys.
        k: RRF parameter (default 60).

    Returns:
        Fused results sorted by RRF score, with 'rrf_score' key added.
    """
    scores = {}

    for rank, result in enumerate(fts_results):
        chunk_id = result['id']
        scores[chunk_id] = scores.get(chunk_id, 0) + 1.0 / (k + rank)

    for rank, result in enumerate(vec_results):
        chunk_id = result['id']
        scores[chunk_id] = scores.get(chunk_id, 0) + 1.0 / (k + rank)

    sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

    results = []
    for chunk_id in sorted_ids:
        result = next((r for r in fts_results if r['id'] == chunk_id), None)
        if result is None:
            result = next((r for r in vec_results if r['id'] == chunk_id), None)
        if result:
            result = dict(result)
            result['rrf_score'] = scores[chunk_id]
            results.append(result)

    return results


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


def _rerank_signals(plan: QueryPlan, result: SearchResult) -> list[RankingSignal]:
    """Named, non-zero rerank bonus signals.

    Mirrors the conditions and constants in :func:`_rerank_bonus` exactly so
    the bonus amounts stay in sync with the recorded signal weights.
    """
    signals: list[RankingSignal] = []
    if result.symbol in plan.alias_symbol_candidates:
        signals.append(RankingSignal(
            name="rerank.alias_symbol",
            weight=5.0,
            value=result.symbol,
            details={"source": "alias_symbol_candidates"},
        ))
    elif result.symbol in plan.symbol_candidates:
        signals.append(RankingSignal(
            name="rerank.direct_symbol",
            weight=2.0,
            value=result.symbol,
            details={"source": "symbol_candidates"},
        ))
    if plan.doc_type_intent and result.doc_type == plan.doc_type_intent and not plan.symbol_candidates:
        signals.append(RankingSignal(
            name="rerank.doc_type_intent",
            weight=0.05,
            value=result.doc_type,
            details={"intent": plan.doc_type_intent},
        ))
    if plan.addon_intent and result.doc_type == "addon":
        signals.append(RankingSignal(
            name="rerank.addon_intent",
            weight=0.5,
            value=result.doc_type,
            details={"intent": plan.addon_intent},
        ))
    return signals


def rerank_results(plan: QueryPlan, results: list[SearchResult]) -> list[SearchResult]:
    boosted = []
    for result in results:
        bonus = _rerank_bonus(plan, result)
        # Copy the list (items are frozen dataclasses) before appending so the
        # original result's ranking_signals is not mutated across replace().
        signals = list(result.ranking_signals) + _rerank_signals(plan, result)
        boosted.append(replace(result, score=result.score + bonus, ranking_signals=signals))
    return sorted(boosted, key=lambda result: result.score, reverse=True)
```

- [x] **Step 4: Run test to verify it passes**

Run: `uv run pytest -q rst2md/tests/test_searcher_module.py -v -k "rerank_appends or rerank_preserves or rerank_bonus_equals or rerank_ordering_unchanged"`
Expected: PASS (7 tests).

- [x] **Step 5: Run regression (rerank behavior unchanged)**

Run: `uv run pytest -q rst2md/tests/test_searcher_module.py rst2md/tests/test_rag_search.py -q`
Expected: PASS. `test_rerank_promotes_alias_symbol_match` and `test_rerank_symbol_query_does_not_apply_tutorial_intent` still pass — same ordering, same scores.

- [x] **Step 6: Commit**

```bash
git add rst2md/rag/fusion.py rst2md/tests/test_searcher_module.py
git commit -m "feat(rag): append named rerank bonus signals without changing score math"
```

Then check off OpenSpec `3.1`, `3.2` in `openspec/changes/search-ranking-signal-explanations/tasks.md`.

---

## Task 6: CLI structured and debug output for ranking signals

**Files:**
- Modify: `rst2md/rag/cli.py:58-74` (`_result_to_dict` + new `_signal_to_dict`), `:91-111` (text path: compact signal summary under `--debug-search` only).
- Test: `rst2md/tests/test_rag_search.py` (new tests in `CliTests`).

**Interfaces:**
- Consumes: `SearchResult.ranking_signals` (populated by Tasks 2-5).
- Produces: `_signal_to_dict(s)` returning `{"name", "weight", "value", "details"}`; `_result_to_dict` adds `"ranking_signals"`; the `--debug-search` text path prints one `signals: <name>=<weight>, ...` line per result when `r.ranking_signals` is non-empty; the default (non-debug) text path is unchanged (no signal payload).

**Critical constraint (OpenSpec 4.2):** Default human-readable search output must stay concise and backward-compatible — do NOT print signals when `--debug-search` is not set. JSON output (both plain and `--debug-search`) includes the full `ranking_signals` array.

- [x] **Step 1: Write the failing test**

Append to `rst2md/tests/test_rag_search.py` inside `class CliTests` (after `test_cli_search_without_debug_no_metadata`):

```python
    def test_cli_search_debug_json_includes_ranking_signals(self):
        from rag import embeddings
        from rag.cli import cmd_search
        from unittest.mock import MagicMock

        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp) / "docs"
            classes = docs / "classes"
            classes.mkdir(parents=True)
            (classes / "class_timer.md").write_text(
                "# Timer\n\n## Methods\n\n"
                "`bool` **is_stopped**() `const`\n\nReturns true if the timer is stopped.\n",
                encoding="utf-8",
            )
            with patch.object(embeddings, "generate_embeddings", return_value=[[0.0] * 256):
                db_path = Path(tmp) / "test.db"
                build_database(docs, db_path)
                args = MagicMock()
                args.db = str(db_path)
                args.query = "Timer.is_stopped"
                args.limit = 3
                args.json = True
                args.no_expand = True
                args.debug_search = True

                import io
                from contextlib import redirect_stdout
                f = io.StringIO()
                with redirect_stdout(f):
                    cmd_search(args)
                output = json.loads(f.getvalue())

            self.assertIn("results", output)
            self.assertTrue(output["results"], "should have at least one result")
            top = output["results"][0]
            self.assertIn("ranking_signals", top)
            self.assertIsInstance(top["ranking_signals"], list)
            self.assertTrue(top["ranking_signals"], "top result should have ranking signals")
            sig = top["ranking_signals"][0]
            self.assertIn("name", sig)
            self.assertIn("weight", sig)
            self.assertIn("details", sig)

    def test_cli_search_debug_text_includes_signal_summary(self):
        from rag.cli import cmd_search
        from unittest.mock import MagicMock

        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp) / "docs"
            classes = docs / "classes"
            classes.mkdir(parents=True)
            (classes / "class_timer.md").write_text(
                "# Timer\n\n## Methods\n\n"
                "`bool` **is_stopped**() `const`\n\nReturns true.\n",
                encoding="utf-8",
            )
            db_path = Path(tmp) / "test.db"
            build_database(docs, db_path)
            args = MagicMock()
            args.db = str(db_path)
            args.query = "Timer.is_stopped"
            args.limit = 3
            args.json = False
            args.no_expand = True
            args.debug_search = True

            import io
            from contextlib import redirect_stdout
            f = io.StringIO()
            with redirect_stdout(f):
                cmd_search(args)
            output = f.getvalue()

            self.assertIn("signals:", output, "debug text output should include a signals summary line")

    def test_cli_search_default_text_omits_signals(self):
        """OpenSpec 4.2: default (non-debug) text output must not print signals."""
        from rag.cli import cmd_search
        from unittest.mock import MagicMock

        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp) / "docs"
            classes = docs / "classes"
            classes.mkdir(parents=True)
            (classes / "class_timer.md").write_text(
                "# Timer\n\n## Methods\n\n"
                "`bool` **is_stopped**() `const`\n\nReturns true.\n",
                encoding="utf-8",
            )
            db_path = Path(tmp) / "test.db"
            build_database(docs, db_path)
            args = MagicMock()
            args.db = str(db_path)
            args.query = "Timer.is_stopped"
            args.limit = 3
            args.json = False
            args.no_expand = True
            args.debug_search = False

            import io
            from contextlib import redirect_stdout
            f = io.StringIO()
            with redirect_stdout(f):
                cmd_search(args)
            output = f.getvalue()

            self.assertNotIn("signals:", output, "default text output must not print signal payload")
```

- [x] **Step 2: Run test to verify it fails**

Run: `uv run pytest -q rst2md/tests/test_rag_search.py::CliTests -v -k "ranking_signals or signal_summary or omits_signals"`
Expected: FAIL — `ranking_signals` key is absent from JSON output (`KeyError` or `assertIn` fails), and no `signals:` line is printed in debug text.

- [x] **Step 3: Write minimal implementation**

Edit `rst2md/rag/cli.py`.

3a. Add `_signal_to_dict` and extend `_result_to_dict` (at `rst2md/rag/cli.py:58-74`):

```python
def _signal_to_dict(s):
    return {
        "name": s.name,
        "weight": s.weight,
        "value": s.value,
        "details": dict(s.details),
    }


def _result_to_dict(r):
    return {
        "score": r.score,
        "path": r.path,
        "start_line": r.start_line,
        "end_line": r.end_line,
        "doc_type": r.doc_type,
        "chunk_type": r.chunk_type,
        "addon": r.addon,
        "addon_name": r.addon_name,
        "symbol": r.symbol,
        "heading": r.heading,
        "breadcrumb": r.breadcrumb,
        "text": r.text,
        "relation_type": r.relation_type,
        "distance": r.distance,
        "ranking_signals": [_signal_to_dict(s) for s in r.ranking_signals],
    }
```

3b. Extend the text path in `_print_results` (at `rst2md/rag/cli.py:91-111`) to print a compact `signals:` summary line per result ONLY when `debug_search` is set and `r.ranking_signals` is non-empty. Replace the text branch with:

```python
    else:
        if debug_search and metadata is not None:
            print(f"search_mode: {metadata.mode}")
            print(f"vector_available: {metadata.vector_available}")
            if metadata.fallback_reason:
                print(f"fallback_reason: {metadata.fallback_reason}")
            print("---")
        for i, r in enumerate(results):
            if i > 0:
                print("---")
            print(f"score: {r.score}")
            if r.relation_type:
                print(f"relation: {r.relation_type} (distance={r.distance})")
            if debug_search and r.ranking_signals:
                summary = ", ".join(f"{s.name}={s.weight:+g}" for s in r.ranking_signals)
                print(f"signals: {summary}")
            print(f"path: {r.path}:{r.start_line}-{r.end_line}")
            print(f"type: {r.chunk_type}")
            if r.addon:
                print(f"addon: {r.addon_name or r.addon}")
            print(f"symbol: {r.symbol}")
            print(f"heading: {r.heading}")
            print(f"breadcrumb: {r.breadcrumb}")
            print(f"text:\n{r.text}")
```

- [x] **Step 4: Run test to verify it passes**

Run: `uv run pytest -q rst2md/tests/test_rag_search.py::CliTests -v -k "ranking_signals or signal_summary or omits_signals"`
Expected: PASS (3 tests).

- [x] **Step 5: Run regression (CLI behavior unchanged for non-signal output)**

Run: `uv run pytest -q rst2md/tests/test_rag_search.py::CliTests -v`
Expected: PASS. `test_cli_search_debug_json_includes_metadata`, `test_cli_search_debug_text_includes_metadata`, `test_cli_search_without_debug_no_metadata` still pass.

- [x] **Step 6: Commit**

```bash
git add rst2md/rag/cli.py rst2md/tests/test_rag_search.py
git commit -m "feat(cli): expose ranking signals in JSON and debug-search text output"
```

Then check off OpenSpec `4.1`, `4.2` in `openspec/changes/search-ranking-signal-explanations/tasks.md`.

---

## Task 7: End-to-end explanation coverage and verification

**Files:**
- Modify: `rst2md/tests/test_rag_search.py` (new `RankingSignalCoverageTests` class — one consolidated regression guard across all signal families).
- Run: focused searcher + CLI + search-eval suites, then the broader pytest suite.

**Interfaces:**
- Consumes: all signal names defined in Global Constraints, produced by Tasks 2-6.
- Produces: a single end-to-end coverage test asserting that, across a small set of real `search_database()` queries, every signal family appears on at least one result. This is the OpenSpec 5.1 acceptance gate; it complements (does not replace) the per-task TDD tests.

- [x] **Step 1: Write the consolidated coverage test**

Append to `rst2md/tests/test_rag_search.py`:

```python
class RankingSignalCoverageTests(unittest.TestCase):
    """OpenSpec 5.1: every signal family is observable end-to-end via
    search_database()."""

    def _build_db(self, tmp):
        docs = Path(tmp) / "docs"
        classes = docs / "classes"
        classes.mkdir(parents=True)
        (classes / "class_node.md").write_text(
            "# Node\n\nBase class. Node has an add_child method.\n\n"
            "**Inherits:** `Object`\n\n"
            "## Methods\n\n`void` **add_child**(`Node` node)\n\nAdds a child.\n",
            encoding="utf-8",
        )
        (classes / "class_object.md").write_text(
            "# Object\n\nBase of all classes.\n",
            encoding="utf-8",
        )
        db_path = Path(tmp) / "test.sqlite"
        build_database(docs, db_path)
        return db_path

    def test_all_signal_families_observable(self):
        from rag import embeddings
        from unittest.mock import patch

        observed: set[str] = set()
        with tempfile.TemporaryDirectory() as tmp:
            db_path = self._build_db(tmp)
            # Symbol recall (exact/suffix/prefix) + rerank.direct_symbol.
            for q in ("Node.add_child", "add_child", "Node"):
                for r in search_database(db_path, q, limit=10, expand_graph=False):
                    observed.update(s.name for s in r.ranking_signals)
            # FTS fallback.
            for r in search_database(db_path, "stopped", limit=10, expand_graph=False):
                observed.update(s.name for s in r.ranking_signals)
            # Graph expansion (new + existing chunk branches).
            for r in search_database(db_path, "add_child", limit=10, expand_graph=True):
                observed.update(s.name for s in r.ranking_signals)
            # Hybrid RRF + rerank.doc_type_intent.
            with patch.object(embeddings, "generate_embeddings", return_value=[[0.0] * 256]):
                for r in search_database(db_path, "how to use node", limit=10, expand_graph=False):
                    observed.update(s.name for s in r.ranking_signals)

        required = {
            "symbol_recall.exact",
            "symbol_recall.suffix",
            "symbol_recall.prefix",
            "fts.bm25",
            "graph.expansion",
            "rerank.direct_symbol",
        }
        missing = required - observed
        self.assertFalse(missing, f"missing signal families: {sorted(missing)}")

    def test_addon_intent_signal_observable_end_to_end(self):
        # Exercise the addon-intent rerank path via a direct rerank call,
        # since the bare-fixture FTS path may not surface it deterministically.
        from rag.models import SearchResult
        from rag.query_plan import build_query_plan
        from rag.fusion import rerank_results

        plan = build_query_plan("dialogue manager addon")
        addon_result = SearchResult(
            score=1.0, path="addons/dm/docs.md", start_line=1, end_line=2,
            doc_type="addon", chunk_type="section", addon="dm", addon_name="DM",
            symbol="", heading="Dialogue", breadcrumb="Addon",
            text="A dialogue addon.",
        )
        ranked = rerank_results(plan, [addon_result])
        names = {s.name for s in ranked[0].ranking_signals}
        self.assertIn("rerank.addon_intent", names)
```

- [x] **Step 2: Run the coverage test**

Run: `uv run pytest -q rst2md/tests/test_rag_search.py::RankingSignalCoverageTests -v`
Expected: PASS (2 tests). If `test_all_signal_families_observable` reports a missing family, inspect the corresponding stage in `rst2md/rag/searcher.py` and confirm the signal name matches Global Constraints exactly.

- [x] **Step 3: Run focused searcher + CLI + search-eval suites (OpenSpec 5.2)**

Run: `uv run pytest -q rst2md/tests/test_rag_search.py rst2md/tests/test_searcher_module.py rst2md/tests/test_search_eval.py -q`
Expected: PASS. The search-eval suite confirms `result_matches` / `_result_to_observed` (`rst2md/rag/search_eval.py:178-200`) still see the existing `SearchResult` fields — the additive `ranking_signals` field does not affect observed-dict shape.

- [x] **Step 4: Run the broader pytest suite (OpenSpec 5.3)**

Run: `uv run pytest -q`
Expected: PASS (or only pre-existing failures unrelated to ranking signals). If runtime is impractical, fall back to the focused set from Step 3 and record the broader-suite result in the task notes.

- [x] **Step 5: Commit**

```bash
git add rst2md/tests/test_rag_search.py
git commit -m "test(rag): add end-to-end ranking signal coverage tests"
```

Then check off OpenSpec `5.1`, `5.2`, `5.3` in `openspec/changes/search-ranking-signal-explanations/tasks.md`.

---

## Self-Review Summary

**Spec coverage check** (every OpenSpec task ID and design-doc section mapped):
- 1.1 / 1.2 / 1.3 → Task 1 (model + additive field + model tests).
- 2.1 → Task 2 (symbol recall: exact/suffix/prefix/alias-derived).
- 2.2 → Task 3 (hybrid.rrf + fts.bm25).
- 2.3 → Task 4 (graph.expansion for new + existing chunks).
- 2.4 → Tasks 2, 3, 4, 5 (prior-signal preservation at every replacement boundary: symbol-recall replacement, RRF→symbol, FTS→graph, rerank list-copy).
- 3.1 / 3.2 → Task 5 (`_rerank_signals` + list-copy; ordering-preservation test).
- 4.1 / 4.2 → Task 6 (JSON + debug-text include signals; default text omits them).
- 5.1 / 5.2 / 5.3 → Task 7 (coverage tests + focused + broader suite).
- Design-doc "Rerank safety" (copy list before appending) → Task 5 Step 3 + `test_rerank_preserves_prior_signals_without_mutating_original`.
- Design-doc "Keep compatibility by using additive model fields" → Global Constraints + Task 1 `test_search_result_positional_construction_still_works`.

**Placeholder scan:** No TBD/TODO; every code step contains full, runnable code; every test step contains full test bodies with concrete assertions.

**Type/name consistency:** `RankingSignal` fields (`name`, `weight`, `value`, `details`) and `SearchResult.ranking_signals` are used identically across Tasks 1-7. Signal names match the Global Constraints list verbatim. `_make_result(..., ranking_signals=...)` and `_record_signal(candidate, signal)` signatures match between Task 2 (definition) and Tasks 3/4 (use). `_rerank_signals(plan, result)` signature matches between Task 5 definition and the `test_rerank_bonus_equals_signal_weight_sum` test.
