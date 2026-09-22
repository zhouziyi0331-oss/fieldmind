# 🚀 快速开始指南

## 5分钟快速体验知识脉络分析系统

---

## 步骤 1: 安装依赖（首次运行）

```bash
# 进入项目目录
cd /Users/alwan

# 运行自动安装脚本
chmod +x install.sh
./install.sh
```

**说明**: 安装脚本会自动：
- 创建 Python 虚拟环境
- 安装所有 Python 依赖
- 安装 FFmpeg、Redis（音视频处理和任务队列）
- 可选安装 Neo4j（知识图谱）
- 下载 NLP 模型（可选，首次运行时也会自动下载）
- 创建必要的数据目录

---

## 步骤 2: 配置环境变量

```bash
# .env 文件已自动创建，使用默认配置即可
# 如需修改，编辑 .env 文件
nano .env
```

**默认配置**（开箱即用）：
```env
DATABASE_URL=sqlite:///./knowledge_system.db  # SQLite 数据库
NEO4J_URI=bolt://localhost:7687               # Neo4j（可选）
REDIS_URL=redis://localhost:6379/0            # Redis
```

---

## 步骤 3: 初始化数据库

```bash
python3 init_db.py
```

**输出示例**：
```
开始初始化数据库...
✓ 数据库表创建成功

已创建 6 个表:
  - documents
  - entities
  - contexts
  - dialogues
  - messages
  - skills

数据库初始化完成！
```

---

## 步骤 4: 启动系统

```bash
chmod +x start.sh
./start.sh
```

**启动选项**：
```
1) 仅启动 API 服务               # 适合快速测试
2) 启动 API + Celery Worker      # 适合文档处理
3) 启动完整系统                   # 推荐，功能完整
```

**推荐选择 3**，按提示输入 `3` 并回车。

**启动成功标志**：
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

---

## 步骤 5: 访问系统

### 方式 1: Web 界面（推荐）

浏览器打开: **http://localhost:8000/index.html**

界面功能：
- 📤 **文档上传**: 上传视频/音频/文本文件
- 📚 **文档管理**: 查看已上传的文档
- 💬 **智能对话**: 基于文档内容的问答
- 📊 **生成报告**: 生成三层分析报告

### 方式 2: API 文档

浏览器打开: **http://localhost:8000/docs**

Swagger UI 自动文档，可以直接测试所有 API。

### 方式 3: 命令行测试

```bash
# 健康检查
curl http://localhost:8000/health

# 查看系统信息
curl http://localhost:8000/
```

---

## 步骤 6: 运行系统测试（可选）

新开一个终端窗口：

```bash
python3 test_system.py
```

测试会自动：
1. ✓ 健康检查
2. ✓ 上传测试文档
3. ✓ 获取文档列表
4. ✓ 测试智能对话
5. ✓ 生成知识脉络
6. ✓ 生成分析报告

**预期输出**：
```
============================================================
  知识脉络分析系统 - 功能测试
============================================================

============================================================
  测试 1: 健康检查
============================================================
✓ 健康检查通过
  状态: healthy
  数据库: connected
  向量数据库: ready

[... 其他测试 ...]

============================================================
  测试总结
============================================================

总测试数: 6
通过: 6
失败: 0
成功率: 100.0%

🎉 所有测试通过！系统运行正常。
```

---

## 📝 快速体验示例

### 1. 上传文档

**Web 界面**：
1. 点击"文档上传"标签
2. 选择一个文本文件（或创建 test.txt）
3. 输入标题（可选）
4. 勾选"自动处理"
5. 点击"上传文档"

**API 方式**：
```bash
# 创建测试文件
cat > test_doc.txt << 'EOF'
十八洞村位于湖南省湘西土家族苗族自治州。
这里是苗族文化的重要传承地。
村民们通过山歌传递历史和文化。
EOF

# 上传文档
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -F "file=@test_doc.txt" \
  -F "title=十八洞村文化调查" \
  -F "auto_process=true"
```

### 2. 智能对话

**Web 界面**：
1. 点击"智能对话"标签
2. 输入问题："十八洞村在哪里？"
3. 点击"发送"

**API 方式**：
```bash
curl -X POST http://localhost:8000/api/v1/chat/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "十八洞村在哪里？有什么文化特色？",
    "top_k": 3
  }'
```

### 3. 生成报告

**Web 界面**：
1. 点击"生成报告"标签
2. 输入文档 ID（例如：1）
3. 选择报告层次
4. 选择导出格式（HTML 或 Markdown）
5. 点击"生成报告"

**API 方式**：
```bash
curl -X POST http://localhost:8000/api/v1/reports/generate \
  -H "Content-Type: application/json" \
  -d '{
    "document_ids": [1],
    "tiers": [1, 2, 3],
    "export_format": "html"
  }'
```

---

## 🎯 关键文件位置

```
/Users/alwan/
├── app/                      # 应用代码
│   ├── main.py              # FastAPI 入口
│   ├── models/              # 数据模型
│   ├── services/            # 业务逻辑
│   └── api/                 # API 路由
├── data/                    # 数据目录
│   ├── uploads/             # 上传的文件
│   ├── processed/           # 处理后的文件
│   ├── chromadb/            # 向量数据库
│   └── reports/             # 生成的报告
├── logs/                    # 日志文件
├── index.html               # Web 界面
├── requirements.txt         # Python 依赖
├── .env                     # 环境配置
├── start.sh                 # 启动脚本
├── install.sh               # 安装脚本
├── init_db.py               # 数据库初始化
├── test_system.py           # 系统测试
├── README.md                # 完整文档
└── PROJECT_STATUS.md        # 项目状态
```

---

## 🔧 常见问题

### Q1: 提示端口 8000 已被占用
```bash
# 查看占用进程
lsof -i :8000

# 杀死进程
kill -9 <PID>

# 或使用其他端口
uvicorn app.main:app --port 8001
```

### Q2: Redis 连接失败
```bash
# macOS
brew services start redis

# Linux
sudo systemctl start redis-server

# 检查状态
redis-cli ping  # 应返回 PONG
```

### Q3: 模型下载慢
```bash
# 使用国内镜像
export HF_ENDPOINT=https://hf-mirror.com
pip install -r requirements.txt
```

### Q4: FFmpeg 未安装
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# 验证安装
ffmpeg -version
```

---

## 📚 下一步

1. **阅读完整文档**: [README.md](README.md)
2. **查看项目状态**: [PROJECT_STATUS.md](PROJECT_STATUS.md)
3. **API 文档**: http://localhost:8000/docs
4. **配置优化**: 根据实际需求调整 `.env` 配置

---

## 💡 提示

- **首次运行**: 模型下载需要时间和网络，请耐心等待
- **生产部署**: 请使用 PostgreSQL 替代 SQLite
- **性能优化**: 有 GPU 可以加速模型推理
- **定期备份**: 重要数据请定期备份 `data/` 目录

---

## 🆘 获取帮助

- 查看日志: `tail -f logs/celery_worker.log`
- 健康检查: `curl http://localhost:8000/health`
- 重启系统: `Ctrl+C` 停止后重新运行 `./start.sh`

---

**祝您使用愉快！** 🎉
