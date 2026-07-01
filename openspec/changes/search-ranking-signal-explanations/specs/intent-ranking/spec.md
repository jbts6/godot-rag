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
