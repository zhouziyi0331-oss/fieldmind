# FieldMind 系统修复执行计划

生成时间：2026-09-15  
目标：将迁移后的前后端连接成完整可用的系统

---

## 🎯 修复目标

将分散在两个位置的代码统一后，修复所有断裂的连接，使系统能够：
1. ✅ 正常启动前端和后端
2. ✅ 完成用户登录注册流程
3. ✅ 项目管理功能可用
4. ✅ 文档上传和查看功能可用
5. ✅ 基础对话功能可用

---

## 📋 已完成的工作

### ✅ Phase 0: 代码迁移
- [x] 从 `/Users/alwan/Downloads/FieldMind` 迁移到 `/Users/alwan/FieldMind`
- [x] 删除旧副本，释放 12GB 空间
- [x] Git 仓库完整性验证
- [x] 提交前后端响应格式修复 (commit 2854d5ea)

### ✅ Phase 1: 响应格式修复
- [x] 修复 `frontend/src/services/fieldmind.ts` 响应拦截器
- [x] 修复 `frontend/src/services/api.ts` 响应拦截器
- [x] 正确处理后端 `{ success, data, error, metadata }` 格式

---

## 🔧 待修复问题清单

### P0 - 阻塞启动的问题

#### 1. 数据库初始化 ⚠️
**问题**: 数据库表未创建，后端无法启动
```bash
# 错误信息可能包含
# sqlalchemy.exc.OperationalError: no such table
```

**修复方案**:
```bash
cd /Users/alwan/FieldMind/backend/src
# 创建数据目录
mkdir -p data
# 运行数据库迁移
alembic upgrade head
```

**验证**: 检查 `data/fieldmind.db` 文件是否创建

---

#### 2. 环境变量配置 ⚠️
**问题**: 部分必需的环境变量未设置

**当前配置**:
```bash
# .env 文件中缺失
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
```

**修复方案**:
```bash
# 最小可运行配置（不使用 AI 功能）
DATABASE_URL=sqlite:///./data/fieldmind.db
DEBUG=True
HOST=0.0.0.0
PORT=8000

# 可选：启用 AI 功能时添加
# OPENAI_API_KEY=sk-xxx
# OLLAMA_BASE_URL=http://localhost:11434
```

**验证**: 后端能够启动到 8000 端口

---

#### 3. CORS 跨域配置 ⚠️
**问题**: 前端 (localhost:3000) 无法访问后端 (localhost:8000)

**当前状态**: 需要验证 CORS 中间件配置

**检查位置**: `backend/src/app/main.py`
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境需要限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**验证**: 浏览器控制台无 CORS 错误

---

### P1 - 核心功能断裂

#### 4. API 路径对齐 ⚠️
**问题**: 前端调用的 API 路径与后端实际路由不完全匹配

**已知对齐情况**:
- ✅ `/api/v1/auth/*` - 已对齐
- ✅ `/api/v1/projects/*` - 已对齐
- ✅ `/api/v1/documents/*` - 已对齐
- ✅ `/api/v1/knowledge-graph/*` - 已对齐
- ⚠️ `/api/chat/*` vs `/api/v1/chat/*` - 需要验证
- ⚠️ `/api/v1/users/*` - 需要检查后端是否实现

**修复方案**:
1. 扫描所有前端 API 调用
2. 对比后端实际路由
3. 添加兼容路由或修改前端调用

**验证**: 所有前端 API 调用返回 200 而非 404

---

#### 5. 用户认证流程 ⚠️
**问题**: 登录/注册可能因为数据库表结构不匹配失败

**依赖**:
- 数据库已初始化
- User 表已创建
- JWT Token 配置正确

**修复方案**:
```bash
# 检查 User 模型
cat backend/src/app/models/user.py

# 检查 JWT 配置
grep -r "SECRET_KEY\|JWT" backend/src/app/core/config.py
```

**验证**:
1. 能够注册新用户
2. 能够登录并获取 token
3. token 能够通过认证中间件

---

#### 6. 项目管理功能 ⚠️
**问题**: 项目 CRUD 操作可能因为表结构或外键关系失败

**依赖**:
- Project 表已创建
- User-Project 关联正确

**验证**:
1. 创建项目成功
2. 项目列表显示
3. 项目详情页加载

---

#### 7. 文档上传功能 ⚠️
**问题**: 文件存储路径或权限问题

**当前配置**: 需要检查
```python
# 上传目录
UPLOAD_DIR = "./uploads"
```

**修复方案**:
```bash
cd /Users/alwan/FieldMind/backend/src
mkdir -p uploads
chmod 755 uploads
```

**验证**:
1. 文件上传成功
2. 文件保存到磁盘
3. 数据库记录创建

---

### P2 - 高级功能断裂

#### 8. Redis 连接 ⚠️
**问题**: 缓存和任务队列需要 Redis

**当前状态**: Redis 可能未启动

**修复方案**:
```bash
# 方案 A: 启动 Redis
brew services start redis

# 方案 B: 禁用 Redis（降级）
# 修改 .env
USE_REDIS_CACHE=false
```

**验证**: 后端启动时无 Redis 连接错误

---

#### 9. Neo4j 连接 ⚠️
**问题**: 知识图谱功能需要 Neo4j

**当前状态**: Neo4j 可能未启动

**修复方案**:
```bash
# 方案 A: 启动 Neo4j
neo4j start

# 方案 B: 禁用知识图谱（降级）
# 注释掉相关路由或使用 fallback
```

**验证**: 知识图谱页面能够加载（即使数据为空）

---

#### 10. ChromaDB 向量检索 ⚠️
**问题**: RAG 对话需要 ChromaDB

**当前状态**: ChromaDB 可能未初始化

**修复方案**:
```bash
# ChromaDB 持久化目录
mkdir -p /Users/alwan/FieldMind/chroma_db
```

**验证**: 对话功能能够启动（即使检索失败）

---

## 🚀 修复执行步骤

### Step 1: 环境准备（5分钟）

```bash
cd /Users/alwan/FieldMind

# 1.1 创建必需目录
mkdir -p backend/src/data
mkdir -p backend/src/uploads
mkdir -p chroma_db
mkdir -p logs

# 1.2 设置权限
chmod 755 backend/src/uploads
chmod 755 chroma_db

# 1.3 验证依赖已安装
cd backend && python3 -c "import fastapi, sqlalchemy, uvicorn" && echo "✅ 后端依赖完整"
cd ../frontend && [ -d node_modules ] && echo "✅ 前端依赖完整"
```

---

### Step 2: 数据库初始化（5分钟）

```bash
cd /Users/alwan/FieldMind/backend/src

# 2.1 检查迁移脚本
ls -la migrations/versions/

# 2.2 运行数据库迁移
alembic upgrade head

# 2.3 验证
ls -lh data/fieldmind.db
sqlite3 data/fieldmind.db ".tables"
```

**预期结果**: 看到 users, projects, documents 等表

---

### Step 3: 配置环境变量（3分钟）

```bash
cd /Users/alwan/FieldMind

# 3.1 备份原配置
cp .env .env.backup

# 3.2 更新最小可运行配置
cat > .env.minimal << 'EOF'
# 基础配置
APP_NAME=FieldMind
DEBUG=True
HOST=0.0.0.0
PORT=8000

# 数据库
DATABASE_URL=sqlite:///./data/fieldmind.db

# JWT
SECRET_KEY=fieldmind-dev-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# 禁用可选服务
USE_REDIS_CACHE=false
NEO4J_ENABLED=false

# 文件存储
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE=104857600
EOF

# 3.3 使用最小配置
cp .env.minimal .env
```

---

### Step 4: 启动后端测试（2分钟）

```bash
cd /Users/alwan/FieldMind/backend/src

# 4.1 启动后端
python -m uvicorn app.main:app --reload --port 8000 &

# 4.2 等待启动
sleep 5

# 4.3 测试健康检查
curl http://localhost:8000/docs
curl http://localhost:8000/api/v1/auth/me || echo "未登录（正常）"

# 4.4 检查日志
tail -f logs/*.log
```

**预期结果**:
- ✅ 后端启动在 8000 端口
- ✅ Swagger 文档可访问
- ✅ 无致命错误

---

### Step 5: 启动前端测试（2分钟）

```bash
cd /Users/alwan/FieldMind/frontend

# 5.1 启动前端
npm run dev &

# 5.2 等待启动
sleep 5

# 5.3 打开浏览器
open http://localhost:3000
```

**预期结果**:
- ✅ 前端启动在 3000 端口
- ✅ 登录页面加载
- ✅ 无控制台错误

---

### Step 6: 端到端功能测试（10分钟）

#### 6.1 用户注册
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "test123456"
  }'
```

**预期**: 返回成功响应

---

#### 6.2 用户登录
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "test123456"
  }'
```

**预期**: 返回 token

---

#### 6.3 创建项目
```bash
TOKEN="从上一步获取的token"

curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "测试项目",
    "description": "这是一个测试项目"
  }'
```

**预期**: 返回项目详情

---

#### 6.4 项目列表
```bash
curl http://localhost:8000/api/v1/projects \
  -H "Authorization: Bearer $TOKEN"
```

**预期**: 返回项目列表，包含刚创建的项目

---

#### 6.5 文档上传
```bash
echo "测试文档内容" > test.txt

curl -X POST http://localhost:8000/api/v1/documents/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test.txt" \
  -F "project_id=1"
```

**预期**: 返回文档信息

---

### Step 7: 前端功能测试（浏览器）

在浏览器中测试：

1. **注册测试**
   - 访问 http://localhost:3000
   - 点击"注册"
   - 填写用户信息
   - 提交
   - ✅ 预期：注册成功，跳转到登录页

2. **登录测试**
   - 输入刚注册的用户名密码
   - 提交
   - ✅ 预期：登录成功，跳转到 Dashboard

3. **项目创建测试**
   - 点击"创建项目"
   - 填写项目信息
   - 提交
   - ✅ 预期：项目创建成功，显示在列表中

4. **文档上传测试**
   - 进入项目详情
   - 点击"上传文档"
   - 选择文件
   - 上传
   - ✅ 预期：文档上传成功，显示在列表中

---

## 🐛 常见问题排查

### 问题 1: 后端启动失败 - 数据库错误

**错误信息**:
```
sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such table: users
```

**解决方案**:
```bash
cd backend/src
rm -f data/fieldmind.db
alembic upgrade head
```

---

### 问题 2: 前端无法连接后端 - CORS 错误

**错误信息** (浏览器控制台):
```
Access to XMLHttpRequest at 'http://localhost:8000/api/v1/auth/login' 
from origin 'http://localhost:3000' has been blocked by CORS policy
```

**解决方案**: 检查 `backend/src/app/main.py` CORS 配置
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

### 问题 3: API 返回 404

**错误**: 前端调用的接口返回 404

**排查步骤**:
1. 检查后端日志，确认路由是否注册
2. 访问 http://localhost:8000/docs 查看所有可用接口
3. 对比前端调用路径和后端实际路径
4. 检查是否有尾部斜杠问题

---

### 问题 4: Token 认证失败

**错误**: API 返回 401 Unauthorized

**排查步骤**:
1. 检查 localStorage 中是否有 token
2. 检查 token 是否过期
3. 检查请求头是否包含 `Authorization: Bearer {token}`
4. 检查后端 SECRET_KEY 配置

---

### 问题 5: 文件上传失败

**错误**: 上传接口返回 500 错误

**排查步骤**:
1. 检查 uploads 目录是否存在和有写权限
2. 检查文件大小是否超过限制
3. 检查 Content-Type 是否为 multipart/form-data
4. 查看后端日志详细错误

---

## 📊 修复进度追踪

### 基础功能（必须）
- [ ] P0-1: 数据库初始化
- [ ] P0-2: 环境变量配置
- [ ] P0-3: CORS 配置验证
- [ ] P1-4: API 路径对齐
- [ ] P1-5: 用户认证流程
- [ ] P1-6: 项目管理功能
- [ ] P1-7: 文档上传功能

### 可选功能（渐进式启用）
- [ ] P2-8: Redis 连接
- [ ] P2-9: Neo4j 连接
- [ ] P2-10: ChromaDB 向量检索
- [ ] AI 对话功能
- [ ] 知识图谱可视化
- [ ] 高级分析功能

---

## ✅ 完成标准

### 最小可用系统（MVP）
- ✅ 后端启动无错误
- ✅ 前端启动无错误
- ✅ 用户能够注册
- ✅ 用户能够登录
- ✅ 能够创建项目
- ✅ 能够上传文档
- ✅ Dashboard 能够显示统计数据

### 完整功能系统
- ✅ MVP 所有功能
- ✅ Redis 缓存正常
- ✅ 知识图谱可视化
- ✅ AI 对话功能
- ✅ 向量检索功能
- ✅ 所有页面正常加载
- ✅ 无控制台错误

---

## 📝 修复日志

### 2026-09-15 14:30
- ✅ 完成代码迁移到统一目录
- ✅ 修复前后端响应格式匹配问题
- ✅ 创建系统分析报告
- ✅ 创建修复执行计划
- ⏳ 等待执行修复步骤...

---

**下一步**: 开始执行 Step 1 - 环境准备
