# Build Efficiency Hotfix Design

## Fix

The release build tool keeps the existing stage graph and command surface, but tightens correctness around cache keys, diagnostics, publish failure reporting, wheel validation, and archived spec metadata.

## Implementation Notes

- Replace the one-size-fits-all fingerprint payload with stage-relevant inputs while retaining common build tool inputs.
- Include deterministic tree/file fingerprints for source directories and documentation inputs. Include tool versions through the existing runner, with failures represented as stable unavailable values rather than hard failures.
- Route standalone diagnostics through `CommandRunner.run(..., env=_env_with_pythonpath(...))`.
- Wrap publish post-build gates so test, diagnostics, version-check, and upload failures produce `_failed_publish_report(...)`, write `last-run.json`, print the summary, and return `FAIL`.
- Replace wheel placeholder creation with a `StageError` when the expected wheel is missing after `uv build --wheel`.
- Replace the archived spec purpose placeholder with a concise description.

## Verification

- Add regression tests that fail on current behavior for each defect.
- Run focused build-release tests.
- Run full pytest.
- Run `openspec validate --all --strict`.
