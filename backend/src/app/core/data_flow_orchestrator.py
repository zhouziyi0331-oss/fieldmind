"""
数据流通编排中台 - 核心协同引擎

职责：
1. 数据流通：打通各个板块的数据端口
2. 工作流串联：第一个功能完成后自动触发第二个功能深化
3. 数据审核：防止AI胡编，审核通过后才显示
4. 项目隔离：确保每个项目数据独立
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from sqlalchemy.orm import Session
import logging
import json

logger = logging.getLogger(__name__)


class StageStatus(str, Enum):
    """阶段状态"""
    PENDING = "pending"
    RUNNING = "running"
    REVIEW = "review"  # 等待审核
    APPROVED = "approved"  # 审核通过
    REJECTED = "rejected"  # 审核拒绝
    COMPLETED = "completed"
    FAILED = "failed"


class DataQualityLevel(str, Enum):
    """数据质量等级"""
    RAW = "raw"  # 原始数据，未验证
    VERIFIED = "verified"  # 已验证，可信
    HALLUCINATED = "hallucinated"  # 检测到幻觉
    APPROVED = "approved"  # 人工审核通过


@dataclass
class DataPacket:
    """数据包 - 在各个阶段流通的标准数据单元"""
    packet_id: str
    project_id: int
    stage_name: str
    data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    quality_level: DataQualityLevel = DataQualityLevel.RAW
    validation_errors: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self):
        return {
            "packet_id": self.packet_id,
            "project_id": self.project_id,
            "stage_name": self.stage_name,
            "data": self.data,
            "metadata": self.metadata,
            "quality_level": self.quality_level.value,
            "validation_errors": self.validation_errors,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class ProcessingStage:
    """处理阶段定义"""
    name: str
    handler: Callable
    validators: List[Callable] = field(default_factory=list)  # 数据验证器
    next_stages: List[str] = field(default_factory=list)  # 下一阶段（可多个）
    require_approval: bool = False  # 是否需要人工审核
    project_isolated: bool = True  # 是否强制项目隔离


class DataFlowOrchestrator:
    """数据流通编排器 - 中台核心"""

    def __init__(self):
        self.stages: Dict[str, ProcessingStage] = {}
        self.data_store: Dict[str, DataPacket] = {}  # 临时存储（生产环境应用Redis）
        self._register_default_pipeline()

    def _register_default_pipeline(self):
        """注册默认的数据处理流水线"""

        # 阶段1：文档上传和提取
        self.register_stage(
            name="document_upload",
            handler=self._handle_document_upload,
            validators=[self._validate_file_exists],
            next_stages=["document_extraction"],
            require_approval=False
        )

        # 阶段2：内容提取
        self.register_stage(
            name="document_extraction",
            handler=self._handle_document_extraction,
            validators=[self._validate_text_content],
            next_stages=["parallel_processing"],  # 进入并行处理
            require_approval=False
        )

        # 阶段3：并行处理（向量化、实体提取、知识图谱）
        self.register_stage(
            name="parallel_processing",
            handler=self._handle_parallel_processing,
            validators=[
                self._validate_chunks_exist,
                self._validate_entities_exist
            ],
            next_stages=["knowledge_synthesis"],  # 进入知识综合
            require_approval=False
        )

        # 阶段4：知识综合（构建图谱、生成脉络）
        self.register_stage(
            name="knowledge_synthesis",
            handler=self._handle_knowledge_synthesis,
            validators=[
                self._validate_graph_completeness,
                self._validate_no_hallucination  # 防止AI胡编
            ],
            next_stages=["analysis_generation"],
            require_approval=True  # 需要审核
        )

        # 阶段5：分析生成（产业分析、报告生成）
        self.register_stage(
            name="analysis_generation",
            handler=self._handle_analysis_generation,
            validators=[
                self._validate_analysis_facts,
                self._validate_citations  # 检查引用来源
            ],
            next_stages=["display_ready"],
            require_approval=True  # 需要审核
        )

        # 阶段6：准备展示
        self.register_stage(
            name="display_ready",
            handler=self._handle_display_ready,
            validators=[],
            next_stages=[],
            require_approval=False
        )

    def register_stage(
        self,
        name: str,
        handler: Callable,
        validators: List[Callable] = None,
        next_stages: List[str] = None,
        require_approval: bool = False,
        project_isolated: bool = True
    ):
        """注册处理阶段"""
        stage = ProcessingStage(
            name=name,
            handler=handler,
            validators=validators or [],
            next_stages=next_stages or [],
            require_approval=require_approval,
            project_isolated=project_isolated
        )
        self.stages[name] = stage
        logger.info(f"注册阶段: {name}")

    async def process_packet(
        self,
        packet: DataPacket,
        db: Session
    ) -> DataPacket:
        """
        处理数据包

        流程：
        1. 项目隔离检查
        2. 执行handler处理
        3. 运行validators验证
        4. 决定是否需要审核
        5. 自动触发下一阶段
        """
        stage = self.stages.get(packet.stage_name)
        if not stage:
            raise ValueError(f"未知阶段: {packet.stage_name}")

        logger.info(f"📦 处理数据包: {packet.packet_id} @ {packet.stage_name} (项目 {packet.project_id})")

        # 1. 项目隔离检查
        if stage.project_isolated:
            self._enforce_project_isolation(packet, db)

        try:
            # 2. 执行handler
            logger.info(f"  🔧 执行handler: {stage.name}")
            result_data = await stage.handler(packet.data, packet.project_id, db)
            packet.data.update(result_data)

            # 3. 运行validators
            validation_passed = True
            for validator in stage.validators:
                logger.info(f"  ✓ 运行验证器: {validator.__name__}")
                is_valid, errors = validator(packet.data, packet.project_id, db)
                if not is_valid:
                    validation_passed = False
                    packet.validation_errors.extend(errors)
                    packet.quality_level = DataQualityLevel.HALLUCINATED

            if validation_passed:
                packet.quality_level = DataQualityLevel.VERIFIED
                logger.info(f"  ✅ 验证通过")
            else:
                logger.warning(f"  ⚠️ 验证失败: {packet.validation_errors}")

            # 4. 决定是否需要审核
            if stage.require_approval and validation_passed:
                packet.quality_level = DataQualityLevel.VERIFIED
                logger.info(f"  🔍 等待审核...")
                # 存储到待审核队列
                await self._save_for_review(packet, db)
                return packet

            # 5. 自动触发下一阶段
            if validation_passed and stage.next_stages:
                logger.info(f"  ➡️ 自动触发下一阶段: {stage.next_stages}")
                for next_stage_name in stage.next_stages:
                    next_packet = DataPacket(
                        packet_id=f"{packet.packet_id}_{next_stage_name}",
                        project_id=packet.project_id,
                        stage_name=next_stage_name,
                        data=packet.data.copy(),  # 继承数据
                        metadata={
                            **packet.metadata,
                            "parent_packet": packet.packet_id,
                            "parent_stage": packet.stage_name
                        },
                        quality_level=DataQualityLevel.RAW
                    )
                    # 递归处理下一阶段
                    await self.process_packet(next_packet, db)

            return packet

        except Exception as e:
            logger.error(f"  ❌ 处理失败: {e}", exc_info=True)
            packet.quality_level = DataQualityLevel.HALLUCINATED
            packet.validation_errors.append(f"处理异常: {str(e)}")
            raise

    def _enforce_project_isolation(self, packet: DataPacket, db: Session):
        """强制项目隔离"""
        if not packet.project_id:
            raise ValueError("缺少project_id，无法进行项目隔离")

        # 验证project_id存在
        from app.models.project import Project
        project = db.query(Project).filter(Project.id == packet.project_id).first()
        if not project:
            raise ValueError(f"项目不存在: {packet.project_id}")

        logger.debug(f"  🔒 项目隔离检查通过: 项目 {packet.project_id} ({project.name})")

    async def _save_for_review(self, packet: DataPacket, db: Session):
        """保存到待审核队列"""
        from app.models.project import ProjectContext
        from sqlalchemy import text

        # 保存到数据库的待审核表
        sql = text("""
            INSERT INTO pending_reviews
            (packet_id, project_id, stage_name, data, metadata, quality_level, created_at)
            VALUES
            (:packet_id, :project_id, :stage_name, :data, :metadata, :quality_level, :created_at)
        """)

        try:
            db.execute(sql, {
                "packet_id": packet.packet_id,
                "project_id": packet.project_id,
                "stage_name": packet.stage_name,
                "data": json.dumps(packet.data, ensure_ascii=False),
                "metadata": json.dumps(packet.metadata, ensure_ascii=False),
                "quality_level": packet.quality_level.value,
                "created_at": packet.created_at
            })
            db.commit()
            logger.info(f"  💾 已保存到待审核队列: {packet.packet_id}")
        except Exception as e:
            logger.error(f"保存待审核失败: {e}")
            # 如果表不存在，先跳过（后面会创建表）
            db.rollback()

    async def approve_packet(self, packet_id: str, db: Session) -> bool:
        """审核通过数据包"""
        # 从待审核队列取出
        from sqlalchemy import text

        sql = text("""
            SELECT * FROM pending_reviews WHERE packet_id = :packet_id
        """)

        row = db.execute(sql, {"packet_id": packet_id}).fetchone()
        if not row:
            return False

        # 重建数据包
        packet = DataPacket(
            packet_id=row.packet_id,
            project_id=row.project_id,
            stage_name=row.stage_name,
            data=json.loads(row.data),
            metadata=json.loads(row.metadata),
            quality_level=DataQualityLevel.APPROVED
        )

        # 继续处理下一阶段
        stage = self.stages.get(packet.stage_name)
        if stage and stage.next_stages:
            for next_stage_name in stage.next_stages:
                next_packet = DataPacket(
                    packet_id=f"{packet.packet_id}_{next_stage_name}_approved",
                    project_id=packet.project_id,
                    stage_name=next_stage_name,
                    data=packet.data.copy(),
                    metadata=packet.metadata,
                    quality_level=DataQualityLevel.APPROVED
                )
                await self.process_packet(next_packet, db)

        # 删除待审核记录
        delete_sql = text("DELETE FROM pending_reviews WHERE packet_id = :packet_id")
        db.execute(delete_sql, {"packet_id": packet_id})
        db.commit()

        logger.info(f"✅ 审核通过并继续处理: {packet_id}")
        return True

    # ==================== Handler实现 ====================

    async def _handle_document_upload(self, data: Dict, project_id: int, db: Session) -> Dict:
        """处理文档上传"""
        file_path = data.get("file_path")
        document_id = data.get("document_id")

        logger.info(f"处理文档上传: {file_path}")

        return {
            "upload_status": "completed",
            "file_path": file_path,
            "document_id": document_id
        }

    async def _handle_document_extraction(self, data: Dict, project_id: int, db: Session) -> Dict:
        """处理内容提取"""
        document_id = data.get("document_id")

        # 调用document_processing_pipeline
        from app.services.document_processing_pipeline import DocumentProcessingPipeline

        pipeline = DocumentProcessingPipeline()
        # 这里简化，实际应从数据库获取文件路径

        logger.info(f"内容提取完成: document_id={document_id}")

        return {
            "extraction_status": "completed",
            "text_length": data.get("text_length", 0)
        }

    async def _handle_parallel_processing(self, data: Dict, project_id: int, db: Session) -> Dict:
        """并行处理：向量化、实体提取、知识图谱"""
        document_id = data.get("document_id")

        logger.info(f"并行处理: document_id={document_id}")

        # 这里会调用实际的处理服务
        # 向量化、实体提取、知识图谱构建同时进行

        return {
            "parallel_status": "completed",
            "chunks_count": data.get("chunks_count", 0),
            "entities_count": data.get("entities_count", 0)
        }

    async def _handle_knowledge_synthesis(self, data: Dict, project_id: int, db: Session) -> Dict:
        """知识综合：构建图谱、生成脉络"""
        logger.info(f"知识综合: project_id={project_id}")

        # 调用知识图谱服务
        # 生成知识脉络

        return {
            "synthesis_status": "completed",
            "graph_nodes": data.get("entities_count", 0),
            "graph_edges": 0
        }

    async def _handle_analysis_generation(self, data: Dict, project_id: int, db: Session) -> Dict:
        """分析生成：产业分析、报告生成"""
        logger.info(f"分析生成: project_id={project_id}")

        # 调用分析服务
        # 生成报告

        return {
            "analysis_status": "completed",
            "report_generated": True
        }

    async def _handle_display_ready(self, data: Dict, project_id: int, db: Session) -> Dict:
        """准备展示"""
        logger.info(f"准备展示: project_id={project_id}")

        return {
            "display_status": "ready",
            "timestamp": datetime.now().isoformat()
        }

    # ==================== Validator实现 ====================

    def _validate_file_exists(self, data: Dict, project_id: int, db: Session) -> tuple[bool, List[str]]:
        """验证文件存在"""
        file_path = data.get("file_path")
        if not file_path:
            return False, ["缺少file_path"]

        import os
        if not os.path.exists(file_path):
            return False, [f"文件不存在: {file_path}"]

        return True, []

    def _validate_text_content(self, data: Dict, project_id: int, db: Session) -> tuple[bool, List[str]]:
        """验证文本内容"""
        text_length = data.get("text_length", 0)
        if text_length < 10:
            return False, ["文本内容太短"]

        return True, []

    def _validate_chunks_exist(self, data: Dict, project_id: int, db: Session) -> tuple[bool, List[str]]:
        """验证chunks存在"""
        chunks_count = data.get("chunks_count", 0)
        if chunks_count == 0:
            return False, ["未生成chunks"]

        return True, []

    def _validate_entities_exist(self, data: Dict, project_id: int, db: Session) -> tuple[bool, List[str]]:
        """验证实体存在"""
        entities_count = data.get("entities_count", 0)
        if entities_count == 0:
            return False, ["未提取实体"]

        return True, []

    def _validate_graph_completeness(self, data: Dict, project_id: int, db: Session) -> tuple[bool, List[str]]:
        """验证知识图谱完整性"""
        graph_nodes = data.get("graph_nodes", 0)
        if graph_nodes < 3:
            return False, ["知识图谱节点太少"]

        return True, []

    def _validate_no_hallucination(self, data: Dict, project_id: int, db: Session) -> tuple[bool, List[str]]:
        """防止AI胡编 - 使用反幻觉检测器"""
        from app.services.anti_hallucination_report import HallucinationDetector

        # 检查生成的文本中的数字是否都来自原始数据
        generated_text = data.get("generated_text", "")
        facts = data.get("facts", {})

        if generated_text and facts:
            is_valid, errors = HallucinationDetector.validate_report(generated_text, facts)
            if not is_valid:
                return False, errors

        return True, []

    def _validate_analysis_facts(self, data: Dict, project_id: int, db: Session) -> tuple[bool, List[str]]:
        """验证分析基于事实"""
        analysis_text = data.get("analysis_text", "")
        if not analysis_text:
            return False, ["缺少分析文本"]

        # 检查是否包含数据来源
        if "来源：" not in analysis_text and "引用：" not in analysis_text:
            return False, ["分析缺少数据来源标注"]

        return True, []

    def _validate_citations(self, data: Dict, project_id: int, db: Session) -> tuple[bool, List[str]]:
        """检查引用来源"""
        analysis_text = data.get("analysis_text", "")

        # 简单检查：是否有引用标记
        import re
        citations = re.findall(r'（来源：[^）]+）', analysis_text)

        if len(citations) == 0:
            return False, ["缺少引用来源"]

        return True, []


# 全局实例
data_flow_orchestrator = DataFlowOrchestrator()
