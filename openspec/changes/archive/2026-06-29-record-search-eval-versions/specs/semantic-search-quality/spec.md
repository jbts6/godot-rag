## MODIFIED Requirements

### Requirement: Baseline artifacts identify their evaluation inputs
Search quality baselines SHALL record enough metadata to prove which database, query suite, and evaluator/search version produced the metrics.

#### Scenario: baseline includes database fingerprint
- **WHEN** a baseline is written from a populated evaluation database
- **THEN** the baseline JSON MUST include document, chunk, symbol, and vector row counts
- **AND** it MUST include a deterministic database fingerprint derived from those counts and available file metadata

#### Scenario: baseline includes query suite identity
- **WHEN** a baseline is written
- **THEN** the baseline JSON MUST include a deterministic hash of the loaded query definitions
- **AND** a later comparison MUST report when the current query-suite hash differs from the baseline hash

#### Scenario: baseline includes evaluator and search versions
- **WHEN** a baseline is written
- **THEN** the baseline JSON MUST include evaluator version metadata
- **AND** it MUST include search version metadata
- **AND** those values MUST be non-empty strings
