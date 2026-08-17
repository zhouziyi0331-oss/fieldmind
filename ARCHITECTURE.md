# FieldMind田野调查知识管理系统 - 系统架构设计

## 📋 目录
1. [系统概述](#系统概述)
2. [技术栈](#技术栈)
3. [三层架构](#三层架构)
4. [核心模块设计](#核心模块设计)
5. [数据流](#数据流)
6. [部署架构](#部署架构)

---

## 系统概述

**FieldMind** 是一个面向田野调查的智能知识管理系统，采用 **Swift (前端) + Python (后端) + React (Web管理)** 三层架构，支持多模态数据采集、AI辅助分析和知识图谱构建。

### 核心特性
- 🎤 **多模态采集**：音视频、文本、图片、PDF、网页
- 🧠 **AI辅助分析**：RAG、知识图谱、主题建模
- 🔍 **智能搜索**：向量检索 + 全文搜索 + 图搜索
- 📊 **数据可视化**：地图、时间线、关系图
- 🤖 **Agent系统**：自动化工作流、多Agent协作
- 🔐 **数据安全**：端到端加密、本地优先

---

## 技术栈

### 前端层 (iOS/macOS App)
```swift
- Swift 6 + SwiftUI
- Combine (响应式编程)
- CoreData (本地数据持久化)
- AVFoundation (音视频采集)
- CoreML (端侧AI推理)
- Alamofire (网络请求)
```

### 后端层 (Python AI引擎)
```python
- FastAPI (API框架)
- SQLAlchemy + PostgreSQL (关系数据库)
- Neo4j (知识图谱)
- ChromaDB + FAISS (向量数据库)
- LangChain (AI框架)
- Whisper (语音转录)
- OpenCV (图像处理)
- Elasticsearch (全文搜索)
```

### Web管理层 (管理后台)
```javascript
- React 18 + TypeScript
- Ant Design / shadcn/ui
- React Query (数据管理)
- Recharts / Plotly (可视化)
- Vite (构建工具)
```

---

## 三层架构

```
┌─────────────────────────────────────────────────────────┐
│                    iOS/macOS App (Swift)                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │采集模块  │  │查看模块  │  │搜索模块  │  │设置模块 │ │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │
│                     ▲ CoreData (本地缓存)                │
└─────────────────────┼───────────────────────────────────┘
                      │ REST API / WebSocket
┌─────────────────────┼───────────────────────────────────┐
│              Python Backend (FastAPI)                    │
│  ┌───────────────────────────────────────────────────┐  │
│  │                  API Gateway                      │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │AI引擎    │  │RAG系统   │  │知识图谱  │  │工作流   │ │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │
│  ┌─────────────────────────────────────────────────────┐│
│  │     数据层: PostgreSQL + Neo4j + ChromaDB          ││
│  └─────────────────────────────────────────────────────┘│
└─────────────────────┼───────────────────────────────────┘
                      │ REST API
┌─────────────────────┼───────────────────────────────────┐
│              Web Admin (React)                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │数据管理  │  │可视化    │  │用户管理  │  │系统监控 │ │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## 核心模块设计

### 1. 数据采集模块

#### 1.1 音视频采集 (Swift)
```swift
// AudioRecorder.swift
class AudioRecorder {
    - AVAudioRecorder
    - 实时波形显示
    - 自动分段 (5分钟/段)
    - 后台录音支持
}

// VideoRecorder.swift
class VideoRecorder {
    - AVCaptureSession
    - 压缩编码 (H.264)
    - 元数据标注 (GPS, 时间戳)
}
```

#### 1.2 文本输入 (Swift)
```swift
// TextEditor.swift
- Markdown编辑器
- 语音输入转文本
- 富文本格式
- 自动保存
```

#### 1.3 网页剪藏 (Python + Swift)
```python
# web_clipper.py
- firecrawl: 网页抓取
- crawl4ai: 内容提取
- browser-use: 动态网页
→ 输出: Markdown + 元数据
```

#### 1.4 PDF处理 (Python)
```python
# pdf_processor.py
- pdfplumber: 文本提取
- PyMuPDF: 布局分析
- PDF-Guru: 表格识别
→ 输出: 结构化文本
```

---

### 2. AI分析模块

#### 2.1 语音转录 (Python)
```python
# transcription_service.py
from whisper import load_model

class TranscriptionService:
    - Whisper large-v3
    - 中文优化
    - 说话人分离 (pyannote)
    - 时间戳对齐
```

#### 2.2 RAG系统 (Python)
```python
# rag_engine.py
from langchain import RAG

class RAGEngine:
    - 文档分块 (RecursiveCharacterTextSplitter)
    - 向量化 (sentence-transformers)
    - ChromaDB存储
    - 检索增强生成
    
    方法:
    - ingest(documents) → 索引文档
    - query(question) → 回答问题
    - cite_sources() → 来源追溯
```

#### 2.3 知识图谱 (Python + Neo4j)
```python
# knowledge_graph.py
from neo4j import GraphDatabase

class KnowledgeGraph:
    - 实体抽取 (HanLP)
    - 关系识别 (graphiti)
    - Neo4j存储
    - 图推理
    
    数据模型:
    - 人物 (Person)
    - 地点 (Location)
    - 事件 (Event)
    - 概念 (Concept)
    - 关系 (Relationship)
```

#### 2.4 主题建模 (Python)
```python
# topic_modeling.py
from bertopic import BERTopic

class TopicModeler:
    - BERTopic主题提取
    - 动态主题演化
    - 可视化输出
```

---

### 3. 搜索模块

#### 3.1 多模式搜索 (Python)
```python
# search_engine.py

class UnifiedSearch:
    def search(query, mode):
        if mode == "semantic":
            return vector_search(query)  # ChromaDB
        elif mode == "fulltext":
            return fulltext_search(query)  # Whoosh/Elasticsearch
        elif mode == "graph":
            return graph_search(query)  # Neo4j
        else:
            return hybrid_search(query)  # 融合三种
```

#### 3.2 向量搜索 (Python)
```python
# vector_search.py
import chromadb

class VectorSearch:
    - sentence-transformers嵌入
    - ChromaDB + FAISS混合
    - 相似度排序
    - 过滤器支持
```

---

### 4. 可视化模块

#### 4.1 地图可视化 (Python + React)
```python
# map_visualization.py
import folium

class MapVisualizer:
    - 田野调查地点标注
    - 轨迹回放
    - 热力图
    - 导出HTML
```

#### 4.2 关系图可视化 (Python + React)
```python
# graph_visualization.py
from pyvis.network import Network

class GraphVisualizer:
    - Neo4j数据导出
    - 交互式网络图
    - 力导向布局
```

#### 4.3 时间线可视化 (React)
```javascript
// Timeline.tsx
- 事件时间线
- 多维度筛选
- 时间轴缩放
```

---

### 5. Agent系统

#### 5.1 工作流引擎 (Python)
```python
# workflow_engine.py
from deer_flow import Workflow

class WorkflowEngine:
    workflows = {
        "auto_transcribe": [
            "检测新音频",
            "Whisper转录",
            "生成摘要",
            "提取关键词",
            "更新知识图谱"
        ],
        "web_research": [
            "输入主题",
            "多源搜索",
            "内容提取",
            "RAG索引",
            "生成报告"
        ]
    }
```

#### 5.2 多Agent协作 (Python)
```python
# agents.py
from autogen import AssistantAgent, UserProxyAgent

class AgentTeam:
    - ResearchAgent: 信息搜集
    - AnalysisAgent: 数据分析
    - SummaryAgent: 报告生成
    - QAAgent: 质量检查
```

---

### 6. 数据安全模块

#### 6.1 加密存储 (Python + Swift)
```python
# encryption.py
from cryptography.fernet import Fernet

class EncryptionService:
    - AES-256加密
    - 密钥管理 (Keychain)
    - 端到端加密
```

#### 6.2 权限管理 (Python)
```python
# auth.py
from fastapi_users import FastAPIUsers

class AuthService:
    - JWT认证
    - RBAC权限
    - 会话管理
```

---

## 数据流

### 典型场景1: 田野访谈录音处理
```
[用户录音] → Swift App
    ↓ 上传 (分块传输)
[Python Backend]
    ↓ Whisper转录
[文本 + 时间戳]
    ↓ 并行处理
    ├─→ RAG索引 (ChromaDB)
    ├─→ 实体抽取 (HanLP) → 知识图谱 (Neo4j)
    ├─→ 主题建模 (BERTopic)
    └─→ 存储 (PostgreSQL)
    ↓
[Swift App] ← 结果推送 (WebSocket)
```

### 典型场景2: 跨模态检索
```
[用户输入问题] → Swift App
    ↓ API请求
[Python Backend - UnifiedSearch]
    ↓ 并行检索
    ├─→ 向量搜索 (ChromaDB) - 语义相似
    ├─→ 全文搜索 (Whoosh) - 关键词匹配
    └─→ 图搜索 (Neo4j) - 关系推理
    ↓ 结果融合 + 重排序
[RAG生成回答] + [来源引用]
    ↓
[Swift App] ← 显示结果
```

---

## 部署架构

### 开发环境
```
┌─────────────────┐
│  macOS/iOS      │
│  - Xcode 16     │
│  - Swift 6      │
└────────┬────────┘
         │
┌────────┴────────┐
│  本地Python服务  │
│  - FastAPI      │
│  - PostgreSQL   │
│  - Neo4j        │
│  - ChromaDB     │
└─────────────────┘
```

### 生产环境
```
┌─────────────────┐
│  iOS/macOS App  │
└────────┬────────┘
         │ HTTPS
┌────────┴────────────────┐
│  Nginx (反向代理)       │
└────────┬────────────────┘
         │
┌────────┴────────────────┐
│  Docker Compose         │
│  ┌──────────────────┐   │
│  │ FastAPI (Gunicorn)│  │
│  ├──────────────────┤   │
│  │ PostgreSQL       │   │
│  ├──────────────────┤   │
│  │ Neo4j            │   │
│  ├──────────────────┤   │
│  │ ChromaDB         │   │
│  ├──────────────────┤   │
│  │ Redis (缓存)     │   │
│  └──────────────────┘   │
└─────────────────────────┘
```

### 云部署选项
- **自托管**: Docker Compose on VPS
- **托管服务**:
  - DB: Supabase (PostgreSQL)
  - Graph: Neo4j Aura
  - Vector: Pinecone / Weaviate Cloud
  - API: Railway / Fly.io

---

## API设计

### RESTful API端点
```
POST   /api/v1/audio/upload          # 上传音频
POST   /api/v1/transcribe             # 转录请求
GET    /api/v1/documents/{id}        # 获取文档
POST   /api/v1/search                 # 统一搜索
POST   /api/v1/rag/query              # RAG问答
GET    /api/v1/knowledge-graph/entities  # 实体列表
POST   /api/v1/knowledge-graph/query # 图查询
POST   /api/v1/workflows/execute     # 执行工作流
```

### WebSocket端点
```
WS     /ws/transcription/{task_id}   # 实时转录进度
WS     /ws/notifications              # 系统通知
```

---

## 性能优化

### 1. 缓存策略
- **Redis**: API响应缓存 (5分钟)
- **CoreData**: Swift本地缓存
- **向量缓存**: ChromaDB持久化

### 2. 异步处理
- **Celery**: 后台任务队列
- **WebSocket**: 实时进度推送
- **批处理**: 夜间批量处理

### 3. 数据压缩
- **音频**: AAC 64kbps
- **视频**: H.264 720p
- **图片**: WebP格式

---

## 扩展性设计

### 插件系统
```python
# plugins/base.py
class FieldMindPlugin:
    def on_document_created(doc):
        pass
    
    def on_search_query(query):
        pass
```

### 示例插件
1. **方言识别插件**: 自动检测方言类型
2. **OCR插件**: 图片文字识别
3. **导出插件**: 多格式导出 (Word, PDF, LaTeX)

---

## 下一步开发计划

### 第一阶段 (2周)
- ✅ 环境搭建
- ⏳ Swift项目初始化
- ⏳ FastAPI基础框架
- ⏳ 数据库设计

### 第二阶段 (4周)
- ⏳ 音视频采集功能
- ⏳ Whisper集成
- ⏳ RAG系统实现
- ⏳ 基础搜索功能

### 第三阶段 (4周)
- ⏳ 知识图谱构建
- ⏳ Agent系统
- ⏳ Web管理后台
- ⏳ 数据可视化

### 第四阶段 (2周)
- ⏳ 性能优化
- ⏳ 安全加固
- ⏳ 测试部署

---

**最后更新**: 2026-07-29
