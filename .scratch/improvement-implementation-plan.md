# Godot RAG 后续优化实现指令稿

## 背景

当前仓库已经完成：

- `addons/scene_manager` 从旧 C# addon 切换到 `glass-brick/Scene-Manager.git` 的 `main` 分支。
- `requires-python` 保持 `>=3.9`。
- `build.sh` 已避免使用 Python 3.11+ 的 `tomllib`。
- `build.sh --publish` 已接入 `uv run --with twine python -m twine upload`。
- README 和 addon 测试已从旧 `TransitionNode` / `ScenesManager` 示例切换到 GDScript `SceneManager` / `change_scene` / `scene_loaded`。
- 当前测试基线：`uv run pytest -q` 为 `57 passed`。

本指令稿用于后续分批实现改进。每一批都应独立提交，提交前跑对应验收命令。

## 总体优先级

1. P0：发布安全和 Python 3.9 兼容护栏。
2. P1：addon API 符号索引质量，尤其支持 `SceneManager.change_scene` 精确命中。
3. P1：README benchmark 和覆盖数字重算，去掉旧数据残影。
4. P2：Scene Manager wiki 文档接入。
5. P2：开发体验整理，包括 `.scratch/` ignore、addon 更新 smoke 工具。

---

## P0-1：强化 `build.sh` 发布护栏

状态：已完成。

完成记录：

- `build.sh` 支持 `--no-bump`、`--publish`、`--test-pypi`、`--help`。
- 发布模式要求起步工作区干净。
- 构建后只检查/上传当前版本 wheel。
- twine 通过 `uv run --with twine python -m twine ...` 调用，避开 `uvx twine` shim 在当前 macOS 环境的 `realpath` 问题。
- 已验证：`bash -n build.sh`、`./build.sh --help`、`./build.sh --no-bump`、`uv run pytest -q`。

### 目标

让本地构建和发布变成两个清楚的模式：

- `./build.sh`：只构建，默认会 bump 版本，保持当前行为。
- `./build.sh --no-bump`：本地验证构建，不改 `pyproject.toml` 和 `uv.lock` 版本。
- `./build.sh --publish`：构建并发布到 PyPI。
- `./build.sh --test-pypi`：构建并发布到 TestPyPI。

发布模式必须更谨慎，避免误传旧 wheel 或脏工作区。

### 具体实现

修改 [build.sh](/Users/jbts6/Site/godot-rag/build.sh)：

1. 参数解析支持：
   - `--publish`
   - `--test-pypi`
   - `--no-bump`
   - `--help`
2. `--publish` 和 `--test-pypi` 互斥。
3. 发布前检查工作区：
   - 允许 `pyproject.toml` / `uv.lock` 因版本 bump 产生改动。
   - 不允许其他未提交改动参与发布。
   - 如果实现复杂，可以先采用严格策略：发布前要求 `git status --porcelain` 为空，然后版本 bump 后继续构建。
4. 构建前清理 `dist`，构建后只上传当前版本 wheel：
   - 不要继续用 `dist/*`。
   - 上传目标应是 `dist/godot_rag-${PKG_VERSION}-py3-none-any.whl`。
5. 发布前运行：
   - `uv run pytest -q`
   - `bash -n build.sh`
   - `uv run --with twine python -m twine check dist/*`
6. PyPI 发布：
   - `uv run --with twine python -m twine upload "$WHEEL_PATH"`
7. TestPyPI 发布：
   - `uv run --with twine python -m twine upload --repository testpypi "$WHEEL_PATH"`
8. 结尾提示更新：
   - 普通发布命令。
   - TestPyPI 发布命令。
   - token 环境变量示例。

### 验收命令

```bash
rtk bash -n build.sh
rtk ./build.sh --help
rtk ./build.sh --no-bump
rtk uv run pytest -q
```

不要求在验收时真实执行 `--publish` 或 `--test-pypi`。

### 建议提交信息

```text
Harden build and publish workflow
```

---

## P0-2：增加 Python 3.9 CI 矩阵

### 目标

既然项目声明 `requires-python = ">=3.9"`，CI 必须覆盖 Python 3.9，防止再次引入 3.11+ API。

### 具体实现

新增 GitHub Actions workflow：

- 文件：`.github/workflows/test.yml`
- 触发：
  - `push`
  - `pull_request`
- matrix：
  - `3.9`
  - `3.10`
  - `3.11`
  - `3.12`
- 步骤：
  1. checkout，包含 submodule 可先不递归，测试不依赖真实 submodule。
  2. 安装 `uv`。
  3. 设置 Python matrix 版本。
  4. `uv sync --dev`
  5. `uv run pytest -q`
  6. `bash -n build.sh`

注意：如果 `uv sync --dev` 在当前 uv 版本下不适合 dependency groups，可改用 `uv run pytest -q`，以本地实际可用命令为准。

### 验收命令

```bash
rtk uv run pytest -q
rtk bash -n build.sh
```

如果本地可以跑 act，可选：

```bash
rtk act -j test
```

### 建议提交信息

```text
Add Python compatibility CI matrix
```

---

## P1-1：支持 addon API 多符号索引

### 目标

当前 `addon_api` 是“一个 API chunk 一个主 symbol”。这已经能让 `change_scene` 通过 FTS 命中，但还不能让 `SceneManager.change_scene` 精确符号命中。

目标是让每个 public GDScript API 声明都进入 `symbols` 表：

- `SceneManager`
- `SceneManager.change_scene`
- `SceneManager.scene_loaded`
- `SceneManager.is_transitioning`
- `change_scene`
- `scene_loaded`

这样 AI agent 用点号查询时也能拿到高分精确结果。

### 推荐设计

不要把 `Chunk.symbol` 从字符串硬改成列表，这会扩大改动面。

更小的做法：

1. 在 `Chunk` model 中新增可选字段：
   - `symbols: List[str] = field(default_factory=list)`
2. 兼容现有逻辑：
   - `chunk.symbol` 仍是主 symbol，用于展示和旧索引。
   - `chunk.symbols` 作为额外 symbol alias。
3. 修改 [rst2md/rag/symbols.py](/Users/jbts6/Site/godot-rag/rst2md/rag/symbols.py)：
   - `extract_symbols()` 先加入 `chunk.symbol`。
   - 再加入 `chunk.symbols`。
   - 去重，避免重复插入。
4. 修改 [rst2md/rag/addon_docs.py](/Users/jbts6/Site/godot-rag/rst2md/rag/addon_docs.py)：
   - GDScript API 抽取时返回 `(primary_symbol, aliases, api_lines)`。
   - 如果文件名是 `SceneManager.gd`，class scope 可用 `SceneManager`。
   - public `func change_scene` 生成：
     - `change_scene`
     - `SceneManager.change_scene`
   - public `signal scene_loaded` 生成：
     - `scene_loaded`
     - `SceneManager.scene_loaded`
   - public `var is_transitioning` 生成：
     - `is_transitioning`
     - `SceneManager.is_transitioning`
   - 跳过 `_private` 开头的 func/var。
5. C# 逻辑保持兼容：
   - 可先只让 C# 继续生成当前主 symbol。
   - 不要为了 C# 过度改大范围。

### 测试要求

修改 [rst2md/tests/test_rag_addon.py](/Users/jbts6/Site/godot-rag/rst2md/tests/test_rag_addon.py)：

1. `chunk_api_file` 测试断言：
   - `chunks[0].symbol == "SceneManager"`
   - `SceneManager.change_scene` 在 `chunks[0].symbols`
   - `_load_scene_resource` 不在 text，也不在 symbols。
2. integration 测试新增：
   - `search_database(db_path, "SceneManager.change_scene", addon="scene_manager")`
   - 断言结果非空。
   - 断言第一个结果 `chunk_type == "addon_api"`。
   - 断言第一个结果 `symbol == "SceneManager"`。

### 验收命令

```bash
rtk uv run pytest -q
rtk uv run python3 - <<'PY'
from pathlib import Path
import tempfile, sys
sys.path.insert(0, "rst2md")
from rag.store import build_database, search_database
with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    docs = tmp / "docs"
    docs.mkdir()
    (docs / "classes").mkdir()
    (docs / "classes" / "class_node.md").write_text("# Node\n", encoding="utf-8")
    db = tmp / "db.sqlite"
    build_database(docs, db, addons_dir=Path("addons"))
    for q in ["SceneManager.change_scene", "SceneManager.scene_loaded", "change_scene"]:
        res = search_database(db, q, limit=3, addon="scene_manager")
        print(q, len(res), res[0].chunk_type if res else "none", res[0].symbol if res else "none")
PY
```

### 建议提交信息

```text
Index addon API symbol aliases
```

---

## P1-2：重算 README benchmark 和 coverage

### 目标

README 当前 benchmark 数字来自旧数据形状。切换 GDScript Scene Manager 后，应重算：

- 总 chunk 数。
- addon chunk 数。
- 每个 addon 的 docs/examples/API 数。
- `change_scene`、`SceneManager`、`SceneManager.change_scene` 查询命中。

### 具体实现

新增本地脚本，建议放在：

- `scripts/benchmark_readme.py`

脚本职责：

1. 使用当前 `godot_rag/rag/godot_docs.sqlite`，如果不存在则提示先运行 `./build.sh --no-bump` 或 `./build.sh`。
2. 查询：
   - 总 chunks。
   - Godot docs chunks。
   - addon chunks。
   - 按 addon + chunk_type 聚合数量。
3. 对一组选定 query 跑 `search_database()` 并输出 markdown table 行。
4. 不自动改 README，先输出 markdown，人工确认后再贴入 README。

建议 queries：

- `change_scene`
- `SceneManager`
- `SceneManager.change_scene`，需要 P1-1 完成后再加入正式表。
- `BehaviorTree`
- `DialogueManager`
- `state machine transitions`
- `scene transition animation`
- `input helper gamepad`

### README 修改要求

更新 [README.md](/Users/jbts6/Site/godot-rag/README.md)：

- benchmark 的总数。
- `scene_manager` coverage 行。
- query 表里的旧数据。
- 如果 `SceneManager.change_scene` 尚未支持精确命中，不要把它写成主 benchmark query。

### 验收命令

```bash
rtk uv run pytest -q
rtk python3 scripts/benchmark_readme.py
```

### 建议提交信息

```text
Refresh README benchmark data
```

---

## P2-1：接入 Scene Manager Wiki 文档

### 目标

新 Scene Manager README 说明主要文档在 GitHub Wiki。当前 RAG 只能看到 README、demo 和本地源码，文档覆盖不足。

### 方案 A：submodule 接入 wiki

添加 wiki submodule：

```bash
rtk git submodule add https://github.com/glass-brick/Scene-Manager.wiki.git addons/scene_manager_wiki
```

然后在 addon discovery 中支持“外部 doc source 映射”。

缺点：需要设计 addon 与 wiki 目录的关联，且多一个 submodule。

### 方案 B：构建时可选拉取 wiki

在 `build.sh` 增加可选参数：

- `--with-wiki`

行为：

- clone/update wiki 到 `.cache/addon-wikis/scene_manager`
- RAG build 时额外纳入该目录为 `scene_manager` 的 docs

缺点：需要 addon_docs 支持额外文档入口。

### 推荐

先做方案 B。理由：

- 不污染 `addons/` 子模块列表。
- wiki 缺失不影响普通 build。
- 更符合“文档缓存”的性质。

### 实现提示

需要给 `rag.cli build` 增加参数，例如：

```bash
--addon-doc-source scene_manager=.cache/addon-wikis/scene_manager
```

或更简单地先写死在 `build.sh`，把 wiki 内容复制/同步到：

```text
addons/scene_manager/docs_wiki/
```

但不要提交复制后的 wiki 内容。

### 验收命令

```bash
rtk ./build.sh --no-bump --with-wiki
rtk godot-rag s-addon "Getting started" --addon scene_manager --db godot_rag/rag/godot_docs.sqlite
rtk godot-rag s-addon "API" --addon scene_manager --db godot_rag/rag/godot_docs.sqlite
```

### 建议提交信息

```text
Add optional Scene Manager wiki docs source
```

---

## P2-2：整理 scratch 和开发噪音

### 目标

避免 `.scratch/` 每次出现在 `git status`。

### 具体实现

修改 `.gitignore`：

```gitignore
.scratch/
```

如果希望保留某些 handoff，可改成：

```gitignore
.scratch/*
!.scratch/README.md
```

当前建议直接 ignore 整个 `.scratch/`。

### 验收命令

```bash
rtk git status --short
```

### 建议提交信息

```text
Ignore local scratch notes
```

---

## P2-3：addon 更新和 smoke test 工具

### 目标

让 addon submodule 更新后可以快速确认 RAG 仍能发现文档、示例和 API。

### 具体实现

新增脚本：

- `scripts/check_addons.py`

脚本输出：

- addon 名称。
- display name。
- doc file count。
- example file count。
- api file count。
- 关键 query smoke 结果。

关键 smoke queries：

- `statecharts`: `state machine`
- `dialogue_manager`: `DialogueManager`
- `doctor`: `verify_node_path`
- `scene_manager`: `change_scene`
- `limboai`: `BehaviorTree`

脚本应使用 `rst2md/rag/addon_docs.py` 的公开函数，不要重复实现发现逻辑。

### 验收命令

```bash
rtk PYTHONPATH=rst2md uv run python3 scripts/check_addons.py
rtk uv run pytest -q
```

### 建议提交信息

```text
Add addon coverage smoke script
```

---

## 推荐执行顺序

1. `P0-1 Harden build and publish workflow`
2. `P0-2 Add Python compatibility CI matrix`
3. `P1-1 Index addon API symbol aliases`
4. `P1-2 Refresh README benchmark data`
5. `P2-2 Ignore local scratch notes`
6. `P2-3 Add addon coverage smoke script`
7. `P2-1 Add optional Scene Manager wiki docs source`

其中 `P2-1` 牵涉设计最多，建议最后做。

## 每个提交前的固定检查

```bash
rtk uv run pytest -q
rtk bash -n build.sh
rtk git diff --check
```

如果改了发布逻辑，额外跑：

```bash
rtk ./build.sh --help
rtk ./build.sh --no-bump
```
