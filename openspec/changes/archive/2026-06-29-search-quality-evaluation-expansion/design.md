## Context

当前搜索质量工作已经具备 deterministic fixture tests、真实数据库 `eval-search`、baseline regression、失败分类、query-suite hash、数据库 fingerprint 和 evaluator/search 版本元数据。近期 baseline 的 gating 集合只有 15 条且全部满分，通过率本身已经不能很好地区分真实质量变化。与此同时，`rst2md/rag/searcher.py` 的核心搜索实现仍集中在较大的 `_search_database_impl` 中，后续要优化稳定性、速度、质量或拆分结构，都需要更强的评估保护。

## Goals / Non-Goals

**Goals:**

- 扩展稳定 gating query 覆盖，优先覆盖真实用户高频和历史脆弱场景。
- 在评估报告中加入 latency、search mode、fallback/degraded reason 等稳定性与速度信号。
- 明确 routine validation 如何运行 deterministic checks 和真实数据库 gate。
- 为后续搜索器等价拆分建立“不改变行为”的验证边界。

**Non-Goals:**

- 不大幅调整 ranking 权重。
- 不更换 embedding 模型。
- 不修改数据库 schema。
- 不把所有 `WIP.md` 中的搜索策略优化一次性实现完。

## Decisions

### 1. 先扩评估信号，再调 ranking

直接改 ranking 会被当前满分 baseline 掩盖。先把 query suite 扩到至少 40 条、gating 至少 25 条，并增加 filter precision、normalization、graph、addon/doc-type 场景，可以让后续优化有更可信的回归信号。仍不稳定或依赖缺失数据的查询继续保持 report-only。

替代方案是先调权重再回填测试。这个顺序反馈快，但容易把当前 fixture 过拟合成目标，且无法解释真实数据库退化。

### 2. latency 与 fallback 进入评估报告，而不是只放 debug command

搜索质量不只看命中率。向量不可用、fallback 到 FTS、p95 延迟上升，都会影响用户体验和后续 ranking 判断。评估报告应记录这些信号，并在 JSON 和 text 输出中都可见。

替代方案是只在 `diagnostics` 命令里暴露运行状态。这样适合排障，但不能进入 baseline/CI 质量闭环。

### 3. 搜索器拆分先作为等价重构边界

`_search_database_impl` 应后续拆成 candidate retrieval、fusion/rerank、graph expansion、result formatting 等阶段。但本 change 的实现应先建立评估保护，最多做低风险的等价拆分，不同时改变 ranking。拆分后的每个阶段仍必须传递 search metadata，保证评估诊断不丢信息。

替代方案是本 change 同时完成完整结构拆分和 ranking 改进。这个范围过大，失败时难以判断是评估、结构还是 ranking 导致退化。

## Risks / Trade-offs

- 扩容 gating queries 可能引入不稳定用例 -> 先用 report-only 承接不稳定查询，只有 expected target 在 canonical database 存在且 rank 稳定时才转 gating。
- latency 指标受机器状态影响 -> 首版将 latency 作为可见诊断和可配置阈值，不默认使用过窄硬阈值。
- 评估输出字段增加可能影响调用方 -> 保留现有字段，只追加新字段。
- 搜索器拆分范围容易扩大 -> tasks 中将拆分限制为验证边界和小步等价改动；ranking 策略优化进入后续 change。
