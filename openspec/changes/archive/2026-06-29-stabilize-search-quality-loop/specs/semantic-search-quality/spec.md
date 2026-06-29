## ADDED Requirements

### Requirement: Baseline artifacts identify their evaluation inputs
Search quality baselines SHALL record enough metadata to prove which database and query suite produced the metrics.

#### Scenario: baseline includes database fingerprint
- **WHEN** a baseline is written from a populated evaluation database
- **THEN** the baseline JSON MUST include document, chunk, symbol, and vector row counts
- **AND** it MUST include a deterministic database fingerprint derived from those counts and available file metadata

#### Scenario: baseline includes query suite identity
- **WHEN** a baseline is written
- **THEN** the baseline JSON MUST include a deterministic hash of the loaded query definitions
- **AND** a later comparison MUST report when the current query-suite hash differs from the baseline hash

### Requirement: Invalid evaluation databases cannot create baselines
Real-database search quality evaluation SHALL reject empty or incomplete databases before writing a baseline.

#### Scenario: empty database baseline write is rejected
- **WHEN** baseline writing is requested for a database with zero documents, chunks, or symbols
- **THEN** the command MUST fail
- **AND** no baseline file MUST be written
- **AND** the error MUST identify the zero-count tables

#### Scenario: vector row mismatch is reported
- **WHEN** baseline writing is requested for a database with a `vec_chunks` row count that does not match the `chunks` row count
- **THEN** the command MUST fail unless vector checks are explicitly disabled for a fixture-only evaluation
- **AND** the error MUST identify the vector row mismatch

### Requirement: Report-only promotion follows objective rules
Search quality evaluation SHALL define when report-only queries can become gating queries.

#### Scenario: stable report-only query is eligible for promotion
- **WHEN** a report-only query has an expected target present in the canonical database
- **AND** graph-enabled evaluation ranks the expected target within the query required window
- **AND** the query category remains represented in gating metrics
- **THEN** the query MAY be promoted to gating in the query fixture

#### Scenario: unstable report-only query remains visible
- **WHEN** a report-only query fails promotion criteria
- **THEN** it MUST remain in evaluation output
- **AND** its failure MUST NOT cause the regression gate to fail

## MODIFIED Requirements

### Requirement: Search quality is evaluated with categorized golden queries
The packaged query suite SHALL contain at least 30 unique query IDs with at least 12 gating queries and at least 8 report-only queries, covering `class`, `symbol`, `tutorial`, `engine`, and `addon` categories. Gating metrics SHALL report empty or missing category coverage explicitly instead of allowing a required category to disappear silently.

#### Scenario: Query suite meets size and tier requirements
- **WHEN** `load_queries` loads the packaged query file
- **THEN** the result SHALL contain >= 30 queries with >= 12 gating and >= 8 report-only

#### Scenario: Query suite covers all required categories
- **WHEN** `load_queries` loads the packaged query file
- **THEN** the query categories SHALL include `class`, `symbol`, `tutorial`, `engine`, and `addon`

#### Scenario: Query suite includes normalization and graph tags
- **WHEN** `load_queries` loads the packaged query file
- **THEN** at least one query SHALL have tag `normalization` and at least one SHALL have tag `graph`

#### Scenario: Required gating category disappears
- **WHEN** real-database evaluation computes gating metrics
- **AND** a required category has zero gating queries
- **THEN** the report MUST include an explicit category coverage warning
