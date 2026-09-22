"""
RAG智能路由器

根据查询类型自动选择最佳RAG提供者
"""
import logging
from typing import List, Dict, Any, Optional
from enum import Enum

from app.core.rag.base_interface import (
    RAGMode, QueryType, RAGQuery
)

logger = logging.getLogger(__name__)


class RoutingStrategy(Enum):
    """路由策略"""
    SINGLE = "single"          # 单一提供者
    PARALLEL = "parallel"      # 并行多提供者
    CASCADE = "cascade"        # 级联（失败时尝试下一个）
    ADAPTIVE = "adaptive"      # 自适应


class RAGRouter:
    """RAG智能路由器"""

    def __init__(self):
        """初始化路由器"""
        # 查询模式关键词
        self.mode_keywords = {
            'factual': ['什么', '哪个', 'what', 'which', 'who', 'when', 'where'],
            'entity': ['关于', '有关', '的', 'about', 'regarding'],
            'conceptual': ['为什么', '如何', '解释', 'why', 'how', 'explain'],
            'analytical': ['分析', '比较', '评估', 'analyze', 'compare', 'evaluate'],
            'complex': ['综合', '全面', '深入', 'comprehensive', 'in-depth']
        }

        # 提供者优先级配置
        self.provider_preferences = {
            QueryType.FACTUAL: ['base_rag', 'lightrag'],
            QueryType.ENTITY: ['lightrag', 'graphrag'],
            QueryType.CONCEPTUAL: ['lightrag', 'graphrag'],
            QueryType.ANALYTICAL: ['graphrag', 'lightrag'],
            QueryType.COMPLEX: ['graphrag', 'lightrag', 'base_rag']
        }

        # 模式到提供者的映射
        self.mode_to_providers = {
            RAGMode.VECTOR: ['base_rag', 'lightrag'],
            RAGMode.KNOWLEDGE_GRAPH: ['lightrag', 'graphrag'],
            RAGMode.LOCAL: ['lightrag', 'graphrag'],
            RAGMode.GLOBAL: ['lightrag', 'graphrag'],
            RAGMode.HYBRID: ['lightrag', 'graphrag', 'base_rag'],
            RAGMode.ADAPTIVE: ['lightrag', 'graphrag', 'base_rag']
        }

        logger.info("✅ RAG路由器初始化")

    def analyze_query(self, query: str) -> QueryType:
        """
        分析查询类型

        Args:
            query: 查询文本

        Returns:
            查询类型
        """
        query_lower = query.lower()

        # 计算每种类型的得分
        scores = {
            QueryType.FACTUAL: 0,
            QueryType.ENTITY: 0,
            QueryType.CONCEPTUAL: 0,
            QueryType.ANALYTICAL: 0,
            QueryType.COMPLEX: 0
        }

        # 根据关键词计算分数
        for query_type_str, keywords in self.mode_keywords.items():
            for keyword in keywords:
                if keyword in query_lower:
                    query_type = QueryType(query_type_str)
                    scores[query_type] += 1

        # 根据查询长度调整
        if len(query) > 100:
            scores[QueryType.COMPLEX] += 2
            scores[QueryType.ANALYTICAL] += 1
        elif len(query) < 20:
            scores[QueryType.FACTUAL] += 1

        # 问号数量
        question_marks = query.count('?') + query.count('？')
        if question_marks > 1:
            scores[QueryType.COMPLEX] += 1

        # 返回得分最高的类型
        max_score = max(scores.values())
        if max_score == 0:
            return QueryType.FACTUAL  # 默认

        for query_type, score in scores.items():
            if score == max_score:
                logger.debug(f"📊 查询类型分析: {query_type.value} (score={score})")
                return query_type

        return QueryType.FACTUAL

    def select_providers(
        self,
        rag_query: RAGQuery,
        available_providers: List[str],
        strategy: RoutingStrategy = RoutingStrategy.ADAPTIVE
    ) -> List[str]:
        """
        选择最佳RAG提供者

        Args:
            rag_query: RAG查询
            available_providers: 可用的提供者列表
            strategy: 路由策略

        Returns:
            选中的提供者列表
        """
        if not available_providers:
            logger.warning("⚠️ 没有可用的RAG提供者")
            return []

        # 1. 如果指定了模式，根据模式选择
        if rag_query.mode != RAGMode.ADAPTIVE:
            preferred = self.mode_to_providers.get(rag_query.mode, [])
            selected = [p for p in preferred if p in available_providers]

            if selected:
                logger.debug(
                    f"🎯 根据模式 {rag_query.mode.value} 选择: {selected}"
                )
                return selected[:2] if strategy == RoutingStrategy.PARALLEL else [selected[0]]

        # 2. 分析查询类型
        query_type = self.analyze_query(rag_query.query)

        # 3. 根据查询类型选择提供者
        preferred = self.provider_preferences.get(query_type, [])
        selected = [p for p in preferred if p in available_providers]

        # 4. 根据策略决定返回多少个提供者
        if strategy == RoutingStrategy.SINGLE:
            result = [selected[0]] if selected else [available_providers[0]]
        elif strategy == RoutingStrategy.PARALLEL:
            # 并行模式：返回前2-3个
            result = selected[:3] if selected else available_providers[:2]
        elif strategy == RoutingStrategy.CASCADE:
            # 级联模式：返回所有推荐的
            result = selected if selected else available_providers
        else:  # ADAPTIVE
            # 自适应：根据查询类型决定
            if query_type == QueryType.COMPLEX:
                # 复杂查询使用多个提供者
                result = selected[:3] if selected else available_providers[:2]
            else:
                # 简单查询使用单个提供者
                result = [selected[0]] if selected else [available_providers[0]]

        logger.debug(
            f"🎯 查询类型 {query_type.value}, "
            f"策略 {strategy.value}, "
            f"选择提供者: {result}"
        )

        return result

    def recommend_mode(
        self,
        query: str,
        provider: str
    ) -> RAGMode:
        """
        为特定提供者推荐最佳检索模式

        Args:
            query: 查询文本
            provider: 提供者名称

        Returns:
            推荐的模式
        """
        query_type = self.analyze_query(query)

        # 根据查询类型和提供者推荐模式
        if provider == 'base_rag':
            return RAGMode.VECTOR

        elif provider == 'lightrag':
            if query_type == QueryType.FACTUAL:
                return RAGMode.VECTOR
            elif query_type == QueryType.ENTITY:
                return RAGMode.LOCAL
            elif query_type == QueryType.CONCEPTUAL:
                return RAGMode.GLOBAL
            elif query_type == QueryType.ANALYTICAL:
                return RAGMode.HYBRID
            else:  # COMPLEX
                return RAGMode.ADAPTIVE

        elif provider == 'graphrag':
            if query_type in [QueryType.FACTUAL, QueryType.ENTITY]:
                return RAGMode.LOCAL
            elif query_type == QueryType.CONCEPTUAL:
                return RAGMode.GLOBAL
            else:  # ANALYTICAL, COMPLEX
                return RAGMode.HYBRID

        return RAGMode.VECTOR

    def should_use_parallel(
        self,
        query: str,
        available_providers: List[str]
    ) -> bool:
        """
        判断是否应该使用并行查询

        Args:
            query: 查询文本
            available_providers: 可用提供者

        Returns:
            是否使用并行
        """
        # 条件1: 有多个提供者
        if len(available_providers) < 2:
            return False

        # 条件2: 查询足够复杂
        query_type = self.analyze_query(query)
        if query_type in [QueryType.COMPLEX, QueryType.ANALYTICAL]:
            return True

        # 条件3: 查询较长
        if len(query) > 50:
            return True

        return False

    def calculate_provider_weight(
        self,
        provider: str,
        query_type: QueryType
    ) -> float:
        """
        计算提供者权重

        Args:
            provider: 提供者名称
            query_type: 查询类型

        Returns:
            权重值 (0-1)
        """
        # 获取该查询类型的推荐提供者列表
        preferred = self.provider_preferences.get(query_type, [])

        if provider not in preferred:
            return 0.5  # 默认权重

        # 根据在推荐列表中的位置计算权重
        index = preferred.index(provider)
        weight = 1.0 - (index * 0.15)  # 第一个1.0，第二个0.85，第三个0.7

        return max(weight, 0.5)

    def get_routing_strategy(
        self,
        query: str,
        available_providers: List[str]
    ) -> RoutingStrategy:
        """
        获取推荐的路由策略

        Args:
            query: 查询文本
            available_providers: 可用提供者

        Returns:
            路由策略
        """
        query_type = self.analyze_query(query)

        # 复杂查询使用并行
        if query_type in [QueryType.COMPLEX, QueryType.ANALYTICAL]:
            if len(available_providers) >= 2:
                return RoutingStrategy.PARALLEL

        # 简单查询使用单一提供者
        if query_type == QueryType.FACTUAL:
            return RoutingStrategy.SINGLE

        # 默认自适应
        return RoutingStrategy.ADAPTIVE

    def get_router_status(self) -> Dict[str, Any]:
        """获取路由器状态"""
        return {
            'query_types': [qt.value for qt in QueryType],
            'routing_strategies': [rs.value for rs in RoutingStrategy],
            'provider_preferences': {
                qt.value: providers
                for qt, providers in self.provider_preferences.items()
            }
        }


# 全局单例
_router_instance = None


def get_rag_router() -> RAGRouter:
    """获取RAG路由器单例"""
    global _router_instance
    if _router_instance is None:
        _router_instance = RAGRouter()
    return _router_instance
