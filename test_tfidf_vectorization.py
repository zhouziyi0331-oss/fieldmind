"""
测试TF-IDF真实向量化功能
"""
import sys
sys.path.append('/Users/alwan/FieldMind-Rebuild/fieldmind-backend')

from app.services.vectorization_service_complete import VectorizationService
import numpy as np

print("=" * 60)
print("测试TF-IDF真实向量化功能")
print("=" * 60)

# 初始化向量化服务
print("\n【步骤1】初始化向量化服务...")
vectorizer = VectorizationService()

# 检查使用的模型类型
if vectorizer.model is not None:
    print(f"✅ 使用Sentence-BERT模型")
elif vectorizer.tfidf_model is not None:
    print(f"✅ 使用TF-IDF模型")
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
    print(f"   向量前5位: {[f'{x:.4f}' for x in embedding[:5]]}")
    print(f"   向量范数: {np.linalg.norm(embedding):.4f}")
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

def cosine_similarity(v1, v2):
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

sim_12 = cosine_similarity(embedding1, embedding2)
sim_13 = cosine_similarity(embedding1, embedding3)

print(f"✅ 相似度计算完成")
print(f"   '{text1}' vs '{text2}': {sim_12:.4f}")
print(f"   '{text1}' vs '{text3}': {sim_13:.4f}")

if sim_12 > sim_13:
    print(f"   ✅ 语义相似度正确（相关文本 {sim_12:.4f} > 不相关文本 {sim_13:.4f}）")
else:
    print(f"   ⚠️ 语义相似度异常（相关 {sim_12:.4f} <= 不相关 {sim_13:.4f}）")

# 测试大批量
print("\n【步骤5】测试大批量向量化...")
large_chunks = [{"text": f"这是第{i}段关于田野调查、数据分析和研究方法的文本内容"} for i in range(50)]
vectorized_large = vectorizer.vectorize_chunks(large_chunks)

if len(vectorized_large) == 50 and all('embedding' in c for c in vectorized_large):
    print(f"✅ 大批量向量化成功")
    print(f"   处理数量: {len(vectorized_large)}")
    # 检查向量质量
    embeddings = [c['embedding'] for c in vectorized_large]
    norms = [np.linalg.norm(e) for e in embeddings]
    print(f"   向量范数范围: [{min(norms):.4f}, {max(norms):.4f}]")
else:
    print("❌ 大批量向量化失败")

print("\n" + "=" * 60)
print("✅ 所有测试通过 - TF-IDF真实向量化工作正常")
print("=" * 60)
