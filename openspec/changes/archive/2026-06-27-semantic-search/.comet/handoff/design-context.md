# Comet Design Handoff

- Change: semantic-search
- Phase: design
- Mode: compact
- Context hash: ae53a17bef05a554a4f751071811405f0a83e5743c9962475551eebb9315565e

Generated-by: comet-handoff.sh

OpenSpec remains the canonical capability spec. This handoff is a deterministic, source-traceable context pack, not an agent-authored summary.

## openspec/changes/semantic-search/proposal.md

- Source: openspec/changes/semantic-search/proposal.md
- Lines: 1-23
- SHA256: 72ea3c84daef63f89f94392fe8666751cc7a1b18ca6df31f41c7e74eb0decb60

```md
## Why

当前搜索只有 FTS5 词法搜索 + 符号索引，无法处理语义相似但词法不同的查询（如 "how to make a button" 无法匹配 "how to create a button"）。此外，Godot 文档中有 190 个有效的 `See also` 交叉引用未被利用。

## What Changes

- 新增 `see_also` 关系类型，从文档中的 `See also \`xxx\`` 格式提取引用（846 个匹配中约 190 个能匹配到已注册符号，其余为全局函数/常量，不在本次范围）
- 引入 sqlite-vec + model2vec 实现向量语义搜索
- 实现 FTS5 + 向量双路召回，RRF 融合排序

## Capabilities

### New Capabilities
- `semantic-search`: 向量语义搜索能力，包括向量生成、存储、检索和 RRF 融合排序
- `see-also-relations`: 从 Godot 文档中提取 `See also` 引用，建立 see_also 关系

### Modified Capabilities

## Impact

- `rst2md/rag/store.py`: 新增 `see_also` 关系构建逻辑、向量表 schema、RRF 搜索函数
- `pyproject.toml`: 新增 `sqlite-vec`、`model2vec` 依赖
- 数据库 schema: 新增 `vec_chunks` 虚拟表
```

## openspec/changes/semantic-search/design.md

- Source: openspec/changes/semantic-search/design.md
- Lines: 1-103
- SHA256: adc4c5a10c848bca40d5532272d46efc8c6c76dac8634fc2c972df9a85d2a1bc

[TRUNCATED]

```md
## Context

当前 godot-rag 使用 FTS5 词法搜索 + 符号索引进行检索。搜索质量受限于词法匹配，无法处理语义相似但措辞不同的查询。Godot 文档中有 `See also` 交叉引用未被利用。

## Goals / Non-Goals

**Goals:**
- 实现向量语义搜索，支持语义相似度匹配
- 提取并利用文档中的 `See also` 交叉引用
- FTS5 + 向量双路召回，RRF 融合排序

**Non-Goals:**
- 不修复 references 噪音问题
- 不扩展符号提取（全局函数、常量）
- 不涉及构建效率优化

## Decisions

### 1. 向量化方案：model2vec

**选择**: model2vec (potion-base-8M, 256 维)

**理由**:
- 支持 Python 3.14（sentence-transformers 不支持）
- 无需 GPU，纯 CPU 推理
- 模型小（~30MB），加载快
- 向量质量足够用于语义搜索

**替代方案**:
- sentence-transformers: 不支持 Python 3.14
- fastembed: 依赖 onnxruntime，不支持 Python 3.14

### 2. 向量存储：sqlite-vec

**选择**: sqlite-vec (v0.1.9)

**理由**:
- 与现有 SQLite 数据库架构一致
- 无需外部服务
- 向量和标量数据在同一数据库，查询方便

**替代方案**:
- ChromaDB: 需要额外依赖和外部服务
- FAISS: 需要额外依赖

### 3. 融合排序：RRF (Reciprocal Rank Fusion)

**选择**: RRF 公式: `score = 1 / (k + rank)`，k=60

**理由**:
- RRF 是标准的多路召回融合算法
- k=60 是常用参数，适合不同量级的分数
- 实现简单，效果稳定

**融合范围**: FTS5 结果 + 向量结果，两路融合。Graph expansion 保持现有逻辑不变（在融合后的 top-K 上执行）。

### 4. 数据库 Schema

新增 `vec_chunks` 虚拟表:
```sql
CREATE VIRTUAL TABLE vec_chunks USING vec0(
    chunk_id INTEGER PRIMARY KEY,
    embedding float[256]
);
```

新增 `chunk_relations` 的 `see_also` 类型:
```sql
INSERT INTO chunk_relations (source_id, target_id, relation, weight)
VALUES (?, ?, 'see_also', 0.6);
```
权重 0.6 介于 references (0.5) 和 inherits (0.8) 之间，反映 see_also 的语义关联强度。

### 5. 搜索流程

```
用户查询
    ↓
┌───────────┬───────────┐
│  FTS5 搜索 │ 向量搜索   │
```

Full source: openspec/changes/semantic-search/design.md

## openspec/changes/semantic-search/tasks.md

- Source: openspec/changes/semantic-search/tasks.md
- Lines: 1-27
- SHA256: 10f9ea613284e145dcfc385d8a6b97df93493ff361854dce80d2bb561381b765

```md
## 1. 依赖与 Schema

- [ ] 1.1 在 pyproject.toml 添加 sqlite-vec 和 model2vec 依赖
- [ ] 1.2 在 store.py 的 SCHEMA 中新增 vec_chunks 虚拟表

## 2. see_also 关系

- [ ] 2.1 在 _build_chunk_relations 中新增 see_also 关系提取逻辑（正则 `See also \`([^`]+)\``）
- [ ] 2.2 验证构建后 chunk_relations 表中 see_also 数量 ≥ 100

## 3. 向量生成与存储

- [ ] 3.1 实现 generate_embeddings 函数：使用 model2vec 对 chunks 批量生成向量（分批处理，每批 1000 个）
- [ ] 3.2 在 build_database 中调用 generate_embeddings 并写入 vec_chunks 表
- [ ] 3.3 验证构建后 vec_chunks 表有 28231 条记录

## 4. 向量搜索与融合

- [ ] 4.1 实现 vector_search 函数：使用 sqlite-vec 进行向量相似度搜索
- [ ] 4.2 实现 rrf_fusion 函数：RRF 融合 FTS5 和向量搜索结果
- [ ] 4.3 修改 search_database 函数：集成向量搜索和 RRF 融合
- [ ] 4.4 验证搜索 "how to make a button" 能返回语义相关结果

## 5. 测试

- [ ] 5.1 编写 see_also 关系构建的单元测试
- [ ] 5.2 编写向量搜索和 RRF 融合的单元测试
```

