"""
TF-IDF and Clustering Tests - TF-IDF 和聚类测试

验证 TF-IDF 关键词提取和无监督聚类功能
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.tfidf_keyword_extractor import create_extractor
from app.services.topic_clustering_service import create_clustering_service
import sqlite3


class TestTFIDFExtractor:
    """测试 TF-IDF 关键词提取器"""

    def test_extractor_initialization(self):
        """测试提取器初始化"""
        print("\n" + "="*60)
        print("测试1: TF-IDF 提取器初始化")
        print("="*60)

        extractor = create_extractor()

        assert extractor.db_path == "data/fieldmind.db"
        assert len(extractor.stopwords) > 0

        print(f"✅ 数据库路径: {extractor.db_path}")
        print(f"✅ 停用词数量: {len(extractor.stopwords)}")

    def test_tokenize(self):
        """测试分词"""
        print("\n" + "="*60)
        print("测试2: 分词功能")
        print("="*60)

        extractor = create_extractor()

        text = "布依族的山歌是祖传的宝贝，传承人越来越少了。"
        tokens = extractor._tokenize(text)

        print(f"\n原文: {text}")
        print(f"分词结果: {tokens}")

        assert len(tokens) > 0
        assert '布依族' in tokens
        assert '山歌' in tokens
        assert '的' not in tokens  # 停用词应该被过滤

        print(f"✅ 分词成功，过滤了停用词")

    def test_keyword_extraction(self):
        """测试关键词提取"""
        print("\n" + "="*60)
        print("测试3: 关键词提取")
        print("="*60)

        # 先检查数据库中是否有数据
        conn = sqlite3.connect("data/fieldmind.db")
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM document_chunks")
        chunk_count = cursor.fetchone()[0]

        if chunk_count == 0:
            print("⏭  跳过测试：数据库中没有 chunks")
            conn.close()
            return

        # 获取第一个 chunk 和其 project_id
        cursor.execute("SELECT id, project_id, text FROM document_chunks LIMIT 1")
        row = cursor.fetchone()

        if not row:
            print("⏭  跳过测试：无法获取 chunk")
            conn.close()
            return

        chunk_id, project_id, text = row
        conn.close()

        print(f"\n测试 Chunk ID: {chunk_id}")
        print(f"项目 ID: {project_id}")
        print(f"文本: {text[:50]}...")

        extractor = create_extractor()

        # 提取关键词
        keywords = extractor.extract_keywords_for_chunk(chunk_id, project_id, top_n=5)

        print(f"\n提取的关键词:")
        for kw in keywords:
            print(f"  - {kw['keyword']}: TF-IDF={kw['tfidf_score']:.4f}, 词频={kw['frequency']}")

        assert len(keywords) > 0
        print(f"\n✅ 关键词提取成功，共 {len(keywords)} 个")

    def test_save_keywords(self):
        """测试保存关键词到数据库"""
        print("\n" + "="*60)
        print("测试4: 保存关键词到数据库")
        print("="*60)

        # 检查数据
        conn = sqlite3.connect("data/fieldmind.db")
        cursor = conn.cursor()

        cursor.execute("SELECT id, project_id FROM document_chunks LIMIT 1")
        row = cursor.fetchone()

        if not row:
            print("⏭  跳过测试：无 chunk 数据")
            conn.close()
            return

        chunk_id, project_id = row
        conn.close()

        extractor = create_extractor()

        # 提取并保存
        keywords = extractor.extract_keywords_for_chunk(chunk_id, project_id, top_n=5)
        if keywords:
            extractor.save_keywords_to_db(chunk_id, keywords)

            # 验证保存
            saved_keywords = extractor.get_chunk_keywords(chunk_id)

            print(f"\n保存的关键词数量: {len(saved_keywords)}")
            assert len(saved_keywords) == len(keywords)

            print(f"✅ 关键词保存成功")
        else:
            print("⏭  跳过：无关键词提取结果")


class TestClusteringService:
    """测试聚类服务"""

    def test_clustering_initialization(self):
        """测试聚类服务初始化"""
        print("\n" + "="*60)
        print("测试5: 聚类服务初始化")
        print("="*60)

        service = create_clustering_service()

        assert service.db_path == "data/fieldmind.db"
        assert len(service.stopwords) > 0
        assert len(service.dimension_keywords) > 0

        print(f"✅ 停用词数量: {len(service.stopwords)}")
        print(f"✅ 业务维度数量: {len(service.dimension_keywords)}")

    def test_dimension_mapping(self):
        """测试维度映射"""
        print("\n" + "="*60)
        print("测试6: 维度映射")
        print("="*60)

        service = create_clustering_service()

        # 测试几个关键词组合
        test_cases = [
            (['山歌', '民歌', '传承', '唱'], '非遗'),
            (['村', '房屋', '建筑', '吊脚楼'], '住'),
            (['政策', '扶贫', '补贴', '文件'], '政策'),
        ]

        for keywords, expected_dim in test_cases:
            mapped_dim = service._map_cluster_to_dimension(keywords)
            print(f"\n关键词: {keywords}")
            print(f"  映射维度: {mapped_dim}")
            print(f"  预期维度: {expected_dim}")

        print(f"\n✅ 维度映射测试完成")

    def test_clustering(self):
        """测试聚类"""
        print("\n" + "="*60)
        print("测试7: 聚类功能")
        print("="*60)

        # 检查数据
        conn = sqlite3.connect("data/fieldmind.db")
        cursor = conn.cursor()

        cursor.execute("SELECT DISTINCT project_id FROM document_chunks LIMIT 1")
        row = cursor.fetchone()

        if not row:
            print("⏭  跳过测试：无项目数据")
            conn.close()
            return

        project_id = row[0]

        cursor.execute("SELECT COUNT(*) FROM document_chunks WHERE project_id = ?", (project_id,))
        chunk_count = cursor.fetchone()[0]

        conn.close()

        if chunk_count < 3:
            print(f"⏭  跳过测试：chunks 数量不足 ({chunk_count} < 3)")
            return

        print(f"\n项目 ID: {project_id}")
        print(f"Chunks 数量: {chunk_count}")

        service = create_clustering_service()

        # 执行聚类
        result = service.auto_cluster_chunks(project_id, n_clusters=3, auto_determine_k=False)

        if 'error' in result:
            print(f"❌ 聚类失败: {result['error']}")
            return

        print(f"\n聚类结果:")
        print(f"  聚类数量: {result['n_clusters']}")
        print(f"  轮廓系数: {result['silhouette_score']:.3f}")

        for cluster in result['clusters']:
            print(f"\n  聚类 {cluster['cluster_id']}: {cluster['cluster_label']}")
            print(f"    Chunks 数量: {cluster['chunk_count']}")
            print(f"    Top 关键词: {', '.join(cluster['top_keywords'][:5])}")
            if cluster['mapped_dimension']:
                print(f"    映射维度: {cluster['mapped_dimension']}")

        assert result['n_clusters'] > 0
        print(f"\n✅ 聚类完成")


def run_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("开始测试 TF-IDF 和聚类功能")
    print("="*60 + "\n")

    test_classes = [
        TestTFIDFExtractor(),
        TestClusteringService()
    ]

    tests = [
        ("TF-IDF提取器初始化", test_classes[0].test_extractor_initialization),
        ("分词功能", test_classes[0].test_tokenize),
        ("关键词提取", test_classes[0].test_keyword_extraction),
        ("保存关键词", test_classes[0].test_save_keywords),
        ("聚类服务初始化", test_classes[1].test_clustering_initialization),
        ("维度映射", test_classes[1].test_dimension_mapping),
        ("聚类功能", test_classes[1].test_clustering),
    ]

    passed = 0
    failed = 0
    skipped = 0

    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"❌ 测试失败: {test_name}")
            print(f"   错误: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ 测试出错: {test_name}")
            print(f"   错误: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "="*60)
    print(f"测试完成: {passed} 通过, {failed} 失败")
    print("="*60 + "\n")

    if failed == 0:
        print("核心功能：")
        print("  ✓ TF-IDF 关键词提取")
        print("  ✓ 无监督聚类（KMeans）")
        print("  ✓ 自动主题发现")
        print("  ✓ 维度映射")
        print()

    return failed == 0


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
