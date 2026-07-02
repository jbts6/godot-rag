# Comet Design Handoff

- Change: subtractive-slimdown
- Phase: design
- Mode: compact
- Context hash: 11cbf95473b6e7d597e3bb3c78d3a9a2aae6fdb0df076902014d515890a41d40

Generated-by: comet-handoff.sh

OpenSpec remains the canonical capability spec. This handoff is a deterministic, source-traceable context pack, not an agent-authored summary.

## openspec/changes/subtractive-slimdown/proposal.md

- Source: openspec/changes/subtractive-slimdown/proposal.md
- Lines: 1-34
- SHA256: 02187a6a59784d3c362629a49e4dc05c213ebd1a4e1304126c5b570df9389100

```md
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
```

## openspec/changes/subtractive-slimdown/design.md

- Source: openspec/changes/subtractive-slimdown/design.md
- Lines: 1-84
- SHA256: dffbfc62451f87d194f4a2560ebc116cdb86e940d750a1238de74df759e588be

[TRUNCATED]

```md
## Context

项目测试代码5880行，源代码4096行。测试/源码比1.43:1。主要膨胀来源：
- 3个测试文件仍有unittest风格（test_rag_addon.py 92个、test_searcher_module.py 42个、test_rag_search.py 176个self.调用）
- 181次TemporaryDirectory重复创建
- 109次build_database重复调用
- 仅1个@pytest.fixture、仅1个@parametrize

上次project-slimdown拆分search_eval.py为包，净增1363行。本次吸取教训：纯减法，不拆分。

## Goals / Non-Goals

**Goals:**
- 测试代码从5880行降至5000行以下（-15%+）
- unittest风格调用从310个降至50个以下
- 提取共享fixtures消除重复setup代码
- 参数化相似测试用例

**Non-Goals:**
- 不拆分任何文件
- 不改变模块结构
- 不改变公共API
- 不新增测试文件

## Decisions

### 决策1：unittest断言迁移为pytest assert

**策略**：逐文件迁移，每次迁移后运行测试验证

**映射规则**：
- `self.assertEqual(a, b)` → `assert a == b`
- `self.assertIn(a, b)` → `assert a in b`
- `self.assertNotIn(a, b)` → `assert a not in b`
- `self.assertTrue(x)` → `assert x`
- `self.assertFalse(x)` → `assert not x`
- `self.assertIsNone(x)` → `assert x is None`
- `self.assertIsNotNone(x)` → `assert x is not None`
- `self.assertGreater(a, b)` → `assert a > b`
- `self.assertAlmostEqual(a, b)` → `assert a == pytest.approx(b)`
- `self.assertIsInstance(a, b)` → `assert isinstance(a, b)`

**风险**：assertTrue语义可能丢失上下文 → 保留注释说明意图

### 决策2：提取共享fixtures到common.py

**已有fixtures**（rst2md/tests/fixtures/common.py）：
- tmp_dir, sample_docs, sample_db

**新增fixtures**：
- `build_db` — 封装build_database调用，接受doc_path和db_path参数
- `tmp_db` — 组合tmp_dir + build_db，一步到位

**使用方式**：将分散的TemporaryDirectory+build_database组合替换为fixture注入

### 决策3：参数化相似测试

**目标**：
- CLI帮助测试（4个相似 → 1个参数化）
- 类似的搜索结果断言测试
- report相关测试中的重复模式

**原则**：只参数化逻辑完全相同的测试，不强行合并有差异的测试

### 决策4：源码压缩策略

**保守原则**：源码只删除明显的死代码和可内联的单次调用函数

**检查项**：
- 未使用的导入
- 可内联的单行辅助函数
- 注释掉的代码
- 重复的条件检查

## Risks / Trade-offs

### 风险1：断言迁移引入语义差异
**缓解**：逐文件迁移，每迁移一个文件运行完整测试

### 风险2：fixture提取导致测试耦合
```

Full source: openspec/changes/subtractive-slimdown/design.md

## openspec/changes/subtractive-slimdown/tasks.md

- Source: openspec/changes/subtractive-slimdown/tasks.md
- Lines: 1-33
- SHA256: eee46f4b3c19547aeb5d3b76ac373663150957234b43c4a72ea6fb27559f0c04

```md
## 1. 扩展共享 Fixtures

- [ ] 1.1 扩展 rst2md/tests/fixtures/common.py：新增 build_db 和 tmp_db fixtures
- [ ] 1.2 在 test_rag_addon.py 中使用 tmp_db fixture 替换重复的 TemporaryDirectory+build_database

## 2. 迁移 unittest 断言（test_rag_addon.py）

- [ ] 2.1 将 test_rag_addon.py 中 92 个 unittest 断言迁移为 pytest assert
- [ ] 2.2 移除 test_rag_addon.py 中的 unittest.TestCase 继承（如适用）

## 3. 迁移 unittest 断言（test_searcher_module.py）

- [ ] 3.1 将 test_searcher_module.py 中 42 个 unittest 断言迁移为 pytest assert

## 4. 迁移 unittest 断言（test_rag_search.py）

- [ ] 4.1 将 test_rag_search.py 中 176 个 self. 调用迁移为 pytest assert
- [ ] 4.2 消除 test_rag_search.py 中的类定义（26个类 → 扁平化）

## 5. 参数化相似测试

- [ ] 5.1 参数化 CLI 帮助测试（test_cli_help.py 和 test_rag_search.py 中的类似测试）
- [ ] 5.2 识别并参数化其他相似测试模式

## 6. 源码压缩

- [ ] 6.1 清理未使用的导入和死代码
- [ ] 6.2 内联仅被调用一次的辅助函数（如适用）

## 7. 验证

- [ ] 7.1 运行完整测试套件，确保 302 个测试全部通过
- [ ] 7.2 统计最终行数，确认测试代码 <5000 行、源代码 <3800 行
```

