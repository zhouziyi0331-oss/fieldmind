"""
企业级治理框架完整集成

将所有治理能力整合到 GovernedHermes：
- ✅ 版本控制和回滚
- ✅ 完整审计日志
- ✅ 权限和访问控制
- ✅ 故障恢复机制
- ✅ 配置管理
- ✅ 合规性检查
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
import logging

from app.core.hermes_governance import GovernedHermes
from app.core.governance.version_control import (
    VersionControlService,
    VersionType,
    VersionStatus
)
from app.core.governance.failure_recovery import (
    FailureRecoveryService,
    CircuitBreaker,
    RetryConfig,
    retry_with_backoff
)
from app.core.governance.configuration import (
    ConfigurationManager,
    ConfigScope,
    ConfigType,
    ConfigurationTemplate
)
from app.core.governance.compliance import (
    ComplianceService,
    ComplianceType,
    ComplianceStatus
)

logger = logging.getLogger(__name__)


class EnterpriseGovernedHermes(GovernedHermes):
    """
    企业级治理化 Hermes

    在 GovernedHermes 基础上添加：
    1. 版本控制和回滚
    2. 故障恢复机制
    3. 配置管理
    4. 合规性检查
    """

    def __init__(self, db: Session, encryption_key: Optional[str] = None):
        super().__init__()

        self.db = db

        # 初始化治理服务
        self.version_control = VersionControlService(db)
        self.failure_recovery = FailureRecoveryService(db)
        self.config_manager = ConfigurationManager(db, encryption_key)
        self.compliance_service = ComplianceService(db)

        # 加载配置
        self._load_configuration()

        logger.info("🏢 EnterpriseGovernedHermes 已启动 - 完整企业治理模式")


    # ==================== 配置管理 ====================

    def _load_configuration(self):
        """加载配置"""
        try:
            # 加载治理配置
            self.enable_audit = self.config_manager.get(
                "hermes.enable_audit",
                default=True
            )
            self.enable_lineage = self.config_manager.get(
                "hermes.enable_lineage",
                default=True
            )
            self.enable_permission_check = self.config_manager.get(
                "hermes.enable_permission",
                default=True
            )

            logger.info("✅ 配置已加载")

        except Exception as e:
            logger.warning(f"配置加载失败，使用默认值: {e}")


    def update_configuration(
        self,
        key: str,
        value: Any,
        user_id: Optional[int] = None
    ):
        """更新配置"""
        self.config_manager.set(
            key=key,
            value=value,
            user_id=user_id
        )

        # 重新加载配置
        self._load_configuration()

        logger.info(f"✅ 配置已更新: {key}")


    def get_configuration(
        self,
        key: str,
        default: Any = None
    ) -> Any:
        """获取配置"""
        return self.config_manager.get(key, default=default)


    # ==================== 版本控制 ====================

    async def create_packet_version(
        self,
        packet_id: str,
        user_id: Optional[int] = None,
        description: Optional[str] = None
    ) -> Any:
        """
        为数据包创建版本

        Args:
            packet_id: 数据包ID
            user_id: 用户ID
            description: 版本描述

        Returns:
            Version 对象
        """
        packet = self.packets.get(packet_id)
        if not packet:
            raise ValueError(f"数据包不存在: {packet_id}")

        # 创建版本
        version = self.version_control.create_version(
            version_type=VersionType.DATA_PACKET,
            resource_id=packet_id,
            resource_name=packet.stage_name,
            content={
                "data": packet.data,
                "metadata": packet.metadata,
                "quality_level": packet.quality_level.value,
                "stage_name": packet.stage_name
            },
            project_id=packet.project_id,
            created_by=user_id,
            description=description
        )

        logger.info(f"✅ 数据包版本已创建: {packet_id} v{version.version_number}")
        return version


    async def rollback_packet(
        self,
        packet_id: str,
        target_version_id: str,
        user_id: int,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        回滚数据包到指定版本

        Args:
            packet_id: 数据包ID
            target_version_id: 目标版本ID
            user_id: 用户ID
            reason: 回滚原因

        Returns:
            回滚结果
        """
        result = self.version_control.rollback(
            resource_id=packet_id,
            version_type=VersionType.DATA_PACKET,
            target_version_id=target_version_id,
            rollback_by=user_id,
            reason=reason
        )

        # 恢复数据包状态
        target_version = self.version_control.get_version(target_version_id)
        if target_version and packet_id in self.packets:
            packet = self.packets[packet_id]
            packet.data = target_version.content.get("data", {})
            packet.metadata = target_version.content.get("metadata", {})

        logger.info(f"✅ 数据包已回滚: {packet_id}")
        return result


    def get_packet_versions(
        self,
        packet_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """获取数据包版本历史"""
        return self.version_control.get_version_history(
            resource_id=packet_id,
            version_type=VersionType.DATA_PACKET,
            limit=limit
        )


    # ==================== 故障恢复 ====================

    async def execute_with_recovery(
        self,
        func,
        service_name: str,
        operation: str,
        *args,
        **kwargs
    ) -> Any:
        """
        使用故障恢复机制执行函数

        包含：
        - 断路器保护
        - 自动重试
        - 故障记录

        Args:
            func: 要执行的函数
            service_name: 服务名称
            operation: 操作名称
            *args, **kwargs: 函数参数

        Returns:
            函数返回值
        """
        # 获取断路器
        circuit_breaker = self.failure_recovery.get_circuit_breaker(service_name)

        try:
            # 通过断路器和重试机制执行
            result = await circuit_breaker.call(
                lambda: retry_with_backoff(
                    func,
                    RetryConfig(max_attempts=3),
                    *args,
                    **kwargs
                )
            )

            return result

        except Exception as e:
            # 记录故障
            from app.core.governance.failure_recovery import FailureType

            await self.failure_recovery.record_failure(
                service_name=service_name,
                operation=operation,
                failure_type=FailureType.EXCEPTION,
                error_message=str(e),
                project_id=kwargs.get("project_id")
            )

            logger.error(f"❌ 执行失败: {service_name}.{operation} - {e}")
            raise


    def get_failure_statistics(
        self,
        service_name: Optional[str] = None,
        time_range_hours: int = 24
    ) -> Dict[str, Any]:
        """获取故障统计"""
        return self.failure_recovery.get_failure_statistics(
            service_name=service_name,
            time_range_hours=time_range_hours
        )


    def get_circuit_breaker_status(self) -> List[Dict[str, Any]]:
        """获取所有断路器状态"""
        return self.failure_recovery.get_circuit_breaker_status()


    # ==================== 合规性检查 ====================

    async def check_compliance(
        self,
        compliance_type: ComplianceType,
        data: Dict[str, Any],
        project_id: Optional[int] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> Any:
        """
        执行合规检查

        Args:
            compliance_type: 合规类型
            data: 待检查数据
            project_id: 项目ID
            resource_type: 资源类型
            resource_id: 资源ID
            user_id: 用户ID

        Returns:
            ComplianceCheck 对象
        """
        check_result = self.compliance_service.run_compliance_check(
            compliance_type=compliance_type,
            data=data,
            project_id=project_id,
            resource_type=resource_type,
            resource_id=resource_id,
            checked_by=user_id
        )

        # 如果不合规，记录警告
        if check_result.status == ComplianceStatus.NON_COMPLIANT.value:
            logger.warning(
                f"⚠️ 合规检查失败: {compliance_type.value} - "
                f"{check_result.violations_count} 个违规"
            )

        return check_result


    async def execute_governed_stage_with_compliance(
        self,
        packet_id: str,
        stage_name: str,
        db: Session,
        user_id: Optional[int] = None,
        compliance_checks: Optional[List[ComplianceType]] = None
    ) -> Dict[str, Any]:
        """
        执行治理化阶段（包含合规检查）

        Args:
            packet_id: 数据包ID
            stage_name: 阶段名称
            db: 数据库会话
            user_id: 用户ID
            compliance_checks: 要执行的合规检查列表

        Returns:
            执行结果
        """
        packet = self.packets.get(packet_id)
        if not packet:
            raise ValueError(f"数据包不存在: {packet_id}")

        # 1. 执行合规检查（如果指定）
        if compliance_checks:
            for compliance_type in compliance_checks:
                check_result = await self.check_compliance(
                    compliance_type=compliance_type,
                    data=packet.data,
                    project_id=packet.project_id,
                    resource_type="data_packet",
                    resource_id=packet_id,
                    user_id=user_id
                )

                # 如果严重不合规，拒绝执行
                if (check_result.status == ComplianceStatus.NON_COMPLIANT.value and
                    check_result.violations_count > 5):
                    raise ValueError(
                        f"合规检查失败，无法执行: {compliance_type.value}"
                    )

        # 2. 创建版本快照
        await self.create_packet_version(
            packet_id=packet_id,
            user_id=user_id,
            description=f"执行阶段前: {stage_name}"
        )

        # 3. 使用故障恢复机制执行阶段
        try:
            result = await self.execute_with_recovery(
                func=lambda: self.execute_governed_stage(
                    packet_id=packet_id,
                    stage_name=stage_name,
                    db=db,
                    user_id=user_id
                ),
                service_name="hermes",
                operation=stage_name,
                project_id=packet.project_id
            )

            # 4. 创建成功后的版本
            await self.create_packet_version(
                packet_id=packet_id,
                user_id=user_id,
                description=f"执行阶段后: {stage_name}"
            )

            return result

        except Exception as e:
            logger.error(f"❌ 阶段执行失败: {stage_name} - {e}")
            raise


    def get_compliance_report(
        self,
        project_id: Optional[int] = None,
        compliance_type: Optional[ComplianceType] = None,
        time_range_days: int = 30
    ) -> Dict[str, Any]:
        """生成合规报告"""
        return self.compliance_service.get_compliance_report(
            project_id=project_id,
            compliance_type=compliance_type,
            time_range_days=time_range_days
        )


    # ==================== 综合治理报告 ====================

    def get_governance_dashboard(
        self,
        project_id: Optional[int] = None,
        time_range_days: int = 7
    ) -> Dict[str, Any]:
        """
        获取治理仪表板数据

        Returns:
            {
                "audit": {...},
                "compliance": {...},
                "failures": {...},
                "versions": {...},
                "circuit_breakers": [...]
            }
        """
        return {
            "audit": {
                # 从审计服务获取
                "total_operations": 0,  # TODO: 实现
                "failed_operations": 0,
            },
            "compliance": self.get_compliance_report(
                project_id=project_id,
                time_range_days=time_range_days
            ),
            "failures": self.get_failure_statistics(
                time_range_hours=time_range_days * 24
            ),
            "circuit_breakers": self.get_circuit_breaker_status(),
            "configuration": {
                "audit_enabled": self.enable_audit,
                "lineage_enabled": self.enable_lineage,
                "permission_check_enabled": self.enable_permission_check
            }
        }


# ==================== 全局实例 ====================

_enterprise_hermes_instance: Optional[EnterpriseGovernedHermes] = None


def get_enterprise_hermes(
    db: Session,
    encryption_key: Optional[str] = None
) -> EnterpriseGovernedHermes:
    """获取企业级 Hermes 实例"""
    global _enterprise_hermes_instance

    if _enterprise_hermes_instance is None:
        _enterprise_hermes_instance = EnterpriseGovernedHermes(db, encryption_key)

    return _enterprise_hermes_instance


# ==================== 初始化函数 ====================

def initialize_enterprise_governance(
    db: Session,
    admin_user_id: Optional[int] = None
) -> EnterpriseGovernedHermes:
    """
    初始化企业级治理系统

    Args:
        db: 数据库会话
        admin_user_id: 管理员用户ID

    Returns:
        EnterpriseGovernedHermes 实例
    """
    hermes = get_enterprise_hermes(db)

    # 初始化默认配置
    ConfigurationTemplate.initialize_defaults(
        hermes.config_manager,
        user_id=admin_user_id
    )

    logger.info("🏢 企业级治理系统已初始化")

    return hermes
