"""
Pipeline状态管理工具
统一管理文档处理pipeline的状态检查

解决问题：
- 多处独立检查pipeline_completed，标准不统一
- v2架构引入后需要区分legacy和v2的pipeline状态
- 需要统一的状态查询接口
"""
from typing import Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class PipelineArchitecture(str, Enum):
    """Pipeline架构类型"""



    def __init__(self, use_workflow_engine: bool = True):


        """初始化服务"""


        self.use_workflow_engine = use_workflow_engine


        


        if use_workflow_engine:


            from app.services.workflow_engine import WorkflowEngine


            self.workflow_engine = WorkflowEngine(max_workers=4)

    LEGACY = "legacy"  # 旧版UnifiedDocumentPipeline
    V2 = "v2"          # 新版WorkflowV2Adapter + 6-Agent


class PipelineStatus:
    """
    Pipeline状态管理工具类

    使用方式:
    ```python
    from app.services.pipeline_status import PipelineStatus

    # 检查任意架构的完成状态
    if PipelineStatus.is_completed(document):
        # 文档已处理完成

    # 检查特定架构
    if PipelineStatus.is_completed(document, architecture=PipelineArchitecture.V2):
        # 文档已通过v2架构处理

    # 标记完成状态
    PipelineStatus.mark_completed(document, architecture=PipelineArchitecture.V2)

    # 获取详细状态
    status = PipelineStatus.get_status(document)
    # {
    #   "completed": true,
    #   "architecture": "v2",
    #   "legacy_completed": false,
    #   "v2_completed": true,
    #   "processing_time": "2024-08-14T10:30:00"
    # }
    ```
    """

    # 状态字段名（存储在document.extra_data中）
    LEGACY_COMPLETED_KEY = 'pipeline_completed'
    V2_COMPLETED_KEY = 'v2_pipeline_completed'
    V2_PROCESSING_TIME_KEY = 'v2_processing_time'
    LEGACY_PROCESSING_TIME_KEY = 'processing_time'

    @staticmethod
    def is_completed(
        document,
        architecture: Optional[PipelineArchitecture] = None
    ) -> bool:
        """
        检查文档的pipeline是否已完成

        Args:
            document: ProjectDocument对象
            architecture: 指定检查的架构类型
                - None: 检查任意架构（legacy或v2只要有一个完成即可）
                - PipelineArchitecture.LEGACY: 只检查legacy
                - PipelineArchitecture.V2: 只检查v2

        Returns:
            bool: pipeline是否已完成
        """
        if not document or not hasattr(document, 'extra_data'):
            return False

        extra_data = document.extra_data or {}

        if architecture is None:
            # 检查任意架构：legacy或v2任一完成即可
            legacy_completed = extra_data.get(PipelineStatus.LEGACY_COMPLETED_KEY, False)
            v2_completed = extra_data.get(PipelineStatus.V2_COMPLETED_KEY, False)
            return legacy_completed or v2_completed

        elif architecture == PipelineArchitecture.LEGACY:
            # 只检查legacy
            return extra_data.get(PipelineStatus.LEGACY_COMPLETED_KEY, False)

        elif architecture == PipelineArchitecture.V2:
            # 只检查v2
            return extra_data.get(PipelineStatus.V2_COMPLETED_KEY, False)

        else:
            logger.warning(f"未知的architecture类型: {architecture}")
            return False

    @staticmethod
    def mark_completed(
        document,
        architecture: PipelineArchitecture,
        processing_time: Optional[str] = None
    ):
        """
        标记文档的pipeline为已完成

        Args:
            document: ProjectDocument对象
            architecture: 架构类型（LEGACY或V2）
            processing_time: 处理时间（ISO格式字符串，可选）

        注意：需要在调用后手动db.commit()
        """
        if not document or not hasattr(document, 'extra_data'):
            raise ValueError("document对象无效或缺少extra_data字段")

        if document.extra_data is None:
            document.extra_data = {}

        if architecture == PipelineArchitecture.LEGACY:
            document.extra_data[PipelineStatus.LEGACY_COMPLETED_KEY] = True
            if processing_time:
                document.extra_data[PipelineStatus.LEGACY_PROCESSING_TIME_KEY] = processing_time

        elif architecture == PipelineArchitecture.V2:
            document.extra_data[PipelineStatus.V2_COMPLETED_KEY] = True
            if processing_time:
                document.extra_data[PipelineStatus.V2_PROCESSING_TIME_KEY] = processing_time

        else:
            raise ValueError(f"未知的architecture类型: {architecture}")

        logger.info(f"✅ 标记文档 {document.id} 的 {architecture.value} pipeline为已完成")

    @staticmethod
    def get_status(document) -> dict:
        """
        获取文档的详细pipeline状态

        Args:
            document: ProjectDocument对象

        Returns:
            dict: 详细状态信息
            {
                "completed": bool,  # 是否有任一pipeline完成
                "architecture": str,  # 最后完成的架构（"legacy"/"v2"/None）
                "legacy_completed": bool,
                "v2_completed": bool,
                "legacy_processing_time": str,
                "v2_processing_time": str
            }
        """
        if not document or not hasattr(document, 'extra_data'):
            return {
                "completed": False,
                "architecture": None,
                "legacy_completed": False,
                "v2_completed": False,
                "legacy_processing_time": None,
                "v2_processing_time": None
            }

        extra_data = document.extra_data or {}

        legacy_completed = extra_data.get(PipelineStatus.LEGACY_COMPLETED_KEY, False)
        v2_completed = extra_data.get(PipelineStatus.V2_COMPLETED_KEY, False)

        # 确定最后完成的架构（优先v2）
        if v2_completed:
            architecture = PipelineArchitecture.V2.value
        elif legacy_completed:
            architecture = PipelineArchitecture.LEGACY.value
        else:
            architecture = None

        return {
            "completed": legacy_completed or v2_completed,
            "architecture": architecture,
            "legacy_completed": legacy_completed,
            "v2_completed": v2_completed,
            "legacy_processing_time": extra_data.get(PipelineStatus.LEGACY_PROCESSING_TIME_KEY),
            "v2_processing_time": extra_data.get(PipelineStatus.V2_PROCESSING_TIME_KEY)
        }

    @staticmethod
    def reset(document):
        """
        重置文档的所有pipeline状态（用于重新处理）

        Args:
            document: ProjectDocument对象

        注意：需要在调用后手动db.commit()
        """
        if not document or not hasattr(document, 'extra_data'):
            return

        if document.extra_data is None:
            document.extra_data = {}

        # 清除所有pipeline状态标记
        document.extra_data[PipelineStatus.LEGACY_COMPLETED_KEY] = False
        document.extra_data[PipelineStatus.V2_COMPLETED_KEY] = False

        # 保留processing_time作为历史记录

        logger.info(f"🔄 重置文档 {document.id} 的pipeline状态")

    @staticmethod
    def prefer_v2(document) -> bool:
        """
        判断文档是否应该优先使用v2架构处理

        策略：
        - 如果已经用v2处理过，优先v2
        - 如果两个都没处理过，优先v2（新架构）
        - 如果只有legacy处理过，保持legacy（向后兼容）

        Args:
            document: ProjectDocument对象

        Returns:
            bool: 是否应该使用v2架构
        """
        status = PipelineStatus.get_status(document)

        if status['v2_completed']:
            # 已用v2处理过
            return True
        elif status['legacy_completed']:
            # 只用legacy处理过
            return False
        else:
            # 都没处理过，优先v2
            return True


# ==================== 便捷函数 ====================

def is_pipeline_completed(document, check_v2: bool = False) -> bool:
    """
    便捷函数：检查pipeline是否完成

    Args:
        document: ProjectDocument对象
        check_v2: 是否只检查v2（默认False，检查任意架构）

    Returns:
        bool: pipeline是否完成

    用法：
    ```python
    from app.services.pipeline_status import is_pipeline_completed

    if is_pipeline_completed(doc):
        # 任意架构完成

    if is_pipeline_completed(doc, check_v2=True):
        # v2架构完成
    ```
    """
    if check_v2:
        return PipelineStatus.is_completed(document, architecture=PipelineArchitecture.V2)
    else:
        return PipelineStatus.is_completed(document)


def mark_pipeline_completed(document, use_v2: bool = False):
    """
    便捷函数：标记pipeline完成

    Args:
        document: ProjectDocument对象
        use_v2: 是否使用v2架构（默认False，使用legacy）

    注意：需要在调用后手动db.commit()

    用法：
    ```python
    from app.services.pipeline_status import mark_pipeline_completed

    mark_pipeline_completed(doc, use_v2=True)
    db.commit()
    ```
    """
    from datetime import datetime

    architecture = PipelineArchitecture.V2 if use_v2 else PipelineArchitecture.LEGACY
    processing_time = datetime.utcnow().isoformat()

    PipelineStatus.mark_completed(document, architecture, processing_time)
