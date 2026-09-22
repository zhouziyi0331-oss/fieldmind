"""
Agent 工具库

提供 Agent 可使用的各种工具
"""
from typing import Any, Dict, Optional
import math
import logging

from app.services.agents.core import Tool, ToolType

logger = logging.getLogger(__name__)


# 搜索工具
async def search_tool(query: str, max_results: int = 10) -> Dict[str, Any]:
    """
    搜索工具

    Args:
        query: 搜索查询
        max_results: 最大结果数

    Returns:
        搜索结果
    """
    # 模拟搜索（实际应该集成真实搜索服务）
    logger.info(f"Searching for: {query}")
    return {
        "query": query,
        "results": [
            {"title": f"Result {i+1}", "content": f"Content for {query}"}
            for i in range(min(3, max_results))
        ],
        "total": 3
    }


# 计算器工具
async def calculator_tool(expression: str) -> Dict[str, Any]:
    """
    计算器工具

    Args:
        expression: 数学表达式

    Returns:
        计算结果
    """
    try:
        # 安全的数学表达式评估
        allowed_names = {
            "abs": abs,
            "round": round,
            "min": min,
            "max": max,
            "sum": sum,
            "pow": pow,
            "sqrt": math.sqrt,
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "log": math.log,
            "pi": math.pi,
            "e": math.e
        }

        result = eval(expression, {"__builtins__": {}}, allowed_names)
        return {
            "expression": expression,
            "result": result,
            "success": True
        }
    except Exception as e:
        logger.error(f"Calculator error: {e}")
        return {
            "expression": expression,
            "error": str(e),
            "success": False
        }


# 代码执行工具
async def code_executor_tool(
    code: str,
    language: str = "python"
) -> Dict[str, Any]:
    """
    代码执行工具

    Args:
        code: 代码
        language: 编程语言

    Returns:
        执行结果
    """
    if language != "python":
        return {
            "error": f"Language {language} not supported",
            "success": False
        }

    try:
        # 注意：实际生产环境应该使用沙箱
        exec_globals = {}
        exec_locals = {}
        exec(code, exec_globals, exec_locals)

        return {
            "code": code,
            "output": exec_locals,
            "success": True
        }
    except Exception as e:
        logger.error(f"Code execution error: {e}")
        return {
            "code": code,
            "error": str(e),
            "success": False
        }


# 文件读取工具
async def file_reader_tool(file_path: str) -> Dict[str, Any]:
    """
    文件读取工具

    Args:
        file_path: 文件路径

    Returns:
        文件内容
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return {
            "file_path": file_path,
            "content": content,
            "size": len(content),
            "success": True
        }
    except Exception as e:
        logger.error(f"File read error: {e}")
        return {
            "file_path": file_path,
            "error": str(e),
            "success": False
        }


# API 调用工具
async def api_call_tool(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    API 调用工具

    Args:
        url: API URL
        method: HTTP 方法
        headers: 请求头
        data: 请求数据

    Returns:
        API 响应
    """
    try:
        import aiohttp

        async with aiohttp.ClientSession() as session:
            async with session.request(
                method=method,
                url=url,
                headers=headers,
                json=data
            ) as response:
                result = await response.json()

                return {
                    "url": url,
                    "status": response.status,
                    "result": result,
                    "success": True
                }
    except Exception as e:
        logger.error(f"API call error: {e}")
        return {
            "url": url,
            "error": str(e),
            "success": False
        }


# LLM 工具
async def llm_tool(
    prompt: str,
    model: str = "gpt-3.5-turbo",
    max_tokens: int = 500
) -> Dict[str, Any]:
    """
    LLM 工具

    Args:
        prompt: 提示词
        model: 模型名称
        max_tokens: 最大 token 数

    Returns:
        LLM 响应
    """
    # 这里应该集成实际的 LLM 服务
    # 暂时返回模拟响应
    return {
        "prompt": prompt,
        "model": model,
        "response": f"AI response to: {prompt}",
        "tokens_used": 50,
        "success": True
    }


# 工具工厂
class ToolFactory:
    """工具工厂"""

    @staticmethod
    def create_search_tool() -> Tool:
        """创建搜索工具"""
        return Tool(
            name="search",
            tool_type=ToolType.SEARCH,
            description="Search for information on the web",
            parameters={
                "query": {"type": "string", "required": True},
                "max_results": {"type": "integer", "default": 10}
            },
            executor=search_tool
        )

    @staticmethod
    def create_calculator_tool() -> Tool:
        """创建计算器工具"""
        return Tool(
            name="calculator",
            tool_type=ToolType.CALCULATOR,
            description="Perform mathematical calculations",
            parameters={
                "expression": {"type": "string", "required": True}
            },
            executor=calculator_tool
        )

    @staticmethod
    def create_code_executor_tool() -> Tool:
        """创建代码执行工具"""
        return Tool(
            name="code_executor",
            tool_type=ToolType.CODE_EXECUTOR,
            description="Execute code in various programming languages",
            parameters={
                "code": {"type": "string", "required": True},
                "language": {"type": "string", "default": "python"}
            },
            executor=code_executor_tool
        )

    @staticmethod
    def create_file_reader_tool() -> Tool:
        """创建文件读取工具"""
        return Tool(
            name="file_reader",
            tool_type=ToolType.FILE_READER,
            description="Read content from files",
            parameters={
                "file_path": {"type": "string", "required": True}
            },
            executor=file_reader_tool
        )

    @staticmethod
    def create_api_call_tool() -> Tool:
        """创建 API 调用工具"""
        return Tool(
            name="api_call",
            tool_type=ToolType.API_CALL,
            description="Make HTTP API calls",
            parameters={
                "url": {"type": "string", "required": True},
                "method": {"type": "string", "default": "GET"},
                "headers": {"type": "object"},
                "data": {"type": "object"}
            },
            executor=api_call_tool
        )

    @staticmethod
    def create_llm_tool() -> Tool:
        """创建 LLM 工具"""
        return Tool(
            name="llm",
            tool_type=ToolType.LLM,
            description="Call Large Language Model for text generation",
            parameters={
                "prompt": {"type": "string", "required": True},
                "model": {"type": "string", "default": "gpt-3.5-turbo"},
                "max_tokens": {"type": "integer", "default": 500}
            },
            executor=llm_tool
        )

    @staticmethod
    def create_all_tools() -> list[Tool]:
        """创建所有工具"""
        return [
            ToolFactory.create_search_tool(),
            ToolFactory.create_calculator_tool(),
            ToolFactory.create_code_executor_tool(),
            ToolFactory.create_file_reader_tool(),
            ToolFactory.create_api_call_tool(),
            ToolFactory.create_llm_tool()
        ]
