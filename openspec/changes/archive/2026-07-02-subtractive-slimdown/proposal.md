## Why

项目经过23次change迭代，测试代码膨胀至5880行（源代码的1.43倍）。上次瘦身（project-slimdown）因拆分文件反而净增1363行。本次采用纯减法策略：不拆分文件、不重构结构，只删重复、参数化、压缩。

## What Changes

- 将3个测试文件中残留的310个unittest风格断言（self.assertEqual/assertTrue/assertIn等）迁移为pytest原生assert
- 提取181次重复的TemporaryDirectory和109次build_database调用为共享fixtures
- 将相似测试用例参数化（当前仅1个@parametrize）
- 压缩冗余的测试辅助代码和重复的setup逻辑
- 精简源码中的冗余代码（重复逻辑、可内联的单次调用函数）

**不做的事**：
- 不拆分任何文件（上次的教训）
- 不改变公共API
- 不降低测试覆盖度
- 不重构模块结构

## Capabilities

### New Capabilities

无。本次为纯实现层优化，不涉及新能力。

### Modified Capabilities

无。不改变任何规格级行为。

## Impact

- 测试文件：test_rag_search.py、test_rag_addon.py、test_searcher_module.py、test_semantic_search.py
- 源码文件：searcher.py、cli.py（如发现冗余）
- 测试fixtures：rst2md/tests/fixtures/common.py（扩展共享fixtures）
- 无API变更、无依赖变更
