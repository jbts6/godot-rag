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
- 保持代码风格一致

## Migration Plan

### 阶段1：测试代码优化（第1周）
1. 参数化CLI帮助测试
2. 提取公共fixtures
3. 合并重复的report测试

### 阶段2：源代码重构（第2周）
1. 拆分search_eval.py
2. 提取公共搜索逻辑

### 阶段3：项目结构优化（第3周）
1. 统一测试组织
2. 优化测试运行

## Open Questions

1. 是否需要保留部分 unittest 风格的测试作为示例？
2. 是否需要更新 CI/CD 配置以支持新的测试结构？
3. 是否需要编写迁移指南供团队参考？