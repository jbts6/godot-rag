## Why

Local release builds are convenient but still repeat expensive work across docs conversion, RAG database generation, diagnostics, package assembly, and wheel creation. A conservative Python build orchestrator can reduce unnecessary rebuild time while making every stage's cost and cache decision visible.

## What Changes

- Add a Python-based release build tool exposed as the project script `godot-rag-build`.
- Replace the main `build.sh` implementation with a thin wrapper around the new Python entrypoint.
- Introduce conservative stage input fingerprints so unchanged build stages can be skipped safely.
- Record build cache state in `.cache/build-release/manifest.json`.
- Print a human-readable stage table and write `.cache/build-release/last-run.json` for each run.
- Cover local wheel builds, PyPI/TestPyPI publishing, release database diagnostics, cache cleanup, and the `--with-wiki` path.
- Keep publish safe by requiring a complete build, tests, diagnostics, version existence checks, and upload without a skip-tests bypass.

## Capabilities

### New Capabilities
- `build-release-efficiency`: Covers the Python release build orchestrator, conservative cache reuse, stage observability, publish safety, and wrapper compatibility.

### Modified Capabilities

## Impact

- Affected files: `build.sh`, `pyproject.toml`, a new Python build tool module/script, and tests for the build orchestration behavior.
- Affected local workflows: local release wheel builds, TestPyPI/PyPI publishing, release database diagnostics, cache cleanup, and optional Scene Manager wiki inclusion.
- Affected generated state: `.cache/build-release/manifest.json`, `.cache/build-release/last-run.json`, `godot_rag/`, and `dist/`.
- CI is not a primary optimization target, but existing workflow checks must remain valid or receive minimal compatibility updates.
