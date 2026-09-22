# FieldMind 集成功能使用指南

## 后端新功能使用

### 1. API 网关

API 网关已自动启用，所有请求会经过限流和监控。

**查看 API 统计**：
```bash
curl http://localhost:8000/api/v1/api-management/stats
```

**查看 API 指标**：
```bash
curl http://localhost:8000/api/v1/api-management/metrics
```

**查看请求日志**：
```bash
curl http://localhost:8000/api/v1/api-management/logs
```

### 2. 知识图谱增强

在代码中使用：

```python
from app.services.knowledge_graph_enhanced import knowledge_graph_enhancer

# 提取实体和关系
result = knowledge_graph_enhancer.enhance_document(text)
entities = result["entities"]
relations = result["relations"]
```

### 3. 高级知识图谱

```python
from app.services.advanced_knowledge_graph import kg_builder

# 构建知识图谱
result = kg_builder.build_from_text(text)
communities = result["communities"]  # 社区发现
central_nodes = result["central_nodes"]  # 中心节点
```

### 4. DLT 数据管道

```python
from app.services.dlt_pipeline import run_document_pipeline, incremental_update_documents

# 完整处理
result = run_document_pipeline(project_id=1)

# 增量更新
result = incremental_update_documents(project_id=1)
```

### 5. 向量检索

```python
from app.services.vector_index_service import vector_index_service

# 添加文档
vector_index_service.add_documents(
    documents=["文档1", "文档2"],
    vectors=embeddings,  # shape: (n, 768)
    doc_ids=[1, 2]
)

# 搜索
results = vector_index_service.search(query_vector, top_k=5)

# 混合检索
results = vector_index_service.hybrid_search(
    query_text="查询文本",
    query_vector=query_embedding,
    top_k=5
)
```

### 6. 代码审查

```python
from app.services.code_review_service import code_review_service

# 审查单个文件
result = code_review_service.review_file("app/services/example.py")
print(f"分数: {result['score']}")
print(f"问题数: {result['total_issues']}")

# 审查整个项目
result = code_review_service.review_project("app/")
report = code_review_service.generate_report(result)
print(report)
```

### 7. Markitdown 文档转换

```python
from app.services.markitdown_converter import enhanced_converter

# 转换文档
content = enhanced_converter.convert("document.pdf")

# 带元数据
result = enhanced_converter.convert_with_metadata("document.docx")
print(result["content"])
print(result["metadata"])
```

## API 端点清单

### API 管理
- GET `/api/v1/api-management/stats` - 统计信息
- GET `/api/v1/api-management/metrics` - API 指标
- GET `/api/v1/api-management/logs` - 请求日志
- GET `/api/v1/api-management/endpoints` - 端点列表
- GET `/api/v1/api-management/performance` - 性能指标
- GET `/api/v1/api-management/errors` - 错误日志
- POST `/api/v1/api-management/rate-limit/reset` - 重置限流

## 前端使用

### 添加文件到 Xcode

1. 打开 Xcode 项目
2. 拖入以下文件：
   - `FieldMindDesignSystem/*.swift` (3 个)
   - `Components/*.swift` (3 个)
   - `Views/*.swift` (5 个)
3. Build 项目
4. 运行验证

### 使用新组件

```swift
import SwiftUI

struct MyView: View {
    var body: some View {
        VStack {
            // 使用统计卡片
            FMStatCard(
                title: "项目数",
                value: "12",
                trend: 8.3,
                icon: "folder.fill"
            )

            // 使用搜索框
            FMSearchField(
                text: $searchText,
                placeholder: "搜索..."
            )

            // 使用折叠面板
            FMAccordion(
                items: accordionItems,
                allowMultiple: true
            )
        }
    }
}
```

## 性能优化建议

1. **向量检索**：首次使用前需要构建索引
2. **DLT 管道**：适合批量处理，单文档使用原有流程
3. **知识图谱**：大文档（>10000字）使用高级知识图谱
4. **API 网关**：默认限流 100 请求/分钟，可配置

## 故障排查

### 导入错误
```bash
# 检查依赖
pip list | grep -E "dlt|markitdown|spacy|networkx|faiss"

# 重新安装
pip install dlt markitdown spacy networkx scikit-learn
```

### API 网关不生效
检查 `app/main.py` 中间件顺序，API 网关应该在最前面。

### 前端 Build 失败
确保所有文件都添加到了正确的 Target。
