"""审计日志定时清理任务

自动清理过期的审计日志
"""
import asyncio
from datetime import datetime, timedelta

from app.core.database import SessionLocal
from app.services.audit_service import AuditService
from app.core.logging import logger


class AuditCleanupTask:
    """审计日志清理任务"""

    def __init__(self, retention_days: int = 15, check_interval_hours: int = 24):
        """初始化清理任务

        Args:
            retention_days: 日志保留天数
            check_interval_hours: 检查间隔（小时）
        """
        self.retention_days = retention_days
        self.check_interval_hours = check_interval_hours
        self.is_running = False
        self._task = None

    async def start(self):
        """启动清理任务"""
        if self.is_running:
            logger.warning("Audit cleanup task is already running")
            return

        self.is_running = True
        self._task = asyncio.create_task(self._run())
        logger.info(
            f"Audit cleanup task started: retention={self.retention_days} days, "
            f"interval={self.check_interval_hours} hours"
        )

    async def stop(self):
        """停止清理任务"""
        if not self.is_running:
            return

        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.info("Audit cleanup task stopped")

    async def _run(self):
        """运行清理任务"""
        while self.is_running:
            try:
                await self._cleanup()
                await asyncio.sleep(self.check_interval_hours * 3600)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in audit cleanup task: {str(e)}")
                await asyncio.sleep(3600)  # 出错后等待1小时再重试

    async def _cleanup(self):
        """执行清理操作"""
        db = SessionLocal()
        try:
            logger.info("Starting audit log cleanup...")

            deleted_count = await AuditService.cleanup_old_logs(
                db=db,
                retention_days=self.retention_days,
                batch_size=1000,
            )

            logger.info(
                f"Audit log cleanup completed: deleted {deleted_count} logs "
                f"older than {self.retention_days} days"
            )

        except Exception as e:
            logger.error(f"Failed to cleanup audit logs: {str(e)}")
            raise

        finally:
            db.close()

    async def cleanup_now(self):
        """立即执行一次清理"""
        db = SessionLocal()
        try:
            deleted_count = await AuditService.cleanup_old_logs(
                db=db,
                retention_days=self.retention_days,
                batch_size=1000,
            )

            logger.info(f"Manual audit log cleanup: deleted {deleted_count} logs")
            return deleted_count

        finally:
            db.close()


# 全局清理任务实例
audit_cleanup_task = AuditCleanupTask(retention_days=15, check_interval_hours=24)
