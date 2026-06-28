---
comet_change: build-efficiency
role: technical-design
canonical_spec: openspec
archived-with: 2026-06-28-build-efficiency
status: final
---

# Build Efficiency Technical Design

## Context

`build.sh` currently owns the local release build path. It handles version bumping, docs conversion, optional Scene Manager wiki input, RAG database generation, diagnostics, package assembly, README merging, wheel building, package-index checks, and optional upload. The script is useful, but repeated local builds still redo expensive work and provide limited structured visibility into why a stage ran or skipped.

The new design keeps local release convenience while moving orchestration into Python, where command parsing, fingerprints, JSON manifests, stage timing, and testable control flow are easier to maintain. CI speed is not the primary goal, but the existing CI checks must remain usable or receive minimal compatibility updates.

## Architecture

Add `scripts/build_release.py` as the primary release build orchestrator and expose it through `pyproject.toml` as:

```toml
[project.scripts]
godot-rag-build = "scripts.build_release:main"
```

`build.sh` becomes a thin wrapper. It should translate supported legacy invocations into `uv run godot-rag-build ...` and fail unsupported forms with clear guidance. The wrapper must not duplicate build-stage logic.

The Python tool exposes four subcommands:

- `build`: build the local wheel and generated package assets.
- `publish --target pypi|testpypi`: perform gated publishing after a complete build.
- `diagnostics`: run release database diagnostics against the current or specified database.
- `clean-cache`: remove `.cache/build-release`.

## Stage Model

Represent the build as ordered stages. Each stage has:

- name
- dependencies
- command/action
- cacheability
- input fingerprint function
- output validation function
- run or skip reason
- elapsed time
- status: `RUN`, `SKIP`, or `FAIL`

Initial stages:

1. Resolve configuration and version.
2. Convert Godot docs to Markdown.
3. Prepare optional Scene Manager wiki input.
4. Build the RAG database.
5. Run RAG database diagnostics and git-ignore validation.
6. Assemble the `godot_rag` package tree.
7. Merge README content for PyPI.
8. Build the wheel.
9. Run publish-required tests.
10. Check package version existence on PyPI or TestPyPI.
11. Upload package.

The stage runner should stop on the first failed required stage. It should still write a `last-run.json` report with the failure status and reason.

## Cache Design

Store durable cache state in:

```text
.cache/build-release/manifest.json
```

Store the latest run report in:

```text
.cache/build-release/last-run.json
```

A cacheable stage may skip only when all of these are true:

- a manifest entry exists for the stage
- the current input fingerprint exactly matches the manifest fingerprint
- expected outputs exist and pass the stage output check
- command options that affect the stage match, including `--with-wiki`

Any uncertainty means `RUN`.

Fingerprint inputs should be conservative:

- build tool source and `build.sh`
- `pyproject.toml` and `uv.lock`
- relevant `rst2md/` source
- `scripts/merge_readme.py`
- README inputs
- `godot-docs` submodule HEAD
- addon docs and addon config inputs
- `--with-wiki` setting and wiki input state
- key tool versions such as Python, uv, and pandoc

Directory fingerprints must use stable ordering. If fingerprinting a large tree is noticeable, the time spent should be visible in the relevant stage timing or reason text.

## Reporting

Every run prints a compact terminal table:

```text
Stage                 Status  Time     Reason
docs-md               SKIP    0.12s    fingerprint match
rag-db                RUN     58.4s    rst2md source changed
diagnostics           RUN     1.8s     required after rag-db
```

`last-run.json` should include:

- command and normalized options
- start/end timestamps
- overall status
- per-stage status, elapsed time, reason, fingerprint key or digest, and output paths
- produced artifacts such as wheel path and database path when available

Secrets and tokens must not be logged.

## Publish Flow

`publish --target pypi|testpypi` is a gated command. It must:

1. require a clean worktree before upload-sensitive work
2. run the complete build pipeline
3. run the full test suite
4. run release database diagnostics
5. check whether the package version already exists on the target package index
6. upload only after all gates pass

The publish command must not expose `--skip-tests`. A version-exists failure must happen before upload starts.

## Wiki Flow

The `--with-wiki` path remains supported. The Python tool prepares the Scene Manager wiki input before RAG database generation, includes the wiki option and relevant wiki input state in affected fingerprints, and cleans transient wiki checkout state after the build. Cached non-wiki outputs must not satisfy wiki-enabled builds, and cached wiki-enabled outputs must not satisfy non-wiki builds.

## Testing Strategy

Use unit tests for orchestration logic and mocks for external commands. Avoid real uploads and full database rebuilds in unit tests.

Required test coverage:

- CLI parsing and subcommand help
- stage cache hit, cache miss, missing manifest, changed-input behavior
- manifest and `last-run.json` writing
- output existence checks preventing false cache hits
- publish gate ordering
- package-version-exists failure before upload
- absence of publish skip-tests option
- `build.sh` wrapper delegation for supported legacy invocations
- `clean-cache` removing `.cache/build-release`

Final verification should include focused build-tool tests and the full project test suite.

## Migration Plan

1. Add `scripts/build_release.py` and tests.
2. Add the `godot-rag-build` project script entrypoint.
3. Implement stage runner, manifest, reports, and `clean-cache`.
4. Port local build stages from `build.sh`.
5. Add diagnostics, publish gates, and wiki support.
6. Replace `build.sh` with a thin wrapper.
7. Keep CI compatible by preserving `bash -n build.sh` or making the minimal workflow update needed for the wrapper.

Rollback is straightforward because the change is isolated to the new build tool, the project script entrypoint, tests, and `build.sh`.

## Open Decisions for Build Phase

- Exact wrapper mapping for every historical `build.sh` argument should be finalized while implementing CLI parsing.
- The first build implementation may keep CI workflows on their explicit commands; migrating CI to `godot-rag-build` can remain optional unless tests require adjustment.
