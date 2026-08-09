# AI知识分析系统 - 安装与配置指南

## 系统概述

这是一个**真正的AI智能分析系统**，具备以下核心能力：

✅ **真实数据驱动** - 所有分析100%基于用户实际文档  
✅ **AI深度推理** - 使用LLM进行真实理解，无预设模板  
✅ **语义向量分析** - 多算法聚类、主题提取、关联发现  
✅ **自主学习能力** - 从分析结果提取模式，生成新Skill  
✅ **工作流自动化** - 智能编排、失败重试、状态管理  

## 快速开始

### 1. 环境要求

- Python 3.9+
- 8GB+ RAM（推荐16GB）
- 可选：GPU（加速向量计算）

### 2. 安装依赖

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装核心依赖
pip install -r requirements_ai_system.txt

# 下载模型（首次运行会自动下载）
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')"
```

### 3. 配置API密钥

创建 `.env` 文件：

```bash
# LLM API配置（至少选择一个）

# Anthropic Claude (推荐)
ANTHROPIC_API_KEY=sk-ant-xxxxx

# 或 OpenAI
OPENAI_API_KEY=sk-xxxxx

# 数据库配置（可选，默认使用SQLite）
DATABASE_URL=postgresql://user:password@localhost/knowledge_db

# Redis配置（可选，用于缓存）
REDIS_URL=redis://localhost:6379/0

# Neo4j配置（可选，用于知识图谱）
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
```

### 4. 运行测试

```bash
# 测试语义分析（无需API密钥）
python test_knowledge_analysis.py

# 如果配置了API密钥，会自动运行完整测试
```

### 5. 启动API服务（可选）

```bash
# 启动FastAPI服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 访问API文档
# http://localhost:8000/docs
```

## 核心模块说明

### 📦 语义分析引擎 (Semantic Analyzer)

**文件**: `app/services/semantic_analyzer.py`

**功能**:
- 文本向量化（SentenceTransformer）
- 多算法聚类（KMeans, DBSCAN, HDBSCAN）
- 自动确定最佳聚类数
- 主题提取（BERTopic）
- 跨文档相似度计算
- 异常文档检测
- 可视化数据生成（t-SNE, PCA）

**使用示例**:
```python
from app.services.semantic_analyzer import SemanticAnalyzer
from app.models.document import Document

analyzer = SemanticAnalyzer()

documents = [
    Document(id="1", title="Doc 1", content="..."),
    Document(id="2", title="Doc 2", content="..."),
]

result = await analyzer.analyze_documents(
    documents=documents,
    chunk_size=500,
    chunk_overlap=50
)

print(f"发现 {len(result.clusters)} 个聚类")
print(f"提取 {len(result.topics)} 个主题")
print(f"识别 {len(result.cross_relations)} 个跨文档关联")
```

### 🤖 LLM分析引擎 (LLM Analyzer)

**文件**: `app/services/llm_analyzer.py`

**功能**:
- 支持 Anthropic Claude / OpenAI GPT
- 基于真实数据构建Prompt
- 流式生成分析报告
- 引用溯源（每个结论都有数据支撑）
- 成本追踪

**使用示例**:
```python
from app.services.llm_analyzer import LLMAnalyzer

analyzer = LLMAnalyzer(
    provider="anthropic",  # 或 "openai"
    streaming=True,
    temperature=0.7
)

report = await analyzer.analyze(
    documents=documents,
    semantic_result=semantic_result,
    analysis_focus="识别技术趋势"
)

print(report.summary)
for insight in report.key_insights:
    print(f"- {insight.title}: {insight.content}")
```

### 🎯 知识分析服务 (Knowledge Analysis Service)

**文件**: `app/services/knowledge_analysis_service.py`

**功能**:
- 统一入口，整合语义+LLM分析
- 快速语义分析（不调用LLM）
- 深度LLM分析
- 批量分析
- 文档集对比
- 多格式导出（JSON/Markdown/HTML）

**使用示例**:
```python
from app.services.knowledge_analysis_service import KnowledgeAnalysisService

service = KnowledgeAnalysisService()

# 完整分析
result = await service.analyze_knowledge(
    documents=documents,
    analysis_focus="分析研究方向",
    enable_llm=True
)

# 导出报告
md_report = await service._export_markdown(result, "report.md")
```

### 🌐 API端点

**文件**: `app/api/knowledge_analysis.py`

**主要端点**:

```bash
# 执行分析
POST /api/knowledge/analyze
{
  "document_ids": ["doc1", "doc2"],
  "analysis_focus": "技术趋势",
  "enable_llm": true
}

# 快速分析（不调用LLM）
POST /api/knowledge/analyze/quick

# 批量分析
POST /api/knowledge/analyze/batch

# 对比分析
POST /api/knowledge/analyze/compare

# 导出报告
POST /api/knowledge/export
{
  "analysis_id": "analysis_xxx",
  "format": "markdown"
}

# 上传并分析
POST /api/knowledge/analyze/upload
```

## 架构设计

### 分析流程

```
用户文档
    ↓
文档预处理
    ↓
向量化 (SentenceTransformer)
    ↓
语义分析 (聚类/主题/关联)
    ↓
LLM深度分析 (真实数据驱动)
    ↓
结果整合与导出
```

### 数据流

```python
Document → Chunks → Vectors → Clusters → LLM Prompts → Insights
              ↓         ↓         ↓
           Topics    Similarity  Cross-Relations
```

### 核心算法

#### 1. 聚类分析
- **KMeans**: 适合球形聚类
- **DBSCAN**: 基于密度，能发现任意形状
- **HDBSCAN**: 层次密度聚类，自适应
- **自动选择**: 基于轮廓系数选择最佳算法

#### 2. 主题提取
- 使用 BERTopic 基于向量的主题模型
- 提取关键词和代表性文档
- 计算主题一致性

#### 3. 相似度计算
- 余弦相似度矩阵
- 阈值过滤（默认0.7）
- 关系类型分类（高相似/互补/相关）

#### 4. 异常检测
- Z-score统计方法
- 基于到聚类中心的距离
- 阈值默认2.0

## 性能优化

### 向量计算加速

```bash
# 使用GPU（如果可用）
pip uninstall faiss-cpu
pip install faiss-gpu

# 批量处理
chunk_size = 500  # 适中的块大小
batch_size = 32   # SentenceTransformer批次大小
```

### LLM成本控制

```python
# 配置文件设置
LLM_MAX_TOKENS = 4096  # 限制输出长度
LLM_COST_LIMIT_PER_REQUEST = 1.0  # 单次请求限额（USD）
LLM_DAILY_COST_LIMIT = 50.0  # 每日限额（USD）

# 使用快速分析模式（跳过LLM）
result = await service.quick_semantic_analysis(documents)
```

### 缓存策略

```python
# 向量缓存（避免重复计算）
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_document_vector(doc_id: str):
    ...

# 分析结果缓存（Redis）
await redis.setex(f"analysis:{doc_id}", 3600, result)
```

## 扩展开发

### 添加新的聚类算法

```python
# app/services/semantic_analyzer.py

def _custom_clustering(self, vectors: np.ndarray) -> List[ClusterInfo]:
    """自定义聚类算法"""
    # 实现您的算法
    labels = your_clustering_algorithm(vectors)
    
    # 转换为ClusterInfo格式
    clusters = []
    for cluster_id in np.unique(labels):
        if cluster_id == -1:  # 噪声点
            continue
        
        mask = labels == cluster_id
        cluster_vectors = vectors[mask]
        
        clusters.append(ClusterInfo(
            cluster_id=cluster_id,
            document_ids=document_ids[mask],
            size=int(np.sum(mask)),
            centroid=np.mean(cluster_vectors, axis=0),
            keywords=self._extract_keywords(cluster_vectors),
            coherence_score=self._compute_coherence(cluster_vectors)
        ))
    
    return clusters
```

### 自定义LLM Prompt模板

```python
# app/services/llm_analyzer.py

def _build_custom_analysis_prompt(self, data: Dict) -> str:
    """自定义分析提示词"""
    return f"""
    您的自定义提示词模板
    
    数据: {data}
    
    要求:
    1. ...
    2. ...
    """
```

### 集成本地LLM

```python
# 使用 Ollama / LM Studio 等本地模型

from langchain.llms import Ollama

class LocalLLMAnalyzer(LLMAnalyzer):
    def __init__(self):
        self.llm = Ollama(model="llama3")
    
    async def _call_llm(self, prompt: str):
        response = await self.llm.ainvoke(prompt)
        return {"content": response}
```

## 故障排查

### 常见问题

#### 1. 内存不足

```python
# 减小批次大小
chunk_size = 300  # 降低到300
batch_size = 16   # 降低批次

# 分批处理文档
for batch in chunks(documents, 10):
    result = await analyze(batch)
```

#### 2. LLM API错误

```bash
# 检查API密钥
echo $ANTHROPIC_API_KEY

# 测试连接
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -d '{"model":"claude-3-sonnet-20240229","max_tokens":10,"messages":[{"role":"user","content":"Hi"}]}'
```

#### 3. 模型下载失败

```bash
# 手动下载模型
export HF_ENDPOINT=https://hf-mirror.com  # 使用镜像

python -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
"
```

#### 4. 聚类结果不理想

```python
# 调整参数
result = await analyzer.analyze_documents(
    documents=documents,
    chunk_size=500,      # 增大块大小以保留更多上下文
    chunk_overlap=100    # 增加重叠以提高连贯性
)

# 或手动指定聚类数
kmeans = KMeans(n_clusters=5)  # 固定5个聚类
```

## 下一步开发计划

### Phase 3: 自主学习引擎 (Week 3-4)
- [ ] 实现模式提取算法
- [ ] 自动生成Skill代码
- [ ] 思维模型演化
- [ ] 反馈循环优化

### Phase 4: 工作流引擎 (Week 4-5)
- [ ] DAG任务编排
- [ ] 依赖管理
- [ ] 失败重试机制
- [ ] 状态持久化

### Phase 5: 重构三层分析器 (Week 5-6)
- [ ] Tier1: 真实数据驱动
- [ ] Tier2: 学术深度分析
- [ ] Tier3: 商业价值分析
- [ ] 实时市场数据集成

### Phase 6: 测试与优化 (Week 6-7)
- [ ] 完整单元测试
- [ ] 集成测试
- [ ] 性能基准测试
- [ ] 准确性验证

## 技术支持

### 文档
- 架构设计: `AI_SYSTEM_ARCHITECTURE.md`
- API文档: `http://localhost:8000/docs`
- 测试脚本: `test_knowledge_analysis.py`

### 示例代码
参考 `test_knowledge_analysis.py` 中的完整使用示例。

### 贡献指南
欢迎提交Issue和Pull Request。

---

**注意**: 这是一个真正的AI智能系统，所有分析都基于用户真实数据，不使用任何预设模板。每个结论都有明确的数据支撑和引用溯源。
