-- FieldMind PostgreSQL + pgvector 初始化脚本

-- 启用 pgvector 扩展
CREATE EXTENSION IF NOT EXISTS vector;

-- 验证扩展安装
SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';

-- 创建向量存储表
CREATE TABLE IF NOT EXISTS document_vectors (
    id SERIAL PRIMARY KEY,
    document_id VARCHAR(50) NOT NULL,
    chunk_id VARCHAR(50) NOT NULL,
    embedding vector(1536),  -- OpenAI ada-002 维度
    model_name VARCHAR(100) DEFAULT 'text-embedding-ada-002',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 索引
    CONSTRAINT unique_chunk_vector UNIQUE (chunk_id)
);

-- 创建 HNSW 索引（性能更好，适合大规模数据）
CREATE INDEX IF NOT EXISTS document_vectors_embedding_hnsw_idx
ON document_vectors USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- 创建 IVFFlat 索引（备选方案）
-- CREATE INDEX IF NOT EXISTS document_vectors_embedding_ivfflat_idx
-- ON document_vectors USING ivfflat (embedding vector_cosine_ops)
-- WITH (lists = 100);

-- 创建文档ID索引
CREATE INDEX IF NOT EXISTS idx_document_vectors_document_id
ON document_vectors(document_id);

-- 创建更新时间触发器
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_document_vectors_updated_at
BEFORE UPDATE ON document_vectors
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- 插入测试数据
INSERT INTO document_vectors (document_id, chunk_id, embedding)
VALUES (
    'test_doc_001',
    'test_chunk_001',
    array_fill(0.1, ARRAY[1536])::vector
) ON CONFLICT (chunk_id) DO NOTHING;

-- 验证安装
SELECT
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'document_vectors';

COMMENT ON TABLE document_vectors IS 'FieldMind文档向量存储表';
COMMENT ON COLUMN document_vectors.embedding IS '1536维向量，支持余弦相似度检索';
COMMENT ON INDEX document_vectors_embedding_hnsw_idx IS 'HNSW向量索引，支持快速ANN检索';
