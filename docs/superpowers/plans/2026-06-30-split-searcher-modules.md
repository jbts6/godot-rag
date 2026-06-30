---
change: split-searcher-modules
design-doc: docs/superpowers/specs/2026-06-30-split-searcher-modules-design.md
base-ref: de8d9a2a9872f95cf14f70600e52908a9fe10ea8
---

# Split Searcher Modules 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 `rst2md/rag/searcher.py`（526 行、13 顶层函数）按职责拆为 `retrieval.py` / `fusion.py` / `snippet.py` 三个 focused sub-module，searcher.py 瘦身为 facade + 编排，行为 byte-for-byte 等价、不改排名。

**Architecture:** 单向分层 `store.py → searcher.py → retrieval/fusion/snippet → db/models/query_plan`。`_search_database_impl` 作为编排层留在 searcher.py，按原顺序调用各 focused module 的函数。searcher.py 顶部用 `from rag.<module> import <name>` 形式 re-export store.py facade 所需的全部 11 个符号（保 `store.py` 零改动 + `test_semantic_search.py` 的 `monkeypatch.setattr(searcher, ...)` 仍生效）。`embeddings` 局部 import 随 `_search_database_impl` 留在 searcher.py。

**Tech Stack:** Python 3.x，pytest，SQLite + FTS5 + sqlite-vec，Godot RAG（`uv run pytest`，`pythonpath=["rst2md"]`，`testpaths=["rst2md/tests"]`）。

## Global Constraints

源码只动 `rst2md/rag/`；`godot_rag/rag/` 是构建产物，由 `./build.sh` 同步，禁止手动改。测试用 `uv run pytest -q`。公开接口（`search_database` / `search_database_with_metadata` 签名与返回结构、排名结果、fallback 行为、DB schema）全部不变。不改排名权重、不换 embedding、不动 `query_plan.py` / `db.py` / `symbols.py` / `models.py` / `store.py`。不实现 graph expansion（`rg` 已确认 `rst2md/rag/` 对 `graph|expand|neighbor|edge` 零命中，措辞沿自旧时代）。不引入新运行时依赖。

### 设计调和说明（执行层，必读）

设计 D1 字面写「私有 helper 移到新模块且 searcher 不 re-export」，但 `rst2md/rag/store.py:6-18` 现状用 `from rag.searcher import (...)` re-export 了 11 个符号（含 7 个私有 helper：`_FTS5_SPECIAL` / `_escape_fts5` / `_extract_snippet` / `_run_vector_query` / `_smart_tokenize` / `_vector_availability` / `rrf_fusion`），带 `# noqa: F401 — re-export for backward compat`。`rst2md/tests/test_rag_search.py:282` 通过 `from rag.store import _smart_tokenize` 依赖此 re-export。若 searcher 严格执行「不 re-export 私有 helper」，`store.py` 的 import 会 ImportError，连锁击穿所有 store 用户，违反 Non-Goals「不动 store.py facade」。

**调和结论**：D1 的「不 re-export」理解为「不为 `test_searcher_module.py` 的 importability 契约而 re-export（该测试按方案 A 改路径）」；但**为 `store.py` facade 的 backward compat 而 re-export** store 所需的 11 个符号（带 `# noqa: F401` 注释）。这是 D1 与 Non-Goals 冲突时的最小破坏解：保 `store→searcher` 单向分层、`store.py` 零改动、`test_rag_search.py` / `test_semantic_search.py` 零改动。

**import 形式约束（关键）**：searcher.py 顶部对 retrieval/fusion/snippet 的 import 必须用 `from rag.<module> import <name>` 形式，**不可**用 `import rag.<module> as _m; _m.<name>(...)` 形式。原因：`test_semantic_search.py:243-244` 用 `monkeypatch.setattr(searcher, "_run_vector_query", fail_vector_search)` 模拟 vector 失败。`_search_database_impl` 定义在 searcher.py，其函数体内调用 `_run_vector_query(...)` 走 searcher 模块全局查找（`searcher.__dict__['_run_vector_query']`）。`from rag.retrieval import _run_vector_query` 使该名字成为 searcher 模块全局，monkeypatch 替换它即生效；若改用模块限定名调用则 monkeypatch 失效、`test_search_metadata_reports_vector_query_failure` 会假绿（vector 不再 fail，走 hybrid 而非 fallback）。因此 searcher.py 必须保持 `from ... import ...` 形式，且 `_search_database_impl` 体内对这些函数的调用保持 bare name（不限定模块）。

### 验证套件

- **4 个测试文件**：`rst2md/tests/test_searcher_module.py` / `test_rag_search.py` / `test_semantic_search.py` / `test_rag_addon.py`
- **45 条 query 确定性套件**：`rst2md/tests/test_search_eval.py` + `rst2md/tests/test_search_eval_cli.py`（确定性，无 DB 依赖；绿 = 结果等价）
- **p50/p95 延迟基准**：`uv run godot-rag eval-search --db godot_rag.db --baseline docs/search-quality/baseline.json --compare-graph`（仅当 `godot_rag.db` 存在时跑；容差 ±5%）

---

## File Structure

| 文件 | 职责 | 本 change 动作 |
|------|------|----------------|
| `rst2md/rag/retrieval.py` | 候选召回：vector 查询、FTS5 查询构造、tokenize/escape、vec 表可用性 | **新建** |
| `rst2md/rag/fusion.py` | RRF 融合 + rerank bonus | **新建** |
| `rst2md/rag/snippet.py` | 片段提取 | **新建** |
| `rst2md/rag/searcher.py` | facade + 编排（`_search_database_impl` + 公开 API + re-export） | **瘦身**（删 10 个移走的函数 + 改 import 块 + 删 orphan import） |
| `rst2md/rag/store.py` | facade（re-export 给外部） | **不动**（靠 searcher re-export 兼容） |
| `rst2md/tests/test_searcher_module.py` | importability 契约 + rerank 单元 | **改 12 处 import 路径 + docstring** |
| `rst2md/tests/test_rag_search.py` | 通过 `from rag.store import` 测 helper | **不动** |
| `rst2md/tests/test_semantic_search.py` | monkeypatch searcher + 45 query 等价 + fallback | **不动** |

函数落位（设计 D2）：

| 模块 | 函数 |
|------|------|
| `retrieval.py` | `_FTS5_SPECIAL`, `_smart_tokenize`, `_escape_fts5`, `vector_search`, `_vector_availability`, `_run_vector_query`, `_run_fts_query` |
| `fusion.py` | `rrf_fusion`, `_rerank_bonus`, `rerank_results` |
| `snippet.py` | `_extract_snippet` |
| `searcher.py`（瘦身后） | `_search_database_impl`（编排），`search_database`，`search_database_with_metadata`；re-export 上述 10 个 + `vector_search` |

---

## Task 1: 基线快照

**Files:**
- Read: `rst2md/rag/searcher.py`（确认 526 行、13 顶层函数现状）
- Generate: `docs/superpowers/plans/.baseline-split-searcher-modules.txt`（基线输出存档，供前后对比）

**Interfaces:**
- Consumes: 当前 `git rev-parse HEAD` = `de8d9a2a9872f95cf14f70600e52908a9fe10ea8`（base-ref）
- Produces: 一份全绿基线（pytest 通过数 + test_search_eval 通过数），后续每个 Task 的 verify 与之对比

- [ ] **Step 1: 跑全量测试套件记录基线**

Run:
```bash
uv run pytest -q rst2md/tests/test_searcher_module.py rst2md/tests/test_rag_search.py rst2md/tests/test_semantic_search.py rst2md/tests/test_rag_addon.py rst2md/tests/test_search_eval.py rst2md/tests/test_search_eval_cli.py 2>&1 | tee docs/superpowers/plans/.baseline-split-searcher-modules.txt
```
Expected: 全绿，结尾 `N passed`。记录通过数 `N` 供后续对比。若 `test_search_eval*.py` 计数与设计所述 45 条 query 不符，以实际数字 `N` 为基线（不调整断言）。

- [ ] **Step 2:（可选）p50/p95 延迟基线**

仅当 `godot_rag.db` 存在时执行：
```bash
uv run godot-rag eval-search --db godot_rag.db --baseline docs/search-quality/baseline.json --compare-graph 2>&1 | tee -a docs/superpowers/plans/.baseline-split-searcher-modules.txt
```
Expected: 通过 gate，记录 p50/p95 数值。若 DB 不存在则跳过（确定性套件已护等价），在基线文件末尾追加一行 `# p50/p95 skipped: godot_rag.db not found`。

- [ ] **Step 3: 确认 git 工作树干净 + base-ref**

Run:
```bash
git status --short && git rev-parse HEAD
```
Expected: 工作树干净（无输出），HEAD = `de8d9a2a9872f95cf14f70600e52908a9fe10ea8`。

- [ ] **Step 4: Commit 基线存档**

```bash
git add docs/superpowers/plans/.baseline-split-searcher-modules.txt
git commit -m "chore(split-searcher-modules): record pre-split baseline"
```

---

## Task 2: 拆 fusion 模块（最独立，无下游依赖）

**Files:**
- Create: `rst2md/rag/fusion.py`
- Modify: `rst2md/rag/searcher.py`（删 `rrf_fusion`/`_rerank_bonus`/`rerank_results` 函数体；改 import 块 re-export）
- Test: `rst2md/tests/test_searcher_module.py` / `rst2md/tests/test_semantic_search.py` / `rst2md/tests/test_search_eval.py`

**Interfaces:**
- Consumes: `from rag.models import SearchResult`（dataclass frozen），`from rag.query_plan import QueryPlan`，`from dataclasses import replace`
- Produces: `rrf_fusion(fts_results: List[dict], vec_results: List[dict], k: int = 60) -> List[dict]`；`_rerank_bonus(plan: QueryPlan, result: SearchResult) -> float`；`rerank_results(plan: QueryPlan, results: list[SearchResult]) -> list[SearchResult]`。签名/行为与原 searcher.py 一字不差。

- [ ] **Step 1: 创建 `rst2md/rag/fusion.py`（完整内容）**

写入以下完整文件（函数体 verbatim 自 `searcher.py:74-128`）：

```python
"""RRF fusion and rerank for search results.

Focused sub-module split from searcher.py (change: split-searcher-modules).
Behavior is byte-for-byte identical to the previous searcher.py implementation.
"""
from dataclasses import replace
from typing import List

from rag.models import SearchResult
from rag.query_plan import QueryPlan


def rrf_fusion(fts_results: List[dict], vec_results: List[dict], k: int = 60) -> List[dict]:
    """Fuse FTS5 and vector search results using Reciprocal Rank Fusion.

    Args:
        fts_results: FTS5 results with 'id' key.
        vec_results: Vector results with 'id' and 'distance' keys.
        k: RRF parameter (default 60).

    Returns:
        Fused results sorted by RRF score, with 'rrf_score' key added.
    """
    scores = {}

    for rank, result in enumerate(fts_results):
        chunk_id = result['id']
        scores[chunk_id] = scores.get(chunk_id, 0) + 1.0 / (k + rank)

    for rank, result in enumerate(vec_results):
        chunk_id = result['id']
        scores[chunk_id] = scores.get(chunk_id, 0) + 1.0 / (k + rank)

    sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

    results = []
    for chunk_id in sorted_ids:
        result = next((r for r in fts_results if r['id'] == chunk_id), None)
        if result is None:
            result = next((r for r in vec_results if r['id'] == chunk_id), None)
        if result:
            result = dict(result)
            result['rrf_score'] = scores[chunk_id]
            results.append(result)

    return results


def _rerank_bonus(plan: QueryPlan, result: SearchResult) -> float:
    bonus = 0.0
    if result.symbol in plan.alias_symbol_candidates:
        bonus += 5.0
    elif result.symbol in plan.symbol_candidates:
        bonus += 2.0
    if plan.doc_type_intent and result.doc_type == plan.doc_type_intent and not plan.symbol_candidates:
        bonus += 0.05
    if plan.addon_intent and result.doc_type == "addon":
        bonus += 0.5
    return bonus


def rerank_results(plan: QueryPlan, results: list[SearchResult]) -> list[SearchResult]:
    boosted = [
        replace(result, score=result.score + _rerank_bonus(plan, result))
        for result in results
    ]
    return sorted(boosted, key=lambda result: result.score, reverse=True)
```

- [ ] **Step 2: 修改 `rst2md/rag/searcher.py` 顶部 import 块，re-export fusion 符号**

在 searcher.py 顶部现有 import 块之后（`from rag.symbols import normalize_symbol` 这一行之后）新增 re-export 块。**注意 import 形式约束（见 Global Constraints）：必须用 `from rag.fusion import ...` 形式。**

新增内容（插入到 `from rag.symbols import normalize_symbol` 之后、`_FTS5_SPECIAL = ...` 之前）：

```python
from rag.fusion import (  # noqa: F401 — rrf_fusion re-exported for store.py facade; rerank_results used by _search_database_impl
    rerank_results,
    rrf_fusion,
)
```

> 注：`_rerank_bonus` 不在 searcher re-export 列表——grep 确认 `store.py` 与 `test_searcher_module.py` 均不 import 它，searcher 自身也不调用（`rerank_results` 在 fusion 内部调它）。它只活在 `fusion.py` 内部。

- [ ] **Step 3: 删除 `rst2md/rag/searcher.py` 中 `rrf_fusion` / `_rerank_bonus` / `rerank_results` 三个函数定义**

删除 searcher.py 中以下行范围的函数体（含函数签名行与尾随空行，共约 55 行：原 `rrf_fusion` line 74-107、`_rerank_bonus` line 110-120、`rerank_results` line 123-128）。删除后 searcher.py 不再定义这三个函数，改为通过 Step 2 的 re-export 引用。

执行者用 Edit 工具，逐个函数删除（匹配从 `def rrf_fusion(...)` 到其 `return results` 后的空行；`def _rerank_bonus(...)` 到 `return bonus` 后空行；`def rerank_results(...)` 到 `return sorted(...)` 后空行）。删除后这三个名字在 searcher 模块全局由 re-export 提供，`_search_database_impl` 体内的 `rrf_fusion(...)`（line 349）与 `rerank_results(plan, search_results)`（line 525）调用保持 bare name 不变。

- [ ] **Step 4: 跑 focused 测试 + 45 query 套件**

Run:
```bash
uv run pytest -q rst2md/tests/test_searcher_module.py rst2md/tests/test_semantic_search.py rst2md/tests/test_search_eval.py
```
Expected: 全绿，通过数与 Task 1 基线一致。重点看 `test_rrf_fusion` / `test_rrf_fusion_empty` / `test_rrf_fusion_single_source` / `test_rrf_fusion_basic` / `test_rerank_promotes_alias_symbol_match` / `test_rerank_symbol_query_does_not_apply_tutorial_intent` 全绿（这些直接调 `rrf_fusion` / `rerank_results`，此时仍从 `rag.searcher` import，靠 re-export 生效）。

- [ ] **Step 5: 跑全量套件确认无回归**

Run:
```bash
uv run pytest -q rst2md/tests/test_searcher_module.py rst2md/tests/test_rag_search.py rst2md/tests/test_semantic_search.py rst2md/tests/test_rag_addon.py rst2md/tests/test_search_eval.py rst2md/tests/test_search_eval_cli.py
```
Expected: 全绿，通过数 = Task 1 基线 `N`。

- [ ] **Step 6: Commit**

```bash
git add rst2md/rag/fusion.py rst2md/rag/searcher.py
git commit -m "refactor(split-searcher-modules): extract fusion.py (rrf_fusion, _rerank_bonus, rerank_results)"
```

verify: searcher re-export fusion 符号，store.py 零改动，全量测试绿。

---

## Task 3: 拆 snippet 模块

**Files:**
- Create: `rst2md/rag/snippet.py`
- Modify: `rst2md/rag/searcher.py`（删 `_extract_snippet`；re-export）

**Interfaces:**
- Consumes: 无外部依赖（纯字符串操作）
- Produces: `_extract_snippet(text: str, query: str, context_lines: int = 3) -> str`

- [ ] **Step 1: 创建 `rst2md/rag/snippet.py`（完整内容）**

写入以下完整文件（函数体 verbatim 自 `searcher.py:131-160`）：

```python
"""Snippet extraction for search results.

Focused sub-module split from searcher.py (change: split-searcher-modules).
Behavior is byte-for-byte identical to the previous searcher.py implementation.
"""


def _extract_snippet(text: str, query: str, context_lines: int = 3) -> str:
    """Extract a snippet from text around the first line containing query keywords."""
    lines = text.split('\n')
    query_lower = query.lower()
    keywords = query_lower.split()

    # Find first line containing any keyword
    match_idx = None
    for i, line in enumerate(lines):
        line_lower = line.lower()
        if any(kw in line_lower for kw in keywords):
            match_idx = i
            break

    if match_idx is None:
        # No match found, return first few lines
        return '\n'.join(lines[:context_lines * 2 + 1])

    # Extract context around match
    start = max(0, match_idx - context_lines)
    end = min(len(lines), match_idx + context_lines + 1)

    snippet_lines = []
    if start > 0:
        snippet_lines.append('...')
    snippet_lines.extend(lines[start:end])
    if end < len(lines):
        snippet_lines.append('...')

    return '\n'.join(snippet_lines)
```

- [ ] **Step 2: 修改 `rst2md/rag/searcher.py` 顶部 import 块，re-export snippet 符号**

在 Task 2 新增的 fusion re-export 块之后追加：

```python
from rag.snippet import _extract_snippet  # noqa: F401 — re-export for store.py facade backward compat
```

- [ ] **Step 3: 删除 `rst2md/rag/searcher.py` 中 `_extract_snippet` 函数定义**

删除 searcher.py 中 `def _extract_snippet(...)` 到 `return '\n'.join(snippet_lines)` 后空行的整段（原 line 131-160）。`_search_database_impl` 体内 `snippet=_extract_snippet(r["text"], query)`（line 521）保持 bare name 不变。

- [ ] **Step 4: 跑 focused 测试 + 45 query 套件**

Run:
```bash
uv run pytest -q rst2md/tests/test_searcher_module.py rst2md/tests/test_semantic_search.py rst2md/tests/test_search_eval.py
```
Expected: 全绿，通过数与基线一致。`test_import_extract_snippet` 靠 re-export 生效。

- [ ] **Step 5: 跑全量套件确认无回归**

Run:
```bash
uv run pytest -q rst2md/tests/test_searcher_module.py rst2md/tests/test_rag_search.py rst2md/tests/test_semantic_search.py rst2md/tests/test_rag_addon.py rst2md/tests/test_search_eval.py rst2md/tests/test_search_eval_cli.py
```
Expected: 全绿，通过数 = 基线 `N`。

- [ ] **Step 6: Commit**

```bash
git add rst2md/rag/snippet.py rst2md/rag/searcher.py
git commit -m "refactor(split-searcher-modules): extract snippet.py (_extract_snippet)"
```

verify: searcher re-export `_extract_snippet`，全量测试绿。

---

## Task 4: 拆 retrieval 模块 + searcher 瘦身收尾

**Files:**
- Create: `rst2md/rag/retrieval.py`
- Modify: `rst2md/rag/searcher.py`（删 7 个 retrieval 符号 + 删 orphan import `import re` / `from dataclasses import replace` + 收窄 `query_plan` import；re-export retrieval 符号；确认编排体不变）

**Interfaces:**
- Consumes: `from rag.symbols import normalize_symbol`（`_run_fts_query` 用），`import re` / `import sqlite3` / `from typing import List`
- Produces: `_FTS5_SPECIAL`（set），`_smart_tokenize(query: str) -> str`，`_escape_fts5(query: str) -> str`，`vector_search(conn, query_embedding: List[float], limit: int = 10) -> List[dict]`，`_vector_availability(conn) -> tuple[bool, str]`，`_run_vector_query(conn, query_embedding, limit, type_filter, type_params, addon_filter, addon_params)`，`_run_fts_query(conn, query, limit, fts_type_filter, fts_type_params, fts_addon_filter, fts_addon_params, fused_exclude="", fused_exclude_params=None) -> list[dict]`

- [ ] **Step 1: 创建 `rst2md/rag/retrieval.py`（完整内容）**

写入以下完整文件（函数体 verbatim 自 `searcher.py:13-71` + `163-199` + `233-259`）：

```python
"""Candidate retrieval: vector + FTS5 query construction and execution.

Focused sub-module split from searcher.py (change: split-searcher-modules).
Behavior is byte-for-byte identical to the previous searcher.py implementation.
"""
import re
import sqlite3
from typing import List

from rag.symbols import normalize_symbol


_FTS5_SPECIAL = set('"*+-:()^')


def _smart_tokenize(query: str) -> str:
    """Split dotted/snake_case symbols into separate tokens for FTS5.

    "Node.add_child" → '"Node" AND "add" AND "child"'
    Plain queries pass through unchanged.
    """
    # Only split if query contains . or _ (likely a symbol)
    if '.' not in query and '_' not in query:
        return _escape_fts5(query)

    tokens = re.split(r'[._]', query)
    fts_tokens = []
    for t in tokens:
        if not t:
            continue
        if any(c in _FTS5_SPECIAL for c in t):
            escaped = t.replace('"', '""')
            fts_tokens.append(f'"{escaped}"')
        else:
            fts_tokens.append(t)
    return " AND ".join(fts_tokens) if fts_tokens else _escape_fts5(query)


def _escape_fts5(query: str) -> str:
    """Escape FTS5 special characters so the query is treated as literal text.

    FTS5 does not support backslash escaping. Tokens containing special
    characters are wrapped in double quotes (phrase matching). Plain tokens
    are left as-is so multi-word queries retain implicit AND semantics.
    """
    tokens = []
    for token in query.split():
        if any(c in _FTS5_SPECIAL for c in token):
            escaped = token.replace('"', '""')
            tokens.append(f'"{escaped}"')
        else:
            tokens.append(token)
    return ' '.join(tokens)


def vector_search(conn, query_embedding: List[float], limit: int = 10) -> List[dict]:
    """Search for similar chunks using vector embeddings.

    Args:
        conn: SQLite connection.
        query_embedding: Query vector (256 dimensions).
        limit: Maximum number of results.

    Returns:
        List of dicts with 'id' and 'distance' keys.
    """
    results = conn.execute(
        "SELECT chunk_id, distance FROM vec_chunks WHERE embedding MATCH ? AND k = ?",
        (str(query_embedding), limit)
    ).fetchall()

    return [{'id': row[0], 'distance': row[1]} for row in results]


def _vector_availability(conn) -> tuple[bool, str]:
    try:
        # Check if vec_chunks table exists and is queryable
        vec_count = conn.execute("SELECT COUNT(*) FROM vec_chunks").fetchone()[0]
    except sqlite3.OperationalError as exc:
        message = str(exc).lower()
        if "no such table" in message or "no such module" in message:
            return False, "missing_vec_chunks"
        return False, "vector_query_failed"

    # Check if vec_chunks is empty
    if vec_count == 0:
        return False, "empty_vec_chunks"

    # Check row count parity with chunks table
    try:
        chunks_count = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        if vec_count != chunks_count:
            return False, "vector_row_count_mismatch"
    except sqlite3.OperationalError:
        return False, "vector_query_failed"

    return True, ""


def _run_vector_query(conn, query_embedding, limit, type_filter, type_params, addon_filter, addon_params):
    vec_query = (
        "SELECT vc.chunk_id, vc.distance FROM vec_chunks vc "
        "JOIN chunks c ON vc.chunk_id = c.id "
        "WHERE vc.embedding MATCH ? AND k = ?"
        + type_filter + addon_filter
    )
    vec_rows = conn.execute(
        vec_query,
        [str(query_embedding), limit * 3] + type_params + addon_params,
    ).fetchall()
    return [{'id': row[0], 'distance': row[1]} for row in vec_rows]


def _run_fts_query(
    conn, query: str, limit: int,
    fts_type_filter: str, fts_type_params: list,
    fts_addon_filter: str, fts_addon_params: list,
    fused_exclude: str = "", fused_exclude_params: list | None = None,
) -> list[dict]:
    if fused_exclude_params is None:
        fused_exclude_params = []
    escaped_query = _smart_tokenize(normalize_symbol(query))
    rows = conn.execute(
        f"""
        SELECT c.id, c.path, c.start_line, c.end_line, c.doc_type,
               c.chunk_type, c.addon, c.addon_name, c.symbol, c.heading,
               c.breadcrumb, c.text,
               bm25(chunks_fts) as score
        FROM chunks_fts
        JOIN chunks c ON chunks_fts.rowid = c.id
        WHERE chunks_fts MATCH ?
        {fts_type_filter}
        {fts_addon_filter}
        {fused_exclude}
        ORDER BY score
        LIMIT ?
        """,
        [escaped_query] + fts_type_params + fts_addon_params + fused_exclude_params + [limit * 3],
    ).fetchall()
    return [{"id": row["id"], "score": row["score"], "row": row} for row in rows]
```

- [ ] **Step 2: 修改 `rst2md/rag/searcher.py` 顶部 import 块，re-export retrieval 符号**

在 Task 3 新增的 snippet re-export 之后追加（**`from ... import ...` 形式，遵守 import 形式约束**）。retrieval 的 7 个符号中，4 个（`_run_fts_query` / `_run_vector_query` / `_smart_tokenize` / `_vector_availability`）被 `_search_database_impl` 直接调用（used），3 个（`_FTS5_SPECIAL` / `_escape_fts5` / `vector_search`）是 store facade re-export only：

```python
# _run_fts_query/_run_vector_query/_smart_tokenize/_vector_availability: used by _search_database_impl.
# _FTS5_SPECIAL/_escape_fts5/vector_search: re-exported for store.py facade (noqa: F401).
from rag.retrieval import (  # noqa: F401
    _FTS5_SPECIAL,
    _escape_fts5,
    _run_fts_query,
    _run_vector_query,
    _smart_tokenize,
    _vector_availability,
    vector_search,
)
```

- [ ] **Step 3: 删除 `rst2md/rag/searcher.py` 中 7 个 retrieval 符号的定义**

逐个删除以下定义段（删除后这些名字由 Step 2 re-export 提供）：
- `_FTS5_SPECIAL = set('"*+-:()^')`（原 line 13）
- `def _smart_tokenize(...)` 整段（原 line 15-35）
- `def _escape_fts5(...)` 整段（原 line 38-52）
- `def vector_search(...)` 整段（原 line 55-71）
- `def _vector_availability(...)` 整段（原 line 163-185）
- `def _run_vector_query(...)` 整段（原 line 188-199）
- `def _run_fts_query(...)` 整段（原 line 233-259）

`_search_database_impl` 体内对这些函数的调用（line 336 `_smart_tokenize(query)`、line 328 `_run_vector_query(...)`、line 430 `_run_fts_query(...)`、line 280 `_vector_availability(conn)`）保持 bare name 不变——由 re-export 提供模块全局绑定。

- [ ] **Step 4: 删除 `rst2md/rag/searcher.py` 的 orphan import**

本 Task 的删除使以下 import 在 searcher.py 中不再被使用（CLAUDE.md「Surgical Changes」要求清理自己造成的 orphan）：
- 删 `import re`（仅 `_smart_tokenize` 用，已移走）
- 删 `from dataclasses import replace`（仅 `_rerank_bonus` 用，Task 2 已移走）
- 收窄 `from rag.query_plan import QueryPlan, build_query_plan` → `from rag.query_plan import build_query_plan`（`QueryPlan` 类型注解随 `_rerank_bonus`/`rerank_results` 移到 fusion.py，searcher 的 `_search_database_impl` 不再用 `QueryPlan` 注解）

**保留**：`import sqlite3`（`_search_database_impl` line 345/449 的 `sqlite3.OperationalError`）、`from pathlib import Path`、`from typing import List, Optional`、`from rag.db import clean_chunk_text, get_connection`（`_make_result` line 316/497 用）、`from rag.models import SearchMetadata, SearchResponse, SearchResult`、`from rag.symbols import normalize_symbol`（line 370 用）。

- [ ] **Step 5: 确认 `_search_database_impl` 编排体与公开 API 未改一行**

Read searcher.py，确认以下三段 verbatim 保留、调用顺序不变：
- `_search_database_impl`（原 line 262-526）：编排顺序 `build_query_plan → _vector_availability → _run_vector_query + _smart_tokenize + rrf_fusion → _run_fts_query → _extract_snippet → rerank_results`，且 `from rag.embeddings import generate_embeddings`（原 line 325）局部 import 仍在函数体内（embeddings optional dependency 随编排层留 searcher）
- `search_database_with_metadata`（原 line 202-215）
- `search_database`（原 line 218-230）

Expected: 三段函数体无任何字符改动；仅顶部 import 块 + 删除的 10 个函数定义发生变化。

- [ ] **Step 6: 跑 focused 测试 + fallback 路径测试（monkeypatch 关键验证）**

Run:
```bash
uv run pytest -q rst2md/tests/test_searcher_module.py rst2md/tests/test_semantic_search.py::test_search_metadata_reports_vector_query_failure rst2md/tests/test_semantic_search.py::test_search_metadata_reports_fts_only_when_vec_table_missing rst2md/tests/test_semantic_search.py::test_search_metadata_reports_empty_vec_chunks rst2md/tests/test_semantic_search.py::test_search_metadata_reports_vector_row_count_mismatch rst2md/tests/test_semantic_search.py::test_search_skips_embeddings_when_vec_table_missing
```
Expected: 全绿。**重点**：`test_search_metadata_reports_vector_query_failure` 必须绿——它验证 `monkeypatch.setattr(searcher, "_run_vector_query", fail_vector_search)` 仍能触发 fallback（mode=fts_only, fallback_reason=vector_query_failed）。若它假绿（vector 不 fail 仍走 hybrid），说明 import 形式违反约束（Step 2 改成了模块限定名），立即回 Step 2 确认用 `from rag.retrieval import (...)` 形式。

- [ ] **Step 7: 跑全量套件 + 45 query 确认无回归**

Run:
```bash
uv run pytest -q rst2md/tests/test_searcher_module.py rst2md/tests/test_rag_search.py rst2md/tests/test_semantic_search.py rst2md/tests/test_rag_addon.py rst2md/tests/test_search_eval.py rst2md/tests/test_search_eval_cli.py
```
Expected: 全绿，通过数 = 基线 `N`。

- [ ] **Step 8: Commit**

```bash
git add rst2md/rag/retrieval.py rst2md/rag/searcher.py
git commit -m "refactor(split-searcher-modules): extract retrieval.py + slim searcher to facade+orchestration"
```

verify: searcher 仅剩 `_search_database_impl` + 公开 API + 三块 re-export；store.py 零改动；monkeypatch 测试绿；全量测试绿。

---

## Task 5: 改 `test_searcher_module.py` import 路径（方案 A）

**Files:**
- Modify: `rst2md/tests/test_searcher_module.py`（12 处 import 改路径 + 2 处 docstring）

**Interfaces:**
- Consumes: Task 2-4 产出的 `rag.retrieval` / `rag.fusion` / `rag.snippet` 模块
- Produces: importability 契约测试从 focused module 直接导入（断言不变，仍 `assertTrue(callable(...))` / `assertIsInstance(...)`）

设计 D6：改路径，断言不变。共 12 处 `from rag.searcher import X` 改路径（移动函数的）；3 处保留 `from rag.searcher`（`search_database` / `search_database_with_metadata` / `_search_database_impl`）。

- [ ] **Step 1: 更新 docstring**

修改 `rst2md/tests/test_searcher_module.py`：
- line 1: `"""TDD test: search functions should be importable from rag.searcher."""` → `"""TDD test: search functions are importable from their focused modules."""`
- line 7: `"""Verify that search functions are importable from rag.searcher."""` → `"""Verify that search functions are importable from their focused modules."""`

- [ ] **Step 2: 改 12 处 import 路径（断言不变）**

按 D6 分组替换（`replace_all` 按符号精确替换；每处只改 `from rag.searcher import X` 的模块部分，断言行不动）：

retrieval（6 处）：
- `from rag.searcher import _smart_tokenize` → `from rag.retrieval import _smart_tokenize`（line 10）
- `from rag.searcher import _escape_fts5` → `from rag.retrieval import _escape_fts5`（line 14）
- `from rag.searcher import vector_search` → `from rag.retrieval import vector_search`（line 18）
- `from rag.searcher import _vector_availability` → `from rag.retrieval import _vector_availability`（line 38）
- `from rag.searcher import _run_vector_query` → `from rag.retrieval import _run_vector_query`（line 42）
- `from rag.searcher import _FTS5_SPECIAL` → `from rag.retrieval import _FTS5_SPECIAL`（line 46）

fusion（5 处：`rrf_fusion` 2 处 + `rerank_results` 3 处）：
- `from rag.searcher import rrf_fusion` → `from rag.fusion import rrf_fusion`（line 22 `test_import_rrf_fusion` 与 line 58 `test_rrf_fusion_basic`，共 2 处，用 `replace_all`）
- `from rag.searcher import rerank_results` → `from rag.fusion import rerank_results`（line 54 `test_import_rerank_results`、line 142 `test_rerank_promotes_alias_symbol_match`、line 182 `test_rerank_symbol_query_does_not_apply_tutorial_intent`，共 3 处，用 `replace_all`）

snippet（1 处）：
- `from rag.searcher import _extract_snippet` → `from rag.snippet import _extract_snippet`（line 34）

保留不动（3 处）：`from rag.searcher import search_database`（line 26）、`from rag.searcher import search_database_with_metadata`（line 30）、`from rag.searcher import _search_database_impl`（line 50）。

替换后核对：`grep -n "from rag.searcher import" rst2md/tests/test_searcher_module.py` 应只剩 3 行（search_database / search_database_with_metadata / _search_database_impl）。

- [ ] **Step 3: 跑 `test_searcher_module.py` 确认 importability 契约从 focused module 成立**

Run:
```bash
uv run pytest -q rst2md/tests/test_searcher_module.py
```
Expected: 全绿。12 个 import 测试 + `test_rrf_fusion_basic` + 2 个 rerank 测试 + query_rewrite/query_plan 等其他测试全过。这验证 focused module 自身可独立 import（不再依赖 searcher re-export）。

- [ ] **Step 4: 跑全量套件确认无回归**

Run:
```bash
uv run pytest -q rst2md/tests/test_searcher_module.py rst2md/tests/test_rag_search.py rst2md/tests/test_semantic_search.py rst2md/tests/test_rag_addon.py rst2md/tests/test_search_eval.py rst2md/tests/test_search_eval_cli.py
```
Expected: 全绿，通过数 = 基线 `N`。`test_rag_search.py` 的 `from rag.store import _smart_tokenize`（line 282/290/295）仍靠 store re-export 生效，不动。

- [ ] **Step 5: Commit**

```bash
git add rst2md/tests/test_searcher_module.py
git commit -m "test(split-searcher-modules): point importability tests at focused modules (scheme A)"
```

verify: 12 处 import 改路径，3 处保留 searcher，断言不变，全量测试绿。

---

## Task 6: 全量验证与延迟对比

**Files:**
- Read: `docs/superpowers/plans/.baseline-split-searcher-modules.txt`（Task 1 基线）

**Interfaces:**
- Consumes: Task 2-5 全部完成后的拆分后状态
- Produces: 拆分后全量绿 + p50/p95 无回归（容差 ±5%）的证据

- [ ] **Step 1: 跑全量 `uv run pytest -q`**

Run:
```bash
uv run pytest -q
```
Expected: 全绿，通过数 = 基线 `N`（全量套件含本 change 未触及的其他测试文件，确认无连锁回归）。

- [ ] **Step 2: 跑 45 query 确定性套件最终对比**

Run:
```bash
uv run pytest -q rst2md/tests/test_search_eval.py rst2md/tests/test_search_eval_cli.py
```
Expected: 全绿。绿 = 拆分前后排名结果 byte-级一致（确定性套件即等价快照）。

- [ ] **Step 3:（可选）p50/p95 延迟对比**

仅当 `godot_rag.db` 存在且 Task 1 Step 2 跑过基线时执行：
```bash
uv run godot-rag eval-search --db godot_rag.db --baseline docs/search-quality/baseline.json --compare-graph
```
Expected: gate 通过；p50/p95 相对基线漂移 ≤ ±5%（多一层 import 不应超此阈值）。若超容差，先排查是否 import 形式违反约束导致 monkeypatch 假绿使 vector 路径异常；排除后再判断是否可接受。

- [ ] **Step 4: 确认 git 工作树状态**

Run:
```bash
git log --oneline -6 && git status --short
```
Expected: 最近 5 个 commit 为 Task 1-5 的 commit；工作树干净（除可能的基线/日志文件外）。

verify: 全量绿 + 45 query 等价 +（若适用）p50/p95 无回归。

---

## Task 7: build.sh 同步构建产物 + WIP 更新

**Files:**
- Modify（由 build.sh 自动）: `godot_rag/rag/*.py`（构建产物，禁止手改）
- Modify: `WIP.md`（标记第 3 步完成、归档 graph expansion 过时描述）

**Interfaces:**
- Consumes: Task 2-5 完成的 `rst2md/rag/` 源码
- Produces: `godot_rag/rag/` 同步含 `retrieval.py` / `fusion.py` / `snippet.py`，import 被改写为 `from godot_rag.rag.<module>`

- [ ] **Step 1: 运行 build.sh 同步构建产物**

Run:
```bash
./build.sh
```
Expected: build 成功，无错误。`build.sh` 把 `rst2md/rag/*.py` 复制到 `godot_rag/rag/`，并把 `from rag.` 改写为 `from godot_rag.rag.`。确认 `godot_rag/rag/retrieval.py` / `fusion.py` / `snippet.py` 已生成。

Run:
```bash
ls godot_rag/rag/retrieval.py godot_rag/rag/fusion.py godot_rag/rag/snippet.py
```
Expected: 三个文件均存在。

- [ ] **Step 2: 验证构建产物 import 正确**

Run:
```bash
uv run python -c "from godot_rag.rag.searcher import search_database, search_database_with_metadata, vector_search; from godot_rag.rag.retrieval import _smart_tokenize, _run_vector_query; from godot_rag.rag.fusion import rrf_fusion, rerank_results; from godot_rag.rag.snippet import _extract_snippet; print('imports ok')"
```
Expected: 输出 `imports ok`，无 ImportError。

- [ ] **Step 3: 更新 WIP.md**

Read `WIP.md`，按 tasks.md 6.4：标记第 3 步（searcher 拆分）完成；归档/删除 graph expansion 的过时描述（设计已确认 graph expansion 未实现、措辞过时）。具体措辞按 WIP.md 现有风格，最小改动。

- [ ] **Step 4: Commit 源码改动与 WIP（不含 build.sh 自动版本号）**

注意：`build.sh` 会自动递增版本号，**不要手动 commit 版本号**（CLAUDE.md 警告：手动 commit 导致版本跳号）。只 commit WIP.md 与源码状态：

```bash
git add WIP.md
git commit -m "docs(split-searcher-modules): mark searcher split done, retire stale graph-expansion wording"
```

`godot_rag/rag/` 构建产物的提交时机按项目惯例（通常由 `./build.sh --publish` 流程处理版本号 + 产物）；本 Task 仅验证产物同步成功，不手动 commit 产物文件。

verify: build.sh 成功生成三个新模块产物，import 链路通，WIP 更新。

---

## Rollback

公开接口保持不变，revert 拆分 commit（Task 2-5）或把代码移回 `searcher.py` 即可。`store.py` 全程未改，无回滚成本。基线文件 `docs/superpowers/plans/.baseline-split-searcher-modules.txt` 保留供事后对比。
