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
