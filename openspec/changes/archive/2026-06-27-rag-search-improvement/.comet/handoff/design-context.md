# Comet Design Handoff

- Change: rag-search-improvement
- Phase: design
- Mode: compact
- Context hash: fdc2d062aa2f8cbcfaf0b6af94dad40e4c4f72cd090cc0d043a98059a566615e

Generated-by: comet-handoff.sh

OpenSpec remains the canonical capability spec. This handoff is a deterministic, source-traceable context pack, not an agent-authored summary.

## openspec/changes/rag-search-improvement/proposal.md

- Source: openspec/changes/rag-search-improvement/proposal.md
- Lines: 1-42
- SHA256: 37f0b31a68f591092daf0f1397b716dd22db82f552052429a279087cb5d7f187

```md
# RAG 搜索质量提升

## 问题

当前 RAG 搜索系统存在以下问题，影响搜索质量：

1. **符号匹配过于粗糙** — `normalize_symbol` 只做 `lowercase + strip "()"`，无法处理 camelCase/snake_case 变体
2. **BM25 分数映射缺乏校准** — `* 0.1` 系数是拍脑袋的，符号层(100/80/40)和 FTS 层(0-40)有巨大断层
3. **chunk 之间无关联** — 命中 method chunk 时无法自动附带 class_summary，缺少继承链、交叉引用等上下文
4. **FTS 查询处理太保守** — 特殊字符全部转义导致含 `.` 的符号查询无法正确分词

## 目标

提升 RAG 搜索的召回率和结果质量，具体指标：
- 符号模糊查询命中率提升
- 搜索结果包含上下文关联信息
- BM25 分数分布合理，不再与符号匹配层断层

## 范围

分 3 个 Phase 实施：

### Phase 1: 基础优化（低复杂度）
- 符号 normalize 增强（去 `_`、camelCase 拆分）
- BM25 分数映射校准（统计实际分布后重设公式）

### Phase 2: 图谱核心（中复杂度）
- `chunk_relations` 表 + 建图逻辑
- parent 关系（chunker 已有信息）
- inherits 关系（正则提取继承链）
- references 关系（FTS 交叉匹配）

### Phase 3: 检索增强（中复杂度）
- 图谱遍历查询（命中 → 关联扩展）
- FTS 查询分词优化
- 分数体系统一（主结果 + 图谱结果融合排序）

## 不在范围内

- 向量嵌入/语义搜索（需引入外部依赖）
- chunk 大小控制/二次切分（独立改进项）
- 静态热度权重（需要使用数据，暂无来源）
```

## openspec/changes/rag-search-improvement/design.md

- Source: openspec/changes/rag-search-improvement/design.md
- Lines: 1-12
- SHA256: 317490450ce7966d4489889eada41dbda941df10a6518367dfab343fe21f1337

```md
# Design: RAG 搜索质量提升

> 设计阶段产物，brainstorming 后填充。

## 待设计

- [ ] 符号 normalize 增强方案
- [ ] BM25 分数映射校准方案
- [ ] chunk_relations 表结构与建图逻辑
- [ ] 图谱遍历查询接口
- [ ] FTS 查询分词优化方案
- [ ] 分数体系统一方案
```

## openspec/changes/rag-search-improvement/tasks.md

- Source: openspec/changes/rag-search-improvement/tasks.md
- Lines: 1-25
- SHA256: 75df72cbc141b5bea595a02f05a7d43b5ea82f7373b0c360c3aa4e35f27a32c6

```md
# Tasks: RAG 搜索质量提升

> 设计完成后细化任务列表。

## Phase 1: 基础优化

- [ ] 1.1 增强 `normalize_symbol`：支持 camelCase 拆分、去 `_` 模糊匹配
- [ ] 1.2 统计 BM25 原始值分布，校准分数映射公式
- [ ] 1.3 更新测试用例

## Phase 2: 图谱核心

- [ ] 2.1 设计并创建 `chunk_relations` 表
- [ ] 2.2 实现 parent 关系建图（chunker 阶段）
- [ ] 2.3 实现 inherits 关系建图（正则提取继承链）
- [ ] 2.4 实现 references 关系建图（FTS 交叉匹配）
- [ ] 2.5 更新测试用例

## Phase 3: 检索增强

- [ ] 3.1 实现图谱遍历查询（命中 top-K → 关联扩展）
- [ ] 3.2 优化 FTS 查询分词（拆 token、处理 `.` 分隔符）
- [ ] 3.3 统一分数体系（主结果 + 图谱结果融合排序）
- [ ] 3.4 CLI 输出增加 relation_type 字段
- [ ] 3.5 更新测试用例
```

