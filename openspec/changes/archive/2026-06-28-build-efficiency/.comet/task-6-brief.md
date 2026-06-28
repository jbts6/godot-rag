# Task 6: Thin Wrapper And Usage Documentation

## Task Description

**Files:**
- Modify: `build.sh`
- Modify: `README.md`
- Modify: `README_zh.md`
- Test: `rst2md/tests/test_build_release_wrapper.py`

**Interfaces:**
- Consumes: `godot-rag-build` CLI from Task 1.
- Produces: `build.sh` legacy mapping:
  - `./build.sh` -> `uv run godot-rag-build build`
  - `./build.sh --no-bump` -> `uv run godot-rag-build build --no-bump`
  - `./build.sh --with-wiki` -> `uv run godot-rag-build build --with-wiki`
  - `./build.sh --publish` and `./build.sh publish` -> `uv run godot-rag-build publish --target pypi`
  - `./build.sh --test-pypi` -> `uv run godot-rag-build publish --target testpypi`
  - publish combinations preserve `--no-bump` and `--with-wiki`
- Produces: hidden test env `GODOT_RAG_BUILD_WRAPPER_DRY_RUN=1` that prints delegated command without executing it.

## Steps

See plan file `docs/superpowers/plans/2026-06-28-build-efficiency.md` Task 6 section (approximately lines 1554-1755) for the full implementation code.

### Key Implementation Notes

1. `build.sh` replaces inline build logic with argument parsing and delegation to `uv run godot-rag-build`
2. `GODOT_RAG_BUILD_WRAPPER_DRY_RUN=1` prints the command without executing (for testing)
3. README updates change build instructions to prefer `uv run godot-rag-build build`
4. Tests verify: syntax validity, default delegation, flag preservation, publish target mapping

### Test Commands

Step 2: `rtk uv run pytest rst2md/tests/test_build_release_wrapper.py -q` (verify fail)
Step 5: `rtk uv run pytest rst2md/tests/test_build_release_wrapper.py rst2md/tests/test_build_release_cli.py -q && rtk bash -n build.sh`

### Commit

```bash
rtk git add build.sh README.md README_zh.md rst2md/tests/test_build_release_wrapper.py
rtk git commit -m "feat: delegate build script to Python tool"
```

## Global Constraints

- `build.sh` 不得保留 docs conversion、RAG database build、package assembly、upload 等主构建逻辑
- Legacy wrapper must delegate all real work to `godot-rag-build`
- README must document `uv run godot-rag-build` as the new entry point
