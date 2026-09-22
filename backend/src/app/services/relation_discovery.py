"""
🔗 关系发现引擎 - 自动发现对象之间的潜在关联

基于四种发现策略：
1. 共现关联 - 在同一段落/文档中出现
2. 时间关联 - 在同一时间窗口内被提及
3. 语义关联 - 向量相似度高
4. 推理关联 - A→B→C 的传递性推断
"""

from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from collections import defaultdict
import numpy as np

from app.models.federation import FieldMindObject, ObjectRelation, FactStatement
from app.services.data_federation_service import DataFederationService


class RelationDiscoveryEngine:
    """关系发现引擎"""
    def __init__(self, db: Session, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.db = db
        self.federation = DataFederationService(db)

    # ==================== 主入口 ====================

    def discover_all_relations(self, object_fid: str) -> List[Dict[str, Any]]:
        """
        发现一个对象的所有潜在关联

        Returns:
            List of discovered relations with confidence scores
        """
        obj = self.db.query(FieldMindObject).filter(
            FieldMindObject.fid == object_fid
        ).first()

        if not obj:
            return []

        project_id = obj.project_id

        # 1. 共现关联
        co_occurrence = self.find_co_occurrences(object_fid, project_id)

        # 2. 时间关联
        temporal = self.find_temporal_proximity(object_fid, project_id)

        # 3. 语义关联
        semantic = self.find_semantic_neighbors(object_fid, project_id)

        # 4. 推理关联
        inferred = self.infer_transitive_relations(object_fid, project_id)

        # 合并所有关联并去重
        all_relations = self._aggregate_relations([
            co_occurrence,
            temporal,
            semantic,
            inferred
        ])

        return all_relations

    # ==================== 策略1：共现关联 ====================

    def find_co_occurrences(self, object_fid: str, project_id: int) -> List[Dict[str, Any]]:
        """
        查找共现关联：在同一个fact/document中一起出现的对象

        适用于：实体-实体、实体-事件的共现
        """
        relations = []

        # 获取当前对象
        obj = self.db.query(FieldMindObject).filter(
            FieldMindObject.fid == object_fid
        ).first()

        if not obj:
            return []

        # 如果是实体类型，查找包含该实体的所有facts
        if obj.object_type == "entity":
            entity_name = obj.object_metadata.get("entity_name") or obj.object_metadata.get("canonical_name")

            if entity_name:
                # 查找所有提到该实体的facts（需要解析JSON）
                import json
                all_facts = self.db.query(FactStatement).filter(
                    FactStatement.project_id == project_id
                ).all()

                facts = []
                for fact in all_facts:
                    if fact.entity_names:
                        # 解析JSON字符串
                        entity_list = json.loads(fact.entity_names) if isinstance(fact.entity_names, str) else fact.entity_names
                        if entity_name in entity_list:
                            facts.append(fact)

                # 统计共现的其他实体
                co_occurrence_count = defaultdict(int)
                co_occurrence_fids = defaultdict(list)

                for fact in facts:
                    if fact.entity_names:
                        # 解析JSON字符串
                        entity_list = json.loads(fact.entity_names) if isinstance(fact.entity_names, str) else fact.entity_names
                        for other_entity in entity_list:
                            if other_entity != entity_name:
                                co_occurrence_count[other_entity] += 1
                                if fact.fid:
                                    co_occurrence_fids[other_entity].append(fact.fid)

                # 为每个共现实体创建关系
                for other_entity, count in co_occurrence_count.items():
                    # 查找对应的fid
                    other_obj = self.db.query(FieldMindObject).filter(
                        FieldMindObject.project_id == project_id,
                        FieldMindObject.object_type == "entity",
                        FieldMindObject.object_metadata["entity_name"].as_string() == other_entity
                    ).first()

                    if other_obj:
                        confidence = min(count / 10.0, 1.0)  # 共现10次以上视为强关联
                        relations.append({
                            "from_fid": object_fid,
                            "to_fid": other_obj.fid,
                            "relation_type": "co_occurrence",
                            "confidence": confidence,
                            "evidence_fids": co_occurrence_fids[other_entity],
                            "relation_data": {
                                "co_occurrence_count": count,
                                "method": "entity_co_occurrence_in_facts"
                            }
                        })

        return relations

    # ==================== 策略2：时间关联 ====================

    def find_temporal_proximity(
        self,
        object_fid: str,
        project_id: int,
        time_window_sec: float = 30.0
    ) -> List[Dict[str, Any]]:
        """
        查找时间邻近关联：在相近时间窗口内提及的对象

        适用于：音视频转录中的事件-人物关联
        """
        relations = []

        # 获取当前对象关联的facts
        obj = self.db.query(FieldMindObject).filter(
            FieldMindObject.fid == object_fid
        ).first()

        if not obj or obj.object_type not in ["entity", "event"]:
            return []

        # 查找包含该对象的facts（带时间戳）
        entity_name = obj.object_metadata.get("entity_name") or obj.object_metadata.get("canonical_name")

        if not entity_name:
            return []

        # 获取该实体出现的所有时间戳
        facts_with_time = self.db.query(FactStatement).filter(
            FactStatement.project_id == project_id,
            FactStatement.entity_names.contains(entity_name),
            FactStatement.start_sec.isnot(None)
        ).all()

        # 对每个时间戳，查找时间窗口内的其他对象
        for fact in facts_with_time:
            time_start = fact.start_sec - time_window_sec
            time_end = fact.start_sec + time_window_sec

            # 查找时间窗口内的其他facts
            nearby_facts = self.db.query(FactStatement).filter(
                FactStatement.project_id == project_id,
                FactStatement.start_sec >= time_start,
                FactStatement.start_sec <= time_end,
                FactStatement.fid != fact.fid
            ).all()

            # 提取这些facts中的实体
            nearby_entities = set()
            for nearby_fact in nearby_facts:
                if nearby_fact.entity_names:
                    nearby_entities.update(nearby_fact.entity_names)

            # 移除当前实体
            nearby_entities.discard(entity_name)

            # 为每个邻近实体创建关系
            for other_entity in nearby_entities:
                other_obj = self.db.query(FieldMindObject).filter(
                    FieldMindObject.project_id == project_id,
                    FieldMindObject.object_type == "entity",
                    FieldMindObject.object_metadata["entity_name"].as_string() == other_entity
                ).first()

                if other_obj:
                    # 计算平均时间距离
                    time_distance = abs(fact.start_sec - nearby_facts[0].start_sec) if nearby_facts else 0
                    confidence = max(0.3, 1.0 - (time_distance / time_window_sec))

                    relations.append({
                        "from_fid": object_fid,
                        "to_fid": other_obj.fid,
                        "relation_type": "temporal_proximity",
                        "confidence": confidence,
                        "evidence_fids": [f.fid for f in nearby_facts if f.fid],
                        "relation_data": {
                            "time_distance_sec": time_distance,
                            "time_window_sec": time_window_sec,
                            "anchor_time": fact.start_sec,
                            "method": "temporal_window"
                        }
                    })

        return relations

    # ==================== 策略3：语义关联 ====================

    def find_semantic_neighbors(
        self,
        object_fid: str,
        project_id: int,
        similarity_threshold: float = 0.75
    ) -> List[Dict[str, Any]]:
        """
        查找语义相似关联：向量空间中相近的对象

        注意：需要向量化支持，暂时返回空列表，后续集成ChromaDB
        """
        # TODO: 集成ChromaDB向量相似度查询
        # 1. 获取object_fid对应的vector_id
        # 2. 在ChromaDB中查询相似向量
        # 3. 返回相似度 > threshold 的对象

        return []

    # ==================== 策略4：推理关联 ====================

    def infer_transitive_relations(
        self,
        object_fid: str,
        project_id: int,
        max_depth: int = 2
    ) -> List[Dict[str, Any]]:
        """
        推理传递关联：A→B→C，则推断A→C

        适用于：通过中间节点建立间接关系
        """
        relations = []

        # 获取直接关系
        direct_relations = self.federation.get_relations(object_fid, direction="from")

        if not direct_relations or max_depth < 2:
            return []

        # 对每个直接关系的目标，再查找其关系
        for rel in direct_relations:
            to_fid = rel.to_fid

            # 查找to_fid的关系
            second_level = self.federation.get_relations(to_fid, direction="from")

            for rel2 in second_level:
                final_fid = rel2.to_fid

                # 避免循环
                if final_fid == object_fid:
                    continue

                # 检查是否已有直接关系
                existing = self.db.query(ObjectRelation).filter(
                    ObjectRelation.from_fid == object_fid,
                    ObjectRelation.to_fid == final_fid
                ).first()

                if not existing:
                    # 推断置信度 = 两条边置信度的乘积
                    inferred_confidence = rel.confidence * rel2.confidence * 0.7  # 乘0.7作为推理惩罚

                    relations.append({
                        "from_fid": object_fid,
                        "to_fid": final_fid,
                        "relation_type": "inferred",
                        "confidence": inferred_confidence,
                        "evidence_fids": [],
                        "relation_data": {
                            "inference_path": [object_fid, to_fid, final_fid],
                            "method": "transitive_inference",
                            "depth": 2
                        }
                    })

        return relations

    # ==================== 关系聚合 ====================

    def _aggregate_relations(self, relation_lists: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        合并多个关系发现策略的结果

        如果同一对象对出现在多个策略中，取最高置信度
        """
        # 使用 (from_fid, to_fid) 作为key去重
        relation_map: Dict[Tuple[str, str], Dict[str, Any]] = {}

        for rel_list in relation_lists:
            for rel in rel_list:
                key = (rel["from_fid"], rel["to_fid"])

                if key not in relation_map:
                    relation_map[key] = rel
                else:
                    # 取更高的置信度
                    if rel["confidence"] > relation_map[key]["confidence"]:
                        relation_map[key] = rel

        return list(relation_map.values())

    # ==================== 批量发现 ====================

    def discover_project_relations(self, project_id: int, batch_size: int = 50) -> int:
        """
        为项目中的所有实体和事件发现关系

        Returns:
            新增关系的数量
        """
        # 查找所有实体和事件对象
        objects = self.db.query(FieldMindObject).filter(
            FieldMindObject.project_id == project_id,
            FieldMindObject.object_type.in_(["entity", "event"])
        ).limit(batch_size).all()

        new_relations_count = 0

        for obj in objects:
            # 发现关系
            discovered = self.discover_all_relations(obj.fid)

            # 写入数据库
            for rel_data in discovered:
                # 检查是否已存在
                existing = self.db.query(ObjectRelation).filter(
                    ObjectRelation.from_fid == rel_data["from_fid"],
                    ObjectRelation.to_fid == rel_data["to_fid"],
                    ObjectRelation.relation_type == rel_data["relation_type"]
                ).first()

                if not existing:
                    self.federation.add_relation(
                        from_fid=rel_data["from_fid"],
                        to_fid=rel_data["to_fid"],
                        relation_type=rel_data["relation_type"],
                        confidence=rel_data["confidence"],
                        project_id=project_id,
                        evidence_fids=rel_data.get("evidence_fids"),
                        relation_data=rel_data.get("relation_data")
                    )
                    new_relations_count += 1

        self.db.commit()
        return new_relations_count
