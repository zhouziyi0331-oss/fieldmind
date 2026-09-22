"""
Runnable辅助组件

提供PassThrough、Map等实用工具
"""
from typing import Any, Dict, Optional, Callable
from app.core.runnable.base import Runnable


class RunnablePassthrough(Runnable):
    """
    透传 - 直接返回输入

    用法：
    chain = RunnablePassthrough() | process | output
    """

    def invoke(self, input: Any, config: Optional[Dict] = None) -> Any:
        """直接返回输入"""
        return input

    async def ainvoke(self, input: Any, config: Optional[Dict] = None) -> Any:
        """异步直接返回输入"""
        return input


class RunnableMap(Runnable):
    """
    映射 - 对列表中每个元素应用Runnable

    用法：
    mapper = RunnableMap(process_func)
    results = mapper.invoke([item1, item2, item3])
    """

    def __init__(self, runnable: Runnable):
        """
        初始化映射器

        Args:
            runnable: 要应用的Runnable
        """
        self.runnable = runnable

    def invoke(self, input: list, config: Optional[Dict] = None) -> list:
        """对每个元素应用Runnable"""
        return [self.runnable.invoke(item, config) for item in input]

    async def ainvoke(self, input: list, config: Optional[Dict] = None) -> list:
        """异步对每个元素应用Runnable"""
        import asyncio
        tasks = [self.runnable.ainvoke(item, config) for item in input]
        return await asyncio.gather(*tasks)


class RunnableAssign(Runnable):
    """
    赋值 - 将结果赋值到字典中

    用法：
    chain = RunnableAssign(summary=summarizer)
    result = chain.invoke({'text': '...'})
    # result = {'text': '...', 'summary': '...'}
    """

    def __init__(self, **runnables: Runnable):
        """
        初始化赋值器

        Args:
            **runnables: 命名的Runnable
        """
        self.runnables = runnables

    def invoke(self, input: Dict, config: Optional[Dict] = None) -> Dict:
        """执行并赋值"""
        result = input.copy() if isinstance(input, dict) else {}

        for key, runnable in self.runnables.items():
            result[key] = runnable.invoke(input, config)

        return result

    async def ainvoke(self, input: Dict, config: Optional[Dict] = None) -> Dict:
        """异步执行并赋值"""
        import asyncio
        result = input.copy() if isinstance(input, dict) else {}

        tasks = {
            key: runnable.ainvoke(input, config)
            for key, runnable in self.runnables.items()
        }

        values = await asyncio.gather(*tasks.values())

        for key, value in zip(tasks.keys(), values):
            result[key] = value

        return result


class RunnablePick(Runnable):
    """
    选择 - 从字典中选择特定键

    用法：
    picker = RunnablePick('result')
    value = picker.invoke({'result': 'x', 'meta': 'y'})
    # value = 'x'
    """

    def __init__(self, *keys: str):
        """
        初始化选择器

        Args:
            *keys: 要选择的键
        """
        self.keys = keys

    def invoke(self, input: Dict, config: Optional[Dict] = None) -> Any:
        """选择键值"""
        if len(self.keys) == 1:
            return input.get(self.keys[0])
        else:
            return {key: input.get(key) for key in self.keys}

    async def ainvoke(self, input: Dict, config: Optional[Dict] = None) -> Any:
        """异步选择键值"""
        return self.invoke(input, config)


def chain(*runnables: Runnable) -> Runnable:
    """
    便捷函数：创建链式组合

    用法：
    my_chain = chain(step1, step2, step3)
    """
    from app.core.runnable.base import RunnableSequence
    return RunnableSequence(*runnables)


def parallel(**runnables: Runnable) -> Runnable:
    """
    便捷函数：创建并行组合

    用法：
    my_parallel = parallel(
        summary=summarizer,
        entities=entity_extractor
    )
    """
    from app.core.runnable.base import RunnableParallel
    return RunnableParallel(**runnables)
