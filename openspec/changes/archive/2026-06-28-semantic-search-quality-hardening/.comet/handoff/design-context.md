# Comet Design Handoff

- Change: semantic-search-quality-hardening
- Phase: design
- Mode: compact
- Context hash: 3f2cc89063b9348049b4f65741d83f04eaa8c3e4bdf3783e55efe04d5a644527

Generated-by: comet-handoff.sh

OpenSpec remains the canonical capability spec. This handoff is a deterministic, source-traceable context pack, not an agent-authored summary.

## openspec/changes/semantic-search-quality-hardening/proposal.md

- Source: openspec/changes/semantic-search-quality-hardening/proposal.md
- Lines: 1-27
- SHA256: 6fe2bc847c5788630b84e7f32282266b08f5754f392e3d916808a16be618e8e9

```md
## Why

`semantic-search` is implemented, but its completion quality still depends on manual checks and generated local artifacts. The next change makes semantic search release-ready by turning quality, performance, generated database, and fallback behavior into explicit gates.

## What Changes

- Add semantic-search quality requirements for release database generation, relevance evaluation, model performance, and fallback observability.
- Add automated validation that the CLI default database contains vector embeddings when semantic search is expected to ship.
- Add golden-query relevance checks so semantic search is judged by result quality, not only by table existence.
- Add model reuse/performance guardrails for interactive search.
- Add observable fallback behavior when vector search is unavailable.

## Capabilities

### New Capabilities

- `semantic-search-quality`: Quality gates and release-readiness requirements for semantic search.

### Modified Capabilities

- None.

## Impact

- Affected code: `rst2md/rag/store.py`, `rst2md/rag/embeddings.py`, `rst2md/rag/cli.py`, tests under `rst2md/tests/`, and release/build helper scripts if needed.
- Affected generated artifacts: ignored default package database under `godot_rag/rag/godot_docs.sqlite`.
- Affected workflows: local release asset generation, semantic-search verification, and CI or pre-release checks.
```

## openspec/changes/semantic-search-quality-hardening/design.md

- Source: openspec/changes/semantic-search-quality-hardening/design.md
- Lines: 1-52
- SHA256: a08328593690a0902d86c50fc74777f11e5690351518f8791942fd50eaa70bd4

```md
## Context

The previous `semantic-search` change added vector storage, query embeddings, and RRF fusion. Review found that the code path could pass tests while the generated CLI default database lacked vectors, and that failures in the vector path were hard to observe. A small follow-up already prevents embedding generation when `vec_chunks` is missing and removes a generated root database from git tracking.

## Goals / Non-Goals

**Goals:**

- Make the default CLI database generation path explicit and verifiable.
- Add relevance-oriented tests with golden queries.
- Reuse the embedding model within a process and guard warm-query latency.
- Expose vector fallback state for diagnostics without noisy normal output.

**Non-Goals:**

- Change the embedding model.
- Redesign the full RAG ranking architecture.
- Change the generated `README_PYPI.md` strategy.
- Commit generated database binaries.

## Decisions

1. **Use a release asset validation command rather than committed DB files.**
   Generated DBs remain ignored. The workflow should validate row parity and table presence after generation so release readiness is reproducible without adding binaries to git.

2. **Use deterministic golden-query tests.**
   Relevance gates should assert expected path or symbol families within top-K results. This avoids brittle exact ranking while still detecting semantic-quality regressions.

3. **Cache the model in `rag.embeddings`.**
   A process-local cache keeps the public API small and avoids threading model state through every search call. Tests can monkeypatch the loader to verify reuse.

4. **Expose fallback through diagnostics/debug metadata.**
   Normal CLI output should stay clean, but tests and diagnostics need a way to detect whether vector search ran or FTS fallback was used.

## Risks / Trade-offs

- Golden queries can become brittle as the corpus changes -> prefer top-K family assertions and document the corpus fixture.
- Performance tests can be noisy -> use a warm-query threshold and avoid asserting cold-start latency.
- Diagnostics can leak into user output -> keep fallback visibility behind debug/status paths unless explicitly requested.
- Release generation can be slow -> separate fast fixture tests from full release validation.

## Migration Plan

1. Add fixture-level tests for model reuse, fallback observability, and golden-query behavior.
2. Add or update release asset generation/validation commands.
3. Wire generated DB validation into the documented verification flow.
4. Run full tests and a local release DB validation pass.

## Open Questions

- What warm-query latency threshold should be used for local CI on this machine?
- Should fallback visibility be a CLI flag, JSON metadata field, or separate diagnostics command?
```

## openspec/changes/semantic-search-quality-hardening/tasks.md

- Source: openspec/changes/semantic-search-quality-hardening/tasks.md
- Lines: 1-27
- SHA256: bc3cce52fd70d929d1f91f02c4727cc2f36dfcfb8921eb0cd07063b644ae82f0

```md
## 1. Relevance Gates

- [ ] 1.1 Define a small set of semantic-search golden queries with expected top-K path or symbol families.
- [ ] 1.2 Add deterministic relevance tests that do not depend on untracked local-only database state.

## 2. Release Database Validation

- [ ] 2.1 Add or update the release database generation flow for the CLI default database path.
- [ ] 2.2 Add validation that `vec_chunks` exists and has the same row count as `chunks`.
- [ ] 2.3 Verify generated database files remain ignored and are not committed.

## 3. Model Reuse And Performance

- [ ] 3.1 Cache the model2vec model inside the embedding layer.
- [ ] 3.2 Add a test proving repeated searches load the model at most once per process.
- [ ] 3.3 Add a warm-query latency guard with a documented threshold.

## 4. Fallback Observability

- [ ] 4.1 Add a debug or diagnostics path that reports vector search availability and fallback reason.
- [ ] 4.2 Add tests for missing table, missing extension, and vector query failure fallback behavior.

## 5. Verification

- [ ] 5.1 Run the focused semantic-search test suite.
- [ ] 5.2 Run the full test suite.
- [ ] 5.3 Run the release database validation flow and record the result.
```

## openspec/changes/semantic-search-quality-hardening/specs/semantic-search-quality/spec.md

- Source: openspec/changes/semantic-search-quality-hardening/specs/semantic-search-quality/spec.md
- Lines: 1-55
- SHA256: 768d894fb7e3d01ff6d2c901f4165e68770a95964d221c6e4d7a48c3146c9e43

```md
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
```

