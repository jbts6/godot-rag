# Godot RAG

Hybrid RAG search for Godot documentation. Search by type for precise results.

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

### Output format

```bash
# JSON output (for AI Agent)
godot-rag s-class "Vector3.normalized" --json

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

## Update

When Godot releases a new version:

```bash
# Update godot-docs submodule
cd godot-docs && git pull origin stable

# Rebuild docs and RAG
./build.sh

# Or manually:
uv run python3 rst2md/rst2md_batch.py -i godot-docs -o godot_rag/docs-md
uv run python3 rst2md/rag/cli.py build --docs godot_rag/docs-md --db godot_rag/rag/godot_docs.sqlite
uv run python3 -m build --wheel
```

## License

MIT
