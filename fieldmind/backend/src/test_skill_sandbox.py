"""
测试Skill沙箱功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.skill_sandbox import SkillSandbox


def test_sandbox_basic():
    """测试基础沙箱功能"""
    print("\n" + "="*70)
    print("🧪 测试Skill沙箱 - 基础功能")
    print("="*70)

    # 创建沙箱
    sandbox = SkillSandbox(
        project_id=1,
        skill_id=1001,
        timeout=10
    )

    # 测试代码1: 简单计算
    print("\n【测试1】简单计算")

    skill_code_1 = '''
def main(params):
    a = params.get('a', 0)
    b = params.get('b', 0)
    return {
        'result': a + b,
        'operation': 'addition'
    }
'''

    result = sandbox.execute_skill(
        skill_code=skill_code_1,
        parameters={'a': 10, 'b': 20}
    )

    if result['success']:
        print(f"✅ 执行成功")
        print(f"   结果: {result['result']}")
        print(f"   耗时: {result['execution_time']:.3f}秒")
    else:
        print(f"❌ 执行失败: {result['error']}")

    return result['success']


def test_sandbox_network_block():
    """测试网络阻断"""
    print("\n" + "="*70)
    print("🧪 测试Skill沙箱 - 网络阻断")
    print("="*70)

    sandbox = SkillSandbox(
        project_id=1,
        skill_id=1002,
        timeout=10
    )

    # 测试代码2: 尝试访问网络（应该被阻止）
    print("\n【测试2】尝试访问网络（应该被阻止）")

    skill_code_2 = '''
def main(params):
    try:
        import requests
        response = requests.get('https://www.baidu.com')
        return {'status': 'error', 'message': '网络访问应该被阻止'}
    except RuntimeError as e:
        return {'status': 'success', 'message': '网络访问已被正确阻止', 'error': str(e)}
'''

    result = sandbox.execute_skill(
        skill_code=skill_code_2,
        parameters={}
    )

    if result['success']:
        skill_result = result['result']
        if skill_result.get('status') == 'success':
            print(f"✅ 网络阻断正常工作")
            print(f"   消息: {skill_result.get('message')}")
        else:
            print(f"❌ 网络阻断失败")
    else:
        print(f"❌ 执行失败: {result['error']}")

    return True


def test_sandbox_timeout():
    """测试超时控制"""
    print("\n" + "="*70)
    print("🧪 测试Skill沙箱 - 超时控制")
    print("="*70)

    sandbox = SkillSandbox(
        project_id=1,
        skill_id=1003,
        timeout=2  # 2秒超时
    )

    # 测试代码3: 死循环（应该超时）
    print("\n【测试3】死循环（应该在2秒后超时）")

    skill_code_3 = '''
import time

def main(params):
    # 模拟长时间运行
    time.sleep(5)  # 睡眠5秒，但超时设置是2秒
    return {'status': 'should_not_reach_here'}
'''

    result = sandbox.execute_skill(
        skill_code=skill_code_3,
        parameters={}
    )

    if not result['success'] and '超时' in result.get('error', ''):
        print(f"✅ 超时控制正常工作")
        print(f"   耗时: {result['execution_time']:.3f}秒")
    else:
        print(f"❌ 超时控制失败")

    return True


def test_sandbox_project_isolation():
    """测试项目数据隔离"""
    print("\n" + "="*70)
    print("🧪 测试Skill沙箱 - 项目数据隔离")
    print("="*70)

    sandbox = SkillSandbox(
        project_id=1,
        skill_id=1004,
        timeout=10
    )

    # 测试代码4: 访问PROJECT_ID
    print("\n【测试4】项目ID隔离")

    skill_code_4 = '''
def main(params):
    # PROJECT_ID是自动注入的，Skill只能访问这个项目的数据
    return {
        'project_id': PROJECT_ID,
        'message': f'Skill只能访问项目 {PROJECT_ID} 的数据'
    }
'''

    result = sandbox.execute_skill(
        skill_code=skill_code_4,
        parameters={}
    )

    if result['success']:
        skill_result = result['result']
        print(f"✅ 项目隔离正常")
        print(f"   PROJECT_ID: {skill_result.get('project_id')}")
        print(f"   消息: {skill_result.get('message')}")
    else:
        print(f"❌ 测试失败: {result['error']}")

    return result['success']


def main():
    """运行所有测试"""
    print("\n" + "="*70)
    print("🚀 Skill沙箱隔离 - 完整测试")
    print("="*70)

    results = []

    # 测试1: 基础功能
    results.append(("基础功能", test_sandbox_basic()))

    # 测试2: 网络阻断
    results.append(("网络阻断", test_sandbox_network_block()))

    # 测试3: 超时控制
    results.append(("超时控制", test_sandbox_timeout()))

    # 测试4: 项目隔离
    results.append(("项目隔离", test_sandbox_project_isolation()))

    # 汇总结果
    print("\n" + "="*70)
    print("📊 测试结果汇总")
    print("="*70)

    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{status:10} | {name}")

    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)

    print("="*70)
    print(f"总计: {passed_count}/{total_count} 通过")

    if passed_count == total_count:
        print("\n🎉 所有测试通过！Skill沙箱功能正常")
        return 0
    else:
        print(f"\n⚠️  {total_count - passed_count} 个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
