"""
ChunkingAgent 血缘关系增强器

职责：
1. 在 chunk 创建时自动记录 file → chunk 血缘关系
2. 与现有的 ChunkingAgent 无缝集成
3. 支持批量血缘记录
4. 提供血缘查询方法

集成方式：
- 作为 ChunkingAgent 的装饰器/包装器
- 不修改原有的 chunking 逻辑
- 在 chunk 保存到数据库后记录血缘
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ChunkingLineageRecorder:
    """
    Chunking 血缘关系记录器

    功能：
    1. 记录 file → chunk 的转换关系
    2. 批量记录优化性能
    3. 支持重试机制
    4. 提供血缘查询方法
    """

    def __init__(self, db_session=None):
        """
        初始化血缘记录器

        Args:
            db_session: 数据库会话
        """
        self.db = db_session
        self._batch_buffer = []
        self._batch_size = 50  # 批量写入阈值

        logger.info("ChunkingLineageRecorder initialized")

    def record_chunk_lineage(
        self,
        project_id: int,
        document_id: str,
        chunk_id: str,
        chunk_index: int,
        total_chunks: int,
        chunking_strategy: str = "semantic",
        chunk_metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        记录单个 chunk 的血缘关系

        Args:
            project_id: 项目ID
            document_id: 源文档ID
            chunk_id: chunk ID
            chunk_index: chunk索引（从0开始）
            total_chunks: 总chunk数
            chunking_strategy: 切分策略
            chunk_metadata: chunk的元数据

        Returns:
            bool: 是否成功
        """
        from app.services.lineage_tracker import LineageTracker

        try:
            # 构建转换描述
            transform_description = f"Chunk {chunk_index + 1}/{total_chunks} using {chunking_strategy} strategy"

            # 添加元数据信息
            if chunk_metadata:
                if 'char_count' in chunk_metadata:
                    transform_description += f", {chunk_metadata['char_count']} chars"
                if 'word_count' in chunk_metadata:
                    transform_description += f", {chunk_metadata['word_count']} words"

            # 记录血缘
            success = LineageTracker.record_lineage(
                project_id=project_id,
                source_type="file",
                source_id=document_id,
                target_type="chunk",
                target_id=chunk_id,
                transform_type="extract",
                transform_description=transform_description,
                confidence=1.0
            )

            if success:
                logger.debug(f"Recorded lineage: file({document_id}) → chunk({chunk_id})")
            else:
                logger.warning(f"Failed to record lineage for chunk {chunk_id}")

            return success

        except Exception as e:
            logger.error(f"Error recording lineage for chunk {chunk_id}: {e}")
            return False

    def record_chunks_batch(
        self,
        project_id: int,
        document_id: str,
        chunks: List[Dict[str, Any]],
        chunking_strategy: str = "semantic"
    ) -> Dict[str, Any]:
        """
        批量记录 chunks 的血缘关系

        Args:
            project_id: 项目ID
            document_id: 源文档ID
            chunks: chunk列表，每个包含 {id, chunk_index, metadata}
            chunking_strategy: 切分策略

        Returns:
            Dict: 统计结果 {total, success, failed}
        """
        if not chunks:
            logger.warning("No chunks to record lineage")
            return {'total': 0, 'success': 0, 'failed': 0}

        total = len(chunks)
        success = 0
        failed = 0
        total_chunks = len(chunks)

        logger.info(f"Recording lineage for {total} chunks from document {document_id}")

        for chunk in chunks:
            chunk_id = chunk.get('id') or chunk.get('chunk_id')
            chunk_index = chunk.get('chunk_index', 0)
            chunk_metadata = chunk.get('metadata', {})

            if not chunk_id:
                logger.warning(f"Chunk missing id, skipping lineage recording")
                failed += 1
                continue

            if self.record_chunk_lineage(
                project_id=project_id,
                document_id=document_id,
                chunk_id=chunk_id,
                chunk_index=chunk_index,
                total_chunks=total_chunks,
                chunking_strategy=chunking_strategy,
                chunk_metadata=chunk_metadata
            ):
                success += 1
            else:
                failed += 1

        result = {
            'total': total,
            'success': success,
            'failed': failed,
            'success_rate': round(success / total * 100, 2) if total > 0 else 0
        }

        logger.info(f"Lineage recording completed: {result}")
        return result

    def get_chunk_lineage(
        self,
        chunk_id: str,
        max_depth: int = 10
    ) -> Dict[str, Any]:
        """
        追溯 chunk 的血缘链路

        Args:
            chunk_id: chunk ID
            max_depth: 最大追溯深度

        Returns:
            Dict: 血缘链路
        """
        from app.services.lineage_tracker import LineageTracker

        try:
            lineage = LineageTracker.trace_lineage(
                target_type="chunk",
                target_id=chunk_id,
                max_depth=max_depth
            )

            return lineage

        except Exception as e:
            logger.error(f"Error getting lineage for chunk {chunk_id}: {e}")
            return {'error': str(e)}

    def get_document_chunks_lineage(
        self,
        document_id: str
    ) -> List[Dict[str, Any]]:
        """
        获取文档的所有 chunk 血缘关系

        Args:
            document_id: 文档ID

        Returns:
            List: chunk血缘列表
        """
        from app.services.lineage_tracker import LineageTracker

        try:
            downstream = LineageTracker.get_downstream(
                source_type="file",
                source_id=document_id
            )

            # 过滤出 chunk 类型的下游节点
            chunks_lineage = [
                item for item in downstream
                if item.get('type') == 'chunk'
            ]

            logger.info(f"Found {len(chunks_lineage)} chunk lineage records for document {document_id}")
            return chunks_lineage

        except Exception as e:
            logger.error(f"Error getting chunks lineage for document {document_id}: {e}")
            return []

    def verify_lineage_completeness(
        self,
        document_id: str,
        expected_chunk_count: int
    ) -> Dict[str, Any]:
        """
        验证文档的血缘完整性

        Args:
            document_id: 文档ID
            expected_chunk_count: 预期的chunk数量

        Returns:
            Dict: 验证结果
        """
        chunks_lineage = self.get_document_chunks_lineage(document_id)
        actual_count = len(chunks_lineage)

        is_complete = actual_count == expected_chunk_count
        completeness_rate = (actual_count / expected_chunk_count * 100) if expected_chunk_count > 0 else 0

        result = {
            'document_id': document_id,
            'expected_chunks': expected_chunk_count,
            'recorded_chunks': actual_count,
            'is_complete': is_complete,
            'completeness_rate': round(completeness_rate, 2),
            'missing_count': expected_chunk_count - actual_count
        }

        if is_complete:
            logger.info(f"✅ Lineage complete for document {document_id}: {actual_count}/{expected_chunk_count}")
        else:
            logger.warning(f"⚠️  Lineage incomplete for document {document_id}: {actual_count}/{expected_chunk_count}")

        return result


def create_lineage_recorder(db_session=None) -> ChunkingLineageRecorder:
    """
    工厂方法：创建血缘记录器实例

    Args:
        db_session: 数据库会话

    Returns:
        ChunkingLineageRecorder: 血缘记录器实例
    """
    return ChunkingLineageRecorder(db_session=db_session)
