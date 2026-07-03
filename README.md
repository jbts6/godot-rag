# Godot RAG

[中文版](README_zh.md)

Hybrid RAG search for Godot documentation and addons. Search by type for precise results.

## Installation

```bash
# As a global tool (recommended)
uv tool install godot-rag

# Or install into current environment
uv pip install godot-rag
```

### AI Agent Skill

Install the godot-rag skill for AI coding agents (Claude Code, opencode, Cursor, etc.):

```bash
npx skills add jbts6/skills --skill godot-rag
```

The skill instructs agents to always query godot-rag before writing Godot code, and includes HyDE-enhanced search for natural language queries.

## Usage

> **Language note**: Queries must be in English. For non-English queries, translate to English first (e.g., "怎么做二段跳" → "how to double jump"). The embedding model is English-only.

### Search by type

All search commands have long aliases: `search`, `search-class`, `search-tutorial`, `search-engine`, `search-addon`.

**Default behavior**: `s`, `s-class`, `s-tutorial`, `s-engine` exclude addon results. Use `s-addon` to search addons.

```bash
# Search class reference (API docs only)
godot-rag s-class "Node.add_child"
godot-rag s-class "Signal.emit" --limit 3

# class.method queries work — finds the class
godot-rag s-class "ResourceLoader.load"

# Tutorials + getting started guides
godot-rag s-tutorial "how to use signals"

# Engine details (architecture, file formats, GDExtension, etc.)
godot-rag s-engine "GDExtension"

# Addon docs and examples (must use s-addon)
godot-rag s-addon "state machine"
godot-rag s-addon "state machine" --addon statecharts

# Search all docs (no type filter, excludes addons)
godot-rag s "Timer"

# Fuzzy symbol matching (camelCase/snake_case/dotted all work)
godot-rag s-class "addChild"          # matches add_child, _add_child
godot-rag s-class "Node.add_child"    # matches Node._add_child

# Disable graph expansion (only return direct matches)
godot-rag s-class "add_child" --no-expand
```

### Search addons

```bash
# Search all addon docs, examples, and API summaries
godot-rag s-addon "state machine"

# Filter by specific addon
godot-rag s-addon "state" --addon statecharts
godot-rag s-addon "change_scene" --addon scene_manager

# JSON output for AI agents
godot-rag s-addon "state machine" --addon statecharts --json
```

### List addons

```bash
godot-rag addons
godot-rag addons --json
```

### Output format

```bash
# JSON output (for AI Agent)
godot-rag s-class "Vector3.normalized" --json

# Limit results
godot-rag s-tutorial "C# Variant" --limit 3

# Debug search metadata
godot-rag s-class "Node.add_child" --debug-search
```

## Update

When Godot releases a new version:

```bash
# Update godot-docs submodule
cd godot-docs && git pull origin stable

# Rebuild docs and RAG
uv run godot-rag-build build

# Build and publish to PyPI
uv run godot-rag-build publish --target pypi

# Build and publish to TestPyPI
uv run godot-rag-build publish --target testpypi
```

## Development

```bash
uv run pytest -q
```

## License

MIT
