# Godot RAG

用于 Godot 文档和插件的混合 RAG 搜索。FTS5 + 向量双重召回，配合 RRF 融合排序。

## 目录结构

- `rst2md/rag/` — **源代码**（在此编辑）
- `godot_rag/` — **构建输出**（切勿手动编辑）
- `rst2md/tests/` — 测试
- `docs/` — 文档和规范
- `openspec/` — OpenSpec 变更管理
- `scripts/` — 实用脚本

**切勿读取 `godot_rag/rag/*.py` — 那些是构建产物。源代码在 `rst2md/rag/` 中。**

## 构建与发布

```bash
./build.sh              # 构建 wheel
./build.sh --publish    # 构建并发布到 PyPI
```

`build.sh` 将 `rst2md/rag/` 中的 `.py` 文件复制到 `godot_rag/rag/`，并将导入从 `from rag.` 重写为 `from godot_rag.rag.`。

**不要手动提交版本号变更** — `build.sh` 自动递增版本号。手动提交会导致版本跳跃。

## 测试

```bash
uv run pytest -q                              # 完整套件
uv run pytest -q rst2md/tests/test_search_eval.py  # 针对性测试
```

测试配置在 `pyproject.toml` 中：`pythonpath = ["rst2md"]`，`testpaths = ["rst2md/tests"]`。

## 关键模块

| 模块 | 用途 |
|------|------|
| `searcher.py` | 混合搜索（FTS5 + 向量 + RRF 融合 + 图扩展） |
| `search_eval.py` | 质量评估、延迟指标、诊断 |
| `cli.py` | 命令行接口（`godot-rag` 命令） |
| `indexer.py` | 数据库索引 |
| `models.py` | 数据模型（`SearchMetadata`、`SearchResponse`） |
| `query_plan.py` | 查询规划和意图检测 |
| `chunker.py` | 文档分块 |

## 搜索质量

运行确定性评估器测试：
```bash
uv run pytest -q rst2md/tests/test_search_eval.py rst2md/tests/test_search_eval_cli.py
```

运行真实数据库门控测试（当 `godot_rag.db` 可用时）：
```bash
uv run godot-rag eval-search --db godot_rag.db --baseline docs/search-quality/baseline.json --compare-graph
```

## CodeGraph

本项目使用 CodeGraph 进行代码智能分析。`.codegraph/` 目录包含所有符号、边和文件的预构建索引。

**在读取文件之前先使用 CodeGraph** — 它在一次调用中返回带有调用路径的逐行源代码，比 grep + 读取循环更快。

```bash
# 通过 MCP 工具查询（首选）
codegraph_explore("searcher search_database")

# 或通过 shell
codegraph explore "searcher search_database"
```

CodeGraph 遵循 grep 无法处理的动态分派（回调、重新导出、多态）。用于：
- 理解代码工作原理
- 查找符号的定义/使用位置
- 跨文件追踪调用路径
- 编辑前的影响范围分析

**不要用 grep 重复验证 CodeGraph 结果** — 它们来自 AST 解析，更加准确。

## 工作流程

本项目使用 OpenSpec + Comet 进行变更管理：
- `/comet` — 开始或继续变更
- `/comet-open` — 开启新变更
- `/comet-design` — 设计阶段
- `/comet-build` — 构建阶段
- `/comet-verify` — 验证阶段
- `/comet-archive` — 归档已完成变更

变更记录在 `openspec/changes/` 中，归档到 `openspec/changes/archive/`。
