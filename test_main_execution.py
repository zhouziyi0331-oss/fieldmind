#!/usr/bin/env python3
"""测试main.py是否完整执行"""
import sys
sys.path.insert(0, '/Users/alwan/FieldMind-Rebuild/fieldmind-backend')

# 在导入前设置钩子
original_include_router = None
call_count = 0

def trace_include_router(self, *args, **kwargs):
    global call_count
    call_count += 1
    print(f"[TRACE {call_count}] include_router called")
    if 'prefix' in kwargs:
        print(f"        prefix={kwargs['prefix']}")
    return original_include_router(self, *args, **kwargs)

# Monkey patch FastAPI before importing main
from fastapi import FastAPI
original_include_router = FastAPI.include_router
FastAPI.include_router = trace_include_router

print("开始导入app.main...")
from app import main as main_module

print(f"\n导入完成，include_router被调用了 {call_count} 次")
print(f"app.routes数量: {len(list(main_module.app.routes))}")
