# Godot RAG

Hybrid RAG search for Godot documentation. One command to search all Godot docs.

## Installation

### Using uv (recommended)

```bash
uv pip install godot-rag
```

Or from wheel:

```bash
uv pip install godot_rag-4.4.0-py3-none-any.whl
```

### Using pip

```bash
pip install godot-rag
```

## Usage

### Search documentation

```bash
# Basic search
godot-rag search "Timer"

# Limit results
godot-rag search "Timer" --limit 3

# JSON output (for AI Agent)
godot-rag search "StringName.is_valid_filename" --json
```

### Show info

```bash
godot-rag info
```

## Examples

```bash
# Search for API
godot-rag search "Vector3.normalized" --limit 3

# Search for concept
godot-rag search "2D pathfinding" --limit 5

# Search for tutorial
godot-rag search "C# Variant" --limit 3
```

## Update

When Godot releases a new version:

```bash
# Update godot-docs submodule
cd tools/godot-docs && git pull origin stable

# Rebuild docs and RAG
./build.sh

# Or manually:
python3 tools/godot-docs-rst2md/rst2md_batch.py --src tools/godot-docs --out godot_rag/docs-md
python3 tools/godot-docs-rst2md/rag/cli.py build --docs godot_rag/docs-md --db godot_rag/rag/godot_docs.sqlite
python3 -m build --wheel
```

## License

MIT
