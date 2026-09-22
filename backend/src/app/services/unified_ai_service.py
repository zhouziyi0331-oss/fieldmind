"""
统一AI服务

整合所有分散的AI功能：enhanced_chat, super_agents, skills, rag, 自学习系统
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.logging import logger


class UnifiedAIService:
    """统一AI服务 - 整合所有AI功能的中央服务"""
    def __init__(self, db: Session, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.db = db
        self._chat_service = None
        self._agents_service = None
        self._skills_service = None
        self._rag_service = None
        self._learning_service = None

    # ==================== 聊天功能 ====================

    @property
    def chat(self):
        """增强聊天服务V2（延迟加载）- 整合记忆、思考、技能"""
        if self._chat_service is None:
            # 优先使用V2增强服务
            try:
                from app.services.enhanced_chat_service_v2 import create_enhanced_chat_service_v2
                self._chat_service = create_enhanced_chat_service_v2(self.db)
                logger.info("✅ 使用增强对话服务V2（完全整合版）")
            except Exception as e:
                logger.warning(f"⚠️ V2服务加载失败，尝试V1: {e}")
                try:
                    from app.services.enhanced_chat_service import EnhancedChatService
                    self._chat_service = EnhancedChatService()
                    logger.info("✅ 使用增强对话服务V1（传统版）")
                except Exception as e2:
                    logger.warning(f"⚠️ V1服务加载失败，使用基础聊天: {e2}")
                    self._chat_service = self._create_basic_chat()
        return self._chat_service

    def chat_with_context(
        self,
        message: str,
        user_id: int,
        project_id: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        带上下文的智能对话

        整合：
        - enhanced_chat的对话能力
        - conversation的记忆管理
        - 自学习系统的经验知识
        """
        return self.chat.process_message(
            message=message,
            user_id=user_id,
            project_id=project_id,
            context=context or {}
        )

    # ==================== Agent功能 ====================

    @property
    def agents(self):
        """超级Agent服务V2（延迟加载）- 整合编排、注册、专业Agent"""
        if self._agents_service is None:
            # 优先使用V2服务
            try:
                from app.services.super_agents_service_v2 import create_super_agents_service_v2
                self._agents_service = create_super_agents_service_v2(self.db)
                logger.info("✅ 使用Super Agents服务V2（完全整合版）")
            except Exception as e:
                logger.warning(f"⚠️ V2服务加载失败，尝试V1: {e}")
                try:
                    from app.services.super_agents_service import SuperAgentsService
                    self._agents_service = SuperAgentsService(self.db)
                    logger.info("✅ 使用Super Agents服务V1（传统版）")
                except Exception as e2:
                    logger.warning(f"⚠️ V1服务加载失败，使用基础Agent: {e2}")
                    self._agents_service = self._create_basic_agents()
        return self._agents_service

    def create_agent(
        self,
        agent_type: str,
        config: Dict[str, Any],
        user_id: int
    ) -> Dict[str, Any]:
        """
        创建AI Agent

        整合：
        - super_agents的Agent管理
        - skills的技能绑定
        - 自学习系统的能力进化
        """
        return self.agents.create(
            agent_type=agent_type,
            config=config,
            user_id=user_id
        )

    def execute_agent(
        self,
        agent_id: str,
        task: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行Agent任务"""
        return self.agents.execute(agent_id=agent_id, task=task)

    # ==================== 技能系统 ====================

    @property
    def skills(self):
        """统一技能服务V2（延迟加载）- 整合注册、执行、推荐、生成、优化"""
        if self._skills_service is None:
            # 优先使用V2完全整合版
            try:
                from app.services.unified_skill_system_v2 import create_unified_skill_system_v2
                self._skills_service = create_unified_skill_system_v2(self.db)
                logger.info("✅ 使用统一技能系统V2（完全整合版）")
            except Exception as e:
                logger.warning(f"⚠️ V2服务加载失败，尝试V1: {e}")
                try:
                    from app.services.unified_skills_service import UnifiedSkillsService
                    self._skills_service = UnifiedSkillsService(self.db)
                    logger.info("✅ 使用统一技能服务V1（传统版）")
                except Exception as e2:
                    logger.warning(f"⚠️ V1服务加载失败: {e2}")
                    self._skills_service = None
        return self._skills_service

    def get_skill(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """
        获取技能

        整合：
        - skills的手动定义技能
        - skill_generation的自动生成技能
        """
        return self.skills.get(skill_id)

    def execute_skill(
        self,
        skill_id: str,
        input_data: Dict[str, Any],
        user_id: int
    ) -> Dict[str, Any]:
        """
        执行技能

        自动记录到执行追踪系统
        """
        # 执行技能
        result = self.skills.execute(skill_id, input_data)

        # 记录到执行追踪系统
        try:
            from app.services.execution_tracker import ExecutionTracker
            tracker = ExecutionTracker(self.db)
            tracker.record_execution(
                execution_type="skill",
                skill_id=skill_id,
                input_data=input_data,
                output_data=result,
                user_id=user_id
            )
        except Exception as e:
            logger.error(f"记录执行失败: {e}")

        return result

    def list_available_skills(
        self,
        category: Optional[str] = None,
        include_generated: bool = True
    ) -> List[Dict[str, Any]]:
        """
        列出可用技能

        参数：
        - category: 技能类别
        - include_generated: 是否包含自动生成的技能
        """
        return self.skills.list_all(
            category=category,
            include_generated=include_generated
        )

    # ==================== RAG检索 ====================

    @property
    def rag(self):
        """统一RAG服务（延迟加载）- 整合Base/LightRAG/GraphRAG"""
        if self._rag_service is None:
            # 优先使用统一RAG引擎
            try:
                import asyncio
                from app.core.rag.unified_engine import get_unified_rag_engine

                # 在事件循环中初始化
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                self._rag_service = loop.run_until_complete(get_unified_rag_engine())
                logger.info("✅ 使用统一RAG引擎（完全整合版）")
            except Exception as e:
                logger.warning(f"⚠️ 统一RAG引擎加载失败: {e}")
                try:
                    from app.core.rag_engine import rag_engine
                    self._rag_service = rag_engine
                    logger.info("✅ 使用基础RAG引擎（传统版）")
                except Exception as e2:
                    logger.warning(f"⚠️ 基础RAG引擎加载失败: {e2}")
                    self._rag_service = self._create_basic_rag()
        return self._rag_service

    def retrieve_and_generate(
        self,
        query: str,
        project_id: Optional[int] = None,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        RAG检索增强生成

        整合：
        - rag的检索功能
        - knowledge_graph的图谱检索
        - experience_graph的经验检索
        """
        return self.rag.retrieve_and_generate(
            query=query,
            project_id=project_id,
            top_k=top_k
        )

    # ==================== 自学习系统 ====================

    @property
    def learning(self):
        """自学习系统（延迟加载）"""
        if self._learning_service is None:
            self._learning_service = self._create_learning_system()
        return self._learning_service

    def _create_learning_system(self):
        """创建自学习系统，整合阶段13-19"""
        from app.services.self_learning_system import SelfLearningSystem
        return SelfLearningSystem(self.db)

    def learn_from_execution(
        self,
        execution_id: str
    ) -> Dict[str, Any]:
        """
        从执行中学习

        启动完整的学习循环：
        1. 执行追踪
        2. 模式识别
        3. 技能生成
        4. 反馈收集
        """
        return self.learning.process_execution(execution_id)

    def get_learning_insights(
        self,
        project_id: int,
        insight_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取学习洞察"""
        return self.learning.get_insights(
            project_id=project_id,
            insight_type=insight_type
        )

    # ==================== 统一智能接口 ====================

    def smart_process(
        self,
        task_type: str,
        input_data: Dict[str, Any],
        user_id: int,
        project_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        智能处理 - 自动选择最佳方式处理任务

        根据任务类型自动路由到：
        - chat: 对话任务
        - agent: 复杂任务
        - skill: 特定技能
        - rag: 知识检索
        """
        logger.info(f"智能处理任务: {task_type}")

        if task_type == "chat" or task_type == "conversation":
            return self.chat_with_context(
                message=input_data.get("message", ""),
                user_id=user_id,
                project_id=project_id,
                context=input_data.get("context")
            )

        elif task_type == "agent" or task_type == "complex":
            # 创建并执行Agent
            agent = self.create_agent(
                agent_type="general",
                config=input_data.get("config", {}),
                user_id=user_id
            )
            return self.execute_agent(
                agent_id=agent["id"],
                task=input_data
            )

        elif task_type == "skill":
            # 执行特定技能
            return self.execute_skill(
                skill_id=input_data.get("skill_id"),
                input_data=input_data.get("data", {}),
                user_id=user_id
            )

        elif task_type == "rag" or task_type == "search":
            # RAG检索
            return self.retrieve_and_generate(
                query=input_data.get("query", ""),
                project_id=project_id,
                top_k=input_data.get("top_k", 5)
            )

        else:
            raise ValueError(f"不支持的任务类型: {task_type}")

    # ==================== 辅助方法 ====================

    def _create_basic_chat(self):
        """创建基础聊天服务"""
        class BasicChat:
            def __init__(self, db):
                self.db = db

            def process_message(self, message, user_id, project_id=None, context=None):
                return {
                    "response": "基础聊天功能",
                    "message": message
                }
        return BasicChat(self.db)

    def _create_basic_agents(self):
        """创建基础Agent服务"""
        class BasicAgents:
            def __init__(self, db):
                self.db = db

            def create(self, agent_type, config, user_id):
                return {"id": "agent_1", "type": agent_type}

            def execute(self, agent_id, task):
                return {"result": "基础Agent执行"}
        return BasicAgents(self.db)

    def _create_basic_rag(self):
        """创建基础RAG服务"""
        class BasicRAG:
            def __init__(self, db):
                self.db = db

            def retrieve_and_generate(self, query, project_id=None, top_k=5):
                return {
                    "query": query,
                    "results": [],
                    "generated": "基础RAG响应"
                }
        return BasicRAG(self.db)

    # ==================== 系统状态 ====================

    def get_system_status(self) -> Dict[str, Any]:
        """获取AI系统状态"""
        return {
            "services": {
                "chat": self._chat_service is not None,
                "agents": self._agents_service is not None,
                "skills": self._skills_service is not None,
                "rag": self._rag_service is not None,
                "learning": self._learning_service is not None
            },
            "timestamp": datetime.utcnow().isoformat()
        }
