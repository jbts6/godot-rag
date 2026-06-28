# Comet Design Handoff

- Change: deepen-rag-modules
- Phase: design
- Mode: compact
- Context hash: 547f7acb69e73544a3499f58a6bb3476ee9f55fc60cf7a0d5790821313e25847

Generated-by: comet-handoff.sh

OpenSpec remains the canonical capability spec. This handoff is a deterministic, source-traceable context pack, not an agent-authored summary.

## openspec/changes/deepen-rag-modules/proposal.md

- Source: openspec/changes/deepen-rag-modules/proposal.md
- Lines: 1-38
- SHA256: 09d4eb251116e27b1665114267d31488fc521fdbfac81e2f8c36da7a84be6c25

```md
## Why

`rst2md/rag/store.py`, `rst2md/rag/addon_docs.py`, and `rst2md/rag/cli.py` have grown into broad modules whose interfaces expose or duplicate too much implementation knowledge. Search quality work, addon ingestion changes, and CLI option changes now require navigating unrelated concerns in the same files, which increases regression risk.

This change deepens the RAG modules while preserving current public behavior so future search and addon improvements have better locality and smaller test surfaces.

## What Changes

- Split internal database indexing concerns out of `store.py` while keeping existing public functions available from `rag.store`.
- Split search execution, result mapping, vector/FTS fallback, RRF fusion, and graph expansion concerns out of `store.py` while preserving current result ordering and metadata behavior.
- Move addon layout discovery and file collection concerns out of `addon_docs.py`, leaving addon chunk production behind the existing `chunk_addon()` interface.
- Consolidate duplicated search command handling in `cli.py` so database checks, debug metadata, JSON output, and graph-expansion options flow through one helper.
- Keep existing CLI commands, arguments, output shape, database schema semantics, and search scoring behavior unchanged.

## Capabilities

### New Capabilities

- `rag-module-architecture`: Internal architecture contract for keeping RAG database, addon chunking, and CLI behavior stable while moving implementation details behind deeper modules. This is not a new user-facing feature.

### Modified Capabilities

None. Existing search, addon chunking, CLI, semantic-search, and build-release requirements remain unchanged.

## Impact

- Affected code:
  - `rst2md/rag/store.py`
  - `rst2md/rag/addon_docs.py`
  - `rst2md/rag/cli.py`
  - New internal modules under `rst2md/rag/`
  - Existing tests under `rst2md/tests/`
- Public APIs:
  - Existing imports from `rag.store` remain valid.
  - Existing CLI entry point and subcommands remain valid.
- Dependencies:
  - No new runtime dependency.
  - No database schema behavior change.
```

## openspec/changes/deepen-rag-modules/design.md

- Source: openspec/changes/deepen-rag-modules/design.md
- Lines: 1-109
- SHA256: 762cf1877e15f419cfdd2201c019818bcc97d00a11724a4f20c45115cd297d4a

[TRUNCATED]

```md
## Context

The current RAG runtime has three broad modules that are doing too much:

- `rst2md/rag/store.py` contains SQLite connection setup, schema constants, database building, chunk insertion, symbol insertion, relation building, vector search, FTS search, RRF fusion, graph expansion, result mapping, stats, and public search facades.
- `rst2md/rag/addon_docs.py` contains addon layout discovery, file collection, markdown chunking, example chunking, public API declaration extraction, and final addon chunk orchestration.
- `rst2md/rag/cli.py` repeats the same search command flow across all search subcommands: resolve database path, check existence, handle `--no-expand`, decide debug metadata behavior, call search, and print results.

The change is a refactor. The public behavior described by existing tests and specs must remain unchanged.

## Goals / Non-Goals

**Goals:**

- Keep `rag.store` as the compatibility facade for existing public imports.
- Move database build implementation behind an indexing-focused module.
- Move search implementation behind a search-focused module.
- Move relation construction behind a relation-focused module.
- Move addon layout discovery and file collection behind an addon-discovery-focused module.
- Consolidate shared CLI search orchestration in one helper.
- Preserve current CLI commands, arguments, output shape, scoring behavior, fallback metadata, addon chunking semantics, and database schema semantics.

**Non-Goals:**

- No search quality changes.
- No CLI feature changes.
- No database schema behavior changes.
- No new runtime dependency.
- No release-build or package-tree restructuring.
- No changes to vendored addon or `godot-docs` sources.

## Decisions

### Decision 1: Keep `rag.store` as a compatibility facade

`rag.store` remains the public import surface. It will re-export or delegate the existing functions used by tests and callers:

- `get_connection`
- `clean_chunk_text`
- `build_database`
- `list_addons`
- `get_stats`
- `search_database`
- `search_database_with_metadata`

Alternative considered: move callers directly to new modules. That would create avoidable public churn and make this refactor look like a behavior change. The facade keeps the external interface stable while letting internal modules get deeper.

### Decision 2: Split `store.py` by runtime responsibility

Create focused internal modules under `rst2md/rag/`:

- `db.py`: SQLite connection setup, shared schema constants, FTS sync constants, text cleanup helpers.
- `relations.py`: `_extract_inherits` and `build_chunk_relations`.
- `indexer.py`: `build_database` and insertion helpers for docs, addons, symbols, FTS sync, and embeddings.
- `searcher.py`: vector availability, vector query, FTS query, RRF fusion, graph expansion, snippet extraction, `search_database`, and `search_database_with_metadata`.

Alternative considered: split only `searcher.py` out first. That reduces immediate diff size but leaves indexing and relation complexity mixed into the facade, so future work would still cross unrelated concerns.

### Decision 3: Separate addon discovery from addon chunk production

Create `rst2md/rag/addon_discovery.py` containing:

- `AddonLayout`
- discovery constants
- path exclusion logic
- plugin root/name detection
- `discover_addon`
- `collect_doc_files`
- `collect_example_files`
- `collect_api_files`

Keep `addon_docs.py` responsible for turning already-discovered files and content into `Chunk` instances. This preserves `chunk_addon(addon_dir)` as the public interface.

Alternative considered: split API extraction into a third module at the same time. That can be done later, but the highest-value locality issue is the discovery/file collection code being interleaved with chunk production.

### Decision 4: Consolidate CLI search orchestration without changing parser behavior

Add a shared helper in `cli.py`, tentatively `_run_search(args, *, doc_types=None, addon=None)`, plus a small database guard helper. Each search command becomes a thin wrapper that passes the right filters:

- all docs: no filter
```

Full source: openspec/changes/deepen-rag-modules/design.md

## openspec/changes/deepen-rag-modules/tasks.md

- Source: openspec/changes/deepen-rag-modules/tasks.md
- Lines: 1-31
- SHA256: 04a17c223a6b72a95e1182654049dfd435b063a19cabfa36cea95c33a4d489d7

```md
## 1. Baseline and Safety

- [ ] 1.1 Run focused baseline tests for RAG search and addon chunking.
- [ ] 1.2 Confirm public store imports and CLI search commands are covered by existing tests.

## 2. Deepen Store Internals

- [ ] 2.1 Extract shared SQLite connection, schema constants, FTS sync, and text cleanup helpers from `store.py` into a focused database module while preserving `rag.store` imports.
- [ ] 2.2 Extract chunk relation construction from `store.py` into a focused relation module and keep database build behavior unchanged.
- [ ] 2.3 Extract database indexing/build logic from `store.py` into an indexing module and delegate `rag.store.build_database` to it.
- [ ] 2.4 Extract search execution, vector fallback, FTS fallback, RRF fusion, graph expansion, snippet extraction, and result mapping from `store.py` into a search module and delegate `rag.store.search_database*` to it.
- [ ] 2.5 Run focused search tests after the store split.

## 3. Deepen Addon Discovery

- [ ] 3.1 Extract `AddonLayout`, addon path filtering, plugin discovery, and file collection helpers from `addon_docs.py` into `addon_discovery.py`.
- [ ] 3.2 Update `addon_docs.py` to use the discovery module while keeping `chunk_addon` and chunk output semantics unchanged.
- [ ] 3.3 Run focused addon chunking tests after the addon discovery split.

## 4. Consolidate CLI Search Orchestration

- [ ] 4.1 Add a shared CLI database guard for commands that read the RAG database.
- [ ] 4.2 Add a shared CLI search runner for all search subcommands, including debug metadata, JSON/text output, graph expansion, doc type filtering, and addon filtering.
- [ ] 4.3 Replace duplicated search command bodies with thin wrappers that pass the appropriate filters.
- [ ] 4.4 Run focused CLI/search tests after CLI consolidation.

## 5. Final Verification

- [ ] 5.1 Run the relevant RAG, addon, semantic-search, and CLI test suites.
- [ ] 5.2 Run OpenSpec validation for `deepen-rag-modules`.
- [ ] 5.3 Review the diff to ensure there are no public behavior changes, unrelated rewrites, generated database artifacts, or vendored source edits.
```

## openspec/changes/deepen-rag-modules/specs/rag-module-architecture/spec.md

- Source: openspec/changes/deepen-rag-modules/specs/rag-module-architecture/spec.md
- Lines: 1-37
- SHA256: a4c92041452280be65f9096dbab0de5836afde1f560a6b0aed307bbe7623ffd2

```md
## ADDED Requirements

### Requirement: Public RAG interfaces remain stable during module deepening
The system SHALL preserve existing public search, database build, addon chunking, and CLI behavior while internal RAG implementation responsibilities are moved behind deeper modules.

#### Scenario: Existing store imports continue to work
- **WHEN** callers import and use `build_database`, `search_database`, `search_database_with_metadata`, `get_stats`, or `list_addons` from `rag.store`
- **THEN** those imports MUST remain valid
- **AND** the observable behavior of those functions MUST remain compatible with the behavior before this change

#### Scenario: Existing search CLI commands keep their behavior
- **WHEN** a user invokes `godot-rag s`, `godot-rag search`, `godot-rag s-class`, `godot-rag s-tutorial`, `godot-rag s-engine`, or `godot-rag s-addon` with existing supported options
- **THEN** the command MUST accept the same arguments
- **AND** it MUST produce the same text or JSON output shape for equivalent database contents

#### Scenario: Addon chunking keeps existing output semantics
- **WHEN** addon documentation, examples, and public declarations are chunked through `chunk_addon`
- **THEN** the generated chunk paths, document types, chunk types, addon identifiers, symbols, headings, breadcrumbs, line spans, and text semantics MUST remain compatible with the behavior before this change

### Requirement: Internal responsibilities are localized behind focused RAG modules
The implementation SHALL separate indexing, search execution, relation building, addon discovery, and CLI search command orchestration so each responsibility can be tested or changed without editing unrelated responsibilities in place.

#### Scenario: Database indexing is localized
- **WHEN** database build behavior changes in the future
- **THEN** schema initialization, document insertion, addon insertion, symbol insertion, FTS sync, and embedding storage concerns MUST live behind an indexing-focused module interface rather than directly inside the public `rag.store` facade

#### Scenario: Search execution is localized
- **WHEN** search ranking, vector fallback, FTS fallback, result mapping, or graph expansion behavior changes in the future
- **THEN** those concerns MUST live behind a search-focused module interface rather than directly inside the public `rag.store` facade

#### Scenario: Addon discovery is localized
- **WHEN** addon documentation layout rules or file collection rules change in the future
- **THEN** those concerns MUST live behind an addon-discovery-focused module interface rather than inside addon chunk production code

#### Scenario: CLI search orchestration is localized
- **WHEN** shared search command behavior changes in the future
- **THEN** database validation, graph expansion option handling, debug metadata routing, and output formatting MUST be centralized instead of duplicated across each search subcommand
```

