"""
AgentCoordinator - 6Agent协调器

统一协调6个专业Agent完成文档处理的完整流程：
1. DocumentAgent - 文档加载与预处理
2. ChunkAgent - 智能分块
3. AnalysisAgent - 深度分析
4. KnowledgeAgent - 知识图谱构建
5. SynthesisAgent - 记忆综合与引用追溯
6. ReportAgent - 综合报告生成

核心原则：
- 真实完整可用：所有Agent必须与真实服务集成
- 流程可追溯：每个阶段都有清晰的输入输出
- 错误可恢复：支持断点续传和失败重试
- 灵活可配置：支持跳过某些阶段或自定义流程
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import logging
import uuid
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.tools.vectorization.vectorization_service_complete import VectorizationService



logger = logging.getLogger(__name__)


class PipelineStage(str, Enum):
    """流水线阶段"""
    DOCUMENT_LOAD = "document_load"      # 文档加载
    CHUNK = "chunk"                      # 智能分块
    ANALYSIS = "analysis"                # 深度分析
    KNOWLEDGE = "knowledge"              # 知识图谱
    SYNTHESIS = "synthesis"              # 综合合成
    REPORT = "report"                    # 报告生成
    COMPLETE = "complete"                # 完成


class PipelineMode(str, Enum):
    """流水线模式"""
    FULL = "full"                        # 完整流程（所有6个阶段）
    QUICK = "quick"                      # 快速模式（跳过知识图谱）
    ANALYSIS_ONLY = "analysis_only"      # 仅分析（文档+分块+分析）
    REPORT_ONLY = "report_only"          # 仅报告（假设前面都已完成）
    CUSTOM = "custom"                    # 自定义阶段列表


@dataclass
class StageResult:
    """单个阶段的执行结果"""
    stage: PipelineStage
    success: bool
    duration_seconds: float
    output: Dict[str, Any]
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineResult:
    """完整流水线执行结果"""
    project_id: int
    mode: PipelineMode
    start_time: datetime
    end_time: datetime
    total_duration_seconds: float
    success: bool
    completed_stages: List[PipelineStage]
    stage_results: Dict[PipelineStage, StageResult]
    final_report: Optional[Dict[str, Any]] = None
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class AgentCoordinator:
    """
    6Agent协调器

    协调所有Agent完成从文档到报告的完整流程
    """

    def __init__(
        self,
        default_mode: PipelineMode = PipelineMode.FULL,
        enable_retry: bool = True,
        max_retries: int = 3,
        enable_checkpoint: bool = True,
        max_parallel_workers: int = 5
    ):
        """
        初始化Coordinator

        Args:
            default_mode: 默认流水线模式
            enable_retry: 启用失败重试
            max_retries: 最大重试次数
            enable_checkpoint: 启用断点续传
            max_parallel_workers: 并行处理文档的最大线程数
        """
        self.default_mode = default_mode
        self.enable_retry = enable_retry
        self.max_retries = max_retries
        self.enable_checkpoint = enable_checkpoint
        self.max_parallel_workers = max_parallel_workers

        # 懒加载所有Agent
        self._document_agent = None
        self._chunk_agent = None
        self._analysis_agent = None
        self._knowledge_agent = None
        self._synthesis_agent = None
        self._report_agent = None

    def _get_document_agent(self):
        """懒加载IngestionAgent (DocumentAgent)"""
        if self._document_agent is None:
            from app.agents.v2.ingestion_agent import IngestionAgent
            self._document_agent = IngestionAgent()
            logger.info("✅ IngestionAgent已加载")
        return self._document_agent

    def _get_chunk_agent(self):
        """懒加载ChunkingAgent (ChunkAgent)"""
        if self._chunk_agent is None:
            from app.agents.v2.chunking_agent import ChunkingAgent
            self._chunk_agent = ChunkingAgent()
            logger.info("✅ ChunkingAgent已加载")
        return self._chunk_agent

    def _get_analysis_agent(self):
        """懒加载VectorizationAgent (AnalysisAgent)"""
        if self._analysis_agent is None:
            from app.agents.v2.vectorization_agent import VectorizationAgent
            self._analysis_agent = VectorizationAgent()
            logger.info("✅ VectorizationAgent已加载")
        return self._analysis_agent

    def _get_knowledge_agent(self):
        """懒加载KnowledgeAgent"""
        if self._knowledge_agent is None:
            from app.agents.v2.knowledge_agent import KnowledgeAgent
            self._knowledge_agent = KnowledgeAgent()
        return self._knowledge_agent

    def _get_synthesis_agent(self):
        """懒加载SynthesisAgent"""
        if self._synthesis_agent is None:
            from app.agents.v2.synthesis_agent import SynthesisAgent
            self._synthesis_agent = SynthesisAgent()
        return self._synthesis_agent

    def _get_report_agent(self):
        """懒加载ReportAgent"""
        if self._report_agent is None:
            from app.agents.v2.report_agent import ReportAgent
            self._report_agent = ReportAgent()
        return self._report_agent

    def process_project(
        self,
        project_id: int,
        db_session,
        mode: Optional[PipelineMode] = None,
        custom_stages: Optional[List[PipelineStage]] = None,
        start_from_stage: Optional[PipelineStage] = None,
        report_level: Optional[str] = None,
        resume_execution_id: Optional[str] = None
    ) -> PipelineResult:
        """
        处理项目的完整流水线

        Args:
            project_id: 项目ID
            db_session: 数据库会话
            mode: 流水线模式（None则使用默认）
            custom_stages: 自定义阶段列表（mode=CUSTOM时使用）
            start_from_stage: 从某个阶段开始（断点续传）
            report_level: 报告等级（level_1/level_2/level_3/dynamic）
            resume_execution_id: 恢复指定的执行ID（自动断点续传）

        Returns:
            PipelineResult对象
        """
        mode = mode or self.default_mode
        start_time = datetime.now()

        # 🔥 新增：自动恢复上次执行
        if resume_execution_id:
            return self._resume_execution(resume_execution_id, db_session, report_level)

        # 🔥 新增：自动检测未完成的执行
        if self.enable_checkpoint:
            unfinished_exec = self._find_unfinished_execution(project_id, db_session)
            if unfinished_exec:
                logger.info(f"🔍 发现未完成的执行: {unfinished_exec.execution_id}，自动恢复中...")
                return self._resume_execution(unfinished_exec.execution_id, db_session, report_level)

        # 🔥 新增：创建执行记录
        execution_id = str(uuid.uuid4())
        stages = self._determine_stages(mode, custom_stages)

        # DISABLED:         pipeline_exec = PipelineExecution(
        # DISABLED: project_id=project_id,
        # DISABLED: execution_id=execution_id,
        # DISABLED: mode=mode.value,
        # DISABLED: status='running',
        # DISABLED: total_stages=len(stages),
        # DISABLED: completed_stages=0,
        # DISABLED: progress_percentage=0.0,
        # DISABLED: start_time=start_time,
        # DISABLED: metadata={'stages': [s.value for s in stages]}
        # DISABLED:         )
        db_session.add(pipeline_exec)
        db_session.commit()

        logger.info(f"🚀 开始处理项目{project_id}（模式={mode}，执行ID={execution_id}）")

        # 断点续传：从指定阶段开始
        if start_from_stage and start_from_stage in stages:
            start_idx = stages.index(start_from_stage)
            stages = stages[start_idx:]
            logger.info(f"📍 从断点续传: {start_from_stage}")

        # 执行流水线
        stage_results = {}
        completed_stages = []
        errors = []
        pipeline_success = True

        for stage in stages:
            logger.info(f"▶️ 执行阶段: {stage.value}")

            # 🔥 新增：更新执行状态
            self._update_execution_progress(
                execution_id=execution_id,
                current_stage=stage.value,
                completed_stages=len(completed_stages),
                total_stages=len(stages),
                db_session=db_session
            )

            stage_result = self._execute_stage(
                stage=stage,
                project_id=project_id,
                db_session=db_session,
                previous_results=stage_results,
                report_level=report_level,
                execution_id=execution_id  # 传递execution_id
            )

            # 🔥 新增：保存阶段结果到数据库
            self._save_stage_result(execution_id, stage, stage_result, db_session)

            stage_results[stage] = stage_result
            completed_stages.append(stage)

            if not stage_result.success:
                logger.error(f"❌ 阶段{stage.value}失败: {stage_result.errors}")
                errors.extend(stage_result.errors)
                pipeline_success = False

                # 🔥 新增：更新执行状态为failed
                self._update_execution_status(
                    execution_id=execution_id,
                    status='failed',
                    error_message='; '.join(stage_result.errors),
                    db_session=db_session
                )

                # 如果不启用重试或重试失败，则停止流水线
                if not self.enable_retry:
                    break

                # 尝试智能重试
                retry_success = self._retry_stage_smart(
                    stage=stage,
                    project_id=project_id,
                    db_session=db_session,
                    previous_results=stage_results,
                    report_level=report_level,
                    execution_id=execution_id,
                    error=stage_result.errors[0] if stage_result.errors else "Unknown error"
                )

                if not retry_success:
                    logger.error(f"❌ 阶段{stage.value}重试失败，停止流水线")
                    break
                else:
                    logger.info(f"✅ 阶段{stage.value}重试成功")
                    pipeline_success = True

        end_time = datetime.now()
        total_duration = (end_time - start_time).total_seconds()

        # 🔥 新增：更新最终执行状态
        final_status = 'completed' if pipeline_success else 'failed'
        self._update_execution_status(
            execution_id=execution_id,
            status=final_status,
            end_time=end_time,
            total_duration=total_duration,
            db_session=db_session
        )

        # 提取最终报告
        final_report = None
        if PipelineStage.REPORT in stage_results:
            report_result = stage_results[PipelineStage.REPORT]
            if report_result.success:
                final_report = report_result.output

        result = PipelineResult(
            project_id=project_id,
            mode=mode,
            start_time=start_time,
            end_time=end_time,
            total_duration_seconds=total_duration,
            success=pipeline_success,
            completed_stages=completed_stages,
            stage_results=stage_results,
            final_report=final_report,
            errors=errors,
            metadata={
                'stages_count': len(stages),
                'completed_count': len(completed_stages),
                'checkpoint_enabled': self.enable_checkpoint,
                'execution_id': execution_id
            }
        )

        status = "✅ 成功" if pipeline_success else "❌ 失败"
        logger.info(f"{status} 项目{project_id}处理完成（耗时={total_duration:.2f}秒）")

        return result

    def _determine_stages(
        self,
        mode: PipelineMode,
        custom_stages: Optional[List[PipelineStage]] = None
    ) -> List[PipelineStage]:
        """确定要执行的阶段列表"""
        if mode == PipelineMode.CUSTOM and custom_stages:
            return custom_stages

        if mode == PipelineMode.FULL:
            return [
                PipelineStage.DOCUMENT_LOAD,
                PipelineStage.CHUNK,
                PipelineStage.ANALYSIS,
                PipelineStage.KNOWLEDGE,
                PipelineStage.SYNTHESIS,
                PipelineStage.REPORT
            ]

        if mode == PipelineMode.QUICK:
            return [
                PipelineStage.DOCUMENT_LOAD,
                PipelineStage.CHUNK,
                PipelineStage.ANALYSIS,
                PipelineStage.SYNTHESIS,
                PipelineStage.REPORT
            ]

        if mode == PipelineMode.ANALYSIS_ONLY:
            return [
                PipelineStage.DOCUMENT_LOAD,
                PipelineStage.CHUNK,
                PipelineStage.ANALYSIS
            ]

        if mode == PipelineMode.REPORT_ONLY:
            return [PipelineStage.REPORT]

        # 默认返回完整流程
        return [
            PipelineStage.DOCUMENT_LOAD,
            PipelineStage.CHUNK,
            PipelineStage.ANALYSIS,
            PipelineStage.KNOWLEDGE,
            PipelineStage.SYNTHESIS,
            PipelineStage.REPORT
        ]

    def _execute_stage(
        self,
        stage: PipelineStage,
        project_id: int,
        db_session,
        previous_results: Dict[PipelineStage, StageResult],
        report_level: Optional[str] = None,
        execution_id: Optional[str] = None
    ) -> StageResult:
        """执行单个阶段"""
        import time

        stage_start = time.time()

        try:
            if stage == PipelineStage.DOCUMENT_LOAD:
                output = self._stage_document_load(project_id, db_session)
            elif stage == PipelineStage.CHUNK:
                output = self._stage_chunk(project_id, db_session, previous_results)
            elif stage == PipelineStage.ANALYSIS:
                output = self._stage_analysis(project_id, db_session, previous_results)
            elif stage == PipelineStage.KNOWLEDGE:
                output = self._stage_knowledge(project_id, db_session, previous_results)
            elif stage == PipelineStage.SYNTHESIS:
                output = self._stage_synthesis(project_id, db_session, previous_results)
            elif stage == PipelineStage.REPORT:
                output = self._stage_report(project_id, db_session, previous_results, report_level)
            else:
                raise ValueError(f"未知阶段: {stage}")

            duration = time.time() - stage_start

            return StageResult(
                stage=stage,
                success=True,
                duration_seconds=duration,
                output=output
            )

        except Exception as e:
            duration = time.time() - stage_start
            logger.error(f"❌ 阶段{stage.value}执行失败: {e}", exc_info=True)

            return StageResult(
                stage=stage,
                success=False,
                duration_seconds=duration,
                output={},
                errors=[str(e)]
            )

    def _retry_stage(
        self,
        stage: PipelineStage,
        project_id: int,
        db_session,
        previous_results: Dict[PipelineStage, StageResult],
        report_level: Optional[str] = None
    ) -> bool:
        """重试失败的阶段"""
        for attempt in range(self.max_retries):
            logger.info(f"🔄 重试阶段{stage.value}（第{attempt + 1}/{self.max_retries}次）")

            result = self._execute_stage(
                stage=stage,
                project_id=project_id,
                db_session=db_session,
                previous_results=previous_results,
                report_level=report_level
            )

            if result.success:
                previous_results[stage] = result
                return True

        return False

    # ==================== 各阶段具体实现 ====================

    def _stage_document_load(self, project_id: int, db_session) -> Dict[str, Any]:
        """阶段1: 文档加载"""
        agent = self._get_document_agent()

        # 从数据库加载项目文档
        from app.models.project import ProjectDocument

        docs = db_session.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id
        ).all()

        logger.info(f"📄 加载了{len(docs)}个文档")

        return {
            'document_count': len(docs),
            'documents': docs,
            'project_id': project_id
        }

    def _stage_chunk(
        self,
        project_id: int,
        db_session,
        previous_results: Dict[PipelineStage, StageResult]
    ) -> Dict[str, Any]:
        """阶段2: 智能分块（并行处理）"""
        # 获取文档
        doc_result = previous_results.get(PipelineStage.DOCUMENT_LOAD)
        if not doc_result or not doc_result.success:
            raise ValueError("文档加载阶段未完成")

        docs = doc_result.output.get('documents', [])

        if not docs:
            raise ValueError("文档加载阶段没有返回文档，无法进行分块")

        # 🔥 并行处理：使用ThreadPoolExecutor
        total_chunks = 0
        all_chunk_ids = []
        failed_docs = []

        logger.info(f"🚀 开始并行处理 {len(docs)} 个文档（最大并发={self.max_parallel_workers}）")

        with ThreadPoolExecutor(max_workers=self.max_parallel_workers) as executor:
            # 提交所有任务
            future_to_doc = {
                executor.submit(self._process_document_parallel, doc, project_id, db_session): doc
                for doc in docs
            }

            # 收集结果
            for future in as_completed(future_to_doc):
                doc = future_to_doc[future]
                try:
                    result = future.result()
                    if result.get('success'):
                        total_chunks += result['chunk_count']
                        all_chunk_ids.extend(result['chunk_ids'])
                    else:
                        failed_docs.append({
                            'document_id': doc.id,
                            'error': result.get('error', 'Unknown error')
                        })
                        logger.error(f"❌ 文档 {doc.id} 处理失败: {result.get('error')}")
                except Exception as e:
                    failed_docs.append({
                        'document_id': doc.id,
                        'error': str(e)
                    })
                    logger.error(f"❌ 文档 {doc.id} 处理异常: {e}")

        logger.info(f"✂️ 并行处理完成：{total_chunks}个chunks已存储到数据库（成功={len(docs) - len(failed_docs)}/{len(docs)}）")

        if failed_docs:
            logger.warning(f"⚠️ {len(failed_docs)} 个文档处理失败")

        return {
            'chunk_count': total_chunks,
            'document_count': len(docs),
            'stored_chunk_ids': all_chunk_ids,
            'failed_documents': failed_docs,
            'success_rate': (len(docs) - len(failed_docs)) / len(docs) if docs else 0
        }

    def _stage_analysis(
        self,
        project_id: int,
        db_session,
        previous_results: Dict[PipelineStage, StageResult]
    ) -> Dict[str, Any]:
        """阶段3: 向量化分析

        优化：从数据库读取已存储的chunks，避免重复传递大量内存数据
        """
        agent = self._get_analysis_agent()

        # 获取分块结果（只需要chunk_ids）
        chunk_result = previous_results.get(PipelineStage.CHUNK)
        if not chunk_result or not chunk_result.success:
            raise ValueError("分块阶段未完成")

        stored_chunk_ids = chunk_result.output.get('stored_chunk_ids', [])

        if not stored_chunk_ids:
            raise ValueError("分块阶段没有返回chunk_ids，无法进行向量化分析")

        # 从数据库读取chunks（避免内存传递）
        from app.models.pipeline_state import DocumentChunk
        db_chunks = db_session.query(DocumentChunk).filter(
            DocumentChunk.id.in_(stored_chunk_ids)
        ).all()

        # 转换为字典格式供VectorizationAgent使用
        chunk_dicts = [
            {
                'chunk_id': chunk.id,
                'text': chunk.chunk_text,
                'metadata': chunk.extra_metadata or {}
            }
            for chunk in db_chunks
        ]

        # 使用VectorizationAgent进行向量化和Entity提取
        result = agent.vectorize_chunks(
            chunks=chunk_dicts,
            store_to_db=True,
            project_id=project_id,
            db_session=db_session
        )

        logger.info(f"📊 完成了{result.success_count}个chunk的向量化和Entity提取")

        return {
            'vectorized_count': result.success_count,
            'failed_count': result.failed_count,
            'embedding_model': result.embedding_model,
            'embedding_dim': result.embedding_dim
        }

    def _stage_knowledge(
        self,
        project_id: int,
        db_session,
        previous_results: Dict[PipelineStage, StageResult]
    ) -> Dict[str, Any]:
        """阶段4: 知识图谱构建"""
        agent = self._get_knowledge_agent()

        # 构建知识图谱
        result = agent.build_knowledge_graph(
            project_id=project_id,
            db_session=db_session
        )

        logger.info(f"🕸️ 构建了知识图谱（实体={result.get('entity_count', 0)}个）")

        return result

    def _stage_synthesis(
        self,
        project_id: int,
        db_session,
        previous_results: Dict[PipelineStage, StageResult]
    ) -> Dict[str, Any]:
        """
        阶段5: 综合合成

        Phase 5更新：调用generate_synthesis_insights()生成综合洞察并存储到数据库
        """
        agent = self._get_synthesis_agent()

        # Phase 5: 调用新的generate_synthesis_insights()方法
        # 这会运行15个分析服务、整合记忆系统、生成综合洞察并存储到synthesis_results表
        result = agent.generate_synthesis_insights(
            project_id=str(project_id),
            db_session=db_session,
            query="生成项目综合报告",
            include_business_analysis=True  # 包含15个商业分析服务
        )

        logger.info(f"🔗 Phase 5综合合成完成（洞察={len(result['key_insights'])}个，建议={len(result['recommendations'])}个）")
        logger.info(f"   - Synthesis Result ID: {result['synthesis_result_id']}")
        logger.info(f"   - 分析服务运行: {result['metadata']['analyses_run']}个")
        logger.info(f"   - 置信度: {result['confidence_score']}")

        return {
            'synthesis_result_id': result['synthesis_result_id'],  # 关键：传递给report阶段
            'key_insights_count': len(result['key_insights']),
            'recommendations_count': len(result['recommendations']),
            'decision_factors_count': len(result['decision_factors']),
            'confidence_score': result['confidence_score'],
            'analyses_run': result['metadata']['analyses_run'],
            'context_summary': result['context_summary']
        }

    def _stage_report(
        self,
        project_id: int,
        db_session,
        previous_results: Dict[PipelineStage, StageResult],
        report_level: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        阶段6: 报告生成

        Phase 5更新：调用generate_three_layer_report()生成三层报告并存储到数据库
        """
        from app.agents.v2.report_agent import ReportLevel, ReportFormat

        agent = self._get_report_agent()

        # Phase 5: 获取synthesis阶段生成的synthesis_result_id
        synthesis_stage_result = previous_results.get(PipelineStage.SYNTHESIS)
        if not synthesis_stage_result or not synthesis_stage_result.success:
            logger.warning("⚠️ Synthesis阶段未成功完成，使用传统报告生成方式")

            # 回退到传统报告生成
            level = ReportLevel(report_level) if report_level else ReportLevel.DYNAMIC
            result = agent.generate_report(
                project_id=project_id,
                db_session=db_session,
                report_level=level,
                export_formats=[ReportFormat.MARKDOWN, ReportFormat.JSON]
            )

            logger.info(f"📝 生成传统报告（成功={'✅' if result.success else '❌'}）")

            return {
                'success': result.success,
                'report_title': result.report_title,
                'section_count': len(result.sections),
                'validation_passed': result.metadata.validation_passed,
                'exports': list(result.export_formats.keys()),
                'report_type': 'traditional'
            }

        # Phase 5: 使用synthesis_result_id生成三层报告
        synthesis_result_id = synthesis_stage_result.output.get('synthesis_result_id')

        if not synthesis_result_id:
            raise ValueError("Synthesis阶段未返回synthesis_result_id，无法生成三层报告")

        logger.info(f"📝 开始生成三层报告（基于Synthesis Result ID: {synthesis_result_id}）")

        # 调用新的generate_three_layer_report()方法
        result = agent.generate_three_layer_report(
            project_id=str(project_id),
            db_session=db_session,
            synthesis_result_id=synthesis_result_id,
            target_words_per_layer=10000,  # 每层10000字
            include_citations=True
        )

        logger.info(f"📝 三层报告生成完成（成功={'✅' if result['success'] else '❌'}）")
        logger.info(f"   - Layer 1 ID: {result['layer_1_id']} ({result['layer_1_words']}字)")
        logger.info(f"   - Layer 2 ID: {result['layer_2_id']} ({result['layer_2_words']}字)")
        logger.info(f"   - Layer 3 ID: {result['layer_3_id']} ({result['layer_3_words']}字)")
        logger.info(f"   - 总字数: {result['total_words']}")

        return {
            'success': result['success'],
            'report_type': 'three_layer',
            'layer_1_id': result['layer_1_id'],
            'layer_2_id': result['layer_2_id'],
            'layer_3_id': result['layer_3_id'],
            'layer_1_words': result['layer_1_words'],
            'layer_2_words': result['layer_2_words'],
            'layer_3_words': result['layer_3_words'],
            'total_words': result['total_words'],
            'synthesis_result_id': synthesis_result_id,
            'confidence_score': result['metadata']['confidence_score']
        }

    # ==================== 辅助方法 ====================

    # ==================== 状态持久化方法 ====================

    def _update_execution_progress(
        self,
        execution_id: str,
        current_stage: str,
        completed_stages: int,
        total_stages: int,
        db_session
    ):
        """更新执行进度"""
        progress = (completed_stages / total_stages) * 100 if total_stages > 0 else 0

        # DISABLED:         pipeline_exec = db_session.query(PipelineExecution).filter(
        # DISABLED:             PipelineExecution.execution_id == execution_id
        # DISABLED:         ).first()

        if pipeline_exec:
            pipeline_exec.current_stage = current_stage
            pipeline_exec.completed_stages = completed_stages
            pipeline_exec.progress_percentage = progress
            pipeline_exec.updated_at = datetime.now()
            db_session.commit()

            logger.info(f"📊 进度更新: {progress:.1f}% ({completed_stages}/{total_stages})")

    def _update_execution_status(
        self,
        execution_id: str,
        status: str,
        db_session,
        error_message: Optional[str] = None,
        end_time: Optional[datetime] = None,
        total_duration: Optional[float] = None
    ):
        """更新执行状态"""
        # DISABLED:         pipeline_exec = db_session.query(PipelineExecution).filter(
        # DISABLED:             PipelineExecution.execution_id == execution_id
        # DISABLED:         ).first()

        if pipeline_exec:
            pipeline_exec.status = status
            if error_message:
                pipeline_exec.error_message = error_message
            if end_time:
                pipeline_exec.end_time = end_time
            if total_duration:
                pipeline_exec.total_duration_seconds = total_duration
            pipeline_exec.updated_at = datetime.now()
            db_session.commit()

    def _save_stage_result(
        self,
        execution_id: str,
        stage: PipelineStage,
        result: StageResult,
        db_session
    ):
        """保存阶段结果到数据库"""
        # DISABLED:         stage_record = db_session.query(PipelineStageResult).filter(
        # DISABLED:             PipelineStageResult.execution_id == execution_id,
        # DISABLED:             PipelineStageResult.stage == stage.value
        # DISABLED:         ).first()

        if not stage_record:
            stage_record = PipelineStageResult(
                execution_id=execution_id,
                stage=stage.value,
                status='completed' if result.success else 'failed',
                success=result.success,
                duration_seconds=result.duration_seconds,
                output=result.output,
                errors=result.errors,
                warnings=result.warnings,
                start_time=datetime.now(),
                end_time=datetime.now()
            )
            db_session.add(stage_record)
        else:
            stage_record.status = 'completed' if result.success else 'failed'
            stage_record.success = result.success
            stage_record.duration_seconds = result.duration_seconds
            stage_record.output = result.output
            stage_record.errors = result.errors
            stage_record.warnings = result.warnings
            stage_record.end_time = datetime.now()

        db_session.commit()

    def _find_unfinished_execution(
        self,
        project_id: int,
        db_session
    ) -> None:
        """查找未完成的执行记录"""
        # DISABLED:         return db_session.query(PipelineExecution).filter(
        # DISABLED:             PipelineExecution.project_id == project_id,
        # DISABLED:             PipelineExecution.status.in_(['running', 'paused'])
        # DISABLED:         ).order_by(PipelineExecution.created_at.desc()).first()

    def _resume_execution(
        self,
        execution_id: str,
        db_session,
        report_level: Optional[str] = None
    ) -> PipelineResult:
        """恢复执行"""
        # DISABLED:         pipeline_exec = db_session.query(PipelineExecution).filter(
        # DISABLED:             PipelineExecution.execution_id == execution_id
        # DISABLED:         ).first()

        if not pipeline_exec:
            raise ValueError(f"执行记录不存在: {execution_id}")

        logger.info(f"🔄 恢复执行 {execution_id}，当前进度: {pipeline_exec.progress_percentage:.1f}%")

        # 加载已完成的阶段结果
        # DISABLED:         stage_records = db_session.query(PipelineStageResult).filter(
        # DISABLED:             PipelineStageResult.execution_id == execution_id,
        # DISABLED:             PipelineStageResult.success == True
        # DISABLED:         ).all()

        stage_results = {}
        for record in stage_records:
            stage_enum = PipelineStage(record.stage)
            stage_results[stage_enum] = StageResult(
                stage=stage_enum,
                success=record.success,
                duration_seconds=record.duration_seconds or 0,
                output=record.output or {},
                errors=record.errors or [],
                warnings=record.warnings or []
            )

        # 确定剩余阶段
        mode = PipelineMode(pipeline_exec.mode)
        all_stages = self._determine_stages(mode)
        completed_stage_names = {record.stage for record in stage_records if record.success}
        remaining_stages = [s for s in all_stages if s.value not in completed_stage_names]

        logger.info(f"📋 剩余阶段: {[s.value for s in remaining_stages]}")

        # 更新状态为running
        pipeline_exec.status = 'running'
        pipeline_exec.updated_at = datetime.now()
        db_session.commit()

        # 继续执行剩余阶段
        for stage in remaining_stages:
            logger.info(f"▶️ 执行阶段: {stage.value}")

            self._update_execution_progress(
                execution_id=execution_id,
                current_stage=stage.value,
                completed_stages=len(stage_results),
                total_stages=len(all_stages),
                db_session=db_session
            )

            stage_result = self._execute_stage(
                stage=stage,
                project_id=pipeline_exec.project_id,
                db_session=db_session,
                previous_results=stage_results,
                report_level=report_level,
                execution_id=execution_id
            )

            self._save_stage_result(execution_id, stage, stage_result, db_session)
            stage_results[stage] = stage_result

            if not stage_result.success:
                logger.error(f"❌ 阶段{stage.value}失败")
                self._update_execution_status(
                    execution_id=execution_id,
                    status='failed',
                    error_message='; '.join(stage_result.errors),
                    db_session=db_session
                )
                break

        # 生成最终结果
        end_time = datetime.now()
        total_duration = (end_time - pipeline_exec.start_time).total_seconds()
        pipeline_success = all(r.success for r in stage_results.values())

        self._update_execution_status(
            execution_id=execution_id,
            status='completed' if pipeline_success else 'failed',
            end_time=end_time,
            total_duration=total_duration,
            db_session=db_session
        )

        return PipelineResult(
            project_id=pipeline_exec.project_id,
            mode=mode,
            start_time=pipeline_exec.start_time,
            end_time=end_time,
            total_duration_seconds=total_duration,
            success=pipeline_success,
            completed_stages=list(stage_results.keys()),
            stage_results=stage_results,
            errors=[],
            metadata={'execution_id': execution_id, 'resumed': True}
        )

    # ==================== 智能重试方法 ====================

    def _classify_error(self, error_message: str) -> str:
        """分类错误类型"""
        error_lower = error_message.lower()

        # 网络相关错误
        if any(keyword in error_lower for keyword in ['connection', 'timeout', 'network', 'dns', 'unreachable']):
            return 'network'

        # 配置相关错误
        if any(keyword in error_lower for keyword in ['config', 'setting', 'parameter', 'key', 'credential']):
            return 'config'

        # 数据相关错误
        if any(keyword in error_lower for keyword in ['invalid', 'parse', 'format', 'corrupt', 'missing']):
            return 'data'

        # 资源不足
        if any(keyword in error_lower for keyword in ['memory', 'disk', 'quota', 'limit']):
            return 'resource'

        return 'unknown'

    def _get_retry_strategy(self, error_type: str) -> Tuple[int, float]:
        """根据错误类型获取重试策略 (max_retries, backoff_factor)"""
        strategies = {
            'network': (5, 2.0),      # 网络问题：多重试，指数退避
            'config': (0, 0.0),       # 配置问题：不重试（需要人工修复）
            'data': (1, 0.0),         # 数据问题：重试1次
            'resource': (3, 1.5),     # 资源问题：适度重试
            'unknown': (2, 1.0)       # 未知问题：保守重试
        }
        return strategies.get(error_type, (2, 1.0))

    def _retry_stage_smart(
        self,
        stage: PipelineStage,
        project_id: int,
        db_session,
        previous_results: Dict[PipelineStage, StageResult],
        report_level: Optional[str],
        execution_id: str,
        error: str
    ) -> bool:
        """智能重试（根据错误类型调整策略）"""
        import time

        error_type = self._classify_error(error)
        max_retries, backoff_factor = self._get_retry_strategy(error_type)

        logger.info(f"🔍 错误类型: {error_type}，重试策略: max={max_retries}, backoff={backoff_factor}")

        if max_retries == 0:
            logger.warning(f"⚠️ 错误类型'{error_type}'不适合重试，需要手动修复")
            return False

        for attempt in range(max_retries):
            # 指数退避
            if backoff_factor > 0:
                wait_time = backoff_factor ** attempt
                logger.info(f"⏳ 等待 {wait_time:.1f}秒 后重试...")
                time.sleep(wait_time)

            logger.info(f"🔄 重试阶段{stage.value}（第{attempt + 1}/{max_retries}次）")

            # 更新重试次数
        # DISABLED:             stage_record = db_session.query(PipelineStageResult).filter(
        # DISABLED:                 PipelineStageResult.execution_id == execution_id,
        # DISABLED:                 PipelineStageResult.stage == stage.value
        # DISABLED:             ).first()

            if stage_record:
                stage_record.retry_count = attempt + 1
                db_session.commit()

            result = self._execute_stage(
                stage=stage,
                project_id=project_id,
                db_session=db_session,
                previous_results=previous_results,
                report_level=report_level,
                execution_id=execution_id
            )

            if result.success:
                self._save_stage_result(execution_id, stage, result, db_session)
                previous_results[stage] = result
                return True

        return False

    # ==================== 并行处理方法 ====================

    def _process_document_parallel(
        self,
        doc,
        project_id: int,
        db_session
    ) -> Dict[str, Any]:
        """并行处理单个文档（用于Chunk阶段）"""
        agent = self._get_chunk_agent()
        vectorization_service = VectorizationService()

        if not doc.text_content:
            return {'document_id': doc.id, 'chunks': [], 'error': 'No text content'}

        try:
            # 使用ChunkingAgent的chunk_text方法
            result = agent.chunk_text(
                text=doc.text_content,
                source_file=doc.file_path or f"doc_{doc.id}",
                file_type=doc.file_type or 'text',
                language='zh',
                metadata={'document_id': doc.id}
            )

            # 将Chunk对象转换为字典格式
            chunks_dict = []
            for idx, chunk in enumerate(result.chunks):
                chunk_dict = {
                    'chunk_id': f"chunk_{doc.id}_{idx}",
                    'text': chunk.text,
                    'embedding': None,
                    'metadata': {
                        'start_char': chunk.metadata.start_pos,
                        'end_char': chunk.metadata.end_pos,
                        'token_count': chunk.metadata.word_count,
                        'document_id': doc.id
                    }
                }
                chunks_dict.append(chunk_dict)

            # 存储到数据库
            stored_chunks = vectorization_service.store_chunks(
                chunks=chunks_dict,
                document_id=doc.id,
                project_id=project_id,
                db=db_session
            )

            chunk_ids = [c.id for c in stored_chunks]  # 修复：使用id而不是chunk_id
            logger.info(f"✅ 文档 {doc.id} 的 {len(stored_chunks)} 个chunks已存储")

            return {
                'document_id': doc.id,
                'chunk_count': len(stored_chunks),
                'chunk_ids': chunk_ids,
                'success': True
            }

        except Exception as e:
            logger.error(f"❌ 处理文档 {doc.id} 失败: {e}")
            return {
                'document_id': doc.id,
                'chunks': [],
                'error': str(e),
                'success': False
            }

    # ==================== 原有辅助方法 ====================

    def get_pipeline_status(
        self,
        project_id: int,
        db_session
    ) -> Dict[str, Any]:
        """获取项目的流水线状态（增强版：从数据库读取）"""
        from app.models.project import ProjectDocument

        # 查找最近的执行记录
        # DISABLED:         latest_exec = db_session.query(PipelineExecution).filter(
        # DISABLED:             PipelineExecution.project_id == project_id
        # DISABLED:         ).order_by(PipelineExecution.created_at.desc()).first()

        if latest_exec:
            # 从数据库读取详细状态
        # DISABLED:             stage_records = db_session.query(PipelineStageResult).filter(
        # DISABLED:                 PipelineStageResult.execution_id == latest_exec.execution_id
        # DISABLED:             ).all()

            stages_status = {record.stage: record.success for record in stage_records}

            return {
                'project_id': project_id,
                'execution_id': latest_exec.execution_id,
                'status': latest_exec.status,
                'current_stage': latest_exec.current_stage,
                'progress_percentage': latest_exec.progress_percentage,
                'completed_stages': latest_exec.completed_stages,
                'total_stages': latest_exec.total_stages,
                'stages': stages_status,
                'can_resume': latest_exec.status in ['running', 'paused', 'failed'],
                'start_time': latest_exec.start_time.isoformat() if latest_exec.start_time else None,
                'error_message': latest_exec.error_message
            }

        # 回退到传统检查
        docs = db_session.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id
        ).all()

        has_documents = len(docs) > 0
        has_chunks = any(doc.chunks for doc in docs)
        has_analysis = any(doc.data_profile for doc in docs)

        return {
            'project_id': project_id,
            'execution_id': None,
            'status': 'not_started',
            'document_count': len(docs),
            'stages': {
                'document_load': has_documents,
                'chunk': has_chunks,
                'analysis': has_analysis,
                'knowledge': False
            },
            'can_skip_to_report': has_documents and has_chunks and has_analysis,
            'can_resume': False
        }

