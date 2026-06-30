# promote-report-only-gating-candidates Verification

## Summary

| Dimension | Status |
| --- | --- |
| Completeness | PASS: 5/5 tasks complete, 1 delta requirement covered |
| Correctness | PASS: query suite is 45 total / 38 gating / 7 report-only; baseline count is 38 |
| Coherence | PASS: implementation follows the design split between promoted non-addon candidates, retained addon candidates, and retained non-ready candidates |

## Checks

- OpenSpec artifacts complete: proposal, design, delta spec, and tasks are present.
- Tasks complete: all 5 tasks are checked in `openspec/changes/promote-report-only-gating-candidates/tasks.md`.
- Delta spec scenarios covered:
  - Reviewed non-addon candidates are promoted by removing `report_only` from 13 selected queries.
  - Unstable addon candidates remain report-only.
  - Non-ready low-ranking / missing-recall candidates remain report-only.
- Baseline refreshed: `docs/search-quality/baseline.json` records `overall.count=38`.
- WIP updated with the new 38 gating / 7 report-only split and follow-up direction.

## Verification Commands

- `rtk uv run pytest -q rst2md/tests/test_search_eval.py rst2md/tests/test_search_eval_cli.py` -> 57 passed.
- `rtk uv run python3 -m rag.cli eval-search --db godot_rag/rag/godot_docs.sqlite --baseline docs/search-quality/baseline.json --write-baseline --compare-graph` -> exit 0, baseline written, count=38.
- `rtk uv run python3 -m rag.cli eval-search --db godot_rag/rag/godot_docs.sqlite --baseline docs/search-quality/baseline.json --compare-graph` -> exit 0, baseline compared, count=38.
- `rtk uv run pytest -q` -> 245 passed.
- `rtk uv run openspec validate promote-report-only-gating-candidates --strict` -> valid.

## Notes

- Current baseline intentionally records existing gating failures for tutorial intent, symbol normalization, and class inheritance recall. This change increases regression coverage; it does not tune ranking.
- Addon promotion-ready candidates remain report-only until addon data stability is explicitly reviewed.
- `review_mode` is `off` for this tweak; no automatic code-review subagent was run.
