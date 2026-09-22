"""
结构化输出客户端

提供类型安全的 LLM 调用接口
"""
from typing import Type, TypeVar, List, Dict, Any, Optional
from pydantic import BaseModel, ValidationError
import json
import asyncio
import time
from app.core.logging import logger

T = TypeVar('T', bound=BaseModel)


class StructuredOutputClient:
    """结构化输出客户端

    核心功能:
    1. 自动生成 JSON Schema
    2. 验证失败时自动重试
    3. 类型强制转换
    4. 模糊字段匹配
    """

    def __init__(self, llm_service):
        """初始化

        Args:
            llm_service: LLM 服务实例（需要有 complete/complete_async 方法）
        """
        self.llm = llm_service
        self.observers = []
        self._stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "retries": 0,
            "validation_errors": 0
        }

    def add_observer(self, observer):
        """添加观察者"""
        self.observers.append(observer)

    async def create_async(
        self,
        messages: List[Dict[str, str]],
        response_model: Type[T],
        max_retries: int = 3,
        validation_strategy: str = "coercive",
        **llm_kwargs
    ) -> T:
        """异步创建结构化输出

        Args:
            messages: 消息列表
            response_model: Pydantic 模型类
            max_retries: 最大重试次数
            validation_strategy: 验证策略 (strict/coercive/lenient)
            **llm_kwargs: LLM 额外参数

        Returns:
            验证后的 Pydantic 模型实例

        Raises:
            ValidationError: 达到最大重试次数后仍验证失败
        """
        self._stats["total_calls"] += 1

        # 生成 JSON Schema
        from .schema_generator import generate_json_schema
        schema = generate_json_schema(response_model)

        # 增强消息（添加 Schema 说明）
        enhanced_messages = self._enhance_messages(messages, schema, response_model)

        # 重试循环
        last_error = None
        for attempt in range(max_retries):
            try:
                # 通知观察者
                self._notify_start(response_model, messages)

                # 调用 LLM
                response = await self.llm.complete_async(
                    messages=enhanced_messages,
                    temperature=llm_kwargs.get("temperature", 0.1),  # 降低温度提高准确性
                    **llm_kwargs
                )

                # 解析 JSON
                try:
                    data = json.loads(response)
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON 解析失败 (尝试 {attempt+1}/{max_retries}): {e}")
                    # 尝试提取 JSON
                    data = self._extract_json_from_text(response)

                # 预处理数据
                data = self._preprocess_data(data, response_model, validation_strategy)

                # 验证模型
                result = response_model(**data)

                # 成功
                self._stats["successful_calls"] += 1
                self._notify_success(result)

                return result

            except ValidationError as e:
                last_error = e
                self._stats["validation_errors"] += 1

                # 通知观察者
                self._notify_error(e, attempt + 1)

                if attempt == max_retries - 1:
                    logger.error(f"达到最大重试次数 ({max_retries})，验证仍失败")
                    raise

                # 记录重试
                self._stats["retries"] += 1

                # 添加错误反馈到对话
                error_msg = self._format_validation_error(e)
                enhanced_messages.append({
                    "role": "assistant",
                    "content": response
                })
                enhanced_messages.append({
                    "role": "user",
                    "content": f"""验证失败。错误信息：

{error_msg}

请仔细检查并修正输出，确保：
1. 所有必需字段都存在
2. 字段类型正确
3. 遵守字段约束（最小值、最大值、格式等）

重新生成完整的 JSON 输出："""
                })

                # 指数退避
                await asyncio.sleep(0.5 * (2 ** attempt))

        raise last_error

    def create(
        self,
        messages: List[Dict[str, str]],
        response_model: Type[T],
        max_retries: int = 3,
        **llm_kwargs
    ) -> T:
        """同步版本（wrapper）"""
        return asyncio.run(
            self.create_async(messages, response_model, max_retries, **llm_kwargs)
        )

    def _enhance_messages(
        self,
        messages: List[Dict],
        schema: Dict,
        model: Type[BaseModel]
    ) -> List[Dict]:
        """增强消息，添加 Schema 指导"""
        schema_message = {
            "role": "system",
            "content": f"""你必须以严格的 JSON 格式返回，符合以下 Schema：

{json.dumps(schema, ensure_ascii=False, indent=2)}

模型说明: {model.__doc__ or model.__name__}

**重要要求**：
1. 只返回纯 JSON，不要有任何其他文本或解释
2. 确保所有必需字段（required）都存在
3. 字段类型必须完全正确
4. 遵守所有字段约束（minimum、maximum、pattern 等）
5. 对于可选字段，如果没有信息可以省略或设为 null

示例格式：
```json
{{
  "field1": "value1",
  "field2": 123
}}
```"""
        }

        return [schema_message] + messages

    def _preprocess_data(
        self,
        data: Dict,
        model: Type[BaseModel],
        strategy: str
    ) -> Dict:
        """预处理数据

        1. 模糊字段匹配
        2. 类型强制转换
        """
        # 1. 字段匹配
        from .field_matcher import match_fields_fuzzy
        data = match_fields_fuzzy(data, model)

        # 2. 类型转换
        if strategy in ("coercive", "lenient"):
            from .type_coercion import coerce_model_data
            data = coerce_model_data(data, model, lenient=(strategy == "lenient"))

        return data

    def _extract_json_from_text(self, text: str) -> Dict:
        """从文本中提取 JSON

        处理 LLM 可能在 JSON 前后添加说明文字的情况
        """
        import re

        # 查找 JSON 对象
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.finditer(json_pattern, text, re.DOTALL)

        for match in matches:
            try:
                json_str = match.group(0)
                return json.loads(json_str)
            except json.JSONDecodeError:
                continue

        # 尝试查找 ```json 代码块
        code_block_pattern = r'```json\s*(.*?)\s*```'
        code_matches = re.finditer(code_block_pattern, text, re.DOTALL)

        for match in code_matches:
            try:
                json_str = match.group(1)
                return json.loads(json_str)
            except json.JSONDecodeError:
                continue

        # 都失败了，抛出原始错误
        raise json.JSONDecodeError("无法从响应中提取有效的 JSON", text, 0)

    def _format_validation_error(self, error: ValidationError) -> str:
        """格式化验证错误为人类可读"""
        errors = []
        for err in error.errors():
            field_path = " -> ".join(str(x) for x in err['loc'])
            msg = err['msg']
            error_type = err['type']

            errors.append(f"• 字段 `{field_path}`: {msg} (类型: {error_type})")

        return "\n".join(errors)

    def _notify_start(self, model: Type[BaseModel], messages: List[Dict]):
        """通知观察者：开始验证"""
        for observer in self.observers:
            try:
                observer.on_validation_start(model, messages)
            except Exception as e:
                logger.warning(f"观察者通知失败: {e}")

    def _notify_success(self, result: BaseModel):
        """通知观察者：验证成功"""
        for observer in self.observers:
            try:
                observer.on_validation_success(result)
            except Exception as e:
                logger.warning(f"观察者通知失败: {e}")

    def _notify_error(self, error: ValidationError, attempt: int):
        """通知观察者：验证错误"""
        for observer in self.observers:
            try:
                observer.on_validation_error(error, attempt)
            except Exception as e:
                logger.warning(f"观察者通知失败: {e}")

    def get_stats(self) -> Dict[str, int]:
        """获取统计信息"""
        return self._stats.copy()
