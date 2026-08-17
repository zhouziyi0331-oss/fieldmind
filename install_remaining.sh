#!/bin/bash

# 待安装组件列表
declare -a COMPONENTS=(
    "reverse-skill|https://github.com/zhaoxuya520/reverse-skill.git|逆向技能|🔧工具"
    "Awesome-Self-Evolving-Agents|https://github.com/EvoAgentX/Awesome-Self-Evolving-Agents.git|自进化Agent资源|🤖Agent"
    "OpenViking|https://github.com/volcengine/OpenViking.git|火山引擎开源模型|🧠模型"
    "rust-memory-container-cs|https://github.com/usagi/rust-memory-container-cs.git|Rust内存容器|💾内存"
    "HyperAgents|https://github.com/facebookresearch/HyperAgents.git|Meta超级Agent|🤖Agent"
    "ANR-WatchDog|https://github.com/SalomonBrys/ANR-WatchDog.git|Android ANR监控|📱移动"
    "gecco|https://github.com/xtuhcy/gecco.git|爬虫框架|🕷️爬虫"
    "browser-use|https://github.com/browser-use/browser-use.git|浏览器自动化|🌐浏览器"
    "deer-flow|https://github.com/bytedance/deer-flow.git|字节工作流|⚙️工作流"
    "awesome-knowledge-graph|https://github.com/husthuke/awesome-knowledge-graph.git|知识图谱资源|📚资源"
    "awesome-reinforcement-learning-zh|https://github.com/wwxFromTju/awesome-reinforcement-learning-zh.git|强化学习资源|📚资源"
    "fufan-chat-api|https://github.com/fufankeji/fufan-chat-api.git|富帆聊天API|💬API"
    "bigdata-growth|https://github.com/collabH/bigdata-growth.git|大数据资源|📚资源"
    "opencv|https://github.com/opencv/opencv.git|计算机视觉|👁️视觉"
    "letta-code|https://github.com/letta-ai/letta-code.git|Letta AI代码|🤖Agent"
    "codebase-memory-mcp|https://github.com/DeusData/codebase-memory-mcp.git|代码库记忆MCP|💾内存"
)

echo "========================================
📋 待安装组件分类分析
========================================
"

echo "🤖 Agent系统 (3个):"
echo "  - Awesome-Self-Evolving-Agents (资源集合)"
echo "  - HyperAgents (Meta研究)"
echo "  - letta-code (Letta AI)"
echo ""

echo "💾 记忆系统 (2个):"
echo "  - rust-memory-container-cs (Rust)"
echo "  - codebase-memory-mcp (MCP协议)"
echo ""

echo "🕷️ 爬虫/浏览器 (2个):"
echo "  - gecco (Java爬虫)"
echo "  - browser-use (浏览器自动化)"
echo ""

echo "⚙️ 工作流/工具 (2个):"
echo "  - deer-flow (字节工作流)"
echo "  - reverse-skill (逆向工具)"
echo ""

echo "👁️ 视觉处理 (1个):"
echo "  - opencv (计算机视觉 - 大型C++项目)"
echo ""

echo "📚 资源集合 (3个):"
echo "  - awesome-knowledge-graph"
echo "  - awesome-reinforcement-learning-zh"
echo "  - bigdata-growth"
echo ""

echo "🧠 模型/API (2个):"
echo "  - OpenViking (火山引擎)"
echo "  - fufan-chat-api"
echo ""

echo "📱 移动开发 (1个):"
echo "  - ANR-WatchDog (Android)"
echo ""

echo "========================================
💡 推荐安装优先级
========================================
"

echo "⭐⭐⭐ 核心推荐 (对FieldMind最重要):"
echo "  1. browser-use - 浏览器自动化 (Web采集必需)"
echo "  2. letta-code - Letta AI (Agent系统)"
echo "  3. codebase-memory-mcp - 代码库记忆 (知识管理)"
echo "  4. deer-flow - 工作流引擎 (流程编排)"
echo "  5. HyperAgents - Meta Agent研究 (前沿技术)"
echo ""

echo "⭐⭐ 强烈推荐:"
echo "  6. gecco - Java爬虫 (数据采集)"
echo "  7. OpenViking - 火山引擎模型 (中文NLP)"
echo "  8. awesome-knowledge-graph - 知识图谱资源"
echo ""

echo "⭐ 可选:"
echo "  9. Awesome-Self-Evolving-Agents - 资源集合"
echo "  10. rust-memory-container-cs - Rust内存"
echo "  11. reverse-skill - 逆向工具"
echo "  12. fufan-chat-api - 聊天API"
echo "  13. awesome-reinforcement-learning-zh - 资源"
echo "  14. bigdata-growth - 资源"
echo ""

echo "⚠️ 需要特殊处理:"
echo "  - opencv: 超大型C++项目，建议pip install opencv-python"
echo "  - ANR-WatchDog: Android专用，macOS不适用"
echo ""

