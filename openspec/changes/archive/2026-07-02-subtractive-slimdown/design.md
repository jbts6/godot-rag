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
**缓解**：fixtures只提取纯机械性重复（tmp_dir、build_db），不提取业务逻辑

### 风险3：参数化降低测试可读性
**缓解**：只参数化逻辑完全相同的测试，保持参数名可读
