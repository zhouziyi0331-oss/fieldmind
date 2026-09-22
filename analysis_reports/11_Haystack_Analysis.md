# Haystack 深度分析报告

**插件名称**: Haystack  
**开发者**: deepset  
**GitHub**: https://github.com/deepset-ai/haystack  
**Stars**: 16.8k+  
**类别**: 生产级 NLP 框架  
**语言**: Python  
**分析日期**: 2026-08-29

---

## 1. 插件概述

### 核心定位
Haystack 是一个生产级的端到端 NLP 框架，专注于构建可扩展的问答、搜索和文档处理系统。它提供了从文档预处理到部署的完整工具链。

### 核心特点
- **Pipeline 架构**: 可组合的组件管道
- **生产就绪**: 内置监控、日志、错误处理
- **多后端支持**: Elasticsearch, OpenSearch, Weaviate, Qdrant 等
- **可扩展性**: 自定义组件和节点
- **混合检索**: 关键词 + 语义混合搜索
- **评估工具**: 内置评估和基准测试

### 架构设计
```
Haystack
├── Document Store (文档存储)
│   ├── Elasticsearch
│   ├── Weaviate
│   ├── Qdrant
│   └── InMemory
├── Pipeline (管道)
│   ├── Node (节点)
│   ├── Edge (边)
│   └── Components (组件)
├── Retriever (检索器)
│   ├── BM25Retriever
│   ├── DenseRetriever
│   └── HybridRetriever
├── Reader (阅读器)
│   ├── FARMReader
│   ├── TransformersReader
│   └── TableReader
├── Generator (生成器)
│   ├── RAGenerator
│   └── OpenAIAnswerGenerator
└── Evaluation (评估)
    ├── Metrics
    └── Pipeline Evaluation
```

---

## 2. 核心概念

### 2.1 Pipeline 架构

```python
from haystack import Pipeline
from haystack.nodes import BM25Retriever, FARMReader

# 创建 Pipeline
pipeline = Pipeline()

# 添加组件
retriever = BM25Retriever(document_store=document_store)
reader = FARMReader(model_name_or_path="deepset/roberta-base-squad2")

pipeline.add_node(component=retriever, name="Retriever", inputs=["Query"])
pipeline.add_node(component=reader, name="Reader", inputs=["Retriever"])

# 运行
result = pipeline.run(
    query="什么是机器学习？",
    params={
        "Retriever": {"top_k": 10},
        "Reader": {"top_k": 3}
    }
)

print(result["answers"])
```

### 2.2 Document Store

```python
from haystack.document_stores import ElasticsearchDocumentStore, WeaviateDocumentStore

# Elasticsearch 后端
es_store = ElasticsearchDocumentStore(
    host="localhost",
    port=9200,
    index="documents",
    embedding_dim=768
)

# 写入文档
from haystack.schema import Document

docs = [
    Document(
        content="Python 是一种高级编程语言。",
        meta={"source": "wiki", "category": "programming"}
    ),
    Document(
        content="机器学习是人工智能的一个分支。",
        meta={"source": "wiki", "category": "AI"}
    )
]

es_store.write_documents(docs)

# 更新嵌入
from haystack.nodes import EmbeddingRetriever

retriever = EmbeddingRetriever(
    document_store=es_store,
    embedding_model="sentence-transformers/all-mpnet-base-v2"
)

es_store.update_embeddings(retriever)

# Weaviate 后端（向量数据库）
weaviate_store = WeaviateDocumentStore(
    host="http://localhost",
    port=8080,
    embedding_dim=768
)
```

### 2.3 Retriever (检索器)

#### BM25Retriever (关键词检索)
```python
from haystack.nodes import BM25Retriever

retriever = BM25Retriever(document_store=document_store)

# 检索
results = retriever.retrieve(
    query="机器学习的应用",
    top_k=10,
    filters={"category": ["AI", "ML"]}
)

for doc in results:
    print(f"Score: {doc.score}")
    print(f"Content: {doc.content}")
    print(f"Meta: {doc.meta}")
```

#### DenseRetriever (密集向量检索)
```python
from haystack.nodes import EmbeddingRetriever

retriever = EmbeddingRetriever(
    document_store=document_store,
    embedding_model="sentence-transformers/all-mpnet-base-v2",
    model_format="sentence_transformers"
)

# 检索
results = retriever.retrieve(
    query="深度学习的最新进展",
    top_k=5
)
```

#### MultiModalRetriever (多模态检索)
```python
from haystack.nodes import MultiModalRetriever

retriever = MultiModalRetriever(
    document_store=document_store,
    query_embedding_model="clip-ViT-B-32",
    document_embedding_models={
        "text": "sentence-transformers/all-mpnet-base-v2",
        "image": "clip-ViT-B-32"
    }
)

# 检索图像和文本
results = retriever.retrieve(
    query="猫的图片",
    top_k=10
)
```

#### HybridRetriever (混合检索)
```python
from haystack.nodes import JoinDocuments

# 创建两个检索器
bm25 = BM25Retriever(document_store=document_store)
dense = EmbeddingRetriever(document_store=document_store)

# 在 Pipeline 中组合
pipeline = Pipeline()
pipeline.add_node(component=bm25, name="BM25", inputs=["Query"])
pipeline.add_node(component=dense, name="Dense", inputs=["Query"])

# 合并结果
joiner = JoinDocuments(
    join_mode="reciprocal_rank_fusion"  # RRF 算法
)
pipeline.add_node(component=joiner, name="Joiner", inputs=["BM25", "Dense"])

# 运行
result = pipeline.run(
    query="Python 编程",
    params={
        "BM25": {"top_k": 10},
        "Dense": {"top_k": 10}
    }
)
```

### 2.4 Reader (阅读器)

```python
from haystack.nodes import FARMReader

# ExtractiveQA Reader
reader = FARMReader(
    model_name_or_path="deepset/roberta-base-squad2",
    use_gpu=True,
    num_processes=0,
    max_seq_len=384,
    doc_stride=128
)

# 预测
results = reader.predict(
    query="谁发明了 Python？",
    documents=retrieved_docs,
    top_k=3
)

for answer in results["answers"]:
    print(f"Answer: {answer.answer}")
    print(f"Score: {answer.score}")
    print(f"Context: {answer.context}")
    print(f"Document: {answer.document_id}")
```

### 2.5 Generator (生成器)

```python
from haystack.nodes import PromptNode, PromptTemplate

# 定义 Prompt 模板
prompt_template = PromptTemplate(
    name="question-answering",
    prompt_text="""
基于以下上下文回答问题。

上下文:
{join(documents)}

问题: {query}

答案:
""",
    output_parser={"type": "AnswerParser"}
)

# 创建 Generator
generator = PromptNode(
    model_name_or_path="gpt-3.5-turbo",
    api_key=openai_api_key,
    default_prompt_template=prompt_template,
    max_length=200
)

# 使用
result = generator.run(
    query="什么是量子计算？",
    documents=retrieved_docs
)

print(result["answers"][0].answer)
```

### 2.6 Agent

```python
from haystack.agents import Agent, Tool
from haystack.agents.memory import ConversationMemory

# 定义工具
search_tool = Tool(
    name="Search",
    pipeline_or_node=search_pipeline,
    description="用于搜索文档的工具"
)

calculator_tool = Tool(
    name="Calculator",
    pipeline_or_node=calculator_node,
    description="用于数学计算的工具"
)

# 创建 Agent
agent = Agent(
    prompt_node=prompt_node,
    tools=[search_tool, calculator_tool],
    memory=ConversationMemory()
)

# 运行
result = agent.run("搜索关于 AI 的信息，然后计算 2024 - 1950")

print(result["answers"])
```

### 2.7 Indexing Pipeline

```python
from haystack import Pipeline
from haystack.nodes import (
    TextConverter,
    PDFToTextConverter,
    Preprocessor,
    EmbeddingRetriever
)

# 创建索引管道
indexing_pipeline = Pipeline()

# 文件转换
text_converter = TextConverter()
pdf_converter = PDFToTextConverter()

indexing_pipeline.add_node(
    component=text_converter,
    name="TextConverter",
    inputs=["File"]
)

indexing_pipeline.add_node(
    component=pdf_converter,
    name="PDFConverter",
    inputs=["File"]
)

# 预处理
preprocessor = Preprocessor(
    clean_empty_lines=True,
    clean_whitespace=True,
    clean_header_footer=True,
    split_by="word",
    split_length=200,
    split_overlap=20,
    split_respect_sentence_boundary=True
)

indexing_pipeline.add_node(
    component=preprocessor,
    name="Preprocessor",
    inputs=["TextConverter", "PDFConverter"]
)

# 写入 Document Store
indexing_pipeline.add_node(
    component=document_store,
    name="DocumentStore",
    inputs=["Preprocessor"]
)

# 更新嵌入
indexing_pipeline.add_node(
    component=retriever,
    name="Retriever",
    inputs=["DocumentStore"]
)

# 运行
indexing_pipeline.run(file_paths=["./data/document.pdf"])
```

---

## 3. 核心算法

### 3.1 Reciprocal Rank Fusion (RRF)

```python
def reciprocal_rank_fusion(
    rankings: List[List[Document]],
    k: int = 60
) -> List[Document]:
    """
    倒数排名融合算法
    
    用于合并多个检索器的结果
    
    公式: RRF(d) = Σ 1/(k + rank_i(d))
    
    参数:
    - rankings: 多个排序列表
    - k: 常数，通常为 60
    """
    doc_scores = {}
    
    for ranking in rankings:
        for rank, doc in enumerate(ranking, start=1):
            doc_id = doc.id
            score = 1.0 / (k + rank)
            
            if doc_id in doc_scores:
                doc_scores[doc_id]["score"] += score
            else:
                doc_scores[doc_id] = {
                    "doc": doc,
                    "score": score
                }
    
    # 排序
    sorted_docs = sorted(
        doc_scores.values(),
        key=lambda x: x["score"],
        reverse=True
    )
    
    return [item["doc"] for item in sorted_docs]

# 时间复杂度: O(n * m) - n 为排序列表数，m 为每个列表长度
# 空间复杂度: O(m)
```

### 3.2 BM25 算法

```python
import math
from collections import Counter

def bm25_score(
    query_terms: List[str],
    document: str,
    doc_length: int,
    avg_doc_length: float,
    doc_freq: dict,
    num_docs: int,
    k1: float = 1.5,
    b: float = 0.75
) -> float:
    """
    BM25 评分算法
    
    公式:
    BM25(q,d) = Σ IDF(qi) * (f(qi,d) * (k1+1)) / (f(qi,d) + k1*(1-b+b*|d|/avgdl))
    
    参数:
    - query_terms: 查询词列表
    - document: 文档文本
    - doc_length: 文档长度
    - avg_doc_length: 平均文档长度
    - doc_freq: 文档频率字典
    - num_docs: 总文档数
    - k1: 词频饱和参数
    - b: 长度归一化参数
    """
    score = 0.0
    doc_terms = Counter(document.lower().split())
    
    for term in query_terms:
        # 词频
        term_freq = doc_terms.get(term.lower(), 0)
        
        # IDF
        df = doc_freq.get(term, 0)
        idf = math.log((num_docs - df + 0.5) / (df + 0.5) + 1.0)
        
        # BM25 分数
        numerator = term_freq * (k1 + 1)
        denominator = term_freq + k1 * (1 - b + b * doc_length / avg_doc_length)
        
        score += idf * (numerator / denominator)
    
    return score

# 时间复杂度: O(q) - q 为查询词数量
# 空间复杂度: O(d) - d 为文档唯一词数
```

### 3.3 Span Extraction (抽取式 QA)

```python
def extract_answer_span(
    question: str,
    context: str,
    model,
    tokenizer,
    max_seq_length: int = 384,
    doc_stride: int = 128
) -> List[Dict]:
    """
    抽取答案片段
    
    算法流程:
    1. 对长文本进行滑动窗口分块
    2. 对每个块预测 start 和 end logits
    3. 提取最可能的答案片段
    4. 合并多个块的结果
    """
    # Tokenize
    inputs = tokenizer(
        question,
        context,
        max_length=max_seq_length,
        stride=doc_stride,
        return_overflowing_tokens=True,
        return_offsets_mapping=True,
        padding="max_length",
        truncation="only_second"
    )
    
    # 预测
    outputs = model(**inputs)
    start_logits = outputs.start_logits
    end_logits = outputs.end_logits
    
    # 提取候选答案
    candidates = []
    
    for i in range(len(start_logits)):
        # 找到 top-k start 和 end 位置
        start_indices = torch.topk(start_logits[i], k=20).indices
        end_indices = torch.topk(end_logits[i], k=20).indices
        
        for start_idx in start_indices:
            for end_idx in end_indices:
                # 验证
                if end_idx < start_idx:
                    continue
                if end_idx - start_idx > 30:  # 答案太长
                    continue
                
                # 计算分数
                score = (
                    start_logits[i][start_idx].item() +
                    end_logits[i][end_idx].item()
                )
                
                # 提取文本
                offset_mapping = inputs["offset_mapping"][i]
                start_char = offset_mapping[start_idx][0]
                end_char = offset_mapping[end_idx][1]
                answer_text = context[start_char:end_char]
                
                candidates.append({
                    "text": answer_text,
                    "score": score,
                    "start": start_char,
                    "end": end_char
                })
    
    # 排序
    candidates.sort(key=lambda x: x["score"], reverse=True)
    
    # 去重
    unique_answers = []
    seen_texts = set()
    
    for candidate in candidates:
        text = candidate["text"].lower().strip()
        if text not in seen_texts:
            seen_texts.add(text)
            unique_answers.append(candidate)
    
    return unique_answers[:5]

# 时间复杂度: O(n * k^2) - n 为块数，k 为 top-k
# 空间复杂度: O(n * k^2)
```

### 3.4 Document Splitting (文档分割)

```python
def split_documents(
    documents: List[Document],
    split_by: str = "word",
    split_length: int = 200,
    split_overlap: int = 20,
    respect_sentence_boundary: bool = True
) -> List[Document]:
    """
    文档分割算法
    
    策略:
    - word: 按词数分割
    - sentence: 按句子分割
    - passage: 按段落分割
    
    特点:
    - 支持重叠
    - 尊重句子边界
    """
    split_docs = []
    
    for doc in documents:
        text = doc.content
        
        if split_by == "word":
            chunks = split_by_word(
                text,
                split_length,
                split_overlap,
                respect_sentence_boundary
            )
        elif split_by == "sentence":
            chunks = split_by_sentence(text, split_length)
        else:
            chunks = [text]
        
        for i, chunk in enumerate(chunks):
            split_doc = Document(
                content=chunk,
                meta={
                    **doc.meta,
                    "split_id": i,
                    "split_idx_start": doc.content.find(chunk)
                }
            )
            split_docs.append(split_doc)
    
    return split_docs

def split_by_word(
    text: str,
    length: int,
    overlap: int,
    respect_boundary: bool
) -> List[str]:
    """按词分割"""
    words = text.split()
    chunks = []
    
    start = 0
    while start < len(words):
        end = min(start + length, len(words))
        
        # 尊重句子边界
        if respect_boundary and end < len(words):
            # 找到最近的句子结束
            chunk_words = words[start:end]
            chunk_text = " ".join(chunk_words)
            
            # 查找句号、问号、感叹号
            for i in range(len(chunk_text) - 1, -1, -1):
                if chunk_text[i] in ".!?。！？":
                    # 截断到这里
                    actual_text = chunk_text[:i+1]
                    chunks.append(actual_text)
                    
                    # 更新 start
                    actual_words = actual_text.split()
                    start += len(actual_words) - overlap
                    break
            else:
                # 没找到句子边界
                chunks.append(chunk_text)
                start += length - overlap
        else:
            chunks.append(" ".join(words[start:end]))
            start += length - overlap
    
    return chunks

# 时间复杂度: O(n) - n 为文档总词数
# 空间复杂度: O(n)
```

### 3.5 Pipeline 执行算法

```python
def execute_pipeline(
    pipeline: Pipeline,
    query: str,
    params: dict
) -> dict:
    """
    Pipeline 执行算法
    
    算法:
    1. 拓扑排序确定执行顺序
    2. 按序执行节点
    3. 传递中间结果
    """
    # 1. 拓扑排序
    execution_order = topological_sort(pipeline.graph)
    
    # 2. 初始化
    data = {"query": query}
    
    # 3. 执行
    for node_name in execution_order:
        node = pipeline.nodes[node_name]
        node_params = params.get(node_name, {})
        
        # 获取输入
        inputs = []
        for input_node in pipeline.get_inputs(node_name):
            if input_node == "Query":
                inputs.append(data)
            else:
                inputs.append(data.get(input_node, {}))
        
        # 执行节点
        try:
            output = node.run(*inputs, **node_params)
            
            # 保存输出
            data[node_name] = output
            
        except Exception as e:
            logging.error(f"节点 {node_name} 执行失败: {e}")
            data[node_name] = {"error": str(e)}
    
    return data

def topological_sort(graph: dict) -> List[str]:
    """
    拓扑排序
    
    算法: Kahn's algorithm
    """
    # 计算入度
    in_degree = {node: 0 for node in graph}
    for node in graph:
        for neighbor in graph[node]:
            in_degree[neighbor] += 1
    
    # 队列
    queue = [node for node in in_degree if in_degree[node] == 0]
    result = []
    
    while queue:
        node = queue.pop(0)
        result.append(node)
        
        for neighbor in graph[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    
    # 检查是否有环
    if len(result) != len(graph):
        raise ValueError("Pipeline 包含环")
    
    return result

# 时间复杂度: O(V + E) - V 为节点数，E 为边数
# 空间复杂度: O(V)
```

---

## 4. 设计模式

### 4.1 管道模式 (Pipeline Pattern)

```python
class Pipeline:
    """管道模式"""
    
    def __init__(self):
        self.graph = {}
        self.nodes = {}
    
    def add_node(self, component, name: str, inputs: List[str]):
        """添加节点"""
        self.nodes[name] = component
        self.graph[name] = []
        
        for input_name in inputs:
            if input_name in self.graph:
                self.graph[input_name].append(name)
    
    def run(self, **kwargs):
        """运行管道"""
        return execute_pipeline(self, **kwargs)
```

### 4.2 策略模式 (Strategy Pattern) - Retriever

```python
class RetrieverStrategy(ABC):
    @abstractmethod
    def retrieve(
        self,
        query: str,
        filters: dict = None,
        top_k: int = 10
    ) -> List[Document]:
        pass

class BM25Strategy(RetrieverStrategy):
    def retrieve(self, query, filters, top_k):
        # BM25 检索
        pass

class DenseStrategy(RetrieverStrategy):
    def retrieve(self, query, filters, top_k):
        # 密集向量检索
        pass

class HybridStrategy(RetrieverStrategy):
    def __init__(self, strategies: List[RetrieverStrategy]):
        self.strategies = strategies
    
    def retrieve(self, query, filters, top_k):
        # 组合多个策略
        all_results = []
        for strategy in self.strategies:
            results = strategy.retrieve(query, filters, top_k)
            all_results.append(results)
        
        # 融合
        return reciprocal_rank_fusion(all_results)
```

### 4.3 适配器模式 (Adapter Pattern) - Document Store

```python
class DocumentStoreAdapter(ABC):
    """文档存储适配器"""
    
    @abstractmethod
    def write_documents(self, documents: List[Document]):
        pass
    
    @abstractmethod
    def get_all_documents(self) -> List[Document]:
        pass
    
    @abstractmethod
    def query_by_embedding(
        self,
        query_emb: np.ndarray,
        top_k: int = 10
    ) -> List[Document]:
        pass

class ElasticsearchAdapter(DocumentStoreAdapter):
    def __init__(self, client):
        self.client = client
    
    def write_documents(self, documents):
        # Elasticsearch 特定实现
        bulk_data = []
        for doc in documents:
            bulk_data.append({
                "index": {
                    "_index": self.index,
                    "_id": doc.id
                }
            })
            bulk_data.append(doc.to_dict())
        
        self.client.bulk(body=bulk_data)
    
    def query_by_embedding(self, query_emb, top_k):
        # Elasticsearch kNN 查询
        query = {
            "knn": {
                "embedding": {
                    "vector": query_emb.tolist(),
                    "k": top_k
                }
            }
        }
        
        response = self.client.search(body=query)
        return self._parse_response(response)

class WeaviateAdapter(DocumentStoreAdapter):
    def __init__(self, client):
        self.client = client
    
    def write_documents(self, documents):
        # Weaviate 特定实现
        with self.client.batch as batch:
            for doc in documents:
                batch.add_data_object(
                    doc.to_dict(),
                    class_name="Document"
                )
    
    def query_by_embedding(self, query_emb, top_k):
        # Weaviate 向量搜索
        result = (
            self.client.query
            .get("Document", ["content", "meta"])
            .with_near_vector({"vector": query_emb.tolist()})
            .with_limit(top_k)
            .do()
        )
        
        return self._parse_response(result)
```

### 4.4 装饰器模式 (Decorator) - Node Wrapper

```python
class NodeDecorator:
    """节点装饰器基类"""
    
    def __init__(self, node):
        self.node = node
    
    def run(self, *args, **kwargs):
        return self.node.run(*args, **kwargs)

class LoggingDecorator(NodeDecorator):
    """日志装饰器"""
    
    def run(self, *args, **kwargs):
        logging.info(f"Running {self.node.__class__.__name__}")
        start = time.time()
        
        result = self.node.run(*args, **kwargs)
        
        duration = time.time() - start
        logging.info(f"Completed in {duration:.2f}s")
        
        return result

class CachingDecorator(NodeDecorator):
    """缓存装饰器"""
    
    def __init__(self, node):
        super().__init__(node)
        self.cache = {}
    
    def run(self, *args, **kwargs):
        cache_key = self._make_key(args, kwargs)
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        result = self.node.run(*args, **kwargs)
        self.cache[cache_key] = result
        
        return result
    
    def _make_key(self, args, kwargs):
        return hash((str(args), str(sorted(kwargs.items()))))

class RetryDecorator(NodeDecorator):
    """重试装饰器"""
    
    def __init__(self, node, max_retries: int = 3):
        super().__init__(node)
        self.max_retries = max_retries
    
    def run(self, *args, **kwargs):
        for attempt in range(self.max_retries):
            try:
                return self.node.run(*args, **kwargs)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                logging.warning(f"Retry {attempt + 1}/{self.max_retries}: {e}")
                time.sleep(2 ** attempt)

# 使用
retriever = BM25Retriever(document_store)
retriever = LoggingDecorator(retriever)
retriever = CachingDecorator(retriever)
retriever = RetryDecorator(retriever, max_retries=3)
```

### 4.5 观察者模式 (Observer) - Pipeline Monitoring

```python
class PipelineObserver(ABC):
    @abstractmethod
    def on_node_start(self, node_name: str, inputs: dict):
        pass
    
    @abstractmethod
    def on_node_complete(self, node_name: str, outputs: dict, duration: float):
        pass
    
    @abstractmethod
    def on_node_error(self, node_name: str, error: Exception):
        pass

class MetricsObserver(PipelineObserver):
    def __init__(self):
        self.metrics = {
            "node_durations": {},
            "node_errors": {},
            "total_runs": 0
        }
    
    def on_node_start(self, node_name, inputs):
        self.metrics["total_runs"] += 1
    
    def on_node_complete(self, node_name, outputs, duration):
        if node_name not in self.metrics["node_durations"]:
            self.metrics["node_durations"][node_name] = []
        
        self.metrics["node_durations"][node_name].append(duration)
    
    def on_node_error(self, node_name, error):
        if node_name not in self.metrics["node_errors"]:
            self.metrics["node_errors"][node_name] = 0
        
        self.metrics["node_errors"][node_name] += 1
    
    def get_report(self) -> dict:
        report = {
            "total_runs": self.metrics["total_runs"],
            "average_durations": {}
        }
        
        for node, durations in self.metrics["node_durations"].items():
            report["average_durations"][node] = sum(durations) / len(durations)
        
        report["error_counts"] = self.metrics["node_errors"]
        
        return report

class MonitoredPipeline(Pipeline):
    def __init__(self):
        super().__init__()
        self.observers: List[PipelineObserver] = []
    
    def add_observer(self, observer: PipelineObserver):
        self.observers.append(observer)
    
    def run(self, **kwargs):
        for node_name in self.execution_order:
            # 通知开始
            for obs in self.observers:
                obs.on_node_start(node_name, kwargs)
            
            start = time.time()
            
            try:
                result = self.nodes[node_name].run(**kwargs)
                duration = time.time() - start
                
                # 通知完成
                for obs in self.observers:
                    obs.on_node_complete(node_name, result, duration)
                
            except Exception as e:
                # 通知错误
                for obs in self.observers:
                    obs.on_node_error(node_name, e)
                raise
```

---

## 5. 可复用组件

### 5.1 核心组件清单

| 组件 | 功能 | 复用优先级 |
|------|------|-----------|
| Pipeline | 可组合管道 | ⭐⭐⭐⭐⭐ |
| Document Store | 统一存储接口 | ⭐⭐⭐⭐⭐ |
| Hybrid Retriever | 混合检索 | ⭐⭐⭐⭐⭐ |
| RRF Algorithm | 结果融合 | ⭐⭐⭐⭐⭐ |
| Preprocessor | 文档预处理 | ⭐⭐⭐⭐⭐ |
| Span Extraction | 答案抽取 | ⭐⭐⭐⭐ |
| Indexing Pipeline | 索引管道 | ⭐⭐⭐⭐ |
| Evaluation Tools | 评估工具 | ⭐⭐⭐⭐ |
| Agent Framework | Agent 框架 | ⭐⭐⭐⭐ |
| Node Decorators | 节点装饰器 | ⭐⭐⭐⭐ |

---

## 6. 集成到 FieldMind

### 6.1 Pipeline 系统

```python
# fieldmind/pipeline/core.py

from typing import Dict, List, Any, Callable
from abc import ABC, abstractmethod

class FMNode(ABC):
    """FieldMind 节点基类"""
    
    @abstractmethod
    async def run(self, **kwargs) -> Dict[str, Any]:
        """执行节点"""
        pass
    
    def get_output_schema(self) -> Dict[str, type]:
        """返回输出模式"""
        return {}

class FMPipeline:
    """FieldMind Pipeline"""
    
    def __init__(self, name: str = "default"):
        self.name = name
        self.nodes: Dict[str, FMNode] = {}
        self.graph: Dict[str, List[str]] = {}
        self.observers: List[PipelineObserver] = []
    
    def add_node(
        self,
        component: FMNode,
        name: str,
        inputs: List[str]
    ):
        """添加节点"""
        self.nodes[name] = component
        self.graph[name] = inputs
    
    def add_observer(self, observer: PipelineObserver):
        """添加观察者"""
        self.observers.append(observer)
    
    async def run_async(
        self,
        query: str = None,
        params: Dict[str, Dict] = None
    ) -> Dict[str, Any]:
        """异步运行管道"""
        # 拓扑排序
        execution_order = self._topological_sort()
        
        # 初始化数据
        data = {"query": query} if query else {}
        
        # 执行
        for node_name in execution_order:
            node = self.nodes[node_name]
            node_params = params.get(node_name, {}) if params else {}
            
            # 通知观察者
            for obs in self.observers:
                obs.on_node_start(node_name, data)
            
            start = time.time()
            
            try:
                # 准备输入
                inputs = self._prepare_inputs(node_name, data)
                
                # 执行
                output = await node.run(**inputs, **node_params)
                
                # 保存输出
                data[node_name] = output
                
                # 通知完成
                duration = time.time() - start
                for obs in self.observers:
                    obs.on_node_complete(node_name, output, duration)
                
            except Exception as e:
                # 通知错误
                for obs in self.observers:
                    obs.on_node_error(node_name, e)
                
                logging.error(f"节点 {node_name} 失败: {e}")
                raise
        
        return data
    
    def _prepare_inputs(
        self,
        node_name: str,
        data: Dict
    ) -> Dict[str, Any]:
        """准备节点输入"""
        inputs = {}
        
        for input_name in self.graph[node_name]:
            if input_name == "Query":
                inputs["query"] = data.get("query")
            elif input_name in data:
                inputs[input_name] = data[input_name]
        
        return inputs
    
    def _topological_sort(self) -> List[str]:
        """拓扑排序"""
        # Kahn's algorithm
        in_degree = {node: 0 for node in self.nodes}
        
        for node in self.graph:
            for input_node in self.graph[node]:
                if input_node in in_degree:
                    in_degree[node] += 1
        
        queue = [n for n in in_degree if in_degree[n] == 0]
        result = []
        
        while queue:
            node = queue.pop(0)
            result.append(node)
            
            # 查找依赖此节点的节点
            for other_node in self.graph:
                if node in self.graph[other_node]:
                    in_degree[other_node] -= 1
                    if in_degree[other_node] == 0:
                        queue.append(other_node)
        
        if len(result) != len(self.nodes):
            raise ValueError("Pipeline 包含循环依赖")
        
        return result
```

### 6.2 混合检索器

```python
# fieldmind/retrieval/hybrid.py

class FMHybridRetriever(FMNode):
    """FieldMind 混合检索器"""
    
    def __init__(
        self,
        keyword_retriever,
        semantic_retriever,
        fusion_method: str = "rrf"
    ):
        self.keyword = keyword_retriever
        self.semantic = semantic_retriever
        self.fusion_method = fusion_method
    
    async def run(
        self,
        query: str,
        top_k: int = 10,
        **kwargs
    ) -> Dict[str, Any]:
        """执行混合检索"""
        
        # 并行检索
        keyword_task = self.keyword.retrieve_async(query, top_k=top_k)
        semantic_task = self.semantic.retrieve_async(query, top_k=top_k)
        
        keyword_results, semantic_results = await asyncio.gather(
            keyword_task,
            semantic_task
        )
        
        # 融合
        if self.fusion_method == "rrf":
            fused = self._reciprocal_rank_fusion(
                [keyword_results, semantic_results]
            )
        elif self.fusion_method == "weighted":
            fused = self._weighted_fusion(
                keyword_results,
                semantic_results,
                weights=[0.4, 0.6]
            )
        else:
            fused = keyword_results + semantic_results
        
        return {
            "documents": fused[:top_k],
            "keyword_count": len(keyword_results),
            "semantic_count": len(semantic_results)
        }
    
    def _reciprocal_rank_fusion(
        self,
        rankings: List[List[Document]],
        k: int = 60
    ) -> List[Document]:
        """RRF 融合"""
        doc_scores = {}
        
        for ranking in rankings:
            for rank, doc in enumerate(ranking, start=1):
                doc_id = doc.id
                score = 1.0 / (k + rank)
                
                if doc_id in doc_scores:
                    doc_scores[doc_id]["score"] += score
                else:
                    doc_scores[doc_id] = {
                        "doc": doc,
                        "score": score
                    }
        
        sorted_docs = sorted(
            doc_scores.values(),
            key=lambda x: x["score"],
            reverse=True
        )
        
        return [item["doc"] for item in sorted_docs]
    
    def _weighted_fusion(
        self,
        results1: List[Document],
        results2: List[Document],
        weights: List[float]
    ) -> List[Document]:
        """加权融合"""
        doc_scores = {}
        
        for doc in results1:
            doc_scores[doc.id] = {
                "doc": doc,
                "score": doc.score * weights[0]
            }
        
        for doc in results2:
            if doc.id in doc_scores:
                doc_scores[doc.id]["score"] += doc.score * weights[1]
            else:
                doc_scores[doc.id] = {
                    "doc": doc,
                    "score": doc.score * weights[1]
                }
        
        sorted_docs = sorted(
            doc_scores.values(),
            key=lambda x: x["score"],
            reverse=True
        )
        
        return [item["doc"] for item in sorted_docs]
```

### 6.3 使用示例

```python
# 示例：构建 RAG Pipeline

from fieldmind.pipeline import FMPipeline, FMNode
from fieldmind.retrieval import FMHybridRetriever
from fieldmind.generation import FMGenerator

# 创建 Pipeline
pipeline = FMPipeline(name="rag_pipeline")

# 检索节点
retriever = FMHybridRetriever(
    keyword_retriever=bm25_retriever,
    semantic_retriever=dense_retriever,
    fusion_method="rrf"
)

pipeline.add_node(
    component=retriever,
    name="Retriever",
    inputs=["Query"]
)

# 生成节点
generator = FMGenerator(llm_service=llm)

pipeline.add_node(
    component=generator,
    name="Generator",
    inputs=["Retriever"]
)

# 添加监控
metrics = MetricsObserver()
pipeline.add_observer(metrics)

# 运行
result = await pipeline.run_async(
    query="什么是量子计算？",
    params={
        "Retriever": {"top_k": 10},
        "Generator": {"max_tokens": 200}
    }
)

print(result["Generator"]["answer"])

# 查看指标
report = metrics.get_report()
print(f"检索耗时: {report['average_durations']['Retriever']:.2f}s")
print(f"生成耗时: {report['average_durations']['Generator']:.2f}s")
```

---

## 7. 核心学习

### 关键概念
1. **Pipeline 架构** - 可组合的节点管道
2. **混合检索** - 关键词 + 语义融合
3. **RRF 算法** - 倒数排名融合
4. **生产就绪** - 监控、日志、错误处理
5. **多后端支持** - 统一接口，多种存储

### 核心算法
1. RRF (Reciprocal Rank Fusion)
2. BM25 (关键词检索)
3. Span Extraction (答案抽取)
4. Document Splitting (文档分割)
5. Topological Sort (管道执行)

### 对 FieldMind 的价值
- ⭐⭐⭐⭐⭐ Pipeline 可组合架构
- ⭐⭐⭐⭐⭐ 混合检索系统
- ⭐⭐⭐⭐⭐ RRF 融合算法
- ⭐⭐⭐⭐ 文档预处理工具
- ⭐⭐⭐⭐ 节点装饰器模式

---

**分析完成时间**: 2026-08-29  
**已完成插件数**: 11/40 (27.5%)  
**下一个插件**: Instructor (Structured Outputs)
