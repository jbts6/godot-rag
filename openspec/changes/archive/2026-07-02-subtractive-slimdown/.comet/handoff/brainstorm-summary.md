# Brainstorm Summary

- Change: subtractive-slimdown
- Date: 2026-07-02

## 确认的技术方案

纯减法瘦身：不拆分文件、不重构结构，只删重复、参数化、压缩。

1. unittest断言迁移：310个self.调用 → pytest assert
2. 共享fixtures提取：扩展common.py，新增build_db/tmp_db
3. 测试参数化：相似测试用例合并为@parametrize
4. 源码压缩：清理死代码、未使用导入

## 关键取舍与风险

- 不拆分文件（上次project-slimdown拆分净增1363行的教训）
- 逐文件迁移，每步验证，避免批量引入bug
- fixtures只提取机械性重复，不提取业务逻辑

## 测试策略

每次迁移一个文件 → 运行 uv run pytest -q → 确认通过后继续

## Spec Patch

无。纯实现层优化，不涉及规格变更。
