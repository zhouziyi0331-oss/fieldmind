"""
RAG 检索与排序服务 - 严格三阶段流水线

核心原则：
1. 禁止盲目扩容 top_k
2. 严格解耦：过滤 → 召回 → 重排
3. 物理隔离不同阶段的逻辑和模型

数据流：
用户问题 → 条件提取（过滤） → 向量检索（召回） → 重排模型（精排） → 最终结果
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)


@dataclass
class FilterCondition:
    """过滤条件"""
    field: str          # 字段名（如 "date", "model", "product_line"）
    operator: str       # 操作符（"=", "in", ">", "<", "between"）
    value: Any          # 值
    is_required: bool = True  # 是否硬性要求


@dataclass
class RetrievalResult:
    """检索结果"""
    chunk_id: str
    text: str
    score: float        # 向量相似度分数
    metadata: Dict[str, Any]
    rerank_score: Optional[float] = None  # 重排分数


class RAGRetrievalService:
    """RAG 检索与排序服务 - 三阶段流水线"""

    def __init__(self,
        vector_store,           # 向量存储（ChromaDB/Lance）
        reranker=None,          # 重排模型
        recall_multiplier: float = 2.0,  # 召回倍数（召回数 = top_k * multiplier）
        min_filter_score: float = 0.0,   # 过滤最低分数
        min_rerank_score: float = 0.0,   # 重排最低分数
        use_workflow_engine: bool = True):
        """
        初始化 RAG 检索服务

        Args:
            vector_store: 向量存储服务
            reranker: 重排模型（可选）
            recall_multiplier: 召回倍数（建议2-3倍）
            min_filter_score: 过滤最低分数阈值
            min_rerank_score: 重排最低分数阈值
        """
        self.vector_store = vector_store
        self.reranker = reranker
        self.recall_multiplier = recall_multiplier
        self.min_filter_score = min_filter_score
        self.min_rerank_score = min_rerank_score

        logger.info(f"✅ RAG 检索服务初始化")
        logger.info(f"   召回倍数: {recall_multiplier}")
        logger.info(f"   重排模型: {'已启用' if reranker else '未启用'}")

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[List[FilterCondition]] = None,
        collection_name: str = "documents",
        enable_rerank: bool = True
    ) -> Tuple[List[RetrievalResult], Dict[str, Any]]:
        """
        执行 RAG 检索（三阶段流水线）

        Args:
            query: 用户查询
            top_k: 最终返回数量（座位数）
            filters: 过滤条件列表
            collection_name: 集合名称
            enable_rerank: 是否启用重排

        Returns:
            (results, stats)
            - results: 排序后的检索结果
            - stats: 统计信息
        """
        stats = {
            "query": query,
            "top_k": top_k,
            "stages": {}
        }

        logger.info(f"🔍 开始 RAG 检索")
        logger.info(f"   查询: {query[:50]}...")
        logger.info(f"   top_k: {top_k}")

        # ========== 阶段1: 前置过滤 ==========
        logger.info(f"\n📍 阶段1: 前置过滤（Pre-filtering）")

        filter_dict = self._build_filter_dict(filters) if filters else None

        if filter_dict:
            logger.info(f"   过滤条件: {json.dumps(filter_dict, ensure_ascii=False)}")
            stats["stages"]["filter"] = {
                "conditions": filter_dict,
                "applied": True
            }
        else:
            logger.info(f"   无过滤条件，跳过")
            stats["stages"]["filter"] = {"applied": False}

        # ========== 阶段2: 多路召回 ==========
        logger.info(f"\n📍 阶段2: 多路召回（Recall）")

        # 计算召回数量（top_k 的倍数）
        recall_n = int(top_k * self.recall_multiplier)
        logger.info(f"   召回数量: {recall_n} (top_k={top_k} × {self.recall_multiplier})")

        # 向量检索
        recall_results = self._vector_search(
            query=query,
            top_k=recall_n,
            filter_dict=filter_dict,
            collection_name=collection_name
        )

        logger.info(f"   ✅ 召回 {len(recall_results)} 个候选")

        stats["stages"]["recall"] = {
            "target_n": recall_n,
            "actual_n": len(recall_results),
            "avg_score": sum(r.score for r in recall_results) / len(recall_results) if recall_results else 0
        }

        # 异常兜底：召回为空
        if len(recall_results) == 0:
            logger.warning(f"⚠️  召回结果为空")

            # 降级策略：去除过滤条件重试
            if filter_dict:
                logger.info(f"   触发降级策略：去除过滤条件重新检索")
                recall_results = self._vector_search(
                    query=query,
                    top_k=recall_n,
                    filter_dict=None,
                    collection_name=collection_name
                )
                logger.info(f"   降级后召回 {len(recall_results)} 个候选")

                stats["stages"]["recall"]["fallback"] = True
                stats["stages"]["recall"]["fallback_n"] = len(recall_results)

            if len(recall_results) == 0:
                logger.error(f"❌ 降级后仍无结果")
                return [], stats

        # ========== 阶段3: 精排重排 ==========
        logger.info(f"\n📍 阶段3: 精排重排（Reranking）")

        if enable_rerank and self.reranker and len(recall_results) > 1:
            logger.info(f"   使用重排模型...")

            # 重排（物理隔离）
            reranked_results = self._rerank(
                query=query,
                candidates=recall_results
            )

            logger.info(f"   ✅ 重排完成")

            # 过滤低分结果
            reranked_results = [
                r for r in reranked_results
                if r.rerank_score >= self.min_rerank_score
            ]

            logger.info(f"   过滤后剩余 {len(reranked_results)} 个")

            # 截取 top_k
            final_results = reranked_results[:top_k]

            stats["stages"]["rerank"] = {
                "enabled": True,
                "input_n": len(recall_results),
                "output_n": len(reranked_results),
                "final_n": len(final_results),
                "avg_rerank_score": sum(r.rerank_score for r in final_results) / len(final_results) if final_results else 0
            }

        else:
            logger.info(f"   跳过重排（未启用或候选<2）")

            # 直接使用召回结果
            final_results = recall_results[:top_k]

            stats["stages"]["rerank"] = {"enabled": False}

        logger.info(f"\n✅ RAG 检索完成")
        logger.info(f"   最终返回: {len(final_results)} 个结果")

        return final_results, stats

    def _build_filter_dict(
        self,
        filters: List[FilterCondition]
    ) -> Dict[str, Any]:
        """
        构建过滤字典

        将 FilterCondition 列表转换为向量存储可用的过滤字典
        """
        filter_dict = {}

        for condition in filters:
            if condition.operator == "=":
                filter_dict[condition.field] = condition.value
            elif condition.operator == "in":
                filter_dict[condition.field] = {"$in": condition.value}
            elif condition.operator == ">":
                filter_dict[condition.field] = {"$gt": condition.value}
            elif condition.operator == "<":
                filter_dict[condition.field] = {"$lt": condition.value}
            elif condition.operator == "between":
                filter_dict[condition.field] = {
                    "$gte": condition.value[0],
                    "$lte": condition.value[1]
                }

        return filter_dict

    def _vector_search(
        self,
        query: str,
        top_k: int,
        filter_dict: Optional[Dict[str, Any]],
        collection_name: str
    ) -> List[RetrievalResult]:
        """
        向量检索（召回阶段）

        Args:
            query: 查询文本
            top_k: 召回数量
            filter_dict: 过滤条件
            collection_name: 集合名称

        Returns:
            召回的结果列表
        """
        try:
            # 调用向量存储的检索接口
            # 这里需要适配你的向量存储（ChromaDB/Lance/Milvus）
            results = self.vector_store.search(
                query=query,
                top_k=top_k,
                filter=filter_dict,
                collection=collection_name
            )

            # 转换为标准格式
            return [
                RetrievalResult(
                    chunk_id=r.get("id", ""),
                    text=r.get("text", ""),
                    score=r.get("score", 0.0),
                    metadata=r.get("metadata", {})
                )
                for r in results
            ]

        except Exception as e:
            logger.error(f"❌ 向量检索失败: {e}")
            return []

    def _rerank(
        self,
        query: str,
        candidates: List[RetrievalResult]
    ) -> List[RetrievalResult]:
        """
        重排（精排阶段）

        物理隔离的重排模型，独立评分

        Args:
            query: 查询文本
            candidates: 候选结果

        Returns:
            重排后的结果（按 rerank_score 降序）
        """
        try:
            # 准备输入
            texts = [c.text for c in candidates]

            # 调用重排模型
            # 注意：重排分数与向量相似度分数是独立的
            rerank_scores = self.reranker.predict(query, texts)

            # 填充重排分数
            for i, candidate in enumerate(candidates):
                candidate.rerank_score = rerank_scores[i]

            # 按重排分数降序排序
            candidates.sort(key=lambda x: x.rerank_score, reverse=True)

            return candidates

        except Exception as e:
            logger.error(f"❌ 重排失败: {e}")
            # 降级：使用原始召回顺序
            return candidates

    def extract_filters_from_query(
        self,
        query: str
    ) -> List[FilterCondition]:
        """
        从用户查询中提取过滤条件

        这是一个关键的 NLP 任务，可以使用：
        1. 规则匹配（正则表达式）
        2. NER（命名实体识别）
        3. LLM（让大模型提取）

        Args:
            query: 用户查询

        Returns:
            提取的过滤条件列表
        """
        filters = []

        # 简单示例：正则匹配
        import re

        # 匹配年份
        year_match = re.search(r'(\d{4})年', query)
        if year_match:
            year = year_match.group(1)
            filters.append(FilterCondition(
                field="year",
                operator="=",
                value=year
            ))

        # 匹配型号
        model_match = re.search(r'([A-Z]\d+)型', query)
        if model_match:
            model = model_match.group(1)
            filters.append(FilterCondition(
                field="model",
                operator="=",
                value=model
            ))

        # TODO: 更复杂的提取逻辑
        # - 使用 NER 模型
        # - 使用 LLM 结构化提取

        return filters






        # WorkflowEngine 集成


        self.use_workflow_engine = use_workflow_engine


        if use_workflow_engine:


            from app.services.workflow_engine import WorkflowEngine


            self.workflow_engine = WorkflowEngine(max_workers=4)

# 全局单例
_rag_service = None


def get_rag_service(
    vector_store,
    reranker=None
) -> RAGRetrievalService:
    """获取 RAG 检索服务单例"""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGRetrievalService(
            vector_store=vector_store,
            reranker=reranker
        )
    return _rag_service


if __name__ == "__main__":
    print("=" * 80)
    print("🧪 RAG 检索与排序服务")
    print("=" * 80)

    print("\n使用示例:")
    print("""
# 1. 初始化服务
from app.services.rag_retrieval import get_rag_service

service = get_rag_service(
    vector_store=chroma_client,
    reranker=rerank_model
)

# 2. 执行检索
results, stats = service.retrieve(
    query="2025年的A型号产品参数",
    top_k=5
)

# 3. 查看结果
for r in results:
    print(f"文本: {r.text}")
    print(f"向量分数: {r.score}")
    print(f"重排分数: {r.rerank_score}")
    """)
