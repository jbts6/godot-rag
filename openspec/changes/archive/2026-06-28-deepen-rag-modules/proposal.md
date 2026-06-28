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
