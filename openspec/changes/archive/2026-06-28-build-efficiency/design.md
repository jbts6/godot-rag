## Context

The current local release build is centered on `build.sh`. It handles version bumping, docs conversion, optional Scene Manager wiki input, RAG database generation, diagnostics, package assembly, README merging, wheel building, package index checks, and optional upload. This works, but the shell script repeats expensive stages unless its current timestamp checks happen to catch a narrow case, and the script gives limited structured visibility into where time went or why a stage ran.

The local developer workflow is the primary target. CI must remain usable, but CI speed is not the main optimization goal. Correctness is more important than aggressive caching: any mismatch in recorded inputs must rerun the affected stage.

## Goals / Non-Goals

**Goals:**
- Introduce a Python release build tool with a project script entrypoint: `godot-rag-build`.
- Make `build.sh` a thin compatibility wrapper around the Python tool.
- Provide subcommands for `build`, `publish`, `diagnostics`, and `clean-cache`.
- Use conservative stage fingerprints to skip only stages whose recorded inputs exactly match current inputs.
- Emit a readable terminal summary with per-stage status, elapsed time, and run or skip reasons.
- Write `.cache/build-release/manifest.json` for cache state and `.cache/build-release/last-run.json` for the latest run report.
- Preserve local PyPI/TestPyPI publishing and optional Scene Manager wiki inclusion.
- Keep publish safe by requiring full build gates, tests, diagnostics, version checks, and upload.

**Non-Goals:**
- Do not optimize CI as a primary goal.
- Do not change RAG search behavior, database schema semantics, or packaging contents beyond build orchestration needs.
- Do not add a publish-time skip-tests escape hatch.
- Do not use approximate or aggressive cache heuristics.

## Decisions

### Python orchestrator as the primary implementation

Implement the release flow in Python and expose it through a project script. Python is better suited than shell for structured manifests, JSON reports, fingerprints, stage timing, and testable orchestration logic. `build.sh` remains only as a thin wrapper so local muscle memory and simple shell entrypoints continue to work.

Alternatives considered:
- Keep the shell script and add cache logic there. This preserves fewer moving pieces, but keeps the hardest parts in the least testable place.
- Add a Python helper only for cache decisions while shell remains the main orchestrator. This reduces initial migration but leaves two sources of orchestration truth.

### Stage graph with conservative fingerprints

Represent the build as named stages with inputs, outputs, dependencies, and an action. Each cacheable stage computes a fingerprint from:
- build tool code and `build.sh`
- `pyproject.toml` and `uv.lock`
- relevant `rst2md/` source
- `scripts/merge_readme.py`
- README inputs
- `godot-docs` submodule HEAD
- addon docs/config inputs
- `--with-wiki` setting and wiki input state
- key environment tool versions such as Python, uv, and pandoc

A stage may skip only when its manifest entry exists, output checks pass, and the fingerprint exactly matches. If any part is missing or different, the stage runs.

### Structured reporting

The terminal output should end with a compact stage table showing `RUN`, `SKIP`, or `FAIL`, elapsed time, and reason. The same facts should be persisted in `.cache/build-release/last-run.json`, while stable cache fingerprints live in `.cache/build-release/manifest.json`.

This separates durable cache state from run diagnostics. It also keeps the cache local and out of release artifacts.

### Publish is a gated command

`publish --target pypi|testpypi` should call the same build pipeline, then require tests, release database diagnostics, package version existence checks, and upload. The command should not expose a skip-tests option. If a gate fails, upload must not start.

### Wiki support remains first-class

The current `--with-wiki` behavior is part of local release capability. The Python tool should preserve it and include the wiki setting/input in fingerprints so cached outputs cannot cross between wiki and non-wiki builds.

## Risks / Trade-offs

- **Large directory hashing can become expensive** -> keep fingerprints deterministic but scoped to relevant files and metadata; report fingerprint time as part of stage timing if needed.
- **Thin wrapper may break old argument habits** -> map the important legacy invocations to the new subcommands and make unsupported forms fail with clear guidance.
- **Cache correctness bugs could reuse stale artifacts** -> require exact fingerprints plus output existence checks; default to rebuild when uncertain.
- **Publishing logic in Python touches network and credentials** -> isolate package-index checks and upload invocation behind testable command construction; never log secrets.
- **CI may still duplicate build logic** -> keep CI compatibility minimal initially, then optionally migrate workflows once the local tool is stable.

## Migration Plan

1. Add the Python build tool and project script entrypoint.
2. Implement stage timing, reporting, manifest read/write, and cache cleanup.
3. Move local build stages into the Python orchestrator.
4. Add publish and wiki support.
5. Replace `build.sh` internals with a thin wrapper.
6. Add tests around command parsing, cache decisions, report writing, wrapper behavior, and publish gates.
7. Keep CI changes minimal: preserve current checks or adjust syntax checks to account for the thin wrapper.

Rollback strategy: keep changes isolated to the new build tool, project script entrypoint, and wrapper. If the new orchestrator fails during development, `git revert` can restore the previous `build.sh` implementation.

## Open Questions

- Whether the Python build tool should live under `scripts/` or a package module. The implementation should choose the location that best supports project script entrypoints and tests without packaging it into the runtime `godot_rag` wheel unnecessarily.
- Whether CI should immediately call `godot-rag-build` or continue its current explicit commands in the first pass.
