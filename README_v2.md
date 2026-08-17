# FieldMind - 田野调查知识管理系统

<div align="center">

**智能化的田野调查知识管理平台**

[![Status](https://img.shields.io/badge/status-active-success.svg)]()
[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)]()
[![License](https://img.shields.io/badge/license-MIT-green.svg)]()

</div>

---

## 📖 简介

FieldMind 是一个专为人类学、社会学等领域研究者设计的田野调查知识管理系统。它通过 AI 技术帮助研究者管理大量的田野调查资料，提供智能分析、长期记忆和自进化的 AI 助手。

### 核心特性

- 🎯 **项目完全隔离** - 每个项目拥有独立的数据空间
- 🧠 **长期记忆系统** - 基于 Mem0 的智能记忆管理
- 🤖 **自进化 AI Agent** - 基于项目资料自动学习和构建技能框架
- 📄 **多格式文档支持** - 支持 14+ 种文档格式自动转换
- 💬 **深度思考对话** - Claude 3.7 Sonnet 提供专业级 AI 对话
- 📊 **数据可视化** - 项目统计、记忆分析、知识图谱（开发中）

---

## 🚀 快速开始

### 1. 启动后端

```bash
cd /Users/alwan/FieldMind-Rebuild/fieldmind-backend
python3 -m uvicorn app.main_simple:app --reload --host 0.0.0.0 --port 8000
```

### 2. 启动前端

```bash
cd /Users/alwan/FieldMind-Rebuild/fieldmind-web
npm run dev
```

### 3. 访问应用

- 🌐 **前端界面**: http://localhost:3000
- 📝 **API 文档**: http://localhost:8000/docs
- 🔍 **健康检查**: http://localhost:8000/health

---

## 📊 功能状态

| 功能 | 状态 | 说明 |
|------|------|------|
| 项目管理 | ✅ | 完全可用 |
| 文档上传 | ✅ | 支持14+格式 |
| 文档转换 | ✅ | MarkItDown自动转换 |
| 长期记忆 | ✅ | Mem0集成 |
| AI对话 | ⚠️ | 需API密钥 |
| 智能分析 | ⚠️ | 需API密钥 |
| 知识图谱 | 🚧 | 开发中 |
| 时间线 | 🚧 | 开发中 |

---

## 🛠️ 技术栈

**后端**: FastAPI + PostgreSQL + Mem0 + Claude AI  
**前端**: React + TypeScript + Tailwind CSS + React Query  
**文档处理**: MarkItDown  
**向量存储**: ChromaDB

---

## 📚 文档

- [集成报告](./INTEGRATION_REPORT.md) - 详细技术实现
- [演示总结](./DEMO_SUMMARY.md) - 功能演示
- [交付总结](./DELIVERY_SUMMARY.md) - 项目交付清单

---

## 🧪 快速测试

```bash
# 系统状态检查
./system_status.sh

# 功能测试
./quick_test.sh
```

---

## ⚙️ 配置 API 密钥（可选）

如需使用 AI 功能：

```bash
cd fieldmind-backend
cat > .env << 'EOF'
ANTHROPIC_API_KEY=your-key-here
OPENAI_API_KEY=your-key-here
EOF
```

---

## 📝 版本

**v2.0.0** (2026-07-31)
- ✨ 项目隔离系统
- ✨ Mem0 长期记忆
- ✨ 智能 Agent
- ✨ 动态前端

---

<div align="center">

**Made with ❤️ by the FieldMind Team**

</div>
