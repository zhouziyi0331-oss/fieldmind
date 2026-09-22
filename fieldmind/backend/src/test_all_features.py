#!/usr/bin/env python3
"""
FieldMind 完整功能测试脚本
测试所有核心功能是否正常工作
"""

import requests
import json
import sys
import time
import os
from pathlib import Path

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")

def print_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.END}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.END}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.END}")

def test_health():
    """测试后端健康状态"""
    print("\n" + "="*60)
    print("测试 1: 后端健康检查")
    print("="*60)

    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success("后端运行正常")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            return True
        else:
            print_error(f"健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"无法连接到后端: {e}")
        return False

def test_register():
    """测试用户注册"""
    print("\n" + "="*60)
    print("测试 2: 用户注册")
    print("="*60)

    username = f"testuser_{int(time.time())}"
    data = {
        "username": username,
        "email": f"{username}@example.com",
        "password": "Test123456"
    }

    try:
        response = requests.post(f"{BASE_URL}/api/auth/register", json=data)
        if response.status_code == 201:
            result = response.json()
            # 支持两种返回格式
            if 'user' in result:
                username = result['user']['username']
            else:
                username = result.get('username', data['username'])
            print_success(f"注册成功: {username}")
            return data['username'], data['password']
        elif "already" in response.text.lower():
            print_warning("用户已存在，使用现有用户")
            return data['username'], data['password']
        else:
            print_error(f"注册失败: {response.text}")
            return None, None
    except Exception as e:
        print_error(f"注册请求失败: {e}")
        return None, None

def test_login(username, password):
    """测试用户登录"""
    print("\n" + "="*60)
    print("测试 3: 用户登录")
    print("="*60)

    data = {
        "username": username,
        "password": password
    }

    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", json=data)
        if response.status_code == 200:
            result = response.json()
            token = result['access_token']
            print_success("登录成功")
            print_info(f"Token: {token[:50]}...")
            return token
        else:
            print_error(f"登录失败: {response.text}")
            return None
    except Exception as e:
        print_error(f"登录请求失败: {e}")
        return None

def test_create_project(token):
    """测试创建项目"""
    print("\n" + "="*60)
    print("测试 4: 创建项目")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "name": f"测试项目_{int(time.time())}",
        "description": "这是一个自动化测试项目"
    }

    try:
        response = requests.post(f"{BASE_URL}/api/projects", json=data, headers=headers)
        if response.status_code in [200, 201]:
            project = response.json()
            print_success(f"项目创建成功: {project['name']} (ID: {project['id']})")
            return project['id']
        else:
            print_error(f"创建项目失败: {response.text}")
            return None
    except Exception as e:
        print_error(f"创建项目请求失败: {e}")
        return None

def test_get_projects(token):
    """测试获取项目列表"""
    print("\n" + "="*60)
    print("测试 5: 获取项目列表")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.get(f"{BASE_URL}/api/projects", headers=headers)
        if response.status_code == 200:
            result = response.json()
            total = result.get('total', 0)
            print_success(f"获取项目列表成功，共 {total} 个项目")
            return True
        else:
            print_error(f"获取项目列表失败: {response.text}")
            return False
    except Exception as e:
        print_error(f"获取项目列表请求失败: {e}")
        return False

def test_project_stats(token, project_id):
    """测试项目统计"""
    print("\n" + "="*60)
    print("测试 6: 项目统计")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.get(f"{BASE_URL}/api/projects/{project_id}/stats", headers=headers)
        if response.status_code == 200:
            stats = response.json()
            print_success("获取项目统计成功")
            print(json.dumps(stats, indent=2, ensure_ascii=False))
            return True
        else:
            print_error(f"获取项目统计失败: {response.text}")
            return False
    except Exception as e:
        print_error(f"获取项目统计请求失败: {e}")
        return False

def test_keyword_search(token, project_id):
    """测试关键词检索"""
    print("\n" + "="*60)
    print("测试 7: 关键词检索")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "keyword": "测试",
        "include_videos": True,
        "include_audios": True,
        "include_documents": True
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/keyword-search/projects/{project_id}/search",
            json=data,
            headers=headers
        )
        if response.status_code == 200:
            result = response.json()
            print_success(f"关键词检索成功，找到 {result['total_mentions']} 处提及")
            return True
        else:
            print_error(f"关键词检索失败: {response.text}")
            return False
    except Exception as e:
        print_error(f"关键词检索请求失败: {e}")
        return False

def test_creative_analysis(token, project_id):
    """测试文创分析"""
    print("\n" + "="*60)
    print("测试 8: 文创分析")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "keywords": ["传统文化", "手工艺"],
        "mode": "creative"
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/creative-analysis/projects/{project_id}/analyze",
            json=data,
            headers=headers
        )
        if response.status_code == 200:
            result = response.json()
            print_success(f"文创分析成功，生成 {len(result.get('creative_possibilities', []))} 个创意建议")
            return True
        else:
            print_error(f"文创分析失败: {response.text}")
            return False
    except Exception as e:
        print_error(f"文创分析请求失败: {e}")
        return False

def test_business_analysis(token, project_id):
    """测试业态分析"""
    print("\n" + "="*60)
    print("测试 9: 业态分析")
    print("="*60)

    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.post(
            f"{BASE_URL}/api/business-analysis/projects/{project_id}/analyze",
            headers=headers
        )
        if response.status_code == 200:
            result = response.json()
            print_success(f"业态分析成功，建议 {len(result.get('suggested_formats', []))} 个新业态")
            return True
        else:
            print_error(f"业态分析失败: {response.text}")
            return False
    except Exception as e:
        print_error(f"业态分析请求失败: {e}")
        return False

def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("🚀 FieldMind 完整功能测试")
    print("="*60)

    results = []

    # 1. 健康检查
    if not test_health():
        print_error("后端未运行，退出测试")
        sys.exit(1)
    results.append(("健康检查", True))

    # 2. 用户注册
    username, password = test_register()
    if not username:
        print_error("注册失败，退出测试")
        sys.exit(1)
    results.append(("用户注册", True))

    # 3. 用户登录
    token = test_login(username, password)
    if not token:
        print_error("登录失败，退出测试")
        sys.exit(1)
    results.append(("用户登录", True))

    # 4. 创建项目
    project_id = test_create_project(token)
    if not project_id:
        print_error("创建项目失败，退出测试")
        sys.exit(1)
    results.append(("创建项目", True))

    # 5. 获取项目列表
    success = test_get_projects(token)
    results.append(("获取项目列表", success))

    # 6. 项目统计
    success = test_project_stats(token, project_id)
    results.append(("项目统计", success))

    # 7. 关键词检索
    success = test_keyword_search(token, project_id)
    results.append(("关键词检索", success))

    # 8. 文创分析
    success = test_creative_analysis(token, project_id)
    results.append(("文创分析", success))

    # 9. 业态分析
    success = test_business_analysis(token, project_id)
    results.append(("业态分析", success))

    # 总结
    print("\n" + "="*60)
    print("📊 测试结果汇总")
    print("="*60)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{status:10} | {name}")

    print("="*60)
    print(f"总计: {passed}/{total} 通过")

    if passed == total:
        print_success("🎉 所有测试通过！")
        return 0
    else:
        print_warning(f"⚠️  {total - passed} 个测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())
