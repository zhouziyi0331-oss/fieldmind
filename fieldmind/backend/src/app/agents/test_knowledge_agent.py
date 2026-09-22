"""
KnowledgeAgent 综合测试
测试知识图谱构建代理的所有功能
"""

import pytest
import sys
import os
from typing import List, Dict, Any
from enum import Enum

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.agents.knowledge_agent import (
    KnowledgeAgent,
    KnowledgeStrategy,
    ExtractedEntity,
    DiscoveredRelation,
    KnowledgeGraph,
    KnowledgeResult
)


@pytest.fixture
def knowledge_agent():
    """创建KnowledgeAgent实例"""
    return KnowledgeAgent(
        default_strategy=KnowledgeStrategy.AUTO,
        enable_llm=False,  # 测试时不启用LLM
        enable_cross_document=True,
        confidence_threshold=0.5
    )


@pytest.fixture
def sample_vectorized_chunks():
    """示例向量化chunks"""
    return [
        {
            'chunk_id': 'chunk_1',
            'text': '费孝通先生在十八洞村进行了深入的田野调查研究。他发现当地的祠堂文化保存完好。',
            'embedding': [0.1] * 1024,
            'metadata': {'document_id': 1, 'chunk_index': 0}
        },
        {
            'chunk_id': 'chunk_2',
            'text': '十八洞村位于湖南省湘西州，是精准扶贫的典型案例。村民们通过发展旅游业实现了脱贫致富。',
            'embedding': [0.2] * 1024,
            'metadata': {'document_id': 1, 'chunk_index': 1}
        },
        {
            'chunk_id': 'chunk_3',
            'text': '祠堂是宗族文化的重要载体。费孝通在《乡土中国》中详细论述了宗族关系对乡村社会的影响。',
            'embedding': [0.3] * 1024,
            'metadata': {'document_id': 2, 'chunk_index': 0}
        }
    ]


class TestKnowledgeAgentInitialization:
    """测试KnowledgeAgent初始化"""

    def test_default_initialization(self):
        """测试默认初始化"""
        agent = KnowledgeAgent()
        assert agent.default_strategy == KnowledgeStrategy.AUTO
        assert agent.enable_llm == False
        assert agent.enable_cross_document == True
        assert agent.confidence_threshold == 0.5

    def test_custom_initialization(self):
        """测试自定义初始化"""
        agent = KnowledgeAgent(
            default_strategy=KnowledgeStrategy.ENTITY_FOCUSED,
            enable_llm=True,
            enable_cross_document=False,
            confidence_threshold=0.7
        )
        assert agent.default_strategy == KnowledgeStrategy.ENTITY_FOCUSED
        assert agent.enable_llm == True
        assert agent.enable_cross_document == False
        assert agent.confidence_threshold == 0.7

    def test_services_lazy_loading(self, knowledge_agent):
        """测试服务延迟加载"""
        # 初始化时服务应为None
        assert knowledge_agent._knowledge_graph_service is None
        assert knowledge_agent._entity_extraction_service is None
        assert knowledge_agent._relation_discovery_engine is None
        assert knowledge_agent._knowledge_graph_builder is None


class TestServiceLoading:
    """测试服务加载"""

    def test_load_knowledge_graph_service(self, knowledge_agent):
        """测试加载KnowledgeGraphService"""
        service = knowledge_agent._get_knowledge_graph_service()
        assert service is not None
        assert knowledge_agent._knowledge_graph_service is not None

        # 再次调用应返回同一实例
        service2 = knowledge_agent._get_knowledge_graph_service()
        assert service is service2

    def test_load_entity_extraction_service(self, knowledge_agent):
        """测试加载EntityExtractionService"""
        service = knowledge_agent._get_entity_extraction_service()
        assert service is not None
        assert knowledge_agent._entity_extraction_service is not None

    def test_load_relation_discovery_engine(self, knowledge_agent):
        """测试加载RelationDiscoveryEngine"""
        # RelationDiscoveryEngine需要db_session参数
        # 这里使用mock db
        from unittest.mock import MagicMock
        mock_db = MagicMock()

        engine = knowledge_agent._get_relation_discovery_engine(mock_db)
        assert engine is not None

    def test_load_knowledge_graph_builder(self, knowledge_agent):
        """测试加载KnowledgeGraphBuilder"""
        # KnowledgeGraphBuilder需要db_session参数
        from unittest.mock import MagicMock
        mock_db = MagicMock()

        builder = knowledge_agent._get_knowledge_graph_builder(mock_db)
        assert builder is not None


class TestStrategySelection:
    """测试策略选择"""

    def test_select_cross_document_strategy(self, knowledge_agent):
        """测试选择跨文档策略"""
        chunks = [{'text': 'test'}] * 10
        document_ids = [1, 2, 3]
        project_id = 1

        strategy = knowledge_agent._select_strategy(chunks, project_id, document_ids)
        assert strategy == KnowledgeStrategy.CROSS_DOCUMENT

    def test_select_comprehensive_strategy(self, knowledge_agent):
        """测试选择综合策略（大量chunks）"""
        chunks = [{'text': 'test'}] * 150
        document_ids = [1]
        project_id = 1

        strategy = knowledge_agent._select_strategy(chunks, project_id, document_ids)
        assert strategy == KnowledgeStrategy.COMPREHENSIVE

    def test_select_entity_focused_strategy(self, knowledge_agent):
        """测试选择实体为中心策略（中等chunks）"""
        chunks = [{'text': 'test'}] * 50
        document_ids = [1]
        project_id = None

        strategy = knowledge_agent._select_strategy(chunks, project_id, document_ids)
        assert strategy == KnowledgeStrategy.ENTITY_FOCUSED

    def test_select_relation_focused_strategy(self, knowledge_agent):
        """测试选择关系为中心策略（少量chunks）"""
        chunks = [{'text': 'test'}] * 10
        document_ids = [1]
        project_id = None

        strategy = knowledge_agent._select_strategy(chunks, project_id, document_ids)
        assert strategy == KnowledgeStrategy.RELATION_FOCUSED


class TestEntityExtraction:
    """测试实体提取"""

    def test_entity_focused_strategy(self, knowledge_agent, sample_vectorized_chunks):
        """测试实体为中心策略"""
        result = knowledge_agent._build_entity_focused(
            chunks=sample_vectorized_chunks,
            project_id=None,
            document_ids=None,
            db_session=None
        )

        assert isinstance(result, KnowledgeResult)
        assert result.strategy == 'entity_focused'
        assert result.entity_count > 0
        assert result.relation_count == 0

        # 验证提取的实体
        entities = result.knowledge_graph.nodes
        assert len(entities) > 0

        # 应该提取到"费孝通"、"十八洞村"、"祠堂"等实体
        entity_names = [e.name for e in entities]
        print(f"\nExtracted entities: {entity_names}")

        # 验证实体类型
        for entity in entities:
            assert isinstance(entity, ExtractedEntity)
            assert entity.name
            assert entity.entity_type
            assert entity.confidence >= 0.0

    def test_deduplicate_entities(self, knowledge_agent):
        """测试实体去重"""
        entities = [
            {'name': '费孝通', 'type': 'person', 'confidence': 0.9},
            {'name': '十八洞村', 'type': 'location', 'confidence': 0.8},
            {'name': '费孝通', 'type': 'person', 'confidence': 0.95},  # 重复
            {'name': '祠堂', 'type': 'custom', 'confidence': 0.7},
        ]

        unique_entities = knowledge_agent._deduplicate_entities(entities)
        assert len(unique_entities) == 3

        names = [e['name'] for e in unique_entities]
        assert '费孝通' in names
        assert '十八洞村' in names
        assert '祠堂' in names


class TestRelationExtraction:
    """测试关系提取"""

    def test_relation_focused_strategy(self, knowledge_agent, sample_vectorized_chunks):
        """测试关系为中心策略"""
        result = knowledge_agent._build_relation_focused(
            chunks=sample_vectorized_chunks,
            project_id=None,
            document_ids=None,
            db_session=None
        )

        assert isinstance(result, KnowledgeResult)
        assert result.strategy == 'relation_focused'
        assert result.entity_count >= 0
        assert result.relation_count >= 0

        # 验证关系
        relations = result.knowledge_graph.edges
        for relation in relations:
            assert isinstance(relation, DiscoveredRelation)
            assert relation.source_entity
            assert relation.target_entity
            assert relation.relation_type
            assert relation.discovery_strategy == 'relation_focused'


class TestComprehensiveStrategy:
    """测试综合策略"""

    def test_comprehensive_build(self, knowledge_agent, sample_vectorized_chunks):
        """测试综合策略构建"""
        result = knowledge_agent._build_comprehensive(
            chunks=sample_vectorized_chunks,
            project_id=1,
            document_ids=[1, 2],
            db_session=None
        )

        assert isinstance(result, KnowledgeResult)
        assert result.strategy == 'comprehensive'
        assert result.entity_count > 0

        # 综合策略应该使用多个服务
        # 应该有实体和可能的关系
        assert len(result.knowledge_graph.nodes) > 0

        print(f"\nComprehensive result: {result.entity_count} entities, {result.relation_count} relations")


class TestBuildFromVectorizedChunks:
    """测试从向量化chunks构建"""

    def test_build_with_auto_strategy(self, knowledge_agent, sample_vectorized_chunks):
        """测试自动策略构建"""
        result = knowledge_agent.build_from_vectorized_chunks(
            vectorized_chunks=sample_vectorized_chunks,
            project_id=None,
            document_ids=[1, 2],
            strategy=KnowledgeStrategy.AUTO
        )

        assert isinstance(result, KnowledgeResult)
        assert result.entity_count >= 0
        assert result.duration_seconds >= 0

        # 验证知识图谱
        kg = result.knowledge_graph
        assert isinstance(kg, KnowledgeGraph)
        assert kg.node_count == len(kg.nodes)
        assert kg.edge_count == len(kg.edges)

    def test_build_with_entity_focused(self, knowledge_agent, sample_vectorized_chunks):
        """测试实体为中心策略"""
        result = knowledge_agent.build_from_vectorized_chunks(
            vectorized_chunks=sample_vectorized_chunks,
            strategy=KnowledgeStrategy.ENTITY_FOCUSED
        )

        assert result.strategy == 'entity_focused'
        assert result.entity_count > 0

    def test_build_with_relation_focused(self, knowledge_agent, sample_vectorized_chunks):
        """测试关系为中心策略"""
        result = knowledge_agent.build_from_vectorized_chunks(
            vectorized_chunks=sample_vectorized_chunks,
            strategy=KnowledgeStrategy.RELATION_FOCUSED
        )

        assert result.strategy == 'relation_focused'

    def test_build_with_comprehensive(self, knowledge_agent, sample_vectorized_chunks):
        """测试综合策略"""
        result = knowledge_agent.build_from_vectorized_chunks(
            vectorized_chunks=sample_vectorized_chunks,
            strategy=KnowledgeStrategy.COMPREHENSIVE
        )

        assert result.strategy == 'comprehensive'


class TestDataStructures:
    """测试数据结构"""

    def test_extracted_entity_structure(self):
        """测试ExtractedEntity结构"""
        entity = ExtractedEntity(
            entity_id='e1',
            name='费孝通',
            entity_type='person',
            confidence=0.9,
            mentions=[{'text': '费孝通先生'}],
            source_document_id=1,
            canonical_id='canonical_e1'
        )

        assert entity.entity_id == 'e1'
        assert entity.name == '费孝通'
        assert entity.entity_type == 'person'
        assert entity.confidence == 0.9
        assert len(entity.mentions) == 1
        assert entity.source_document_id == 1
        assert entity.canonical_id == 'canonical_e1'

    def test_discovered_relation_structure(self):
        """测试DiscoveredRelation结构"""
        relation = DiscoveredRelation(
            relation_id='r1',
            source_entity='费孝通',
            target_entity='十八洞村',
            relation_type='研究',
            confidence=0.85,
            evidence=['费孝通在十八洞村进行调研'],
            discovery_strategy='co-occurrence'
        )

        assert relation.relation_id == 'r1'
        assert relation.source_entity == '费孝通'
        assert relation.target_entity == '十八洞村'
        assert relation.relation_type == '研究'
        assert relation.confidence == 0.85
        assert len(relation.evidence) == 1
        assert relation.discovery_strategy == 'co-occurrence'

    def test_knowledge_graph_structure(self):
        """测试KnowledgeGraph结构"""
        entity1 = ExtractedEntity(
            entity_id='e1',
            name='费孝通',
            entity_type='person',
            confidence=0.9,
            mentions=[]
        )
        entity2 = ExtractedEntity(
            entity_id='e2',
            name='十八洞村',
            entity_type='location',
            confidence=0.8,
            mentions=[]
        )
        relation = DiscoveredRelation(
            relation_id='r1',
            source_entity='e1',
            target_entity='e2',
            relation_type='研究',
            confidence=0.85,
            evidence=[],
            discovery_strategy='test'
        )

        kg = KnowledgeGraph(
            nodes=[entity1, entity2],
            edges=[relation],
            node_count=2,
            edge_count=1,
            graph_metadata={'test': True}
        )

        assert len(kg.nodes) == 2
        assert len(kg.edges) == 1
        assert kg.node_count == 2
        assert kg.edge_count == 1
        assert kg.graph_metadata['test'] == True


class TestExportFunctionality:
    """测试导出功能"""

    def test_export_to_dict(self, knowledge_agent, sample_vectorized_chunks):
        """测试导出为字典"""
        result = knowledge_agent.build_from_vectorized_chunks(
            vectorized_chunks=sample_vectorized_chunks,
            strategy=KnowledgeStrategy.ENTITY_FOCUSED
        )

        result_dict = knowledge_agent.export_to_dict(result)

        assert isinstance(result_dict, dict)
        assert 'knowledge_graph' in result_dict
        assert 'strategy' in result_dict
        assert 'entity_count' in result_dict
        assert 'relation_count' in result_dict
        assert 'duration_seconds' in result_dict


class TestEdgeCases:
    """测试边界情况"""

    def test_empty_chunks(self, knowledge_agent):
        """测试空chunks"""
        result = knowledge_agent.build_from_vectorized_chunks(
            vectorized_chunks=[],
            strategy=KnowledgeStrategy.ENTITY_FOCUSED
        )

        assert result.entity_count == 0

    def test_chunks_without_text(self, knowledge_agent):
        """测试没有文本的chunks"""
        chunks = [
            {'chunk_id': 'c1', 'embedding': [0.1] * 1024},
            {'chunk_id': 'c2', 'text': '', 'embedding': [0.2] * 1024}
        ]

        result = knowledge_agent.build_from_vectorized_chunks(
            vectorized_chunks=chunks,
            strategy=KnowledgeStrategy.ENTITY_FOCUSED
        )

        # 应该不会崩溃
        assert result.entity_count == 0

    def test_invalid_strategy(self, knowledge_agent, sample_vectorized_chunks):
        """测试无效策略"""
        # 直接构造一个无效策略
        with pytest.raises(ValueError):
            knowledge_agent._build_comprehensive(
                chunks=sample_vectorized_chunks,
                project_id=None,
                document_ids=None,
                db_session=None
            )
            # 然后手动触发无效策略
            class InvalidStrategy(str, Enum):
                INVALID = "invalid"

            knowledge_agent.build_from_vectorized_chunks(
                vectorized_chunks=sample_vectorized_chunks,
                strategy=InvalidStrategy.INVALID
            )


class TestIntegration:
    """集成测试"""

    def test_full_pipeline_entity_focused(self, knowledge_agent, sample_vectorized_chunks):
        """测试完整流程 - 实体为中心"""
        result = knowledge_agent.build_from_vectorized_chunks(
            vectorized_chunks=sample_vectorized_chunks,
            project_id=1,
            document_ids=[1, 2],
            strategy=KnowledgeStrategy.ENTITY_FOCUSED
        )

        assert result.entity_count > 0
        assert result.duration_seconds >= 0
        assert result.project_id == 1
        assert result.document_ids == [1, 2]

        # 验证实体质量
        for entity in result.knowledge_graph.nodes:
            assert entity.name
            assert entity.entity_type in ['person', 'location', 'organization', 'time', 'custom', 'unknown']
            assert 0.0 <= entity.confidence <= 1.0

    def test_full_pipeline_comprehensive(self, knowledge_agent, sample_vectorized_chunks):
        """测试完整流程 - 综合策略"""
        result = knowledge_agent.build_from_vectorized_chunks(
            vectorized_chunks=sample_vectorized_chunks,
            strategy=KnowledgeStrategy.COMPREHENSIVE
        )

        assert result.entity_count >= 0
        assert result.relation_count >= 0

        print(f"\n=== Comprehensive Pipeline Result ===")
        print(f"Entities: {result.entity_count}")
        print(f"Relations: {result.relation_count}")
        print(f"Duration: {result.duration_seconds:.2f}s")
        print(f"Strategy: {result.strategy}")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
