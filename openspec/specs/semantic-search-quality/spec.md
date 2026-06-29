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
The packaged query suite SHALL contain at least 30 unique query IDs with at least 12 gating queries and at least 8 report-only queries, covering `class`, `symbol`, `tutorial`, `engine`, and `addon` categories.

#### Scenario: Query suite meets size and tier requirements
- **WHEN** `load_queries` loads the packaged query file
- **THEN** the result SHALL contain >= 30 queries with >= 12 gating and >= 8 report-only

#### Scenario: Query suite covers all required categories
- **WHEN** `load_queries` loads the packaged query file
- **THEN** the query categories SHALL include `class`, `symbol`, `tutorial`, `engine`, and `addon`

#### Scenario: Query suite includes normalization and graph tags
- **WHEN** `load_queries` loads the packaged query file
- **THEN** at least one query SHALL have tag `normalization` and at least one SHALL have tag `graph`

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

### Requirement: CLI entry point is importable
The `godot-rag` project script SHALL point to `rag.cli:main` and the wheel SHALL include `rst2md/rag` package.

#### Scenario: pyproject.toml has correct script target
- **WHEN** `pyproject.toml` is parsed
- **THEN** `[project.scripts]` SHALL contain `godot-rag = "rag.cli:main"`

#### Scenario: pyproject.toml includes rag package in wheel
- **WHEN** `pyproject.toml` is parsed
- **THEN** `[tool.hatch.build.targets.wheel]` `packages` SHALL include `"rst2md/rag"`

