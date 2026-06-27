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
