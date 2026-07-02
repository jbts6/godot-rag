## 1. 扩展共享 Fixtures

- [x] 1.1 扩展 rst2md/tests/fixtures/common.py：新增 build_db 和 tmp_db fixtures
- [x] 1.2 在 test_rag_addon.py 中使用 tmp_db fixture 替换重复的 TemporaryDirectory+build_database

## 2. 迁移 unittest 断言（test_rag_addon.py）

- [x] 2.1 将 test_rag_addon.py 中 92 个 unittest 断言迁移为 pytest assert
- [x] 2.2 移除 test_rag_addon.py 中的 unittest.TestCase 继承（如适用）

## 3. 迁移 unittest 断言（test_searcher_module.py）

- [x] 3.1 将 test_searcher_module.py 中 42 个 unittest 断言迁移为 pytest assert

## 4. 迁移 unittest 断言（test_rag_search.py）

- [x] 4.1 将 test_rag_search.py 中 176 个 self. 调用迁移为 pytest assert
- [x] 4.2 消除 test_rag_search.py 中的类定义（26个类 → 扁平化）

## 5. 参数化相似测试

- [x] 5.1 参数化 CLI 帮助测试（test_cli_help.py 和 test_rag_search.py 中的类似测试）
- [x] 5.2 识别并参数化其他相似测试模式

## 6. 源码压缩

- [x] 6.1 清理未使用的导入和死代码
- [x] 6.2 内联仅被调用一次的辅助函数（如适用）

## 7. 验证

- [x] 7.1 运行完整测试套件，确保 302 个测试全部通过
- [x] 7.2 统计最终行数，确认测试代码 <5000 行、源代码 <3800 行
