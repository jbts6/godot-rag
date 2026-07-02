# Tasks

## 0. 前置基线锁定

- [x] 0.1 跑 `uv run godot-rag eval-search`，确认 `Node inherits Object` 当前 rank=None；锁定 stage-0 基线到 `docs/search-quality/inheritance-recall-stage-0.json`
- [x] 0.2 确认 Node / Object `class_summary` chunk 在索引库中的 `symbol` / `heading` / `chunk_type` 字段值（为设计召回查询提供依据）

## 1. 实现召回修复（方案待 design brainstorming 确认）

- [x] 1.1 设计 brainstorming 确认召回方案（候选 1-4 中选一个或组合）
- [ ] 1.2 实现召回逻辑：inheritance-intent 查询时确保目标 `class_summary` 进入候选集（TDD：Red 测试复现生产 gap — class_summary 不在默认 top-K 时仍被召回）
- [ ] 1.3 跑 `uv run pytest -q` 全套不回归

## 2. 评估验证

- [ ] 2.1 跑 `uv run godot-rag eval-search`，`Node inherits Object` rank ≤ 5；Hit@5 ≥ 97.37%；MRR@5 ≥ 87.50%
- [ ] 2.2 对比 stage-0 基线：32 个原通过查询无回归
- [ ] 2.3 锁定 final 基线到 `docs/search-quality/inheritance-recall-final.json`，更新 `baseline.json`

## 3. 收尾验证

- [ ] 3.1 跑完整 `uv run pytest -q` 全套通过
- [ ] 3.2 准备 verify 阶段材料
