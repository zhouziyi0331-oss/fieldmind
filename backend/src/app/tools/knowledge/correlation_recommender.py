"""
💡 智能关联推荐引擎 - 主动发现用户可能感兴趣的内容

功能：
1. 基于当前对象推荐相关内容
2. 深度2关联：通过中间节点发现潜在关系
3. 过滤已浏览内容，保证新鲜度
4. 按关联强度和新鲜度排序
"""

from typing import List, Dict, Any, Optional, Set
from sqlalchemy.orm import Session
from collections import defaultdict
from datetime import datetime, timedelta

from app.models.federation import FieldMindObject, ObjectRelation
from app.services.data_federation_service import DataFederationService


class CorrelationRecommender:
    """关联推荐引擎"""

    def __init__(self, db: Session):
        self.db = db
        self.federation = DataFederationService(db)

    # ==================== 主推荐入口 ====================

    def recommend(
        self,
        current_fid: str,
        user_viewed_history: Optional[Set[str]] = None,
        max_recommendations: int = 5,
        min_confidence: float = 0.6
    ) -> List[Dict[str, Any]]:
        """
        推荐与当前对象相关的其他对象

        Args:
            current_fid: 当前正在查看的对象
            user_viewed_history: 用户已浏览过的fid集合
            max_recommendations: 最多推荐数量
            min_confidence: 最低置信度阈值

        Returns:
            [
                {
                    "fid": "entity_xyz",
                    "type": "entity",
                    "title": "杀猪菜",
                    "reason": "与老王共现8次",
                    "confidence": 0.89,
                    "path": ["entity_abc", "fact_def", "entity_xyz"]
                }
            ]
        """
        if user_viewed_history is None:
            user_viewed_history = set()
        elif isinstance(user_viewed_history, list):
            user_viewed_history = set(user_viewed_history)

        # 添加当前fid到已浏览
        user_viewed_history.add(current_fid)

        # 1. 获取直接关联（深度1）
        direct_relations = self._get_direct_relations(current_fid)

        # 2. 获取间接关联（深度2）
        indirect_relations = self._get_indirect_relations(current_fid, direct_relations)

        # 3. 合并所有候选
        all_candidates = direct_relations + indirect_relations

        # 4. 过滤已浏览和低置信度
        candidates = [
            c for c in all_candidates
            if c["fid"] not in user_viewed_history and c["confidence"] >= min_confidence
        ]

        # 5. 按关联强度排序
        candidates = self._rank_by_relevance(candidates)

        # 6. 返回top N
        return candidates[:max_recommendations]

    # ==================== 深度1：直接关联 ====================

    def _get_direct_relations(self, current_fid: str) -> List[Dict[str, Any]]:
        """获取直接关联的对象"""
        relations = self.federation.get_relations(current_fid, direction="from")

        candidates = []
        for rel in relations:
            # 获取目标对象信息
            target_obj = self.db.query(FieldMindObject).filter(
                FieldMindObject.fid == rel.to_fid
            ).first()

            if target_obj:
                # 生成推荐理由
                reason = self._generate_reason(rel, None)

                candidates.append({
                    "fid": target_obj.fid,
                    "type": target_obj.object_type,
                    "title": self._extract_title(target_obj),
                    "reason": reason,
                    "confidence": rel.confidence,
                    "path": [current_fid, target_obj.fid],
                    "depth": 1,
                    "relation_type": rel.relation_type
                })

        return candidates

    # ==================== 深度2：间接关联 ====================

    def _get_indirect_relations(
        self,
        current_fid: str,
        direct_relations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """通过中间节点获取间接关联"""
        candidates = []

        # 对每个直接关联的对象，查找其关联
        for direct in direct_relations:
            intermediate_fid = direct["fid"]

            # 获取中间节点的关联
            second_level = self.federation.get_relations(intermediate_fid, direction="from")

            for rel2 in second_level:
                # 避免循环回到起点
                if rel2.to_fid == current_fid:
                    continue

                # 获取最终目标对象
                final_obj = self.db.query(FieldMindObject).filter(
                    FieldMindObject.fid == rel2.to_fid
                ).first()

                if final_obj:
                    # 计算间接关联的置信度（两跳的乘积，带衰减）
                    indirect_confidence = direct["confidence"] * rel2.confidence * 0.8

                    # 生成推荐理由（说明通过什么路径）
                    reason = self._generate_indirect_reason(
                        direct["title"],
                        direct["relation_type"],
                        rel2.relation_type
                    )

                    candidates.append({
                        "fid": final_obj.fid,
                        "type": final_obj.object_type,
                        "title": self._extract_title(final_obj),
                        "reason": reason,
                        "confidence": indirect_confidence,
                        "path": [current_fid, intermediate_fid, final_obj.fid],
                        "depth": 2,
                        "relation_type": "indirect"
                    })

        return candidates

    # ==================== 排序：按相关性 ====================

    def _rank_by_relevance(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        按关联强度和新鲜度排序

        排序规则：
        1. 深度1优先于深度2
        2. 相同深度，置信度高的优先
        3. 相同置信度，新创建的优先
        """
        def sort_key(c):
            # 深度权重：深度1 = 1.0，深度2 = 0.8
            depth_weight = 1.0 if c["depth"] == 1 else 0.8

            # 综合分数 = 深度权重 × 置信度
            score = depth_weight * c["confidence"]

            return (-score, c["depth"])  # 负号表示降序

        candidates.sort(key=sort_key)
        return candidates

    # ==================== 生成推荐理由 ====================

    def _generate_reason(self, relation: ObjectRelation, intermediate: Optional[str]) -> str:
        """生成推荐理由"""
        rel_type = relation.relation_type
        rel_data = relation.relation_data or {}

        if rel_type == "co_occurrence":
            count = rel_data.get("co_occurrence_count", 0)
            return f"共现{count}次" if count > 0 else "共同出现"

        elif rel_type == "temporal_proximity":
            time_dist = rel_data.get("time_distance_sec", 0)
            return f"在时间上相近（相差{time_dist:.1f}秒）"

        elif rel_type == "semantic_similarity":
            score = rel_data.get("semantic_score", 0)
            return f"语义相似度{score:.2f}"

        elif rel_type == "inferred":
            return "通过推理关联"

        else:
            return "相关内容"

    def _generate_indirect_reason(
        self,
        intermediate_title: str,
        first_relation: str,
        second_relation: str
    ) -> str:
        """生成间接关联的推荐理由"""
        # 简化关系类型名称
        rel_map = {
            "co_occurrence": "共现",
            "temporal_proximity": "时间相近",
            "semantic_similarity": "语义相似",
            "inferred": "推理",
            "mentions": "提及"
        }

        first = rel_map.get(first_relation, first_relation)
        second = rel_map.get(second_relation, second_relation)

        return f"通过「{intermediate_title}」关联（{first}→{second}）"

    # ==================== 提取标题 ====================

    def _extract_title(self, obj: FieldMindObject) -> str:
        """从对象元数据中提取标题"""
        metadata = obj.object_metadata or {}

        # 不同类型对象的标题字段不同
        if obj.object_type == "entity":
            return metadata.get("entity_name") or metadata.get("canonical_name") or "未命名实体"

        elif obj.object_type == "event":
            return metadata.get("event_summary") or "未命名事件"

        elif obj.object_type == "document":
            return metadata.get("title") or metadata.get("filename") or "未命名文档"

        elif obj.object_type == "fact":
            preview = metadata.get("content_preview") or ""
            return preview[:30] + "..." if len(preview) > 30 else preview

        elif obj.object_type == "topic":
            return metadata.get("topic_name") or "未命名主题"

        else:
            return f"{obj.object_type}_{obj.fid[:8]}"

    # ==================== 批量推荐：为多个对象推荐 ====================

    def batch_recommend(
        self,
        fids: List[str],
        max_per_object: int = 3
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        为多个对象批量生成推荐

        Returns:
            {
                "entity_abc": [...推荐列表...],
                "event_xyz": [...推荐列表...]
            }
        """
        results = {}

        for fid in fids:
            recommendations = self.recommend(fid, max_recommendations=max_per_object)
            results[fid] = recommendations

        return results

    # ==================== 项目级推荐：发现热点 ====================

    def discover_hot_connections(
        self,
        project_id: int,
        top_n: int = 10
    ) -> List[Dict[str, Any]]:
        """
        发现项目中的热点连接（关联最多的对象对）

        Returns:
            [
                {
                    "from_title": "老王",
                    "to_title": "杀猪菜",
                    "relation_count": 8,
                    "confidence_avg": 0.87
                }
            ]
        """
        # 统计每对对象之间的关系数量
        query = f"""
            SELECT
                from_fid,
                to_fid,
                COUNT(*) as relation_count,
                AVG(confidence) as confidence_avg
            FROM object_relations
            WHERE project_id = {project_id}
            GROUP BY from_fid, to_fid
            ORDER BY relation_count DESC, confidence_avg DESC
            LIMIT {top_n}
        """

        result = self.db.execute(query).fetchall()

        hot_connections = []
        for row in result:
            from_obj = self.db.query(FieldMindObject).filter(
                FieldMindObject.fid == row[0]
            ).first()

            to_obj = self.db.query(FieldMindObject).filter(
                FieldMindObject.fid == row[1]
            ).first()

            if from_obj and to_obj:
                hot_connections.append({
                    "from_fid": row[0],
                    "from_title": self._extract_title(from_obj),
                    "to_fid": row[1],
                    "to_title": self._extract_title(to_obj),
                    "relation_count": row[2],
                    "confidence_avg": float(row[3])
                })

        return hot_connections
