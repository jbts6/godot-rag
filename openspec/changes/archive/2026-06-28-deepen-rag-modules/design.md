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
- class: `["class"]`
- tutorial: `["tutorial", "getting_started"]`
- engine: `["engine_detail"]`
- addon: `["addon"]` and optional addon filter

Alternative considered: introduce a command object or new CLI module. That would be more abstraction than the current CLI needs.

## Risks / Trade-offs

- Behavior drift during moves → Mitigation: use existing tests as a baseline, then run focused search/addon/CLI tests after each slice.
- Import cycles between new modules → Mitigation: keep shared database primitives in `db.py`; keep `store.py` as a thin facade; use local imports only where optional dependencies already require them.
- Test coupling to private helpers → Mitigation: prefer existing public-interface tests; add tests only for externally observable compatibility gaps.
- Large diff from mechanical moves → Mitigation: move one responsibility at a time and run focused tests after each move.

## Migration Plan

1. Establish current behavior with focused tests.
2. Extract shared database primitives and relation building.
3. Extract database indexing into `indexer.py`, then make `store.build_database` delegate to it.
4. Extract search execution into `searcher.py`, then make `store.search_database*` delegate to it.
5. Extract addon discovery into `addon_discovery.py`, then update `addon_docs.py` imports.
6. Consolidate CLI search command orchestration.
7. Run focused and full relevant tests.

Rollback is straightforward: since public interfaces are preserved, revert the refactor commits or move delegated code back into the original modules.

## Open Questions

None. The change scope is intentionally limited to internal refactoring with behavior preservation.
