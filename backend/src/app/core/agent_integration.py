"""
Agent集成模块 - 将6个Agent注册到Hermes统一编排引擎

将6个专业Agent作为处理阶段注册到Hermes：
1. IngestionAgent - 数据采集（18个服务：文档转换、音频转录、OCR等）
2. ChunkingAgent - 智能分块（4个服务：语义分块、文档分块等）
3. VectorizationAgent - 向量化（7个服务：FlagEmbedding、OpenAI等）
4. KnowledgeAgent - 知识图谱（实体识别、关系提取、图谱构建）
5. SynthesisAgent - 综合合成（记忆管理、上下文准备）
6. ReportAgent - 报告生成（报告生成、引用验证）

核心设计：
- 每个Agent作为ProcessingStage的handler
- 输入/输出都是DataPacket格式
- 自动触发下一阶段
- 人工审核关键节点（knowledge_graph、report_generation）
- 项目隔离
- 反幻觉验证
"""

from typing import Dict, Any, List, Tuple, TYPE_CHECKING
from sqlalchemy.orm import Session
import logging
from datetime import datetime
import uuid

if TYPE_CHECKING:
    from app.core.hermes import Hermes

from app.core.hermes import DataPacket
from app.core.data_flow_orchestrator import DataFlowOrchestrator

logger = logging.getLogger(__name__)


class AgentIntegration:
    """
    Agent集成器

    职责：
    1. 初始化6个Agent
    2. 将Agent注册为Hermes的处理阶段
    3. 提供统一的入口方法
    """

    def __init__(self, hermes: "Hermes"):
        self.hermes = hermes

        # 懒加载6个Agent
        self._ingestion_agent = None
        self._chunking_agent = None
        self._vectorization_agent = None
        self._knowledge_agent = None
        self._synthesis_agent = None
        self._report_agent = None

        # 注册所有Agent作为处理阶段
        self._register_all_agents()

        logger.info("✅ AgentIntegration初始化完成，6个Agent已注册到DataFlowOrchestrator")

    # ==================== Agent懒加载 ====================

    def _get_ingestion_agent(self):
        """加载IngestionAgent"""
        if self._ingestion_agent is None:
            from app.agents.ingestion_agent import get_ingestion_agent
            self._ingestion_agent = get_ingestion_agent()
        return self._ingestion_agent

    def _get_chunking_agent(self):
        """加载ChunkingAgent"""
        if self._chunking_agent is None:
            from app.agents.chunking_agent import get_chunking_agent
            self._chunking_agent = get_chunking_agent()
        return self._chunking_agent

    def _get_vectorization_agent(self):
        """加载VectorizationAgent"""
        if self._vectorization_agent is None:
            from app.agents.vectorization_agent import VectorizationAgent
            self._vectorization_agent = VectorizationAgent()
        return self._vectorization_agent

    def _get_knowledge_agent(self):
        """加载KnowledgeAgent"""
        if self._knowledge_agent is None:
            from app.agents.knowledge_agent import KnowledgeAgent
            self._knowledge_agent = KnowledgeAgent()
        return self._knowledge_agent

    def _get_synthesis_agent(self):
        """加载SynthesisAgent"""
        if self._synthesis_agent is None:
            from app.agents.synthesis_agent import SynthesisAgent
            self._synthesis_agent = SynthesisAgent()
        return self._synthesis_agent

    def _get_report_agent(self):
        """加载ReportAgent"""
        if self._report_agent is None:
            from app.agents.report_agent import ReportAgent
            self._report_agent = ReportAgent()
        return self._report_agent

    # ==================== 注册Agent为处理阶段 ====================

    def _register_all_agents(self):
        """将所有Agent注册为DataFlowOrchestrator的处理阶段"""

        # 阶段1: 数据采集（替换原有的document_upload和document_extraction）
        self.hermes.register_stage(
            name="agent_ingestion",
            handler=self._handler_ingestion,
            validators=[
                self._validate_ingestion_result
            ],
            next_stages=["agent_chunking"],
            require_approval=False,
            project_isolated=True
        )

        # 阶段2: 智能分块
        self.hermes.register_stage(
            name="agent_chunking",
            handler=self._handler_chunking,
            validators=[
                self._validate_chunks_quality
            ],
            next_stages=["agent_vectorization"],
            require_approval=False,
            project_isolated=True
        )

        # 阶段3: 向量化
        self.hermes.register_stage(
            name="agent_vectorization",
            handler=self._handler_vectorization,
            validators=[
                self._validate_vectorization_quality
            ],
            next_stages=["agent_knowledge_graph"],
            require_approval=False,
            project_isolated=True
        )

        # 阶段4: 知识图谱（需要人工审核）
        self.hermes.register_stage(
            name="agent_knowledge_graph",
            handler=self._handler_knowledge_graph,
            validators=[
                self._validate_knowledge_graph,
                self._validate_no_hallucination_kg
            ],
            next_stages=["agent_synthesis"],
            require_approval=True,  # 需要审核
            project_isolated=True
        )

        # 阶段5: 综合合成
        self.hermes.register_stage(
            name="agent_synthesis",
            handler=self._handler_synthesis,
            validators=[
                self._validate_synthesis_quality
            ],
            next_stages=["agent_report"],
            require_approval=False,
            project_isolated=True
        )

        # 阶段6: 报告生成（需要人工审核）
        self.hermes.register_stage(
            name="agent_report",
            handler=self._handler_report,
            validators=[
                self._validate_report_quality,
                self._validate_report_citations
            ],
            next_stages=["display_ready"],
            require_approval=True,  # 需要审核
            project_isolated=True
        )

        logger.info("📋 已注册6个Agent作为处理阶段")

    # ==================== Handler实现（调用Agent） ====================

    async def _handler_ingestion(
        self,
        data: Dict[str, Any],
        project_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """
        阶段1: 数据采集

        输入data应包含：
        - file_path: 文件路径
        - document_id: 文档ID

        输出：
        - raw_content: 提取的原始文本
        - file_type: 文件类型
        - metrics: 量化指标
        """
        agent = self._get_ingestion_agent()

        file_path = data.get("file_path")
        if not file_path:
            raise ValueError("缺少file_path")

        logger.info(f"🔧 Agent 1 (IngestionAgent): 采集文件 {file_path}")

        # 调用IngestionAgent
        result = agent.ingest_file(file_path)

        return {
            "raw_content": result.raw_content,
            "file_type": result.file_type.value,
            "metrics": result.metrics,
            "metadata": result.metadata,
            "document_id": data.get("document_id"),
            "ingestion_success": True
        }

    async def _handler_chunking(
        self,
        data: Dict[str, Any],
        project_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """
        阶段2: 智能分块

        输入data应包含：
        - raw_content: 原始文本（来自阶段1）
        - file_type: 文件类型
        - document_id: 文档ID

        输出：
        - chunks: 分块列表
        - chunk_count: 分块数量
        """
        agent = self._get_chunking_agent()

        raw_content = data.get("raw_content")
        file_type = data.get("file_type", "text")
        document_id = data.get("document_id")

        if not raw_content:
            raise ValueError("缺少raw_content")

        logger.info(f"🔧 Agent 2 (ChunkingAgent): 分块文档 {document_id}")

        # 调用ChunkingAgent
        result = agent.chunk_text(
            text=raw_content,
            source_file=data.get("file_path", f"doc_{document_id}"),
            file_type=file_type,
            language=data.get("language", "zh"),
            metadata=data.get("metadata", {})
        )

        # 转换为字典格式
        chunks_dict = [chunk.to_dict() for chunk in result.chunks]

        return {
            "chunks": chunks_dict,
            "chunk_count": result.total_chunks,
            "strategy_used": result.strategy_used,
            "avg_chunk_size": result.avg_chunk_size,
            "chunking_success": True
        }

    async def _handler_vectorization(
        self,
        data: Dict[str, Any],
        project_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """
        阶段3: 向量化

        输入data应包含：
        - chunks: 分块列表（来自阶段2）
        - document_id: 文档ID

        输出：
        - vectorized_count: 向量化成功数量
        - embedding_model: 使用的模型
        - embedding_dim: 向量维度
        """
        agent = self._get_vectorization_agent()

        chunks = data.get("chunks", [])
        document_id = data.get("document_id")

        if not chunks:
            raise ValueError("缺少chunks")

        logger.info(f"🔧 Agent 3 (VectorizationAgent): 向量化 {len(chunks)} 个chunks")

        # 调用VectorizationAgent
        result = agent.vectorize_chunks(
            chunks=chunks,
            store_to_db=True,
            document_id=document_id,
            project_id=project_id,
            db_session=db
        )

        return {
            "vectorized_count": result.success_count,
            "failed_count": result.failed_count,
            "embedding_model": result.embedding_model,
            "embedding_dim": result.embedding_dim,
            "stored_to_db": result.stored_to_db,
            "vectorization_success": True
        }

    async def _handler_knowledge_graph(
        self,
        data: Dict[str, Any],
        project_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """
        阶段4: 知识图谱构建

        输入data应包含：
        - project_id: 项目ID

        输出：
        - entity_count: 实体数量
        - relation_count: 关系数量
        - graph_stats: 图谱统计信息
        """
        agent = self._get_knowledge_agent()

        logger.info(f"🔧 Agent 4 (KnowledgeAgent): 构建知识图谱 (项目 {project_id})")

        # 调用KnowledgeAgent
        result = agent.build_knowledge_graph(
            project_id=project_id,
            db_session=db
        )

        return {
            "entity_count": result.get("entity_count", 0),
            "relation_count": result.get("relation_count", 0),
            "graph_stats": result.get("stats", {}),
            "knowledge_graph_success": True
        }

    async def _handler_synthesis(
        self,
        data: Dict[str, Any],
        project_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """
        阶段5: 综合合成

        输入data应包含：
        - project_id: 项目ID

        输出：
        - memory_count: 记忆片段数量
        - citation_count: 引用数量
        - context_summary: 上下文摘要
        """
        agent = self._get_synthesis_agent()

        logger.info(f"🔧 Agent 5 (SynthesisAgent): 综合合成 (项目 {project_id})")

        # 调用SynthesisAgent
        result = agent.prepare_synthesis_context(
            project_id=project_id,
            query="综合分析项目所有内容",
            db_session=db,
            include_documents=True,
            include_conversation=True,
            include_citations=True
        )

        return {
            "memory_count": len(result.memory_fragments),
            "citation_count": len(result.citations),
            "context_summary": result.context_summary,
            "synthesis_success": True
        }

    async def _handler_report(
        self,
        data: Dict[str, Any],
        project_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """
        阶段6: 报告生成

        输入data应包含：
        - project_id: 项目ID
        - report_level: 报告等级（可选）

        输出：
        - report_title: 报告标题
        - section_count: 章节数量
        - validation_passed: 是否通过验证
        """
        from app.agents.report_agent import ReportLevel, ReportFormat

        agent = self._get_report_agent()

        report_level_str = data.get("report_level", "dynamic")
        report_level = ReportLevel(report_level_str)

        logger.info(f"🔧 Agent 6 (ReportAgent): 生成报告 (项目 {project_id}, 等级 {report_level.value})")

        # 调用ReportAgent
        result = agent.generate_report(
            project_id=project_id,
            db_session=db,
            report_level=report_level,
            export_formats=[ReportFormat.MARKDOWN, ReportFormat.JSON]
        )

        return {
            "report_title": result.report_title,
            "section_count": len(result.sections),
            "validation_passed": result.metadata.validation_passed,
            "exports": list(result.export_formats.keys()),
            "report_success": result.success,
            "generated_text": result.export_formats.get(ReportFormat.MARKDOWN, "")
        }

    # ==================== Validator实现 ====================

    def _validate_ingestion_result(
        self,
        data: Dict[str, Any],
        project_id: int,
        db: Session
    ) -> Tuple[bool, List[str]]:
        """验证数据采集结果"""
        raw_content = data.get("raw_content", "")

        if not raw_content:
            return False, ["采集结果为空"]

        if len(raw_content) < 10:
            return False, ["采集文本过短（<10字符）"]

        return True, []

    def _validate_chunks_quality(
        self,
        data: Dict[str, Any],
        project_id: int,
        db: Session
    ) -> Tuple[bool, List[str]]:
        """验证分块质量"""
        chunks = data.get("chunks", [])

        if not chunks:
            return False, ["未生成任何chunks"]

        if len(chunks) < 1:
            return False, ["chunk数量过少"]

        # 检查chunk内容
        empty_chunks = [i for i, c in enumerate(chunks) if not c.get("text")]
        if empty_chunks:
            return False, [f"存在空chunk: {empty_chunks}"]

        return True, []

    def _validate_vectorization_quality(
        self,
        data: Dict[str, Any],
        project_id: int,
        db: Session
    ) -> Tuple[bool, List[str]]:
        """验证向量化质量"""
        vectorized_count = data.get("vectorized_count", 0)
        chunk_count = data.get("chunk_count", 0)

        if vectorized_count == 0:
            return False, ["未向量化任何chunk"]

        # 检查成功率
        if chunk_count > 0:
            success_rate = vectorized_count / chunk_count
            if success_rate < 0.8:
                return False, [f"向量化成功率过低: {success_rate:.1%}"]

        return True, []

    def _validate_knowledge_graph(
        self,
        data: Dict[str, Any],
        project_id: int,
        db: Session
    ) -> Tuple[bool, List[str]]:
        """验证知识图谱质量"""
        entity_count = data.get("entity_count", 0)

        if entity_count < 3:
            return False, ["知识图谱实体过少（<3个）"]

        return True, []

    def _validate_no_hallucination_kg(
        self,
        data: Dict[str, Any],
        project_id: int,
        db: Session
    ) -> Tuple[bool, List[str]]:
        """反幻觉检测 - 知识图谱"""
        # TODO: 实现反幻觉检测逻辑
        # 检查实体是否都来自原始文档
        return True, []

    def _validate_synthesis_quality(
        self,
        data: Dict[str, Any],
        project_id: int,
        db: Session
    ) -> Tuple[bool, List[str]]:
        """验证综合合成质量"""
        memory_count = data.get("memory_count", 0)

        if memory_count == 0:
            return False, ["未生成任何记忆片段"]

        return True, []

    def _validate_report_quality(
        self,
        data: Dict[str, Any],
        project_id: int,
        db: Session
    ) -> Tuple[bool, List[str]]:
        """验证报告质量"""
        section_count = data.get("section_count", 0)

        if section_count == 0:
            return False, ["报告无章节"]

        return True, []

    def _validate_report_citations(
        self,
        data: Dict[str, Any],
        project_id: int,
        db: Session
    ) -> Tuple[bool, List[str]]:
        """检查报告引用"""
        generated_text = data.get("generated_text", "")

        if not generated_text:
            return True, []  # 如果没有文本，跳过检查

        # 简单检查：是否有引用标记
        import re
        citations = re.findall(r'（来源：[^）]+）|【来源：[^】]+】', generated_text)

        if len(citations) == 0:
            return False, ["报告缺少引用来源"]

        return True, []

    # ==================== 统一入口方法 ====================

    async def process_document(
        self,
        project_id: int,
        file_path: str,
        document_id: int,
        db: Session
    ) -> DataPacket:
        """
        处理单个文档的完整流程

        Args:
            project_id: 项目ID
            file_path: 文件路径
            document_id: 文档ID
            db: 数据库会话

        Returns:
            最终的DataPacket
        """
        # 创建初始数据包
        packet = DataPacket(
            packet_id=f"doc_{document_id}_{uuid.uuid4().hex[:8]}",
            project_id=project_id,
            stage_name="agent_ingestion",
            data={
                "file_path": file_path,
                "document_id": document_id
            },
            metadata={
                "started_at": datetime.now().isoformat()
            }
        )

        # 交给orchestrator处理
        result_packet = await self.hermes.process_packet(packet, db)

        return result_packet


# ==================== 全局实例 ====================

_agent_integration: AgentIntegration = None


def get_agent_integration(orchestrator: DataFlowOrchestrator = None) -> AgentIntegration:
    """获取AgentIntegration单例"""
    global _agent_integration

    if _agent_integration is None:
        if orchestrator is None:
            from app.core.data_flow_orchestrator import data_flow_orchestrator
            orchestrator = data_flow_orchestrator

        _agent_integration = AgentIntegration(orchestrator)

    return _agent_integration
