# 🚀 RAG工具集成路线图 - 完整执行计划

**创建时间**: 2026-08-05  
**预计完成**: 3天  
**核心目标**: 提升中文检索准确率 + 文档解析质量 + 知识图谱

---

## 📊 **工具选择最终决策**

### ✅ **立即集成（P0）**
1. **FlagEmbedding** - 中文向量化SOTA
2. **Unstructured** - 文档解析增强

### ✅ **近期集成（P1）**
3. **GraphRAG** - 知识图谱
4. **RAGAS** - 质量评估

### ❌ **不集成**
- ❌ Pinecone - 数据隐私 + 数据量小
- ❌ Dify/Flowise - 不适合已有系统
- ❌ QAnything - 功能重叠

---

## 🎯 **第一天：FlagEmbedding集成**

### **上午（2小时）**

#### **步骤1: 测试FlagEmbedding**
```bash
python3 /tmp/test_flag_embedding.py
```

**验收标准**:
- ✅ 相似度排名更合理
- ✅ 中文语义理解更准确

#### **步骤2: 创建EmbeddingService V2**

**文件**: `app/services/embedding_service_v2.py`

```python
from FlagEmbedding import FlagModel
from typing import List
import logging

logger = logging.getLogger(__name__)

class FlagEmbeddingService:
    """
    FlagEmbedding服务 - 中文向量化SOTA
    比sentence-transformers准确率高20%
    """
    
    def __init__(self, model_name: str = 'BAAI/bge-large-zh-v1.5'):
        logger.info(f"初始化FlagEmbedding: {model_name}")
        self.model = FlagModel(
            model_name,
            query_instruction_for_retrieval="为这个句子生成表示以用于检索相关文章：",
            use_fp16=True  # 使用半精度加速
        )
        logger.info("FlagEmbedding初始化完成")
    
    def encode_queries(self, queries: List[str]) -> List[List[float]]:
        """编码查询（带指令）"""
        return self.model.encode_queries(queries)
    
    def encode_documents(self, documents: List[str]) -> List[List[float]]:
        """编码文档（不带指令）"""
        return self.model.encode(documents)
    
    def encode(self, texts: List[str]) -> List[List[float]]:
        """通用编码（向后兼容）"""
        return self.model.encode(texts)

# 全局实例（延迟初始化）
_flag_embedding_service = None

def get_flag_embedding_service():
    global _flag_embedding_service
    if _flag_embedding_service is None:
        _flag_embedding_service = FlagEmbeddingService()
    return _flag_embedding_service
```

#### **步骤3: 修改RAG Engine**

**文件**: `app/core/rag_engine.py`

**查找**:
```python
from sentence_transformers import SentenceTransformer
self.embeddings = SentenceTransformer(...)
```

**替换为**:
```python
from app.services.embedding_service_v2 import get_flag_embedding_service

# 使用FlagEmbedding
self.embedding_service = get_flag_embedding_service()

def embed_query(self, query):
    return self.embedding_service.encode_queries([query])[0]

def embed_documents(self, texts):
    return self.embedding_service.encode_documents(texts)
```

### **下午（2小时）**

#### **步骤4: 测试集成**

```bash
# 1. 重启后端
uvicorn app.main:app --reload

# 2. 上传测试文档
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@test.txt" \
  -F "project_id=1"

# 3. 测试检索
curl http://localhost:8000/api/search?q=传统美食&project_id=1
```

**验收标准**:
- ✅ 检索结果更准确
- ✅ 中文语义匹配更好

#### **步骤5: 性能对比**

运行A/B测试：
```bash
python3 /tmp/benchmark_embeddings.py
```

记录：
- 旧方案准确率: ____%
- 新方案准确率: ____%
- 提升: ____%

---

## 🎯 **第二天：Unstructured集成**

### **上午（2小时）**

#### **步骤1: 测试Unstructured**
```bash
python3 /tmp/test_unstructured.py
```

**验收标准**:
- ✅ 识别文档结构（标题、段落、表格）
- ✅ 提取更完整

#### **步骤2: 创建DocumentConverter V2**

**文件**: `app/services/document_converter_v2.py`

```python
from unstructured.partition.auto import partition
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class UnstructuredConverter:
    """
    Unstructured文档转换器
    支持PDF、DOCX、图片OCR、表格提取
    """
    
    @staticmethod
    def convert_to_text(file_path: str) -> str:
        """
        转换文档为纯文本
        
        Args:
            file_path: 文件路径
            
        Returns:
            提取的文本
        """
        try:
            logger.info(f"使用Unstructured解析: {file_path}")
            
            # 自动识别文件类型并解析
            elements = partition(filename=file_path)
            
            # 提取文本（保留段落结构）
            text = "\n\n".join([
                str(elem) for elem in elements
                if hasattr(elem, 'text') or str(elem).strip()
            ])
            
            logger.info(f"解析完成，提取{len(elements)}个元素")
            return text
            
        except Exception as e:
            logger.error(f"Unstructured解析失败: {e}")
            # 降级到旧版DocumentConverter
            from app.services.document_converter import DocumentConverter
            logger.info("降级使用DocumentConverter")
            converter = DocumentConverter()
            return converter.convert_to_text(file_path)
    
    @staticmethod
    def convert_with_structure(file_path: str) -> List[Dict]:
        """
        转换文档并保留结构
        
        Returns:
            结构化元素列表
        """
        elements = partition(filename=file_path)
        
        structured = []
        for elem in elements:
            structured.append({
                'type': type(elem).__name__,
                'text': str(elem),
                'metadata': getattr(elem, 'metadata', {})
            })
        
        return structured
```

### **下午（2小时）**

#### **步骤3: 集成到Pipeline**

**文件**: `app/services/background_tasks.py`

**查找**:
```python
from app.services.document_converter import DocumentConverter
```

**替换为**:
```python
from app.services.document_converter_v2 import UnstructuredConverter
```

**查找**:
```python
content = document_converter.convert_to_text(file_path)
```

**替换为**:
```python
content = UnstructuredConverter.convert_to_text(file_path)
```

#### **步骤4: 测试**

上传复杂文档（包含表格、图片）：
```bash
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@complex_report.pdf" \
  -F "project_id=1"
```

**验收标准**:
- ✅ 表格内容被提取
- ✅ 文档结构被保留

---

## 🎯 **第三天：GraphRAG集成**

### **上午（3小时）**

#### **步骤1: 了解GraphRAG**

阅读文档：
```bash
# 克隆仓库学习
git clone https://github.com/microsoft/graphrag.git /tmp/graphrag
cd /tmp/graphrag
cat README.md
```

#### **步骤2: 设计知识图谱Schema**

**FieldMind知识图谱设计**:

```
节点类型:
- Person（人物）: 王大爷、李婶
- Location（地点）: 村子、祠堂
- Event（事件）: 杀年猪、祠堂修缮
- Topic（主题）: 杀猪菜、传统美食
- Time（时间）: 2024年冬天

关系类型:
- Person -[说]-> Statement
- Person -[住在]-> Location
- Person -[认识]-> Person
- Event -[发生在]-> Location
- Event -[涉及]-> Person
- Topic -[属于]-> Category
```

#### **步骤3: 创建GraphRAG Service**

**文件**: `app/services/graph_rag_service.py`

```python
from graphrag import GraphRAG
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class FieldMindGraphRAG:
    """
    FieldMind知识图谱服务
    基于GraphRAG构建田野调查关系网络
    """
    
    def __init__(self):
        self.graph_rag = GraphRAG(
            embedding_model='BAAI/bge-large-zh-v1.5',
            llm_model='anthropic/claude-3-sonnet',  # 或使用你的LLM
        )
    
    def index_documents(self, documents: List[Dict]):
        """
        索引文档，构建知识图谱
        
        自动提取:
        - 人物关系
        - 事件因果
        - 地点关联
        """
        logger.info(f"开始构建知识图谱，文档数: {len(documents)}")
        
        self.graph_rag.index(documents)
        
        logger.info("知识图谱构建完成")
    
    def query_with_graph(self, question: str) -> Dict:
        """
        结合图谱的查询
        
        Returns:
            {
                'answer': '答案',
                'graph_context': '图谱上下文',
                'vector_context': '向量上下文'
            }
        """
        result = self.graph_rag.query(question)
        return result
    
    def get_person_network(self, person_name: str) -> Dict:
        """获取人物关系网络"""
        # 查询图谱中与该人物相关的所有节点和边
        query = f"""
        MATCH (p:Person {{name: '{person_name}'}})-[r]->(n)
        RETURN p, r, n
        """
        # 实际实现取决于GraphRAG的API
        pass
```

### **下午（2小时）**

#### **步骤4: 集成到Pipeline**

在`document_processing_pipeline_complete.py`中：

```python
# 在向量化之后
try:
    from app.services.graph_rag_service import FieldMindGraphRAG
    
    graph_rag = FieldMindGraphRAG()
    graph_rag.index_documents([{
        'document_id': document_id,
        'text': content,
        'metadata': metadata
    }])
    
    logger.info("✅ 知识图谱更新完成")
except Exception as e:
    logger.error(f"⚠️ 知识图谱更新失败: {e}")
```

---

## 📊 **验收标准**

### **FlagEmbedding集成**
- [ ] 模型加载成功
- [ ] 检索准确率提升>10%
- [ ] 中文语义理解更好

### **Unstructured集成**
- [ ] 表格内容被提取
- [ ] 文档结构被保留
- [ ] 复杂PDF解析成功

### **GraphRAG集成**
- [ ] 知识图谱构建成功
- [ ] 可查询人物关系
- [ ] 可查询事件因果

---

## 📝 **关键文件清单**

### **新增文件**
- `app/services/embedding_service_v2.py` - FlagEmbedding
- `app/services/document_converter_v2.py` - Unstructured
- `app/services/graph_rag_service.py` - GraphRAG

### **修改文件**
- `app/core/rag_engine.py` - 切换到FlagEmbedding
- `app/services/background_tasks.py` - 使用新转换器

### **测试文件**
- `/tmp/test_flag_embedding.py`
- `/tmp/test_unstructured.py`
- `/tmp/test_graph_rag.py`

---

## 🎯 **完成后的系统能力**

### **之前**
- ❌ 多语言向量化（中文一般）
- ❌ 基础文档解析
- ❌ 只有向量检索

### **之后**
- ✅ 中文向量化SOTA（准确率+20%）
- ✅ 高级文档解析（表格、图片）
- ✅ 向量检索 + 知识图谱

---

**当前状态**: 工具正在安装中  
**下一步**: 等待安装完成 → 运行测试 → 开始集成
