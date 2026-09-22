"""
Agent能力增强模块 (Agent Enhancement)

实现意图识别、多轮对话、工具调用、任务编排等Agent核心能力
"""
from typing import List, Dict, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
import json
import re

logger = logging.getLogger(__name__)


# ============================================================================
# 意图识别 (Intent Recognition)
# ============================================================================

class IntentType(Enum):
    """意图类型"""
    QUERY = "query"                    # 信息查询
    SEARCH = "search"                  # 文档搜索
    SUMMARIZE = "summarize"            # 内容摘要
    COMPARE = "compare"                # 对比分析
    EXPLAIN = "explain"                # 解释说明
    HOWTO = "howto"                    # 操作指南
    TROUBLESHOOT = "troubleshoot"      # 问题排查
    RECOMMEND = "recommend"            # 推荐建议
    CALCULATE = "calculate"            # 计算分析
    TRANSLATE = "translate"            # 翻译转换
    UNKNOWN = "unknown"                # 未知意图


@dataclass
class Intent:
    """意图识别结果"""
    intent_type: IntentType
    confidence: float                   # 置信度 0-1
    entities: Dict[str, Any]           # 提取的实体
    keywords: List[str]                # 关键词
    constraints: Dict[str, Any]        # 约束条件

    def to_dict(self) -> Dict[str, Any]:
        return {
            "intent_type": self.intent_type.value,
            "confidence": self.confidence,
            "entities": self.entities,
            "keywords": self.keywords,
            "constraints": self.constraints
        }


class IntentRecognizer:
    """
    意图识别器

    基于规则和模式匹配的意图识别
    """

    # 意图关键词模式
    INTENT_PATTERNS = {
        IntentType.QUERY: [
            r'(什么是|是什么|介绍.*|.*定义)',
            r'(what is|define|introduction)',
        ],
        IntentType.SEARCH: [
            r'(查找|搜索|找.*|检索)',
            r'(search|find|look for)',
        ],
        IntentType.SUMMARIZE: [
            r'(总结|摘要|概括|归纳)',
            r'(summarize|summary|overview)',
        ],
        IntentType.COMPARE: [
            r'(对比|比较|差异|区别)',
            r'(compare|difference|versus|vs)',
        ],
        IntentType.EXPLAIN: [
            r'(解释|说明|为什么|原因)',
            r'(explain|why|reason|how come)',
        ],
        IntentType.HOWTO: [
            r'(如何|怎么|怎样.*|.*步骤|.*方法)',
            r'(how to|how do|steps|guide)',
        ],
        IntentType.TROUBLESHOOT: [
            r'(问题|错误|故障|失败|报错)',
            r'(error|problem|issue|fail|troubleshoot)',
        ],
        IntentType.RECOMMEND: [
            r'(推荐|建议|选择.*|.*最好)',
            r'(recommend|suggest|best|should)',
        ],
        IntentType.CALCULATE: [
            r'(计算|统计|多少|数量)',
            r'(calculate|compute|count|how many)',
        ],
        IntentType.TRANSLATE: [
            r'(翻译|转换)',
            r'(translate|convert)',
        ],
    }

    def recognize(self, query: str) -> Intent:
        """
        识别用户意图

        Args:
            query: 用户查询

        Returns:
            意图识别结果
        """
        # 提取关键词
        keywords = self._extract_keywords(query)

        # 提取实体
        entities = self._extract_entities(query)

        # 匹配意图
        intent_scores: Dict[IntentType, float] = {}

        for intent_type, patterns in self.INTENT_PATTERNS.items():
            score = 0.0
            for pattern in patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    score += 1.0

            if score > 0:
                intent_scores[intent_type] = score / len(patterns)

        # 选择最高分意图
        if intent_scores:
            best_intent = max(intent_scores.items(), key=lambda x: x[1])
            intent_type, confidence = best_intent
        else:
            intent_type = IntentType.UNKNOWN
            confidence = 0.0

        return Intent(
            intent_type=intent_type,
            confidence=confidence,
            entities=entities,
            keywords=keywords,
            constraints={}
        )

    @staticmethod
    def _extract_keywords(text: str) -> List[str]:
        """提取关键词"""
        # 简单实现：提取名词性词汇
        words = re.findall(r'[a-zA-Z]+|[一-鿿]+', text)

        # 过滤停用词
        stopwords = {'的', '了', '是', '在', '和', 'the', 'is', 'a', 'an', 'and', 'or'}
        keywords = [w for w in words if w.lower() not in stopwords and len(w) > 1]

        return keywords

    @staticmethod
    def _extract_entities(text: str) -> Dict[str, Any]:
        """提取实体（简化版）"""
        entities = {}

        # 提取文件格式
        formats = re.findall(r'(PDF|Word|Excel|Markdown|txt|md|doc|docx)', text, re.IGNORECASE)
        if formats:
            entities['file_formats'] = list(set(formats))

        # 提取数字
        numbers = re.findall(r'\d+', text)
        if numbers:
            entities['numbers'] = [int(n) for n in numbers]

        # 提取URL
        urls = re.findall(r'https?://[^\s]+', text)
        if urls:
            entities['urls'] = urls

        return entities


# ============================================================================
# 多轮对话管理 (Multi-turn Conversation)
# ============================================================================

@dataclass
class ConversationTurn:
    """对话轮次"""
    turn_id: int
    user_message: str
    assistant_message: str
    intent: Optional[Intent] = None
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "turn_id": self.turn_id,
            "user_message": self.user_message,
            "assistant_message": self.assistant_message,
            "intent": self.intent.to_dict() if self.intent else None,
            "context": self.context,
            "timestamp": self.timestamp.isoformat()
        }


class ConversationManager:
    """
    对话管理器

    管理多轮对话历史和上下文
    """

    def __init__(self, max_history: int = 10):
        """
        初始化对话管理器

        Args:
            max_history: 保留的最大历史轮数
        """
        self.max_history = max_history
        self.conversation_id = self._generate_conversation_id()
        self.turns: List[ConversationTurn] = []
        self.shared_context: Dict[str, Any] = {}  # 跨轮次共享的上下文

    def add_turn(
        self,
        user_message: str,
        assistant_message: str,
        intent: Optional[Intent] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ConversationTurn:
        """
        添加对话轮次

        Args:
            user_message: 用户消息
            assistant_message: 助手回复
            intent: 意图识别结果
            context: 本轮上下文

        Returns:
            对话轮次对象
        """
        turn_id = len(self.turns) + 1

        turn = ConversationTurn(
            turn_id=turn_id,
            user_message=user_message,
            assistant_message=assistant_message,
            intent=intent,
            context=context or {}
        )

        self.turns.append(turn)

        # 保持历史长度限制
        if len(self.turns) > self.max_history:
            self.turns.pop(0)

        logger.info(f"Added conversation turn {turn_id} to {self.conversation_id}")
        return turn

    def get_recent_turns(self, n: int = 3) -> List[ConversationTurn]:
        """获取最近N轮对话"""
        return self.turns[-n:] if self.turns else []

    def get_context_summary(self) -> str:
        """
        获取上下文摘要

        用于构建prompt时提供对话历史
        """
        if not self.turns:
            return ""

        recent_turns = self.get_recent_turns(3)

        summary_parts = ["Recent conversation:"]
        for turn in recent_turns:
            summary_parts.append(f"User: {turn.user_message}")
            summary_parts.append(f"Assistant: {turn.assistant_message[:100]}...")

        return "\n".join(summary_parts)

    def extract_context_entities(self) -> Dict[str, Any]:
        """
        从历史对话中提取上下文实体

        用于理解用户的后续问题
        """
        entities = {}

        for turn in self.turns:
            if turn.intent and turn.intent.entities:
                for key, value in turn.intent.entities.items():
                    if key not in entities:
                        entities[key] = value

        return entities

    def clear_history(self):
        """清空对话历史"""
        self.turns.clear()
        self.shared_context.clear()
        logger.info(f"Cleared conversation history for {self.conversation_id}")

    @staticmethod
    def _generate_conversation_id() -> str:
        """生成对话ID"""
        import uuid
        return f"conv_{uuid.uuid4().hex[:8]}"


# ============================================================================
# 工具调用 (Tool Calling)
# ============================================================================

@dataclass
class Tool:
    """工具定义"""
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema格式
    function: Callable

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }


@dataclass
class ToolCall:
    """工具调用记录"""
    tool_name: str
    arguments: Dict[str, Any]
    result: Any
    success: bool
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "arguments": self.arguments,
            "result": str(self.result) if not isinstance(self.result, (dict, list)) else self.result,
            "success": self.success,
            "error": self.error,
            "timestamp": self.timestamp.isoformat()
        }


class ToolRegistry:
    """
    工具注册表

    管理可用工具的注册和调用
    """

    def __init__(self):
        """初始化工具注册表"""
        self.tools: Dict[str, Tool] = {}

    def register(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        function: Callable
    ):
        """
        注册工具

        Args:
            name: 工具名称
            description: 工具描述
            parameters: 参数定义（JSON Schema）
            function: 工具函数
        """
        tool = Tool(
            name=name,
            description=description,
            parameters=parameters,
            function=function
        )

        self.tools[name] = tool
        logger.info(f"Registered tool: {name}")

    def call(self, tool_name: str, **kwargs) -> ToolCall:
        """
        调用工具

        Args:
            tool_name: 工具名称
            **kwargs: 工具参数

        Returns:
            工具调用记录
        """
        if tool_name not in self.tools:
            return ToolCall(
                tool_name=tool_name,
                arguments=kwargs,
                result=None,
                success=False,
                error=f"Tool '{tool_name}' not found"
            )

        tool = self.tools[tool_name]

        try:
            # 调用工具函数
            result = tool.function(**kwargs)

            return ToolCall(
                tool_name=tool_name,
                arguments=kwargs,
                result=result,
                success=True
            )

        except Exception as e:
            logger.error(f"Tool call failed: {tool_name}, error: {str(e)}")
            return ToolCall(
                tool_name=tool_name,
                arguments=kwargs,
                result=None,
                success=False,
                error=str(e)
            )

    def list_tools(self) -> List[Dict[str, Any]]:
        """列出所有可用工具"""
        return [tool.to_dict() for tool in self.tools.values()]

    def get_tool(self, name: str) -> Optional[Tool]:
        """获取工具定义"""
        return self.tools.get(name)


# ============================================================================
# 任务编排 (Task Orchestration)
# ============================================================================

class TaskType(Enum):
    """任务类型"""
    RETRIEVAL = "retrieval"           # 检索任务
    GENERATION = "generation"         # 生成任务
    ANALYSIS = "analysis"             # 分析任务
    TOOL_CALL = "tool_call"          # 工具调用任务
    COMPOSITE = "composite"           # 组合任务


@dataclass
class Task:
    """任务定义"""
    task_id: str
    task_type: TaskType
    description: str
    dependencies: List[str] = field(default_factory=list)  # 依赖的任务ID
    parameters: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"  # pending, running, completed, failed
    result: Any = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type.value,
            "description": self.description,
            "dependencies": self.dependencies,
            "parameters": self.parameters,
            "status": self.status,
            "result": str(self.result) if self.result and not isinstance(self.result, (dict, list)) else self.result,
            "error": self.error
        }


class TaskOrchestrator:
    """
    任务编排器

    管理复杂任务的分解和执行
    """

    def __init__(self):
        """初始化任务编排器"""
        self.tasks: Dict[str, Task] = {}
        self.execution_order: List[str] = []

    def add_task(
        self,
        task_id: str,
        task_type: TaskType,
        description: str,
        dependencies: Optional[List[str]] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Task:
        """
        添加任务

        Args:
            task_id: 任务ID
            task_type: 任务类型
            description: 任务描述
            dependencies: 依赖任务列表
            parameters: 任务参数

        Returns:
            任务对象
        """
        task = Task(
            task_id=task_id,
            task_type=task_type,
            description=description,
            dependencies=dependencies or [],
            parameters=parameters or {}
        )

        self.tasks[task_id] = task
        logger.info(f"Added task: {task_id} ({task_type.value})")

        return task

    def build_execution_plan(self) -> List[str]:
        """
        构建执行计划（拓扑排序）

        Returns:
            按依赖关系排序的任务ID列表
        """
        # 计算入度
        in_degree: Dict[str, int] = {task_id: 0 for task_id in self.tasks}

        for task in self.tasks.values():
            for dep in task.dependencies:
                if dep in in_degree:
                    in_degree[task.task_id] += 1

        # 拓扑排序
        queue = [task_id for task_id, degree in in_degree.items() if degree == 0]
        execution_order = []

        while queue:
            current = queue.pop(0)
            execution_order.append(current)

            # 找到依赖当前任务的任务
            for task in self.tasks.values():
                if current in task.dependencies:
                    in_degree[task.task_id] -= 1
                    if in_degree[task.task_id] == 0:
                        queue.append(task.task_id)

        # 检查循环依赖
        if len(execution_order) != len(self.tasks):
            raise ValueError("Circular dependency detected in tasks")

        self.execution_order = execution_order
        return execution_order

    def execute_task(self, task_id: str, executor: Callable) -> Any:
        """
        执行单个任务

        Args:
            task_id: 任务ID
            executor: 执行函数

        Returns:
            任务结果
        """
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")

        task = self.tasks[task_id]

        # 检查依赖是否完成
        for dep_id in task.dependencies:
            dep_task = self.tasks[dep_id]
            if dep_task.status != "completed":
                raise RuntimeError(f"Dependency {dep_id} not completed")

        # 执行任务
        task.status = "running"

        try:
            result = executor(task)
            task.result = result
            task.status = "completed"
            logger.info(f"Task {task_id} completed successfully")
            return result

        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            logger.error(f"Task {task_id} failed: {str(e)}")
            raise

    def get_task_results(self) -> Dict[str, Any]:
        """获取所有任务结果"""
        return {
            task_id: task.result
            for task_id, task in self.tasks.items()
            if task.status == "completed"
        }

    def reset(self):
        """重置所有任务状态"""
        for task in self.tasks.values():
            task.status = "pending"
            task.result = None
            task.error = None

        self.execution_order.clear()


# ============================================================================
# 内置工具函数
# ============================================================================

def tool_calculate(expression: str) -> Union[float, str]:
    """计算工具"""
    try:
        # 安全的数学表达式求值
        allowed_names = {"abs": abs, "round": round, "min": min, "max": max}
        result = eval(expression, {"__builtins__": {}}, allowed_names)
        return float(result)
    except Exception as e:
        return f"计算错误: {str(e)}"


def tool_count_words(text: str) -> int:
    """词数统计工具"""
    words = re.findall(r'\w+', text)
    return len(words)


def tool_extract_urls(text: str) -> List[str]:
    """URL提取工具"""
    urls = re.findall(r'https?://[^\s]+', text)
    return urls


def tool_format_json(data: str) -> str:
    """JSON格式化工具"""
    try:
        obj = json.loads(data)
        return json.dumps(obj, indent=2, ensure_ascii=False)
    except Exception as e:
        return f"JSON格式化错误: {str(e)}"
