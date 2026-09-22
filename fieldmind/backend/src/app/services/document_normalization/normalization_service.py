"""
文档规范化服务 - 统一入口
提供对所有5条规范化规则的统一访问接口

功能：
1. 根据文件类型自动路由到对应规则
2. 集成AI服务增强（Whisper, OCR, BLIP-2）
3. 结果持久化和缓存
4. 事件发布
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path
import time
from datetime import datetime

from .normalization_rules import (
    FileType,
    NormalizationResult,
    AudioToTextRule,
    ImageToTextRule,
    TableToTextRule
)
from .additional_rules import (
    VideoToTextRule,
    DocumentToTextRule
)

logger = logging.getLogger(__name__)


class NormalizationService:
    """文档规范化服务 - 统一协调器"""

    def __init__(self):
        # 初始化所有规则
        self.rules = {
            FileType.AUDIO: AudioToTextRule(),
            FileType.VIDEO: VideoToTextRule(),
            FileType.IMAGE: ImageToTextRule(),
            FileType.TABLE: TableToTextRule(),
            FileType.DOCUMENT: DocumentToTextRule()
        }

        logger.info("✅ 规范化服务初始化完成，已加载5条规则")

    def normalize_document(
        self,
        document_id: int,
        file_type: str,
        file_content: bytes,
        metadata: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
        db_session = None
    ) -> NormalizationResult:
        """
        规范化文档内容的统一入口

        Args:
            document_id: 文档ID
            file_type: 文件类型 (audio/video/image/table/document)
            file_content: 文件二进制内容
            metadata: 文件元数据
            use_cache: 是否使用缓存的规范化结果
            db_session: 数据库会话（用于检查缓存和持久化）

        Returns:
            NormalizationResult: 规范化结果
        """
        start_time = time.time()

        logger.info(f"{'='*60}")
        logger.info(f"🔧 开始规范化处理 - 文档 {document_id}")
        logger.info(f"   文件类型: {file_type}")
        logger.info(f"   文件大小: {len(file_content) / 1024:.2f} KB")
        logger.info(f"{'='*60}")

        # 1. 检查缓存
        if use_cache and db_session:
            cached_result = self._get_cached_result(document_id, db_session)
            if cached_result:
                logger.info(f"✅ 使用缓存的规范化结果")
                return cached_result

        # 2. 识别文件类型并路由
        file_type_enum = self._parse_file_type(file_type)
        if file_type_enum not in self.rules:
            logger.error(f"❌ 不支持的文件类型: {file_type}")
            return self._create_error_result(f"不支持的文件类型: {file_type}")

        # 3. 获取对应的规则
        rule = self.rules[file_type_enum]
        logger.info(f"📋 使用规则: {rule.__class__.__name__}")

        # 4. 执行规范化
        try:
            result = rule.convert(
                file_content=file_content,
                metadata=metadata or {}
            )

            # 5. 添加处理时间
            processing_time = (time.time() - start_time) * 1000
            result.processing_time_ms = int(processing_time)

            # 6. 添加元数据
            result.metadata['document_id'] = document_id
            result.metadata['file_type'] = file_type
            result.metadata['normalized_at'] = datetime.utcnow().isoformat()

            logger.info(f"{'='*60}")
            logger.info(f"✅ 规范化完成 - 文档 {document_id}")
            logger.info(f"   字数: {result.word_count}")
            logger.info(f"   置信度: {result.confidence:.2%}")
            logger.info(f"   处理时间: {processing_time:.0f}ms")
            logger.info(f"   脏数据处理: {len(result.dirty_data_handled)}项")
            logger.info(f"{'='*60}")

            # 7. 持久化结果
            if db_session:
                self._persist_result(document_id, result, db_session)

            # 8. 发布事件
            self._publish_normalization_event(document_id, result)

            return result

        except Exception as e:
            logger.error(f"❌ 规范化失败: {e}", exc_info=True)
            return self._create_error_result(str(e))

    def normalize_from_file_path(
        self,
        document_id: int,
        file_path: str,
        file_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        db_session = None
    ) -> NormalizationResult:
        """
        从文件路径读取并规范化

        Args:
            document_id: 文档ID
            file_path: 文件路径
            file_type: 文件类型
            metadata: 元数据
            db_session: 数据库会话

        Returns:
            NormalizationResult
        """
        try:
            with open(file_path, 'rb') as f:
                file_content = f.read()

            # 自动添加文件名到元数据
            if metadata is None:
                metadata = {}
            metadata['filename'] = Path(file_path).name

            return self.normalize_document(
                document_id=document_id,
                file_type=file_type,
                file_content=file_content,
                metadata=metadata,
                db_session=db_session
            )

        except Exception as e:
            logger.error(f"❌ 读取文件失败: {e}")
            return self._create_error_result(f"读取文件失败: {e}")

    def batch_normalize(
        self,
        documents: list,
        db_session = None,
        max_workers: int = 4
    ) -> Dict[int, NormalizationResult]:
        """
        批量规范化文档

        Args:
            documents: 文档列表 [(document_id, file_type, file_content, metadata), ...]
            db_session: 数据库会话
            max_workers: 最大并行数

        Returns:
            Dict[document_id, NormalizationResult]
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        results = {}

        logger.info(f"🚀 开始批量规范化: {len(documents)}个文档")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_doc = {}

            for doc_id, file_type, file_content, metadata in documents:
                future = executor.submit(
                    self.normalize_document,
                    doc_id,
                    file_type,
                    file_content,
                    metadata,
                    True,  # use_cache
                    db_session
                )
                future_to_doc[future] = doc_id

            for future in as_completed(future_to_doc):
                doc_id = future_to_doc[future]
                try:
                    result = future.result()
                    results[doc_id] = result
                    logger.info(f"✅ 文档 {doc_id} 规范化完成")
                except Exception as e:
                    logger.error(f"❌ 文档 {doc_id} 规范化失败: {e}")
                    results[doc_id] = self._create_error_result(str(e))

        logger.info(f"✅ 批量规范化完成: {len(results)}/{len(documents)}")
        return results

    def get_normalization_status(
        self,
        document_id: int,
        db_session
    ) -> Dict[str, Any]:
        """
        获取文档的规范化状态

        Args:
            document_id: 文档ID
            db_session: 数据库会话

        Returns:
            状态信息
        """
        try:
            from app.models.project import ProjectDocument

            doc = db_session.query(ProjectDocument).filter(
                ProjectDocument.id == document_id
            ).first()

            if not doc:
                return {
                    'normalized': False,
                    'error': '文档不存在'
                }

            # 检查是否已规范化
            has_normalization = (
                doc.extra_data and
                'normalization' in doc.extra_data
            )

            if has_normalization:
                norm_data = doc.extra_data['normalization']
                return {
                    'normalized': True,
                    'method': norm_data.get('method'),
                    'confidence': norm_data.get('confidence'),
                    'word_count': norm_data.get('word_count'),
                    'normalized_at': norm_data.get('normalized_at'),
                    'processing_time_ms': norm_data.get('processing_time_ms')
                }
            else:
                return {
                    'normalized': False,
                    'file_type': doc.file_type,
                    'ready_for_normalization': bool(doc.file_content or doc.storage_path)
                }

        except Exception as e:
            logger.error(f"获取规范化状态失败: {e}")
            return {
                'normalized': False,
                'error': str(e)
            }

    # ========== 私有方法 ==========

    def _parse_file_type(self, file_type: str) -> FileType:
        """解析文件类型字符串为枚举"""
        type_mapping = {
            'audio': FileType.AUDIO,
            'video': FileType.VIDEO,
            'image': FileType.IMAGE,
            'table': FileType.TABLE,
            'document': FileType.DOCUMENT,
            'pdf': FileType.DOCUMENT,
            'doc': FileType.DOCUMENT,
            'docx': FileType.DOCUMENT,
            'txt': FileType.DOCUMENT,
            'mp3': FileType.AUDIO,
            'wav': FileType.AUDIO,
            'm4a': FileType.AUDIO,
            'mp4': FileType.VIDEO,
            'avi': FileType.VIDEO,
            'mov': FileType.VIDEO,
            'jpg': FileType.IMAGE,
            'jpeg': FileType.IMAGE,
            'png': FileType.IMAGE,
            'csv': FileType.TABLE,
            'xlsx': FileType.TABLE,
            'xls': FileType.TABLE
        }

        return type_mapping.get(file_type.lower(), FileType.DOCUMENT)

    def _get_cached_result(
        self,
        document_id: int,
        db_session
    ) -> Optional[NormalizationResult]:
        """从数据库获取缓存的规范化结果"""
        try:
            from app.models.project import ProjectDocument

            doc = db_session.query(ProjectDocument).filter(
                ProjectDocument.id == document_id
            ).first()

            if not doc or not doc.extra_data:
                return None

            norm_data = doc.extra_data.get('normalization')
            if not norm_data:
                return None

            # 重建 NormalizationResult
            result = NormalizationResult()
            result.text_content = doc.text_content or ""
            result.word_count = norm_data.get('word_count', 0)
            result.confidence = norm_data.get('confidence', 1.0)
            result.metadata = norm_data.get('metadata', {})
            result.structure_info = norm_data.get('structure', {})
            result.processing_time_ms = norm_data.get('processing_time_ms', 0)

            return result

        except Exception as e:
            logger.warning(f"获取缓存结果失败: {e}")
            return None

    def _persist_result(
        self,
        document_id: int,
        result: NormalizationResult,
        db_session
    ):
        """持久化规范化结果到数据库"""
        try:
            from app.models.project import ProjectDocument

            doc = db_session.query(ProjectDocument).filter(
                ProjectDocument.id == document_id
            ).first()

            if not doc:
                logger.warning(f"文档 {document_id} 不存在，跳过持久化")
                return

            # 更新文本内容
            doc.text_content = result.text_content

            # 更新元数据
            if doc.extra_data is None:
                doc.extra_data = {}

            doc.extra_data['normalization'] = {
                'method': result.metadata.get('method', 'unknown'),
                'confidence': result.confidence,
                'word_count': result.word_count,
                'structure': result.structure_info,
                'normalized_at': datetime.utcnow().isoformat(),
                'processing_time_ms': result.processing_time_ms,
                'ai_services_used': result.metadata.get('ai_services_used', []),
                'dirty_data_handled': [
                    {
                        'type': item['type'],
                        'action': item['action'],
                        'description': item.get('description', '')
                    }
                    for item in result.dirty_data_handled
                ]
            }

            db_session.commit()
            logger.info(f"✅ 规范化结果已持久化到数据库")

        except Exception as e:
            logger.error(f"❌ 持久化失败: {e}", exc_info=True)
            db_session.rollback()

    def _publish_normalization_event(
        self,
        document_id: int,
        result: NormalizationResult
    ):
        """发布规范化完成事件"""
        try:
            from app.services.event_bus import publish_event, EventTypes

            # 检查EventTypes是否有DOCUMENT_NORMALIZED
            if not hasattr(EventTypes, 'DOCUMENT_NORMALIZED'):
                logger.warning("EventTypes.DOCUMENT_NORMALIZED 未定义，跳过事件发布")
                return

            event_data = {
                'document_id': document_id,
                'project_id': result.metadata.get('project_id'),
                'normalized_text': result.text_content,
                'word_count': result.word_count,
                'confidence': result.confidence,
                'method': result.metadata.get('method'),
                'metadata': {
                    'structure': result.structure_info,
                    'ai_services_used': result.metadata.get('ai_services_used', [])
                }
            }

            publish_event(EventTypes.DOCUMENT_NORMALIZED, event_data)
            logger.info(f"✅ 已发布规范化完成事件")

        except Exception as e:
            logger.warning(f"发布事件失败（非致命）: {e}")

    def _create_error_result(self, error_message: str) -> NormalizationResult:
        """创建错误结果"""
        result = NormalizationResult()
        result.text_content = ""
        result.word_count = 0
        result.confidence = 0.0
        result.metadata = {
            'error': error_message,
            'success': False
        }
        return result


# ========== 全局单例 ==========

_normalization_service: Optional[NormalizationService] = None


def get_normalization_service() -> NormalizationService:
    """获取规范化服务单例"""
    global _normalization_service
    if _normalization_service is None:
        _normalization_service = NormalizationService()
    return _normalization_service


# ========== 便捷函数 ==========

def normalize_document(
    document_id: int,
    file_type: str,
    file_content: bytes,
    metadata: Optional[Dict[str, Any]] = None,
    db_session = None
) -> NormalizationResult:
    """
    便捷函数：规范化文档
    """
    service = get_normalization_service()
    return service.normalize_document(
        document_id=document_id,
        file_type=file_type,
        file_content=file_content,
        metadata=metadata,
        db_session=db_session
    )


def normalize_from_file(
    document_id: int,
    file_path: str,
    file_type: str,
    metadata: Optional[Dict[str, Any]] = None,
    db_session = None
) -> NormalizationResult:
    """
    便捷函数：从文件路径规范化
    """
    service = get_normalization_service()
    return service.normalize_from_file_path(
        document_id=document_id,
        file_path=file_path,
        file_type=file_type,
        metadata=metadata,
        db_session=db_session
    )
