# FieldMind 扎实实施计划

## 实施原则

### 核心理念
> **"慢就是快，稳就是进"**

1. **彻底性** - 不留技术债，不走捷径
2. **稳妥性** - 每一步都经过测试验证
3. **扎实性** - 代码质量优先于速度
4. **可用性** - 每个里程碑都能独立运行

### 质量标准

**每个功能必须满足：**
- ✅ 单元测试覆盖率 > 80%
- ✅ 集成测试通过
- ✅ 代码审查通过
- ✅ 文档完整
- ✅ 性能达标
- ✅ 实际可用

---

## 总体时间规划

**预计总时长：16-20周**

- 阶段0：基础设施准备（2周）
- 阶段1：数据流统一（3周）
- 阶段2：数据治理（3周）
- 阶段3：知识图谱（4周）
- 阶段4：统一查询（3周）
- 阶段5：前端统一（3周）
- 阶段6：测试优化（2周）

---

## 阶段0：基础设施准备（第1-2周）

### 目标
搭建坚实的技术基础设施

### Week 1：开发环境与工具链

#### Day 1-2：数据库设计与初始化

**任务**:
1. 设计完整的数据库Schema
2. 创建迁移脚本
3. 编写种子数据
4. 配置备份策略

**产出**:
```sql
-- backend/src/app/migrations/001_initial_schema.sql
CREATE TABLE documents (...);
CREATE TABLE document_metadata (...);
CREATE TABLE entities (...);
-- ... 所有10个核心表
```

**验收**:
- [ ] 所有表创建成功
- [ ] 索引配置正确
- [ ] 外键约束生效
- [ ] 可以回滚迁移

#### Day 3-4：对象存储配置

**任务**:
1. 部署MinIO或配置S3
2. 创建存储桶（buckets）
3. 配置访问策略
4. 实现文件上传/下载工具类

**产出**:
```python
# backend/src/app/core/storage.py
class ObjectStorage:
    async def upload_file(self, file: UploadFile, bucket: str) -> str
    async def download_file(self, path: str) -> bytes
    async def delete_file(self, path: str) -> bool
    async def get_presigned_url(self, path: str) -> str
```

**验收**:
- [ ] 可以上传文件
- [ ] 可以下载文件
- [ ] 可以生成预签名URL
- [ ] 存储空间监控正常

#### Day 5：向量数据库配置

**任务**:
1. 配置pgvector扩展
2. 创建向量索引
3. 测试向量检索性能
4. 编写向量操作工具类

**产出**:
```python
# backend/src/app/core/vector_store.py
class VectorStore:
    async def add_embedding(self, entity_id: str, vector: List[float]) -> int
    async def search_similar(self, vector: List[float], limit: int) -> List[Match]
    async def delete_embedding(self, entity_id: str) -> bool
```

**验收**:
- [ ] 向量存储功能正常
- [ ] 检索速度 < 100ms
- [ ] 准确率测试通过

### Week 2：核心服务框架

#### Day 1-2：统一响应格式

**任务**:
1. 定义标准响应模型
2. 创建响应包装器
3. 实现错误处理中间件
4. 编写响应序列化器

**产出**:
```python
# backend/src/app/core/response.py
class StandardResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    message: str
    error: Optional[str] = None
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

def success_response(data: Any, message: str = "成功") -> StandardResponse:
    return StandardResponse(success=True, data=data, message=message)

def error_response(error: str, code: str, message: str = "失败") -> StandardResponse:
    return StandardResponse(success=False, error=error, error_code=code, message=message)
```

**验收**:
- [ ] 所有API返回统一格式
- [ ] 错误信息清晰
- [ ] 日志记录完整

#### Day 3-4：日志与监控

**任务**:
1. 配置结构化日志
2. 实现请求追踪
3. 配置性能监控
4. 实现健康检查接口

**产出**:
```python
# backend/src/app/core/logging.py
class StructuredLogger:
    def log_request(self, request_id: str, method: str, path: str)
    def log_processing(self, document_id: str, stage: str, duration: float)
    def log_error(self, error: Exception, context: Dict)

# backend/src/app/api/health.py
@router.get("/health")
async def health_check() -> HealthStatus:
    return {
        "status": "healthy",
        "database": await check_database(),
        "storage": await check_storage(),
        "services": await check_services()
    }
```

**验收**:
- [ ] 日志结构清晰
- [ ] 可以追踪请求链路
- [ ] 性能指标可查询
- [ ] 健康检查正常

#### Day 5：测试框架搭建

**任务**:
1. 配置pytest
2. 编写测试工具类
3. 创建测试数据工厂
4. 实现API测试客户端

**产出**:
```python
# backend/src/tests/conftest.py
@pytest.fixture
async def db_session():
    # 测试数据库会话
    
@pytest.fixture
async def test_client():
    # 测试API客户端
    
@pytest.fixture
def sample_document():
    # 测试文档工厂
```

**验收**:
- [ ] 测试环境独立
- [ ] 测试数据自动清理
- [ ] CI/CD集成完成

---

## 阶段1：数据流统一（第3-5周）

### 目标
建立统一的文件处理管道，所有文件通过单一入口处理

### Week 3：统一上传网关

#### Day 1-2：上传接口实现

**任务**:
1. 创建统一上传API
2. 实现文件验证
3. 实现哈希计算
4. 实现去重检查

**产出**:
```python
# backend/src/app/api/v1/upload.py
@router.post("/upload")
async def upload_file(
    file: UploadFile,
    project_id: int,
    db: Session = Depends(get_db)
) -> StandardResponse:
    """
    统一上传入口
    1. 验证文件（类型、大小、安全）
    2. 计算哈希
    3. 检查重复
    4. 存储到对象存储
    5. 创建Document记录
    6. 触发处理任务
    """
    
    # 1. 验证
    await validate_file(file)
    
    # 2. 计算哈希
    file_hash = await compute_hash(file)
    
    # 3. 去重检查
    existing = await db.query(Document).filter_by(hash=file_hash).first()
    if existing:
        return success_response(
            data={"document_id": existing.id, "duplicate": True},
            message="文件已存在"
        )
    
    # 4. 存储
    file_path = await storage.upload_file(file, bucket="documents")
    
    # 5. 创建记录
    document = Document(
        id=generate_id(),
        project_id=project_id,
        name=file.filename,
        type=detect_type(file),
        file_path=file_path,
        hash=file_hash,
        status="uploaded"
    )
    db.add(document)
    db.commit()
    
    # 6. 触发处理
    await processing_queue.enqueue(document.id)
    
    return success_response(
        data={"document_id": document.id},
        message="上传成功，开始处理"
    )
```

**测试**:
```python
# backend/src/tests/api/test_upload.py
async def test_upload_new_file(test_client, sample_file):
    response = await test_client.post("/api/v1/upload", files={"file": sample_file})
    assert response.status_code == 200
    assert response.json()["success"] == True
    
async def test_upload_duplicate_file(test_client, sample_file):
    # 第一次上传
    await test_client.post("/api/v1/upload", files={"file": sample_file})
    # 第二次上传相同文件
    response = await test_client.post("/api/v1/upload", files={"file": sample_file})
    assert response.json()["data"]["duplicate"] == True
```

**验收**:
- [ ] 可以上传文件
- [ ] 重复文件被识别
- [ ] 文件验证生效
- [ ] 测试覆盖率 > 80%

#### Day 3-4：文件分类器

**任务**:
1. 实现MIME类型检测
2. 实现文件扩展名映射
3. 实现内容嗅探（魔数检测）
4. 创建路由规则

**产出**:
```python
# backend/src/app/services/file_classifier.py
class FileClassifier:
    """文件分类器"""
    
    MIME_TYPE_MAP = {
        "application/pdf": FileType.DOCUMENT,
        "image/jpeg": FileType.IMAGE,
        "audio/mpeg": FileType.AUDIO,
        "video/mp4": FileType.VIDEO,
        "application/vnd.ms-excel": FileType.TABLE,
    }
    
    async def classify(self, file_path: str) -> FileType:
        """
        分类策略：
        1. MIME类型检测
        2. 扩展名匹配
        3. 魔数检测
        """
        
        # 1. MIME类型
        mime_type = await self.detect_mime_type(file_path)
        if mime_type in self.MIME_TYPE_MAP:
            return self.MIME_TYPE_MAP[mime_type]
        
        # 2. 扩展名
        ext = Path(file_path).suffix.lower()
        if ext in self.EXTENSION_MAP:
            return self.EXTENSION_MAP[ext]
        
        # 3. 魔数检测
        magic_type = await self.detect_by_magic_number(file_path)
        if magic_type:
            return magic_type
        
        return FileType.OTHER
    
    async def detect_mime_type(self, file_path: str) -> str:
        # 使用python-magic库
        import magic
        mime = magic.Magic(mime=True)
        return mime.from_file(file_path)
```

**测试**:
```python
async def test_classify_pdf(classifier, sample_pdf):
    file_type = await classifier.classify(sample_pdf)
    assert file_type == FileType.DOCUMENT

async def test_classify_jpg(classifier, sample_jpg):
    file_type = await classifier.classify(sample_jpg)
    assert file_type == FileType.IMAGE
```

**验收**:
- [ ] 识别准确率 > 95%
- [ ] 支持所有常见格式
- [ ] 测试覆盖率 > 90%

#### Day 5：处理任务队列

**任务**:
1. 配置Celery或RQ
2. 实现任务调度器
3. 实现任务状态追踪
4. 实现失败重试机制

**产出**:
```python
# backend/src/app/services/task_queue.py
class ProcessingQueue:
    """处理任务队列"""
    
    async def enqueue(self, document_id: str, priority: int = 0):
        """将文档加入处理队列"""
        task = process_document.apply_async(
            args=[document_id],
            priority=priority
        )
        await self.db.update_document_status(document_id, "queued", task_id=task.id)
        return task.id
    
    async def get_status(self, task_id: str) -> TaskStatus:
        """查询任务状态"""
        task = AsyncResult(task_id)
        return {
            "task_id": task_id,
            "state": task.state,
            "progress": task.info.get("progress", 0) if task.info else 0
        }

# backend/src/app/workers/document_processor.py
@celery_app.task(bind=True, max_retries=3)
def process_document(self, document_id: str):
    """处理文档任务"""
    try:
        # 1. 加载文档
        document = db.query(Document).get(document_id)
        
        # 2. 分类
        file_type = classifier.classify(document.file_path)
        
        # 3. 路由到对应管道
        if file_type == FileType.DOCUMENT:
            result = document_pipeline.process(document)
        elif file_type == FileType.IMAGE:
            result = image_pipeline.process(document)
        # ... 其他类型
        
        # 4. 保存元数据
        await save_metadata(document_id, result)
        
        # 5. 更新状态
        await db.update_document_status(document_id, "completed")
        
    except Exception as e:
        logger.error(f"处理失败: {document_id}", exc_info=e)
        await db.update_document_status(document_id, "failed", error=str(e))
        raise self.retry(exc=e, countdown=60)
```

**验收**:
- [ ] 任务可以排队
- [ ] 状态可以查询
- [ ] 失败自动重试
- [ ] 并发处理正常

### Week 4-5：处理管道实现

#### 文档处理管道（2天）

**任务**:
1. 实现文本提取（PDF, DOCX, TXT）
2. 实现结构识别
3. 实现实体识别（NER）
4. 实现关键词提取

**产出**:
```python
# backend/src/app/services/pipelines/document_pipeline.py
class DocumentPipeline:
    """文档处理管道"""
    
    async def process(self, document: Document) -> DocumentMetadata:
        logger.info(f"开始处理文档: {document.id}")
        
        # 1. 文本提取
        text = await self.extract_text(document.file_path)
        logger.info(f"提取文本: {len(text)} 字符")
        
        # 2. 结构识别
        structure = await self.parse_structure(text)
        logger.info(f"识别结构: {len(structure.sections)} 章节")
        
        # 3. 实体识别
        entities = await self.extract_entities(text)
        logger.info(f"识别实体: {len(entities)} 个")
        
        # 4. 关键词提取
        keywords = await self.extract_keywords(text)
        logger.info(f"提取关键词: {len(keywords)} 个")
        
        # 5. 摘要生成
        summary = await self.generate_summary(text)
        
        # 6. 分块
        chunks = await self.chunk_text(text)
        logger.info(f"文本分块: {len(chunks)} 块")
        
        # 7. 向量化
        embeddings = await self.generate_embeddings(chunks)
        
        return DocumentMetadata(
            document_id=document.id,
            text=text,
            structure=structure,
            entities=entities,
            keywords=keywords,
            summary=summary,
            chunks=chunks,
            embeddings=embeddings
        )
    
    async def extract_text(self, file_path: str) -> str:
        """提取文本（支持PDF, DOCX, TXT）"""
        ext = Path(file_path).suffix.lower()
        
        if ext == ".pdf":
            return await self._extract_from_pdf(file_path)
        elif ext in [".docx", ".doc"]:
            return await self._extract_from_docx(file_path)
        elif ext == ".txt":
            return await self._extract_from_txt(file_path)
        else:
            raise ValueError(f"不支持的文件类型: {ext}")
    
    async def _extract_from_pdf(self, file_path: str) -> str:
        import PyPDF2
        text = ""
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text()
        return text
```

**测试**:
```python
async def test_process_pdf(pipeline, sample_pdf_document):
    result = await pipeline.process(sample_pdf_document)
    assert len(result.text) > 0
    assert len(result.entities) > 0
    assert len(result.keywords) > 0

async def test_extract_entities(pipeline):
    text = "张三在北京工作。"
    entities = await pipeline.extract_entities(text)
    assert any(e.text == "张三" and e.type == "PERSON" for e in entities)
    assert any(e.text == "北京" and e.type == "LOCATION" for e in entities)
```

**验收**:
- [ ] 可以提取PDF文本
- [ ] 可以提取DOCX文本
- [ ] 实体识别准确率 > 80%
- [ ] 测试覆盖率 > 85%

#### 图片处理管道（2天）

**产出**:
```python
# backend/src/app/services/pipelines/image_pipeline.py
class ImagePipeline:
    async def process(self, document: Document) -> ImageMetadata:
        # 1. EXIF提取
        exif = await self.extract_exif(document.file_path)
        
        # 2. 图像识别
        labels = await self.recognize_image(document.file_path)
        
        # 3. OCR
        ocr_text = await self.extract_text(document.file_path)
        
        # 4. 颜色分析
        colors = await self.analyze_colors(document.file_path)
        
        return ImageMetadata(...)
```

#### 音频处理管道（2天）

**产出**:
```python
# backend/src/app/services/pipelines/audio_pipeline.py
class AudioPipeline:
    async def process(self, document: Document) -> AudioMetadata:
        # 1. 转录
        transcript = await self.transcribe(document.file_path)
        
        # 2. 说话人识别
        speakers = await self.diarize_speakers(document.file_path)
        
        return AudioMetadata(...)
```

#### 视频处理管道（2天）

**产出**:
```python
# backend/src/app/services/pipelines/video_pipeline.py
class VideoPipeline:
    async def process(self, document: Document) -> VideoMetadata:
        # 1. 关键帧提取
        keyframes = await self.extract_keyframes(document.file_path)
        
        # 2. 音频提取和转录
        audio_metadata = await self.process_audio(document.file_path)
        
        return VideoMetadata(...)
```

#### 表格处理管道（2天）

**产出**:
```python
# backend/src/app/services/pipelines/table_pipeline.py
class TablePipeline:
    async def process(self, document: Document) -> TableMetadata:
        # 1. 解析
        sheets = await self.parse_sheets(document.file_path)
        
        # 2. Schema推断
        schema = await self.infer_schema(sheets)
        
        return TableMetadata(...)
```

---

## 阶段2：数据治理（第6-8周）

### Week 6：元数据管理

#### Day 1-2：元数据存储服务

**产出**:
```python
# backend/src/app/services/metadata_service.py
class MetadataService:
    async def save_metadata(self, document_id: str, metadata: Dict):
        """保存元数据到JSON字段"""
        
    async def get_metadata(self, document_id: str, metadata_type: str) -> Dict:
        """获取特定类型的元数据"""
        
    async def update_metadata(self, document_id: str, updates: Dict):
        """更新元数据"""
```

#### Day 3-5：数据质量检查

**产出**:
```python
# backend/src/app/services/data_quality/quality_checker.py
class DataQualityChecker:
    async def validate_metadata(self, metadata: Dict) -> QualityReport:
        """
        检查项：
        1. 完整性
        2. 一致性
        3. 准确性
        4. 唯一性
        5. 时效性
        """
```

### Week 7：去重与标签

#### Day 1-2：去重服务

**产出**:
```python
# backend/src/app/services/data_quality/deduplication.py
class DeduplicationService:
    async def check_duplicate(self, file_path: str) -> Optional[str]:
        # 1. 哈希去重
        # 2. 向量相似度去重
        # 3. 元数据去重
```

#### Day 3-5：标签管理

**产出**:
```python
# backend/src/app/services/tag_service.py
class TagService:
    async def auto_tag(self, document_id: str) -> List[str]:
        """自动标签生成"""
        
    async def add_tag(self, document_id: str, tag: str, created_by: str):
        """添加标签"""
        
    async def suggest_tags(self, document_id: str) -> List[str]:
        """标签推荐"""
```

### Week 8：文本分块与向量化

**产出**:
```python
# backend/src/app/services/chunking_service.py
class ChunkingService:
    async def chunk_text(self, text: str, max_tokens: int = 512) -> List[Chunk]:
        """语义分块"""

# backend/src/app/services/embedding_service.py
class EmbeddingService:
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """生成向量嵌入"""
```

---

## 阶段3：知识图谱（第9-12周）

### Week 9-10：实体管理

**产出**:
```python
# backend/src/app/services/knowledge_graph/entity_service.py
class EntityService:
    async def create_entity(self, text: str, entity_type: str) -> Entity
    async def find_or_create(self, text: str, entity_type: str) -> Entity
    async def merge_entities(self, entity_ids: List[int]) -> Entity

# backend/src/app/services/knowledge_graph/entity_resolver.py
class EntityResolver:
    async def resolve_entity(self, text: str, entity_type: str, context: str) -> Entity:
        """实体消歧"""
```

### Week 11-12：关系提取与图存储

**产出**:
```python
# backend/src/app/services/knowledge_graph/relation_extractor.py
class RelationExtractor:
    async def extract_relations(self, text: str, entities: List[Entity]) -> List[Relation]

# backend/src/app/services/knowledge_graph/graph_store.py
class GraphStore:
    async def add_entity(self, entity: Entity)
    async def add_relation(self, relation: Relation)
    async def query_neighbors(self, entity_id: str) -> Graph
```

---

## 阶段4：统一查询（第13-15周）

### Week 13：全文搜索

**产出**:
```python
# backend/src/app/services/search/fulltext_search.py
class FulltextSearchService:
    async def index_document(self, document_id: str, text: str)
    async def search(self, query: str, filters: List[Filter]) -> SearchResult
```

### Week 14：向量检索

**产出**:
```python
# backend/src/app/services/search/vector_search.py
class VectorSearchService:
    async def search_similar(self, query: str, limit: int) -> List[Match]
```

### Week 15：统一查询引擎

**产出**:
```python
# backend/src/app/services/query_engine/unified_query.py
class UnifiedQueryEngine:
    async def query(self, request: QueryRequest) -> QueryResult:
        # 支持5种查询类型
```

---

## 阶段5：前端统一（第16-18周）

### Week 16：数据层重构

**产出**:
```swift
// Sources/Services/UnifiedFileService.swift
class UnifiedFileService {
    func query(request: FileQueryRequest) async throws -> FileQueryResult
    func getDetails(fileId: String) async throws -> FileDetails
}
```

### Week 17：ViewModel重构

**产出**:
```swift
// Sources/ViewModels/UnifiedFileViewModel.swift
class UnifiedFileViewModel: ObservableObject {
    func loadFiles(projectId: Int) async
    func addFilter(_ filter: FileFilter) async
}
```

### Week 18：UI组件统一

**产出**:
```swift
// Sources/Views/UnifiedFileView.swift
struct UnifiedFileView: View {
    // 统一的文件浏览器
}
```

---

## 阶段6：测试优化（第19-20周）

### Week 19：全面测试

**任务**:
1. 端到端测试
2. 性能测试
3. 压力测试
4. 安全测试

### Week 20：优化与发布

**任务**:
1. 性能优化
2. 代码优化
3. 文档完善
4. 部署准备

---

## 每日工作流程

### 每天开始前
1. 回顾昨天的工作
2. 确认今天的目标
3. 检查依赖是否就绪

### 开发过程中
1. 先写测试（TDD）
2. 实现功能
3. 运行测试
4. 代码审查
5. 文档更新

### 每天结束时
1. 提交代码
2. 更新进度
3. 记录问题
4. 规划明天

---

## 质量检查清单

### 每个功能完成时必须检查

**代码质量**:
- [ ] 测试覆盖率 > 80%
- [ ] 没有重复代码
- [ ] 变量命名清晰
- [ ] 注释充分

**功能质量**:
- [ ] 满足需求
- [ ] 边界情况处理
- [ ] 错误处理完善
- [ ] 性能达标

**文档质量**:
- [ ] API文档完整
- [ ] 使用示例清晰
- [ ] 注意事项说明

---

## 风险管理

### 识别到的风险

1. **技术风险**
   - AI模型准确率不达标
   - 处理性能不足
   - 向量检索速度慢

   **应对**: 提前做POC验证

2. **时间风险**
   - 某个模块开发时间超预期

   **应对**: 预留缓冲时间，及时调整计划

3. **质量风险**
   - 测试不充分

   **应对**: 严格执行测试标准，不妥协

---

## 成功标准

### 阶段成功的标志

**技术指标**:
- ✅ 测试覆盖率 > 80%
- ✅ 性能指标达标
- ✅ 没有已知bug

**功能指标**:
- ✅ 所有功能可用
- ✅ 用户体验流畅
- ✅ 文档完整

**业务指标**:
- ✅ 解决了实际问题
- ✅ 架构可扩展
- ✅ 代码可维护

---

## 下一步行动

### 立即开始（明天）

**第一天任务**:
1. 创建数据库Schema设计文档
2. 编写迁移脚本
3. 配置测试数据库
4. 运行迁移测试

**需要你确认**:
1. 这个计划是否符合你的预期？
2. 时间安排是否合理？
3. 有哪些地方需要调整？
4. 我们什么时候开始？

---

**我已经准备好了，请告诉我你的决定。**
