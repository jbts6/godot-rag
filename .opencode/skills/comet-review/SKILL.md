# Skill: comet-review

# Comet 归档后回顾（Post-Archive Review）

归档完成后回顾整个变更弧线：从提案到设计、实施、验证、spec 合并。目标是提取经验教训、验证 spec 合并完整性、评估过程质量。

**与 verify 的区别**：verify 是合并前的质量门禁（正确性、安全、边界条件）；review 是合并后的回顾（过程质量、设计决策复盘、spec 健康度、经验沉淀）。

## 前置条件

- change 已归档（`archived: true`，归档目录存在）

## 步骤

### 0. 输出语言约束

回顾报告使用触发本次工作流的用户请求语言。

### 1. 定位归档 Change

运行 `openspec list --json --archived` 获取归档 change 列表。

**判定逻辑**：
- 若用户指定了 change 名称 → 直接使用
- 若恰好 1 个归档 change → 自动选中
- 若多个归档 change → 列出清单让用户选择

定位归档目录：

```bash
ARCHIVE_DIR=$(find openspec/changes/archive -maxdepth 1 -type d -name "*-<change-name>" | sort -r | head -1)
```

确认目录存在且包含 `.comet.yaml`。读取状态文件获取 `base_ref`、`workflow`、`verify_result`、`verification_report` 等字段。

### 2. 加载回顾上下文

读取以下文件（存在时）：

| 文件 | 路径 | 用途 |
|------|------|------|
| proposal | `$ARCHIVE_DIR/proposal.md` | 原始目标与范围 |
| design | `$ARCHIVE_DIR/design.md` | 高层设计决策 |
| tasks | `$ARCHIVE_DIR/tasks.md` | 任务清单与完成状态 |
| delta spec | `$ARCHIVE_DIR/` 下的 spec 文件 | 变更规格 |
| verification report | `.comet.yaml` 中 `verification_report` 指向的文件 | 验证结论 |
| main spec | `openspec/specs/` 下关联的主 spec | 合并后的最终状态 |

### 3. 获取实施 Diff

从 `.comet.yaml` 的 `base_ref` 到归档前最后一次提交，获取完整改动：

```bash
BASE_REF=$("$COMET_BASH" "$COMET_STATE" get <archive-name> base_ref 2>/dev/null || grep 'base_ref:' "$ARCHIVE_DIR/.comet.yaml" | sed 's/base_ref: *//')
git log --oneline "$BASE_REF"..HEAD -- .
git diff --stat "$BASE_REF"..HEAD
```

若 `base_ref` 不可用，回退到 `git log --oneline` 按 change 名称搜索相关提交。

### 4. 执行回顾审查

逐项审查以下维度。每项标注 PASS / NOTE / CONCERN，附具体证据。

#### 4a. Spec 合并完整性

- 主 spec 中是否残留 delta-only section 标题（`ADDED:`、`MODIFIED:`、`REMOVED:`、`RENAMED:`）
- 合并后主 spec 是否自洽（无断裂段落、无重复内容）
- delta spec 中声明的变更是否全部体现在主 spec 中

#### 4b. 设计-实施对齐

- 对照 design.md 的决策，实施是否偏离
- 偏离是否有正当理由（在 commit message 或 tasks.md 中记录）
- 是否存在 design.md 未覆盖的隐式决策

#### 4c. 漂移分析

- 对照 proposal.md 的原始目标，最终实施是否收敛
- tasks.md 中是否有被取消或跳过的任务（标记为 `- [x]` 但实际未实现，或 `- [ ]` 残留）
- 范围是否膨胀（实际改动文件数 vs 计划）

#### 4d. 代码质量快照

基于 diff 做快速扫描（不替代 verify 阶段的深度审查）：
- 是否有明显的 TODO/FIXME/HACK 残留
- 是否有未使用的导入或死代码
- 错误处理是否一致

#### 4e. 过程质量

- workflow 类型（full/hotfix/tweak）是否合适
- 是否触发过升级条件或范围扩张
- verify 阶段是否有失败记录
- commit 粒度是否合理（每任务一次 vs 整体一次）

### 5. 生成回顾报告

将审查结果写入报告文件：

```bash
mkdir -p docs/superpowers/reports
# docs/superpowers/reports/YYYY-MM-DD-<change-name>-review.md
```

报告结构：

```markdown
# Change Review: <change-name>

**归档日期**: YYYY-MM-DD
**Workflow**: full | hotfix | tweak
**改动规模**: N files, M commits

## 审查摘要

| 维度 | 状态 | 关键发现 |
|------|------|---------|
| Spec 合并完整性 | PASS/CONCERN | ... |
| 设计-实施对齐 | PASS/CONCERN | ... |
| 漂移分析 | PASS/CONCERN | ... |
| 代码质量 | PASS/CONCERN | ... |
| 过程质量 | NOTE | ... |

## 详细发现

### Spec 合并完整性
...

### 设计-实施对齐
...

### 漂移分析
...

### 代码质量
...

### 过程质量
...

## 经验教训

- **做得好**: ...
- **下次改进**: ...
- **模式识别**: 本次变更是否体现了可复用的模式或反模式
```

### 6. 呈现回顾

向用户展示回顾报告摘要：
- 各维度状态一览
- CONCERN 项的简要说明
- 经验教训要点

这是信息输出，不需要用户决策。报告已落盘，用户可随时查阅完整内容。

## 退出条件

- 回顾报告文件已写入 `docs/superpowers/reports/`
- 报告内容覆盖全部 5 个审查维度
- 每个维度有明确的 PASS / NOTE / CONCERN 标注

## 何时回顾

回顾不是强制步骤，但在以下场景推荐执行：
- 完成 full workflow 归档后（复杂变更值得复盘）
- verify 阶段曾出现失败或范围扩张的变更
- 用户希望沉淀经验教训

对于 hotfix / tweak 的小改动，回顾可选。

Base directory for this skill: /Users/jbts6/Site/godot-rag/.opencode/skills/comet-review
Relative paths in this skill (e.g., scripts/, reference/) are relative to this base directory.
