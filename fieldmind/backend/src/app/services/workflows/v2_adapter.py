"""
WorkflowV2Adapter - 统一编排系统适配器

将6-Agent v2架构适配到WorkflowBase系统，实现两套编排系统的互操作性
"""
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class V2AgentResult:
    """v2 Agent执行结果（统一格式）"""
    success: bool
    output_data: Dict[str, Any]
    errors: list
    warnings: list
    agent_type: str
    execution_time: float = 0.0


class WorkflowV2Adapter:
    """
    v2 Agent适配器

    让WorkflowBase能够调用6-Agent v2架构中的Agents
    """

    def __init__(self):
        """初始化适配器，懒加载所有v2 Agents"""
        self._ingestion_agent = None
        self._chunking_agent = None
        self._vectorization_agent = None
        self._knowledge_agent = None
        self._synthesis_agent = None
        self._report_agent = None

        # 映射：agent_type字符串 -> v2 Agent实例获取方法
        self._agent_getters = {
            'ingestion': self._get_ingestion_agent,
            'chunking': self._get_chunking_agent,
            'vectorization': self._get_vectorization_agent,
            'knowledge': self._get_knowledge_agent,
            'synthesis': self._get_synthesis_agent,
            'report': self._get_report_agent
        }

    # ==================== 懒加载v2 Agents ====================

    def _get_ingestion_agent(self):
        """懒加载IngestionAgent"""
        if self._ingestion_agent is None:
            from app.agents.v2.ingestion_agent import IngestionAgent
            self._ingestion_agent = IngestionAgent()
            logger.info("✅ IngestionAgent已加载")
        return self._ingestion_agent

    def _get_chunking_agent(self):
        """懒加载ChunkingAgent"""
        if self._chunking_agent is None:
            from app.agents.v2.chunking_agent import ChunkingAgent
            self._chunking_agent = ChunkingAgent()
            logger.info("✅ ChunkingAgent已加载")
        return self._chunking_agent

    def _get_vectorization_agent(self):
        """懒加载VectorizationAgent"""
        if self._vectorization_agent is None:
            from app.agents.v2.vectorization_agent import VectorizationAgent
            self._vectorization_agent = VectorizationAgent()
            logger.info("✅ VectorizationAgent已加载")
        return self._vectorization_agent

    def _get_knowledge_agent(self):
        """懒加载KnowledgeAgent"""
        if self._knowledge_agent is None:
            from app.agents.v2.knowledge_agent import KnowledgeAgent
            self._knowledge_agent = KnowledgeAgent()
            logger.info("✅ KnowledgeAgent已加载")
        return self._knowledge_agent

    def _get_synthesis_agent(self):
        """懒加载SynthesisAgent"""
        if self._synthesis_agent is None:
            from app.agents.v2.synthesis_agent import SynthesisAgent
            self._synthesis_agent = SynthesisAgent()
            logger.info("✅ SynthesisAgent已加载")
        return self._synthesis_agent

    def _get_report_agent(self):
        """懒加载ReportAgent"""
        if self._report_agent is None:
            from app.agents.v2.report_agent import ReportAgent
            self._report_agent = ReportAgent()
            logger.info("✅ ReportAgent已加载")
        return self._report_agent

    # ==================== 适配接口 ====================

    def supports_agent_type(self, agent_type: str) -> bool:
        """检查是否支持该agent_type"""
        return agent_type in self._agent_getters

    def execute_v2_agent(
        self,
        agent_type: str,
        input_data: Dict[str, Any],
        db_session,
        metadata: Optional[Dict[str, Any]] = None
    ) -> V2AgentResult:
        """
        执行v2 Agent

        Args:
            agent_type: Agent类型（ingestion/chunking/vectorization/knowledge/synthesis/report）
            input_data: 输入数据
            db_session: 数据库会话
            metadata: 元数据

        Returns:
            V2AgentResult对象
        """
        import time

        if agent_type not in self._agent_getters:
            return V2AgentResult(
                success=False,
                output_data={},
                errors=[f"未知的v2 Agent类型: {agent_type}"],
                warnings=[],
                agent_type=agent_type
            )

        start_time = time.time()

        try:
            # 获取Agent实例
            agent = self._agent_getters[agent_type]()

            # 根据agent_type调用相应方法
            if agent_type == 'ingestion':
                output = self._execute_ingestion(agent, input_data, db_session)
            elif agent_type == 'chunking':
                output = self._execute_chunking(agent, input_data, db_session)
            elif agent_type == 'vectorization':
                output = self._execute_vectorization(agent, input_data, db_session)
            elif agent_type == 'knowledge':
                output = self._execute_knowledge(agent, input_data, db_session)
            elif agent_type == 'synthesis':
                output = self._execute_synthesis(agent, input_data, db_session, metadata)
            elif agent_type == 'report':
                output = self._execute_report(agent, input_data, db_session, metadata)
            else:
                raise ValueError(f"未实现的agent_type: {agent_type}")

            elapsed_time = time.time() - start_time

            return V2AgentResult(
                success=True,
                output_data=output,
                errors=[],
                warnings=[],
                agent_type=agent_type,
                execution_time=elapsed_time
            )

        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"❌ v2 Agent {agent_type} 执行失败: {e}", exc_info=True)

            return V2AgentResult(
                success=False,
                output_data={},
                errors=[str(e)],
                warnings=[],
                agent_type=agent_type,
                execution_time=elapsed_time
            )

    # ==================== 各Agent执行逻辑 ====================

    def _execute_ingestion(self, agent, input_data: Dict[str, Any], db_session) -> Dict[str, Any]:
        """执行IngestionAgent"""
        project_id = input_data.get('project_id')

        if not project_id:
            raise ValueError("IngestionAgent需要project_id参数")

        # 从数据库加载文档
        from app.models.project import ProjectDocument

        docs = db_session.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id
        ).all()

        logger.info(f"📄 IngestionAgent加载了{len(docs)}个文档")

        return {
            'document_count': len(docs),
            'documents': docs,
            'project_id': project_id
        }

    def _execute_chunking(self, agent, input_data: Dict[str, Any], db_session) -> Dict[str, Any]:
        """执行ChunkingAgent"""
        documents = input_data.get('documents', [])
        project_id = input_data.get('project_id')

        if not documents:
            raise ValueError("ChunkingAgent输入没有文档，无法进行分块")

        # 使用ChunkingAgent处理文档
        from concurrent.futures import ThreadPoolExecutor, as_completed

        total_chunks = 0
        all_chunk_ids = []
        failed_docs = []

        max_workers = 5
        logger.info(f"🚀 ChunkingAgent并行处理 {len(documents)} 个文档（最大并发={max_workers}）")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_doc = {
                executor.submit(self._process_document_chunk, agent, doc, project_id, db_session): doc
                for doc in documents
            }

            for future in as_completed(future_to_doc):
                doc = future_to_doc[future]
                try:
                    result = future.result()
                    if result.get('success'):
                        total_chunks += result['chunk_count']
                        all_chunk_ids.extend(result['chunk_ids'])
                    else:
                        failed_docs.append({
                            'document_id': doc.id,
                            'error': result.get('error', 'Unknown error')
                        })
                except Exception as e:
                    failed_docs.append({
                        'document_id': doc.id,
                        'error': str(e)
                    })

        logger.info(f"✂️ ChunkingAgent完成：{total_chunks}个chunks")

        return {
            'chunk_count': total_chunks,
            'document_count': len(documents),
            'stored_chunk_ids': all_chunk_ids,
            'failed_documents': failed_docs
        }

    def _process_document_chunk(self, agent, doc, project_id, db_session) -> Dict[str, Any]:
        """处理单个文档的分块"""
        try:
            # 调用ChunkingAgent的chunk_text方法
            result = agent.chunk_text(
                text=doc.content,
                source_file=doc.file_path or f"doc_{doc.id}",
                file_type=doc.doc_type or 'text',
                language='zh',
                metadata={'title': doc.title, 'document_id': doc.id},
                project_id=project_id
            )

            # result是ChunkingResult对象，包含chunks列表
            chunks = result.chunks

            # 存储到数据库
            from app.models.pipeline_state import DocumentChunk

            chunk_ids = []
            for chunk_data in chunks:
                db_chunk = DocumentChunk(
                    project_id=project_id,
                    document_id=doc.id,
                    chunk_index=chunk_data['chunk_index'],
                    chunk_text=chunk_data['text'],
                    token_count=chunk_data.get('token_count', 0),
                    extra_metadata=chunk_data.get('metadata', {})
                )
                db_session.add(db_chunk)
                db_session.flush()
                chunk_ids.append(db_chunk.id)

            db_session.commit()

            return {
                'success': True,
                'chunk_count': len(chunks),
                'chunk_ids': chunk_ids
            }

        except Exception as e:
            logger.error(f"❌ 文档 {doc.id} 分块失败: {e}")
            db_session.rollback()
            return {
                'success': False,
                'error': str(e)
            }

    def _execute_vectorization(self, agent, input_data: Dict[str, Any], db_session) -> Dict[str, Any]:
        """执行VectorizationAgent"""
        stored_chunk_ids = input_data.get('stored_chunk_ids', [])
        project_id = input_data.get('project_id')

        if not stored_chunk_ids:
            raise ValueError("VectorizationAgent输入没有chunk_ids，无法进行向量化")

        # 从数据库读取chunks
        from app.models.pipeline_state import DocumentChunk

        db_chunks = db_session.query(DocumentChunk).filter(
            DocumentChunk.id.in_(stored_chunk_ids)
        ).all()

        # 转换为字典格式
        chunk_dicts = [
            {
                'chunk_id': chunk.id,
                'text': chunk.chunk_text,
                'metadata': chunk.extra_metadata or {}
            }
            for chunk in db_chunks
        ]

        # 调用VectorizationAgent
        result = agent.vectorize_chunks(
            chunks=chunk_dicts,
            store_to_db=True,
            project_id=project_id,
            db_session=db_session
        )

        logger.info(f"📊 VectorizationAgent完成了{result.success_count}个chunk的向量化")

        return {
            'vectorized_count': result.success_count,
            'failed_count': result.failed_count,
            'embedding_model': result.embedding_model,
            'embedding_dim': result.embedding_dim
        }

    def _execute_knowledge(self, agent, input_data: Dict[str, Any], db_session) -> Dict[str, Any]:
        """执行KnowledgeAgent"""
        project_id = input_data.get('project_id')

        if not project_id:
            raise ValueError("KnowledgeAgent需要project_id参数")

        # 构建知识图谱
        result = agent.build_knowledge_graph(
            project_id=project_id,
            db_session=db_session
        )

        logger.info(f"🕸️ KnowledgeAgent构建了知识图谱（实体={result.get('entity_count', 0)}个）")

        return result

    def _execute_synthesis(
        self,
        agent,
        input_data: Dict[str, Any],
        db_session,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """执行SynthesisAgent"""
        project_id = input_data.get('project_id')
        query = input_data.get('query', '生成项目综合报告')
        include_business_analysis = input_data.get('include_business_analysis', True)

        if not project_id:
            raise ValueError("SynthesisAgent需要project_id参数")

        # 调用generate_synthesis_insights
        result = agent.generate_synthesis_insights(
            project_id=str(project_id),
            db_session=db_session,
            query=query,
            include_business_analysis=include_business_analysis
        )

        logger.info(f"🔗 SynthesisAgent综合完成（洞察={len(result['key_insights'])}个）")

        return {
            'synthesis_result_id': result['synthesis_result_id'],
            'key_insights_count': len(result['key_insights']),
            'recommendations_count': len(result['recommendations']),
            'confidence_score': result['confidence_score'],
            'context_summary': result['context_summary']
        }

    def _execute_report(
        self,
        agent,
        input_data: Dict[str, Any],
        db_session,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """执行ReportAgent"""
        project_id = input_data.get('project_id')
        synthesis_result_id = input_data.get('synthesis_result_id')
        report_level = input_data.get('report_level', 'dynamic')

        if not project_id:
            raise ValueError("ReportAgent需要project_id参数")

        # 如果有synthesis_result_id，使用三层报告生成
        if synthesis_result_id:
            result = agent.generate_three_layer_report(
                project_id=str(project_id),
                db_session=db_session,
                synthesis_result_id=synthesis_result_id,
                target_words_per_layer=10000,
                include_citations=True
            )

            logger.info(f"📝 ReportAgent生成三层报告（总字数={result['total_words']}）")

            return {
                'success': result['success'],
                'report_type': 'three_layer',
                'layer_1_id': result['layer_1_id'],
                'layer_2_id': result['layer_2_id'],
                'layer_3_id': result['layer_3_id'],
                'total_words': result['total_words']
            }

        # 否则使用传统报告生成
        from app.agents.v2.report_agent import ReportLevel, ReportFormat

        level = ReportLevel(report_level) if report_level else ReportLevel.DYNAMIC
        result = agent.generate_report(
            project_id=project_id,
            db_session=db_session,
            report_level=level,
            export_formats=[ReportFormat.MARKDOWN, ReportFormat.JSON]
        )

        logger.info(f"📝 ReportAgent生成传统报告（成功={'✅' if result.success else '❌'}）")

        return {
            'success': result.success,
            'report_title': result.report_title,
            'section_count': len(result.sections),
            'report_type': 'traditional'
        }


# ==================== 全局适配器实例 ====================

_global_adapter = None


def get_v2_adapter() -> WorkflowV2Adapter:
    """获取全局v2适配器实例（单例模式）"""
    global _global_adapter
    if _global_adapter is None:
        _global_adapter = WorkflowV2Adapter()
    return _global_adapter
