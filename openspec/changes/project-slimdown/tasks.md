## 1. 测试代码优化

- [x] 1.1 参数化CLI帮助测试（合并4个相似测试为1个参数化测试）
- [x] 1.2 提取公共fixtures（创建 rst2md/tests/fixtures/common.py）
- [x] 1.3 合并重复的report测试（合并23个report相关测试中的相似测试）
- [ ] 1.4 迁移 test_rag_search.py 到 pytest 风格（移除类定义，简化断言）

## 2. 源代码重构

- [x] 2.1 拆分 search_eval.py 为 search_eval/ 包
- [x] 2.2 创建 search_eval/models.py（数据模型）
- [x] 2.3 创建 search_eval/metrics.py（指标计算）
- [x] 2.4 创建 search_eval/reports.py（报告生成）
- [x] 2.5 创建 search_eval/baseline.py（基线管理）
- [x] 2.6 创建 search_eval/evaluation.py（评估逻辑）
- [x] 2.7 更新 search_eval/__init__.py（公共接口）

## 3. 项目结构优化

- [x] 3.1 统一测试组织（将CLI相关测试集中到test_cli.py）
- [x] 3.2 优化测试运行（使用pytest.mark.parametrize减少重复测试）
- [x] 3.3 更新 pyproject.toml 配置（支持新的测试结构）

## 4. 验证与收尾

- [x] 4.1 运行完整测试套件（确保100%通过率）
- [x] 4.2 检查测试覆盖度（确保覆盖度不变）
- [ ] 4.3 更新文档（记录新的测试结构和重构指南）