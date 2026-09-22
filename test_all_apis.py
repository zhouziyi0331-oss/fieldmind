#!/usr/bin/env python3
"""
完整的API测试验证脚本
测试所有三个问题是否真正解决
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8013"

print("=" * 80)
print("🧪 完整API测试验证")
print("=" * 80)
print()

# 测试1：照片API
print("【测试1】照片API")
print("-" * 80)
url = f"{BASE_URL}/api/photos?project_id=1"
try:
    response = requests.get(url, timeout=5)
    print(f"URL: {url}")
    print(f"状态码: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"✅ 照片API成功")
        print(f"响应格式: {list(data.keys())}")

        if 'success' in data and data['success']:
            print(f"✅ success: true")
            if 'data' in data and isinstance(data['data'], dict):
                print(f"✅ data字段存在")
                inner_data = data['data']
                print(f"data keys: {list(inner_data.keys())}")

                if 'photos' in inner_data:
                    print(f"✅ photos数组存在")
                    print(f"照片数量: {len(inner_data['photos'])}")
                    print(f"总数: {inner_data.get('total', 0)}")
                else:
                    print(f"❌ 缺少photos字段")
        else:
            print(f"❌ success字段错误或不存在")
    else:
        print(f"❌ 请求失败")
        print(f"响应: {response.text[:200]}")
except Exception as e:
    print(f"❌ 错误: {e}")

print()

# 测试2：表格API
print("【测试2】表格API")
print("-" * 80)
url = f"{BASE_URL}/api/v1/projects/1/tables/"
try:
    response = requests.get(url, timeout=5)
    print(f"URL: {url}")
    print(f"状态码: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"✅ 表格API成功")
        print(f"响应格式: {list(data.keys())}")

        if 'success' in data and data['success']:
            print(f"✅ success: true")
            if 'data' in data and isinstance(data['data'], dict):
                print(f"✅ data字段存在")
                inner_data = data['data']
                print(f"data keys: {list(inner_data.keys())}")

                if 'tables' in inner_data:
                    print(f"✅ tables数组存在")
                    print(f"表格数量: {len(inner_data['tables'])}")
                    print(f"总数: {inner_data.get('total', 0)}")
                else:
                    print(f"❌ 缺少tables字段")
        else:
            print(f"❌ success字段错误或不存在")
    else:
        print(f"❌ 请求失败")
        print(f"响应: {response.text[:200]}")
except Exception as e:
    print(f"❌ 错误: {e}")

print()

# 测试3：文档API（检查字数和状态）
print("【测试3】文档API - 字数和状态")
print("-" * 80)
url = f"{BASE_URL}/api/v1/projects/1/documents/"
try:
    response = requests.get(url, timeout=5)
    print(f"URL: {url}")
    print(f"状态码: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"✅ 文档API成功")
        print(f"响应格式: {list(data.keys())}")

        if 'success' in data and data['success']:
            if 'data' in data and isinstance(data['data'], dict):
                inner_data = data['data']

                if 'documents' in inner_data:
                    docs = inner_data['documents']
                    print(f"✅ documents数组存在")
                    print(f"文档数量: {len(docs)}")

                    # 检查前3个文档的状态和字数
                    print()
                    print("文档状态和字数检查:")
                    for i, doc in enumerate(docs[:3], 1):
                        filename = doc.get('filename', 'unknown')[:40]
                        status = doc.get('status', 'unknown')
                        word_count = doc.get('word_count', 0)
                        print(f"  {i}. {filename}")
                        print(f"     状态: {status}, 字数: {word_count}")

                        # 验证逻辑
                        if status == 'completed' and word_count > 0:
                            print(f"     ✅ 完成且有字数")
                        elif status in ['pending', 'processing']:
                            print(f"     ✅ 状态正确（前端应显示处理中）")
                        else:
                            print(f"     ⚠️  状态:{status}, 字数:{word_count}")
                else:
                    print(f"❌ 缺少documents字段")
        else:
            print(f"❌ success字段错误或不存在")
    else:
        print(f"❌ 请求失败")
        print(f"响应: {response.text[:200]}")
except Exception as e:
    print(f"❌ 错误: {e}")

print()
print("=" * 80)
print("📊 测试总结")
print("=" * 80)
print()
print("如果看到以上所有 ✅，说明后端API工作正常。")
print()
print("下一步：")
print("1. 重新编译并运行桌面应用")
print("2. 打开应用，查看控制台日志")
print("3. 访问照片管理、表格管理、文件管理器页面")
print("4. 查看是否还有「数据解析失败」错误")
print()
