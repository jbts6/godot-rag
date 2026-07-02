# 项目瘦身提案

## 问题陈述

项目经过22次change迭代，测试代码膨胀严重：
- 测试代码：5729行，比源代码（3860行）多48%
- 测试用例：292个
- 最大的测试文件：test_rag_search.py（1807行，76个测试函数）

## 现状分析

### 测试代码分布
- test_rag_search.py: 1807行，76个测试函数，26个测试类
- test_search_eval.py: 1072行，47个测试函数
- test_searcher_module.py: 624行，51个测试函数
- test_rag_addon.py: 517行，32个测试函数
- test_semantic_search.py: 511行，18个测试函数

### 源代码复杂度
- search_eval.py: 863行（最复杂的模块）
- searcher.py: 518行
- cli.py: 364行

### 主要问题
1. **重复的测试模式**：
   - CLI帮助测试：4个相似的测试可以参数化
   - 临时目录创建：50次重复使用tempfile.TemporaryDirectory
   - 数据库构建：12个重复的_build_db方法

2. **测试代码膨胀**：
   - report相关测试：23个，可能有些可以合并
   - evaluate相关测试：7个，可能有些重复

3. **源代码复杂度过高**：
   - search_eval.py：863行，需要拆分

## 瘦身方案

### 阶段1：测试代码优化（预计减少500-800行）

#### 1.1 参数化CLI帮助测试
**目标**：将4个CLI帮助测试合并为1个参数化测试

**当前代码**：
```python
def test_cli_search_class_help(self):
    result = subprocess.run(
        [sys.executable, "-m", "rag.cli", "s-class", "--help"],
        text=True, capture_output=True, env=TEST_ENV,
    )
    self.assertEqual(result.returncode, 0)
    self.assertIn("query", result.stdout)

def test_cli_search_tutorial_help(self):
    # 类似代码...
```

**优化后**：
```python
@pytest.mark.parametrize("command", [
    "s-class", "s-tutorial", "s-engine", "diagnostics"
])
def test_cli_help_commands(command):
    result = subprocess.run(
        [sys.executable, "-m", "rag.cli", command, "--help"],
        text=True, capture_output=True, env=TEST_ENV,
    )
    assert result.returncode == 0
    assert "query" in result.stdout
```

**预计减少**：3个测试函数，约30行代码

#### 1.2 提取公共fixtures
**目标**：将重复的setup代码提取为公共fixtures

**创建新文件**：`rst2md/tests/fixtures/common.py`
```python
import tempfile
from pathlib import Path
import pytest

@pytest.fixture
def tmp_dir():
    """提供临时目录"""
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)

@pytest.fixture
def sample_docs(tmp_dir):
    """创建示例文档结构"""
    docs = tmp_dir / "docs"
    classes = docs / "classes"
    classes.mkdir(parents=True)
    
    # 创建示例类文件
    (classes / "class_node.md").write_text(
        "# Node\n\nBase class.\n\n## Methods\n\n"
        "`void` **add_child**(`Node` node)\n\nAdds a child.\n",
        encoding="utf-8",
    )
    return docs

@pytest.fixture
def sample_db(sample_docs, tmp_dir):
    """创建示例数据库"""
    from rag.store import build_database
    db_path = tmp_dir / "test.sqlite"
    build_database(sample_docs, db_path)
    return db_path
```

**预计减少**：约200行重复代码

#### 1.3 合并重复的report测试
**目标**：检查23个report相关测试，合并相似的测试

**分析**：
- test_report_to_dict_includes_version_metadata
- test_report_to_dict_includes_latency_summary
- test_report_to_dict_includes_report_only_triage

这些测试可以合并为一个参数化测试。

**预计减少**：5-8个测试函数，约100行代码

### 阶段2：源代码重构（预计减少200-300行）

#### 2.1 拆分search_eval.py
**目标**：将863行的模块拆分为更小的模块

**新模块结构**：
```
search_eval/
├── __init__.py          # 公共接口
├── models.py           # 数据模型（GoldenQuery, DatabaseFingerprint等）
├── metrics.py          # 指标计算（calculate_metrics, latency_summary等）
├── reports.py          # 报告生成（format_text_report, report_to_dict等）
├── baseline.py         # 基线管理（apply_baseline, compare_with_baseline等）
└── evaluation.py       # 评估逻辑（evaluate_results, evaluate_database等）
```

**预计每个模块**：200-300行

#### 2.2 提取公共搜索逻辑
**目标**：从searcher.py中提取公共的搜索逻辑

**提取内容**：
- FTS查询构建
- 向量查询构建
- 结果排序逻辑

**预计减少**：约100行代码

### 阶段3：项目结构优化（长期）

#### 3.1 统一测试组织
**目标**：将CLI相关测试集中到test_cli.py

**新结构**：
```
tests/
├── test_cli.py           # CLI测试（从test_rag_search.py提取）
├── test_search_eval.py   # 搜索评估测试
├── test_searcher.py      # 搜索器测试
├── test_addon.py         # 插件测试
├── test_semantic.py      # 语义搜索测试
└── fixtures/             # 公共fixtures
```

#### 3.2 优化测试运行
**目标**：使用pytest.mark.parametrize减少重复测试

**示例**：
```python
@pytest.mark.parametrize("query,expected", [
    ("Node.add_child", "Node.add_child"),
    ("attach node to scene tree", "Node.add_child"),
])
def test_symbol_queries(query, expected):
    # 测试逻辑...
```

## 实施计划

### 第1周：测试代码优化
- [ ] 参数化CLI帮助测试
- [ ] 提取公共fixtures
- [ ] 合并重复的report测试

### 第2周：源代码重构
- [ ] 拆分search_eval.py
- [ ] 提取公共搜索逻辑

### 第3周：项目结构优化
- [ ] 统一测试组织
- [ ] 优化测试运行

## 预期效果

### 代码减少
- 测试代码：从5729行减少到4500-5000行（减少12-20%）
- 源代码：从3860行减少到3500-3600行（减少7-10%）

### 维护性提升
- 减少重复代码
- 提高测试可读性
- 简化模块结构

### 性能提升
- 测试运行时间可能减少
- 代码维护成本降低

## 风险与缓解

### 风险1：重构引入bug
**缓解**：
- 逐步重构，每步都运行测试
- 保持公共接口不变

### 风险2：测试覆盖度下降
**缓解**：
- 重构前记录测试覆盖度
- 重构后验证覆盖度不变

### 风险3：团队适应成本
**缓解**：
- 提供重构指南
- 逐步引入新结构

## 成功指标

1. **代码减少**：测试代码减少15%以上
2. **测试通过率**：保持100%通过率
3. **维护性**：新开发者理解代码时间减少20%
4. **性能**：测试运行时间减少10%以上