#!/usr/bin/env python3
"""
FieldMind功能模块测试工具
逐个测试每个功能是否真实可用
"""

import json
import time
from pathlib import Path

print("="*80)
print("FieldMind 功能模块测试工具")
print("="*80)

def test_file_upload():
    """测试文件上传流程"""
    print("\n📁 1. 文件上传功能测试")
    print("-" * 60)

    # 创建测试文件
    test_file = Path('/tmp/test_fieldmind.txt')
    test_file.write_text("这是一个测试文件，用于验证FieldMind的文件上传功能。\n包含关键词：AI、机器学习、数据分析、自然语言处理。")

    print(f"✅ 创建测试文件: {test_file}")
    print(f"   文件大小: {test_file.stat().st_size} bytes")

    print("\n📝 测试检查点:")
    print("   ☐ 1. 前端可以选择文件")
    print("   ☐ 2. 文件上传到后端 (/api/files/upload)")
    print("   ☐ 3. 后端保存文件到数据库")
    print("   ☐ 4. 自动提取关键词")
    print("   ☐ 5. 显示上传成功提示")
    print("   ☐ 6. 刷新文件列表")

    print("\n🔧 手动测试步骤:")
    print("   1. 启动FieldMind应用")
    print("   2. 进入「资料导入」页面")
    print("   3. 拖拽或选择测试文件上传")
    print("   4. 观察上传进度和结果提示")
    print("   5. 检查文件列表是否显示新文件")

def test_keyword_extraction():
    """测试关键词提取"""
    print("\n🔑 2. 关键词提取功能测试")
    print("-" * 60)

    print("📝 测试检查点:")
    print("   ☐ 1. 上传文件后自动提取关键词")
    print("   ☐ 2. 可以手动触发关键词提取")
    print("   ☐ 3. 关键词保存到数据库")
    print("   ☐ 4. 关键词在「关键词引擎」页面显示")
    print("   ☐ 5. 显示关键词频率统计")

    print("\n🔧 手动测试步骤:")
    print("   1. 上传包含明显关键词的文件")
    print("   2. 等待AI处理完成")
    print("   3. 进入「关键词引擎」页面")
    print("   4. 检查提取的关键词是否准确")
    print("   5. 验证关键词频率是否正确")

def test_ai_chat():
    """测试AI对话"""
    print("\n💬 3. AI对话功能测试")
    print("-" * 60)

    test_questions = [
        "你好，请介绍一下你自己",
        "帮我分析一下当前项目的关键信息",
        "总结一下已上传的文件内容",
    ]

    print("📝 测试检查点:")
    print("   ☐ 1. 可以输入消息")
    print("   ☐ 2. 消息发送到后端 (/api/chat)")
    print("   ☐ 3. AI返回有意义的回复")
    print("   ☐ 4. 对话历史正确保存")
    print("   ☐ 5. 错误时显示友好提示")

    print("\n💡 建议测试问题:")
    for i, q in enumerate(test_questions, 1):
        print(f"   {i}. {q}")

    print("\n🔧 手动测试步骤:")
    print("   1. 进入「对话」或「AI助手」页面")
    print("   2. 输入测试问题")
    print("   3. 观察AI响应时间和回复质量")
    print("   4. 刷新页面检查历史是否保存")

def test_report_generation():
    """测试报告生成"""
    print("\n📊 4. 报告生成功能测试")
    print("-" * 60)

    print("📝 测试检查点:")
    print("   ☐ 1. 可以选择报告类型")
    print("   ☐ 2. 生成报告 (/api/reports/generate)")
    print("   ☐ 3. 报告包含项目统计数据")
    print("   ☐ 4. 可以导出为PDF/Markdown/DOCX")
    print("   ☐ 5. 下载链接可用")

    print("\n🔧 手动测试步骤:")
    print("   1. 确保项目中有文件和关键词数据")
    print("   2. 进入「报告」页面")
    print("   3. 选择报告类型（全面分析/关键词报告等）")
    print("   4. 点击生成报告")
    print("   5. 尝试导出为不同格式")
    print("   6. 验证导出文件内容正确")

def test_skill_system():
    """测试Skill系统"""
    print("\n⚡ 5. Skill生态系统测试")
    print("-" * 60)

    print("📝 测试检查点:")
    print("   ☐ 1. 显示可用Skill列表")
    print("   ☐ 2. 可以执行Skill (/api/skills/llm)")
    print("   ☐ 3. Skill接受输入参数")
    print("   ☐ 4. 返回执行结果")
    print("   ☐ 5. 可以创建自定义Skill")

    print("\n🔧 手动测试步骤:")
    print("   1. 进入「Skill生态」页面")
    print("   2. 查看可用的Skill列表")
    print("   3. 选择一个Skill并执行")
    print("   4. 输入测试参数")
    print("   5. 验证执行结果是否正确")
    print("   6. 尝试创建新的Skill")

def test_workflow_system():
    """测试工作流系统"""
    print("\n🔄 6. 工作流系统测试")
    print("-" * 60)

    print("📝 测试检查点:")
    print("   ☐ 1. 显示可用工作流列表")
    print("   ☐ 2. 可以执行工作流 (/api/workflows/execute)")
    print("   ☐ 3. 工作流步骤按顺序执行")
    print("   ☐ 4. 显示执行进度")
    print("   ☐ 5. 返回最终结果")

    print("\n🔧 手动测试步骤:")
    print("   1. 进入「工作流」页面")
    print("   2. 查看可用的工作流")
    print("   3. 选择一个工作流执行")
    print("   4. 观察执行过程")
    print("   5. 验证最终结果")

def test_knowledge_threads():
    """测试知识脉络"""
    print("\n🧠 7. 知识脉络生成测试")
    print("-" * 60)

    print("📝 测试检查点:")
    print("   ☐ 1. 从关键词生成知识脉络")
    print("   ☐ 2. 显示概念关联关系")
    print("   ☐ 3. 可视化知识图谱")
    print("   ☐ 4. 支持交互式探索")

    print("\n🔧 手动测试步骤:")
    print("   1. 确保有足够的关键词数据")
    print("   2. 进入「知识脉络」页面")
    print("   3. 生成知识脉络")
    print("   4. 查看概念关联")
    print("   5. 测试交互功能")

def test_search_function():
    """测试搜索功能"""
    print("\n🔍 8. 搜索功能测试")
    print("-" * 60)

    print("📝 测试检查点:")
    print("   ☐ 1. 可以输入搜索关键词")
    print("   ☐ 2. 搜索文件内容")
    print("   ☐ 3. 搜索关键词")
    print("   ☐ 4. 返回相关结果")
    print("   ☐ 5. 结果可以点击查看详情")

    print("\n🔧 手动测试步骤:")
    print("   1. 在搜索框输入关键词")
    print("   2. 查看搜索结果")
    print("   3. 验证结果的相关性")
    print("   4. 点击结果查看详情")

def create_test_data():
    """创建测试数据"""
    print("\n📦 创建测试数据")
    print("-" * 60)

    test_files = {
        'test_ai.txt': """
人工智能（AI）是计算机科学的一个分支，致力于创建能够模拟人类智能的系统。
机器学习是AI的核心技术，包括监督学习、无监督学习和强化学习。
深度学习使用神经网络模型处理复杂的数据模式。
自然语言处理（NLP）使计算机能够理解和生成人类语言。
计算机视觉使机器能够理解和分析图像和视频。
        """,
        'test_business.txt': """
商业分析需要理解市场需求、竞争环境和客户需求。
数据驱动决策是现代企业的核心竞争力。
用户体验（UX）直接影响产品的成功。
敏捷开发方法提高了团队的响应速度。
持续集成和持续部署（CI/CD）是DevOps的关键实践。
        """,
        'test_research.txt': """
科研方法论包括定性研究和定量研究。
文献综述是研究的起点，帮助理解现有知识。
实验设计需要考虑变量控制和样本选择。
数据收集和分析是验证假设的关键步骤。
论文写作需要清晰的逻辑结构和严谨的论证。
        """
    }

    test_dir = Path('/tmp/fieldmind_test_data')
    test_dir.mkdir(exist_ok=True)

    for filename, content in test_files.items():
        filepath = test_dir / filename
        filepath.write_text(content.strip(), encoding='utf-8')
        print(f"✅ 创建测试文件: {filepath}")

    print(f"\n📁 测试数据目录: {test_dir}")
    print("💡 可以使用这些文件测试上传和分析功能")

def generate_test_report():
    """生成测试报告模板"""
    print("\n📋 生成测试报告模板")
    print("-" * 60)

    report = {
        "test_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "modules": [
            {
                "name": "文件上传",
                "status": "未测试",
                "issues": [],
                "notes": ""
            },
            {
                "name": "关键词提取",
                "status": "未测试",
                "issues": [],
                "notes": ""
            },
            {
                "name": "AI对话",
                "status": "未测试",
                "issues": [],
                "notes": ""
            },
            {
                "name": "报告生成",
                "status": "未测试",
                "issues": [],
                "notes": ""
            },
            {
                "name": "Skill系统",
                "status": "未测试",
                "issues": [],
                "notes": ""
            },
            {
                "name": "工作流",
                "status": "未测试",
                "issues": [],
                "notes": ""
            },
            {
                "name": "知识脉络",
                "status": "未测试",
                "issues": [],
                "notes": ""
            },
            {
                "name": "搜索功能",
                "status": "未测试",
                "issues": [],
                "notes": ""
            }
        ]
    }

    report_path = Path('/tmp/fieldmind_test_report.json')
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"✅ 测试报告模板: {report_path}")
    print("💡 测试完成后可以填写此报告记录结果")

def main():
    print("\n开始功能测试...")

    # 创建测试数据
    create_test_data()

    # 逐个测试功能
    test_file_upload()
    test_keyword_extraction()
    test_ai_chat()
    test_report_generation()
    test_skill_system()
    test_workflow_system()
    test_knowledge_threads()
    test_search_function()

    # 生成测试报告模板
    generate_test_report()

    print("\n" + "="*80)
    print("🎯 测试指南生成完成")
    print("="*80)
    print("\n下一步:")
    print("1. 启动FieldMind应用")
    print("2. 按照上述步骤逐个测试每个功能")
    print("3. 记录发现的问题")
    print("4. 填写测试报告 (/tmp/fieldmind_test_report.json)")
    print("\n💡 如果发现问题，请详细描述:")
    print("   - 问题现象")
    print("   - 复现步骤")
    print("   - 预期行为")
    print("   - 实际行为")
    print("="*80)

if __name__ == '__main__':
    main()
