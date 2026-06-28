# Brainstorm Summary

- Change: deepen-rag-modules
- Date: 2026-06-28

## Confirmed Technical Approach

- Keep `rag.store` as the compatibility facade for existing imports.
- Extract shared database primitives into `rst2md/rag/db.py`.
- Extract relation building into `rst2md/rag/relations.py`.
- Extract database build/indexing into `rst2md/rag/indexer.py`.
- Extract search execution into `rst2md/rag/searcher.py`.
- Extract addon layout discovery and file collection into `rst2md/rag/addon_discovery.py`.
- Consolidate CLI search subcommands through a shared helper in `rst2md/rag/cli.py`.

## Key Trade-offs and Risks

- Mechanical moves can accidentally change behavior. Mitigation: move one responsibility at a time and run focused tests after each slice.
- Import cycles are possible after splitting `store.py`. Mitigation: keep shared primitives in `db.py` and keep `store.py` as a thin facade.
- Too much abstraction could make the code harder to navigate. Mitigation: only add modules matching current real responsibilities and keep public interfaces unchanged.

## Testing Strategy

- Establish baseline with `rst2md/tests/test_rag_search.py` and `rst2md/tests/test_rag_addon.py`.
- After store split, rerun focused RAG search tests.
- After addon discovery split, rerun addon tests.
- After CLI consolidation, rerun CLI/search tests.
- Final verification includes relevant RAG, addon, semantic-search, CLI tests and `openspec validate deepen-rag-modules`.

## Spec Patches

None currently proposed.
