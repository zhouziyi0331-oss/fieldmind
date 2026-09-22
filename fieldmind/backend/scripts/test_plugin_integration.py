"""
插件系统与规范化层集成测试

测试目标：
1. 验证插件系统能够正确加载和调用
2. 验证规范化层能够调用插件获取基础信息
3. 验证AI增强能够在插件基础上叠加
4. 使用真实文件进行端到端测试

测试文件来源：/Users/alwan/Downloads/
"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

import logging
from typing import Dict, Any, List
import json

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def find_test_files() -> Dict[str, List[str]]:
    """在下载文件夹中查找测试文件"""
    downloads_dir = Path("/Users/alwan/Downloads")

    test_files = {
        "audio": [],
        "video": [],
        "image": [],
        "table": [],
        "document": []
    }

    # 音频格式
    audio_extensions = ['.mp3', '.wav', '.m4a', '.flac', '.ogg']
    # 视频格式
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv']
    # 图片格式
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
    # 表格格式
    table_extensions = ['.xlsx', '.xls', '.csv']
    # 文档格式
    document_extensions = ['.pdf', '.docx', '.doc', '.txt', '.md']

    logger.info(f"🔍 扫描下载文件夹: {downloads_dir}")

    # 只扫描一级目录，不递归
    for file_path in downloads_dir.iterdir():
        if not file_path.is_file():
            continue

        ext = file_path.suffix.lower()

        if ext in audio_extensions:
            test_files["audio"].append(str(file_path))
        elif ext in video_extensions:
            test_files["video"].append(str(file_path))
        elif ext in image_extensions:
            test_files["image"].append(str(file_path))
        elif ext in table_extensions:
            test_files["table"].append(str(file_path))
        elif ext in document_extensions:
            test_files["document"].append(str(file_path))

    # 打印找到的文件
    for file_type, files in test_files.items():
        logger.info(f"  📁 {file_type}: {len(files)} 个文件")
        for f in files[:3]:  # 只显示前3个
            logger.info(f"     - {Path(f).name}")

    return test_files


def test_plugin_manager():
    """测试插件管理器"""
    logger.info("\n" + "="*60)
    logger.info("测试 1: 插件管理器加载")
    logger.info("="*60)

    try:
        from app.core.plugin_manager import PluginManager

        manager = PluginManager()
        logger.info(f"✅ 插件管理器初始化成功")
        logger.info(f"   已加载插件数量: {len(manager.plugins)}")

        for name, plugin in manager.plugins.items():
            logger.info(f"   - {name}: {plugin.__class__.__name__}")

        return True

    except Exception as e:
        logger.error(f"❌ 插件管理器初始化失败: {e}", exc_info=True)
        return False


def test_plugin_integration_service():
    """测试插件集成服务"""
    logger.info("\n" + "="*60)
    logger.info("测试 2: 插件集成服务")
    logger.info("="*60)

    try:
        from app.services.document_normalization.plugin_integration import get_plugin_integration_service

        service = get_plugin_integration_service()
        logger.info(f"✅ 插件集成服务初始化成功")

        if service.plugin_manager:
            logger.info(f"   插件管理器已加载: {len(service.plugin_manager.plugins)} 个插件")
        else:
            logger.warning(f"   ⚠️ 插件管理器未加载")

        return True

    except Exception as e:
        logger.error(f"❌ 插件集成服务初始化失败: {e}", exc_info=True)
        return False


def test_audio_normalization(test_file: str):
    """测试音频规范化（集成插件）"""
    logger.info("\n" + "="*60)
    logger.info(f"测试 3: 音频规范化 - {Path(test_file).name}")
    logger.info("="*60)

    try:
        from app.services.document_normalization.normalization_rules import AudioToTextRule, FileType

        # 读取文件
        with open(test_file, 'rb') as f:
            file_content = f.read()

        logger.info(f"📄 文件大小: {len(file_content) / 1024 / 1024:.2f} MB")

        # 创建规则
        rule = AudioToTextRule()

        # 执行规范化
        metadata = {
            "file_type": Path(test_file).suffix[1:],
            "file_path": test_file
        }

        logger.info(f"🔄 开始规范化处理...")
        result = rule.convert(file_content, metadata)

        # 打印结果
        logger.info(f"✅ 规范化完成:")
        logger.info(f"   字数: {result.word_count}")
        logger.info(f"   处理耗时: {result.processing_time_ms}ms")
        logger.info(f"   完整性评分: {result.completeness['score']:.1%}")
        logger.info(f"   置信度: {result.confidence:.1%}")
        logger.info(f"   结构化内容数: {len(result.normalized_contents)}")

        if result.text_content:
            logger.info(f"   文本预览: {result.text_content[:200]}...")

        return True

    except Exception as e:
        logger.error(f"❌ 音频规范化失败: {e}", exc_info=True)
        return False


def test_image_normalization(test_file: str):
    """测试图片规范化（集成插件）"""
    logger.info("\n" + "="*60)
    logger.info(f"测试 4: 图片规范化 - {Path(test_file).name}")
    logger.info("="*60)

    try:
        from app.services.document_normalization.normalization_rules import ImageToTextRule

        # 读取文件
        with open(test_file, 'rb') as f:
            file_content = f.read()

        logger.info(f"📄 文件大小: {len(file_content) / 1024:.2f} KB")

        # 创建规则
        rule = ImageToTextRule()

        # 执行规范化
        metadata = {
            "file_type": Path(test_file).suffix[1:],
            "file_path": test_file
        }

        logger.info(f"🔄 开始规范化处理...")
        result = rule.convert(file_content, metadata)

        # 打印结果
        logger.info(f"✅ 规范化完成:")
        logger.info(f"   字数: {result.word_count}")
        logger.info(f"   处理耗时: {result.processing_time_ms}ms")
        logger.info(f"   完整性评分: {result.completeness['score']:.1%}")
        logger.info(f"   置信度: {result.confidence:.1%}")
        logger.info(f"   结构化内容数: {len(result.normalized_contents)}")
        logger.info(f"   检测到文字: {result.structure_info.get('has_text', False)}")

        if result.text_content:
            logger.info(f"   文本预览: {result.text_content[:300]}...")

        return True

    except Exception as e:
        logger.error(f"❌ 图片规范化失败: {e}", exc_info=True)
        return False


def test_table_normalization(test_file: str):
    """测试表格规范化（集成插件）"""
    logger.info("\n" + "="*60)
    logger.info(f"测试 5: 表格规范化 - {Path(test_file).name}")
    logger.info("="*60)

    try:
        from app.services.document_normalization.normalization_rules import TableToTextRule

        # 读取文件
        with open(test_file, 'rb') as f:
            file_content = f.read()

        logger.info(f"📄 文件大小: {len(file_content) / 1024:.2f} KB")

        # 创建规则
        rule = TableToTextRule()

        # 执行规范化
        metadata = {
            "file_type": Path(test_file).suffix[1:],
            "file_path": test_file
        }

        logger.info(f"🔄 开始规范化处理...")
        result = rule.convert(file_content, metadata)

        # 打印结果
        logger.info(f"✅ 规范化完成:")
        logger.info(f"   字数: {result.word_count}")
        logger.info(f"   处理耗时: {result.processing_time_ms}ms")
        logger.info(f"   完整性评分: {result.completeness['score']:.1%}")
        logger.info(f"   工作表数: {result.structure_info.get('sheets', []).__len__()}")
        logger.info(f"   总行数: {result.structure_info.get('total_rows', 0)}")
        logger.info(f"   总列数: {result.structure_info.get('total_cols', 0)}")
        logger.info(f"   包含公式: {result.structure_info.get('has_formulas', False)}")

        if result.text_content:
            logger.info(f"   文本预览: {result.text_content[:300]}...")

        return True

    except Exception as e:
        logger.error(f"❌ 表格规范化失败: {e}", exc_info=True)
        return False


def test_document_normalization(test_file: str):
    """测试文档规范化（集成插件）"""
    logger.info("\n" + "="*60)
    logger.info(f"测试 6: 文档规范化 - {Path(test_file).name}")
    logger.info("="*60)

    try:
        from app.services.document_normalization.additional_rules import DocumentToTextRule

        # 读取文件
        with open(test_file, 'rb') as f:
            file_content = f.read()

        logger.info(f"📄 文件大小: {len(file_content) / 1024:.2f} KB")

        # 创建规则
        rule = DocumentToTextRule()

        # 执行规范化
        metadata = {
            "file_type": Path(test_file).suffix[1:],
            "file_path": test_file
        }

        logger.info(f"🔄 开始规范化处理...")
        result = rule.convert(file_content, metadata)

        # 打印结果
        logger.info(f"✅ 规范化完成:")
        logger.info(f"   字数: {result.word_count}")
        logger.info(f"   处理耗时: {result.processing_time_ms}ms")
        logger.info(f"   完整性评分: {result.completeness['score']:.1%}")
        logger.info(f"   页数: {result.metadata.get('page_count', 0)}")
        logger.info(f"   章节数: {result.metadata.get('section_count', 0)}")

        if result.text_content:
            logger.info(f"   文本预览: {result.text_content[:300]}...")

        return True

    except Exception as e:
        logger.error(f"❌ 文档规范化失败: {e}", exc_info=True)
        return False


def test_video_normalization(test_file: str):
    """测试视频规范化（集成插件）"""
    logger.info("\n" + "="*60)
    logger.info(f"测试 7: 视频规范化 - {Path(test_file).name}")
    logger.info("="*60)

    try:
        from app.services.document_normalization.additional_rules import VideoToTextRule

        # 读取文件
        with open(test_file, 'rb') as f:
            file_content = f.read()

        logger.info(f"📄 文件大小: {len(file_content) / 1024 / 1024:.2f} MB")

        # 创建规则
        rule = VideoToTextRule()

        # 执行规范化
        metadata = {
            "file_type": Path(test_file).suffix[1:],
            "file_path": test_file
        }

        logger.info(f"🔄 开始规范化处理（这可能需要较长时间）...")
        result = rule.convert(file_content, metadata)

        # 打印结果
        logger.info(f"✅ 规范化完成:")
        logger.info(f"   字数: {result.word_count}")
        logger.info(f"   处理耗时: {result.processing_time_ms}ms")
        logger.info(f"   完整性评分: {result.completeness['score']:.1%}")
        logger.info(f"   时长: {result.metadata.get('total_duration', 0):.1f}秒")
        logger.info(f"   场景数: {result.structure_info.get('scene_count', 0)}")
        logger.info(f"   关键帧数: {result.structure_info.get('frame_count', 0)}")
        logger.info(f"   音频覆盖率: {result.metadata.get('audio_coverage', 0):.1%}")

        if result.text_content:
            logger.info(f"   文本预览: {result.text_content[:300]}...")

        return True

    except Exception as e:
        logger.error(f"❌ 视频规范化失败: {e}", exc_info=True)
        return False


def main():
    """主测试函数"""
    logger.info("\n" + "="*60)
    logger.info("🚀 插件系统与规范化层集成测试")
    logger.info("="*60)

    # 1. 查找测试文件
    test_files = find_test_files()

    # 2. 测试插件管理器
    if not test_plugin_manager():
        logger.error("❌ 插件管理器测试失败，终止测试")
        return

    # 3. 测试插件集成服务
    if not test_plugin_integration_service():
        logger.error("❌ 插件集成服务测试失败，终止测试")
        return

    # 4. 测试音频规范化
    if test_files["audio"]:
        test_audio_normalization(test_files["audio"][0])
    else:
        logger.warning("⚠️ 未找到音频文件，跳过音频测试")

    # 5. 测试图片规范化
    if test_files["image"]:
        test_image_normalization(test_files["image"][0])
    else:
        logger.warning("⚠️ 未找到图片文件，跳过图片测试")

    # 6. 测试表格规范化
    if test_files["table"]:
        test_table_normalization(test_files["table"][0])
    else:
        logger.warning("⚠️ 未找到表格文件，跳过表格测试")

    # 7. 测试文档规范化
    if test_files["document"]:
        test_document_normalization(test_files["document"][0])
    else:
        logger.warning("⚠️ 未找到文档文件，跳过文档测试")

    # 8. 测试视频规范化（可选，因为耗时较长）
    if test_files["video"]:
        logger.info("\n⏳ 视频测试耗时较长，跳过（如需测试，请取消注释）")
        # test_video_normalization(test_files["video"][0])
    else:
        logger.warning("⚠️ 未找到视频文件，跳过视频测试")

    logger.info("\n" + "="*60)
    logger.info("✅ 集成测试完成")
    logger.info("="*60)


if __name__ == "__main__":
    main()
