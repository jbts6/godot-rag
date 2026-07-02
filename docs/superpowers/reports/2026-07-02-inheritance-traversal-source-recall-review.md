# Change Review: inheritance-traversal-source-recall

**归档日期**: 2026-07-02
**Workflow**: full
**改动规模**: 21 files, 13 commits (base-ref: 9137b74)

## 审查摘要

| 维度 | 状态 | 关键发现 |
|------|------|---------|
| Spec 合并完整性 | ✅ PASS | 主 spec 含 4 个场景，recall 前置条件已合并，无 delta-only 标题残留 |
| 设计-实施对齐 | ✅ PASS | D1-D4 全部遵循，无偏离 |
| 漂移分析 | ✅ PASS | 10/10 任务完成，proposal 目标全部达成，无范围膨胀 |
| 代码质量 | ✅ PASS | 无 TODO/FIXME/HACK，+49 行 searcher.py，遵循现有模式 |
| 过程质量 | ✅ NOTE | full workflow 合理，TDD 完整，standard review 模式，13 提交粒度清晰 |

## 详细发现

### Spec 合并完整性

**PASS**

- 主 spec `openspec/specs/intent-ranking/spec.md` 的 "Inheritance relation traversal in search" 需求（lines 158-188）已包含 delta spec 声明的全部修改：
  - recall 前置条件段落（lines 160-162）
  - Scenario 1: recall target class_summary（lines 164-169）
  - Scenario 2: recall parent class_summary（lines 171-176）
  - Scenario 3: scoped to inherits relation（lines 178-182）
  - Scenario 4: no edge doesn't crash（lines 184-188）
- 无 `ADDED:`/`MODIFIED:`/`REMOVED:`/`RENAMED:` 残留标题
- 合并后主 spec 自洽，无断裂段落或重复内容

### 设计-实施对齐

**PASS**

| 设计决策 | 实施位置 | 偏离 |
|---------|---------|------|
| D1: PascalCase + DB 验证 | `searcher.py:265-284`（regex + `WHERE c.symbol=? AND c.chunk_type='class_summary'`） | 无 |
| D2: step 3.5 位置（symbol recall 后、FTS 前） | `searcher.py:249-305`（prefix 信号块与 FTS 注释之间） | 无 |
| D3: score 90.0 + 信号 `inheritance_recall.class_summary` | `searcher.py:265-284`（`recall_score = 90.0`，`name="inheritance_recall.class_summary"`） | 无 |
| D4: `plan.inheritance_intent` 门控 | `searcher.py:249`（`if plan.inheritance_intent:`） | 无 |

- 隐式决策：`seen_classes` 去重（防止同一类名多次查询 DB）— 合理，无需 design.md 覆盖
- 隐式决策：`c.*` / `c.symbol` 别名与 `type_filter` / `addon_filter` 兼容 — 已在 plan 中记录

### 漂移分析

**PASS**

- **任务完成度**：10/10 全部 ✅
- **Proposal 目标达成**：
  - `Node inherits Object` rank=None → rank=1（目标 ≤ 5）✅
  - Hit@5 ≥ 97.37%（实际 97.37%）✅
  - MRR@5 ≥ 87.50%（实际 90.13%）✅
  - 32 原通过查询零回归 ✅
- **范围膨胀**：计划改动 5-6 文件，实际改动 6 文件（searcher.py + test_rag_search.py + 4 baseline JSON）— 无膨胀
- **未完成任务**：无
- **范围外发现**：review 阶段发现的 test_searcher_module.py 弱断言 + 过时注释（loop-2 遗留）— 已顺手修复，不属本 change 范围但合理附带

### 代码质量

**PASS**

- **TODO/FIXME/HACK**：无残留
- **导入**：`import re` 新增，其余复用既有导入，无未使用导入
- **代码量**：searcher.py +49 行（step 3.5 召回块 + regex 常量），test_rag_search.py +103 行（2 个测试 + 辅助函数）
- **模式一致性**：复用 `_make_result` / `_record_signal` / `RankingSignal` 模式，与 symbol recall 风格一致
- **错误处理**：DB 查询返回空集时安全跳过，无需额外错误处理
- **边界条件**：`seen_classes` 去重、`if cid not in results or results[cid]["score"] < recall_score` 高分更新逻辑正确

### 过程质量

**NOTE**

- **Workflow 选择**：full 合理（10 任务，20 文件，跨模块协调）
- **TDD 纪律**：完整 Red → Green → 回归 → eval 流程，RED/GREEN 证据齐全
- **Review 模式**：standard（无 per-task reviewer，一次 final lightweight reviewer）— 合适
- **Commit 粒度**：13 提交，每任务 2 提交（checkoff + 实现）+ 基线/归档 — 清晰可追溯
- **Verify 阶段**：首次通过，无失败记录
- **范围扩张**：无（未触发 50% 阈值或 spec 增量更新）

## 经验教训

### 做得好

- **TDD Red 锚点设计**：用 `inheritance_recall.class_summary` 信号断言作为 Red 锚点（而非 Node/Object 是否在 top-5），确保 Red 失败原因精确指向 step 3.5 缺失
- **Noise DB 复现生产 gap**：ScrollBar/Slider/PopupPanel 的继承链文本含 Node+Object，精准复现 FTS 淹没问题
- **阶段基线锁定**：stage-0 和 final 基线分开锁定，eval 对比证据完整
- **Comet 状态机追踪**：每个 task 的 checkoff、commit、RED/GREEN 证据均有记录，断点恢复可靠

### 下次改进

- **Plan 中 `rtk` 前缀**：plan 命令使用 `rtk` 前缀，subagent 需要自行判断是否使用。建议 plan 统一使用裸命令或明确标注 `rtk` 用途
- **Task 3 subagent 首次失败**：返回空结果，report 文件残留旧变更内容。原因可能是 subagent 上下文不足或超时。建议为操作型任务（eval + commit）提供更简洁的 dispatch prompt

### 模式识别

- **"Feature works in tests but silent in production" 模式**：unit test 使用小 DB（无 noise），生产 DB 有大量噪声 chunks 导致排名变化。教训：集成测试应包含 noise 数据以复现生产动态
- **FTS score cap 平局问题**：所有负 bm25 匹配达到 40.0 上限，FTS 无法区分。这不仅影响 inheritance 查询，可能影响其他高召回场景。值得后续评估是否调整 FTS score 公式
