---
change: inheritance-traversal-source-recall
design-doc: docs/superpowers/specs/2026-07-02-inheritance-traversal-source-recall-design.md
base-ref: 9137b74a1bae4b6160b725b919728121c7fa82c0
---

# Inheritance Traversal Source Recall 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 `_search_database_impl` 中插入 step 3.5 inheritance-directed class_summary 召回，修复 `Node inherits Object` 查询的生产 gap（Node class_summary 不进 top_k=3 → inherits 遍历无源 → Object 不被召回 → rank=None）。

**Architecture:** 仅动**召回**层。在 symbol recall（step 1-3）之后、FTS（step 4）之前插入门控的 step 3.5：对 `plan.inheritance_intent=True` 的查询，按空白分词筛 PascalCase token，对每个候选查 `chunks WHERE symbol=? AND chunk_type='class_summary'` 验证，验证通过者以 90.0 分写入候选集并记录 `inheritance_recall.class_summary` 信号。Node 以 90 分进 top_k=3 → 既有的 inherits 遍历代码（`searcher.py:384-442`，**不动**）触发 → Object 经 `inherits` 边被拉入。

**Tech Stack:** Python 3.10+、SQLite + FTS5、`rag.searcher._search_database_impl`、`rag.query_plan.QueryPlan`、`rag.models.RankingSignal`、pytest（unittest 风格）、`uv run godot-rag eval-search`。

**Design Doc:** `docs/superpowers/specs/2026-07-02-inheritance-traversal-source-recall-design.md`

**Tasks 边界:** `openspec/changes/inheritance-traversal-source-recall/tasks.md`

## Global Constraints

- **不改排序数学**：RRF k=60、`fts_score = min(40.0, max(0.0, 40.0 / (1.0 + bm25 * 0.01)))`、embeddings 模型、chunker schema 全部不动。
- **不改 inherits 遍历代码**：`rst2md/rag/searcher.py:382-442` 的 `if plan.inheritance_intent:` 遍历块保持原样。
- **不引入 LLM reranker。**
- **不新增 eval 查询**：保留 45 条（38 baseline-gated + 7 report_only，含 `class-inheritance-node-object`）。
- **eval 基线**：38 baseline-gated 查询 Hit@5 ≥ 97.37%、MRR@5 ≥ 87.50%，32 原通过查询零回归。
- **`Node inherits Object`**（report_only，required_at=5）：当前 rank=None → 修复后 rank ≤ 5。
- **分数常量**：step 3.5 召回分 `90.0`（低于 `symbol_recall.exact=100`，高于 FTS cap `40` / RRF `~36.8`），信号名 `inheritance_recall.class_summary`。
- **门控**：step 3.5 整体由 `if plan.inheritance_intent:` 门控，与既有 inherits 遍历同条件。
- **DB 事实**（`./godot_rag.db`）：Node class_summary `symbol="Node"`、text 含 `**Inherits:** \`Object\``；Object class_summary `symbol="Object"`。
- **源代码导入风格**：源码用 `from rag.module import ...`（构建时重写为 `from godot_rag.rag.module`），测试同。
- **运行环境**：`uv run pytest -q`（全量）、`uv run godot-rag eval-search`（评估）。

---

## File Structure

| 文件 | 职责 | 本计划动作 |
|------|------|-----------|
| `rst2md/rag/searcher.py` | 混合搜索引擎主实现，含 `_search_database_impl` | **修改**：加 `import re` + 模块级 regex 常量；在 step 1-3 与 step 4 之间插入 step 3.5 召回块 |
| `rst2md/tests/test_rag_search.py` | 搜索引擎测试套件（unittest 风格） | **修改**：新增 `InheritanceRecallTests` 类（Red 测试 + D4 门控回归测试） |
| `docs/search-quality/inheritance-recall-stage-0.json` | 修复前 eval 基线快照 | **创建**：stage-0 基线（`Node inherits Object` rank=None） |
| `docs/search-quality/inheritance-recall-final.json` | 修复后 eval 基线快照 | **创建**：final 基线（`Node inherits Object` rank ≤ 5） |
| `docs/search-quality/baseline.json` | 项目 canonical 基线 | **更新**：用 final 基线覆盖 |

**不动的文件**：`rst2md/rag/query_plan.py`（`_inheritance_intent` / `QueryPlan.inheritance_intent` 已就绪）、`rst2md/rag/relations.py`（`extract_inherits` / `build_chunk_relations` 已就绪）、`rst2md/rag/fusion.py`（RRF / rerank 不动）、`rst2md/rag/models.py`（`RankingSignal` 不动）。

---

## Task 0: 锁定 stage-0 基线与 DB 事实

**对应 tasks.md**：0.1、0.2

**Files:**
- Read: `./godot_rag.db`（生产 eval DB）
- Create: `docs/search-quality/inheritance-recall-stage-0.json`

**Interfaces:**
- Consumes: `./godot_rag.db`、`rst2md/rag/search_eval_queries.json`（45 条 golden queries）
- Produces: stage-0 基线 JSON（含 `class-inheritance-node-object` rank=None 的事实记录），供 Task 3 对比

- [x] **Step 1: 确认生产 eval DB 存在**

Run:
```bash
rtk ls -lh ./godot_rag.db
```
Expected: 文件存在，大小 > 10MB。若不存在，停止并询问用户——本计划依赖该 DB。

- [x] **Step 2: 写 stage-0 基线（`--write-baseline` 跳过对比，仅快照）**

Run:
```bash
rtk mkdir -p docs/search-quality
rtk uv run godot-rag eval-search --db ./godot_rag.db --write-baseline --baseline docs/search-quality/inheritance-recall-stage-0.json
```
Expected: 退出码 0；写入 `docs/search-quality/inheritance-recall-stage-0.json`；stdout 文本报告显示 `class-inheritance-node-object` 行为 "MISS" / rank=None（report_only 查询不拉低 baseline 指标，但出现在 diagnostics 里）。38 baseline-gated 查询的 Hit@5/MRR@5 即为修复前基线（应 ≥ 97.37% / ≥ 87.50%）。

- [x] **Step 3: SQL 确认 Node / Object class_summary 字段（tasks.md 0.2）**

Run:
```bash
rtk uv run python -c "
from rag.db import get_connection
with get_connection('./godot_rag.db') as c:
    for sym in ('Node','Object'):
        r = c.execute(\"SELECT id, symbol, chunk_type, substr(text, 1, 120) AS preview FROM chunks WHERE symbol=? AND chunk_type='class_summary'\", (sym,)).fetchone()
        print(sym, dict(r) if r else 'NOT FOUND')
    # 确认 Node -> Object 的 inherits 边存在
    e = c.execute(\"SELECT source_id, target_id, relation, weight FROM chunk_relations WHERE relation='inherits' AND source_id=(SELECT id FROM chunks WHERE symbol='Node' AND chunk_type='class_summary')\").fetchall()
    print('Node inherits edges:', [dict(x) for x in e])
"
```
Expected: Node 行 `id=5710`（或近似）、`symbol="Node"`、`chunk_type="class_summary"`、preview 含 `**Inherits:** \`Object\``；Object 行 `symbol="Object"`、`chunk_type="class_summary"`；Node 的 inherits 边 target 指向 Object class_summary 的 id、`weight=0.8`。若任一不符，停止——设计文档的 DB 事实前提不成立。

- [x] **Step 4: Commit stage-0 基线**

```bash
rtk git add docs/search-quality/inheritance-recall-stage-0.json
rtk git commit -m "chore(search-quality): lock stage-0 baseline for inheritance-traversal-source-recall"
```

---

## Task 1: TDD Red — 复现 inheritance-recall gap

**对应 tasks.md**：1.2（Red 阶段）

**Files:**
- Modify: `rst2md/tests/test_rag_search.py`（在 `InheritsGraphTraversalTests` 类之后、`if __name__ == "__main__":` 之前插入新类）

**Interfaces:**
- Consumes: `rag.searcher.search_database`、`rag.indexer.build_database`、`rag.embeddings`（monkeypatch 为空 list 禁用向量）
- Produces: 失败测试 `test_inheritance_recall_pulls_class_summary_into_top_k`，锚定 step 3.5 的契约（Node+Object 进 top-5、Node 含 `inheritance_recall.class_summary` 信号）

**Red 机理**：当前代码无 step 3.5 → `inheritance_recall.class_summary` 信号不存在 → 第 3 条断言必然失败（可靠 Red 锚点）。同时构造的 noise DB（ScrollBar/Slider/PopupPanel 的继承链文本含 Node+Object）使 FTS cap-40 平局动态接近生产 gap。

**注意**：已有的 `InheritsGraphTraversalTests.test_node_inherits_object_reaches_object_class_summary`（`test_rag_search.py:1677`）在无 noise 的小 DB 上**已通过**——它不复现生产 gap，本任务新增的 noise DB 才是真正的 Red。

- [x] **Step 1: 写失败测试**

在 `rst2md/tests/test_rag_search.py` 中定位 `InheritsGraphTraversalTests` 类的结尾（约 line 1708，`self.assertIn("graph.inherits", names)` 行之后）与 `if __name__ == "__main__":`（line 1711）之间的空行。用 Edit 在该位置插入新类。

`oldString`（定位插入点，唯一匹配 `InheritsGraphTraversalTests` 末尾 + main 守卫）：
```python
            names = [s.name for s in obj.ranking_signals]
            self.assertIn("graph.inherits", names)


if __name__ == "__main__":
    unittest.main()
```

`newString`：
```python
            names = [s.name for s in obj.ranking_signals]
            self.assertIn("graph.inherits", names)


class InheritanceRecallTests(unittest.TestCase):
    """Step 3.5 inheritance-directed class_summary recall.

    Reproduces the production gap: query ``Node inherits Object`` floods FTS
    top_k with noise class_summary chunks (each inheritance chain mentions
    Node and Object), leaving Node's class_summary out of the candidate set
    so the inherits traversal at searcher.py:384 never fires and Object is
    never recalled. Step 3.5 recalls Node's class_summary directly so it
    enters top_k and the traversal can pull Object via the inherits edge.
    """

    def _build_db_with_noise(self, tmp):
        from rag import embeddings
        from unittest.mock import patch
        from rag.indexer import build_database

        docs = Path(tmp) / "docs"
        classes = docs / "classes"
        classes.mkdir(parents=True)
        (classes / "class_node.md").write_text(
            "# Node\n\nBase class for scene nodes.\n\n**Inherits:** `Object`\n\n",
            encoding="utf-8",
        )
        (classes / "class_object.md").write_text(
            "# Object\n\nRoot of all things.\n\n",
            encoding="utf-8",
        )
        # Noise class_summary chunks whose inheritance-chain text mentions both
        # Node and Object, so they match the FTS query "Node inherits Object"
        # and flood top_k=3, reproducing the production gap.
        (classes / "class_scrollbar.md").write_text(
            "# ScrollBar\n\nA scrollbar control.\n\n"
            "**Inherits:** `Range` **<** `Control` **<** `CanvasItem` **<** `Node` **<** `Object`\n\n",
            encoding="utf-8",
        )
        (classes / "class_slider.md").write_text(
            "# Slider\n\nA slider control.\n\n"
            "**Inherits:** `Range` **<** `Control` **<** `CanvasItem` **<** `Node` **<** `Object`\n\n",
            encoding="utf-8",
        )
        (classes / "class_popuppanel.md").write_text(
            "# PopupPanel\n\nA popup container.\n\n"
            "**Inherits:** `Window` **<** `Viewport` **<** `Node` **<** `Object`\n\n",
            encoding="utf-8",
        )
        db_path = Path(tmp) / "t.sqlite"
        # Disable vectors (empty embeddings list) so the search runs in
        # FTS-only mode and the FTS-cap-at-40 tie dynamics match the gap.
        with patch.object(embeddings, "generate_embeddings", lambda texts: []):
            build_database(docs, db_path)
        return db_path

    def test_inheritance_recall_pulls_class_summary_into_top_k(self):
        from rag.searcher import search_database

        with tempfile.TemporaryDirectory() as tmp:
            db_path = self._build_db_with_noise(tmp)
            results = search_database(
                db_path, "Node inherits Object", limit=5, expand_graph=True,
            )
        symbols = [r.symbol for r in results]
        self.assertIn(
            "Node", symbols,
            "Node class_summary should be recalled into top-5 by step 3.5",
        )
        self.assertIn(
            "Object", symbols,
            "Object class_summary should be reached (via step 3.5 recall or inherits traversal)",
        )
        node = next(r for r in results if r.symbol == "Node")
        names = [s.name for s in node.ranking_signals]
        self.assertIn(
            "inheritance_recall.class_summary", names,
            "Node must carry the inheritance_recall.class_summary signal (D3)",
        )


if __name__ == "__main__":
    unittest.main()
```

- [x] **Step 2: 运行新测试，确认 Red**

Run:
```bash
rtk uv run pytest -q rst2md/tests/test_rag_search.py::InheritanceRecallTests::test_inheritance_recall_pulls_class_summary_into_top_k -v
```
Expected: **FAIL**。失败原因含 `AssertionError: 'inheritance_recall.class_summary' not found in [...]`（第 3 条断言失败——可靠 Red 锚点）。前两条断言（`"Node"` / `"Object"` in symbols）在该 noise DB 上可能通过也可能失败——只要整体测试 FAIL 即为合格 Red。

- [x] **Step 3: Commit Red 测试**

```bash
rtk git add rst2md/tests/test_rag_search.py
rtk git commit -m "test(searcher): add failing test for inheritance class_summary recall gap"
```

---

## Task 2: TDD Green — 实现 step 3.5 召回逻辑

**对应 tasks.md**：1.1（方案已由 design brainstorming 确认）、1.2（Green 阶段）、1.3（pytest 回归）

**Files:**
- Modify: `rst2md/rag/searcher.py`（顶部 imports + 模块级常量；`_search_database_impl` 内 step 1-3 与 step 4 之间插入 step 3.5）
- Modify: `rst2md/tests/test_rag_search.py`（在 `InheritanceRecallTests` 类内追加 D4 门控回归测试）

**Interfaces:**
- Consumes: `rag.query_plan.QueryPlan`（`plan.inheritance_intent: bool`、`plan.original: str`）、`rag.models.RankingSignal`、`rag.db.get_connection` 的 `conn`、`_make_result` / `_record_signal` 闭包、`type_filter` / `type_params` / `addon_filter` / `addon_params`
- Produces: 在 `results` dict 中写入/更新 class_summary 候选（score=90.0、信号 `inheritance_recall.class_summary`），供后续 sort（line 308）→ top_k=3（line 312）→ inherits 遍历（line 384-442）消费

- [x] **Step 1: 加 `import re` 到 searcher.py 顶部**

Edit `rst2md/rag/searcher.py`：

`oldString`：
```python
import sqlite3
from pathlib import Path
from typing import List, Optional
```

`newString`：
```python
import re
import sqlite3
from pathlib import Path
from typing import List, Optional
```

- [x] **Step 2: 加模块级 PascalCase regex 常量（D1）**

Edit `rst2md/rag/searcher.py`——在 retrieval import 块结束（`vector_search,` + `)`）与 `def search_database_with_metadata(` 之间插入常量。

`oldString`（唯一匹配 retrieval import 闭合 + 函数定义头）：
```python
from rag.retrieval import (  # noqa: F401
    _FTS5_SPECIAL,
    _escape_fts5,
    _run_fts_query,
    _run_vector_query,
    _smart_tokenize,
    _vector_availability,
    vector_search,
)


def search_database_with_metadata(
```

`newString`：
```python
from rag.retrieval import (  # noqa: F401
    _FTS5_SPECIAL,
    _escape_fts5,
    _run_fts_query,
    _run_vector_query,
    _smart_tokenize,
    _vector_availability,
    vector_search,
)

# PascalCase class-name candidates for inheritance-directed recall (D1).
# Godot class names follow PascalCase; the subsequent DB validation
# (symbol=? AND chunk_type='class_summary') filters non-class PascalCase
# tokens like the keyword "Inherits".
_INHERITANCE_CLASS_NAME_RE = re.compile(r'^[A-Z][a-zA-Z0-9_]+$')


def search_database_with_metadata(
```

- [x] **Step 3: 插入 step 3.5 召回块（D2 + D3 + D4）**

Edit `rst2md/rag/searcher.py`——在 step 1-3 symbol recall 的 prefix 匹配块结束（`symbol_recall.prefix` 信号 `_record_signal` 闭合）与 step 4 FTS 注释之间插入 step 3.5。

`oldString`（唯一匹配 prefix 信号块 + FTS 注释，跨 line 239-249）：
```python
                    _record_signal(
                        results[cid],
                        RankingSignal(
                            name="symbol_recall.prefix",
                            weight=40.0,
                            value=candidate,
                            details={"alias_derived": alias_derived},
                        ),
                    )

        # 4. FTS5 search (bm25 → 0-40 score, skip chunks already in fused results)
```

`newString`：
```python
                    _record_signal(
                        results[cid],
                        RankingSignal(
                            name="symbol_recall.prefix",
                            weight=40.0,
                            value=candidate,
                            details={"alias_derived": alias_derived},
                        ),
                    )

        # 3.5. Inheritance-directed class_summary recall (D2). When the query
        # signals inheritance intent (D4), pull class_summary chunks for
        # PascalCase tokens so they enter the candidate set before top_k
        # selection. Without this, FTS floods top_k with noise class_summary
        # chunks and the inherits traversal at line 384 has no class_summary
        # source to traverse. Score 90.0 (D3): below symbol_recall.exact=100,
        # above FTS cap=40 / RRF~36.8 — guarantees entry into top_k=3.
        if plan.inheritance_intent:
            seen_classes: set[str] = set()
            for token in plan.original.split():
                if not _INHERITANCE_CLASS_NAME_RE.match(token):
                    continue
                if token in seen_classes:
                    continue
                seen_classes.add(token)
                rows = conn.execute(
                    "SELECT c.* FROM chunks c "
                    "WHERE c.symbol = ? AND c.chunk_type = 'class_summary'"
                    + type_filter + addon_filter,
                    [token] + type_params + addon_params,
                ).fetchall()
                for row in rows:
                    cid = row["id"]
                    recall_score = 90.0
                    if cid not in results or results[cid]["score"] < recall_score:
                        prior = (
                            results[cid].get("ranking_signals", [])
                            if cid in results else []
                        )
                        results[cid] = _make_result(
                            row, recall_score, ranking_signals=prior,
                        )
                        _record_signal(
                            results[cid],
                            RankingSignal(
                                name="inheritance_recall.class_summary",
                                weight=recall_score,
                                value=token,
                                details={"source": "inheritance_intent_recall"},
                            ),
                        )

        # 4. FTS5 search (bm25 → 0-40 score, skip chunks already in fused results)
```

**注意 `c.*` / `c.symbol` 别名**：`type_filter` / `addon_filter` 用 `c.doc_type` / `c.addon` 别名（见 line 89/96），所以 step 3.5 查询必须用 `FROM chunks c` + `c.*` / `c.symbol` / `c.chunk_type`，否则 SQL 报 `no such column: c.doc_type`。

- [x] **Step 4: 运行 Task 1 测试，确认 Green**

Run:
```bash
rtk uv run pytest -q rst2md/tests/test_rag_search.py::InheritanceRecallTests::test_inheritance_recall_pulls_class_summary_into_top_k -v
```
Expected: **PASS**。Node 以 90 分进 top_k=3 → inherits 遍历触发 → Object 被 `graph.inherits` 拉入（或被 step 3.5 直接召回），三者断言全过。

- [x] **Step 5: 追加 D4 门控回归测试**

在 `rst2md/tests/test_rag_search.py` 的 `InheritanceRecallTests` 类中、`test_inheritance_recall_pulls_class_summary_into_top_k` 方法之后追加（在类内、`if __name__` 之前）。

`oldString`（定位类末尾 + main 守卫）：
```python
        node = next(r for r in results if r.symbol == "Node")
        names = [s.name for s in node.ranking_signals]
        self.assertIn(
            "inheritance_recall.class_summary", names,
            "Node must carry the inheritance_recall.class_summary signal (D3)",
        )


if __name__ == "__main__":
    unittest.main()
```

`newString`：
```python
        node = next(r for r in results if r.symbol == "Node")
        names = [s.name for s in node.ranking_signals]
        self.assertIn(
            "inheritance_recall.class_summary", names,
            "Node must carry the inheritance_recall.class_summary signal (D3)",
        )

    def test_non_inheritance_query_does_not_trigger_inheritance_recall(self):
        """D4 gating: a non-inheritance query must never produce the
        inheritance_recall.class_summary signal (protects 32 baseline queries)."""
        from rag.searcher import search_database

        with tempfile.TemporaryDirectory() as tmp:
            db_path = self._build_db_with_noise(tmp)
            results = search_database(
                db_path, "Node add_child", limit=5, expand_graph=True,
            )
        for r in results:
            for sig in r.ranking_signals:
                self.assertNotEqual(
                    sig.name, "inheritance_recall.class_summary",
                    "inheritance_recall signal must not fire for non-inheritance "
                    "queries (D4 gating)",
                )


if __name__ == "__main__":
    unittest.main()
```

**验证 query 选择**：`"Node add_child"` 不含 `inherits`/`subclass of`/`parent class`/`derived from`（见 `query_plan._INHERITANCE_KEYWORDS`），故 `plan.inheritance_intent=False`，step 3.5 整体跳过。

- [x] **Step 6: 运行新测试，确认 Green**

Run:
```bash
rtk uv run pytest -q rst2md/tests/test_rag_search.py::InheritanceRecallTests -v
```
Expected: 2 passed（`test_inheritance_recall_pulls_class_summary_into_top_k` + `test_non_inheritance_query_does_not_trigger_inheritance_recall`）。

- [x] **Step 7: 全套 pytest 回归（tasks.md 1.3）**

Run:
```bash
rtk uv run pytest -q
```
Expected: 全绿（基线 290 测试通过，0 失败）。重点关注 `test_rag_search.py`、`test_searcher_module.py`、`test_semantic_search.py`、`test_search_eval.py` 无回归。若任何测试失败，**不要提交**——回到 Step 3 检查 step 3.5 是否破坏了既有候选集聚合逻辑（特别留意 `results[cid]["score"] < recall_score` 的比较是否覆盖了既有高分候选）。

- [x] **Step 8: Commit Green 实现**

```bash
rtk git add rst2md/rag/searcher.py rst2md/tests/test_rag_search.py
rtk git commit -m "feat(searcher): recall class_summary for inheritance-intent queries (step 3.5)"
```

---

## Task 3: eval-search 验证 + 锁定 final 基线 + 收尾

**对应 tasks.md**：2.1、2.2、2.3、3.1、3.2

**Files:**
- Create: `docs/search-quality/inheritance-recall-final.json`
- Update: `docs/search-quality/baseline.json`

**Interfaces:**
- Consumes: `./godot_rag.db`（已含修复后的 searcher，因为 `uv run godot-rag` 从源码加载）、`rst2md/rag/search_eval_queries.json`、stage-0 基线
- Produces: final 基线 + 更新的 canonical baseline + verify 阶段材料清单

- [ ] **Step 1: 跑 eval-search 对比 stage-0 基线（tasks.md 2.1 + 2.2）**

Run:
```bash
rtk uv run godot-rag eval-search --db ./godot_rag.db --baseline docs/search-quality/inheritance-recall-stage-0.json
```
Expected:
- 退出码 0（无回归）。
- `class-inheritance-node-object`（report_only）：rank ≤ 5（修复前 rank=None）。在文本报告中该行从 MISS 变为 OK 或在 diagnostics 中显示 rank ∈ [1,5]。`expected_paths=["classes/class_node.md"]` 命中。
- 38 baseline-gated 查询：Hit@5 ≥ 97.37%、MRR@5 ≥ 87.50%、无 `regression_failed` 标记。
- 32 原通过查询：无状态翻转为 FAIL。

若 `class-inheritance-node-object` 仍 rank > 5，说明 step 3.5 在生产 DB 上未把 Node 推进 top_k=3——回到 Task 2 Step 3 检查 PascalCase 提取或 DB 验证查询是否在生产 DB 上命中（设计文档 D1 已确认 Node class_summary symbol="Node"）。

- [ ] **Step 2: 写 final 基线（tasks.md 2.3）**

Run:
```bash
rtk uv run godot-rag eval-search --db ./godot_rag.db --write-baseline --baseline docs/search-quality/inheritance-recall-final.json
```
Expected: 退出码 0；写入 `docs/search-quality/inheritance-recall-final.json`。

- [ ] **Step 3: 更新 canonical baseline.json**

```bash
rtk cp docs/search-quality/inheritance-recall-final.json docs/search-quality/baseline.json
```

- [ ] **Step 4: 复跑全套 pytest 收尾（tasks.md 3.1）**

Run:
```bash
rtk uv run pytest -q
```
Expected: 全绿。

- [ ] **Step 5: 准备 verify 阶段材料（tasks.md 3.2）**

在仓库根创建临时汇总（不入库，仅供 `/comet-verify` 读取）：
```bash
rtk cat > /tmp/inheritance-recall-verify-summary.md <<'EOF'
# inheritance-traversal-source-recall verify 材料

## 修复
- searcher.py step 3.5：inheritance_intent 门控的 class_summary PascalCase 召回，score=90.0，信号 inheritance_recall.class_summary

## 证据
- TDD Red → Green：InheritanceRecallTests 2 测试通过
- 全套 pytest：290/0
- eval-search（./godot_rag.db）：
  - class-inheritance-node-object: rank=None → rank ≤ 5
  - 38 baseline-gated: Hit@5 ≥ 97.37%、MRR@5 ≥ 87.50%
  - 32 原通过查询零回归
- 基线：stage-0 与 final 已锁定到 docs/search-quality/

## 未改
- inherits 遍历代码 searcher.py:382-442
- 排序数学 / RRF k=60 / embeddings / chunker schema
- eval 查询集（45 条）
EOF
```

- [ ] **Step 6: Commit final 基线 + canonical baseline 更新**

```bash
rtk git add docs/search-quality/inheritance-recall-final.json docs/search-quality/baseline.json
rtk git commit -m "chore(search-quality): lock final baseline after inheritance-traversal-source-recall"
```

---

## Self-Review

**1. Spec coverage**（对照 design doc 决策与边界）：
- D1（PascalCase + DB 验证）→ Task 2 Step 2（regex 常量）+ Step 3（`_INHERITANCE_CLASS_NAME_RE.match` + `WHERE c.symbol=? AND c.chunk_type='class_summary'`）。✓
- D2（step 3.5 插入位置）→ Task 2 Step 3（prefix 信号块与 FTS 注释之间）。✓
- D3（分数 90.0 + 信号名）→ Task 2 Step 3（`recall_score = 90.0` + `name="inheritance_recall.class_summary"` + `details={"source": "inheritance_intent_recall"}`）。✓
- D4（`plan.inheritance_intent` 门控）→ Task 2 Step 3（`if plan.inheritance_intent:`）+ Step 5（门控回归测试）。✓
- 边界条件表（类名不在 DB / 无 PascalCase / 多类名 / chunk 已在结果集 / 非 inheritance 查询）→ Step 3 代码覆盖（DB 验证返回空即跳过；`seen_classes` 去重；`if cid not in results or results[cid]["score"] < recall_score` 高分更新 + 追加信号；门控跳过）+ Task 1/2 测试覆盖多类名（Node+Object）与非 inheritance 查询。✓
- TDD Red → Green → 回归 → Task 0 基线 + Task 1 Red + Task 2 Green + Task 3 eval。✓
- binding constraints（不改排序/RRF/embeddings/chunker、不改 inherits 遍历、不引入 LLM、不增 eval 查询、eval 基线阈值、Node rank ≤ 5）→ Global Constraints + 各 Task 验证步骤。✓

**2. Placeholder scan**：无 TBD/TODO/"implement later"/"add error handling"；每个代码步骤含完整可运行代码；命令含 expected output。✓

**3. Type / 命名一致性**：
- `_INHERITANCE_CLASS_NAME_RE`：Task 2 Step 2 定义、Step 3 引用——一致。
- `inheritance_recall.class_summary`：Task 1 测试断言、Task 2 Step 3 信号名、Task 2 Step 5 门控测试——一致。
- `recall_score = 90.0`：design D3、Global Constraints、Task 2 Step 3——一致。
- `plan.inheritance_intent` / `plan.original`：`QueryPlan` dataclass 字段（`query_plan.py:80,74`）、Task 2 Step 3 引用——一致。
- `_make_result(row, score, ranking_signals=None)` / `_record_signal(candidate, signal)`：定义于 `searcher.py:99,119`，Task 2 Step 3 调用签名一致。
- `type_filter` / `type_params` / `addon_filter` / `addon_params`：定义于 `searcher.py:85-97`，Step 3 复用——一致。
- 测试类名 `InheritanceRecallTests`、辅助 `_build_db_with_noise`：Task 1 Step 1 定义、Task 2 Step 5 复用——一致。

无类型/命名漂移。✓
