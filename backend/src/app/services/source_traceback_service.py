"""
材料溯源服务 - 分析结果与原始材料的关联追踪
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import logging

from app.models.analysis import (
    AnalysisResult,
    AnalysisStatement,
    StatementSource,
    SourceVerification
)
from app.services.vectorization_service_complete import DocumentChunk, VectorizationService
from app.models.project import ProjectDocument

logger = logging.getLogger(__name__)


class SourceTracebackService:
    """材料溯源服务"""
    def __init__(self, db: Session, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.db = db
        self.vectorizer = VectorizationService()

    def save_analysis_with_sources(
        self,
        project_id: int,
        analysis_type: str,
        title: str,
        parameters: Dict[str, Any],
        result: Dict[str, Any],
        created_by: Optional[str] = None
    ) -> AnalysisResult:
        """
        保存分析结果并自动追溯来源

        Args:
            project_id: 项目ID
            analysis_type: 分析类型
            title: 分析标题
            parameters: 分析参数
            result: 分析结果
            created_by: 创建者ID

        Returns:
            保存的分析结果对象
        """
        # 1. 保存分析结果
        analysis = AnalysisResult(
            project_id=project_id,
            created_by=created_by,
            analysis_type=analysis_type,
            title=title,
            parameters=parameters,
            result=result
        )
        self.db.add(analysis)
        self.db.flush()  # 获取ID但不提交

        # 2. 提取陈述并追溯来源
        statements = self._extract_statements_from_result(result, analysis_type)

        for statement_data in statements:
            # 创建陈述记录
            statement = AnalysisStatement(
                analysis_id=analysis.id,
                statement_text=statement_data['text'],
                statement_type=statement_data.get('type', 'fact'),
                section=statement_data.get('section'),
                order_index=statement_data.get('order'),
                confidence_score=statement_data.get('confidence', 0.8)
            )
            self.db.add(statement)
            self.db.flush()

            # 3. 查找来源
            sources = self._find_sources_for_statement(
                project_id,
                statement_data['text'],
                statement_data.get('keywords', [])
            )

            # 4. 保存来源关联
            for source_data in sources:
                source = StatementSource(
                    statement_id=statement.id,
                    source_type=source_data['type'],
                    source_chunk_id=source_data.get('chunk_id'),
                    source_document_id=source_data.get('document_id'),
                    position_info=source_data.get('position_info'),
                    relevance_score=source_data.get('relevance_score', 0.5),
                    confidence_score=source_data.get('confidence_score', 0.5),
                    quoted_text=source_data.get('quoted_text')
                )
                self.db.add(source)

        self.db.commit()
        logger.info(f"分析结果已保存，ID: {analysis.id}, 陈述数: {len(statements)}")

        return analysis

    def _extract_statements_from_result(
        self,
        result: Dict[str, Any],
        analysis_type: str
    ) -> List[Dict[str, Any]]:
        """
        从分析结果中提取陈述

        根据不同的分析类型，提取不同的陈述
        """
        statements = []

        if analysis_type == 'keyword_search':
            # 关键词搜索：每个匹配结果是一个陈述
            for doc in result.get('documents', []):
                statements.append({
                    'text': doc.get('text', ''),
                    'type': 'quote',
                    'section': 'search_results',
                    'keywords': [result.get('keyword')]
                })

        elif analysis_type == 'creative':
            # 文创分析：每个创意建议是一个陈述
            for idx, possibility in enumerate(result.get('creative_possibilities', [])):
                statements.append({
                    'text': possibility.get('idea', ''),
                    'type': 'recommendation',
                    'section': 'creative_ideas',
                    'order': idx,
                    'keywords': result.get('keywords', [])
                })

        elif analysis_type == 'business':
            # 业态分析：每个业态建议是一个陈述
            for idx, format_data in enumerate(result.get('suggested_formats', [])):
                statements.append({
                    'text': format_data.get('format_name', ''),
                    'type': 'recommendation',
                    'section': 'business_formats',
                    'order': idx,
                    'keywords': []  # 业态分析基于全文
                })

        return statements

    def _find_sources_for_statement(
        self,
        project_id: int,
        statement_text: str,
        keywords: List[str]
    ) -> List[Dict[str, Any]]:
        """
        为陈述查找来源

        使用语义搜索查找最相关的chunks作为来源
        """
        sources = []

        # 1. 尝试使用语义搜索查找相关chunks
        search_results = self.vectorizer.semantic_search(
            query=statement_text,
            project_id=project_id,
            db=self.db,
            top_k=3,
            threshold=0.01  # 降低阈值以适应TF-IDF
        )

        logger.info(f"语义搜索找到 {len(search_results)} 个结果")

        # 2. 如果语义搜索没有结果，使用关键词文本搜索作为fallback
        if not search_results and keywords:
            logger.info(f"语义搜索无结果，使用关键词搜索: {keywords}")
            from app.services.vectorization_service_complete import DocumentChunk

            # 构建关键词搜索
            for keyword in keywords:
                chunks = self.db.query(DocumentChunk).filter(
                    DocumentChunk.project_id == project_id,
                    DocumentChunk.text.like(f'%{keyword}%')
                ).limit(2).all()

                for chunk in chunks:
                    search_results.append({
                        'chunk_id': chunk.chunk_id,
                        'text': chunk.text,
                        'similarity': 0.5,  # 固定相似度
                        'metadata': chunk.chunk_metadata
                    })

            logger.info(f"关键词搜索找到 {len(search_results)} 个结果")

        # 3. 转换为来源格式
        for result in search_results[:3]:  # 最多3个来源
            chunk_id = self._extract_chunk_id(result['chunk_id'])
            if chunk_id:
                from app.services.vectorization_service_complete import DocumentChunk
                chunk = self.db.query(DocumentChunk).filter(
                    DocumentChunk.id == chunk_id
                ).first()

                if chunk:
                    sources.append({
                        'type': 'chunk',
                        'chunk_id': chunk.id,
                        'document_id': chunk.document_id,
                        'position_info': {
                            'start_pos': chunk.start_pos,
                            'end_pos': chunk.end_pos,
                            'chunk_index': chunk.chunk_index
                        },
                        'relevance_score': result['similarity'],
                        'confidence_score': result['similarity'],
                        'quoted_text': result['text'][:200]
                    })

        logger.info(f"最终返回 {len(sources)} 个来源")
        return sources

    def _extract_chunk_id(self, chunk_id_str: str) -> Optional[int]:
        """从chunk_id字符串中提取数字ID"""
        try:
            # chunk_id格式: "doc_123_chunk_0001"
            parts = chunk_id_str.split('_')
            if len(parts) >= 2:
                # 查询数据库获取真实ID
                chunk = self.db.query(DocumentChunk).filter(
                    DocumentChunk.chunk_id == chunk_id_str
                ).first()
                return chunk.id if chunk else None
        except Exception as e:
            logger.error(f"提取chunk ID失败: {e}")
        return None

    def get_statement_sources(
        self,
        statement_id: int
    ) -> List[Dict[str, Any]]:
        """
        获取陈述的所有来源

        Returns:
            来源列表，包含原始材料信息和位置信息
        """
        sources = self.db.query(StatementSource).filter(
            StatementSource.statement_id == statement_id
        ).all()

        result = []
        for source in sources:
            source_data = {
                'id': source.id,
                'type': source.source_type,
                'relevance_score': source.relevance_score,
                'confidence_score': source.confidence_score,
                'quoted_text': source.quoted_text,
                'position_info': source.position_info
            }

            # 获取chunk详情
            if source.source_chunk_id:
                chunk = self.db.query(DocumentChunk).filter(
                    DocumentChunk.id == source.source_chunk_id
                ).first()

                if chunk:
                    source_data['chunk'] = {
                        'id': chunk.id,
                        'chunk_id': chunk.chunk_id,
                        'text': chunk.text,
                        'document_id': chunk.document_id
                    }

            # 获取文档详情
            if source.source_document_id:
                doc = self.db.query(ProjectDocument).filter(
                    ProjectDocument.id == source.source_document_id
                ).first()

                if doc:
                    source_data['document'] = {
                        'id': doc.id,
                        'filename': doc.filename,
                        'file_type': doc.file_type
                    }

            result.append(source_data)

        return result

    def verify_source(
        self,
        source_id: int,
        user_id: str,
        status: str,
        notes: Optional[str] = None
    ) -> SourceVerification:
        """
        用户验证来源

        Args:
            source_id: 来源ID
            user_id: 验证者ID
            status: 验证状态 ('verified', 'questioned', 'incorrect')
            notes: 验证备注

        Returns:
            验证记录
        """
        verification = SourceVerification(
            statement_source_id=source_id,
            verified_by=user_id,
            status=status,
            notes=notes
        )
        self.db.add(verification)
        self.db.commit()

        logger.info(f"来源 {source_id} 已被用户 {user_id} 验证为 {status}")

        return verification

    def get_analysis_with_sources(
        self,
        analysis_id: int
    ) -> Dict[str, Any]:
        """
        获取完整的分析结果（包含溯源信息）
        """
        analysis = self.db.query(AnalysisResult).filter(
            AnalysisResult.id == analysis_id
        ).first()

        if not analysis:
            return None

        # 获取所有陈述
        statements = self.db.query(AnalysisStatement).filter(
            AnalysisStatement.analysis_id == analysis_id
        ).order_by(AnalysisStatement.order_index).all()

        result = {
            'id': analysis.id,
            'project_id': analysis.project_id,
            'analysis_type': analysis.analysis_type,
            'title': analysis.title,
            'result': analysis.result,
            'created_at': analysis.created_at.isoformat() if analysis.created_at else None,
            'statements': []
        }

        for statement in statements:
            # 获取来源
            sources = self.get_statement_sources(statement.id)

            # 获取验证状态 - 修复join问题
            verification_summary = {'verified': 0, 'questioned': 0, 'incorrect': 0}

            if sources:
                source_ids = [s['id'] for s in sources]
                verifications = self.db.query(SourceVerification).filter(
                    SourceVerification.statement_source_id.in_(source_ids)
                ).all()

                for v in verifications:
                    if v.status == 'verified':
                        verification_summary['verified'] += 1
                    elif v.status == 'questioned':
                        verification_summary['questioned'] += 1
                    elif v.status == 'incorrect':
                        verification_summary['incorrect'] += 1

            result['statements'].append({
                'id': statement.id,
                'text': statement.statement_text,
                'type': statement.statement_type,
                'confidence_score': statement.confidence_score,
                'sources': sources,
                'verifications': verification_summary
            })

        return result
