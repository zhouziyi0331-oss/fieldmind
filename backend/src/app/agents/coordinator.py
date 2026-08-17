"""
AgentCoordinator - 多Agent协调器

职责：
1. 管理Agent执行顺序
2. 处理Agent之间的数据传递
3. 根据项目配置决定启用哪些Agent和Skill
4. 监控整体执行状态
"""

import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.agents.base_agent import BaseAgent, AgentResult
from app.models.project import Project

logger = logging.getLogger(__name__)


class AgentCoordinator:
    """
    Agent协调器

    负责编排多个Agent的执行流程
    """

    def __init__(self, project_id: int, db: Session):
        """
        初始化协调器

        Args:
            project_id: 项目ID
            db: 数据库会话
        """
        self.project_id = project_id
        self.db = db
        self.project = self._load_project()
        self.enabled_skills = self._load_enabled_skills()
        self.agent_registry = {}  # Agent注册表
        self.execution_log = []   # 执行日志

    def _load_project(self) -> Project:
        """加载项目配置"""
        project = self.db.query(Project).filter(Project.id == self.project_id).first()
        if not project:
            raise ValueError(f"项目不存在: {self.project_id}")
        return project

    def _load_enabled_skills(self) -> List[str]:
        """
        加载项目启用的Skill列表

        Returns:
            Skill ID列表，如 ['xiangtu_china', 'multi_village_sop']
        """
        if not self.project.settings:
            return []

        enabled = self.project.settings.get('enabled_skills', [])
        logger.info(f"项目 {self.project_id} 启用的Skill: {enabled}")
        return enabled

    def register_agent(self, agent: BaseAgent, agent_id: Optional[str] = None):
        """
        注册Agent到协调器

        Args:
            agent: Agent实例
            agent_id: Agent唯一标识（默认使用类名）
        """
        agent_id = agent_id or agent.agent_name
        self.agent_registry[agent_id] = agent
        logger.info(f"注册Agent: {agent_id}")

    def should_run_agent(self, agent_id: str) -> bool:
        """
        判断是否应该运行某个Agent

        Args:
            agent_id: Agent标识

        Returns:
            True表示应该运行
        """
        # 目前简单逻辑：所有注册的Agent都运行
        # 未来可以根据项目配置、文档类型等条件决定
        return agent_id in self.agent_registry

    def run(
        self,
        document_id: int,
        text_content: str,
        entities: Optional[List[Dict]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        执行完整的多Agent分析流程

        Args:
            document_id: 文档ID
            text_content: 文档文本内容
            entities: 已提取的实体列表（来自动态发现引擎）
            context: 额外的上下文信息

        Returns:
            包含所有Agent结果的字典
        """
        logger.info(f"🎯 协调器启动 - 文档ID: {document_id}, 项目ID: {self.project_id}")

        context = context or {}
        entities = entities or []

        # 准备共享的输入数据
        shared_input = {
            'document_id': document_id,
            'project_id': self.project_id,
            'text_content': text_content,
            'entities': entities,
            'enabled_skills': self.enabled_skills,
            'context': context
        }

        # 执行结果汇总
        results = {
            'document_id': document_id,
            'project_id': self.project_id,
            'agents_executed': [],
            'agent_results': {},
            'overall_success': True,
            'total_execution_time': 0.0
        }

        # 按顺序执行Agent
        execution_order = self._determine_execution_order()

        for agent_id in execution_order:
            if not self.should_run_agent(agent_id):
                logger.info(f"⏭️  跳过Agent: {agent_id}")
                continue

            agent = self.agent_registry[agent_id]

            # 准备该Agent的输入（可能依赖前面Agent的输出）
            agent_input = self._prepare_agent_input(agent_id, shared_input, results)

            # 执行Agent
            logger.info(f"▶️  执行Agent: {agent_id}")
            agent_result = agent.execute(agent_input)

            # 记录结果
            results['agents_executed'].append(agent_id)
            results['agent_results'][agent_id] = agent_result.to_dict()
            results['total_execution_time'] += agent_result.execution_time

            if not agent_result.success:
                results['overall_success'] = False
                logger.warning(f"⚠️  Agent {agent_id} 执行失败: {agent_result.errors}")
            else:
                logger.info(
                    f"✅ Agent {agent_id} 完成 "
                    f"(耗时: {agent_result.execution_time:.2f}s)"
                )

            # 记录执行日志
            self.execution_log.append({
                'agent_id': agent_id,
                'success': agent_result.success,
                'execution_time': agent_result.execution_time
            })

        logger.info(
            f"🎉 协调器完成 - 执行了 {len(results['agents_executed'])} 个Agent, "
            f"总耗时: {results['total_execution_time']:.2f}s"
        )

        return results

    def _determine_execution_order(self) -> List[str]:
        """
        确定Agent执行顺序

        Returns:
            Agent ID列表（按执行顺序）
        """
        # 标准执行顺序（根据架构文档）
        standard_order = [
            'EntityRelationAgent',      # 1. 实体关系分析
            'AcademicTheoryAgent',       # 2. 学术理论映射
            'FieldDimensionAgent',       # 3. 田野维度解构
            'KnowledgeGraphAgent',       # 4. 知识图谱构建
            'ReportGenerationAgent'      # 5. 报告生成
        ]

        # 只返回已注册的Agent
        return [aid for aid in standard_order if aid in self.agent_registry]

    def _prepare_agent_input(
        self,
        agent_id: str,
        shared_input: Dict[str, Any],
        previous_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        为特定Agent准备输入数据

        Args:
            agent_id: Agent标识
            shared_input: 共享输入数据
            previous_results: 之前Agent的执行结果

        Returns:
            该Agent的输入数据
        """
        # 基础输入：所有Agent都需要的数据
        agent_input = shared_input.copy()

        # 根据Agent类型添加特定输入
        if agent_id == 'EntityRelationAgent':
            # 第一个Agent，只需要基础输入
            pass

        elif agent_id == 'AcademicTheoryAgent':
            # 需要实体关系分析结果
            if 'EntityRelationAgent' in previous_results['agent_results']:
                entity_result = previous_results['agent_results']['EntityRelationAgent']
                agent_input['entity_relations'] = entity_result.get('data', {})

        elif agent_id == 'FieldDimensionAgent':
            # 需要实体信息
            if 'EntityRelationAgent' in previous_results['agent_results']:
                entity_result = previous_results['agent_results']['EntityRelationAgent']
                agent_input['entity_relations'] = entity_result.get('data', {})

        elif agent_id == 'KnowledgeGraphAgent':
            # 需要前面所有Agent的结果
            agent_input['entity_relations'] = previous_results['agent_results'].get(
                'EntityRelationAgent', {}
            ).get('data', {})
            agent_input['academic_mapping'] = previous_results['agent_results'].get(
                'AcademicTheoryAgent', {}
            ).get('data', {})
            agent_input['field_dimensions'] = previous_results['agent_results'].get(
                'FieldDimensionAgent', {}
            ).get('data', {})

        elif agent_id == 'ReportGenerationAgent':
            # 需要知识图谱
            if 'KnowledgeGraphAgent' in previous_results['agent_results']:
                kg_result = previous_results['agent_results']['KnowledgeGraphAgent']
                agent_input['knowledge_graph'] = kg_result.get('data', {})

            # 也需要前面的所有分析结果
            agent_input['all_analyses'] = previous_results['agent_results']

        return agent_input

    def get_execution_summary(self) -> Dict[str, Any]:
        """
        获取执行总结

        Returns:
            执行统计信息
        """
        if not self.execution_log:
            return {'status': 'not_run'}

        successful = sum(1 for log in self.execution_log if log['success'])
        failed = len(self.execution_log) - successful
        total_time = sum(log['execution_time'] for log in self.execution_log)

        return {
            'total_agents': len(self.execution_log),
            'successful': successful,
            'failed': failed,
            'total_execution_time': total_time,
            'average_execution_time': total_time / len(self.execution_log) if self.execution_log else 0,
            'execution_log': self.execution_log
        }
