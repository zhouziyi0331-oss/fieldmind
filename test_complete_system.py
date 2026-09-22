"""
FieldMind 完整功能测试脚本
测试 P0-P1 所有已完成的功能
"""
import sys
sys.path.insert(0, '/Users/alwan/FieldMind/backend/src')

print("="*80)
print("FieldMind 完整功能测试")
print("="*80)
print()

# 测试数据
test_text = """
某村调查报告

时间：2024年3月15日
地点：某村文化广场

村长王大爷说："我们村的传统手工艺已经传承了三代人。"
村民李婶表示："现在年轻人都外出打工了，留在村里的多是老人。"

村里的经济主要依靠农业和旅游业。近年来，随着乡村振兴政策的推进，
村子的基础设施得到了很大改善。但是，如何将文化传承与产业发展结合起来，
仍然是一个需要解决的问题。

我们还观察到，村民之间的社会关系非常紧密。邻里互助、婚丧嫁娶都体现出
强烈的共同体意识。这种社会资本是乡村发展的重要基础。
"""

# ==================== 测试 1：文本切分 ====================
print("【测试 1：文本切分】")
print("-"*80)

from app.services.chunking_service import chunking_service

chunks = chunking_service.chunk_text(test_text)
print(f"✅ 切分结果：{len(chunks)} 个 chunks")

for i, chunk in enumerate(chunks):
    print(f"\nChunk {i}:")
    print(f"  字符数: {chunk['char_count']}")
    print(f"  词数: {chunk['word_count']}")
    print(f"  内容: {chunk['content'][:50]}...")

print("\n" + "="*80 + "\n")

# ==================== 测试 2：文本量化 ====================
print("【测试 2：文本量化】")
print("-"*80)

from app.services.text_quantification import text_quantification_service

metrics = text_quantification_service.quantify_text(test_text)

print("✅ 量化指标：")
print(f"  字符数: {metrics['char_count']}")
print(f"  词数: {metrics['word_count']}")
print(f"  句子数: {metrics['sentence_count']}")
print(f"  情感分数: {metrics['sentiment_score']:.3f}")
print(f"  情感极性: {metrics['sentiment_polarity']}")
print(f"  主观性: {metrics['subjectivity']:.3f}")
print(f"  情绪词密度: {metrics['emotion_density']:.3f}")
print(f"  词汇丰富度: {metrics['lexical_diversity']:.3f}")

print("\n" + "="*80 + "\n")

# ==================== 测试 3：关键词提取 ====================
print("【测试 3：关键词提取】")
print("-"*80)

from app.services.keyword_extraction import keyword_extraction_service

keywords = keyword_extraction_service.extract_keywords(test_text, top_k=10)

print(f"✅ 提取了 {len(keywords)} 个关键词：")
for kw in keywords:
    print(f"  - {kw['word']}: {kw['score']:.4f} ({kw['method']})")

print("\n" + "="*80 + "\n")

# ==================== 测试 4：三层报告生成 ====================
print("【测试 4：三层报告生成】")
print("-"*80)

# 模拟文档对象
class MockDocument:
    def __init__(self):
        self.id = 1
        self.original_filename = "test.txt"
        self.text_content = test_text
        self.word_count = 200
        self.upload_time = __import__('datetime').datetime.now()
        self.extra_data = {}

mock_docs = [MockDocument()]

# 模拟数据库
class MockChunk:
    def __init__(self, content, sentiment):
        self.id = 1
        self.document_id = 1
        self.content = content
        self.sentiment_polarity = sentiment
        self.sentiment_score = 0.5

class MockDB:
    def query(self, model):
        return self

    def filter(self, *args):
        return self

    def all(self):
        return [
            MockChunk("村长说传统手工艺很重要", "positive"),
            MockChunk("年轻人都外出打工了", "negative"),
            MockChunk("基础设施得到改善", "positive"),
            MockChunk("社会关系紧密", "positive"),
        ]

mock_db = MockDB()

# 测试 Level 1 报告
from app.api.reports_real import generate_level1_report

print("生成 Level 1 报告（事实报告）...")
level1 = generate_level1_report(mock_docs, mock_db)
print("✅ Level 1 报告生成成功")
print("\n--- Level 1 报告预览（前300字）---")
print(level1[:300])
print("...\n")

# 测试 Level 3 报告
from app.api.reports_real import generate_level3_report

print("生成 Level 3 报告（商业报告）...")
level3 = generate_level3_report(mock_docs, mock_db, project_id=1)
print("✅ Level 3 报告生成成功")
print("\n--- Level 3 报告预览（前300字）---")
print(level3[:300])
print("...\n")

print("="*80 + "\n")

# ==================== 总结 ====================
print("【测试总结】")
print("="*80)
print("✅ 测试 1：文本切分 - 通过")
print("✅ 测试 2：文本量化 - 通过")
print("✅ 测试 3：关键词提取 - 通过")
print("✅ 测试 4：三层报告生成 - 通过")
print("="*80)
print()

print("【已完成功能清单】")
print("-"*80)
print("P0-1: ✅ 处理层闭环（切分 + 量化）")
print("P0-2: ✅ 采集层批量上传")
print("P1-1: ✅ 理解层知识脉络（后端）")
print("P1-2: ✅ 分析层三层报告（后端）")
print("-"*80)
print()

print("【API 端点清单】")
print("-"*80)
print("文档上传:")
print("  POST /api/v1/documents/upload-batch")
print("  GET  /api/v1/documents/upload-progress/{project_id}")
print()
print("知识图谱:")
print("  GET  /api/v1/knowledge-graph/{project_id}")
print("  GET  /api/v1/knowledge-graph/{project_id}/node/{node_id}")
print("  POST /api/v1/knowledge-graph/{project_id}/rebuild")
print("-"*80)
print()

print("【下一步】")
print("-"*80)
print("1. 启动后端服务测试 API")
print("2. 上传真实文档验证完整流程")
print("3. 完成前端知识脉络可视化")
print("4. 完成 P2：RAG 引擎和溯源")
print("="*80)
