# intent-ranking Specification

## Purpose
TBD - created by archiving change search-quality-optimization-loop. Update Purpose after archive.
## Requirements
### Requirement: Tutorial intent detection
The system SHALL detect tutorial intent from query patterns and boost tutorial doc-type results.

#### Scenario: How-to query boosts tutorial results
- **WHEN** a query starts with "how to " or contains " tutorial", " guide", or "learn "
- **THEN** `doc_type_boost` SHALL return 0.05 for `doc_type == "tutorial"` and 0.0 for other types

#### Scenario: Symbol query does not trigger intent boost
- **WHEN** a query contains "." or "_" (symbol-like pattern)
- **THEN** `doc_type_boost` SHALL return 0.0 for all doc types

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
Search SHALL apply deterministic reranking signals after candidate assembly and before returning final results.

#### Scenario: alias symbol match is promoted
- **WHEN** a candidate result symbol exactly matches a query-plan alias-derived symbol candidate
- **THEN** reranking MUST increase that candidate's final rank relative to candidates without symbol, path, heading, or intent matches

#### Scenario: doc-type intent remains constrained
- **WHEN** a query expresses tutorial intent
- **THEN** reranking MUST prefer tutorial results without suppressing exact symbol matches for symbol-like queries

#### Scenario: addon intent can be represented without gating unstable data
- **WHEN** a query expresses addon intent
- **THEN** reranking MUST expose addon intent as a ranking signal
- **AND** evaluation MUST keep addon queries report-only unless expected addon rows exist in the canonical database

