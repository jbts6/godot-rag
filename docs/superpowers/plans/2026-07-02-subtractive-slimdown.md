---
change: subtractive-slimdown
design-doc: docs/superpowers/specs/2026-07-02-subtractive-slimdown-design.md
base-ref: 3f5652a65834e56e81f74ce4031f5040bba3c483
archived-with: 2026-07-02-subtractive-slimdown
---

# 纯减法瘦身实施计划

## 基准数据

- 源代码：4096行
- 测试代码：5880行
- 测试数量：302个
- unittest调用：310个（test_rag_addon.py 92、test_rag_search.py 176、test_searcher_module.py 42）

## 任务 1：扩展共享 Fixtures

**文件**：`rst2md/tests/fixtures/common.py`

**操作**：
- 新增 `build_db` fixture：返回构建数据库的工厂函数
- 新增 `tmp_db` fixture：组合 tmp_dir + sample_docs + build_db

**验证**：`uv run pytest -q rst2md/tests/` 通过

## 任务 2：迁移 test_rag_addon.py（92个断言）

**文件**：`rst2md/tests/test_rag_addon.py`（518行）

**操作**：
- 将 59 个 assertEqual → assert ==
- 将 22 个 assertIn → assert in
- 将 6 个 assertNotIn → assert not in
- 将 4 个 assertGreater → assert >
- 将 1 个 assertTrue → assert
- 替换 TemporaryDirectory+build_database 为 fixtures

**验证**：`uv run pytest -q rst2md/tests/test_rag_addon.py` 通过

## 任务 3：迁移 test_searcher_module.py（42个断言）

**文件**：`rst2md/tests/test_searcher_module.py`（625行）

**操作**：
- 将 15 个 assertTrue → assert
- 将 10 个 assertIs → assert is
- 将 8 个 assertEqual → assert ==
- 将 3 个 assertIn → assert in
- 将 3 个 assertFalse → assert not
- 将 2 个 assertAlmostEqual → assert == pytest.approx
- 将 1 个 assertIsInstance → assert isinstance

**验证**：`uv run pytest -q rst2md/tests/test_searcher_module.py` 通过

## 任务 4：迁移 test_rag_search.py（176个self.调用）

**文件**：`rst2md/tests/test_rag_search.py`（1808行）

**操作**：
- 将所有 self.assertEqual/assertIn/assertTrue 等迁移为 pytest assert
- 消除 26 个类定义，扁平化为模块级函数
- 替换 TemporaryDirectory+build_database 为 fixtures

**验证**：`uv run pytest -q rst2md/tests/test_rag_search.py` 通过

## 任务 5：参数化相似测试

**文件**：`rst2md/tests/test_cli_help.py`、`rst2md/tests/test_rag_search.py`

**操作**：
- 识别 CLI 帮助测试中的 4 个相似测试，合并为 1 个 @parametrize
- 识别其他可参数化的测试模式

**验证**：`uv run pytest -q` 通过，测试数量不变或减少

## 任务 6：源码压缩

**文件**：检查所有 rst2md/rag/*.py

**操作**：
- 清理未使用的导入
- 删除注释掉的代码
- 删除空的 except 块等死代码

**验证**：`uv run pytest -q` 通过

## 任务 7：最终验证

**操作**：
- 运行 `uv run pytest -q` 确认全部测试通过
- 统计最终行数，确认目标达成

**目标**：
- 测试代码 < 5000 行
- 源代码 < 3800 行（可选，保守执行）
- unittest 调用 < 50 个
