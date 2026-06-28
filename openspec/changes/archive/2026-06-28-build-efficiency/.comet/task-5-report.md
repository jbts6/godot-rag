# Task 5: Publish Gates And Package Index Checks

## Status: DONE

## Commit

- `a67ad9e` feat: add gated release publishing

## Test Summary

- 4/4 publish tests pass (`rst2md/tests/test_build_release_publish.py`)
- 1/1 CLI no-skip-tests test passes (`test_publish_help_has_no_skip_tests`)

## Implementation

Created `godot_rag_build/publish.py` with:
- `PublishOptions` dataclass (target, no_bump, with_wiki, cache_dir, root, runner)
- `check_worktree_clean()` — runs `git status --porcelain`, raises on dirty
- `package_version_exists()` — checks PyPI/TestPyPI JSON API via injectable opener
- `_failed_publish_report()` — helper for FAIL reports with publish_error artifact
- `run_publish()` — full gated pipeline: worktree check → build → tests → diagnostics → version check → upload

Created `rst2md/tests/test_build_release_publish.py` with:
- `FakeRunner` for recording command calls
- `test_package_version_exists_true_for_200_response` — 200 → True
- `test_package_version_exists_false_for_404` — 404 → False
- `test_publish_runs_tests_and_version_check_before_upload` — verifies ordering and OK status
- `test_existing_package_version_blocks_upload` — version exists → no upload, FAIL

## Key Decisions

- No `--skip-tests` exposed on publish subcommand (verified by CLI test)
- Upload command uses `uv run --with twine python -m twine upload`
- TestPyPI upload includes `--repository testpypi` flag
- Diagnostics runs with `PYTHONPATH=rst2md` env var
