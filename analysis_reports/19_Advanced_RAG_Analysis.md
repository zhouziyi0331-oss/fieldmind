# LlamaIndex Advanced RAG 深度分析报告

**插件名称**: LlamaIndex Advanced RAG  
**开发者**: LlamaIndex Team  
**GitHub**: https://github.com/run-llama/llama_index  
**类别**: 高级RAG技术  
**语言**: Python  
**分析日期**: 2026-08-30

---

## 1. 核心概述

LlamaIndex 除了基础功能外，还提供了多种高级 RAG 技术，这些技术能显著提升检索质量和生成准确性。

### 高级RAG技术分类
```
Advanced RAG Techniques
├── Query Transformation
│   ├── Query Decomposition
│   ├── Step-back Prompting
│   ├── HyDE (Hypothetical Document)
│   └── Query Rewriting
├── Retrieval Enhancement
│   ├── Sentence Window Retrieval
│   ├── Auto-merging Retrieval
│   ├── Recursive Retrieval
│   └── Small-to-Big Retrieval
├── Post-Retrieval
│   ├── Reranking
│   ├── Context Compression
│   ├── Filtering
│   └── Ensemble
└── Response Generation
    ├── Citation
    ├── Multi-step Reasoning
    └── Self-RAG (Self-reflection)
```

---

## 2. Query Transformation

### 2.1 Query Decomposition

```python
from llama_index.query_engine import SubQuestionQueryEngine
from llama_index.tools import QueryEngineTool

# 创建多个特定领域的查询引擎
vector_tool = QueryEngineTool.from_defaults(
    query_engine=vector_query_engine,
    description="用于搜索技术文档"
)

summary_tool = QueryEngineTool.from_defaults(
    query_engine=summary_query_engine,
    description="用于获取文档摘要"
)

# 子问题查询引擎
sub_question_engine = SubQuestionQueryEngine.from_defaults(
    query_engine_tools=[vector_tool, summary_tool]
)

# 复杂查询自动分解
response = sub_question_engine.query(
    "比较Python和JavaScript的优缺点，并给出使用建议"
)
# 自动分解为:
# 1. Python的优缺点是什么？
# 2. JavaScript的优缺点是什么？
# 3. 如何选择使用Python还是JavaScript？
```

**算法实现**:
```python
def decompose_query(
    complex_query: str,
    llm
) -> List[str]:
    """
    查询分解算法
    
    使用LLM将复杂查询分解为多个子查询
    """
    prompt = f"""
将以下复杂查询分解为多个简单的子查询：

查询: {complex_query}

子查询列表（每行一个）:
1.
"""
    
    response = llm.complete(prompt)
    sub_queries = parse_sub_queries(response)
    
    return sub_queries

# 时间复杂度: O(n) - n为子查询数量
```

### 2.2 HyDE (Hypothetical Document Embeddings)

```python
from llama_index.indices.query.query_transform import HyDEQueryTransform

# HyDE 转换
hyde_transform = HyDEQueryTransform(include_original=True)

# 使用
query_engine = index.as_query_engine()
query_engine = TransformQueryEngine(
    query_engine,
    query_transform=hyde_transform
)

# HyDE 工作流程:
# 1. 用户查询: "什么是量子计算？"
# 2. LLM生成假设文档: "量子计算是利用量子力学原理..."
# 3. 用假设文档的embedding检索
# 4. 检索到的真实文档更相关
```

**算法实现**:
```python
def hyde_transform(
    query: str,
    llm,
    num_hypothetical_docs: int = 1
) -> List[str]:
    """
    HyDE (Hypothetical Document Embeddings)
    
    生成假设文档来改善检索
    """
    prompt = f"""
基于以下查询，生成一个假设的、详细的文档片段来回答这个问题：

查询: {query}

假设文档:
"""
    
    hypothetical_docs = []
    
    for _ in range(num_hypothetical_docs):
        doc = llm.complete(prompt)
        hypothetical_docs.append(doc)
    
    return hypothetical_docs

# 效果: 通常能提升 10-20% 的检索质量
```

### 2.3 Step-back Prompting

```python
def step_back_prompting(query: str, llm) -> str:
    """
    退一步提示
    
    先提出更抽象的问题，再回答具体问题
    """
    # 生成抽象问题
    abstract_prompt = f"""
给定具体问题: {query}

生成一个更抽象、更general的相关问题：
"""
    
    abstract_query = llm.complete(abstract_prompt)
    
    # 先检索抽象问题的答案
    abstract_context = retrieve(abstract_query)
    
    # 再用抽象上下文回答具体问题
    answer_prompt = f"""
背景知识:
{abstract_context}

现在请回答具体问题: {query}

答案:
"""
    
    answer = llm.complete(answer_prompt)
    return answer

# 示例:
# 具体问题: "2024年iPhone 15的价格是多少？"
# 抽象问题: "iPhone的定价策略是什么？"
# → 获得定价背景 → 更好地回答具体问题
```

---

## 3. Retrieval Enhancement

### 3.1 Sentence Window Retrieval

```python
from llama_index.node_parser import SentenceWindowNodeParser
from llama_index.postprocessor import MetadataReplacementPostProcessor

# 使用句子窗口解析
node_parser = SentenceWindowNodeParser.from_defaults(
    window_size=3,  # 前后各3个句子
    window_metadata_key="window",
    original_text_metadata_key="original_text"
)

# 创建索引
index = VectorStoreIndex.from_documents(
    documents,
    node_parser=node_parser
)

# 查询时替换为完整上下文
query_engine = index.as_query_engine(
    node_postprocessors=[
        MetadataReplacementPostProcessor(target_metadata_key="window")
    ]
)
```

**原理**:
```
文档: [S1] [S2] [S3] [S4] [S5] [S6] [S7]

索引: 只嵌入 S4
检索: 匹配到 S4
返回: S1 S2 S3 [S4] S5 S6 S7  (窗口=3)

优势: 检索粒度细，但返回上下文完整
```

### 3.2 Auto-merging Retrieval

```python
from llama_index.node_parser import HierarchicalNodeParser
from llama_index.retrievers import AutoMergingRetriever

# 层次化解析
node_parser = HierarchicalNodeParser.from_defaults(
    chunk_sizes=[2048, 512, 128]  # 3层
)

nodes = node_parser.get_nodes_from_documents(documents)

# 创建存储（保留层次关系）
storage_context = StorageContext.from_defaults()
storage_context.docstore.add_documents(nodes)

# Auto-merging 检索器
retriever = AutoMergingRetriever(
    vector_retriever,
    storage_context.docstore,
    verbose=True
)

# 工作流程:
# 1. 检索小块 (128 tokens)
# 2. 如果多个小块来自同一个中块，合并为中块
# 3. 如果多个中块来自同一个大块，合并为大块
```

**算法**:
```python
def auto_merge_nodes(
    retrieved_nodes: List[Node],
    threshold: float = 0.5
) -> List[Node]:
    """
    自动合并节点
    
    如果来自同一父节点的子节点比例超过阈值，
    则返回父节点
    """
    # 按父节点分组
    parent_groups = defaultdict(list)
    
    for node in retrieved_nodes:
        parent_id = node.parent_id
        if parent_id:
            parent_groups[parent_id].append(node)
    
    # 检查是否合并
    merged_nodes = []
    
    for parent_id, children in parent_groups.items():
        parent_node = get_node(parent_id)
        total_children = len(parent_node.child_nodes)
        
        # 如果检索到的子节点比例超过阈值
        if len(children) / total_children >= threshold:
            # 返回父节点
            merged_nodes.append(parent_node)
        else:
            # 保留子节点
            merged_nodes.extend(children)
    
    return merged_nodes

# 优势: 自适应上下文大小
```

### 3.3 Recursive Retrieval

```python
from llama_index.retrievers import RecursiveRetriever

# 递归检索器
recursive_retriever = RecursiveRetriever(
    "vector",
    retriever_dict={"vector": vector_retriever},
    node_dict=node_dict,
    verbose=True
)

# 工作流程:
# 1. 检索顶层节点
# 2. 对于每个检索到的节点，递归检索其子节点
# 3. 合并所有相关节点
```

**算法**:
```python
def recursive_retrieve(
    query: str,
    node: Node,
    depth: int = 0,
    max_depth: int = 3
) -> List[Node]:
    """
    递归检索
    
    深度优先遍历文档树
    """
    if depth >= max_depth:
        return [node]
    
    results = [node]
    
    # 如果节点有子节点
    if node.child_nodes:
        for child in node.child_nodes:
            # 计算相关性
            relevance = compute_relevance(query, child)
            
            if relevance > threshold:
                # 递归检索子节点
                child_results = recursive_retrieve(
                    query,
                    child,
                    depth + 1,
                    max_depth
                )
                results.extend(child_results)
    
    return results

# 时间复杂度: O(b^d) - b为分支因子，d为深度
```

---

## 4. Post-Retrieval Processing

### 4.1 Context Compression

```python
from llama_index.postprocessor import LongLLMLinguaPostprocessor

# 上下文压缩
compressor = LongLLMLinguaPostprocessor(
    instruction_str="Given the context, please answer the question",
    target_token=300,  # 压缩到300 tokens
    rank_method="longllmlingua",
    additional_compress_kwargs={
        "condition_compare": True,
        "condition_in_question": "after",
        "context_budget": "+100",
        "reorder_context": "sort"
    }
)

query_engine = index.as_query_engine(
    node_postprocessors=[compressor]
)

# 效果: 保留最相关的内容，减少token消耗
```

**算法**:
```python
def compress_context(
    context: str,
    query: str,
    target_length: int,
    llm
) -> str:
    """
    上下文压缩
    
    保留与查询最相关的部分
    """
    # 1. 分句
    sentences = split_into_sentences(context)
    
    # 2. 计算每句相关性
    relevance_scores = []
    
    for sent in sentences:
        score = compute_relevance(query, sent, llm)
        relevance_scores.append((sent, score))
    
    # 3. 按相关性排序
    relevance_scores.sort(key=lambda x: x[1], reverse=True)
    
    # 4. 选择句子直到达到目标长度
    compressed = []
    current_length = 0
    
    for sent, score in relevance_scores:
        sent_length = len(sent.split())
        if current_length + sent_length <= target_length:
            compressed.append(sent)
            current_length += sent_length
        else:
            break
    
    # 5. 重排序（恢复原始顺序）
    compressed.sort(key=lambda x: sentences.index(x))
    
    return " ".join(compressed)

# 效果: 节省 50-70% token，保持答案质量
```

### 4.2 Metadata Filtering

```python
from llama_index.vector_stores.types import MetadataFilters, MetadataFilter

# 元数据过滤
filters = MetadataFilters(
    filters=[
        MetadataFilter(key="category", value="技术"),
        MetadataFilter(key="year", value=2024, operator=">=")
    ]
)

retriever = index.as_retriever(
    similarity_top_k=10,
    filters=filters
)
```

### 4.3 Ensemble Retrieval

```python
from llama_index.retrievers import QueryFusionRetriever

# 集成多个检索器
retriever = QueryFusionRetriever(
    [vector_retriever, bm25_retriever, keyword_retriever],
    similarity_top_k=10,
    num_queries=4,  # 生成4个查询变体
    mode="reciprocal_rerank",  # RRF模式
    use_async=True
)
```

---

## 5. 核心算法

### 5.1 Multi-step Reasoning

```python
def multi_step_reasoning(
    query: str,
    index,
    llm,
    max_steps: int = 5
) -> str:
    """
    多步推理
    
    迭代式检索和推理
    """
    context = ""
    current_query = query
    
    for step in range(max_steps):
        # 1. 检索
        retrieved = index.retrieve(current_query)
        new_context = "\n".join([n.text for n in retrieved])
        context += "\n" + new_context
        
        # 2. 推理
        reasoning_prompt = f"""
已知信息:
{context}

问题: {query}

当前步骤: {step + 1}
请进行推理。如果需要更多信息，生成下一个查询。
如果可以回答，给出最终答案。

格式:
思考: ...
是否需要更多信息: 是/否
下一个查询: ... (如果需要)
最终答案: ... (如果不需要更多信息)
"""
        
        response = llm.complete(reasoning_prompt)
        
        # 3. 解析响应
        if "是否需要更多信息: 否" in response:
            # 得到最终答案
            answer = extract_final_answer(response)
            return answer
        else:
            # 生成下一个查询
            current_query = extract_next_query(response)
    
    # 达到最大步数，返回当前答案
    return llm.complete(f"基于以下信息回答: {query}\n\n{context}")

# 时间复杂度: O(s * r) - s为步数，r为每次检索时间
```

### 5.2 Self-RAG (Self-Reflective RAG)

```python
def self_rag(
    query: str,
    index,
    llm
) -> str:
    """
    Self-RAG: 带自我反思的RAG
    
    步骤:
    1. 检索
    2. 生成答案
    3. 自我评估（相关性、准确性）
    4. 如果不满意，重新检索
    """
    max_iterations = 3
    
    for iteration in range(max_iterations):
        # 1. 检索
        retrieved = index.retrieve(query, top_k=5)
        context = "\n".join([n.text for n in retrieved])
        
        # 2. 生成答案
        answer = llm.complete(f"Context: {context}\n\nQuestion: {query}\n\nAnswer:")
        
        # 3. 自我评估
        evaluation_prompt = f"""
评估以下答案的质量：

问题: {query}
上下文: {context}
答案: {answer}

请评分（1-5）：
相关性:
准确性:
完整性:

总体评分:
是否需要改进: 是/否
改进建议: ...
"""
        
        evaluation = llm.complete(evaluation_prompt)
        score = extract_score(evaluation)
        
        # 4. 判断是否重新检索
        if score >= 4:
            return answer
        else:
            # 根据改进建议生成新查询
            improvement = extract_improvement(evaluation)
            query = refine_query(query, improvement, llm)
    
    return answer

# 效果: 提升答案质量 15-25%
```

### 5.3 RAG-Fusion

```python
def rag_fusion(
    query: str,
    index,
    llm,
    num_queries: int = 4
) -> str:
    """
    RAG-Fusion: 多查询融合
    
    生成多个相关查询，融合结果
    """
    # 1. 生成多个查询
    queries = generate_related_queries(query, llm, num_queries)
    queries.append(query)  # 包含原始查询
    
    # 2. 并行检索
    all_results = []
    for q in queries:
        results = index.retrieve(q, top_k=10)
        all_results.append(results)
    
    # 3. RRF融合
    fused_results = reciprocal_rank_fusion(all_results)
    
    # 4. 生成答案
    context = "\n".join([n.text for n in fused_results[:5]])
    answer = llm.complete(f"Context: {context}\n\nQuestion: {query}\n\nAnswer:")
    
    return answer

def generate_related_queries(
    original_query: str,
    llm,
    num_queries: int
) -> List[str]:
    """生成相关查询"""
    prompt = f"""
原始查询: {original_query}

生成 {num_queries} 个相关但角度不同的查询：
1.
2.
...
"""
    
    response = llm.complete(prompt)
    queries = parse_queries(response)
    
    return queries

# 效果: 提升召回率 20-30%
```

---

## 6. 可复用组件清单

| 组件 | 功能 | 复用优先级 |
|------|------|-----------|
| Query Decomposition | 查询分解 | ⭐⭐⭐⭐⭐ |
| HyDE | 假设文档生成 | ⭐⭐⭐⭐⭐ |
| Step-back Prompting | 抽象化查询 | ⭐⭐⭐⭐ |
| Sentence Window | 句子窗口检索 | ⭐⭐⭐⭐⭐ |
| Auto-merging | 自动合并节点 | ⭐⭐⭐⭐⭐ |
| Recursive Retrieval | 递归检索 | ⭐⭐⭐⭐ |
| Context Compression | 上下文压缩 | ⭐⭐⭐⭐⭐ |
| Multi-step Reasoning | 多步推理 | ⭐⭐⭐⭐⭐ |
| Self-RAG | 自我反思RAG | ⭐⭐⭐⭐⭐ |
| RAG-Fusion | 多查询融合 | ⭐⭐⭐⭐⭐ |

---

## 7. 核心学习

### 关键技术
1. **HyDE** - 用假设文档改善检索
2. **句子窗口** - 细粒度索引+完整上下文
3. **自动合并** - 自适应上下文大小
4. **上下文压缩** - 节省token保持质量
5. **Self-RAG** - 自我评估和改进

### 对 FieldMind 的价值
- ⭐⭐⭐⭐⭐ HyDE技术
- ⭐⭐⭐⭐⭐ 句子窗口检索
- ⭐⭐⭐⭐⭐ 上下文压缩
- ⭐⭐⭐⭐⭐ Multi-step推理
- ⭐⭐⭐⭐⭐ RAG-Fusion

---

**分析完成时间**: 2026-08-30  
**已完成插件数**: 19/40 (47.5%)  
**剩余**: 21个插件
