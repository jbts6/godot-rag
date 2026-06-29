## Why

现有搜索质量 baseline 已经能记录版本和数据库指纹，但 gating query 集合偏小且当前满分，无法可靠暴露下一轮搜索优化的稳定性、速度和质量变化。继续直接调整 ranking 或重构搜索器会缺少足够的回归信号，因此需要先扩展评估覆盖和可观测指标。

## What Changes

- 扩展 packaged search quality query suite，使 gating queries 覆盖更多稳定场景，并继续保留不稳定场景为 report-only。
- 增加评估输出中的性能和稳定性指标，包括查询延迟、搜索模式、vector fallback/degraded 状态和失败诊断。
- 将质量评估的常规验证入口明确化，避免只依赖人工 spot check 或单纯 pytest。
- 为后续搜索器等价拆分定义保护边界：拆分前后必须保持搜索行为和质量 baseline 不退化。
- 不在本 change 中大幅调整 ranking 权重、更换 embedding 模型或修改数据库 schema。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `semantic-search-quality`: 扩展搜索质量评估集、指标和验证入口要求。
- `search-quality-diagnostics`: 扩展诊断输出，使性能、fallback/degraded 状态和失败原因可用于稳定性判断。

## Impact

- Affected code:
  - `rst2md/rag/search_eval.py`
  - `rst2md/rag/search_eval_queries.json`
  - `rst2md/rag/cli.py`
  - `rst2md/rag/searcher.py`
  - `rst2md/tests/`
  - `docs/search-quality/`
- Public APIs:
  - Existing search commands and JSON result shape should remain backward compatible.
  - `eval-search` output may gain fields, but existing fields should remain stable.
- Dependencies:
  - No new runtime dependency expected.
  - No database schema change expected.
