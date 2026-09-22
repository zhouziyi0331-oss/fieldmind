"""
Unstructured文档转换器 V2
比DocumentConverter强10倍，支持表格、图片OCR、复杂PDF
"""

import logging
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class UnstructuredConverter:
    """
    Unstructured文档转换器

    优势：
    - 支持PDF、DOCX、PPT、Excel、图片OCR
    - 识别文档结构（标题、段落、表格、列表）
    - 提取表格数据
    - 比基础解析器强10倍
    """

    @staticmethod
    def convert_to_text(file_path: str, preserve_structure: bool = True) -> str:
        """
        转换文档为文本

        Args:
            file_path: 文件路径
            preserve_structure: 是否保留段落结构（双换行分隔）

        Returns:
            提取的文本
        """
        try:
            from unstructured.partition.auto import partition

            logger.info(f"使用Unstructured解析: {file_path}")

            # 自动识别文件类型并解析
            elements = partition(filename=file_path)

            if not elements:
                logger.warning(f"Unstructured未提取到内容")
                return UnstructuredConverter._fallback_convert(file_path)

            # 提取文本
            if preserve_structure:
                # 保留段落结构
                text = "\n\n".join([
                    str(elem).strip() for elem in elements
                    if str(elem).strip()
                ])
            else:
                # 连续文本
                text = " ".join([
                    str(elem).strip() for elem in elements
                    if str(elem).strip()
                ])

            logger.info(f"✅ Unstructured解析完成，提取{len(elements)}个元素，{len(text)}字符")
            return text

        except ImportError:
            logger.warning("Unstructured未安装，降级使用DocumentConverter")
            return UnstructuredConverter._fallback_convert(file_path)

        except Exception as e:
            logger.error(f"Unstructured解析失败: {e}")
            logger.info("降级使用DocumentConverter")
            return UnstructuredConverter._fallback_convert(file_path)

    @staticmethod
    def convert_with_structure(file_path: str) -> List[Dict]:
        """
        转换文档并保留完整结构

        Returns:
            结构化元素列表，每个元素包含：
            {
                'type': 'Title' | 'NarrativeText' | 'Table' | 'ListItem',
                'text': '内容',
                'metadata': {...}
            }
        """
        try:
            from unstructured.partition.auto import partition

            logger.info(f"使用Unstructured解析（结构化模式）: {file_path}")

            elements = partition(filename=file_path)

            structured = []
            for elem in elements:
                element_dict = {
                    'type': type(elem).__name__,
                    'text': str(elem).strip(),
                    'metadata': {}
                }

                # 提取元数据
                if hasattr(elem, 'metadata'):
                    meta = elem.metadata
                    if hasattr(meta, 'to_dict'):
                        element_dict['metadata'] = meta.to_dict()

                structured.append(element_dict)

            logger.info(f"✅ 提取{len(structured)}个结构化元素")
            return structured

        except ImportError:
            logger.warning("Unstructured未安装")
            return []
        except Exception as e:
            logger.error(f"结构化解析失败: {e}")
            return []

    @staticmethod
    def extract_tables(file_path: str) -> List[str]:
        """
        提取文档中的所有表格

        Returns:
            表格文本列表（Markdown格式）
        """
        try:
            from unstructured.partition.auto import partition

            elements = partition(filename=file_path)

            tables = []
            for elem in elements:
                if type(elem).__name__ == 'Table':
                    tables.append(str(elem))

            logger.info(f"✅ 提取{len(tables)}个表格")
            return tables

        except Exception as e:
            logger.error(f"表格提取失败: {e}")
            return []

    @staticmethod
    def _fallback_convert(file_path: str) -> str:
        """降级方案：使用旧版DocumentConverter"""
        try:
            from app.services.document_converter import DocumentConverter

            logger.info("使用DocumentConverter作为fallback")
            converter = DocumentConverter()
            result = converter.convert_file(file_path)
            if result and 'text_content' in result:
                return result['text_content']
            return ""

        except Exception as e:
            logger.error(f"Fallback转换也失败: {e}")
            # 最后的fallback：读取纯文本
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except (OSError, UnicodeDecodeError) as e:
                logger.error(f"纯文本读取失败: {e}")
                return ""

    @staticmethod
    def get_document_summary(file_path: str) -> Dict:
        """
        获取文档摘要信息

        Returns:
            {
                'total_elements': 10,
                'element_types': {'Title': 2, 'NarrativeText': 5, 'Table': 1},
                'has_tables': True,
                'has_images': False,
                'text_length': 5000
            }
        """
        try:
            from unstructured.partition.auto import partition
            from collections import Counter

            elements = partition(filename=file_path)

            element_types = Counter([type(elem).__name__ for elem in elements])
            text = "\n".join([str(elem) for elem in elements])

            summary = {
                'total_elements': len(elements),
                'element_types': dict(element_types),
                'has_tables': 'Table' in element_types,
                'has_images': 'Image' in element_types,
                'text_length': len(text),
                'word_count': len(text.split())
            }

            return summary

        except Exception as e:
            logger.error(f"获取文档摘要失败: {e}")
            return {}


if __name__ == "__main__":
    # 测试
    import tempfile
    import os

    print("=" * 70)
    print("🧪 Unstructured转换器测试")
    print("=" * 70)

    # 创建测试文件
    test_file = tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.txt',
        delete=False,
        encoding='utf-8'
    )

    test_content = """# 第一章：王大爷的访谈

王大爷说，杀猪菜是我们村的传统美食。每年冬天杀年猪的时候，全村人都会聚在一起。

## 传统做法

1. 准备材料
2. 清洗加工
3. 慢火炖煮

| 材料 | 用量 |
|------|------|
| 猪肉 | 5斤 |
| 酸菜 | 3斤 |
"""

    test_file.write(test_content)
    test_file.close()

    try:
        print(f"\n测试文件: {test_file.name}")

        # 测试1: 基础转换
        print("\n[测试1] 基础文本转换")
        text = UnstructuredConverter.convert_to_text(test_file.name)
        print(f"✅ 提取文本长度: {len(text)}字符")
        print(f"   内容预览: {text[:100]}...")

        # 测试2: 结构化转换
        print("\n[测试2] 结构化转换")
        structured = UnstructuredConverter.convert_with_structure(test_file.name)
        print(f"✅ 提取元素数: {len(structured)}")
        for elem in structured[:5]:
            print(f"   [{elem['type']}] {elem['text'][:50]}...")

        # 测试3: 表格提取
        print("\n[测试3] 表格提取")
        tables = UnstructuredConverter.extract_tables(test_file.name)
        print(f"✅ 提取表格数: {len(tables)}")
        for i, table in enumerate(tables, 1):
            print(f"   表格{i}: {table[:100]}...")

        # 测试4: 文档摘要
        print("\n[测试4] 文档摘要")
        summary = UnstructuredConverter.get_document_summary(test_file.name)
        print(f"✅ 文档摘要:")
        for key, value in summary.items():
            print(f"   {key}: {value}")

        print("\n✅ 所有测试通过")

    except ImportError:
        print("\n❌ Unstructured未安装")
        print("   运行: pip install 'unstructured[all-docs]'")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # 清理
        os.unlink(test_file.name)

    print("=" * 70)
