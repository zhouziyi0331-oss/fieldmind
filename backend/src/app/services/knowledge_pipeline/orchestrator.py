"""
知识构建流水线编排器
Knowledge Pipeline Orchestrator
🔥 WorkflowEngine集成 - 阶段1

功能：
1. 协调九步流水线执行
2. 状态管理
3. 错误处理与重试
4. 结果持久化
5. 🔥 支持WorkflowEngine DAG执行
"""

import logging
import traceback
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum
import asyncio
from app.services.workflow_engine import WorkflowEngine

logger = logging.getLogger(__name__)


class PipelineStatus(str, Enum):
    """流水线状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PipelineStep(str, Enum):
    """流水线步骤"""
    CLEANING = "cleaning"
    STRUCTURE = "structure"
    ENTITY = "entity"
    EVENT = "event"
    RELATION = "relation"
    ONTOLOGY = "ontology"
    INFERENCE = "inference"
    KNOWLEDGE = "knowledge"
    READER = "reader"


class KnowledgePipelineOrchestrator:
    """
    知识构建流水线编排器
    🔥 支持WorkflowEngine DAG执行模式
    """

    def __init__(
        self,
        document_id: str,
        project_id: str,
        user_id: str,
        db_session=None,
        llm_service=None,
        use_workflow_engine: bool = True  # 🔥 新增：是否使用WorkflowEngine
    ):
        self.document_id = document_id
        self.project_id = project_id
        self.user_id = user_id
        self.db = db_session
        self.llm_service = llm_service
        self.use_workflow_engine = use_workflow_engine  # 🔥 新增

        # 🔥 初始化WorkflowEngine
        if use_workflow_engine:
            self.workflow_engine = WorkflowEngine(max_workers=3)

        # 导入服务
        from .step1_cleaning import TextCleaningService
        from .step2_structure import StructureAnalysisService
        from .step3_entity import EntityConstructionService
        from .step4_event import EventExtractionService
        from .step5_relation import RelationDiscoveryService
        from .step6_ontology import OntologyConstructionService
        from .step7_inference import LogicInferenceService
        from .step8_knowledge import KnowledgeUnitizationService
        from .step9_reader import ReaderGenerationService

        self.services = {
            PipelineStep.CLEANING: TextCleaningService(llm_service),
            PipelineStep.STRUCTURE: StructureAnalysisService(),
            PipelineStep.ENTITY: EntityConstructionService(),
            PipelineStep.EVENT: EventExtractionService(),
            PipelineStep.RELATION: RelationDiscoveryService(),
            PipelineStep.ONTOLOGY: OntologyConstructionService(),
            PipelineStep.INFERENCE: LogicInferenceService(),
            PipelineStep.KNOWLEDGE: KnowledgeUnitizationService(),
            PipelineStep.READER: ReaderGenerationService(),
        }

        # 执行状态
        self.status = PipelineStatus.PENDING
        self.current_step: Optional[PipelineStep] = None
        self.execution_id: Optional[str] = None
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.results: Dict[str, Any] = {}
        self.errors: Dict[str, str] = {}

    async def execute(
        self,
        text: str,
        enable_statistical_cleaning: bool = True,
        enable_llm_cleaning: bool = False,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        执行完整的九步流水线

        Args:
            text: 原始文本
            enable_statistical_cleaning: 是否启用统计清洗
            enable_llm_cleaning: 是否启用 LLM 清洗
            max_retries: 最大重试次数

        Returns:
            流水线执行结果
        """
        self.status = PipelineStatus.RUNNING
        self.start_time = datetime.utcnow()
        self.execution_id = f"exec_{self.document_id}_{int(self.start_time.timestamp())}"

        logger.info(f"🚀 开始执行知识构建流水线：{self.execution_id}")

        try:
            # 🔥 根据配置选择执行方式
            if self.use_workflow_engine:
                return await self._execute_with_workflow_engine(
                    text=text,
                    enable_statistical_cleaning=enable_statistical_cleaning,
                    enable_llm_cleaning=enable_llm_cleaning,
                    max_retries=max_retries
                )
            else:
                return await self._execute_traditional(
                    text=text,
                    enable_statistical_cleaning=enable_statistical_cleaning,
                    enable_llm_cleaning=enable_llm_cleaning,
                    max_retries=max_retries
                )

        except Exception as e:
            self.status = PipelineStatus.FAILED
            self.end_time = datetime.utcnow()
            error_msg = f"流水线执行失败: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            self.errors['pipeline'] = error_msg

            return {
                'execution_id': self.execution_id,
                'status': self.status.value,
                'error': error_msg,
                'results': self.results,
                'errors': self.errors
            }

    async def _execute_with_workflow_engine(
        self,
        text: str,
        enable_statistical_cleaning: bool,
        enable_llm_cleaning: bool,
        max_retries: int
    ) -> Dict[str, Any]:
        """
        🔥 使用WorkflowEngine执行流水线（DAG模式）
        """
        logger.info(f"🔥 [WorkflowEngine] 开始知识流水线 {self.execution_id}")

        # 创建工作流
        workflow = self.workflow_engine.create_workflow(
            name=f"knowledge_pipeline_{self.document_id}",
            description=f"知识构建流水线 - 文档ID: {self.document_id}"
        )

        # 🔥 Task 1: 文本清洗（cleaning）
        self.workflow_engine.add_task(
            workflow,
            name="cleaning",
            func=self._task_cleaning,
            kwargs={
                'text': text,
                'enable_statistical': enable_statistical_cleaning,
                'enable_llm': enable_llm_cleaning
            },
            dependencies=[]
        )

        # 🔥 Task 2: 结构分析（structure）
        self.workflow_engine.add_task(
            workflow,
            name="structure",
            func=self._task_structure,
            kwargs={'cleaned_text': '$cleaning.cleaned_text'},
            dependencies=["cleaning"]
        )

        # 🔥 Task 3: 实体构建（entity）
        self.workflow_engine.add_task(
            workflow,
            name="entity",
            func=self._task_entity,
            kwargs={
                'cleaned_text': '$cleaning.cleaned_text',
                'structure_tree': '$structure.structure_tree'
            },
            dependencies=["cleaning", "structure"]
        )

        # 🔥 Task 4: 事件提取（event） - 可与relation并行
        self.workflow_engine.add_task(
            workflow,
            name="event",
            func=self._task_event,
            kwargs={
                'cleaned_text': '$cleaning.cleaned_text',
                'entities': '$entity.entities'
            },
            dependencies=["cleaning", "entity"]
        )

        # 🔥 Task 5: 关系发现（relation） - 可与event并行
        self.workflow_engine.add_task(
            workflow,
            name="relation",
            func=self._task_relation,
            kwargs={
                'cleaned_text': '$cleaning.cleaned_text',
                'entities': '$entity.entities',
                'events': '$event.events'
            },
            dependencies=["cleaning", "entity", "event"]
        )

        # 🔥 Task 6: 本体构建（ontology）
        self.workflow_engine.add_task(
            workflow,
            name="ontology",
            func=self._task_ontology,
            kwargs={
                'entities': '$entity.entities',
                'relations': '$relation.relations'
            },
            dependencies=["entity", "relation"]
        )

        # 🔥 Task 7: 逻辑推理（inference）
        self.workflow_engine.add_task(
            workflow,
            name="inference",
            func=self._task_inference,
            kwargs={
                'entities': '$entity.entities',
                'relations': '$relation.relations',
                'events': '$event.events',
                'ontology': '$ontology.ontology'
            },
            dependencies=["entity", "relation", "event", "ontology"]
        )

        # 🔥 Task 8: 知识单元化（knowledge）
        self.workflow_engine.add_task(
            workflow,
            name="knowledge",
            func=self._task_knowledge,
            kwargs={
                'entities': '$entity.entities',
                'relations': '$relation.relations',
                'events': '$event.events',
                'inference_result': '$inference',
                'ontology': '$ontology.ontology'
            },
            dependencies=["entity", "relation", "event", "inference", "ontology"]
        )

        # 🔥 Task 9: 阅读器生成（reader）
        self.workflow_engine.add_task(
            workflow,
            name="reader",
            func=self._task_reader,
            kwargs={
                'entities': '$entity.entities',
                'relations': '$relation.relations',
                'events': '$event.events',
                'knowledge_units': '$knowledge.knowledge_units'
            },
            dependencies=["entity", "relation", "event", "knowledge"]
        )

        # 执行工作流
        workflow_results = self.workflow_engine.execute(workflow)

        # 整合结果
        self.results = {
            'cleaning': workflow_results['cleaning'],
            'structure': workflow_results['structure'],
            'entity': workflow_results['entity'],
            'event': workflow_results['event'],
            'relation': workflow_results['relation'],
            'ontology': workflow_results['ontology'],
            'inference': workflow_results['inference'],
            'knowledge': workflow_results['knowledge'],
            'reader': workflow_results['reader']
        }

        # 持久化结果
        if self.db:
            await self._persist_results()

        self.status = PipelineStatus.COMPLETED
        self.end_time = datetime.utcnow()

        duration = (self.end_time - self.start_time).total_seconds()
        logger.info(f"✅ [WorkflowEngine] 知识构建流水线完成：{self.execution_id}，耗时 {duration:.2f} 秒")

        return {
            'execution_id': self.execution_id,
            'status': self.status.value,
            'duration': duration,
            'results': self.results,
            'errors': self.errors,
            'workflow_engine': True
        }

    async def _execute_traditional(
        self,
        text: str,
        enable_statistical_cleaning: bool,
        enable_llm_cleaning: bool,
        max_retries: int
    ) -> Dict[str, Any]:
        """
        传统顺序执行模式（向后兼容）
        """
        logger.info(f"📝 [传统模式] 开始知识流水线 {self.execution_id}")

        try:
            # Step 1: 文本校刊
            await self._execute_step_with_retry(
                PipelineStep.CLEANING,
                self._step1_cleaning,
                max_retries,
                text=text,
                enable_statistical=enable_statistical_cleaning,
                enable_llm=enable_llm_cleaning
            )

            # Step 2: 结构分析
            await self._execute_step_with_retry(
                PipelineStep.STRUCTURE,
                self._step2_structure,
                max_retries
            )

            # Step 3: 实体构建
            await self._execute_step_with_retry(
                PipelineStep.ENTITY,
                self._step3_entity,
                max_retries
            )

            # Step 4: 事件提取
            await self._execute_step_with_retry(
                PipelineStep.EVENT,
                self._step4_event,
                max_retries
            )

            # Step 5: 关系发现
            await self._execute_step_with_retry(
                PipelineStep.RELATION,
                self._step5_relation,
                max_retries
            )

            # Step 6: 本体构建（核心步骤）
            await self._execute_step_with_retry(
                PipelineStep.ONTOLOGY,
                self._step6_ontology,
                max_retries
            )

            # Step 7: 逻辑推理
            await self._execute_step_with_retry(
                PipelineStep.INFERENCE,
                self._step7_inference,
                max_retries
            )

            # Step 8: 知识单元化
            await self._execute_step_with_retry(
                PipelineStep.KNOWLEDGE,
                self._step8_knowledge,
                max_retries
            )

            # Step 9: 阅读器生成
            await self._execute_step_with_retry(
                PipelineStep.READER,
                self._step9_reader,
                max_retries
            )

            # 持久化结果
            if self.db:
                await self._persist_results()

            self.status = PipelineStatus.COMPLETED
            self.end_time = datetime.utcnow()

            duration = (self.end_time - self.start_time).total_seconds()
            logger.info(f"✅ [传统模式] 知识构建流水线完成：{self.execution_id}，耗时 {duration:.2f} 秒")

            return {
                'execution_id': self.execution_id,
                'status': self.status.value,
                'duration': duration,
                'results': self.results,
                'errors': self.errors,
                'workflow_engine': False
            }

        except Exception as e:
            self.status = PipelineStatus.FAILED
            self.end_time = datetime.utcnow()
            error_msg = f"流水线执行失败: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            self.errors['pipeline'] = error_msg

            return {
                'execution_id': self.execution_id,
                'status': self.status.value,
                'error': error_msg,
                'results': self.results,
                'errors': self.errors,
                'workflow_engine': False
            }

    async def _execute_step_with_retry(
        self,
        step: PipelineStep,
        step_func,
        max_retries: int,
        **kwargs
    ):
        """执行步骤（带重试）"""
        self.current_step = step
        retries = 0

        while retries <= max_retries:
            try:
                logger.info(f"▶️  Step {step.value} 开始（尝试 {retries + 1}/{max_retries + 1}）")
                result = await step_func(**kwargs)
                self.results[step.value] = result
                logger.info(f"✅ Step {step.value} 完成")
                return result

            except Exception as e:
                retries += 1
                error_msg = f"Step {step.value} 失败: {str(e)}"
                logger.error(error_msg)

                if retries > max_retries:
                    self.errors[step.value] = error_msg
                    raise Exception(f"Step {step.value} 在 {max_retries} 次重试后仍然失败")

                # 指数退避
                wait_time = 2 ** retries
                logger.info(f"⏳ 等待 {wait_time} 秒后重试...")
                await asyncio.sleep(wait_time)

    # ========================================
    # 🔥 WorkflowEngine Task Functions (9个任务函数)
    # ========================================

    def _task_cleaning(self, text: str, enable_statistical: bool, enable_llm: bool, _context: dict) -> dict:
        """
        🔥 Task 1: 文本清洗
        """
        logger.info(f"  [Task] cleaning: 处理 {len(text)} 字符")

        service = self.services[PipelineStep.CLEANING]

        # 同步执行（WorkflowEngine在线程池中运行）
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        cleaning_result = loop.run_until_complete(
            service.clean(
                text=text,
                enable_statistical=enable_statistical,
                enable_llm=enable_llm
            )
        )
        loop.close()

        result = {
            'cleaned_text': cleaning_result.cleaned_text,
            'logs': [
                {
                    'category': log.rule_category,
                    'description': log.rule_description,
                    'position': log.position
                }
                for log in cleaning_result.logs
            ],
            'statistics': cleaning_result.statistics
        }

        logger.info(f"  ✅ cleaning: 清洗完成，输出 {len(result['cleaned_text'])} 字符")
        return result

    def _task_structure(self, cleaned_text: str, _context: dict) -> dict:
        """
        🔥 Task 2: 结构分析
        """
        logger.info(f"  [Task] structure: 分析文档结构")

        service = self.services[PipelineStep.STRUCTURE]

        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        structure_tree = loop.run_until_complete(service.analyze(cleaned_text))
        loop.close()

        result = {
            'structure_tree': structure_tree,
            'metadata': structure_tree.metadata,
            'node_count': len(structure_tree.nodes)
        }

        logger.info(f"  ✅ structure: 发现 {result['node_count']} 个结构节点")
        return result

    def _task_entity(self, cleaned_text: str, structure_tree, _context: dict) -> dict:
        """
        🔥 Task 3: 实体构建
        """
        logger.info(f"  [Task] entity: 构建实体")

        service = self.services[PipelineStep.ENTITY]

        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        entity_result = loop.run_until_complete(
            service.construct(cleaned_text, structure_tree)
        )
        loop.close()

        result = {
            'entities': entity_result['entities'],
            'mentions': entity_result['mentions'],
            'coref_chains': entity_result['coref_chains'],
            'statistics': entity_result['statistics']
        }

        logger.info(f"  ✅ entity: 提取 {len(result['entities'])} 个实体")
        return result

    def _task_event(self, cleaned_text: str, entities: list, _context: dict) -> dict:
        """
        🔥 Task 4: 事件提取
        """
        logger.info(f"  [Task] event: 提取事件")

        service = self.services[PipelineStep.EVENT]

        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        event_result = loop.run_until_complete(
            service.extract(cleaned_text, entities)
        )
        loop.close()

        result = {
            'events': event_result['events'],
            'event_chain': event_result['event_chain'],
            'statistics': event_result['statistics']
        }

        logger.info(f"  ✅ event: 提取 {len(result['events'])} 个事件")
        return result

    def _task_relation(self, cleaned_text: str, entities: list, events: list, _context: dict) -> dict:
        """
        🔥 Task 5: 关系发现
        """
        logger.info(f"  [Task] relation: 发现关系")

        service = self.services[PipelineStep.RELATION]

        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        relation_result = loop.run_until_complete(
            service.discover(cleaned_text, entities, events)
        )
        loop.close()

        result = {
            'relations': relation_result['relations'],
            'statistics': relation_result['statistics']
        }

        logger.info(f"  ✅ relation: 发现 {len(result['relations'])} 个关系")
        return result

    def _task_ontology(self, entities: list, relations: list, _context: dict) -> dict:
        """
        🔥 Task 6: 本体构建
        """
        logger.info(f"  [Task] ontology: 构建本体")

        service = self.services[PipelineStep.ONTOLOGY]

        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        ontology_result = loop.run_until_complete(
            service.construct(
                entities,
                relations,
                ontology_name=f"FieldMind_{self.project_id}"
            )
        )
        loop.close()

        result = {
            'ontology': ontology_result['ontology'],
            'owl_xml': ontology_result['owl_xml'],
            'statistics': ontology_result['statistics']
        }

        logger.info(f"  ✅ ontology: 本体构建完成")
        return result

    def _task_inference(self, entities: list, relations: list, events: list, ontology, _context: dict) -> dict:
        """
        🔥 Task 7: 逻辑推理
        """
        logger.info(f"  [Task] inference: 执行逻辑推理")

        service = self.services[PipelineStep.INFERENCE]

        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        inference_result = loop.run_until_complete(
            service.infer(entities, relations, events, ontology)
        )
        loop.close()

        result = {
            'findings': inference_result['findings'],
            'transitive_relations': inference_result['transitive_relations'],
            'conflicts': inference_result['conflicts'],
            'statistics': inference_result['statistics']
        }

        logger.info(f"  ✅ inference: 发现 {len(result['findings'])} 个推理结果")
        return result

    def _task_knowledge(self, entities: list, relations: list, events: list,
                       inference_result: dict, ontology, _context: dict) -> dict:
        """
        🔥 Task 8: 知识单元化
        """
        logger.info(f"  [Task] knowledge: 知识单元化")

        service = self.services[PipelineStep.KNOWLEDGE]

        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        knowledge_result = loop.run_until_complete(
            service.unitize(
                entities,
                relations,
                events,
                inference_result,
                ontology
            )
        )
        loop.close()

        result = {
            'knowledge_units': knowledge_result['knowledge_units'],
            'statistics': knowledge_result['statistics']
        }

        logger.info(f"  ✅ knowledge: 生成 {len(result['knowledge_units'])} 个知识单元")
        return result

    def _task_reader(self, entities: list, relations: list, events: list,
                     knowledge_units: list, _context: dict) -> dict:
        """
        🔥 Task 9: 阅读器生成
        """
        logger.info(f"  [Task] reader: 生成阅读器")

        service = self.services[PipelineStep.READER]

        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        reader_result = loop.run_until_complete(
            service.generate(
                entities,
                relations,
                events,
                knowledge_units
            )
        )
        loop.close()

        result = {
            'timeline': reader_result['timeline'],
            'topics': reader_result['topics'],
            'network': reader_result['network'],
            'wiki_pages': reader_result['wiki_pages'],
            'metadata': reader_result['metadata']
        }

        logger.info(f"  ✅ reader: 阅读器生成完成")
        return result

    async def _step1_cleaning(
        self,
        text: str,
        enable_statistical: bool,
        enable_llm: bool
    ) -> Dict[str, Any]:
        """Step 1: 文本校刊"""
        service = self.services[PipelineStep.CLEANING]
        cleaning_result = await service.clean(
            text=text,
            enable_statistical=enable_statistical,
            enable_llm=enable_llm
        )

        return {
            'cleaned_text': cleaning_result.cleaned_text,
            'logs': [
                {
                    'category': log.rule_category,
                    'description': log.rule_description,
                    'position': log.position
                }
                for log in cleaning_result.logs
            ],
            'statistics': cleaning_result.statistics
        }

    async def _step2_structure(self) -> Dict[str, Any]:
        """Step 2: 结构分析"""
        cleaned_text = self.results[PipelineStep.CLEANING.value]['cleaned_text']
        service = self.services[PipelineStep.STRUCTURE]
        structure_tree = await service.analyze(cleaned_text)

        return {
            'structure_tree': structure_tree,
            'metadata': structure_tree.metadata,
            'node_count': len(structure_tree.nodes)
        }

    async def _step3_entity(self) -> Dict[str, Any]:
        """Step 3: 实体构建"""
        cleaned_text = self.results[PipelineStep.CLEANING.value]['cleaned_text']
        structure_tree = self.results[PipelineStep.STRUCTURE.value]['structure_tree']

        service = self.services[PipelineStep.ENTITY]
        entity_result = await service.construct(cleaned_text, structure_tree)

        return {
            'entities': entity_result['entities'],
            'mentions': entity_result['mentions'],
            'coref_chains': entity_result['coref_chains'],
            'statistics': entity_result['statistics']
        }

    async def _step4_event(self) -> Dict[str, Any]:
        """Step 4: 事件提取"""
        cleaned_text = self.results[PipelineStep.CLEANING.value]['cleaned_text']
        entities = self.results[PipelineStep.ENTITY.value]['entities']

        service = self.services[PipelineStep.EVENT]
        event_result = await service.extract(cleaned_text, entities)

        return {
            'events': event_result['events'],
            'event_chain': event_result['event_chain'],
            'statistics': event_result['statistics']
        }

    async def _step5_relation(self) -> Dict[str, Any]:
        """Step 5: 关系发现"""
        cleaned_text = self.results[PipelineStep.CLEANING.value]['cleaned_text']
        entities = self.results[PipelineStep.ENTITY.value]['entities']
        events = self.results[PipelineStep.EVENT.value]['events']

        service = self.services[PipelineStep.RELATION]
        relation_result = await service.discover(cleaned_text, entities, events)

        return {
            'relations': relation_result['relations'],
            'statistics': relation_result['statistics']
        }

    async def _step6_ontology(self) -> Dict[str, Any]:
        """Step 6: 本体构建（核心步骤）"""
        entities = self.results[PipelineStep.ENTITY.value]['entities']
        relations = self.results[PipelineStep.RELATION.value]['relations']

        service = self.services[PipelineStep.ONTOLOGY]
        ontology_result = await service.construct(
            entities,
            relations,
            ontology_name=f"FieldMind_{self.project_id}"
        )

        return {
            'ontology': ontology_result['ontology'],
            'owl_xml': ontology_result['owl_xml'],
            'statistics': ontology_result['statistics']
        }

    async def _step7_inference(self) -> Dict[str, Any]:
        """Step 7: 逻辑推理"""
        entities = self.results[PipelineStep.ENTITY.value]['entities']
        relations = self.results[PipelineStep.RELATION.value]['relations']
        events = self.results[PipelineStep.EVENT.value]['events']
        ontology = self.results[PipelineStep.ONTOLOGY.value]['ontology']

        service = self.services[PipelineStep.INFERENCE]
        inference_result = await service.infer(entities, relations, events, ontology)

        return {
            'findings': inference_result['findings'],
            'transitive_relations': inference_result['transitive_relations'],
            'conflicts': inference_result['conflicts'],
            'statistics': inference_result['statistics']
        }

    async def _step8_knowledge(self) -> Dict[str, Any]:
        """Step 8: 知识单元化"""
        entities = self.results[PipelineStep.ENTITY.value]['entities']
        relations = self.results[PipelineStep.RELATION.value]['relations']
        events = self.results[PipelineStep.EVENT.value]['events']
        inference_result = self.results[PipelineStep.INFERENCE.value]
        ontology = self.results[PipelineStep.ONTOLOGY.value]['ontology']

        service = self.services[PipelineStep.KNOWLEDGE]
        knowledge_result = await service.unitize(
            entities,
            relations,
            events,
            inference_result,
            ontology
        )

        return {
            'knowledge_units': knowledge_result['knowledge_units'],
            'statistics': knowledge_result['statistics']
        }

    async def _step9_reader(self) -> Dict[str, Any]:
        """Step 9: 阅读器生成"""
        entities = self.results[PipelineStep.ENTITY.value]['entities']
        relations = self.results[PipelineStep.RELATION.value]['relations']
        events = self.results[PipelineStep.EVENT.value]['events']
        knowledge_units = self.results[PipelineStep.KNOWLEDGE.value]['knowledge_units']

        service = self.services[PipelineStep.READER]
        reader_result = await service.generate(
            entities,
            relations,
            events,
            knowledge_units
        )

        return {
            'timeline': reader_result['timeline'],
            'topics': reader_result['topics'],
            'network': reader_result['network'],
            'wiki_pages': reader_result['wiki_pages'],
            'metadata': reader_result['metadata']
        }

    async def _persist_results(self):
        """持久化结果到数据库"""
        if not self.db:
            return

        logger.info("💾 开始持久化流水线结果...")

        try:
            # 导入数据库模型
            from app.models.knowledge import (
                KnowledgeEntity,
                KnowledgeRelation,
                KnowledgeEvent,
                KnowledgeUnit,
                PipelineExecution
            )

            # 1. 保存流水线执行记录
            execution = PipelineExecution(
                id=self.execution_id,
                document_id=self.document_id,
                project_id=self.project_id,
                user_id=self.user_id,
                status=self.status.value,
                start_time=self.start_time,
                end_time=self.end_time,
                results=self.results,
                errors=self.errors
            )
            self.db.add(execution)

            # 2. 保存实体
            entities = self.results.get(PipelineStep.ENTITY.value, {}).get('entities', [])
            for entity in entities:
                db_entity = KnowledgeEntity(
                    id=entity.id,
                    name=entity.name,
                    type=entity.type.value,
                    document_id=self.document_id,
                    project_id=self.project_id,
                    aliases=list(entity.aliases) if hasattr(entity, 'aliases') else [],
                    confidence=entity.confidence if hasattr(entity, 'confidence') else 1.0,
                    metadata={'mentions': len(entity.mentions) if hasattr(entity, 'mentions') else 0}
                )
                self.db.add(db_entity)

            # 3. 保存关系
            relations = self.results.get(PipelineStep.RELATION.value, {}).get('relations', [])
            for relation in relations:
                db_relation = KnowledgeRelation(
                    id=relation.id,
                    type=relation.type.value,
                    source_entity_id=relation.source_id,
                    target_entity_id=relation.target_id,
                    document_id=self.document_id,
                    project_id=self.project_id,
                    confidence=relation.confidence if hasattr(relation, 'confidence') else 1.0,
                    evidence=relation.evidence if hasattr(relation, 'evidence') else []
                )
                self.db.add(db_relation)

            # 4. 保存事件
            events = self.results.get(PipelineStep.EVENT.value, {}).get('events', [])
            for event in events:
                db_event = KnowledgeEvent(
                    id=event.id,
                    type=event.type.value,
                    trigger=event.trigger,
                    document_id=self.document_id,
                    project_id=self.project_id,
                    who=event.who if hasattr(event, 'who') else [],
                    what=event.what if hasattr(event, 'what') else '',
                    when=event.when if hasattr(event, 'when') else [],
                    where=event.where if hasattr(event, 'where') else [],
                    why=event.why if hasattr(event, 'why') else '',
                    how=event.how if hasattr(event, 'how') else '',
                    confidence=event.confidence if hasattr(event, 'confidence') else 1.0
                )
                self.db.add(db_event)

            # 5. 保存知识单元
            knowledge_units = self.results.get(PipelineStep.KNOWLEDGE.value, {}).get('knowledge_units', [])
            for unit in knowledge_units:
                db_unit = KnowledgeUnit(
                    id=unit.id,
                    type=unit.type.value,
                    title=unit.title,
                    content=unit.content,
                    document_id=self.document_id,
                    project_id=self.project_id,
                    importance=unit.importance,
                    confidence=unit.confidence,
                    completeness=unit.completeness,
                    tags=unit.tags,
                    source=unit.source
                )
                self.db.add(db_unit)

            await self.db.commit()
            logger.info("✅ 流水线结果持久化完成")

        except Exception as e:
            logger.error(f"❌ 持久化失败: {str(e)}")
            await self.db.rollback()
            raise

    def get_status(self) -> Dict[str, Any]:
        """获取当前状态"""
        return {
            'execution_id': self.execution_id,
            'status': self.status.value,
            'current_step': self.current_step.value if self.current_step else None,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'completed_steps': list(self.results.keys()),
            'errors': self.errors
        }
