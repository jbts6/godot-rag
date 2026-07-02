# intent-ranking Specification

## Purpose
TBD - created by archiving change search-quality-optimization-loop. Update Purpose after archive.
## Requirements
### Requirement: Tutorial intent detection
The system SHALL detect tutorial intent from query patterns. The legacy fixed additive boost (`doc_type_boost` returning 0.05 for tutorial doc_type) SHALL be replaced by a floor-plus-multiplicative rerank boost applied in `_rerank_bonus`. The `doc_type_boost` function SHALL return 0.0 for all inputs (retained for backward compatibility with existing callers and tests) and the substantive tutorial weighting SHALL move to the rerank stage.

The boost SHALL use two tunable constants: `TUTORIAL_SCORE_FLOOR` (minimum pre-rerank score eligible for multiplicative treatment, default ≥ 3.0) and `TUTORIAL_BOOST_FACTOR` (multiplicative factor, default ≥ 5.0). Both SHALL be set to the smallest combination that lifts both `scene tree tutorial` and `how to use scene tree nodes` queries into rank ≤5 on the canonical baseline, with spec-fixed lower bounds.

The rerank bonus formula SHALL be `max(result.score, TUTORIAL_SCORE_FLOOR) * (TUTORIAL_BOOST_FACTOR - 1)`, yielding a reranked score of `result.score + max(result.score, TUTORIAL_SCORE_FLOOR) * (TUTORIAL_BOOST_FACTOR - 1)`. When `result.score >= TUTORIAL_SCORE_FLOOR`, this reduces to `result.score * TUTORIAL_BOOST_FACTOR`. When `result.score < TUTORIAL_SCORE_FLOOR`, the floor lifts the effective base so that low-bm25 tutorial results can still overtake high-bm25 class results.

#### Scenario: How-to query triggers tutorial intent
- **WHEN** a query starts with "how to " or contains " tutorial", " guide", or "learn "
- **THEN** `_doc_type_intent` SHALL return "tutorial"
- **AND** `doc_type_boost` SHALL return 0.0 for all doc types (legacy function retained but neutralized)
- **AND** `_rerank_bonus` SHALL apply a floor-plus-multiplicative boost to tutorial doc_type results when no symbol candidates exist in the plan

#### Scenario: Symbol query does not trigger intent boost
- **WHEN** a query contains "." or "_" (symbol-like pattern)
- **THEN** `_doc_type_intent` SHALL return None
- **AND** `_rerank_bonus` SHALL NOT apply the tutorial boost to any result

#### Scenario: Tutorial boost is floored multiplicative on result score
- **WHEN** `_rerank_bonus` is called for a result whose `doc_type == "tutorial"` and the plan has tutorial intent and no symbol candidates
- **THEN** the bonus SHALL equal `max(result.score, TUTORIAL_SCORE_FLOOR) * (TUTORIAL_BOOST_FACTOR - 1)`
- **AND** the reranked score SHALL equal `result.score + max(result.score, TUTORIAL_SCORE_FLOOR) * (TUTORIAL_BOOST_FACTOR - 1)`
- **AND** the bonus SHALL be recorded as a named ranking signal `rerank.doc_type_intent` with weight equal to the bonus amount

#### Scenario: Low tutorial score is floored before boost
- **WHEN** `_rerank_bonus` is called for a tutorial result whose `result.score < TUTORIAL_SCORE_FLOOR` (e.g., score=0.66, FLOOR=3.0, FACTOR=5.0)
- **THEN** the reranked score SHALL equal `result.score + TUTORIAL_SCORE_FLOOR * (TUTORIAL_BOOST_FACTOR - 1)` (e.g., 0.66 + 3*4 = 12.66)
- **AND** the reranked score MUST be able to overtake class-doc results with bm25-scaled scores up to `TUTORIAL_SCORE_FLOOR * (TUTORIAL_BOOST_FACTOR - 1)` (e.g., 12.0)

#### Scenario: High tutorial score is not overshooting
- **WHEN** `_rerank_bonus` is called for a tutorial result whose `result.score >= TUTORIAL_SCORE_FLOOR` (e.g., score=5.0, FLOOR=3.0, FACTOR=5.0)
- **THEN** the reranked score SHALL equal `result.score * TUTORIAL_BOOST_FACTOR` (e.g., 25.0)
- **AND** the reranked score MUST remain below the symbol exact-match score (100.0) so that symbol candidates, when present, are not suppressed

### Requirement: Intent boost applied post-ranking
The system SHALL apply deterministic intent reranking after candidate assembly, before final sort. Existing doc-type boosts SHALL become one named reranking signal rather than the only intent-ranking mechanism.

#### Scenario: Boost adjusts scores and re-sorts
- **WHEN** search results are assembled and intent boost is applicable
- **THEN** each result's score SHALL be adjusted by named reranking signals
- **AND** results SHALL be re-sorted by adjusted score descending

#### Scenario: Reranking is explainable in tests
- **WHEN** a focused search ranking test asserts an alias or intent promotion
- **THEN** the expected promotion MUST correspond to a named deterministic signal

### Requirement: Deterministic reranking uses query-plan signals
Search SHALL apply deterministic reranking signals after candidate assembly and before returning final results. For tutorial intent, the reranking SHALL be floor-plus-multiplicative rather than purely additive so that tutorial results with low lexical scores can overtake class results with high bm25 scores when the user expresses tutorial intent.

#### Scenario: alias symbol match is promoted
- **WHEN** a candidate result symbol exactly matches a query-plan alias-derived symbol candidate
- **THEN** reranking MUST increase that candidate's final rank relative to candidates without symbol, path, heading, or intent matches

#### Scenario: tutorial intent floored-multiplicative promotes tutorial results
- **WHEN** a query expresses tutorial intent (e.g., "scene tree tutorial") and a candidate result has `doc_type == "tutorial"`
- **THEN** reranking MUST apply bonus `max(result.score, TUTORIAL_SCORE_FLOOR) * (TUTORIAL_BOOST_FACTOR - 1)` (defaults FLOOR ≥ 3.0, FACTOR ≥ 5.0)
- **AND** the candidate MUST be able to overtake class-doc results whose bm25-scaled scores would otherwise dominate under additive-only boosting

#### Scenario: doc-type intent remains constrained
- **WHEN** a query expresses tutorial intent
- **THEN** reranking MUST prefer tutorial results without suppressing exact symbol matches for symbol-like queries

#### Scenario: addon intent can be represented without gating unstable data
- **WHEN** a query expresses addon intent
- **THEN** reranking MUST expose addon intent as a ranking signal
- **AND** evaluation MUST keep addon queries report-only unless expected addon rows exist in the canonical database

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

### Requirement: Inheritance intent detection
The system SHALL detect inheritance intent from query patterns and surface it on the query plan so that the searcher can apply targeted `inherits`-relation traversal. Inheritance intent SHALL be triggered by the keywords `inherits`, `subclass of`, `parent class`, and `derived from` (case-insensitive, whole-word/whole-phrase matching). The bare verb `extends` SHALL NOT trigger inheritance intent to avoid false positives on queries like "how to extend Node functionality".

#### Scenario: inherits keyword triggers inheritance intent
- **WHEN** a query contains the token "inherits" (case-insensitive) as a whole word (e.g., "Node inherits Object")
- **THEN** `_inheritance_intent` SHALL return True
- **AND** the query plan SHALL set `inheritance_intent = True`

#### Scenario: synonym phrases trigger inheritance intent
- **WHEN** a query contains any of the phrases "subclass of", "parent class", or "derived from" (case-insensitive)
- **THEN** `_inheritance_intent` SHALL return True
- **AND** the query plan SHALL set `inheritance_intent = True`

#### Scenario: bare verb extends does not trigger inheritance intent
- **WHEN** a query contains the word "extends" or "extend" but NOT in the `Class extends Class` form (e.g., "how to extend Node functionality")
- **THEN** `_inheritance_intent` SHALL return False
- **AND** the query plan SHALL set `inheritance_intent = False`

#### Scenario: non-inheritance query does not trigger
- **WHEN** a query does not contain any inheritance keyword (e.g., "Node connect", "tutorial scene tree")
- **THEN** `_inheritance_intent` SHALL return False
- **AND** the query plan SHALL set `inheritance_intent = False`

### Requirement: Inheritance relation traversal in search

When the query plan expresses inheritance intent, search SHALL first ensure that the relevant `class_summary` chunks are present in the candidate set — the query's named classes SHALL be recalled even when their FTS/vector score falls below the default top-K threshold — and SHALL then traverse `inherits` relations from each `class_summary` chunk in the candidate set, adding parent `class_summary` chunks to the result set with a score boost higher than the generic graph-expansion weight.

The recall precondition exists because the directed `inherits` traversal can only fire on source chunks already in the candidate set. Without the precondition, the traversal is vacuously satisfied (no source chunks → no traversal) and the feature delivers no value for inheritance queries whose target `class_summary` is not in the default top-K — which is the observed production gap for `Node inherits Object` (Node `class_summary` absent from top-K → `inherits` traversal never fires → Object `class_summary` never recalled → `rank=None`).

#### Scenario: inheritance query recalls target class_summary into candidate set

- **WHEN** the query "Node inherits Object" is searched with inheritance intent
- **AND** the Node `class_summary` chunk's default FTS/vector score falls below the top-K threshold
- **THEN** the search SHALL still include the Node `class_summary` chunk in the candidate set passed to `inherits` traversal
- **AND** this recall SHALL be scoped to inheritance-intent queries (non-inheritance queries MUST NOT receive this boost)

#### Scenario: inheritance query recalls parent class_summary

- **WHEN** the query "Node inherits Object" is searched with inheritance intent
- **AND** the Node `class_summary` chunk is in the candidate set (per the recall precondition above)
- **THEN** the result set SHALL include the Object `class_summary` chunk
- **AND** the Object chunk SHALL carry a `graph.inherits` ranking signal

#### Scenario: inheritance traversal is scoped to inherits relation

- **WHEN** inheritance intent traversal runs
- **THEN** the SQL query MUST filter `r.relation = 'inherits'` (not generic graph expansion)
- **AND** traversal MUST NOT pull `references`, `see_also`, or `parent` edges via this code path (those remain on the generic graph expansion path)

#### Scenario: no inherits edge does not crash

- **WHEN** inheritance intent is detected but no `inherits` edge exists in the relations table
- **THEN** traversal SHALL return no additional chunks
- **AND** the search SHALL NOT raise an error

