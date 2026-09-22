"""
KnowledgeAPI - Agent访问知识库的标准接口

核心原则：
1. Agent 不能直接访问数据库，必须通过这个API
2. 所有返回结果都带 credibility（可信度）
3. 所有结果都可溯源到原始文件
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
import json
import logging

from app.models.project import ProjectDocument
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class KnowledgeAPI:
    """
    Agent访问知识库的唯一入口

    所有方法返回的结果都包含：
    - credibility: 可信度 (0-1)
    - source_trace: 溯源信息 (原始文件位置)
    """

    def __init__(self, db: Session):
        """初始化"""
        self.db = db

    def search(
        self,
        query: str,
        project_id: int,
        top_k: int = 10,
        min_credibility: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        语义检索：返回最相关的 chunk 列表

        Args:
            query: 查询文本
            project_id: 项目ID
            top_k: 返回数量
            min_credibility: 最低可信度阈值

        Returns:
            [{
                chunk_id: int,
                text: str,
                source_file: str,
                source_type: str,
                credibility: float,
                score: float,
                position: {start: int, end: int},
                trace: {file_id: int, file_name: str, char_start: int, char_end: int}
            }]
        """
        # 记录访问日志
        self._log_access('search', {
            'query': query,
            'project_id': project_id,
            'top_k': top_k,
            'min_credibility': min_credibility
        })

        # 查询chunks（简化版，实际应该用向量检索）
        query_sql = text("""
            SELECT
                c.id as chunk_id,
                c.content as text,
                c.source_type,
                c.credibility,
                c.original_file_id,
                c.char_start,
                c.char_end,
                pd.file_name as source_file,
                pd.id as file_id
            FROM chunks c
            LEFT JOIN project_documents pd ON c.original_file_id = pd.id
            WHERE pd.project_id = :project_id
              AND c.credibility >= :min_credibility
              AND c.content LIKE :query_pattern
            ORDER BY c.credibility DESC
            LIMIT :top_k
        """)

        results = self.db.execute(query_sql, {
            'project_id': project_id,
            'min_credibility': min_credibility,
            'query_pattern': f'%{query}%',
            'top_k': top_k
        }).fetchall()

        formatted_results = []
        for row in results:
            formatted_results.append({
                'chunk_id': row.chunk_id,
                'text': row.text,
                'source_file': row.source_file or 'unknown',
                'source_type': row.source_type or 'note',
                'credibility': row.credibility or 0.6,
                'score': 0.8,  # 简化版，实际应该是语义相似度
                'position': {
                    'start': row.char_start or 0,
                    'end': row.char_end or 0
                },
                'trace': {
                    'file_id': row.file_id,
                    'file_name': row.source_file,
                    'char_start': row.char_start or 0,
                    'char_end': row.char_end or 0
                }
            })

        logger.info(f"KnowledgeAPI.search: 项目{project_id} 查询'{query[:30]}...' 返回{len(formatted_results)}个结果")
        return formatted_results

    def get_by_id(self, chunk_id: int) -> Optional[Dict[str, Any]]:
        """
        按 ID 获取 chunk 详情

        Args:
            chunk_id: chunk ID

        Returns:
            {
                chunk_id: int,
                text: str,
                source_file: str,
                source_type: str,
                credibility: float,
                position: {start: int, end: int},
                metadata: dict,
                trace: {file_id: int, file_name: str, position: str}
            }
        """
        self._log_access('get_by_id', {'chunk_id': chunk_id})

        query_sql = text("""
            SELECT
                c.id,
                c.content,
                c.source_type,
                c.credibility,
                c.char_start,
                c.char_end,
                c.metadata,
                c.original_file_id,
                pd.file_name,
                pd.id as file_id
            FROM chunks c
            LEFT JOIN project_documents pd ON c.original_file_id = pd.id
            WHERE c.id = :chunk_id
        """)

        result = self.db.execute(query_sql, {'chunk_id': chunk_id}).fetchone()

        if not result:
            logger.warning(f"KnowledgeAPI.get_by_id: chunk {chunk_id} 不存在")
            return None

        return {
            'chunk_id': result.id,
            'text': result.content,
            'source_file': result.file_name or 'unknown',
            'source_type': result.source_type or 'note',
            'credibility': result.credibility or 0.6,
            'position': {
                'start': result.char_start or 0,
                'end': result.char_end or 0
            },
            'metadata': json.loads(result.metadata) if result.metadata else {},
            'trace': {
                'file_id': result.file_id,
                'file_name': result.file_name,
                'position': f"{result.char_start}-{result.char_end}"
            }
        }

    def get_entities(self, project_id: int) -> List[Dict[str, Any]]:
        """
        获取项目内所有实体

        Args:
            project_id: 项目ID

        Returns:
            [{
                entity_id: int,
                name: str,
                type: str,
                credibility: float,
                source_chunks: [chunk_id1, chunk_id2, ...],
                trace: {...}
            }]
        """
        self._log_access('get_entities', {'project_id': project_id})

        # 查询entities表（假设存在）
        query_sql = text("""
            SELECT
                e.id,
                e.name,
                e.type,
                e.metadata_json
            FROM entities e
            WHERE e.metadata_json LIKE :project_pattern
            LIMIT 100
        """)

        results = self.db.execute(query_sql, {
            'project_pattern': f'%"project_ids": [%{project_id}%]%'
        }).fetchall()

        formatted_results = []
        for row in results:
            metadata = json.loads(row.metadata_json) if row.metadata_json else {}
            formatted_results.append({
                'entity_id': row.id,
                'name': row.name,
                'type': row.type or 'unknown',
                'credibility': metadata.get('credibility', 0.7),
                'source_chunks': metadata.get('chunk_ids', []),
                'trace': {
                    'source': 'entity_extraction',
                    'confidence': metadata.get('confidence', 0.0)
                }
            })

        logger.info(f"KnowledgeAPI.get_entities: 项目{project_id} 返回{len(formatted_results)}个实体")
        return formatted_results

    def get_relations(self, entity_id: int) -> List[Dict[str, Any]]:
        """
        获取某个实体的所有关系

        Args:
            entity_id: 实体ID

        Returns:
            [{
                relation_id: int,
                source_entity: str,
                relation_type: str,
                target_entity: str,
                credibility: float,
                source_chunk: int
            }]
        """
        self._log_access('get_relations', {'entity_id': entity_id})

        # 查询关系表（假设存在entity_relations）
        query_sql = text("""
            SELECT
                er.id,
                e1.name as source_entity,
                er.relation_type,
                e2.name as target_entity,
                er.confidence
            FROM entity_relations er
            JOIN entities e1 ON er.source_entity_id = e1.id
            JOIN entities e2 ON er.target_entity_id = e2.id
            WHERE er.source_entity_id = :entity_id
               OR er.target_entity_id = :entity_id
            LIMIT 50
        """)

        try:
            results = self.db.execute(query_sql, {'entity_id': entity_id}).fetchall()
        except Exception as e:
            logger.warning(f"查询关系失败: {e}")
            return []

        formatted_results = []
        for row in results:
            formatted_results.append({
                'relation_id': row.id,
                'source_entity': row.source_entity,
                'relation_type': row.relation_type,
                'target_entity': row.target_entity,
                'credibility': row.confidence or 0.7,
                'source_chunk': None  # 需要额外查询
            })

        logger.info(f"KnowledgeAPI.get_relations: 实体{entity_id} 返回{len(formatted_results)}个关系")
        return formatted_results

    def trace_citation(self, citation_id: int) -> Optional[Dict[str, Any]]:
        """
        溯源：给定引用ID，返回原始文件位置

        Args:
            citation_id: chunk ID 或 citation ID

        Returns:
            {
                file_id: int,
                file_name: str,
                position: {start: int, end: int},
                source_type: str,
                credibility: float,
                timestamp: str,
                full_path: str  # 如果文件在磁盘上
            }
        """
        self._log_access('trace_citation', {'citation_id': citation_id})

        query_sql = text("""
            SELECT
                c.id as chunk_id,
                c.char_start,
                c.char_end,
                c.source_type,
                c.credibility,
                pd.id as file_id,
                pd.file_name,
                pd.file_path,
                pd.created_at
            FROM chunks c
            JOIN project_documents pd ON c.original_file_id = pd.id
            WHERE c.id = :citation_id
        """)

        result = self.db.execute(query_sql, {'citation_id': citation_id}).fetchone()

        if not result:
            logger.warning(f"KnowledgeAPI.trace_citation: citation {citation_id} 无法溯源")
            return None

        return {
            'file_id': result.file_id,
            'file_name': result.file_name,
            'position': {
                'start': result.char_start or 0,
                'end': result.char_end or 0
            },
            'source_type': result.source_type or 'note',
            'credibility': result.credibility or 0.6,
            'timestamp': result.created_at.isoformat() if result.created_at else None,
            'full_path': result.file_path
        }

    def get_source_credibility(self, source_type: str) -> float:
        """
        获取来源类型的可信度

        Args:
            source_type: 来源类型

        Returns:
            可信度 (0-1)
        """
        query_sql = text("""
            SELECT credibility_base
            FROM knowledge_sources
            WHERE source_type = :source_type
        """)

        result = self.db.execute(query_sql, {'source_type': source_type}).fetchone()

        if result:
            return result.credibility_base

        logger.warning(f"未知的来源类型: {source_type}，返回默认可信度0.5")
        return 0.5

    def _log_access(self, api_method: str, params: Dict[str, Any], agent_trace_id: Optional[int] = None):
        """记录知识库访问日志"""
        try:
            insert_sql = text("""
                INSERT INTO knowledge_access_logs (agent_trace_id, api_method, params, accessed_at)
                VALUES (:agent_trace_id, :api_method, :params, CURRENT_TIMESTAMP)
            """)

            self.db.execute(insert_sql, {
                'agent_trace_id': agent_trace_id,
                'api_method': api_method,
                'params': json.dumps(params, ensure_ascii=False)
            })
            self.db.commit()
        except Exception as e:
            logger.warning(f"记录访问日志失败: {e}")

    def validate_knowledge_quality(self, chunk_id: int) -> Dict[str, Any]:
        """
        验证知识质量

        Args:
            chunk_id: chunk ID

        Returns:
            {
                completeness: float,
                consistency: float,
                citation_valid: bool,
                overall_quality: float
            }
        """
        chunk = self.get_by_id(chunk_id)
        if not chunk:
            return {
                'completeness': 0.0,
                'consistency': 0.0,
                'citation_valid': False,
                'overall_quality': 0.0
            }

        # 简化版质量检查
        completeness = 1.0 if len(chunk['text']) > 50 else 0.5
        consistency = chunk['credibility']
        citation_valid = chunk['trace']['file_id'] is not None

        overall_quality = (completeness + consistency + (1.0 if citation_valid else 0.0)) / 3.0

        return {
            'completeness': completeness,
            'consistency': consistency,
            'citation_valid': citation_valid,
            'overall_quality': overall_quality
        }


# 全局单例
_knowledge_api_instance: Optional[KnowledgeAPI] = None


def get_knowledge_api(db: Session) -> KnowledgeAPI:
    """获取KnowledgeAPI实例"""
    return KnowledgeAPI(db)
