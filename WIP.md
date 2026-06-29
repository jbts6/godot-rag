# WIP

本文件记录下一步主要工作。细节进入 Comet change 后，以对应 `openspec/changes/<change>/` 为准。

## 当前优先方向：搜索质量优化闭环

目标：先让搜索质量、速度和稳定性变化能被可靠测出来，再安全调整检索策略和代码结构。

### 1. 扩搜索质量评估集 ✅ 已打开

- 将 gating queries 从当前的小集合扩到覆盖 40-60 条稳定场景。
- 覆盖符号 alias、自然语言教程、addon API、engine 概念、camelCase/snake_case/dotted symbol、graph expansion 等场景。
- 增加负例和精确性检查：addon filter 不串库，class/tutorial/engine/addon 类型不互相污染。

### 2. 加入速度与稳定性基准 ✅ 已打开

- 在 `eval-search` 或相邻命令中报告 p50/p95、冷启动/热查询、FTS-only/hybrid 模式指标。
- 把 vector fallback reason 和 degraded 状态纳入 regression 保护。
- 将搜索质量命令接入常规验证路径，而不只依赖 `pytest`。

### 3. 等价拆分搜索器结构

- 拆分 `rst2md/rag/searcher.py` 中的 query planning、candidate retrieval、fusion/rerank、graph expansion、result formatting。
- 第一阶段只做行为等价重构，不改变排名。
- 用扩充后的质量和速度测试护住重构。

### 4. 搜索策略优化

- 扩展 alias/query rewrite 机制，减少硬编码孤例。
- 强化符号查询的精确优先级，让 `Node.add_child`、`addChild`、`node_add_child` 稳定命中同一族目标。
- 让 tutorial/addon/engine intent scoring 更可解释，并在诊断输出中展示命中原因。

## 已打开的 Comet change

- 名称：`search-quality-evaluation-expansion`
- 状态：实施中（Task 1-3 已完成，Task 4 进行中）
- 范围：评估集扩容、速度/稳定性指标设计、搜索器等价拆分的前置验证边界。
- 非目标：本 change 不直接大幅调整 ranking 权重，不更换 embedding 模型，不改变数据库 schema。
