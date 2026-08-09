"""
Phase 5测试套件 - 测试重构后的三层分析器
"""
import pytest
import asyncio
from datetime import datetime
from typing import List, Dict, Any

# 导入要测试的组件
from app.services.citation_tracker import CitationTracker, Citation, AnnotatedText
from app.services.cost_controller import CostController, CostBudget, ModelConfig
from app.services.tier1_analyzer_v2 import Tier1AnalyzerV2
from app.services.tier2_analyzer_v2 import Tier2AnalyzerV2
from app.services.tier3_analyzer_v2 import Tier3AnalyzerV2, MarketDataCollector
from app.services.analysis_workflow import AnalysisWorkflow, analyze_documents


# ============================================================================
# Mock对象
# ============================================================================

class MockDocument:
    """模拟Document对象"""
    def __init__(self, doc_id: int, filename: str, content: str):
        self.id = doc_id
        self.filename = filename
        self.content = content
        self.file_type = 'txt'
        self.file_size = len(content)
        self.word_count = len(content)
        self.summary = content[:200]
        self.uploaded_at = datetime.now()
        self.status = 'processed'


class MockEntity:
    """模拟Entity对象"""
    def __init__(self, entity_id: int, name: str, entity_type: str):
        self.id = entity_id
        self.name = name
        self.entity_type = entity_type
        self.mention_count = 5
        self.confidence = 0.9
        self.description = f"这是{name}"
        self.aliases = []
        self.first_mentioned_doc = 1
        self.document_ids = [1, 2]


class MockLLMAnalyzer:
    """模拟LLM分析器"""
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.3,
        response_format: str = 'text',
        model: str = 'claude-3-sonnet'
    ) -> str:
        """返回模拟的LLM响应"""
        if response_format == 'json':
            # 根据prompt内容返回不同的JSON
            if 'dimensions' in prompt:
                return '''{"dimensions": [
                    {"name": "数据特征", "description": "文档的基本特征", "data_support": "5份文档"},
                    {"name": "实体网络", "description": "实体关系", "data_support": "20个实体"}
                ]}'''
            elif 'phenomena' in prompt:
                return '''{"phenomena": [
                    {"name": "社会网络", "description": "复杂的关系网络", "evidence": ["数据1"], "significance": "重要"}
                ]}'''
            elif 'frameworks' in prompt:
                return '''{"frameworks": [
                    {"name": "社会网络分析", "scholar": "格兰诺维特", "core_concepts": ["弱关系"], "applicability": "适用", "analysis_focus": "关系"}
                ]}'''
            elif 'findings' in prompt:
                return '''{"findings": ["发现1", "发现2", "发现3"]}'''
            elif 'insights' in prompt:
                return '''{"insights": [
                    {"insight": "洞察1", "theoretical_contribution": "贡献", "research_value": "价值"}
                ]}'''
            elif 'opportunities' in prompt or 'business_elements' in prompt:
                return '''{"resources": [], "target_market": {}, "value_proposition": {}, "revenue_sources": [], "partners": [], "cost_structure": []}'''
            else:
                return '{"result": "mock json"}'
        else:
            return f"这是基于数据的分析结果。[模拟LLM输出，prompt长度: {len(prompt)}字符]"


class MockSemanticAnalyzer:
    """模拟语义分析器"""
    async def analyze_documents(self, documents):
        from app.services.semantic_analyzer import SemanticAnalysisResult, ClusterInfo, TopicInfo
        import numpy as np

        return SemanticAnalysisResult(
            clusters=[
                ClusterInfo(
                    cluster_id=0,
                    document_ids=[str(d.id) for d in documents],
                    size=len(documents),
                    centroid=np.array([0.1, 0.2, 0.3]),
                    keywords=["扶贫", "乡村", "发展"],
                    coherence_score=0.85,
                    representative_chunks=["代表性文本块1"]
                )
            ],
            topics=[
                TopicInfo(
                    topic_id=0,
                    keywords=[("扶贫", 0.9), ("发展", 0.8), ("乡村", 0.7)],
                    document_count=len(documents),
                    representative_texts=["代表性文本1"],
                    topic_coherence=0.82
                )
            ],
            similarity_matrix=np.eye(len(documents)),
            cross_relations=[],
            outliers=[],
            vectors=np.random.rand(len(documents), 384),
            document_embeddings={str(d.id): np.random.rand(384) for d in documents},
            visualization_data={
                "tsne_coordinates": np.random.rand(len(documents), 2).tolist(),
                "cluster_colors": ["#FF0000"] * len(documents)
            },
            analysis_metadata={
                "total_documents": len(documents),
                "total_chunks": len(documents) * 10,
                "embedding_dimension": 384,
                "analysis_time": "2026-08-01T19:30:00"
            }
        )


class MockGraphBuilder:
    """模拟图谱构建器"""
    async def build_graph(self, documents):
        return {
            'nodes': [
                {'name': '实体1', 'type': 'person', 'degree': 5},
                {'name': '实体2', 'type': 'location', 'degree': 3}
            ],
            'edges': [
                {'from': '实体1', 'to': '实体2', 'type': 'located_in', 'weight': 1.0}
            ],
            'communities': []
        }


class MockDB:
    """模拟数据库会话"""
    def __init__(self, documents=None, entities=None):
        self._documents = documents or []
        self._entities = entities or []

    def query(self, model):
        return self

    def filter(self, condition):
        return self

    def all(self):
        # 根据model类型返回不同数据
        if hasattr(self, '_return_docs'):
            return self._documents
        elif hasattr(self, '_return_entities'):
            return self._entities
        return []


# ============================================================================
# 测试 1: CitationTracker
# ============================================================================

@pytest.mark.asyncio
async def test_citation_tracker():
    """测试引用追踪系统"""
    print("\n" + "="*60)
    print("测试 1: CitationTracker - 引用追踪系统")
    print("="*60)

    tracker = CitationTracker()

    # 创建引用
    citation = tracker.create_citation(
        document_id='doc_123',
        text_snippet='18洞村在2013年开始精准扶贫试点',
        start_pos=0,
        end_pos=20,
        confidence=1.0
    )

    print(f"✓ 创建引用: {citation.citation_id[:8]}...")
    print(f"  - 文档ID: {citation.document_id}")
    print(f"  - 文本片段: {citation.text_snippet}")
    print(f"  - 置信度: {citation.confidence}")

    # 测试引用标注
    text = "18洞村在2013年开始精准扶贫试点，成为示范点。"
    documents = [
        {'id': 'doc_123', 'content': '18洞村在2013年开始精准扶贫试点，取得显著成效。'}
    ]

    annotated = tracker.annotate_text_with_citations(text, documents)
    print(f"\n✓ 自动标注引用: {len(annotated.citations)}个引用")

    # 验证报告
    report = tracker.generate_citation_report()
    print(f"\n✓ 生成引用报告:")
    print(f"  - 总引用数: {report['total_citations']}")
    print(f"  - 引用文档数: {report['documents_cited']}")
    print(f"  - 平均置信度: {report['avg_confidence']:.2f}")

    assert report['total_citations'] >= 1, "应该有至少1个引用"
    print("\n✅ CitationTracker测试通过")


# ============================================================================
# 测试 2: CostController
# ============================================================================

@pytest.mark.asyncio
async def test_cost_controller():
    """测试成本控制系统"""
    print("\n" + "="*60)
    print("测试 2: CostController - 成本控制系统")
    print("="*60)

    budget = CostBudget(
        daily_limit=5.0,
        per_request_limit=1.0,
        monthly_limit=100.0
    )
    controller = CostController(budget)

    # 估算成本
    prompt = "这是一个测试prompt，需要估算token成本。" * 10
    estimate = controller.estimate_cost(
        prompt=prompt,
        max_output_tokens=1000,
        model='claude-3-sonnet'
    )

    print(f"✓ 成本估算:")
    print(f"  - 模型: {estimate['model']}")
    print(f"  - 输入tokens: {estimate['estimated_input_tokens']}")
    print(f"  - 输出tokens: {estimate['max_output_tokens']}")
    print(f"  - 预估成本: ${estimate['total_cost']:.4f}")
    print(f"  - 在预算内: {estimate['within_budget']}")

    # 检查是否应该继续
    should_proceed, reason = controller.should_proceed(estimate['total_cost'])
    print(f"\n✓ 预算检查: {should_proceed}")
    print(f"  - 原因: {reason}")

    # 记录使用
    record = controller.record_usage(
        model='claude-3-sonnet',
        input_tokens=100,
        output_tokens=500,
        purpose='test'
    )
    print(f"\n✓ 记录使用:")
    print(f"  - 实际成本: ${record.cost:.4f}")
    print(f"  - 用途: {record.purpose}")

    # 使用报告
    report = controller.get_usage_report()
    print(f"\n✓ 使用报告:")
    print(f"  - 总请求数: {report['total_requests']}")
    print(f"  - 总成本: ${report['total_cost']:.4f}")
    print(f"  - 日已用: ${report['budget_status']['daily_spent']:.4f}")
    print(f"  - 日剩余: ${report['budget_status']['daily_remaining']:.4f}")

    # 模型推荐
    model = controller.suggest_model('complex', budget_priority=False)
    print(f"\n✓ 模型推荐（复杂任务）: {model}")

    assert report['total_requests'] == 1, "应该有1条记录"
    assert report['total_cost'] > 0, "成本应该大于0"
    print("\n✅ CostController测试通过")


# ============================================================================
# 测试 3: Tier1AnalyzerV2
# ============================================================================

@pytest.mark.asyncio
async def test_tier1_analyzer():
    """测试Tier1分析器V2"""
    print("\n" + "="*60)
    print("测试 3: Tier1AnalyzerV2 - LLM驱动的数据整理分析")
    print("="*60)

    # 创建mock对象
    documents = [
        MockDocument(1, 'doc1.txt', '18洞村位于湘西，是精准扶贫首倡地。' * 10),
        MockDocument(2, 'doc2.txt', '该村通过发展旅游业和特色农业实现脱贫。' * 10)
    ]

    entities = [
        MockEntity(1, '18洞村', 'location'),
        MockEntity(2, '习近平', 'person'),
        MockEntity(3, '湘西', 'location')
    ]

    # 创建分析器（替换LLM为mock）
    analyzer = Tier1AnalyzerV2()
    analyzer.llm_analyzer = MockLLMAnalyzer()
    analyzer.semantic_analyzer = MockSemanticAnalyzer()

    # 创建mock DB
    mock_db = MockDB(documents, entities)

    print("✓ 准备数据:")
    print(f"  - 文档数: {len(documents)}")
    print(f"  - 实体数: {len(entities)}")

    # 执行分析
    print("\n⚙️  执行Tier1分析...")
    start_time = datetime.now()

    result = await analyzer.generate_report(
        db=mock_db,
        document_ids=[1, 2],
        context_ids=[],
        entity_ids=[1, 2, 3]
    )

    duration = (datetime.now() - start_time).total_seconds()

    print(f"✓ 分析完成 (耗时: {duration:.2f}秒)")
    print(f"\n✓ 分析结果:")
    print(f"  - Tier: {result['tier']}")
    print(f"  - 标题: {result['title']}")
    print(f"  - 关键维度数: {len(result.get('key_dimensions', []))}")
    print(f"  - 分析章节数: {len(result.get('sections', []))}")
    print(f"  - 关键发现数: {len(result.get('key_findings', []))}")

    # 验证结果结构
    assert result['tier'] == 1, "应该是Tier1"
    assert 'summary' in result, "应该有摘要"
    assert 'key_dimensions' in result, "应该有关键维度"
    assert 'sections' in result, "应该有分析章节"
    assert 'metadata' in result, "应该有元数据"
    assert result['metadata']['llm_driven'] == True, "应该是LLM驱动"

    print("\n✓ 成本统计:")
    print(f"  - 总请求数: {result['cost_report']['total_requests']}")
    print(f"  - 总成本: ${result['cost_report']['total_cost']:.4f}")

    print("\n✅ Tier1AnalyzerV2测试通过")


# ============================================================================
# 测试 4: Tier2AnalyzerV2
# ============================================================================

@pytest.mark.asyncio
async def test_tier2_analyzer():
    """测试Tier2分析器V2"""
    print("\n" + "="*60)
    print("测试 4: Tier2AnalyzerV2 - LLM驱动的学术深度分析")
    print("="*60)

    documents = [
        MockDocument(1, 'doc1.txt', '社会网络分析显示村民之间存在紧密联系。' * 10)
    ]

    # Mock Tier1结果
    tier1_result = {
        'key_findings': ['发现1', '发现2'],
        'key_dimensions': [
            {'name': '维度1', 'description': '描述1', 'data_support': '支持1'}
        ],
        'data_stats': {'documents': 2, 'entities': 3}
    }

    # 创建分析器
    analyzer = Tier2AnalyzerV2()
    analyzer.llm_analyzer = MockLLMAnalyzer()
    analyzer.graph_builder = MockGraphBuilder()

    mock_db = MockDB(documents)

    print("✓ 准备数据:")
    print(f"  - Tier1维度数: {len(tier1_result['key_dimensions'])}")

    print("\n⚙️  执行Tier2分析...")
    start_time = datetime.now()

    result = await analyzer.generate_report(
        db=mock_db,
        document_ids=[1],
        tier1_result=tier1_result,
        semantic_result=None,
        knowledge_graph=None
    )

    duration = (datetime.now() - start_time).total_seconds()

    print(f"✓ 分析完成 (耗时: {duration:.2f}秒)")
    print(f"\n✓ 分析结果:")
    print(f"  - Tier: {result['tier']}")
    print(f"  - 识别现象数: {len(result.get('phenomena', []))}")
    print(f"  - 理论框架数: {len(result.get('theoretical_frameworks', []))}")
    print(f"  - 框架分析数: {len(result.get('framework_analyses', []))}")
    print(f"  - 学术洞察数: {len(result.get('academic_insights', []))}")

    assert result['tier'] == 2, "应该是Tier2"
    assert 'phenomena' in result, "应该识别学术现象"
    assert 'theoretical_frameworks' in result, "应该选择理论框架"
    assert result['metadata']['frameworks_auto_selected'] == True, "框架应该自动选择"

    print("\n✅ Tier2AnalyzerV2测试通过")


# ============================================================================
# 测试 5: Tier3AnalyzerV2
# ============================================================================

@pytest.mark.asyncio
async def test_tier3_analyzer():
    """测试Tier3分析器V2"""
    print("\n" + "="*60)
    print("测试 5: Tier3AnalyzerV2 - LLM驱动的商业价值分析")
    print("="*60)

    documents = [
        MockDocument(1, 'doc1.txt', '旅游业发展潜力巨大，年收入增长30%。' * 10)
    ]

    tier1_result = {
        'key_findings': ['市场潜力大'],
        'key_dimensions': []
    }

    tier2_result = {
        'phenomena': [{'name': '经济增长'}],
        'academic_insights': [{'insight': '可持续发展'}]
    }

    # 创建分析器
    analyzer = Tier3AnalyzerV2()
    analyzer.llm_analyzer = MockLLMAnalyzer()

    mock_db = MockDB(documents)

    print("✓ 准备数据:")
    print(f"  - Tier1发现数: {len(tier1_result['key_findings'])}")
    print(f"  - Tier2现象数: {len(tier2_result['phenomena'])}")

    print("\n⚙️  执行Tier3分析...")
    start_time = datetime.now()

    result = await analyzer.generate_report(
        db=mock_db,
        document_ids=[1],
        tier1_result=tier1_result,
        tier2_result=tier2_result,
        market_context={'industry': '文化旅游', 'region': '湘西'}
    )

    duration = (datetime.now() - start_time).total_seconds()

    print(f"✓ 分析完成 (耗时: {duration:.2f}秒)")
    print(f"\n✓ 分析结果:")
    print(f"  - Tier: {result['tier']}")
    print(f"  - 商业机会数: {len(result.get('opportunities', []))}")
    print(f"  - 商业模式数: {len(result.get('business_models', []))}")
    print(f"  - 市场数据质量: {result.get('market_data', {}).get('data_quality')}")

    assert result['tier'] == 3, "应该是Tier3"
    assert 'business_elements' in result, "应该有商业要素"
    assert 'market_data' in result, "应该有市场数据"
    assert 'opportunities' in result, "应该有商业机会"

    print("\n✅ Tier3AnalyzerV2测试通过")


# ============================================================================
# 测试 6: MarketDataCollector
# ============================================================================

@pytest.mark.asyncio
async def test_market_data_collector():
    """测试市场数据收集器"""
    print("\n" + "="*60)
    print("测试 6: MarketDataCollector - 市场数据收集")
    print("="*60)

    collector = MarketDataCollector()

    market_data = await collector.collect_market_data(
        industry='文化旅游',
        region='湘西',
        keywords=['乡村旅游', '精准扶贫']
    )

    print("✓ 收集市场数据:")
    print(f"  - 行业: {market_data['industry']}")
    print(f"  - 地区: {market_data['region']}")
    print(f"  - 数据质量: {market_data['data_quality']}")
    print(f"  - 收集时间: {market_data['collected_at']}")

    assert 'industry' in market_data, "应该有行业信息"
    assert 'market_size' in market_data, "应该有市场规模"
    print("\n✅ MarketDataCollector测试通过")


# ============================================================================
# 测试 7: AnalysisWorkflow集成测试
# ============================================================================

@pytest.mark.asyncio
async def test_analysis_workflow():
    """测试完整分析工作流"""
    print("\n" + "="*60)
    print("测试 7: AnalysisWorkflow - 完整工作流集成")
    print("="*60)

    # 注意：这个测试需要更多的mock，这里只做基本验证
    workflow = AnalysisWorkflow()

    print("✓ 工作流创建成功")
    print(f"  - 文档处理器: {workflow.doc_processor is not None}")
    print(f"  - 语义分析器: {workflow.semantic_analyzer is not None}")
    print(f"  - Tier1分析器: {workflow.tier1_analyzer is not None}")
    print(f"  - Tier2分析器: {workflow.tier2_analyzer is not None}")
    print(f"  - Tier3分析器: {workflow.tier3_analyzer is not None}")
    print(f"  - 工作流引擎: {workflow.workflow_engine is not None}")

    assert workflow.tier1_analyzer is not None, "应该有Tier1分析器"
    assert workflow.tier2_analyzer is not None, "应该有Tier2分析器"
    assert workflow.tier3_analyzer is not None, "应该有Tier3分析器"

    print("\n✅ AnalysisWorkflow测试通过")


# ============================================================================
# 运行所有测试
# ============================================================================

async def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*70)
    print(" " * 15 + "Phase 5 - 重构分析器测试套件")
    print("="*70)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)

    tests = [
        ('CitationTracker', test_citation_tracker),
        ('CostController', test_cost_controller),
        ('Tier1AnalyzerV2', test_tier1_analyzer),
        ('Tier2AnalyzerV2', test_tier2_analyzer),
        ('Tier3AnalyzerV2', test_tier3_analyzer),
        ('MarketDataCollector', test_market_data_collector),
        ('AnalysisWorkflow', test_analysis_workflow),
    ]

    passed = 0
    failed = 0
    errors = []

    for name, test_func in tests:
        try:
            await test_func()
            passed += 1
        except Exception as e:
            failed += 1
            errors.append((name, str(e)))
            print(f"\n❌ {name}测试失败: {e}")

    # 总结
    print("\n" + "="*70)
    print(" " * 25 + "测试总结")
    print("="*70)
    print(f"✅ 通过: {passed}/{len(tests)}")
    print(f"❌ 失败: {failed}/{len(tests)}")
    print(f"📊 通过率: {(passed/len(tests)*100):.1f}%")

    if errors:
        print("\n失败的测试:")
        for name, error in errors:
            print(f"  - {name}: {error}")

    print("\n" + "="*70)

    return passed, failed


if __name__ == '__main__':
    # 运行测试
    passed, failed = asyncio.run(run_all_tests())

    # 退出码
    exit(0 if failed == 0 else 1)
