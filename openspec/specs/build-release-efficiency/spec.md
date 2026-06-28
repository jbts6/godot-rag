# build-release-efficiency Specification

## Purpose
Define the local release build workflow for `godot-rag-build`, including conservative cache reuse, stage reporting, diagnostics, publishing gates, wrapper compatibility, wiki input handling, and cache cleanup.
## Requirements
### Requirement: Python release build entrypoint
The system SHALL provide a Python-based release build tool exposed as the project script `godot-rag-build` with `build`, `publish`, `diagnostics`, and `clean-cache` subcommands.

#### Scenario: Build command is available
- **WHEN** a developer runs the project script help for `godot-rag-build`
- **THEN** the output lists the `build`, `publish`, `diagnostics`, and `clean-cache` subcommands

#### Scenario: Thin wrapper delegates to Python tool
- **WHEN** a developer invokes `./build.sh` for a supported local build or publish action
- **THEN** `build.sh` delegates to the Python release build tool instead of containing the primary build implementation

### Requirement: Conservative stage cache reuse
The build tool SHALL reuse stage outputs only when that stage's recorded input fingerprint exactly matches the current input fingerprint, including stage-relevant source inputs, documentation inputs, addon/wiki inputs, and tool/environment versions.

#### Scenario: Unchanged inputs skip reusable stages
- **WHEN** a developer runs the same build command twice without changing tracked build inputs
- **THEN** reusable stages report `SKIP` and explain that the current fingerprint matches the manifest

#### Scenario: Changed inputs rerun affected stages
- **WHEN** a developer changes an input covered by a stage fingerprint
- **THEN** that stage reports `RUN` and rebuilds its output instead of using the cached result

#### Scenario: Missing manifest reruns stages
- **WHEN** `.cache/build-release/manifest.json` is absent
- **THEN** the build tool treats cache state as unavailable and runs required stages

#### Scenario: Stage-specific source inputs affect fingerprints
- **WHEN** a developer changes `rst2md/` source, README inputs, addon documentation/configuration, wiki input state, or a tracked tool/environment version
- **THEN** affected reusable stages produce a different fingerprint and cannot reuse the stale manifest entry

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

