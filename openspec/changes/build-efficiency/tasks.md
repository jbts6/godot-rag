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
