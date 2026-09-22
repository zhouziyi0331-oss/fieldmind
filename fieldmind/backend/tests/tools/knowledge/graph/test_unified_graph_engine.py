"""
Tests for Unified Knowledge Graph Engine
"""

import pytest
from app.tools.knowledge.graph import (
    UnifiedKnowledgeGraphEngine,
    GraphPersistenceService,
    create_knowledge_graph
)


class TestMultiStrategyEntityExtractor:
    """测试多策略实体提取"""

    def test_extract_entities_basic(self):
        """测试基础实体提取"""
        engine = UnifiedKnowledgeGraphEngine(use_jieba=False)  # 使用regex

        text = "张教授在北京大学进行田野调查，研究传统文化的传承问题。"
        entities = engine.entity_extractor.extract_entities(text)

        assert 'person' in entities
        assert 'location' in entities
        assert 'organization' in entities
        assert 'concept' in entities

        # Check specific entities
        person_texts = [e['text'] for e in entities.get('person', [])]
        assert any('教授' in p for p in person_texts)

    def test_stopwords_filtering(self):
        """测试停用词过滤"""
        engine = UnifiedKnowledgeGraphEngine(use_jieba=False)

        text = "这个调查研究的发现表明什么问题呢？"
        entities = engine.entity_extractor.extract_entities(text)

        # Should not extract stopwords
        all_texts = []
        for entity_list in entities.values():
            all_texts.extend([e['text'] for e in entity_list])

        assert '这个' not in all_texts
        assert '什么' not in all_texts


class TestEnhancedRelationExtractor:
    """测试增强关系提取"""

    def test_extract_relations(self):
        """测试关系提取"""
        engine = UnifiedKnowledgeGraphEngine()

        text = "张教授在北京大学工作"
        entities = engine.entity_extractor.extract_entities(text)
        relations = engine.relation_extractor.extract_relations(text, entities)

        assert len(relations) > 0

        # Check relation structure
        rel = relations[0]
        assert 'source' in rel
        assert 'target' in rel
        assert 'relation_type' in rel
        assert 'strength' in rel
        assert 0 <= rel['strength'] <= 1

    def test_relation_strength_calculation(self):
        """测试关系强度计算"""
        engine = UnifiedKnowledgeGraphEngine()

        # Close entities should have higher strength
        text1 = "张教授在北京大学"
        entities1 = engine.entity_extractor.extract_entities(text1)
        relations1 = engine.relation_extractor.extract_relations(text1, entities1)

        # Distant entities should have lower strength
        text2 = "张教授进行了长期的田野调查研究工作最后来到北京大学"
        entities2 = engine.entity_extractor.extract_entities(text2)
        relations2 = engine.relation_extractor.extract_relations(text2, entities2)

        if relations1 and relations2:
            assert relations1[0]['strength'] >= relations2[0]['strength']


class TestUnifiedKnowledgeGraphEngine:
    """测试统一知识图谱引擎"""

    def test_build_graph_from_document(self):
        """测试从文档构建图谱"""
        engine = UnifiedKnowledgeGraphEngine()

        text = "张教授在北京大学研究传统文化"
        graph = engine.build_graph_from_document("doc1", text)

        assert 'doc_id' in graph
        assert 'nodes' in graph
        assert 'edges' in graph
        assert 'statistics' in graph
        assert graph['doc_id'] == 'doc1'
        assert len(graph['nodes']) > 0

    def test_build_unified_graph(self):
        """测试构建统一图谱"""
        engine = UnifiedKnowledgeGraphEngine()

        # Build multiple document graphs
        docs = {
            'doc1': "张教授在北京大学工作",
            'doc2': "张三教授研究传统文化",
            'doc3': "北京大学的研究项目"
        }

        for doc_id, content in docs.items():
            engine.build_graph_from_document(doc_id, content)

        # Build unified graph
        unified = engine.build_unified_graph(align_entities=True)

        assert 'nodes' in unified
        assert 'edges' in unified
        assert 'entity_alignment' in unified
        assert 'statistics' in unified
        assert len(unified['source_documents']) == 3

    def test_query_graph(self):
        """测试图查询"""
        engine = UnifiedKnowledgeGraphEngine()

        text = "张教授在北京大学研究传统文化，他的学生李博士协助调查"
        engine.build_graph_from_document("doc1", text)

        # Query subgraph
        subgraph = engine.query_graph("教授", max_depth=2, use_unified=False)

        assert 'nodes' in subgraph
        assert 'edges' in subgraph
        assert 'center' in subgraph

    def test_find_path(self):
        """测试路径查找"""
        engine = UnifiedKnowledgeGraphEngine()

        text = "张教授在北京大学研究传统文化"
        engine.build_graph_from_document("doc1", text)

        # Find path between entities
        nodes = engine.graphs['doc1']['nodes']
        if len(nodes) >= 2:
            source = nodes[0]['id']
            target = nodes[1]['id']
            path = engine.find_path(source, target, use_unified=False)

            if path:
                assert isinstance(path, list)
                assert source in path
                assert target in path

    def test_get_top_entities(self):
        """测试获取重要实体"""
        engine = UnifiedKnowledgeGraphEngine()

        text = "张教授在北京大学研究传统文化。李教授也在北京大学工作。"
        engine.build_graph_from_document("doc1", text)

        top_entities = engine.get_top_entities(top_k=5, use_unified=False)

        assert isinstance(top_entities, list)
        assert len(top_entities) <= 5

        if top_entities:
            entity, score = top_entities[0]
            assert isinstance(entity, str)
            assert isinstance(score, float)


class TestEntityAlignment:
    """测试实体对齐"""

    def test_entity_alignment(self):
        """测试实体对齐功能"""
        engine = UnifiedKnowledgeGraphEngine()

        # Documents with variant entity names
        docs = {
            'doc1': "张教授在北京大学工作",
            'doc2': "张三教授研究文化",
            'doc3': "张老师进行调查"
        }

        for doc_id, content in docs.items():
            engine.build_graph_from_document(doc_id, content)

        unified = engine.build_unified_graph(align_entities=True)
        alignment = unified['entity_alignment']

        # Check alignment exists
        assert isinstance(alignment, dict)


class TestGraphPersistence:
    """测试图谱持久化"""

    def test_save_and_load_json(self, tmp_path):
        """测试JSON保存和加载"""
        persistence = GraphPersistenceService(
            storage_type='json',
            storage_path=str(tmp_path)
        )

        # Create test graph
        graph_data = {
            'nodes': [
                {'id': 'entity1', 'type': 'person'},
                {'id': 'entity2', 'type': 'location'}
            ],
            'edges': [
                {'source': 'entity1', 'target': 'entity2', 'type': 'located_in'}
            ]
        }

        # Save
        success = persistence.save_graph('test_graph', graph_data)
        assert success

        # Load
        loaded = persistence.load_graph('test_graph')
        assert loaded is not None
        assert loaded['graph_id'] == 'test_graph'
        assert len(loaded['data']['nodes']) == 2

    def test_versioning(self, tmp_path):
        """测试版本控制"""
        persistence = GraphPersistenceService(
            storage_type='json',
            storage_path=str(tmp_path)
        )

        # Save multiple versions
        for i in range(3):
            graph_data = {'nodes': [{'id': f'entity{i}'}], 'edges': []}
            persistence.save_graph('test_graph', graph_data)

        versions = persistence.get_graph_versions('test_graph')
        assert len(versions) == 3
        assert versions == [1, 2, 3]

    def test_list_graphs(self, tmp_path):
        """测试列出图谱"""
        persistence = GraphPersistenceService(
            storage_type='json',
            storage_path=str(tmp_path)
        )

        # Save multiple graphs
        for i in range(3):
            graph_data = {'nodes': [], 'edges': []}
            persistence.save_graph(f'graph{i}', graph_data)

        graphs = persistence.list_graphs()
        assert len(graphs) == 3

    def test_incremental_update(self, tmp_path):
        """测试增量更新"""
        persistence = GraphPersistenceService(
            storage_type='json',
            storage_path=str(tmp_path)
        )

        # Initial graph
        initial = {
            'nodes': [{'id': 'entity1', 'type': 'person'}],
            'edges': []
        }
        persistence.save_graph('test_graph', initial)

        # Incremental update
        updates = {
            'nodes': [{'id': 'entity2', 'type': 'location'}],
            'edges': [{'source': 'entity1', 'target': 'entity2', 'type': 'located_in'}]
        }
        success = persistence.update_graph('test_graph', updates, incremental=True)
        assert success

        # Check merged result
        loaded = persistence.load_graph('test_graph')
        assert len(loaded['data']['nodes']) == 2
        assert len(loaded['data']['edges']) == 1


class TestConvenienceFunctions:
    """测试便捷函数"""

    def test_create_knowledge_graph(self):
        """测试快速创建图谱函数"""
        text = "张教授在北京大学研究传统文化"
        graph = create_knowledge_graph(text)

        assert 'nodes' in graph
        assert 'edges' in graph
        assert 'doc_id' in graph
        assert len(graph['nodes']) > 0


class TestIntegration:
    """集成测试"""

    def test_full_workflow(self, tmp_path):
        """测试完整工作流"""
        # 1. Create engine
        engine = UnifiedKnowledgeGraphEngine()

        # 2. Build graphs from multiple documents
        docs = {
            'interview_001': "张教授在北京大学进行传统文化研究",
            'interview_002': "李博士在清华大学研究民俗学",
            'interview_003': "张三教授和李老师合作项目"
        }

        for doc_id, content in docs.items():
            graph = engine.build_graph_from_document(doc_id, content)
            assert len(graph['nodes']) > 0

        # 3. Build unified graph
        unified = engine.build_unified_graph(
            align_entities=True,
            detect_communities=True
        )

        assert 'communities' in unified
        assert 'pagerank' in unified

        # 4. Query graph
        if unified['nodes']:
            center_entity = unified['nodes'][0]['id']
            subgraph = engine.query_graph(center_entity, max_depth=2)
            assert 'nodes' in subgraph

        # 5. Get top entities
        top = engine.get_top_entities(top_k=5, metric='pagerank')
        assert len(top) <= 5

        # 6. Save to persistence
        persistence = GraphPersistenceService(
            storage_type='json',
            storage_path=str(tmp_path)
        )

        success = persistence.save_graph('unified', unified)
        assert success

        # 7. Load from persistence
        loaded = persistence.load_graph('unified')
        assert loaded is not None
        assert len(loaded['data']['nodes']) == len(unified['nodes'])


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
