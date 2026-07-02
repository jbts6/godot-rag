---
comet_change: flatten-test-rag-search
role: technical-design
canonical_spec: openspec
archived-with: 2026-07-02-flatten-test-rag-search
status: final
---

# 扁平化 test_rag_search.py Design Doc

## Context

test_rag_search.py 有 26 个类、13 个 `_build_db` 方法。上次瘦身因命名冲突无法扁平化。

## 决策：重命名 + 扁平化

1. 将 13 个 `_build_db` 重命名为唯一名称
2. 扁平化 26 个类为模块级函数
3. 移除 `import unittest`

## 重命名映射

- FtsScoreTests._build_db → _build_fts_score_db
- FtsEscapeTests._build_db → _build_fts_escape_db
- DocTypeFilterTests._build_db → _build_doctype_db
- ChunkRelationTests._build_db → _build_chunk_relation_db
- GraphExpansionTests._build_db → _build_graph_expansion_db
- AddonSearchTests._build_db → _build_addon_db
- StatsCommandTests._build_db → _build_stats_db
- SnippetTests._build_db → _build_snippet_db
- RunSearchTests._build_db → _build_run_search_db
- SymbolRecallSignalTests._build_db → _build_symbol_recall_db
- RankingSignalCoverageTests._build_db → _build_ranking_signal_db
- BuildChunkRelationsCoverageTests._build_db → _build_chunk_relations_db
- InheritanceRecallTests._build_db → _build_inheritance_db

## 执行顺序

1. 重命名 _build_db 方法
2. 更新所有调用
3. 扁平化类
4. 验证测试通过
