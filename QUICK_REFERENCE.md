# FieldMind 快速参考手册

## 🚀 一键启动

```bash
cd ~/FieldMind-Rebuild
./start_system.sh
```

## 🛑 停止系统

```bash
cd ~/FieldMind-Rebuild
./stop_system.sh
```

## 🔍 检查状态

```bash
cd ~/FieldMind-Rebuild
./check_status.sh
```

---

## 常用命令

### 后端服务

```bash
# 进入后端目录
cd ~/FieldMind-Rebuild/fieldmind-backend

# 激活虚拟环境
source ../venv/bin/activate

# 启动开发服务器
uvicorn app.main:app --reload

# 启动 Celery Worker
celery -A app.celery_app worker --loglevel=info

# 初始化数据库
python init_db.py

# 运行测试
pytest
```

### Web 前端

```bash
# 启动前端服务器
cd ~/FieldMind-Rebuild/frontend
python3 -m http.server 8080

# 访问地址
open http://localhost:8080
```

### macOS 应用

```bash
# 编译应用
cd ~/Desktop/FieldMindApp
swift build

# 运行应用
swift run

# 发布版本
swift build -c release
.build/release/FieldMind

# 清理构建
swift package clean
```

---

## 🔐 登录信息

```
用户名: demo
密码: demo123
```

---

## 🌐 服务地址

| 服务 | 地址 |
|------|------|
| 后端 API | http://localhost:8000 |
| API 文档 | http://localhost:8000/docs |
| Web 前端 | http://localhost:8080 |
| Redis | localhost:6379 |
| PostgreSQL | localhost:5432 |

---

## 📂 重要路径

```bash
# 后端项目
~/FieldMind-Rebuild/fieldmind-backend/

# Web 前端
~/FieldMind-Rebuild/frontend/

# macOS 应用
~/Desktop/FieldMindApp/

# 数据库文件
~/FieldMind-Rebuild/fieldmind-backend/data/fieldmind.db

# 日志文件
~/FieldMind-Rebuild/fieldmind-backend/logs/app.log

# 上传文件
~/FieldMind-Rebuild/fieldmind-backend/data/uploads/

# 技能脚本
~/FieldMind-Rebuild/fieldmind-backend/skills/

# 生成报告
~/FieldMind-Rebuild/fieldmind-backend/reports/
```

---

## 🐛 常见问题

### 端口被占用

```bash
# 查找占用进程
lsof -i :8000
lsof -i :8080

# 终止进程
kill -9 <PID>
```

### Redis 未启动

```bash
# 启动 Redis
brew services start redis

# 检查状态
redis-cli ping
```

### 虚拟环境问题

```bash
# 重新创建虚拟环境
cd ~/FieldMind-Rebuild
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r fieldmind-backend/requirements.txt
```

### Swift 编译错误

```bash
# 清理并重新编译
cd ~/Desktop/FieldMindApp
swift package clean
swift package update
swift build
```

### 数据库重置

```bash
cd ~/FieldMind-Rebuild/fieldmind-backend
rm -rf data/fieldmind.db
python init_db.py
```

---

## 📊 系统监控

### 查看日志

```bash
# 后端日志
tail -f ~/FieldMind-Rebuild/fieldmind-backend/logs/app.log

# Celery 日志
tail -f ~/FieldMind-Rebuild/fieldmind-backend/logs/celery.log
```

### 查看进程

```bash
# 查看所有相关进程
ps aux | grep -E "uvicorn|celery|http.server"

# 查看端口监听
netstat -an | grep -E "8000|8080|6379"
```

### 资源使用

```bash
# 查看磁盘空间
df -h ~/FieldMind-Rebuild

# 查看数据库大小
du -h ~/FieldMind-Rebuild/fieldmind-backend/data/
```

---

## 🔧 开发调试

### 后端调试

```bash
# 启用详细日志
LOG_LEVEL=DEBUG uvicorn app.main:app --reload

# Python 调试
python -m pdb app/main.py
```

### 前端调试

```
打开浏览器开发者工具 (F12)
查看 Console 和 Network 标签页
```

### macOS 应用调试

```bash
# 使用 lldb 调试
cd ~/Desktop/FieldMindApp
swift build
lldb .build/debug/FieldMind

# 查看崩溃日志
open ~/Library/Logs/DiagnosticReports/
```

---

## 📦 依赖管理

### Python 依赖

```bash
# 查看已安装依赖
pip list

# 更新单个包
pip install --upgrade <package>

# 更新所有包
pip install --upgrade -r requirements.txt

# 导出当前依赖
pip freeze > requirements.txt
```

### Swift 依赖

```bash
# 更新依赖
swift package update

# 显示依赖树
swift package show-dependencies

# 重置依赖
swift package reset
```

---

## 🔐 安全检查清单

- [ ] 修改默认密码 (demo/demo123)
- [ ] 更改 SECRET_KEY 和 JWT_SECRET_KEY
- [ ] 配置 OpenAI API Key
- [ ] 限制 CORS 允许的源
- [ ] 启用 HTTPS (生产环境)
- [ ] 配置防火墙规则
- [ ] 定期备份数据库
- [ ] 更新依赖包到最新版本

---

## 📝 API 快速测试

### 使用 curl 测试

```bash
# 登录
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"demo","password":"demo123"}'

# 获取项目列表
curl http://localhost:8000/api/projects \
  -H "Authorization: Bearer <token>"

# 上传文档
curl -X POST http://localhost:8000/api/projects/1/documents/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@document.pdf"
```

### 使用 httpie 测试

```bash
# 安装 httpie
brew install httpie

# 登录
http POST localhost:8000/api/auth/login \
  username=demo password=demo123

# 获取项目
http localhost:8000/api/projects \
  Authorization:"Bearer <token>"
```

---

## 📚 学习资源

### 后端 (FastAPI)
- 官方文档: https://fastapi.tiangolo.com/
- API 文档: http://localhost:8000/docs

### 前端 (JavaScript)
- MDN Web Docs: https://developer.mozilla.org/

### macOS 应用 (SwiftUI)
- 官方文档: https://developer.apple.com/documentation/swiftui/
- Swift 指南: https://docs.swift.org/swift-book/

---

## 💡 最佳实践

1. **开发前先启动所有服务**
2. **定期检查系统状态**
3. **查看日志了解错误**
4. **使用版本控制 (Git)**
5. **编写测试用例**
6. **定期备份数据**
7. **文档化新功能**
8. **代码审查和重构**

---

## 🎯 下一步

1. ✅ 启动系统: `./start_system.sh`
2. ✅ 访问前端: http://localhost:8080
3. ✅ 登录系统: demo/demo123
4. ✅ 创建项目
5. ✅ 上传文档
6. ✅ 开始分析

---

**FieldMind** - 让田野调查更智能 🌾✨
