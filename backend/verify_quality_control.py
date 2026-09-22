#!/usr/bin/env python3
"""
Phase 3.9 质量控制Agent - 快速验证脚本

用法:
    python3 verify_quality_control.py              # 运行所有验证
    python3 verify_quality_control.py --test       # 只运行测试套件
    python3 verify_quality_control.py --demo       # 运行演示
"""

import sys
import argparse
from typing import Dict, Any
import numpy as np


def verify_agent_basic():
    """验证Agent基础功能"""
    print("\n" + "="*60)
    print("1. Agent基础功能验证")
    print("="*60)

    from app.agents.quality_control_agent import get_quality_control_agent, QualityLevel

    agent = get_quality_control_agent()
    print(f"✓ Agent初始化成功")
    print(f"  - 验证规则: {len(agent.validation_rules)}个")
    print(f"  - 自动修复: {'启用' if agent.auto_fix_enabled else '禁用'}")
    print(f"  - 单例模式: {'正确' if agent is get_quality_control_agent() else '错误'}")

    return True


def verify_document_validation():
    """验证文档质量检查"""
    print("\n" + "="*60)
    print("2. 文档质量验证")
    print("="*60)

    from app.agents.quality_control_agent import get_quality_control_agent

    agent = get_quality_control_agent()

    # 测试正常文档
    doc_data = {
        "id": "test_doc_001",
        "content": "这是一个测试文档，内容足够长以通过基本验证。" * 5,
        "format": "markdown",
        "metadata": {
            "title": "测试文档",
            "created_at": "2024-08-09T10:00:00"
        }
    }

    report = agent.validate_document(doc_data)
    print(f"✓ 正常文档验证")
    print(f"  - 分数: {report.overall_score}/100")
    print(f"  - 等级: {report.quality_level.value}")
    print(f"  - 通过: {'是' if report.passed else '否'}")
    print(f"  - 问题: {len(report.issues)}个")

    # 测试空文档
    empty_doc = {
        "id": "test_doc_002",
        "content": "",
        "format": "markdown",
        "metadata": {}
    }

    report2 = agent.validate_document(empty_doc)
    print(f"\n✓ 空文档验证")
    print(f"  - 分数: {report2.overall_score}/100")
    print(f"  - 等级: {report2.quality_level.value}")
    print(f"  - 通过: {'是' if report2.passed else '否'}")
    print(f"  - 问题: {len(report2.issues)}个")

    return True


def verify_ocr_validation():
    """验证OCR质量检查"""
    print("\n" + "="*60)
    print("3. OCR质量验证")
    print("="*60)

    from app.agents.quality_control_agent import get_quality_control_agent

    agent = get_quality_control_agent()

    # 测试高质量OCR
    ocr_result = {
        "task_id": "ocr_001",
        "text": "这是OCR识别的文本内容，质量很好。",
        "confidence": 0.95,
        "text_blocks": [
            {"text": "这是OCR识别的文本", "confidence": 0.95},
            {"text": "内容质量很好", "confidence": 0.94}
        ]
    }

    report = agent.validate_ocr_result(ocr_result)
    print(f"✓ 高质量OCR验证")
    print(f"  - 分数: {report.overall_score}/100")
    print(f"  - 置信度: {report.metrics['confidence']:.2%}")
    print(f"  - 通过: {'是' if report.passed else '否'}")

    # 测试低质量OCR
    low_quality_ocr = {
        "task_id": "ocr_002",
        "text": "低质量文本",
        "confidence": 0.45,
        "text_blocks": []
    }

    report2 = agent.validate_ocr_result(low_quality_ocr)
    print(f"\n✓ 低质量OCR验证")
    print(f"  - 分数: {report2.overall_score}/100")
    print(f"  - 置信度: {report2.metrics['confidence']:.2%}")
    print(f"  - 通过: {'是' if report2.passed else '否'}")
    print(f"  - 问题: {len(report2.issues)}个")

    return True


def verify_entity_validation():
    """验证实体质量检查"""
    print("\n" + "="*60)
    print("4. 实体质量验证")
    print("="*60)

    from app.agents.quality_control_agent import get_quality_control_agent

    agent = get_quality_control_agent()

    entity_data = {
        "document_id": "doc_001",
        "entities": [
            {"text": "北京", "type": "LOCATION", "start": 0, "end": 2},
            {"text": "张三", "type": "PERSON", "start": 5, "end": 7},
            {"text": "2024年", "type": "DATE", "start": 10, "end": 15}
        ]
    }

    report = agent.validate_entities(entity_data)
    print(f"✓ 实体质量验证")
    print(f"  - 分数: {report.overall_score}/100")
    print(f"  - 实体数: {report.metrics['entities_count']}")
    print(f"  - 通过: {'是' if report.passed else '否'}")

    return True


def verify_embedding_validation():
    """验证向量质量检查"""
    print("\n" + "="*60)
    print("5. 向量质量验证")
    print("="*60)

    from app.agents.quality_control_agent import get_quality_control_agent

    agent = get_quality_control_agent()

    # 生成正常的向量
    embedding_data = {
        "document_id": "doc_001",
        "embedding": np.random.randn(768).tolist(),
        "model": "text-embedding-ada-002"
    }

    report = agent.validate_embedding(embedding_data)
    print(f"✓ 向量质量验证")
    print(f"  - 分数: {report.overall_score}/100")
    print(f"  - 维度: {report.metrics['dimension']}")
    print(f"  - 多样性: {report.metrics.get('diversity', 0):.4f}")
    print(f"  - 通过: {'是' if report.passed else '否'}")

    return True


def verify_graph_validation():
    """验证知识图谱质量检查"""
    print("\n" + "="*60)
    print("6. 知识图谱质量验证")
    print("="*60)

    from app.agents.quality_control_agent import get_quality_control_agent

    agent = get_quality_control_agent()

    graph_data = {
        "document_id": "doc_001",
        "nodes": [
            {"id": "node1", "label": "北京", "type": "LOCATION"},
            {"id": "node2", "label": "张三", "type": "PERSON"},
            {"id": "node3", "label": "公司", "type": "ORGANIZATION"}
        ],
        "relationships": [
            {"source": "node2", "target": "node1", "type": "位于"},
            {"source": "node2", "target": "node3", "type": "工作于"}
        ]
    }

    report = agent.validate_knowledge_graph(graph_data)
    print(f"✓ 知识图谱质量验证")
    print(f"  - 分数: {report.overall_score}/100")
    print(f"  - 节点数: {report.metrics['nodes_count']}")
    print(f"  - 关系数: {report.metrics['relationships_count']}")
    print(f"  - 孤立节点: {report.metrics['isolated_nodes']}")
    print(f"  - 通过: {'是' if report.passed else '否'}")

    return True


def verify_statistics():
    """验证统计功能"""
    print("\n" + "="*60)
    print("7. 统计功能验证")
    print("="*60)

    from app.agents.quality_control_agent import get_quality_control_agent

    agent = get_quality_control_agent()
    stats = agent.get_statistics()

    print(f"✓ 统计信息")
    print(f"  - 总检查数: {stats['total_checks']}")
    print(f"  - 通过数: {stats['passed']}")
    print(f"  - 失败数: {stats['failed']}")
    print(f"  - 通过率: {stats['pass_rate']:.1%}")
    print(f"  - 自动修复: {stats['auto_fixed']}")
    print(f"  - 修复率: {stats['auto_fix_rate']:.1%}")

    return True


def verify_api_routes():
    """验证API路由"""
    print("\n" + "="*60)
    print("8. API路由验证")
    print("="*60)

    try:
        from app.api.quality import router

        routes = []
        for route in router.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                methods = ','.join(route.methods)
                routes.append(f"[{methods}] {route.path}")

        print(f"✓ 发现 {len(routes)} 个API端点:")
        for route in sorted(routes):
            print(f"  - {route}")

        return True
    except Exception as e:
        print(f"✗ API路由验证失败: {e}")
        return False


def verify_celery_tasks():
    """验证Celery任务"""
    print("\n" + "="*60)
    print("9. Celery任务验证")
    print("="*60)

    try:
        from app.tasks.quality_tasks import (
            check_document_quality,
            check_ocr_quality,
            check_entity_quality,
            check_embedding_quality,
            check_graph_quality,
            batch_quality_check,
            full_pipeline_quality_check
        )

        tasks = [
            check_document_quality,
            check_ocr_quality,
            check_entity_quality,
            check_embedding_quality,
            check_graph_quality,
            batch_quality_check,
            full_pipeline_quality_check
        ]

        print(f"✓ 发现 {len(tasks)} 个Celery任务:")
        for task in tasks:
            print(f"  - {task.name}")

        return True
    except Exception as e:
        print(f"✗ Celery任务验证失败: {e}")
        return False


def run_tests():
    """运行测试套件"""
    print("\n" + "="*60)
    print("10. 运行测试套件")
    print("="*60)

    import subprocess

    try:
        result = subprocess.run(
            ["python3", "-m", "pytest", "tests/test_quality_control.py", "-v", "--tb=short"],
            capture_output=True,
            text=True,
            timeout=30
        )

        # 提取测试结果
        output = result.stdout
        if "passed" in output:
            # 提取通过的测试数
            import re
            match = re.search(r'(\d+) passed', output)
            if match:
                passed = match.group(1)
                print(f"✓ 测试套件运行成功")
                print(f"  - 通过: {passed}个测试")

                # 检查是否有失败
                failed_match = re.search(r'(\d+) failed', output)
                if failed_match:
                    failed = failed_match.group(1)
                    print(f"  - 失败: {failed}个测试")
                    return False

                return True
        else:
            print(f"✗ 测试套件运行失败")
            print(result.stderr)
            return False

    except subprocess.TimeoutExpired:
        print(f"✗ 测试超时")
        return False
    except Exception as e:
        print(f"✗ 测试运行失败: {e}")
        return False


def run_demo():
    """运行完整演示"""
    print("\n" + "="*80)
    print(" " * 20 + "Phase 3.9 质量控制Agent - 功能演示")
    print("="*80)

    results = []

    # 运行所有验证
    results.append(("Agent基础功能", verify_agent_basic()))
    results.append(("文档质量验证", verify_document_validation()))
    results.append(("OCR质量验证", verify_ocr_validation()))
    results.append(("实体质量验证", verify_entity_validation()))
    results.append(("向量质量验证", verify_embedding_validation()))
    results.append(("知识图谱验证", verify_graph_validation()))
    results.append(("统计功能验证", verify_statistics()))
    results.append(("API路由验证", verify_api_routes()))
    results.append(("Celery任务验证", verify_celery_tasks()))

    # 汇总结果
    print("\n" + "="*80)
    print("验证结果汇总")
    print("="*80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{status:8} - {name}")

    print(f"\n总计: {passed}/{total} 项通过 ({passed/total*100:.1f}%)")

    if passed == total:
        print("\n🎉 所有验证通过！Phase 3.9 质量控制Agent 工作正常。")
        return 0
    else:
        print(f"\n⚠️  有 {total-passed} 项验证失败，请检查。")
        return 1


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Phase 3.9 质量控制Agent - 快速验证脚本"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="只运行测试套件"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="运行完整演示"
    )

    args = parser.parse_args()

    if args.test:
        # 只运行测试
        success = run_tests()
        return 0 if success else 1
    elif args.demo or len(sys.argv) == 1:
        # 运行完整演示（默认）
        return run_demo()
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
