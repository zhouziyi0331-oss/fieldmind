"""
分层检索服务 - 链路17：报告优先级机制

核心功能：
1. 按source_level分层检索（三度报告 > 二度报告 > 一度报告 > 原始材料）
2. 混合排序（层级权重 + 相似度）
3. 智能降级（高层级没结果时，自动降级到低层级）
4. 引用格式区分层级
"""
from typing import List, Dict, Any, Optional
import logging

from app.services.vectorization_service_v2 import get_vectorization_service_v2
from app.schemas.document_metadata import SourceLevel

logger = logging.getLogger(__name__)


class HierarchicalRetriever:
    """分层检索器"""

    def __init__(self):
        self.vectorizer = get_vectorization_service_v2()

        # 层级权重配置（用于混合排序）
        self.level_weights = {
            SourceLevel.REPORT_LEVEL_3: 1.0,    # 三度报告（最高优先级）
            SourceLevel.REPORT_LEVEL_2: 0.7,    # 二度报告
            SourceLevel.REPORT_LEVEL_1: 0.4,    # 一度报告
            SourceLevel.RAW_MATERIAL: 0.1       # 原始材料（最低优先级）
        }

    def retrieve_with_hierarchy(
        self,
        query_text: str,
        n_results: int = 5,
        project_id: Optional[int] = None,
        prefer_reports: bool = True,
        min_level: int = SourceLevel.RAW_MATERIAL,
        date_range: Optional[tuple] = None
    ) -> List[Dict[str, Any]]:
        """
        分层检索（链路17核心功能）

        Args:
            query_text: 查询文本
            n_results: 期望返回数量
            project_id: 项目ID
            prefer_reports: 是否优先报告（True=优先高层级，False=混合）
            min_level: 最低接受层级（0=原始材料，1=一度报告...）
            date_range: 日期范围过滤

        Returns:
            按层级和相似度排序的结果列表

        检索策略：
        1. prefer_reports=True: 优先检索高层级报告，不足时降级
        2. prefer_reports=False: 混合检索所有层级，按加权分数排序
        """
        if prefer_reports:
            return self._retrieve_with_fallback(
                query_text=query_text,
                n_results=n_results,
                project_id=project_id,
                min_level=min_level,
                date_range=date_range
            )
        else:
            return self._retrieve_mixed(
                query_text=query_text,
                n_results=n_results,
                project_id=project_id,
                min_level=min_level,
                date_range=date_range
            )

    def _retrieve_with_fallback(
        self,
        query_text: str,
        n_results: int,
        project_id: Optional[int],
        min_level: int,
        date_range: Optional[tuple]
    ) -> List[Dict[str, Any]]:
        """
        降级检索策略

        先查高层级报告，不足时逐级降低，直到min_level
        """
        results = []
        remaining = n_results

        # 从高到低逐层检索
        for level in [SourceLevel.REPORT_LEVEL_3, SourceLevel.REPORT_LEVEL_2,
                      SourceLevel.REPORT_LEVEL_1, SourceLevel.RAW_MATERIAL]:

            if level < min_level:
                break

            if remaining <= 0:
                break

            logger.info(f"🔍 检索层级 {level} (source_level={level})...")

            # 检索该层级
            level_results = self.vectorizer.query_with_metadata(
                query_text=query_text,
                n_results=remaining * 2,  # 多取一些，后面过滤
                project_id=project_id,
                source_levels=[level],
                date_range=date_range
            )

            if level_results:
                # 添加层级标记
                for result in level_results:
                    result["source_level"] = level
                    result["level_name"] = self._get_level_name(level)

                results.extend(level_results[:remaining])
                remaining -= len(level_results[:remaining])
                logger.info(f"  ✅ 从层级{level}获取 {len(level_results[:remaining])} 条结果")

        # 按层级和相似度排序
        results = self._sort_by_hierarchy(results)

        logger.info(f"✅ 分层检索完成: 共 {len(results)} 条结果")
        return results[:n_results]

    def _retrieve_mixed(
        self,
        query_text: str,
        n_results: int,
        project_id: Optional[int],
        min_level: int,
        date_range: Optional[tuple]
    ) -> List[Dict[str, Any]]:
        """
        混合检索策略

        检索所有层级，按加权分数（层级权重 * 相似度）排序
        """
        # 获取允许的层级
        allowed_levels = [level for level in range(SourceLevel.REPORT_LEVEL_3, min_level - 1, -1)]

        logger.info(f"🔍 混合检索 (允许层级: {allowed_levels})...")

        # 检索所有层级
        all_results = self.vectorizer.query_with_metadata(
            query_text=query_text,
            n_results=n_results * 3,  # 多取一些，后面重排
            project_id=project_id,
            source_levels=allowed_levels if allowed_levels else None,
            date_range=date_range
        )

        if not all_results:
            return []

        # 计算加权分数
        for result in all_results:
            source_level = result["metadata"].get("source_level", 0)
            relevance = result.get("relevance", 0.5)

            # 加权分数 = 层级权重 * 相似度
            level_weight = self.level_weights.get(source_level, 0.1)
            result["weighted_score"] = level_weight * relevance
            result["source_level"] = source_level
            result["level_name"] = self._get_level_name(source_level)

        # 按加权分数排序
        all_results.sort(key=lambda x: x["weighted_score"], reverse=True)

        logger.info(f"✅ 混合检索完成: 共 {len(all_results[:n_results])} 条结果")
        return all_results[:n_results]

    def _sort_by_hierarchy(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        按层级和相似度排序

        排序规则：
        1. 先按source_level降序（3 > 2 > 1 > 0）
        2. 同层级内按relevance降序
        """
        return sorted(
            results,
            key=lambda x: (x.get("source_level", 0), x.get("relevance", 0)),
            reverse=True
        )

    def _get_level_name(self, level: int) -> str:
        """获取层级的中文名称"""
        level_names = {
            SourceLevel.REPORT_LEVEL_3: "三度报告",
            SourceLevel.REPORT_LEVEL_2: "二度报告",
            SourceLevel.REPORT_LEVEL_1: "一度报告",
            SourceLevel.RAW_MATERIAL: "原始材料"
        }
        return level_names.get(level, "未知层级")

    def format_result_with_level(self, result: Dict[str, Any]) -> str:
        """
        格式化检索结果（突出层级信息）

        示例：
        - [三度报告] "费孝通指出，差序格局是中国社会的基本特征..."
          来源：深度分析报告.pdf P12

        - [原始材料] "我们村的祠堂再不修就要塌了..."
          来源：访谈老李_20240801.mp3 老李 01:05-01:18
        """
        level_name = result.get("level_name", "未知")
        text = result.get("text", "")
        citation = result.get("citation", "[来源未知]")

        # 文本截断（最多150字）
        text_preview = text[:150] + "..." if len(text) > 150 else text

        return f'[{level_name}] "{text_preview}"\n  {citation}'


# 全局单例
_hierarchical_retriever = None

def get_hierarchical_retriever() -> HierarchicalRetriever:
    """获取分层检索器单例"""
    global _hierarchical_retriever
    if _hierarchical_retriever is None:
        _hierarchical_retriever = HierarchicalRetriever()
    return _hierarchical_retriever
