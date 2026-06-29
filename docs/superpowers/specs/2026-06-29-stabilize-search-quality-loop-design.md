---
comet_change: stabilize-search-quality-loop
role: technical-design
canonical_spec: openspec
archived-with: 2026-06-29-stabilize-search-quality-loop
status: final
---

# Stabilize Search Quality Loop - Technical Design

## Context

The previous search quality work made `eval-search` usable and added a real-database baseline, but the loop still needs two upgrades before it can drive quality safely:

- Baselines must prove which database and query suite produced them, and invalid databases must be rejected before a baseline can be written.
- Query aliases currently improve FTS recall only. Natural-language symbol intent needs to participate in symbol recall and deterministic reranking so report-only normalization failures can become stable gating queries.

This design keeps the current SQLite FTS5, sqlite-vec, RRF, graph expansion, and golden-query infrastructure. It adds a small query-planning layer and stricter evaluation metadata instead of replacing the search architecture.

## Goals

- Reject empty or incomplete real-database baseline writes.
- Record baseline input metadata: database counts, database fingerprint, query-suite hash, and relevant evaluator/search versions.
- Add category coverage warnings for required gating categories with zero gating queries.
- Introduce an internal `QueryPlan` that exposes original text, normalized text, symbol candidates, alias-derived symbol candidates, doc-type intent, and addon intent.
- Use query-plan symbol candidates in exact, suffix, and prefix symbol recall.
- Replace the narrow post-ranking intent boost with deterministic named reranking signals.
- Promote only stable natural-language symbol report-only queries after they pass against the canonical database.

## Non-Goals

- No LLM reranker, learned reranker, external search service, or new runtime dependency.
- No database schema migration.
- No broad rewrite of `searcher.py` beyond extracting focused helpers where needed.
- No addon query promotion until diagnostics show expected addon rows exist in the canonical database.
- No requirement to commit generated database binaries.

## Architecture

### Evaluation Layer

`rst2md/rag/search_eval.py` remains responsible for loading golden queries, evaluating results, calculating metrics, comparing baselines, and formatting reports.

Add focused helpers:

- `query_suite_hash(queries: Sequence[GoldenQuery]) -> str`
- `database_fingerprint(db_path: Path) -> DatabaseFingerprint`
- `validate_baseline_input(fingerprint: DatabaseFingerprint, *, require_vectors: bool = True) -> list[str]`
- `promotion_eligibility(result: QueryResult) -> PromotionStatus`

`EvaluationReport` gains metadata fields instead of hiding metadata only in the written JSON. `report_to_dict()` writes the metadata consistently for both baseline writes and JSON output.

Baseline write flow:

```text
load queries
  -> calculate query_suite_hash
  -> inspect database counts
  -> validate baseline input
  -> evaluate search
  -> write report metadata + metrics + query results
```

Baseline compare flow:

```text
load baseline
  -> compare current metrics over baseline gating IDs
  -> compare current query hash against baseline metadata
  -> report query-suite drift separately from ranking regression
```

Invalid baseline inputs fail before evaluation writes a new baseline. Comparison can still run on existing baselines, but it must report metadata drift clearly.

### Query Planning Layer

Add a focused internal module, likely `rst2md/rag/query_plan.py`, with:

```python
@dataclass(frozen=True)
class QueryPlan:
    original: str
    normalized: str
    fts_variants: tuple[str, ...]
    symbol_candidates: tuple[str, ...]
    alias_symbol_candidates: tuple[str, ...]
    doc_type_intent: str | None
    addon_intent: str | None
```

`build_query_plan(query: str) -> QueryPlan` uses existing query rewrite behavior as input:

- `fts_variants` preserves current `expand_query_variants()` output.
- Exact symbol-like queries create one normalized symbol candidate.
- Alias rules add alias-derived symbol candidates.
- Tutorial/addon intent remains conservative and string-pattern based.

This module is internal. Public `search_database()` and `search_database_with_metadata()` signatures do not change.

### Search Recall

`_search_database_impl()` builds one `QueryPlan` at the top and passes it to focused helper functions.

Recall responsibilities:

- Vector search uses `plan.original`.
- FTS search uses `plan.fts_variants`.
- Exact symbol lookup runs for every `plan.symbol_candidates`.
- Suffix symbol lookup runs for every `plan.symbol_candidates`.
- Prefix symbol lookup runs for normalized symbol-like candidates only when safe.

This keeps semantic search natural-language oriented while allowing aliases like "attach node to scene tree" to reach `Node.add_child` through symbol recall.

### Deterministic Reranking

Replace `_apply_intent_boost(query, results)` with a query-plan aware reranker:

```python
def rerank_results(plan: QueryPlan, results: list[SearchResult]) -> list[SearchResult]:
    ...
```

Reranking stays deterministic and explainable. Suggested named signals:

- `alias_symbol_match`: result symbol exactly matches an alias-derived symbol candidate.
- `symbol_match`: result symbol matches a symbol candidate.
- `path_heading_match`: path, heading, or breadcrumb contains important query tokens.
- `doc_type_intent_match`: tutorial intent boosts tutorial docs.
- `addon_intent_match`: addon intent boosts addon docs only when addon metadata is present.

Signals should be small enough to avoid overturning high-confidence exact symbol matches accidentally, but strong enough to fix current low-ranking alias cases. Tests should assert behavior, not magic numeric constants.

### Promotion Lifecycle

Promotion is a derived quality decision, not a hidden manual habit.

A report-only query is eligible when:

- expected rows are present in the canonical database;
- graph-enabled evaluation ranks the expected target within `required_at`;
- the query is not blocked by missing addon data;
- required gating category coverage remains healthy after promotion.

Promotion checks can initially be exposed through tests and evaluation metadata. The actual query fixture change remains explicit in `search_eval_queries.json`.

## Error Handling

- Empty database: fail baseline write with the zero-count fields named.
- Missing `vec_chunks`: fail baseline write for real-database mode unless vector checks are explicitly disabled for deterministic fixture tests.
- Vector/chunk count mismatch: fail baseline write and report both counts.
- Query-suite hash mismatch: do not call it a ranking regression; report it as query-suite drift.
- Required category has zero gating queries: emit a coverage warning in JSON/text output.

## Testing Strategy

Focused unit tests:

- query-suite hash is stable for identical query definitions and changes when definitions change;
- empty database baseline write fails and does not write a file;
- vector/chunk mismatch is diagnosed;
- `build_query_plan("attach node to scene tree")` includes `Node.add_child`;
- exact symbol queries deduplicate symbol candidates;
- tutorial intent does not suppress exact symbol behavior;
- promotion eligibility rejects missing expected rows and accepts passing present rows.

Search integration tests:

- natural-language alias queries reach the expected symbol through symbol recall;
- deterministic reranking promotes alias symbol matches over weaker lexical/vector candidates;
- report-only addon queries remain visible but not gating when expected addon rows are absent.

End-to-end verification:

```bash
rtk uv run pytest rst2md/tests/test_search_eval.py rst2md/tests/test_search_eval_cli.py rst2md/tests/test_searcher_module.py -q
rtk uv run godot-rag eval-search --db godot_rag.db --baseline docs/search-quality/baseline.json --compare-graph
```

## Implementation Notes

- Keep `QueryPlan` separate from `SearchResult` so result models remain stable.
- Prefer helper extraction over adding more nested logic inside `_search_database_impl()`.
- Keep reranking signal names close to tests so failures explain which quality signal regressed.
- Refresh `docs/search-quality/baseline.json` only after the new metadata and promoted queries pass on `godot_rag.db`.
