---
comet_change: deepen-rag-modules
role: technical-design
canonical_spec: openspec
archived-with: 2026-06-28-deepen-rag-modules
status: final
---

# Deepen RAG Modules Technical Design

## Context

The `godot-rag` runtime has accumulated several broad modules:

- `rst2md/rag/store.py` owns database connection setup, schema constants, database build, symbol insertion, relation construction, vector search, FTS search, result fusion, graph expansion, stats, and public search facades.
- `rst2md/rag/addon_docs.py` owns addon layout discovery, file collection, markdown chunking, example chunking, public API declaration extraction, and final addon chunk orchestration.
- `rst2md/rag/cli.py` repeats the same search orchestration across multiple subcommands.

This change is an internal architecture refactor. It must preserve existing public imports, CLI commands, output shape, search scoring behavior, vector fallback metadata, graph expansion behavior, database schema semantics, and addon chunk semantics.

## Technical Approach

Keep `rag.store` as the compatibility facade. Existing callers continue importing `build_database`, `search_database`, `search_database_with_metadata`, `get_stats`, `list_addons`, `get_connection`, and `clean_chunk_text` from `rag.store`.

Move implementation details behind focused modules:

- `rst2md/rag/db.py`: SQLite connection setup, schema constants, vector table schema, FTS sync SQL, text cleanup helpers.
- `rst2md/rag/relations.py`: class inheritance extraction and chunk relation construction.
- `rst2md/rag/indexer.py`: database build workflow, document insertion, addon insertion, symbol insertion, FTS sync, and embedding storage.
- `rst2md/rag/searcher.py`: vector availability checks, vector search, FTS search, RRF fusion, graph expansion, snippet extraction, metadata construction, and result mapping.
- `rst2md/rag/addon_discovery.py`: `AddonLayout`, addon exclusion rules, plugin root discovery, plugin display-name discovery, and doc/example/API file collection.

Keep `rst2md/rag/addon_docs.py` focused on chunk production:

- markdown section chunking
- code example chunking
- public API declaration chunking
- `chunk_addon(addon_dir)` orchestration using `addon_discovery`

Consolidate CLI search orchestration in `rst2md/rag/cli.py`:

- add a shared database guard for commands that read the database
- add a shared search runner for debug metadata, JSON/text output, graph expansion, doc-type filters, and addon filters
- keep parser commands and aliases unchanged

## Data Flow

Database build:

```text
build_database()
  -> indexer.build_database()
     -> db.get_connection()
     -> chunker.chunk_markdown()
     -> addon_docs.chunk_addon()
        -> addon_discovery.discover_addon()
        -> addon_discovery.collect_*_files()
     -> symbols.extract_symbols()
     -> relations.build_chunk_relations()
     -> embeddings.generate_embeddings()
     -> db.FTS_SYNC
```

Search:

```text
search_database*()
  -> searcher.search_database*()
     -> db.get_connection()
     -> searcher._vector_availability()
     -> embeddings.generate_embeddings() only when vectors are available
     -> FTS and symbol queries
     -> searcher.rrf_fusion()
     -> graph expansion through chunk_relations
     -> SearchResult / SearchResponse
```

CLI:

```text
cmd_search*()
  -> _run_search(args, doc_types=..., addon=...)
     -> _require_db(args)
     -> search_database() or search_database_with_metadata()
     -> _print_results()
```

## Trade-offs

Keeping `rag.store` as a facade means there will be one extra delegation layer. That is intentional: it preserves compatibility and reduces migration risk.

Splitting into several modules increases file count, but each new module maps to an existing responsibility already present in the code. The split is not speculative; it improves locality around indexing, searching, relation construction, addon discovery, and CLI search orchestration.

The first pass will not extract every possible helper. For example, public API declaration extraction can remain in `addon_docs.py` because the highest-value split is separating discovery/file collection from chunk production.

## Risks and Mitigations

- Behavior drift during mechanical moves -> move one responsibility at a time and run focused tests after each slice.
- Import cycles -> keep shared primitives in `db.py`; keep `store.py` thin; avoid importing `store.py` from new internal modules.
- Over-abstraction -> only introduce modules that match current responsibilities; avoid new classes unless they remove real complexity.
- Optional vector dependency behavior drift -> keep current lazy imports and broad fallback behavior unchanged while moving code.

## Testing Strategy

Baseline:

```bash
rtk uv run pytest rst2md/tests/test_rag_search.py rst2md/tests/test_rag_addon.py
```

After the store split:

```bash
rtk uv run pytest rst2md/tests/test_rag_search.py rst2md/tests/test_semantic_search.py
```

After the addon discovery split:

```bash
rtk uv run pytest rst2md/tests/test_rag_addon.py
```

After CLI consolidation:

```bash
rtk uv run pytest rst2md/tests/test_rag_search.py rst2md/tests/test_rag_addon.py rst2md/tests/test_build_release_cli.py
```

Final verification:

```bash
rtk uv run pytest rst2md/tests/test_rag_search.py rst2md/tests/test_rag_addon.py rst2md/tests/test_semantic_search.py rst2md/tests/test_build_release_cli.py
rtk openspec validate deepen-rag-modules
```

## Spec Patches

No OpenSpec delta spec patches are needed beyond the already-created `rag-module-architecture` internal architecture contract.
