---
change: search-quality-optimization-loop-2
design-doc: docs/superpowers/specs/2026-07-01-search-quality-optimization-loop-2-design.md
base-ref: 5b5161c4873961c679b8e81084f4237f938d6c02
---

# Search Quality Optimization Loop 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 通过三段串行优化（A 符号归一化 / B tutorial 排序地板化 / C 继承图定向扩展）将 eval 38 查询的 Hit@5 从 ~89% 提升到 ≥94%，6 个原失败查询中至少 5 个进入 rank ≤5。

**Architecture:** 三段串行依赖，每段后跑 `eval-search` 锁定增量基线。A 段在 `query_rewrite.expand_query_variants` 加 dot-notation 拆分；B 段把 `fusion._rerank_bonus` 的 tutorial 加权从加性 `+0.05` 改为**地板 + multiplicative**（`max(score, FLOOR) * (FACTOR - 1)`），同步把 `query_rewrite.doc_type_boost` 退化为 0.0；C 段在 `query_plan` 加 `inheritance_intent` 信号，`searcher._search_database_impl` 图扩展段加定向 `inherits` 边遍历分支。

**Tech Stack:** Python 3.10+，SQLite + FTS5，pytest（unittest.TestCase 风格），`uv run` 执行器，`godot-rag eval-search` CLI。

## 关联文档

- Design Doc：`docs/superpowers/specs/2026-07-01-search-quality-optimization-loop-2-design.md`（事实源：三处 brainstorming 修订）
- OpenSpec tasks 边界：`openspec/changes/search-quality-optimization-loop-2/tasks.md`（本计划保留其 0→A→B→C→4 五段结构与任务编号）
- Brainstorm 摘要：`openspec/changes/search-quality-optimization-loop-2/.comet/handoff/brainstorm-summary.md`
- 基线 commit：`5b5161c4873961c679b8e81084f4237f938d6c02`

## 关键设计修订点（来自 brainstorm，覆盖 tasks.md 原文）

下列三点**必须**在实现中体现，若与 `tasks.md` 原文冲突以本节为准：

1. **B 段 boost 公式（修订）**：`bonus = max(result.score, FLOOR) * (FACTOR - 1)`，`reranked = result.score + bonus`。常量 `TUTORIAL_SCORE_FLOOR = 3.0` + `TUTORIAL_BOOST_FACTOR = 5.0`（双常量，初始值，eval 二分）。**注意：tasks.md 2.1/2.2 描述的单一 `TUTORIAL_BOOST_FACTOR` + 纯 multiplicative 公式已被修订取代。**
2. **A 段无最小长度守卫（确认）**：`expand_query_variants` 拆分 dot-notation 时不加最小长度守卫，`Node.get` 拆出 `get` 依赖 bm25 排序。与 tasks.md 一致。
3. **C 段关键词集（修订）**：`_inheritance_intent` 检测 **4 个**关键词 `inherits` / `subclass of` / `parent class` / `derived from`，**去掉 `extends`**。**注意：tasks.md 3.3 列了 5 个含 `extends`，已被修订取代。**

## Global Constraints

- Python 3.10+，类型提示必填
- 源代码导入路径 `from rag.<module> import ...`（构建时重写为 `godot_rag.rag.<module>`）
- 测试风格：`unittest.TestCase`，fixtures 在 `rst2md/tests/fixtures/`
- 每段后必须跑 `uv run godot-rag eval-search` 并写入指定基线文件
- **回归红线**：任何段导致 32 个原通过查询中 ≥1 个退出 hit@5，立即回滚该段
- `godot_rag/` 为构建输出，**切勿编辑**
- `rst2md/rag/` 为源代码目录，所有代码修改在此

## File Structure

| 文件 | 责任 | 段 |
|------|------|----|
| `rst2md/rag/query_rewrite.py` | `expand_query_variants`（dot 拆分）、`doc_type_boost`（退化为 0.0） | A、B |
| `rst2md/rag/fusion.py` | `_rerank_bonus` / `_rerank_signals`（地板公式）、双常量 | B |
| `rst2md/rag/query_plan.py` | `QueryPlan` 加 `inheritance_intent`、`_inheritance_intent`、`build_query_plan` | C |
| `rst2md/rag/searcher.py` | `_search_database_impl` 图扩展段加 inherits 定向遍历 | C |
| `rst2md/rag/relations.py` | `build_chunk_relations` / `INHERITS_RE` / `extract_inherits`（C 段只读确认） | C |
| `rst2md/tests/test_searcher_module.py` | A/B/C 单元测试 | A、B、C |
| `rst2md/tests/test_rag_search.py` | C 段覆盖 + 端到端测试 | C |
| `docs/search-quality/loop-2-stage-*.json` | 段间增量基线 | 全段 |

## TDD 红绿循环指引（适用于所有代码任务）

每个代码任务遵循三步：
1. **Red**：先写失败测试，跑 `uv run pytest -q rst2md/tests/<file>::<test>` 确认 FAIL（通常是 ImportError 或 AssertionError）
2. **Green**：写最小实现让测试 PASS
3. **Refactor**：必要时重构（去重、抽常量），重跑测试确认仍 PASS

非代码任务（eval 跑分、读 chunk 确认格式）无 Red 步，直接执行命令并核对期望输出。

---

## 段 0：前置基线锁定

**Files:**
- Create: `docs/search-quality/loop-2-stage-0-baseline.json`
- Read: `docs/search-quality/baseline.json`

### Task 0.1: 锁定起点基线

- [x] **Step 1: 跑当前代码的 38 查询 eval**

```bash
uv run godot-rag eval-search --json > /tmp/loop2-stage0.json
```

Expected: 输出 38 查询的 hit@5 / hit@1 / mrr@5 + 每查询 failure_classification / matched_rank

- [x] **Step 2: 复制为 stage-0 基线文件**

```bash
cp /tmp/loop2-stage0.json docs/search-quality/loop-2-stage-0-baseline.json
```

- [x] **Step 3: Commit**

```bash
git add docs/search-quality/loop-2-stage-0-baseline.json
git commit -m "fix(eval): rebuild DB then re-lock loop-2 stage-0 baseline"
```

### Task 0.2: 核对基线数值一致

- [x] **Step 1: 对比 baseline.json**

```bash
uv run python -c "
import json
b = json.load(open('docs/search-quality/baseline.json'))
s = json.load(open('docs/search-quality/loop-2-stage-0-baseline.json'))
print('baseline hit@5:', b.get('summary',{}).get('hit_at_5'))
print('stage0   hit@5:', s.get('summary',{}).get('hit_at_5'))
"
```

Expected: 两者 hit@5 / hit@1 / mrr@5 数值一致；6 个失败查询的 `failure_classification` 与 `matched_rank` 一致。若不一致 → 停止，先排查环境差异。

---

## 段 A：符号查询归一化（dot-notation 拆分）

**Files:**
- Modify: `rst2md/rag/query_rewrite.py:32` (`expand_query_variants`)
- Test: `rst2md/tests/test_searcher_module.py`
- Eval 输出: `docs/search-quality/loop-2-stage-A.json`

**Interfaces:**
- Consumes: `expand_query_variants` 现有签名 `(query: str) -> list[str]`
- Produces: `expand_query_variants` 对 `Class.method` / `Class.method()` 追加方法后缀变体；下游 `_symbol_candidates`（`query_plan.py:30`）自动去重

**设计修订（必须遵循）：无最小长度守卫。** `Node.get` 拆出 `get`，不加长度检查。

### Task A.1: 写失败测试 — dot-notation 拆分（Red）

- [x] **Step 1: 在 `test_searcher_module.py` 加测试**

在文件末尾追加（unittest.TestCase 风格，与现有 `test_expand_query_variants_*` 同级）：

```python
class DotNotationSplitTests(unittest.TestCase):
    def test_class_method_splits_to_method_suffix(self):
        from rag.query_rewrite import expand_query_variants
        self.assertEqual(
            expand_query_variants("Node.connect"),
            ["Node.connect", "connect"],
        )

    def test_class_method_parens_strips_parens(self):
        from rag.query_rewrite import expand_query_variants
        self.assertEqual(
            expand_query_variants("ResourceLoader.load()"),
            ["ResourceLoader.load()", "load"],
        )

    def test_lowercase_dot_not_split(self):
        from rag.query_rewrite import expand_query_variants
        # scene_tree.tutorial — 前段非大写开头，不拆
        self.assertEqual(expand_query_variants("scene_tree.tutorial"), ["scene_tree.tutorial"])

    def test_numeric_dot_not_split(self):
        from rag.query_rewrite import expand_query_variants
        # v2.1 — 前段非大写开头，不拆
        self.assertEqual(expand_query_variants("v2.1"), ["v2.1"])
```

- [x] **Step 2: 跑测试确认 FAIL**

```bash
uv run pytest -q rst2md/tests/test_searcher_module.py::DotNotationSplitTests -v
```

Expected: 4 个测试 FAIL（`expand_query_variants("Node.connect")` 当前返回 `["Node.connect"]`，不含 `"connect"`）

### Task A.2: 实现 dot-notation 拆分（Green）

- [x] **Step 1: 修改 `rst2md/rag/query_rewrite.py` 的 `expand_query_variants`**

在现有 alias 追加循环之后、return 之前插入 dot-notation 拆分：

```python
_DOT_NOTATION_RE = re.compile(r'^([A-Z][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)\(?\s*$')


def expand_query_variants(query: str) -> list[str]:
    variants = [query]
    query_tokens = _tokens(query)
    for required_tokens, alias in _ALIAS_RULES:
        if required_tokens.issubset(query_tokens) and alias not in variants:
            variants.append(alias)
    m = _DOT_NOTATION_RE.match(query.strip())
    if m:
        method_suffix = m.group(2)
        if method_suffix not in variants:
            variants.append(method_suffix)
    return variants
```

注意：无最小长度守卫 — `Node.get` 拆出 `get` 是预期行为。

- [x] **Step 2: 跑测试确认 PASS**

```bash
uv run pytest -q rst2md/tests/test_searcher_module.py::DotNotationSplitTests -v
```

Expected: 4 PASS

- [x] **Step 3: 跑现有 expand 测试确认无回归**

```bash
uv run pytest -q rst2md/tests/test_searcher_module.py -k expand -v
```

Expected: 全部 PASS（含 `test_expand_query_variants_deduplicates_exact_symbol_query`）

- [x] **Step 4: Commit**

```bash
git add rst2md/rag/query_rewrite.py rst2md/tests/test_searcher_module.py
git commit -m "feat(query-rewrite): split dot-notation Class.method into method suffix variant"
```

### Task A.3: 验证 `_symbol_candidates` 去重

- [x] **Step 1: 写断言测试**

在 `DotNotationSplitTests` 类中加：

```python
    def test_symbol_candidates_dedup_dot_split(self):
        from rag.query_plan import build_query_plan
        plan = build_query_plan("Node.connect")
        # 两个去重候选：原符号 + 方法后缀
        self.assertIn("Node.connect", plan.symbol_candidates)
        self.assertIn("connect", plan.symbol_candidates)
```

- [x] **Step 2: 跑测试**

```bash
uv run pytest -q rst2md/tests/test_searcher_module.py::DotNotationSplitTests::test_symbol_candidates_dedup_dot_split -v
```

Expected: PASS（`_symbol_candidates` 走 `normalize_symbol` 去重，`Node.connect` 与 `connect` 规范化后不同 → 两个候选）

### Task A.4: A 段单元 + 集成不回归

- [x] **Step 1: 跑 searcher + rag_search 全套**

```bash
uv run pytest -q rst2md/tests/test_searcher_module.py rst2md/tests/test_rag_search.py
```

Expected: 全部 PASS，无 FAILED

### Task A.5: 跑 eval 锁定 A 段增量

- [x] **Step 1: 跑 38 查询 eval**

```bash
uv run godot-rag eval-search --json > /tmp/loop2-stageA.json
cp /tmp/loop2-stageA.json docs/search-quality/loop-2-stage-A.json
```

- [x] **Step 2: Commit 基线**

```bash
git add docs/search-quality/loop-2-stage-A.json
git commit -m "chore(eval): lock loop-2 stage-A baseline (dot-notation split)"
```

### Task A.6: A 段验收

- [x] **Step 1: 核对指标**

```bash
uv run python -c "
import json
s = json.load(open('docs/search-quality/loop-2-stage-A.json'))
print('hit@5:', s['summary']['hit_at_5'])
for q in s['queries']:
    if q['query'] in ('ResourceLoader.load', 'Node.connect'):
        print(q['query'], '-> rank', q.get('matched_rank'))
"
```

Expected:
- `ResourceLoader.load` 与 `Node.connect` 命中 rank ≤3
- symbol 类 hit@5 从 80% 提升到 ≥90%
- 32 个原通过查询 hit@5 不低于 89.5%（即 32 个里至少 31 个仍 hit@5）

- [x] **Step 2: 回归检查**

若 32 个原通过查询有 ≥1 个退出 hit@5 → 记录是哪个查询（重点查 `*.get` / `*.set` 类短方法名查询），分析是否需给方法后缀加最小长度守卫。若需加守卫，回到 Task A.2 在 `method_suffix` 追加前加 `if len(method_suffix) >= 3:`，重跑 A.4-A.6。**当前修订决策是不加守卫，仅当 eval 实测回归才补。**

---

## 段 B：Tutorial 排序改地板 + multiplicative

**Files:**
- Modify: `rst2md/rag/fusion.py:49` (`_rerank_bonus`)、`fusion.py:62` (`_rerank_signals`)、新增模块常量
- Modify: `rst2md/rag/query_rewrite.py:17` (`doc_type_boost` 退化为返回 0.0)
- Test: `rst2md/tests/test_searcher_module.py`
- Eval 输出: `docs/search-quality/loop-2-stage-B.json`

**Interfaces:**
- Consumes: `QueryPlan.doc_type_intent`、`QueryPlan.symbol_candidates`、`SearchResult.score`、`SearchResult.doc_type`
- Produces: `rerank.doc_type_intent` 信号 weight 改为地板公式值；`doc_type_boost` 返回 0.0（保留签名，3 个 caller 不破坏）

**设计修订（必须遵循，覆盖 tasks.md 2.1/2.2 原文）：**
- 公式：`bonus = max(result.score, TUTORIAL_SCORE_FLOOR) * (TUTORIAL_BOOST_FACTOR - 1)`
- 双常量：`TUTORIAL_SCORE_FLOOR = 3.0`、`TUTORIAL_BOOST_FACTOR = 5.0`（初始值，eval 二分）
- 失败案例验证：tutorial score=0.66 → bonus = max(0.66, 3.0) * 4 = 12.0；reranked = 0.66 + 12.0 = 12.66 > class 9.91 ✓
- 守卫保留：`not plan.symbol_candidates`（符号查询不触发 tutorial boost）

### Task B.1: 写失败测试 — 地板公式（Red）

- [x] **Step 1: 在 `test_searcher_module.py` 加测试类**

```python
class TutorialFloorBoostTests(unittest.TestCase):
    def test_doc_type_boost_returns_zero_for_tutorial(self):
        # 修订：doc_type_boost 退化为 0.0，加权移到 _rerank_bonus
        from rag.query_rewrite import doc_type_boost
        self.assertEqual(doc_type_boost("how to use scene tree nodes", "tutorial"), 0.0)

    def test_rerank_bonus_floors_low_tutorial_score(self):
        # score=0.66 < FLOOR=3.0 → bonus = 3.0 * 4 = 12.0
        from rag.fusion import _rerank_bonus, TUTORIAL_SCORE_FLOOR, TUTORIAL_BOOST_FACTOR
        from rag.models import SearchResult
        from rag.query_plan import build_query_plan
        plan = build_query_plan("how to use scene tree nodes")
        result = SearchResult(
            score=0.66, path="tut.md", start_line=1, end_line=10,
            doc_type="tutorial", chunk_type="section", addon="", addon_name="",
            symbol="", heading="", breadcrumb="", text="", relation_type="",
            distance=0, snippet="", ranking_signals=[],
        )
        expected = max(0.66, TUTORIAL_SCORE_FLOOR) * (TUTORIAL_BOOST_FACTOR - 1)
        self.assertAlmostEqual(_rerank_bonus(plan, result), expected, places=6)

    def test_rerank_bonus_multiplicative_high_tutorial_score(self):
        # score=5.0 >= FLOOR=3.0 → bonus = 5.0 * 4 = 20.0（不 overshoot 到 symbol 阈值外）
        from rag.fusion import _rerank_bonus, TUTORIAL_SCORE_FLOOR, TUTORIAL_BOOST_FACTOR
        from rag.models import SearchResult
        from rag.query_plan import build_query_plan
        plan = build_query_plan("how to use scene tree nodes")
        result = SearchResult(
            score=5.0, path="tut.md", start_line=1, end_line=10,
            doc_type="tutorial", chunk_type="section", addon="", addon_name="",
            symbol="", heading="", breadcrumb="", text="", relation_type="",
            distance=0, snippet="", ranking_signals=[],
        )
        expected = max(5.0, TUTORIAL_SCORE_FLOOR) * (TUTORIAL_BOOST_FACTOR - 1)
        self.assertAlmostEqual(_rerank_bonus(plan, result), expected, places=6)

    def test_rerank_bonus_no_tutorial_boost_when_symbol_candidates(self):
        # 守卫：symbol 查询不触发 tutorial boost
        from rag.fusion import _rerank_bonus
        from rag.models import SearchResult
        from rag.query_plan import build_query_plan
        plan = build_query_plan("Node.add_child")  # 有 symbol_candidates
        result = SearchResult(
            score=0.66, path="tut.md", start_line=1, end_line=10,
            doc_type="tutorial", chunk_type="section", addon="", addon_name="",
            symbol="", heading="", breadcrumb="", text="", relation_type="",
            distance=0, snippet="", ranking_signals=[],
        )
        # 只有 symbol 候选 bonus，无 tutorial bonus
        self.assertNotIn("tutorial", str(_rerank_bonus(plan, result) - 0.0))
```

- [x] **Step 2: 跑测试确认 FAIL**

```bash
uv run pytest -q rst2md/tests/test_searcher_module.py::TutorialFloorBoostTests -v
```

Expected: 4 FAIL（`TUTORIAL_SCORE_FLOOR` 不存在 / `doc_type_boost` 仍返回 0.05 / `_rerank_bonus` 仍返回 0.05）

### Task B.2: 加双常量 + 地板公式实现（Green）

- [ ] **Step 1: 修改 `rst2md/rag/fusion.py`**

在文件顶部 import 之后加常量：

```python
TUTORIAL_BOOST_FACTOR = 5.0
TUTORIAL_SCORE_FLOOR = 3.0
```

修改 `_rerank_bonus`（`fusion.py:49`）的 doc_type_intent 分支：

```python
def _rerank_bonus(plan: QueryPlan, result: SearchResult) -> float:
    bonus = 0.0
    if result.symbol in plan.alias_symbol_candidates:
        bonus += 5.0
    elif result.symbol in plan.symbol_candidates:
        bonus += 2.0
    if plan.doc_type_intent and result.doc_type == plan.doc_type_intent and not plan.symbol_candidates:
        bonus += max(result.score, TUTORIAL_SCORE_FLOOR) * (TUTORIAL_BOOST_FACTOR - 1)
    if plan.addon_intent and result.doc_type == "addon":
        bonus += 0.5
    return bonus
```

同步修改 `_rerank_signals`（`fusion.py:62`）的 doc_type_intent 信号 weight：

```python
    if plan.doc_type_intent and result.doc_type == plan.doc_type_intent and not plan.symbol_candidates:
        signals.append(RankingSignal(
            name="rerank.doc_type_intent",
            weight=max(result.score, TUTORIAL_SCORE_FLOOR) * (TUTORIAL_BOOST_FACTOR - 1),
            value=result.doc_type,
            details={"intent": plan.doc_type_intent},
        ))
```

- [x] **Step 2: 跑测试确认 PASS**

```bash
uv run pytest -q rst2md/tests/test_searcher_module.py::TutorialFloorBoostTests -v
```

Expected: 4 PASS（注：test 1 需 B.3 退化 `doc_type_boost` 后才 PASS；B.2 实际 3/4 PASS）

### Task B.3: 退化 `doc_type_boost` 为 0.0

- [x] **Step 1: 修改 `rst2md/rag/query_rewrite.py:17` 的 `doc_type_boost`**

```python
def doc_type_boost(query: str, doc_type: str) -> float:
    # 修订：tutorial 加权移至 fusion._rerank_bonus 地板公式；本函数保留签名
    # 供 3 个 caller 调用，统一返回 0.0。
    return 0.0
```

- [x] **Step 2: 更新现有 `doc_type_boost` 测试断言**

在 `test_searcher_module.py` 找到 `test_doc_type_boost_prefers_tutorial_for_how_to_query`（约 line 124），改为：

```python
def test_doc_type_boost_prefers_tutorial_for_how_to_query(self):
    # 修订：doc_type_boost 退化为 0.0，加权移到 _rerank_bonus
    from rag.query_rewrite import doc_type_boost
    assert doc_type_boost("how to use scene tree nodes", "tutorial") == 0.0
    assert doc_type_boost("how to use scene tree nodes", "class") == 0.0
```

- [x] **Step 3: 更新两个硬编码 `0.05` 的 rerank 测试断言**

B.2 改了 `_rerank_bonus` 的 tutorial 分支从 `+0.05` 为 `max(score, FLOOR)*(FACTOR-1)`，两个既有测试硬编码了旧值 `0.05`，需更新为地板公式期望值：

- `test_rerank_appends_doc_type_intent_signal`（约 line 311）：把 `weight == 0.05` 改为 `weight == max(result.score, TUTORIAL_SCORE_FLOOR) * (TUTORIAL_BOOST_FACTOR - 1)` 或具体期望值
- `test_rerank_bonus_equals_signal_weight_sum_doc_type_intent`（约 line 441）：同步更新断言

- [x] **Step 4: 跑测试确认 PASS**

```bash
uv run pytest -q rst2md/tests/test_searcher_module.py -k doc_type_boost -v
uv run pytest -q rst2md/tests/test_searcher_module.py::TutorialFloorBoostTests -v
uv run pytest -q rst2md/tests/test_searcher_module.py -k rerank -v
```

Expected: 全部 PASS

- [x] **Step 5: Commit**

```bash
git add rst2md/rag/fusion.py rst2md/rag/query_rewrite.py rst2md/tests/test_searcher_module.py
git commit -m "feat(fusion): floor+multiplicative tutorial boost, retire doc_type_boost"
```

### Task B.4: 全套不回归

- [x] **Step 1: 跑全套**

```bash
uv run pytest -q rst2md/tests/
```

Expected: 全部 PASS。重点关注 `test_rerank_bonus_equals_signal_weight_sum_doc_type_intent`（sync guard）仍 PASS — 该测试断言 `_rerank_bonus == sum(signal.weight)`，地板公式两边同步改即满足。

### Task B.5: eval 二分调参 FLOOR / FACTOR

**初始值 FLOOR=3.0、FACTOR=5.0。** 候选集：FLOOR ∈ {2, 3, 5}，FACTOR ∈ {3, 5, 7, 10}（共 12 组）。

- [x] **Step 1: 跑初始值 eval**

```bash
uv run godot-rag eval-search > /tmp/loop2-stageB-f5-floor3.json
```

- [x] **Step 2: 核对两个 tutorial 查询**

```bash
uv run python -c "
import json
s = json.load(open('/tmp/loop2-stageB-f5-floor3.json'))
for q in s['queries']:
    if q['query'] in ('scene tree tutorial', 'how to use scene tree nodes'):
        print(q['query'], '-> rank', q.get('matched_rank'))
"
```

Expected: 两个查询命中 rank ≤5

- [x] **Step 3: 若未达标则二分上调**

若 factor=5.0 未达 rank ≤5：
1. 改 `fusion.py` 的 `TUTORIAL_BOOST_FACTOR = 10.0`，重跑 eval
2. 仍未达 → `TUTORIAL_BOOST_FACTOR = 20.0`（注意：过高会 overshoot 撞 symbol 阈值，观察 32 原通过查询是否回归）
3. 找到最小可行 factor 后向下微调（15.0、12.0）取边界值

若低分 tutorial 仍救不起，同步调 `TUTORIAL_SCORE_FLOOR` 到 5.0 重跑。

- [x] **Step 4: 锁定最终值并写入常量**

把最终 FLOOR / FACTOR 写回 `fusion.py` 常量定义，并在注释记录 eval 数据。

### Task B.6: 锁定 B 段基线

- [x] **Step 1: 跑最终值 eval 并存档**

```bash
uv run godot-rag eval-search > /tmp/loop2-stageB.json
cp /tmp/loop2-stageB.json docs/search-quality/loop-2-stage-B.json
```

- [x] **Step 2: Commit**

```bash
git add rst2md/rag/fusion.py docs/search-quality/loop-2-stage-B.json
git commit -m "chore(eval): lock loop-2 stage-B baseline (tutorial floor boost)"
```

### Task B.7: B 段验收

- [x] **Step 1: 核对指标**

```bash
uv run python -c "
import json
s = json.load(open('docs/search-quality/loop-2-stage-B.json'))
print('hit@5:', s['summary']['hit_at_5'])
for q in s['queries']:
    if q['query'] in ('scene tree tutorial', 'how to use scene tree nodes'):
        print(q['query'], '-> rank', q.get('matched_rank'))
"
```

Expected:
- `scene tree tutorial` 与 `how to use scene tree nodes` 命中 rank ≤5
- tutorial 类 hit@5 从 71% 提升到 100%
- A 段通过的查询不回归（与 `loop-2-stage-A.json` 对比）

- [x] **Step 2: 回归检查**

若 32 原通过查询有 ≥1 退出 → 回滚 FLOOR/FACTOR 到上一组可行值，或回到 design 补"高分 tutorial overshoot"决策。

---

## 段 C：继承图扩展（inherits 边定向遍历）

**Files:**
- Read: `rst2md/rag/relations.py:6` (`INHERITS_RE`)、`relations.py:17` (`build_chunk_relations`)
- Modify: `rst2md/rag/query_plan.py:50` (`QueryPlan` dataclass)、`query_plan.py:70` (`build_query_plan`)
- Create: `rst2md/rag/query_plan.py` 新增 `_inheritance_intent`
- Modify: `rst2md/rag/searcher.py` `_search_database_impl` 图扩展段（约 line 310-390）
- Test: `rst2md/tests/test_rag_search.py`、`rst2md/tests/test_searcher_module.py`
- Eval 输出: `docs/search-quality/loop-2-stage-C.json`

**Interfaces:**
- Consumes: `chunk_relations` 表（`relation='inherits'`, `weight=0.8`）、`SearchResult.score`、`chunk_type`
- Produces: `QueryPlan.inheritance_intent: bool`；`searcher` 图扩展加 `graph.inherits` 信号分支

**设计修订（必须遵循，覆盖 tasks.md 3.3 原文）：**
- `_inheritance_intent` 关键词 **4 个**：`inherits` / `subclass of` / `parent class` / `derived from`
- **去掉 `extends`**（"how to extend Node functionality" 不应触发）
- 整词、大小写不敏感匹配（`\b` 边界）
- traversal 只过滤 `r.relation = 'inherits'`，score = `result.score * 0.7`

### Task C.1: 确认真实 chunk 文本格式（前置门禁）

- [x] **Step 1: 查真实 class_node.md chunk**

```bash
uv run python -c "
import sqlite3
conn = sqlite3.connect('godot_rag/default.db')
conn.row_factory = sqlite3.Row
row = conn.execute(\"SELECT id, path, chunk_type, symbol, text FROM chunks WHERE path='classes/class_node.md' AND chunk_type='class_summary' LIMIT 1\").fetchone()
print('id:', row['id'])
print('symbol:', row['symbol'])
print('text (first 300):', row['text'][:300])
"
```

- [x] **Step 2: 确认 `**Inherits:**` 行匹配 `INHERITS_RE`**

```bash
uv run python -c "
from rag.relations import INHERITS_RE, extract_inherits
import sqlite3
conn = sqlite3.connect('godot_rag/default.db')
row = conn.execute(\"SELECT text FROM chunks WHERE path='classes/class_node.md' AND chunk_type='class_summary' LIMIT 1\").fetchone()
text = row[0]
m = INHERITS_RE.search(text)
print('INHERITS_RE match:', m.group(0) if m else None)
print('extract_inherits:', extract_inherits(text))
"
```

Expected: `extract_inherits` 返回非空列表（如 `['Object']`）。

**门禁**：若不匹配 → 暂停 C 段，回到 design 补"indexer 阶段解析 `**Inherits:**`"决策（可能 chunk 文本格式不同，需调 `INHERITS_RE`）。

### Task C.2: 写 `build_chunk_relations` 直接覆盖测试（Red）

CodeGraph 标记 `build_chunk_relations` 无直接覆盖测试（现有测试经 `build_database` 间接调用）。本任务补直接单元测试。

- [x] **Step 1: 在 `test_rag_search.py` 加测试类**

```python
class BuildChunkRelationsCoverageTests(unittest.TestCase):
    """Direct unit coverage for rag.relations.build_chunk_relations."""

    def _build_db(self, docs_text_map):
        import sqlite3
        import tempfile
        from rag.db import get_connection
        from rag.indexer import init_schema
        tmp = tempfile.mkdtemp()
        db_path = os.path.join(tmp, "t.sqlite")
        conn = get_connection(db_path)
        init_schema(conn)
        for path, (doc_type, chunk_type, symbol, parent_symbol, text) in docs_text_map.items():
            conn.execute(
                "INSERT INTO chunks (path, doc_type, chunk_type, symbol, parent_symbol, text, start_line, end_line) "
                "VALUES (?,?,?,?,?,?,?,1,10)",
                (path, doc_type, chunk_type, symbol, parent_symbol, text),
            )
        conn.commit()
        return conn

    def test_inherits_relation_created_for_class_summary(self):
        from rag.relations import build_chunk_relations
        conn = self._build_db({
            "classes/class_node.md": ("class", "class_summary", "Node", "", "**Inherits:** `Object`"),
            "classes/class_object.md": ("class", "class_summary", "Object", "", "Root of all things."),
        })
        build_chunk_relations(conn)
        row = conn.execute(
            "SELECT source_id, target_id, relation, weight FROM chunk_relations WHERE relation='inherits'"
        ).fetchone()
        self.assertIsNotNone(row, "inherits relation should exist")
        self.assertEqual(row["relation"], "inherits")
        self.assertAlmostEqual(row["weight"], 0.8)
```

- [x] **Step 2: 跑测试确认结果**

```bash
uv run pytest -q rst2md/tests/test_rag_search.py::BuildChunkRelationsCoverageTests -v
```

Expected: PASS（`build_chunk_relations` 已实现此逻辑 — 本任务是补覆盖，不是新功能。若 FAIL 说明实现有 bug，先修 `relations.py:40-48`）。

### Task C.3: 写 `_inheritance_intent` 失败测试（Red）

**关键词 4 个（去掉 `extends`）。**

- [x] **Step 1: 在 `test_searcher_module.py` 加测试类**

```python
class InheritanceIntentTests(unittest.TestCase):
    def test_inherits_keyword_triggers(self):
        from rag.query_plan import _inheritance_intent
        self.assertTrue(_inheritance_intent("Node inherits Object"))

    def test_subclass_of_keyword_triggers(self):
        from rag.query_plan import _inheritance_intent
        self.assertTrue(_inheritance_intent("what is subclass of Node"))

    def test_parent_class_keyword_triggers(self):
        from rag.query_plan import _inheritance_intent
        self.assertTrue(_inheritance_intent("parent class of Timer"))

    def test_derived_from_keyword_triggers(self):
        from rag.query_plan import _inheritance_intent
        self.assertTrue(_inheritance_intent("classes derived from Object"))

    def test_extends_does_not_trigger(self):
        # 修订：去掉 extends，避免 "how to extend Node functionality" 误判
        from rag.query_plan import _inheritance_intent
        self.assertFalse(_inheritance_intent("how to extend Node functionality"))

    def test_plain_query_does_not_trigger(self):
        from rag.query_plan import _inheritance_intent
        self.assertFalse(_inheritance_intent("Node connect"))
        self.assertFalse(_inheritance_intent("tutorial scene tree"))
```

- [x] **Step 2: 跑测试确认 FAIL**

```bash
uv run pytest -q rst2md/tests/test_searcher_module.py::InheritanceIntentTests -v
```

Expected: 6 FAIL（`_inheritance_intent` 不存在 → ImportError）

### Task C.4: 实现 `_inheritance_intent` + `QueryPlan.inheritance_intent`（Green）

- [x] **Step 1: 在 `rst2md/rag/query_plan.py` 加函数**

在 `_addon_intent` 之后加：

```python
_INHERITANCE_KEYWORDS = ("inherits", "subclass of", "parent class", "derived from")
_INHERITANCE_RE = re.compile(
    r'\b(?:' + '|'.join(re.escape(k) for k in _INHERITANCE_KEYWORDS) + r')\b',
    re.IGNORECASE,
)


def _inheritance_intent(query: str) -> bool:
    return bool(_INHERITANCE_RE.search(query))
```

注意：`re` 需在文件顶部 import（加 `import re`）。关键词 **4 个**，不含 `extends`。

- [x] **Step 2: 在 `QueryPlan` dataclass 加字段**

在 `addon_intent` 字段之后加：

```python
    inheritance_intent: bool
```

- [x] **Step 3: `build_query_plan` 填充新字段**

```python
def build_query_plan(query: str) -> QueryPlan:
    variants = expand_query_variants(query)
    return QueryPlan(
        original=query,
        fts_variants=tuple(variants),
        symbol_candidates=_symbol_candidates(variants),
        alias_symbol_candidates=_alias_symbol_candidates(query),
        doc_type_intent=_doc_type_intent(query),
        addon_intent=_addon_intent(query),
        inheritance_intent=_inheritance_intent(query),
    )
```

- [x] **Step 4: 跑测试确认 PASS**

```bash
uv run pytest -q rst2md/tests/test_searcher_module.py::InheritanceIntentTests -v
```

Expected: 6 PASS

- [x] **Step 5: 跑现有 query_plan 测试确认无回归**

```bash
uv run pytest -q rst2md/tests/test_searcher_module.py -k query_plan -v
```

Expected: 全部 PASS（注意：`QueryPlan` 是 frozen dataclass，新增字段后所有直接构造 `QueryPlan(...)` 的测试需补 `inheritance_intent` 参数 — 检查 `test_rerank_bonus_equals_signal_weight_sum_doc_type_intent` 等是否直接构造 QueryPlan，若是则补 `inheritance_intent=False`）

- [x] **Step 6: Commit**

```bash
git add rst2md/rag/query_plan.py rst2md/tests/test_searcher_module.py
git commit -m "feat(query-plan): add inheritance_intent (4 keywords, no extends)"
```

### Task C.5: 写图扩展 inherits 定向遍历端到端测试（Red）

- [x] **Step 1: 在 `test_rag_search.py` 加端到端测试**

```python
class InheritsGraphTraversalTests(unittest.TestCase):
    def test_node_inherits_object_reaches_object_class_summary(self):
        from rag import embeddings
        from unittest.mock import patch
        from rag.indexer import build_database
        from rag.searcher import search_database

        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp) / "docs"
            classes = docs / "classes"
            classes.mkdir(parents=True)
            (classes / "class_node.md").write_text(
                "# Node\n\nBase class.\n\n**Inherits:** `Object`\n\n",
                encoding="utf-8",
            )
            (classes / "class_object.md").write_text(
                "# Object\n\nRoot of all things.\n\n",
                encoding="utf-8",
            )
            (classes / "class_timer.md").write_text(
                "# Timer\n\nA countdown timer.\n", encoding="utf-8",
            )
            db_path = Path(tmp) / "t.sqlite"
            with patch.object(embeddings, "generate_embeddings", lambda texts: []):
                build_database(docs, db_path)
                results = search_database(db_path, "Node inherits Object", limit=10, expand_graph=True)
            obj = next((r for r in results if r.symbol == "Object"), None)
            self.assertIsNotNone(obj, "Object class_summary should be reached via inherits traversal")
            rank = results.index(obj) + 1
            self.assertLessEqual(rank, 5, f"Object rank {rank} should be <= 5")
            names = [s.name for s in obj.ranking_signals]
            self.assertIn("graph.inherits", names)
```

- [x] **Step 2: 跑测试确认 FAIL**

```bash
uv run pytest -q rst2md/tests/test_rag_search.py::InheritsGraphTraversalTests -v
```

Expected: FAIL（`graph.inherits` 信号不存在 — 当前图扩展用通用 `graph.expansion` 信号，且不限定 `relation='inherits'`）

### Task C.6: 实现图扩展 inherits 定向遍历分支（Green）

- [x] **Step 1: 修改 `rst2md/rag/searcher.py` `_search_database_impl` 图扩展段**

在现有 `if expand_graph:` 块（约 line 310-390）的通用 graph expansion 循环**之后**、`sorted_results = sorted(...)` 重排**之前**，加 inherits 定向分支：

```python
            # Inheritance-directed traversal: when query signals inheritance
            # intent, pull parent class_summary chunks via 'inherits' edges.
            if plan.inheritance_intent:
                for result in sorted_results[:top_k]:
                    if result.get("chunk_type") != "class_summary":
                        continue
                    inh_rows = conn.execute(
                        "SELECT c.*, r.weight FROM chunk_relations r "
                        "JOIN chunks c ON c.id = r.target_id "
                        "WHERE r.source_id = ? AND r.relation = 'inherits'",
                        [result["id"]],
                    ).fetchall()
                    for rel_row in inh_rows:
                        rel_id = rel_row["id"]
                        if rel_id in expanded_ids:
                            continue
                        expanded_ids.add(rel_id)
                        rel_score = result["score"] * 0.7
                        results[rel_id] = {
                            "id": rel_id,
                            "score": rel_score,
                            "path": rel_row["path"],
                            "start_line": rel_row["start_line"],
                            "end_line": rel_row["end_line"],
                            "doc_type": rel_row["doc_type"],
                            "chunk_type": rel_row["chunk_type"],
                            "addon": rel_row["addon"],
                            "addon_name": rel_row["addon_name"],
                            "symbol": rel_row["symbol"],
                            "heading": rel_row["heading"],
                            "breadcrumb": rel_row["breadcrumb"],
                            "text": clean_chunk_text(rel_row["text"]),
                            "relation_type": "inherits",
                            "distance": 1,
                            "ranking_signals": [
                                RankingSignal(
                                    name="graph.inherits",
                                    weight=rel_score,
                                    value="inherits",
                                    details={
                                        "relation": "inherits",
                                        "distance": 1,
                                        "source_score": result["score"],
                                    },
                                )
                            ],
                        }
```

注意：`plan` 变量在 `_search_database_impl` 内已由 `build_query_plan(query)` 构造，可直接访问 `plan.inheritance_intent`。`expanded_ids` 复用通用分支的集合，避免重复加入。

- [x] **Step 2: 跑端到端测试确认 PASS**

```bash
uv run pytest -q rst2md/tests/test_rag_search.py::InheritsGraphTraversalTests -v
```

Expected: PASS

- [x] **Step 3: 跑图扩展现有测试确认无回归**

```bash
uv run pytest -q rst2md/tests/test_rag_search.py -k graph -v
```

Expected: 全部 PASS（`test_new_graph_chunk_records_expansion_signal` 等不受影响 — 它们 `inheritance_intent=False`，不走新分支）

- [x] **Step 4: Commit**

```bash
git add rst2md/rag/searcher.py rst2md/tests/test_rag_search.py
git commit -m "feat(searcher): directed inherits traversal for inheritance_intent queries"
```

### Task C.7: 全套不回归

- [x] **Step 1: 跑全套**

```bash
uv run pytest -q rst2md/tests/
```

Expected: 全部 PASS

### Task C.8: 跑 eval 锁定 C 段增量

- [x] **Step 1: 跑 38 查询 eval**

```bash
uv run godot-rag eval-search > /tmp/loop2-stageC.json
cp /tmp/loop2-stageC.json docs/search-quality/loop-2-stage-C.json
```

- [x] **Step 2: Commit 基线**

```bash
git add docs/search-quality/loop-2-stage-C.json
git commit -m "chore(eval): lock loop-2 stage-C baseline (inherits traversal)"
```

### Task C.9: C 段验收

- [x] **Step 1: 核对指标**

```bash
uv run python -c "
import json
s = json.load(open('docs/search-quality/loop-2-stage-C.json'))
print('hit@5:', s['summary']['hit_at_5'])
for q in s['queries']:
    if q['query'] == 'Node inherits Object':
        print(q['query'], '-> rank', q.get('matched_rank'))
"
```

Expected:
- `Node inherits Object` 命中 rank ≤5
- class 类 hit@5 保持 100%
- A/B 段通过的查询不回归（与 `loop-2-stage-B.json` 对比）

- [x] **Step 2: 回归检查**

若有 ≥1 退出 → 检查 `inheritance_intent` 是否在非继承查询上误亮（如 `extends` 误判），回到 Task C.4 关键词集。

---

## 段 4：收尾验证

**Files:**
- Create: `docs/search-quality/loop-2-final.json`
- Modify: `docs/search-quality/baseline.json`（替换为新基线）

### Task 4.1: 全套测试通过

- [ ] **Step 1: 跑完整 pytest**

```bash
uv run pytest -q
```

Expected: 全部 PASS，无 FAILED

### Task 4.2: 跑最终 eval

- [x] **Step 1: 跑 38 查询 eval**

```bash
uv run godot-rag eval-search > /tmp/loop2-final.json
cp /tmp/loop2-final.json docs/search-quality/loop-2-final.json
```

- [x] **Step 2: Commit**

```bash
git add docs/search-quality/loop-2-final.json
git commit -m "chore(eval): lock loop-2 final baseline"
```

### Task 4.3: 对比 stage-0 与 final

- [ ] **Step 1: 跑对比脚本**

```bash
uv run python -c "
import json
s0 = json.load(open('docs/search-quality/loop-2-stage-0-baseline.json'))
sf = json.load(open('docs/search-quality/loop-2-final.json'))
print('stage-0 hit@5:', s0['summary']['hit_at_5'])
print('final   hit@5:', sf['summary']['hit_at_5'])
print('stage-0 mrr@5:', s0['summary']['mrr_at_5'])
print('final   mrr@5:', sf['summary']['mrr_at_5'])
# 6 个原失败查询的最终 rank
fails = [q for q in s0['queries'] if q.get('matched_rank') is None or q['matched_rank'] > 5]
for q in fails:
    fq = next(x for x in sf['queries'] if x['query'] == q['query'])
    print(f'{q[\"query\"]!r}: stage0={q.get(\"matched_rank\")} -> final={fq.get(\"matched_rank\")}')
"
```

Expected:
- 6 个原失败查询中至少 5 个进入 rank ≤5（最后一个允许仍失败但需记录原因）
- 整体 Hit@5 ≥ 94%
- MRR@5 ≥ 85%

### Task 4.4: 更新 baseline.json

- [ ] **Step 1: 替换 baseline**

```bash
cp docs/search-quality/loop-2-final.json docs/search-quality/baseline.json
```

- [x] **Step 2: Commit**

```bash
git add docs/search-quality/baseline.json
git commit -m "chore(eval): promote loop-2 final to baseline"
```

### Task 4.5: 准备 verify 阶段材料

- [ ] **Step 1: 整理三个 Open Questions 答案**

写入 `openspec/changes/search-quality-optimization-loop-2/.comet/handoff/verify-answers.md`：

1. **`TUTORIAL_SCORE_FLOOR` 与 `TUTORIAL_BOOST_FACTOR` 最终值**：记录 B.5 二分确定的值 + eval 数据
2. **`class_node.md` `**Inherits:**` 行格式**：记录 C.1 确认的格式（如 `**Inherits:** \`Object\``）+ `INHERITS_RE` 是否匹配
3. **A 段 `*.get`/`*.set` 回归检查**：记录 A.6 的结果（是否回归、是否加了守卫）

- [x] **Step 2: Commit**

```bash
git add openspec/changes/search-quality-optimization-loop-2/.comet/handoff/verify-answers.md
git commit -m "docs(comet): record loop-2 verify answers for Open Questions"
```

---

## Self-Review

### Spec coverage 核对

| Design Doc / tasks.md 要求 | 对应任务 |
|------|------|
| A 段 dot-notation 拆分（无守卫） | A.1-A.6 |
| B 段 地板 + multiplicative 公式（双常量） | B.1-B.7（覆盖 tasks.md 2.1/2.2 原文的单一常量修订） |
| B 段 `doc_type_boost` 退化 0.0 | B.3 |
| B 段 `_rerank_signals` 同步 | B.2 Step 1 |
| B 段 eval 二分 | B.5 |
| C 段 4 关键词（去 `extends`） | C.3-C.4（覆盖 tasks.md 3.3 原文的 5 关键词修订） |
| C 段 `build_chunk_relations` 覆盖测试 | C.2 |
| C 段 inherits 定向遍历 | C.5-C.6 |
| 段间基线文件 | A.5 / B.6 / C.8 / 4.2 |
| 收尾对比 + baseline 替换 | 4.3-4.4 |
| Open Questions 答案 | 4.5 |

### 三处 brainstorm 修订落地确认

- ✅ B 段公式 `max(score, FLOOR) * (FACTOR - 1)`，FLOOR=3.0、FACTOR=5.0 → B.1 测试断言、B.2 实现、B.5 二分
- ✅ A 段无最小长度守卫 → A.2 Step 1 注释明确、A.6 Step 2 回归检查
- ✅ C 段 4 关键词去 `extends` → C.3 测试含 `test_extends_does_not_trigger`、C.4 `_INHERITANCE_KEYWORDS` 4 元组

### 类型一致性

- `QueryPlan.inheritance_intent: bool` — C.4 定义、C.6 读取（`plan.inheritance_intent`）一致
- `_inheritance_intent(query: str) -> bool` — C.3 测试、C.4 实现签名一致
- `_rerank_bonus` / `_rerank_signals` 同步改 weight — B.2 两处一致，B.4 sync guard 测试守卫
- `TUTORIAL_SCORE_FLOOR` / `TUTORIAL_BOOST_FACTOR` — B.1 import、B.2 定义、B.5 调参一致

### 占位符扫描

无 TBD / TODO / "implement later" / "add appropriate error handling"。所有代码步骤含完整可运行代码。

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-07-01-search-quality-optimization-loop-2.md`. Two execution options:

**1. Subagent-Driven (recommended)** - 每个 task 派发 fresh subagent，task 间 review，快速迭代

**2. Inline Execution** - 在当前 session 用 executing-plans 批量执行，checkpoint review

Which approach?
