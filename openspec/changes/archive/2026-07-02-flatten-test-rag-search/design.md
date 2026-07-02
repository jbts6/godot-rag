## Context

test_rag_search.py 有 26 个类，每个类可能有 `_build_db` 方法创建不同测试数据。扁平化时同名方法会冲突。

## Goals / Non-Goals

**Goals:**
- 扁平化 26 个类为模块级函数
- 重命名 _build_db 为唯一名称
- 减少 200-300 行代码

**Non-Goals:**
- 不改变测试逻辑
- 不删除测试

## Decisions

### 重命名映射

| 类名 | 原方法 | 新名称 |
|------|--------|--------|
| FtsScoreTests | _build_db | _build_fts_score_db |
| FtsEscapeTests | _build_db | _build_fts_escape_db |
| DocTypeFilterTests | _build_db | _build_doctype_db |
| ChunkRelationTests | _build_db | _build_chunk_relation_db |
| GraphExpansionTests | _build_db | _build_graph_expansion_db |
| AddonSearchTests | _build_db | _build_addon_db |
| StatsCommandTests | _build_db | _build_stats_db |
| SnippetTests | _build_db | _build_snippet_db |
| RunSearchTests | _build_db | _build_run_search_db |
| SymbolRecallSignalTests | _build_db | _build_symbol_recall_db |
| RankingSignalCoverageTests | _build_db | _build_ranking_signal_db |
| BuildChunkRelationsCoverageTests | _build_db | _build_chunk_relations_db |
| InheritanceRecallTests | _build_db | _build_inheritance_db |

### 扁平化规则

- `class XxxTests(unittest.TestCase):` → 移除类定义
- `def test_xxx(self):` → `def test_xxx():`
- `self._build_db(tmp)` → `_build_xxx_db(tmp)`
- `self.assertEqual(a, b)` → `assert a == b`（已完成）
- 移除 `import unittest`（如不再需要）

## Risks / Trade-offs

- 风险：重命名遗漏导致 NameError → 逐类迁移，每类测试验证
