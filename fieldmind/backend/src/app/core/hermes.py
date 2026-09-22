"""
Hermes - 统一编排引擎（系统大脑）
整合了DataFlowOrchestrator、WorkflowEngine、WorkflowOrchestrator三个系统
负责：数据流编排、Agent协调、任务调度、质量控制、人工审核
"""

from typing import Dict, List, Any, Optional, Callable, Union
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import logging
from sqlalchemy.orm import Session
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


# ==================== 数据结构定义 ====================

class DataQualityLevel(str, Enum):
    """数据质量等级"""
    RAW = "raw"  # 原始数据
    VERIFIED = "verified"  # 已验证
    HALLUCINATED = "hallucinated"  # 检测到幻觉
    APPROVED = "approved"  # 人工审核通过


class StageStatus(str, Enum):
    """处理阶段状态"""
    PENDING = "pending"
    RUNNING = "running"
    REVIEW = "review"  # 等待人工审核
    APPROVED = "approved"  # 审核通过
    REJECTED = "rejected"  # 审核拒绝
    COMPLETED = "completed"
    FAILED = "failed"


class WorkflowType(str, Enum):
    """工作流类型"""
    DOCUMENT = "document"
    AUDIO = "audio"
    VIDEO = "video"
    CRAWLER = "crawler"
    RAG = "rag"
    REPORT = "report"
    KNOWLEDGE_GRAPH = "knowledge_graph"
    AGENT_PIPELINE = "agent_pipeline"  # 6-Agent管道


@dataclass
class DataPacket:
    """数据包 - 在各阶段间流转的标准数据单元"""
    packet_id: str
    project_id: int
    stage_name: str
    data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    quality_level: DataQualityLevel = DataQualityLevel.RAW
    validation_errors: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ProcessingStage:
    """处理阶段定义"""
    name: str
    handler: Callable  # async (data: Dict, project_id: int, db: Session) -> Dict
    validators: List[Callable] = field(default_factory=list)  # (data, project_id, db) -> (bool, List[str])
    next_stages: List[str] = field(default_factory=list)
    require_approval: bool = False  # 是否需要人工审核
    project_isolated: bool = True  # 是否项目隔离
    timeout: Optional[int] = None  # 超时时间（秒）
    retry_on_failure: bool = False


@dataclass
class StageExecution:
    """阶段执行记录"""
    execution_id: str
    packet_id: str
    stage_name: str
    status: StageStatus
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error: Optional[str] = None
    result_data: Optional[Dict] = None


# ==================== Hermes 核心类 ====================

class Hermes:
    """
    统一编排引擎 - 系统大脑

    职责：
    1. 数据流编排 - 管理ProcessingStage和DataPacket流转
    2. Agent协调 - 协调6个Agent（Ingestion、Chunking、Vectorization、Knowledge、Synthesis、Report）
    3. 任务调度 - 同步/异步任务执行
    4. 质量控制 - 数据验证、反幻觉检测
    5. 人工审核 - 关键节点的人工介入
    6. 业务工作流 - 文档、音频、爬虫、RAG等预定义流程
    """

    def __init__(self):
        # 核心存储
        self.stages: Dict[str, ProcessingStage] = {}  # 已注册的处理阶段
        self.packets: Dict[str, DataPacket] = {}  # 数据包缓存
        self.executions: Dict[str, StageExecution] = {}  # 执行记录

        # 任务执行器
        self.executor = ThreadPoolExecutor(max_workers=10)

        # Agent集成标志
        self._agent_integration_loaded = False

        # WebSocket管理器（用于实时通知）
        self.ws_manager = None

        # 学习引擎（自学习能力）
        self.learning_engine = None
        try:
            from app.services.hermes_learning_engine import get_learning_engine
            self.learning_engine = get_learning_engine()
            logger.info("✅ Hermes已集成自学习引擎")
        except Exception as e:
            logger.warning(f"⚠️ Hermes学习引擎初始化失败: {e}")

        logger.info("🧠 Hermes统一编排引擎已初始化")


    # ==================== 阶段管理 ====================

    def register_stage(
        self,
        name: str,
        handler: Callable,
        validators: List[Callable] = None,
        next_stages: List[str] = None,
        require_approval: bool = False,
        project_isolated: bool = True,
        timeout: Optional[int] = None,
        retry_on_failure: bool = False
    ):
        """
        注册处理阶段

        Args:
            name: 阶段名称（唯一标识）
            handler: 处理函数 async (data: Dict, project_id: int, db: Session) -> Dict
            validators: 验证器列表 [(data, project_id, db) -> (bool, List[str])]
            next_stages: 成功后自动触发的下一阶段列表
            require_approval: 是否需要人工审核
            project_isolated: 是否项目隔离
            timeout: 超时时间（秒）
            retry_on_failure: 失败时是否重试
        """
        stage = ProcessingStage(
            name=name,
            handler=handler,
            validators=validators or [],
            next_stages=next_stages or [],
            require_approval=require_approval,
            project_isolated=project_isolated,
            timeout=timeout,
            retry_on_failure=retry_on_failure
        )
        self.stages[name] = stage
        logger.info(f"✅ 注册阶段: {name} (审核={require_approval}, 下一阶段={next_stages})")


    def get_stage(self, name: str) -> Optional[ProcessingStage]:
        """获取处理阶段"""
        return self.stages.get(name)


    def list_stages(self) -> List[str]:
        """列出所有已注册的阶段"""
        return list(self.stages.keys())


    # ==================== 数据包处理 ====================

    async def create_packet(
        self,
        stage_name: str,
        data: Dict[str, Any],
        project_id: int,
        metadata: Dict[str, Any] = None
    ) -> DataPacket:
        """
        创建数据包并开始处理

        Args:
            stage_name: 起始阶段名称
            data: 输入数据
            project_id: 项目ID
            metadata: 元数据

        Returns:
            DataPacket: 创建的数据包
        """
        packet_id = f"pkt_{uuid.uuid4().hex[:12]}"
        packet = DataPacket(
            packet_id=packet_id,
            project_id=project_id,
            stage_name=stage_name,
            data=data,
            metadata=metadata or {},
            quality_level=DataQualityLevel.RAW
        )
        self.packets[packet_id] = packet

        logger.info(f"📦 创建数据包: {packet_id} (项目={project_id}, 阶段={stage_name})")

        # 立即开始处理
        from app.core.database import get_db
        db = next(get_db())
        try:
            await self.process_packet(packet_id, db)
        finally:
            db.close()

        return packet


    async def process_packet(self, packet_id: str, db: Session):
        """
        处理数据包 - 执行当前阶段并自动触发下一阶段

        Args:
            packet_id: 数据包ID
            db: 数据库会话
        """
        packet = self.packets.get(packet_id)
        if not packet:
            logger.error(f"❌ 数据包不存在: {packet_id}")
            return

        stage = self.stages.get(packet.stage_name)
        if not stage:
            logger.error(f"❌ 阶段不存在: {packet.stage_name}")
            return

        execution_id = f"exec_{uuid.uuid4().hex[:12]}"
        execution = StageExecution(
            execution_id=execution_id,
            packet_id=packet_id,
            stage_name=packet.stage_name,
            status=StageStatus.RUNNING,
            start_time=datetime.utcnow()
        )
        self.executions[execution_id] = execution

        logger.info(f"▶️  处理数据包 {packet_id} 在阶段 {packet.stage_name}")

        try:
            # 1. 执行handler
            result_data = await stage.handler(packet.data, packet.project_id, db)
            packet.data.update(result_data)
            packet.updated_at = datetime.utcnow()

            # 2. 运行验证器
            validation_passed = True
            validation_errors = []
            for validator in stage.validators:
                is_valid, errors = validator(packet.data, packet.project_id, db)
                if not is_valid:
                    validation_passed = False
                    validation_errors.extend(errors)

            packet.validation_errors = validation_errors

            if not validation_passed:
                packet.quality_level = DataQualityLevel.HALLUCINATED
                execution.status = StageStatus.FAILED
                execution.error = f"验证失败: {', '.join(validation_errors)}"
                logger.warning(f"⚠️  数据包 {packet_id} 验证失败: {validation_errors}")

                # 发送WebSocket通知
                await self._notify_stage_update(packet_id, execution.status, validation_errors)
                return

            packet.quality_level = DataQualityLevel.VERIFIED

            # 3. 检查是否需要人工审核
            if stage.require_approval:
                execution.status = StageStatus.REVIEW
                logger.info(f"👁️  数据包 {packet_id} 需要人工审核")

                # 发送WebSocket通知 - 等待审核
                await self._notify_stage_update(packet_id, StageStatus.REVIEW, None)
                return  # 暂停，等待approve_packet调用

            # 4. 标记完成
            execution.status = StageStatus.COMPLETED
            execution.end_time = datetime.utcnow()
            execution.result_data = result_data

            logger.info(f"✅ 数据包 {packet_id} 在阶段 {packet.stage_name} 完成")

            # 5. 自动触发下一阶段
            for next_stage_name in stage.next_stages:
                logger.info(f"🔄 自动触发下一阶段: {next_stage_name}")
                packet.stage_name = next_stage_name
                await self.process_packet(packet_id, db)

        except Exception as e:
            execution.status = StageStatus.FAILED
            execution.error = str(e)
            execution.end_time = datetime.utcnow()
            logger.error(f"❌ 数据包 {packet_id} 处理失败: {e}", exc_info=True)

            # 发送WebSocket通知
            await self._notify_stage_update(packet_id, StageStatus.FAILED, [str(e)])


    async def approve_packet(self, packet_id: str, db: Session) -> bool:
        """
        审核通过数据包 - 继续执行下一阶段

        Args:
            packet_id: 数据包ID
            db: 数据库会话

        Returns:
            bool: 是否成功
        """
        packet = self.packets.get(packet_id)
        if not packet:
            logger.error(f"❌ 数据包不存在: {packet_id}")
            return False

        stage = self.stages.get(packet.stage_name)
        if not stage:
            logger.error(f"❌ 阶段不存在: {packet.stage_name}")
            return False

        # 标记为已审核
        packet.quality_level = DataQualityLevel.APPROVED
        packet.updated_at = datetime.utcnow()

        logger.info(f"✅ 数据包 {packet_id} 审核通过")

        # 查找对应的execution并更新状态
        for execution in self.executions.values():
            if execution.packet_id == packet_id and execution.status == StageStatus.REVIEW:
                execution.status = StageStatus.APPROVED
                execution.end_time = datetime.utcnow()
                break

        # 触发下一阶段
        for next_stage_name in stage.next_stages:
            logger.info(f"🔄 审核通过后触发下一阶段: {next_stage_name}")
            packet.stage_name = next_stage_name
            await self.process_packet(packet_id, db)

        return True


    async def reject_packet(self, packet_id: str, reason: str) -> bool:
        """
        拒绝数据包 - 停止处理

        Args:
            packet_id: 数据包ID
            reason: 拒绝原因

        Returns:
            bool: 是否成功
        """
        packet = self.packets.get(packet_id)
        if not packet:
            return False

        packet.quality_level = DataQualityLevel.HALLUCINATED
        packet.validation_errors.append(f"人工拒绝: {reason}")

        # 更新execution状态
        for execution in self.executions.values():
            if execution.packet_id == packet_id and execution.status == StageStatus.REVIEW:
                execution.status = StageStatus.REJECTED
                execution.error = reason
                execution.end_time = datetime.utcnow()
                break

        logger.info(f"❌ 数据包 {packet_id} 被拒绝: {reason}")

        # 发送WebSocket通知
        await self._notify_stage_update(packet_id, StageStatus.REJECTED, [reason])

        return True


    def get_packet(self, packet_id: str) -> Optional[DataPacket]:
        """获取数据包"""
        return self.packets.get(packet_id)


    def get_project_packets(self, project_id: int) -> List[DataPacket]:
        """获取项目的所有数据包"""
        return [p for p in self.packets.values() if p.project_id == project_id]


    # ==================== Agent集成 ====================

    def load_agent_integration(self):
        """
        加载Agent集成模块 - 注册6个Agent为ProcessingStage

        注册的阶段：
        - agent_ingestion: IngestionAgent（18个服务）
        - agent_chunking: ChunkingAgent（4个服务）
        - agent_vectorization: VectorizationAgent（7个服务）
        - agent_knowledge_graph: KnowledgeAgent（需要审核）
        - agent_synthesis: SynthesisAgent
        - agent_report: ReportAgent（需要审核）
        """
        if self._agent_integration_loaded:
            return

        try:
            from app.core.agent_integration import AgentIntegration
            agent_integration = AgentIntegration(self)
            self._agent_integration_loaded = True
            logger.info("✅ Agent集成模块已加载，6个Agent已注册为处理阶段")
        except Exception as e:
            logger.error(f"❌ Agent集成模块加载失败: {e}")
            raise


    # ==================== 业务工作流 ====================

    async def process_document(
        self,
        file_path: str,
        project_id: int,
        document_id: Optional[int] = None,
        db: Session = None
    ) -> DataPacket:
        """
        文档处理工作流 - 完整的6-Agent管道

        流程：
        1. IngestionAgent - 提取文本
        2. ChunkingAgent - 分块
        3. VectorizationAgent - 向量化
        4. KnowledgeAgent - 知识图谱（需要审核）
        5. SynthesisAgent - 综合分析
        6. ReportAgent - 生成报告（需要审核）

        Args:
            file_path: 文件路径
            project_id: 项目ID
            document_id: 文档ID（可选）
            db: 数据库会话

        Returns:
            DataPacket: 初始数据包
        """
        # 确保Agent集成已加载
        self.load_agent_integration()

        # 创建数据包并启动agent_ingestion阶段
        packet = await self.create_packet(
            stage_name="agent_ingestion",
            data={
                "file_path": file_path,
                "document_id": document_id
            },
            project_id=project_id,
            metadata={
                "workflow_type": WorkflowType.AGENT_PIPELINE.value,
                "started_at": datetime.utcnow().isoformat()
            }
        )

        return packet


    async def run_rag_query(
        self,
        query: str,
        project_id: int,
        top_k: int = 5,
        use_llm: bool = True,
        db: Session = None
    ) -> Dict[str, Any]:
        """
        RAG查询工作流 - 多路检索 + LLM生成

        流程：
        1. 提取查询实体
        2. 并行检索（向量、全文、图谱、关键词）
        3. RRF融合排序
        4. LLM生成答案

        Args:
            query: 查询文本
            project_id: 项目ID
            top_k: 返回结果数
            use_llm: 是否使用LLM生成
            db: 数据库会话

        Returns:
            Dict: 查询结果
        """
        from app.core.rag_engine import rag_engine

        logger.info(f"🔍 RAG查询: {query} (项目={project_id})")

        try:
            result = await rag_engine.query(
                query=query,
                project_id=project_id,
                top_k=top_k,
                use_llm=use_llm,
                db=db
            )
            return result
        except Exception as e:
            logger.error(f"❌ RAG查询失败: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "query": query
            }


    async def crawl_and_process(
        self,
        url: str,
        project_id: int,
        crawler_type: Optional[str] = None,
        db: Session = None
    ) -> DataPacket:
        """
        爬虫+处理工作流

        流程：
        1. 智能爬取网页
        2. 提取内容
        3. 进入文档处理管道（agent_ingestion开始）

        Args:
            url: 目标URL
            project_id: 项目ID
            crawler_type: 爬虫类型（news/gecco/playwright等）
            db: 数据库会话

        Returns:
            DataPacket: 数据包
        """
        from app.services.crawler_service import intelligent_crawl

        logger.info(f"🕷️ 爬取URL: {url}")

        try:
            # 1. 爬取内容
            crawl_result = await intelligent_crawl(url, crawler_type)

            # 2. 保存为临时文件
            import tempfile
            import os
            temp_file = tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.txt',
                delete=False,
                encoding='utf-8'
            )
            temp_file.write(crawl_result.get("content", ""))
            temp_file.close()

            # 3. 进入文档处理管道
            packet = await self.process_document(
                file_path=temp_file.name,
                project_id=project_id,
                db=db
            )

            # 添加爬虫元数据
            packet.metadata.update({
                "source_url": url,
                "crawler_type": crawler_type,
                "crawl_time": datetime.utcnow().isoformat()
            })

            return packet

        except Exception as e:
            logger.error(f"❌ 爬虫处理失败: {e}", exc_info=True)
            raise


    async def process_audio(
        self,
        file_path: str,
        project_id: int,
        db: Session = None
    ) -> DataPacket:
        """
        音频处理工作流

        流程：
        1. 提取音频元数据
        2. Whisper语音转文字
        3. 进入文档处理管道

        Args:
            file_path: 音频文件路径
            project_id: 项目ID
            db: 数据库会话

        Returns:
            DataPacket: 数据包
        """
        # 直接进入agent_ingestion，IngestionAgent内部会处理音频
        packet = await self.process_document(
            file_path=file_path,
            project_id=project_id,
            db=db
        )
        packet.metadata["workflow_type"] = WorkflowType.AUDIO.value
        return packet


    async def generate_report(
        self,
        project_id: int,
        title: str,
        time_range: Optional[Dict[str, str]] = None,
        report_type: str = "summary",
        db: Session = None
    ) -> Dict[str, Any]:
        """
        报告生成工作流

        Args:
            project_id: 项目ID
            title: 报告标题
            time_range: 时间范围 {"start": "2024-01-01", "end": "2024-12-31"}
            report_type: 报告类型（summary/detailed/weekly等）
            db: 数据库会话

        Returns:
            Dict: 报告数据
        """
        logger.info(f"📊 生成报告: {title} (项目={project_id})")

        # 调用ReportAgent
        from app.agents.report_agent import ReportAgent

        agent = ReportAgent()
        report_result = agent.generate_report(
            project_id=project_id,
            title=title,
            time_range=time_range,
            report_type=report_type,
            db_session=db
        )

        return {
            "success": True,
            "report": report_result.report_content,
            "metadata": report_result.metadata,
            "citations": report_result.citations
        }


    # ==================== 批量处理 ====================

    async def batch_process_documents(
        self,
        file_paths: List[str],
        project_id: int,
        db: Session = None
    ) -> List[DataPacket]:
        """
        批量处理文档

        Args:
            file_paths: 文件路径列表
            project_id: 项目ID
            db: 数据库会话

        Returns:
            List[DataPacket]: 数据包列表
        """
        logger.info(f"📚 批量处理 {len(file_paths)} 个文档")

        tasks = [
            self.process_document(fp, project_id, db=db)
            for fp in file_paths
        ]

        packets = await asyncio.gather(*tasks, return_exceptions=True)

        # 过滤掉异常
        valid_packets = [p for p in packets if isinstance(p, DataPacket)]
        failed_count = len(packets) - len(valid_packets)

        if failed_count > 0:
            logger.warning(f"⚠️  {failed_count} 个文档处理失败")

        return valid_packets


    # ==================== 状态查询 ====================

    def get_stage_status(self, packet_id: str) -> Dict[str, Any]:
        """
        获取数据包的处理状态

        Args:
            packet_id: 数据包ID

        Returns:
            Dict: 状态信息
        """
        packet = self.packets.get(packet_id)
        if not packet:
            return {"error": "数据包不存在"}

        # 查找相关的executions
        executions = [
            {
                "execution_id": e.execution_id,
                "stage_name": e.stage_name,
                "status": e.status.value,
                "start_time": e.start_time.isoformat() if e.start_time else None,
                "end_time": e.end_time.isoformat() if e.end_time else None,
                "error": e.error
            }
            for e in self.executions.values()
            if e.packet_id == packet_id
        ]

        return {
            "packet_id": packet_id,
            "project_id": packet.project_id,
            "current_stage": packet.stage_name,
            "quality_level": packet.quality_level.value,
            "validation_errors": packet.validation_errors,
            "created_at": packet.created_at.isoformat(),
            "updated_at": packet.updated_at.isoformat(),
            "executions": executions
        }


    def get_project_status(self, project_id: int) -> Dict[str, Any]:
        """
        获取项目的处理状态概览

        Args:
            project_id: 项目ID

        Returns:
            Dict: 项目状态
        """
        packets = self.get_project_packets(project_id)

        # 统计各阶段的数据包数量
        stage_counts = {}
        quality_counts = {
            "raw": 0,
            "verified": 0,
            "hallucinated": 0,
            "approved": 0
        }

        for packet in packets:
            # 阶段统计
            stage_counts[packet.stage_name] = stage_counts.get(packet.stage_name, 0) + 1

            # 质量统计
            quality_counts[packet.quality_level.value] += 1

        # 统计待审核的数据包
        pending_review = [
            p.packet_id for p in packets
            if any(
                e.status == StageStatus.REVIEW
                for e in self.executions.values()
                if e.packet_id == p.packet_id
            )
        ]

        return {
            "project_id": project_id,
            "total_packets": len(packets),
            "stage_distribution": stage_counts,
            "quality_distribution": quality_counts,
            "pending_review": pending_review,
            "pending_review_count": len(pending_review)
        }


    # ==================== WebSocket通知 ====================

    async def _notify_stage_update(
        self,
        packet_id: str,
        status: StageStatus,
        errors: Optional[List[str]]
    ):
        """
        发送WebSocket通知

        Args:
            packet_id: 数据包ID
            status: 阶段状态
            errors: 错误列表
        """
        if not self.ws_manager:
            return

        packet = self.packets.get(packet_id)
        if not packet:
            return

        message = {
            "type": "stage_update",
            "packet_id": packet_id,
            "project_id": packet.project_id,
            "stage_name": packet.stage_name,
            "status": status.value,
            "quality_level": packet.quality_level.value,
            "errors": errors or [],
            "timestamp": datetime.utcnow().isoformat()
        }

        try:
            await self.ws_manager.broadcast(message, project_id=packet.project_id)
        except Exception as e:
            logger.error(f"WebSocket通知失败: {e}")


    def set_websocket_manager(self, ws_manager):
        """设置WebSocket管理器"""
        self.ws_manager = ws_manager
        logger.info("✅ WebSocket管理器已设置")

    # ==================== 自学习能力（Hermes Learning Integration） ====================

    def record_stage_learning(
        self,
        project_id: int,
        stage_name: str,
        context: Dict[str, Any],
        result: Dict[str, Any],
        success: bool,
        execution_time: float
    ):
        """
        记录阶段执行的学习经验

        Args:
            project_id: 项目ID
            stage_name: 阶段名称
            context: 执行上下文
            result: 执行结果
            success: 是否成功
            execution_time: 执行时间
        """
        if not self.learning_engine:
            return

        try:
            from app.services.hermes_learning_engine import LearningType

            self.learning_engine.record_experience(
                project_id=project_id,
                learning_type=LearningType.WORKFLOW_OPTIMIZATION,
                context={
                    "stage_name": stage_name,
                    **context
                },
                action={
                    "stage": stage_name,
                    "handler": self.stages.get(stage_name).__class__.__name__ if stage_name in self.stages else "unknown"
                },
                result=result,
                success=success,
                execution_time=execution_time
            )
            logger.debug(f"📚 记录阶段学习: {stage_name} (project={project_id})")

        except Exception as e:
            logger.warning(f"⚠️ 记录阶段学习失败: {e}")

    def suggest_next_stage(
        self,
        project_id: int,
        current_stage: str,
        context: Dict[str, Any]
    ) -> Optional[str]:
        """
        基于历史学习，建议下一个最优阶段

        Args:
            project_id: 项目ID
            current_stage: 当前阶段
            context: 当前上下文

        Returns:
            建议的下一个阶段名称，或 None
        """
        if not self.learning_engine:
            return None

        try:
            from app.services.hermes_learning_engine import LearningType

            suggested = self.learning_engine.suggest_action(
                context={
                    "current_stage": current_stage,
                    **context
                },
                learning_type=LearningType.WORKFLOW_OPTIMIZATION
            )

            if suggested and "stage" in suggested:
                return suggested["stage"]

        except Exception as e:
            logger.warning(f"⚠️ 建议下一阶段失败: {e}")

        return None

    def get_learning_insights(self) -> Dict[str, Any]:
        """
        获取 Hermes 的学习洞察

        Returns:
            学习统计和洞察
        """
        if not self.learning_engine:
            return {
                "learning_enabled": False,
                "message": "Learning engine not available"
            }

        try:
            stats = self.learning_engine.get_stats()
            return {
                "learning_enabled": True,
                "total_experiences": stats["total_experiences"],
                "total_skills": stats["total_skills"],
                "success_rate": stats["success_rate"],
                "workflow_optimizations": stats["learning_types"].get("workflow", 0)
            }
        except Exception as e:
            logger.error(f"❌ 获取学习洞察失败: {e}")
            return {
                "learning_enabled": False,
                "error": str(e)
            }



# ==================== 全局实例 ====================

# Hermes统一编排引擎实例
hermes = Hermes()


# ==================== 向后兼容的别名 ====================

# 为了兼容现有代码，提供别名
data_flow_orchestrator = hermes  # 旧的DataFlowOrchestrator
workflow_engine = hermes  # 旧的WorkflowEngine
orchestrator = hermes  # 旧的WorkflowOrchestrator
