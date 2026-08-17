#!/usr/bin/env python3
"""测试所有已安装的Python组件导入"""

import sys
from typing import Dict, List

def test_imports() -> Dict[str, bool]:
    """测试所有核心组件的导入"""
    results = {}

    # 音视频处理
    packages = {
        '音视频处理': [
            'whisper',
            'cv2',
            'pydub',
            'librosa',
            'soundfile',
        ],
        '向量数据库': [
            'chromadb',
            'faiss',
            'sentence_transformers',
        ],
        '数据库驱动': [
            'sqlalchemy',
            'psycopg2',
            'neo4j',
        ],
        '加密': [
            'cryptography',
        ],
        '中文分词': [
            'jieba',
        ],
        'AI框架': [
            'langchain',
            'langchain_openai',
            'langchain_anthropic',
            'spacy',
        ],
        '可视化': [
            'folium',
            'geopy',
            'plotly',
            'networkx',
            'pyvis',
        ],
        '搜索引擎': [
            'whoosh',
        ],
        'PDF处理': [
            'pdfplumber',
            'fitz',  # PyMuPDF
        ],
    }

    print("=" * 60)
    print("🧪 开始测试组件导入...")
    print("=" * 60)

    for category, modules in packages.items():
        print(f"\n📦 {category}:")
        for module in modules:
            try:
                __import__(module)
                results[module] = True
                print(f"  ✅ {module}")
            except ImportError as e:
                results[module] = False
                print(f"  ❌ {module}: {e}")
            except Exception as e:
                results[module] = False
                print(f"  ⚠️  {module}: {e}")

    # 统计
    success = sum(1 for v in results.values() if v)
    total = len(results)

    print("\n" + "=" * 60)
    print(f"📊 测试结果: {success}/{total} 成功 ({success/total*100:.1f}%)")
    print("=" * 60)

    return results

if __name__ == '__main__':
    results = test_imports()

    # 如果有失败的，返回非零退出码
    if not all(results.values()):
        sys.exit(1)
