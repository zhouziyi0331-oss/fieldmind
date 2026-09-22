#!/usr/bin/env python3
"""
阶段1：注册所有未注册的核心API模块
"""

REGISTRATION_CODE = """
# ============================================================================
# 注册未注册的核心API (添加到 src/app/main.py)
# ============================================================================

# 1. 导入语句（添加到imports部分）
from app.api import memory, timeline, tables, proposal, photos
from app.api.v1 import super_agents, tasks, topic_analysis, sop
from app.api.v1 import chunks_quantification, dashboard_optimized
from app.api.routes import agent_pipeline
from app.api import export_summaries, file_summaries, quantification
from app.api import websocket, monitoring

# 2. 路由注册（添加到路由注册部分）

# 核心功能API
app.include_router(memory.router, prefix="/api/memory", tags=["记忆管理"])
app.include_router(timeline.router, prefix="/api/timeline", tags=["时间线"])
app.include_router(tables.router, prefix="/api/tables", tags=["表格处理"])
app.include_router(proposal.router, prefix="/api/proposal", tags=["方案生成"])
app.include_router(photos.router, prefix="/api/photos", tags=["图片管理"])

# V1核心API
app.include_router(super_agents.router, prefix="/api/v1/super-agents", tags=["超级Agent"])
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["任务管理"])
app.include_router(topic_analysis.router, prefix="/api/v1/topic-analysis", tags=["主题分析"])
app.include_router(sop.router, prefix="/api/v1/sop", tags=["标准作业程序"])

# 增强功能API
app.include_router(chunks_quantification.router, prefix="/api/v1/chunks-quantification", tags=["块量化"])
app.include_router(dashboard_optimized.router, prefix="/api/v1/dashboard-optimized", tags=["优化Dashboard"])

# 工具API
app.include_router(agent_pipeline.router, prefix="/api/agent-pipeline", tags=["Agent流水线"])
app.include_router(export_summaries.router, prefix="/api/export", tags=["导出摘要"])
app.include_router(file_summaries.router, prefix="/api/file-summaries", tags=["文件摘要"])
app.include_router(quantification.router, prefix="/api/quantification", tags=["数据量化"])

# 通信API
app.include_router(websocket.router, prefix="/api/websocket", tags=["WebSocket"])
app.include_router(monitoring.router, prefix="/api/monitoring", tags=["系统监控"])
"""

print("="*80)
print("阶段1: 注册未注册的API模块")
print("="*80)
print("\n需要注册的模块:")
print("  核心功能: memory, timeline, tables, proposal, photos, super_agents, agent_pipeline")
print("  增强功能: tasks, topic_analysis, sop, chunks_quantification, dashboard_optimized")
print("  工具功能: export_summaries, file_summaries, quantification, websocket, monitoring")
print(f"\n总计: 17个模块")
print("\n注册代码已生成，保存到: API_REGISTRATION_CODE.txt")

with open("API_REGISTRATION_CODE.txt", "w", encoding="utf-8") as f:
    f.write(REGISTRATION_CODE)

print("\n✅ 完成!")
