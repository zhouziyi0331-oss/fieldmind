"""
Super Agents 服务 V2 - 完全整合版
Super Agents Service V2 - Fully Integrated

整合模块：
1. AgentCoordinator - 多Agent编排
2. AgentRegistry - Agent注册中心
3. SpecializedAgents - 5个专业Agent

提供统一的多Agent编排能力
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.agent_coordinator import AgentCoordinator, ExecutionMode, get_agent_coordinator
from app.core.agent_registry import AgentRegistry, get_agent_registry
from app.services.agents.specialized_agents import (
    KnowledgeAgent,
    SearchAgent,
    SummaryAgent,
    TranscriptAgent,
    AnalysisAgent
)

logger = logging.getLogger(__name__)


class SuperAgentsServiceV2:
    """Super Agents 服务 V2"""
    def __init__(self, db: Session, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        """
        初始化服务

        Args:
            db: 数据库会话
        """
        self.db = db

        # 初始化核心组件
        self.registry = get_agent_registry()
        self.coordinator = get_agent_coordinator(self.registry)

        # 注册内置Agent
        self._register_builtin_agents()

        logger.info("✅ Super Agents 服务V2初始化完成")

    def _register_builtin_agents(self):
        """注册内置的专业Agent"""
        try:
            # 注册5个专业Agent类（延迟实例化）
            self.registry.register_agent_class("knowledge", KnowledgeAgent)
            self.registry.register_agent_class("search", SearchAgent)
            self.registry.register_agent_class("summary", SummaryAgent)
            self.registry.register_agent_class("transcript", TranscriptAgent)
            self.registry.register_agent_class("analysis", AnalysisAgent)

            logger.info("✅ 已注册5个内置Agent")

        except Exception as e:
            logger.error(f"❌ 注册内置Agent失败: {e}")

    # ==================== 单Agent执行 ====================

    def execute_agent(
        self,
        agent_type: str,
        input_data: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        执行单个Agent

        Args:
            agent_type: Agent类型
            input_data: 输入数据
            config: Agent配置

        Returns:
            执行结果
        """
        start_time = datetime.now()

        logger.info(f"🤖 执行单Agent: type={agent_type}")

        try:
            # 获取Agent实例
            agent = self.registry.get_agent(agent_type, config)

            if not agent:
                return {
                    'success': False,
                    'error': f"Agent '{agent_type}' not found"
                }

            # 执行
            result = agent.execute(input_data)

            processing_time = (datetime.now() - start_time).total_seconds()

            logger.info(
                f"✅ 单Agent执行完成: type={agent_type}, "
                f"time={processing_time:.2f}s"
            )

            return {
                'success': True,
                'agent_type': agent_type,
                'result': result,
                'processing_time': processing_time,
                'timestamp': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ 单Agent执行失败: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    # ==================== 多Agent编排 ====================

    def orchestrate_agents(
        self,
        tasks: List[Dict[str, Any]],
        mode: str = "dependency",
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        编排多个Agent

        Args:
            tasks: 任务列表，每个任务包含：
                {
                    'task_id': str,
                    'agent_type': str,
                    'input_data': dict,
                    'dependencies': [task_ids],  # 可选
                    'metadata': dict  # 可选
                }
            mode: 执行模式 (parallel/sequential/dependency)
            config: 配置选项

        Returns:
            编排结果
        """
        start_time = datetime.now()

        logger.info(
            f"🎯 开始多Agent编排: mode={mode}, "
            f"tasks={len(tasks)}"
        )

        try:
            # 转换模式
            execution_mode = ExecutionMode(mode)

            # 执行编排
            result = self.coordinator.orchestrate(
                tasks=tasks,
                mode=execution_mode,
                config=config or {}
            )

            processing_time = (datetime.now() - start_time).total_seconds()

            logger.info(
                f"✅ 多Agent编排完成: "
                f"success={result['success']}, "
                f"time={processing_time:.2f}s"
            )

            result['processing_time'] = processing_time

            return result

        except Exception as e:
            logger.error(f"❌ 多Agent编排失败: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    # ==================== 预设工作流 ====================

    def knowledge_extraction_workflow(
        self,
        text: str,
        project_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        知识提取工作流

        流程：
        1. 知识分析 (knowledge)
        2. 摘要生成 (summary)
        """
        tasks = [
            {
                'task_id': 'knowledge_analysis',
                'agent_type': 'knowledge',
                'input_data': {
                    'text': text,
                    'extract_entities': True,
                    'extract_relations': True,
                    'build_graph': True
                },
                'dependencies': []
            },
            {
                'task_id': 'summary_generation',
                'agent_type': 'summary',
                'input_data': {
                    'text': text,
                    'summary_type': 'structured',
                    'max_length': 500
                },
                'dependencies': []
            }
        ]

        return self.orchestrate_agents(
            tasks=tasks,
            mode='parallel',
            config={
                'aggregation_strategy': 'merge'
            }
        )

    def research_workflow(
        self,
        query: str,
        project_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        研究工作流

        流程：
        1. 智能检索 (search)
        2. 深度分析 (analysis) - 依赖检索结果
        3. 摘要生成 (summary) - 依赖分析结果
        """
        tasks = [
            {
                'task_id': 'search',
                'agent_type': 'search',
                'input_data': {
                    'query': query,
                    'sources': ['documents', 'memory'],
                    'top_k': 10,
                    'project_id': project_id
                },
                'dependencies': []
            },
            {
                'task_id': 'analysis',
                'agent_type': 'analysis',
                'input_data': {
                    'text': query,  # 将被检索结果替换
                    'analysis_type': 'research'
                },
                'dependencies': ['search']
            },
            {
                'task_id': 'summary',
                'agent_type': 'summary',
                'input_data': {
                    'text': '',  # 将被分析结果替换
                    'summary_type': 'detailed',
                    'max_length': 1000
                },
                'dependencies': ['analysis']
            }
        ]

        return self.orchestrate_agents(
            tasks=tasks,
            mode='dependency',
            config={
                'aggregation_strategy': 'hierarchy'
            }
        )

    def multi_perspective_analysis(
        self,
        text: str,
        perspectives: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        多视角分析工作流

        并行从多个视角分析同一文本：
        - 知识视角
        - 情感视角
        - 逻辑视角
        """
        if not perspectives:
            perspectives = ['knowledge', 'sentiment', 'logic']

        tasks = []

        for idx, perspective in enumerate(perspectives):
            tasks.append({
                'task_id': f'analysis_{perspective}',
                'agent_type': 'analysis',
                'input_data': {
                    'text': text,
                    'analysis_type': perspective
                },
                'dependencies': [],
                'metadata': {
                    'perspective': perspective
                }
            })

        # 添加汇总任务
        tasks.append({
            'task_id': 'summary_all',
            'agent_type': 'summary',
            'input_data': {
                'text': text,
                'summary_type': 'structured'
            },
            'dependencies': [f'analysis_{p}' for p in perspectives]
        })

        return self.orchestrate_agents(
            tasks=tasks,
            mode='dependency',
            config={
                'aggregation_strategy': 'hierarchy'
            }
        )

    # ==================== Agent管理 ====================

    def list_available_agents(
        self,
        capability: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        列出可用的Agent

        Args:
            capability: 筛选具有特定能力的Agent

        Returns:
            Agent列表
        """
        return self.registry.list_agents(
            capability=capability,
            include_metadata=True
        )

    def get_agent_info(self, agent_type: str) -> Optional[Dict[str, Any]]:
        """
        获取Agent信息

        Args:
            agent_type: Agent类型

        Returns:
            Agent信息
        """
        return self.registry.get_agent_metadata(agent_type)

    def register_custom_agent(
        self,
        agent_type: str,
        agent_instance: Any
    ) -> bool:
        """
        注册自定义Agent

        Args:
            agent_type: Agent类型
            agent_instance: Agent实例

        Returns:
            是否成功
        """
        return self.registry.register_agent(agent_type, agent_instance)

    # ==================== 执行历史 ====================

    def get_execution_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取执行历史"""
        return self.coordinator.get_execution_history(limit)

    def get_execution_statistics(self) -> Dict[str, Any]:
        """获取执行统计"""
        return self.registry.get_execution_statistics()

    # ==================== 服务状态 ====================

    def get_service_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        registry_status = self.registry.get_registry_status()
        coordinator_status = self.coordinator.get_coordinator_status()

        return {
            'service': 'super_agents_v2',
            'registry': registry_status,
            'coordinator': coordinator_status,
            'builtin_agents': [
                'knowledge', 'search', 'summary', 'transcript', 'analysis'
            ],
            'timestamp': datetime.utcnow().isoformat()
        }


# 工厂函数
def create_super_agents_service_v2(db: Session) -> SuperAgentsServiceV2:
    """创建Super Agents服务V2实例"""
    return SuperAgentsServiceV2(db)
