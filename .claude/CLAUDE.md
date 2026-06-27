# Godot RAG 项目指南

## 目录结构

- `rst2md/rag/` — **源码**（修改这里）
- `godot_rag/` — **构建产物**（禁止手动编辑或读取参考）

`build.sh` 会从 `rst2md/rag/` 复制 `.py` 文件到 `godot_rag/rag/`，并把 `from rag.` 改写为 `from godot_rag.rag.`。

**永远不要读 `godot_rag/rag/*.py`，那是构建产物。源码在 `rst2md/rag/`。**

## 构建与发布

```bash
./build.sh              # 构建 wheel
./build.sh --publish    # 构建并发布到 PyPI
```

## 测试

```bash
uv run pytest -q
```

测试源码在 `rst2md/tests/`，通过 `pyproject.toml` 的 `pythonpath = ["rst2md"]` 配置。
