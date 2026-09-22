"""
RAG系统基础接口和数据结构

定义所有RAG提供者必须实现的统一接口
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class RAGMode(Enum):
    """RAG检索模式"""
    VECTOR = "vector"              # 纯向量检索
    KNOWLEDGE_GRAPH = "knowledge_graph"  # 知识图谱
    LOCAL = "local"                # 局部检索
    GLOBAL = "global"              # 全局检索
    HYBRID = "hybrid"              # 混合模式
    ADAPTIVE = "adaptive"          # 自适应


class QueryType(Enum):
    """查询类型"""
    FACTUAL = "factual"           # 事实查询
    ENTITY = "entity"             # 实体查询
    CONCEPTUAL = "conceptual"     # 概念查询
    ANALYTICAL = "analytical"     # 分析查询
    COMPLEX = "complex"           # 复杂查询


@dataclass
class RAGResult:
    """统一的RAG检索结果"""
    content: str                              # 内容
    score: float                              # 相关度分数 (0-1)
    source: str                               # 来源RAG ('base_rag', 'lightrag', 'graphrag')
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据

    # 可选字段
    document_id: Optional[str] = None         # 文档ID
    chunk_id: Optional[str] = None            # 分块ID
    entities: Optional[List[str]] = None      # 提取的实体
    relations: Optional[List[Dict]] = None    # 关系三元组
    timestamp: Optional[datetime] = None      # 时间戳

    def __post_init__(self):
        """后处理"""
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

        # 确保score在0-1之间
        if self.score < 0:
            self.score = 0.0
        elif self.score > 1:
            self.score = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'content': self.content,
            'score': self.score,
            'source': self.source,
            'metadata': self.metadata,
            'document_id': self.document_id,
            'chunk_id': self.chunk_id,
            'entities': self.entities,
            'relations': self.relations,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


@dataclass
class RAGQuery:
    """RAG查询请求"""
    query: str                                # 查询文本
    mode: RAGMode = RAGMode.VECTOR            # 检索模式
    top_k: int = 5                            # 返回结果数
    project_id: Optional[str] = None          # 项目ID
    filters: Optional[Dict[str, Any]] = None  # 过滤条件
    options: Dict[str, Any] = field(default_factory=dict)  # 额外选项

    def __post_init__(self):
        """验证参数"""
        if self.top_k < 1:
            self.top_k = 1
        elif self.top_k > 100:
            self.top_k = 100


@dataclass
class RAGResponse:
    """RAG查询响应"""
    query: str                                # 原始查询
    results: List[RAGResult]                  # 检索结果
    total_count: int                          # 结果总数
    sources_used: List[str]                   # 使用的RAG源
    processing_time: float                    # 处理时间(秒)
    metadata: Dict[str, Any] = field(default_factory=dict)  # 响应元数据

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'query': self.query,
            'results': [r.to_dict() for r in self.results],
            'total_count': self.total_count,
            'sources_used': self.sources_used,
            'processing_time': processing_time,
            'metadata': self.metadata
        }


class BaseRAGInterface(ABC):
    """RAG提供者基础接口"""

    # 提供者信息
    provider_name: str = "base"
    provider_version: str = "1.0.0"
    supported_modes: List[RAGMode] = [RAGMode.VECTOR]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化RAG提供者

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self._initialized = False

    @abstractmethod
    async def initialize(self) -> bool:
        """
        初始化提供者

        Returns:
            是否成功
        """
        pass

    @abstractmethod
    async def query(
        self,
        rag_query: RAGQuery
    ) -> List[RAGResult]:
        """
        执行检索查询

        Args:
            rag_query: RAG查询请求

        Returns:
            检索结果列表
        """
        pass

    @abstractmethod
    async def ingest(
        self,
        content: str,
        document_id: str,
        project_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        插入文档

        Args:
            content: 文档内容
            document_id: 文档ID
            project_id: 项目ID
            metadata: 元数据

        Returns:
            是否成功
        """
        pass

    @abstractmethod
    async def delete(
        self,
        document_id: str,
        project_id: Optional[str] = None
    ) -> bool:
        """
        删除文档

        Args:
            document_id: 文档ID
            project_id: 项目ID

        Returns:
            是否成功
        """
        pass

    def supports_mode(self, mode: RAGMode) -> bool:
        """检查是否支持指定模式"""
        return mode in self.supported_modes

    def get_provider_info(self) -> Dict[str, Any]:
        """获取提供者信息"""
        return {
            'name': self.provider_name,
            'version': self.provider_version,
            'supported_modes': [m.value for m in self.supported_modes],
            'initialized': self._initialized
        }

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return {
            'provider': self.provider_name,
            'status': 'healthy' if self._initialized else 'not_initialized',
            'timestamp': datetime.utcnow().isoformat()
        }


@dataclass
class RAGProviderConfig:
    """RAG提供者配置"""
    enabled: bool = True
    priority: int = 1  # 优先级，数字越大优先级越高
    weight: float = 1.0  # 结果权重
    timeout: float = 10.0  # 超时时间(秒)
    options: Dict[str, Any] = field(default_factory=dict)


class RAGException(Exception):
    """RAG异常基类"""
    pass


class RAGProviderNotFoundError(RAGException):
    """RAG提供者未找到"""
    pass


class RAGQueryError(RAGException):
    """RAG查询错误"""
    pass


class RAGIngestionError(RAGException):
    """RAG索引错误"""
    pass
