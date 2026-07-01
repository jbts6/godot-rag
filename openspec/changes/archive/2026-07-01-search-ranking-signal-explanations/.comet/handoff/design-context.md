# Comet Design Handoff

- Change: search-ranking-signal-explanations
- Phase: design
- Mode: compact
- Context hash: fbcaecbbdd163f07c24a089b946c430f14f810eadc7b986b53bff30f5ee4c0f9

Generated-by: comet-handoff.sh

OpenSpec remains the canonical capability spec. This handoff is a deterministic, source-traceable context pack, not an agent-authored summary.

## openspec/changes/search-ranking-signal-explanations/proposal.md

- Source: openspec/changes/search-ranking-signal-explanations/proposal.md
- Lines: 1-27
- SHA256: 3f09e4a2e72ad472187fa156f0a8ac5a27a73efdff6885963172292899adc0f0

```md
## Why

Search ranking now combines symbol recall, FTS/BM25, vector/RRF fusion, graph expansion, and deterministic reranking, but callers only receive final scores and sparse relation metadata. This makes it hard to diagnose why a result ranked highly, why expected results were demoted, or which existing ranking signal should be adjusted.

## What Changes

- Add structured ranking signal explanations to search results so each returned result can describe the major signals that affected its final rank.
- Preserve the existing `search_database()` compatibility surface while exposing explanations through metadata-bearing search responses and CLI/debug output.
- Ensure explanations cover existing signal families: symbol matches, hybrid retrieval/RRF, FTS scoring, graph expansion, and deterministic reranking.
- Extend tests so ranking assertions can validate named signals instead of depending only on final order.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `intent-ranking`: Search results expose named ranking signals and explanation metadata for deterministic ranking and reranking behavior.

## Impact

- Affected code: `rst2md/rag/models.py`, `rst2md/rag/searcher.py`, `rst2md/rag/fusion.py` or reranking helpers if needed, `rst2md/rag/cli.py`, and focused tests under `rst2md/tests/`.
- APIs: `search_database_with_metadata()` may return richer result metadata; `search_database()` should remain source-compatible for existing callers.
- Dependencies: no new runtime dependencies expected.
- Systems: search quality diagnostics and CLI/debug output can consume the explanations, but the ranking algorithm itself should remain behaviorally stable unless tests reveal existing unexplained signal gaps.
```

## openspec/changes/search-ranking-signal-explanations/design.md

- Source: openspec/changes/search-ranking-signal-explanations/design.md
- Lines: 1-82
- SHA256: e143b6cd5aa74deceb5f08aa08d334efad5676013b86c347f5546f726931e3b2

[TRUNCATED]

```md
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
```

Full source: openspec/changes/search-ranking-signal-explanations/design.md

## openspec/changes/search-ranking-signal-explanations/tasks.md

- Source: openspec/changes/search-ranking-signal-explanations/tasks.md
- Lines: 1-28
- SHA256: d15b421872918b30a91bff56c62d9d560851865e288a69d14d15ddc6a0d1dbe8

```md
## 1. Model and Compatibility

- [ ] 1.1 Add a structured ranking signal model to `rst2md/rag/models.py`.
- [ ] 1.2 Add default-empty ranking explanations to `SearchResult` without breaking existing construction.
- [ ] 1.3 Extend model shape tests to cover ranking signal defaults and serialization-friendly fields.

## 2. Search Signal Recording

- [ ] 2.1 Record symbol recall signals for exact, suffix, prefix, and alias-derived matches.
- [ ] 2.2 Record hybrid/RRF and FTS scoring signals during candidate assembly.
- [ ] 2.3 Record graph expansion signals including relation type and distance.
- [ ] 2.4 Preserve accumulated signals when later ranking stages improve an existing candidate.

## 3. Rerank Signal Recording

- [ ] 3.1 Update deterministic reranking to append named non-zero bonus signals.
- [ ] 3.2 Preserve existing rerank score math and final ordering behavior.

## 4. CLI and Diagnostics Output

- [ ] 4.1 Expose ranking signals in structured or debug search output.
- [ ] 4.2 Keep default human-readable search output concise and backward-compatible.

## 5. Verification

- [ ] 5.1 Add focused tests for symbol, FTS fallback, hybrid/RRF, graph expansion, and rerank explanations.
- [ ] 5.2 Run focused searcher, CLI, and search evaluation tests.
- [ ] 5.3 Run the broader pytest suite if focused tests pass and runtime is practical.
```

## openspec/changes/search-ranking-signal-explanations/specs/intent-ranking/spec.md

- Source: openspec/changes/search-ranking-signal-explanations/specs/intent-ranking/spec.md
- Lines: 1-63
- SHA256: db750a381baf77619ca4cad2dd76699b0db0472be122e38f2ea94a0822ff0928

```md
## ADDED Requirements

### Requirement: Search results expose ranking signal explanations
Search results SHALL expose structured ranking signal explanations for the named signals that materially contributed to each returned result's final rank.

#### Scenario: symbol recall explanation is present
- **WHEN** a result is selected through exact, suffix, prefix, or alias-derived symbol matching
- **THEN** the result MUST include a ranking signal whose name identifies the symbol match type
- **AND** the signal MUST include the score or bonus contribution used by that match type

#### Scenario: hybrid fusion explanation is present
- **WHEN** a result is selected through hybrid FTS and vector recall with RRF fusion
- **THEN** the result MUST include a ranking signal identifying RRF fusion
- **AND** the signal MUST include a stable value or detail sufficient to distinguish it from FTS-only scoring

#### Scenario: FTS explanation is present without vectors
- **WHEN** vector search is unavailable and a result is selected through FTS scoring
- **THEN** the result MUST include a ranking signal identifying FTS scoring
- **AND** the signal MUST remain available even when search metadata reports an FTS-only fallback

#### Scenario: graph expansion explanation is present
- **WHEN** graph expansion adds or annotates a related result
- **THEN** the result MUST include a ranking signal identifying graph expansion
- **AND** the signal MUST include the relation type and graph distance when available

#### Scenario: deterministic rerank explanation is present
- **WHEN** deterministic reranking changes a result score through alias, symbol, doc-type intent, or addon intent logic
- **THEN** the result MUST include one or more ranking signals identifying the reranking causes
- **AND** each reranking signal MUST include the bonus value applied to the final score

### Requirement: Ranking explanations preserve search API compatibility
Ranking signal explanations SHALL be additive to the search result model and SHALL NOT break existing callers that consume search results without explanation data.

#### Scenario: legacy search result construction remains valid
- **WHEN** existing tests or callers construct `SearchResult` without ranking explanation fields
- **THEN** construction MUST still succeed
- **AND** the result MUST expose an empty explanation list by default

#### Scenario: basic search API remains source-compatible
- **WHEN** callers use `search_database()` to retrieve a list of search results
- **THEN** the returned values MUST remain `SearchResult` instances with the existing fields still available
- **AND** ranking explanations MUST be available as additional result data

#### Scenario: metadata search API includes explanations per result
- **WHEN** callers use `search_database_with_metadata()`
- **THEN** each returned result MAY include ranking explanations
- **AND** query-level metadata MUST continue to expose search mode, vector availability, and fallback reason

### Requirement: CLI and diagnostics can display ranking explanations
Search-facing CLI or diagnostic output SHALL be able to display ranking signal explanations without requiring ranking behavior to change.

#### Scenario: structured output includes ranking signals
- **WHEN** a search command emits structured result output
- **THEN** each result entry MUST include ranking signal explanation data when any signals are present

#### Scenario: default human output remains concise
- **WHEN** a search command emits default human-readable output
- **THEN** ranking explanation data MUST NOT make the default output substantially noisier
- **AND** a debug, verbose, or structured output path MUST remain available for inspecting the signals

#### Scenario: ranking tests assert named signals
- **WHEN** focused search ranking tests verify symbol, hybrid, graph, or rerank behavior
- **THEN** tests MUST be able to assert named ranking signals in addition to final result ordering
```

