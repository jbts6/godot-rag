## MODIFIED Requirements

### Requirement: Failure diagnostics for evaluation queries
The system SHALL attach diagnostic metadata to failed evaluation queries when `diagnostic_limit` is specified. Diagnostics SHALL also expose enough search execution metadata to distinguish ranking failures from degraded search mode, vector fallback, graph expansion changes, and filter precision issues.

#### Scenario: Diagnostics show expected target exists in DB
- **WHEN** a query fails but its expected paths/symbols exist in the database
- **THEN** `FailureDiagnostics.expected_present` SHALL be `True` and `expected_rows` SHALL contain the matching rows

#### Scenario: Diagnostics show best rank in window
- **WHEN** a query fails and `diagnostic_limit` is set
- **THEN** `FailureDiagnostics.best_rank` SHALL be the rank of the best matching result within the diagnostic window, or `None` if not found

#### Scenario: Diagnostics include search execution mode
- **WHEN** evaluation produces failures with diagnostics enabled
- **THEN** diagnostics MUST include whether the query used hybrid search or FTS-only fallback
- **AND** diagnostics MUST include the fallback or degraded reason when one exists

#### Scenario: Diagnostics included in JSON output
- **WHEN** evaluation produces failures with diagnostics enabled
- **THEN** the JSON output SHALL include `failures[].diagnostics` with `expected_present`, `best_rank`, `best_rank_no_graph`, `expected_rows`, `diagnostic_window`, search mode, and fallback/degraded fields

#### Scenario: Diagnostics included in text report
- **WHEN** evaluation produces failures with diagnostics enabled
- **THEN** the text report SHALL include `diagnostics:` lines showing `expected_present`, `best_rank` values, search mode, and fallback/degraded reason

### Requirement: Failure diagnostics guide promotion decisions
Search quality diagnostics SHALL expose whether a failed or report-only query is blocked by missing data, recall, ranking, filtering, graph expansion, or degraded search execution.

#### Scenario: report-only query has missing expected data
- **WHEN** a report-only query expects addon or symbol data that is absent from the canonical database
- **THEN** diagnostics MUST mark the expected target as not present
- **AND** the query MUST be ineligible for gating promotion

#### Scenario: report-only query has low ranking
- **WHEN** a report-only query's expected target is present but below the required rank
- **THEN** diagnostics MUST include the best observed rank in the diagnostic window
- **AND** the query MUST remain report-only until ranking improves

#### Scenario: report-only query is affected by degraded search mode
- **WHEN** a report-only query fails while vector search is unavailable or degraded
- **THEN** diagnostics MUST identify the degraded mode
- **AND** promotion decisions MUST not treat the failure as a pure ranking regression

## ADDED Requirements

### Requirement: Evaluation diagnostics include latency summaries
Search quality diagnostics SHALL include latency summaries for evaluated query runs.

#### Scenario: JSON report includes latency summary
- **WHEN** search quality evaluation emits JSON
- **THEN** the report MUST include latency summary fields for evaluated queries

#### Scenario: text report includes latency summary
- **WHEN** search quality evaluation emits text output
- **THEN** the report MUST include a concise latency summary suitable for spotting slowdowns

### Requirement: Searcher refactors preserve diagnostics
Internal searcher restructuring SHALL preserve externally visible search results, evaluation metrics, and diagnostic metadata.

#### Scenario: equivalent refactor keeps baseline stable
- **WHEN** searcher internals are split without intended ranking changes
- **THEN** deterministic quality tests and real-database baseline comparison MUST remain stable

#### Scenario: metadata remains available after refactor
- **WHEN** search execution internals are reorganized
- **THEN** evaluation diagnostics MUST still receive search mode, fallback/degraded reason, and latency data
