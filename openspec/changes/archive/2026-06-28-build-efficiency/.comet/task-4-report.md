# Task 4: Local Build Orchestration — Report

## Status: DONE

## What Was Done

Created `godot_rag_build/orchestrator.py` — the main build orchestrator that ports the `build.sh` release flow into Python with caching support.

### Files Created
- `godot_rag_build/orchestrator.py` (323 lines)
- `rst2md/tests/test_build_release_orchestrator.py` (63 lines)

### TDD Process
1. Wrote 3 failing tests in `test_build_release_orchestrator.py`
2. Verified tests failed with `ModuleNotFoundError` (orchestrator didn't exist)
3. Implemented orchestrator to pass all tests
4. Verified: 3/3 new tests pass, 14/14 existing tests still pass

### Implementation Summary

**Public API:**
- `BuildOptions` — frozen dataclass with `no_bump`, `with_wiki`, `cache_dir`, `root`, `runner`
- `resolve_godot_version(root)` — extracts version from `godot-docs/conf.py`
- `resolve_package_version(root, godot_version, no_bump)` — reads/bumps `.postN` suffix in `pyproject.toml`
- `assemble_package_tree(root)` — copies `rst2md/rag/*.py` to `godot_rag/rag/`, rewriting imports
- `create_build_stages(options)` — returns 11 ordered `StageSpec`s
- `run_build(options)` — orchestrates all stages, returns `BuildReport`
- `run_release_diagnostics(db_path)` — standalone diagnostics runner

**Stage pipeline (11 stages, strict dependency ordering):**
1. `submodule` — git submodule update
2. `version` — resolve Godot + package version, bump if needed
3. `docs-md` — rst2md batch conversion (cacheable)
4. `wiki` — clone Scene Manager wiki, clean `.git` (cacheable)
5. `rag-db` — build RAG database (cacheable)
6. `diagnostics` — run rag.cli diagnostics + git-ignore check
7. `cleanup-wiki` — remove transient wiki copy
8. `package-tree` — assemble package with import rewriting (cacheable)
9. `readme` — merge readme (cacheable)
10. `wheel` — build wheel
11. `twine-check` — validate wheel

**Key behaviors:**
- `_rewrite_imports` replaces `from rag.` → `from godot_rag.rag.` and `import rag.` → `import godot_rag.rag.`
- Wiki stage cleans `.git` directory from copied wiki
- `resolve_package_version` modifies `pyproject.toml` when bumping
- Fingerprinting includes `with_wiki` flag, `pyproject.toml`, `uv.lock`, build tool tree, `build.sh`

## Commits

- `507ff98` — `feat: port local release build orchestration`

## Test Summary

3 passed, 0 failed (17 total including existing tests)
