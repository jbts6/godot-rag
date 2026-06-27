## 1. 依赖与 Schema

- [x] 1.1 在 pyproject.toml 添加 sqlite-vec 和 model2vec 依赖
- [x] 1.2 在 store.py 的 SCHEMA 中新增 vec_chunks 虚拟表

## 2. see_also 关系

- [x] 2.1 在 _build_chunk_relations 中新增 see_also 关系提取逻辑（正则 `See also \`([^`]+)\``）
- [x] 2.2 验证构建后 chunk_relations 表中 see_also 数量 ≥ 100

## 3. 向量生成与存储

- [x] 3.1 实现 generate_embeddings 函数：使用 model2vec 对 chunks 批量生成向量（分批处理，每批 1000 个）
- [x] 3.2 在 build_database 中调用 generate_embeddings 并写入 vec_chunks 表
- [x] 3.3 验证构建后 vec_chunks 表有 28231 条记录

## 4. 向量搜索与融合

- [x] 4.1 实现 vector_search 函数：使用 sqlite-vec 进行向量相似度搜索
- [x] 4.2 实现 rrf_fusion 函数：RRF 融合 FTS5 和向量搜索结果
- [x] 4.3 修改 search_database 函数：集成向量搜索和 RRF 融合
- [x] 4.4 验证搜索 "how to make a button" 能返回语义相关结果

## 5. 测试

- [x] 5.1 编写 see_also 关系构建的单元测试
- [x] 5.2 编写向量搜索和 RRF 融合的单元测试
