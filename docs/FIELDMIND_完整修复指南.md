# FieldMind 完整修复指南

## 问题总结

### 当前确认的问题
1. ❌ **Redis未安装** - Celery任务队列无法工作
2. ❌ **Celery Worker未运行** - 文档处理管道完全失效
3. ❌ **文档处理失效** - 导致：
   - 上传的文档字数统计错误（万字文档显示几个字）
   - chunk_count全部为0（未分块）
   - 文档内容未被提取和向量化
   - 无法进行语义搜索

### 根本原因
**FieldMind的文档处理是异步架构**：
```
文件上传 → FastAPI接收 → Celery任务队列 → Celery Worker处理 → 更新数据库
                                ↓ (需要Redis)
```

如果Redis和Celery Worker不运行，文档就永远停留在"已上传但未处理"状态。

---

## 完整修复步骤

### 第1步：安装Homebrew（包管理器）

打开**终端**，运行以下命令：

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

**重要提示：**
- 安装过程会要求输入管理员密码
- 大约需要5-10分钟
- 完成后，根据提示运行配置命令（通常是添加到PATH）

如果你的Mac是**Apple Silicon (M1/M2/M3)**，安装完成后运行：
```bash
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

如果是**Intel Mac**，运行：
```bash
echo 'eval "$(/usr/local/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/usr/local/bin/brew shellenv)"
```

验证安装：
```bash
brew --version
```

---

### 第2步：安装Redis

```bash
# 安装Redis
brew install redis

# 启动Redis服务（开机自启）
brew services start redis

# 验证Redis运行
redis-cli ping
# 应该返回: PONG
```

---

### 第3步：启动Celery Worker

打开**新的终端窗口**，运行：

```bash
cd /Users/alwan/FieldMind/backend/src

export DATABASE_URL="sqlite:////Users/alwan/FieldMind/backend/src/data/fieldmind.db"
export PYTHONPATH=/Users/alwan/FieldMind/backend/src

# 启动Celery Worker
/Library/Frameworks/Python.framework/Versions/3.11/bin/celery -A app.celery_app worker --loglevel=info --pool=solo
```

**保持这个终端窗口打开** - Celery Worker需要持续运行。

你应该看到类似这样的输出：
```
[tasks]
  . app.tasks.document_tasks.process_document
  . app.tasks.audio_tasks.transcribe_audio
  ...

celery@hostname ready.
```

---

### 第4步：验证系统

在**另一个终端窗口**中运行：

```bash
# 1. 检查Redis
redis-cli ping

# 2. 检查后端API
curl http://localhost:8000/health | jq '.checks.redis'

# 3. 手动触发文档处理
curl -X POST "http://localhost:8000/api/document-processing/documents/1004/reprocess"

# 4. 等待10秒后检查结果
sleep 10
sqlite3 /Users/alwan/FieldMind/backend/src/data/fieldmind.db \
  "SELECT id, filename, word_count, chunk_count, status FROM project_documents WHERE id = 1004;"
```

如果word_count从11变成了正常的数值，说明修复成功！

---

### 第5步：重新处理所有待处理的文档

```bash
# 获取所有待处理的文档ID
sqlite3 /Users/alwan/FieldMind/backend/src/data/fieldmind.db \
  "SELECT id FROM project_documents WHERE status = 'processing' OR chunk_count = 0;"

# 手动触发每个文档的处理（替换<document_id>为实际ID）
curl -X POST "http://localhost:8000/api/document-processing/documents/<document_id>/reprocess"
```

或者使用Python脚本批量处理：

```python
import requests
import sqlite3

# 连接数据库
conn = sqlite3.connect('/Users/alwan/FieldMind/backend/src/data/fieldmind.db')
cursor = conn.cursor()

# 获取所有需要处理的文档
cursor.execute("SELECT id FROM project_documents WHERE chunk_count = 0")
docs = cursor.fetchall()

# 触发处理
for (doc_id,) in docs:
    response = requests.post(f"http://localhost:8000/api/document-processing/documents/{doc_id}/reprocess")
    print(f"文档 {doc_id}: {response.json()}")

conn.close()
```

---

## 长期运行方案

### 方案A：使用launchd（macOS系统服务）

创建Celery自动启动配置：

```bash
# 创建launchd配置文件
cat > ~/Library/LaunchAgents/com.fieldmind.celery.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.fieldmind.celery</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Library/Frameworks/Python.framework/Versions/3.11/bin/celery</string>
        <string>-A</string>
        <string>app.celery_app</string>
        <string>worker</string>
        <string>--loglevel=info</string>
        <string>--pool=solo</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/alwan/FieldMind/backend/src</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>DATABASE_URL</key>
        <string>sqlite:////Users/alwan/FieldMind/backend/src/data/fieldmind.db</string>
        <key>PYTHONPATH</key>
        <string>/Users/alwan/FieldMind/backend/src</string>
    </dict>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/celery.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/celery.error.log</string>
</dict>
</plist>
EOF

# 加载服务
launchctl load ~/Library/LaunchAgents/com.fieldmind.celery.plist

# 启动服务
launchctl start com.fieldmind.celery

# 检查状态
launchctl list | grep fieldmind
```

### 方案B：使用tmux/screen保持会话

```bash
# 安装tmux
brew install tmux

# 创建后台会话
tmux new -s celery -d

# 在会话中启动Celery
tmux send-keys -t celery "cd /Users/alwan/FieldMind/backend/src" C-m
tmux send-keys -t celery "export DATABASE_URL='sqlite:////Users/alwan/FieldMind/backend/src/data/fieldmind.db'" C-m
tmux send-keys -t celery "export PYTHONPATH=/Users/alwan/FieldMind/backend/src" C-m
tmux send-keys -t celery "/Library/Frameworks/Python.framework/Versions/3.11/bin/celery -A app.celery_app worker --loglevel=info --pool=solo" C-m

# 查看会话
tmux attach -t celery  # 按Ctrl+B然后D退出但保持运行
```

---

## 启动脚本

创建一个一键启动脚本：

```bash
cat > /Users/alwan/start_fieldmind.sh << 'EOF'
#!/bin/bash

echo "=== 启动FieldMind完整系统 ==="

# 1. 启动Redis
echo "1. 检查Redis..."
if ! redis-cli ping > /dev/null 2>&1; then
    echo "   启动Redis..."
    brew services start redis
    sleep 2
fi
echo "   ✅ Redis运行中"

# 2. 启动后端API
echo "2. 启动后端API..."
cd /Users/alwan/FieldMind/backend
export DATABASE_URL="sqlite:////Users/alwan/FieldMind/backend/src/data/fieldmind.db"
export PYTHONPATH=/Users/alwan/FieldMind/backend/src

# 停止旧进程
pkill -f "uvicorn.*app.main" 2>/dev/null
sleep 2

# 启动新进程
/Library/Frameworks/Python.framework/Versions/3.11/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
sleep 5
echo "   ✅ 后端API运行中 (http://localhost:8000)"

# 3. 启动Celery Worker
echo "3. 启动Celery Worker..."
cd /Users/alwan/FieldMind/backend/src

# 停止旧Worker
pkill -f "celery.*worker" 2>/dev/null
sleep 2

# 启动新Worker
/Library/Frameworks/Python.framework/Versions/3.11/bin/celery -A app.celery_app worker --loglevel=info --pool=solo > /tmp/celery.log 2>&1 &
sleep 5
echo "   ✅ Celery Worker运行中"

# 4. 启动前端
echo "4. 启动FieldMind应用..."
open /Applications/FieldMind.app
sleep 2
echo "   ✅ FieldMind应用已启动"

echo ""
echo "=== 所有服务已启动 ==="
echo "后端API: http://localhost:8000"
echo "后端日志: tail -f /tmp/backend.log"
echo "Celery日志: tail -f /tmp/celery.log"
echo ""
echo "按Ctrl+C停止监控（服务继续在后台运行）"
echo ""

# 持续显示日志
tail -f /tmp/celery.log
EOF

chmod +x /Users/alwan/start_fieldmind.sh

echo "✅ 启动脚本已创建: /Users/alwan/start_fieldmind.sh"
```

使用方法：
```bash
/Users/alwan/start_fieldmind.sh
```

---

## 停止脚本

```bash
cat > /Users/alwan/stop_fieldmind.sh << 'EOF'
#!/bin/bash

echo "=== 停止FieldMind系统 ==="

# 停止FieldMind应用
killall FieldMind 2>/dev/null
echo "✅ FieldMind应用已停止"

# 停止Celery Worker
pkill -f "celery.*worker" 2>/dev/null
echo "✅ Celery Worker已停止"

# 停止后端API
pkill -f "uvicorn.*app.main" 2>/dev/null
echo "✅ 后端API已停止"

# 可选：停止Redis
# brew services stop redis
# echo "✅ Redis已停止"

echo ""
echo "=== 所有服务已停止 ==="
EOF

chmod +x /Users/alwan/stop_fieldmind.sh
```

---

## 常见问题排查

### 1. Redis连接失败
```bash
# 检查Redis是否运行
brew services list | grep redis

# 重启Redis
brew services restart redis

# 查看Redis日志
tail -f /opt/homebrew/var/log/redis.log
```

### 2. Celery无法连接Redis
```bash
# 检查Redis端口
lsof -i :6379

# 测试连接
redis-cli -h localhost -p 6379 ping
```

### 3. 文档处理卡住
```bash
# 查看Celery日志
tail -f /tmp/celery.log

# 查看活动任务
redis-cli KEYS "celery-task-meta-*" | wc -l

# 清空任务队列（谨慎使用）
redis-cli FLUSHALL
```

### 4. 后端API错误
```bash
# 查看后端日志
tail -f /tmp/backend.log

# 检查数据库
sqlite3 /Users/alwan/FieldMind/backend/src/data/fieldmind.db ".tables"

# 重启后端
pkill -f uvicorn
/Users/alwan/start_fieldmind.sh
```

---

## 性能优化

### 增加Celery Worker数量（处理速度更快）

```bash
# 使用多个worker进程
celery -A app.celery_app worker --concurrency=4 --loglevel=info
```

### 配置Redis持久化（数据安全）

编辑Redis配置：
```bash
# 备份原配置
cp /opt/homebrew/etc/redis.conf /opt/homebrew/etc/redis.conf.backup

# 启用AOF持久化
echo "appendonly yes" >> /opt/homebrew/etc/redis.conf

# 重启Redis
brew services restart redis
```

---

## 系统监控

### 监控脚本

```bash
cat > /Users/alwan/monitor_fieldmind.sh << 'EOF'
#!/bin/bash

echo "=== FieldMind系统状态 ==="
echo ""

# Redis
echo "1. Redis:"
if redis-cli ping > /dev/null 2>&1; then
    echo "   ✅ 运行中"
else
    echo "   ❌ 未运行"
fi

# 后端API
echo "2. 后端API:"
if curl -s http://localhost:8000/health > /dev/null; then
    echo "   ✅ 运行中"
else
    echo "   ❌ 未运行"
fi

# Celery Worker
echo "3. Celery Worker:"
if pgrep -f "celery.*worker" > /dev/null; then
    echo "   ✅ 运行中"
    TASKS=$(redis-cli LLEN celery 2>/dev/null || echo 0)
    echo "   待处理任务: $TASKS"
else
    echo "   ❌ 未运行"
fi

# FieldMind应用
echo "4. FieldMind应用:"
if pgrep -x "FieldMind" > /dev/null; then
    echo "   ✅ 运行中"
else
    echo "   ❌ 未运行"
fi

echo ""
echo "=== 数据库统计 ==="
sqlite3 /Users/alwan/FieldMind/backend/src/data/fieldmind.db << SQL
.mode column
SELECT 
    status,
    COUNT(*) as count,
    SUM(word_count) as total_words
FROM project_documents
GROUP BY status;
SQL

echo ""
echo "=== 最近日志 ==="
echo "后端API (最后5行):"
tail -5 /tmp/backend.log 2>/dev/null || echo "  无日志"
echo ""
echo "Celery (最后5行):"
tail -5 /tmp/celery.log 2>/dev/null || echo "  无日志"
EOF

chmod +x /Users/alwan/monitor_fieldmind.sh
```

---

## 下一步

1. ✅ **完成第1-4步** - 安装依赖并验证系统
2. ✅ **重新处理所有文档** - 使用第5步的方法
3. ✅ **配置自动启动** - 使用launchd或tmux
4. ✅ **测试完整工作流** - 上传新文档 → 自动处理 → 查看结果

---

## 联系支持

如果遇到问题，请提供：
1. 错误截图或日志
2. Redis状态：`redis-cli ping`
3. Celery日志：`tail -50 /tmp/celery.log`
4. 后端日志：`tail -50 /tmp/backend.log`
