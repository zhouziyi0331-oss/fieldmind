#!/usr/bin/env python3
"""
快速测试 TranscriptAgent - 使用小文件
"""

import sys
import os
from pathlib import Path

# 添加项目路径
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path / "src"))

from app.services.agents.transcript_agent import TranscriptAgent
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_transcript_agent_simple():
    """简单测试 TranscriptAgent"""

    # 选择一个小的测试文件
    test_audio = "/Users/alwan/FieldMind/uploads/project_1/simple_test.mp3"

    if not os.path.exists(test_audio):
        # 尝试其他文件
        test_audio = "/Users/alwan/FieldMind/external-tools/markitdown/packages/markitdown/tests/test_files/test.mp3"

    if not os.path.exists(test_audio):
        logger.error(f"❌ 测试文件不存在")
        return False

    logger.info(f"📂 使用测试文件: {test_audio}")
    logger.info(f"📏 文件大小: {os.path.getsize(test_audio) / 1024:.2f} KB")

    print("\n" + "="*80)
    print("🧪 快速测试 TranscriptAgent")
    print("="*80 + "\n")

    # 测试 TranscriptAgent 初始化
    print("📝 Step 1: 初始化 TranscriptAgent...")
    try:
        agent = TranscriptAgent()
        print(f"✅ TranscriptAgent 初始化成功")
        print(f"   角色: {agent.role}")
        print(f"   名称: {agent.name}")
    except Exception as e:
        logger.error(f"❌ TranscriptAgent 初始化失败: {e}", exc_info=True)
        return False

    # 测试转录
    print(f"\n📝 Step 2: 测试转录功能...")
    try:
        result = agent.transcribe_file(
            file_path=test_audio,
            file_type='audio',
            language='auto',
            file_id=888,
            enable_metrics=True
        )

        print(f"✅ 转录完成")
        print(f"   状态: {result.get('status')}")

        # 检查结果结构
        transcript_data = result.get('transcript', {})
        print(f"\n   转录数据:")
        print(f"   - 原始文本长度: {len(transcript_data.get('raw_text', ''))} 字符")
        print(f"   - 清洗后文本长度: {len(transcript_data.get('full_text', ''))} 字符")
        print(f"   - segments数量: {len(transcript_data.get('segments', []))}")

        # 检查 metrics
        metrics = result.get('metrics', {})
        if metrics:
            print(f"\n   量化指标:")
            print(f"   - 专业名词: {len(metrics.get('专业名词', []))} 个")
            print(f"   - 核心人物: {len(metrics.get('核心人物', []))} 个")
            print(f"   - 特殊事件: {len(metrics.get('特殊事件', []))} 个")
            print(f"   - 文化分类维度: {len(metrics.get('文化分类', {}))}")

        # 检查 stats
        stats = result.get('total', {})
        if stats:
            print(f"\n   统计信息:")
            print(f"   - 时长: {stats.get('时长', 0)} 秒")
            print(f"   - 原始字数: {stats.get('原始字数', 0)}")
            print(f"   - 清洗后字数: {stats.get('清洗后字数', 0)}")

        # 显示文本预览
        full_text = transcript_data.get('full_text', '')
        if full_text:
            print(f"\n   文本预览:")
            print(f"   {full_text[:200]}...")

    except Exception as e:
        logger.error(f"❌ 转录失败: {e}", exc_info=True)
        return False

    print("\n" + "="*80)
    print("✅ 快速测试完成！")
    print("="*80)

    return True


if __name__ == "__main__":
    success = test_transcript_agent_simple()
    sys.exit(0 if success else 1)
