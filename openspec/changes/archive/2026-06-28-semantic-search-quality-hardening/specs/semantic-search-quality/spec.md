# semantic-search-quality Specification

## Purpose

Define the quality gates required for semantic search to be considered release-ready.

## ADDED Requirements

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
