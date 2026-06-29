---
change: record-search-eval-versions
design-doc: docs/superpowers/specs/2026-06-29-record-search-eval-versions-design.md
base-ref: f926b125cef77dff592b027c753768073814f5d9
archived-with: 2026-06-29-record-search-eval-versions
---

# Record Search Evaluation Versions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在搜索质量评估报告与 baseline 中记录 evaluator/search 版本元数据，使 baseline 自描述产生指标所用的代码版本。

**Architecture:** 在 `rst2md/rag/search_eval.py` 加一个解析 package version 的 helper（`importlib.metadata` → `tomllib` 解析 `pyproject.toml` → `"unknown"`），在 `report_to_dict` 的 `metadata` 块下新增 `versions` 字段。`apply_baseline(write_baseline=True)` 复用 `report_to_dict`，无需单独 baseline 写入路径。`compare_with_baseline` 不查 `versions`，老 baseline 缺 `versions` 自动容忍。

**Tech Stack:** Python 3.10+、stdlib（`importlib.metadata`、`tomllib`）、pytest、uv、OpenSpec。

## Global Constraints

- 源码在 `rst2md/rag/`，**禁止读取或编辑 `godot_rag/rag/*.py`**（构建产物）。
- 不改 ranking、query loading、baseline 比较阈值、database 结构。
- `pyproject.toml`：`name = "godot-rag"`，`version = "4.7.0.post10"`，`requires-python = ">=3.10"`。
- 测试命令：`uv run pytest -q`；构建命令：`uv build`；CLI 入口：`godot-rag = "rag.cli:main"`。
- baseline 数据库：`./godot_rag.db`（项目根）；baseline 产物：`docs/search-quality/baseline.json`。
- 每个 task 验收后：勾选 `openspec/changes/record-search-eval-versions/tasks.md` 对应项 → `git commit`，commit message 体现设计意图，结尾带 `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`。
- `metadata` 仅在 `report.database` 存在时写入（`report_to_dict` 现有 gating），`versions` 作为 `metadata` 的同级键，与 `query_suite_hash`/`database` 一起序列化。

archived-with: 2026-06-29-record-search-eval-versions
---

## Task 1: 版本元数据 helper 与 report_to_dict 序列化（TDD）

**Files:**
- Modify: `rst2md/rag/search_eval.py`（在 `report_to_dict` 之前加 `_package_version` + `_evaluation_versions`；在 `report_to_dict` 的 `metadata` 块加 `versions`）
- Test: `rst2md/tests/test_search_eval.py`（在 `test_apply_baseline_writes_metadata` 之后追加两个聚焦测试）

**Interfaces:**
- Consumes: `report.database`（`DatabaseFingerprint | None`）、`report.query_suite_hash`（已有字段，本任务不动）
- Produces: `_package_version() -> str`、`_evaluation_versions() -> dict[str, str]`；`report_to_dict(report)` 在 `report.database` 非空时输出 `result["metadata"]["versions"] = {"evaluator": <ver>, "search": <ver>}`

**对应 OpenSpec tasks：** 1.1（写聚焦失败测试）、1.2（实现版本元数据序列化）

- [x] **Step 1: 写失败测试**

在 `rst2md/tests/test_search_eval.py` 末尾的 `test_apply_baseline_writes_metadata`（约 line 549-567）之后追加：

```python
def test_report_to_dict_includes_version_metadata():
    report = EvaluationReport(
        overall={"count": 1, "hit@1": 1.0, "hit@3": 1.0, "hit@5": 1.0, "mrr@5": 1.0},
        categories={},
        failures=[],
        query_results=[],
        graph_changes=[],
        database=DatabaseFingerprint("godot_rag.db", 123, 10, 20, 30, 20),
        query_suite_hash="abc123",
    )

    data = report_to_dict(report)

    versions = data["metadata"]["versions"]
    assert isinstance(versions["evaluator"], str) and versions["evaluator"]
    assert isinstance(versions["search"], str) and versions["search"]
    assert versions["evaluator"] == versions["search"]


def test_apply_baseline_write_includes_version_metadata(tmp_path):
    report = EvaluationReport(
        overall={"count": 1, "hit@1": 1.0, "hit@3": 1.0, "hit@5": 1.0, "mrr@5": 1.0},
        categories={},
        failures=[],
        query_results=[],
        graph_changes=[],
        database=DatabaseFingerprint("godot_rag.db", 123, 10, 20, 30, 20),
        query_suite_hash="abc123",
    )
    baseline = tmp_path / "baseline.json"

    apply_baseline(report, baseline, write_baseline=True)
    payload = json.loads(baseline.read_text(encoding="utf-8"))

    versions = payload["metadata"]["versions"]
    assert versions["evaluator"]
    assert versions["search"]
    assert versions["evaluator"] == versions["search"]
```

依赖的符号在文件已有 import 段中可用：`EvaluationReport`、`apply_baseline`（line 236 段），`report_to_dict`、`DatabaseFingerprint`（line 132 段），`json`（line 234 段）。

- [x] **Step 2: 运行测试，确认失败**

Run: `uv run pytest -q rst2md/tests/test_search_eval.py::test_report_to_dict_includes_version_metadata rst2md/tests/test_search_eval.py::test_apply_baseline_write_includes_version_metadata`
Expected: FAIL — `KeyError: 'versions'`（`metadata` 当前只有 `query_suite_hash` 和 `database`）

- [x] **Step 3: 实现 helper 并在 report_to_dict 加 versions**

在 `rst2md/rag/search_eval.py` 的 `_query_result_to_dict` 函数之后、`report_to_dict` 之前（约 line 622）插入两个 helper：

```python
def _package_version() -> str:
    """Resolve the godot-rag package version, falling back to pyproject.toml then 'unknown'."""
    try:
        from importlib.metadata import version as _dist_version

        return _dist_version("godot-rag")
    except Exception:
        pass
    try:
        import tomllib

        pyproject = Path(__file__).resolve().parents[2] / "pyproject.toml"
        with pyproject.open("rb") as handle:
            data = tomllib.load(handle)
        return str(data["project"]["version"])
    except Exception:
        return "unknown"


def _evaluation_versions() -> dict[str, str]:
    version = _package_version()
    return {"evaluator": version, "search": version}
```

`Path` 已在文件顶部导入（`from pathlib import Path`），无需新增 import。

然后修改 `report_to_dict` 的 `metadata` 块，在 `database` 之后加 `versions`。把：

```python
    if report.database:
        result["metadata"] = {
            "query_suite_hash": report.query_suite_hash,
            "database": {
                "path": report.database.path,
                "size_bytes": report.database.size_bytes,
                "documents": report.database.documents,
                "chunks": report.database.chunks,
                "symbols": report.database.symbols,
                "vectors": report.database.vectors,
            },
        }
    return result
```

改为：

```python
    if report.database:
        result["metadata"] = {
            "query_suite_hash": report.query_suite_hash,
            "database": {
                "path": report.database.path,
                "size_bytes": report.database.size_bytes,
                "documents": report.database.documents,
                "chunks": report.database.chunks,
                "symbols": report.database.symbols,
                "vectors": report.database.vectors,
            },
            "versions": _evaluation_versions(),
        }
    return result
```

- [x] **Step 4: 运行测试，确认通过**

Run: `uv run pytest -q rst2md/tests/test_search_eval.py::test_report_to_dict_includes_version_metadata rst2md/tests/test_search_eval.py::test_apply_baseline_write_includes_version_metadata`
Expected: PASS — 2 passed

- [x] **Step 5: 运行整个 search_eval 测试文件，确认无回归**

Run: `uv run pytest -q rst2md/tests/test_search_eval.py`
Expected: PASS — 所有现有测试 + 2 个新测试全通过（`test_apply_baseline_writes_metadata` 等仍通过，因为 `versions` 是新增键，不破坏现有 `query_suite_hash`/`database` 断言）

- [x] **Step 6: 勾选 tasks.md 1.1 与 1.2，提交**

把 `openspec/changes/record-search-eval-versions/tasks.md` 中 `- [ ] 1.1` 与 `- [ ] 1.2` 改为 `- [x]`。

```bash
git add rst2md/rag/search_eval.py rst2md/tests/test_search_eval.py openspec/changes/record-search-eval-versions/tasks.md
git commit -m "feat: serialize evaluator/search version metadata in search quality reports

Add _package_version helper (importlib.metadata -> tomllib pyproject.toml
-> 'unknown') and emit metadata.versions in report_to_dict so baselines
and JSON reports record which package version produced the evaluator and
search behavior.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

archived-with: 2026-06-29-record-search-eval-versions
---

## Task 2: 刷新 checked-in baseline 含版本元数据

**Files:**
- Modify: `docs/search-quality/baseline.json`（通过真实 evaluator 重新生成）

**Interfaces:**
- Consumes: Task 1 的 `report_to_dict` 含 `metadata.versions`；`./godot_rag.db`
- Produces: `docs/search-quality/baseline.json` 的 `metadata.versions` 含非空 `evaluator`/`search`

**对应 OpenSpec tasks：** 1.3（用真实数据库 baseline 刷新 checked-in baseline，含版本元数据）

- [x] **Step 1: 用真实 evaluator 对 godot_rag.db 重写 baseline**

Run: `uv run godot-rag eval-search --db godot_rag.db --baseline docs/search-quality/baseline.json --write-baseline --compare-graph`
Expected: 命令成功退出（`--write-baseline` 走 `apply_baseline(write_baseline=True)`，写入 `report_to_dict` 输出，含 `metadata.versions`；`--compare-graph` 让 `evaluate_database(compare_graph=True)` 产出与 baseline 一致的 graph_changes）

- [x] **Step 2: 验证 baseline 含 versions 且为非空字符串**

Run: `uv run python -c "import json; d=json.load(open('docs/search-quality/baseline.json')); v=d['metadata']['versions']; print(v); assert v['evaluator'] and v['search'], 'missing versions'; assert v['evaluator']==v['search']"`
Expected: 打印 `{'evaluator': '4.7.0.post10', 'search': '4.7.0.post10'}`（或源码树解析得到的当前 package version），无 AssertionError

- [x] **Step 3: 勾选 tasks.md 1.3，提交**

把 `tasks.md` 中 `- [ ] 1.3` 改为 `- [x]`。

```bash
git add docs/search-quality/baseline.json openspec/changes/record-search-eval-versions/tasks.md
git commit -m "feat: refresh search quality baseline with version metadata

Regenerate docs/search-quality/baseline.json against godot_rag.db so the
checked-in artifact carries metadata.versions (evaluator/search).

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

archived-with: 2026-06-29-record-search-eval-versions
---

## Task 3: 验证（聚焦测试 + 全量 + 构建 + baseline 比较 + OpenSpec）

**Files:**
- 无源码改动；仅运行验证命令并勾选 tasks.md

**对应 OpenSpec tasks：** 2.1（运行聚焦搜索评估测试）、2.2（运行全量测试、构建、search quality baseline 比较、OpenSpec 验证）

- [x] **Step 1: 聚焦搜索评估测试（2.1）**

Run: `uv run pytest -q rst2md/tests/test_search_eval.py`
Expected: PASS — 全部通过

- [x] **Step 2: 全量测试（2.2a）**

Run: `uv run pytest -q`
Expected: PASS — 全仓库测试通过，无回归

- [x] **Step 3: 构建（2.2b）**

Run: `uv build`
Expected: wheel 构建成功（`dist/godot_rag-4.7.0.post10-*.whl` 生成）

- [x] **Step 4: search quality baseline 比较（2.2c）**

Run: `uv run godot-rag eval-search --db godot_rag.db --baseline docs/search-quality/baseline.json --compare-graph`
Expected: 退出码 0（`report.regression_failed` 为 False；当前 evaluator 与刚刷新的 baseline 指标一致，无 hit@5/mrr@5 回归）

- [x] **Step 5: OpenSpec 验证（2.2d）**

Run: `npx openspec validate record-search-eval-versions --strict`
Expected: PASS — delta spec 符合 OpenSpec 规则，`semantic-search-quality` 的 "baseline includes evaluator and search versions" scenario 可被校验

- [x] **Step 6: 勾选 tasks.md 2.1 与 2.2，提交**

把 `tasks.md` 中 `- [ ] 2.1` 与 `- [ ] 2.2` 改为 `- [x]`。

```bash
git add openspec/changes/record-search-eval-versions/tasks.md
git commit -m "chore: complete record-search-eval-versions verification

Focused + full pytest, uv build, baseline comparison, and OpenSpec
validation all pass.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

archived-with: 2026-06-29-record-search-eval-versions
---

## Self-Review

**1. Spec coverage：**
- spec scenario "baseline includes database fingerprint" → 已有实现，Task 1 不动 ✓
- spec scenario "baseline includes query suite identity" → 已有实现，Task 1 不动 ✓
- spec scenario "baseline includes evaluator and search versions"（delta spec line 16-20）→ Task 1 实现 + 测试，Task 2 刷新 baseline 落地 ✓
- proposal "Add version metadata to reports and baselines" → Task 1 ✓
- proposal "Keep database fingerprint and query-suite hash unchanged" → Task 1 只新增 `versions` 键，不改既有键 ✓
- proposal "Refresh baseline.json" → Task 2 ✓
- proposal "Add regression tests that fail when version metadata is omitted" → Task 1 Step 1 两个测试在实现前会 KeyError 失败 ✓
- proposal "Tighten semantic-search-quality spec" → delta spec 已含该 scenario（design 阶段产物），无需 plan task ✓
- tasks.md 1.1 → Task 1 Step 1-2 ✓；1.2 → Task 1 Step 3-5 ✓；1.3 → Task 2 ✓；2.1 → Task 3 Step 1 ✓；2.2 → Task 3 Step 2-5 ✓

**2. Placeholder scan：** 无 TBD/TODO/"add appropriate error handling"/"similar to Task N"。所有代码步骤含完整代码，所有命令含预期输出。

**3. Type consistency：**
- `_evaluation_versions()` 返回 `dict[str, str]`，`report_to_dict` 用 `"versions": _evaluation_versions()` ✓
- 测试访问 `data["metadata"]["versions"]["evaluator"]` / `["search"]`，与 helper 输出键名一致 ✓
- `DatabaseFingerprint("godot_rag.db", 123, 10, 20, 30, 20)` 参数顺序匹配 dataclass（`path, size_bytes, documents, chunks, symbols, vectors`）✓
- `EvaluationReport` 构造参数匹配 dataclass 字段 ✓
- `apply_baseline(report, baseline, write_baseline=True)` 签名匹配 cli.py:252 调用 ✓
