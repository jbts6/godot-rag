## MODIFIED Requirements

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
