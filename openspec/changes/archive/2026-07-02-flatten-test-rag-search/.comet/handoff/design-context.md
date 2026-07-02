# Comet Design Handoff

- Change: flatten-test-rag-search
- Phase: design
- Mode: compact
- Context hash: f5ad475a2c04f0046f3502b8267e1972bdc0cda39a4df532a5515943308590bf

Generated-by: comet-handoff.sh

OpenSpec remains the canonical capability spec. This handoff is a deterministic, source-traceable context pack, not an agent-authored summary.

## openspec/changes/flatten-test-rag-search/proposal.md

- Source: openspec/changes/flatten-test-rag-search/proposal.md
- Lines: 1-26
- SHA256: 26bcb6ea35e40f8e28384d9f850fd932f15654f79c865ade6590f6ac49207a93

```md
## Why

test_rag_search.py 是项目最大测试文件（1786行，26个类）。上次瘦身因 `_build_db` 命名冲突无法扁平化。本次通过重命名为唯一名称后扁平化，预计减少 200-300 行。

## What Changes

- 将 13 个 `_build_db` 方法重命名为唯一名称（如 `_build_fts_db`、`_build_escape_db`）
- 将 26 个 unittest.TestCase 类扁平化为模块级函数
- 提取重复的 TemporaryDirectory+build_database 为共享 fixtures

**不做**：不改变测试逻辑、不删除测试、不改变断言

## Capabilities

### New Capabilities

无

### Modified Capabilities

无

## Impact

- 仅影响 rst2md/tests/test_rag_search.py
- 无 API 变更
```

## openspec/changes/flatten-test-rag-search/design.md

- Source: openspec/changes/flatten-test-rag-search/design.md
- Lines: 1-46
- SHA256: ef2bc03b7458920282a45830e90e173c470484202a34917c679ad9dedc6a53cc

```md
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
```

## openspec/changes/flatten-test-rag-search/tasks.md

- Source: openspec/changes/flatten-test-rag-search/tasks.md
- Lines: 1-15
- SHA256: c994a9f4a2c0eb20acd4bad1415306822f3caf08e82f382eaf9bd0d8ef17bee2

```md
## 1. 重命名 _build_db 方法

- [ ] 1.1 将 13 个 _build_db 重命名为唯一名称
- [ ] 1.2 更新所有 self._build_db 调用为新名称

## 2. 扁平化类

- [ ] 2.1 移除类定义，扁平化为模块级函数
- [ ] 2.2 移除 self 参数
- [ ] 2.3 清理 import unittest

## 3. 验证

- [ ] 3.1 运行测试确保 76 个测试全部通过
- [ ] 3.2 统计行数变化
```

