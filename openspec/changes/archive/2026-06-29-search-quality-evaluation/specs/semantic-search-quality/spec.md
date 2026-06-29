## ADDED Requirements

### Requirement: Search quality is evaluated with categorized golden queries
Semantic search quality SHALL be evaluated with a categorized golden-query set that supports both deterministic fixture tests and real-database evaluation.

#### Scenario: fixture golden queries run in normal verification
- **WHEN** the focused search quality test suite runs
- **THEN** it MUST build or use a small deterministic fixture database
- **AND** it MUST execute categorized golden queries without depending on untracked generated database files

#### Scenario: real database evaluation runs from an explicit database path
- **WHEN** a developer runs the search quality evaluation against a provided release database path
- **THEN** the evaluator MUST execute the real-database golden query set against that database
- **AND** it MUST NOT require the generated SQLite database file to be committed

#### Scenario: query entries describe expected result constraints
- **WHEN** a golden query entry is loaded
- **THEN** it MUST include a query string, category, and top-K requirement
- **AND** it MUST be able to express expected path, symbol, doc type, or addon constraints

### Requirement: Search quality metrics are reported consistently
Search quality evaluation SHALL report ranking metrics in a stable shape suitable for humans and regression checks.

#### Scenario: metrics are calculated overall and by category
- **WHEN** search quality evaluation completes
- **THEN** it MUST report `hit@1`, `hit@3`, `hit@5`, and `MRR@5`
- **AND** it MUST report those metrics overall and grouped by query category

#### Scenario: failed queries include diagnostic detail
- **WHEN** a golden query fails its top-K expectation
- **THEN** the report MUST include the query, category, expected constraints, observed top results, and failure classification

#### Scenario: machine-readable output is available
- **WHEN** a developer requests JSON output from search quality evaluation
- **THEN** the evaluator MUST emit the same metric values and failed-query details in machine-readable form

### Requirement: Real-database quality gates only clear regressions
Real-database search quality evaluation SHALL compare results with a baseline and fail only on clear regressions.

#### Scenario: first run can establish a baseline
- **WHEN** real-database evaluation runs without an existing baseline
- **THEN** it MUST be able to write a baseline artifact
- **AND** it MUST report that no regression comparison was performed

#### Scenario: significant metric regression fails the gate
- **WHEN** real-database evaluation runs with an existing baseline
- **AND** `hit@5` drops by more than the configured percentage-point threshold or `MRR@5` drops by more than the configured relative threshold
- **THEN** the evaluation command MUST fail
- **AND** it MUST report the baseline value, current value, and threshold that triggered failure

#### Scenario: non-gating queries are report-only
- **WHEN** a golden query is marked report-only or newly introduced outside the gating baseline
- **THEN** its result MUST appear in the report
- **AND** its failure MUST NOT cause the regression gate to fail

### Requirement: Evaluation identifies likely failure modes
Search quality evaluation SHALL classify failed queries into actionable failure modes for future search improvements.

#### Scenario: missing expected result is classified
- **WHEN** no observed result satisfies a golden query expectation within the evaluated result window
- **THEN** the failure MUST be classified as missing recall

#### Scenario: expected result ranks too low is classified
- **WHEN** an observed result satisfies the expectation but appears below the required top-K rank
- **THEN** the failure MUST be classified as low ranking

#### Scenario: filter-sensitive failures are classified
- **WHEN** a query expectation includes addon or doc type constraints and observed results violate those constraints
- **THEN** the failure MUST be classified as a filter mismatch

#### Scenario: graph expansion impact can be isolated
- **WHEN** evaluation compares graph expansion enabled and disabled modes
- **THEN** the report MUST identify queries whose pass or fail status changes between those modes
