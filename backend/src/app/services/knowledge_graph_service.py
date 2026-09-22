"""
知识图谱服务
基于NetworkX + spaCy + LLM构建田野调查知识图谱
支持跨文档实体整合和关系发现
"""

import logging
import networkx as nx
from typing import List, Dict, Any, Tuple, Optional
import json
from datetime import datetime
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class Entity:
    """实体"""
    def __init__(self, name: str, entity_type: str, properties: Dict = None, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.name = name
        self.entity_type = entity_type
        self.properties = properties or {}
        self.id = f"{entity_type}_{name}"

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.entity_type,
            'properties': self.properties
        }


class Relation:
    """关系"""
    def __init__(self, source: str, target: str, relation_type: str, properties: Dict = None):
        self.source = source
        self.target = target
        self.relation_type = relation_type
        self.properties = properties or {}

    def to_dict(self):
        return {
            'source': self.source,
            'target': self.target,
            'type': self.relation_type,
            'properties': self.properties
        }


class KnowledgeGraphService:
    """知识图谱服务"""

    def __init__(self):
        self.graph = nx.MultiDiGraph()  # 有向多重图
        logger.info("✅ 知识图谱服务初始化完成")

    # 🆕 跨文档知识图谱构建
    def build_cross_document_graph(self, project_id: int, db: Session) -> Dict[str, Any]:
        """
        构建跨文档知识图谱

        Args:
            project_id: 项目ID
            db: 数据库会话

        Returns:
            图谱统计信息
        """
        try:
            logger.info(f"开始构建项目{project_id}的跨文档知识图谱")

            # 1. 获取跨文档实体消歧结果
            from app.services.cross_document_entity_resolver import cross_document_resolver
            entity_result = cross_document_resolver.resolve_entities(project_id, db)
            canonical_entities = entity_result.get('canonical_entities', [])

            if not canonical_entities:
                logger.warning("没有可用的实体，跳过知识图谱构建")
                return {'entities_count': 0, 'relations_count': 0}

            # 2. 清空现有图谱（项目级别重建）
            self.graph.clear()

            # 3. 添加消歧后的实体节点
            for entity in canonical_entities:
                self.graph.add_node(
                    entity['canonical_id'],
                    name=entity['name'],
                    entity_type=entity['type'],
                    mention_count=entity['mention_count'],
                    document_ids=entity['document_ids'],
                    contexts=entity.get('contexts', []),
                    confidence=entity['confidence']
                )

            # 4. 添加实体间关系（基于共现和上下文）
            relations_count = self._discover_entity_relations(canonical_entities)

            # 5. 丰富图谱（添加文档上下文）
            self._enrich_graph_with_document_context(project_id, db)

            # 6. 计算图统计指标
            stats = self._compute_graph_statistics()

            logger.info(f"✅ 跨文档知识图谱构建完成: {stats}")

            return stats

        except Exception as e:
            logger.error(f"❌ 跨文档知识图谱构建失败: {e}", exc_info=True)
            return {'entities_count': 0, 'relations_count': 0, 'error': str(e)}

    def _discover_entity_relations(self, canonical_entities: List[Dict]) -> int:
        """发现实体间关系"""
        relations_count = 0

        try:
            # 基于共现关系：如果两个实体在同一文档中出现，建立关系
            for i, entity_a in enumerate(canonical_entities):
                docs_a = set(entity_a['document_ids'])

                for j, entity_b in enumerate(canonical_entities):
                    if i >= j:
                        continue

                    docs_b = set(entity_b['document_ids'])
                    shared_docs = docs_a & docs_b

                    if shared_docs:
                        # 添加共现关系
                        self.graph.add_edge(
                            entity_a['canonical_id'],
                            entity_b['canonical_id'],
                            relation_type='CO_OCCURS',
                            weight=len(shared_docs),
                            shared_documents=list(shared_docs),
                            confidence=min(1.0, len(shared_docs) / 5)
                        )
                        relations_count += 1

            logger.info(f"发现{relations_count}个实体间关系")
            return relations_count

        except Exception as e:
            logger.error(f"实体关系发现失败: {e}")
            return relations_count

    def _enrich_graph_with_document_context(self, project_id: int, db: Session):
        """用文档上下文丰富图谱"""
        try:
            from app.models.project import ProjectDocument

            documents = db.query(ProjectDocument).filter(
                ProjectDocument.project_id == project_id,
                ProjectDocument.status == "completed"
            ).all()

            # 为每个实体节点添加文档信息
            for node_id in self.graph.nodes():
                node_data = self.graph.nodes[node_id]
                doc_ids = node_data.get('document_ids', [])

                # 添加文档详情
                doc_details = []
                for doc in documents:
                    if doc.id in doc_ids:
                        doc_details.append({
                            'document_id': doc.id,
                            'document_name': doc.filename,
                            'created_at': doc.created_at.isoformat() if doc.created_at else None
                        })

                node_data['documents'] = doc_details

            logger.info("图谱已用文档上下文丰富")

        except Exception as e:
            logger.error(f"图谱丰富失败: {e}")

    def _compute_graph_statistics(self) -> Dict[str, Any]:
        """计算图统计指标"""
        try:
            stats = {
                'entities_count': self.graph.number_of_nodes(),
                'relations_count': self.graph.number_of_edges(),
                'density': 0,
                'avg_degree': 0,
                'connected_components': 0
            }

            if stats['entities_count'] > 0:
                # 图密度
                if stats['entities_count'] > 1:
                    stats['density'] = nx.density(self.graph)

                # 平均度
                degrees = [d for n, d in self.graph.degree()]
                stats['avg_degree'] = sum(degrees) / len(degrees) if degrees else 0

                # 连通分量数
                undirected = self.graph.to_undirected()
                stats['connected_components'] = nx.number_connected_components(undirected)

            return stats

        except Exception as e:
            logger.error(f"统计指标计算失败: {e}")
            return {
                'entities_count': self.graph.number_of_nodes(),
                'relations_count': self.graph.number_of_edges()
            }

    def export_graph_data(self) -> Dict[str, Any]:
        """导出图谱数据供前端可视化"""
        try:
            nodes = []
            edges = []

            # 导出节点
            for node_id in self.graph.nodes():
                node_data = self.graph.nodes[node_id]
                nodes.append({
                    'id': node_id,
                    'name': node_data.get('name', node_id),
                    'type': node_data.get('entity_type', 'UNKNOWN'),
                    'mention_count': node_data.get('mention_count', 0),
                    'document_count': len(node_data.get('document_ids', [])),
                    'confidence': node_data.get('confidence', 0.5)
                })

            # 导出边
            for source, target, key, edge_data in self.graph.edges(keys=True, data=True):
                edges.append({
                    'source': source,
                    'target': target,
                    'type': edge_data.get('relation_type', 'RELATED'),
                    'weight': edge_data.get('weight', 1),
                    'confidence': edge_data.get('confidence', 0.5)
                })

            return {
                'nodes': nodes,
                'edges': edges,
                'statistics': self._compute_graph_statistics()
            }

        except Exception as e:
            logger.error(f"图谱数据导出失败: {e}")
            return {'nodes': [], 'edges': [], 'statistics': {}}

    def extract_entities_and_relations(self, text: str, document_id: int = None, use_llm: bool = True) -> Tuple[List[Entity], List[Relation]]:
        """
        从文本提取实体和关系（多策略融合）

        Args:
            text: 输入文本
            document_id: 文档ID
            use_llm: 是否使用LLM增强（默认True）

        Returns:
            (实体列表, 关系列表)
        """
        entities = []
        relations = []

        try:
            # 【方法1】使用LLM增强提取（准确率最高）
            if use_llm:
                try:
                    from app.services.llm_enhanced_extractor import get_llm_extractor
                    llm_extractor = get_llm_extractor()
                    entities_llm, relations_llm = llm_extractor.extract_with_llm(text)

                    # 转换为Entity和Relation对象
                    for e in entities_llm:
                        entities.append(Entity(
                            name=e['name'],
                            entity_type=e['type'],
                            properties={**e.get('properties', {}), 'source': 'llm'}
                        ))

                    for r in relations_llm:
                        relations.append(Relation(
                            source=r['source'],
                            target=r['target'],
                            relation_type=r['type'],
                            properties={'confidence': r.get('confidence', 0.95), 'source': 'llm'}
                        ))

                    logger.info(f"✅ LLM提取: {len(entities_llm)}个实体, {len(relations_llm)}个关系")
                except Exception as e:
                    logger.warning(f"LLM提取失败，回退到规则方法: {e}")

            # 【方法2】使用spaCy NER（实体识别）
            entities_spacy, relations_spacy = self._extract_with_spacy(text)
            entities.extend(entities_spacy)
            relations.extend(relations_spacy)

            # 【方法3】使用增强规则模板（针对田野调查）
            entities_rule, relations_rule = self._extract_with_enhanced_rules(text)
            entities.extend(entities_rule)
            relations.extend(relations_rule)

            # 去重和过滤
            entities = self._deduplicate_entities(entities)
            entities = self._filter_low_quality_entities(entities)

            logger.info(f"✅ 总计提取: {len(entities)}个实体, {len(relations)}个关系")

        except Exception as e:
            logger.error(f"实体关系提取失败: {e}")

        return entities, relations

    def _extract_with_spacy(self, text: str) -> Tuple[List[Entity], List[Relation]]:
        """使用spaCy提取实体"""
        entities = []
        relations = []

        try:
            import spacy
            # 使用已安装的中文模型
            nlp = spacy.load("zh_core_web_sm")
            doc = nlp(text)

            # 提取命名实体
            for ent in doc.ents:
                entity = Entity(
                    name=ent.text,
                    entity_type=ent.label_,
                    properties={'source': 'spacy'}
                )
                entities.append(entity)

        except Exception as e:
            logger.warning(f"spaCy提取失败: {e}")

        return entities, relations

    def _extract_with_rules(self, text: str) -> Tuple[List[Entity], List[Relation]]:
        """使用规则模板提取（田野调查专用）"""
        entities = []
        relations = []

        # 规则1: "XXX说" → 人物实体
        import re
        person_pattern = r'([^，。！？\s]{2,4})(说|讲|告诉|表示)'
        matches = re.finditer(person_pattern, text)

        for match in matches:
            name = match.group(1)
            entity = Entity(
                name=name,
                entity_type='PERSON',
                properties={'source': 'rule', 'role': '受访者'}
            )
            entities.append(entity)

        # 规则2: "XXX是YYY" → 实体 + 关系
        is_pattern = r'([^，。！？\s]{2,10})是([^，。！？\s]{2,15})'
        matches = re.finditer(is_pattern, text)

        for match in matches:
            subject = match.group(1)
            obj = match.group(2)

            # 添加实体
            entities.append(Entity(subject, 'THING', {'source': 'rule'}))
            entities.append(Entity(obj, 'CONCEPT', {'source': 'rule'}))

            # 添加关系
            relations.append(Relation(subject, obj, '是', {'confidence': 0.9}))

        # 规则3: "XXX的YYY" → 所属关系
        belong_pattern = r'([^，。！？\s]{2,10})的([^，。！？\s]{2,10})'
        matches = re.finditer(belong_pattern, text)

        for match in matches:
            owner = match.group(1)
            owned = match.group(2)

            entities.append(Entity(owner, 'ENTITY', {'source': 'rule'}))
            entities.append(Entity(owned, 'ENTITY', {'source': 'rule'}))

            relations.append(Relation(owner, owned, '拥有', {'confidence': 0.8}))

        return entities, relations

    def _extract_with_enhanced_rules(self, text: str) -> Tuple[List[Entity], List[Relation]]:
        """增强规则提取（更多田野调查场景）"""
        entities = []
        relations = []
        import re

        # 规则4: "XXX认为YYY" → 观点关系
        opinion_pattern = r'([^，。！？\s]{2,4})(认为|觉得|表示|指出)([^，。！？]{5,30})'
        matches = re.finditer(opinion_pattern, text)
        for match in matches:
            person = match.group(1)
            opinion = match.group(3).strip()
            entities.append(Entity(person, 'PERSON', {'source': 'rule_enhanced'}))
            entities.append(Entity(opinion, 'CONCEPT', {'source': 'rule_enhanced', 'type': 'opinion'}))
            relations.append(Relation(person, opinion, '认为', {'confidence': 0.85}))

        # 规则5: "在XXX" → 地点实体
        location_pattern = r'在([^，。！？\s]{2,8})(村|镇|市|县|省|区|街|路|里)'
        matches = re.finditer(location_pattern, text)
        for match in matches:
            location = match.group(1) + match.group(2)
            entities.append(Entity(location, 'LOCATION', {'source': 'rule_enhanced'}))

        # 规则6: "参加XXX" → 事件实体
        event_pattern = r'(参加|举办|进行|开展)([^，。！？\s]{2,10})(活动|仪式|节日|庆典|会议)'
        matches = re.finditer(event_pattern, text)
        for match in matches:
            event = match.group(2) + match.group(3)
            entities.append(Entity(event, 'EVENT', {'source': 'rule_enhanced'}))

        # 规则7: "XXX年" → 时间实体
        year_pattern = r'(\d{4})年'
        matches = re.finditer(year_pattern, text)
        for match in matches:
            year = match.group(0)
            entities.append(Entity(year, 'DATE', {'source': 'rule_enhanced', 'year': match.group(1)}))

        # 规则8: "XXX影响YYY" → 影响关系
        influence_pattern = r'([^，。！？\s]{2,10})(影响|导致|促进|阻碍)([^，。！？\s]{2,10})'
        matches = re.finditer(influence_pattern, text)
        for match in matches:
            source = match.group(1)
            target = match.group(3)
            relation_type = match.group(2)
            entities.append(Entity(source, 'CONCEPT', {'source': 'rule_enhanced'}))
            entities.append(Entity(target, 'CONCEPT', {'source': 'rule_enhanced'}))
            relations.append(Relation(source, target, relation_type, {'confidence': 0.8}))

        # 规则9: "XXX属于YYY" → 归属关系
        belong_to_pattern = r'([^，。！？\s]{2,10})(属于|隶属于|归属)([^，。！？\s]{2,10})'
        matches = re.finditer(belong_to_pattern, text)
        for match in matches:
            entity = match.group(1)
            group = match.group(3)
            entities.append(Entity(entity, 'ENTITY', {'source': 'rule_enhanced'}))
            entities.append(Entity(group, 'ORGANIZATION', {'source': 'rule_enhanced'}))
            relations.append(Relation(entity, group, '属于', {'confidence': 0.9}))

        # 规则10: "XXX包括YYY" → 包含关系
        include_pattern = r'([^，。！？\s]{2,10})(包括|包含|含有)([^，。！？\s]{2,15})'
        matches = re.finditer(include_pattern, text)
        for match in matches:
            whole = match.group(1)
            part = match.group(3)
            entities.append(Entity(whole, 'CONCEPT', {'source': 'rule_enhanced'}))
            entities.append(Entity(part, 'ENTITY', {'source': 'rule_enhanced'}))
            relations.append(Relation(whole, part, '包含', {'confidence': 0.85}))

        return entities, relations

    def _filter_low_quality_entities(self, entities: List[Entity]) -> List[Entity]:
        """过滤低质量实体"""
        filtered = []

        # 过滤规则
        stop_words = {'这个', '那个', '什么', '怎么', '一个', '这样', '那样', '如此', '非常', '很多'}

        for entity in entities:
            name = entity.name.strip()

            # 过滤条件
            if len(name) < 2:  # 太短
                continue
            if name in stop_words:  # 停用词
                continue
            if name.isdigit():  # 纯数字（除非是年份）
                if entity.entity_type != 'DATE':
                    continue

            filtered.append(entity)

        return filtered

    def _deduplicate_entities(self, entities: List[Entity]) -> List[Entity]:
        """实体去重"""
        seen = {}
        unique_entities = []

        for entity in entities:
            key = f"{entity.name}_{entity.entity_type}"
            if key not in seen:
                seen[key] = entity
                unique_entities.append(entity)

        return unique_entities

    def add_entities_and_relations(
        self,
        entities: List[Entity],
        relations: List[Relation],
        document_id: Optional[int] = None,
    ):
        """添加实体和关系到图谱"""
        # 添加节点
        for entity in entities:
            self.graph.add_node(
                entity.id,
                name=entity.name,
                entity_type=entity.entity_type,  # 避免与NetworkX的type冲突
                **entity.properties
            )

        # 添加边
        for relation in relations:
            source_id = self._find_entity_id(relation.source)
            target_id = self._find_entity_id(relation.target)

            if source_id and target_id:
                self.graph.add_edge(
                    source_id,
                    target_id,
                    relation=relation.relation_type,
                    **relation.properties
                )

        logger.info(f"图谱更新: {self.graph.number_of_nodes()} 节点, {self.graph.number_of_edges()} 边")

        # 持久化到当前统一实体模型；关系也必须一并落库，避免只存在内存图。
        self._persist_to_sqlite(entities, relations, document_id=document_id)

        # 同步到Neo4j
        self._sync_to_neo4j()

    def _find_entity_id(self, name: str) -> Optional[str]:
        """根据名称查找实体ID"""
        for node_id, data in self.graph.nodes(data=True):
            if data.get('name') == name:
                return node_id
        return None

    def _persist_to_sqlite(
        self,
        entities: List[Entity],
        relations: Optional[List[Relation]] = None,
        document_id: Optional[int] = None,
    ):
        """持久化实体、实体关系和可用的文档关联到统一SQLite模型。"""
        try:
            from app.core.database import get_db
            from app.models.entity import Entity as EntityModel
            from app.models.entity import EntityRelation, DocumentEntity
            from app.models.document import Document
            from sqlalchemy import and_, func
            import uuid

            db = next(get_db())
            persisted_entities = {}

            for entity in entities:
                text = entity.name.strip()
                entity_type = entity.entity_type.strip().upper()
                # 当前模型字段是 text/type，旧实现使用 name/entity_type 会直接抛 AttributeError。
                existing = db.query(EntityModel).filter(
                    EntityModel.text == text,
                    EntityModel.type == entity_type
                ).first()

                if existing:
                    metadata = dict(existing.metadata_json or {})
                    metadata["mention_count"] = int(metadata.get("mention_count", 0)) + 1
                    if entity.properties.get("source"):
                        metadata["sources"] = sorted(
                            set(metadata.get("sources", [])) | {entity.properties["source"]}
                        )
                    existing.metadata_json = metadata
                    existing.legacy_name = text
                    existing.legacy_entity_type = entity_type
                    existing.legacy_properties = entity.properties
                    existing.canonical_form = existing.canonical_form or text
                else:
                    new_entity = EntityModel(
                        id=str(uuid.uuid4()),
                        text=text,
                        type=entity_type,
                        legacy_name=text,
                        legacy_entity_type=entity_type,
                        legacy_properties=entity.properties,
                        canonical_form=text,
                        description=entity.properties.get("description"),
                        metadata_json={
                            **entity.properties,
                            "mention_count": 1,
                        },
                    )
                    db.add(new_entity)
                    db.flush()
                    existing = new_entity

                persisted_entities[(text, entity_type)] = existing

                # ProjectDocument 是当前上传主表；只有旧 documents 表中存在对应记录时，
                # 才写入 DocumentEntity，避免把两套文档主键强行混用。
                if document_id is not None:
                    legacy_document = db.query(Document).filter(
                        Document.id == str(document_id)
                    ).first()
                    if legacy_document:
                        link = db.query(DocumentEntity).filter(
                            and_(
                                DocumentEntity.document_id == str(document_id),
                                DocumentEntity.entity_id == existing.id,
                            )
                        ).first()
                        if link:
                            link.mentions = (link.mentions or 0) + 1
                        else:
                            db.add(DocumentEntity(
                                document_id=str(document_id),
                                entity_id=existing.id,
                                mentions=1,
                                confidence=float(entity.properties.get("confidence", 0.85)),
                                context=entity.properties.get("context"),
                            ))

            # SQLite 不会为声明为 BIGINT 的主键执行 INTEGER PRIMARY KEY
            # 的隐式自增。显式分配下一个关系 ID，避免实体关系写入时出现
            # NOT NULL constraint failed，同时兼容现有数据库结构。
            next_relation_id = int(db.query(func.max(EntityRelation.id)).scalar() or 0) + 1

            for relation in relations or []:
                source = next(
                    (item for key, item in persisted_entities.items() if key[0] == relation.source),
                    None,
                )
                target = next(
                    (item for key, item in persisted_entities.items() if key[0] == relation.target),
                    None,
                )
                if not source or not target or source.id == target.id:
                    continue

                relation_row = db.query(EntityRelation).filter(
                    EntityRelation.source_entity_id == source.id,
                    EntityRelation.target_entity_id == target.id,
                    EntityRelation.relation_type == relation.relation_type,
                ).first()
                if relation_row:
                    relation_row.confidence = max(
                        float(relation_row.confidence or 0),
                        float(relation.properties.get("confidence", 0.5)),
                    )
                    if document_id is not None:
                        docs = list(relation_row.source_documents or [])
                        if document_id not in docs:
                            docs.append(document_id)
                        relation_row.source_documents = docs
                else:
                    db.add(EntityRelation(
                        id=next_relation_id,
                        source_entity_id=source.id,
                        target_entity_id=target.id,
                        relation_type=relation.relation_type,
                        confidence=float(relation.properties.get("confidence", 0.5)),
                        source_documents=[document_id] if document_id is not None else [],
                        metadata_json=relation.properties,
                    ))
                    next_relation_id += 1

            db.commit()
            logger.info(
                f"✅ 已持久化{len(persisted_entities)}个实体、"
                f"{len(relations or [])}个关系到SQLite"
            )

        except Exception as e:
            logger.error(f"SQLite持久化失败: {e}")
            if 'db' in locals():
                db.rollback()

    def _sync_to_neo4j(self):
        """同步图谱数据到Neo4j"""
        try:
            from app.services.neo4j_adapter import Neo4jAdapter

            adapter = Neo4jAdapter()
            if adapter.connect():
                stats = adapter.export_from_networkx(self.graph)
                logger.info(f"✅ 知识图谱已同步到Neo4j: {stats['nodes_created']}个节点, {stats['relationships_created']}个关系")
                adapter.close()
            else:
                logger.warning("⚠️ Neo4j未连接，跳过同步")
        except Exception as e:
            logger.warning(f"⚠️ Neo4j同步失败（非致命）: {e}")

    def get_graph_data(self) -> Dict:
        """获取图谱数据（用于前端可视化）"""
        nodes = []
        edges = []

        # 节点
        for node_id, data in self.graph.nodes(data=True):
            nodes.append({
                'id': node_id,
                'label': data.get('name', node_id),
                'type': data.get('entity_type', 'UNKNOWN'),  # 修复：使用entity_type
                'properties': {k: v for k, v in data.items() if k not in ['name', 'entity_type']}
            })

        # 边
        for source, target, data in self.graph.edges(data=True):
            edges.append({
                'source': source,
                'target': target,
                'label': data.get('relation', 'RELATED'),
                'properties': {k: v for k, v in data.items() if k != 'relation'}
            })

        return {
            'nodes': nodes,
            'edges': edges,
            'stats': {
                'node_count': len(nodes),
                'edge_count': len(edges),
                'updated_at': datetime.now().isoformat()
            }
        }

    def query_related_entities(self, entity_name: str, max_depth: int = 2) -> List[Dict]:
        """查询相关实体"""
        entity_id = self._find_entity_id(entity_name)
        if not entity_id:
            return []

        related = []
        visited = set()

        def traverse(node_id, depth):
            if depth > max_depth or node_id in visited:
                return
            visited.add(node_id)

            # 获取邻居
            for neighbor in self.graph.neighbors(node_id):
                if neighbor not in visited:
                    node_data = self.graph.nodes[neighbor]
                    edge_data = self.graph[node_id][neighbor]

                    related.append({
                        'entity': node_data.get('name'),
                        'type': node_data.get('type'),
                        'relation': list(edge_data.values())[0].get('relation', 'RELATED'),
                        'depth': depth
                    })

                    traverse(neighbor, depth + 1)

        traverse(entity_id, 1)
        return related

    def get_statistics(self) -> Dict:
        """获取图谱统计信息"""
        node_count = self.graph.number_of_nodes()
        edge_count = self.graph.number_of_edges()

        return {
            'node_count': node_count,
            'edge_count': edge_count,
            'entity_types': self._count_entity_types(),
            'relation_types': self._count_relation_types(),
            'density': nx.density(self.graph) if node_count > 0 else 0.0,
            'is_connected': nx.is_weakly_connected(self.graph) if node_count > 0 else False
        }

    def _count_entity_types(self) -> Dict[str, int]:
        """统计实体类型分布"""
        types = {}
        for _, data in self.graph.nodes(data=True):
            entity_type = data.get('entity_type', 'UNKNOWN')  # 修复：使用entity_type
            types[entity_type] = types.get(entity_type, 0) + 1
        return types

    def _count_relation_types(self) -> Dict[str, int]:
        """统计关系类型分布"""
        types = {}
        for _, _, data in self.graph.edges(data=True):
            relation_type = data.get('relation', 'UNKNOWN')
            types[relation_type] = types.get(relation_type, 0) + 1
        return types

    def save_to_file(self, filepath: str):
        """保存图谱到文件"""
        data = nx.node_link_data(self.graph)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"图谱已保存到: {filepath}")

    def load_from_file(self, filepath: str):
        """从文件加载图谱"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.graph = nx.node_link_graph(data)
        logger.info(f"图谱已加载: {self.graph.number_of_nodes()} 节点")

    def export_for_visualization(self, output_path: str):
        """导出为pyvis可视化HTML"""
        try:
            from pyvis.network import Network

            net = Network(height='750px', width='100%', directed=True)

            # 添加节点
            for node_id, data in self.graph.nodes(data=True):
                net.add_node(
                    node_id,
                    label=data.get('name', node_id),
                    title=f"类型: {data.get('entity_type', 'UNKNOWN')}",  # 修复：使用entity_type
                    color=self._get_node_color(data.get('entity_type'))
                )

            # 添加边
            for source, target, data in self.graph.edges(data=True):
                net.add_edge(
                    source,
                    target,
                    label=data.get('relation', ''),
                    title=data.get('relation', 'RELATED')
                )

            net.save_graph(output_path)
            logger.info(f"可视化已保存到: {output_path}")

        except Exception as e:
            logger.error(f"导出可视化失败: {e}")

    def _get_node_color(self, entity_type: str) -> str:
        """根据实体类型返回颜色"""
        colors = {
            'PERSON': '#FF6B6B',      # 红色 - 人物
            'LOCATION': '#4ECDC4',    # 青色 - 地点
            'ORGANIZATION': '#45B7D1', # 蓝色 - 组织
            'CONCEPT': '#FFA07A',     # 橙色 - 概念
            'THING': '#98D8C8',       # 绿色 - 物品
            'EVENT': '#9B59B6',       # 紫色 - 事件
            'DATE': '#F39C12',        # 黄色 - 日期
        }
        return colors.get(entity_type, '#CCCCCC')


# 全局知识图谱服务实例
_knowledge_graph_service = None

def get_knowledge_graph_service() -> KnowledgeGraphService:
    """获取知识图谱服务单例"""
    global _knowledge_graph_service
    if _knowledge_graph_service is None:
        _knowledge_graph_service = KnowledgeGraphService()
    return _knowledge_graph_service


# 测试代码
if __name__ == "__main__":
    # 测试
    kg = KnowledgeGraphService()

    # 测试文本
    test_text = """
    王大爷说，杀猪菜是我们村的传统美食。
    李婶也很喜欢做这道菜。
    村里的祠堂是明代建筑。
    """

    # 提取实体和关系
    entities, relations = kg.extract_entities_and_relations(test_text)

    print(f"\n提取的实体:")
    for e in entities:
        print(f"  - {e.name} ({e.entity_type})")

    print(f"\n提取的关系:")
    for r in relations:
        print(f"  - {r.source} --[{r.relation_type}]--> {r.target}")

    # 添加到图谱
    kg.add_entities_and_relations(entities, relations)

    # 获取统计
    stats = kg.get_statistics()
    print(f"\n图谱统计:")
    print(f"  节点数: {stats['node_count']}")
    print(f"  边数: {stats['edge_count']}")


# ===== 新增方法：补充缺失的功能 =====

def build_knowledge_graph(db: Session, project_id: int) -> Dict[str, Any]:
    """
    从项目的所有 chunks 构建知识图谱

    Args:
        db: 数据库会话
        project_id: 项目 ID

    Returns:
        {
            "nodes": [{"id": str, "label": str, "type": str, "count": int}],
            "edges": [{"source": str, "target": str, "type": str, "weight": float}],
            "statistics": {...}
        }
    """
    from app.models.chunk import Chunk
    from app.services.keyword_extraction import keyword_extraction_service

    logger.info(f"开始构建项目 {project_id} 的知识图谱")

    # 1. 提取项目级关键词（作为主要节点）
    keywords = keyword_extraction_service.extract_from_chunks(db, project_id, top_k=50)

    if not keywords:
        return {"nodes": [], "edges": [], "statistics": {}}

    # 2. 从 chunks 表聚合维度信息
    chunks = db.query(Chunk).filter(Chunk.project_id == project_id).all()

    # 3. 构建节点（大脉络 = dimension_category）
    dimension_counts = {}
    sub_dimension_counts = {}

    for chunk in chunks:
        dim = chunk.dimension_category or "未分类"
        sub_dim = chunk.dimension_sub_category or "其他"

        dimension_counts[dim] = dimension_counts.get(dim, 0) + 1
        sub_dimension_counts[f"{dim}::{sub_dim}"] = sub_dimension_counts.get(f"{dim}::{sub_dim}", 0) + 1

    nodes = []

    # 添加大脉络节点
    for dim, count in dimension_counts.items():
        nodes.append({
            "id": dim,
            "label": dim,
            "type": "dimension",
            "count": count,
            "size": count * 2  # 节点大小与数量成正比
        })

    # 添加子脉络节点
    for key, count in sub_dimension_counts.items():
        dim, sub_dim = key.split("::", 1)
        nodes.append({
            "id": key,
            "label": sub_dim,
            "type": "sub_dimension",
            "parent": dim,
            "count": count,
            "size": count
        })

    # 添加关键词节点（前20个）
    for kw in keywords[:20]:
        nodes.append({
            "id": f"keyword::{kw['word']}",
            "label": kw['word'],
            "type": "keyword",
            "score": kw['score'],
            "size": int(kw['score'] * 10)
        })

    # 4. 构建边（关系）
    edges = []

    # 大脉络 → 子脉络
    for key in sub_dimension_counts.keys():
        dim, sub_dim = key.split("::", 1)
        edges.append({
            "source": dim,
            "target": key,
            "type": "contains",
            "weight": 1.0
        })

    # 5. 统计信息
    statistics = {
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "dimension_count": len(dimension_counts),
        "sub_dimension_count": len(sub_dimension_counts),
        "keyword_count": min(20, len(keywords)),
        "total_chunks": len(chunks)
    }

    logger.info(f"知识图谱构建完成：{statistics['total_nodes']} 个节点，{statistics['total_edges']} 条边")

    return {
        "nodes": nodes,
        "edges": edges,
        "statistics": statistics
    }


def extract_relations(text: str, entities: List[Dict]) -> List[Dict[str, Any]]:
    """
    从文本中提取实体关系

    Args:
        text: 文本内容
        entities: 已识别的实体列表

    Returns:
        [
            {
                "source": str,
                "target": str,
                "relation": str,
                "confidence": float
            }
        ]
    """
    relations = []

    if len(entities) < 2:
        return relations

    # 简单的共现关系提取
    # 如果两个实体在同一段文本中出现，认为它们有关联

    for i, e1 in enumerate(entities):
        for e2 in entities[i+1:]:
            # 检查两个实体是否在文本中接近
            pos1 = text.find(e1['name'])
            pos2 = text.find(e2['name'])

            if pos1 != -1 and pos2 != -1:
                distance = abs(pos1 - pos2)

                # 如果距离小于100字符，认为有关联
                if distance < 100:
                    relations.append({
                        "source": e1['name'],
                        "target": e2['name'],
                        "relation": "相关",
                        "confidence": max(0.5, 1 - distance / 100)
                    })

    return relations
    print(f"  实体类型: {stats['entity_types']}")

    # 导出可视化
    kg.export_for_visualization('/tmp/knowledge_graph.html')
    print(f"\n可视化已保存到: /tmp/knowledge_graph.html")
