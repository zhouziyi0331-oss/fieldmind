# Guidance 深度分析报告

**插件名称**: Guidance  
**开发者**: Microsoft  
**GitHub**: https://github.com/guidance-ai/guidance  
**Stars**: 18k+  
**类别**: 结构化生成控制  
**语言**: Python  
**分析日期**: 2026-08-30

---

## 1. 插件概述

### 核心定位
Guidance 是 Microsoft 开发的一个框架，用于控制和约束 LLM 的生成过程。与 Guardrails 的事后验证不同，Guidance 在生成时就进行约束，确保输出符合预期格式。

### 核心特点
- **模板语法**: Handlebars风格的模板
- **生成时约束**: 在生成过程中强制格式
- **分支控制**: 条件判断和循环
- **角色对话**: 结构化对话管理
- **Token healing**: 修复token边界问题
- **正则约束**: 用正则表达式约束生成

### 架构设计
```
Guidance
├── Template Engine (模板引擎)
│   ├── Handlebars Syntax
│   ├── Variable Binding
│   ├── Control Flow
│   └── Function Calls
├── Generation Control (生成控制)
│   ├── Grammar Constraints
│   ├── Regex Patterns
│   ├── Token Healing
│   └── Selective Generation
├── Role Management (角色管理)
│   ├── System/User/Assistant
│   ├── Context Window
│   └── Chat Templates
└── Integration
    ├── OpenAI API
    ├── Transformers
    ├── LlamaCpp
    └── Custom Models
```

---

## 2. 核心概念

### 2.1 基础模板语法

```python
import guidance

# 设置 LLM
guidance.llm = guidance.llms.OpenAI("gpt-3.5-turbo")

# 基础模板
program = guidance('''
The best thing about {{topic}} is {{gen 'best' max_tokens=50}}
''')

# 执行
result = program(topic="programming")
print(result["best"])
```

### 2.2 结构化生成

```python
# JSON 生成约束
program = guidance('''
{{#system~}}
你是一个数据提取助手。
{{~/system}}

{{#user~}}
从以下文本提取信息：
{{text}}
{{~/user}}

{{#assistant~}}
{{gen 'response' temperature=0}}
{{~/assistant}}

提取的 JSON:
```json
{
    "name": "{{gen 'name' pattern='[A-Za-z ]+' stop='"'}}",
    "age": {{gen 'age' pattern='[0-9]+' stop=','}},
    "email": "{{gen 'email' pattern='[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}' stop='"'}}"
}
```
''')

result = program(text="John Doe is 30 years old, email: john@example.com")
```

### 2.3 选择和分支

```python
# 单选
program = guidance('''
问题：这是一个积极的评论吗？"{{review}}"

答案：{{#select 'sentiment'}}positive{{or}}negative{{/select}}
''')

result = program(review="This product is amazing!")
print(result["sentiment"])  # "positive" 或 "negative"

# 多选
program = guidance('''
从以下选项中选择所有适用的：

{{#select 'categories' multiple=True}}
- Technology
- Science  
- Politics
- Sports
{{/select}}
''')

# 条件分支
program = guidance('''
{{#if user_type == "premium"}}
欢迎，尊贵的用户！您有无限访问权限。
{{else}}
您是免费用户，每天有 10 次查询限制。
{{/if}}
''')
```

### 2.4 循环生成

```python
# 生成列表
program = guidance('''
生成 {{num}} 个编程语言：

{{#geneach 'languages' num_iterations=num}}
{{@index}}. {{gen 'this' max_tokens=10}}
{{/geneach}}
''')

result = program(num=5)
print(result["languages"])  # ["Python", "JavaScript", ...]

# 动态循环
program = guidance('''
生成关键词列表，直到说 "DONE":

关键词：
{{#geneach 'keywords' stop='DONE'}}
- {{gen 'this' max_tokens=20}}
{{/geneach}}
''')
```

### 2.5 角色对话管理

```python
# 结构化对话
program = guidance('''
{{#system~}}
你是一个有帮助的助手。
{{~/system}}

{{#user~}}
{{user_message}}
{{~/user}}

{{#assistant~}}
{{gen 'response' max_tokens=200}}
{{~/assistant}}

{{#user~}}
请总结你的回答。
{{~/user}}

{{#assistant~}}
{{gen 'summary' max_tokens=50}}
{{~/assistant}}
''')

result = program(user_message="解释什么是机器学习")
```

### 2.6 Token Healing

```python
# Token Healing 修复边界问题
program = guidance('''
The answer is{{gen 'answer' max_tokens=10}}
''')

# 不使用 token healing:
# 可能生成: "The answer is an apple"
# Tokenized as: ["The", " answer", " is", "an", " apple"]
# 但 "is" 后面缺少空格

# 使用 token healing:
# 自动修复: "The answer is an apple"
# 正确的 tokenization

# 默认开启
result = program()
```

### 2.7 正则约束

```python
# 使用正则表达式约束生成
program = guidance('''
生成一个符合以下格式的日期：

日期: {{gen 'date' pattern='[0-9]{4}-[0-9]{2}-[0-9]{2}' max_tokens=10}}

时间: {{gen 'time' pattern='[0-9]{2}:[0-9]{2}:[0-9]{2}' max_tokens=8}}

邮箱: {{gen 'email' pattern='[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}' max_tokens=50}}
''')

result = program()
# 保证输出符合格式
```

---

## 3. 核心算法

### 3.1 Constrained Generation 算法

```python
def constrained_generation(
    prompt: str,
    pattern: str,
    model,
    tokenizer,
    max_tokens: int = 50
) -> str:
    """
    约束生成算法
    
    使用正则表达式约束 token 选择
    
    流程:
    1. 生成下一个 token
    2. 检查是否匹配正则
    3. 只保留匹配的 token
    4. 重复直到完成
    """
    import re
    
    current_text = prompt
    regex = re.compile(pattern)
    
    for _ in range(max_tokens):
        # 1. 获取所有可能的下一个 token
        inputs = tokenizer(current_text, return_tensors="pt")
        outputs = model(**inputs)
        logits = outputs.logits[0, -1, :]  # 最后一个位置的 logits
        
        # 2. 获取 top-k token
        top_k = 100
        top_tokens = torch.topk(logits, top_k).indices
        
        # 3. 过滤：只保留匹配正则的
        valid_tokens = []
        
        for token_id in top_tokens:
            # 解码 token
            token_text = tokenizer.decode([token_id])
            
            # 测试是否匹配
            test_text = current_text + token_text
            
            # 部分匹配或完全匹配
            if regex.match(test_text) or is_partial_match(regex, test_text):
                valid_tokens.append((token_id, logits[token_id].item()))
        
        # 4. 如果没有有效 token，结束
        if not valid_tokens:
            break
        
        # 5. 选择概率最高的有效 token
        best_token = max(valid_tokens, key=lambda x: x[1])[0]
        
        # 6. 添加到序列
        token_text = tokenizer.decode([best_token])
        current_text += token_text
        
        # 7. 检查是否完全匹配（生成结束）
        if regex.fullmatch(current_text.replace(prompt, "")):
            break
    
    return current_text.replace(prompt, "")

def is_partial_match(regex: re.Pattern, text: str) -> bool:
    """
    检查是否为正则的部分匹配
    
    即：text 是某个完全匹配的前缀
    """
    # 简化实现：检查是否匹配开头
    return regex.match(text) is not None

# 时间复杂度: O(n * k) - n为生成长度，k为候选token数
# 空间复杂度: O(k)
```

### 3.2 Token Healing 算法

```python
def token_healing(
    prompt: str,
    generated: str,
    tokenizer
) -> str:
    """
    Token Healing 算法
    
    修复 token 边界问题
    
    问题:
    prompt = "The answer is"
    如果直接生成，可能得到 ["an", " apple"]
    但理想的 tokenization 应该是 [" an", " apple"]
    
    解决:
    回退几个 token，重新生成
    """
    # 1. 组合 prompt 和 generated
    full_text = prompt + generated
    
    # 2. Tokenize 整个文本
    ideal_tokens = tokenizer.encode(full_text)
    
    # 3. Tokenize prompt
    prompt_tokens = tokenizer.encode(prompt)
    
    # 4. 比较
    # 如果 prompt 的最后几个 token 在完整 tokenization 中不同
    # 说明有边界问题
    
    # 查找分歧点
    divergence_point = find_token_divergence(
        prompt_tokens,
        ideal_tokens[:len(prompt_tokens)]
    )
    
    if divergence_point is not None:
        # 5. 回退到分歧点
        healed_prompt_tokens = ideal_tokens[:divergence_point]
        healed_prompt = tokenizer.decode(healed_prompt_tokens)
        
        # 6. 从分歧点重新生成
        healed_generated_tokens = ideal_tokens[divergence_point:]
        healed_generated = tokenizer.decode(healed_generated_tokens)
        
        return healed_prompt, healed_generated
    
    return prompt, generated

def find_token_divergence(tokens1: List[int], tokens2: List[int]) -> Optional[int]:
    """找到两个 token 序列的分歧点"""
    for i, (t1, t2) in enumerate(zip(tokens1, tokens2)):
        if t1 != t2:
            return i
    return None

# 示例:
# prompt = "The color is"
# 不使用 healing: "The color is" + "red" → tokenized as ["The", " color", " is", "red"]
# 使用 healing: 回退到 "The color" + " is red" → ["The", " color", " is", " red"]

# 时间复杂度: O(n) - n为token数
```

### 3.3 Grammar-based Generation 算法

```python
class Grammar:
    """语法规则"""
    def __init__(self, rules: Dict[str, List[str]]):
        self.rules = rules
    
    def is_valid_next_token(
        self,
        current_state: str,
        token: str
    ) -> bool:
        """检查 token 是否符合语法"""
        if current_state not in self.rules:
            return False
        
        return token in self.rules[current_state]
    
    def get_valid_tokens(self, current_state: str) -> List[str]:
        """获取当前状态的有效 token"""
        return self.rules.get(current_state, [])

def grammar_constrained_generation(
    prompt: str,
    grammar: Grammar,
    model,
    tokenizer,
    max_tokens: int = 50
) -> str:
    """
    基于语法的约束生成
    
    使用形式语法约束生成
    """
    current_text = prompt
    current_state = "START"
    
    for _ in range(max_tokens):
        # 1. 获取语法允许的 token
        valid_token_texts = grammar.get_valid_tokens(current_state)
        
        if not valid_token_texts:
            break
        
        # 2. 将文本转为 token IDs
        valid_token_ids = [
            tokenizer.encode(t, add_special_tokens=False)[0]
            for t in valid_token_texts
        ]
        
        # 3. 获取模型预测
        inputs = tokenizer(current_text, return_tensors="pt")
        outputs = model(**inputs)
        logits = outputs.logits[0, -1, :]
        
        # 4. 只考虑有效 token 的概率
        valid_logits = [(tid, logits[tid].item()) for tid in valid_token_ids]
        
        # 5. 选择最高概率的有效 token
        best_token_id = max(valid_logits, key=lambda x: x[1])[0]
        token_text = tokenizer.decode([best_token_id])
        
        # 6. 更新状态
        current_text += token_text
        current_state = grammar.next_state(current_state, token_text)
    
    return current_text.replace(prompt, "")

# JSON 语法示例
json_grammar = Grammar({
    "START": ["{"],
    "{": ['"'],
    '"': ["key_name"],
    "key_name": ['"'],
    '":': ["value"],
    "value": ['"', "number", "{", "["],
    ",": ['"'],
    "}": ["END"]
})

# 时间复杂度: O(n * v) - n为生成长度，v为有效token数
```

### 3.4 Selective Generation 算法

```python
def selective_generation(
    prompt: str,
    choices: List[str],
    model,
    tokenizer
) -> str:
    """
    选择性生成（从给定选项中选择）
    
    {{#select 'answer'}}yes{{or}}no{{/select}}
    
    算法:
    1. 计算每个选项的概率
    2. 选择概率最高的
    """
    # 1. 编码 prompt
    inputs = tokenizer(prompt, return_tensors="pt")
    
    # 2. 计算每个选项的概率
    choice_scores = []
    
    for choice in choices:
        # 编码选项
        choice_tokens = tokenizer.encode(choice, add_special_tokens=False)
        
        # 计算联合概率
        total_logprob = 0.0
        current_input = inputs.copy()
        
        for token_id in choice_tokens:
            # 预测
            outputs = model(**current_input)
            logits = outputs.logits[0, -1, :]
            
            # 获取这个 token 的 log 概率
            logprobs = torch.log_softmax(logits, dim=-1)
            token_logprob = logprobs[token_id].item()
            
            total_logprob += token_logprob
            
            # 添加 token 到输入
            current_input = add_token_to_input(current_input, token_id)
        
        choice_scores.append((choice, total_logprob))
    
    # 3. 选择得分最高的
    best_choice = max(choice_scores, key=lambda x: x[1])[0]
    
    return best_choice

# 时间复杂度: O(c * l) - c为选项数，l为选项平均长度
```

### 3.5 Context Window 管理算法

```python
def manage_context_window(
    messages: List[Dict[str, str]],
    max_tokens: int = 4096,
    tokenizer
) -> List[Dict[str, str]]:
    """
    上下文窗口管理
    
    当对话超过上下文限制时，智能截断
    
    策略:
    1. 保留系统消息（最重要）
    2. 保留最近的消息
    3. 中间消息用摘要替代
    """
    # 1. 计算每条消息的 token 数
    message_tokens = []
    total_tokens = 0
    
    for msg in messages:
        tokens = len(tokenizer.encode(msg['content']))
        message_tokens.append(tokens)
        total_tokens += tokens
    
    # 2. 如果没超过限制，直接返回
    if total_tokens <= max_tokens:
        return messages
    
    # 3. 需要截断
    # 策略：保留 system + 最近的 + 摘要中间
    
    result = []
    
    # 保留 system 消息
    system_msgs = [m for m in messages if m['role'] == 'system']
    result.extend(system_msgs)
    
    # 从后往前保留最近的消息
    recent_budget = max_tokens - sum(
        len(tokenizer.encode(m['content'])) for m in system_msgs
    )
    recent_budget = int(recent_budget * 0.7)  # 70% 给最近消息
    
    recent_messages = []
    current_tokens = 0
    
    for msg in reversed(messages):
        if msg['role'] == 'system':
            continue
        
        msg_tokens = len(tokenizer.encode(msg['content']))
        
        if current_tokens + msg_tokens <= recent_budget:
            recent_messages.insert(0, msg)
            current_tokens += msg_tokens
        else:
            break
    
    # 中间消息生成摘要
    middle_messages = [
        m for m in messages
        if m not in system_msgs and m not in recent_messages
    ]
    
    if middle_messages:
        summary = summarize_messages(middle_messages)
        result.append({
            'role': 'system',
            'content': f"[前文摘要] {summary}"
        })
    
    # 添加最近消息
    result.extend(recent_messages)
    
    return result

def summarize_messages(messages: List[Dict]) -> str:
    """生成消息摘要"""
    # 使用 LLM 生成摘要
    combined = "\n".join([
        f"{m['role']}: {m['content']}"
        for m in messages
    ])
    
    summary_prompt = f"总结以下对话（50词以内）：\n{combined}"
    summary = llm.complete(summary_prompt, max_tokens=100)
    
    return summary

# 时间复杂度: O(n) - n为消息数
```

---

## 4. 设计模式

### 4.1 建造者模式 (Builder) - 程序构建

```python
class GuidanceBuilder:
    """Guidance 程序构建器"""
    
    def __init__(self):
        self.template_parts = []
        self.variables = {}
    
    def system(self, content: str) -> 'GuidanceBuilder':
        """添加系统消息"""
        self.template_parts.append(f"{{{{#system~}}}}\n{content}\n{{{{~/system}}}}")
        return self
    
    def user(self, content: str, var_name: str = None) -> 'GuidanceBuilder':
        """添加用户消息"""
        if var_name:
            content = f"{{{{{var_name}}}}}"
        self.template_parts.append(f"{{{{#user~}}}}\n{content}\n{{{{~/user}}}}")
        return self
    
    def assistant(self, gen_name: str, **kwargs) -> 'GuidanceBuilder':
        """添加助手生成"""
        gen_params = " ".join([f"{k}={v}" for k, v in kwargs.items()])
        self.template_parts.append(
            f"{{{{#assistant~}}}}\n{{{{gen '{gen_name}' {gen_params}}}}}\n{{{{~/assistant}}}}"
        )
        return self
    
    def select(self, var_name: str, choices: List[str]) -> 'GuidanceBuilder':
        """添加选择"""
        choice_text = "{{or}}".join(choices)
        self.template_parts.append(
            f"{{{{#select '{var_name}'}}}}{choice_text}{{{{/select}}}}"
        )
        return self
    
    def build(self) -> guidance.Program:
        """构建 Guidance 程序"""
        template = "\n\n".join(self.template_parts)
        return guidance(template)

# 使用
program = (GuidanceBuilder()
    .system("你是一个有帮助的助手")
    .user("{{question}}")
    .assistant("answer", max_tokens=100)
    .user("请用一句话总结")
    .assistant("summary", max_tokens=50)
    .build())
```

### 4.2 装饰器模式 (Decorator) - 生成包装

```python
class GenerationDecorator:
    """生成装饰器"""
    def __init__(self, program):
        self.program = program
    
    def __call__(self, **kwargs):
        return self.program(**kwargs)

class LoggedGeneration(GenerationDecorator):
    """带日志的生成"""
    def __call__(self, **kwargs):
        logging.info(f"开始生成，参数: {kwargs}")
        result = self.program(**kwargs)
        logging.info(f"生成完成，变量: {list(result.keys())}")
        return result

class CachedGeneration(GenerationDecorator):
    """带缓存的生成"""
    def __init__(self, program):
        super().__init__(program)
        self.cache = {}
    
    def __call__(self, **kwargs):
        cache_key = hash(frozenset(kwargs.items()))
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        result = self.program(**kwargs)
        self.cache[cache_key] = result
        
        return result

class ValidatedGeneration(GenerationDecorator):
    """带验证的生成"""
    def __init__(self, program, validators: Dict[str, Callable]):
        super().__init__(program)
        self.validators = validators
    
    def __call__(self, **kwargs):
        result = self.program(**kwargs)
        
        # 验证每个生成的变量
        for var_name, validator in self.validators.items():
            if var_name in result:
                if not validator(result[var_name]):
                    raise ValidationError(f"{var_name} 验证失败")
        
        return result

# 使用
program = guidance('''...''')
program = LoggedGeneration(program)
program = CachedGeneration(program)
program = ValidatedGeneration(program, {
    "email": lambda x: "@" in x,
    "age": lambda x: 0 <= int(x) <= 150
})
```

### 4.3 策略模式 (Strategy) - 生成策略

```python
from abc import ABC, abstractmethod

class GenerationStrategy(ABC):
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        pass

class GreedyStrategy(GenerationStrategy):
    """贪心生成"""
    def generate(self, prompt, **kwargs):
        return guidance(f'{prompt}{{{{gen "output" temperature=0}}}}')()["output"]

class SamplingStrategy(GenerationStrategy):
    """采样生成"""
    def __init__(self, temperature: float = 0.7):
        self.temperature = temperature
    
    def generate(self, prompt, **kwargs):
        return guidance(
            f'{prompt}{{{{gen "output" temperature={self.temperature}}}}}'
        )()["output"]

class ConstrainedStrategy(GenerationStrategy):
    """约束生成"""
    def __init__(self, pattern: str):
        self.pattern = pattern
    
    def generate(self, prompt, **kwargs):
        return guidance(
            f'{prompt}{{{{gen "output" pattern="{self.pattern}"}}}}'
        )()["output"]

# 使用
class ConfigurableGenerator:
    def __init__(self, strategy: GenerationStrategy):
        self.strategy = strategy
    
    def generate(self, prompt: str) -> str:
        return self.strategy.generate(prompt)

# 切换策略
generator = ConfigurableGenerator(GreedyStrategy())
result = generator.generate("The answer is")

generator = ConfigurableGenerator(SamplingStrategy(temperature=0.9))
result = generator.generate("Tell me a story")
```

### 4.4 模板方法模式 (Template Method) - 对话流程

```python
class ConversationTemplate(ABC):
    """对话模板基类"""
    
    def execute(self, **params):
        """模板方法"""
        # 1. 初始化
        self.setup(**params)
        
        # 2. 系统提示
        system_prompt = self.get_system_prompt()
        
        # 3. 用户输入
        user_input = self.get_user_input(**params)
        
        # 4. 助手响应
        assistant_response = self.generate_response(system_prompt, user_input)
        
        # 5. 后处理
        result = self.postprocess(assistant_response)
        
        return result
    
    def setup(self, **params):
        """初始化（可选覆盖）"""
        pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """获取系统提示（必须实现）"""
        pass
    
    @abstractmethod
    def get_user_input(self, **params) -> str:
        """获取用户输入（必须实现）"""
        pass
    
    def generate_response(self, system: str, user: str) -> str:
        """生成响应（默认实现）"""
        program = guidance(f'''
{{{{#system~}}}}
{system}
{{{{~/system}}}}

{{{{#user~}}}}
{user}
{{{{~/user}}}}

{{{{#assistant~}}}}
{{{{gen 'response' max_tokens=200}}}}
{{{{~/assistant}}}}
''')
        return program()['response']
    
    def postprocess(self, response: str) -> str:
        """后处理（可选覆盖）"""
        return response

# 具体实现
class SummarizationConversation(ConversationTemplate):
    def get_system_prompt(self):
        return "你是一个文本摘要助手"
    
    def get_user_input(self, **params):
        return f"请总结以下文本：\n{params['text']}"
    
    def postprocess(self, response):
        # 移除多余空格
        return response.strip()

# 使用
conv = SummarizationConversation()
summary = conv.execute(text="很长的文本...")
```

### 4.5 观察者模式 (Observer) - 生成监控

```python
class GenerationObserver(ABC):
    @abstractmethod
    def on_token_generated(self, token: str, context: Dict):
        pass
    
    @abstractmethod
    def on_generation_complete(self, output: str, context: Dict):
        pass

class LoggingObserver(GenerationObserver):
    def on_token_generated(self, token, context):
        logging.debug(f"Token: {token}")
    
    def on_generation_complete(self, output, context):
        logging.info(f"完成生成，长度: {len(output)}")

class MetricsObserver(GenerationObserver):
    def __init__(self):
        self.token_count = 0
        self.generation_count = 0
    
    def on_token_generated(self, token, context):
        self.token_count += 1
    
    def on_generation_complete(self, output, context):
        self.generation_count += 1

class ObservableGuidance:
    def __init__(self, program):
        self.program = program
        self.observers = []
    
    def add_observer(self, observer: GenerationObserver):
        self.observers.append(observer)
    
    def __call__(self, **kwargs):
        # 执行生成
        result = self.program(**kwargs)
        
        # 通知观察者
        for observer in self.observers:
            observer.on_generation_complete(str(result), kwargs)
        
        return result
```

---

## 5. 可复用组件清单

| 组件 | 功能 | 复用优先级 |
|------|------|-----------|
| Constrained Generation | 正则约束生成 | ⭐⭐⭐⭐⭐ |
| Token Healing | Token边界修复 | ⭐⭐⭐⭐⭐ |
| Grammar-based Gen | 语法约束生成 | ⭐⭐⭐⭐ |
| Selective Generation | 选择性生成 | ⭐⭐⭐⭐⭐ |
| Context Window Mgmt | 上下文管理 | ⭐⭐⭐⭐⭐ |
| Role Management | 角色对话管理 | ⭐⭐⭐⭐⭐ |
| Template Builder | 模板构建器 | ⭐⭐⭐⭐ |
| Generation Decorators | 生成装饰器 | ⭐⭐⭐⭐ |
| Conversation Templates | 对话模板 | ⭐⭐⭐⭐ |
| Generation Observers | 生成监控 | ⭐⭐⭐⭐ |

---

## 6. 核心学习

### 关键概念
1. **生成时约束** - 在生成过程中强制格式
2. **Token Healing** - 修复token边界问题
3. **正则约束** - 用正则表达式控制输出
4. **语法约束** - 用形式语法控制生成
5. **角色管理** - 结构化对话控制

### 核心算法
1. Constrained Generation（约束生成）
2. Token Healing（边界修复）
3. Grammar-based Generation（语法生成）
4. Selective Generation（选择生成）
5. Context Window Management（窗口管理）

### 对 FieldMind 的价值
- ⭐⭐⭐⭐⭐ 约束生成技术
- ⭐⭐⭐⭐⭐ Token Healing
- ⭐⭐⭐⭐⭐ 角色对话管理
- ⭐⭐⭐⭐ 语法约束生成
- ⭐⭐⭐⭐⭐ 上下文窗口管理

---

**分析完成时间**: 2026-08-30  
**已完成插件数**: 27/40 (67.5%)  
**下一个插件**: LangSmith (Observability)
