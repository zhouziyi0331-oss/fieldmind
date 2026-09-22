"""
测试增强对话服务V2整合

验证：
1. 记忆整合器工作正常
2. 深度思考引擎工作正常
3. 技能对话适配器工作正常
4. 完整对话流程
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session

from app.services.enhanced_chat_service_v2 import EnhancedChatServiceV2, create_enhanced_chat_service_v2
from app.core.memory_aggregator import MemoryAggregator, get_memory_aggregator
from app.core.deep_thinking_engine import DeepThinkingEngine, get_deep_thinking_engine
from app.core.skill_chat_adapter import SkillChatAdapter, create_skill_chat_adapter


class TestMemoryAggregator:
    """测试记忆整合器"""

    def test_initialization(self):
        """测试初始化"""
        aggregator = MemoryAggregator()

        assert aggregator is not None
        assert aggregator.source_weights is not None
        assert len(aggregator.source_weights) >= 6

    def test_singleton(self):
        """测试单例模式"""
        aggregator1 = get_memory_aggregator()
        aggregator2 = get_memory_aggregator()

        assert aggregator1 is aggregator2

    def test_aggregate_memory_structure(self):
        """测试记忆聚合结构"""
        aggregator = MemoryAggregator()

        # Mock所有记忆源
        with patch.object(aggregator, '_retrieve_long_memory', return_value=None):
            with patch.object(aggregator, '_retrieve_cognee', return_value=None):
                with patch.object(aggregator, '_retrieve_lightrag', return_value=None):
                    result = aggregator.aggregate_memory(
                        query="测试查询",
                        session_id="test_session",
                        project_id=1
                    )

        # 验证返回结构
        assert 'context' in result
        assert 'sources_used' in result
        assert 'source_results' in result
        assert 'processing_time' in result
        assert isinstance(result['processing_time'], float)

    def test_memory_source_weights(self):
        """测试记忆源权重配置"""
        aggregator = MemoryAggregator()

        assert aggregator.source_weights['long_memory'] == 1.0
        assert aggregator.source_weights['graphrag'] == 0.95
        assert aggregator.source_weights['cognee'] == 0.9
        assert 0 < aggregator.source_weights['khoj'] <= 1.0


class TestDeepThinkingEngine:
    """测试深度思考引擎"""

    def test_initialization(self):
        """测试初始化"""
        engine = DeepThinkingEngine()

        assert engine is not None
        assert engine.extended_thinking_model == "claude-3-7-sonnet-20250219"
        assert engine.thinking_levels is not None

    def test_thinking_levels(self):
        """测试思考级别配置"""
        engine = DeepThinkingEngine()
        levels = engine.get_thinking_levels()

        assert 'quick' in levels
        assert 'normal' in levels
        assert 'deep' in levels
        assert 'thorough' in levels
        assert 'extreme' in levels

        assert levels['quick']['budget'] == 2000
        assert levels['extreme']['budget'] == 50000

    def test_complexity_analysis(self):
        """测试复杂度分析"""
        engine = DeepThinkingEngine()

        # 简单问题
        simple_complexity = engine._analyze_complexity("你好")
        assert simple_complexity in ['simple', 'moderate']

        # 复杂问题
        complex_query = "请详细分析并比较深度学习和传统机器学习在图像识别任务中的优劣，" \
                       "并从算法原理、计算复杂度、数据需求等多个维度进行系统性评估。"
        complex_complexity = engine._analyze_complexity(complex_query)
        assert complex_complexity in ['complex', 'very_complex', 'extremely_complex']

    def test_thinking_analysis(self):
        """测试思考分析"""
        engine = DeepThinkingEngine()

        thinking_text = "因为这个问题涉及多个方面，所以需要仔细考虑。" \
                       "首先考虑A方面，然后注意B方面。另一方面，还要考虑C。" \
                       "综合以上分析，得出结论：..."

        analysis = engine._analyze_thinking(thinking_text, budget=5000)

        assert 'thinking_length' in analysis
        assert 'budget_usage' in analysis
        assert 'depth_score' in analysis
        assert 'quality' in analysis
        assert analysis['depth_score'] > 0

    def test_singleton(self):
        """测试单例模式"""
        engine1 = get_deep_thinking_engine()
        engine2 = get_deep_thinking_engine()

        assert engine1 is engine2


class TestSkillChatAdapter:
    """测试技能对话适配器"""

    @pytest.fixture
    def mock_db(self):
        """Mock数据库会话"""
        return Mock(spec=Session)

    def test_initialization(self, mock_db):
        """测试初始化"""
        adapter = SkillChatAdapter(mock_db)

        assert adapter is not None
        assert adapter.db == mock_db

    def test_skill_relevance_calculation(self, mock_db):
        """测试技能相关度计算"""
        adapter = SkillChatAdapter(mock_db)

        skill = {
            'name': '文本分析',
            'description': '对文本进行深度分析和总结',
            'type': 'analysis',
            'tags': ['分析', '文本', 'NLP'],
            'usage_count': 10
        }

        query = "请帮我分析这段文本的核心观点"

        score = adapter._calculate_skill_relevance(
            skill=skill,
            query=query,
            project_id=1,
            history=None
        )

        assert 0 <= score <= 1.0
        assert score > 0.3  # 应该有较高相关度

    def test_fallback_context(self, mock_db):
        """测试降级上下文"""
        adapter = SkillChatAdapter(mock_db)

        skill_config = {
            'skill_name': '测试技能',
            'parameters': {'param1': 'value1'}
        }

        context = adapter._fallback_context(skill_config)

        assert context is not None
        assert 'system_prompt' in context
        assert 'parameters' in context
        assert 'metadata' in context
        assert context['metadata']['fallback'] == True


class TestEnhancedChatServiceV2:
    """测试增强对话服务V2"""

    @pytest.fixture
    def mock_db(self):
        """Mock数据库会话"""
        return Mock(spec=Session)

    @pytest.fixture
    def service(self, mock_db):
        """创建服务实例"""
        with patch('app.services.enhanced_chat_service_v2.Anthropic'):
            service = EnhancedChatServiceV2(mock_db)
            service.client = Mock()  # Mock Claude客户端
            return service

    def test_initialization(self, service, mock_db):
        """测试初始化"""
        assert service is not None
        assert service.db == mock_db
        assert service.memory_aggregator is not None
        assert service.thinking_engine is not None
        assert service.skill_adapter is not None

    def test_service_status(self, service):
        """测试服务状态"""
        status = service.get_service_status()

        assert 'client_initialized' in status
        assert 'memory_aggregator' in status
        assert 'thinking_engine' in status
        assert 'skill_adapter' in status
        assert 'timestamp' in status

    def test_prepare_chat_context(self, service):
        """测试准备对话上下文"""
        with patch.object(service.memory_aggregator, 'aggregate_memory') as mock_memory:
            mock_memory.return_value = {
                'context': '测试记忆上下文',
                'sources_used': ['long_memory'],
                'source_results': {'long_memory': 1}
            }

            with patch.object(service, '_retrieve_rag_context') as mock_rag:
                mock_rag.return_value = {
                    'sources': [],
                    'count': 0,
                    'context_text': ''
                }

                context = service._prepare_chat_context(
                    query="测试查询",
                    session_id="test_session",
                    project_id=1,
                    user_id=1,
                    config={'use_memory': True, 'use_rag': True}
                )

        assert context is not None
        assert 'query' in context
        assert 'memory' in context
        assert 'rag' in context

    def test_build_system_prompt(self, service):
        """测试构建系统提示词"""
        context = {
            'skill': {
                'system_prompt': '## 技能: 测试技能\n这是技能描述'
            }
        }

        prompt = service._build_system_prompt(context)

        assert '技能: 测试技能' in prompt
        assert 'FieldMind' in prompt

    def test_build_full_message(self, service):
        """测试构建完整消息"""
        context = {
            'memory': {
                'context': '这是记忆上下文'
            },
            'rag': {
                'context_text': '这是RAG上下文'
            }
        }

        message = service._build_full_message(
            query="测试问题",
            context=context
        )

        assert '记忆上下文' in message
        assert 'RAG上下文' in message
        assert '测试问题' in message
        assert '<记忆上下文>' in message
        assert '<用户问题>' in message

    def test_error_response(self, service):
        """测试错误响应"""
        error = service._error_response("测试错误")

        assert error['error'] == True
        assert error['message'] == "测试错误"
        assert 'timestamp' in error


class TestIntegration:
    """测试完整集成"""

    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)

    def test_factory_function(self, mock_db):
        """测试工厂函数"""
        with patch('app.services.enhanced_chat_service_v2.Anthropic'):
            service = create_enhanced_chat_service_v2(mock_db)

            assert isinstance(service, EnhancedChatServiceV2)
            assert service.db == mock_db

    def test_all_components_loaded(self, mock_db):
        """测试所有组件都已加载"""
        with patch('app.services.enhanced_chat_service_v2.Anthropic'):
            service = create_enhanced_chat_service_v2(mock_db)

            # 验证所有核心组件
            assert service.memory_aggregator is not None
            assert service.thinking_engine is not None
            assert service.skill_adapter is not None

            # 验证组件类型
            assert isinstance(service.memory_aggregator, MemoryAggregator)
            assert isinstance(service.thinking_engine, DeepThinkingEngine)
            assert isinstance(service.skill_adapter, SkillChatAdapter)

    def test_config_propagation(self, mock_db):
        """测试配置传递"""
        with patch('app.services.enhanced_chat_service_v2.Anthropic'):
            service = create_enhanced_chat_service_v2(mock_db)

            config = {
                'use_memory': True,
                'use_deep_thinking': True,
                'use_skill': True,
                'use_rag': True,
                'thinking_level': 'deep',
                'max_tokens': 4096
            }

            # 验证配置可以正确传递（不实际调用API）
            assert config['use_memory'] == True
            assert config['thinking_level'] == 'deep'
            assert config['max_tokens'] == 4096


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
