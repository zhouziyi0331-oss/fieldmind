# FieldMind 快速启动指南

## 立即开始

### 1. 安装依赖（首次运行）

```bash
cd /Users/alwan/FieldMind-Rebuild

# 安装新增的Python包
source venv/bin/activate
pip install python-jose[cryptography] passlib[bcrypt] python-multipart psycopg2-binary
```

### 2. 启动数据库服务

```bash
# 启动PostgreSQL
brew services start postgresql@14

# 启动Redis
brew services start redis

# 启动Neo4j (如果需要知识图谱功能)
brew services start neo4j
```

### 3. 初始化数据库

```bash
cd fieldmind-backend
python init_db.py
```

这会创建：
- 所有数据表（users, skills, timeline_events, industry_categories, reports等）
- 默认管理员账户：admin@fieldmind.com / admin123
- 7个默认业态类别

### 4. 启动后端服务

**终端1 - FastAPI服务器**:
```bash
cd fieldmind-backend
python -m app.main

# 或使用uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**终端2 - Celery Worker** (可选，用于异步任务):
```bash
cd fieldmind-backend
celery -A app.celery_app worker -l info -Q documents,audio,crawler,rag,graph,reports
```

### 5. 访问API文档

打开浏览器访问: http://localhost:8000/docs

你会看到完整的48个API端点！

---

## API测试流程

### Step 1: 注册/登录

**注册新用户**:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "researcher@example.com",
    "username": "researcher",
    "password": "password123",
    "role": "researcher"
  }'
```

**或使用管理员登录**:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@fieldmind.com",
    "password": "admin123"
  }'
```

响应会包含 `access_token`，保存它用于后续请求。

### Step 2: 测试技能管理

**获取所有技能**:
```bash
curl -X GET "http://localhost:8000/api/v1/skills" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**上传测试技能**:
创建一个测试技能文件 `test_skill.py`:
```python
"""测试技能"""

def process(data):
    return f"Processed: {data}"

if __name__ == "__main__":
    print(process("test"))
```

上传：
```bash
curl -X POST "http://localhost:8000/api/v1/skills/upload" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@test_skill.py" \
  -F 'metadata={
    "name": "Test Skill",
    "description": "A test skill",
    "category": "other",
    "version": "1.0.0",
    "dependencies": []
  }'
```

### Step 3: 测试业态分析

**获取业态类别**:
```bash
curl -X GET "http://localhost:8000/api/v1/industry/categories" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**获取传统农业详细分析**:
```bash
curl -X GET "http://localhost:8000/api/v1/industry/traditional-agriculture/details" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Step 4: 测试时间线

**创建时间线事件**:
```bash
curl -X POST "http://localhost:8000/api/v1/timeline/events" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2024-01-15T10:00:00",
    "title": "田野调查启动",
    "description": "开始在XX村进行田野调查",
    "category": "research",
    "tags": ["调查", "启动"]
  }'
```

**获取时间线事件**:
```bash
curl -X GET "http://localhost:8000/api/v1/timeline/events?sort=desc&limit=10" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Step 5: 测试报告生成

**生成报告**:
```bash
curl -X POST "http://localhost:8000/api/v1/reports/generate" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "2024年度调研报告",
    "report_type": "research",
    "include": {
      "charts": true,
      "maps": true,
      "tables": true,
      "wordcloud": true
    },
    "format": "docx"
  }'
```

响应会包含 `report_id` 和 `task_id`。

**查看报告状态**:
```bash
curl -X GET "http://localhost:8000/api/v1/reports/REPORT_ID" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## 前端开发

### 创建服务文件

在 `fieldmind-web/src/services/` 创建：

1. **authService.ts** - 认证服务
2. **skillService.ts** - 技能管理
3. **industryService.ts** - 业态分析
4. **timelineService.ts** - 时间线
5. **reportService.ts** - 报告生成（增强现有）

### 创建React Hooks

在 `fieldmind-web/src/hooks/` 创建：

1. **useAuth.ts** - 认证Hook
2. **useSkills.ts** - 技能管理Hook
3. **useIndustry.ts** - 业态分析Hook
4. **useTimeline.ts** - 时间线Hook

### 创建页面组件

1. **pages/Auth/**
   - LoginPage.tsx
   - RegisterPage.tsx

2. **pages/Skills/**
   - SkillListPage.tsx
   - SkillDetailPage.tsx
   - components/SkillUploader.tsx
   - components/SkillCard.tsx

3. **pages/Industry/**
   - IndustryOverviewPage.tsx
   - IndustryDetailPage.tsx
   - components/IndustryCard.tsx
   - components/TrendChart.tsx

4. **pages/Timeline/**
   - TimelinePage.tsx
   - components/TimelineView.tsx
   - components/TimelineEvent.tsx

5. **pages/Reports/** (增强)
   - ReportGeneratorPage.tsx
   - ReportListPage.tsx
   - ReportDetailPage.tsx
   - SummaryGeneratorPage.tsx

### 配置环境变量

`.env.local`:
```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_WS_URL=ws://localhost:8000/ws
```

### 配置Axios拦截器

`services/api.ts`:
```typescript
import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 30000,
})

// 请求拦截器 - 添加Token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器 - 处理401
api.interceptors.response.use(
  (response) => response.data,
  async (error) => {
    if (error.response?.status === 401) {
      // Token过期，尝试刷新
      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken) {
        try {
          const { data } = await axios.post(
            `${import.meta.env.VITE_API_BASE_URL}/auth/refresh`,
            { refresh_token: refreshToken }
          )
          localStorage.setItem('access_token', data.access_token)
          // 重试原请求
          error.config.headers.Authorization = `Bearer ${data.access_token}`
          return axios(error.config)
        } catch (refreshError) {
          // 刷新失败，跳转登录
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          window.location.href = '/login'
        }
      } else {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export default api
```

---

## 常见问题

### Q1: 数据库连接失败？
**A**: 检查PostgreSQL是否运行，并确保连接信息正确：
```bash
# 查看PostgreSQL状态
brew services list | grep postgresql

# 测试连接
psql -h localhost -U fieldmind -d fieldmind
```

### Q2: 导入错误？
**A**: 确保所有依赖已安装：
```bash
pip install -r fieldmind-backend/requirements.txt
pip install python-jose[cryptography] passlib[bcrypt] python-multipart psycopg2-binary
```

### Q3: Token验证失败？
**A**: 检查 `.env` 文件中的 `SECRET_KEY` 配置，或在 `app/core/security.py` 中设置。

### Q4: 技能上传验证失败？
**A**: 确保上传的Python文件语法正确，且依赖包已安装。

### Q5: 报告生成不工作？
**A**: 确保Celery worker正在运行：
```bash
celery -A app.celery_app worker -l info
```

---

## 下一步

1. ✅ 运行 `quick_start.sh` 初始化系统
2. ✅ 访问 http://localhost:8000/docs 测试API
3. ✅ 使用Swagger UI测试所有48个端点
4. ✅ 开始前端开发
5. ✅ 实现拖拽上传、详细页面、编年史视图

---

**需要帮助？**
- API文档: http://localhost:8000/docs
- 实施报告: IMPLEMENTATION_COMPLETE.md
- API映射: FRONTEND_BACKEND_API_MAPPING.md

**祝开发顺利！** 🚀
