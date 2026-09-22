# Prompt Engineering 技术深度分析报告

**插件名称**: Advanced Prompt Engineering Techniques  
**类别**: Prompt优化技术集  
**分析日期**: 2026-08-30

---

## 1. 概述

Prompt Engineering 是 LLM 应用开发的核心技能。本报告整合业界最佳实践，包括 Chain-of-Thought、Few-shot Learning、Self-consistency 等技术。

### 核心技术分类
```
Prompt Engineering
├── Basic Techniques (基础技术)
│   ├── Zero-shot Prompting
│   ├── Few-shot Learning
│   ├── Role Prompting
│   └── Instruction Following
├── Advanced Reasoning (高级推理)
│   ├── Chain-of-Thought (CoT)
│   ├── Tree of Thoughts (ToT)
│   ├── Self-Consistency
│   └── ReAct
├── Decomposition (任务分解)
│   ├── Least-to-Most
│   ├── Subquestion Decomposition
│   └── Plan-and-Solve
├── Self-Improvement (自我改进)
│   ├── Self-Refinement
│   ├── Self-Critique
│   └── Reflexion
└── Calibration (校准)
    ├── Self-Calibration
    ├── Temperature Tuning
    └── Confidence Scoring
```

---

## 2. 基础技术

### 2.1 Zero-shot Prompting

```python
def zero_shot_prompt(task: str, query: str) -> str:
    """
    零样本提示
    
    直接描述任务，不提供示例
    """
    prompt = f"""
任务: {task}

输入: {query}

输出:
"""
    return prompt

# 使用
prompt = zero_shot_prompt(
    task="将以下文本分类为正面或负面情感",
    query="这个产品太棒了！"
)
# 任务: 将以下文本分类为正面或负面情感
# 输入: 这个产品太棒了！
# 输出:
```

### 2.2 Few-shot Learning

```python
def few_shot_prompt(
    task: str,
    examples: List[Dict[str, str]],
    query: str
) -> str:
    """
    少样本学习
    
    提供几个示例来指导模型
    """
    prompt_parts = [f"任务: {task}\n"]
    
    # 添加示例
    for i, example in enumerate(examples, 1):
        prompt_parts.append(f"示例 {i}:")
        prompt_parts.append(f"输入: {example['input']}")
        prompt_parts.append(f"输出: {example['output']}\n")
    
    # 添加查询
    prompt_parts.append(f"现在，请处理以下输入:")
    prompt_parts.append(f"输入: {query}")
    prompt_parts.append("输出:")
    
    return "\n".join(prompt_parts)

# 使用
examples = [
    {"input": "这个产品很好用", "output": "正面"},
    {"input": "质量太差了", "output": "负面"},
    {"input": "还可以，一般般", "output": "中性"}
]

prompt = few_shot_prompt(
    task="情感分类",
    examples=examples,
    query="超出预期，非常满意！"
)
```

### 2.3 Role Prompting

```python
def role_prompt(
    role: str,
    context: str,
    task: str
) -> str:
    """
    角色提示
    
    赋予模型特定角色和背景
    """
    prompt = f"""
你是一个{role}。

背景信息:
{context}

任务:
{task}

请以{role}的专业角度完成任务。
"""
    return prompt

# 使用
prompt = role_prompt(
    role="资深Python工程师",
    context="你有10年的Python开发经验，擅长代码优化和性能调优",
    task="审查以下代码并提出改进建议:\n\n```python\n...\n```"
)
```

---

## 3. Chain-of-Thought (CoT)

### 3.1 基础 CoT

```python
def chain_of_thought_prompt(question: str) -> str:
    """
    思维链提示
    
    引导模型逐步推理
    """
    prompt = f"""
问题: {question}

让我们一步一步思考:

"""
    return prompt

# 使用
question = "一个数字的3倍加上5等于20，这个数字是多少？"
prompt = chain_of_thought_prompt(question)

# 模型输出:
# 让我们一步一步思考:
# 1. 设这个数字为 x
# 2. 根据题意：3x + 5 = 20
# 3. 移项：3x = 20 - 5
# 4. 计算：3x = 15
# 5. 求解：x = 15 / 3 = 5
# 
# 答案: 5
```

### 3.2 Few-shot CoT

```python
def few_shot_cot_prompt(
    examples: List[Dict],
    question: str
) -> str:
    """
    少样本思维链
    
    提供带推理过程的示例
    """
    prompt_parts = []
    
    # 添加示例
    for example in examples:
        prompt_parts.append(f"问题: {example['question']}")
        prompt_parts.append(f"思考过程:")
        prompt_parts.append(example['reasoning'])
        prompt_parts.append(f"答案: {example['answer']}\n")
    
    # 添加查询
    prompt_parts.append(f"问题: {question}")
    prompt_parts.append("思考过程:")
    
    return "\n".join(prompt_parts)

# 使用
examples = [
    {
        "question": "Roger有5个网球。他又买了2罐网球，每罐3个。他现在有多少个网球？",
        "reasoning": "1. Roger最初有5个网球\n2. 他买了2罐，每罐3个，所以买了 2 × 3 = 6个\n3. 总共: 5 + 6 = 11个",
        "answer": "11个"
    }
]

prompt = few_shot_cot_prompt(examples, "Alice有3盒铅笔，每盒8支。她送给朋友5支。她还有多少支？")
```

### 3.3 Zero-shot CoT

```python
def zero_shot_cot_prompt(question: str) -> str:
    """
    零样本思维链
    
    只需添加 "Let's think step by step"
    """
    prompt = f"""
问题: {question}

让我们一步一步地思考。

"""
    return prompt

# 研究表明，这个简单的提示能显著提升推理能力
```

---

## 4. Self-Consistency

```python
def self_consistency(
    question: str,
    llm,
    num_samples: int = 5,
    temperature: float = 0.7
) -> str:
    """
    自一致性算法
    
    生成多个推理路径，选择最一致的答案
    
    流程:
    1. 用 CoT 生成多个推理路径
    2. 提取每个路径的答案
    3. 投票选择最常见的答案
    """
    # 1. 生成多个推理路径
    prompt = chain_of_thought_prompt(question)
    
    responses = []
    for _ in range(num_samples):
        response = llm.complete(
            prompt,
            temperature=temperature  # 高温度增加多样性
        )
        responses.append(response)
    
    # 2. 提取答案
    answers = []
    for response in responses:
        # 解析最终答案
        answer = extract_final_answer(response)
        answers.append(answer)
    
    # 3. 投票
    from collections import Counter
    answer_counts = Counter(answers)
    most_common_answer = answer_counts.most_common(1)[0][0]
    
    return most_common_answer

def extract_final_answer(response: str) -> str:
    """从推理过程中提取最终答案"""
    # 查找 "答案:" 或 "Answer:" 后的内容
    import re
    
    patterns = [
        r"答案[:：]\s*(.+?)(?:\n|$)",
        r"Answer[:：]\s*(.+?)(?:\n|$)",
        r"因此[，,]\s*(.+?)(?:\n|$)"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, response)
        if match:
            return match.group(1).strip()
    
    # 如果找不到，返回最后一行
    return response.strip().split('\n')[-1]

# 使用
answer = self_consistency(
    "一个停车场有3排，每排有15个车位。如果已经停了25辆车，还能停多少辆？",
    llm=openai_llm,
    num_samples=5
)

# 时间复杂度: O(n * t) - n为样本数，t为生成时间
# 优势: 提升准确率 10-20%
```

---

## 5. Tree of Thoughts (ToT)

```python
class ThoughtNode:
    """思维树节点"""
    def __init__(
        self,
        thought: str,
        parent=None,
        depth: int = 0
    ):
        self.thought = thought
        self.parent = parent
        self.children = []
        self.depth = depth
        self.value = None  # 评估分数
    
    def add_child(self, child):
        self.children.append(child)

def tree_of_thoughts(
    problem: str,
    llm,
    max_depth: int = 3,
    num_branches: int = 3,
    evaluator = None
) -> str:
    """
    思维树算法
    
    探索多条推理路径，选择最优的
    
    流程:
    1. 生成初始想法
    2. 对每个想法，生成子想法
    3. 评估每个节点
    4. 选择最佳路径
    """
    # 1. 创建根节点
    root = ThoughtNode(thought=problem, depth=0)
    
    # 2. BFS 构建树
    from collections import deque
    queue = deque([root])
    
    while queue:
        node = queue.popleft()
        
        if node.depth >= max_depth:
            continue
        
        # 生成子想法
        children_thoughts = generate_next_thoughts(
            problem,
            node.thought,
            llm,
            num_branches
        )
        
        for thought in children_thoughts:
            child = ThoughtNode(
                thought=thought,
                parent=node,
                depth=node.depth + 1
            )
            node.add_child(child)
            queue.append(child)
    
    # 3. 评估所有叶子节点
    leaves = get_leaf_nodes(root)
    
    for leaf in leaves:
        leaf.value = evaluate_thought_path(leaf, evaluator, llm)
    
    # 4. 选择最佳路径
    best_leaf = max(leaves, key=lambda x: x.value)
    
    # 5. 回溯完整路径
    path = []
    current = best_leaf
    while current:
        path.append(current.thought)
        current = current.parent
    
    path.reverse()
    
    return "\n→ ".join(path)

def generate_next_thoughts(
    problem: str,
    current_thought: str,
    llm,
    num_thoughts: int
) -> List[str]:
    """生成下一步的想法"""
    prompt = f"""
问题: {problem}

当前思路: {current_thought}

请提出 {num_thoughts} 个不同的下一步思路来解决这个问题。

思路1:
思路2:
思路3:
"""
    
    response = llm.complete(prompt, temperature=0.8)
    
    # 解析
    thoughts = []
    for line in response.split('\n'):
        if line.startswith('思路'):
            thought = line.split(':', 1)[1].strip()
            thoughts.append(thought)
    
    return thoughts[:num_thoughts]

def evaluate_thought_path(
    leaf_node: ThoughtNode,
    evaluator,
    llm
) -> float:
    """评估思维路径"""
    # 构建完整路径
    path = []
    current = leaf_node
    while current.parent:  # 跳过根节点（问题）
        path.append(current.thought)
        current = current.parent
    
    path.reverse()
    
    if evaluator:
        return evaluator(path)
    
    # 默认评估：使用 LLM 打分
    path_text = "\n".join([f"{i+1}. {t}" for i, t in enumerate(path)])
    
    prompt = f"""
评估以下推理路径的质量（0-10分）：

{path_text}

评分（只需要数字）:
"""
    
    score_text = llm.complete(prompt, temperature=0)
    
    try:
        score = float(score_text.strip())
        return score
    except:
        return 5.0  # 默认中等分数

def get_leaf_nodes(root: ThoughtNode) -> List[ThoughtNode]:
    """获取所有叶子节点"""
    leaves = []
    
    def traverse(node):
        if not node.children:
            leaves.append(node)
        else:
            for child in node.children:
                traverse(child)
    
    traverse(root)
    return leaves

# 时间复杂度: O(b^d) - b为分支因子，d为深度
# 空间复杂度: O(b^d)
```

---

## 6. Self-Refinement

```python
def self_refinement(
    task: str,
    llm,
    max_iterations: int = 3
) -> str:
    """
    自我精炼算法
    
    迭代改进输出
    
    流程:
    1. 初始生成
    2. 自我批评
    3. 基于批评改进
    4. 重复直到满意
    """
    # 1. 初始生成
    initial_prompt = f"""
任务: {task}

请完成这个任务:
"""
    
    output = llm.complete(initial_prompt)
    
    # 2-4. 迭代改进
    for iteration in range(max_iterations):
        # 自我批评
        critique_prompt = f"""
原始任务: {task}

当前输出:
{output}

请批评这个输出，指出可以改进的地方：
"""
        
        critique = llm.complete(critique_prompt)
        
        # 检查是否满意
        if "没有需要改进" in critique or "已经很好" in critique:
            break
        
        # 基于批评改进
        refinement_prompt = f"""
原始任务: {task}

之前的输出:
{output}

批评意见:
{critique}

请根据批评意见改进输出:
"""
        
        output = llm.complete(refinement_prompt)
    
    return output

# 时间复杂度: O(k) - k为迭代次数
```

---

## 7. Least-to-Most Prompting

```python
def least_to_most_prompting(
    complex_problem: str,
    llm
) -> str:
    """
    从简到繁提示
    
    将复杂问题分解为简单子问题，逐个解决
    
    流程:
    1. 分解问题
    2. 按顺序解决子问题
    3. 组合答案
    """
    # 1. 分解问题
    decomposition_prompt = f"""
将以下复杂问题分解为简单的子问题：

问题: {complex_problem}

子问题列表（从简单到复杂）:
1.
"""
    
    decomposition = llm.complete(decomposition_prompt)
    
    # 解析子问题
    subproblems = []
    for line in decomposition.split('\n'):
        if line.strip() and line[0].isdigit():
            subproblem = line.split('.', 1)[1].strip()
            subproblems.append(subproblem)
    
    # 2. 逐个解决
    context = ""
    answers = []
    
    for i, subproblem in enumerate(subproblems):
        solving_prompt = f"""
原始问题: {complex_problem}

{context}

当前子问题: {subproblem}

请解决这个子问题:
"""
        
        answer = llm.complete(solving_prompt)
        answers.append(answer)
        
        # 更新上下文
        context += f"\n子问题 {i+1}: {subproblem}\n答案: {answer}\n"
    
    # 3. 组合答案
    final_prompt = f"""
原始问题: {complex_problem}

我们已经解决了以下子问题:
{context}

请综合这些答案，给出原始问题的完整回答:
"""
    
    final_answer = llm.complete(final_prompt)
    
    return final_answer

# 时间复杂度: O(n) - n为子问题数量
# 优势: 处理复杂推理，准确率提升 15-25%
```

---

## 8. Reflexion

```python
def reflexion(
    task: str,
    llm,
    max_trials: int = 3
) -> str:
    """
    反思算法
    
    从失败中学习，迭代改进
    
    流程:
    1. 尝试任务
    2. 评估结果
    3. 反思失败原因
    4. 用反思指导下次尝试
    """
    memory = []  # 存储历史尝试和反思
    
    for trial in range(max_trials):
        # 1. 构建提示（包含历史反思）
        attempt_prompt = f"""
任务: {task}

"""
        
        if memory:
            attempt_prompt += "之前的尝试和反思:\n"
            for i, mem in enumerate(memory):
                attempt_prompt += f"\n尝试 {i+1}:\n{mem['attempt']}\n"
                attempt_prompt += f"反思: {mem['reflection']}\n"
            
            attempt_prompt += "\n基于以上经验，请再次尝试:\n"
        else:
            attempt_prompt += "请尝试完成任务:\n"
        
        # 2. 尝试
        attempt = llm.complete(attempt_prompt)
        
        # 3. 评估
        evaluation = evaluate_attempt(task, attempt, llm)
        
        if evaluation['success']:
            return attempt
        
        # 4. 反思
        reflection_prompt = f"""
任务: {task}

你的尝试:
{attempt}

评估结果: {evaluation['feedback']}

请反思：
1. 哪里做错了？
2. 为什么会错？
3. 下次应该如何改进？

反思:
"""
        
        reflection = llm.complete(reflection_prompt)
        
        # 保存到记忆
        memory.append({
            'attempt': attempt,
            'evaluation': evaluation,
            'reflection': reflection
        })
    
    # 达到最大尝试次数
    return memory[-1]['attempt']

def evaluate_attempt(
    task: str,
    attempt: str,
    llm
) -> Dict:
    """评估尝试"""
    eval_prompt = f"""
任务: {task}

尝试的答案:
{attempt}

这个答案是否正确完成了任务？如果不正确，请指出问题。

评估:
"""
    
    feedback = llm.complete(eval_prompt)
    
    # 简化判断
    success = "正确" in feedback or "成功" in feedback
    
    return {
        'success': success,
        'feedback': feedback
    }

# 时间复杂度: O(k) - k为尝试次数
```

---

## 9. 核心算法总结

### 9.1 Few-shot 示例选择算法

```python
def select_few_shot_examples(
    query: str,
    example_pool: List[Dict],
    k: int = 3,
    method: str = "similarity"
) -> List[Dict]:
    """
    选择最相关的 few-shot 示例
    
    方法:
    - similarity: 基于语义相似度
    - diversity: 最大化多样性
    - difficulty: 选择难度适中的
    """
    if method == "similarity":
        return select_by_similarity(query, example_pool, k)
    elif method == "diversity":
        return select_by_diversity(example_pool, k)
    elif method == "difficulty":
        return select_by_difficulty(query, example_pool, k)

def select_by_similarity(
    query: str,
    examples: List[Dict],
    k: int
) -> List[Dict]:
    """基于相似度选择"""
    from sentence_transformers import SentenceTransformer
    
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # 编码
    query_emb = model.encode(query)
    example_embs = model.encode([ex['input'] for ex in examples])
    
    # 计算相似度
    from sklearn.metrics.pairwise import cosine_similarity
    similarities = cosine_similarity([query_emb], example_embs)[0]
    
    # Top-K
    top_indices = np.argsort(similarities)[::-1][:k]
    
    return [examples[i] for i in top_indices]

# 时间复杂度: O(n * d) - n个示例，d为嵌入维度
```

### 9.2 提示优化算法

```python
def optimize_prompt(
    base_prompt: str,
    test_cases: List[Dict],
    llm,
    num_iterations: int = 5
) -> str:
    """
    自动优化提示
    
    使用遗传算法/梯度下降优化提示
    """
    best_prompt = base_prompt
    best_score = evaluate_prompt(best_prompt, test_cases, llm)
    
    for iteration in range(num_iterations):
        # 生成变体
        variants = generate_prompt_variants(best_prompt, llm)
        
        # 评估每个变体
        for variant in variants:
            score = evaluate_prompt(variant, test_cases, llm)
            
            if score > best_score:
                best_score = score
                best_prompt = variant
    
    return best_prompt

def generate_prompt_variants(
    prompt: str,
    llm
) -> List[str]:
    """生成提示变体"""
    variant_prompt = f"""
给定以下提示:
{prompt}

请生成3个改进版本:
1.
2.
3.
"""
    
    response = llm.complete(variant_prompt)
    
    # 解析变体
    variants = []
    for line in response.split('\n'):
        if line.strip() and line[0].isdigit():
            variant = line.split('.', 1)[1].strip()
            variants.append(variant)
    
    return variants

def evaluate_prompt(
    prompt: str,
    test_cases: List[Dict],
    llm
) -> float:
    """评估提示质量"""
    correct = 0
    
    for case in test_cases:
        full_prompt = prompt.format(**case['input'])
        response = llm.complete(full_prompt)
        
        if is_correct_answer(response, case['expected_output']):
            correct += 1
    
    return correct / len(test_cases)

# 时间复杂度: O(i * v * n) - i次迭代，v个变体，n个测试用例
```

---

## 10. 可复用组件清单

| 组件 | 功能 | 复用优先级 |
|------|------|-----------|
| Chain-of-Thought | 思维链推理 | ⭐⭐⭐⭐⭐ |
| Self-Consistency | 自一致性投票 | ⭐⭐⭐⭐⭐ |
| Tree of Thoughts | 思维树探索 | ⭐⭐⭐⭐ |
| Self-Refinement | 自我精炼 | ⭐⭐⭐⭐⭐ |
| Least-to-Most | 从简到繁分解 | ⭐⭐⭐⭐⭐ |
| Reflexion | 反思学习 | ⭐⭐⭐⭐ |
| Few-shot Selection | 示例选择 | ⭐⭐⭐⭐⭐ |
| Prompt Optimization | 提示优化 | ⭐⭐⭐⭐ |
| Role Prompting | 角色扮演 | ⭐⭐⭐⭐⭐ |
| Answer Extraction | 答案提取 | ⭐⭐⭐⭐⭐ |

---

## 11. 核心学习

### 关键技术
1. **Chain-of-Thought** - 逐步推理
2. **Self-Consistency** - 多路径投票
3. **Tree of Thoughts** - 树形探索
4. **Self-Refinement** - 迭代改进
5. **Least-to-Most** - 分解简化

### 核心算法
1. CoT推理生成
2. Self-Consistency投票
3. ToT树搜索
4. 自我精炼迭代
5. Few-shot示例选择

### 对 FieldMind 的价值
- ⭐⭐⭐⭐⭐ CoT推理框架
- ⭐⭐⭐⭐⭐ Self-Consistency实现
- ⭐⭐⭐⭐ ToT探索
- ⭐⭐⭐⭐⭐ Self-Refinement
- ⭐⭐⭐⭐⭐ Least-to-Most分解

---

**分析完成时间**: 2026-08-30  
**已完成插件数**: 29/40 (72.5%)  
**下一个插件**: Memory Systems
