---
comet_change: subtractive-slimdown
role: technical-design
canonical_spec: openspec
archived-with: 2026-07-02-subtractive-slimdown
status: final
---

# 纯减法瘦身 Design Doc

## Context

项目测试代码5880行，源代码4096行，测试/源码比1.43:1。上次project-slimdown因拆分文件净增1363行。本次采用纯减法策略。

## 决策1：unittest断言迁移

逐文件将self.assertEqual/assertTrue/assertIn等迁移为pytest原生assert。

映射规则：
- assertEqual(a, b) → assert a == b
- assertIn(a, b) → assert a in b
- assertTrue(x) → assert x
- assertFalse(x) → assert not x
- assertIsNone(x) → assert x is None
- assertGreater(a, b) → assert a > b
- assertAlmostEqual(a, b) → assert a == pytest.approx(b)
- assertIsInstance(a, b) → assert isinstance(a, b)

目标文件：test_rag_addon.py(92个)、test_searcher_module.py(42个)、test_rag_search.py(176个)

## 决策2：共享fixtures提取

扩展 rst2md/tests/fixtures/common.py：

```python
@pytest.fixture
def build_db(tmp_dir):
    """返回构建数据库的工厂函数"""
    def _build(doc_path, db_path=None):
        from rag.store import build_database
        if db_path is None:
            db_path = tmp_dir / "test.sqlite"
        build_database(doc_path, db_path)
        return db_path
    return _build

@pytest.fixture
def tmp_db(tmp_dir, sample_docs, build_db):
    """一步到位：tmp目录 + 示例文档 + 构建数据库"""
    db_path = build_db(sample_docs)
    return db_path
```

替换181次TemporaryDirectory和109次build_database重复调用。

## 决策3：测试参数化

目标：
- CLI帮助测试（4个相似 → 1个@parametrize）
- 类似的搜索结果断言测试
- report相关测试中的重复模式

原则：只参数化逻辑完全相同的测试。

## 决策4：源码压缩

保守策略：只清理未使用导入、死代码、注释掉的代码。不内联函数（风险高收益低）。

## 执行顺序

1. 先提取fixtures（后续迁移依赖）
2. 逐文件迁移unittest断言（每文件迁移后测试验证）
3. 参数化相似测试
4. 源码压缩
5. 最终验证
