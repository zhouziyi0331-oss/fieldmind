"""
搜索 Agent
提供智能搜索和信息检索功能
"""
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from .base_agent import BaseAgent
from .agent_registry import register_agent

logger = logging.getLogger(__name__)


@register_agent(
    name="search_agent",
    description="智能搜索和信息检索",
    version="1.0.0",
    capabilities=["search", "retrieval", "ranking"],
    dependencies=[]
)
class SearchAgent(BaseAgent):
    """
    搜索 Agent

    功能：
    - 关键词搜索
    - 语义搜索
    - 结果排序
    - 相关性评分
    """

    def __init__(self):
        super().__init__()
        self.name = "SearchAgent"
        logger.info("搜索 Agent 已初始化")

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行搜索

        Args:
            input_data: {
                "query": str,  # 搜索查询
                "documents": List[Dict],  # 文档列表
                "top_k": int,  # 返回前k个结果（默认10）
                "search_type": str  # 搜索类型：keyword/semantic（默认keyword）
            }

        Returns:
            {
                "results": List[Dict],  # 搜索结果
                "total": int,  # 总结果数
                "query": str  # 原始查询
            }
        """
        query = input_data.get("query", "")
        documents = input_data.get("documents", [])
        top_k = input_data.get("top_k", 10)
        search_type = input_data.get("search_type", "keyword")

        if not query:
            return {"results": [], "total": 0, "query": query}

        # 执行搜索
        if search_type == "semantic":
            results = self._semantic_search(query, documents, top_k)
        else:
            results = self._keyword_search(query, documents, top_k)

        return {
            "results": results,
            "total": len(results),
            "query": query,
            "search_type": search_type,
            "searched_at": datetime.now().isoformat()
        }

    def _keyword_search(self, query: str, documents: List[Dict], top_k: int) -> List[Dict]:
        """关键词搜索"""
        results = []
        query_lower = query.lower()

        for doc in documents:
            text = doc.get("text", "").lower()
            score = self._calculate_keyword_score(query_lower, text)

            if score > 0:
                results.append({
                    **doc,
                    "score": score,
                    "matched_query": query
                })

        # 按分数排序
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def _semantic_search(self, query: str, documents: List[Dict], top_k: int) -> List[Dict]:
        """语义搜索（简化版）"""
        # 这里简化处理，实际应该使用向量相似度
        return self._keyword_search(query, documents, top_k)

    def _calculate_keyword_score(self, query: str, text: str) -> float:
        """计算关键词匹配分数"""
        if query in text:
            # 完全匹配
            count = text.count(query)
            return min(count * 2.0, 10.0)

        # 部分匹配
        query_words = query.split()
        score = sum(1.0 for word in query_words if word in text)
        return score

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """验证输入"""
        return "query" in input_data and "documents" in input_data

    def get_capabilities(self) -> List[str]:
        """返回能力"""
        return ["search", "retrieval", "ranking"]
