"""
工作流编排器 - 定义工具间的自动触发和协作逻辑
实现"点一下，下一个自动配套"的核心机制
"""

from typing import Dict, List, Any, Optional, Callable
from enum import Enum
from celery import chain, group, chord
from app.celery_app import celery_app
import logging

logger = logging.getLogger(__name__)


class WorkflowType(Enum):
    """工作流类型"""
    DOCUMENT = "document"
    AUDIO = "audio"
    CRAWLER = "crawler"
    RAG = "rag"
    REPORT = "report"
    KNOWLEDGE_GRAPH = "knowledge_graph"


class WorkflowOrchestrator:
    """工作流编排器 - 管理所有自动化工作流"""

    def __init__(self):
        self.workflows: Dict[WorkflowType, Callable] = {}
        self._register_workflows()

    def _register_workflows(self):
        """注册所有工作流"""
        self.workflows[WorkflowType.DOCUMENT] = self.create_document_workflow
        self.workflows[WorkflowType.AUDIO] = self.create_audio_workflow
        self.workflows[WorkflowType.CRAWLER] = self.create_crawler_workflow
        self.workflows[WorkflowType.RAG] = self.create_rag_workflow
        self.workflows[WorkflowType.REPORT] = self.create_report_workflow

    # ==================== 文档处理工作流 ====================

    def create_document_workflow(self, file_path: str, metadata: Optional[Dict] = None):
        """
        创建文档处理工作流

        流程：上传 → 转换 → [向量化, 实体识别, 全文索引, 存储] → 完成通知
        """
        from app.tasks.document_tasks import (
            convert_to_markdown,
            vectorize_and_store,
            extract_entities,
            fulltext_index,
            save_to_db,
            notify_completion
        )

        workflow = chain(
            # 步骤1：转换为markdown
            convert_to_markdown.s(file_path, metadata or {}),

            # 步骤2：并行处理（4个独立任务）
            chord([
                vectorize_and_store.s(),
                extract_entities.s(),
                fulltext_index.s(),
                save_to_db.s(),
            ])(
                # 步骤3：所有任务完成后通知
                notify_completion.s()
            )
        )

        logger.info(f"创建文档工作流: {file_path}")
        return workflow

    # ==================== 音频处理工作流 ====================

    def create_audio_workflow(self, file_path: str, metadata: Optional[Dict] = None):
        """
        创建音频处理工作流

        流程：上传 → 提取元数据 → 转录 → 文档处理流
        """
        from app.tasks.audio_tasks import (
            extract_audio_metadata,
            transcribe_audio
        )
        from app.tasks.document_tasks import (
            vectorize_and_store,
            extract_entities,
            fulltext_index,
            save_to_db,
            notify_completion
        )

        workflow = chain(
            # 步骤1：提取音频元数据
            extract_audio_metadata.s(file_path, metadata or {}),

            # 步骤2：语音转文字
            transcribe_audio.s(),

            # 步骤3：进入文档处理流（并行）
            chord([
                vectorize_and_store.s(),
                extract_entities.s(),
                fulltext_index.s(),
                save_to_db.s(),
            ])(
                notify_completion.s()
            )
        )

        logger.info(f"创建音频工作流: {file_path}")
        return workflow

    # ==================== 爬虫处理工作流 ====================

    def create_crawler_workflow(
        self,
        url: str,
        crawler_type: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """
        创建爬虫工作流

        流程：URL → 智能选择爬虫 → 爬取 → 内容提取 → 文档处理流
        """
        from app.tasks.crawler_tasks import (
            intelligent_crawl,
            extract_news_content
        )
        from app.tasks.document_tasks import (
            vectorize_and_store,
            extract_entities,
            fulltext_index,
            save_to_db,
            notify_completion
        )

        # 判断是否是新闻URL
        is_news = any(keyword in url.lower() for keyword in [
            'news', 'article', 'xinhua', 'people', 'sina', 'sohu', '新闻'
        ])

        if is_news:
            # 新闻工作流：爬取 → 新闻提取 → 文档处理
            workflow = chain(
                intelligent_crawl.s(url, crawler_type, metadata or {}),
                extract_news_content.s(),
                chord([
                    vectorize_and_store.s(),
                    extract_entities.s(),
                    fulltext_index.s(),
                    save_to_db.s(),
                ])(
                    notify_completion.s()
                )
            )
        else:
            # 普通网页工作流：爬取 → 文档处理
            workflow = chain(
                intelligent_crawl.s(url, crawler_type, metadata or {}),
                chord([
                    vectorize_and_store.s(),
                    extract_entities.s(),
                    fulltext_index.s(),
                    save_to_db.s(),
                ])(
                    notify_completion.s()
                )
            )

        logger.info(f"创建爬虫工作流: {url}")
        return workflow

    # ==================== RAG查询工作流 ====================

    def create_rag_workflow(
        self,
        query: str,
        top_k: int = 5,
        use_llm: bool = True
    ):
        """
        创建RAG查询工作流

        流程：查询 → 实体识别 → [向量检索, 全文检索, 图谱检索, 关键词检索] → RRF融合 → LLM生成
        """
        from app.tasks.rag_tasks import (
            extract_query_entities,
            vector_search,
            fulltext_search,
            graph_search,
            keyword_search,
            reciprocal_rank_fusion,
            generate_answer
        )

        if use_llm:
            # 完整RAG流程
            workflow = chain(
                # 步骤1：提取查询实体
                extract_query_entities.s(query),

                # 步骤2：四路并行检索 + RRF融合
                chord([
                    vector_search.s(query, top_k * 2),
                    fulltext_search.s(query, top_k * 2),
                    graph_search.s(),  # 使用提取的实体
                    keyword_search.s(query, top_k * 2),
                ])(
                    reciprocal_rank_fusion.s(top_k)
                ),

                # 步骤3：LLM生成答案
                generate_answer.s(query)
            )
        else:
            # 仅检索，不生成
            workflow = chain(
                extract_query_entities.s(query),
                chord([
                    vector_search.s(query, top_k * 2),
                    fulltext_search.s(query, top_k * 2),
                    graph_search.s(),
                    keyword_search.s(query, top_k * 2),
                ])(
                    reciprocal_rank_fusion.s(top_k)
                )
            )

        logger.info(f"创建RAG工作流: {query}")
        return workflow

    # ==================== 报告生成工作流 ====================

    def create_report_workflow(
        self,
        title: str,
        time_range: Dict[str, str],
        include_charts: bool = True,
        include_maps: bool = False,
        format_list: List[str] = None
    ):
        """
        创建报告生成工作流

        流程：查询数据 → [图表生成, 地图生成, 词云生成] → 模板渲染 → [Word导出, PDF导出]
        """
        from app.tasks.report_tasks import (
            query_report_data,
            generate_charts,
            generate_maps,
            generate_wordcloud,
            render_report_template,
            export_to_word,
            export_to_pdf
        )

        format_list = format_list or ["word", "pdf"]

        # 构建可视化任务组
        visualization_tasks = []
        if include_charts:
            visualization_tasks.append(generate_charts.s())
        if include_maps:
            visualization_tasks.append(generate_maps.s())
        visualization_tasks.append(generate_wordcloud.s())

        # 构建导出任务组
        export_tasks = []
        if "word" in format_list:
            export_tasks.append(export_to_word.s())
        if "pdf" in format_list:
            export_tasks.append(export_to_pdf.s())

        workflow = chain(
            # 步骤1：查询报告数据
            query_report_data.s(title, time_range),

            # 步骤2：并行生成可视化
            chord(visualization_tasks)(
                # 步骤3：渲染报告模板
                render_report_template.s(title)
            ),

            # 步骤4：并行导出多格式
            group(export_tasks)
        )

        logger.info(f"创建报告工作流: {title}")
        return workflow

    # ==================== 批量处理工作流 ====================

    def create_batch_workflow(
        self,
        items: List[Dict[str, Any]],
        workflow_type: WorkflowType
    ):
        """
        创建批量处理工作流

        Args:
            items: 待处理项目列表
            workflow_type: 工作流类型
        """
        workflow_creator = self.workflows.get(workflow_type)
        if not workflow_creator:
            raise ValueError(f"未知工作流类型: {workflow_type}")

        # 为每个项目创建独立工作流
        workflows = []
        for item in items:
            if workflow_type == WorkflowType.DOCUMENT:
                wf = workflow_creator(item["file_path"], item.get("metadata"))
            elif workflow_type == WorkflowType.AUDIO:
                wf = workflow_creator(item["file_path"], item.get("metadata"))
            elif workflow_type == WorkflowType.CRAWLER:
                wf = workflow_creator(
                    item["url"],
                    item.get("crawler_type"),
                    item.get("metadata")
                )
            else:
                continue
            workflows.append(wf)

        # 并行执行所有工作流
        batch_workflow = group(workflows)
        logger.info(f"创建批量工作流: {len(items)}个项目")
        return batch_workflow

    # ==================== 定时任务工作流 ====================

    def create_scheduled_crawler_workflow(self, urls: List[str]):
        """
        创建定时爬虫工作流（每日更新）

        Args:
            urls: 需要定时爬取的URL列表
        """
        workflows = [
            self.create_crawler_workflow(url)
            for url in urls
        ]
        return group(workflows)

    def create_scheduled_report_workflow(self, report_configs: List[Dict]):
        """
        创建定时报告工作流（每周/月生成）

        Args:
            report_configs: 报告配置列表
        """
        workflows = [
            self.create_report_workflow(
                config["title"],
                config["time_range"],
                config.get("include_charts", True),
                config.get("include_maps", False),
                config.get("format_list", ["word", "pdf"])
            )
            for config in report_configs
        ]
        return group(workflows)

    # ==================== 工作流执行 ====================

    def execute_workflow(
        self,
        workflow_type: WorkflowType,
        **kwargs
    ):
        """
        执行工作流

        Args:
            workflow_type: 工作流类型
            **kwargs: 工作流参数

        Returns:
            AsyncResult: Celery异步结果对象
        """
        workflow_creator = self.workflows.get(workflow_type)
        if not workflow_creator:
            raise ValueError(f"未知工作流类型: {workflow_type}")

        workflow = workflow_creator(**kwargs)
        result = workflow.apply_async()

        logger.info(f"执行工作流 {workflow_type.value}, task_id: {result.id}")
        return result

    def execute_custom_workflow(self, workflow):
        """
        执行自定义工作流

        Args:
            workflow: Celery工作流对象

        Returns:
            AsyncResult: Celery异步结果对象
        """
        result = workflow.apply_async()
        logger.info(f"执行自定义工作流, task_id: {result.id}")
        return result


# ==================== 工作流模板 ====================

class WorkflowTemplates:
    """预定义工作流模板"""

    @staticmethod
    def full_document_pipeline(file_path: str) -> chain:
        """完整文档处理管道"""
        orchestrator = WorkflowOrchestrator()
        return orchestrator.create_document_workflow(file_path)

    @staticmethod
    def full_audio_pipeline(file_path: str) -> chain:
        """完整音频处理管道"""
        orchestrator = WorkflowOrchestrator()
        return orchestrator.create_audio_workflow(file_path)

    @staticmethod
    def news_crawler_pipeline(url: str) -> chain:
        """新闻爬取管道"""
        orchestrator = WorkflowOrchestrator()
        return orchestrator.create_crawler_workflow(url, crawler_type="news")

    @staticmethod
    def government_crawler_pipeline(url: str) -> chain:
        """政府网站爬取管道"""
        orchestrator = WorkflowOrchestrator()
        return orchestrator.create_crawler_workflow(url, crawler_type="gecco")

    @staticmethod
    def intelligent_rag_pipeline(query: str, top_k: int = 5) -> chain:
        """智能RAG查询管道"""
        orchestrator = WorkflowOrchestrator()
        return orchestrator.create_rag_workflow(query, top_k, use_llm=True)

    @staticmethod
    def weekly_report_pipeline(title: str) -> chain:
        """周报生成管道"""
        from datetime import datetime, timedelta

        today = datetime.now()
        week_ago = today - timedelta(days=7)
        time_range = {
            "start": week_ago.strftime("%Y-%m-%d"),
            "end": today.strftime("%Y-%m-%d")
        }

        orchestrator = WorkflowOrchestrator()
        return orchestrator.create_report_workflow(
            title,
            time_range,
            include_charts=True,
            include_maps=True,
            format_list=["word", "pdf"]
        )

    @staticmethod
    def batch_document_processing(file_paths: List[str]) -> group:
        """批量文档处理"""
        orchestrator = WorkflowOrchestrator()
        items = [{"file_path": fp} for fp in file_paths]
        return orchestrator.create_batch_workflow(items, WorkflowType.DOCUMENT)

    @staticmethod
    def batch_url_crawling(urls: List[str]) -> group:
        """批量URL爬取"""
        orchestrator = WorkflowOrchestrator()
        items = [{"url": url} for url in urls]
        return orchestrator.create_batch_workflow(items, WorkflowType.CRAWLER)


# ==================== 工作流触发器 ====================

class WorkflowTrigger:
    """工作流触发器 - 基于事件自动触发工作流"""

    def __init__(self):
        self.orchestrator = WorkflowOrchestrator()
        self.triggers: Dict[str, List[Callable]] = {}

    def register_trigger(self, event: str, workflow_func: Callable):
        """注册触发器"""
        if event not in self.triggers:
            self.triggers[event] = []
        self.triggers[event].append(workflow_func)
        logger.info(f"注册触发器: {event} -> {workflow_func.__name__}")

    def trigger(self, event: str, **kwargs):
        """触发工作流"""
        if event not in self.triggers:
            logger.warning(f"未找到事件触发器: {event}")
            return []

        results = []
        for workflow_func in self.triggers[event]:
            try:
                workflow = workflow_func(**kwargs)
                result = workflow.apply_async()
                results.append(result)
                logger.info(f"触发工作流 {workflow_func.__name__}, task_id: {result.id}")
            except Exception as e:
                logger.error(f"触发工作流失败: {e}")

        return results


# ==================== 全局实例 ====================

# 工作流编排器实例
orchestrator = WorkflowOrchestrator()

# 工作流触发器实例
trigger = WorkflowTrigger()

# 注册默认触发器
trigger.register_trigger(
    "document_uploaded",
    WorkflowTemplates.full_document_pipeline
)
trigger.register_trigger(
    "audio_uploaded",
    WorkflowTemplates.full_audio_pipeline
)
trigger.register_trigger(
    "url_submitted",
    lambda url: WorkflowTemplates.news_crawler_pipeline(url)
    if any(kw in url.lower() for kw in ['news', 'article'])
    else WorkflowTemplates.government_crawler_pipeline(url)
)
