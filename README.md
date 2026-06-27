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

### Search by type

```bash
# Search class reference (API docs only)
godot-rag s-class "Node.add_child"
godot-rag s-class "Signal.emit" --limit 3

# Search tutorials (tutorials + getting started guides)
godot-rag s-tutorial "how to use signals"
godot-rag s-tutorial "2D pathfinding" --limit 5

# Search engine details (architecture, file formats, GDExtension, etc.)
godot-rag s-engine "GDExtension"
godot-rag s-engine "IDE debugging" --limit 3

# Search addon docs and examples
godot-rag s-addon "state machine"
godot-rag s-addon "state machine" --addon statecharts
godot-rag s-addon "dialogue" --limit 3

# Search all docs (no type filter)
godot-rag s "Timer"
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

### Output format

```bash
# JSON output (for AI Agent)
godot-rag s-class "Vector3.normalized" --json
godot-rag s-addon "change_scene" --addon scene_manager --json

# Limit results
godot-rag s-tutorial "C# Variant" --limit 3
```

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

A hybrid RAG system (FTS5 + symbol index) gives significantly better results than raw text search for AI-assisted documentation lookup.

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
./build.sh

# Or manually:
PYTHONPATH=rst2md uv run python3 rst2md/rst2md_batch.py -i godot-docs -o godot_rag/docs-md
PYTHONPATH=rst2md uv run python3 -m rag.cli build --docs godot_rag/docs-md --db godot_rag/rag/godot_docs.sqlite --addons addons
uv build --wheel
```

## Development

```bash
uv run pytest -q
```

## License

MIT
