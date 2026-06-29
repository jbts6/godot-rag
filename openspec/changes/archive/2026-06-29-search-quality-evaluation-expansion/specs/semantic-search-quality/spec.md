## MODIFIED Requirements

### Requirement: Search quality is evaluated with categorized golden queries
The packaged query suite SHALL contain at least 40 unique query IDs with at least 25 gating queries and at least 10 report-only queries, covering `class`, `symbol`, `tutorial`, `engine`, and `addon` categories. Gating metrics SHALL report empty or missing category coverage explicitly instead of allowing a required category to disappear silently. The suite SHALL include stable checks for symbol format variants, natural-language alias intent, graph expansion behavior, and addon/doc-type filter precision.

#### Scenario: Query suite meets expanded size and tier requirements
- **WHEN** `load_queries` loads the packaged query file
- **THEN** the result SHALL contain >= 40 queries with >= 25 gating and >= 10 report-only

#### Scenario: Query suite covers all required categories
- **WHEN** `load_queries` loads the packaged query file
- **THEN** the query categories SHALL include `class`, `symbol`, `tutorial`, `engine`, and `addon`

#### Scenario: Query suite includes normalization and graph tags
- **WHEN** `load_queries` loads the packaged query file
- **THEN** at least one query SHALL have tag `normalization` and at least one SHALL have tag `graph`

#### Scenario: Query suite includes filter precision checks
- **WHEN** `load_queries` loads the packaged query file
- **THEN** at least one gating query SHALL validate addon or doc-type filter precision

#### Scenario: Required gating category disappears
- **WHEN** real-database evaluation computes gating metrics
- **AND** a required category has zero gating queries
- **THEN** the report MUST include an explicit category coverage warning

### Requirement: Search quality metrics are reported consistently
Search quality evaluation SHALL report ranking and performance metrics in a stable shape suitable for humans and regression checks.

#### Scenario: metrics are calculated overall and by category
- **WHEN** search quality evaluation completes
- **THEN** it MUST report `hit@1`, `hit@3`, `hit@5`, and `MRR@5`
- **AND** it MUST report those metrics overall and grouped by query category

#### Scenario: latency metrics are reported for evaluated queries
- **WHEN** search quality evaluation completes
- **THEN** it MUST report query latency summary metrics including p50 and p95
- **AND** latency metrics MUST be available in machine-readable JSON output

#### Scenario: failed queries include diagnostic detail
- **WHEN** a golden query fails its top-K expectation
- **THEN** the report MUST include the query, category, expected constraints, observed top results, and failure classification

#### Scenario: machine-readable output is available
- **WHEN** a developer requests JSON output from search quality evaluation
- **THEN** the evaluator MUST emit the same metric values, performance metrics, and failed-query details in machine-readable form

### Requirement: Real-database quality gates only clear regressions
Real-database search quality evaluation SHALL compare results with a baseline and fail only on clear regressions, including clear quality regressions and configured stability regressions.

#### Scenario: first run can establish a baseline
- **WHEN** real-database evaluation runs without an existing baseline
- **THEN** it MUST be able to write a baseline artifact
- **AND** it MUST report that no regression comparison was performed

#### Scenario: significant metric regression fails the gate
- **WHEN** real-database evaluation runs with an existing baseline
- **AND** `hit@5` drops by more than the configured percentage-point threshold or `MRR@5` drops by more than the configured relative threshold
- **THEN** the evaluation command MUST fail
- **AND** it MUST report the baseline value, current value, and threshold that triggered failure

#### Scenario: significant latency regression is visible
- **WHEN** real-database evaluation runs with an existing baseline containing latency metrics
- **AND** current p95 latency exceeds the configured threshold
- **THEN** the evaluation report MUST identify the latency regression

#### Scenario: non-gating queries are report-only
- **WHEN** a golden query is marked report-only or newly introduced outside the gating baseline
- **THEN** its result MUST appear in the report
- **AND** its failure MUST NOT cause the regression gate to fail

## ADDED Requirements

### Requirement: Search quality verification is part of routine validation
The project SHALL provide a documented routine command or script path that runs the deterministic search quality checks and the real-database evaluation gate when the release database is available.

#### Scenario: routine validation includes deterministic quality tests
- **WHEN** a developer runs the documented routine validation path
- **THEN** deterministic search quality tests MUST be included

#### Scenario: real database gate is documented
- **WHEN** a release database is available locally
- **THEN** the documented validation path MUST explain how to run the real-database search quality gate with baseline comparison
