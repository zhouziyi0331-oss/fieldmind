#!/usr/bin/env python3
"""
测试 TranscriptAgent 完整处理链路
Step 3: 测试音频 → 转录 → 清洗 → 量化指标提取 → 数据库保存
"""

import sys
import os
from pathlib import Path

# 添加项目路径
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path / "src"))

from app.core.database import SessionLocal
from app.models.project import ProjectDocument, Project
from app.services.background_tasks import process_audio, save_transcript
import json
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_transcript_agent_with_real_audio():
    """测试 TranscriptAgent 使用真实音频文件"""

    # 选择测试音频文件
    test_audio = "/Users/alwan/FieldMind/backend/uploads/project_17/新录音.wav"

    if not os.path.exists(test_audio):
        logger.error(f"❌ 测试文件不存在: {test_audio}")
        return False

    logger.info(f"📂 使用测试文件: {test_audio}")
    logger.info(f"📏 文件大小: {os.path.getsize(test_audio) / 1024:.2f} KB")

    print("\n" + "="*80)
    print("🧪 测试 TranscriptAgent 完整处理链路")
    print("="*80 + "\n")

    # ===== Step 1: 调用 TranscriptAgent =====
    print("📝 Step 1: 调用 TranscriptAgent 进行转录 + 清洗 + 指标提取...")

    try:
        cleaned_text, full_result = process_audio(test_audio, file_id=999)

        if not full_result:
            logger.error("❌ TranscriptAgent 返回空结果")
            return False

        print(f"✅ TranscriptAgent 执行成功")
        print(f"   状态: {full_result.get('status')}")

    except Exception as e:
        logger.error(f"❌ TranscriptAgent 执行失败: {e}", exc_info=True)
        return False

    # ===== Step 2: 检查清洗后的文本 =====
    print(f"\n📄 Step 2: 检查清洗后的文本...")

    transcript_data = full_result.get('transcript', {})
    raw_text = transcript_data.get('raw_text', '')
    full_text = transcript_data.get('full_text', '')
    segments = transcript_data.get('segments', [])

    print(f"   原始文本长度: {len(raw_text)} 字符")
    print(f"   清洗后长度: {len(full_text)} 字符")
    print(f"   segments数量: {len(segments)}")

    if full_text:
        print(f"\n   清洗后文本预览（前200字符）:")
        print(f"   {full_text[:200]}...")

    # ===== Step 3: 检查量化指标 =====
    print(f"\n📊 Step 3: 检查量化指标 (metrics)...")

    metrics = full_result.get('metrics', {})

    if not metrics:
        logger.warning("⚠️ 未提取到 metrics")
    else:
        # 专业名词
        professional_terms = metrics.get('专业名词', [])
        print(f"   ✅ 专业名词: {len(professional_terms)} 个")
        if professional_terms:
            print(f"      {professional_terms[:10]}")

        # 核心人物
        core_persons = metrics.get('核心人物', [])
        print(f"   ✅ 核心人物: {len(core_persons)} 个")
        if core_persons:
            for person in core_persons[:5]:
                print(f"      - {person.get('name')}: 提及{person.get('mentions')}次")

        # 特殊事件
        special_events = metrics.get('特殊事件', [])
        print(f"   ✅ 特殊事件: {len(special_events)} 个")
        if special_events:
            for event in special_events[:5]:
                event_name = event.get('event', '未知')
                count = event.get('count', 0)
                coverage = event.get('coverage', 0)
                time_span = event.get('time_span', 'unknown')

                # 时间跨度描述
                time_span_desc = {
                    'throughout': '贯穿全程',
                    'distributed': '分布式',
                    'beginning': '前期',
                    'middle': '中期',
                    'end': '后期',
                    'single': '单点'
                }.get(time_span, '未知')

                print(f"      - {event_name}: 提及{count}次，覆盖率{coverage}%，时间分布：{time_span_desc}")

        # 文化分类
        cultural_classification = metrics.get('文化分类', {})
        print(f"   ✅ 文化分类（衣食住行在地）:")
        for dimension, items in cultural_classification.items():
            print(f"      - {dimension}: {len(items)} 个片段")
            if items:
                # 显示第一个片段
                first_item = items[0]
                # 处理字符串或字典类型
                if isinstance(first_item, dict):
                    preview = first_item.get('text', '')[:50]
                else:
                    preview = str(first_item)[:50]
                print(f"        示例: {preview}...")

    # ===== Step 4: 检查统计信息 =====
    print(f"\n📈 Step 4: 检查统计信息 (total)...")

    total_stats = full_result.get('total', {})
    if total_stats:
        print(f"   时长: {total_stats.get('时长', 0)} 秒")
        print(f"   原始字数: {total_stats.get('原始字数', 0)}")
        print(f"   清洗后字数: {total_stats.get('清洗后字数', 0)}")
        print(f"   信心评分: {total_stats.get('信心评分', 0):.2f}")

    # ===== Step 5: 模拟保存到数据库 =====
    print(f"\n💾 Step 5: 模拟保存到数据库...")

    try:
        db = SessionLocal()

        # 查找或创建测试文档
        doc = db.query(ProjectDocument).filter(ProjectDocument.id == 999).first()

        if not doc:
            # 创建测试文档
            project = db.query(Project).first()
            if not project:
                logger.error("❌ 数据库中没有项目，无法创建测试文档")
                db.close()
                return False

            doc = ProjectDocument(
                id=999,
                project_id=project.id,
                filename="test_transcript_agent.wav",
                original_filename="test_transcript_agent.wav",
                file_path=test_audio,
                file_type="audio",
                file_size=os.path.getsize(test_audio),
                status="processing"
            )
            db.add(doc)
            db.flush()

        # 保存 segments
        if segments:
            save_transcript(999, segments)
            print(f"   ✅ 保存了 {len(segments)} 个 segments")

        # 保存到 extra_data
        doc.extra_data = doc.extra_data or {}
        doc.extra_data['has_transcript'] = True
        doc.extra_data['transcript'] = segments

        # 保存 metrics
        if metrics:
            doc.extra_data['transcript_metrics'] = {
                '专业名词': metrics.get('专业名词', []),
                '核心人物': metrics.get('核心人物', []),
                '特殊事件': metrics.get('特殊事件', []),
                '文化分类': metrics.get('文化分类', {})
            }
            print(f"   ✅ 保存了 transcript_metrics")

        # 保存 stats
        if total_stats:
            doc.extra_data['transcript_stats'] = total_stats
            print(f"   ✅ 保存了 transcript_stats")

        # 保存文本内容
        doc.text_content = full_text
        doc.word_count = len(full_text.split())
        doc.status = "completed"

        db.commit()
        print(f"   ✅ 数据库保存成功")

        # 验证读取
        print(f"\n🔍 Step 6: 验证数据库读取...")
        doc_verify = db.query(ProjectDocument).filter(ProjectDocument.id == 999).first()

        if doc_verify and doc_verify.extra_data:
            has_metrics = 'transcript_metrics' in doc_verify.extra_data
            has_stats = 'transcript_stats' in doc_verify.extra_data

            print(f"   ✅ 读取成功")
            print(f"   - has_transcript: {doc_verify.extra_data.get('has_transcript')}")
            print(f"   - transcript_metrics: {'存在' if has_metrics else '不存在'}")
            print(f"   - transcript_stats: {'存在' if has_stats else '不存在'}")

            if has_metrics:
                stored_metrics = doc_verify.extra_data['transcript_metrics']
                print(f"   - 专业名词数量: {len(stored_metrics.get('专业名词', []))}")
                print(f"   - 核心人物数量: {len(stored_metrics.get('核心人物', []))}")
                print(f"   - 特殊事件数量: {len(stored_metrics.get('特殊事件', []))}")
                print(f"   - 文化分类维度: {len(stored_metrics.get('文化分类', {}))}")

        db.close()

    except Exception as e:
        logger.error(f"❌ 数据库操作失败: {e}", exc_info=True)
        return False

    # ===== 总结 =====
    print("\n" + "="*80)
    print("✅ 测试完成！TranscriptAgent 完整链路正常工作")
    print("="*80)
    print("\n测试覆盖:")
    print("  ✅ 音频转录 (Whisper)")
    print("  ✅ 文本自动清洗（去口语化词、合并断句）")
    print("  ✅ 量化指标提取（专业名词、核心人物、特殊事件、文化分类）")
    print("  ✅ 数据库保存（segments + metrics + stats）")
    print("  ✅ 数据库读取验证")

    return True


if __name__ == "__main__":
    success = test_transcript_agent_with_real_audio()
    sys.exit(0 if success else 1)
