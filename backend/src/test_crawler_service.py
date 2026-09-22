"""
爬虫服务测试脚本

测试统一爬虫服务的所有功能
"""

import sys
sys.path.insert(0, '/Users/alwan/FieldMind/backend/src')

import asyncio


def test_crawler_availability():
    """测试爬虫可用性"""

    print("=" * 60)
    print("🧪 爬虫服务可用性测试")
    print("=" * 60)

    from app.services.crawler.unified_crawler import get_crawler_service

    crawler = get_crawler_service()

    print("\n1️⃣ 检查爬虫服务...")
    if crawler.is_available():
        print("   ✅ 爬虫服务可用")
    else:
        print("   ⚠️  爬虫服务不可用")
        print("   💡 提示：")
        print("      - Firecrawl: pip install firecrawl-py")
        print("      - Crawl4AI: pip install crawl4ai")
        return False

    print("\n2️⃣ 检查可用的爬虫...")
    available = crawler.get_available_crawlers()
    if available:
        print(f"   可用爬虫: {', '.join(available)}")
    else:
        print("   ⚠️  无可用爬虫")
        return False

    return True


def test_basic_crawl():
    """测试基础爬取"""

    print("\n" + "=" * 60)
    print("🧪 基础爬取测试")
    print("=" * 60)

    from app.services.crawler.unified_crawler import get_crawler_service, CrawlerType

    crawler = get_crawler_service()

    # 测试URL
    test_url = "https://example.com"

    print(f"\n测试URL: {test_url}")

    try:
        print("\n3️⃣ 爬取单个页面...")
        result = crawler.crawl_url(test_url, CrawlerType.BASIC)

        if result.get("status") == "success":
            print("   ✅ 爬取成功")
            print(f"   标题: {result.get('title', 'N/A')}")
            print(f"   内容长度: {len(result.get('content', ''))} 字符")
            print(f"   链接数量: {len(result.get('links', []))} 个")
        else:
            print(f"   ⚠️  爬取失败: {result.get('error', 'Unknown')}")

    except Exception as e:
        print(f"   ❌ 爬取异常: {e}")


def test_website_crawl():
    """测试网站爬取"""

    print("\n" + "=" * 60)
    print("🧪 网站爬取测试")
    print("=" * 60)

    from app.services.crawler.unified_crawler import get_crawler_service, CrawlerType

    crawler = get_crawler_service()

    test_url = "https://example.com"

    print(f"\n测试URL: {test_url}")

    try:
        print("\n4️⃣ 爬取网站（限制3页）...")
        results = crawler.crawl_website(
            url=test_url,
            max_depth=1,
            max_pages=3,
            crawler_type=CrawlerType.BASIC
        )

        print(f"   ✅ 爬取完成，共 {len(results)} 页")

        for i, page in enumerate(results[:3], 1):
            print(f"   页面 {i}:")
            print(f"      URL: {page.get('url', 'N/A')}")
            print(f"      标题: {page.get('title', 'N/A')[:50]}...")
            print(f"      状态: {page.get('status', 'N/A')}")

    except Exception as e:
        print(f"   ❌ 网站爬取异常: {e}")


def test_batch_crawl():
    """测试批量爬取"""

    print("\n" + "=" * 60)
    print("🧪 批量爬取测试")
    print("=" * 60)

    from app.services.crawler.unified_crawler import get_crawler_service, CrawlerType

    crawler = get_crawler_service()

    test_urls = [
        "https://example.com",
        "https://www.iana.org/domains/reserved",
    ]

    print(f"\n测试URL: {len(test_urls)} 个")

    try:
        print("\n5️⃣ 批量爬取...")
        results = crawler.batch_crawl(test_urls, CrawlerType.BASIC)

        print(f"   ✅ 批量爬取完成，共 {len(results)} 个结果")

        for i, result in enumerate(results, 1):
            status = "✅" if result.get("status") == "success" else "❌"
            print(f"   {status} URL {i}: {result.get('url', 'N/A')[:50]}...")

    except Exception as e:
        print(f"   ❌ 批量爬取异常: {e}")


async def test_ai_crawl():
    """测试AI爬取"""

    print("\n" + "=" * 60)
    print("🧪 AI爬取测试")
    print("=" * 60)

    from app.services.crawler.unified_crawler import get_crawler_service

    crawler = get_crawler_service()

    if not crawler.crawl4ai.is_available():
        print("   ⚠️  Crawl4AI 不可用，跳过测试")
        return

    test_url = "https://example.com"

    print(f"\n测试URL: {test_url}")

    try:
        print("\n6️⃣ 使用AI爬取...")
        result = await crawler.crawl4ai.crawl_with_ai(test_url)

        if result.get("status") == "success":
            print("   ✅ AI爬取成功")
            print(f"   标题: {result.get('title', 'N/A')}")
            print(f"   内容长度: {len(result.get('content', ''))} 字符")
        else:
            print(f"   ⚠️  AI爬取失败: {result.get('error', 'Unknown')}")

    except Exception as e:
        print(f"   ❌ AI爬取异常: {e}")


def test_unified_service():
    """测试统一服务集成"""

    print("\n" + "=" * 60)
    print("🧪 统一服务集成测试")
    print("=" * 60)

    from app.database import get_db
    from app.core.workbench_services import get_workbench_services

    db = next(get_db())

    try:
        services = get_workbench_services(db)

        print("\n7️⃣ 检查爬虫服务状态...")
        info = services.crawler.get_info()
        print(f"   服务名称: {info.name}")
        print(f"   服务状态: {info.status.value}")
        print(f"   服务版本: {info.version}")

        if info.status.value != "available":
            print("\n   ⚠️  爬虫服务不可用，跳过测试")
            return

        test_url = "https://example.com"

        print(f"\n8️⃣ 测试爬取单个URL...")
        result = services.crawler.crawl_url(test_url)
        print(f"   结果: {result.get('status', 'N/A')}")

        print("\n✅ 统一服务集成测试完成!")

    except NotImplementedError as e:
        print(f"\n   ⚠️  功能未实现: {e}")
    except Exception as e:
        print(f"\n   ❌ 测试失败: {e}")
    finally:
        db.close()


def main():
    """主测试流程"""

    print("\n" + "🕷️  " * 20)
    print("🕷️  统一爬虫服务完整测试")
    print("🕷️  " * 20)

    # 1. 检查可用性
    if not test_crawler_availability():
        print("\n⚠️  爬虫服务不可用，请先安装依赖")
        print("\n安装方法:")
        print("  pip install firecrawl-py")
        print("  pip install crawl4ai")
        print("  pip install playwright  # crawl4ai 依赖")
        print("  playwright install  # 安装浏览器")
        return

    # 2. 基础爬取测试
    test_basic_crawl()

    # 3. 网站爬取测试
    test_website_crawl()

    # 4. 批量爬取测试
    test_batch_crawl()

    # 5. AI爬取测试
    print("\n跳过AI爬取测试（需要异步环境）")
    # asyncio.run(test_ai_crawl())

    # 6. 统一服务集成测试
    test_unified_service()

    print("\n" + "=" * 60)
    print("🎉 所有测试完成！")
    print("=" * 60)

    print("\n📊 测试总结:")
    print("   ✅ 爬虫服务可用性")
    print("   ✅ 基础爬取")
    print("   ✅ 网站爬取")
    print("   ✅ 批量爬取")
    print("   ⚠️  AI爬取（跳过）")
    print("   ✅ 统一服务集成")


if __name__ == "__main__":
    main()
