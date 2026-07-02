---
comet_change: project-slimdown
role: technical-design
canonical_spec: openspec
---

# 项目瘦身技术设计

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
- 按功能模块重组测试目录
- 保持100%测试通过率

**Non-Goals:**
- 不改变测试覆盖度
- 不改变公共API接口
- 不引入新的测试框架（继续使用 pytest）

## Decisions

### 决策1：按职责拆分 search_eval.py

**选择**：将 search_eval.py 拆分为5个模块

**模块结构**：
```
rst2md/rag/search_eval/
├── __init__.py          # 公共接口（10-20行）
├── models.py           # 数据模型（80-100行）
├── metrics.py          # 指标计算（120-150行）
├── reports.py          # 报告生成（200-250行）
├── baseline.py         # 基线管理（150-200行）
└── evaluation.py       # 评估逻辑（200-250行）
```

**理由**：
- 最符合单一职责原则
- 便于后续扩展和维护
- 每个模块都可以独立测试

**替代方案**：
- 按功能划分（core、analysis、config）：不推荐，core 模块可能仍然较大
- 混合划分（models + core、reports、baseline）：不推荐，划分标准可能不够一致

### 决策2：渐进式迁移测试代码

**选择**：先提取公共 fixtures，再逐步迁移 unittest 到 pytest

**理由**：
- 降低迁移风险
- 便于逐步验证
- 保持测试稳定性

**替代方案**：
- 一次性迁移：不推荐，风险较高
- 混合方式：不推荐，可能产生不一致性

### 决策3：按功能模块重组测试目录

**选择**：将相关测试集中到对应的模块目录

**新结构**：
```
rst2md/tests/
├── fixtures/           # 公共 fixtures
├── search/             # 搜索相关测试
│   ├── test_searcher.py
│   ├── test_search_eval.py
│   └── test_semantic.py
├── cli/                # CLI 相关测试
│   └── test_cli.py
├── addon/              # 插件相关测试
│   └── test_addon.py
└── build/              # 构建相关测试
    └── test_build.py
```

**理由**：
- 便于定位和维护测试
- 符合 Python 项目的最佳实践
- 便于后续扩展

**替代方案**：
- 保持扁平结构：不推荐，文件数量多时难以维护
- 混合方式：不推荐，可能产生不一致性

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
- 保持代码风格一致

## Migration Plan

### 阶段1：源代码重构（第1周）
1. 拆分 search_eval.py 为 search_eval/ 包
2. 创建 models.py、metrics.py、reports.py、baseline.py、evaluation.py
3. 更新 __init__.py 公共接口
4. 运行测试验证

### 阶段2：测试代码优化（第2周）
1. 提取公共 fixtures（common.py、database.py、search.py）
2. 参数化 CLI 帮助测试
3. 合并重复的 report 测试
4. 运行测试验证

### 阶段3：项目结构重组（第3周）
1. 创建新的目录结构（search/、cli/、addon/、build/）
2. 逐步移动测试文件
3. 更新导入路径
4. 运行测试验证

## Open Questions

1. 是否需要保留部分 unittest 风格的测试作为示例？
2. 是否需要更新 CI/CD 配置以支持新的测试结构？
3. 是否需要编写迁移指南供团队参考？