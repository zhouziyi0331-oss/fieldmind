"""
测试Skill沙箱的网络阻断功能
"""
import sys
sys.path.append('/Users/alwan/FieldMind-Rebuild/fieldmind-backend')

from app.services.skill_sandbox import SkillSandbox
from pathlib import Path
import tempfile

print("=" * 60)
print("测试Skill沙箱网络阻断")
print("=" * 60)

# 创建临时工作区
workspace = Path(tempfile.mkdtemp())

# 创建沙箱
sandbox = SkillSandbox(
    project_id=1,
    skill_id=999,
    timeout=30
)

# 测试1：尝试导入requests
print("\n【测试1】尝试import requests...")
skill_code_1 = """
import requests
result = "网络访问成功"
"""

result1 = sandbox.execute_skill(skill_code_1, {})
if result1['success'] and result1['result'].get('status') == 'error':
    if '禁止导入' in result1['result'].get('error', ''):
        print("✅ 网络阻断成功 - requests被禁止")
    else:
        print(f"⚠️ 失败但原因不同: {result1['result'].get('error', '')}")
else:
    print("❌ 网络阻断失败 - requests可以导入")

# 测试2：尝试使用urllib
print("\n【测试2】尝试import urllib...")
skill_code_2 = """
import urllib.request
result = "网络访问成功"
"""

result2 = sandbox.execute_skill(skill_code_2, {})
if result2['success'] and result2['result'].get('status') == 'error':
    if '禁止导入' in result2['result'].get('error', ''):
        print("✅ 网络阻断成功 - urllib被禁止")
    else:
        print(f"⚠️ 失败但原因不同: {result2['result'].get('error', '')}")
else:
    print("❌ 网络阻断失败 - urllib可以导入")

# 测试3：尝试使用socket
print("\n【测试3】尝试import socket...")
skill_code_3 = """
import socket
result = "网络访问成功"
"""

result3 = sandbox.execute_skill(skill_code_3, {})
if result3['success'] and result3['result'].get('status') == 'error':
    if '禁止导入' in result3['result'].get('error', ''):
        print("✅ 网络阻断成功 - socket被禁止")
    else:
        print(f"⚠️ 失败但原因不同: {result3['result'].get('error', '')}")
else:
    print("❌ 网络阻断失败 - socket可以导入")

# 测试4：正常代码应该可以执行
print("\n【测试4】正常代码执行...")
skill_code_4 = """
# 正常的数据处理代码
numbers = [1, 2, 3, 4, 5]
result = sum(numbers)
"""

result4 = sandbox.execute_skill(skill_code_4, {})
if result4['success']:
    print("✅ 正常代码执行成功")
else:
    print(f"❌ 正常代码执行失败: {result4.get('error', '')}")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
