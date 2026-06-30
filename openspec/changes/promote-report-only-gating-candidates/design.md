## Context

The archived `search-ranking-report-only-triage` work classified 20 report-only queries. The latest real-database run found 17 `promotion_ready`, 2 `low_ranking`, and 1 `missing_recall`.

## Approach

Promote only the non-addon `promotion_ready` queries:

- `child-node-attach`
- `start-countdown-timer`
- `how-to-change-scenes`
- `script-signals-tutorial`
- `physics-server-engine`
- `timer-related-methods`
- `object-signal-methods`
- `editor-plugin-running-code`
- `container-ui-class`
- `shader-material-class`
- `navigation-agent-3d-class`
- `physics-raycast-query`
- `multiplayer-networking-tutorial`

Keep these addon candidates report-only:

- `state-machine-addon`
- `addon-dialogue-manager`
- `addon-phantom-camera`
- `addon-limboai-behavior-tree`

Keep the remaining non-ready queries report-only:

- `nodes-and-scenes-tutorial`
- `vector-fallback-metadata`
- `class-inheritance-node-object`

This change edits the query fixture only. Baseline refresh is mechanical after the updated gating set passes against `godot_rag/rag/godot_docs.sqlite`.

## Validation

- Add or tighten a packaged-query test that asserts the updated tier counts and selected promoted/non-promoted query IDs.
- Run focused evaluator tests.
- Run `eval-search` with `--baseline docs/search-quality/baseline.json --write-baseline --compare-graph`.
- Re-run baseline comparison without `--write-baseline`.
- Run the full pytest suite.
