## Why

`_canonical_form`（`rst2md/rag/symbols.py:23`）在归一化时执行 `name.replace("_", "").replace(".", "")`，把 dot 符号（`ResourceLoader.load`、`Node.connect`、`Node.add_child`）的 dot 边界抹掉。这使 suffix symbol recall 的 LIKE `'%.{normalized}'` 永远无法命中已索引符号，导致两条 symbol gating 查询（`resource-loader`、`node-connect-signal`）当前 `matched_rank = null`（零召回），并让上一轮 `search-ranking-signal-explanations` 录制的 `symbol_recall.suffix` 信号处于 dormant 状态（带 `@expectedFailure` 测试）。

`query-rewrite` spec 已经要求 suffix symbol lookup 评估 `Node.add_child` 这类 dot-notation 候选，但实现并不满足该契约。本 change 修复归一化让 spec 真正成立。

## What Changes

- 修复 `_canonical_form` 的 dot 处理：保留 dot 作为符号边界，使 suffix recall LIKE `'%.{normalized}'` 能命中 `Class.method` 形态的已索引符号。
- 保证已索引符号的 normalized 形态与查询归一化对称（不会一边去 dot、一边留 dot）。
- 转正 `test_suffix_symbol_match_records_signal` 的 `@expectedFailure`，断言 suffix 信号在 dot-notation 查询上被录制。
- 刷新 `docs/search-quality/baseline.json` 并通过 baseline comparison，确认 `resource-loader` 与 `node-connect-signal` 进入 diagnostic window。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `query-rewrite`: 强化 dot-notation 符号的 suffix recall 契约——明确归一化必须保留 dot 边界以使 suffix LIKE 匹配成立，并补一条 dot-notation 查询被 suffix recall 命中的可测场景。

## Impact

- **代码**：`rst2md/rag/symbols.py`（`_canonical_form`）、相关符号召回路径（`retrieval.py` / `searcher.py` 中调用 `normalize_symbol` 的位置）。
- **测试**：转正 `rst2md/tests/` 中的 xfail 测试；可能新增 dot-notation 归一化单元测试。
- **评估**：`docs/search-quality/baseline.json` 刷新；45 查询 baseline 不退化。
- **非影响**：不改 rerank 权重、不改 alias 表、不改 DB schema、不换 embedding、不动 FTS5 排序逻辑。
