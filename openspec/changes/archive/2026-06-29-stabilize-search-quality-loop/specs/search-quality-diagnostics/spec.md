## ADDED Requirements

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
Search quality diagnostics SHALL expose whether a failed or report-only query is blocked by missing data, recall, ranking, or filtering.

#### Scenario: report-only query has missing expected data
- **WHEN** a report-only query expects addon or symbol data that is absent from the canonical database
- **THEN** diagnostics MUST mark the expected target as not present
- **AND** the query MUST be ineligible for gating promotion

#### Scenario: report-only query has low ranking
- **WHEN** a report-only query's expected target is present but below the required rank
- **THEN** diagnostics MUST include the best observed rank in the diagnostic window
- **AND** the query MUST remain report-only until ranking improves
