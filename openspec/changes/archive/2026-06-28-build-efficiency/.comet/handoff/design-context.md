# Comet Design Handoff

- Change: build-efficiency
- Phase: design
- Mode: compact
- Context hash: 356caa801bfc2adca44fd25a0c7d99f7275f7eda7d71d927b03556b00cdebbc9

Generated-by: comet-handoff.sh

OpenSpec remains the canonical capability spec. This handoff is a deterministic, source-traceable context pack, not an agent-authored summary.

## openspec/changes/build-efficiency/proposal.md

- Source: openspec/changes/build-efficiency/proposal.md
- Lines: 1-27
- SHA256: 683e2e8815959f62ed71ff62246dfc8363d6499644afe29a955befeced357b67

```md
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
```

## openspec/changes/build-efficiency/design.md

- Source: openspec/changes/build-efficiency/design.md
- Lines: 1-87
- SHA256: 18cefc5c7a3a39dacb33b4855c38f71629ffea1904ad4c01c33a7ab4508118ef

[TRUNCATED]

```md
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
```

Full source: openspec/changes/build-efficiency/design.md

## openspec/changes/build-efficiency/tasks.md

- Source: openspec/changes/build-efficiency/tasks.md
- Lines: 1-37
- SHA256: 56a48409be7753daa6addd0ed79e22f29ddd9f0efe87da15fca5a37aa1fce9a5

```md
## 1. Tool Structure and CLI

- [ ] 1.1 Decide the Python module location for the release build tool and add the `godot-rag-build` project script entrypoint.
- [ ] 1.2 Implement subcommand parsing for `build`, `publish`, `diagnostics`, and `clean-cache`.
- [ ] 1.3 Replace `build.sh` with a thin wrapper that delegates supported invocations to the Python tool.

## 2. Stage Orchestration, Cache, and Reports

- [ ] 2.1 Implement a stage model with status, dependencies, elapsed time, run or skip reason, outputs, and failure handling.
- [ ] 2.2 Implement conservative input fingerprinting for docs conversion, wiki input, RAG database generation, package assembly, README merge, wheel build, and relevant tool/environment versions.
- [ ] 2.3 Persist cache state to `.cache/build-release/manifest.json` and latest run details to `.cache/build-release/last-run.json`.
- [ ] 2.4 Implement terminal summary output showing each stage's `RUN`, `SKIP`, or `FAIL` status, elapsed time, and reason.
- [ ] 2.5 Implement `clean-cache` to remove `.cache/build-release`.

## 3. Build, Diagnostics, Publish, and Wiki Flows

- [ ] 3.1 Port the local wheel build flow from `build.sh` into the Python orchestrator.
- [ ] 3.2 Preserve release database diagnostics and git-ignore validation for generated database outputs.
- [ ] 3.3 Preserve optional Scene Manager wiki inclusion and cleanup behavior.
- [ ] 3.4 Implement `publish --target pypi|testpypi` with mandatory full build, tests, diagnostics, package version checks, and upload.
- [ ] 3.5 Ensure publish does not expose a skip-tests bypass.

## 4. Tests and Compatibility

- [ ] 4.1 Add tests for CLI parsing and subcommand help.
- [ ] 4.2 Add tests for cache hit, cache miss, missing manifest, and changed-input behavior.
- [ ] 4.3 Add tests for JSON report and manifest writing.
- [ ] 4.4 Add tests for publish gate ordering and version-exists failure before upload.
- [ ] 4.5 Add tests or checks for `build.sh` wrapper compatibility.
- [ ] 4.6 Run focused build-tool tests and the full test suite.

## 5. Documentation and Verification

- [ ] 5.1 Update local build usage text to document `uv run godot-rag-build`.
- [ ] 5.2 Verify repeated local builds skip reusable stages when inputs are unchanged.
- [ ] 5.3 Verify cache cleanup forces required stages to run on the next build.
- [ ] 5.4 Verify existing CI checks are not broken or apply minimal compatibility updates.
```

## openspec/changes/build-efficiency/specs/build-release-efficiency/spec.md

- Source: openspec/changes/build-efficiency/specs/build-release-efficiency/spec.md
- Lines: 1-75
- SHA256: 6255ee502f005246144c253c09ed90d84173c10dab95da430200ee6b5774571f

```md
## ADDED Requirements

### Requirement: Python release build entrypoint
The system SHALL provide a Python-based release build tool exposed as the project script `godot-rag-build` with `build`, `publish`, `diagnostics`, and `clean-cache` subcommands.

#### Scenario: Build command is available
- **WHEN** a developer runs the project script help for `godot-rag-build`
- **THEN** the output lists the `build`, `publish`, `diagnostics`, and `clean-cache` subcommands

#### Scenario: Thin wrapper delegates to Python tool
- **WHEN** a developer invokes `./build.sh` for a supported local build or publish action
- **THEN** `build.sh` delegates to the Python release build tool instead of containing the primary build implementation

### Requirement: Conservative stage cache reuse
The build tool SHALL reuse stage outputs only when that stage's recorded input fingerprint exactly matches the current input fingerprint.

#### Scenario: Unchanged inputs skip reusable stages
- **WHEN** a developer runs the same build command twice without changing tracked build inputs
- **THEN** reusable stages report `SKIP` and explain that the current fingerprint matches the manifest

#### Scenario: Changed inputs rerun affected stages
- **WHEN** a developer changes an input covered by a stage fingerprint
- **THEN** that stage reports `RUN` and rebuilds its output instead of using the cached result

#### Scenario: Missing manifest reruns stages
- **WHEN** `.cache/build-release/manifest.json` is absent
- **THEN** the build tool treats cache state as unavailable and runs required stages

### Requirement: Stage timing and run reports
The build tool SHALL report every stage's status, elapsed time, and run or skip reason in a human-readable terminal summary and SHALL write `.cache/build-release/last-run.json`.

#### Scenario: Terminal summary explains decisions
- **WHEN** a build finishes
- **THEN** the terminal output includes each stage's `RUN` or `SKIP` status, elapsed time, and reason

#### Scenario: JSON report records run details
- **WHEN** a build finishes
- **THEN** `.cache/build-release/last-run.json` contains the command, stage statuses, elapsed times, reasons, and output paths relevant to the run

### Requirement: Safe publish workflow
The publish command SHALL perform a complete build, run tests, run release database diagnostics, check the target package version does not already exist, and only then upload to PyPI or TestPyPI.

#### Scenario: Publish performs gates before upload
- **WHEN** a developer runs `godot-rag-build publish --target testpypi` or `--target pypi`
- **THEN** the tool completes build, tests, diagnostics, and version-existence checks before upload

#### Scenario: Publish has no skip-tests bypass
- **WHEN** a developer asks for publish command help
- **THEN** the help does not expose a flag that skips required publish tests

#### Scenario: Existing package version blocks upload
- **WHEN** the target package version already exists on the selected package index
- **THEN** the publish command fails before attempting upload

### Requirement: Wiki build path support
The build tool SHALL support the existing optional Scene Manager wiki inclusion path for local builds and publishing.

#### Scenario: Wiki option includes and cleans wiki input
- **WHEN** a developer runs a build with the wiki option enabled
- **THEN** the tool fetches or prepares the Scene Manager wiki input for RAG database generation and removes transient wiki checkout state after the build

#### Scenario: Wiki option participates in cache fingerprints
- **WHEN** the wiki option changes between builds
- **THEN** stages affected by wiki input do not reuse fingerprints recorded for the opposite wiki setting

### Requirement: Cache cleanup
The build tool SHALL provide a `clean-cache` command that removes local release build cache state.

#### Scenario: Clean cache removes build cache directory
- **WHEN** a developer runs `godot-rag-build clean-cache`
- **THEN** `.cache/build-release` is removed or left absent

#### Scenario: Build after clean cache reruns required stages
- **WHEN** a developer runs a build after cleaning the cache
- **THEN** required build stages run instead of reporting cache hits
```

