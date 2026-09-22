"""
专业Agent实现 (Specialized Agents)

实现5个专业Agent：
1. KnowledgeAgent - 知识分析
2. SearchAgent - 智能检索
3. SummaryAgent - 结构化摘要
4. TranscriptAgent - 音视频转录
5. AnalysisAgent - 深度分析

每个Agent专注于特定领域
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.core.agent_registry import BaseAgent

logger = logging.getLogger(__name__)


# ==================== Knowledge Agent ====================

class KnowledgeAgent(BaseAgent):
    """知识分析Agent"""

    agent_type = "knowledge"
    agent_name = "Knowledge Analysis Agent"
    agent_version = "1.0.0"
    agent_description = "分析文本，提取实体、关系和主题，构建知识图谱"

    capabilities = [
        "entity_extraction",      # 实体提取
        "relation_extraction",    # 关系提取
        "topic_analysis",         # 主题分析
        "knowledge_graph",        # 知识图谱构建
        "semantic_understanding"  # 语义理解
    ]

    input_schema = {
        'required': ['text'],
        'properties': {
            'text': {'type': 'string', 'description': '待分析文本'},
            'extract_entities': {'type': 'boolean', 'default': True},
            'extract_relations': {'type': 'boolean', 'default': True},
            'build_graph': {'type': 'boolean', 'default': False}
        }
    }

    output_schema = {
        'properties': {
            'entities': {'type': 'array', 'description': '提取的实体'},
            'relations': {'type': 'array', 'description': '提取的关系'},
            'topics': {'type': 'array', 'description': '识别的主题'},
            'knowledge_graph': {'type': 'object', 'description': '知识图谱'}
        }
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None, use_workflow_engine: bool = True):



        self.use_workflow_engine = use_workflow_engine



        if use_workflow_engine:


            from app.services.workflow_engine import WorkflowEngine


            self.workflow_engine = WorkflowEngine(max_workers=4)
        super().__init__(config)
        self._lightrag_service = None
        self._chinese_nlp_service = None

    @property
    def lightrag_service(self):
        """LightRAG服务（延迟加载）"""
        if self._lightrag_service is None:
            try:
                from app.services.lightrag_service import get_lightrag_service
                self._lightrag_service = get_lightrag_service()
            except Exception as e:
                logger.warning(f"⚠️ LightRAG服务加载失败: {e}")
        return self._lightrag_service

    @property
    def chinese_nlp_service(self):
        """中文NLP服务（延迟加载）"""
        if self._chinese_nlp_service is None:
            try:
                from app.services.chinese_nlp_service import get_chinese_nlp_service
                self._chinese_nlp_service = get_chinese_nlp_service()
            except Exception as e:
                logger.warning(f"⚠️ 中文NLP服务加载失败: {e}")
        return self._chinese_nlp_service

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行知识分析"""
        self._record_execution()

        if not self.validate_input(input_data):
            return {'error': 'Invalid input'}

        text = input_data['text']
        extract_entities = input_data.get('extract_entities', True)
        extract_relations = input_data.get('extract_relations', True)
        build_graph = input_data.get('build_graph', False)

        logger.info(f"🧠 执行知识分析: text_length={len(text)}")

        result = {
            'entities': [],
            'relations': [],
            'topics': [],
            'knowledge_graph': None
        }

        try:
            # 1. 实体提取
            if extract_entities:
                entities = self._extract_entities(text)
                result['entities'] = entities

            # 2. 关系提取
            if extract_relations:
                relations = self._extract_relations(text, result['entities'])
                result['relations'] = relations

            # 3. 主题分析
            topics = self._analyze_topics(text)
            result['topics'] = topics

            # 4. 构建知识图谱
            if build_graph:
                graph = self._build_knowledge_graph(
                    result['entities'],
                    result['relations']
                )
                result['knowledge_graph'] = graph

            logger.info(
                f"✅ 知识分析完成: "
                f"entities={len(result['entities'])}, "
                f"relations={len(result['relations'])}, "
                f"topics={len(result['topics'])}"
            )

            return result

        except Exception as e:
            logger.error(f"❌ 知识分析失败: {e}", exc_info=True)
            return {'error': str(e)}

    def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """提取实体"""
        entities = []

        # 使用中文NLP服务提取实体
        if self.chinese_nlp_service:
            try:
                nlp_result = self.chinese_nlp_service.analyse_text(text)

                # 从LAC提取实体
                if 'lac' in nlp_result and nlp_result['lac'].get('entities'):
                    for entity in nlp_result['lac']['entities']:
                        entities.append({
                            'text': entity['text'],
                            'type': entity['type'],
                            'source': 'lac'
                        })

            except Exception as e:
                logger.warning(f"⚠️ 中文NLP实体提取失败: {e}")

        return entities

    def _extract_relations(
        self,
        text: str,
        entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """提取关系"""
        relations = []

        # TODO: 实现更复杂的关系提取逻辑
        # 可以使用规则、模式或LLM

        return relations

    def _analyze_topics(self, text: str) -> List[Dict[str, Any]]:
        """主题分析"""
        topics = []

        # 使用中文NLP服务提取关键词作为主题
        if self.chinese_nlp_service:
            try:
                nlp_result = self.chinese_nlp_service.analyse_text(text)

                # 从jieba提取关键词
                if 'jieba' in nlp_result and nlp_result['jieba'].get('keywords'):
                    for kw in nlp_result['jieba']['keywords'][:5]:
                        topics.append({
                            'topic': kw['keyword'],
                            'weight': kw['weight'],
                            'source': 'jieba'
                        })

            except Exception as e:
                logger.warning(f"⚠️ 主题分析失败: {e}")

        return topics

    def _build_knowledge_graph(
        self,
        entities: List[Dict[str, Any]],
        relations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """构建知识图谱"""
        graph = {
            'nodes': entities,
            'edges': relations,
            'metadata': {
                'node_count': len(entities),
                'edge_count': len(relations),
                'created_at': datetime.utcnow().isoformat()
            }
        }

        return graph


# ==================== Search Agent ====================

class SearchAgent(BaseAgent):
    """智能检索Agent"""

    agent_type = "search"
    agent_name = "Intelligent Search Agent"
    agent_version = "1.0.0"
    agent_description = "多源智能检索，包括文档、网络、知识库"

    capabilities = [
        "document_search",    # 文档检索
        "web_search",         # 网络检索
        "memory_search",      # 记忆检索
        "semantic_search",    # 语义检索
        "result_ranking"      # 结果排序
    ]

    input_schema = {
        'required': ['query'],
        'properties': {
            'query': {'type': 'string', 'description': '检索查询'},
            'sources': {'type': 'array', 'description': '检索源列表'},
            'top_k': {'type': 'integer', 'default': 10},
            'project_id': {'type': 'integer'}
        }
    }

    output_schema = {
        'properties': {
            'results': {'type': 'array', 'description': '检索结果'},
            'total_count': {'type': 'integer'},
            'sources_used': {'type': 'array'}
        }
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._rag_engine = None
        self._memory_aggregator = None

    @property
    def rag_engine(self):
        """RAG引擎（延迟加载）"""
        if self._rag_engine is None:
            try:
                from app.core.rag_engine import rag_engine
                self._rag_engine = rag_engine
            except Exception as e:
                logger.warning(f"⚠️ RAG引擎加载失败: {e}")
        return self._rag_engine

    @property
    def memory_aggregator(self):
        """记忆整合器（延迟加载）"""
        if self._memory_aggregator is None:
            try:
                from app.core.memory_aggregator import get_memory_aggregator
                self._memory_aggregator = get_memory_aggregator()
            except Exception as e:
                logger.warning(f"⚠️ 记忆整合器加载失败: {e}")
        return self._memory_aggregator

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行智能检索"""
        self._record_execution()

        if not self.validate_input(input_data):
            return {'error': 'Invalid input'}

        query = input_data['query']
        sources = input_data.get('sources', ['documents', 'memory'])
        top_k = input_data.get('top_k', 10)
        project_id = input_data.get('project_id')

        logger.info(f"🔍 执行智能检索: query='{query[:50]}...', sources={sources}")

        all_results = []
        sources_used = []

        try:
            # 1. 文档检索
            if 'documents' in sources and self.rag_engine:
                doc_results = self._search_documents(query, top_k, project_id)
                all_results.extend(doc_results)
                if doc_results:
                    sources_used.append('documents')

            # 2. 记忆检索
            if 'memory' in sources and self.memory_aggregator:
                memory_results = self._search_memory(query, top_k, project_id)
                all_results.extend(memory_results)
                if memory_results:
                    sources_used.append('memory')

            # 3. 网络检索（如果配置）
            if 'web' in sources:
                web_results = self._search_web(query, top_k)
                all_results.extend(web_results)
                if web_results:
                    sources_used.append('web')

            # 4. 结果排序和去重
            ranked_results = self._rank_and_deduplicate(all_results, top_k)

            logger.info(
                f"✅ 智能检索完成: "
                f"total={len(ranked_results)}, "
                f"sources={sources_used}"
            )

            return {
                'results': ranked_results,
                'total_count': len(ranked_results),
                'sources_used': sources_used,
                'query': query
            }

        except Exception as e:
            logger.error(f"❌ 智能检索失败: {e}", exc_info=True)
            return {'error': str(e)}

    def _search_documents(
        self,
        query: str,
        top_k: int,
        project_id: Optional[int]
    ) -> List[Dict[str, Any]]:
        """检索文档"""
        try:
            result = self.rag_engine.query(
                question=query,
                top_k=top_k,
                return_sources=True
            )

            sources = result.get('sources', [])

            return [
                {
                    'content': s.get('content', ''),
                    'document_name': s.get('document_name', ''),
                    'source': 'documents',
                    'score': s.get('score', 0.5)
                }
                for s in sources
            ]

        except Exception as e:
            logger.warning(f"⚠️ 文档检索失败: {e}")
            return []

    def _search_memory(
        self,
        query: str,
        top_k: int,
        project_id: Optional[int]
    ) -> List[Dict[str, Any]]:
        """检索记忆"""
        try:
            result = self.memory_aggregator.aggregate_memory(
                query=query,
                project_id=project_id,
                memory_config={'search_depth': top_k}
            )

            context = result.get('context', '')

            if context:
                return [{
                    'content': context,
                    'source': 'memory',
                    'score': 0.8
                }]

            return []

        except Exception as e:
            logger.warning(f"⚠️ 记忆检索失败: {e}")
            return []

    def _search_web(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """网络检索"""
        # TODO: 实现网络检索（crawl4ai等）
        return []

    def _rank_and_deduplicate(
        self,
        results: List[Dict[str, Any]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """结果排序和去重"""
        # 按分数排序
        sorted_results = sorted(
            results,
            key=lambda x: x.get('score', 0),
            reverse=True
        )

        # 简单去重（基于内容）
        seen_contents = set()
        unique_results = []

        for result in sorted_results:
            content = result.get('content', '')[:100]  # 取前100字符作为指纹

            if content not in seen_contents:
                seen_contents.add(content)
                unique_results.append(result)

            if len(unique_results) >= top_k:
                break

        return unique_results


# ==================== Summary Agent ====================

class SummaryAgent(BaseAgent):
    """结构化摘要Agent"""

    agent_type = "summary"
    agent_name = "Structured Summary Agent"
    agent_version = "1.0.0"
    agent_description = "生成结构化摘要，提取关键点"

    capabilities = [
        "text_summarization",     # 文本摘要
        "key_points_extraction",  # 关键点提取
        "structured_output",      # 结构化输出
        "multi_level_summary"     # 多层次摘要
    ]

    input_schema = {
        'required': ['text'],
        'properties': {
            'text': {'type': 'string', 'description': '待总结文本'},
            'summary_type': {'type': 'string', 'enum': ['brief', 'detailed', 'structured']},
            'max_length': {'type': 'integer', 'default': 500}
        }
    }

    output_schema = {
        'properties': {
            'summary': {'type': 'string', 'description': '摘要'},
            'key_points': {'type': 'array', 'description': '关键点'},
            'structure': {'type': 'object', 'description': '结构化内容'}
        }
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._claude_client = None

    @property
    def claude_client(self):
        """Claude客户端（延迟加载）"""
        if self._claude_client is None:
            try:
                import os
                from anthropic import Anthropic
                api_key = os.getenv("ANTHROPIC_API_KEY")
                if api_key:
                    self._claude_client = Anthropic(api_key=api_key)
            except Exception as e:
                logger.warning(f"⚠️ Claude客户端加载失败: {e}")
        return self._claude_client

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行摘要生成"""
        self._record_execution()

        if not self.validate_input(input_data):
            return {'error': 'Invalid input'}

        text = input_data['text']
        summary_type = input_data.get('summary_type', 'brief')
        max_length = input_data.get('max_length', 500)

        logger.info(
            f"📝 执行摘要生成: text_length={len(text)}, "
            f"type={summary_type}"
        )

        try:
            if not self.claude_client:
                return {'error': 'Claude client not available'}

            # 构建提示词
            prompt = self._build_summary_prompt(text, summary_type, max_length)

            # 调用Claude API
            response = self.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # 提取结果
            summary_text = response.content[0].text

            # 解析结构化内容
            key_points = self._extract_key_points(summary_text)

            logger.info(f"✅ 摘要生成完成: length={len(summary_text)}")

            return {
                'summary': summary_text,
                'key_points': key_points,
                'original_length': len(text),
                'summary_length': len(summary_text),
                'compression_ratio': len(summary_text) / len(text) if len(text) > 0 else 0
            }

        except Exception as e:
            logger.error(f"❌ 摘要生成失败: {e}", exc_info=True)
            return {'error': str(e)}

    def _build_summary_prompt(
        self,
        text: str,
        summary_type: str,
        max_length: int
    ) -> str:
        """构建摘要提示词"""
        if summary_type == 'brief':
            return f"""请为以下文本生成简要摘要（不超过{max_length}字）：

{text}

摘要："""
        elif summary_type == 'detailed':
            return f"""请为以下文本生成详细摘要（不超过{max_length}字）：

{text}

摘要："""
        else:  # structured
            return f"""请为以下文本生成结构化摘要：

{text}

请按以下格式输出：
1. 核心观点：
2. 关键论据：
3. 结论："""

    def _extract_key_points(self, summary_text: str) -> List[str]:
        """从摘要中提取关键点"""
        key_points = []

        # 简单提取：按行分割，寻找列表项
        lines = summary_text.split('\n')

        for line in lines:
            line = line.strip()
            if line and (line.startswith('-') or line.startswith('•') or
                        line[0].isdigit() and '.' in line[:3]):
                # 去除标记
                point = line.lstrip('-•0123456789. ')
                if point:
                    key_points.append(point)

        return key_points


# ==================== Transcript Agent ====================

class TranscriptAgent(BaseAgent):
    """音视频转录Agent"""

    agent_type = "transcript"
    agent_name = "Audio/Video Transcript Agent"
    agent_version = "1.0.0"
    agent_description = "音视频转文本，支持时间戳和语义分段"

    capabilities = [
        "audio_transcription",    # 音频转录
        "video_transcription",    # 视频转录
        "timestamp_alignment",    # 时间戳对齐
        "semantic_segmentation"   # 语义分段
    ]

    input_schema = {
        'required': ['file_path'],
        'properties': {
            'file_path': {'type': 'string', 'description': '文件路径'},
            'include_timestamps': {'type': 'boolean', 'default': True},
            'segment_by_topic': {'type': 'boolean', 'default': False}
        }
    }

    output_schema = {
        'properties': {
            'transcript': {'type': 'string', 'description': '转录文本'},
            'segments': {'type': 'array', 'description': '分段内容'},
            'metadata': {'type': 'object'}
        }
    }

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行转录"""
        self._record_execution()

        if not self.validate_input(input_data):
            return {'error': 'Invalid input'}

        file_path = input_data['file_path']
        include_timestamps = input_data.get('include_timestamps', True)

        logger.info(f"🎤 执行转录: file={file_path}")

        # TODO: 实现实际的转录功能（Whisper等）
        # 这里提供占位实现

        return {
            'transcript': '转录功能待实现',
            'segments': [],
            'metadata': {
                'file_path': file_path,
                'duration': 0,
                'language': 'zh'
            },
            'note': 'Transcript功能需要集成Whisper或其他转录服务'
        }


# ==================== Analysis Agent ====================

class AnalysisAgent(BaseAgent):
    """深度分析Agent"""

    agent_type = "analysis"
    agent_name = "Deep Analysis Agent"
    agent_version = "1.0.0"
    agent_description = "深度分析文本，提供多维度洞察"

    capabilities = [
        "sentiment_analysis",     # 情感分析
        "trend_analysis",         # 趋势分析
        "comparative_analysis",   # 对比分析
        "critical_analysis"       # 批判性分析
    ]

    input_schema = {
        'required': ['text'],
        'properties': {
            'text': {'type': 'string', 'description': '待分析文本'},
            'analysis_type': {'type': 'string'},
            'context': {'type': 'object'}
        }
    }

    output_schema = {
        'properties': {
            'analysis': {'type': 'string', 'description': '分析结果'},
            'insights': {'type': 'array', 'description': '洞察'},
            'recommendations': {'type': 'array', 'description': '建议'}
        }
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._thinking_engine = None

    @property
    def thinking_engine(self):
        """深度思考引擎（延迟加载）"""
        if self._thinking_engine is None:
            try:
                from app.core.deep_thinking_engine import get_deep_thinking_engine
                self._thinking_engine = get_deep_thinking_engine()
            except Exception as e:
                logger.warning(f"⚠️ 深度思考引擎加载失败: {e}")
        return self._thinking_engine

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行深度分析"""
        self._record_execution()

        if not self.validate_input(input_data):
            return {'error': 'Invalid input'}

        text = input_data['text']
        analysis_type = input_data.get('analysis_type', 'general')

        logger.info(f"🔬 执行深度分析: type={analysis_type}")

        try:
            if not self.thinking_engine:
                return {'error': 'Thinking engine not available'}

            # 使用深度思考引擎进行分析
            prompt = f"""请对以下文本进行{analysis_type}分析：

{text}

请提供：
1. 深度分析
2. 关键洞察
3. 建议"""

            result = self.thinking_engine.think_and_respond(
                prompt=prompt,
                thinking_level='deep'
            )

            logger.info(f"✅ 深度分析完成")

            return {
                'analysis': result['answer'],
                'thinking_process': result.get('thinking_process'),
                'insights': [],  # TODO: 从分析中提取
                'recommendations': []
            }

        except Exception as e:
            logger.error(f"❌ 深度分析失败: {e}", exc_info=True)
            return {'error': str(e)}
