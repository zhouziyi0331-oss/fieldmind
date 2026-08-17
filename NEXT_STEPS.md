# FieldMind 下一步行动指南

**当前状态**: ✅ 后端运行正常，前端编译成功  
**日期**: 2026-08-02

---

## 一、立即可测试的功能

### 1. 后端API测试

#### 健康检查 ✅
```bash
curl http://localhost:8000/health
```

#### 用户注册
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "Test123456"
  }'
```

#### 用户登录
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "Test123456"
  }'
```

保存返回的 `access_token` 用于后续请求。

#### 创建项目
```bash
TOKEN="your_access_token_here"

curl -X POST http://localhost:8000/api/projects \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "测试项目",
    "description": "这是一个测试项目"
  }'
```

#### 上传文档
```bash
curl -X POST http://localhost:8000/api/documents/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "project_id=1" \
  -F "file=@/path/to/your/document.pdf"
```

#### 获取项目统计
```bash
curl -X GET http://localhost:8000/api/projects/1/stats \
  -H "Authorization: Bearer $TOKEN"
```

### 2. 前端桌面应用测试

```bash
cd /Users/alwan/FieldMind-Rebuild/fieldmind-desktop
swift run
```

**测试流程**:
1. 启动应用
2. 在设置中配置API地址: `http://localhost:8000`
3. 注册/登录账户
4. 创建新项目
5. 上传测试文档
6. 测试各个功能模块

---

## 二、需要实现的核心服务

### 🚧 关键词检索服务

**文件**: `app/services/keyword_search_service.py`

**需要实现的方法**:

```python
class KeywordSearchService:
    def __init__(self, db: Session):
        self.db = db
    
    async def search_keyword(
        self, 
        project_id: int, 
        keyword: str,
        include_videos: bool = True,
        include_audios: bool = True,
        include_documents: bool = True
    ) -> KeywordSearchResponse:
        """
        在项目的所有材料中搜索关键词
        
        返回:
        - 视频中的时间戳位置
        - 音频中的时间戳位置
        - 文档中的匹配位置
        - 关键词时间线
        - 相关关键词推荐
        """
        # TODO: 实现搜索逻辑
        # 1. 从数据库查询项目的所有文档
        # 2. 在文档内容中搜索关键词
        # 3. 如果有转录文本，在转录中搜索时间戳
        # 4. 构建时间线
        # 5. 使用TF-IDF或词嵌入推荐相关关键词
        
        pass
    
    async def get_top_keywords(
        self, 
        project_id: int, 
        limit: int = 50
    ) -> List[dict]:
        """提取项目中的Top关键词"""
        # TODO: 使用jieba/HanLP提取关键词
        # 统计词频，返回Top N
        pass
    
    async def get_keyword_timeline(
        self, 
        project_id: int, 
        keyword: str
    ) -> List[dict]:
        """获取关键词在项目时间线上的分布"""
        # TODO: 按时间顺序返回关键词出现的位置
        pass
```

**依赖**:
- jieba 或 HanLP (中文分词)
- 数据库中的文档和转录表
- 可选: 词嵌入模型用于相关词推荐

### 🚧 文创分析服务

**文件**: `app/services/creative_analysis_service.py`

**需要实现的方法**:

```python
class CreativeAnalysisService:
    def __init__(self, db: Session):
        self.db = db
        # 可选: 集成Claude API或其他LLM
    
    async def analyze_creative_possibilities(
        self,
        project_id: int,
        keywords: List[str],
        mode: str = "creative"
    ) -> CreativeAnalysisResponse:
        """
        基于关键词和项目内容，生成文创分析
        
        核心思路:
        1. 提取项目中的文化元素
        2. 识别独特性和文化内涵
        3. 结合关键词生成创意可能性
        4. 避免刻板建议（如"制作周边"）
        5. 提供创新点、可行性评分、目标受众
        """
        # TODO: 实现分析逻辑
        # 1. 从项目文档中提取文化元素
        # 2. 使用LLM生成创意建议
        # 3. 评估每个建议的可行性
        # 4. 识别反模式（刻板建议）
        
        pass
    
    async def extract_cultural_elements(
        self,
        project_id: int
    ) -> List[CulturalElement]:
        """从项目内容中提取文化元素"""
        # TODO: 使用NLP提取文化相关实体
        # 返回元素、独特性、文化意义
        pass
```

**依赖**:
- Anthropic Claude API (推荐) 或其他LLM
- NER模型用于实体提取
- 项目文档的文本内容

### 🚧 业态分析服务

**文件**: `app/services/business_analysis_service.py`

**需要实现的方法**:

```python
class BusinessAnalysisService:
    def __init__(self, db: Session):
        self.db = db
    
    async def analyze_business_formats(
        self,
        project_id: int
    ) -> BusinessAnalysisResponse:
        """
        分析现有业态并建议新业态
        
        核心逻辑:
        1. 识别现有业态（从文档中提取）
        2. 分析每个业态的状态和规模
        3. 基于调研数据建议新业态
        4. 可行性评分（有理有据）
        5. 列出所需资源、风险点、实施步骤
        6. 分析业态间的协同效应
        """
        # TODO: 实现分析逻辑
        # 1. 从文档中识别现有业态
        # 2. 使用LLM分析潜在业态
        # 3. 评估可行性（基于文档中的证据）
        # 4. 计算协同效应
        
        pass
    
    async def get_existing_formats(
        self,
        project_id: int
    ) -> List[ExistingFormat]:
        """提取项目中的现有业态"""
        # TODO: 从文档中识别业态类型
        pass
    
    async def analyze_synergy(
        self,
        project_id: int
    ) -> str:
        """分析业态间的协同效应"""
        # TODO: 分析不同业态之间的互补关系
        pass
```

**依赖**:
- LLM (Claude/GPT) 用于生成分析
- 文本分析工具
- 业态知识库（可选）

---

## 三、环境配置

### 1. 添加必要的环境变量

编辑 `/Users/alwan/FieldMind-Rebuild/fieldmind-backend/.env`:

```bash
# AI 服务
ANTHROPIC_API_KEY=sk-ant-xxxxx
OPENAI_API_KEY=sk-xxxxx  # 可选

# 数据库
DATABASE_URL=sqlite:///./fieldmind.db
# 或使用PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost/fieldmind

# Redis (用于Celery)
REDIS_URL=redis://localhost:6379/0

# 向量数据库
CHROMA_DB_PATH=./chroma_db
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# 上传目录
UPLOAD_DIR=./uploads

# CORS配置
CORS_ORIGINS=["http://localhost:3000","http://localhost:8080"]

# Debug模式
DEBUG=True
```

### 2. 安装缺失的Python包

```bash
cd /Users/alwan/FieldMind-Rebuild/fieldmind-backend

# 中文NLP工具
pip install jieba hanlp

# 向量化和嵌入
pip install sentence-transformers

# 如果需要离线模型
pip install transformers torch

# AI SDK
pip install anthropic openai

# 其他可能缺失的包
pip install python-multipart aiofiles
```

### 3. 启动必要的服务

#### Redis (用于Celery)
```bash
# macOS
brew install redis
brew services start redis

# 或手动启动
redis-server
```

#### Neo4j (可选，用于知识图谱)
```bash
# macOS
brew install neo4j
neo4j start
```

#### Celery Worker
```bash
cd /Users/alwan/FieldMind-Rebuild/fieldmind-backend
celery -A app.tasks.document_tasks:celery_app worker --loglevel=info
```

---

## 四、数据库初始化和测试数据

### 1. 初始化数据库

```bash
cd /Users/alwan/FieldMind-Rebuild/fieldmind-backend
python3 init_db.py
```

### 2. 创建测试数据

创建脚本 `create_test_data.py`:

```python
from app.core.database import SessionLocal
from app.models.user import User, UserRole
from app.models.project import Project
from app.core.security import get_password_hash

db = SessionLocal()

# 创建测试用户
test_user = User(
    username="demo",
    email="demo@fieldmind.com",
    hashed_password=get_password_hash("Demo123456"),
    role=UserRole.RESEARCHER,
    is_active=True
)
db.add(test_user)
db.commit()

# 创建测试项目
test_project = Project(
    name="布依族文化调研",
    description="贵州布依族传统文化与非遗保护研究",
    owner_id=test_user.id
)
db.add(test_project)
db.commit()

print(f"✅ 创建测试用户: {test_user.username}")
print(f"✅ 创建测试项目: {test_project.name} (ID: {test_project.id})")
```

运行:
```bash
python3 create_test_data.py
```

---

## 五、前后端联调步骤

### 步骤 1: 启动后端
```bash
cd /Users/alwan/FieldMind-Rebuild/fieldmind-backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 步骤 2: 验证后端API
```bash
# 健康检查
curl http://localhost:8000/health

# 查看API文档
open http://localhost:8000/docs
```

### 步骤 3: 启动桌面应用
```bash
cd /Users/alwan/FieldMind-Rebuild/fieldmind-desktop
swift run
```

### 步骤 4: 测试基础流程
1. **用户注册/登录**
   - 在桌面应用中注册新账户
   - 验证Token是否正确保存

2. **创建项目**
   - 创建一个新项目
   - 验证项目列表是否显示

3. **上传文档**
   - 上传一个PDF或文本文档
   - 验证文档是否出现在项目中

4. **测试统计**
   - 查看项目统计页面
   - 验证文档数量等统计信息

### 步骤 5: 测试新功能
1. **关键词检索**
   - 进入关键词检索页面
   - 输入关键词搜索
   - 查看返回结果（即使是模拟数据）

2. **文创分析**
   - 进入文创分析页面
   - 触发分析
   - 查看分析结果

3. **业态分析**
   - 进入业态分析页面
   - 触发分析
   - 查看业态建议

---

## 六、问题排查

### 后端无法启动

**检查项**:
1. 端口8000是否被占用
   ```bash
   lsof -ti:8000
   ```

2. 数据库文件是否存在
   ```bash
   ls -la fieldmind.db
   ```

3. Python依赖是否完整
   ```bash
   pip list | grep -E "(fastapi|sqlalchemy|pydantic)"
   ```

### 前端无法连接后端

**检查项**:
1. 后端是否正常运行
   ```bash
   curl http://localhost:8000/health
   ```

2. 前端API地址配置
   - 检查 `APIService.swift` 中的 `baseURL`
   - 默认应该是 `http://localhost:8000`

3. CORS配置
   - 检查 `.env` 中的 `CORS_ORIGINS`
   - 确保包含前端地址

### API返回500错误

**排查步骤**:
1. 查看后端日志
   ```bash
   tail -f /tmp/fieldmind-backend.log
   ```

2. 检查数据库连接
3. 检查环境变量配置
4. 检查服务实现是否抛出异常

---

## 七、开发优先级建议

### 🔴 高优先级 (立即实现)

1. **KeywordSearchService 基础功能**
   - 在文档内容中搜索关键词
   - 返回匹配位置和上下文
   - 简单的词频统计

2. **测试数据和Mock数据**
   - 创建测试项目和文档
   - 为新功能返回模拟数据
   - 确保前端可以正常显示

3. **错误处理和日志**
   - 添加详细的错误日志
   - 统一的错误响应格式
   - 前端友好的错误提示

### 🟡 中优先级 (后续完善)

1. **CreativeAnalysisService 集成LLM**
   - 配置Anthropic Claude API
   - 实现文化元素提取
   - 生成创意建议

2. **BusinessAnalysisService 业态分析**
   - 识别现有业态
   - 生成新业态建议
   - 可行性评分

3. **文档处理Pipeline**
   - 实现完整的文档转换
   - 文本提取和存储
   - 向量化和索引

### 🟢 低优先级 (长期优化)

1. **Celery异步任务**
   - 启动Redis和Celery worker
   - 实现后台文档处理
   - 任务状态跟踪

2. **向量检索优化**
   - 配置本地embedding模型
   - 实现语义搜索
   - 混合检索(BM25 + Vector)

3. **知识图谱**
   - Neo4j集成
   - 实体关系提取
   - 图谱可视化

---

## 八、快速命令参考

### 后端相关
```bash
# 启动后端
cd /Users/alwan/FieldMind-Rebuild/fieldmind-backend
python3 -m uvicorn app.main:app --reload

# 查看日志
tail -f /tmp/fieldmind-backend.log

# 测试导入
python3 -c "from app.main import app; print('OK')"

# 数据库迁移
alembic upgrade head

# 创建迁移
alembic revision --autogenerate -m "描述"
```

### 前端相关
```bash
# 启动桌面应用
cd /Users/alwan/FieldMind-Rebuild/fieldmind-desktop
swift run

# 编译检查
swift build

# 清理缓存
rm -rf .build
```

### 服务管理
```bash
# 停止后端
kill $(lsof -ti:8000)

# 启动Redis
redis-server

# 启动Celery
celery -A app.tasks.document_tasks:celery_app worker -l info
```

---

**更新时间**: 2026-08-02 12:45  
**文档状态**: 待更新（随开发进度）
