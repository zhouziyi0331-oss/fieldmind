"""
分析服务基类
所有15个分析服务的统一接口和缓存逻辑
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text


class BaseAnalysisService(ABC):
    """分析服务基类"""

    def __init__(self, analysis_type: str):
        self.analysis_type = analysis_type

    @abstractmethod
    async def analyze(
        self,
        project_id: str,
        db_session: Session,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        执行分析

        Args:
            project_id: 项目ID
            db_session: 数据库会话
            force_refresh: 是否强制刷新缓存

        Returns:
            分析结果字典
        """
        pass

    async def get_or_compute(
        self,
        project_id: str,
        db_session: Session,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        获取缓存或计算新结果（核心方法）

        实现"可验证、可分析"的数据流：
        1. 先查缓存（report_analysis_cache表）
        2. 缓存未命中或force_refresh=True，执行analyze()
        3. 存储结果到数据库
        4. 返回结果
        """
        # 1. 检查缓存
        if not force_refresh:
            cached = await self._get_cached_result(project_id, db_session)
            if cached:
                return cached

        # 2. 执行分析
        start_time = datetime.now()
        result_data = await self.analyze(project_id, db_session, force_refresh)
        processing_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        # 3. 获取数据来源
        source_info = await self._get_source_info(project_id, db_session)

        # 4. 存储到缓存表
        cache_record = {
            'project_id': project_id,
            'analysis_type': self.analysis_type,
            'result_data': result_data,
            'metadata': {
                'version': '1.0',
                'service_class': self.__class__.__name__,
            },
            'source_chunks': source_info.get('chunk_ids', []),
            'source_documents': source_info.get('document_ids', []),
            'confidence_score': result_data.get('confidence_score'),
            'processing_time_ms': processing_time_ms,
            'is_valid': True,
            'created_at': datetime.now(),
        }

        await self._save_to_cache(cache_record, db_session)

        return result_data

    async def _get_cached_result(
        self,
        project_id: str,
        db_session: Session
    ) -> Optional[Dict[str, Any]]:
        """从缓存表读取有效结果"""
        query = text("""
            SELECT result_data, confidence_score, processing_time_ms, created_at
            FROM report_analysis_cache
            WHERE project_id = :project_id
              AND analysis_type = :analysis_type
              AND is_valid = 1
            ORDER BY created_at DESC
            LIMIT 1
        """)

        result = db_session.execute(
            query,
            {'project_id': project_id, 'analysis_type': self.analysis_type}
        ).fetchone()

        if result:
            return dict(result._mapping)['result_data']
        return None

    async def _save_to_cache(
        self,
        cache_record: Dict[str, Any],
        db_session: Session
    ):
        """保存分析结果到缓存表"""
        # 先将该项目的此类型分析标记为失效
        invalidate_query = text("""
            UPDATE report_analysis_cache
            SET is_valid = 0,
                invalidated_at = :now,
                invalidation_reason = 'new_analysis_computed'
            WHERE project_id = :project_id
              AND analysis_type = :analysis_type
              AND is_valid = 1
        """)

        db_session.execute(invalidate_query, {
            'project_id': cache_record['project_id'],
            'analysis_type': cache_record['analysis_type'],
            'now': datetime.now()
        })

        # 插入新记录
        import json
        insert_query = text("""
            INSERT INTO report_analysis_cache (
                project_id, analysis_type, result_data, metadata,
                source_chunks, source_documents, confidence_score,
                processing_time_ms, is_valid, created_at
            ) VALUES (
                :project_id, :analysis_type, :result_data, :metadata,
                :source_chunks, :source_documents, :confidence_score,
                :processing_time_ms, :is_valid, :created_at
            )
        """)

        db_session.execute(insert_query, {
            'project_id': cache_record['project_id'],
            'analysis_type': cache_record['analysis_type'],
            'result_data': json.dumps(cache_record['result_data'], ensure_ascii=False),
            'metadata': json.dumps(cache_record['metadata'], ensure_ascii=False),
            'source_chunks': json.dumps(cache_record.get('source_chunks', []), ensure_ascii=False),
            'source_documents': json.dumps(cache_record.get('source_documents', []), ensure_ascii=False),
            'confidence_score': cache_record.get('confidence_score'),
            'processing_time_ms': cache_record['processing_time_ms'],
            'is_valid': cache_record['is_valid'],
            'created_at': cache_record['created_at']
        })

        db_session.commit()

    async def _get_source_info(
        self,
        project_id: str,
        db_session: Session
    ) -> Dict[str, List[str]]:
        """获取项目的数据来源信息（chunks和documents）"""
        # 查询chunks
        chunk_query = text("""
            SELECT id FROM chunks WHERE project_id = :project_id
        """)
        chunk_result = db_session.execute(chunk_query, {'project_id': project_id})
        chunk_ids = [str(row[0]) for row in chunk_result.fetchall()]

        # 查询documents
        doc_query = text("""
            SELECT id FROM documents WHERE project_id = :project_id
        """)
        doc_result = db_session.execute(doc_query, {'project_id': project_id})
        document_ids = [str(row[0]) for row in doc_result.fetchall()]

        return {
            'chunk_ids': chunk_ids,
            'document_ids': document_ids
        }

    @staticmethod
    async def invalidate_all_cache(project_id: str, db_session: Session):
        """使某个项目的所有分析缓存失效（当项目内容更新时调用）"""
        query = text("""
            UPDATE report_analysis_cache
            SET is_valid = 0,
                invalidated_at = :now,
                invalidation_reason = 'project_content_updated'
            WHERE project_id = :project_id AND is_valid = 1
        """)

        db_session.execute(query, {
            'project_id': project_id,
            'now': datetime.now()
        })
        db_session.commit()
