# semantic-search-quality Specification

## Purpose
TBD - created by archiving change semantic-search-quality-hardening. Update Purpose after archive.
## Requirements
### Requirement: Default CLI database includes semantic vectors
The release asset generation flow SHALL build the database used by the CLI default path with semantic vector data.

#### Scenario: generated default database contains matching vector rows
- **WHEN** the release database generation flow completes successfully
- **THEN** the default CLI database MUST contain a `vec_chunks` table
- **AND** the `vec_chunks` row count MUST equal the `chunks` row count

#### Scenario: generated databases remain ignored artifacts
- **WHEN** release database files are generated locally
- **THEN** generated SQLite or DB files MUST remain ignored by git
- **AND** the workflow MUST NOT require committing generated database binaries

### Requirement: Semantic relevance is evaluated with golden queries
Semantic search SHALL be verified against representative user queries with expected result constraints.

#### Scenario: golden query returns expected top result family
- **WHEN** a golden query such as a concept-oriented Godot search is executed
- **THEN** at least one expected document, symbol, or path family MUST appear within the configured top results

#### Scenario: relevance checks run without requiring committed generated DB files
- **WHEN** relevance tests run in CI or local verification
- **THEN** they MUST either build the required test database or use a small deterministic fixture database
- **AND** they MUST NOT depend on untracked local-only state

### Requirement: Query embedding model is reused
Semantic search SHALL avoid reloading the embedding model for each query in a long-lived process.

#### Scenario: repeated searches reuse the loaded model
- **WHEN** two semantic searches run in the same Python process
- **THEN** the embedding model MUST be loaded at most once

#### Scenario: query latency has a regression guard
- **WHEN** the semantic-search performance check runs on a fixture database
- **THEN** warm-query latency MUST stay below 1 second after the embedding model is already loaded

### Requirement: Vector fallback is observable and cheap
Semantic search SHALL make vector-path fallback explicit enough to diagnose and SHALL avoid unnecessary embedding work when vector search is unavailable.

#### Scenario: missing vector table avoids embedding generation
- **WHEN** a database does not contain a usable `vec_chunks` table
- **THEN** search MUST NOT generate a query embedding before falling back to FTS

#### Scenario: vector fallback can be observed
- **WHEN** vector search is unavailable due to missing table, missing extension, or query failure
- **THEN** JSON/debug search metadata MUST report that FTS fallback was used
- **AND** a diagnostics command MUST report the vector-search availability problem

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

### Requirement: CLI entry point is importable
The `godot-rag` project script SHALL point to `rag.cli:main` and the wheel SHALL include `rst2md/rag` package.

#### Scenario: pyproject.toml has correct script target
- **WHEN** `pyproject.toml` is parsed
- **THEN** `[project.scripts]` SHALL contain `godot-rag = "rag.cli:main"`

#### Scenario: pyproject.toml includes rag package in wheel
- **WHEN** `pyproject.toml` is parsed
- **THEN** `[tool.hatch.build.targets.wheel]` `packages` SHALL include `"rst2md/rag"`

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

### Requirement: Search quality verification is part of routine validation
The project SHALL provide a documented routine command or script path that runs the deterministic search quality checks and the real-database evaluation gate when the release database is available.

#### Scenario: routine validation includes deterministic quality tests
- **WHEN** a developer runs the documented routine validation path
- **THEN** deterministic search quality tests MUST be included

#### Scenario: real database gate is documented
- **WHEN** a release database is available locally
- **THEN** the documented validation path MUST explain how to run the real-database search quality gate with baseline comparison

