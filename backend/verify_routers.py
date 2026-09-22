#!/usr/bin/env python3
"""验证每个模块是否有router"""
import sys
import os

modules = [
    ("src/app/api/memory.py", "memory"),
    ("src/app/api/timeline.py", "timeline"),
    ("src/app/api/tables.py", "tables"),
    ("src/app/api/proposal.py", "proposal"),
    ("src/app/api/photos.py", "photos"),
    ("src/app/api/v1/super_agents.py", "super_agents"),
    ("src/app/api/routes/agent_pipeline.py", "agent_pipeline"),
    ("src/app/api/v1/tasks.py", "tasks"),
    ("src/app/api/v1/topic_analysis.py", "topic_analysis"),
    ("src/app/api/v1/sop.py", "sop"),
    ("src/app/api/v1/chunks_quantification.py", "chunks_quantification"),
    ("src/app/api/v1/dashboard_optimized.py", "dashboard_optimized"),
    ("src/app/api/export_summaries.py", "export_summaries"),
    ("src/app/api/file_summaries.py", "file_summaries"),
    ("src/app/api/quantification.py", "quantification"),
    ("src/app/api/websocket.py", "websocket"),
    ("src/app/api/monitoring.py", "monitoring"),
]

print("="*80)
print("检查每个模块是否有router定义")
print("="*80)

for file_path, name in modules:
    if not os.path.exists(file_path):
        print(f"❌ {name:30} - 文件不存在")
        continue
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # 检查是否有router定义
    has_router_import = 'APIRouter' in content
    has_router_def = 'router = APIRouter' in content or 'router=APIRouter' in content
    has_endpoints = '@router.' in content
    
    if has_router_def and has_endpoints:
        print(f"✅ {name:30} - router正常")
    elif has_router_import but not has_router_def:
        print(f"⚠️  {name:30} - 导入了APIRouter但未定义router")
    elif not has_endpoints:
        print(f"⚠️  {name:30} - 没有@router.装饰器")
    else:
        print(f"❌ {name:30} - 无router定义")

