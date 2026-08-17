#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FieldMind 组件导入测试脚本
测试所有已安装的Python包是否可以正常导入
"""

import sys
from typing import Tuple, List

def test_import(module_name: str, display_name: str = None) -> Tuple[bool, str]:
    """测试单个模块导入"""
    if display_name is None:
        display_name = module_name

    try:
        __import__(module_name)
        return True, f"✓ {display_name}"
    except ImportError as e:
        return False, f"✗ {display_name}: {str(e)}"
    except Exception as e:
        return False, f"✗ {display_name}: 未知错误 - {str(e)}"

def main():
    """主测试函数"""

    print("=" * 60)
    print("FieldMind 组件导入测试")
    print("=" * 60)
    print()

    # 定义需要测试的模块
    test_cases: List[Tuple[str, str]] = [
        # 必装核心
        ("graphrag", "Microsoft GraphRAG"),
        ("hanlp", "HanLP"),
        ("pyhanlp", "PyHanLP"),
        ("duckdb", "DuckDB"),
        ("mem0", "Mem0"),
        ("PIL", "Pillow"),

        # 常用依赖
        ("anthropic", "Anthropic SDK"),
        ("openai", "OpenAI SDK"),
        ("numpy", "NumPy"),
        ("pandas", "Pandas"),
        ("torch", "PyTorch"),
        ("transformers", "Transformers"),
        ("langchain", "LangChain"),
        ("chromadb", "ChromaDB"),
        ("faiss", "FAISS"),
        ("sentence_transformers", "Sentence-Transformers"),

        # Web和爬虫
        ("requests", "Requests"),
        ("bs4", "BeautifulSoup4"),
        ("crawl4ai", "Crawl4AI"),

        # 数据处理
        ("sqlalchemy", "SQLAlchemy"),
        ("networkx", "NetworkX"),
        ("matplotlib", "Matplotlib"),
        ("seaborn", "Seaborn"),
        ("plotly", "Plotly"),
    ]

    results = []
    success_count = 0
    fail_count = 0

    print("🔍 测试核心组件导入...")
    print()

    for module_name, display_name in test_cases:
        success, message = test_import(module_name, display_name)
        results.append((success, message))

        if success:
            print(f"\033[0;32m{message}\033[0m")
            success_count += 1
        else:
            print(f"\033[0;31m{message}\033[0m")
            fail_count += 1

    print()
    print("=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"✓ 成功: {success_count}/{len(test_cases)}")
    print(f"✗ 失败: {fail_count}/{len(test_cases)}")
    print()

    if fail_count > 0:
        print("⚠️  部分组件导入失败，可能需要：")
        print("   1. 检查虚拟环境是否激活")
        print("   2. 重新运行安装脚本")
        print("   3. 手动安装失败的包: pip install <package-name>")
        print()
        return 1
    else:
        print("🎉 所有核心组件导入成功！")
        print()
        return 0

if __name__ == "__main__":
    sys.exit(main())
