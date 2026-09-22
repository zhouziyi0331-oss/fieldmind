"""
实体分析服务
识别并分析文档中的关键实体（人物、组织、地点、产品等）
"""
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import text
from .base_analysis import BaseAnalysisService


class EntityAnalysisService(BaseAnalysisService):
    """实体分析服务"""
    def __init__(self, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        super().__init__(analysis_type='entity')

    async def analyze(
        self,
        project_id: str,
        db_session: Session,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """执行实体识别与分析"""
        # 查询entities表
        query = text("""
            SELECT id, name, entity_type, properties, confidence
            FROM entities
            WHERE project_id = :project_id
            ORDER BY confidence DESC
        """)
        result = db_session.execute(query, {'project_id': project_id})
        entities = [dict(row._mapping) for row in result.fetchall()]

        # 按类型分组
        entities_by_type = {}
        for entity in entities:
            etype = entity['entity_type']
            if etype not in entities_by_type:
                entities_by_type[etype] = []
            entities_by_type[etype].append({
                'id': entity['id'],
                'name': entity['name'],
                'confidence': entity['confidence']
            })

        return {
            'total_entities': len(entities),
            'entities_by_type': entities_by_type,
            'key_entities': entities[:10],  # Top 10
            'entity_types_count': {k: len(v) for k, v in entities_by_type.items()},
            'confidence_score': 0.88
        }
