# Instructor 深度分析报告

**插件名称**: Instructor  
**开发者**: Jason Liu  
**GitHub**: https://github.com/jxnl/instructor  
**Stars**: 7.4k+  
**类别**: 结构化输出框架  
**语言**: Python  
**分析日期**: 2026-08-29

---

## 1. 插件概述

### 核心定位
Instructor 是一个轻量级库，用于从 LLM 获取结构化输出。它使用 Pydantic 模型定义期望的输出格式，并自动处理验证、重试和类型转换。

### 核心特点
- **类型安全**: 基于 Pydantic 的强类型输出
- **自动重试**: 验证失败时自动重试
- **流式支持**: 支持部分结果流式返回
- **多模型支持**: OpenAI, Anthropic, Cohere, Ollama 等
- **验证器**: 自定义验证逻辑
- **零样板代码**: 最小化模板代码

### 架构设计
```
Instructor
├── Patching (猴子补丁)
│   ├── OpenAI Client Patch
│   ├── Anthropic Client Patch
│   └── Custom Client Patch
├── Response Model (响应模型)
│   ├── Pydantic Model
│   ├── Validation
│   └── Type Conversion
├── Retry Logic (重试逻辑)
│   ├── Validation Error Handler
│   ├── Max Retries
│   └── Exponential Backoff
├── Streaming (流式)
│   ├── Partial Model
│   ├── Iterable Model
│   └── Progressive Updates
└── Validators (验证器)
    ├── Field Validators
    ├── Model Validators
    └── Custom Validators
```

---

## 2. 核心概念

### 2.1 基础使用

```python
import instructor
from openai import OpenAI
from pydantic import BaseModel

# Patch OpenAI client
client = instructor.from_openai(OpenAI())

# 定义响应模型
class User(BaseModel):
    name: str
    age: int
    email: str

# 调用 LLM
user = client.chat.completions.create(
    model="gpt-4",
    response_model=User,
    messages=[
        {"role": "user", "content": "Extract: John is 30 years old, email john@example.com"}
    ]
)

print(user.name)  # "John"
print(user.age)   # 30
print(user.email) # "john@example.com"
```

### 2.2 复杂数据结构

```python
from typing import List
from pydantic import BaseModel, Field

class Address(BaseModel):
    street: str
    city: str
    country: str

class Person(BaseModel):
    name: str
    age: int
    addresses: List[Address] = Field(description="所有地址")
    occupation: str | None = None

# 提取
person = client.chat.completions.create(
    model="gpt-4",
    response_model=Person,
    messages=[
        {"role": "user", "content": """
        提取信息：
        张三，35岁，软件工程师。
        住址1：北京市朝阳区xxx街
        住址2：上海市浦东新区yyy路
        """}
    ]
)

print(person.name)  # "张三"
print(len(person.addresses))  # 2
print(person.addresses[0].city)  # "北京市"
```

### 2.3 验证器

```python
from pydantic import BaseModel, field_validator, model_validator

class Product(BaseModel):
    name: str
    price: float
    quantity: int
    
    @field_validator('price')
    @classmethod
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError('价格必须大于0')
        return v
    
    @field_validator('quantity')
    @classmethod
    def validate_quantity(cls, v):
        if v < 0:
            raise ValueError('数量不能为负')
        return v
    
    @model_validator(mode='after')
    def validate_total(self):
        total = self.price * self.quantity
        if total > 10000:
            raise ValueError('总价不能超过10000')
        return self

# 使用
product = client.chat.completions.create(
    model="gpt-4",
    response_model=Product,
    max_retries=3,  # 验证失败时重试3次
    messages=[
        {"role": "user", "content": "提取：iPhone 15, 价格5999元, 数量2台"}
    ]
)
```

### 2.4 枚举类型

```python
from enum import Enum
from pydantic import BaseModel

class Sentiment(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"

class Review(BaseModel):
    text: str
    sentiment: Sentiment
    score: int = Field(ge=1, le=5, description="评分1-5")

# 情感分析
review = client.chat.completions.create(
    model="gpt-4",
    response_model=Review,
    messages=[
        {"role": "user", "content": "分析评论：这个产品非常好用，超出预期！"}
    ]
)

print(review.sentiment)  # Sentiment.POSITIVE
print(review.score)      # 5
```

### 2.5 流式输出

```python
from instructor import Partial

class Story(BaseModel):
    title: str
    content: str
    chapters: List[str]

# 流式生成
story_stream = client.chat.completions.create(
    model="gpt-4",
    response_model=Partial[Story],  # Partial 允许部分结果
    stream=True,
    messages=[
        {"role": "user", "content": "写一个关于AI的科幻故事，包含3个章节"}
    ]
)

for partial_story in story_stream:
    print(f"标题: {partial_story.title}")
    print(f"内容长度: {len(partial_story.content or '')}")
    print(f"章节数: {len(partial_story.chapters or [])}")
    print("---")
```

### 2.6 Iterable 输出

```python
from instructor import Iterable

class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str

# 流式返回多个结果
results = client.chat.completions.create(
    model="gpt-4",
    response_model=Iterable[SearchResult],  # 逐个返回
    stream=True,
    messages=[
        {"role": "user", "content": "搜索关于机器学习的5篇文章"}
    ]
)

for result in results:
    print(f"{result.title}: {result.url}")
```

### 2.7 多模态

```python
from pydantic import BaseModel

class ImageAnalysis(BaseModel):
    description: str
    objects: List[str]
    colors: List[str]
    mood: str

# 图像分析
analysis = client.chat.completions.create(
    model="gpt-4-vision",
    response_model=ImageAnalysis,
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "分析这张图片"},
                {"type": "image_url", "image_url": {"url": image_url}}
            ]
        }
    ]
)

print(analysis.description)
print(analysis.objects)
```

---

## 3. 核心算法

### 3.1 自动重试算法

```python
def retry_with_validation(
    client,
    messages: List[dict],
    response_model: type,
    max_retries: int = 3,
    backoff_factor: float = 2.0
) -> BaseModel:
    """
    带验证的自动重试
    
    算法流程:
    1. 调用 LLM
    2. 解析 JSON
    3. 验证 Pydantic 模型
    4. 如果验证失败，将错误信息添加到对话历史
    5. 重试（指数退避）
    """
    attempt = 0
    conversation = messages.copy()
    
    while attempt < max_retries:
        try:
            # 1. 调用 LLM
            response = client.chat.completions.create(
                model="gpt-4",
                messages=conversation,
                response_format={"type": "json_object"}
            )
            
            # 2. 解析 JSON
            content = response.choices[0].message.content
            data = json.loads(content)
            
            # 3. 验证模型
            result = response_model(**data)
            
            # 成功
            return result
            
        except ValidationError as e:
            attempt += 1
            
            if attempt >= max_retries:
                raise
            
            # 4. 添加错误信息到对话
            error_msg = format_validation_error(e)
            conversation.append({
                "role": "assistant",
                "content": content
            })
            conversation.append({
                "role": "user",
                "content": f"验证失败，错误：{error_msg}。请修正输出。"
            })
            
            # 5. 指数退避
            time.sleep(backoff_factor ** attempt)
    
    raise ValueError("达到最大重试次数")

def format_validation_error(error: ValidationError) -> str:
    """格式化验证错误"""
    errors = []
    for err in error.errors():
        field = ".".join(str(x) for x in err['loc'])
        msg = err['msg']
        errors.append(f"{field}: {msg}")
    
    return "; ".join(errors)

# 时间复杂度: O(r) - r 为重试次数
# 空间复杂度: O(m) - m 为消息历史大小
```

### 3.2 部分模型流式解析

```python
def stream_partial_model(
    stream_iterator,
    model_class: type
) -> Iterator[BaseModel]:
    """
    流式解析部分模型
    
    算法:
    1. 累积 JSON 片段
    2. 尝试解析部分 JSON
    3. 使用 Partial 容忍缺失字段
    4. 逐步返回越来越完整的对象
    """
    accumulated = ""
    
    for chunk in stream_iterator:
        # 1. 累积
        delta = chunk.choices[0].delta.content or ""
        accumulated += delta
        
        # 2. 尝试解析
        try:
            # 处理不完整的 JSON
            cleaned = clean_partial_json(accumulated)
            data = json.loads(cleaned)
            
            # 3. 创建部分模型
            partial = create_partial_model(model_class, data)
            
            # 4. 返回
            yield partial
            
        except json.JSONDecodeError:
            # JSON 尚未完整，继续累积
            continue

def clean_partial_json(text: str) -> str:
    """清理部分 JSON"""
    # 移除末尾不完整的部分
    text = text.strip()
    
    # 如果以 { 开头但没有 }，添加 }
    open_braces = text.count('{')
    close_braces = text.count('}')
    
    if open_braces > close_braces:
        text += '}' * (open_braces - close_braces)
    
    # 移除末尾不完整的键值对
    if text.endswith(','):
        text = text[:-1]
    
    return text

def create_partial_model(
    model_class: type,
    data: dict
) -> BaseModel:
    """创建部分模型（容忍缺失字段）"""
    # 获取字段定义
    fields = model_class.model_fields
    
    # 填充缺失字段为 None
    for field_name, field_info in fields.items():
        if field_name not in data:
            # 使用默认值或 None
            if field_info.default is not None:
                data[field_name] = field_info.default
            else:
                data[field_name] = None
    
    # 创建模型（禁用验证）
    return model_class.model_construct(**data)

# 时间复杂度: O(n) - n 为 chunk 数量
# 空间复杂度: O(s) - s 为累积字符串大小
```

### 3.3 Schema 生成算法

```python
def generate_json_schema(
    model_class: type,
    include_descriptions: bool = True
) -> dict:
    """
    从 Pydantic 模型生成 JSON Schema
    
    用于 OpenAI Function Calling
    """
    schema = {
        "type": "object",
        "properties": {},
        "required": []
    }
    
    for field_name, field_info in model_class.model_fields.items():
        # 字段类型
        field_type = field_info.annotation
        
        # 转换为 JSON Schema 类型
        property_schema = convert_type_to_schema(field_type)
        
        # 描述
        if include_descriptions and field_info.description:
            property_schema["description"] = field_info.description
        
        # 约束
        if field_info.ge is not None:
            property_schema["minimum"] = field_info.ge
        if field_info.le is not None:
            property_schema["maximum"] = field_info.le
        
        schema["properties"][field_name] = property_schema
        
        # 必需字段
        if field_info.is_required():
            schema["required"].append(field_name)
    
    return schema

def convert_type_to_schema(python_type) -> dict:
    """转换 Python 类型到 JSON Schema"""
    origin = get_origin(python_type)
    
    if python_type is str:
        return {"type": "string"}
    elif python_type is int:
        return {"type": "integer"}
    elif python_type is float:
        return {"type": "number"}
    elif python_type is bool:
        return {"type": "boolean"}
    elif origin is list:
        item_type = get_args(python_type)[0]
        return {
            "type": "array",
            "items": convert_type_to_schema(item_type)
        }
    elif origin is dict:
        return {"type": "object"}
    elif isinstance(python_type, type) and issubclass(python_type, BaseModel):
        # 嵌套模型
        return generate_json_schema(python_type)
    else:
        return {"type": "string"}  # 默认

# 时间复杂度: O(f * d) - f 为字段数，d 为嵌套深度
# 空间复杂度: O(f * d)
```

### 3.4 类型强制转换算法

```python
def coerce_value(
    value: Any,
    target_type: type
) -> Any:
    """
    类型强制转换
    
    处理 LLM 输出的常见类型错误
    """
    origin = get_origin(target_type)
    
    # 基础类型
    if target_type is str:
        return str(value)
    
    elif target_type is int:
        if isinstance(value, str):
            # 移除逗号等
            value = value.replace(',', '').strip()
        return int(float(value))  # 先转 float 再转 int
    
    elif target_type is float:
        if isinstance(value, str):
            value = value.replace(',', '').strip()
        return float(value)
    
    elif target_type is bool:
        if isinstance(value, str):
            return value.lower() in ('true', 'yes', '1', 'y')
        return bool(value)
    
    # 列表
    elif origin is list:
        if not isinstance(value, list):
            value = [value]
        
        item_type = get_args(target_type)[0]
        return [coerce_value(item, item_type) for item in value]
    
    # 字典
    elif origin is dict:
        if not isinstance(value, dict):
            raise ValueError(f"Cannot coerce {type(value)} to dict")
        
        key_type, value_type = get_args(target_type)
        return {
            coerce_value(k, key_type): coerce_value(v, value_type)
            for k, v in value.items()
        }
    
    # 枚举
    elif isinstance(target_type, type) and issubclass(target_type, Enum):
        if isinstance(value, target_type):
            return value
        # 尝试从值或名称创建
        try:
            return target_type(value)
        except ValueError:
            return target_type[value.upper()]
    
    # Pydantic 模型
    elif isinstance(target_type, type) and issubclass(target_type, BaseModel):
        if isinstance(value, dict):
            return target_type(**value)
        return value
    
    return value

# 时间复杂度: O(n) - n 为值的大小（递归）
# 空间复杂度: O(n)
```

### 3.5 智能字段匹配算法

```python
def match_fields_fuzzy(
    llm_output: dict,
    model_class: type
) -> dict:
    """
    模糊字段匹配
    
    处理 LLM 输出字段名不匹配的情况
    
    策略:
    1. 精确匹配
    2. 小写匹配
    3. 下划线/驼峰转换
    4. 语义相似度匹配
    """
    model_fields = model_class.model_fields
    matched = {}
    
    for llm_key, llm_value in llm_output.items():
        matched_field = None
        
        # 1. 精确匹配
        if llm_key in model_fields:
            matched_field = llm_key
        
        # 2. 小写匹配
        elif llm_key.lower() in [f.lower() for f in model_fields]:
            for field in model_fields:
                if field.lower() == llm_key.lower():
                    matched_field = field
                    break
        
        # 3. 下划线/驼峰转换
        else:
            # snake_case <-> camelCase
            camel_key = to_camel_case(llm_key)
            snake_key = to_snake_case(llm_key)
            
            for field in model_fields:
                if field == camel_key or field == snake_key:
                    matched_field = field
                    break
        
        # 4. 语义相似度（可选）
        if matched_field is None and USE_SEMANTIC_MATCHING:
            matched_field = find_most_similar_field(
                llm_key,
                list(model_fields.keys())
            )
        
        if matched_field:
            matched[matched_field] = llm_value
        else:
            # 未匹配的字段保留
            matched[llm_key] = llm_value
    
    return matched

def to_camel_case(snake_str: str) -> str:
    """snake_case -> camelCase"""
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])

def to_snake_case(camel_str: str) -> str:
    """camelCase -> snake_case"""
    import re
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', camel_str)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def find_most_similar_field(
    target: str,
    candidates: List[str],
    threshold: float = 0.8
) -> str:
    """找到最相似的字段（编辑距离）"""
    from difflib import SequenceMatcher
    
    best_match = None
    best_score = 0
    
    for candidate in candidates:
        score = SequenceMatcher(None, target.lower(), candidate.lower()).ratio()
        if score > best_score and score >= threshold:
            best_score = score
            best_match = candidate
    
    return best_match

# 时间复杂度: O(n * m) - n 为 LLM 输出字段数，m 为模型字段数
# 空间复杂度: O(n)
```

---

## 4. 设计模式

### 4.1 装饰器模式 (Decorator) - Client Patching

```python
def from_openai(client: OpenAI) -> InstructorClient:
    """
    装饰 OpenAI 客户端
    
    添加 response_model 支持
    """
    original_create = client.chat.completions.create
    
    def patched_create(
        *args,
        response_model: type = None,
        max_retries: int = 1,
        **kwargs
    ):
        if response_model is None:
            # 无 response_model，直接调用原始方法
            return original_create(*args, **kwargs)
        
        # 生成 JSON Schema
        schema = generate_json_schema(response_model)
        
        # 添加 function calling
        kwargs['functions'] = [{
            "name": "extract_data",
            "description": f"Extract data matching {response_model.__name__}",
            "parameters": schema
        }]
        kwargs['function_call'] = {"name": "extract_data"}
        
        # 重试逻辑
        for attempt in range(max_retries):
            try:
                response = original_create(*args, **kwargs)
                
                # 解析 function call
                function_args = response.choices[0].message.function_call.arguments
                data = json.loads(function_args)
                
                # 验证和转换
                result = response_model(**data)
                
                return result
                
            except ValidationError as e:
                if attempt == max_retries - 1:
                    raise
                
                # 添加错误信息重试
                error_msg = format_validation_error(e)
                kwargs['messages'].append({
                    "role": "user",
                    "content": f"Validation error: {error_msg}. Please fix."
                })
    
    # 替换方法
    client.chat.completions.create = patched_create
    
    return client
```

### 4.2 适配器模式 (Adapter) - Multi-Provider

```python
class ProviderAdapter(ABC):
    """提供商适配器"""
    
    @abstractmethod
    def create_completion(
        self,
        messages: List[dict],
        schema: dict,
        **kwargs
    ) -> dict:
        """创建补全"""
        pass

class OpenAIAdapter(ProviderAdapter):
    def __init__(self, client):
        self.client = client
    
    def create_completion(self, messages, schema, **kwargs):
        response = self.client.chat.completions.create(
            messages=messages,
            functions=[{
                "name": "extract",
                "parameters": schema
            }],
            function_call={"name": "extract"},
            **kwargs
        )
        
        return json.loads(
            response.choices[0].message.function_call.arguments
        )

class AnthropicAdapter(ProviderAdapter):
    def __init__(self, client):
        self.client = client
    
    def create_completion(self, messages, schema, **kwargs):
        # Anthropic 使用 XML 提示
        system_prompt = self._schema_to_xml_prompt(schema)
        
        response = self.client.messages.create(
            messages=messages,
            system=system_prompt,
            **kwargs
        )
        
        # 解析 XML 响应
        return self._parse_xml_response(response.content[0].text)
    
    def _schema_to_xml_prompt(self, schema: dict) -> str:
        """转换 Schema 为 XML 提示"""
        parts = ["Please respond in the following XML format:"]
        parts.append("<response>")
        
        for field, props in schema["properties"].items():
            parts.append(f"  <{field}>...</{field}>")
        
        parts.append("</response>")
        return "\n".join(parts)

class UnifiedClient:
    """统一客户端"""
    
    def __init__(self, adapter: ProviderAdapter):
        self.adapter = adapter
    
    def create(
        self,
        messages: List[dict],
        response_model: type,
        **kwargs
    ):
        schema = generate_json_schema(response_model)
        data = self.adapter.create_completion(messages, schema, **kwargs)
        return response_model(**data)
```

### 4.3 构建器模式 (Builder) - Prompt Builder

```python
class PromptBuilder:
    """Prompt 构建器"""
    
    def __init__(self):
        self.messages = []
        self.schema = None
        self.examples = []
    
    def system(self, content: str) -> 'PromptBuilder':
        """添加系统消息"""
        self.messages.append({
            "role": "system",
            "content": content
        })
        return self
    
    def user(self, content: str) -> 'PromptBuilder':
        """添加用户消息"""
        self.messages.append({
            "role": "user",
            "content": content
        })
        return self
    
    def with_schema(self, model: type) -> 'PromptBuilder':
        """添加 Schema"""
        self.schema = generate_json_schema(model)
        return self
    
    def add_example(
        self,
        input: str,
        output: BaseModel
    ) -> 'PromptBuilder':
        """添加示例"""
        self.examples.append({
            "input": input,
            "output": output.model_dump_json()
        })
        return self
    
    def build(self) -> List[dict]:
        """构建最终 Prompt"""
        messages = self.messages.copy()
        
        # 插入 Schema 说明
        if self.schema:
            schema_msg = self._format_schema()
            messages.insert(0, {
                "role": "system",
                "content": schema_msg
            })
        
        # 插入示例
        if self.examples:
            for ex in self.examples:
                messages.append({
                    "role": "user",
                    "content": ex["input"]
                })
                messages.append({
                    "role": "assistant",
                    "content": ex["output"]
                })
        
        return messages
    
    def _format_schema(self) -> str:
        """格式化 Schema 说明"""
        parts = ["Respond with JSON matching this schema:"]
        parts.append(json.dumps(self.schema, indent=2))
        return "\n".join(parts)

# 使用
prompt = (PromptBuilder()
    .system("You are a data extraction assistant")
    .with_schema(Person)
    .add_example(
        "John, 30, lives in NYC",
        Person(name="John", age=30, city="NYC")
    )
    .user("Extract: Alice, 25, lives in LA")
    .build())
```

### 4.4 策略模式 (Strategy) - Validation Strategy

```python
class ValidationStrategy(ABC):
    @abstractmethod
    def validate(self, value: Any, field_info) -> Any:
        pass

class StrictValidation(ValidationStrategy):
    """严格验证"""
    def validate(self, value, field_info):
        # 不做任何转换，严格匹配类型
        if not isinstance(value, field_info.annotation):
            raise ValueError(f"Type mismatch")
        return value

class CoerciveValidation(ValidationStrategy):
    """强制转换验证"""
    def validate(self, value, field_info):
        # 尝试强制转换
        return coerce_value(value, field_info.annotation)

class LenientValidation(ValidationStrategy):
    """宽松验证"""
    def validate(self, value, field_info):
        # 如果转换失败，使用默认值
        try:
            return coerce_value(value, field_info.annotation)
        except:
            return field_info.default

class ConfigurableValidator:
    def __init__(self, strategy: ValidationStrategy):
        self.strategy = strategy
    
    def validate_model(self, data: dict, model_class: type):
        validated = {}
        
        for field_name, field_info in model_class.model_fields.items():
            if field_name in data:
                validated[field_name] = self.strategy.validate(
                    data[field_name],
                    field_info
                )
        
        return model_class(**validated)
```

### 4.5 观察者模式 (Observer) - Validation Observer

```python
class ValidationObserver(ABC):
    @abstractmethod
    def on_validation_start(self, model: type, data: dict):
        pass
    
    @abstractmethod
    def on_validation_success(self, result: BaseModel):
        pass
    
    @abstractmethod
    def on_validation_error(self, error: ValidationError, attempt: int):
        pass

class LoggingObserver(ValidationObserver):
    def on_validation_start(self, model, data):
        logging.info(f"验证 {model.__name__}")
    
    def on_validation_success(self, result):
        logging.info(f"验证成功: {result.__class__.__name__}")
    
    def on_validation_error(self, error, attempt):
        logging.warning(f"验证失败 (尝试 {attempt}): {error}")

class MetricsObserver(ValidationObserver):
    def __init__(self):
        self.attempts = []
        self.successes = 0
        self.failures = 0
    
    def on_validation_start(self, model, data):
        self.attempts.append({"model": model.__name__, "success": None})
    
    def on_validation_success(self, result):
        self.successes += 1
        self.attempts[-1]["success"] = True
    
    def on_validation_error(self, error, attempt):
        if attempt == 1:
            self.failures += 1
        self.attempts[-1]["success"] = False

class ObservableClient:
    def __init__(self, client):
        self.client = client
        self.observers: List[ValidationObserver] = []
    
    def add_observer(self, observer: ValidationObserver):
        self.observers.append(observer)
    
    def create(self, response_model, **kwargs):
        # 通知开始
        for obs in self.observers:
            obs.on_validation_start(response_model, kwargs)
        
        try:
            result = self.client.create(
                response_model=response_model,
                **kwargs
            )
            
            # 通知成功
            for obs in self.observers:
                obs.on_validation_success(result)
            
            return result
            
        except ValidationError as e:
            # 通知错误
            for obs in self.observers:
                obs.on_validation_error(e, 1)
            raise
```

---

## 5. 可复用组件

### 5.1 核心组件清单

| 组件 | 功能 | 复用优先级 |
|------|------|-----------|
| Response Model | Pydantic 模型验证 | ⭐⭐⭐⭐⭐ |
| Auto Retry | 验证失败自动重试 | ⭐⭐⭐⭐⭐ |
| Schema Generation | JSON Schema 生成 | ⭐⭐⭐⭐⭐ |
| Partial Streaming | 部分结果流式返回 | ⭐⭐⭐⭐⭐ |
| Type Coercion | 类型强制转换 | ⭐⭐⭐⭐ |
| Field Matching | 模糊字段匹配 | ⭐⭐⭐⭐ |
| Validation Observer | 验证观察者 | ⭐⭐⭐⭐ |
| Multi-Provider Adapter | 多提供商适配器 | ⭐⭐⭐⭐ |
| Prompt Builder | Prompt 构建器 | ⭐⭐⭐ |
| Enum Support | 枚举类型支持 | ⭐⭐⭐⭐⭐ |

---

## 6. 集成到 FieldMind

### 6.1 结构化输出系统

```python
# fieldmind/structured/core.py

from pydantic import BaseModel, ValidationError
from typing import Type, TypeVar, List
import json

T = TypeVar('T', bound=BaseModel)

class FMStructuredClient:
    """FieldMind 结构化输出客户端"""
    
    def __init__(self, llm_service):
        self.llm = llm_service
        self.observers = []
    
    async def create_async(
        self,
        messages: List[dict],
        response_model: Type[T],
        max_retries: int = 3,
        **kwargs
    ) -> T:
        """创建结构化输出"""
        
        # 生成 Schema
        schema = self._generate_schema(response_model)
        
        # 添加 Schema 到消息
        enhanced_messages = self._add_schema_to_messages(
            messages,
            schema,
            response_model
        )
        
        # 重试循环
        for attempt in range(max_retries):
            try:
                # 通知观察者
                for obs in self.observers:
                    obs.on_validation_start(response_model, messages)
                
                # 调用 LLM
                response = await self.llm.complete_async(
                    messages=enhanced_messages,
                    response_format="json",
                    **kwargs
                )
                
                # 解析 JSON
                data = json.loads(response)
                
                # 模糊字段匹配
                data = self._match_fields(data, response_model)
                
                # 类型强制转换
                data = self._coerce_types(data, response_model)
                
                # 验证
                result = response_model(**data)
                
                # 通知成功
                for obs in self.observers:
                    obs.on_validation_success(result)
                
                return result
                
            except ValidationError as e:
                # 通知错误
                for obs in self.observers:
                    obs.on_validation_error(e, attempt + 1)
                
                if attempt == max_retries - 1:
                    raise
                
                # 添加错误信息
                error_msg = self._format_error(e)
                enhanced_messages.append({
                    "role": "assistant",
                    "content": response
                })
                enhanced_messages.append({
                    "role": "user",
                    "content": f"验证失败。错误: {error_msg}。请修正输出，确保符合 Schema。"
                })
        
        raise ValueError("达到最大重试次数")
    
    def _generate_schema(self, model: Type[BaseModel]) -> dict:
        """生成 JSON Schema"""
        schema = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        for field_name, field_info in model.model_fields.items():
            property_schema = self._field_to_schema(field_info)
            
            if field_info.description:
                property_schema["description"] = field_info.description
            
            schema["properties"][field_name] = property_schema
            
            if field_info.is_required():
                schema["required"].append(field_name)
        
        return schema
    
    def _add_schema_to_messages(
        self,
        messages: List[dict],
        schema: dict,
        model: Type[BaseModel]
    ) -> List[dict]:
        """添加 Schema 到消息"""
        schema_message = {
            "role": "system",
            "content": f"""
请以 JSON 格式返回，必须符合以下 Schema:

{json.dumps(schema, ensure_ascii=False, indent=2)}

模型说明: {model.__doc__ or model.__name__}

要求:
1. 只返回 JSON，不要有其他文本
2. 确保所有必需字段都存在
3. 字段类型必须正确
4. 遵守字段约束（如最小值、最大值等）
"""
        }
        
        return [schema_message] + messages
    
    def _match_fields(
        self,
        data: dict,
        model: Type[BaseModel]
    ) -> dict:
        """模糊字段匹配"""
        matched = {}
        model_fields = model.model_fields
        
        for key, value in data.items():
            # 精确匹配
            if key in model_fields:
                matched[key] = value
                continue
            
            # 小写匹配
            key_lower = key.lower()
            for field in model_fields:
                if field.lower() == key_lower:
                    matched[field] = value
                    break
        
        return matched
    
    def _coerce_types(
        self,
        data: dict,
        model: Type[BaseModel]
    ) -> dict:
        """类型强制转换"""
        coerced = {}
        
        for field_name, field_info in model.model_fields.items():
            if field_name not in data:
                continue
            
            value = data[field_name]
            target_type = field_info.annotation
            
            try:
                coerced[field_name] = self._coerce_value(value, target_type)
            except Exception as e:
                logging.warning(f"无法转换字段 {field_name}: {e}")
                coerced[field_name] = value
        
        return coerced
    
    def _coerce_value(self, value: Any, target_type: type) -> Any:
        """转换单个值"""
        # 实现类型强制转换逻辑
        # （参考前面的 coerce_value 算法）
        pass
    
    def _format_error(self, error: ValidationError) -> str:
        """格式化错误"""
        errors = []
        for err in error.errors():
            field = ".".join(str(x) for x in err['loc'])
            msg = err['msg']
            errors.append(f"- {field}: {msg}")
        
        return "\n".join(errors)
```

### 6.2 使用示例

```python
# 示例：信息抽取

from pydantic import BaseModel, Field
from typing import List
from enum import Enum

class PersonType(str, Enum):
    CUSTOMER = "customer"
    EMPLOYEE = "employee"
    SUPPLIER = "supplier"

class Contact(BaseModel):
    """联系方式"""
    phone: str | None = Field(None, description="电话号码")
    email: str | None = Field(None, description="邮箱地址")
    address: str | None = Field(None, description="地址")

class Person(BaseModel):
    """人物信息"""
    name: str = Field(description="姓名")
    age: int | None = Field(None, ge=0, le=150, description="年龄")
    type: PersonType = Field(description="人物类型")
    contact: Contact = Field(description="联系方式")
    notes: List[str] = Field(default_factory=list, description="备注")

# 使用
client = FMStructuredClient(llm_service)

person = await client.create_async(
    messages=[
        {"role": "user", "content": """
        提取信息：
        张三，35岁，是我们的客户。
        电话：13812345678
        邮箱：zhangsan@example.com
        住址：北京市朝阳区xxx街
        备注：VIP客户，需要特别关注
        """}
    ],
    response_model=Person,
    max_retries=3
)

print(f"姓名: {person.name}")
print(f"年龄: {person.age}")
print(f"类型: {person.type}")
print(f"电话: {person.contact.phone}")
print(f"备注: {', '.join(person.notes)}")
```

---

## 7. 核心学习

### 关键概念
1. **类型安全** - Pydantic 模型保证输出类型
2. **自动重试** - 验证失败时自动修正
3. **Schema 驱动** - JSON Schema 指导 LLM 输出
4. **流式支持** - 部分结果渐进返回
5. **零样板** - 最小化模板代码

### 核心算法
1. 自动重试与错误反馈
2. 部分模型流式解析
3. JSON Schema 生成
4. 类型强制转换
5. 模糊字段匹配

### 对 FieldMind 的价值
- ⭐⭐⭐⭐⭐ 结构化输出系统
- ⭐⭐⭐⭐⭐ 自动验证和重试
- ⭐⭐⭐⭐⭐ 类型安全保证
- ⭐⭐⭐⭐ 流式部分结果
- ⭐⭐⭐⭐ 多提供商适配

---

**分析完成时间**: 2026-08-29  
**已完成插件数**: 12/40 (30%)  
**下一阶段**: 已完成 AI Agent 框架类别，准备进入 RAG 增强类别
