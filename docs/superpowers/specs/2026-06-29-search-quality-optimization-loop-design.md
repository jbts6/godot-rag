---
comet_change: search-quality-optimization-loop
role: technical-design
canonical_spec: openspec
archived-with: 2026-06-29-search-quality-optimization-loop
status: final
---

# Search Quality Optimization Loop — Technical Design

## Context

The godot-rag project has an existing search pipeline using SQLite FTS5 + sqlite-vec + RRF fusion. An `eval-search` CLI command exists but is broken due to packaging misconfiguration. The current golden-query suite has only 5 entries. Failed queries provide no diagnostic information, making it difficult to distinguish recall failures from ranking failures.

## Goals / Non-Goals

**Goals:**
- Make `eval-search` CLI runnable via correct packaging
- Provide failure diagnostics for debugging query failures
- Expand query coverage to 30+ tiered queries across 5 categories
- Improve recall for natural-language queries via conservative alias rewriting
- Improve ranking for tutorial-intent queries via doc-type boost
- Establish a reviewable baseline for regression detection

**Non-Goals:**
- Replace or retrain the embedding model
- Change SQLite, FTS5, sqlite-vec, or RRF fusion architecture
- Require full release-database evaluation in default CI
- Make broad/corpus-sensitive queries gating (keep as `report_only`)

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────┐
│  eval-search CLI                                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ load_queries  │  │ evaluate_    │  │ format_      │  │
│  │ (JSON → list) │  │ database()   │  │ text_report  │  │
│  └──────────────┘  └──────┬───────┘  └──────────────┘  │
│                           │                              │
│  ┌────────────────────────▼───────────────────────────┐ │
│  │ FailureDiagnostics (opt-in via diagnostic_limit)   │ │
│  │ - expected_present, best_rank, expected_rows       │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  searcher.py                                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ expand_query_ │  │ _run_fts_    │  │ _apply_      │  │
│  │ variants()    │  │ query()      │  │ intent_boost │  │
│  │ (query_rewrite│  │ (per variant)│  │ (post-rank)  │  │
│  │  module)      │  └──────────────┘  └──────────────┘  │
│  └──────────────┘                                       │
└─────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Query Input** → `expand_query_variants()` produces `[original, ...aliases]`
2. **FTS Path** → `_run_fts_query()` runs per variant, merges by best score per doc ID
3. **Vector Path** → Uses original query text only (no aliases)
4. **RRF Fusion** → Combines FTS and vector results as before
5. **Intent Boost** → `_apply_intent_boost()` adds doc_type_boost to each result
6. **Diagnostics** → If `diagnostic_limit` set, `_fetch_expected_rows()` and `_find_matching_rank()` compute FailureDiagnostics

## Decisions

### D1: Query rewriting as lexical recall candidates only

**Decision:** `expand_query_variants()` returns alias strings used only for FTS matching. Vector search continues using the original query text.

**Rationale:** Aliases are conservative symbol mappings (e.g., "attach node to scene tree" → "Node.add_child"). Using them for vector search would dilute semantic intent. FTS benefits from exact symbol matches; vector search does not.

**Implementation:**
- `rst2md/rag/query_rewrite.py`: New module with `_ALIAS_RULES` tuple and `expand_query_variants()` function
- `searcher.py`: Extract `_run_fts_query()` helper, loop over variants, merge by best score

### D2: Intent boost as post-ranking score adjustment

**Decision:** Apply `doc_type_boost()` after candidate assembly, before final sort. Boost is a small additive value (0.05) applied to tutorial results for how-to queries.

**Rationale:** Keeps the boost transparent and separable from the core ranking. Does not alter FTS or vector scores. Easy to tune or remove.

**Implementation:**
- `query_rewrite.py`: Add `doc_type_boost(query, doc_type) -> float`
- `searcher.py`: Add `_apply_intent_boost()` helper, call before return

### D3: Tiered query suite with `report_only` flag

**Decision:** Use the existing `GoldenQuery.report_only` field to tier queries. Gating queries (≥12) must pass; report-only queries (≥8) surface regressions without blocking.

**Rationale:** Broad queries (aliases, intent, graph, addon) are valuable for diagnostics but too corpus-sensitive for CI gating.

### D4: Failure diagnostics as separate dataclass

**Decision:** `FailureDiagnostics` is a frozen dataclass attached to `QueryResult.diagnostics`. It is computed on-demand via `diagnostic_limit` parameter, not by default.

**Rationale:** Diagnostics require extra DB queries. Making it opt-in keeps the default evaluation fast.

**Implementation:**
- `search_eval.py`: Add `FailureDiagnostics` dataclass, update `QueryResult`, add `_query_constraints()`, `_fetch_expected_rows()`, `_find_matching_rank()` helpers
- `report_to_dict()` and `format_text_report()` include diagnostics when present

## Risks / Trade-offs

- **Alias rules are manually curated** → Start with 5 rules, expand based on observed failures
- **Intent boost is heuristic** → Small value (0.05), easy to tune; tutorial queries are `report_only` initially
- **Baseline JSON is point-in-time** → `--write-baseline` flag for refresh
- **Diagnostic queries add latency** → `diagnostic_limit` is opt-in

## Test Strategy

- TDD: Each task writes failing test first, then implements
- Unit tests for `expand_query_variants`, `doc_type_boost`, `FailureDiagnostics`
- Integration tests for search alias recall, tutorial intent ranking
- Shape tests for query suite size/tier/category coverage
- CLI tests for entry point and help output
- Final full suite verification: `pytest rst2md/tests/test_search_eval.py test_search_eval_cli.py test_searcher_module.py test_rag_search.py test_semantic_search.py`
