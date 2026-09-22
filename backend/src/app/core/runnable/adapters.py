"""
Runnable适配的AI服务示例

将现有的AI服务适配为Runnable接口
"""
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from app.core.runnable.base import Runnable
from app.services.unified_ai_service import UnifiedAIService


class RunnableChat(Runnable):
    """
    可运行的聊天服务

    用法：
    chat = RunnableChat(db)
    result = chat.invoke({
        'query': 'hello',
        'session_id': 'session_1'
    })

    # 或链式组合
    chain = memory_retrieval | RunnableChat(db) | response_formatter
    result = chain.invoke({'query': 'hello'})
    """

    def __init__(self, db: Session, config: Optional[Dict] = None):
        """
        初始化聊天服务

        Args:
            db: 数据库会话
            config: 默认配置
        """
        self.service = UnifiedAIService(db)
        self.default_config = config or {}

    def invoke(self, input: Dict, config: Optional[Dict] = None) -> Dict:
        """
        执行聊天

        Args:
            input: {
                'query': str,
                'session_id': str,
                'project_id': Optional[int],
                'user_id': Optional[int]
            }

        Returns:
            聊天结果
        """
        merged_config = {**self.default_config, **(config or {})}

        result = self.service.chat.chat(
            query=input['query'],
            session_id=input['session_id'],
            project_id=input.get('project_id'),
            user_id=input.get('user_id'),
            config=merged_config
        )

        return result

    async def ainvoke(self, input: Dict, config: Optional[Dict] = None) -> Dict:
        """异步执行聊天"""
        # 如果有异步版本
        if hasattr(self.service.chat, 'async_chat'):
            merged_config = {**self.default_config, **(config or {})}
            return await self.service.chat.async_chat(
                query=input['query'],
                session_id=input['session_id'],
                project_id=input.get('project_id'),
                user_id=input.get('user_id'),
                config=merged_config
            )
        else:
            # 降级到同步
            import asyncio
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                self.invoke,
                input,
                config
            )


class RunnableRAG(Runnable):
    """
    可运行的RAG服务

    用法：
    rag = RunnableRAG(db)
    result = await rag.ainvoke({
        'query': 'what is field research?',
        'mode': 'hybrid',
        'top_k': 5
    })
    """

    def __init__(self, db: Session):
        """初始化RAG服务"""
        self.service = UnifiedAIService(db)

    def invoke(self, input: Dict, config: Optional[Dict] = None) -> Dict:
        """执行RAG查询（同步版本会阻塞）"""
        import asyncio
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.ainvoke(input, config))

    async def ainvoke(self, input: Dict, config: Optional[Dict] = None) -> Dict:
        """异步执行RAG查询"""
        from app.core.rag.base_interface import RAGMode

        mode = RAGMode(input.get('mode', 'adaptive'))

        result = await self.service.rag.query(
            query=input['query'],
            mode=mode,
            top_k=input.get('top_k', 5),
            project_id=input.get('project_id')
        )

        return result


class RunnableAgent(Runnable):
    """
    可运行的Agent服务

    用法：
    agent = RunnableAgent(db)
    result = agent.invoke({
        'agent_type': 'knowledge',
        'input_data': {'text': '...'}
    })
    """

    def __init__(self, db: Session):
        """初始化Agent服务"""
        self.service = UnifiedAIService(db)

    def invoke(self, input: Dict, config: Optional[Dict] = None) -> Dict:
        """执行Agent"""
        result = self.service.agents.execute_agent(
            agent_type=input['agent_type'],
            input_data=input['input_data'],
            config=config or {}
        )

        return result

    async def ainvoke(self, input: Dict, config: Optional[Dict] = None) -> Dict:
        """异步执行Agent"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.invoke,
            input,
            config
        )


class RunnableSkill(Runnable):
    """
    可运行的技能服务

    用法：
    skill = RunnableSkill(db)
    result = await skill.ainvoke({
        'skill_id': 'skill_001',
        'input_data': {'text': '...'}
    })
    """

    def __init__(self, db: Session):
        """初始化技能服务"""
        self.service = UnifiedAIService(db)

    def invoke(self, input: Dict, config: Optional[Dict] = None) -> Dict:
        """执行技能（同步版本会阻塞）"""
        import asyncio
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.ainvoke(input, config))

    async def ainvoke(self, input: Dict, config: Optional[Dict] = None) -> Dict:
        """异步执行技能"""
        result = await self.service.skills.execute_skill(
            skill_id=input['skill_id'],
            input_data=input['input_data']
        )

        return result


# ==================== 使用示例 ====================

def example_usage():
    """使用示例"""
    from sqlalchemy.orm import Session
    from app.core.runnable.base import RunnableLambda
    from app.core.runnable.utils import chain, parallel

    # 假设有数据库会话
    db: Session = None

    # 示例1: 简单链式调用
    chat_chain = (
        RunnableLambda(lambda x: {'query': x, 'session_id': 'test'})
        | RunnableChat(db)
        | RunnableLambda(lambda x: x['answer'])
    )

    answer = chat_chain.invoke("你好")
    print(answer)

    # 示例2: 并行执行RAG和Agent
    parallel_chain = parallel(
        rag=RunnableRAG(db),
        knowledge=RunnableAgent(db)
    )

    result = parallel_chain.invoke({
        'query': '田野调查',
        'agent_type': 'knowledge',
        'input_data': {'text': '田野调查'}
    })
    print(result)  # {'rag': {...}, 'knowledge': {...}}

    # 示例3: 复杂工作流
    workflow = chain(
        # 1. 准备输入
        RunnableLambda(lambda x: {
            'query': x,
            'session_id': 'workflow',
            'mode': 'hybrid'
        }),

        # 2. 并行RAG和记忆检索
        parallel(
            rag=RunnableRAG(db),
            memory=RunnableLambda(lambda x: {'memory': 'retrieved'})
        ),

        # 3. 合并上下文
        RunnableLambda(lambda x: {
            'context': f"RAG: {x['rag']}\nMemory: {x['memory']}"
        }),

        # 4. 生成回答
        RunnableChat(db)
    )

    final_result = workflow.invoke("复杂查询")
    print(final_result)


if __name__ == '__main__':
    example_usage()
