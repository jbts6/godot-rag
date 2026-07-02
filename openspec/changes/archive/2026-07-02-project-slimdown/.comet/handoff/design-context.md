# Comet Design Handoff

- Change: project-slimdown
- Phase: design
- Mode: compact
- Context hash: d8f35f2540548b24929296bf975fb871f80a14ebe0d76feb639c5e03ee1442cb

Generated-by: comet-handoff.sh

OpenSpec remains the canonical capability spec. This handoff is a deterministic, source-traceable context pack, not an agent-authored summary.

## openspec/changes/project-slimdown/proposal.md

- Source: openspec/changes/project-slimdown/proposal.md
- Lines: 1-235
- SHA256: 2b2f5632fd50d2deb833926814c6c56517f56af85c9b1b9090fdf6f513d8fdfc

[TRUNCATED]

```md
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
```

Full source: openspec/changes/project-slimdown/proposal.md

## openspec/changes/project-slimdown/design.md

- Source: openspec/changes/project-slimdown/design.md
- Lines: 1-101
- SHA256: e0639ccdfe339503cb1ee82b5dcd5aad9c9d6c50d46dc02f34600cdb3463cc55

[TRUNCATED]

```md
## Context

项目经过22次change迭代，测试代码膨胀严重（5729行，比源代码多48%）。主要问题：
- 3个测试文件仍在使用 unittest 风格（test_rag_search.py、test_searcher_module.py、test_rag_addon.py）
- 重复的测试模式：50次临时目录创建、12个重复的_build_db方法
- 源代码模块过大：search_eval.py（863行）需要拆分

## Goals / Non-Goals

**Goals:**
- 将 unittest 风格测试迁移到 pytest，减少代码量
- 提取公共 fixtures，消除重复代码
- 拆分过大的源代码模块
- 保持100%测试通过率

**Non-Goals:**
- 不改变测试覆盖度
- 不改变公共API接口
- 不引入新的测试框架（继续使用 pytest）

## Decisions

### 决策1：优先迁移 unittest 到 pytest

**选择**：将 test_rag_search.py 从 unittest 迁移到 pytest

**理由**：
- test_rag_search.py 是最大的测试文件（1807行）
- 有144次 self.assert* 调用，可以简化为 assert
- 有26个测试类，可以移除类定义
- 预计减少450行代码（25%）

**替代方案**：
- 保持 unittest 风格：不推荐，因为 pytest 更简洁
- 使用 pytest-unittest 插件：不推荐，因为没有简化代码

### 决策2：提取公共 fixtures

**选择**：创建 rst2md/tests/fixtures/common.py

**理由**：
- 50次重复的 tempfile.TemporaryDirectory 调用
- 12个重复的 _build_db 方法
- 可以提取为 pytest fixtures

**替代方案**：
- 在每个测试文件中定义 fixtures：不推荐，因为重复
- 使用 unittest setUp：不推荐，因为 pytest fixtures 更灵活

### 决策3：拆分 search_eval.py

**选择**：将 search_eval.py 拆分为 search_eval/ 包

**理由**：
- 863行代码，职责过多
- 可以拆分为 models、metrics、reports、baseline、evaluation 5个模块
- 每个模块200-300行，更易维护

**替代方案**：
- 保持单文件：不推荐，因为过大
- 使用 mixin：不推荐，因为复杂

## Risks / Trade-offs

### 风险1：重构引入 bug
**缓解**：
- 逐步重构，每步都运行测试
- 保持公共接口不变
- 使用 pytest 的 --tb=short 快速定位问题

### 风险2：测试覆盖度下降
**缓解**：
- 重构前记录测试覆盖度
- 重构后验证覆盖度不变
- 使用 pytest --cov 检查覆盖度

### 风险3：团队适应成本
**缓解**：
- 提供重构指南
- 逐步引入新结构
```

Full source: openspec/changes/project-slimdown/design.md

## openspec/changes/project-slimdown/tasks.md

- Source: openspec/changes/project-slimdown/tasks.md
- Lines: 1-27
- SHA256: b5db8e61adc674e0cf7ad11d549921c7443ec3fb025d7f19244fd65b86b0f770

```md
## 1. 测试代码优化

- [ ] 1.1 参数化CLI帮助测试（合并4个相似测试为1个参数化测试）
- [ ] 1.2 提取公共fixtures（创建 rst2md/tests/fixtures/common.py）
- [ ] 1.3 合并重复的report测试（合并23个report相关测试中的相似测试）
- [ ] 1.4 迁移 test_rag_search.py 到 pytest 风格（移除类定义，简化断言）

## 2. 源代码重构

- [ ] 2.1 拆分 search_eval.py 为 search_eval/ 包
- [ ] 2.2 创建 search_eval/models.py（数据模型）
- [ ] 2.3 创建 search_eval/metrics.py（指标计算）
- [ ] 2.4 创建 search_eval/reports.py（报告生成）
- [ ] 2.5 创建 search_eval/baseline.py（基线管理）
- [ ] 2.6 创建 search_eval/evaluation.py（评估逻辑）
- [ ] 2.7 更新 search_eval/__init__.py（公共接口）

## 3. 项目结构优化

- [ ] 3.1 统一测试组织（将CLI相关测试集中到test_cli.py）
- [ ] 3.2 优化测试运行（使用pytest.mark.parametrize减少重复测试）
- [ ] 3.3 更新 pyproject.toml 配置（支持新的测试结构）

## 4. 验证与收尾

- [ ] 4.1 运行完整测试套件（确保100%通过率）
- [ ] 4.2 检查测试覆盖度（确保覆盖度不变）
- [ ] 4.3 更新文档（记录新的测试结构和重构指南）```

