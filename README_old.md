# FieldMind 田野调查智能分析系统

完整的田野调查智能分析平台，集成文档管理、智能对话、知识图谱、时间线分析等功能。

## 🎯 系统组成

### 1. 后端服务 (Python)
- **框架**: FastAPI + SQLAlchemy + Celery
- **数据库**: PostgreSQL / SQLite
- **AI集成**: OpenAI GPT-4, Whisper, LangChain
- **功能**: RESTful API, 文档处理, RAG对话, 知识抽取

### 2. Web 前端
- **技术**: HTML5 + CSS3 + JavaScript
- **特点**: 响应式设计, 单页应用, 实时更新

### 3. macOS 原生应用 (Swift)
- **框架**: SwiftUI + Alamofire
- **系统要求**: macOS 13.0+
- **特点**: 原生性能, 系统集成, 优雅界面

## 📦 快速开始

### 前置要求

```bash
# macOS 系统
brew install python@3.11
brew install redis
brew install postgresql  # 可选，也可使用 SQLite

# Swift 开发（macOS 应用）
xcode-select --install
```

### 一键启动

```bash
cd ~/FieldMind-Rebuild

# 1. 启动所有服务
./start_system.sh

# 2. 检查系统状态
./check_status.sh

# 3. 停止所有服务
./stop_system.sh
```

### 手动启动步骤

#### 步骤 1: 启动后端

```bash
cd ~/FieldMind-Rebuild

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
cd fieldmind-backend
pip install -r requirements.txt

# 初始化数据库
python init_db.py

# 启动 Redis
brew services start redis

# 启动后端服务
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 另开终端，启动 Celery Worker
celery -A app.celery_app worker --loglevel=info
```

#### 步骤 2: 启动 Web 前端

```bash
cd ~/FieldMind-Rebuild/frontend
python3 -m http.server 8080
```

访问: http://localhost:8080

#### 步骤 3: 编译并运行 macOS 应用

```bash
cd ~/Desktop/FieldMindApp

# 编译
swift build

# 运行
swift run

# 或发布版本
swift build -c release
.build/release/FieldMind
```

## 🔐 默认账号

```
用户名: demo
密码: demo123
```

## 🌐 服务地址

- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **Web 前端**: http://localhost:8080
- **macOS 应用**: 本地运行

## 📚 核心功能

### 1. 项目管理
- 创建和管理多个调研项目
- 项目成员协作
- 项目数据隔离

### 2. 文档管理
- 支持格式: PDF, Word, Excel, TXT, Markdown
- 自动文本提取和分析
- 文档状态跟踪（处理中、已完成、失败）
- 批量上传和处理

### 3. 知识上下文（三层体系）
- **一级上下文**: 宏观主题（如"乡村振兴"）
- **二级上下文**: 具体维度（如"产业发展"）
- **三级上下文**: 细分类别（如"电商模式"）
- 关键词标签
- 层级导航

### 4. 智能对话
- RAG 增强对话（基于已上传文档）
- 多会话管理
- 理论框架集成（费孝通、SOP等）
- 数据来源溯源
- 实时对话历史

### 5. 时间线分析
- 自动从文档提取时间事件
- 年份组织
- 事件详情展示
- 时间脉络可视化

### 6. 知识图谱
- 实体识别（人物、地点、事件、概念）
- 关系抽取
- 交互式图谱可视化
- 节点详情和关系查看
- 拖拽和缩放

### 7. 技能脚本
- 上传自定义 Python 分析脚本
- 启用/禁用管理
- 脚本执行和结果查看
- 扩展分析能力

### 8. 分析框架
- **费孝通理论**: 差序格局、礼治秩序、熟人社会
- **标准流程 (SOP)**: 调研准备、实施、分析、报告
- **自定义框架**: 支持扩展

### 9. 报告生成
- 基于分析结果自动生成报告
- 多种报告模板
- Markdown/PDF 导出
- 图表集成

### 10. 音视频处理
- 音频转文字（Whisper）
- 视频字幕提取
- 多语言支持

## 🏗️ 项目结构

```
FieldMind-Rebuild/
├── fieldmind-backend/          # 后端服务
│   ├── app/
│   │   ├── main.py            # FastAPI 主应用
│   │   ├── models/            # 数据模型
│   │   ├── routers/           # API 路由
│   │   ├── services/          # 业务逻辑
│   │   ├── tasks/             # Celery 异步任务
│   │   └── middleware/        # 中间件
│   ├── data/                  # 数据目录
│   ├── logs/                  # 日志文件
│   ├── skills/                # 技能脚本
│   ├── reports/               # 生成的报告
│   ├── requirements.txt       # Python 依赖
│   ├── init_db.py            # 数据库初始化
│   └── .env                   # 环境变量
├── frontend/                   # Web 前端
│   ├── index.html
│   ├── css/
│   ├── js/
│   └── assets/
├── start_system.sh            # 启动脚本
├── stop_system.sh             # 停止脚本
└── check_status.sh            # 状态检查

FieldMindApp/                   # macOS 应用
├── Package.swift              # Swift 包配置
├── Sources/
│   └── FieldMind/
│       ├── main.swift         # 应用入口
│       ├── Models/            # 数据模型
│       ├── Services/          # API 服务
│       ├── Views/             # SwiftUI 视图
│       └── Utils/             # 工具类
└── README.md
```

## 🔧 配置说明

### 环境变量 (.env)

```bash
# 数据库
DATABASE_URL=sqlite:///./data/fieldmind.db

# API Keys
OPENAI_API_KEY=your-key-here
ANTHROPIC_API_KEY=your-key-here

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# 应用配置
DEBUG=true
LOG_LEVEL=INFO
```

### API 配置 (macOS 应用)

编辑 [APIService.swift:11](~/Desktop/FieldMindApp/Sources/FieldMind/Services/APIService.swift#L11):
```swift
private let baseURL = "http://localhost:8000"
```

## 📖 使用流程

### 典型工作流

1. **登录系统**
   - Web: 访问 http://localhost:8080
   - macOS: 启动应用
   - 使用 demo/demo123 登录

2. **创建项目**
   - 点击"项目管理"
   - 创建新项目，填写名称和描述

3. **上传文档**
   - 进入"文档管理"
   - 上传调研文档（PDF、Word等）
   - 等待自动处理完成

4. **构建知识上下文**
   - 进入"知识上下文"
   - 创建三层上下文结构
   - 添加关键词和关联报告

5. **智能对话**
   - 进入"智能对话"
   - 创建新会话，选择相关文档
   - 选择分析框架（可选）
   - 提问获取AI分析

6. **生成时间线**
   - 进入"时间线分析"
   - 点击"生成时间线"
   - 查看事件时间脉络

7. **构建知识图谱**
   - 进入"知识图谱"
   - 点击"构建图谱"
   - 交互式探索实体关系

8. **使用技能脚本**
   - 进入"技能管理"
   - 上传自定义Python脚本
   - 启用并执行分析

## 🔌 API 端点

### 认证
- `POST /api/auth/login` - 用户登录
- `POST /api/auth/logout` - 用户登出
- `GET /api/auth/me` - 获取当前用户

### 项目
- `GET /api/projects` - 获取项目列表
- `POST /api/projects` - 创建项目
- `GET /api/projects/{id}` - 获取项目详情
- `DELETE /api/projects/{id}` - 删除项目

### 文档
- `GET /api/projects/{pid}/documents` - 获取文档列表
- `POST /api/projects/{pid}/documents/upload` - 上传文档
- `POST /api/documents/{id}/process` - 处理文档
- `DELETE /api/documents/{id}` - 删除文档

### 对话
- `GET /api/projects/{pid}/chat/sessions` - 获取会话列表
- `POST /api/projects/{pid}/chat/sessions` - 创建会话
- `POST /api/chat/sessions/{sid}/messages` - 发送消息

### 分析
- `POST /api/projects/{pid}/timeline/generate` - 生成时间线
- `POST /api/projects/{pid}/graph/build` - 构建知识图谱
- `GET /api/projects/{pid}/contexts` - 获取上下文

详细 API 文档: http://localhost:8000/docs

## 🧪 测试

```bash
cd ~/FieldMind-Rebuild/fieldmind-backend

# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_auth.py

# 测试完整系统
python test_complete_system.py
```

## 🐛 故障排除

### 后端无法启动
```bash
# 检查端口占用
lsof -i :8000
kill -9 <PID>

# 检查依赖
pip install -r requirements.txt

# 查看日志
tail -f fieldmind-backend/logs/app.log
```

### Redis 连接失败
```bash
# 启动 Redis
brew services start redis

# 检查状态
redis-cli ping
```

### macOS 应用编译失败
```bash
# 清理构建
cd ~/Desktop/FieldMindApp
swift package clean

# 更新依赖
swift package update

# 重新编译
swift build
```

### 文档处理卡住
```bash
# 检查 Celery Worker
ps aux | grep celery

# 重启 Worker
pkill -f celery
celery -A app.celery_app worker --loglevel=info
```

## 📊 性能优化

### 后端优化
- 使用 PostgreSQL 替代 SQLite（生产环境）
- 增加 Celery Worker 数量
- 启用 Redis 缓存
- 配置数据库连接池

### 前端优化
- 使用 CDN 加载静态资源
- 启用浏览器缓存
- 压缩图片和资源文件

### macOS 应用优化
- 使用 Release 模式编译
- 启用编译器优化
- 减少不必要的 UI 重绘

## 🔒 安全建议

1. **修改默认密码**
2. **使用强密钥** (SECRET_KEY, JWT_SECRET_KEY)
3. **启用 HTTPS** (生产环境)
4. **配置 CORS** (限制允许的源)
5. **API 限流** (防止滥用)
6. **定期备份数据库**
7. **更新依赖包** (安全补丁)

## 📝 开发指南

### 添加新功能

1. **后端**: 在 `app/routers/` 添加新路由
2. **前端**: 在 `frontend/js/` 添加新组件
3. **macOS**: 在 `Sources/FieldMind/Views/` 添加新视图

### 调试模式

```bash
# 后端详细日志
LOG_LEVEL=DEBUG uvicorn app.main:app --reload

# macOS 应用调试
cd ~/Desktop/FieldMindApp
swift build && lldb .build/debug/FieldMind
```

## 📄 许可证

本项目仅供学习和研究使用。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📧 联系方式

- 项目文档: 查看各目录下的 README.md
- API 文档: http://localhost:8000/docs
- 问题反馈: GitHub Issues

---

**FieldMind** - 让田野调查更智能 🌾✨
