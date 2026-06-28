# Task 7: Integration Verification And OpenSpec Bookkeeping

## Task Description

**Files:**
- Modify: `openspec/changes/build-efficiency/tasks.md`
- Verify: `docs/superpowers/plans/2026-06-28-build-efficiency.md`
- Verify: `.github/workflows/test.yml`
- Verify: `.github/workflows/publish.yml`

**Interfaces:**
- Consumes: all previous tasks.
- Produces: checked OpenSpec task list for implemented items.
- Produces: verification evidence from focused build-tool tests, full project tests, wrapper syntax check, OpenSpec validation, and command help smoke test.

## Steps

### Step 1: Run focused build-tool tests

```bash
rtk uv run pytest rst2md/tests/test_build_release_cli.py rst2md/tests/test_build_release_stages.py rst2md/tests/test_build_release_cache.py rst2md/tests/test_build_release_orchestrator.py rst2md/tests/test_build_release_publish.py rst2md/tests/test_build_release_wrapper.py -q
```

Expected: PASS.

### Step 2: Run full project tests

```bash
rtk uv run pytest -q
```

Expected: PASS.

### Step 3: Run syntax and CLI smoke checks

```bash
rtk bash -n build.sh
rtk uv run godot-rag-build --help
rtk uv run godot-rag-build publish --help
```

Expected: `bash -n` exits 0, root help lists four subcommands, publish help does not contain `--skip-tests`.

### Step 4: Run OpenSpec validation

```bash
rtk openspec validate build-efficiency --strict
```

Expected: PASS.

### Step 5: Confirm CI compatibility scope

Inspect workflow references:

```bash
rtk rg -n "build.sh|godot-rag-build|uv run pytest|uv build" .github/workflows
```

Expected: existing `bash -n build.sh` checks remain valid.

### Step 6: Update OpenSpec tasks

Edit `openspec/changes/build-efficiency/tasks.md` so completed implementation items are checked. Apply `[x]` to sections 1-5 for behavior verified by Steps 1-5.

### Step 7: Commit final verification bookkeeping

```bash
rtk git status --short
rtk git add openspec/changes/build-efficiency/tasks.md
rtk git commit -m "chore: mark build efficiency tasks complete"
```

## Global Constraints

- All focused build-tool tests must pass
- Full project test suite must pass
- `bash -n build.sh` must exit 0
- CLI help must list 4 subcommands
- Publish help must not contain `--skip-tests`
