"""
统一服务层 - FieldMind 工作舱核心服务整合

提供统一的服务接口，整合所有功能模块：
- NLP 服务
- 知识图谱服务
- RAG 服务
- 爬虫服务（占位，待实现）
- 文档处理服务
- 可视化服务（占位，待实现）
- 记忆服务（占位，待实现）
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import logging

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class ServiceStatus(str, Enum):
    """服务状态"""
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    DEGRADED = "degraded"
    INITIALIZING = "initializing"


@dataclass
class ServiceInfo:
    """服务信息"""
    name: str
    status: ServiceStatus
    version: str
    description: str
    capabilities: List[str]


# ==================== NLP 服务 ====================

class UnifiedNLPService:
    """
    统一 NLP 服务

    整合：
    - PaddleNLP UIE（高精度实体识别）✅
    - HanLP（中文 NLP）✅
    - funNLP（待整合）
    """

    def __init__(self):
        self.status = ServiceStatus.AVAILABLE
        self._hanlp = None
        self._paddlenlp = None

        # 初始化 PaddleNLP UIE（优先）
        try:
            from app.services.nlp.paddlenlp_service import get_paddlenlp_service
            self._paddlenlp = get_paddlenlp_service()
            if self._paddlenlp.is_available():
                logger.info("📝 NLP 服务已初始化（PaddleNLP UIE + HanLP）")
            else:
                logger.warning("📝 NLP 服务已初始化（PaddleNLP UIE 不可用）")
        except Exception as e:
            logger.warning(f"PaddleNLP 加载失败: {e}")

        # 初始化 HanLP（备用）
        try:
            from app.services.nlp.hanlp_service import get_hanlp_service
            self._hanlp = get_hanlp_service()
            if not self._paddlenlp and not self._hanlp.is_available():
                logger.warning("📝 NLP 服务已初始化（所有NLP工具不可用，使用基础功能）")
                self.status = ServiceStatus.DEGRADED
        except Exception as e:
            logger.warning(f"📝 NLP 服务已初始化（HanLP 加载失败: {e}）")
            self.status = ServiceStatus.DEGRADED

    def tokenize(self, text: str, language: str = "zh") -> List[str]:
        """
        分词

        Args:
            text: 输入文本
            language: 语言（zh/en）

        Returns:
            分词结果
        """
        if language == "zh" and self._hanlp and self._hanlp.is_available():
            # 使用 HanLP 中文分词
            return self._hanlp.segment(text)

        # 基础分词（降级）
        return text.split()

    def extract_keywords(
        self,
        text: str,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        关键词提取

        Args:
            text: 输入文本
            top_k: 返回前k个关键词

        Returns:
            关键词列表 [{"word": "关键词", "score": 0.95}]
        """
        if self._hanlp and self._hanlp.is_available():
            # 使用 HanLP 关键词提取
            return self._hanlp.extract_keywords(text, top_k)

        # 降级方案
        logger.warning("HanLP 不可用，使用简单关键词提取")
        return []

    def extract_entities(
        self,
        text: str
    ) -> List[Dict[str, Any]]:
        """
        命名实体识别（优先使用 PaddleNLP UIE）

        Args:
            text: 输入文本

        Returns:
            实体列表 [{"text": "实体", "type": "PER", "start": 0, "end": 2}]
        """
        # 优先使用 PaddleNLP UIE（更准确）
        if self._paddlenlp and self._paddlenlp.is_available():
            try:
                return self._paddlenlp.extract_entities(text)
            except Exception as e:
                logger.warning(f"PaddleNLP 实体识别失败，降级到 HanLP: {e}")

        # 降级到 HanLP
        if self._hanlp and self._hanlp.is_available():
            return self._hanlp.recognize_entities(text)

        # 最终降级
        logger.warning("所有 NER 工具不可用")
        return []

    def summarize(
        self,
        text: str,
        max_length: int = 200
    ) -> str:
        """
        文本摘要

        Args:
            text: 输入文本
            max_length: 最大长度

        Returns:
            摘要文本
        """
        if self._hanlp and self._hanlp.is_available():
            # 使用 HanLP 摘要
            return self._hanlp.summarize(text, max_length)

        # 降级方案
        logger.warning("HanLP 不可用，使用简单摘要")
        return text[:max_length] + ("..." if len(text) > max_length else "")

    def sentiment_analysis(self, text: str) -> Dict[str, Any]:
        """
        情感分析

        Args:
            text: 输入文本

        Returns:
            {"sentiment": "positive", "score": 0.85}
        """
        if self._hanlp and self._hanlp.is_available():
            # 使用 HanLP 情感分析
            return self._hanlp.sentiment_analysis(text)

        # 降级方案
        logger.warning("HanLP 不可用，无法进行情感分析")
        return {"sentiment": "neutral", "score": 0.5}

    def get_info(self) -> ServiceInfo:
        """获取服务信息"""
        return ServiceInfo(
            name="NLP Service",
            status=self.status,
            version="1.0.0",
            description="统一自然语言处理服务",
            capabilities=[
                "tokenize",
                "extract_keywords",
                "extract_entities",
                "summarize",
                "sentiment_analysis"
            ]
        )


# ==================== 知识图谱服务 ====================

class UnifiedKGService:
    """
    统一知识图谱服务

    整合：
    - 现有 knowledge_graph ✅
    - GraphRAG ✅
    - Neo4j-KGBuilder ⏳
    """

    def __init__(self, db: Session):
        self.db = db
        self.status = ServiceStatus.AVAILABLE
        self._kg_builder = None

        # 初始化知识图谱构建器
        try:
            from app.services.kg.kg_builder import get_kg_builder
            self._kg_builder = get_kg_builder(db)
            logger.info("🕸️ 知识图谱服务已初始化（GraphRAG 已加载）")
        except Exception as e:
            logger.warning(f"🕸️ 知识图谱服务初始化警告: {e}")
            self.status = ServiceStatus.DEGRADED

    def build_graph_from_documents(
        self,
        document_ids: List[int],
        project_id: int
    ) -> Dict[str, Any]:
        """
        从文档自动构建知识图谱

        Args:
            document_ids: 文档ID列表
            project_id: 项目ID

        Returns:
            构建结果
        """
        if not self._kg_builder:
            logger.warning("知识图谱构建器不可用")
            return {
                "status": "pending",
                "message": "知识图谱构建器未初始化"
            }

        try:
            return self._kg_builder.build_from_documents(
                document_ids=document_ids,
                project_id=project_id,
                use_graphrag=True
            )
        except Exception as e:
            logger.error(f"构建知识图谱失败: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }

    def query_graph(
        self,
        query: str,
        project_id: int,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        查询知识图谱

        Args:
            query: 查询语句或自然语言
            project_id: 项目ID
            limit: 结果数量

        Returns:
            查询结果
        """
        # TODO: 实现图查询
        logger.warning("图查询功能待完善")
        return []

    def find_path(
        self,
        start_entity: str,
        end_entity: str,
        project_id: int,
        max_depth: int = 5
    ) -> List[List[Dict[str, Any]]]:
        """
        查找实体间路径

        Args:
            start_entity: 起始实体
            end_entity: 目标实体
            project_id: 项目ID
            max_depth: 最大深度

        Returns:
            路径列表
        """
        # TODO: 实现路径查找
        logger.warning("路径查找功能待实现")
        return []

    def get_entity_neighbors(
        self,
        entity_id: int,
        project_id: int,
        depth: int = 1
    ) -> Dict[str, Any]:
        """
        获取实体的邻居节点

        Args:
            entity_id: 实体ID
            project_id: 项目ID
            depth: 深度

        Returns:
            邻居信息
        """
        # TODO: 实现邻居查询
        logger.warning("邻居查询功能待实现")
        return {"nodes": [], "edges": []}

    def get_info(self) -> ServiceInfo:
        """获取服务信息"""
        return ServiceInfo(
            name="Knowledge Graph Service",
            status=self.status,
            version="1.0.0",
            description="统一知识图谱服务",
            capabilities=[
                "build_graph",
                "query_graph",
                "find_path",
                "get_neighbors"
            ]
        )


# ==================== RAG 服务 ====================

class UnifiedRAGService:
    """
    统一 RAG 服务

    整合：
    - 现有 rag_engine
    - LightRAG
    - GraphRAG（待整合）
    """

    def __init__(self, db: Session):
        self.db = db
        self.status = ServiceStatus.AVAILABLE

        # 加载 RAG 引擎
        try:
            from app.core.rag.unified_engine import UnifiedRAGEngine
            self.rag_engine = UnifiedRAGEngine()
        except Exception as e:
            logger.warning(f"RAG 引擎加载失败: {e}")
            self.rag_engine = None
            self.status = ServiceStatus.DEGRADED

        logger.info("🔍 RAG 服务已初始化")

    def query(
        self,
        question: str,
        project_id: int,
        top_k: int = 5,
        strategy: str = "auto"
    ) -> Dict[str, Any]:
        """
        RAG 问答

        Args:
            question: 问题
            project_id: 项目ID
            top_k: 检索数量
            strategy: 检索策略（auto/lightrag/graphrag）

        Returns:
            {
                "answer": "答案",
                "contexts": [...],
                "sources": [...]
            }
        """
        if not self.rag_engine:
            return {
                "answer": "RAG 服务不可用",
                "contexts": [],
                "sources": []
            }

        try:
            result = self.rag_engine.query(
                question=question,
                top_k=top_k
            )
            return result
        except Exception as e:
            logger.error(f"RAG 查询失败: {e}")
            return {
                "answer": f"查询失败: {str(e)}",
                "contexts": [],
                "sources": []
            }

    def index_documents(
        self,
        document_ids: List[int],
        project_id: int
    ) -> Dict[str, Any]:
        """
        索引文档

        Args:
            document_ids: 文档ID列表
            project_id: 项目ID

        Returns:
            索引结果
        """
        # TODO: 实现批量索引
        logger.warning("批量索引功能待完善")
        return {
            "indexed": 0,
            "failed": 0
        }

    def get_info(self) -> ServiceInfo:
        """获取服务信息"""
        return ServiceInfo(
            name="RAG Service",
            status=self.status,
            version="1.0.0",
            description="统一检索增强生成服务",
            capabilities=[
                "query",
                "index_documents",
                "multi_strategy"
            ]
        )


# ==================== 文档处理服务 ====================

class UnifiedDocumentService:
    """
    统一文档处理服务

    整合：
    - 现有 document_processor
    - 15 个 ingestion 插件
    """

    def __init__(self, db: Session):
        self.db = db
        self.status = ServiceStatus.AVAILABLE

        logger.info("📄 文档处理服务已初始化")

    def process_file(
        self,
        file_path: str,
        project_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """
        处理文件

        Args:
            file_path: 文件路径
            project_id: 项目ID
            user_id: 用户ID

        Returns:
            处理结果
        """
        # TODO: 调用 document_processor
        logger.warning("文档处理功能待整合")
        return {
            "document_id": None,
            "status": "pending"
        }

    def batch_process(
        self,
        file_paths: List[str],
        project_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """
        批量处理文件

        Args:
            file_paths: 文件路径列表
            project_id: 项目ID
            user_id: 用户ID

        Returns:
            批量处理结果
        """
        # TODO: 实现批量处理
        logger.warning("批量处理功能待实现")
        return {
            "total": len(file_paths),
            "processed": 0,
            "failed": 0
        }

    def get_supported_formats(self) -> List[str]:
        """获取支持的文件格式"""
        return [
            "pdf", "docx", "doc", "xlsx", "xls",
            "pptx", "ppt", "txt", "md", "html",
            "jpg", "jpeg", "png", "mp3", "wav",
            "mp4", "avi", "zip", "tar", "gz"
        ]

    def get_info(self) -> ServiceInfo:
        """获取服务信息"""
        return ServiceInfo(
            name="Document Service",
            status=self.status,
            version="1.0.0",
            description="统一文档处理服务",
            capabilities=[
                "process_file",
                "batch_process",
                "15_formats_support"
            ]
        )


# ==================== 爬虫服务（占位） ====================

class UnifiedCrawlerService:
    """
    统一爬虫服务

    整合：
    - firecrawl（基础爬虫）✅
    - crawl4ai（AI 爬虫）✅
    - browser-use（浏览器自动化）⏳
    """

    def __init__(self):
        self.status = ServiceStatus.AVAILABLE
        self._crawler = None

        # 初始化爬虫服务
        try:
            from app.services.crawler.unified_crawler import get_crawler_service
            self._crawler = get_crawler_service()
            if self._crawler.is_available():
                logger.info("🕷️ 爬虫服务已初始化（已加载爬虫工具）")
            else:
                logger.warning("🕷️ 爬虫服务已初始化（无可用爬虫）")
                self.status = ServiceStatus.UNAVAILABLE
        except Exception as e:
            logger.warning(f"🕷️ 爬虫服务初始化失败: {e}")
            self.status = ServiceStatus.UNAVAILABLE

    def crawl_website(
        self,
        url: str,
        max_depth: int = 2,
        max_pages: int = 100
    ) -> Dict[str, Any]:
        """
        爬取网站

        Args:
            url: 起始URL
            max_depth: 最大深度
            max_pages: 最大页面数

        Returns:
            爬取结果
        """
        if not self._crawler or not self._crawler.is_available():
            raise NotImplementedError("爬虫服务不可用，请安装 firecrawl-py 或 crawl4ai")

        try:
            from app.services.crawler.unified_crawler import CrawlerType

            results = self._crawler.crawl_website(
                url=url,
                max_depth=max_depth,
                max_pages=max_pages,
                crawler_type=CrawlerType.BASIC
            )

            return {
                "url": url,
                "pages": results,
                "total_pages": len(results),
                "status": "success"
            }
        except Exception as e:
            logger.error(f"爬取网站失败: {e}")
            raise

    def crawl_url(
        self,
        url: str,
        use_ai: bool = False
    ) -> Dict[str, Any]:
        """
        爬取单个URL

        Args:
            url: 目标URL
            use_ai: 是否使用AI爬虫

        Returns:
            爬取结果
        """
        if not self._crawler or not self._crawler.is_available():
            raise NotImplementedError("爬虫服务不可用")

        try:
            from app.services.crawler.unified_crawler import CrawlerType

            crawler_type = CrawlerType.AI if use_ai else CrawlerType.BASIC

            return self._crawler.crawl_url(url, crawler_type)
        except Exception as e:
            logger.error(f"爬取URL失败: {e}")
            raise

    def get_info(self) -> ServiceInfo:
        """获取服务信息"""
        return ServiceInfo(
            name="Crawler Service",
            status=self.status,
            version="0.0.0",
            description="统一爬虫服务（待整合）",
            capabilities=[]
        )


# ==================== 记忆服务（占位） ====================

class UnifiedMemoryService:
    """
    统一记忆服务

    整合：
    - mem0（长期记忆）✅
    - 对话历史
    - 用户偏好
    """

    def __init__(self, db: Session):
        self.db = db
        self.status = ServiceStatus.AVAILABLE
        self._mem0 = None

        # 初始化 mem0
        try:
            from app.services.memory.mem0_service import get_mem0_service
            self._mem0 = get_mem0_service(db)
            if self._mem0.is_available():
                logger.info("🧠 记忆服务已初始化（Mem0 已加载）")
            else:
                logger.warning("🧠 记忆服务已初始化（Mem0 不可用）")
                self.status = ServiceStatus.UNAVAILABLE
        except Exception as e:
            logger.warning(f"🧠 记忆服务初始化失败: {e}")
            self.status = ServiceStatus.UNAVAILABLE

    def store_memory(
        self,
        user_id: int,
        content: str,
        context: Dict[str, Any]
    ) -> int:
        """
        存储记忆

        Args:
            user_id: 用户ID
            content: 内容
            context: 上下文

        Returns:
            记忆ID
        """
        if not self._mem0 or not self._mem0.is_available():
            raise NotImplementedError("记忆服务不可用")

        try:
            memory_id = self._mem0.store_memory(
                user_id=user_id,
                content=content,
                context=context
            )
            return memory_id
        except Exception as e:
            logger.error(f"存储记忆失败: {e}")
            raise

    def search_memory(
        self,
        user_id: int,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        搜索记忆

        Args:
            user_id: 用户ID
            query: 查询内容
            limit: 结果数量

        Returns:
            记忆列表
        """
        if not self._mem0 or not self._mem0.is_available():
            return []

        try:
            return self._mem0.search_memory(user_id, query, limit)
        except Exception as e:
            logger.error(f"搜索记忆失败: {e}")
            return []

    def get_conversation_context(
        self,
        user_id: int,
        conversation_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取对话上下文

        Args:
            user_id: 用户ID
            conversation_id: 对话ID
            limit: 上下文条数

        Returns:
            上下文列表
        """
        if not self._mem0 or not self._mem0.is_available():
            return []

        try:
            return self._mem0.get_conversation_context(user_id, conversation_id, limit)
        except Exception as e:
            logger.error(f"获取对话上下文失败: {e}")
            return []

    def get_info(self) -> ServiceInfo:
        """获取服务信息"""
        return ServiceInfo(
            name="Memory Service",
            status=self.status,
            version="0.0.0",
            description="统一记忆服务（待整合）",
            capabilities=[]
        )


# ==================== 可视化服务（占位） ====================

class UnifiedVisualizationService:
    """
    统一可视化服务

    待整合：
    - mind-map（思维导图）
    - nvd3（图表）
    - rawgraphs（数据可视化）
    """

    def __init__(self):
        self.status = ServiceStatus.UNAVAILABLE

        logger.warning("📊 可视化服务待整合")

    def generate_mind_map(
        self,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        生成思维导图

        Args:
            data: 数据

        Returns:
            思维导图数据
        """
        logger.error("可视化服务尚未实现")
        raise NotImplementedError("可视化服务待整合")

    def get_info(self) -> ServiceInfo:
        """获取服务信息"""
        return ServiceInfo(
            name="Visualization Service",
            status=self.status,
            version="0.0.0",
            description="统一可视化服务（待整合）",
            capabilities=[]
        )


# ==================== 工作舱统一服务 ====================

class WorkbenchServices:
    """
    FieldMind 工作舱统一服务

    提供所有服务的统一入口
    """

    def __init__(self, db: Session):
        self.db = db

        # 初始化各服务
        self.nlp = UnifiedNLPService()
        self.knowledge_graph = UnifiedKGService(db)
        self.rag = UnifiedRAGService(db)
        self.document = UnifiedDocumentService(db)
        self.crawler = UnifiedCrawlerService()
        self.memory = UnifiedMemoryService(db)
        self.visualization = UnifiedVisualizationService()

        logger.info("🏢 FieldMind 工作舱服务已初始化")

    def get_all_services_status(self) -> Dict[str, ServiceInfo]:
        """获取所有服务状态"""
        return {
            "nlp": self.nlp.get_info(),
            "knowledge_graph": self.knowledge_graph.get_info(),
            "rag": self.rag.get_info(),
            "document": self.document.get_info(),
            "crawler": self.crawler.get_info(),
            "memory": self.memory.get_info(),
            "visualization": self.visualization.get_info()
        }

    def health_check(self) -> Dict[str, Any]:
        """
        健康检查

        Returns:
            {
                "status": "healthy",
                "services": {...}
            }
        """
        services = self.get_all_services_status()

        available_count = sum(
            1 for s in services.values()
            if s.status == ServiceStatus.AVAILABLE
        )

        total_count = len(services)

        overall_status = "healthy" if available_count == total_count else "degraded"

        return {
            "status": overall_status,
            "available_services": available_count,
            "total_services": total_count,
            "services": {
                name: {
                    "status": info.status.value,
                    "version": info.version
                }
                for name, info in services.items()
            }
        }


# ==================== 全局实例 ====================

_workbench_services: Optional[WorkbenchServices] = None


def get_workbench_services(db: Session) -> WorkbenchServices:
    """获取工作舱服务实例"""
    global _workbench_services

    if _workbench_services is None:
        _workbench_services = WorkbenchServices(db)

    return _workbench_services
