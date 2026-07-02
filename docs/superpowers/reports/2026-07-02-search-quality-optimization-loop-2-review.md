# Change Review: search-quality-optimization-loop-2

**归档日期**: 2026-07-02
**Workflow**: full
**改动规模**: 29 文件（4 生产 `rst2md/rag/` + 2 测试 `rst2md/tests/` + 6 eval JSON + 17 change/spec/docs 产物），+31226/-1237 行；54 提交（6 feat / 6 test / 38 chore / 2 docs / 1 merge / 1 fix）
**Base-ref**: `5b5161c..HEAD`（已合并 main）

## 审查摘要

| 维度 | 状态 | 关键发现 |
|------|------|---------|
| Spec 合并完整性 | PASS | 主 spec 0 个 delta-only 残留标题；6 个 delta requirement 全部体现在主 spec；自洽 |
| 设计-实施对齐 | PASS | design.md 6 项决策全部遵循；design doc 3 项 修订 均带 spec patch；4 项实施偏离全部文档化并接受 |
| 漂移分析 | NOTE | 整体目标超额达成（Hit@5 +7.89pp vs +4.5pp 目标），但 6 个失败查询只修了 3 个（目标 ≥5）；2 个失败有根因记录 |
| 代码质量 | PASS | rst2md/rag 无 TODO/FIXME/HACK；290/0 全套通过；3 项 SUGGESTION 非阻塞 |
| 过程质量 | NOTE | full workflow 合适；TDD 每任务 RED/GREEN；但 38 个 `chore(comet): check off` 提交造成 git log 噪音 |

## 详细发现

### Spec 合并完整性 — PASS

- 主 spec `openspec/specs/intent-ranking/spec.md` 与 `openspec/specs/query-rewrite/spec.md` 中 `ADDED/MODIFIED/REMOVED/RENAMED:` delta-only 标题残留 = **0**（归档脚本校验通过）。
- delta spec 声明的 6 个 requirement 全部体现在主 spec：
  - `intent-ranking` delta 4 个 requirement（Tutorial intent detection / Deterministic reranking uses query-plan signals / Inheritance intent detection / Inheritance relation traversal in search）→ 主 spec 全部命中。
  - `query-rewrite` delta 2 个 requirement（Conservative query alias expansion / Query plan exposes structured search intent）→ 主 spec 全部命中。
- 主 spec 自洽：无断裂段落、无重复内容。`intent-ranking` 主 spec 现 8 个 requirement（含本次新增 2 个 inheritance requirement），`query-rewrite` 主 spec 现 4 个 requirement（含本次修订的 dot-notation 拆分场景）。

### 设计-实施对齐 — PASS

design.md（archive）的 6 项决策 + design doc（superpowers）的 3 项修订全部落实：

**design.md 决策**：
1. **A1**：`expand_query_variants` 拆分点号查询 → `query_rewrite.py` 实现 `Class.method` → method-suffix variant。✓
2. **A2**：防止 over-split 误伤 → 大写开头 + 小写开头守卫，`scene_tree.tutorial` 不拆。✓
3. **B1**：Tutorial 改 additive 为 multiplicative → `_rerank_bonus` 实现 `max(score, FLOOR) * (FACTOR - 1)`。✓
4. **B2**：防止 class 查询被 tutorial intent 误伤 → `doc_type_boost` 退役为 0.0，symbol 候选存在时不触发。✓
5. **C1**：继承 intent 检测 + 定向 inherits 遍历 → `_inheritance_intent` 4 关键词 + `searcher.py` 定向 SQL。✓
6. **C2**：补 `build_chunk_relations` 覆盖测试 → `test_searcher_module.py` 新增直接覆盖。✓

**design doc 修订**（设计层变更，带 spec patch）：
- 修订 1（B 段）：tutorial boost 改"地板 + multiplicative" → spec 同步更新。✓
- 修订 2（A 段）：短方法名不加守卫 → spec 不变（与 design.md 一致）。✓
- 修订 3（C 段）：inheritance intent 去掉 `extends` 关键词 → spec 关键词从 5 词改 4 词 + 新增"bare verb extends does not trigger"场景。✓

**实施偏离项**（verification report 记录 4 项，均有正当理由，全部接受）：
1. **B.2 regex `\(?\)?`**：plan regex 不匹配右括号，修复以匹配 `ResourceLoader.load()`。
2. **B.2 `_ALIAS_FORMS` guard**：plan 代码会破坏 dedup 测试，加 guard 跳过 alias canonical forms。
3. **B.2 dead guard removal**：`not plan.symbol_candidates` 永远为 False（死代码），移除以启用 floor formula；symbol 查询由 `_doc_type_intent` 返回 None 保护。
4. **C.6 `_record_signal` for existing results**：generic graph expansion 先跑会把 Object 拉入 `expanded_ids`，inherits 分支用 `_record_signal` 追加 `graph.inherits` 信号而非跳过。

**无隐式决策**：所有偏离都在 commit message、tasks.md 或 verification report 中记录。

### 漂移分析 — NOTE

- **proposal 目标收敛**：4 项原始目标达成情况：
  - **A 段（ResourceLoader.load / Node.connect 命中 rank ≤3；symbol hit@5 80%→90%+）**：symbol hit@5 92.11%→97.37% ✓；但 `ResourceLoader.load` 仍失败（与 `@GDScript.load`/`Image.load` 竞争）✗。
  - **B 段（tutorial hit@5 71%→100%）**：✓ 完全达成（tutorial 100%）。
  - **C 段（Node inherits Object 命中 rank ≤5；class hit@5 保持 100%）**：class hit@5 100% 维持 ✓；但 `Node inherits Object` 仍 rank=None（source chunk 不在 top-K，inherits 遍历无法触发）✗。
  - **整体（Hit@5 89.5%→94%+，MRR@5 80.5%→85%+，32 个原通过查询不回归）**：Hit@5 89.47%→97.37%（+7.89pp，目标 +4.5pp ✓ 超额）；MRR@5 80.48%→87.50%（+7.02pp，目标 +4.5pp ✓ 超额）；无回归 ✓。
- **tasks.md**：32/32 `[x]`，无 `- [ ]` 残留，无"标完成但未实现"项。
- **失败查询修复**：6 → 3（3/6 fixed，目标 ≥5/6）— **部分未达标**。3 个未修失败：
  - `ResourceLoader.load`：score 竞争（WARNING 1 记录）。
  - `Node inherits Object`：source chunk 不在 top-K，inherits 遍历无法触发（WARNING 2 记录，留作 future loop）。
  - 1 个 report_only failure（未在本 change 范围）。
- **范围**：实际改动 4 生产 + 2 测试 = 6 个 `rst2md/` 文件 = proposal "Affected code" 列出的预期。无范围膨胀。其余 23 文件为 eval JSON 基线（6）+ change/spec/docs 产物（17），非代码膨胀。

### 代码质量 — PASS

- `rst2md/rag/` 4 个改动文件（fusion.py / query_plan.py / query_rewrite.py / searcher.py）无 `TODO`/`FIXME`/`HACK`/`XXX` 残留。
- 全套测试 290/0 通过（含 6 个新 requirement、23 个新 scenario 覆盖）。
- 错误处理一致：`_record_signal` 统一 append 模式；rerank 用 list-copy 保护；`doc_type_boost` 退役但保留向后兼容。
- 3 项 SUGGESTION（非阻塞，verify 阶段已记录）：
  1. `test_rerank_bonus_no_tutorial_boost_when_symbol_candidates` 弱断言：`assertNotIn("tutorial", str(float))` 永真，应为 `assertEqual(bonus, 0.0)`。
  2. Inherits SQL 无 LIMIT（Godot 继承 1:1，无实际影响）。
  3. 两个 rerank 测试注释陈旧（提及已移除的 `not plan.symbol_candidates` guard）。

### 过程质量 — NOTE

- **workflow=full** 合适（3 段 × 多任务、新 capability、多模块改动）。
- **未触发升级条件**：三段串行按 plan 推进，每段后锁定增量基线，无范围扩张。
- **TDD**：每任务 RED/GREEN 证据齐全（commit log 可见 `test(...)` Red → `feat(...)` Green → `chore(comet): check off` 三拍）；`tdd_mode: tdd` 贯彻。
- **build_mode=subagent-driven-development**：主 session 上下文干净，subagent-progress.md 跟踪每段完成状态。
- **verify**：一次通过（`verify_result: pass`，2 WARNING + 3 SUGGESTION，无 CRITICAL）。
- **3 个 Open Question 全部在 verify-prep.md 答复**：FLOOR/FACTOR 最终值（3.0/5.0）、Inherits 行格式确认（`**Inherits:** \`X\``）、A 段回归检查结果（无回归）。
- **提交粒度**：6 feat + 6 test + 1 fix = 13 个实质提交（每任务一次 Red/Green），合理。
- **⚠️ 反模式：38 个 `chore(comet): check off X.Y` 提交**：
  - 每完成一个任务子项就一次 chore 提交勾选 tasks.md，造成 git log 噪音（54 提交中 38 个是 checkoff）。
  - 建议：将 task 勾选合并进对应的 feat/test 提交，或批量勾选（如每段结束一次）。

## 经验教训

- **做得好**：
  - **三段增量基线锁定**（stage-0/A/B/C/final JSON）提供清晰归因：每段改动对 Hit@5/MRR@5 的贡献可量化（A 段 +2.6pp、B 段 +5.26pp、C 段持平）。该模式可直接复用到任何多阶段排序改动。
  - **design doc 修订机制**：3 项设计层变更（修订 1/2/3）在 build 阶段发现后正式记录，每项带 spec patch，确保 spec 与最终决策一致。
  - **binding constraints 全程守住**：未动向量模型、RRF k=60、未引入 LLM reranker、未重构 searcher 主流程、未改 chunker schema、未新增 eval 查询。
  - **TDD + subagent dispatch** 保持主 session 上下文干净；Red/Green 证据齐全。
  - **整体目标超额达成**：Hit@5 +7.89pp（目标 +4.5pp）、MRR@5 +7.02pp（目标 +4.5pp）。

- **下次改进**：
  - **task checkoff 提交策略**：38 个 `chore(comet): check off` 提交是 git log 噪音。建议将 tasks.md 勾选合并进 feat/test 提交（commit 同时改代码 + 勾选任务），或每段结束批量勾选一次。
  - **弱断言应被 TDD Red 阶段抓住**：`assertNotIn("tutorial", str(float))` 永真，意味着 Red 阶段该测试不会 fail。TDD Red 阶段应验证测试"按预期失败"，而非仅"有失败"。
  - **未修失败应主动开跟踪**：`ResourceLoader.load`（score 竞争）和 `Node inherits Object`（source chunk 不在 top-K）有根因记录但无跟踪 issue。建议归档后开 future change 提案，避免遗忘。`Node inherits Object` 尤其值得注意：C 段 feature 在单元测试中 PASS 但生产查询不触发（source chunk 缺席），存在"单元测试绿但集成无效"的盲区。
  - **设计-实施偏离计数表述不一致**：design doc 有 3 项"修订"，verification report 说"4 documented deviations"——前者是设计层修订，后者是实施层偏离，语义不同但易混淆。建议 verify 报告明确区分"design revisions"与"implementation deviations"。

- **模式识别**：
  - **可复用模式**：
    - "Stage-gated eval baseline"（stage-N.json 增量基线）—— 任何多阶段排序改动都可套用。
    - "Floor + multiplicative boost"（`max(score, FLOOR) * (FACTOR - 1)`）—— 低分相关结果救起的通用公式。
    - "Intent-gated relation traversal"（intent 检测 → 定向 SQL `r.relation = 'X'` 过滤）—— 可扩展到 `references`/`see_also` 等其他关系类型。
  - **反模式**：
    - "chore commit per task checkoff"—— 造成 git log 噪音，应折叠进实质提交。
    - "Unit test green but integration silent"—— C 段 inherits 遍历单元测试 PASS 但生产查询因 source chunk 缺席无法触发；集成层验证不能只靠 unit test。
