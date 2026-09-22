"""
流式支持

支持部分结果的流式返回
"""
from typing import TypeVar, Iterator, AsyncIterator
from pydantic import BaseModel
import json
from app.core.logging import logger

T = TypeVar('T', bound=BaseModel)


class PartialModel:
    """部分模型包装器

    允许模型字段逐步填充
    """

    def __init__(self, model_class: type[T]):
        self.model_class = model_class
        self._data = {}

    def update(self, data: dict):
        """更新部分数据"""
        self._data.update(data)

    def to_model(self) -> T:
        """转换为完整模型（如果可能）"""
        return self.model_class(**self._data)

    def to_partial_model(self) -> T:
        """转换为部分模型（填充默认值）"""
        # 填充缺失字段
        filled_data = self._data.copy()

        for field_name, field_info in self.model_class.model_fields.items():
            if field_name not in filled_data:
                if field_info.default is not None and field_info.default != ...:
                    filled_data[field_name] = field_info.default
                else:
                    # 使用 None 或类型默认值
                    filled_data[field_name] = None

        return self.model_class.model_construct(**filled_data)

    @property
    def data(self) -> dict:
        """当前数据"""
        return self._data.copy()


async def stream_partial(
    stream_iterator: AsyncIterator,
    model_class: type[T]
) -> AsyncIterator[T]:
    """流式解析部分模型

    Args:
        stream_iterator: 流式迭代器（返回文本片段）
        model_class: 目标模型类

    Yields:
        逐步完善的部分模型
    """
    accumulated = ""
    partial = PartialModel(model_class)

    async for chunk in stream_iterator:
        # 累积文本
        accumulated += chunk

        # 尝试解析 JSON
        try:
            cleaned = _clean_partial_json(accumulated)
            data = json.loads(cleaned)

            # 更新部分模型
            partial.update(data)

            # 返回当前状态
            yield partial.to_partial_model()

        except json.JSONDecodeError:
            # JSON 尚未完整，继续累积
            continue


def _clean_partial_json(text: str) -> str:
    """清理部分 JSON

    处理不完整的 JSON 字符串
    """
    text = text.strip()

    # 移除可能的前缀文本
    if '{' in text:
        text = text[text.find('{'):]

    # 补全不完整的括号
    open_braces = text.count('{')
    close_braces = text.count('}')

    if open_braces > close_braces:
        text += '}' * (open_braces - close_braces)

    # 移除末尾的逗号
    if text.rstrip().endswith(','):
        text = text.rstrip()[:-1]

    # 移除不完整的键值对
    # 查找最后一个完整的键值对
    lines = text.split('\n')
    cleaned_lines = []

    for line in lines:
        # 如果行包含完整的键值对或者是括号
        if ':' in line or line.strip() in ['{', '}', '[', ']']:
            cleaned_lines.append(line)

    return '\n'.join(cleaned_lines)


def stream_sync(
    stream_iterator: Iterator,
    model_class: type[T]
) -> Iterator[T]:
    """同步版本的流式解析"""
    accumulated = ""
    partial = PartialModel(model_class)

    for chunk in stream_iterator:
        accumulated += chunk

        try:
            cleaned = _clean_partial_json(accumulated)
            data = json.loads(cleaned)

            partial.update(data)
            yield partial.to_partial_model()

        except json.JSONDecodeError:
            continue
