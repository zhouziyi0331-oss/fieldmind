# DSPy 深度分析报告

**插件名称**: DSPy (Declarative Self-improving Language Programs)  
**开发者**: Stanford NLP (Omar Khattab)  
**GitHub**: https://github.com/stanfordnlp/dspy  
**Stars**: 17.2k+  
**类别**: 声明式编程框架 + 自优化系统  
**语言**: Python  
**分析日期**: 2026-08-29

---

## 1. 插件概述

### 核心定位
DSPy 是一个声明式框架，用于编写和优化 LLM 程序。它将 Prompt 工程转变为编程问题，通过自动优化替代手工调试 Prompt。核心思想：分离程序逻辑和 Prompt 优化。

### 核心特点
- **声明式编程**: 定义"做什么"而非"怎么做"
- **自动优化**: 自动优化 Prompt 和权重
- **模块化**: Signature + Module 架构
- **编译器**: 将高级程序编译为优化的 Prompt
- **Teleprompter**: 自动 Prompt 优化器
- **评估驱动**: 基于 Metric 的自动改进

### 架构设计
```
DSPy
├── Signature (签名)
│   ├── Input Fields
│   ├── Output Fields
│   └── Instructions
├── Module (模块)
│   ├── Predict (预测)
│   ├── ChainOfThought (思维链)
│   ├── ReAct (推理-行动)
│   └── Custom Modules
├── Optimizer (优化器/Teleprompter)
│   ├── BootstrapFewShot
│   ├── MIPRO
│   ├── SignatureOptimizer
│   └── Ensemble
├── Compiler (编译器)
│   ├── Program → Prompts
│   ├── Example Selection
│   └── Instruction Generation
└── Metrics (评估)
    ├── Exact Match
    ├── F1 Score
    └── Custom Metrics
```

---

## 2. 核心概念

### 2.1 Signature (签名)

**核心思想**: 声明式定义输入输出，而非手工编写 Prompt

```python
import dspy

# 方式 1: 字符串签名
signature = "question -> answer"

# 方式 2: 详细签名
signature = dspy.Signature(
    "question -> answer",
    question="用户的问题",
    answer="简洁准确的答案"
)

# 方式 3: 类签名（最推荐）
class QA(dspy.Signature):
    """回答用户问题"""
    
    question: str = dspy.InputField(desc="用户的问题")
    answer: str = dspy.OutputField(desc="简洁准确的答案")

class MultiHopQA(dspy.Signature):
    """多跳推理问答"""
    
    context: str = dspy.InputField(desc="相关上下文")
    question: str = dspy.InputField(desc="需要多步推理的问题")
    reasoning: str = dspy.OutputField(desc="推理过程")
    answer: str = dspy.OutputField(desc="最终答案")

# 使用
predictor = dspy.Predict(QA)
result = predictor(question="什么是 DSPy？")
print(result.answer)
```

**优势**:
- 自动生成 Prompt
- 类型安全
- 易于复用
- 便于优化

### 2.2 Module (模块)

#### Predict (基础预测)
```python
class BasicQA(dspy.Module):
    def __init__(self):
        super().__init__()
        self.predictor = dspy.Predict("question -> answer")
    
    def forward(self, question):
        return self.predictor(question=question)

# 使用
qa = BasicQA()
result = qa(question="Python 的优势是什么？")
```

#### ChainOfThought (思维链)
```python
class CoTQA(dspy.Module):
    """带思维链的问答"""
    
    def __init__(self):
        super().__init__()
        # ChainOfThought 自动添加 "reasoning" 中间步骤
        self.cot = dspy.ChainOfThought("question -> answer")
    
    def forward(self, question):
        return self.cot(question=question)

# 使用
cot_qa = CoTQA()
result = cot_qa(question="为什么天空是蓝色的？")
print(result.reasoning)  # 推理过程
print(result.answer)     # 最终答案
```

#### ReAct (推理-行动)
```python
class ReActAgent(dspy.Module):
    """ReAct 模式 Agent"""
    
    def __init__(self, tools):
        super().__init__()
        self.tools = tools
        self.react = dspy.ReAct("question -> answer")
    
    def forward(self, question):
        return self.react(question=question, tools=self.tools)

# 使用
agent = ReActAgent(tools=[search_tool, calculator_tool])
result = agent(question="2024年奥运会在哪里举办？")
```

#### 自定义模块组合
```python
class RAG(dspy.Module):
    """检索增强生成"""
    
    def __init__(self, retriever, k=3):
        super().__init__()
        self.retriever = retriever
        self.k = k
        
        # 定义生成签名
        self.generate = dspy.ChainOfThought(
            "context, question -> answer"
        )
    
    def forward(self, question):
        # 1. 检索
        docs = self.retriever(question, k=self.k)
        context = "\n".join(docs)
        
        # 2. 生成
        result = self.generate(context=context, question=question)
        
        return result

# 使用
rag = RAG(retriever=my_retriever)
result = rag(question="什么是量子计算？")
```

### 2.3 Optimizer (Teleprompter)

**核心思想**: 自动优化程序的 Prompt 和 Few-shot 示例

#### BootstrapFewShot
```python
from dspy.teleprompt import BootstrapFewShot

# 定义评估函数
def validate_answer(example, prediction, trace=None):
    """验证答案是否正确"""
    return example.answer.lower() == prediction.answer.lower()

# 创建优化器
optimizer = BootstrapFewShot(
    metric=validate_answer,
    max_bootstrapped_demos=4,  # 最多 4 个示例
    max_labeled_demos=2  # 最多 2 个标注示例
)

# 优化程序
compiled_rag = optimizer.compile(
    student=rag,  # 要优化的程序
    trainset=train_examples  # 训练数据
)

# 优化后的程序自动包含优化的 few-shot 示例
result = compiled_rag(question="什么是深度学习？")
```

**BootstrapFewShot 工作原理**:
1. 在训练集上运行程序
2. 收集成功的执行轨迹
3. 选择最有代表性的示例
4. 将这些示例注入到 Prompt 中

#### MIPRO (Multi-prompt Instruction Proposal Optimizer)
```python
from dspy.teleprompt import MIPRO

# MIPRO 自动优化指令和示例
optimizer = MIPRO(
    metric=validate_answer,
    num_candidates=10,  # 生成 10 个候选指令
    init_temperature=1.0
)

compiled_rag = optimizer.compile(
    student=rag,
    trainset=train_examples,
    num_trials=50  # 尝试 50 次
)
```

**MIPRO 工作原理**:
1. 生成多个候选指令
2. 对每个指令进行评估
3. 选择表现最好的指令
4. 结合 Few-shot 示例

#### SignatureOptimizer
```python
from dspy.teleprompt import SignatureOptimizer

# 优化 Signature 的描述和指令
optimizer = SignatureOptimizer(
    metric=validate_answer,
    breadth=10,  # 每步生成 10 个候选
    depth=3  # 优化 3 轮
)

optimized_rag = optimizer.compile(
    student=rag,
    devset=dev_examples
)
```

### 2.4 Compiler (编译)

```python
# DSPy 编译过程示例
class MultiHopRAG(dspy.Module):
    def __init__(self):
        super().__init__()
        
        # 第一跳：分解问题
        self.decompose = dspy.ChainOfThought(
            "question -> sub_question1, sub_question2"
        )
        
        # 第二跳：检索每个子问题
        self.retrieve = dspy.Predict("sub_question -> context")
        
        # 第三跳：综合答案
        self.synthesize = dspy.ChainOfThought(
            "context1, context2, question -> answer"
        )
    
    def forward(self, question):
        # 分解
        decomp = self.decompose(question=question)
        
        # 检索
        ctx1 = self.retrieve(sub_question=decomp.sub_question1)
        ctx2 = self.retrieve(sub_question=decomp.sub_question2)
        
        # 综合
        result = self.synthesize(
            context1=ctx1.context,
            context2=ctx2.context,
            question=question
        )
        
        return result

# 编译优化
optimizer = BootstrapFewShot(metric=validate_answer)
compiled_multihop = optimizer.compile(
    student=MultiHopRAG(),
    trainset=train_data
)

# 编译后，每个 Predict/ChainOfThought 都包含优化的:
# - 指令
# - Few-shot 示例
# - 格式说明
```

### 2.5 Evaluation (评估)

```python
from dspy import Evaluate

# 定义评估指标
def exact_match(example, prediction, trace=None):
    """完全匹配"""
    return example.answer == prediction.answer

def f1_score(example, prediction, trace=None):
    """F1 分数"""
    pred_tokens = set(prediction.answer.lower().split())
    gold_tokens = set(example.answer.lower().split())
    
    if not pred_tokens or not gold_tokens:
        return 0.0
    
    common = pred_tokens & gold_tokens
    precision = len(common) / len(pred_tokens)
    recall = len(common) / len(gold_tokens)
    
    if precision + recall == 0:
        return 0.0
    
    return 2 * precision * recall / (precision + recall)

# 评估器
evaluator = Evaluate(
    devset=dev_examples,
    metric=f1_score,
    num_threads=4,
    display_progress=True
)

# 评估程序
score = evaluator(compiled_rag)
print(f"F1 Score: {score}")

# 详细评估
results = evaluator(compiled_rag, return_outputs=True)
for example, prediction, score in results:
    print(f"Q: {example.question}")
    print(f"Pred: {prediction.answer}")
    print(f"Gold: {example.answer}")
    print(f"Score: {score}\n")
```

---

## 3. 核心算法

### 3.1 Bootstrap Few-Shot 算法

```python
def bootstrap_few_shot(
    program: dspy.Module,
    trainset: List[Example],
    metric: Callable,
    max_demos: int = 4
) -> dspy.Module:
    """
    Bootstrap Few-Shot 优化算法
    
    算法流程:
    1. 在训练集上运行程序
    2. 收集成功的轨迹（通过 metric 验证）
    3. 选择最有代表性的示例
    4. 注入到程序的 Prompt 中
    """
    successful_traces = []
    
    # 1. 收集成功轨迹
    for example in trainset:
        try:
            # 运行程序
            prediction = program(**example.inputs())
            
            # 验证
            if metric(example, prediction):
                # 记录成功的输入-输出对
                successful_traces.append({
                    "inputs": example.inputs(),
                    "outputs": prediction.outputs(),
                    "trace": get_execution_trace()
                })
        except Exception as e:
            continue
    
    # 2. 选择代表性示例
    selected_demos = select_diverse_demos(
        successful_traces,
        max_demos=max_demos
    )
    
    # 3. 注入到程序
    for module in program.predictors():
        module.demos = selected_demos
    
    return program

def select_diverse_demos(
    traces: List[Dict],
    max_demos: int
) -> List[Dict]:
    """
    选择多样化的示例
    
    策略:
    1. 计算每个示例的嵌入向量
    2. 使用聚类或最大边际相关性（MMR）
    3. 选择覆盖最广的示例
    """
    if len(traces) <= max_demos:
        return traces
    
    # 计算嵌入
    embeddings = [
        embed(trace["inputs"]["question"])
        for trace in traces
    ]
    
    # MMR 选择
    selected = []
    remaining = list(range(len(traces)))
    
    # 第一个：选择最中心的
    centroid = np.mean(embeddings, axis=0)
    first_idx = np.argmax([
        cosine_similarity(emb, centroid)
        for emb in embeddings
    ])
    selected.append(traces[first_idx])
    remaining.remove(first_idx)
    
    # 后续：最大化多样性
    while len(selected) < max_demos and remaining:
        max_min_dist = -1
        best_idx = None
        
        for idx in remaining:
            # 计算到已选示例的最小距离
            min_dist = min([
                1 - cosine_similarity(embeddings[idx], embeddings[sel_idx])
                for sel_idx in [traces.index(s) for s in selected]
            ])
            
            if min_dist > max_min_dist:
                max_min_dist = min_dist
                best_idx = idx
        
        selected.append(traces[best_idx])
        remaining.remove(best_idx)
    
    return selected

# 时间复杂度: O(n * T + k^2) - n 为训练样本数，T 为程序执行时间，k 为示例数
# 空间复杂度: O(n * d) - d 为嵌入维度
```

### 3.2 MIPRO 优化算法

```python
def mipro_optimize(
    program: dspy.Module,
    trainset: List[Example],
    metric: Callable,
    num_candidates: int = 10,
    num_trials: int = 50
) -> dspy.Module:
    """
    MIPRO (Multi-prompt Instruction Proposal Optimizer)
    
    算法流程:
    1. 生成多个候选指令
    2. 评估每个指令
    3. 选择最佳指令
    4. 结合 Few-shot 示例优化
    """
    best_score = 0
    best_program = None
    
    for trial in range(num_trials):
        # 1. 生成候选指令
        candidates = generate_instruction_candidates(
            program,
            trainset,
            num_candidates=num_candidates
        )
        
        # 2. 评估每个候选
        for candidate in candidates:
            # 应用候选指令
            temp_program = apply_instruction(program.deepcopy(), candidate)
            
            # 在验证集上评估
            score = evaluate_on_dataset(temp_program, trainset[:50], metric)
            
            if score > best_score:
                best_score = score
                best_program = temp_program
        
        # 3. 基于最佳程序生成下一轮候选
        if best_program:
            program = best_program
    
    return best_program

def generate_instruction_candidates(
    program: dspy.Module,
    examples: List[Example],
    num_candidates: int
) -> List[str]:
    """
    生成候选指令
    
    策略:
    1. 分析现有指令
    2. 分析示例
    3. 使用 LLM 生成变体
    """
    current_instruction = program.get_instruction()
    
    # 分析示例特征
    example_analysis = analyze_examples(examples[:10])
    
    prompt = f"""
当前指令: {current_instruction}

示例特征: {example_analysis}

请生成 {num_candidates} 个改进的指令，使程序在这些示例上表现更好。

要求:
1. 每个指令应该清晰具体
2. 指令应该指导模型产生更准确的输出
3. 考虑示例的共同模式

候选指令（每行一个）:
"""
    
    response = llm.generate(prompt)
    candidates = response.strip().split('\n')[:num_candidates]
    
    return candidates

# 时间复杂度: O(trials * candidates * n * T) - T 为程序执行时间
# 空间复杂度: O(candidates * model_size)
```

### 3.3 Signature 优化算法

```python
def optimize_signature(
    signature: dspy.Signature,
    examples: List[Example],
    metric: Callable,
    breadth: int = 10,
    depth: int = 3
) -> dspy.Signature:
    """
    优化 Signature 的描述
    
    算法: 广度优先搜索 + 剪枝
    """
    queue = [(signature, 0, 0)]  # (sig, score, depth)
    best = (signature, 0)
    
    while queue:
        current_sig, current_score, current_depth = queue.pop(0)
        
        if current_depth >= depth:
            if current_score > best[1]:
                best = (current_sig, current_score)
            continue
        
        # 生成变体
        variants = generate_signature_variants(
            current_sig,
            examples,
            breadth=breadth
        )
        
        # 评估变体
        for variant in variants:
            score = evaluate_signature(variant, examples, metric)
            
            if score > current_score:
                queue.append((variant, score, current_depth + 1))
            
            if score > best[1]:
                best = (variant, score)
    
    return best[0]

def generate_signature_variants(
    signature: dspy.Signature,
    examples: List[Example],
    breadth: int
) -> List[dspy.Signature]:
    """
    生成 Signature 变体
    
    策略:
    1. 改进字段描述
    2. 添加中间字段
    3. 调整指令
    """
    variants = []
    
    # 策略 1: 改进输出字段描述
    for output_field in signature.output_fields:
        improved_desc = improve_field_description(
            field=output_field,
            examples=examples
        )
        
        new_sig = signature.copy()
        new_sig.output_fields[output_field].desc = improved_desc
        variants.append(new_sig)
    
    # 策略 2: 添加推理字段
    if "reasoning" not in signature.fields:
        new_sig = signature.copy()
        new_sig.add_field(
            "reasoning",
            dspy.OutputField(desc="一步步推理过程")
        )
        variants.append(new_sig)
    
    # 策略 3: 优化全局指令
    improved_instruction = optimize_instruction(
        signature.instructions,
        examples
    )
    new_sig = signature.copy()
    new_sig.instructions = improved_instruction
    variants.append(new_sig)
    
    return variants[:breadth]

# 时间复杂度: O(breadth^depth * n * T)
# 空间复杂度: O(breadth * depth)
```

### 3.4 示例选择算法 (MMR)

```python
def maximal_marginal_relevance(
    query: str,
    candidates: List[str],
    k: int,
    lambda_param: float = 0.5
) -> List[str]:
    """
    最大边际相关性 (MMR)
    
    平衡相关性和多样性
    
    公式: MMR = λ * Sim(query, doc) - (1-λ) * max(Sim(doc, selected))
    """
    query_emb = embed(query)
    candidate_embs = [embed(c) for c in candidates]
    
    selected = []
    remaining = list(range(len(candidates)))
    
    while len(selected) < k and remaining:
        max_mmr = -float('inf')
        best_idx = None
        
        for idx in remaining:
            # 相关性得分
            relevance = cosine_similarity(query_emb, candidate_embs[idx])
            
            # 多样性得分（与已选择的最大相似度）
            if selected:
                max_similarity = max([
                    cosine_similarity(candidate_embs[idx], candidate_embs[sel_idx])
                    for sel_idx in selected
                ])
            else:
                max_similarity = 0
            
            # MMR 得分
            mmr = lambda_param * relevance - (1 - lambda_param) * max_similarity
            
            if mmr > max_mmr:
                max_mmr = mmr
                best_idx = idx
        
        selected.append(best_idx)
        remaining.remove(best_idx)
    
    return [candidates[i] for i in selected]

# 时间复杂度: O(k * n^2) - k 为选择数量，n 为候选数量
# 空间复杂度: O(n * d) - d 为嵌入维度
```

### 3.5 程序跟踪和分析算法

```python
def trace_program_execution(
    program: dspy.Module,
    example: Example
) -> Dict:
    """
    跟踪程序执行
    
    记录:
    1. 每个模块的输入输出
    2. 生成的 Prompt
    3. LLM 的响应
    4. 中间状态
    """
    trace = {
        "inputs": example.inputs(),
        "modules": [],
        "outputs": None
    }
    
    # Hook 每个 Predictor
    for name, module in program.named_predictors():
        original_forward = module.forward
        
        def traced_forward(*args, **kwargs):
            # 记录输入
            module_trace = {
                "name": name,
                "inputs": kwargs.copy(),
                "prompt": None,
                "response": None,
                "outputs": None
            }
            
            # 执行
            result = original_forward(*args, **kwargs)
            
            # 记录输出
            module_trace["prompt"] = module.last_prompt
            module_trace["response"] = module.last_response
            module_trace["outputs"] = result
            
            trace["modules"].append(module_trace)
            
            return result
        
        module.forward = traced_forward
    
    # 执行程序
    outputs = program(**example.inputs())
    trace["outputs"] = outputs
    
    return trace

def analyze_trace(
    trace: Dict,
    example: Example,
    metric: Callable
) -> Dict:
    """
    分析执行轨迹
    
    识别:
    1. 错误发生在哪个模块
    2. 哪些 Prompt 效果好
    3. 哪些示例有帮助
    """
    analysis = {
        "success": metric(example, trace["outputs"]),
        "bottlenecks": [],
        "good_prompts": [],
        "bad_prompts": []
    }
    
    # 分析每个模块
    for module_trace in trace["modules"]:
        # 检查输出质量
        quality = assess_output_quality(
            module_trace["outputs"],
            expected=example.outputs()
        )
        
        if quality < 0.5:
            analysis["bottlenecks"].append({
                "module": module_trace["name"],
                "issue": "low_quality_output"
            })
            analysis["bad_prompts"].append(module_trace["prompt"])
        else:
            analysis["good_prompts"].append(module_trace["prompt"])
    
    return analysis

# 时间复杂度: O(m) - m 为模块数量
# 空间复杂度: O(t) - t 为轨迹大小
```

---

## 4. 设计模式

### 4.1 模板方法模式 (Template Method)

```python
class dspy.Module:
    """DSPy 模块基类"""
    
    def __call__(self, *args, **kwargs):
        """模板方法"""
        # 1. 预处理
        inputs = self._prepare_inputs(*args, **kwargs)
        
        # 2. 核心逻辑（子类实现）
        outputs = self.forward(**inputs)
        
        # 3. 后处理
        result = self._process_outputs(outputs)
        
        return result
    
    @abstractmethod
    def forward(self, **kwargs):
        """子类必须实现"""
        pass
    
    def _prepare_inputs(self, *args, **kwargs):
        """预处理输入"""
        return kwargs
    
    def _process_outputs(self, outputs):
        """后处理输出"""
        return outputs
```

### 4.2 策略模式 (Strategy Pattern) - Optimizer

```python
class OptimizerStrategy(ABC):
    @abstractmethod
    def compile(
        self,
        student: dspy.Module,
        trainset: List[Example],
        **kwargs
    ) -> dspy.Module:
        pass

class BootstrapFewShotStrategy(OptimizerStrategy):
    def compile(self, student, trainset, **kwargs):
        # Bootstrap 优化逻辑
        pass

class MIPROStrategy(OptimizerStrategy):
    def compile(self, student, trainset, **kwargs):
        # MIPRO 优化逻辑
        pass

class EnsembleStrategy(OptimizerStrategy):
    def compile(self, student, trainset, **kwargs):
        # 集成多个优化器
        pass

# 使用
optimizer = BootstrapFewShotStrategy()
compiled = optimizer.compile(program, trainset)
```

### 4.3 装饰器模式 (Decorator)

```python
class TracedModule(dspy.Module):
    """带跟踪的模块装饰器"""
    
    def __init__(self, module: dspy.Module):
        super().__init__()
        self.module = module
        self.traces = []
    
    def forward(self, **kwargs):
        trace = {
            "inputs": kwargs,
            "timestamp": time.time()
        }
        
        result = self.module(**kwargs)
        
        trace["outputs"] = result
        trace["duration"] = time.time() - trace["timestamp"]
        self.traces.append(trace)
        
        return result

class CachedModule(dspy.Module):
    """带缓存的模块装饰器"""
    
    def __init__(self, module: dspy.Module):
        super().__init__()
        self.module = module
        self.cache = {}
    
    def forward(self, **kwargs):
        cache_key = hash(frozenset(kwargs.items()))
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        result = self.module(**kwargs)
        self.cache[cache_key] = result
        
        return result

# 使用
traced = TracedModule(my_module)
cached_traced = CachedModule(traced)
```

### 4.4 组合模式 (Composite)

```python
class PipelineModule(dspy.Module):
    """管道组合"""
    
    def __init__(self, *modules):
        super().__init__()
        self.modules = modules
    
    def forward(self, **kwargs):
        result = kwargs
        
        for module in self.modules:
            result = module(**result)
        
        return result

class ParallelModule(dspy.Module):
    """并行组合"""
    
    def __init__(self, modules: Dict[str, dspy.Module]):
        super().__init__()
        self.modules = modules
    
    def forward(self, **kwargs):
        results = {}
        
        for name, module in self.modules.items():
            results[name] = module(**kwargs)
        
        return results

# 使用
pipeline = PipelineModule(
    retrieve_module,
    rerank_module,
    generate_module
)

parallel = ParallelModule({
    "search": search_module,
    "calculate": calc_module
})
```

### 4.5 工厂模式 (Factory)

```python
class PredictorFactory:
    """Predictor 工厂"""
    
    @staticmethod
    def create(
        signature: Union[str, dspy.Signature],
        mode: str = "predict"
    ) -> dspy.Module:
        """创建 Predictor"""
        
        if mode == "predict":
            return dspy.Predict(signature)
        
        elif mode == "chain_of_thought":
            return dspy.ChainOfThought(signature)
        
        elif mode == "react":
            return dspy.ReAct(signature)
        
        elif mode == "program_of_thought":
            return dspy.ProgramOfThought(signature)
        
        else:
            raise ValueError(f"Unknown mode: {mode}")

# 使用
predictor = PredictorFactory.create(
    "question -> answer",
    mode="chain_of_thought"
)
```

---

## 5. 可复用组件

### 5.1 核心组件清单

| 组件 | 功能 | 复用优先级 |
|------|------|-----------|
| Signature | 声明式接口定义 | ⭐⭐⭐⭐⭐ |
| Module | 可组合的程序模块 | ⭐⭐⭐⭐⭐ |
| BootstrapFewShot | Few-shot 自动优化 | ⭐⭐⭐⭐⭐ |
| ChainOfThought | 思维链模块 | ⭐⭐⭐⭐⭐ |
| MIPRO | 指令优化器 | ⭐⭐⭐⭐ |
| SignatureOptimizer | 签名优化器 | ⭐⭐⭐⭐ |
| Evaluate | 评估框架 | ⭐⭐⭐⭐⭐ |
| Trace System | 执行跟踪 | ⭐⭐⭐⭐ |
| MMR Selector | 示例选择器 | ⭐⭐⭐⭐ |
| Compiler | 程序编译器 | ⭐⭐⭐⭐ |

---

## 6. 集成到 FieldMind

### 6.1 声明式 AI 程序系统

```python
# fieldmind/dspy_integration/signature.py

from typing import get_type_hints, get_args, get_origin
from dataclasses import dataclass, field

@dataclass
class FieldSpec:
    """字段规范"""
    name: str
    type: type
    description: str
    is_input: bool

class FMSignature:
    """FieldMind Signature"""
    
    def __init__(self, signature_class: type):
        self.signature_class = signature_class
        self.fields = self._parse_fields()
        self.instructions = signature_class.__doc__ or ""
    
    def _parse_fields(self) -> list[FieldSpec]:
        """解析字段"""
        hints = get_type_hints(self.signature_class)
        fields = []
        
        for name, type_hint in hints.items():
            # 获取字段元数据
            field_obj = getattr(self.signature_class, name, None)
            
            if hasattr(field_obj, '__metadata__'):
                metadata = field_obj.__metadata__
                is_input = metadata.get('input', True)
                desc = metadata.get('desc', '')
            else:
                is_input = True
                desc = ''
            
            fields.append(FieldSpec(
                name=name,
                type=type_hint,
                description=desc,
                is_input=is_input
            ))
        
        return fields
    
    def generate_prompt(self, **inputs) -> str:
        """生成 Prompt"""
        parts = []
        
        # 指令
        if self.instructions:
            parts.append(self.instructions)
            parts.append("")
        
        # 输入字段
        for field in self.fields:
            if field.is_input and field.name in inputs:
                parts.append(f"{field.description}:")
                parts.append(str(inputs[field.name]))
                parts.append("")
        
        # 输出字段
        output_fields = [f for f in self.fields if not f.is_input]
        if output_fields:
            parts.append("请提供:")
            for field in output_fields:
                parts.append(f"- {field.name}: {field.description}")
        
        return "\n".join(parts)

# fieldmind/dspy_integration/module.py

class FMModule:
    """FieldMind 模块"""
    
    def __init__(self):
        self.predictors = []
    
    def __call__(self, **kwargs):
        return self.forward(**kwargs)
    
    def forward(self, **kwargs):
        """子类实现"""
        raise NotImplementedError
    
    def named_predictors(self):
        """返回所有 Predictor"""
        for name, value in self.__dict__.items():
            if isinstance(value, FMPredictor):
                yield name, value

class FMPredictor(FMModule):
    """基础预测器"""
    
    def __init__(self, signature: FMSignature, llm_service):
        super().__init__()
        self.signature = signature
        self.llm = llm_service
        self.demos = []  # Few-shot 示例
    
    def forward(self, **kwargs):
        # 生成 Prompt
        prompt = self.signature.generate_prompt(**kwargs)
        
        # 添加 Few-shot 示例
        if self.demos:
            demo_text = self._format_demos()
            prompt = demo_text + "\n\n" + prompt
        
        # 调用 LLM
        response = self.llm.complete(prompt)
        
        # 解析输出
        outputs = self._parse_outputs(response)
        
        return outputs
    
    def _format_demos(self) -> str:
        """格式化示例"""
        parts = ["示例:"]
        
        for i, demo in enumerate(self.demos):
            parts.append(f"\n示例 {i+1}:")
            parts.append(f"输入: {demo['inputs']}")
            parts.append(f"输出: {demo['outputs']}")
        
        return "\n".join(parts)
    
    def _parse_outputs(self, response: str) -> dict:
        """解析 LLM 输出"""
        # 简单实现：假设 LLM 返回 JSON
        import json
        try:
            return json.loads(response)
        except:
            # 回退：返回原始文本
            output_fields = [f for f in self.signature.fields if not f.is_input]
            if len(output_fields) == 1:
                return {output_fields[0].name: response}
            return {"output": response}

class FMChainOfThought(FMPredictor):
    """思维链预测器"""
    
    def forward(self, **kwargs):
        # 修改 Signature 添加 reasoning 字段
        enhanced_signature = self._add_reasoning_field()
        
        # 生成 Prompt
        prompt = enhanced_signature.generate_prompt(**kwargs)
        prompt += "\n请一步步思考，先给出推理过程，再给出最终答案。"
        
        # 调用 LLM
        response = self.llm.complete(prompt)
        
        # 解析
        outputs = self._parse_cot_output(response)
        
        return outputs
    
    def _add_reasoning_field(self):
        """添加推理字段"""
        # 实现略
        pass
    
    def _parse_cot_output(self, response: str) -> dict:
        """解析思维链输出"""
        # 提取推理过程和最终答案
        lines = response.strip().split('\n')
        
        reasoning = []
        answer = None
        
        for line in lines:
            if line.startswith("推理:") or line.startswith("Reasoning:"):
                reasoning.append(line.split(":", 1)[1].strip())
            elif line.startswith("答案:") or line.startswith("Answer:"):
                answer = line.split(":", 1)[1].strip()
        
        return {
            "reasoning": "\n".join(reasoning),
            "answer": answer
        }
```

### 6.2 自动优化器

```python
# fieldmind/dspy_integration/optimizer.py

class FMBootstrapFewShot:
    """FieldMind Bootstrap Few-Shot 优化器"""
    
    def __init__(
        self,
        metric: Callable,
        max_demos: int = 4,
        max_rounds: int = 3
    ):
        self.metric = metric
        self.max_demos = max_demos
        self.max_rounds = max_rounds
    
    async def compile(
        self,
        program: FMModule,
        trainset: List[Example]
    ) -> FMModule:
        """编译优化程序"""
        
        successful_traces = []
        
        # 多轮 Bootstrap
        for round_num in range(self.max_rounds):
            print(f"Bootstrap 第 {round_num + 1} 轮...")
            
            for example in trainset:
                try:
                    # 运行程序
                    prediction = await program(**example.inputs())
                    
                    # 验证
                    if self.metric(example, prediction):
                        # 记录成功轨迹
                        successful_traces.append({
                            "inputs": example.inputs(),
                            "outputs": prediction,
                            "round": round_num
                        })
                except Exception as e:
                    logging.error(f"执行失败: {e}")
                    continue
            
            # 选择示例
            selected = self._select_demos(
                successful_traces,
                max_demos=self.max_demos
            )
            
            # 注入到程序
            for name, predictor in program.named_predictors():
                predictor.demos = selected
        
        return program
    
    def _select_demos(
        self,
        traces: List[Dict],
        max_demos: int
    ) -> List[Dict]:
        """选择多样化示例 (MMR)"""
        if len(traces) <= max_demos:
            return traces
        
        # 使用 MMR 算法
        from fieldmind.utils.mmr import maximal_marginal_relevance
        
        # 提取查询（假设使用第一个输入字段）
        queries = [json.dumps(t["inputs"]) for t in traces]
        
        selected_indices = maximal_marginal_relevance(
            query="",  # 无特定查询
            candidates=queries,
            k=max_demos,
            lambda_param=0.5
        )
        
        return [traces[i] for i in selected_indices]

class FMSignatureOptimizer:
    """FieldMind Signature 优化器"""
    
    def __init__(
        self,
        metric: Callable,
        llm_service,
        num_variants: int = 5
    ):
        self.metric = metric
        self.llm = llm_service
        self.num_variants = num_variants
    
    async def optimize(
        self,
        signature: FMSignature,
        examples: List[Example]
    ) -> FMSignature:
        """优化 Signature"""
        
        best_signature = signature
        best_score = 0
        
        # 生成变体
        variants = await self._generate_variants(signature, examples)
        
        # 评估变体
        for variant in variants:
            score = await self._evaluate_signature(variant, examples)
            
            if score > best_score:
                best_score = score
                best_signature = variant
        
        return best_signature
    
    async def _generate_variants(
        self,
        signature: FMSignature,
        examples: List[Example]
    ) -> List[FMSignature]:
        """生成 Signature 变体"""
        
        prompt = f"""
当前 Signature:
指令: {signature.instructions}
字段: {[f.name + ': ' + f.description for f in signature.fields]}

示例:
{self._format_examples(examples[:3])}

请生成 {self.num_variants} 个改进的 Signature 变体。
对于每个变体，提供:
1. 改进的指令
2. 改进的字段描述

返回 JSON 数组格式:
[
  {{
    "instructions": "改进的指令",
    "fields": {{"field_name": "改进的描述"}}
  }}
]
"""
        
        response = await self.llm.complete_async(prompt)
        
        # 解析变体
        import json
        variants_data = json.loads(response)
        
        variants = []
        for data in variants_data:
            variant = self._create_variant(signature, data)
            variants.append(variant)
        
        return variants
    
    def _create_variant(
        self,
        base: FMSignature,
        data: Dict
    ) -> FMSignature:
        """创建变体"""
        # 复制并修改 Signature
        # 实现略
        pass
```

### 6.3 使用示例

```python
# 示例: 优化 RAG 系统

from fieldmind.dspy_integration import (
    FMSignature,
    FMModule,
    FMPredictor,
    FMChainOfThought,
    FMBootstrapFewShot
)

# 1. 定义 Signature
class RAGSignature(FMSignature):
    """检索增强生成"""
    
    context: str  # 输入
    question: str  # 输入
    answer: str  # 输出

# 2. 定义模块
class OptimizedRAG(FMModule):
    def __init__(self, retriever, llm_service):
        super().__init__()
        self.retriever = retriever
        self.generate = FMChainOfThought(
            RAGSignature(),
            llm_service
        )
    
    async def forward(self, question):
        # 检索
        docs = await self.retriever.search(question, k=3)
        context = "\n".join(docs)
        
        # 生成
        result = await self.generate(
            context=context,
            question=question
        )
        
        return result

# 3. 优化
async def optimize_rag():
    # 准备数据
    trainset = load_training_data()
    
    # 定义评估指标
    def validate(example, prediction):
        return f1_score(example.answer, prediction["answer"]) > 0.7
    
    # 创建优化器
    optimizer = FMBootstrapFewShot(
        metric=validate,
        max_demos=4
    )
    
    # 优化
    rag = OptimizedRAG(retriever, llm_service)
    optimized_rag = await optimizer.compile(rag, trainset)
    
    return optimized_rag

# 4. 使用
optimized_rag = await optimize_rag()
result = await optimized_rag(question="什么是量子计算？")
print(result["answer"])
```

---

## 7. 核心学习

### 关键概念
1. **声明式编程** - 定义"做什么"而非"怎么做"
2. **分离关注点** - 程序逻辑与 Prompt 优化分离
3. **自动优化** - 基于数据自动改进 Prompt
4. **模块化** - Signature + Module 的可组合架构
5. **评估驱动** - Metric 指导优化方向

### 核心算法
1. Bootstrap Few-Shot（收集成功轨迹）
2. MIPRO（多候选指令优化）
3. Signature 优化（广度优先搜索）
4. MMR 示例选择（平衡相关性和多样性）
5. 程序跟踪和分析

### 对 FieldMind 的价值
- ⭐⭐⭐⭐⭐ 声明式 Prompt 系统
- ⭐⭐⭐⭐⭐ 自动 Few-shot 优化
- ⭐⭐⭐⭐⭐ 可组合的模块架构
- ⭐⭐⭐⭐ 指令自动优化
- ⭐⭐⭐⭐ 评估驱动的改进循环

---

**分析完成时间**: 2026-08-29  
**已完成插件数**: 10/40 (25%)  
**下一个插件**: Haystack (Production-ready NLP Framework)
