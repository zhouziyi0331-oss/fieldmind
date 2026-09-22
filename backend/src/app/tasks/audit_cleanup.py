"""审计日志定时清理任务

定期清理过期的审计日志记录
"""
import asyncio
from datetime import datetime, timedelta
from typing import Optional

from app.core.logging import logger
from app.core.database import SessionLocal
from app.services.audit_service import AuditService


class AuditCleanupTask:
    """审计日志清理任务"""

    def __init__(
        self,
        retention_days: int = 90,
        check_interval_hours: int = 24,
        batch_size: int = 1000,
    ):
        """初始化清理任务

        Args:
            retention_days: 日志保留天数
            check_interval_hours: 检查间隔（小时）
            batch_size: 批量删除大小
        """
        self.retention_days = retention_days
        self.check_interval_hours = check_interval_hours
        self.batch_size = batch_size
        self.task: Optional[asyncio.Task] = None
        self.running = False

    async def start(self):
        """启动清理任务"""
        if self.running:
            logger.warning("审计日志清理任务已在运行")
            return

        self.running = True
        self.task = asyncio.create_task(self._run())
        logger.info(
            f"审计日志清理任务已启动 - 保留{self.retention_days}天，"
            f"每{self.check_interval_hours}小时检查一次"
        )

    async def stop(self):
        """停止清理任务"""
        if not self.running:
            return

        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

        logger.info("审计日志清理任务已停止")

    async def _run(self):
        """运行清理循环"""
        while self.running:
            try:
                await self._cleanup()
            except Exception as e:
                logger.error(f"审计日志清理失败: {e}")

            # 等待下次检查
            await asyncio.sleep(self.check_interval_hours * 3600)

    async def _cleanup(self):
        """执行清理操作"""
        logger.info("开始清理过期审计日志...")

        db = SessionLocal()

        try:
            deleted_count = await AuditService.cleanup_old_logs(
                db=db,
                retention_days=self.retention_days,
                batch_size=self.batch_size,
            )

            if deleted_count > 0:
                logger.info(f"✅ 清理完成，删除了 {deleted_count} 条过期审计日志")
            else:
                logger.info("✅ 清理完成，没有需要删除的日志")

        except Exception as e:
            logger.error(f"清理审计日志时发生错误: {e}")
            raise
        finally:
            db.close()

    async def cleanup_now(self) -> int:
        """立即执行一次清理

        Returns:
            删除的记录数
        """
        logger.info("手动触发审计日志清理...")

        db = SessionLocal()

        try:
            deleted_count = await AuditService.cleanup_old_logs(
                db=db,
                retention_days=self.retention_days,
                batch_size=self.batch_size,
            )

            logger.info(f"✅ 手动清理完成，删除了 {deleted_count} 条过期审计日志")
            return deleted_count

        finally:
            db.close()


# 全局实例
audit_cleanup_task = AuditCleanupTask(
    retention_days=90,  # 保留90天
    check_interval_hours=24,  # 每天检查一次
    batch_size=1000,
)
