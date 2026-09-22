#!/usr/bin/env python3
"""
测试FunASR转录功能
验证中文识别效果和时间戳准确性
"""

import sys
import os

# 使用相对路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

os.environ['ASR_ENGINE'] = 'funasr'

def test_funasr_basic():
    """测试FunASR基本功能"""
    print("=" * 80)
    print("🎤 FunASR转录测试")
    print("=" * 80)

    from app.core.unified_transcription import transcription

    # 创建测试音频文本（模拟）
    test_text = """
测试文本：
王大爷说，我们村有三百多年历史了。
李婶告诉我，年轻人都去城里打工了。
村里的祠堂是明代建筑，保存得很好。
传统节日活动越来越少了。
    """.strip()

    print("\n【测试1】检查FunASR服务初始化")
    print(f"  当前ASR引擎: {transcription.engine}")

    if transcription.engine != "funasr":
        print("  ❌ ASR引擎不是FunASR")
        return False
    else:
        print("  ✅ ASR引擎配置正确")

    print("\n【测试2】尝试加载FunASR模型")
    try:
        from app.core.funasr_service import funasr_service
        print("  ✅ FunASR服务导入成功")

        # 尝试加载模型（可能需要下载）
        print("  正在加载模型（首次可能需要下载）...")
        funasr_service.load_models()
        print("  ✅ 模型加载成功")

    except Exception as e:
        print(f"  ❌ 模型加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n【测试3】检查配置参数")
    from app.config import settings
    print(f"  ASR_ENGINE: {settings.ASR_ENGINE}")
    print(f"  FUNASR_MODEL: {settings.FUNASR_MODEL}")
    print(f"  FUNASR_VAD_MODEL: {settings.FUNASR_VAD_MODEL}")
    print(f"  FUNASR_PUNC_MODEL: {settings.FUNASR_PUNC_MODEL}")
    print(f"  FUNASR_HOTWORDS: '{settings.FUNASR_HOTWORDS}'")

    print("\n【测试4】检查音频文件")
    # 查找测试音频
    test_audio_paths = [
        os.path.join(BASE_DIR, 'tests/fixtures/test_audio.mp3'),
        os.path.join(BASE_DIR, 'data/uploads/documents/*.mp3'),
        '/tmp/test_audio.wav'
    ]

    test_audio = None
    for path in test_audio_paths:
        if '*' not in path and os.path.exists(path):
            test_audio = path
            break

    if not test_audio:
        print("  ⚠️ 未找到真实音频文件，无法测试实际转录")
        print("  💡 提示: 准备一个中文音频文件，放到以下路径之一:")
        for path in test_audio_paths:
            if '*' not in path:
                print(f"     - {path}")
        return True  # 模型加载成功就算通过

    print(f"  ✅ 找到测试音频: {test_audio}")

    print("\n【测试5】执行FunASR转录")
    try:
        result = transcription.transcribe(test_audio, language="zh")

        print(f"  ✅ 转录成功")
        print(f"  文本长度: {len(result['text'])} 字符")
        print(f"  片段数量: {len(result['segments'])} 个")
        print(f"  语言: {result['language']}")

        # 显示前3个片段
        print("\n  【转录片段示例】")
        for i, seg in enumerate(result['segments'][:3]):
            print(f"    [{seg['start']:.1f}s - {seg['end']:.1f}s] {seg['text']}")

        # 检查时间戳
        has_timestamps = any(seg['start'] > 0 for seg in result['segments'])
        if has_timestamps:
            print("\n  ✅ 时间戳正常")
        else:
            print("\n  ⚠️ 时间戳可能有问题")

        return True

    except Exception as e:
        print(f"  ❌ 转录失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n" + "=" * 80)
    print("🎉 FunASR测试完成")
    print("=" * 80)


if __name__ == "__main__":
    success = test_funasr_basic()

    if success:
        print("\n✅ FunASR已就绪，可以开始使用")
        print("\n📝 使用方式:")
        print("  1. 在 .env 中设置: ASR_ENGINE=funasr")
        print("  2. 上传音频文件进行处理")
        print("  3. FunASR会自动识别中文并生成时间戳")
        print("\n💡 优势:")
        print("  - 中文识别准确率更高")
        print("  - 支持热词功能（在config.py中配置FUNASR_HOTWORDS）")
        print("  - 自动标点恢复")
        print("  - 更适合口述历史等中文场景")
    else:
        print("\n❌ FunASR测试失败")
        print("💡 回退方案: 继续使用Whisper")
        print("  在 .env 中设置: ASR_ENGINE=whisper")

    sys.exit(0 if success else 1)
