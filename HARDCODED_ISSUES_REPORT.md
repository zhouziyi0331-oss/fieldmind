# FieldMind 硬编码问题详细报告

**生成时间**: 2026-08-09  
**扫描范围**: 前端 + 后端全部代码

---

## 🔴 严重问题：大量硬编码 API 端点

### 前端硬编码（FieldMind.app）

#### 问题 1: 端口号不统一

发现 **3 个不同的端口号**：

| 文件 | 硬编码 | 问题 |
|------|--------|------|
| `api.js:8` | `http://localhost:5000` | ❌ 端口 5000 |
| `fieldmind_api.js:6` | `http://127.0.0.1:5001` | ❌ 端口 5001 |
| `fieldmind_frontend.js:7` | `http://localhost:5001/api` | ❌ 端口 5001 |
| `index.html` (多处) | `http://localhost:8000` | ❌ 端口 8000 |
| `vite.config.js:16` | `http://localhost:8765` | ❌ 端口 8765 (MinerU) |

**影响**: 
- 前端无法连接到正确的后端
- 不同页面调用不同端口
- 开发/生产环境切换困难

#### 问题 2: index.html 中的 26+ 处硬编码

```javascript
// 示例（index.html 中的硬编码）
行 4705: fetch('http://localhost:8000/api/v1/projects/', ...)
行 4741: fetch('http://localhost:8000/api/v1/projects/')
行 4955: xhr.open('POST', 'http://localhost:8000/api/documents/upload')
行 5057: fetch(`http://localhost:8000/api/documents/${doc.id}`)
行 5166: fetch(`http://localhost:8000/api/v1/projects/${projectId}/documents/`)
行 5324: fetch(`http://localhost:8000/api/v1/projects/${projectId}/keywords`)
行 5345: fetch(`http://localhost:8000/api/v1/projects/${projectId}/veins`)
行 5366: fetch(`http://localhost:8000/api/v1/projects/${projectId}/documents/`)
行 5433: fetch(`http://localhost:8000/api/v1/projects/${projectId}/`)
行 7385: fetch(`http://localhost:8000/api/documents/status?project_id=...`)
行 7498: fetch('http://localhost:8000/api/documents/knowledge-base/status')
行 15982: fetch(`http://localhost:8000/api/documents/aggregate/keywords?...`)
行 16100: fetch(`http://localhost:8000/api/documents/aggregate/skills?...`)
行 16249: fetch(`http://localhost:8000/api/dashboard/stats/${projectId}`)
行 16286: fetch(`http://localhost:8000/api/dashboard/progress/${projectId}`)
行 16326: fetch(`http://localhost:8000/api/dashboard/timeline/${projectId}?...`)
行 16364: fetch('http://localhost:8000/api/chat-rag/query', ...)
行 16418: fetch('http://localhost:8000/api/reports/generate', ...)
... 还有更多
```

---

### 后端硬编码（backend/src/app）

#### 问题 3: 数据库连接硬编码（30+ 处）

```python
# PostgreSQL
config.py:44:    POSTGRES_HOST: str = "localhost"
core/config.py:21:    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
core/config/settings.py:24:    host: str = Field(default="localhost")

# Neo4j
config.py:49:    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
core/config.py:30:    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
core/config/settings.py:57:    uri: str = Field(default="bolt://localhost:7687")
tasks/rag_tasks.py:102:        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
tasks/graph_tasks.py:77:        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
tasks/graph_tasks.py:144:        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
tasks/graph_tasks.py:186:        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")

# Redis
celery_app.py:9:    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
config.py:54:    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
core/config.py:35:    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
core/config/settings.py:77:    host: str = Field(default="localhost")
tasks/document_tasks.py:21:    broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0')
tasks/document_tasks.py:22:    backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# ChromaDB
config.py:63:    CHROMADB_HOST: str = os.getenv("CHROMADB_HOST", "localhost")
core/config.py:40:    CHROMADB_HOST: str = os.getenv("CHROMADB_HOST", "localhost")
core/config/settings.py:100:    host: str = Field(default="localhost")
```

#### 问题 4: 第三方服务硬编码

```python
# RAGFlow
config.py:104:    RAGFLOW_API_URL: str = os.getenv("RAGFLOW_API_URL", "http://localhost:9380")
core/config.py:64:    RAGFLOW_API_URL: str = os.getenv("RAGFLOW_API_URL", "http://localhost:9380")
core/config/settings.py:129:    ragflow_api_url: str = Field(default="http://localhost:9380")

# Ollama
tasks/rag_tasks.py:306:    os.getenv("OLLAMA_API_URL", "http://localhost:11434/api/generate")
agents/crew_config.py:26:    "base_url": os.getenv("OLLAMA_API_URL", "http://localhost:11434")
workflows/integration.py:587:    os.getenv("OLLAMA_API_URL", "http://localhost:11434") + "/api/generate"

# MinerU (文档解析)
services/document_parser.py:25:    mineru_url: str = "http://localhost:8765"
services/document_parser.py:373:    mineru_url: str = "http://localhost:8765"
```

#### 问题 5: CORS 配置硬编码

```python
config.py:29-34:
    "http://localhost:3000,http://localhost:5173,capacitor://localhost,ionic://localhost"
    "http://localhost:3000",  # React Web
    "http://localhost:5173",  # Vite dev server
    "capacitor://localhost",  # iOS App
    "ionic://localhost",

core/config/settings.py:200:
    cors_origins: List[str] = Field(default=["http://localhost:3000"])
```

---

## 📊 硬编码统计

| 类别 | 数量 | 严重程度 |
|------|------|----------|
| **前端 API 端点** | 26+ | 🔴 严重 |
| **后端数据库连接** | 30+ | 🔴 严重 |
| **第三方服务 URL** | 8+ | 🟠 中等 |
| **CORS 配置** | 6+ | 🟡 轻微 |
| **TODO/FIXME 标记** | 26+ | 🟡 轻微 |

**总计**: 96+ 处硬编码

---

## 🛠️ 修复方案

### 方案 1: 前端统一配置（推荐）

创建环境配置文件：

```javascript
// FieldMind.app/Contents/Resources/config.js
const CONFIG = {
    API_BASE_URL: process.env.API_BASE_URL || 'http://localhost:8000',
    WS_URL: process.env.WS_URL || 'ws://localhost:8000/ws',
    MINERU_URL: process.env.MINERU_URL || 'http://localhost:8765',
};

// 自动检测环境
if (window.location.hostname !== 'localhost') {
    CONFIG.API_BASE_URL = `https://${window.location.hostname}/api`;
    CONFIG.WS_URL = `wss://${window.location.hostname}/ws`;
}

window.FIELDMIND_CONFIG = CONFIG;
```

然后全局替换：
```javascript
// 替换前
fetch('http://localhost:8000/api/v1/projects/')

// 替换后
fetch(`${window.FIELDMIND_CONFIG.API_BASE_URL}/api/v1/projects/`)
```

---

### 方案 2: 后端环境变量（已部分实现）

后端已经使用 `os.getenv()` 但缺少统一管理。

#### 创建 `.env` 模板：

```bash
# .env.example

# === 后端配置 ===
API_HOST=0.0.0.0
API_PORT=8000

# === 数据库配置 ===
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=fieldmind
POSTGRES_PASSWORD=your_password_here
POSTGRES_DB=fieldmind

# === Neo4j 配置 ===
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password_here

# === Redis 配置 ===
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_URL=redis://localhost:6379/0

# === ChromaDB 配置 ===
CHROMADB_HOST=localhost
CHROMADB_PORT=8100

# === 第三方服务 ===
OLLAMA_API_URL=http://localhost:11434
RAGFLOW_API_URL=http://localhost:9380
MINERU_API_URL=http://localhost:8765

# === CORS 配置 ===
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# === AI 模型配置 ===
LLM_MODEL=qwen2.5:32b
EMBEDDING_MODEL=bge-large-zh-v1.5
```

---

### 方案 3: 配置管理器（长期方案）

```python
# backend/src/app/core/config_manager.py

from pydantic import BaseSettings
from typing import List, Optional
import os

class DatabaseConfig(BaseSettings):
    """数据库配置"""
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    neo4j_uri: str = "bolt://localhost:7687"
    redis_url: str = "redis://localhost:6379/0"
    chromadb_host: str = "localhost"
    
    class Config:
        env_file = ".env"
        env_prefix = "DB_"

class ServiceConfig(BaseSettings):
    """第三方服务配置"""
    ollama_url: str = "http://localhost:11434"
    ragflow_url: str = "http://localhost:9380"
    mineru_url: str = "http://localhost:8765"
    
    class Config:
        env_file = ".env"
        env_prefix = "SERVICE_"

class APIConfig(BaseSettings):
    """API 配置"""
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: List[str] = ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"
        env_prefix = "API_"

# 全局配置实例
config = {
    "database": DatabaseConfig(),
    "services": ServiceConfig(),
    "api": APIConfig(),
}
```

---

## ⚡ 快速修复脚本

### 步骤 1: 前端统一 API 端点

```bash
#!/bin/bash
# fix_frontend_hardcode.sh

cd ~/FieldMind/FieldMind.app/Contents/Resources

# 备份
cp index.html index.html.backup

# 全局替换
sed -i '' 's|http://localhost:5000|${API_BASE_URL}|g' api.js
sed -i '' 's|http://127.0.0.1:5001|${API_BASE_URL}|g' fieldmind_api.js
sed -i '' 's|http://localhost:5001|${API_BASE_URL}|g' fieldmind_frontend.js
sed -i '' 's|http://localhost:8000|${API_BASE_URL}|g' index.html

echo "✅ 前端硬编码已修复"
```

### 步骤 2: 生成 .env 文件

```bash
#!/bin/bash
# generate_env.sh

cat > ~/FieldMind/.env << 'EOF'
# FieldMind 环境配置
API_HOST=0.0.0.0
API_PORT=8000

POSTGRES_HOST=localhost
NEO4J_URI=bolt://localhost:7687
REDIS_HOST=localhost
CHROMADB_HOST=localhost

OLLAMA_API_URL=http://localhost:11434
RAGFLOW_API_URL=http://localhost:9380
MINERU_API_URL=http://localhost:8765

CORS_ORIGINS=http://localhost:3000,http://localhost:5173
EOF

echo "✅ .env 文件已生成"
```

---

## 🎯 修复优先级

### 🔴 高优先级（今天完成）

1. **统一前端 API 端点** → 解决端口混乱问题
2. **创建 .env 配置文件** → 集中管理所有配置
3. **修复 index.html 中的硬编码** → 26+ 处 fetch 调用

### 🟠 中优先级（本周完成）

4. **后端配置统一** → 使用配置管理器
5. **CORS 配置优化** → 支持动态域名
6. **第三方服务配置** → MinerU、Ollama 等

### 🟡 低优先级（本月完成）

7. **清理 TODO/FIXME** → 26 处标记
8. **代码质量提升** → 重构硬编码逻辑
9. **文档更新** → 配置说明文档

---

## 💡 预期效果

修复后的效果：

### ✅ 开发环境
```bash
# 本地开发
API_BASE_URL=http://localhost:8000 npm run dev
```

### ✅ 生产环境
```bash
# 服务器部署
API_BASE_URL=https://api.fieldmind.com npm run build
```

### ✅ Docker 部署
```yaml
version: '3.8'
services:
  backend:
    environment:
      - API_PORT=8000
      - POSTGRES_HOST=postgres
      - NEO4J_URI=bolt://neo4j:7687
```

---

## 📈 工作量估算

| 任务 | 预计时间 | 难度 |
|------|----------|------|
| 前端配置统一 | 2h | 🟢 简单 |
| 后端 .env 配置 | 1h | 🟢 简单 |
| index.html 批量替换 | 1h | 🟢 简单 |
| 配置管理器开发 | 3h | 🟡 中等 |
| 全面测试 | 2h | 🟡 中等 |

**总计**: 约 9 小时

---

## 下一步

**请确认是否立即开始修复？**

1. ✅ 是 → 我立即开始修复前端硬编码
2. ⏸️ 否 → 请告诉我优先级调整
