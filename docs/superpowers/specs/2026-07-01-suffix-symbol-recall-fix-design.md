---
comet_change: suffix-symbol-recall-fix
role: technical-design
canonical_spec: openspec
status: final
archived-with: 2026-07-01-suffix-symbol-recall-fix
status: final
---

# Suffix Symbol Recall Fix - Technical Design

## Context

`_canonical_form`（`rst2md/rag/symbols.py:17-24`）在归一化末尾执行 `name.replace("_", "").replace(".", "")`，同时抹掉 underscore 和 dot。`Symbol.normalized_name` 在索引时由 `extract_symbols` → `normalize_symbol` 写入 `symbols` 表，查询时由 `searcher._search_database_impl` 对 `plan.symbol_candidates` 调用 `normalize_symbol` 后用于 exact/prefix/suffix 三层 LIKE 匹配。

Suffix 层的 LIKE 模式是 `f"%.{normalized}"`（`rst2md/rag/searcher.py:211`），**要求 normalized 形态中含 dot**。但 `_canonical_form` 把 dot 去掉了，所以已索引的 `normalized_name` 永不含 dot，suffix LIKE 永不命中 → suffix recall 是死代码，`symbol_recall.suffix` 信号从未录制（上一轮 `search-ranking-signal-explanations` 已用 `@expectedFailure` 锁定该状态，见 `rst2md/tests/test_rag_search.py:1250`）。

`query-rewrite` spec 的 "Query plan signals feed symbol recall and ranking" 要求里已有 `Node.add_child` 这类 dot-notation 候选必须被 exact/suffix lookup 评估的场景，但实现并不满足契约。本 change 修归一化让 spec 真正成立。

## Goals / Non-Goals

**Goals:**
- 让 `_canonical_form` 保留 dot 作为符号边界，使 suffix recall LIKE `'%.{normalized}'` 对 `Class.method` 形态的已索引符号生效。
- 保证查询侧与索引侧归一化对称（同一函数，无需双写）。
- 转正 `test_suffix_symbol_match_records_signal`，并更新断言旧 dot-stripping 输出的两个 canonical 单元测试。
- 刷新 `docs/search-quality/baseline.json`，确认 45 查询 baseline 不退化。

**Non-Goals:**
- 不改 rerank 权重、不改 alias 表（`_ALIAS_RULES`）、不改 DB schema、不换 embedding。
- 不动 FTS5 排序逻辑、不动 graph expansion。
- 不调 `symbol_recall.exact/prefix` 的权重（+100/+40）。
- 不保证 `resource-loader` / `node-connect-signal` 两条 gating failure 一定进入 `required_at`（见 Open Questions）。

## Design

### D1：修 `_canonical_form`，保留 dot，继续去 underscore

把 `rst2md/rag/symbols.py:23` 的 `name.replace("_", "").replace(".", "")` 改为 `name.replace("_", "")`（只去 underscore，保留 dot），并更新 docstring。

Suffix LIKE `'%.{normalized}'` 的语义就是「按 dot 边界匹配方法后缀」。dot 是符号层级的结构边界（`Class.method`），underscore 只是命名风格（`add_child` ≡ `addchild`）。保留 dot 后：

- `Node.add_child` → `node.addchild`（camelCase 不触发，lower 后去 underscore，留 dot）
- 查询 `add_child` → `addchild`
- suffix LIKE `%.addchild` 命中 `node.addchild` ✓

`normalize_symbol` 在索引（`extract_symbols`）和查询（`searcher` 对 `plan.symbol_candidates`）两侧都被调用，改一处即可，两侧自动一致。

**备选 A（拒绝）**：改 LIKE 模式而非归一化。LIKE 模式语义正确，错的是归一化把结构信息丢了；改 LIKE 会引入新分隔符歧义。

**备选 B（拒绝）**：两侧都去 dot 且 LIKE 不要求 dot。这正是当前 bug 状态：去 dot 后 `Node.add_child` 与 `Nodeadd_child`、`NodeAdd_Child` 全部塌缩，suffix 与 prefix 的语义边界消失，召回会引入大量跨类误匹配。

### D2：迁移策略——重建索引

`normalized_name` 是 DB 持久化字段。修了 `_canonical_form` 后，旧 DB 里的 `normalized_name` 仍是 dot-stripped 形态，新查询产生 dot-preserved 形态，两者不匹配。

- 评估 DB 由测试 fixture 重建（`test_search_eval._build_eval_db`），无迁移问题。
- `docs/search-quality/baseline.json` 在 eval 流程里重建 DB 后再生成，自动一致。
- 生产 DB（用户本地）需要重建才能享受修复；`indexer.build_database` 已经调用 `extract_symbols`，重跑 `godot-rag index` 即可。无 schema 变更，无需迁移脚本。

### D3：测试更新清单

- `rst2md/tests/test_rag_symbols.py::test_canonical_dotted`：`"nodeaddchild"` → `"node.addchild"`。
- `rst2md/tests/test_rag_symbols.py::test_normalizes_method_symbols`：`"stringnameisvalidfilename"` → `"stringname.isvalidfilename"`。
- `rst2md/tests/test_rag_search.py::test_suffix_symbol_match_records_signal`：移除 `@expectedFailure`，断言保持不变（query=`add_child`，期望命中 `Node.add_child` 并录制 `symbol_recall.suffix` weight=80.0）。
- 其余非 dot-notation 的 canonical 测试（camelCase/snake_case/leading underscore/mixed）输出不变，无需改动。

## Risks / Trade-offs

- **[风险] 修 dot 后 prefix LIKE 行为变化**：`Node` 查询的 prefix LIKE 从 `node%`（匹配 `nodeaddchild`）变成 `node%`（匹配 `node.addchild`，仍命中）。实测在 build 阶段跑 45 查询确认无新误匹配。→ 缓解：baseline comparison 把关，hit@1/hit@5/mrr@5 不得下降。
- **[风险] 两条 gating failure 可能仍未进 `required_at`**：`resource-loader`（query=`ResourceLoader.load`）和 `node-connect-signal`（query=`Node.connect`）当前 `matched=null`。若预期目标在索引里符号名不是 `Class.method` 形态（例如只存了 `load` 或 `connect`），suffix/exact recall 仍可能不命中。→ 缓解：build 阶段先跑 eval 定位预期 chunk 的实际 symbol，再决定是否需追加 alias 或调 query rewrite；若需改 ranking，开下一个 change，不在本 change 内扩范围。
- **[风险] 已发布 DB 与新代码不兼容**：用户升级 `godot-rag` 后不重建 DB，dot-notation 符号查询的 exact/prefix/suffix 三层 symbol recall 全部失效——旧 DB 的 `normalized_name` 是 dot-stripped，新查询归一化保留 dot，二者不匹配。这相对旧状态是 exact/prefix 的退化（旧状态 exact/prefix 可命中，仅 suffix 死；新代码+旧 DB 三层全失效）。FTS5 召回仍可用，搜索不崩，但排名丢失 symbol 加分。→ 缓解：CHANGELOG 注明「升级后必须 `godot-rag build` 重建」；后续 change 可加 stale-DB 检测器。
- **[权衡] 保留 dot 使 normalized 形态不再是「纯 token 串」**：下游若有代码假设 `normalized_name` 不含标点会被影响。→ 已核查：`normalized_name` 仅用于 `symbols` 表的 `=`/`LIKE` 查询，无其他消费者。

## Migration Plan

1. 改 `_canonical_form`（D1）。
2. 更新 3 个测试（D3）。
3. `uv run pytest -q` 全绿（含转正的 xfail）。
4. 跑 eval 刷新 `docs/search-quality/baseline.json`，baseline comparison 通过。
5. CHANGELOG 注明升级后需重建索引。

回滚：revert `_canonical_form` 一行 + 3 个测试即可，无 DB schema 后果（旧 DB 仍可读）。

## Open Questions

- Q1：`resource-loader` / `node-connect-signal` 的预期目标 chunk 在索引里的 `symbol` 字段实际形态是什么？build 阶段先 `_build_eval_db` + 直接查 `symbols` 表确认，再判断 suffix 修复是否足够。
- Q2：若 Q1 显示预期目标 symbol 不是 `Class.method` 形态，是否在本 change 内追加 alias 规则？倾向**否**——保持本 change 只修归一化 bug，alias 调整开后续 change，避免归因混淆。
