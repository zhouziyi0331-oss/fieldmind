"""
文档网络构建器 - 构建多层次的文档关系网络
"""
import logging
from typing import Dict, List, Any, Optional
import networkx as nx
from sqlalchemy.orm import Session
import json

logger = logging.getLogger(__name__)


class DocumentNetworkBuilder:
    """文档网络构建器"""

    def __init__(self):
        logger.info("✅ 文档网络构建器初始化完成")

    def build_unified_network(self, project_id: int, db: Session) -> Dict[str, Any]:
        """
        构建统一的多层网络

        Returns:
            {
                'entities': List[Dict],           # 实体节点
                'documents': List[Dict],          # 文档节点
                'entity_links': List[Dict],       # 实体间关系
                'document_links': List[Dict],     # 文档间关系
                'entity_document_links': List[Dict],  # 实体-文档关联
                'temporal_chain': List[Dict],     # 时间线
                'communities': List[Dict],        # 社区/聚类
                'statistics': Dict                # 网络统计
            }
        """
        try:
            logger.info(f"开始构建项目{project_id}的文档网络")

            # 1. 构建实体网络
            entity_network = self.build_entity_network(project_id, db)

            # 2. 构建文档相似度网络
            doc_similarity_network = self.build_document_similarity_network(project_id, db)

            # 3. 构建时间网络
            temporal_network = self.build_temporal_network(project_id, db)

            # 4. 整合所有网络
            unified_network = {
                'entities': entity_network.get('nodes', []),
                'entity_links': entity_network.get('edges', []),
                'documents': doc_similarity_network.get('nodes', []),
                'document_links': doc_similarity_network.get('edges', []),
                'entity_document_links': entity_network.get('entity_document_links', []),
                'temporal_chain': temporal_network.get('chain', []),
                'communities': doc_similarity_network.get('communities', []),
                'statistics': self._compute_statistics(entity_network, doc_similarity_network, temporal_network)
            }

            logger.info(f"✅ 网络构建完成: {len(unified_network['documents'])}个文档, "
                       f"{len(unified_network['entities'])}个实体, "
                       f"{len(unified_network['document_links'])}个文档关系")

            return unified_network

        except Exception as e:
            logger.error(f"❌ 文档网络构建失败: {e}", exc_info=True)
            return self._empty_network()

    def build_entity_network(self, project_id: int, db: Session) -> Dict[str, Any]:
        """构建实体网络（基于跨文档实体消歧结果）"""
        from app.tools.entity import create_engine

        try:
            # 获取消歧后的实体
            result = cross_document_resolver.resolve_entities(project_id, db)
            canonical_entities = result['canonical_entities']

            if not canonical_entities:
                return {'nodes': [], 'edges': [], 'entity_document_links': []}

            # 构建NetworkX图
            G = nx.Graph()

            # 添加实体节点
            nodes = []
            for entity in canonical_entities:
                G.add_node(entity['canonical_id'], **entity)
                nodes.append({
                    'id': entity['canonical_id'],
                    'name': entity['name'],
                    'type': entity['type'],
                    'mention_count': entity['mention_count'],
                    'document_count': len(entity['document_ids']),
                    'confidence': entity['confidence']
                })

            # 添加边：如果两个实体在同一文档中出现，则连接
            edges = []
            entity_document_links = []

            for i, entity_a in enumerate(canonical_entities):
                docs_a = set(entity_a['document_ids'])

                # 记录实体-文档关联
                for doc_id in docs_a:
                    entity_document_links.append({
                        'entity_id': entity_a['canonical_id'],
                        'document_id': doc_id,
                        'entity_name': entity_a['name'],
                        'entity_type': entity_a['type']
                    })

                # 实体间关系
                for j, entity_b in enumerate(canonical_entities):
                    if i >= j:
                        continue

                    docs_b = set(entity_b['document_ids'])
                    shared_docs = docs_a & docs_b

                    if shared_docs:
                        weight = len(shared_docs)
                        G.add_edge(entity_a['canonical_id'], entity_b['canonical_id'], weight=weight)

                        edges.append({
                            'source': entity_a['canonical_id'],
                            'target': entity_b['canonical_id'],
                            'weight': weight,
                            'shared_documents': len(shared_docs),
                            'relation': 'co-occurs'
                        })

            # 计算中心性
            if len(G.nodes) > 0:
                centrality = nx.degree_centrality(G)
                for node in nodes:
                    node['centrality'] = centrality.get(node['id'], 0)

            return {
                'nodes': nodes,
                'edges': edges,
                'entity_document_links': entity_document_links,
                'graph': G
            }

        except Exception as e:
            logger.error(f"❌ 实体网络构建失败: {e}")
            return {'nodes': [], 'edges': [], 'entity_document_links': []}

    def build_document_similarity_network(self, project_id: int, db: Session) -> Dict[str, Any]:
        """构建文档相似度网络（基于文档关系发现）"""
        from app.models.project import ProjectDocument
        from app.services.document_relation_discovery import document_relation_discovery

        try:
            # 获取所有文档
            documents = db.query(ProjectDocument).filter(
                ProjectDocument.project_id == project_id,
                ProjectDocument.status == "completed"
            ).all()

            if len(documents) < 2:
                return {'nodes': [], 'edges': [], 'communities': []}

            # 发现文档关系
            relations = document_relation_discovery.discover_relations(project_id, db)

            # 构建NetworkX图
            G = nx.Graph()

            # 添加文档节点
            nodes = []
            for doc in documents:
                G.add_node(doc.id, document=doc)
                nodes.append({
                    'id': doc.id,
                    'name': doc.file_name,
                    'type': doc.file_type,
                    'created_at': doc.created_at.isoformat() if doc.created_at else None,
                    'word_count': doc.word_count or 0,
                    'entity_count': len(doc.extracted_entities) if doc.extracted_entities else 0,
                    'status': doc.status
                })

            # 添加边
            edges = []
            for relation in relations:
                source_id = relation['source_document_id']
                target_id = relation['target_document_id']
                relation_type = relation['relation_type']
                confidence = relation['confidence']

                # 为不同关系类型设置不同权重
                weight = confidence
                if relation_type == 'REFERENCES':
                    weight *= 1.5  # 引用关系更重要
                elif relation_type == 'TEMPORAL_SEQUENCE':
                    weight *= 1.2

                if G.has_edge(source_id, target_id):
                    # 如果已存在边，增加权重
                    G[source_id][target_id]['weight'] += weight
                else:
                    G.add_edge(source_id, target_id, weight=weight)

                edges.append({
                    'source': source_id,
                    'target': target_id,
                    'relation_type': relation_type,
                    'confidence': confidence,
                    'evidence': relation.get('evidence', {})
                })

            # 社区检测（文档聚类）
            communities = []
            if len(G.nodes) > 2 and len(G.edges) > 0:
                try:
                    from networkx.algorithms import community
                    communities_iter = community.greedy_modularity_communities(G)

                    for idx, comm in enumerate(communities_iter):
                        doc_ids = list(comm)
                        doc_names = [d['name'] for d in nodes if d['id'] in doc_ids]

                        communities.append({
                            'id': f"community_{idx}",
                            'document_ids': doc_ids,
                            'document_names': doc_names,
                            'size': len(doc_ids)
                        })

                    logger.info(f"发现{len(communities)}个文档社区")
                except Exception as e:
                    logger.warning(f"社区检测失败: {e}")

            # 计算PageRank（识别核心文档）
            if len(G.nodes) > 0 and len(G.edges) > 0:
                try:
                    pagerank = nx.pagerank(G, weight='weight')
                    for node in nodes:
                        node['importance'] = pagerank.get(node['id'], 0)
                except Exception as e:
                    logger.warning(f"PageRank计算失败: {e}")

            return {
                'nodes': nodes,
                'edges': edges,
                'communities': communities,
                'graph': G
            }

        except Exception as e:
            logger.error(f"❌ 文档相似度网络构建失败: {e}")
            return {'nodes': [], 'edges': [], 'communities': []}

    def build_temporal_network(self, project_id: int, db: Session) -> Dict[str, Any]:
        """构建时间网络（文档的时间顺序）"""
        from app.models.project import ProjectDocument
        from app.services.document_relation_discovery import document_relation_discovery

        try:
            documents = db.query(ProjectDocument).filter(
                ProjectDocument.project_id == project_id,
                ProjectDocument.status == "completed"
            ).order_by(ProjectDocument.created_at).all()

            if not documents:
                return {'chain': []}

            # 构建时间链
            chain = []
            discovery = document_relation_discovery

            for doc in documents:
                time = discovery._extract_time(doc)

                chain.append({
                    'document_id': doc.id,
                    'document_name': doc.file_name,
                    'timestamp': time.isoformat() if time else doc.created_at.isoformat(),
                    'position': len(chain)
                })

            logger.info(f"构建时间链: {len(chain)}个节点")

            return {'chain': chain}

        except Exception as e:
            logger.error(f"❌ 时间网络构建失败: {e}")
            return {'chain': []}

    def _compute_statistics(self, entity_network: Dict, doc_network: Dict, temporal_network: Dict) -> Dict:
        """计算网络统计指标"""
        return {
            'entity_count': len(entity_network.get('nodes', [])),
            'entity_link_count': len(entity_network.get('edges', [])),
            'document_count': len(doc_network.get('nodes', [])),
            'document_link_count': len(doc_network.get('edges', [])),
            'community_count': len(doc_network.get('communities', [])),
            'temporal_chain_length': len(temporal_network.get('chain', []))
        }

    def _empty_network(self) -> Dict[str, Any]:
        """返回空网络"""
        return {
            'entities': [],
            'entity_links': [],
            'documents': [],
            'document_links': [],
            'entity_document_links': [],
            'temporal_chain': [],
            'communities': [],
            'statistics': {}
        }


# 全局实例
document_network_builder = DocumentNetworkBuilder()
