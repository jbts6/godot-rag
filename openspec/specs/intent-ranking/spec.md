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
The system SHALL apply doc-type boost after candidate assembly, before final sort.

#### Scenario: Boost adjusts scores and re-sorts
- **WHEN** search results are assembled and intent boost is applicable
- **THEN** each result's score SHALL be increased by the boost value and results SHALL be re-sorted by adjusted score descending

