"""
统一管道协调器 (Unified Pipeline Coordinator)
串联整个系统的核心组件

功能：
1. 脏数据通道：接收原始上传文件，提取文本内容
2. 数据契约验证：验证数据质量，确保符合"干净数据"标准
3. 九步知识流水线：实体提取、事件提取、关系发现、本体构建等
4. 事件总线集成：发布流水线事件，触发下游服务
5. 自动缩影生成：通过事件自动触发
6. 知识图谱更新：流水线结果自动写入知识图谱

数据流：
上传 → 提取内容 → 契约验证 → 九步流水线 → 事件发布 → 缩影生成 → 完成
"""

from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import logging
import time
from datetime import datetime
import json

from app.models.project import ProjectDocument
from app.services.data_contract_validator import (
    CleanDataContract,
    DirtyToCleanConverter,
    PipelineGate,
    validate_clean_data,
    convert_dirty_to_clean,
    check_pipeline_gate,
    DataQualityLevel
)
from app.services.boundary1_validator import validate_boundary1, get_boundary1_report
from app.services.boundary2_validator import validate_boundary2, get_boundary2_report
from app.services.event_bus import publish_event, EventTypes

logger = logging.getLogger(__name__)


class DataContractViolation(Exception):
    """数据契约验证失败异常"""
    pass


class PipelineGateRejection(Exception):
    """流水线门控拒绝异常"""
    pass


class PipelineExecutionError(Exception):
    """流水线执行失败异常"""
    pass


class UnifiedPipelineCoordinator:
    """
    统一管道协调器

    这是整个系统的核心协调器，负责串联所有处理步骤：
    - 脏数据通道（文本提取）
    - 数据契约验证
    - 九步知识流水线
    - 事件总线
    - 自动缩影生成
    """

    def __init__(self, db: Session):
        self.db = db
        self.execution_log = []  # 执行日志

    def process_document(self, document_id: int) -> Dict[str, Any]:
        """
        处理文档的完整流程

        Args:
            document_id: 文档ID

        Returns:
            处理结果，包含所有步骤的详细信息
        """
        overall_start = time.time()

        logger.info(f"{'='*60}")
        logger.info(f"🚀 统一管道协调器启动 - 文档 {document_id}")
        logger.info(f"{'='*60}")

        try:
            # ========== 步骤 1: 加载文档 ==========
            doc = self._load_document(document_id)
            project_id = doc.project_id

            # ========== 步骤 2: 检查是否已有提取的内容 ==========
            content = self._get_extracted_content(doc)
            if not content:
                logger.warning(f"⚠️ 文档 {document_id} 没有提取的文本内容，跳过知识流水线")
                return {
                    'success': False,
                    'document_id': document_id,
                    'error': '文档内容为空，无法进入知识流水线',
                    'stage': 'content_extraction'
                }

            # ========== 🆕 步骤 2.5: 文档规范化处理 ==========
            # 对于多模态文件（音频、视频、图片、表格），应用AI增强的规范化处理
            normalization_result = self._normalize_document_content(doc)
            if normalization_result:
                # 使用规范化后的高质量文本
                content = normalization_result.text_content
                logger.info(f"✅ 使用规范化后的文本内容，置信度: {normalization_result.confidence:.2%}")

                self._log_step('文档规范化', {
                    'method': normalization_result.metadata.get('method'),
                    'confidence': normalization_result.confidence,
                    'word_count': normalization_result.word_count,
                    'processing_time_ms': normalization_result.processing_time_ms
                })

            # ========== 步骤 3: 构建脏数据 ==========
            raw_data = self._build_raw_data(doc)
            self._log_step('构建脏数据', {'filename': doc.original_filename})

            # ========== 步骤 3.5: 边界1验证（多模态→统一文本）==========
            logger.info(f"🔍 边界1验证：多模态→统一文本")
            doc_dict = self._doc_to_dict(doc)
            is_boundary1_clean, boundary1_result = validate_boundary1(doc_dict)

            if not is_boundary1_clean:
                logger.warning(f"⚠️ 边界1验证未通过，但允许继续（标记质量问题）")
                logger.warning(get_boundary1_report(doc_dict))
                # 记录边界1验证结果
                self._record_boundary1_validation(doc, boundary1_result, passed=False)
            else:
                logger.info(f"✅ 边界1验证通过：完整性 {boundary1_result['completeness_score']:.1%}")
                self._record_boundary1_validation(doc, boundary1_result, passed=True)

            self._log_step('边界1验证', {
                'passed': is_boundary1_clean,
                'completeness': boundary1_result['completeness_score']
            })

            # ========== 步骤 4: 转换为干净数据 ==========
            clean_data = self._convert_to_clean_data(raw_data, content, document_id)
            self._log_step('转换为干净数据', {
                'word_count': clean_data['word_count'],
                'quality_level': clean_data['quality_level']
            })

            # ========== 步骤 5: 数据契约验证 ==========
            self._validate_contract(clean_data, document_id)
            self._log_step('数据契约验证', {'status': '通过'})

            # ========== 步骤 6: 流水线门控检查 ==========
            self._check_pipeline_gate(clean_data, document_id)
            self._log_step('流水线门控检查', {'status': '通过'})

            # ========== 步骤 7: 记录契约验证结果 ==========
            self._record_contract_validation(doc, clean_data)

            # ========== 步骤 8: 执行九步知识流水线 ==========
            pipeline_result = self._execute_knowledge_pipeline(document_id, project_id)
            self._log_step('九步知识流水线', {
                'success': pipeline_result['success'],
                'steps_completed': pipeline_result['steps_completed'],
                'elapsed_time': pipeline_result['elapsed_time']
            })

            if not pipeline_result['success']:
                raise PipelineExecutionError(
                    f"九步流水线执行失败: {pipeline_result.get('error')}"
                )

            # ========== 步骤 9: 记录流水线执行结果 ==========
            self._record_pipeline_execution(doc, pipeline_result)

            # ========== 步骤 9.5: 边界2验证（文本→可用知识）==========
            logger.info(f"🔍 边界2验证：文本→可用知识")
            doc_dict = self._doc_to_dict(doc)
            is_boundary2_enriched, boundary2_result = validate_boundary2(doc_dict, pipeline_result)

            if not is_boundary2_enriched:
                logger.warning(f"⚠️ 边界2验证未通过：脉络清晰度或可用性不足")
                logger.warning(get_boundary2_report(doc_dict, boundary2_result))
                # 记录边界2验证结果
                self._record_boundary2_validation(doc, boundary2_result, passed=False)
            else:
                logger.info(f"✅ 边界2验证通过：脉络清晰度 {boundary2_result['logic_clarity_score']:.1%}，可用性 {boundary2_result['usability_score']:.1%}")
                self._record_boundary2_validation(doc, boundary2_result, passed=True)

            self._log_step('边界2验证', {
                'passed': is_boundary2_enriched,
                'logic_clarity': boundary2_result['logic_clarity_score'],
                'usability': boundary2_result['usability_score']
            })

            # ========== 步骤 10: 发布流水线完成事件 ==========
            # 注意：事件总线会自动触发缩影生成（通过 event_handler_registry）
            self._publish_pipeline_events(document_id, project_id, pipeline_result)
            self._log_step('发布流水线事件', {
                'events': ['PIPELINE_COMPLETED', 'KNOWLEDGE_UNITS_CREATED']
            })

            # ========== 完成 ==========
            elapsed_time = time.time() - overall_start

            result = {
                'success': True,
                'document_id': document_id,
                'project_id': project_id,
                'stages': {
                    'content_extraction': 'completed',
                    'contract_validation': 'passed',
                    'pipeline_gate': 'passed',
                    'knowledge_pipeline': 'completed',
                    'event_published': 'completed'
                },
                'pipeline_result': pipeline_result,
                'elapsed_time': round(elapsed_time, 2),
                'execution_log': self.execution_log
            }

            logger.info(f"{'='*60}")
            logger.info(f"✅ 统一管道协调器完成 - 文档 {document_id}")
            logger.info(f"   总耗时: {elapsed_time:.2f}秒")
            logger.info(f"   流水线步骤: {pipeline_result['steps_completed']}/{pipeline_result['total_steps']}")
            logger.info(f"{'='*60}")

            return result

        except DataContractViolation as e:
            return self._handle_error(document_id, 'contract_validation', str(e))

        except PipelineGateRejection as e:
            return self._handle_error(document_id, 'pipeline_gate', str(e))

        except PipelineExecutionError as e:
            return self._handle_error(document_id, 'knowledge_pipeline', str(e))

        except Exception as e:
            logger.error(f"❌ 统一管道协调器失败: {e}", exc_info=True)
            return self._handle_error(document_id, 'unknown', str(e))

    # ========== 私有方法：各个处理步骤 ==========

    def _load_document(self, document_id: int) -> ProjectDocument:
        """加载文档"""
        logger.info(f"📂 加载文档 {document_id}")

        doc = self.db.query(ProjectDocument).filter(
            ProjectDocument.id == document_id
        ).first()

        if not doc:
            raise ValueError(f"文档 {document_id} 不存在")

        logger.info(f"   文件名: {doc.original_filename}")
        logger.info(f"   文件类型: {doc.file_type}")
        logger.info(f"   项目ID: {doc.project_id}")

        return doc

    def _get_extracted_content(self, doc: ProjectDocument) -> Optional[str]:
        """获取已提取的文本内容"""
        # 优先从 text_content 字段读取
        if doc.text_content:
            logger.info(f"✅ 找到文档文本内容，长度: {len(doc.text_content)} 字符")
            return doc.text_content

        # 尝试从 extra_data 读取
        if doc.extra_data:
            content = doc.extra_data.get('text_content') or doc.extra_data.get('content')
            if content:
                logger.info(f"✅ 从 extra_data 读取文本内容，长度: {len(content)} 字符")
                return content

        logger.warning(f"⚠️ 文档 {doc.id} 没有文本内容")
        return None

    def _build_raw_data(self, doc: ProjectDocument) -> Dict[str, Any]:
        """构建脏数据（原始上传数据）"""
        return {
            'document_id': doc.id,
            'filename': doc.original_filename,
            'file_type': doc.file_type,
            'file_size': doc.file_size,
            'mime_type': doc.mime_type,
            'created_at': doc.created_at,
            'metadata': doc.extra_data or {}
        }

    def _convert_to_clean_data(
        self,
        raw_data: Dict[str, Any],
        content: str,
        document_id: int
    ) -> Dict[str, Any]:
        """将脏数据转换为干净数据"""
        logger.info(f"🔄 转换脏数据 → 干净数据")

        clean_data = convert_dirty_to_clean(
            raw_data=raw_data,
            extracted_text=content,
            document_id=document_id
        )

        logger.info(f"   字数: {clean_data['word_count']}")
        logger.info(f"   质量等级: {clean_data['quality_level']}")
        logger.info(f"   来源层级: {clean_data['metadata']['source_level']}")

        return clean_data

    def _validate_contract(self, clean_data: Dict[str, Any], document_id: int):
        """验证数据契约"""
        logger.info(f"🔍 验证数据契约")

        is_valid, errors = validate_clean_data(clean_data)

        if not is_valid:
            error_msg = f"数据契约验证失败: {'; '.join(errors)}"
            logger.error(f"❌ {error_msg}")
            raise DataContractViolation(error_msg)

        logger.info(f"✅ 数据契约验证通过")

    def _check_pipeline_gate(self, clean_data: Dict[str, Any], document_id: int):
        """检查流水线门控"""
        logger.info(f"🚪 检查流水线门控")

        can_enter, reason = check_pipeline_gate(clean_data)

        if not can_enter:
            error_msg = f"流水线门控拒绝: {reason}"
            logger.error(f"❌ {error_msg}")
            raise PipelineGateRejection(error_msg)

        logger.info(f"✅ 通过流水线门控检查")

    def _record_contract_validation(self, doc: ProjectDocument, clean_data: Dict[str, Any]):
        """记录契约验证结果到数据库"""
        logger.info(f"💾 记录契约验证结果")

        extra_data = dict(doc.extra_data or {})
        extra_data['contract_validation'] = {
            'status': 'passed',
            'validated_at': datetime.utcnow().isoformat(),
            'quality_level': clean_data['quality_level'],
            'word_count': clean_data['word_count'],
            'source_level': clean_data['metadata']['source_level']
        }

        doc.extra_data = extra_data
        self.db.commit()

        logger.info(f"✅ 契约验证结果已记录")

    def _execute_knowledge_pipeline(
        self,
        document_id: int,
        project_id: int
    ) -> Dict[str, Any]:
        """执行九步知识流水线"""
        logger.info(f"🔬 执行九步知识流水线")
        logger.info(f"   文档ID: {document_id}")
        logger.info(f"   项目ID: {project_id}")

        from app.services.knowledge_pipeline.pipeline_orchestrator import KnowledgePipeline

        pipeline = KnowledgePipeline(self.db)
        pipeline_result = pipeline.run(
            document_id=document_id,
            skip_steps=None  # 执行所有步骤
        )

        if pipeline_result['success']:
            logger.info(f"✅ 九步流水线执行成功")
            logger.info(f"   完成步骤: {pipeline_result['steps_completed']}/{pipeline_result['total_steps']}")
            logger.info(f"   耗时: {pipeline_result['elapsed_time']}秒")
        else:
            logger.error(f"❌ 九步流水线执行失败: {pipeline_result.get('error')}")

        return pipeline_result

    def _record_pipeline_execution(self, doc: ProjectDocument, pipeline_result: Dict[str, Any]):
        """记录流水线执行结果到数据库"""
        logger.info(f"💾 记录流水线执行结果")

        extra_data = dict(doc.extra_data or {})
        extra_data['knowledge_pipeline'] = {
            'status': 'completed' if pipeline_result['success'] else 'failed',
            'executed_at': datetime.utcnow().isoformat(),
            'steps_completed': pipeline_result['steps_completed'],
            'total_steps': pipeline_result['total_steps'],
            'elapsed_time': pipeline_result['elapsed_time'],
            'errors': pipeline_result.get('errors')
        }

        # 记录每一步的详细结果
        if 'results' in pipeline_result:
            step_details = {}
            for step_num, step_result in pipeline_result['results'].items():
                step_name = self._get_step_name(step_num)
                step_details[step_name] = {
                    'step_number': step_num,
                    'status': 'completed',
                    'elapsed_time': step_result.get('step_elapsed_time')
                }

                # 记录关键统计数据
                if step_num == 3:  # 实体提取
                    step_details[step_name]['entities_count'] = step_result.get('entities_count', 0)
                elif step_num == 4:  # 事件提取
                    step_details[step_name]['events_count'] = step_result.get('events_count', 0)
                elif step_num == 5:  # 关系发现
                    step_details[step_name]['relationships_count'] = step_result.get('relationships_count', 0)
                elif step_num == 8:  # 知识单元化
                    step_details[step_name]['knowledge_units_count'] = step_result.get('units_count', 0)

            extra_data['knowledge_pipeline']['step_details'] = step_details

        doc.extra_data = extra_data
        self.db.commit()

        logger.info(f"✅ 流水线执行结果已记录")

    def _publish_pipeline_events(
        self,
        document_id: int,
        project_id: int,
        pipeline_result: Dict[str, Any]
    ):
        """发布流水线完成事件"""
        logger.info(f"📢 发布流水线事件")

        # 1. 发布流水线完成事件
        publish_event(
            event_type=EventTypes.PIPELINE_COMPLETED,
            payload={
                'document_id': document_id,
                'project_id': project_id,
                'steps_completed': pipeline_result['steps_completed'],
                'total_steps': pipeline_result['total_steps'],
                'elapsed_time': pipeline_result['elapsed_time'],
                'timestamp': datetime.utcnow().isoformat()
            },
            publisher='UnifiedPipelineCoordinator'
        )
        logger.info(f"   ✅ 已发布 PIPELINE_COMPLETED 事件")

        # 2. 如果 Step 8（知识单元化）成功，发布 KNOWLEDGE_UNITS_CREATED 事件
        # 这会触发 event_handler_registry 中的缩影生成
        if 8 in pipeline_result.get('results', {}):
            step8_result = pipeline_result['results'][8]

            publish_event(
                event_type=EventTypes.KNOWLEDGE_UNITS_CREATED,
                payload={
                    'document_id': document_id,
                    'project_id': project_id,
                    'units_count': step8_result.get('units_count', 0),
                    'timestamp': datetime.utcnow().isoformat()
                },
                publisher='UnifiedPipelineCoordinator'
            )
            logger.info(f"   ✅ 已发布 KNOWLEDGE_UNITS_CREATED 事件（将触发缩影生成）")

    def _get_step_name(self, step_num: int) -> str:
        """获取步骤名称"""
        step_names = {
            1: 'text_cleaning',
            2: 'structure_analysis',
            3: 'entity_extraction',
            4: 'event_extraction',
            5: 'relationship_discovery',
            6: 'ontology_construction',
            7: 'logical_inference',
            8: 'knowledge_unitization',
            9: 'reader_generation'
        }
        return step_names.get(step_num, f'step_{step_num}')

    def _doc_to_dict(self, doc: ProjectDocument) -> Dict[str, Any]:
        """将文档对象转换为字典"""
        return {
            'id': doc.id,
            'original_filename': doc.original_filename,
            'filename': doc.filename,
            'file_type': doc.file_type,
            'file_size': doc.file_size,
            'mime_type': doc.mime_type,
            'text_content': doc.text_content,
            'word_count': doc.word_count,
            'extra_data': doc.extra_data or {}
        }

    def _record_boundary1_validation(self, doc: ProjectDocument, validation_result: Dict[str, Any], passed: bool):
        """记录边界1验证结果"""
        logger.info(f"💾 记录边界1验证结果")

        extra_data = dict(doc.extra_data or {})
        extra_data['boundary1_validation'] = {
            'status': 'passed' if passed else 'failed',
            'validated_at': datetime.utcnow().isoformat(),
            'modality': validation_result['modality'],
            'completeness_score': validation_result['completeness_score'],
            'missing_items': validation_result.get('missing_items', []),
            'quality_issues': validation_result.get('quality_issues', []),
            'recommendations': validation_result.get('recommendations', [])
        }

        doc.extra_data = extra_data
        self.db.commit()

        logger.info(f"✅ 边界1验证结果已记录")

    def _record_boundary2_validation(self, doc: ProjectDocument, validation_result: Dict[str, Any], passed: bool):
        """记录边界2验证结果"""
        logger.info(f"💾 记录边界2验证结果")

        extra_data = dict(doc.extra_data or {})
        extra_data['boundary2_validation'] = {
            'status': 'passed' if passed else 'failed',
            'validated_at': datetime.utcnow().isoformat(),
            'logic_clarity_score': validation_result['logic_clarity_score'],
            'usability_score': validation_result['usability_score'],
            'missing_elements': validation_result.get('missing_elements', []),
            'quality_report': validation_result.get('quality_report', {}),
            'recommendations': validation_result.get('recommendations', [])
        }

        doc.extra_data = extra_data
        self.db.commit()

        logger.info(f"✅ 边界2验证结果已记录")

    def _normalize_document_content(self, doc: ProjectDocument) -> Optional[Any]:
        """
        对文档内容进行规范化处理

        根据文件类型选择对应的规范化规则:
        - audio → AudioToTextRule (Whisper)
        - video → VideoToTextRule (场景提取 + BLIP-2)
        - image → ImageToTextRule (OCR + Vision)
        - table → TableToTextRule (结构化)
        - document → DocumentToTextRule (文档解析)

        Returns:
            NormalizationResult 或 None（如果不需要规范化或失败）
        """
        try:
            from app.services.document_normalization.normalization_service import get_normalization_service

            # 检查文件类型是否需要规范化处理
            multimodal_types = ['audio', 'video', 'image', 'table']

            if doc.file_type not in multimodal_types:
                logger.info(f"📄 文件类型 {doc.file_type} 不需要特殊规范化处理")
                return None

            # 检查是否已有规范化结果（使用缓存）
            if doc.extra_data and 'normalization' in doc.extra_data:
                logger.info(f"✅ 使用已缓存的规范化结果")
                # 从缓存重建结果对象
                from app.services.document_normalization.normalization_rules import NormalizationResult
                result = NormalizationResult()
                result.text_content = doc.text_content
                result.confidence = doc.extra_data['normalization'].get('confidence', 1.0)
                result.word_count = doc.extra_data['normalization'].get('word_count', 0)
                result.metadata = doc.extra_data['normalization']
                return result

            logger.info(f"🔧 开始规范化处理: 文件类型 {doc.file_type}")

            # 获取文件内容
            file_content = self._get_document_file_content(doc)
            if not file_content:
                logger.warning(f"⚠️ 无法获取文件内容，跳过规范化")
                return None

            # 执行规范化
            norm_service = get_normalization_service()
            result = norm_service.normalize_document(
                document_id=doc.id,
                file_type=doc.file_type,
                file_content=file_content,
                metadata={
                    'filename': doc.original_filename,
                    'mime_type': doc.mime_type,
                    'project_id': doc.project_id
                },
                use_cache=True,
                db_session=self.db
            )

            # 触发RAG集成（异步，不阻塞）
            if result and result.confidence > 0.5:
                self._trigger_rag_integration(doc, result)

            return result

        except Exception as e:
            logger.error(f"❌ 规范化处理失败: {e}", exc_info=True)
            return None

    def _get_document_file_content(self, doc: ProjectDocument) -> Optional[bytes]:
        """
        获取文档的文件内容（二进制）

        Args:
            doc: 文档对象

        Returns:
            文件二进制内容或None
        """
        try:
            # 方法1: 从数据库的file_content字段读取
            if doc.file_content:
                logger.info(f"✅ 从数据库读取文件内容")
                return doc.file_content

            # 方法2: 从对象存储下载
            if doc.storage_path:
                logger.info(f"📥 从对象存储下载文件: {doc.storage_path}")
                from app.core.storage import get_storage
                storage = get_storage()

                # 解析存储路径
                if '/' in doc.storage_path:
                    parts = doc.storage_path.split('/', 1)
                    bucket = parts[0]
                    object_name = parts[1]
                else:
                    bucket = 'documents'
                    object_name = doc.storage_path

                # 下载到临时文件
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False) as tmp:
                    tmp_path = tmp.name

                success = storage.download_file(
                    bucket=bucket,
                    object_name=object_name,
                    file_path=tmp_path
                )

                if success:
                    with open(tmp_path, 'rb') as f:
                        content = f.read()

                    # 清理临时文件
                    import os
                    os.unlink(tmp_path)

                    return content

            logger.warning(f"⚠️ 无法获取文件内容：无file_content且无storage_path")
            return None

        except Exception as e:
            logger.error(f"❌ 获取文件内容失败: {e}", exc_info=True)
            return None

    def _trigger_rag_integration(self, doc: ProjectDocument, normalization_result: Any):
        """
        触发RAG引擎集成（异步，不阻塞主流程）

        将规范化后的文档索引到所有启用的RAG引擎
        """
        try:
            import asyncio
            from app.services.rag_integration_service import get_rag_integration_service

            logger.info(f"🚀 触发RAG多引擎索引（异步）")

            # 创建异步任务，不阻塞主流程
            async def async_index():
                try:
                    rag_service = get_rag_integration_service()
                    result = await rag_service.index_normalized_document(
                        document_id=doc.id,
                        normalized_text=normalization_result.text_content,
                        project_id=str(doc.project_id),
                        metadata={
                            'filename': doc.original_filename,
                            'file_type': doc.file_type,
                            'normalization_method': normalization_result.metadata.get('method'),
                            'confidence': normalization_result.confidence
                        }
                    )
                    logger.info(f"✅ RAG索引完成: {result.get('success_count', 0)}个引擎成功")
                except Exception as e:
                    logger.error(f"❌ RAG索引失败（非致命）: {e}")

            # 在后台运行
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # 如果已有事件循环，创建task
                    asyncio.create_task(async_index())
                else:
                    # 否则直接运行
                    loop.run_until_complete(async_index())
            except RuntimeError:
                # 没有事件循环，创建新的
                asyncio.run(async_index())

        except Exception as e:
            logger.warning(f"⚠️ 触发RAG集成失败（非致命）: {e}")

    def _log_step(self, step_name: str, details: Dict[str, Any]):
        """记录执行步骤到日志"""
        log_entry = {
            'step': step_name,
            'timestamp': datetime.utcnow().isoformat(),
            'details': details
        }
        self.execution_log.append(log_entry)

    def _handle_error(self, document_id: int, stage: str, error: str) -> Dict[str, Any]:
        """统一错误处理"""
        elapsed_time = 0
        if self.execution_log:
            start_time = datetime.fromisoformat(self.execution_log[0]['timestamp'])
            end_time = datetime.utcnow()
            elapsed_time = (end_time - start_time).total_seconds()

        logger.error(f"❌ 处理失败 - 阶段: {stage}, 错误: {error}")

        return {
            'success': False,
            'document_id': document_id,
            'stage': stage,
            'error': error,
            'elapsed_time': round(elapsed_time, 2),
            'execution_log': self.execution_log
        }


# ========== 便捷函数 ==========

def process_document_unified(document_id: int, db: Session) -> Dict[str, Any]:
    """
    使用统一管道协调器处理文档的便捷函数

    Args:
        document_id: 文档ID
        db: 数据库会话

    Returns:
        处理结果
    """
    coordinator = UnifiedPipelineCoordinator(db)
    return coordinator.process_document(document_id)
