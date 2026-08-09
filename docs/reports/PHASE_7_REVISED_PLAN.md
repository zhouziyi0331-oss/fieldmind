# Phase 7 修订版：AI生态集成计划

## 📋 综合分析与优先级

### 原计划库（8个）
| 库 | 状态 | 优先级 | 理由 |
|---|------|--------|------|
| ImageBind | ✅ 已集成 | - | 多模态基础 |
| AutoRAG | 📦 已克隆 | 低 | RAG优化 |
| KAG | 📦 已克隆 | 低 | 知识图谱增强 |
| n8n | 📦 已克隆 | 低 | UI工作流 |
| langchain | ⏳ 待克隆 | 中 | LLM编排框架 |
| unstructured | ⏳ 待克隆 | 🔴 高 | 文档处理核心 |
| ragas | ⏳ 待克隆 | 🔴 高 | RAG评估 |
| lm-evaluation-harness | ⏳ 待克隆 | 低→弃用 | 被deepeval替代 |

### 新增库分析（14个）

#### 🔴 **必须安装（9个）**

1. **sentence-transformers** ⭐⭐⭐⭐⭐
   - 用途：句子嵌入，与现有向量存储完美集成
   - 集成点：Phase 4数据层、Phase 7.2多模态
   - 优势：支持中文，多种预训练模型

2. **FunASR** ⭐⭐⭐⭐⭐
   - 用途：阿里达摩院语音识别，中文优化
   - 集成点：补充ImageBind音频能力
   - 优势：工业级、中文场景优化

3. **PaddleOCR** ⭐⭐⭐⭐⭐
   - 用途：百度OCR，图像文字识别
   - 集成点：多模态文档处理
   - 优势：中文OCR最强，轻量级

4. **HanLP** ⭐⭐⭐⭐⭐
   - 用途：中文NLP工具包
   - 集成点：Phase 3知识图谱、文本分析
   - 优势：中文分词、命名实体识别、依存句法

5. **pyannote-audio** ⭐⭐⭐⭐
   - 用途：说话人分离、语音活动检测
   - 集成点：音频分析场景
   - 优势：会议转录、多人对话分析

6. **deepeval** ⭐⭐⭐⭐
   - 用途：现代LLM评估框架
   - 集成点：替代lm-evaluation-harness
   - 优势：更现代、易用、支持RAG评估

7. **celery** ⭐⭐⭐⭐
   - 用途：分布式任务队列
   - 集成点：增强Phase 6事件驱动
   - 优势：成熟、可扩展、支持异步

8. **unstructured** ⭐⭐⭐⭐（原计划）
   - 用途：非结构化文档处理
   - 集成点：文档解析核心
   - 优势：支持PDF、Word、HTML等

9. **ragas** ⭐⭐⭐⭐（原计划）
   - 用途：RAG系统评估
   - 集成点：Phase 2 RAG质量监控
   - 优势：专门针对RAG场景

#### 🟡 **推荐安装（3个）**

10. **noScribe** ⭐⭐⭐
    - 用途：音频转录工具
    - 集成点：音频处理工作流
    - 理由：提供完整转录方案

11. **hamilton** ⭐⭐⭐
    - 用途：数据流编排框架
    - 集成点：与celery配合
    - 理由：声明式数据管道

12. **langchain** ⭐⭐⭐（原计划）
    - 用途：LLM应用框架
    - 集成点：现有LLM层包装
    - 理由：生态丰富，但可能过重

#### ⚪ **不推荐（2个）**

13. **lac** - 被HanLP替代
14. **Skeleton** - CSS框架，无关

#### ❌ **已有/弃用（3个）**

15. **pydantic** - 项目已使用
16. **lm-evaluation-harness** - 被deepeval替代
17. **n8n** - UI工作流，后端不需要

---

## 🎯 最终安装计划

### Phase 7.3-7.14 集成路线图（12个子阶段）

| Phase | 库 | 优先级 | 代码量 | 时间 | 核心功能 |
|-------|---|--------|--------|------|----------|
| 7.3 | **sentence-transformers** | 🔴 | 800行 | 1天 | 句子嵌入增强 |
| 7.4 | **unstructured** | 🔴 | 1000行 | 1.5天 | 文档解析 |
| 7.5 | **PaddleOCR** | 🔴 | 900行 | 1.5天 | OCR识别 |
| 7.6 | **FunASR** | 🔴 | 1000行 | 1.5天 | 语音识别 |
| 7.7 | **HanLP** | 🔴 | 800行 | 1天 | 中文NLP |
| 7.8 | **pyannote-audio** | 🔴 | 700行 | 1天 | 说话人分离 |
| 7.9 | **ragas** | 🔴 | 600行 | 1天 | RAG评估 |
| 7.10 | **deepeval** | 🔴 | 600行 | 1天 | LLM评估 |
| 7.11 | **celery** | 🔴 | 800行 | 1天 | 任务队列 |
| 7.12 | **noScribe** | 🟡 | 500行 | 0.5天 | 转录工作流 |
| 7.13 | **hamilton** | 🟡 | 600行 | 1天 | 数据编排 |
| 7.14 | **langchain** | 🟡 | 1200行 | 2天 | LLM框架 |

**总计**: 12个库，~9,500行代码，~14天

### 已克隆但低优先级（延后Phase 8）
- AutoRAG - Phase 8.1
- KAG - Phase 8.2
- n8n - Phase 8.3

---

## 📦 克隆命令清单

```bash
# 必须安装（9个）
git clone --depth 1 https://github.com/huggingface/sentence-transformers.git external_libs/sentence-transformers
git clone --depth 1 https://github.com/Unstructured-IO/unstructured.git external_libs/unstructured
git clone --depth 1 https://github.com/PaddlePaddle/PaddleOCR.git external_libs/PaddleOCR
git clone --depth 1 https://github.com/modelscope/FunASR.git external_libs/FunASR
git clone --depth 1 https://github.com/hankcs/HanLP.git external_libs/HanLP
git clone --depth 1 https://github.com/pyannote/pyannote-audio.git external_libs/pyannote-audio
git clone --depth 1 https://github.com/vibrantlabsai/ragas.git external_libs/ragas
git clone --depth 1 https://github.com/confident-ai/deepeval.git external_libs/deepeval
git clone --depth 1 https://github.com/celery/celery.git external_libs/celery

# 推荐安装（3个）
git clone --depth 1 https://github.com/kaixxx/noScribe.git external_libs/noScribe
git clone --depth 1 https://github.com/apache/hamilton.git external_libs/hamilton
git clone --depth 1 https://github.com/langchain-ai/langchain.git external_libs/langchain
```

---

## 🏗️ 集成架构

### 核心能力矩阵

| 能力域 | 涉及库 | 集成到Phase |
|--------|--------|-------------|
| **多模态嵌入** | sentence-transformers, ImageBind | Phase 4 + 7.2 |
| **文档处理** | unstructured, PaddleOCR | 新建 Phase 7 Documents |
| **语音处理** | FunASR, pyannote-audio, noScribe | 新建 Phase 7 Audio |
| **中文NLP** | HanLP | Phase 3 知识图谱 |
| **评估监控** | ragas, deepeval | Phase 2 + 新建监控 |
| **任务编排** | celery, hamilton | Phase 6 事件驱动 |
| **LLM框架** | langchain | Phase 1 LLM层 |

### 技术栈更新

```
现有系统 (Phase 1-6)
├── LLM: OpenAI, Anthropic
├── 向量: ChromaDB, Pinecone
├── 图谱: Neo4j
├── 数据库: PostgreSQL
├── 事件: FastAPI SSE
└── 多模态: ImageBind

新增 (Phase 7)
├── 嵌入: sentence-transformers ✨
├── 文档: unstructured + PaddleOCR ✨
├── 语音: FunASR + pyannote-audio ✨
├── 中文: HanLP ✨
├── 评估: ragas + deepeval ✨
├── 任务: celery ✨
├── 编排: hamilton ✨
└── 框架: langchain (可选)
```

---

## 🎬 立即行动：Phase 7.3

**目标**: sentence-transformers集成（最高优先级）

**理由**:
1. 与现有向量存储无缝集成
2. 代码量适中（800行）
3. 立即提升嵌入质量
4. 为后续库打基础

**关键任务**:
1. 克隆仓库 ✅
2. 研究核心API
3. 创建嵌入服务包装
4. 集成到Phase 4数据层
5. 支持中文模型
6. 编写测试用例
7. 性能对比测试

**预期成果**:
```python
from app.embeddings import SentenceTransformerEmbedding

# 多语言支持
embedder = SentenceTransformerEmbedding(model="paraphrase-multilingual-MiniLM-L12-v2")
vectors = embedder.embed(["Hello", "你好", "こんにちは"])

# 与现有ChromaDB集成
collection.add(embeddings=vectors, documents=docs)
```

---

## 📊 修订对比

| 指标 | 原计划 | 修订计划 | 变化 |
|------|--------|----------|------|
| 库数量 | 8个 | 12个 | +4个 |
| 代码量 | ~6,000行 | ~9,500行 | +58% |
| 时间 | ~10天 | ~14天 | +4天 |
| 必须库 | 5个 | 9个 | +4个 |
| 语音能力 | ❌ | ✅ 3个库 | 新增 |
| 中文能力 | ⚠️ 弱 | ✅ 强 | 显著增强 |
| OCR能力 | ❌ | ✅ PaddleOCR | 新增 |
| 评估能力 | ⚠️ 单一 | ✅ 双重 | ragas+deepeval |

---

## ✅ 决策总结

**新增核心能力**:
- ✨ 语音处理全栈（识别+分离+转录）
- ✨ 中文NLP深度支持
- ✨ OCR文档理解
- ✨ 句子嵌入增强
- ✨ 双重评估体系

**淘汰决策**:
- ❌ lm-evaluation-harness → deepeval更好
- ❌ lac → HanLP已包含
- ❌ n8n → celery+hamilton更适合
- ❌ Skeleton → 无关

**延后决策**:
- ⏸️ AutoRAG → Phase 8
- ⏸️ KAG → Phase 8
- ⏸️ langchain → Phase 7.14（最后）

---

**准备开始 Phase 7.3: sentence-transformers集成** 🚀
