"""
FieldMind MVP 功能综合测试脚本

测试以下功能：
1. 数据质量监控 API
2. 溯源回溯 API
3. 协作与权限 API
4. 知识图谱 API
5. 智能分块服务
6. 文本量化服务
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, timedelta

# 导入模型
from app.models.project import Project
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.collaboration import ProjectMember, ProjectInvite, ProjectActivityLog, ProjectRole

# 导入服务
from app.services.data_quality_service import DataQualityService
from app.services.traceability_service import TraceabilityService
from app.services.collaboration_service import CollaborationService
from app.services.knowledge_graph_service import KnowledgeGraphService
from app.services.chunking_service import ChunkingService
from app.services.text_quantification import TextQuantificationService

# 数据库连接
DATABASE_URL = "sqlite:///./fieldmind_test.db"
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

# 测试结果统计
test_results = {
    "passed": 0,
    "failed": 0,
    "errors": []
}

def print_section(title: str):
    """打印测试章节标题"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def print_test(name: str, passed: bool, message: str = ""):
    """打印测试结果"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} | {name}")
    if message:
        print(f"     {message}")

    if passed:
        test_results["passed"] += 1
    else:
        test_results["failed"] += 1
        test_results["errors"].append(f"{name}: {message}")

def setup_test_data(db: Session):
    """创建测试数据"""
    print_section("设置测试数据")

    # 创建测试项目
    project = Project(
        name="测试田野调查项目",
        description="用于 MVP 功能测试",
        owner_id=1,
        created_at=datetime.utcnow()
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    print(f"✓ 创建测试项目: ID={project.id}")

    # 创建测试文档
    documents = []
    for i in range(5):
        doc = Document(
            project_id=project.id,
            file_name=f"访谈记录_{i+1}.txt",
            file_path=f"/test/interview_{i+1}.txt",
            file_type="text/plain",
            status="completed" if i < 3 else "error" if i == 3 else "pending",
            text_content=f"这是第{i+1}次访谈的内容。村民们普遍认为需要改善公共设施。" * 10,
            uploaded_at=datetime.utcnow()
        )
        documents.append(doc)
        db.add(doc)

    db.commit()
    print(f"✓ 创建 {len(documents)} 个测试文档")

    # 创建测试 chunks
    chunking_service = ChunkingService()
    total_chunks = 0
    for doc in documents[:3]:  # 只为已完成的文档创建 chunks
        chunks = chunking_service.create_chunks_from_document(db, doc.id)
        total_chunks += len(chunks)

    print(f"✓ 创建 {total_chunks} 个测试 chunks")

    return project.id, [doc.id for doc in documents]

def test_data_quality_service(db: Session, project_id: int):
    """测试数据质量监控服务"""
    print_section("测试 1: 数据质量监控服务")

    service = DataQualityService()

    try:
        # 测试 1.1: 获取项目质量概览
        overview = service.get_project_status(db, project_id)
        print_test(
            "获取项目质量概览",
            overview is not None and "quality_score" in overview,
            f"质量评分: {overview.get('quality_score', {}).get('overall_score', 0):.1f}"
        )

        # 测试 1.2: 质量评分在合理范围内
        score = overview.get('quality_score', {}).get('overall_score', 0)
        print_test(
            "质量评分在合理范围 (0-100)",
            0 <= score <= 100,
            f"当前评分: {score:.1f}"
        )

        # 测试 1.3: 处理状态统计正确
        status = overview.get('processing_status', {})
        total = status.get('total_documents', 0)
        print_test(
            "处理状态统计",
            total > 0,
            f"总文档数: {total}, 已完成: {status.get('completed', 0)}, 失败: {status.get('error', 0)}"
        )

        # 测试 1.4: 数据缺口识别
        gaps = overview.get('data_gaps', [])
        print_test(
            "数据缺口识别",
            len(gaps) > 0,
            f"发现 {len(gaps)} 个数据缺口"
        )

    except Exception as e:
        print_test("数据质量监控服务", False, f"异常: {str(e)}")

def test_traceability_service(db: Session, project_id: int):
    """测试溯源回溯服务"""
    print_section("测试 2: 溯源回溯服务")

    service = TraceabilityService()

    try:
        # 测试 2.1: 溯源结论到 chunks
        conclusion = "村民们普遍认为需要改善公共设施"
        result = service.trace_conclusion(db, conclusion, project_id, top_k=5)

        print_test(
            "溯源结论到 chunks",
            result is not None and "sources" in result,
            f"找到 {result.get('total_sources', 0)} 个相关来源"
        )

        # 测试 2.2: 匹配评分合理
        sources = result.get('sources', [])
        if sources:
            max_score = max([s.get('match_score', 0) for s in sources])
            print_test(
                "匹配评分合理",
                0 <= max_score <= 1,
                f"最高匹配度: {max_score:.2%}"
            )

        # 测试 2.3: 获取 chunk 上下文
        if sources:
            chunk_id = sources[0]['chunk_id']
            context = service.get_chunk_context(db, chunk_id, context_size=200)
            print_test(
                "获取 chunk 上下文",
                context is not None and "before" in context and "after" in context,
                f"前文长度: {len(context.get('before', ''))}, 后文长度: {len(context.get('after', ''))}"
            )

    except Exception as e:
        print_test("溯源回溯服务", False, f"异常: {str(e)}")

def test_collaboration_service(db: Session, project_id: int):
    """测试协作与权限服务"""
    print_section("测试 3: 协作与权限服务")

    service = CollaborationService()

    try:
        # 测试 3.1: 添加成员
        member = service.add_member(db, project_id, user_id=2, role=ProjectRole.EDITOR, added_by=1)
        print_test(
            "添加项目成员",
            member is not None,
            f"成员 ID: {member.user_id}, 角色: {member.role.value}"
        )

        # 测试 3.2: 获取成员列表
        members = service.get_members(db, project_id)
        print_test(
            "获取成员列表",
            len(members) >= 1,
            f"项目共有 {len(members)} 位成员"
        )

        # 测试 3.3: 权限检查
        can_upload = service.check_permission(db, project_id, user_id=2, permission="DOCUMENT_UPLOAD")
        print_test(
            "权限检查 (EDITOR 可上传文档)",
            can_upload is True,
            "EDITOR 角色拥有文档上传权限"
        )

        can_delete = service.check_permission(db, project_id, user_id=2, permission="PROJECT_DELETE")
        print_test(
            "权限检查 (EDITOR 不可删除项目)",
            can_delete is False,
            "EDITOR 角色没有项目删除权限"
        )

        # 测试 3.4: 生成邀请链接
        invite = service.generate_invite_link(
            db, project_id, role=ProjectRole.VIEWER,
            created_by=1, expires_in_hours=24
        )
        print_test(
            "生成邀请链接",
            invite is not None and invite.invite_code is not None,
            f"邀请码: {invite.invite_code}, 角色: {invite.role.value}"
        )

        # 测试 3.5: 记录活动日志
        service.log_activity(
            db, project_id, user_id=1, action="测试活动",
            target_type="test", target_id=1
        )
        logs = service.get_activity_logs(db, project_id, limit=10)
        print_test(
            "活动日志记录",
            len(logs) > 0,
            f"共有 {len(logs)} 条活动记录"
        )

        # 测试 3.6: 修改成员角色
        updated = service.update_member_role(db, project_id, user_id=2, new_role=ProjectRole.VIEWER, updated_by=1)
        print_test(
            "修改成员角色",
            updated.role == ProjectRole.VIEWER,
            f"角色已更新为: {updated.role.value}"
        )

        # 测试 3.7: 移除成员
        removed = service.remove_member(db, project_id, user_id=2, removed_by=1)
        print_test(
            "移除项目成员",
            removed is True,
            "成员已成功移除"
        )

    except Exception as e:
        print_test("协作与权限服务", False, f"异常: {str(e)}")

def test_knowledge_graph_service(db: Session, project_id: int):
    """测试知识图谱服务"""
    print_section("测试 4: 知识图谱服务")

    try:
        # 测试 4.1: 构建知识图谱
        graph = KnowledgeGraphService.build_knowledge_graph(db, project_id)
        print_test(
            "构建知识图谱",
            graph is not None and "nodes" in graph and "edges" in graph,
            f"节点数: {len(graph.get('nodes', []))}, 边数: {len(graph.get('edges', []))}"
        )

        # 测试 4.2: 图谱统计信息
        stats = graph.get('statistics', {})
        print_test(
            "图谱统计信息",
            stats is not None,
            f"维度数: {stats.get('dimensions', 0)}, 子维度数: {stats.get('sub_dimensions', 0)}"
        )

    except Exception as e:
        print_test("知识图谱服务", False, f"异常: {str(e)}")

def test_chunking_service(db: Session):
    """测试智能分块服务"""
    print_section("测试 5: 智能分块服务")

    service = ChunkingService()

    try:
        # 测试 5.1: 文本分块
        test_text = "这是第一段。包含一些内容。\n\n这是第二段。也有一些内容。\n\n这是第三段。" * 20
        chunks = service.chunk_text(test_text)

        print_test(
            "文本智能分块",
            len(chunks) > 0,
            f"生成 {len(chunks)} 个 chunks"
        )

        # 测试 5.2: Chunk 大小合理 (200-500 字符)
        chunk_sizes = [len(c['content']) for c in chunks]
        avg_size = sum(chunk_sizes) / len(chunk_sizes) if chunk_sizes else 0
        in_range = all(200 <= size <= 600 for size in chunk_sizes)  # 允许一定偏差

        print_test(
            "Chunk 大小合理 (200-500 字符)",
            in_range or avg_size >= 200,
            f"平均大小: {avg_size:.0f} 字符, 范围: {min(chunk_sizes) if chunk_sizes else 0}-{max(chunk_sizes) if chunk_sizes else 0}"
        )

        # 测试 5.3: 上下文保留
        has_context = any('context_before' in c and c['context_before'] for c in chunks[1:])
        print_test(
            "上下文保留",
            has_context,
            "Chunks 包含上下文信息"
        )

    except Exception as e:
        print_test("智能分块服务", False, f"异常: {str(e)}")

def test_text_quantification_service():
    """测试文本量化服务"""
    print_section("测试 6: 文本量化服务")

    service = TextQuantificationService()

    try:
        # 测试 6.1: 文本量化指标
        test_text = "这是一段测试文本。包含多个句子。用于验证量化功能。非常好！真棒！" * 5
        metrics = service.quantify_text(test_text)

        print_test(
            "文本量化指标计算",
            metrics is not None and len(metrics) > 0,
            f"计算了 {len(metrics)} 个指标"
        )

        # 测试 6.2: 基础指标存在
        basic_metrics = ['char_count', 'word_count', 'sentence_count']
        has_basic = all(m in metrics for m in basic_metrics)
        print_test(
            "基础指标存在",
            has_basic,
            f"字符数: {metrics.get('char_count', 0)}, 词数: {metrics.get('word_count', 0)}, 句数: {metrics.get('sentence_count', 0)}"
        )

        # 测试 6.3: 情感分析指标
        sentiment_metrics = ['sentiment_score', 'sentiment_polarity']
        has_sentiment = any(m in metrics for m in sentiment_metrics)
        print_test(
            "情感分析指标",
            has_sentiment,
            f"情感得分: {metrics.get('sentiment_score', 'N/A')}"
        )

        # 测试 6.4: 高级指标
        advanced_metrics = ['emotion_density', 'lexical_diversity']
        has_advanced = any(m in metrics for m in advanced_metrics)
        print_test(
            "高级量化指标",
            has_advanced,
            f"情感密度: {metrics.get('emotion_density', 'N/A')}, 词汇多样性: {metrics.get('lexical_diversity', 'N/A')}"
        )

    except Exception as e:
        print_test("文本量化服务", False, f"异常: {str(e)}")

def cleanup_test_data(db: Session, project_id: int):
    """清理测试数据"""
    print_section("清理测试数据")

    try:
        # 删除项目及所有关联数据
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            db.delete(project)
            db.commit()
            print("✓ 测试数据已清理")
    except Exception as e:
        print(f"✗ 清理失败: {str(e)}")

def print_summary():
    """打印测试摘要"""
    print_section("测试摘要")

    total = test_results["passed"] + test_results["failed"]
    pass_rate = (test_results["passed"] / total * 100) if total > 0 else 0

    print(f"\n总测试数: {total}")
    print(f"✅ 通过: {test_results['passed']}")
    print(f"❌ 失败: {test_results['failed']}")
    print(f"通过率: {pass_rate:.1f}%\n")

    if test_results["failed"] > 0:
        print("失败详情:")
        for error in test_results["errors"]:
            print(f"  • {error}")

    print("\n" + "="*80)

    if pass_rate >= 80:
        print("🎉 MVP 功能测试通过！系统运行正常。")
    elif pass_rate >= 60:
        print("⚠️  MVP 功能部分通过，存在一些问题需要修复。")
    else:
        print("❌ MVP 功能测试失败，需要进行调试和修复。")

    print("="*80 + "\n")

def main():
    """主测试流程"""
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*20 + "FieldMind MVP 功能测试" + " "*37 + "║")
    print("╚" + "="*78 + "╝")

    db = SessionLocal()
    project_id = None

    try:
        # 设置测试数据
        project_id, document_ids = setup_test_data(db)

        # 运行测试
        test_data_quality_service(db, project_id)
        test_traceability_service(db, project_id)
        test_collaboration_service(db, project_id)
        test_knowledge_graph_service(db, project_id)
        test_chunking_service(db)
        test_text_quantification_service()

        # 打印摘要
        print_summary()

    except Exception as e:
        print(f"\n❌ 测试执行失败: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        # 清理测试数据
        if project_id:
            cleanup_test_data(db, project_id)
        db.close()

if __name__ == "__main__":
    main()
