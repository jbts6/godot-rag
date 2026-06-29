# search-quality-diagnostics Specification

## Purpose
TBD - created by archiving change search-quality-optimization-loop. Update Purpose after archive.
## Requirements
### Requirement: Failure diagnostics for evaluation queries
The system SHALL attach diagnostic metadata to failed evaluation queries when `diagnostic_limit` is specified.

#### Scenario: Diagnostics show expected target exists in DB
- **WHEN** a query fails but its expected paths/symbols exist in the database
- **THEN** `FailureDiagnostics.expected_present` SHALL be `True` and `expected_rows` SHALL contain the matching rows

#### Scenario: Diagnostics show best rank in window
- **WHEN** a query fails and `diagnostic_limit` is set
- **THEN** `FailureDiagnostics.best_rank` SHALL be the rank of the best matching result within the diagnostic window, or `None` if not found

#### Scenario: Diagnostics included in JSON output
- **WHEN** evaluation produces failures with diagnostics enabled
- **THEN** the JSON output SHALL include `failures[].diagnostics` with `expected_present`, `best_rank`, `best_rank_no_graph`, `expected_rows`, and `diagnostic_window` fields

#### Scenario: Diagnostics included in text report
- **WHEN** evaluation produces failures with diagnostics enabled
- **THEN** the text report SHALL include `diagnostics:` lines showing `expected_present`, `best_rank` values

### Requirement: Diagnostic limit is opt-in
The system SHALL only compute diagnostics when `diagnostic_limit` parameter is explicitly provided.

#### Scenario: Default evaluation skips diagnostics
- **WHEN** `evaluate_database` is called without `diagnostic_limit`
- **THEN** `QueryResult.diagnostics` SHALL be `None` for all results

