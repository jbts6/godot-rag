# Task 6 Report: Thin Wrapper And Usage Documentation

## Status: DONE

## Commit

- `14770ce` feat: delegate build script to Python tool

## What Changed

- **`build.sh`** (275 → 42 lines): Replaced all inline build logic (submodule update, RST conversion, RAG build, wheel assembly, PyPI upload) with a thin argument-parsing wrapper that delegates to `uv run godot-rag-build`. Added `GODOT_RAG_BUILD_WRAPPER_DRY_RUN=1` env var for test-only dry-run mode.
- **`README.md`**: Updated "Update" section to show `uv run godot-rag-build build` as primary entry, kept `./build.sh` as legacy.
- **`README_zh.md`**: Same update in Chinese.
- **`rst2md/tests/test_build_release_wrapper.py`** (new): 5 tests covering syntax validity, default delegation, flag preservation, and publish target mapping.

## Test Results

- 10/10 passed (`test_build_release_wrapper.py` + `test_build_release_cli.py`)
- `bash -n build.sh` syntax check: clean

## Verification

- `build.sh` contains zero inline build logic (docs conversion, RAG build, package assembly, upload)
- `GODOT_RAG_BUILD_WRAPPER_DRY_RUN=1` prints delegated command without executing
- `README.md` and `README_zh.md` both show `uv run godot-rag-build build` as primary entry
- Legacy `./build.sh` flags map correctly: `--no-bump`, `--with-wiki`, `--publish` → pypi, `--test-pypi` → testpypi

## Concerns

None.
