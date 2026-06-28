# Task 3 Report: Fingerprints, Manifest Cache, And Clean Cache

## Status: DONE

## Files Created
- `godot_rag_build/fingerprints.py` — SHA-256 fingerprint functions for files, trees, and option maps
- `godot_rag_build/cache.py` — `BuildCache` with manifest persistence, `CacheDecision`, and `clean_cache`
- `rst2md/tests/test_build_release_cache.py` — 6 tests covering fingerprint stability, cache skip/miss, and cache cleanup

## Implementation Notes
- Fingerprints use SHA-256 with `\0`-delimited chunks and sorted key/path ordering for stability
- `BuildCache.should_skip` checks all three conditions before skipping: fingerprint match, output_check callback, and output file existence
- `clean_cache` uses `shutil.rmtree` to remove the entire cache directory tree
- Cache integrates with `run_stages` via the existing `cache` parameter (already wired in Task 2)

## Test Results
6/6 passed — all cache and fingerprint tests green

## Commit
- 1953620 feat: add release build cache manifest
