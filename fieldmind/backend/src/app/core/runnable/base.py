"""
Runnable统一接口

基于LangChain的Runnable设计，为FieldMind所有AI服务提供统一接口
"""
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Iterator, AsyncIterator
import asyncio

logger = logging.getLogger(__name__)


class Runnable(ABC):
    """
    可运行接口 - 所有AI服务的统一接口

    基于LangChain的Runnable设计，提供：
    1. 统一的invoke接口
    2. 异步支持
    3. 流式处理
    4. 链式组合（管道操作符）
    """

    @abstractmethod
    def invoke(self, input: Any, config: Optional[Dict] = None) -> Any:
        """
        同步执行

        Args:
            input: 输入数据
            config: 配置选项

        Returns:
            执行结果
        """
        pass

    @abstractmethod
    async def ainvoke(self, input: Any, config: Optional[Dict] = None) -> Any:
        """
        异步执行

        Args:
            input: 输入数据
            config: 配置选项

        Returns:
            执行结果
        """
        pass

    def stream(self, input: Any, config: Optional[Dict] = None) -> Iterator[Any]:
        """
        流式执行（同步）

        Args:
            input: 输入数据
            config: 配置选项

        Yields:
            执行结果的增量
        """
        # 默认实现：返回完整结果
        yield self.invoke(input, config)

    async def astream(
        self,
        input: Any,
        config: Optional[Dict] = None
    ) -> AsyncIterator[Any]:
        """
        流式执行（异步）

        Args:
            input: 输入数据
            config: 配置选项

        Yields:
            执行结果的增量
        """
        # 默认实现：返回完整结果
        yield await self.ainvoke(input, config)

    def batch(
        self,
        inputs: list,
        config: Optional[Dict] = None
    ) -> list:
        """
        批量执行（同步）

        Args:
            inputs: 输入列表
            config: 配置选项

        Returns:
            结果列表
        """
        return [self.invoke(input, config) for input in inputs]

    async def abatch(
        self,
        inputs: list,
        config: Optional[Dict] = None
    ) -> list:
        """
        批量执行（异步）

        Args:
            inputs: 输入列表
            config: 配置选项

        Returns:
            结果列表
        """
        tasks = [self.ainvoke(input, config) for input in inputs]
        return await asyncio.gather(*tasks)

    def __or__(self, other: 'Runnable') -> 'RunnableSequence':
        """
        管道操作符 |

        允许链式组合：
        chain = runnable1 | runnable2 | runnable3

        Args:
            other: 下一个Runnable

        Returns:
            组合后的RunnableSequence
        """
        return RunnableSequence(self, other)

    def __ror__(self, other: Any) -> 'RunnableSequence':
        """反向管道操作符（支持非Runnable对象）"""
        from app.core.runnable.passthrough import RunnablePassthrough
        return RunnablePassthrough() | self


class RunnableSequence(Runnable):
    """
    可运行序列 - 链式组合多个Runnable

    支持：
    chain = step1 | step2 | step3
    result = chain.invoke(input)
    """

    def __init__(self, *runnables: Runnable):
        """
        初始化序列

        Args:
            *runnables: 多个Runnable实例
        """
        self.runnables = list(runnables)

    def invoke(self, input: Any, config: Optional[Dict] = None) -> Any:
        """顺序执行所有Runnable"""
        result = input

        for runnable in self.runnables:
            result = runnable.invoke(result, config)

        return result

    async def ainvoke(self, input: Any, config: Optional[Dict] = None) -> Any:
        """异步顺序执行所有Runnable"""
        result = input

        for runnable in self.runnables:
            result = await runnable.ainvoke(result, config)

        return result

    def stream(self, input: Any, config: Optional[Dict] = None) -> Iterator[Any]:
        """流式执行序列"""
        result = input

        for i, runnable in enumerate(self.runnables):
            is_last = (i == len(self.runnables) - 1)

            if is_last:
                # 最后一个：流式返回
                for chunk in runnable.stream(result, config):
                    yield chunk
            else:
                # 中间步骤：完整执行
                result = runnable.invoke(result, config)

    async def astream(
        self,
        input: Any,
        config: Optional[Dict] = None
    ) -> AsyncIterator[Any]:
        """异步流式执行序列"""
        result = input

        for i, runnable in enumerate(self.runnables):
            is_last = (i == len(self.runnables) - 1)

            if is_last:
                # 最后一个：流式返回
                async for chunk in runnable.astream(result, config):
                    yield chunk
            else:
                # 中间步骤：完整执行
                result = await runnable.ainvoke(result, config)

    def __or__(self, other: Runnable) -> 'RunnableSequence':
        """继续链式组合"""
        return RunnableSequence(*self.runnables, other)


class RunnableParallel(Runnable):
    """
    并行可运行 - 并行执行多个Runnable

    用法：
    parallel = RunnableParallel(
        summary=summary_runnable,
        entities=entity_runnable
    )
    result = parallel.invoke(input)
    # result = {'summary': '...', 'entities': [...]}
    """

    def __init__(self, **runnables: Runnable):
        """
        初始化并行执行器

        Args:
            **runnables: 命名的Runnable实例
        """
        self.runnables = runnables

    def invoke(self, input: Any, config: Optional[Dict] = None) -> Dict[str, Any]:
        """并行执行所有Runnable（同步）"""
        return {
            key: runnable.invoke(input, config)
            for key, runnable in self.runnables.items()
        }

    async def ainvoke(self, input: Any, config: Optional[Dict] = None) -> Dict[str, Any]:
        """并行执行所有Runnable（异步）"""
        tasks = {
            key: runnable.ainvoke(input, config)
            for key, runnable in self.runnables.items()
        }

        results = await asyncio.gather(*tasks.values())

        return dict(zip(tasks.keys(), results))


class RunnableBranch(Runnable):
    """
    条件分支 - 根据条件选择执行路径

    用法：
    branch = RunnableBranch(
        (condition1, runnable1),
        (condition2, runnable2),
        default_runnable
    )
    """

    def __init__(self, *branches, default: Optional[Runnable] = None):
        """
        初始化分支

        Args:
            *branches: (condition, runnable) 元组
            default: 默认Runnable
        """
        self.branches = branches
        self.default = default

    def invoke(self, input: Any, config: Optional[Dict] = None) -> Any:
        """根据条件选择分支执行"""
        for condition, runnable in self.branches:
            if callable(condition):
                if condition(input):
                    return runnable.invoke(input, config)
            elif condition:
                return runnable.invoke(input, config)

        if self.default:
            return self.default.invoke(input, config)

        raise ValueError("No matching branch and no default provided")

    async def ainvoke(self, input: Any, config: Optional[Dict] = None) -> Any:
        """异步根据条件选择分支执行"""
        for condition, runnable in self.branches:
            if callable(condition):
                if condition(input):
                    return await runnable.ainvoke(input, config)
            elif condition:
                return await runnable.ainvoke(input, config)

        if self.default:
            return await self.default.ainvoke(input, config)

        raise ValueError("No matching branch and no default provided")


class RunnableLambda(Runnable):
    """
    Lambda包装器 - 将普通函数包装为Runnable

    用法：
    add_one = RunnableLambda(lambda x: x + 1)
    result = add_one.invoke(5)  # 6
    """

    def __init__(self, func, afunc=None):
        """
        初始化Lambda

        Args:
            func: 同步函数
            afunc: 异步函数（可选）
        """
        self.func = func
        self.afunc = afunc

    def invoke(self, input: Any, config: Optional[Dict] = None) -> Any:
        """执行函数"""
        return self.func(input)

    async def ainvoke(self, input: Any, config: Optional[Dict] = None) -> Any:
        """异步执行函数"""
        if self.afunc:
            return await self.afunc(input)
        else:
            # 在线程池中执行同步函数
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self.func, input)
