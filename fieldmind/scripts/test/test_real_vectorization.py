"""
测试真实向量化功能
"""
import sys
sys.path.append('/Users/alwan/FieldMind-Rebuild/fieldmind-backend')

from app.services.vectorization_service_complete import VectorizationService

print("=" * 60)
print("测试真实向量化功能")
print("=" * 60)

# 初始化向量化服务
print("\n【步骤1】初始化向量化服务...")
vectorizer = VectorizationService()

# 检查是否使用真实模型
if vectorizer.model is not None:
    print(f"✅ 真实模型加载成功")
    print(f"   模型: {vectorizer.model_name}")
    print(f"   维度: {vectorizer.embedding_dim}")
else:
    print("❌ 使用模拟向量")
    sys.exit(1)

# 测试单个文本向量化
print("\n【步骤2】测试单个文本向量化...")
test_text = "这是一个关于田野调查的研究文档"
embedding = vectorizer.vectorize_text(test_text)

if embedding:
    print(f"✅ 向量化成功")
    print(f"   文本: {test_text}")
    print(f"   向量维度: {len(embedding)}")
    print(f"   向量前5位: {embedding[:5]}")
else:
    print("❌ 向量化失败")

# 测试批量向量化
print("\n【步骤3】测试批量向量化...")
chunks = [
    {"text": "第一段文本：田野调查方法"},
    {"text": "第二段文本：数据收集技术"},
    {"text": "第三段文本：分析框架设计"},
]

vectorized_chunks = vectorizer.vectorize_chunks(chunks)

if vectorized_chunks and all('embedding' in c for c in vectorized_chunks):
    print(f"✅ 批量向量化成功")
    print(f"   处理数量: {len(vectorized_chunks)}")
    for i, chunk in enumerate(vectorized_chunks):
        print(f"   Chunk {i+1}: 维度={len(chunk['embedding'])}, 模型={chunk['embedding_model']}")
else:
    print("❌ 批量向量化失败")

# 测试语义相似度
print("\n【步骤4】测试语义相似度...")
text1 = "田野调查方法研究"
text2 = "田野研究的方法论"
text3 = "计算机编程技术"

embedding1 = vectorizer.vectorize_text(text1)
embedding2 = vectorizer.vectorize_text(text2)
embedding3 = vectorizer.vectorize_text(text3)

import numpy as np

def cosine_similarity(v1, v2):
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

sim_12 = cosine_similarity(embedding1, embedding2)
sim_13 = cosine_similarity(embedding1, embedding3)

print(f"✅ 相似度计算完成")
print(f"   '{text1}' vs '{text2}': {sim_12:.4f}")
print(f"   '{text1}' vs '{text3}': {sim_13:.4f}")

if sim_12 > sim_13:
    print(f"   ✅ 语义相似度正确（相关文本 > 不相关文本）")
else:
    print(f"   ⚠️ 语义相似度异常")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
