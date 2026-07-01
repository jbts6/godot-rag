# Comet Design Handoff

- Change: suffix-symbol-recall-fix
- Phase: design
- Mode: compact
- Context hash: 8b15e6eab44d8057d52be3c031cc595acdc90de06ee8c85ced90a1f774bd2009

Generated-by: comet-handoff.sh

OpenSpec remains the canonical capability spec. This handoff is a deterministic, source-traceable context pack, not an agent-authored summary.

## openspec/changes/suffix-symbol-recall-fix/proposal.md

- Source: openspec/changes/suffix-symbol-recall-fix/proposal.md
- Lines: 1-29
- SHA256: 1b8f5427ee9bdb65e6880d549d9bee386996f61e453b5ad4998307e0a1d4d7e8

```md
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
```

## openspec/changes/suffix-symbol-recall-fix/design.md

- Source: openspec/changes/suffix-symbol-recall-fix/design.md
- Lines: 1-73
- SHA256: 28767ffeb9a633360879f7945ed379ea5f98d977d58b4e0f366f53b6dd069548

```md
## Context

`_canonical_form`（`rst2md/rag/symbols.py:17-24`）在归一化末尾执行 `name.replace("_", "").replace(".", "")`，把 dot 边界和 underscore 都抹掉。`Symbol.normalized_name` 在索引时由 `extract_symbols` → `normalize_symbol` 写入 DB（`symbols` 表），查询时由 `searcher._search_database_impl` 对 `plan.symbol_candidates` 调用 `normalize_symbol` 后用于 exact/prefix/suffix 三层 LIKE 匹配。

Suffix 层的 LIKE 模式是 `f"%.{normalized}"`（`rst2md/rag/searcher.py:211`），**要求 normalized 形态中含 dot**。但 `_canonical_form` 把 dot 去掉了，所以已索引的 `normalized_name` 永不含 dot，suffix LIKE 永不命中 → suffix recall 是死代码，`symbol_recall.suffix` 信号从未录制（上一轮 change 已用 `@expectedFailure` 锁定该状态，见 `rst2md/tests/test_rag_search.py:1250`）。

`query-rewrite` spec 的 "Query plan signals feed symbol recall and ranking" 要求里已有 `Node.add_child` 这类 dot-notation 候选必须被 exact/suffix lookup 评估的场景，但实现并不满足契约（suffix 永不命中）。本 change 修归一化让 spec 真正成立。

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

## Decisions

### D1：修 `_canonical_form`，保留 dot，继续去 underscore

**选择**：把第 23 行 `name.replace("_", "").replace(".", "")` 改为 `name.replace("_", "")`（只去 underscore，保留 dot）。

**理由**：suffix LIKE `'%.{normalized}'` 的语义就是「按 dot 边界匹配方法后缀」。dot 是符号层级的结构边界（`Class.method`），underscore 只是命名风格（`add_child` ≡ `addchild`）。保留 dot 让 `Node.add_child` → `node.addchild`，suffix 查询 `add_child` → `addchild`，LIKE `%.addchild` 命中。

**对称性**：`normalize_symbol` 在索引（`extract_symbols`）和查询（`searcher` 对 `plan.symbol_candidates`）两侧都被调用，改一处即可，两侧自动一致。

**备选 A：改 LIKE 模式而非归一化**（如改成 `%.{normalized}` 不要求 dot，用其他分隔符）。拒绝——LIKE 模式语义正确，错的是归一化把结构信息丢了；改 LIKE 会引入新分隔符歧义。

**备选 B：两侧都去 dot 且 LIKE 不要求 dot**。拒绝——这正是当前 bug 状态：去 dot 后 `Node.add_child` 与 `Nodeadd_child`、`NodeAdd_Child` 全部塌缩到同一 normalized 形态，suffix 与 prefix 的语义边界消失，召回会引入大量跨类误匹配。

### D2：迁移策略——重建索引

`normalized_name` 是 DB 持久化字段。修了 `_canonical_form` 后，旧 DB 里的 `normalized_name` 仍是 dot-stripped 形态，新查询产生 dot-preserved 形态，两者不匹配。

**处理**：
- 评估 DB 由测试 fixture 重建（`test_search_eval._build_eval_db`），无迁移问题。
- `docs/search-quality/baseline.json` 在 eval 流程里重建 DB 后再生成，自动一致。
- 生产 DB（用户本地）需要重建才能享受修复；`indexer.build_database` 已经调用 `extract_symbols`，重跑 `godot-rag index` 即可。无 schema 变更，无需迁移脚本。

### D3：测试更新清单

- `rst2md/tests/test_rag_symbols.py::test_canonical_dotted`：`"nodeaddchild"` → `"node.addchild"`。
- `rst2md/tests/test_rag_symbols.py::test_normalizes_method_symbols`：`"stringnameisvalidfilename"` → `"stringname.isvalidfilename"`。
- `rst2md/tests/test_rag_search.py::test_suffix_symbol_match_records_signal`：移除 `@expectedFailure`，断言保持不变（query=`"add_child"`，期望命中 `Node.add_child` 并录制 `symbol_recall.suffix` 信号）。
- 其他非 dot-notation 的 canonical 测试（camelCase/snake_case/leading underscore/mixed）输出不变，无需改动。

## Risks / Trade-offs

- **[风险] 修 dot 后 prefix LIKE 行为变化**：`Node` 查询的 prefix LIKE 从 `node%`（匹配 `nodeaddchild`）变成 `node%`（匹配 `node.addchild`，仍命中）。`ResourceLoader` 类前缀同理。实测应在 build 阶段跑 45 查询确认无新误匹配。→ 缓解：baseline comparison 把关，hit@1/hit@5/mrr@5 不得下降。
- **[风险] 两条 gating failure 可能仍未进 `required_at`**：`resource-loader`（query=`ResourceLoader.load`）和 `node-connect-signal`（query=`Node.connect`）当前 `matched=null`。若预期目标在索引里符号名不是 `Class.method` 形态（例如只存了 `load` 或 `connect`），suffix/exact recall 仍可能不命中。→ 缓解：build 阶段先跑 eval 定位预期 chunk 的实际 symbol，再决定是否需追加 alias 或调 query rewrite；若需改 ranking，开下一个 change，不在本 change 内扩范围。
- **[风险] 已发布 DB 与新代码不兼容**：用户升级 `godot-rag` 后不重建 DB，suffix recall 仍失效（但不会崩）。→ 缓解：在 CHANGELOG/release notes 注明「升级后请重建索引」；代码层面无 schema 变更，旧 DB 行为退化到「suffix 不命中」即原本状态，无回归。
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
```

## openspec/changes/suffix-symbol-recall-fix/tasks.md

- Source: openspec/changes/suffix-symbol-recall-fix/tasks.md
- Lines: 1-24
- SHA256: 19646439a594df032ac79acd7e8d75def91daaa6edc9d871275c226bbb08446a

```md
## 1. 修复归一化函数

- [ ] 1.1 修改 `rst2md/rag/symbols.py` 的 `_canonical_form`：去掉 `.replace(".", "")`，只保留 `name.replace("_", "")`，更新 docstring（不再说 "strip ."）。
- [ ] 1.2 更新 `rst2md/tests/test_rag_symbols.py::test_canonical_dotted` 断言：`"nodeaddchild"` → `"node.addchild"`。
- [ ] 1.3 更新 `rst2md/tests/test_rag_symbols.py::test_normalizes_method_symbols` 断言：`"stringnameisvalidfilename"` → `"stringname.isvalidfilename"`。
- [ ] 1.4 确认其余 canonical 测试（camelCase/snake_case/leading_underscore/mixed）输出不变，无需改动。

## 2. 转正 suffix recall 测试

- [ ] 2.1 移除 `rst2md/tests/test_rag_search.py::test_suffix_symbol_match_records_signal` 的 `@unittest.expectedFailure` 装饰器，保留断言不变（query=`add_child`，期望命中 `Node.add_child` 并录制 `symbol_recall.suffix` weight=80.0）。
- [ ] 2.2 更新该测试的 docstring，去掉「Expected failure / deferred to a separate change」措辞，改为说明 suffix recall 现已生效。
- [ ] 2.3 检查 `rst2md/tests/test_rag_search.py` 与 `rst2md/tests/test_searcher_module.py` 中引用 suffix-recall dead-code / xfail 的注释（约 1561、1572 行），更新为已修复状态。

## 3. 验证与 baseline 刷新

- [ ] 3.1 运行 `uv run pytest -q rst2md/tests/test_rag_symbols.py rst2md/tests/test_rag_search.py`，确认 canonical 与 suffix 测试通过。
- [ ] 3.2 运行 `uv run pytest -q` 全套，确认 272 pass（原 271 pass + 1 xfail 转正为 272 pass，无新 fail）。
- [ ] 3.3 运行 eval 刷新 `docs/search-quality/baseline.json`，记录 `resource-loader` / `node-connect-signal` 的 matched_rank 变化。
- [ ] 3.4 baseline comparison：确认 hit@1/hit@5/mrr@5 ≥ 当前（0.763 / 0.895 / 0.805），无新增 gating failure。

## 4. 归档收尾

- [ ] 4.1 在 `CHANGELOG.md` 注明「升级后需重建索引以激活 suffix symbol recall」。
- [ ] 4.2 更新 `WIP.md`：把本 change 移入「已完成的 Comet change」，并根据 baseline 实际结果刷新「下一步方向」（若 `resource-loader`/`node-connect-signal` 仍未进 window，记录后续切入点）。
```

## openspec/changes/suffix-symbol-recall-fix/specs/query-rewrite/spec.md

- Source: openspec/changes/suffix-symbol-recall-fix/specs/query-rewrite/spec.md
- Lines: 1-23
- SHA256: 1f0a46e047e00031b5a8587fea04928ee0a24e30677f7a3431bdd0e7c1f8edb8

```md
## MODIFIED Requirements

### Requirement: Query plan signals feed symbol recall and ranking
Search SHALL use query-plan symbol candidates outside FTS-only recall.

#### Scenario: alias symbol participates in exact symbol lookup
- **WHEN** `search_database` receives "attach node to scene tree"
- **THEN** exact or suffix symbol lookup MUST evaluate the `Node.add_child` query-plan candidate

#### Scenario: alias symbol can influence deterministic reranking
- **WHEN** a result symbol matches a query-plan alias-derived symbol candidate
- **THEN** deterministic reranking MUST be able to promote that result ahead of lower-confidence lexical or vector-only matches

#### Scenario: dot-notation symbol is recalled via suffix match
- **WHEN** `search_database` receives a query whose symbol candidate is a method suffix of an indexed dot-notation symbol (e.g. query `add_child` against indexed `Node.add_child`)
- **THEN** suffix symbol lookup MUST match the indexed `Class.method` symbol
- **AND** the matched candidate MUST record a `symbol_recall.suffix` ranking signal
- **AND** symbol normalization MUST preserve the dot boundary so that the suffix LIKE pattern `%.{normalized}` can match

#### Scenario: dot-notation symbol normalization stays symmetric
- **WHEN** a dot-notation symbol is normalized at index time and at query time
- **THEN** both sides MUST produce the same normalized form with the dot preserved
- **AND** underscore stripping MUST still apply so that `add_child` and `addchild` share one normalized form
```

