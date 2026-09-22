"""
FieldMind 多Agent系统
提供田野调查资料的智能分析能力
"""

from .base_agent import AgentBase as BaseAgent, AgentResult
from .coordinator import AgentCoordinator

__all__ = [
    'BaseAgent',
    'AgentResult',
    'AgentCoordinator'
]
