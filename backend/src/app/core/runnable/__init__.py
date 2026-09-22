"""
Runnable模块

基于LangChain的Runnable设计，提供统一的可运行接口
"""
from app.core.runnable.base import (
    Runnable,
    RunnableSequence,
    RunnableParallel,
    RunnableBranch,
    RunnableLambda
)

from app.core.runnable.utils import (
    RunnablePassthrough,
    RunnableMap,
    RunnableAssign,
    RunnablePick,
    chain,
    parallel
)

from app.core.runnable.adapters import (
    RunnableChat,
    RunnableRAG,
    RunnableAgent,
    RunnableSkill
)

__all__ = [
    # 基础
    'Runnable',
    'RunnableSequence',
    'RunnableParallel',
    'RunnableBranch',
    'RunnableLambda',

    # 工具
    'RunnablePassthrough',
    'RunnableMap',
    'RunnableAssign',
    'RunnablePick',
    'chain',
    'parallel',

    # 适配器
    'RunnableChat',
    'RunnableRAG',
    'RunnableAgent',
    'RunnableSkill'
]
