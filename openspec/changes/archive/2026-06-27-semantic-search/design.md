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
└─────┬─────┴─────┬─────┘
      │           │
      ▼           ▼
   FTS5 结果   向量结果
      │           │
      └─────┬─────┘
            ▼
      RRF 融合排序
            │
            ▼
       最终结果
```

## Risks / Trade-offs

- **向量生成性能**: 28231 个 chunk 批量生成向量可能需要较长时间 → 分批处理，增量更新
- **模型首次加载**: model2vec 首次加载需要下载模型 → 缓存到本地
- **向量维度固定**: 256 维可能限制表达能力 → 后续可升级模型

## Open Questions

- RRF 的 k 参数是否需要调优？
- see_also 关系的权重 (0.6) 是否合适？
