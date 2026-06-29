# Agents Guide

## Project Overview

Godot RAG is a hybrid RAG (Retrieval-Augmented Generation) search system for Godot Engine documentation and addons. It uses FTS5 + vector dual-recall with RRF (Reciprocal Rank Fusion) ranking.

## Architecture

### Core Components

- **Searcher** (`rst2md/rag/searcher.py`): Hybrid search engine with FTS5, vector search, RRF fusion, and graph expansion
- **Indexer** (`rst2md/rag/indexer.py`): Database indexing for documents and embeddings
- **CLI** (`rst2md/rag/cli.py`): Command-line interface (`godot-rag` command)
- **Query Planner** (`rst2md/rag/query_plan.py`): Intent detection and query routing
- **Search Evaluator** (`rst2md/rag/search_eval.py`): Quality metrics, latency measurement, diagnostics

### Data Flow

1. Documents indexed via `indexer.py` into SQLite with FTS5 + vector embeddings
2. Queries processed by `query_plan.py` for intent detection
3. `searcher.py` performs hybrid search with FTS5 + vector + RRF fusion
4. Graph expansion adds related documents
5. Results ranked and returned

## Directory Layout

```
rst2md/rag/           # Source code (edit here)
  ├── cli.py          # CLI entry point
  ├── searcher.py     # Hybrid search engine
  ├── search_eval.py  # Quality evaluation
  ├── indexer.py      # Database indexing
  ├── models.py       # Data models
  └── ...

rst2md/tests/         # Test suite
  ├── test_rag_search.py
  ├── test_search_eval.py
  └── ...

godot_rag/            # Build output (NEVER edit)
docs/                 # Documentation
openspec/             # Change management
```

## Code Intelligence

This project uses **CodeGraph** for code navigation and understanding. The `.codegraph/` directory contains a pre-built SQLite knowledge graph of every symbol, edge, and file.

### When to Use CodeGraph

**Always use CodeGraph BEFORE grep or reading files** for code questions:
- "How does X work?" → `codegraph_explore("X")`
- "Where is X defined?" → `codegraph_explore("X")`
- "What calls X?" → `codegraph_explore("X")`
- "What does X affect?" → `codegraph_explore("X")`

### How to Query

```bash
# Via MCP tool (preferred in agent environments)
codegraph_explore("search_database hybrid search")

# Via shell
codegraph explore "search_database hybrid search"
```

### What CodeGraph Returns

- Verbatim, line-numbered source code grouped by file
- Call paths between symbols (including dynamic dispatch)
- Blast radius summary of what depends on them

### Advantages Over Grep

- Follows dynamic dispatch (callbacks, re-exports, polymorphism)
- Returns call paths, not just text matches
- One call replaces dozens of grep + read cycles
- More accurate than regex-based search

### Anti-Patterns

- **Don't grep first** — use CodeGraph, then grep only for specifics CodeGraph missed
- **Don't re-verify CodeGraph results** — they come from AST parsing
- **Don't read files separately** — CodeGraph returns verbatim source you can edit from

## Development

### Setup

```bash
uv sync                 # Install dependencies
uv run pytest -q        # Run tests
```

### Testing

```bash
# Full suite
uv run pytest -q

# Focused tests
uv run pytest -q rst2md/tests/test_search_eval.py
uv run pytest -q rst2md/tests/test_rag_search.py
```

### Build & Publish

```bash
./build.sh              # Build wheel
./build.sh --publish    # Build and publish to PyPI
```

**Important**: `build.sh` auto-increments versions. Do NOT manually commit version changes.

## Code Conventions

- Python 3.10+ with type hints
- Dataclasses for models (`SearchMetadata`, `SearchResponse`, etc.)
- pytest for testing with fixtures in `rst2md/tests/fixtures/`
- Source imports use `from rag.module import ...` (rewritten to `from godot_rag.rag.module` in build)

## Key Patterns

### Search Flow
```python
from rag.searcher import search_database
from rag.models import SearchResponse

response: SearchResponse = search_database(db_path, query, limit=10, expand_graph=True)
```

### Evaluation
```python
from rag.search_eval import evaluate_database, load_queries

queries = load_queries(Path("rst2md/rag/search_eval_queries.json"))
report = evaluate_database(db_path, queries, diagnostic_window=50)
```

## Change Management

This project uses OpenSpec + Comet for structured change management:

1. **Open** — Create change proposal and design
2. **Design** — Deep design with brainstorming
3. **Build** — Implement with TDD
4. **Verify** — Validate implementation
5. **Archive** — Merge specs and archive

See `openspec/changes/` for active changes and `openspec/changes/archive/` for completed ones.

## Common Tasks

### Add a new search feature
1. Modify `rst2md/rag/searcher.py`
2. Update models in `rst2md/rag/models.py` if needed
3. Add tests in `rst2md/tests/test_rag_search.py`
4. Run `uv run pytest -q` to verify

### Update search quality evaluation
1. Modify `rst2md/rag/search_eval.py`
2. Update queries in `rst2md/rag/search_eval_queries.json`
3. Add tests in `rst2md/tests/test_search_eval.py`
4. Run evaluator tests: `uv run pytest -q rst2md/tests/test_search_eval.py`

### Add CLI command
1. Add command in `rst2md/rag/cli.py`
2. Add tests in `rst2md/tests/`
3. Run `uv run pytest -q` to verify
