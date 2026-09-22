# 结构化输出系统 - 使用指南

## 概述

结构化输出系统为 FieldMind 提供类型安全的 LLM 输出。基于 Instructor 的设计理念，支持：

- ✅ 自动验证和重试
- ✅ 类型强制转换
- ✅ 模糊字段匹配
- ✅ 流式部分结果
- ✅ 多种验证策略

## 快速开始

### 1. 定义响应模型

```python
from pydantic import BaseModel, Field
from typing import List, Optional

class Person(BaseModel):
    """人物信息"""
    name: str = Field(description="姓名")
    age: Optional[int] = Field(None, ge=0, le=150, description="年龄")
    occupation: Optional[str] = Field(None, description="职业")
    skills: List[str] = Field(default_factory=list, description="技能列表")
```

### 2. 创建客户端

```python
from app.core.structured_output import StructuredOutputClient

# 使用现有的 LLM 服务
client = StructuredOutputClient(llm_service)
```

### 3. 调用并获取结构化输出

```python
person = await client.create_async(
    messages=[
        {"role": "user", "content": "提取：张三，35岁，Python工程师"}
    ],
    response_model=Person,
    max_retries=3
)

print(person.name)  # "张三"
print(person.age)   # 35
```

## 核心特性

### 自动验证和重试

当 LLM 输出不符合模型时，系统会：
1. 解析验证错误
2. 将错误信息反馈给 LLM
3. 自动重试（最多 max_retries 次）

```python
result = await client.create_async(
    messages=messages,
    response_model=MyModel,
    max_retries=3  # 验证失败时最多重试3次
)
```

### 类型强制转换

自动处理常见的类型错误：

```python
# LLM 输出: {"age": "35"}  (字符串)
# 自动转换为: {"age": 35}  (整数)

# LLM 输出: {"is_active": "true"}  (字符串)
# 自动转换为: {"is_active": True}  (布尔)
```

### 模糊字段匹配

处理字段名不匹配：

```python
# LLM 输出: {"userName": "张三", "userAge": 35}  (驼峰命名)
# 自动匹配到: {"user_name": "张三", "user_age": 35}  (下划线命名)
```

### 枚举类型支持

```python
from enum import Enum

class Sentiment(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"

class Review(BaseModel):
    sentiment: Sentiment
    score: int = Field(ge=1, le=5)

# LLM 可以返回字符串，自动转换为枚举
```

### 验证策略

三种验证策略：

```python
# 严格模式（不做转换）
result = await client.create_async(
    messages=messages,
    response_model=MyModel,
    validation_strategy="strict"
)

# 强制转换模式（默认）
result = await client.create_async(
    messages=messages,
    response_model=MyModel,
    validation_strategy="coercive"  # 默认
)

# 宽松模式（转换失败时使用默认值）
result = await client.create_async(
    messages=messages,
    response_model=MyModel,
    validation_strategy="lenient"
)
```

### 观察者模式

监控验证过程：

```python
from app.core.structured_output.observers import LoggingObserver, MetricsObserver

# 添加观察者
logging_obs = LoggingObserver()
metrics_obs = MetricsObserver()

client.add_observer(logging_obs)
client.add_observer(metrics_obs)

# 执行调用
result = await client.create_async(...)

# 获取指标
report = metrics_obs.get_report()
print(f"成功率: {report['success_rate']}")
```

## 集成到 UnifiedAIService

### 方式1：直接使用

```python
from app.core.structured_output import StructuredOutputClient
from app.services.unified_ai_service import UnifiedAIService

# 在服务中使用
class MyService:
    def __init__(self, db):
        self.ai_service = UnifiedAIService(db)
        self.structured_client = StructuredOutputClient(
            self.ai_service.chat  # 使用聊天服务
        )
    
    async def extract_info(self, text: str):
        return await self.structured_client.create_async(
            messages=[{"role": "user", "content": text}],
            response_model=MyModel
        )
```

### 方式2：扩展 UnifiedAIService

在 `unified_ai_service.py` 中添加：

```python
@property
def structured(self):
    """结构化输出服务"""
    if not hasattr(self, '_structured_client'):
        from app.core.structured_output import StructuredOutputClient
        self._structured_client = StructuredOutputClient(self.chat)
    return self._structured_client

def extract_structured(
    self,
    message: str,
    response_model: Type[BaseModel],
    **kwargs
) -> BaseModel:
    """提取结构化数据"""
    return self.structured.create_async(
        messages=[{"role": "user", "content": message}],
        response_model=response_model,
        **kwargs
    )
```

## 实际应用场景

### 场景1：信息提取

```python
class Contact(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None

# 从文本中提取联系信息
contact = await client.create_async(
    messages=[{"role": "user", "content": "联系人：张三，电话13812345678"}],
    response_model=Contact
)
```

### 场景2：情感分析

```python
class SentimentAnalysis(BaseModel):
    sentiment: Sentiment
    score: int = Field(ge=1, le=5)
    keywords: List[str]

analysis = await client.create_async(
    messages=[{"role": "user", "content": "分析：这个产品太棒了！"}],
    response_model=SentimentAnalysis
)
```

### 场景3：数据转换

```python
class Document(BaseModel):
    title: str
    summary: str
    tags: List[str]
    word_count: int

doc = await client.create_async(
    messages=[{"role": "user", "content": f"总结文档：{long_text}"}],
    response_model=Document
)
```

### 场景4：多轮对话

```python
messages = [
    {"role": "system", "content": "你是一个数据提取助手"},
    {"role": "user", "content": "我叫张三"},
    {"role": "assistant", "content": "好的，我记住了"},
    {"role": "user", "content": "我35岁，是工程师"}
]

person = await client.create_async(
    messages=messages,
    response_model=Person
)
```

## 性能优化

### 1. 降低温度

结构化输出建议使用较低的温度：

```python
result = await client.create_async(
    messages=messages,
    response_model=MyModel,
    temperature=0.1  # 降低随机性
)
```

### 2. 缓存常见模式

对于相同类型的提取，可以缓存示例：

```python
# 在 Prompt 中添加示例
messages = [
    {"role": "system", "content": "提取人物信息，示例：..."},
    {"role": "user", "content": actual_text}
]
```

### 3. 批量处理

对于大量数据，考虑批量处理：

```python
tasks = [
    client.create_async(messages=[...], response_model=MyModel)
    for item in items
]

results = await asyncio.gather(*tasks)
```

## 调试技巧

### 查看生成的 Schema

```python
from app.core.structured_output.schema_generator import generate_json_schema
import json

schema = generate_json_schema(Person)
print(json.dumps(schema, indent=2))
```

### 使用 DebugObserver

```python
from app.core.structured_output.observers import DebugObserver

debug_obs = DebugObserver()
client.add_observer(debug_obs)

# 执行调用
result = await client.create_async(...)

# 查看详细历史
for event in debug_obs.get_history():
    print(event)
```

### 测试类型转换

```python
from app.core.structured_output.type_coercion import coerce_value

# 测试转换
result = coerce_value("123", int)
print(result)  # 123
```

## 常见问题

### Q: 如何处理嵌套模型？

A: 直接定义嵌套的 Pydantic 模型即可：

```python
class Address(BaseModel):
    city: str
    street: str

class Person(BaseModel):
    name: str
    address: Address  # 嵌套模型
```

### Q: 如何处理可选字段？

A: 使用 `Optional` 和默认值：

```python
from typing import Optional

class MyModel(BaseModel):
    required_field: str
    optional_field: Optional[str] = None
    field_with_default: str = "default_value"
```

### Q: 验证一直失败怎么办？

A: 检查以下几点：
1. 模型定义是否合理
2. 约束是否过于严格
3. 使用 DebugObserver 查看错误详情
4. 尝试使用 lenient 模式

### Q: 如何提高准确性？

A: 几个建议：
1. 在字段中添加详细的 description
2. 在模型的 docstring 中说明用途
3. 降低 temperature
4. 在 Prompt 中添加示例
5. 使用更强大的模型

## 测试

运行测试：

```bash
cd /Users/alwan/FieldMind/backend
PYTHONPATH=src:$PYTHONPATH python3 test_structured_output.py
```

## 总结

结构化输出系统提供了：

✅ **类型安全** - Pydantic 模型保证输出类型  
✅ **自动重试** - 验证失败时自动修正  
✅ **智能转换** - 处理常见类型错误  
✅ **容错能力** - 模糊字段匹配  
✅ **可观测性** - 观察者模式监控  
✅ **零样板** - 最小化模板代码  

使用这个系统，您可以让 LLM 的输出变得可预测、可靠、易于使用。
