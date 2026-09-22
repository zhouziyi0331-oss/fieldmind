"""
Quality Control Examples - 质量控制使用示例
演示如何使用质量控制Agent进行自动化质量检查
"""
import asyncio
import logging
from typing import Dict, Any
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================== Example 1: 基础文档质量检查 ====================

def example_1_basic_document_check():
    """
    示例1：基础文档质量检查

    检查文档转换质量，包括内容、编码、元数据等
    """
    print("\n" + "="*60)
    print("示例1：基础文档质量检查")
    print("="*60)

    from app.agents.quality_control_agent import get_quality_control_agent

    agent = get_quality_control_agent()

    # 准备文档数据
    document_data = {
        "id": "doc_20240109_001",
        "content": """
        # 田野调查报告

        本次调查在北京市朝阳区进行，时间为2024年1月。
        调查对象包括10个社区，共访谈了50位居民。

        ## 主要发现

        1. 居民满意度较高
        2. 基础设施完善
        3. 社区活动丰富
        """,
        "format": "markdown",
        "metadata": {
            "title": "2024年北京社区调查报告",
            "created_at": "2024-01-09T10:00:00",
            "author": "张三",
            "location": "北京市朝阳区"
        }
    }

    # 执行质量检查
    report = agent.validate_document(document_data)

    # 输出结果
    print(f"\n任务ID: {report.task_id}")
    print(f"质量等级: {report.quality_level.value}")
    print(f"总分: {report.overall_score}/100")
    print(f"是否通过: {'✓ 通过' if report.passed else '✗ 未通过'}")

    if report.issues:
        print(f"\n发现 {len(report.issues)} 个问题:")
        for issue in report.issues:
            print(f"  - [{issue.severity.upper()}] {issue.description}")
            if issue.suggestion:
                print(f"    建议: {issue.suggestion}")
    else:
        print("\n✓ 未发现质量问题")

    if report.auto_fixed:
        print(f"\n自动修复的问题: {', '.join(report.auto_fixed)}")

    print(f"\n指标:")
    for key, value in report.metrics.items():
        print(f"  - {key}: {value}")


# ==================== Example 2: OCR结果质量检查 ====================

def example_2_ocr_quality_check():
    """
    示例2：OCR结果质量检查

    检查OCR识别的置信度、乱码、布局等
    """
    print("\n" + "="*60)
    print("示例2：OCR结果质量检查")
    print("="*60)

    from app.agents.quality_control_agent import get_quality_control_agent

    agent = get_quality_control_agent()

    # 模拟OCR结果
    ocr_result = {
        "task_id": "ocr_20240109_001",
        "text": """
        田野调查记录

        时间：2024年1月9日
        地点：北京市朝阳区望京街道
        调查员：李四

        今日访谈了3位居民，记录如下：
        1. 王女士（65岁）- 退休教师
        2. 刘先生（42岁）- 个体户
        3. 赵女士（38岁）- 公司职员
        """,
        "confidence": 0.92,
        "text_blocks": [
            {"text": "田野调查记录", "confidence": 0.95, "bbox": [100, 100, 300, 150]},
            {"text": "时间：2024年1月9日", "confidence": 0.93, "bbox": [100, 160, 350, 180]},
            {"text": "地点：北京市朝阳区望京街道", "confidence": 0.91, "bbox": [100, 190, 450, 210]},
            {"text": "调查员：李四", "confidence": 0.94, "bbox": [100, 220, 250, 240]},
            {"text": "今日访谈了3位居民，记录如下：", "confidence": 0.90, "bbox": [100, 260, 450, 280]},
            {"text": "1. 王女士（65岁）- 退休教师", "confidence": 0.89, "bbox": [120, 290, 400, 310]},
            {"text": "2. 刘先生（42岁）- 个体户", "confidence": 0.92, "bbox": [120, 320, 400, 340]},
            {"text": "3. 赵女士（38岁）- 公司职员", "confidence": 0.88, "bbox": [120, 350, 400, 370]}
        ]
    }

    # 执行质量检查
    report = agent.validate_ocr_result(ocr_result)

    # 输出结果
    print(f"\n任务ID: {report.task_id}")
    print(f"质量等级: {report.quality_level.value}")
    print(f"总分: {report.overall_score}/100")
    print(f"是否通过: {'✓ 通过' if report.passed else '✗ 未通过'}")

    print(f"\nOCR指标:")
    print(f"  - 平均置信度: {report.metrics['confidence']:.2%}")
    print(f"  - 文本长度: {report.metrics['text_length']} 字符")
    print(f"  - 文本块数量: {report.metrics['blocks_count']}")
    print(f"  - 乱码比例: {report.metrics['garbled_ratio']:.2%}")
    print(f"  - 平均块置信度: {report.metrics['avg_block_confidence']:.2%}")

    if report.issues:
        print(f"\n发现 {len(report.issues)} 个问题:")
        for issue in report.issues:
            print(f"  - [{issue.severity.upper()}] {issue.description}")
    else:
        print("\n✓ OCR质量良好")


# ==================== Example 3: 实体识别质量检查 ====================

def example_3_entity_quality_check():
    """
    示例3：实体识别质量检查

    检查实体数量、类型、重复等
    """
    print("\n" + "="*60)
    print("示例3：实体识别质量检查")
    print("="*60)

    from app.agents.quality_control_agent import get_quality_control_agent

    agent = get_quality_control_agent()

    # 模拟实体识别结果
    entity_data = {
        "document_id": "doc_20240109_001",
        "entities": [
            {"text": "北京市", "type": "LOCATION", "start": 15, "end": 18},
            {"text": "朝阳区", "type": "LOCATION", "start": 18, "end": 21},
            {"text": "望京街道", "type": "LOCATION", "start": 21, "end": 25},
            {"text": "2024年1月", "type": "DATE", "start": 8, "end": 15},
            {"text": "李四", "type": "PERSON", "start": 35, "end": 37},
            {"text": "王女士", "type": "PERSON", "start": 50, "end": 53},
            {"text": "刘先生", "type": "PERSON", "start": 65, "end": 68},
            {"text": "赵女士", "type": "PERSON", "start": 78, "end": 81},
            {"text": "退休教师", "type": "ORGANIZATION", "start": 58, "end": 62},
            {"text": "个体户", "type": "ORGANIZATION", "start": 73, "end": 76}
        ]
    }

    # 执行质量检查
    report = agent.validate_entities(entity_data)

    # 输出结果
    print(f"\n文档ID: {report.task_id}")
    print(f"质量等级: {report.quality_level.value}")
    print(f"总分: {report.overall_score}/100")
    print(f"是否通过: {'✓ 通过' if report.passed else '✗ 未通过'}")

    print(f"\n实体统计:")
    print(f"  - 实体总数: {report.metrics['entities_count']}")
    print(f"  - 唯一实体: {report.metrics['unique_entities']}")
    print(f"  - 重复率: {report.metrics['duplicate_ratio']:.2%}")

    print(f"\n类型分布:")
    for entity_type, count in report.metrics['type_distribution'].items():
        if count > 0:
            print(f"  - {entity_type}: {count}")

    if report.issues:
        print(f"\n发现 {len(report.issues)} 个问题:")
        for issue in report.issues:
            print(f"  - [{issue.severity.upper()}] {issue.description}")
    else:
        print("\n✓ 实体识别质量良好")


# ==================== Example 4: 向量化质量检查 ====================

def example_4_embedding_quality_check():
    """
    示例4：向量化质量检查

    检查向量维度、多样性、零值比例等
    """
    print("\n" + "="*60)
    print("示例4：向量化质量检查")
    print("="*60)

    from app.agents.quality_control_agent import get_quality_control_agent

    agent = get_quality_control_agent()

    # 生成模拟向量（768维）
    embedding = np.random.randn(768).tolist()

    embedding_data = {
        "document_id": "doc_20240109_001",
        "embedding": embedding
    }

    # 执行质量检查
    report = agent.validate_embedding(embedding_data)

    # 输出结果
    print(f"\n文档ID: {report.task_id}")
    print(f"质量等级: {report.quality_level.value}")
    print(f"总分: {report.overall_score}/100")
    print(f"是否通过: {'✓ 通过' if report.passed else '✗ 未通过'}")

    print(f"\n向量指标:")
    print(f"  - 维度: {report.metrics['dimension']}")
    print(f"  - 均值: {report.metrics['mean']:.4f}")
    print(f"  - 标准差: {report.metrics['std']:.4f}")
    print(f"  - 最小值: {report.metrics['min']:.4f}")
    print(f"  - 最大值: {report.metrics['max']:.4f}")
    print(f"  - 零值比例: {report.metrics['zero_ratio']:.2%}")

    if report.issues:
        print(f"\n发现 {len(report.issues)} 个问题:")
        for issue in report.issues:
            print(f"  - [{issue.severity.upper()}] {issue.description}")
    else:
        print("\n✓ 向量质量良好")


# ==================== Example 5: 知识图谱质量检查 ====================

def example_5_graph_quality_check():
    """
    示例5：知识图谱质量检查

    检查节点、关系、孤立节点等
    """
    print("\n" + "="*60)
    print("示例5：知识图谱质量检查")
    print("="*60)

    from app.agents.quality_control_agent import get_quality_control_agent

    agent = get_quality_control_agent()

    # 模拟知识图谱
    graph_data = {
        "document_id": "doc_20240109_001",
        "nodes": [
            {"id": "n1", "label": "北京市", "type": "LOCATION"},
            {"id": "n2", "label": "朝阳区", "type": "LOCATION"},
            {"id": "n3", "label": "望京街道", "type": "LOCATION"},
            {"id": "n4", "label": "李四", "type": "PERSON"},
            {"id": "n5", "label": "王女士", "type": "PERSON"},
            {"id": "n6", "label": "刘先生", "type": "PERSON"},
            {"id": "n7", "label": "2024年1月", "type": "DATE"}
        ],
        "relationships": [
            {"source": "n2", "target": "n1", "type": "位于"},
            {"source": "n3", "target": "n2", "type": "位于"},
            {"source": "n4", "target": "n3", "type": "调查于"},
            {"source": "n5", "target": "n3", "type": "居住于"},
            {"source": "n6", "target": "n3", "type": "居住于"},
            {"source": "n4", "target": "n7", "type": "时间"}
        ]
    }

    # 执行质量检查
    report = agent.validate_knowledge_graph(graph_data)

    # 输出结果
    print(f"\n文档ID: {report.task_id}")
    print(f"质量等级: {report.quality_level.value}")
    print(f"总分: {report.overall_score}/100")
    print(f"是否通过: {'✓ 通过' if report.passed else '✗ 未通过'}")

    print(f"\n图谱统计:")
    print(f"  - 节点数量: {report.metrics['nodes_count']}")
    print(f"  - 关系数量: {report.metrics['relationships_count']}")
    print(f"  - 孤立节点: {report.metrics['isolated_nodes']}")
    print(f"  - 孤立率: {report.metrics['isolated_ratio']:.2%}")
    print(f"  - 平均度: {report.metrics['avg_degree']:.2f}")

    if report.issues:
        print(f"\n发现 {len(report.issues)} 个问题:")
        for issue in report.issues:
            print(f"  - [{issue.severity.upper()}] {issue.description}")
    else:
        print("\n✓ 知识图谱质量良好")


# ==================== Example 6: 批量质量检查 ====================

def example_6_batch_quality_check():
    """
    示例6：批量质量检查

    一次性检查多个任务
    """
    print("\n" + "="*60)
    print("示例6：批量质量检查")
    print("="*60)

    from app.agents.quality_control_agent import get_quality_control_agent

    agent = get_quality_control_agent()

    # 准备多个任务
    tasks = []

    # 任务1: 文档
    tasks.append({
        "type": "document",
        "data": {
            "id": "batch_doc_1",
            "content": "这是第一个批量测试文档" * 5,
            "metadata": {"title": "批量文档1", "created_at": "2024-01-09"}
        }
    })

    # 任务2: OCR
    tasks.append({
        "type": "ocr",
        "data": {
            "task_id": "batch_ocr_1",
            "text": "这是OCR识别的文本",
            "confidence": 0.88,
            "text_blocks": [{"text": "OCR文本", "confidence": 0.88}]
        }
    })

    # 任务3: 实体
    tasks.append({
        "type": "entity",
        "data": {
            "document_id": "batch_doc_1",
            "entities": [
                {"text": "北京", "type": "LOCATION"},
                {"text": "张三", "type": "PERSON"}
            ]
        }
    })

    # 批量执行
    reports = []
    for i, task in enumerate(tasks, 1):
        task_type = task["type"]
        task_data = task["data"]

        if task_type == "document":
            report = agent.validate_document(task_data)
        elif task_type == "ocr":
            report = agent.validate_ocr_result(task_data)
        elif task_type == "entity":
            report = agent.validate_entities(task_data)

        reports.append(report)
        print(f"\n任务 {i}/{len(tasks)}: {task_type}")
        print(f"  - 分数: {report.overall_score}/100")
        print(f"  - 结果: {'✓ 通过' if report.passed else '✗ 未通过'}")

    # 汇总统计
    passed = sum(1 for r in reports if r.passed)
    failed = len(reports) - passed
    avg_score = sum(r.overall_score for r in reports) / len(reports)

    print(f"\n批量检查汇总:")
    print(f"  - 总任务数: {len(reports)}")
    print(f"  - 通过: {passed}")
    print(f"  - 失败: {failed}")
    print(f"  - 平均分: {avg_score:.2f}/100")


# ==================== Example 7: 完整流水线质量检查 ====================

def example_7_full_pipeline_check():
    """
    示例7：完整流水线质量检查

    模拟完整的文档处理流水线，检查每个环节
    """
    print("\n" + "="*60)
    print("示例7：完整流水线质量检查")
    print("="*60)

    from app.agents.quality_control_agent import get_quality_control_agent

    agent = get_quality_control_agent()
    document_id = "pipeline_test_doc"

    print(f"\n处理文档: {document_id}")

    # 1. 文档转换
    print("\n[1/4] 文档转换质量检查...")
    doc_data = {
        "id": document_id,
        "content": "完整流水线测试文档内容" * 10,
        "format": "markdown",
        "metadata": {"title": "流水线测试", "created_at": "2024-01-09"}
    }
    doc_report = agent.validate_document(doc_data)
    print(f"  分数: {doc_report.overall_score}/100 - {'✓ 通过' if doc_report.passed else '✗ 未通过'}")

    # 2. 实体识别
    print("\n[2/4] 实体识别质量检查...")
    entity_data = {
        "document_id": document_id,
        "entities": [
            {"text": "北京", "type": "LOCATION"},
            {"text": "2024年", "type": "DATE"},
            {"text": "张三", "type": "PERSON"}
        ]
    }
    entity_report = agent.validate_entities(entity_data)
    print(f"  分数: {entity_report.overall_score}/100 - {'✓ 通过' if entity_report.passed else '✗ 未通过'}")

    # 3. 向量化
    print("\n[3/4] 向量化质量检查...")
    embedding_data = {
        "document_id": document_id,
        "embedding": np.random.randn(768).tolist()
    }
    emb_report = agent.validate_embedding(embedding_data)
    print(f"  分数: {emb_report.overall_score}/100 - {'✓ 通过' if emb_report.passed else '✗ 未通过'}")

    # 4. 知识图谱
    print("\n[4/4] 知识图谱质量检查...")
    graph_data = {
        "document_id": document_id,
        "nodes": [
            {"id": "n1", "label": "北京"},
            {"id": "n2", "label": "张三"},
            {"id": "n3", "label": "2024年"}
        ],
        "relationships": [
            {"source": "n2", "target": "n1", "type": "位于"},
            {"source": "n2", "target": "n3", "type": "时间"}
        ]
    }
    graph_report = agent.validate_knowledge_graph(graph_data)
    print(f"  分数: {graph_report.overall_score}/100 - {'✓ 通过' if graph_report.passed else '✗ 未通过'}")

    # 流水线总结
    print("\n" + "-"*60)
    print("流水线质量报告")
    print("-"*60)

    reports = [doc_report, entity_report, emb_report, graph_report]
    stages = ["文档转换", "实体识别", "向量化", "知识图谱"]

    overall_score = sum(r.overall_score for r in reports) / len(reports)
    all_passed = all(r.passed for r in reports)

    for stage, report in zip(stages, reports):
        status = "✓" if report.passed else "✗"
        print(f"{status} {stage:10s}: {report.overall_score:5.1f}/100")

    print("-"*60)
    print(f"总体评分: {overall_score:.2f}/100")
    print(f"流水线状态: {'✓ 全部通过' if all_passed else '✗ 存在问题'}")


# ==================== Example 8: HTTP API调用示例 ====================

def example_8_http_api_usage():
    """
    示例8：HTTP API调用

    展示如何通过REST API使用质量控制
    """
    print("\n" + "="*60)
    print("示例8：HTTP API调用示例")
    print("="*60)

    print("\n1. 文档质量检查:")
    print("""
    curl -X POST 'http://localhost:8000/api/quality/validate/document' \\
      -H 'Content-Type: application/json' \\
      -d '{
        "id": "doc123",
        "content": "文档内容...",
        "format": "markdown",
        "metadata": {
          "title": "测试文档",
          "created_at": "2024-01-09T00:00:00"
        }
      }'
    """)

    print("\n2. OCR质量检查:")
    print("""
    curl -X POST 'http://localhost:8000/api/quality/validate/ocr' \\
      -H 'Content-Type: application/json' \\
      -d '{
        "task_id": "ocr123",
        "text": "识别的文本",
        "confidence": 0.92,
        "text_blocks": [
          {"text": "文本块1", "confidence": 0.93}
        ]
      }'
    """)

    print("\n3. 批量检查:")
    print("""
    curl -X POST 'http://localhost:8000/api/quality/validate/batch' \\
      -H 'Content-Type: application/json' \\
      -d '{
        "tasks": [
          {
            "type": "document",
            "data": {"id": "doc1", "content": "...", "metadata": {}}
          },
          {
            "type": "ocr",
            "data": {"task_id": "ocr1", "text": "...", "confidence": 0.9}
          }
        ]
      }'
    """)

    print("\n4. 获取统计:")
    print("""
    curl -X GET 'http://localhost:8000/api/quality/statistics'
    """)

    print("\n5. 健康检查:")
    print("""
    curl -X GET 'http://localhost:8000/api/quality/health'
    """)


# ==================== 主函数 ====================

def main():
    """运行所有示例"""
    print("\n" + "="*60)
    print("FieldMind 质量控制系统 - 使用示例")
    print("="*60)

    try:
        # 运行所有示例
        example_1_basic_document_check()
        example_2_ocr_quality_check()
        example_3_entity_quality_check()
        example_4_embedding_quality_check()
        example_5_graph_quality_check()
        example_6_batch_quality_check()
        example_7_full_pipeline_check()
        example_8_http_api_usage()

        # 显示统计
        from app.agents.quality_control_agent import get_quality_control_agent
        agent = get_quality_control_agent()
        stats = agent.get_statistics()

        print("\n" + "="*60)
        print("总体统计")
        print("="*60)
        print(f"总检查次数: {stats['total_checks']}")
        print(f"通过: {stats['passed']}")
        print(f"失败: {stats['failed']}")
        print(f"通过率: {stats['pass_rate']:.2%}")
        print(f"自动修复: {stats['auto_fixed']}")
        print(f"自动修复率: {stats['auto_fix_rate']:.2%}")

    except Exception as e:
        logger.error(f"运行示例时出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
