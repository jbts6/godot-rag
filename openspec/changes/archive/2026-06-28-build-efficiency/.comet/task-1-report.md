# Task 1 Report: Packaged CLI Entrypoint

## Status: DONE

## Commit

- `51a230f` — feat: add release build CLI entrypoint

## Test Summary

5/5 tests pass: CLI help listing, publish has no --skip-tests, publish target choices, project script wiring, main returns zero for help.

## Files Created/Modified

| File | Action |
|------|--------|
| `godot_rag_build/__init__.py` | Created — package marker |
| `godot_rag_build/cli.py` | Created — argparse parser with 4 subcommands, lazy handler imports |
| `godot_rag_build/runner.py` | Created — CommandResult dataclass + CommandRunner class |
| `rst2md/tests/test_build_release_cli.py` | Created — 5 tests per task brief |
| `pyproject.toml` | Modified — added `godot-rag-build` script, added `godot_rag_build` to wheel packages |

## Key Decisions

- All handler imports (`orchestrator`, `publish`, `cache`) are lazy inside handler functions — these modules don't exist yet and will be implemented in later tasks.
- `publish` subcommand exposes only `--target`, `--no-bump`, `--with-wiki`, `--cache-dir` — no test-skipping parameter.
- Project script points to `godot_rag_build.cli:main` as required.
