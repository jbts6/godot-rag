## Context

The current search path assembles results in `rst2md/rag/searcher.py` from several independent ranking sources:

- hybrid retrieval via FTS and vector search fused with RRF;
- symbol recall with fixed score tiers for exact, suffix, and prefix matches;
- FTS-only scoring derived from BM25;
- graph expansion through `chunk_relations`;
- deterministic reranking in `rst2md/rag/fusion.py`.

`SearchResult` currently exposes the final score plus relation metadata, but it does not preserve the named signals that produced or adjusted that score. Existing diagnostics can show search mode and fallback reason, yet they cannot explain why an individual result ranked above another result.

## Goals / Non-Goals

**Goals:**

- Attach structured, stable ranking signal explanations to each `SearchResult`.
- Preserve existing `search_database()` and `search_database_with_metadata()` call compatibility.
- Cover all current signal families: symbol recall, FTS/BM25, hybrid/RRF, graph expansion, and deterministic reranking.
- Make CLI/debug and test assertions able to reference named ranking signals.

**Non-Goals:**

- Do not retune ranking weights as part of this change.
- Do not add new retrieval channels or database schema.
- Do not make explanations depend on generated embeddings being available.
- Do not require every internal intermediate value to be exposed if it would make the API unstable.

## Decisions

### Add a structured signal model to search results

Add a small frozen dataclass such as `RankingSignal` with fields for `name`, `weight`, `value`, and optional `details`, then add `ranking_signals: list[RankingSignal]` to `SearchResult` with a default empty list.

Alternatives considered:

- Store explanations only in `SearchMetadata`: rejected because ranking causes are per-result, not per-query.
- Store a free-form string: rejected because tests and JSON/debug output need stable names.

### Record signals during candidate assembly, not after the fact

The searcher should keep a mutable internal result dictionary that includes a `ranking_signals` list alongside the score. Each scoring stage appends or updates signals when it creates or improves a candidate. At final conversion time, those signals become immutable `SearchResult` data.

Alternatives considered:

- Recompute explanations from final scores: rejected because final score alone cannot distinguish symbol, RRF, FTS, graph, or rerank contributions.
- Add separate debug-only code paths: rejected because explanations should test the same path used by normal search.

### Make reranking return explainable adjustments

`rerank_results()` currently applies `_rerank_bonus()` and returns replaced results. It should preserve current ordering behavior while adding named signals for non-zero bonuses, such as alias symbol, direct symbol, doc-type intent, or addon intent.

Alternatives considered:

- Keep rerank explanations only in tests: rejected because diagnostics and CLI/debug output should see the same signal names.

### Keep compatibility by using additive model fields

Existing callers should continue to receive `SearchResult` objects with all existing fields. Adding a dataclass field with a default factory keeps direct construction tests and callers source-compatible.

CLI JSON/debug output can include ranking signals when emitting structured result data. Human output should remain concise and show signals only in debug or metadata-oriented modes unless an existing command already has a verbose search output path.

## Risks / Trade-offs

- **Risk:** Signal lists become noisy or too verbose. → **Mitigation:** expose stable signal names and concise details; avoid dumping every raw candidate comparison.
- **Risk:** Mutating signal lists while replacing dataclass instances causes accidental sharing. → **Mitigation:** use default factories and copy lists when replacing results.
- **Risk:** Reranking explanations accidentally change ranking behavior. → **Mitigation:** focused tests must assert final ordering remains stable while signal names are added.
- **Risk:** CLI output shape changes unexpectedly. → **Mitigation:** keep default human output compatible and add signals to structured/debug output where existing metadata already belongs.

## Migration Plan

1. Add the additive model fields and tests for default construction compatibility.
2. Thread signal recording through searcher candidate assembly and graph expansion.
3. Update reranking to append named bonus signals without changing score math.
4. Expose signals in CLI/debug or JSON output where appropriate.
5. Run focused searcher, CLI, and search evaluation tests, then full test suite if feasible.

Rollback is straightforward: remove the additive signal field and signal recording code. No persisted database migration is involved.

## Open Questions

- Whether the default human CLI output should show a compact signal summary immediately or only under an existing verbose/debug mode should be finalized during implementation after inspecting current CLI output conventions.
