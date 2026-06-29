## Context

The godot-rag project has an existing search pipeline using SQLite FTS5 + sqlite-vec + RRF fusion. An `eval-search` CLI command exists but is broken due to packaging misconfiguration. The current golden-query suite has only 5 entries. Failed queries provide no diagnostic information, making it difficult to distinguish recall failures from ranking failures.

## Goals / Non-Goals

**Goals:**
- Make `eval-search` CLI runnable via correct packaging
- Provide failure diagnostics for debugging query failures
- Expand query coverage to 30+ tiered queries across 5 categories
- Improve recall for natural-language queries via conservative alias rewriting
- Improve ranking for tutorial-intent queries via doc-type boost
- Establish a reviewable baseline for regression detection

**Non-Goals:**
- Replace or retrain the embedding model
- Change SQLite, FTS5, sqlite-vec, or RRF fusion architecture
- Require full release-database evaluation in default CI
- Make broad/corpus-sensitive queries gating (keep as `report_only`)

## Decisions

### D1: Query rewriting as lexical recall candidates only

**Decision:** `expand_query_variants()` returns alias strings used only for FTS matching. Vector search continues using the original query text.

**Rationale:** Aliases are conservative symbol mappings (e.g., "attach node to scene tree" → "Node.add_child"). Using them for vector search would dilute semantic intent. FTS benefits from exact symbol matches; vector search does not.

**Alternatives considered:**
- Rewrite for both FTS and vector: rejected — aliases are lexical, not semantic
- Use aliases as RRF sub-queries: rejected — adds complexity without clear benefit

### D2: Intent boost as post-ranking score adjustment

**Decision:** Apply `doc_type_boost()` after candidate assembly, before final sort. Boost is a small additive value (0.05) applied to tutorial results for how-to queries.

**Rationale:** Keeps the boost transparent and separable from the core ranking. Does not alter FTS or vector scores. Easy to tune or remove.

**Alternatives considered:**
- Re-rank with separate model: rejected — overkill for tutorial intent
- Filter by doc_type: rejected — would remove relevant class results entirely

### D3: Tiered query suite with `report_only` flag

**Decision:** Use the existing `GoldenQuery.report_only` field to tier queries. Gating queries (≥12) must pass; report-only queries (≥8) surface regressions without blocking.

**Rationale:** Broad queries (aliases, intent, graph, addon) are valuable for diagnostics but too corpus-sensitive for CI gating. The tiering lets us track them without false failures.

### D4: Failure diagnostics as separate dataclass

**Decision:** `FailureDiagnostics` is a frozen dataclass attached to `QueryResult.diagnostics`. It is computed on-demand via `diagnostic_limit` parameter, not by default.

**Rationale:** Diagnostics require extra DB queries. Making it opt-in keeps the default evaluation fast. The `diagnostic_limit` controls how far to search for the expected target.

## Risks / Trade-offs

- **Alias rules are manually curated** → Risk: maintenance burden grows. Mitigation: start conservative (5 rules), expand based on observed failures.
- **Intent boost is heuristic** → Risk: may over-boost or under-boost. Mitigation: small value (0.05), easy to tune; tutorial queries are `report_only` initially.
- **Baseline JSON is point-in-time** → Risk: stale baseline after corpus changes. Mitigation: `--write-baseline` flag for refresh; baseline is reviewed, not auto-generated.
- **Diagnostic queries add latency** → Risk: slower evaluation. Mitigation: `diagnostic_limit` is opt-in; default evaluation skips diagnostics.
