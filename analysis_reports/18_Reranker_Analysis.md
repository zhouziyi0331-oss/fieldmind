# Sentence-Transformers (Reranker) 深度分析报告

**插件名称**: Sentence-Transformers / Cross-Encoder  
**开发者**: UKPLab  
**GitHub**: https://github.com/UKPLab/sentence-transformers  
**Stars**: 14k+  
**类别**: 句子嵌入和重排序  
**语言**: Python  
**分析日期**: 2026-08-30

---

## 1. 插件概述

### 核心定位
Sentence-Transformers 提供了易用的句子、段落嵌入接口。其 Cross-Encoder 模块是 RAG 系统中重排序的标准解决方案，能显著提升检索质量。

### 核心特点
- **Bi-Encoder**: 独立编码查询和文档
- **Cross-Encoder**: 联合编码实现精确重排
- **预训练模型**: 丰富的预训练模型库
- **易用性**: 简洁的 API
- **多语言**: 支持100+语言
- **语义搜索**: 开箱即用

### 架构设计
```
Sentence-Transformers
├── Bi-Encoder (双塔编码)
│   ├── Query Encoder
│   ├── Document Encoder
│   ├── Similarity Computation
│   └── Vector Search
├── Cross-Encoder (交叉编码)
│   ├── Query-Doc Joint Encoding
│   ├── Relevance Scoring
│   ├── Reranking
│   └── Top-K Selection
├── Training
│   ├── Contrastive Learning
│   ├── Triplet Loss
│   ├── Multiple Negatives
│   └── Knowledge Distillation
└── Evaluation
    ├── Information Retrieval Metrics
    ├── Semantic Similarity
    └── Classification
```

---

## 2. 核心概念

### 2.1 Bi-Encoder (检索阶段)

```python
from sentence_transformers import SentenceTransformer
import numpy as np

# 加载模型
model = SentenceTransformer('all-MiniLM-L6-v2')

# 编码文档
documents = [
    "Python is a programming language",
    "Machine learning is a subset of AI",
    "Deep learning uses neural networks"
]

doc_embeddings = model.encode(documents)

# 编码查询
query = "What is Python?"
query_embedding = model.encode(query)

# 计算相似度
from sklearn.metrics.pairwise import cosine_similarity
similarities = cosine_similarity([query_embedding], doc_embeddings)[0]

# 排序
ranked_indices = np.argsort(similarities)[::-1]
for idx in ranked_indices:
    print(f"{documents[idx]}: {similarities[idx]:.4f}")
```

### 2.2 Cross-Encoder (重排序阶段)

```python
from sentence_transformers import CrossEncoder

# 加载 Cross-Encoder
reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

# 准备查询-文档对
query = "What is machine learning?"
documents = [
    "Machine learning is a subset of AI",
    "Python is a programming language",
    "Deep learning uses neural networks"
]

# 打分
pairs = [[query, doc] for doc in documents]
scores = reranker.predict(pairs)

# 重排序
ranked_indices = np.argsort(scores)[::-1]
for idx in ranked_indices:
    print(f"{documents[idx]}: {scores[idx]:.4f}")
```

### 2.3 两阶段检索

```python
class TwoStageRetriever:
    """两阶段检索：Bi-Encoder + Cross-Encoder"""
    
    def __init__(
        self,
        bi_encoder_name: str = 'all-MiniLM-L6-v2',
        cross_encoder_name: str = 'cross-encoder/ms-marco-MiniLM-L-6-v2'
    ):
        self.bi_encoder = SentenceTransformer(bi_encoder_name)
        self.cross_encoder = CrossEncoder(cross_encoder_name)
        
        self.doc_embeddings = None
        self.documents = []
    
    def index(self, documents: List[str]):
        """索引文档"""
        self.documents = documents
        self.doc_embeddings = self.bi_encoder.encode(
            documents,
            show_progress_bar=True,
            batch_size=32
        )
    
    def retrieve(
        self,
        query: str,
        top_k_retrieval: int = 100,
        top_k_rerank: int = 10
    ) -> List[Tuple[str, float]]:
        """两阶段检索"""
        
        # 阶段1: Bi-Encoder 快速检索
        query_embedding = self.bi_encoder.encode(query)
        similarities = cosine_similarity([query_embedding], self.doc_embeddings)[0]
        
        # 取 top_k_retrieval 候选
        top_indices = np.argsort(similarities)[::-1][:top_k_retrieval]
        candidates = [self.documents[i] for i in top_indices]
        
        # 阶段2: Cross-Encoder 精确重排
        pairs = [[query, doc] for doc in candidates]
        rerank_scores = self.cross_encoder.predict(pairs)
        
        # 最终排序
        final_indices = np.argsort(rerank_scores)[::-1][:top_k_rerank]
        
        results = [
            (candidates[i], rerank_scores[i])
            for i in final_indices
        ]
        
        return results

# 使用
retriever = TwoStageRetriever()
retriever.index(documents)

results = retriever.retrieve(
    "What is AI?",
    top_k_retrieval=100,
    top_k_rerank=10
)

for doc, score in results:
    print(f"{doc}: {score:.4f}")
```

### 2.4 语义搜索优化

```python
from sentence_transformers import util

# Semantic Search with util
def semantic_search(
    query: str,
    corpus: List[str],
    model: SentenceTransformer,
    top_k: int = 5
):
    """语义搜索"""
    
    # 编码
    query_embedding = model.encode(query, convert_to_tensor=True)
    corpus_embeddings = model.encode(corpus, convert_to_tensor=True)
    
    # 使用 util.semantic_search (高效实现)
    hits = util.semantic_search(
        query_embedding,
        corpus_embeddings,
        top_k=top_k
    )[0]
    
    results = []
    for hit in hits:
        results.append({
            'corpus_id': hit['corpus_id'],
            'score': hit['score'],
            'text': corpus[hit['corpus_id']]
        })
    
    return results

# 批量语义搜索
def batch_semantic_search(
    queries: List[str],
    corpus: List[str],
    model: SentenceTransformer,
    top_k: int = 5
):
    """批量语义搜索"""
    
    query_embeddings = model.encode(queries, convert_to_tensor=True)
    corpus_embeddings = model.encode(corpus, convert_to_tensor=True)
    
    # 批量搜索
    all_hits = util.semantic_search(
        query_embeddings,
        corpus_embeddings,
        top_k=top_k
    )
    
    return all_hits
```

### 2.5 训练自定义模型

```python
from sentence_transformers import SentenceTransformer, InputExample, losses
from torch.utils.data import DataLoader

# 准备训练数据
train_examples = [
    InputExample(texts=['Query 1', 'Relevant doc'], label=1.0),
    InputExample(texts=['Query 1', 'Irrelevant doc'], label=0.0),
    InputExample(texts=['Query 2', 'Relevant doc'], label=1.0),
]

# 创建 DataLoader
train_dataloader = DataLoader(
    train_examples,
    shuffle=True,
    batch_size=16
)

# 加载基础模型
model = SentenceTransformer('distilbert-base-uncased')

# 定义损失函数
train_loss = losses.CosineSimilarityLoss(model)

# 训练
model.fit(
    train_objectives=[(train_dataloader, train_loss)],
    epochs=1,
    warmup_steps=100
)

# 保存
model.save('my-custom-model')
```

### 2.6 多向量表示

```python
from sentence_transformers import SentenceTransformer

# ColBERT 风格的多向量表示
class MultiVectorEncoder:
    """多向量编码器"""
    
    def __init__(self, model_name: str):
        self.model = SentenceTransformer(model_name)
    
    def encode_multi_vector(
        self,
        texts: List[str],
        max_length: int = 512
    ) -> List[np.ndarray]:
        """
        编码为多向量表示
        
        每个token一个向量
        """
        # 使用模型的tokenizer
        features = self.model.tokenize(texts)
        
        # 获取所有token的embeddings
        with torch.no_grad():
            outputs = self.model(**features)
            token_embeddings = outputs[0]  # (batch, seq_len, hidden_size)
        
        return token_embeddings.cpu().numpy()
    
    def max_sim_score(
        self,
        query_vectors: np.ndarray,
        doc_vectors: np.ndarray
    ) -> float:
        """
        MaxSim 评分 (ColBERT)
        
        对每个查询向量，找到文档中最相似的向量
        """
        # query_vectors: (q_len, dim)
        # doc_vectors: (d_len, dim)
        
        # 计算所有对的相似度
        sim_matrix = np.dot(query_vectors, doc_vectors.T)  # (q_len, d_len)
        
        # 对每个查询token，取最大相似度
        max_sims = np.max(sim_matrix, axis=1)
        
        # 求和
        score = np.sum(max_sims)
        
        return score
```

---

## 3. 核心算法

### 3.1 Contrastive Learning 算法

```python
def contrastive_loss(
    query_embedding: torch.Tensor,
    pos_doc_embedding: torch.Tensor,
    neg_doc_embeddings: torch.Tensor,
    temperature: float = 0.05
) -> torch.Tensor:
    """
    对比学习损失 (InfoNCE)
    
    目标: 让查询更接近正样本，远离负样本
    
    公式:
    L = -log(exp(sim(q, d+) / τ) / Σ exp(sim(q, di) / τ))
    """
    # 计算相似度
    pos_sim = torch.sum(query_embedding * pos_doc_embedding, dim=-1) / temperature
    
    # 负样本相似度
    neg_sims = torch.matmul(
        query_embedding.unsqueeze(0),
        neg_doc_embeddings.T
    ).squeeze(0) / temperature
    
    # 组合所有相似度
    all_sims = torch.cat([pos_sim.unsqueeze(0), neg_sims])
    
    # Softmax + 负对数似然
    loss = -pos_sim + torch.logsumexp(all_sims, dim=0)
    
    return loss

# 时间复杂度: O(d) - d为嵌入维度
# 空间复杂度: O(n) - n为负样本数
```

### 3.2 Hard Negative Mining 算法

```python
def hard_negative_mining(
    query_embedding: np.ndarray,
    positive_doc: str,
    candidate_docs: List[str],
    doc_embeddings: np.ndarray,
    n_hard: int = 5
) -> List[int]:
    """
    难负样本挖掘
    
    选择与查询相似但不相关的文档作为难负样本
    
    策略:
    1. 计算查询与所有候选的相似度
    2. 排除正样本
    3. 选择相似度最高的作为难负样本
    """
    # 计算相似度
    similarities = cosine_similarity([query_embedding], doc_embeddings)[0]
    
    # 找到正样本的索引
    pos_idx = candidate_docs.index(positive_doc)
    
    # 排除正样本
    similarities[pos_idx] = -np.inf
    
    # 选择最相似的作为难负样本
    hard_neg_indices = np.argsort(similarities)[::-1][:n_hard]
    
    return hard_neg_indices.tolist()

def dynamic_hard_negative_mining(
    model: SentenceTransformer,
    query: str,
    positive_doc: str,
    corpus: List[str],
    n_hard: int = 5
) -> List[str]:
    """
    动态难负样本挖掘
    
    在训练过程中动态选择
    """
    # 编码
    query_emb = model.encode(query)
    corpus_embs = model.encode(corpus)
    
    # 挖掘
    hard_neg_indices = hard_negative_mining(
        query_emb,
        positive_doc,
        corpus,
        corpus_embs,
        n_hard
    )
    
    return [corpus[i] for i in hard_neg_indices]

# 时间复杂度: O(n * d) - n为候选数，d为维度
# 空间复杂度: O(n)
```

### 3.3 Knowledge Distillation 算法

```python
def distillation_loss(
    student_scores: torch.Tensor,
    teacher_scores: torch.Tensor,
    temperature: float = 2.0,
    alpha: float = 0.5
) -> torch.Tensor:
    """
    知识蒸馏损失
    
    从大模型(teacher)蒸馏到小模型(student)
    
    损失 = α * KL(teacher, student) + (1-α) * task_loss
    """
    # KL 散度
    teacher_probs = F.softmax(teacher_scores / temperature, dim=-1)
    student_log_probs = F.log_softmax(student_scores / temperature, dim=-1)
    
    kl_loss = F.kl_div(
        student_log_probs,
        teacher_probs,
        reduction='batchmean'
    ) * (temperature ** 2)
    
    return kl_loss

def train_with_distillation(
    student_model: SentenceTransformer,
    teacher_model: SentenceTransformer,
    train_data: List[InputExample],
    alpha: float = 0.5,
    temperature: float = 2.0
):
    """使用知识蒸馏训练"""
    
    for batch in train_data:
        queries, docs = batch
        
        # Teacher 预测
        with torch.no_grad():
            teacher_scores = teacher_model.predict(queries, docs)
        
        # Student 预测
        student_scores = student_model.predict(queries, docs)
        
        # 计算损失
        loss = distillation_loss(
            student_scores,
            teacher_scores,
            temperature,
            alpha
        )
        
        # 反向传播
        loss.backward()

# 效果: 通常能达到 teacher 的 95%+ 性能，但参数量减少 10x
```

### 3.4 Query Expansion 算法

```python
def query_expansion_with_pseudo_relevance_feedback(
    query: str,
    initial_results: List[str],
    model: SentenceTransformer,
    top_k: int = 3,
    expansion_terms: int = 5
) -> str:
    """
    查询扩展 - 伪相关反馈
    
    算法:
    1. 用原始查询检索
    2. 假设 top-k 结果是相关的
    3. 从中提取关键词扩展查询
    """
    # 1. 取 top-k 结果
    top_docs = initial_results[:top_k]
    
    # 2. 提取关键词 (简化: 使用 TF-IDF)
    from sklearn.feature_extraction.text import TfidfVectorizer
    
    vectorizer = TfidfVectorizer(max_features=expansion_terms)
    tfidf_matrix = vectorizer.fit_transform(top_docs)
    
    # 获取高权重词
    feature_names = vectorizer.get_feature_names_out()
    scores = tfidf_matrix.sum(axis=0).A1
    top_term_indices = scores.argsort()[::-1][:expansion_terms]
    
    expansion_terms_list = [feature_names[i] for i in top_term_indices]
    
    # 3. 扩展查询
    expanded_query = query + " " + " ".join(expansion_terms_list)
    
    return expanded_query

def query_expansion_with_llm(
    query: str,
    llm,
    num_variations: int = 3
) -> List[str]:
    """
    使用 LLM 生成查询变体
    
    生成同义查询以提高召回
    """
    prompt = f"""
Given the query: "{query}"

Generate {num_variations} alternative phrasings that mean the same thing:

1.
2.
3.
"""
    
    response = llm.complete(prompt)
    variations = parse_variations(response)
    
    return [query] + variations

# 时间复杂度: O(k * d) - k为top文档数
# 空间复杂度: O(v) - v为词汇表大小
```

### 3.5 Reciprocal Rank Fusion for Reranking

```python
def reciprocal_rank_fusion_rerank(
    query: str,
    documents: List[str],
    rankers: List[Callable],
    k: int = 60
) -> List[Tuple[str, float]]:
    """
    倒数排名融合 - 多个排序器的结果融合
    
    适用于: 结合多个reranker的结果
    
    公式: RRF(d) = Σ 1/(k + rank_i(d))
    """
    # 获取每个ranker的排序
    all_rankings = []
    
    for ranker in rankers:
        scores = ranker(query, documents)
        ranking = np.argsort(scores)[::-1]
        all_rankings.append(ranking)
    
    # 计算 RRF 分数
    rrf_scores = {}
    
    for ranking in all_rankings:
        for rank, doc_idx in enumerate(ranking):
            if doc_idx not in rrf_scores:
                rrf_scores[doc_idx] = 0
            
            rrf_scores[doc_idx] += 1.0 / (k + rank + 1)
    
    # 排序
    sorted_indices = sorted(
        rrf_scores.keys(),
        key=lambda x: rrf_scores[x],
        reverse=True
    )
    
    results = [
        (documents[idx], rrf_scores[idx])
        for idx in sorted_indices
    ]
    
    return results

# 使用多个reranker
rankers = [
    lambda q, docs: cross_encoder1.predict([[q, d] for d in docs]),
    lambda q, docs: cross_encoder2.predict([[q, d] for d in docs]),
    lambda q, docs: bm25_scores(q, docs)
]

results = reciprocal_rank_fusion_rerank(query, documents, rankers)

# 时间复杂度: O(r * n) - r个ranker，n个文档
# 空间复杂度: O(n)
```

---

## 4. 设计模式

### 4.1 策略模式 (Strategy) - Reranking 策略

```python
from abc import ABC, abstractmethod

class RerankStrategy(ABC):
    @abstractmethod
    def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: int
    ) -> List[Tuple[str, float]]:
        pass

class CrossEncoderStrategy(RerankStrategy):
    """Cross-Encoder 重排序"""
    def __init__(self, model_name: str):
        self.model = CrossEncoder(model_name)
    
    def rerank(self, query, documents, top_k):
        pairs = [[query, doc] for doc in documents]
        scores = self.model.predict(pairs)
        
        sorted_indices = np.argsort(scores)[::-1][:top_k]
        return [(documents[i], scores[i]) for i in sorted_indices]

class BiEncoderStrategy(RerankStrategy):
    """Bi-Encoder 重排序"""
    def __init__(self, model_name: str):
        self.model = SentenceTransformer(model_name)
    
    def rerank(self, query, documents, top_k):
        query_emb = self.model.encode(query)
        doc_embs = self.model.encode(documents)
        
        scores = cosine_similarity([query_emb], doc_embs)[0]
        
        sorted_indices = np.argsort(scores)[::-1][:top_k]
        return [(documents[i], scores[i]) for i in sorted_indices]

class EnsembleStrategy(RerankStrategy):
    """集成多个reranker"""
    def __init__(self, strategies: List[RerankStrategy], weights: List[float]):
        self.strategies = strategies
        self.weights = weights
    
    def rerank(self, query, documents, top_k):
        # 获取所有策略的分数
        all_scores = []
        
        for strategy in self.strategies:
            results = strategy.rerank(query, documents, len(documents))
            scores = {doc: score for doc, score in results}
            all_scores.append(scores)
        
        # 加权平均
        final_scores = {}
        for doc in documents:
            final_scores[doc] = sum(
                w * scores.get(doc, 0)
                for w, scores in zip(self.weights, all_scores)
            )
        
        sorted_docs = sorted(
            final_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_k]
        
        return sorted_docs
```

### 4.2 装饰器模式 (Decorator) - 缓存和日志

```python
class RerankDecorator:
    """Rerank 装饰器基类"""
    def __init__(self, reranker):
        self.reranker = reranker
    
    def rerank(self, query, documents, top_k):
        return self.reranker.rerank(query, documents, top_k)

class CachedReranker(RerankDecorator):
    """带缓存的 Reranker"""
    def __init__(self, reranker):
        super().__init__(reranker)
        self.cache = {}
    
    def rerank(self, query, documents, top_k):
        cache_key = (query, tuple(documents), top_k)
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        result = self.reranker.rerank(query, documents, top_k)
        self.cache[cache_key] = result
        
        return result

class LoggedReranker(RerankDecorator):
    """带日志的 Reranker"""
    def rerank(self, query, documents, top_k):
        import time
        start = time.time()
        
        result = self.reranker.rerank(query, documents, top_k)
        
        duration = time.time() - start
        logging.info(f"Reranked {len(documents)} docs in {duration:.2f}s")
        
        return result

# 使用
reranker = CrossEncoderStrategy('ms-marco-MiniLM-L-6-v2')
reranker = CachedReranker(reranker)
reranker = LoggedReranker(reranker)
```

### 4.3 工厂模式 (Factory) - 模型工厂

```python
class SentenceTransformerFactory:
    """Sentence-Transformer 工厂"""
    
    # 预定义配置
    MODELS = {
        "fast": "all-MiniLM-L6-v2",
        "balanced": "all-mpnet-base-v2",
        "multilingual": "paraphrase-multilingual-mpnet-base-v2",
        "best": "all-roberta-large-v1"
    }
    
    RERANKERS = {
        "fast": "cross-encoder/ms-marco-TinyBERT-L-2-v2",
        "balanced": "cross-encoder/ms-marco-MiniLM-L-6-v2",
        "best": "cross-encoder/ms-marco-electra-base"
    }
    
    @staticmethod
    def create_encoder(preset: str = "balanced", **kwargs):
        """创建编码器"""
        model_name = SentenceTransformerFactory.MODELS.get(preset, preset)
        return SentenceTransformer(model_name, **kwargs)
    
    @staticmethod
    def create_reranker(preset: str = "balanced", **kwargs):
        """创建重排器"""
        model_name = SentenceTransformerFactory.RERANKERS.get(preset, preset)
        return CrossEncoder(model_name, **kwargs)
    
    @staticmethod
    def create_two_stage(
        encoder_preset: str = "fast",
        reranker_preset: str = "balanced"
    ):
        """创建两阶段检索器"""
        return TwoStageRetriever(
            bi_encoder_name=SentenceTransformerFactory.MODELS[encoder_preset],
            cross_encoder_name=SentenceTransformerFactory.RERANKERS[reranker_preset]
        )

# 使用
encoder = SentenceTransformerFactory.create_encoder("fast")
reranker = SentenceTransformerFactory.create_reranker("best")
```

### 4.4 模板方法模式 (Template Method) - 训练流程

```python
class TrainingPipeline(ABC):
    """训练流程模板"""
    
    def train(self, train_data, val_data):
        """模板方法"""
        # 1. 准备数据
        train_loader = self.prepare_data(train_data)
        
        # 2. 设置模型
        model = self.setup_model()
        
        # 3. 设置损失函数
        loss_fn = self.setup_loss()
        
        # 4. 训练循环
        for epoch in range(self.num_epochs):
            # 训练
            self.train_epoch(model, train_loader, loss_fn)
            
            # 验证
            metrics = self.validate(model, val_data)
            
            # 日志
            self.log_metrics(epoch, metrics)
            
            # 早停
            if self.should_stop(metrics):
                break
        
        # 5. 保存
        self.save_model(model)
    
    @abstractmethod
    def prepare_data(self, data):
        pass
    
    @abstractmethod
    def setup_model(self):
        pass
    
    @abstractmethod
    def setup_loss(self):
        pass
    
    def train_epoch(self, model, loader, loss_fn):
        """默认训练epoch"""
        model.fit(train_objectives=[(loader, loss_fn)], epochs=1)
    
    def validate(self, model, val_data):
        """默认验证"""
        return {}
    
    def should_stop(self, metrics):
        """早停判断"""
        return False

class ContrastiveLearningPipeline(TrainingPipeline):
    """对比学习训练流程"""
    
    def setup_loss(self):
        return losses.MultipleNegativesRankingLoss(self.model)
```

### 4.5 观察者模式 (Observer) - 训练监控

```python
class TrainingObserver(ABC):
    @abstractmethod
    def on_epoch_end(self, epoch: int, metrics: Dict):
        pass

class TensorBoardObserver(TrainingObserver):
    """TensorBoard 记录"""
    def __init__(self, log_dir: str):
        from torch.utils.tensorboard import SummaryWriter
        self.writer = SummaryWriter(log_dir)
    
    def on_epoch_end(self, epoch, metrics):
        for key, value in metrics.items():
            self.writer.add_scalar(key, value, epoch)

class WandbObserver(TrainingObserver):
    """Weights & Biases 记录"""
    def __init__(self, project: str):
        import wandb
        wandb.init(project=project)
    
    def on_epoch_end(self, epoch, metrics):
        wandb.log(metrics, step=epoch)

class MonitoredTraining:
    """带监控的训练"""
    def __init__(self):
        self.observers = []
    
    def add_observer(self, observer: TrainingObserver):
        self.observers.append(observer)
    
    def train_with_monitoring(self, model, data):
        for epoch in range(num_epochs):
            # 训练...
            metrics = evaluate(model, val_data)
            
            # 通知观察者
            for obs in self.observers:
                obs.on_epoch_end(epoch, metrics)
```

---

## 5. 可复用组件

### 5.1 核心组件清单

| 组件 | 功能 | 复用优先级 |
|------|------|-----------|
| Two-Stage Retrieval | Bi+Cross两阶段 | ⭐⭐⭐⭐⭐ |
| Cross-Encoder Reranking | 精确重排序 | ⭐⭐⭐⭐⭐ |
| Contrastive Learning | 对比学习训练 | ⭐⭐⭐⭐⭐ |
| Hard Negative Mining | 难负样本挖掘 | ⭐⭐⭐⭐⭐ |
| Knowledge Distillation | 模型蒸馏 | ⭐⭐⭐⭐ |
| Query Expansion | 查询扩展 | ⭐⭐⭐⭐ |
| RRF Reranking | 多排序器融合 | ⭐⭐⭐⭐⭐ |
| Ensemble Reranker | 集成重排序 | ⭐⭐⭐⭐ |
| Cached Reranker | 缓存优化 | ⭐⭐⭐⭐⭐ |
| Model Factory | 模型工厂 | ⭐⭐⭐⭐ |

---

## 6. 核心学习

### 关键概念
1. **两阶段检索** - Bi-Encoder召回 + Cross-Encoder精排
2. **对比学习** - InfoNCE损失
3. **难负样本** - 提升模型区分能力
4. **知识蒸馏** - 大模型→小模型
5. **查询扩展** - 提升召回率

### 核心算法
1. Contrastive Learning (InfoNCE)
2. Hard Negative Mining
3. Knowledge Distillation
4. Query Expansion (PRF)
5. Reciprocal Rank Fusion

### 对 FieldMind 的价值
- ⭐⭐⭐⭐⭐ 两阶段检索架构
- ⭐⭐⭐⭐⭐ Cross-Encoder重排序
- ⭐⭐⭐⭐⭐ 对比学习训练
- ⭐⭐⭐⭐ 难负样本挖掘
- ⭐⭐⭐⭐⭐ RRF多排序融合

---

**分析完成时间**: 2026-08-30  
**已完成插件数**: 18/40 (45%)  
**下一个插件**: LlamaIndex Advanced RAG
