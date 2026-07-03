# Build 精简 + 指纹重构 + 文档瘦身 — 计划

## 一、指纹重构

### 问题

`_fingerprint_common()` (`orchestrator.py:228-261`) 把通用输入塞进所有 cacheable stage 的指纹：
- `pyproject.toml` — version stage 在 fingerprint 计算前已修改它，没有 `--no-bump` 时缓存永远不命中
- `uv_lock` / `python_version` / `uv_version` — 不影响任何 cacheable stage 的输出
- `build_tool` / `build_sh` — 仅 package-tree 需要
- `pandoc_version` — 仅 docs-md 需要
- `with_wiki` — 仅 rag-db 需要

### 方案

删除 `_fingerprint_common()`，每个 cacheable stage 使用独立 fingerprint 函数。

### 改动（`godot_rag_build/orchestrator.py`）

**docs-md** — 3 项输入：
```python
fingerprint=lambda ctx: fingerprint_items({
    "godot_docs": _submodule_commit_hash(ctx, "godot-docs"),
    "rst2md": fingerprint_tree(ctx.root / "rst2md", include_suffixes=(".py", ".json", ".yaml", ".yml")),
    "pandoc_version": _tool_version(ctx, ["pandoc", "--version"]),
})
```

**wiki** — 1 项输入（`with_wiki=False` 时返回常量）：
```python
fingerprint=lambda ctx: fingerprint_items({
    "wiki_cache": fingerprint_tree(_wiki_dir(ctx), exclude_dirs=(".git",)) if ctx.options["with_wiki"] and _wiki_dir(ctx).exists() else "disabled",
})
```

**rag-db** — 6 项输入：
```python
fingerprint=lambda ctx: fingerprint_items({
    "with_wiki": str(ctx.options["with_wiki"]).lower(),
    "godot_docs": _submodule_commit_hash(ctx, "godot-docs"),
    "rst2md": fingerprint_tree(ctx.root / "rst2md", include_suffixes=(".py", ".json", ".yaml", ".yml")),
    "wiki_cache": fingerprint_tree(_wiki_dir(ctx), exclude_dirs=(".git",)) if _wiki_dir(ctx).exists() else "missing",
    "addons": fingerprint_tree(ctx.root / "addons", include_suffixes=(".md", ".rst", ".gd", ".cs", ".json", ".yaml", ".yml", ".cfg"), exclude_dirs=(".git", ".godot", "__pycache__")),
    "addon_configs": fingerprint_tree(ctx.root / "rst2md/rag/addon_configs", include_suffixes=(".py", ".json", ".yaml", ".yml")),
})
```

**package-tree** — 3 项输入：
```python
fingerprint=lambda ctx: fingerprint_items({
    "rag_source": fingerprint_tree(ctx.root / "rst2md/rag", include_suffixes=(".py", ".json", ".yaml", ".yml")),
    "addon_configs": fingerprint_tree(ctx.root / "rst2md/rag/addon_configs", include_suffixes=(".py", ".json", ".yaml", ".yml")),
    "build_tool": fingerprint_tree(ctx.root / "godot_rag_build", include_suffixes=(".py",)),
})
```

**readme** — 3 项输入：
```python
fingerprint=lambda ctx: fingerprint_items({
    "merge_readme": fingerprint_file(ctx.root / "scripts/merge_readme.py"),
    "readme": fingerprint_file(ctx.root / "README.md"),
    "readme_zh": fingerprint_file(ctx.root / "README_zh.md"),
})
```

## 二、CLI 精简

### godot-rag-build 移除 2 个命令

| 命令 | 理由 |
|------|------|
| `diagnostics` | 透传 `rag.cli diagnostics`，publish 内部已调用，用户可直接 `uv run python -m rag.cli diagnostics` |
| `clean-cache` | `rm -rf .cache/build-release` 即可 |

改动文件：
- `godot_rag_build/cli.py` — 删除 `diagnostics` 和 `clean-cache` 子命令
- `godot_rag_build/orchestrator.py` — 删除 `run_release_diagnostics()` 函数
- `build.sh` — 无需改动（这两个命令原本就没暴露）

### godot-rag 移除 3 个命令

| 命令 | 理由 |
|------|------|
| `stats` | 开发者/运维工具，非搜索功能 |
| `diagnostics` | 与 godot-rag-build 重复，且可用 `rag.cli` 直接调用 |
| `eval-search` | 测试/评估工具，非终端用户功能 |

改动文件：
- `rst2md/rag/cli.py` — 删除 `stats`、`diagnostics`、`eval-search` 子命令及相关函数（`cmd_stats`、`cmd_diagnostics`、`cmd_eval_search`）。底层模块（`rag.diagnostics`、`rag.search_eval`、`rag.store`）仍可用
- `godot_rag_build/orchestrator.py` — 删除 `run_release_diagnostics()` 函数（CLI 删除后变成死代码）

## 三、README 瘦身

英文（351 行）和中文（313 行）均需精简。

### 移除段落

| 段落 | 行数×2 | 理由 |
|------|--------|------|
| RAG vs Non-RAG 基准测试 | ~80 行 | 营销材料，非使用文档 |
| 数据库覆盖表格 | ~15 行 | 会过时，用户不需要 |
| Search Quality Evaluation | ~40 行 | 内部质量指标 |

### 更新段落

- **Update 段落**：移除 `diagnostics` 和 `clean-cache` 的引用
- **示例段落**：精简，只保留核心用法

### 保留段落

- 安装、使用方法（搜索类型、addon 搜索、输出格式）
- 基本示例（2-3 个）
- 开发、许可证

## 四、SKILL.md 瘦身

当前 266 行，目标 ~80 行。

### 移除段落

| 段落 | 理由 |
|------|------|
| Common Rationalizations | 说教式，无实际约束力 |
| No Results Found（详细版） | 一句"尝试更宽泛的词"够了 |
| When to Query 大表格 | "任何时候都先查"一句话概括 |
| Database Coverage 表格 | 与 README 重复，会过时 |
| 安装指引 | 与 README 重复 |

### 保留并精简

- 核心规则（先查再写，一句话）
- Red Flags — 保留核心精神，压缩到 3-4 行
- 查询命令速查（搜索类型 + 常用选项）
- 结果解读（score、chunk_type、symbol）
- Query Strategy 表格（精简版）

## 执行顺序

1. 指纹重构（`orchestrator.py`）
2. CLI 精简（`cli.py` × 2 + `orchestrator.py` 删除 `run_release_diagnostics`）
3. README 瘦身（英文 + 中文）
4. SKILL.md 瘦身
5. 测试验证

## 验证

1. `uv run pytest -q` — 现有测试通过
2. 连续两次 `./build.sh --no-bump`，第二次所有 cacheable stage 应 SKIP
3. 修改 `rst2md/` 脚本后，docs-md 和 rag-db 应重新执行
4. 修改 `README.md` 后，只有 readme stage 重新执行

## Brainstorm 备忘

- CLI 函数可直接删除，无需保留（无外部调用者）
- `run_release_diagnostics()` 在 CLI 删除后变成死代码，一并删除
- SKILL.md Red Flags 保留核心精神（3-4 行），不完全删除
- README 移除 ~135 行后约 215 行（英文）/ 178 行（中文），长度合理
