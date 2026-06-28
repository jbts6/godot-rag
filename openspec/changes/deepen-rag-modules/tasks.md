## 1. Baseline and Safety

- [x] 1.1 Run focused baseline tests for RAG search and addon chunking.
- [x] 1.2 Confirm public store imports and CLI search commands are covered by existing tests.

## 2. Deepen Store Internals

- [x] 2.1 Extract shared SQLite connection, schema constants, FTS sync, and text cleanup helpers from `store.py` into a focused database module while preserving `rag.store` imports.
- [x] 2.2 Extract chunk relation construction from `store.py` into a focused relation module and keep database build behavior unchanged.
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
