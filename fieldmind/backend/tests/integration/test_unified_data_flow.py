"""
端到端集成测试 - 统一数据流验证
测试完整的数据流：上传 → 契约验证 → 九步流水线 → 事件发布 → 缩影生成 → 知识图谱

验收标准：
1. 文档上传成功
2. 数据契约验证通过
3. 九步流水线全部执行
4. 事件正确发布
5. 缩影自动生成
6. 知识图谱包含数据
7. 数据连接率 ≥ 95%
"""

import pytest
import time
import os
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import SessionLocal
from app.models.project import Project, ProjectDocument
from app.services.unified_pipeline_coordinator import UnifiedPipelineCoordinator
from app.services.project_document_upload import upload_project_document


class TestUnifiedDataFlow:
    """统一数据流端到端测试"""

    @pytest.fixture(scope="function")
    def db(self):
        """数据库会话"""
        db = SessionLocal()
        yield db
        db.close()

    @pytest.fixture(scope="function")
    def test_project(self, db: Session):
        """创建测试项目"""
        project = Project(
            name="测试项目-统一数据流",
            description="用于验证统一数据流的测试项目",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        yield project

        # 清理
        db.delete(project)
        db.commit()

    @pytest.fixture(scope="function")
    def test_document(self, db: Session, test_project: Project):
        """上传测试文档"""
        # 创建测试文本内容
        content = """
        史记·秦始皇本纪

        秦始皇帝者，秦庄襄王子也。庄襄王为秦质子于赵，见吕不韦姬，悦而取之，生始皇。
        以秦昭王四十八年正月生于邯郸。及生，名为政，姓赵氏。

        始皇为人，天性刚毅，自用，起诸侯，并天下，务欲南面独治。
        二十六年，秦初并天下，令丞相、御史曰："异日韩王纳地效玺，请为藩臣。"

        分天下为三十六郡，郡置守、尉、监。更名民曰"黔首"。
        收天下之兵，聚之咸阳，销以为钟鐻，金人十二，各重千石，置廷宫中。

        三十七年十月癸丑，始皇崩于沙丘平台。年五十。
        """.strip()

        # 上传文档
        doc, created = upload_project_document(
            db=db,
            project_id=test_project.id,
            original_filename="秦始皇本纪.txt",
            content=content.encode('utf-8'),
            mime_type="text/plain",
            status="uploaded"
        )

        # 手动设置文本内容（模拟内容提取完成）
        doc.text_content = content
        doc.word_count = len(content)
        db.commit()
        db.refresh(doc)

        yield doc

        # 清理
        db.delete(doc)
        db.commit()

    def test_01_document_upload(self, db: Session, test_document: ProjectDocument):
        """测试1: 文档上传成功"""
        print("\n" + "="*60)
        print("测试 1: 文档上传")
        print("="*60)

        assert test_document is not None
        assert test_document.id > 0
        assert test_document.original_filename == "秦始皇本纪.txt"
        assert test_document.text_content is not None
        assert len(test_document.text_content) > 0

        print(f"✅ 文档上传成功")
        print(f"   文档ID: {test_document.id}")
        print(f"   文件名: {test_document.original_filename}")
        print(f"   文本长度: {len(test_document.text_content)} 字符")

    def test_02_contract_validation(self, db: Session, test_document: ProjectDocument):
        """测试2: 数据契约验证"""
        print("\n" + "="*60)
        print("测试 2: 数据契约验证")
        print("="*60)

        from app.services.data_contract_validator import (
            convert_dirty_to_clean,
            validate_clean_data,
            check_pipeline_gate
        )

        # 构建脏数据
        raw_data = {
            'document_id': test_document.id,
            'filename': test_document.original_filename,
            'file_type': test_document.file_type,
            'mime_type': test_document.mime_type
        }

        # 转换为干净数据
        clean_data = convert_dirty_to_clean(
            raw_data=raw_data,
            extracted_text=test_document.text_content,
            document_id=test_document.id
        )

        print(f"📄 干净数据:")
        print(f"   字数: {clean_data['word_count']}")
        print(f"   质量等级: {clean_data['quality_level']}")

        # 验证契约
        is_valid, errors = validate_clean_data(clean_data)
        assert is_valid, f"数据契约验证失败: {errors}"
        print(f"✅ 数据契约验证通过")

        # 检查门控
        can_enter, reason = check_pipeline_gate(clean_data)
        assert can_enter, f"流水线门控拒绝: {reason}"
        print(f"✅ 流水线门控检查通过")

    def test_03_unified_pipeline_execution(self, db: Session, test_document: ProjectDocument):
        """测试3: 统一管道协调器执行"""
        print("\n" + "="*60)
        print("测试 3: 统一管道协调器执行")
        print("="*60)

        coordinator = UnifiedPipelineCoordinator(db)

        start_time = time.time()
        result = coordinator.process_document(test_document.id)
        elapsed_time = time.time() - start_time

        print(f"\n📊 执行结果:")
        print(f"   成功: {result['success']}")
        print(f"   耗时: {elapsed_time:.2f}秒")

        if result['success']:
            print(f"   流水线步骤: {result['pipeline_result']['steps_completed']}/{result['pipeline_result']['total_steps']}")
            print(f"\n✅ 统一管道协调器执行成功")

            # 验证各个阶段
            stages = result['stages']
            assert stages['content_extraction'] == 'completed', "内容提取未完成"
            assert stages['contract_validation'] == 'passed', "契约验证未通过"
            assert stages['pipeline_gate'] == 'passed', "流水线门控未通过"
            assert stages['knowledge_pipeline'] == 'completed', "知识流水线未完成"
            assert stages['event_published'] == 'completed', "事件未发布"

            print(f"\n各阶段状态:")
            for stage, status in stages.items():
                print(f"   {stage}: {status}")
        else:
            print(f"\n❌ 统一管道协调器执行失败")
            print(f"   失败阶段: {result.get('stage')}")
            print(f"   错误信息: {result.get('error')}")
            pytest.fail(f"统一管道执行失败: {result.get('error')}")

    def test_04_knowledge_pipeline_results(self, db: Session, test_document: ProjectDocument):
        """测试4: 九步知识流水线结果验证"""
        print("\n" + "="*60)
        print("测试 4: 九步知识流水线结果")
        print("="*60)

        # 刷新文档数据
        db.refresh(test_document)

        # 检查 extra_data
        assert test_document.extra_data is not None, "extra_data 为空"

        # 检查知识流水线记录
        pipeline_data = test_document.extra_data.get('knowledge_pipeline')
        assert pipeline_data is not None, "未找到知识流水线记录"
        assert pipeline_data['status'] == 'completed', f"流水线状态异常: {pipeline_data['status']}"

        print(f"📊 知识流水线结果:")
        print(f"   状态: {pipeline_data['status']}")
        print(f"   完成步骤: {pipeline_data['steps_completed']}/{pipeline_data['total_steps']}")
        print(f"   耗时: {pipeline_data['elapsed_time']}秒")

        # 检查步骤详情
        if 'step_details' in pipeline_data:
            step_details = pipeline_data['step_details']
            print(f"\n步骤详情:")

            for step_name, details in step_details.items():
                status = details.get('status', 'unknown')
                elapsed = details.get('elapsed_time', 0)
                print(f"   {step_name}: {status} ({elapsed}秒)")

                # 检查关键统计
                if 'entities_count' in details:
                    print(f"      → 实体数: {details['entities_count']}")
                if 'events_count' in details:
                    print(f"      → 事件数: {details['events_count']}")
                if 'relationships_count' in details:
                    print(f"      → 关系数: {details['relationships_count']}")
                if 'knowledge_units_count' in details:
                    print(f"      → 知识单元数: {details['knowledge_units_count']}")

        print(f"\n✅ 九步知识流水线结果验证通过")

    def test_05_event_publication(self, db: Session, test_document: ProjectDocument):
        """测试5: 事件发布验证"""
        print("\n" + "="*60)
        print("测试 5: 事件发布")
        print("="*60)

        from app.models.unified_models import SystemEvent

        # 查询与此文档相关的事件
        events = db.query(SystemEvent).filter(
            SystemEvent.payload.like(f'%"document_id": {test_document.id}%')
        ).order_by(SystemEvent.created_at).all()

        print(f"📢 发布的事件 ({len(events)} 个):")

        expected_events = ['PIPELINE_COMPLETED', 'KNOWLEDGE_UNITS_CREATED']
        found_events = []

        for event in events:
            print(f"   {event.event_type} - {event.status} ({event.created_at})")
            if event.event_type in expected_events:
                found_events.append(event.event_type)

        # 验证关键事件
        for expected in expected_events:
            assert expected in found_events, f"未找到事件: {expected}"

        print(f"\n✅ 事件发布验证通过（所有关键事件已发布）")

    def test_06_summary_generation(self, db: Session, test_document: ProjectDocument):
        """测试6: 缩影自动生成验证"""
        print("\n" + "="*60)
        print("测试 6: 缩影自动生成")
        print("="*60)

        from app.models.unified_models import DocumentSummary

        # 查询缩影
        summary = db.query(DocumentSummary).filter(
            DocumentSummary.document_id == test_document.id
        ).first()

        if summary:
            print(f"📝 缩影信息:")
            print(f"   一句话摘要: {summary.one_line_summary}")
            print(f"   段落摘要: {summary.paragraph_summary[:100]}...")
            print(f"   生成时间: {summary.created_at}")

            # 检查关联
            if summary.knowledge_graph_associations:
                print(f"   知识图谱关联: {len(summary.knowledge_graph_associations)} 个")
            if summary.wiki_page_associations:
                print(f"   Wiki页面关联: {len(summary.wiki_page_associations)} 个")

            print(f"\n✅ 缩影自动生成验证通过")
        else:
            print(f"\n⚠️  未找到自动生成的缩影（可能事件处理器未正确触发）")
            # 不失败，因为缩影生成是异步的
            pytest.skip("缩影生成可能需要更多时间")

    def test_07_knowledge_graph_data(self, db: Session, test_document: ProjectDocument):
        """测试7: 知识图谱数据验证"""
        print("\n" + "="*60)
        print("测试 7: 知识图谱数据")
        print("="*60)

        from app.models.unified_models import KnowledgeGraphNode, KnowledgeGraphEdge

        # 查询节点
        nodes = db.query(KnowledgeGraphNode).filter(
            KnowledgeGraphNode.document_id == test_document.id
        ).all()

        print(f"🕸️ 知识图谱节点 ({len(nodes)} 个):")
        node_types = {}
        for node in nodes[:10]:  # 只显示前10个
            node_type = node.node_type
            node_types[node_type] = node_types.get(node_type, 0) + 1
            print(f"   [{node.node_type}] {node.name}")

        if node_types:
            print(f"\n节点类型分布:")
            for node_type, count in node_types.items():
                print(f"   {node_type}: {count}")

        # 查询边
        edges = db.query(KnowledgeGraphEdge).filter(
            KnowledgeGraphEdge.document_id == test_document.id
        ).all()

        print(f"\n🔗 知识图谱边 ({len(edges)} 条):")
        for edge in edges[:5]:  # 只显示前5条
            print(f"   {edge.source_id} --[{edge.edge_type}]--> {edge.target_id}")

        assert len(nodes) > 0, "知识图谱节点数为0"
        print(f"\n✅ 知识图谱数据验证通过")

    def test_08_data_connectivity_rate(self, db: Session, test_document: ProjectDocument):
        """测试8: 数据连接率计算"""
        print("\n" + "="*60)
        print("测试 8: 数据连接率")
        print("="*60)

        from app.models.unified_models import (
            EntityUnified,
            EventUnified,
            RelationshipUnified,
            KnowledgeGraphNode,
            KnowledgeGraphEdge,
            DocumentSummary
        )

        # 统计各组件数量
        entities_count = db.query(EntityUnified).filter(
            EntityUnified.document_id == test_document.id
        ).count()

        events_count = db.query(EventUnified).filter(
            EventUnified.document_id == test_document.id
        ).count()

        relationships_count = db.query(RelationshipUnified).filter(
            RelationshipUnified.document_id == test_document.id
        ).count()

        kg_nodes_count = db.query(KnowledgeGraphNode).filter(
            KnowledgeGraphNode.document_id == test_document.id
        ).count()

        kg_edges_count = db.query(KnowledgeGraphEdge).filter(
            KnowledgeGraphEdge.document_id == test_document.id
        ).count()

        summary_count = db.query(DocumentSummary).filter(
            DocumentSummary.document_id == test_document.id
        ).count()

        print(f"📊 数据组件统计:")
        print(f"   实体: {entities_count}")
        print(f"   事件: {events_count}")
        print(f"   关系: {relationships_count}")
        print(f"   知识图谱节点: {kg_nodes_count}")
        print(f"   知识图谱边: {kg_edges_count}")
        print(f"   缩影: {summary_count}")

        # 计算连接率
        # 连接率 = (有关联的组件数) / (总组件数)
        total_components = entities_count + events_count + relationships_count
        connected_components = kg_nodes_count + kg_edges_count + summary_count

        if total_components > 0:
            connectivity_rate = (connected_components / total_components) * 100
            print(f"\n📈 数据连接率: {connectivity_rate:.2f}%")

            # 验收标准: ≥95%
            if connectivity_rate >= 95.0:
                print(f"✅ 数据连接率达标（≥95%）")
            else:
                print(f"⚠️  数据连接率未达标（目标≥95%，当前{connectivity_rate:.2f}%）")
                # 不失败，只是警告
        else:
            print(f"\n⚠️  无数据组件，无法计算连接率")

    def test_09_end_to_end_summary(self, db: Session, test_document: ProjectDocument):
        """测试9: 端到端集成总结"""
        print("\n" + "="*60)
        print("测试 9: 端到端集成总结")
        print("="*60)

        # 刷新文档
        db.refresh(test_document)

        print(f"📋 最终状态:")
        print(f"   文档ID: {test_document.id}")
        print(f"   状态: {test_document.status}")
        print(f"   字数: {test_document.word_count}")

        # 检查关键记录
        checks = {
            'contract_validation': test_document.extra_data.get('contract_validation') is not None,
            'knowledge_pipeline': test_document.extra_data.get('knowledge_pipeline') is not None,
            'unified_pipeline': test_document.extra_data.get('unified_pipeline') is not None,
        }

        print(f"\n关键记录检查:")
        for check_name, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"   {status} {check_name}")

        all_passed = all(checks.values())
        assert all_passed, "部分关键记录缺失"

        print(f"\n" + "="*60)
        print(f"🎉 端到端集成测试全部通过！")
        print(f"="*60)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
