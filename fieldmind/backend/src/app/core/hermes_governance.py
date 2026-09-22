"""
Hermes 治理框架集成层

将 Hermes 智能体编排引擎与企业治理能力整合：
- 审计日志 (audit.py)
- 数据血缘追踪 (lineage_tracking.py)
- 权限控制 (permission_decorators.py)
- Agent 协调 (agent_coordinator.py)

提供企业级的可控性、可审计性、可恢复性
"""

from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from functools import wraps
import asyncio
import logging

from sqlalchemy.orm import Session

from app.core.hermes import Hermes, DataPacket, StageStatus, DataQualityLevel
from app.core.audit import audit_log, audit_ai_operation
from app.core.lineage_tracking import track_lineage, LineageContext
from app.core.permission_decorators import require_permission
from app.core.agent_coordinator import AgentTask, TaskStatus
from app.models.audit_log import ActionType, ActorType
from app.models.permission import PermissionAction, ResourceType as PermissionResourceType

logger = logging.getLogger(__name__)


class GovernedHermes(Hermes):
    """
    治理化的 Hermes 引擎

    在 Hermes 基础上添加企业治理能力：
    1. 所有操作自动审计
    2. 数据流转自动追踪血缘
    3. 敏感操作权限控制
    4. Agent 执行可追溯
    5. 错误恢复和回滚
    """

    def __init__(self):
        super().__init__()

        # 治理配置
        self.enable_audit = True
        self.enable_lineage = True
        self.enable_permission_check = True

        # 血缘追踪缓存
        self._lineage_records: List[Dict] = []

        logger.info("🛡️ GovernedHermes 已启动 - 企业治理模式")


    # ==================== 治理化的阶段注册 ====================

    def register_governed_stage(
        self,
        name: str,
        handler: Callable,
        validators: List[Callable] = None,
        next_stages: List[str] = None,
        require_approval: bool = False,
        require_permission: Optional[PermissionAction] = None,
        resource_type: Optional[PermissionResourceType] = None,
        **kwargs
    ):
        """
        注册治理化的处理阶段

        在原有 handler 基础上自动添加：
        - 审计日志记录
        - 数据血缘追踪
        - 权限检查

        Args:
            name: 阶段名称
            handler: 原始处理函数
            validators: 验证器列表
            next_stages: 下一阶段列表
            require_approval: 是否需要人工审核
            require_permission: 需要的权限
            resource_type: 资源类型
            **kwargs: 其他参数传递给 register_stage
        """

        # 包装 handler，添加治理能力
        governed_handler = self._wrap_handler_with_governance(
            handler=handler,
            stage_name=name,
            require_permission=require_permission,
            resource_type=resource_type
        )

        # 注册到 Hermes
        self.register_stage(
            name=name,
            handler=governed_handler,
            validators=validators,
            next_stages=next_stages,
            require_approval=require_approval,
            **kwargs
        )

        logger.info(f"🛡️ 治理化阶段已注册: {name} (权限={require_permission})")


    def _wrap_handler_with_governance(
        self,
        handler: Callable,
        stage_name: str,
        require_permission: Optional[PermissionAction] = None,
        resource_type: Optional[PermissionResourceType] = None
    ) -> Callable:
        """
        包装处理函数，添加治理能力

        执行顺序：
        1. 权限检查
        2. 审计日志（开始）
        3. 执行 handler
        4. 数据血缘追踪
        5. 审计日志（结束）
        """

        @wraps(handler)
        async def governed_wrapper(
            data: Dict[str, Any],
            project_id: int,
            db: Session,
            user_id: Optional[int] = None,
            **handler_kwargs
        ) -> Dict[str, Any]:

            start_time = datetime.utcnow()
            error = None
            result = None

            try:
                # 1. 权限检查
                if self.enable_permission_check and require_permission and user_id:
                    await self._check_permission(
                        user_id=user_id,
                        action=require_permission,
                        resource_type=resource_type or PermissionResourceType.PROJECT,
                        resource_id=str(project_id),
                        db=db
                    )

                # 2. 执行原始 handler
                result = await handler(data, project_id, db, **handler_kwargs)

                # 3. 记录数据血缘
                if self.enable_lineage:
                    await self._record_stage_lineage(
                        db=db,
                        project_id=project_id,
                        stage_name=stage_name,
                        input_data=data,
                        output_data=result,
                        user_id=user_id
                    )

                return result

            except Exception as e:
                error = e
                logger.error(f"❌ 阶段 {stage_name} 执行失败: {e}")
                raise

            finally:
                # 4. 审计日志
                if self.enable_audit:
                    duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                    await self._record_audit(
                        db=db,
                        stage_name=stage_name,
                        project_id=project_id,
                        user_id=user_id,
                        result=result,
                        error=error,
                        duration_ms=duration_ms
                    )

        return governed_wrapper


    # ==================== 治理能力实现 ====================

    async def _check_permission(
        self,
        user_id: int,
        action: PermissionAction,
        resource_type: PermissionResourceType,
        resource_id: str,
        db: Session
    ):
        """权限检查"""
        from app.services.permission_service import PermissionService

        permission_service = PermissionService(db)
        has_permission = await permission_service.check_permission(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id
        )

        if not has_permission:
            raise PermissionError(
                f"权限不足: 用户 {user_id} 需要 {action.value} {resource_type.value} 权限"
            )


    async def _record_audit(
        self,
        db: Session,
        stage_name: str,
        project_id: int,
        user_id: Optional[int],
        result: Optional[Dict],
        error: Optional[Exception],
        duration_ms: int
    ):
        """记录审计日志"""
        from app.services.audit_service import AuditService
        from app.models.audit_log import AuditResult

        try:
            await AuditService.create_log(
                db=db,
                actor_type=ActorType.AI if not user_id else ActorType.USER,
                actor_id=user_id or "hermes",
                action=ActionType.EXECUTE,
                resource_type="hermes_stage",
                resource_id=stage_name,
                resource_name=stage_name,
                project_id=project_id,
                result=AuditResult.SUCCESS if not error else AuditResult.FAILURE,
                error_message=str(error) if error else None,
                duration_ms=duration_ms,
                extra_metadata={
                    "stage": stage_name,
                    "has_result": result is not None,
                    "engine": "hermes"
                }
            )
        except Exception as e:
            logger.warning(f"审计日志记录失败: {e}")


    async def _record_stage_lineage(
        self,
        db: Session,
        project_id: int,
        stage_name: str,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        user_id: Optional[int]
    ):
        """记录阶段血缘"""
        from app.services.lineage_service import DataLineageService

        try:
            lineage_service = DataLineageService(db)

            # 提取输入/输出 ID
            source_id = self._extract_id(input_data)
            target_id = self._extract_id(output_data)

            if source_id and target_id:
                await lineage_service.create_lineage(
                    project_id=project_id,
                    source_type="data_packet",
                    source_id=str(source_id),
                    target_type="data_packet",
                    target_id=str(target_id),
                    operation=stage_name,
                    transformation={
                        "stage": stage_name,
                        "timestamp": datetime.utcnow().isoformat(),
                        "engine": "hermes"
                    },
                    actor_id=user_id,
                    actor_type="user" if user_id else "system"
                )

                logger.debug(f"✅ 血缘已记录: {source_id} -> {target_id} via {stage_name}")

        except Exception as e:
            logger.warning(f"血缘追踪失败: {e}")


    def _extract_id(self, data: Dict[str, Any]) -> Optional[str]:
        """从数据中提取 ID"""
        if not data:
            return None

        # 尝试多种 ID 字段
        for key in ['id', 'packet_id', 'document_id', 'task_id', 'resource_id']:
            if key in data:
                return str(data[key])

        # 如果没有 ID，使用数据的哈希
        return str(hash(str(data)))


    # ==================== 治理化的数据包处理 ====================

    async def create_governed_packet(
        self,
        stage_name: str,
        data: Dict[str, Any],
        project_id: int,
        user_id: Optional[int] = None,
        metadata: Dict[str, Any] = None,
        db: Session = None
    ) -> DataPacket:
        """
        创建治理化的数据包

        自动记录：
        - 创建审计日志
        - 初始血缘记录
        """

        # 创建数据包
        packet = await self.create_packet(
            stage_name=stage_name,
            data=data,
            project_id=project_id,
            metadata=metadata or {}
        )

        # 审计日志
        if self.enable_audit and db:
            await self._record_audit(
                db=db,
                stage_name="create_packet",
                project_id=project_id,
                user_id=user_id,
                result={"packet_id": packet.packet_id},
                error=None,
                duration_ms=0
            )

        logger.info(f"🛡️ 治理化数据包已创建: {packet.packet_id}")
        return packet


    async def execute_governed_stage(
        self,
        packet_id: str,
        stage_name: str,
        db: Session,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        执行治理化的阶段

        包含完整的审计和血缘追踪
        """

        packet = self.packets.get(packet_id)
        if not packet:
            raise ValueError(f"数据包不存在: {packet_id}")

        stage = self.get_stage(stage_name)
        if not stage:
            raise ValueError(f"阶段不存在: {stage_name}")

        # 执行阶段（已包含治理能力）
        result = await stage.handler(
            data=packet.data,
            project_id=packet.project_id,
            db=db,
            user_id=user_id
        )

        # 更新数据包
        packet.data = result
        packet.updated_at = datetime.utcnow()

        logger.info(f"✅ 治理化阶段执行完成: {stage_name} for {packet_id}")
        return result


    # ==================== 血缘查询 ====================

    async def get_packet_lineage(
        self,
        packet_id: str,
        db: Session,
        depth: int = 5
    ) -> Dict[str, Any]:
        """
        获取数据包的完整血缘链路

        Returns:
            {
                "packet_id": "...",
                "upstream": [...],  # 上游数据源
                "downstream": [...],  # 下游数据产物
                "stages": [...]  # 经过的处理阶段
            }
        """
        from app.services.lineage_service import DataLineageService

        lineage_service = DataLineageService(db)

        # 获取上游血缘
        upstream = await lineage_service.get_upstream_lineage(
            target_type="data_packet",
            target_id=packet_id,
            depth=depth
        )

        # 获取下游血缘
        downstream = await lineage_service.get_downstream_lineage(
            source_type="data_packet",
            source_id=packet_id,
            depth=depth
        )

        return {
            "packet_id": packet_id,
            "upstream": upstream,
            "downstream": downstream,
            "stages": self._extract_stages_from_lineage(upstream, downstream)
        }


    def _extract_stages_from_lineage(
        self,
        upstream: List[Dict],
        downstream: List[Dict]
    ) -> List[str]:
        """从血缘记录中提取阶段名称"""
        stages = set()

        for record in upstream + downstream:
            if 'operation' in record:
                stages.add(record['operation'])

        return sorted(list(stages))


    # ==================== 审计查询 ====================

    async def get_stage_audit_trail(
        self,
        stage_name: str,
        project_id: int,
        db: Session,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        获取阶段的审计轨迹

        Returns:
            按时间倒序的审计日志列表
        """
        from app.services.audit_service import AuditService

        logs = await AuditService.get_logs(
            db=db,
            resource_type="hermes_stage",
            resource_id=stage_name,
            project_id=project_id,
            limit=limit
        )

        return [log.to_dict() for log in logs]


    # ==================== 治理配置 ====================

    def configure_governance(
        self,
        enable_audit: bool = True,
        enable_lineage: bool = True,
        enable_permission_check: bool = True
    ):
        """配置治理能力的开关"""
        self.enable_audit = enable_audit
        self.enable_lineage = enable_lineage
        self.enable_permission_check = enable_permission_check

        logger.info(
            f"🛡️ 治理配置已更新: "
            f"审计={enable_audit}, "
            f"血缘={enable_lineage}, "
            f"权限={enable_permission_check}"
        )


# ==================== 全局单例 ====================

_governed_hermes_instance: Optional[GovernedHermes] = None


def get_governed_hermes() -> GovernedHermes:
    """获取治理化 Hermes 单例"""
    global _governed_hermes_instance

    if _governed_hermes_instance is None:
        _governed_hermes_instance = GovernedHermes()

    return _governed_hermes_instance


# ==================== 便捷装饰器 ====================

def governed_stage(
    stage_name: str,
    require_permission: Optional[PermissionAction] = None,
    resource_type: Optional[PermissionResourceType] = None,
    next_stages: List[str] = None,
    require_approval: bool = False
):
    """
    治理化阶段装饰器

    用法:
        @governed_stage(
            stage_name="document_processing",
            require_permission=PermissionAction.EDIT,
            resource_type=PermissionResourceType.DOCUMENT
        )
        async def process_document(data: Dict, project_id: int, db: Session):
            # 处理逻辑
            return {"processed": True}
    """
    def decorator(func: Callable) -> Callable:
        hermes = get_governed_hermes()

        hermes.register_governed_stage(
            name=stage_name,
            handler=func,
            require_permission=require_permission,
            resource_type=resource_type,
            next_stages=next_stages or [],
            require_approval=require_approval
        )

        return func

    return decorator
