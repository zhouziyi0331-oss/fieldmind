"""
RAG混合检索引擎

结合三种检索方式：
1. 向量语义搜索
2. 知识图谱遍历
3. 全文关键词检索

提供统一的检索接口和智能重排序
"""
from typing import List, Dict, Any, Optional, Set
from sqlalchemy.orm import Session
import logging
from collections import defaultdict

from app.services.vector_store import VectorStore
from app.models.knowledge_graph import Entity, Relation

logger = logging.getLogger(__name__)


class GraphQueryEngine:
    """
    知识图谱查询引擎

    支持实体查询、关系遍历、路径查找
    """

    def __init__(self, db: Session):
        self.db = db

    def find_entity(self, entity_name: str) -> Optional[Entity]:
        """查找实体（模糊匹配）"""
        # 精确匹配
        entity = self.db.query(Entity).filter(
            Entity.name == entity_name
        ).first()

        if entity:
            return entity

        # 模糊匹配
        entity = self.db.query(Entity).filter(
            Entity.name.ilike(f"%{entity_name}%")
        ).first()

        return entity

    def find_entities_by_type(self, entity_type: str, limit: int = 10) -> List[Entity]:
        """按类型查找实体"""
        return self.db.query(Entity).filter(
            Entity.entity_type == entity_type
        ).limit(limit).all()

    async def traverse(
        self,
        start_entities: List[str],
        max_depth: int = 2,
        relation_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        图遍历

        从起始实体开始，遍历指定深度的关系网络

        返回：
        {
            "entities": [...],
            "relations": [...],
            "paths": [...]
        }
        """
        visited_entities = set()
        visited_relations = set()
        all_entities = []
        all_relations = []

        # 查找起始实体
        current_entities = []
        for name in start_entities:
            entity = self.find_entity(name)
            if entity:
                current_entities.append(entity)
                visited_entities.add(entity.id)

        # BFS遍历
        for depth in range(max_depth):
            next_entities = []

            for entity in current_entities:
                # 获取出边
                outgoing = self.db.query(Relation).filter(
                    Relation.source_id == entity.id
                ).all()

                # 获取入边
                incoming = self.db.query(Relation).filter(
                    Relation.target_id == entity.id
                ).all()

                for relation in outgoing + incoming:
                    if relation.id in visited_relations:
                        continue

                    # 过滤关系类型
                    if relation_types and relation.relation_type not in relation_types:
                        continue

                    visited_relations.add(relation.id)
                    all_relations.append(self._relation_to_dict(relation))

                    # 添加目标实体
                    target_id = relation.target_id if relation.source_id == entity.id else relation.source_id

                    if target_id not in visited_entities:
                        target_entity = self.db.query(Entity).filter(Entity.id == target_id).first()
                        if target_entity:
                            visited_entities.add(target_id)
                            next_entities.append(target_entity)
                            all_entities.append(self._entity_to_dict(target_entity))

            current_entities = next_entities

            if not current_entities:
                break

        return {
            "entities": all_entities,
            "relations": all_relations,
            "depth": depth + 1
        }

    def find_shortest_path(self, source_name: str, target_name: str, max_depth: int = 5) -> Optional[List]:
        """查找两个实体之间的最短路径"""
        source = self.find_entity(source_name)
        target = self.find_entity(target_name)

        if not source or not target:
            return None

        # BFS查找最短路径
        from collections import deque

        queue = deque([(source.id, [source.id])])
        visited = {source.id}

        while queue:
            current_id, path = queue.popleft()

            if len(path) > max_depth:
                continue

            if current_id == target.id:
                # 找到路径，构建详细信息
                return self._build_path_details(path)

            # 获取相邻实体
            relations = self.db.query(Relation).filter(
                (Relation.source_id == current_id) | (Relation.target_id == current_id)
            ).all()

            for relation in relations:
                next_id = relation.target_id if relation.source_id == current_id else relation.source_id

                if next_id not in visited:
                    visited.add(next_id)
                    queue.append((next_id, path + [next_id]))

        return None

    def _build_path_details(self, entity_ids: List[int]) -> List[Dict]:
        """构建路径详细信息"""
        path = []

        for i in range(len(entity_ids)):
            entity = self.db.query(Entity).filter(Entity.id == entity_ids[i]).first()
            path.append({
                "entity": self._entity_to_dict(entity)
            })

            if i < len(entity_ids) - 1:
                # 查找连接关系
                relation = self.db.query(Relation).filter(
                    ((Relation.source_id == entity_ids[i]) & (Relation.target_id == entity_ids[i+1])) |
                    ((Relation.source_id == entity_ids[i+1]) & (Relation.target_id == entity_ids[i]))
                ).first()

                if relation:
                    path.append({
                        "relation": self._relation_to_dict(relation)
                    })

        return path

    def _entity_to_dict(self, entity: Entity) -> Dict:
        """实体转字典"""
        return {
            "entity_id": entity.entity_id,
            "name": entity.name,
            "type": entity.entity_type,
            "description": entity.description,
            "attributes": entity.attributes
        }

    def _relation_to_dict(self, relation: Relation) -> Dict:
        """关系转字典"""
        return {
            "relation_id": relation.relation_id,
            "source_id": relation.source_id,
            "target_id": relation.target_id,
            "type": relation.relation_type,
            "description": relation.description,
            "properties": relation.properties
        }


class HybridRetriever:
    """
    混合检索引擎

    智能结合三种检索方式，提供最佳结果
    """

    def __init__(
        self,
        db: Session,
        vector_store: VectorStore,
        graph_query: GraphQueryEngine,
        llm_enhancer = None
    ):
        self.db = db
        self.vector_store = vector_store
        self.graph_query = graph_query
        self.llm = llm_enhancer

    async def retrieve(
        self,
        query: str,
        strategy: str = 'hybrid',
        top_k: int = 10,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        统一检索接口

        strategy:
        - vector: 纯向量检索
        - graph: 纯图谱检索
        - keyword: 纯关键词检索
        - hybrid: 混合检索（默认）
        """
        logger.info(f"开始检索，策略: {strategy}, 查询: {query[:100]}")

        if strategy == 'vector':
            return await self._vector_only_retrieve(query, top_k)

        elif strategy == 'graph':
            return await self._graph_only_retrieve(query, top_k)

        elif strategy == 'keyword':
            return await self._keyword_only_retrieve(query, top_k)

        else:  # hybrid
            return await self._hybrid_retrieve(query, top_k, **kwargs)

    async def _vector_only_retrieve(self, query: str, top_k: int) -> List[Dict]:
        """纯向量检索"""
        results = await self.vector_store.similarity_search(query, top_k=top_k)
        return results

    async def _graph_only_retrieve(self, query: str, top_k: int) -> List[Dict]:
        """纯图谱检索"""
        # 1. 从查询中提取实体
        query_entities = await self._extract_query_entities(query)

        if not query_entities:
            logger.warning("查询中未识别到实体，降级到向量检索")
            return await self._vector_only_retrieve(query, top_k)

        # 2. 图遍历
        graph_result = await self.graph_query.traverse(
            query_entities,
            max_depth=2
        )

        # 3. 转换为统一格式
        results = []
        for entity in graph_result['entities']:
            results.append({
                "content": f"{entity['name']}: {entity['description']}",
                "entity_id": entity['entity_id'],
                "type": "entity",
                "score": 0.8,
                "method": "graph"
            })

        return results[:top_k]

    async def _keyword_only_retrieve(self, query: str, top_k: int) -> List[Dict]:
        """纯关键词检索"""
        results = await self.vector_store._keyword_search(query, top_k)
        return results

    async def _hybrid_retrieve(
        self,
        query: str,
        top_k: int,
        vector_weight: float = 0.5,
        graph_weight: float = 0.3,
        keyword_weight: float = 0.2
    ) -> List[Dict]:
        """
        混合检索

        并行执行三种检索，然后融合结果
        """
        # 1. 并行检索
        import asyncio

        vector_task = self._vector_only_retrieve(query, top_k * 2)
        graph_task = self._graph_only_retrieve(query, top_k * 2)
        keyword_task = self._keyword_only_retrieve(query, top_k * 2)

        vector_results, graph_results, keyword_results = await asyncio.gather(
            vector_task,
            graph_task,
            keyword_task,
            return_exceptions=True
        )

        # 处理异常
        if isinstance(vector_results, Exception):
            logger.error(f"向量检索失败: {vector_results}")
            vector_results = []

        if isinstance(graph_results, Exception):
            logger.error(f"图谱检索失败: {graph_results}")
            graph_results = []

        if isinstance(keyword_results, Exception):
            logger.error(f"关键词检索失败: {keyword_results}")
            keyword_results = []

        # 2. 融合结果
        combined = self._fuse_results(
            vector_results,
            graph_results,
            keyword_results,
            vector_weight,
            graph_weight,
            keyword_weight
        )

        # 3. 重排序（如果启用LLM）
        if self.llm and self.llm.enabled:
            reranked = await self._rerank_with_llm(query, combined, top_k)
            return reranked
        else:
            return combined[:top_k]

    def _fuse_results(
        self,
        vector_results: List[Dict],
        graph_results: List[Dict],
        keyword_results: List[Dict],
        vector_weight: float,
        graph_weight: float,
        keyword_weight: float
    ) -> List[Dict]:
        """
        结果融合算法

        使用Reciprocal Rank Fusion (RRF)
        """
        k = 60  # RRF常数

        # 计算每个结果的RRF分数
        all_results = {}

        # 向量结果
        for i, result in enumerate(vector_results):
            key = result.get('chunk_id', f"vector_{i}")
            all_results[key] = {
                **result,
                'rrf_score': vector_weight / (k + i + 1)
            }

        # 图谱结果
        for i, result in enumerate(graph_results):
            key = result.get('entity_id', f"graph_{i}")
            if key in all_results:
                all_results[key]['rrf_score'] += graph_weight / (k + i + 1)
                all_results[key]['method'] = 'hybrid'
            else:
                all_results[key] = {
                    **result,
                    'rrf_score': graph_weight / (k + i + 1)
                }

        # 关键词结果
        for i, result in enumerate(keyword_results):
            key = result.get('chunk_id', f"keyword_{i}")
            if key in all_results:
                all_results[key]['rrf_score'] += keyword_weight / (k + i + 1)
                all_results[key]['method'] = 'hybrid'
            else:
                all_results[key] = {
                    **result,
                    'rrf_score': keyword_weight / (k + i + 1)
                }

        # 按RRF分数排序
        sorted_results = sorted(
            all_results.values(),
            key=lambda x: x['rrf_score'],
            reverse=True
        )

        return sorted_results

    async def _rerank_with_llm(
        self,
        query: str,
        candidates: List[Dict],
        top_k: int
    ) -> List[Dict]:
        """使用LLM重排序"""
        if not self.llm or not self.llm.enabled:
            return candidates

        # 限制候选数量
        candidates_to_rerank = candidates[:top_k * 2]

        # 构建重排序提示词
        candidate_texts = []
        for i, cand in enumerate(candidates_to_rerank):
            candidate_texts.append(f"{i+1}. {cand.get('content', '')[:200]}")

        prompt = f"""
        查询: {query}

        候选结果:
        {chr(10).join(candidate_texts)}

        请按相关性从高到低排序，返回排序后的编号列表。
        只返回JSON格式: {{"ranking": [3, 1, 5, 2, 4, ...]}}
        """

        try:
            response = await self.llm.client.chat.completions.create(
                model=self.llm.model,
                messages=[
                    {"role": "system", "content": "你是一个信息检索专家。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            import json
            result = json.loads(response.choices[0].message.content)
            ranking = result.get("ranking", [])

            # 重排序
            reranked = []
            for rank in ranking:
                if 1 <= rank <= len(candidates_to_rerank):
                    reranked.append(candidates_to_rerank[rank - 1])

            # 添加剩余的候选
            for cand in candidates_to_rerank:
                if cand not in reranked:
                    reranked.append(cand)

            return reranked[:top_k]

        except Exception as e:
            logger.error(f"LLM重排序失败: {str(e)}")
            return candidates[:top_k]

    async def _extract_query_entities(self, query: str) -> List[str]:
        """从查询中提取实体"""
        # 简单版本：查找数据库中已有的实体
        entities = []

        # 查询所有实体名称
        all_entities = self.db.query(Entity).limit(1000).all()

        for entity in all_entities:
            if entity.name.lower() in query.lower():
                entities.append(entity.name)

        # 如果启用LLM，使用更智能的提取
        if self.llm and self.llm.enabled and len(entities) == 0:
            # TODO: 使用LLM提取实体
            pass

        return entities
