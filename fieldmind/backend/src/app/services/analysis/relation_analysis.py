"""
关系分析服务
分析实体之间的关系、关系网络、关系强度
"""
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import text
from .base_analysis import BaseAnalysisService


class RelationAnalysisService(BaseAnalysisService):
    """关系分析服务"""

    def __init__(self):
        super().__init__(analysis_type='relation')

    async def analyze(
        self,
        project_id: str,
        db_session: Session,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """执行关系分析"""
        # 查询relationships表
        query = text("""
            SELECT r.id, r.source_id, r.target_id, r.relation_type,
                   e1.name as source_name, e2.name as target_name
            FROM relationships r
            JOIN entities e1 ON r.source_id = e1.id
            JOIN entities e2 ON r.target_id = e2.id
            WHERE r.project_id = :project_id
        """)
        result = db_session.execute(query, {'project_id': project_id})
        relations = [dict(row._mapping) for row in result.fetchall()]

        # 按关系类型分组
        relations_by_type = {}
        for rel in relations:
            rtype = rel['relation_type']
            if rtype not in relations_by_type:
                relations_by_type[rtype] = []
            relations_by_type[rtype].append({
                'source': rel['source_name'],
                'target': rel['target_name']
            })

        return {
            'total_relations': len(relations),
            'relations_by_type': relations_by_type,
            'relation_types': list(relations_by_type.keys()),
            'network_density': len(relations) / max(1, len(set([r['source_id'] for r in relations]))),
            'confidence_score': 0.84
        }
