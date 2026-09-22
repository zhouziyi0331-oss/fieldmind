"""
统一爬虫服务

整合多个爬虫工具：
- firecrawl: 基础网页爬取
- crawl4ai: AI智能爬取
- 浏览器自动化

提供统一的爬虫接口
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
import logging
import asyncio

logger = logging.getLogger(__name__)


class CrawlerType(str, Enum):
    """爬虫类型"""
    BASIC = "basic"  # 基础爬虫
    AI = "ai"  # AI 爬虫
    BROWSER = "browser"  # 浏览器自动化


class CrawlStatus(str, Enum):
    """爬取状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# ==================== Firecrawl 爬虫 ====================

class FirecrawlService:
    """
    Firecrawl 基础爬虫服务

    提供：
    - 单页爬取
    - 网站爬取
    - 结构化数据提取
    """

    def __init__(self):
        self._firecrawl = None
        self._initialized = False

        try:
            from firecrawl import FirecrawlApp
            self._FirecrawlApp = FirecrawlApp
            self._initialized = True
            logger.info("✅ Firecrawl 服务初始化成功")
        except ImportError:
            logger.warning("⚠️ Firecrawl 未安装，请运行: pip install firecrawl-py")
        except Exception as e:
            logger.error(f"❌ Firecrawl 初始化失败: {e}")

    def is_available(self) -> bool:
        """检查服务是否可用"""
        return self._initialized

    def crawl_url(
        self,
        url: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        爬取单个URL

        Args:
            url: 目标URL
            options: 爬取选项

        Returns:
            爬取结果
        """
        if not self.is_available():
            raise NotImplementedError("Firecrawl 不可用")

        try:
            # 初始化 Firecrawl（需要 API key）
            api_key = options.get("api_key") if options else None
            if not api_key:
                logger.warning("未提供 Firecrawl API key")
                return self._crawl_basic(url)

            app = self._FirecrawlApp(api_key=api_key)

            # 爬取页面
            result = app.scrape_url(url, params=options or {})

            return {
                "url": url,
                "title": result.get("metadata", {}).get("title", ""),
                "content": result.get("markdown", ""),
                "html": result.get("html", ""),
                "links": result.get("links", []),
                "metadata": result.get("metadata", {}),
                "status": "success"
            }

        except Exception as e:
            logger.error(f"Firecrawl 爬取失败: {e}")
            return self._crawl_basic(url)

    def crawl_website(
        self,
        url: str,
        max_depth: int = 2,
        max_pages: int = 100,
        options: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        爬取整个网站

        Args:
            url: 起始URL
            max_depth: 最大深度
            max_pages: 最大页面数
            options: 爬取选项

        Returns:
            爬取结果列表
        """
        if not self.is_available():
            raise NotImplementedError("Firecrawl 不可用")

        try:
            api_key = options.get("api_key") if options else None
            if not api_key:
                logger.warning("未提供 Firecrawl API key，使用基础爬取")
                return [self._crawl_basic(url)]

            app = self._FirecrawlApp(api_key=api_key)

            # 爬取网站
            crawl_params = {
                "limit": max_pages,
                "scrapeOptions": options or {}
            }

            result = app.crawl_url(url, params=crawl_params)

            pages = []
            for page in result.get("data", [])[:max_pages]:
                pages.append({
                    "url": page.get("url", url),
                    "title": page.get("metadata", {}).get("title", ""),
                    "content": page.get("markdown", ""),
                    "metadata": page.get("metadata", {}),
                    "status": "success"
                })

            return pages

        except Exception as e:
            logger.error(f"Firecrawl 网站爬取失败: {e}")
            return [self._crawl_basic(url)]

    def _crawl_basic(self, url: str) -> Dict[str, Any]:
        """基础爬取（降级方案）"""
        try:
            import requests
            from bs4 import BeautifulSoup

            response = requests.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # 提取标题
            title = soup.title.string if soup.title else ""

            # 提取文本内容
            for script in soup(["script", "style"]):
                script.decompose()
            content = soup.get_text()
            lines = (line.strip() for line in content.splitlines())
            content = '\n'.join(line for line in lines if line)

            # 提取链接
            links = []
            for link in soup.find_all('a', href=True):
                links.append(link['href'])

            return {
                "url": url,
                "title": title,
                "content": content[:5000],  # 限制长度
                "html": response.text[:10000],
                "links": links[:50],
                "metadata": {"method": "basic"},
                "status": "success"
            }

        except Exception as e:
            logger.error(f"基础爬取失败: {e}")
            return {
                "url": url,
                "title": "",
                "content": "",
                "html": "",
                "links": [],
                "metadata": {"error": str(e)},
                "status": "failed"
            }


# ==================== Crawl4AI 爬虫 ====================

class Crawl4AIService:
    """
    Crawl4AI 智能爬虫服务

    提供：
    - AI 理解内容
    - 智能提取
    - 反爬虫处理
    """

    def __init__(self):
        self._crawl4ai = None
        self._initialized = False

        try:
            from crawl4ai import WebCrawler
            self._WebCrawler = WebCrawler
            self._initialized = True
            logger.info("✅ Crawl4AI 服务初始化成功")
        except ImportError:
            logger.warning("⚠️ Crawl4AI 未安装，请运行: pip install crawl4ai")
        except Exception as e:
            logger.error(f"❌ Crawl4AI 初始化失败: {e}")

    def is_available(self) -> bool:
        """检查服务是否可用"""
        return self._initialized

    async def crawl_with_ai(
        self,
        url: str,
        instructions: Optional[str] = None,
        extract_schema: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        使用 AI 智能爬取

        Args:
            url: 目标URL
            instructions: AI 指令
            extract_schema: 提取模式

        Returns:
            爬取结果
        """
        if not self.is_available():
            raise NotImplementedError("Crawl4AI 不可用")

        try:
            crawler = self._WebCrawler()

            # 爬取页面
            result = await crawler.arun(
                url=url,
                word_count_threshold=10,
                extraction_strategy=instructions,
                chunking_strategy=extract_schema
            )

            return {
                "url": url,
                "title": result.metadata.get("title", ""),
                "content": result.extracted_content or result.markdown,
                "structured_data": result.extracted_data if extract_schema else None,
                "links": result.links,
                "metadata": result.metadata,
                "status": "success"
            }

        except Exception as e:
            logger.error(f"Crawl4AI 爬取失败: {e}")
            return {
                "url": url,
                "content": "",
                "status": "failed",
                "error": str(e)
            }


# ==================== 统一爬虫服务 ====================

class UnifiedCrawlerService:
    """
    统一爬虫服务

    整合多个爬虫工具，提供统一接口
    """

    def __init__(self):
        self.firecrawl = FirecrawlService()
        self.crawl4ai = Crawl4AIService()

        logger.info("🕷️ 统一爬虫服务已初始化")

    def is_available(self) -> bool:
        """检查是否有可用的爬虫"""
        return self.firecrawl.is_available() or self.crawl4ai.is_available()

    def get_available_crawlers(self) -> List[str]:
        """获取可用的爬虫列表"""
        crawlers = []
        if self.firecrawl.is_available():
            crawlers.append("firecrawl")
        if self.crawl4ai.is_available():
            crawlers.append("crawl4ai")
        return crawlers

    def crawl_url(
        self,
        url: str,
        crawler_type: CrawlerType = CrawlerType.BASIC,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        爬取单个URL

        Args:
            url: 目标URL
            crawler_type: 爬虫类型
            options: 爬取选项

        Returns:
            爬取结果
        """
        try:
            if crawler_type == CrawlerType.BASIC and self.firecrawl.is_available():
                return self.firecrawl.crawl_url(url, options)

            elif crawler_type == CrawlerType.AI and self.crawl4ai.is_available():
                # Crawl4AI 需要异步运行
                import asyncio
                return asyncio.run(self.crawl4ai.crawl_with_ai(url))

            else:
                # 降级到基础爬取
                return self.firecrawl._crawl_basic(url)

        except Exception as e:
            logger.error(f"爬取失败: {e}")
            return {
                "url": url,
                "status": "failed",
                "error": str(e)
            }

    def crawl_website(
        self,
        url: str,
        max_depth: int = 2,
        max_pages: int = 100,
        crawler_type: CrawlerType = CrawlerType.BASIC,
        options: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        爬取整个网站

        Args:
            url: 起始URL
            max_depth: 最大深度
            max_pages: 最大页面数
            crawler_type: 爬虫类型
            options: 爬取选项

        Returns:
            爬取结果列表
        """
        try:
            if crawler_type == CrawlerType.BASIC and self.firecrawl.is_available():
                return self.firecrawl.crawl_website(url, max_depth, max_pages, options)

            else:
                # 单页爬取
                result = self.crawl_url(url, crawler_type, options)
                return [result] if result else []

        except Exception as e:
            logger.error(f"网站爬取失败: {e}")
            return []

    def batch_crawl(
        self,
        urls: List[str],
        crawler_type: CrawlerType = CrawlerType.BASIC,
        options: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        批量爬取URL

        Args:
            urls: URL列表
            crawler_type: 爬虫类型
            options: 爬取选项

        Returns:
            爬取结果列表
        """
        results = []
        for url in urls:
            try:
                result = self.crawl_url(url, crawler_type, options)
                results.append(result)
            except Exception as e:
                logger.error(f"批量爬取 {url} 失败: {e}")
                results.append({
                    "url": url,
                    "status": "failed",
                    "error": str(e)
                })

        return results


# ==================== 全局单例 ====================

_crawler_service: Optional[UnifiedCrawlerService] = None


def get_crawler_service() -> UnifiedCrawlerService:
    """获取统一爬虫服务单例"""
    global _crawler_service

    if _crawler_service is None:
        _crawler_service = UnifiedCrawlerService()

    return _crawler_service
