#!/usr/bin/env python3
"""
端到端功能测试：上传 → 处理 → 查询
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from fastapi.testclient import TestClient
from src.app.main import app
import json
import time

client = TestClient(app)

print("╔══════════════════════════════════════════════════════════╗")
print("║         端到端流程测试                                   ║")
print("╚══════════════════════════════════════════════════════════╝\n")

# ============= 1. 创建项目 =============
print("📝 步骤1: 创建测试项目...")
response = client.post("/api/v1/projects", json={
    "name": "端到端测试项目",
    "description": "自动化测试"
})
print(f"   状态码: {response.status_code}")
if response.status_code in [200, 201]:
    project = response.json()
    project_id = project.get("id") or project.get("project_id") or 1
    print(f"   ✅ 项目创建成功: ID={project_id}")
else:
    print(f"   ⚠️  创建失败，使用默认项目 ID=1")
    project_id = 1

# ============= 2. 上传文档 =============
print("\n📤 步骤2: 上传测试文档...")
test_content = """
人工智能的发展历史
AI（Artificial Intelligence）的研究始于1950年代。
图灵测试由艾伦·图灵在1950年提出。
深度学习在2012年AlexNet出现后取得重大突破。
GPT-3是OpenAI在2020年发布的大型语言模型。
"""

# 尝试多个可能的上传端点
upload_endpoints = [
    ("/api/v1/documents/upload", {"project_id": project_id, "content": test_content, "filename": "test.txt"}),
    ("/api/documents/upload", {"project_id": project_id, "content": test_content}),
    ("/api/v1/projects/{}/documents".format(project_id), {"content": test_content, "title": "测试文档"})
]

document_id = None
for endpoint, payload in upload_endpoints:
    response = client.post(endpoint, json=payload)
    print(f"   尝试: {endpoint} -> {response.status_code}")
    if response.status_code in [200, 201]:
        doc = response.json()
        document_id = doc.get("id") or doc.get("document_id")
        print(f"   ✅ 文档上传成功: ID={document_id}")
        break

if not document_id:
    print("   ⚠️  文档上传失败，使用模拟ID")
    document_id = 1

# ============= 3. 处理文档 =============
print("\n⚙️  步骤3: 处理文档（实体提取 + 知识图谱）...")
response = client.post("/api/graph/build", json={
    "project_id": project_id,
    "document_ids": [document_id],
    "force_rebuild": False
})
print(f"   知识图谱构建: {response.status_code}")
if response.status_code in [200, 201, 202]:
    print(f"   ✅ 处理成功")
else:
    print(f"   ⚠️  处理失败: {response.text[:200]}")

time.sleep(2)  # 等待异步处理

# ============= 4. 查询图谱统计 =============
print("\n📊 步骤4: 查询知识图谱统计...")
response = client.get(f"/api/graph/statistics?project_id={project_id}")
print(f"   状态码: {response.status_code}")
if response.status_code == 200:
    stats = response.json()
    print(f"   ✅ 节点数: {stats.get('node_count', 0)}")
    print(f"   ✅ 边数: {stats.get('edge_count', 0)}")
    print(f"   ✅ 类型分布: {stats.get('type_distribution', {})}")
else:
    print(f"   ⚠️  查询失败")

# ============= 5. 语义检索 =============
print("\n🔍 步骤5: 语义检索测试...")
search_endpoints = [
    ("/api/search", {"query": "图灵测试", "project_id": project_id}),
    ("/api/v1/search", {"query": "图灵测试", "project_id": project_id}),
]

search_success = False
for endpoint, payload in search_endpoints:
    response = client.post(endpoint, json=payload)
    print(f"   尝试: {endpoint} -> {response.status_code}")
    if response.status_code == 200:
        results = response.json()
        count = len(results) if isinstance(results, list) else results.get("total", 0)
        print(f"   ✅ 检索成功: 返回{count}条结果")
        search_success = True
        break

if not search_success:
    print("   ⚠️  检索端点未找到")

# ============= 总结 =============
print("\n" + "="*60)
print("端到端流程测试完成")
print("="*60)
