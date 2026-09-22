"""
数据血缘自动追踪装饰器

用于自动记录数据转换和处理过程的血缘关系
"""
from functools import wraps
from typing import Optional, Callable, Any, Dict
from datetime import datetime
import inspect
import asyncio

from app.services.lineage_service import DataLineageService
from app.core.deps import get_db


def track_lineage(
    source_type: str,
    target_type: str,
    operation: str,
    get_source_id: Optional[Callable] = None,
    get_target_id: Optional[Callable] = None,
    get_project_id: Optional[Callable] = None,
    capture_transformation: bool = True,
    get_actor_id: Optional[Callable] = None
):
    """
    数据血缘追踪装饰器

    用法示例：
        @track_lineage(
            source_type="document",
            target_type="analysis",
            operation="extract_entities",
            get_source_id=lambda args, kwargs, result: kwargs.get('document_id'),
            get_target_id=lambda args, kwargs, result: result['analysis_id'],
            get_project_id=lambda args, kwargs, result: kwargs.get('project_id')
        )
        async def extract_entities(document_id: int, project_id: int):
            # ... 实体提取逻辑
            return {"analysis_id": 123, "entities": [...]}

    Args:
        source_type: 源数据类型
        target_type: 目标数据类型
        operation: 操作名称
        get_source_id: 从函数参数/返回值中提取source_id的回调函数
        get_target_id: 从函数参数/返回值中提取target_id的回调函数
        get_project_id: 从函数参数/返回值中提取project_id的回调函数
        capture_transformation: 是否捕获转换参数
        get_actor_id: 从函数参数中提取actor_id的回调函数
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # 执行原函数
            result = await func(*args, **kwargs)

            # 异步记录血缘
            asyncio.create_task(_record_lineage(
                func, args, kwargs, result,
                source_type, target_type, operation,
                get_source_id, get_target_id, get_project_id,
                capture_transformation, get_actor_id
            ))

            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # 执行原函数
            result = func(*args, **kwargs)

            # 异步记录血缘（不阻塞）
            asyncio.create_task(_record_lineage(
                func, args, kwargs, result,
                source_type, target_type, operation,
                get_source_id, get_target_id, get_project_id,
                capture_transformation, get_actor_id
            ))

            return result

        # 根据函数类型返回对应包装器
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


async def _record_lineage(
    func: Callable,
    args: tuple,
    kwargs: dict,
    result: Any,
    source_type: str,
    target_type: str,
    operation: str,
    get_source_id: Optional[Callable],
    get_target_id: Optional[Callable],
    get_project_id: Optional[Callable],
    capture_transformation: bool,
    get_actor_id: Optional[Callable]
):
    """实际记录血缘的内部函数"""
    try:
        # 提取source_id
        source_id = None
        if get_source_id:
            source_id = get_source_id(args, kwargs, result)
        elif 'source_id' in kwargs:
            source_id = kwargs['source_id']
        elif len(args) > 0:
            source_id = str(args[0])

        # 提取target_id
        target_id = None
        if get_target_id:
            target_id = get_target_id(args, kwargs, result)
        elif isinstance(result, dict) and 'id' in result:
            target_id = str(result['id'])
        elif isinstance(result, dict) and 'target_id' in result:
            target_id = str(result['target_id'])

        # 提取project_id
        project_id = None
        if get_project_id:
            project_id = get_project_id(args, kwargs, result)
        elif 'project_id' in kwargs:
            project_id = kwargs['project_id']

        # 提取actor_id
        actor_id = None
        actor_type = "system"
        if get_actor_id:
            actor_id = get_actor_id(args, kwargs, result)
        elif 'user_id' in kwargs:
            actor_id = kwargs['user_id']
            actor_type = "user"
        elif 'current_user' in kwargs:
            user = kwargs['current_user']
            actor_id = getattr(user, 'id', None)
            actor_type = "user"

        # 必须有source_id和target_id才记录
        if not source_id or not target_id:
            return

        # 捕获转换信息
        transformation = None
        if capture_transformation:
            transformation = {
                "function": func.__name__,
                "module": func.__module__,
                "timestamp": datetime.utcnow().isoformat(),
                "parameters": _serialize_parameters(kwargs)
            }

        # 获取数据库会话并记录
        async for db in get_db():
            lineage_service = DataLineageService(db)
            await lineage_service.create_lineage(
                project_id=project_id or 0,
                source_type=source_type,
                source_id=str(source_id),
                target_type=target_type,
                target_id=str(target_id),
                operation=operation,
                transformation=transformation,
                actor_id=actor_id,
                actor_type=actor_type
            )
            break

    except Exception as e:
        # 血缘记录失败不应影响业务逻辑
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"血缘追踪失败: {e}")


def _serialize_parameters(params: dict) -> dict:
    """序列化参数，过滤掉不可序列化的对象"""
    serializable = {}
    for key, value in params.items():
        if key in ['db', 'session', 'current_user']:
            continue  # 跳过数据库会话和用户对象

        try:
            # 尝试序列化
            if isinstance(value, (str, int, float, bool, type(None))):
                serializable[key] = value
            elif isinstance(value, (list, dict)):
                serializable[key] = str(value)[:200]  # 限制长度
            else:
                serializable[key] = str(type(value).__name__)
        except:
            continue

    return serializable


def track_file_processing(
    operation: str,
    get_file_path: Optional[Callable] = None,
    get_output_id: Optional[Callable] = None
):
    """
    文件处理血缘追踪装饰器（特化版本）

    用法示例：
        @track_file_processing(
            operation="parse_pdf",
            get_file_path=lambda args, kwargs, result: kwargs.get('file_path'),
            get_output_id=lambda args, kwargs, result: result['document_id']
        )
        async def parse_pdf(file_path: str, project_id: int):
            # ... PDF解析逻辑
            return {"document_id": 456, "text": "..."}
    """
    return track_lineage(
        source_type="file",
        target_type="document",
        operation=operation,
        get_source_id=get_file_path,
        get_target_id=get_output_id,
        capture_transformation=True
    )


def track_ai_operation(
    operation: str,
    get_input_id: Optional[Callable] = None,
    get_output_id: Optional[Callable] = None,
    capture_prompt: bool = False
):
    """
    AI操作血缘追踪装饰器（特化版本）

    用法示例：
        @track_ai_operation(
            operation="summarize",
            get_input_id=lambda args, kwargs, result: kwargs.get('document_id'),
            get_output_id=lambda args, kwargs, result: result['summary_id'],
            capture_prompt=True
        )
        async def summarize_document(document_id: int, prompt: str):
            # ... AI摘要生成
            return {"summary_id": 789, "summary": "..."}
    """
    def decorator(func):
        lineage_decorator = track_lineage(
            source_type="document",
            target_type="ai_output",
            operation=operation,
            get_source_id=get_input_id,
            get_target_id=get_output_id,
            capture_transformation=capture_prompt
        )
        return lineage_decorator(func)

    return decorator


def track_data_transformation(
    source_type: str,
    target_type: str,
    operation: str
):
    """
    通用数据转换血缘追踪装饰器

    用法示例：
        @track_data_transformation(
            source_type="raw_data",
            target_type="clean_data",
            operation="data_cleaning"
        )
        async def clean_data(source_id: int, project_id: int):
            # ... 数据清洗逻辑
            return {"id": 999, "status": "cleaned"}
    """
    return track_lineage(
        source_type=source_type,
        target_type=target_type,
        operation=operation,
        get_source_id=lambda args, kwargs, result: kwargs.get('source_id'),
        get_target_id=lambda args, kwargs, result: result.get('id') if isinstance(result, dict) else None,
        get_project_id=lambda args, kwargs, result: kwargs.get('project_id'),
        capture_transformation=True
    )


class LineageContext:
    """
    血缘上下文管理器（用于手动记录复杂血缘）

    用法示例：
        async with LineageContext(db, project_id=1) as lineage:
            # 步骤1：提取
            doc_id = await extract_text(file_id)
            await lineage.record("file", file_id, "document", doc_id, "extract")

            # 步骤2：分析
            analysis_id = await analyze_text(doc_id)
            await lineage.record("document", doc_id, "analysis", analysis_id, "analyze")

            # 步骤3：生成报告
            report_id = await generate_report(analysis_id)
            await lineage.record("analysis", analysis_id, "report", report_id, "generate")
    """

    def __init__(self, db, project_id: int, actor_id: Optional[int] = None, actor_type: str = "system"):
        self.db = db
        self.project_id = project_id
        self.actor_id = actor_id
        self.actor_type = actor_type
        self.lineage_service = None

    async def __aenter__(self):
        self.lineage_service = DataLineageService(self.db)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    async def record(
        self,
        source_type: str,
        source_id: str,
        target_type: str,
        target_id: str,
        operation: str,
        transformation: Optional[Dict[str, Any]] = None
    ):
        """记录血缘关系"""
        if self.lineage_service:
            await self.lineage_service.create_lineage(
                project_id=self.project_id,
                source_type=source_type,
                source_id=str(source_id),
                target_type=target_type,
                target_id=str(target_id),
                operation=operation,
                transformation=transformation,
                actor_id=self.actor_id,
                actor_type=self.actor_type
            )
