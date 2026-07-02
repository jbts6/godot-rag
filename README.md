# Godot RAG

[中文版](README_zh.md)

Hybrid RAG search for Godot documentation and addons. Search by type for precise results.

## Installation

```bash
uv pip install godot-rag
```

Or from wheel:

```bash
uv pip install godot_rag-4.7.0-py3-none-any.whl
```

## Usage

> **Language note**: Queries must be in English. For non-English queries, translate to English first (e.g., "怎么做二段跳" → "how to double jump"). The embedding model is English-only.

### Search by type

All search commands have long aliases: `search`, `search-class`, `search-tutorial`, `search-engine`, `search-addon`.

**Default behavior**: `s`, `s-class`, `s-tutorial`, `s-engine` exclude addon results. Use `s-addon` to search addons.

```bash
# Search class reference (API docs only, no addon results)
godot-rag s-class "Node.add_child"
godot-rag s-class "Signal.emit" --limit 3

# class.method queries work — finds the class
godot-rag s-class "ResourceLoader.load"    # finds ResourceLoader class
godot-rag s-class "Input.is_action_pressed" # finds Input class

# Tutorials + getting started guides
godot-rag s-tutorial "how to use signals"
godot-rag s-tutorial "2D pathfinding" --limit 5

# Engine details (architecture, file formats, GDExtension, etc.)
godot-rag s-engine "GDExtension"
godot-rag s-engine "IDE debugging" --limit 3

# Addon docs and examples (must use s-addon)
godot-rag s-addon "state machine"
godot-rag s-addon "state machine" --addon statecharts
godot-rag s-addon "dialogue" --limit 3

# Search all docs (no type filter, excludes addons)
godot-rag s "Timer"

# Fuzzy symbol matching (camelCase/snake_case/dotted all work)
godot-rag s-class "addChild"          # matches add_child, _add_child
godot-rag s-class "Node.add_child"    # matches Node._add_child
godot-rag s-class "node_add_child"    # matches Node.addChild

# Disable graph expansion (only return direct matches)
godot-rag s-class "add_child" --no-expand
```

### Search addons

```bash
# Search all addon docs, examples, and API summaries
godot-rag s-addon "state machine"
godot-rag s-addon "dialogue balloon"
godot-rag s-addon "scene transition"

# Filter by specific addon
godot-rag s-addon "state" --addon statecharts
godot-rag s-addon "change_scene" --addon scene_manager
godot-rag s-addon "test" --addon gdUnit4

# Find API symbols
godot-rag s-addon "SceneManager" --addon scene_manager
godot-rag s-addon "change_scene" --addon scene_manager
godot-rag s-addon "scene_loaded" --addon scene_manager
godot-rag s-addon "BehaviorTree" --addon limboai
godot-rag s-addon "DialogueManager" --addon dialogue_manager

# Search example code
godot-rag s-addon "ninja_frog" --addon statecharts
godot-rag s-addon "verify_node_path" --addon doctor

# JSON output for AI agents
godot-rag s-addon "state machine" --addon statecharts --json
godot-rag s-addon "change_scene" --json
```

### List addons

```bash
# List all indexed addons with chunk counts
godot-rag addons

# JSON output
godot-rag addons --json
```

### Output format

```bash
# JSON output (for AI Agent)
godot-rag s-class "Vector3.normalized" --json
godot-rag s-addon "change_scene" --addon scene_manager --json

# Limit results
godot-rag s-tutorial "C# Variant" --limit 3

# Debug search metadata (shows search mode, vector availability, fallback reason)
godot-rag s-class "Node.add_child" --debug-search
godot-rag s-class "Node.add_child" --debug-search --json
```

JSON output includes graph relation info:

```json
{
  "score": 100.0,
  "symbol": "Node.add_child",
  "relation_type": "",
  "distance": 0,
  ...
},
{
  "score": 50.0,
  "symbol": "Node",
  "relation_type": "parent",
  "distance": 1,
  ...
}
```

- `relation_type`: `""` (direct match), `"parent"`, `"inherits"`, `"references"`, `"see_also"`
- `distance`: `0` (direct), `1` (graph-expanded)

### Database statistics

```bash
# Show database statistics (chunk counts, symbols, relations)
godot-rag stats

# JSON output
godot-rag stats --json
```

### Diagnostics

```bash
# Validate semantic search readiness (vector embeddings, model availability)
godot-rag diagnostics

# JSON output
godot-rag diagnostics --json

# Skip model availability check
godot-rag diagnostics --no-model
```

## Search Quality Evaluation

Current metrics (44 queries, gating=38, report_only=6):

| Metric | Value |
|--------|-------|
| hit@1 | 86.8% |
| hit@3 | 97.4% |
| hit@5 | 100% |
| mrr@5 | 0.914 |
| Failures | 0 |

Run deterministic evaluator tests during development:

```bash
rtk uv run pytest -q rst2md/tests/test_search_eval.py rst2md/tests/test_search_eval_cli.py
```

Run the real-database gate when `godot_rag.db` is available:

```bash
rtk uv run godot-rag eval-search --db godot_rag.db --baseline docs/search-quality/baseline.json --compare-graph --diagnostic-limit 50
```

Reports include ranking metrics, failed-query diagnostics, and latency summaries.
Use `--p95-latency-threshold-ms` to fail on configured p95 latency regressions.

Write or refresh the reviewed baseline:

```bash
godot-rag eval-search \
  --db godot_rag/rag/godot_docs.sqlite \
  --baseline docs/search-quality/baseline.json \
  --write-baseline
```

Compare against the reviewed baseline:

```bash
godot-rag eval-search \
  --db godot_rag/rag/godot_docs.sqlite \
  --baseline docs/search-quality/baseline.json \
  --compare-graph \
  --diagnostic-limit 50
```

When `--diagnostic-limit` is set, failed queries include diagnostics showing whether expected targets exist in the database and where the best match appears inside the diagnostic window.

Use `--json` for machine-readable reports.

## Examples

```bash
# AI workflow: look up tutorial first, then API details
godot-rag s-tutorial "scene tree" --json
godot-rag s-class "Node.get_children" --json

# AI workflow: check addon docs and examples
godot-rag s-addon "state machine" --addon statecharts --json
godot-rag s-addon "dialogue balloon" --addon dialogue_manager --json

# Quick API lookup
godot-rag s-class "StringName.is_valid_filename"

# Broad search across all docs
godot-rag s "physics interpolation"
```

## RAG vs Non-RAG: Why It Matters

A hybrid RAG system (FTS5 + symbol index + vector semantic search) gives significantly better results than raw text search for AI-assisted documentation lookup. The system uses RRF (Reciprocal Rank Fusion) to combine lexical (FTS5) and semantic (vector) search results.

### Benchmark: Real Query Comparison

Tested on a database of **30,529 chunks** (28,231 Godot docs + 2,298 addon chunks across 9 addons).

| Metric | RAG (this tool) | grep (raw files) | Improvement |
|---|---|---|---|
| **Average latency** | 7.1 ms | 120 ms | **17× faster** |
| **Multi-word queries** | ✅ semantic ranking | ❌ exact match only | — |
| **API symbol lookup** | ✅ O(1) indexed | ❌ linear scan | — |
| **Result ranking** | ✅ BM25 relevance | ❌ no ranking | — |
| **Filters (addon/type)** | ✅ SQL WHERE | ❌ post-process | — |
| **Noise (test/assets)** | ✅ auto-excluded | ❌ manual filter | — |

### Query Hit Rate

| Query | RAG Results | grep Results | Notes |
|---|---|---|---|
| `change_scene` | ✅ 3 hits (12ms) | ✅ 13 files (152ms) | RAG: ranked, deduped |
| `SceneManager` | ✅ 3 hits (12ms) | ✅ 41 files (100ms) | grep: too many noise files |
| `SceneManager.change_scene` | ✅ 1 hit (12ms) | ❌ 0 files | **RAG: precise symbol hit** |
| `BehaviorTree` | ✅ 3 hits (12ms) | ✅ 2 files (96ms) | RAG: includes doc context |
| `DialogueManager` | ✅ 3 hits (13ms) | ✅ 26 files (98ms) | RAG: only relevant docs |
| `state machine transitions` | ✅ 3 hits (13ms) | ❌ 0 files | **grep fails on multi-word** |
| `scene transition animation` | ✅ 2 hits (11.9ms) | ❌ 0 files | **grep fails on multi-word** |
| `input helper gamepad` | ✅ 2 hits (12ms) | ❌ 0 files | **grep fails on multi-word** |
| `input action mapping` | ✅ 3 hits (11ms) | — | RAG finds cross-references |

**Key insight**: grep can only find exact substring matches. RAG handles natural language queries like "state machine transitions" and returns ranked, contextual results.

### Graph Expansion: Contextual Results

When graph expansion is enabled (default), search results are enriched with related chunks:

- **parent**: Searching `add_child` also returns the `Node` class summary
- **inherits**: Searching `Node` also returns `Object` (its parent class)
- **references**: Chunks that mention matched symbols in their text

```bash
# Graph expansion adds context
$ godot-rag s-class "add_child"
  score: 100.0  symbol: Node.add_child        # direct match
  score: 50.0   symbol: Node    relation: parent (distance=1)  # auto-expanded

# Disable for faster, minimal results
$ godot-rag s-class "add_child" --no-expand
  score: 100.0  symbol: Node.add_child        # direct match only
```

### --addon Filter: Precision Search

```bash
# Without filter: results from multiple addons
$ godot-rag s-addon "state machine"
  → statecharts (API), limboai (docs)    # mixed results

# With filter: only target addon
$ godot-rag s-addon "state machine" --addon statecharts
  → statecharts (API, docs, examples)    # precise
```

### Database Coverage

| Addon | Docs | Examples | API | Total |
|---|---|---|---|---|
| dialogue_manager | 140 | 2 | 55 | 197 |
| doctor | 34 | 125 | 41 | 200 |
| gdUnit4 | 1,030 | — | 214 | 1,244 |
| input_helper | 32 | 3 | 6 | 41 |
| limboai | 299 | 27 | — | 326 |
| phantom-camera | 12 | 11 | 38 | 61 |
| scene_manager | 1 | 2 | 5 | 8 |
| sound_manager | 13 | 2 | 7 | 22 |
| statecharts | 80 | 21 | 98 | 199 |
| **Total** | **1,641** | **193** | **464** | **2,298** |

- **addon_doc**: Documentation markdown/RST, split by headings
- **addon_example**: Example .gd/.cs code files
- **addon_api**: Public declarations and doc comments only (not full source)

## Update

When Godot releases a new version:

```bash
# Update godot-docs submodule
cd godot-docs && git pull origin stable

# Rebuild docs and RAG
uv run godot-rag-build build

# Include Scene Manager wiki docs
uv run godot-rag-build build --with-wiki

# Build and publish to PyPI
uv run godot-rag-build publish --target pypi

# Build and publish to TestPyPI
uv run godot-rag-build publish --target testpypi

# Release database diagnostics
uv run godot-rag-build diagnostics

# Clean build cache
uv run godot-rag-build clean-cache

# Legacy wrapper still works:
./build.sh
```

## Development

```bash
uv run pytest -q
```

## License

MIT
