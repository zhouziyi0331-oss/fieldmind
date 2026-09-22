"""定时任务调度服务"""
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
try:
    from croniter import croniter
except ImportError:
    croniter = None
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.models.scheduled_task import ScheduledTask, ScheduledTaskExecution
from app.services.scheduler_executor import SchedulerExecutor
from app.schemas.scheduler import validate_cron_expression
import logging

logger = logging.getLogger(__name__)


class SchedulerService:
    """定时任务调度服务"""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.executor = SchedulerExecutor()

    @staticmethod
    def _next_run(cron_expression: str) -> Optional[datetime]:
        """计算下次运行时间；缺少 croniter 时交给 APScheduler 运行并保留空值。"""
        if croniter is None:
            logger.warning("croniter未安装，定时任务仍可由APScheduler执行，但不预计算next_run_at")
            return None
        return croniter(cron_expression, datetime.utcnow()).get_next(datetime)

    def start(self):
        """启动调度器"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("定时任务调度器已启动")

    def shutdown(self):
        """关闭调度器"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("定时任务调度器已关闭")

    @staticmethod
    def create_task(
        db: Session,
        project_id: Optional[int],
        name: str,
        description: Optional[str],
        task_type: str,
        cron_expression: str,
        config: Dict[str, Any],
        is_active: bool = True,
        created_by: Optional[int] = None
    ) -> ScheduledTask:
        """创建定时任务"""
        task_id = str(uuid.uuid4())

        # 计算下次运行时间
        next_run_at = None
        if is_active:
            validate_cron_expression(cron_expression)
            next_run_at = SchedulerService._next_run(cron_expression)

        task = ScheduledTask(
            task_id=task_id,
            project_id=project_id,
            name=name,
            description=description,
            task_type=task_type,
            cron_expression=cron_expression,
            is_active=is_active,
            config=config,
            next_run_at=next_run_at,
            created_by=created_by
        )

        db.add(task)
        db.commit()
        db.refresh(task)

        logger.info(f"创建定时任务: {task.name} (ID: {task.task_id})")
        return task

    def add_job_to_scheduler(self, task: ScheduledTask, db_factory):
        """将任务添加到调度器"""
        if not task.is_active:
            return

        try:
            # 解析cron表达式
            parts = task.cron_expression.split()
            if len(parts) != 5:
                raise ValueError("Cron表达式必须是5个字段")

            minute, hour, day, month, day_of_week = parts

            trigger = CronTrigger(
                minute=minute,
                hour=hour,
                day=day,
                month=month,
                day_of_week=day_of_week
            )

            self.scheduler.add_job(
                func=self.executor.execute_task,
                trigger=trigger,
                args=[task.id, db_factory],
                id=task.task_id,
                replace_existing=True,
                name=task.name
            )

            logger.info(f"任务已添加到调度器: {task.name} (cron: {task.cron_expression})")
        except Exception as e:
            logger.error(f"添加任务到调度器失败: {task.name}, 错误: {str(e)}")
            raise

    def remove_job_from_scheduler(self, task_id: str):
        """从调度器中移除任务"""
        try:
            self.scheduler.remove_job(task_id)
            logger.info(f"任务已从调度器移除: {task_id}")
        except Exception as e:
            logger.warning(f"移除任务失败: {task_id}, 错误: {str(e)}")

    @staticmethod
    def get_task(db: Session, task_id: str) -> Optional[ScheduledTask]:
        """获取任务详情"""
        return db.query(ScheduledTask).filter(ScheduledTask.task_id == task_id).first()

    @staticmethod
    def get_task_by_id(db: Session, id: int) -> Optional[ScheduledTask]:
        """通过数据库ID获取任务"""
        return db.query(ScheduledTask).filter(ScheduledTask.id == id).first()

    def update_task(
        self,
        db: Session,
        task_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        cron_expression: Optional[str] = None,
        is_active: Optional[bool] = None,
        config: Optional[Dict[str, Any]] = None,
        db_factory = None
    ) -> Optional[ScheduledTask]:
        """更新任务"""
        task = self.get_task(db, task_id)
        if not task:
            return None

        # 记录是否需要重新调度
        need_reschedule = False

        if name is not None:
            task.name = name
        if description is not None:
            task.description = description
        if config is not None:
            task.config = config

        if cron_expression is not None and cron_expression != task.cron_expression:
            task.cron_expression = cron_expression
            need_reschedule = True

        if is_active is not None and is_active != task.is_active:
            task.is_active = is_active
            need_reschedule = True

        # 更新下次运行时间
        if task.is_active:
            validate_cron_expression(task.cron_expression)
            task.next_run_at = SchedulerService._next_run(task.cron_expression)
        else:
            task.next_run_at = None

        task.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(task)

        # 重新调度任务
        if need_reschedule and db_factory:
            self.remove_job_from_scheduler(task.task_id)
            if task.is_active:
                self.add_job_to_scheduler(task, db_factory)

        logger.info(f"任务已更新: {task.name}")
        return task

    def delete_task(self, db: Session, task_id: str) -> bool:
        """删除任务"""
        task = self.get_task(db, task_id)
        if not task:
            return False

        # 从调度器移除
        self.remove_job_from_scheduler(task_id)

        # 从数据库删除
        db.delete(task)
        db.commit()

        logger.info(f"任务已删除: {task.name}")
        return True

    @staticmethod
    def list_tasks(
        db: Session,
        project_id: Optional[int] = None,
        task_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[ScheduledTask]:
        """列出任务"""
        query = db.query(ScheduledTask)

        if project_id is not None:
            query = query.filter(ScheduledTask.project_id == project_id)
        if task_type is not None:
            query = query.filter(ScheduledTask.task_type == task_type)
        if is_active is not None:
            query = query.filter(ScheduledTask.is_active == is_active)

        query = query.order_by(ScheduledTask.created_at.desc())
        return query.limit(limit).offset(offset).all()

    @staticmethod
    def count_tasks(
        db: Session,
        project_id: Optional[int] = None,
        task_type: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> int:
        """统计任务数量"""
        query = db.query(ScheduledTask)

        if project_id is not None:
            query = query.filter(ScheduledTask.project_id == project_id)
        if task_type is not None:
            query = query.filter(ScheduledTask.task_type == task_type)
        if is_active is not None:
            query = query.filter(ScheduledTask.is_active == is_active)

        return query.count()

    @staticmethod
    def create_execution(db: Session, task_id: int) -> ScheduledTaskExecution:
        """创建执行记录"""
        execution = ScheduledTaskExecution(
            task_id=task_id,
            status="running"
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)
        return execution

    @staticmethod
    def update_execution(
        db: Session,
        execution_id: int,
        status: str,
        result: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ):
        """更新执行记录"""
        execution = db.query(ScheduledTaskExecution).filter(
            ScheduledTaskExecution.id == execution_id
        ).first()

        if execution:
            execution.status = status
            execution.completed_at = datetime.utcnow()
            if result is not None:
                execution.result = result
            if error_message is not None:
                execution.error_message = error_message
            db.commit()

    @staticmethod
    def get_executions(
        db: Session,
        task_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[ScheduledTaskExecution]:
        """获取执行记录列表"""
        query = db.query(ScheduledTaskExecution)

        if task_id is not None:
            task = db.query(ScheduledTask).filter(ScheduledTask.task_id == task_id).first()
            if task:
                query = query.filter(ScheduledTaskExecution.task_id == task.id)

        if status is not None:
            query = query.filter(ScheduledTaskExecution.status == status)

        query = query.order_by(ScheduledTaskExecution.started_at.desc())
        return query.limit(limit).offset(offset).all()

    @staticmethod
    def count_executions(
        db: Session,
        task_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> int:
        """统计执行记录数量"""
        query = db.query(ScheduledTaskExecution)

        if task_id is not None:
            task = db.query(ScheduledTask).filter(ScheduledTask.task_id == task_id).first()
            if task:
                query = query.filter(ScheduledTaskExecution.task_id == task.id)

        if status is not None:
            query = query.filter(ScheduledTaskExecution.status == status)

        return query.count()

    def load_all_tasks(self, db: Session, db_factory):
        """加载所有活跃任务到调度器"""
        tasks = db.query(ScheduledTask).filter(ScheduledTask.is_active == True).all()
        for task in tasks:
            try:
                self.add_job_to_scheduler(task, db_factory)
            except Exception as e:
                logger.error(f"加载任务失败: {task.name}, 错误: {str(e)}")

        logger.info(f"已加载 {len(tasks)} 个活跃任务到调度器")


# 全局调度器实例
scheduler_service = SchedulerService()
