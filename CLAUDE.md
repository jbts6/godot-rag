# Godot RAG

Hybrid RAG search for Godot documentation and addons. FTS5 + vector dual-recall with RRF fusion ranking.

## Directory Structure

- `rst2md/rag/` — **Source code** (edit here)
- `godot_rag/` — **Build output** (NEVER edit manually)
- `rst2md/tests/` — Tests
- `docs/` — Documentation and specs
- `openspec/` — OpenSpec change management
- `scripts/` — Utility scripts

**NEVER read `godot_rag/rag/*.py` — those are build artifacts. Source is in `rst2md/rag/`.**

## Build & Publish

```bash
./build.sh              # Build wheel
./build.sh --publish    # Build and publish to PyPI
```

`build.sh` copies `.py` files from `rst2md/rag/` to `godot_rag/rag/` and rewrites imports from `from rag.` to `from godot_rag.rag.`.

**Do NOT manually commit version bumps** — `build.sh` auto-increments versions. Manual commits cause version skips.

## Testing

```bash
uv run pytest -q                              # Full suite
uv run pytest -q rst2md/tests/test_search_eval.py  # Focused
```

Test config in `pyproject.toml`: `pythonpath = ["rst2md"]`, `testpaths = ["rst2md/tests"]`.

## Key Modules

| Module | Purpose |
|--------|---------|
| `searcher.py` | Hybrid search (FTS5 + vector + RRF fusion + graph expansion) |
| `search_eval.py` | Quality evaluation, latency metrics, diagnostics |
| `cli.py` | CLI interface (`godot-rag` command) |
| `indexer.py` | Database indexing |
| `models.py` | Data models (`SearchMetadata`, `SearchResponse`) |
| `query_plan.py` | Query planning and intent detection |
| `chunker.py` | Document chunking |

## Search Quality

Run deterministic evaluator tests:
```bash
uv run pytest -q rst2md/tests/test_search_eval.py rst2md/tests/test_search_eval_cli.py
```

Run real-database gate (when `godot_rag.db` available):
```bash
uv run godot-rag eval-search --db godot_rag.db --baseline docs/search-quality/baseline.json --compare-graph
```

## Workflow

This project uses OpenSpec + Comet for change management:
- `/comet` — Start or continue a change
- `/comet-open` — Open new change
- `/comet-design` — Design phase
- `/comet-build` — Build phase
- `/comet-verify` — Verify phase
- `/comet-archive` — Archive completed change

Changes are tracked in `openspec/changes/` and archived to `openspec/changes/archive/`.
