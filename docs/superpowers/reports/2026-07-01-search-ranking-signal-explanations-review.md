# Change Review: search-ranking-signal-explanations

**归档日期**: 2026-07-01
**Workflow**: full
**改动规模**: 6 个 `rst2md/` 文件（4 生产 + 2 测试），+969/-12 行；8 个 feat/test 提交（每任务一次）+ 最终修复提交
**Base-ref**: fb5491a..HEAD（已合并 main）

## 审查摘要

| 维度 | 状态 | 关键发现 |
|------|------|---------|
| Spec 合并完整性 | PASS | 主 spec 0 个 delta-only 残留标题；intent-ranking 从 3 → 6 requirements；自洽 |
| 设计-实施对齐 | PASS | design.md 4 项决策全部遵循；2 个延后项已文档化（suffix 死代码、_rerank_bonus guard） |
| 漂移分析 | PASS | proposal 目标全部收敛；tasks 14/14 完成，无跳过/残留；实际 6 文件 = 计划预期，无膨胀 |
| 代码质量 | PASS | rst2md/rag 无 TODO/FIXME/HACK；无新增死代码（suffix 录制为 dormant 非 dead-on-arrival） |
| 过程质量 | NOTE | full workflow 合适；TDD 每任务 RED/GREEN；提交粒度优；但 5/7 任务 plan 的测试数据有缺陷 |

## 详细发现

### Spec 合并完整性 — PASS

- 主 spec `openspec/specs/intent-ranking/spec.md` 中 `## ADDED/MODIFIED/REMOVED/RENAMED` delta-only 标题残留 = **0**（归档脚本校验通过）。
- delta spec 声明的 3 个 requirement 全部体现在主 spec（主 spec 现 6 个 requirement，含本次新增的 "Search results expose ranking signal explanations" / "Ranking explanations preserve search API compatibility" / "CLI and diagnostics can display ranking explanations"）。
- 主 spec 自洽，无断裂段落或重复内容。

### 设计-实施对齐 — PASS

design.md 的 4 项高层决策全部落实：
1. "Add a structured signal model" → `RankingSignal` frozen dataclass（`models.py`）。✓
2. "Record signals during candidate assembly, not after" → `_make_result`/`_record_signal` 贯穿 searcher 各阶段。✓
3. "Make reranking return explainable adjustments" → `_rerank_signals` + list-copy（`fusion.py`）。✓
4. "Keep compatibility by using additive model fields" → `ranking_signals` 为末字段 + `field(default_factory=list)`。✓

**偏离项（均有正当理由，已文档化）**：
- suffix-recall 死代码：`_canonical_form` 剥点导致 suffix LIKE 永不匹配。design.md "Deferred Issues" 节记录延后（修复会改排序，违反约束）。`test_suffix` 标 `@unittest.expectedFailure`。
- 可能的 `_rerank_bonus` guard 预存问题：`not plan.symbol_candidates` 可能本意只针对点号符号。超出范围（约束禁止改 `_rerank_bonus`），flagged for separate change。
- **无隐式决策**：所有偏离都在 commit message 或 design.md 中记录。

### 漂移分析 — PASS

- **proposal 目标收敛**：4 项原始目标（结构化信号解释、保留 `search_database()` 兼容、覆盖全信号族、测试可断言命名信号）全部达成。
- **tasks.md**：14/14 `[x]`，无 `- [ ]` 残留，无"标完成但未实现"项。
- **范围**：实际改动 6 个 `rst2md/` 文件（models/searcher/fusion/cli + 2 测试）= proposal "Affected code" 列出的预期。无范围膨胀。（早期 diff stat 显示 90 文件含用户的 f4d3ce9 skill 提交 + change 产物，非代码膨胀。）

### 代码质量 — PASS

- `rst2md/rag/` 无 `TODO`/`FIXME`/`HACK`/`XXX` 残留。
- 无新增死代码：`symbol_recall.suffix` 录制代码 dormant（tier 当前死，但代码正确，bug 修复后自动生效），非 dead-on-arrival。
- 错误处理一致：信号录制用 `_record_signal` 统一 append，prior-signal 保留用 `list(ranking_signals or [])` 模式。
- rerank list-copy 正确（`list(result.ranking_signals)` 浅拷贝 + frozen dataclass 不可变，安全），有非变更测试守护。
- JSON-friendliness：所有 `value`/`details` 类型符合约束（Minor：`details: dict[str, object]` 类型注解比约束略松，但不影响运行）。

### 过程质量 — NOTE

- **workflow=full** 合适（14 任务、新 API 表面、多模块）。
- **未触发升级条件**。
- **TDD**：每任务 RED/GREEN 证据齐全；`tdd_mode: tdd` 贯彻。
- **提交粒度**：8 个 feat/test 提交（每任务一次）+ 1 最终修复提交 + 若干 chore 提交。合理。
- **verify**：一次通过（build 阶段已做最终审查 + 1 轮修复）。
- **dirty-worktree 协议**：成功归因用户的 f4d3ce9 skill 提交 + AGENTS/CLAUDE 改动，未污染 change。
- **⚠️ 反模式：5/7 任务的 plan 测试数据有缺陷**
  - Task 2：suffix 测试假设死代码 tier 能触发。
  - Task 3：mock `return_value=[[0.0]*256]` 对 N chunks 只返回 1 embedding。
  - Task 4：fixture 太少（top_k 全收入 expanded_ids）+ query 不匹配 class_summary + 缺 mock。
  - Task 5：doc_type_intent 测试用 `build_query_plan`（总是非空 symbol_candidates，阻塞 guard）。
  - Task 7：required 含死代码 suffix + 查询在 sqlite-vec 环境不触发 FTS/graph fallback。
  - 全部由 implementer test-only 修复，**生产代码 byte-for-byte 等于 plan**。

## 经验教训

- **做得好**：
  - TDD 每任务 RED/GREEN 证据 + subagent-driven dispatch 保持主 session 上下文干净。
  - binding constraints（不改排序数学/排序、源兼容）全程守住；rerank list-copy 有非变更测试守护。
  - 最终审查抓住真实测试加固缺口（sync guard 只覆盖 1/4 分支、覆盖测试名不副实），1 轮修复闭环。
  - dirty-worktree 协议 + 决策点协议正确拦截了用户的不相关提交和 plan-vs-constraint 冲突（suffix 死代码）。

- **下次改进**：
  - **Plan 生成应校验测试数据**：5/7 任务的 plan 生产代码 byte-for-byte 正确，但测试数据反复出错。根因：plan 作者按设计写生产代码（对），但按假设写测试数据（错——未验证 sqlite-vec 环境行为、`normalize_symbol` 剥点、`build_query_plan` 总含原 query）。建议 plan 生成加一步"针对当前代码跑测试确认按预期 fail"，或在 plan 中标注"测试数据需 implementer 按实际 env 校准"。
  - **预存 bug 发现应主动 flag**：suffix 死代码是 plan 测试暴露的预存 ranking bug。本次正确延后，但应在归档后主动开一个跟踪 issue / 新 change 提案，避免遗忘。

- **模式识别**：
  - **"生产代码对，测试数据错"** 是可复用模式——plan 从 design doc 推导生产代码通常准，但测试数据依赖运行时 env 细节（向量可用性、normalize 行为、query plan 候选生成），plan 作者若不实测就会错。缓解：plan 生成时对每个测试用例跑一次"确认按预期 fail"的 smoke check，或明确指示 implementer 把测试数据视为待校准。
  - **dormant 代码 + xfail + 延后 change** 是处理"测试暴露预存 bug 但修复超范围"的有效三件套——保留正确代码、文档化 bug、不阻塞当前 change。
