## Context

Search evaluation now has a real-database baseline, but the loop is still fragile: a baseline can be refreshed from the wrong database unless the artifact records what it represents, category coverage can silently collapse, and report-only failures are not yet tied to a promotion path. Search ranking also treats alias expansion as an FTS-only fallback, so natural-language symbol intent is not consistently available to exact symbol lookup, hybrid candidate generation, graph comparison, or final ranking.

The existing implementation already has useful pieces: golden query categories, report-only queries, failure classification, conservative alias expansion, vector fallback metadata, and a small intent boost. This change should connect those pieces into a stable quality loop instead of replacing the search stack.

## Goals / Non-Goals

**Goals:**

- Make baseline artifacts self-describing and reject empty or incomplete canonical databases before writing a baseline.
- Keep report-only failures visible while defining explicit rules for promoting stable queries back into gating.
- Introduce a structured query plan that carries original text, normalized symbol candidates, alias candidates, doc-type intent, and addon intent.
- Use query-plan signals across recall and deterministic reranking so natural-language symbol queries can rank expected symbols in top-K.
- Add tests that protect the specific regression classes found by the current report-only failures.

**Non-Goals:**

- Do not add an LLM, learned reranker, external search service, or new model dependency.
- Do not perform a broad rewrite of search storage or database schema.
- Do not require committing generated database binaries.
- Do not promote addon queries to gating until the underlying indexed data is proven present and stable.

## Decisions

1. Use a canonical evaluation metadata gate before baseline writes.

   The evaluator will record database fingerprint fields such as document, chunk, symbol, and vector counts, plus a query-suite hash. Baseline writing will fail early when required counts are zero or inconsistent. This is preferred over relying on README discipline because it makes invalid baselines impossible to create through the CLI path.

2. Represent query understanding as a `QueryPlan`.

   A small internal data object will be created from each query. It will include the original query, normalized query, alias-derived symbol candidates, symbol-like candidates, doc-type intent, and addon intent. Existing alias expansion will feed this object first; recall channels can then consume structured signals instead of each stage recomputing partial normalization.

3. Keep recall broad and ranking deterministic.

   Exact/suffix/prefix symbol lookup should evaluate query-plan symbol candidates. FTS should still run original and alias variants. Vector search should keep the original natural-language query by default, but the final candidate pool should carry the plan signals into a deterministic reranker. This avoids vector overfitting to symbol aliases while still promoting exact alias hits.

4. Treat promotion as a tested lifecycle.

   Report-only queries become gating only when the expected target is present in the canonical database, the query passes within top-K under graph-enabled evaluation, and no category coverage check is violated. This keeps unstable addon and ingestion-dependent queries visible without making the gate flaky.

## Risks / Trade-offs

- Alias boosts can over-promote symbol results for tutorial-like queries -> keep symbol-like and tutorial intent mutually constrained, and test how-to/tutorial queries separately.
- Baseline metadata can make local workflows stricter -> provide clear failure messages that name the missing DB counts or mismatched query hash.
- A deterministic reranker can become a pile of magic constants -> keep boosts named, small, and covered by focused tests for each failure class.
- Addon failures may reflect missing indexed content rather than ranking -> keep addon queries report-only until diagnostics show expected addon rows are present.

## Migration Plan

1. Add metadata validation without changing search behavior.
2. Add query-plan construction and tests for alias/symbol/doc-type/addon intent.
3. Wire query-plan symbol candidates into existing recall paths.
4. Add deterministic reranking and promote only queries that pass on the canonical database.
5. Refresh the baseline with metadata once the quality gate is stable.

Rollback is straightforward: revert the change commits and restore the previous baseline/query fixture. No database migration is required.

## Open Questions

- The canonical database for local verification is assumed to be `godot_rag.db`; CI may need an equivalent generated or fixture database if that file is not available.
- Addon query promotion depends on whether addon documents are indexed in the canonical database; this change should diagnose that before changing addon gating.
