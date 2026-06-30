# search-quality-diagnostics Specification

## Purpose
TBD - created by archiving change search-quality-optimization-loop. Update Purpose after archive.
## Requirements
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

### Requirement: Diagnostic limit is opt-in
The system SHALL only compute diagnostics when `diagnostic_limit` parameter is explicitly provided.

#### Scenario: Default evaluation skips diagnostics
- **WHEN** `evaluate_database` is called without `diagnostic_limit`
- **THEN** `QueryResult.diagnostics` SHALL be `None` for all results

### Requirement: Evaluation reports baseline input validity
Search quality diagnostics SHALL report whether the evaluated database is valid for baseline writes and regression comparisons.

#### Scenario: invalid baseline input is diagnosed
- **WHEN** a database fails baseline input validation
- **THEN** diagnostics MUST include the failing count or consistency check
- **AND** the command output MUST explain why the baseline was not written

#### Scenario: baseline comparison reports query-suite mismatch
- **WHEN** a baseline comparison uses a query suite whose hash differs from the baseline metadata
- **THEN** diagnostics MUST report the mismatch
- **AND** regression messages MUST distinguish query-suite drift from ranking regression

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

### Requirement: Report-only query triage is summarized
Search quality diagnostics SHALL produce a triage summary for report-only evaluation queries when diagnostics are requested.

#### Scenario: report-only queries are classified
- **WHEN** search quality evaluation runs with report-only queries and a diagnostic window
- **THEN** each report-only query MUST be assigned a triage classification
- **AND** the classification MUST distinguish missing expected data, missing recall, low ranking, filter mismatch, degraded search execution, and promotion-ready results

#### Scenario: triage output includes evidence
- **WHEN** a report-only query is classified
- **THEN** the triage output MUST include the evidence used for the decision, including expected target presence, best observed rank when available, search mode, fallback reason, and observed top results

#### Scenario: promotion-ready queries are explicit
- **WHEN** a report-only query's expected target is present and matches within its required rank without degraded search execution
- **THEN** diagnostics MUST mark the query as eligible for gating promotion
- **AND** the output MUST identify that promotion as a candidate recommendation rather than silently changing the query suite

#### Scenario: follow-up ownership is identified
- **WHEN** a report-only query is not promotion-ready
- **THEN** diagnostics MUST identify the likely follow-up type as data or fixture work, recall work, ranking work, filter work, or degraded search investigation

### Requirement: Promotion-ready report-only queries can be reviewed into gating
Search quality diagnostics SHALL support a manual workflow where report-only queries classified as promotion-ready can be converted into gating queries after review.

#### Scenario: reviewed non-addon candidates are promoted
- **WHEN** report-only triage classifies a non-addon query as promotion-ready on the canonical database
- **THEN** maintainers MAY remove its `report_only` flag
- **AND** the refreshed baseline MUST include that query in the gating comparison set

#### Scenario: unstable candidates remain report-only
- **WHEN** a promotion-ready query belongs to a category with unstable data ownership, such as addon coverage
- **THEN** maintainers SHOULD keep it report-only until the data source is explicitly accepted as stable

#### Scenario: non-ready queries remain advisory
- **WHEN** a report-only query is classified as low ranking, missing recall, missing expected data, filter mismatch, or degraded search
- **THEN** it MUST remain report-only until a focused follow-up change resolves the underlying cause

