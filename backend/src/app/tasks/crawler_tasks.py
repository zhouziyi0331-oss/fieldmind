"""
网络爬虫任务 - 整合现有爬虫工具
使用：crawl4ai, gecco, browser-use, firecrawl
不自己实现新爬虫，只做智能调度和整合
"""
from celery import chain
from app.celery_app import celery_app
from typing import Dict, Any, List
import os
from datetime import datetime
from enum import Enum


class CrawlerType(Enum):
    """爬虫类型选择"""
    CRAWL4AI = "crawl4ai"  # 轻量级，适合简单页面
    GECCO = "gecco"  # 配置化，适合结构化数据
    BROWSER_USE = "browser-use"  # AI驱动，适合复杂交互
    FIRECRAWL = "firecrawl"  # 企业级（需付费），适合大规模


@celery_app.task(name="app.tasks.crawler_tasks.intelligent_crawl", rate_limit="10/m")
def intelligent_crawl(url: str, crawler_type: str = "auto") -> Dict[str, Any]:
    """
    智能爬虫调度：根据目标网站类型选择最合适的爬虫

    - crawl4ai: 静态页面、新闻文章
    - gecco: 政府网站、结构化数据
    - browser-use: 需要登录、JavaScript 渲染、复杂交互
    - firecrawl: 大规模爬取（需付费 API）
    """
    try:
        # 自动选择爬虫
        if crawler_type == "auto":
            crawler_type = _select_crawler(url)

        # 根据类型调用相应爬虫
        if crawler_type == CrawlerType.CRAWL4AI.value:
            result = _crawl_with_crawl4ai(url)
        elif crawler_type == CrawlerType.GECCO.value:
            result = _crawl_with_gecco(url)
        elif crawler_type == CrawlerType.BROWSER_USE.value:
            result = _crawl_with_browser_use(url)
        elif crawler_type == CrawlerType.FIRECRAWL.value:
            result = _crawl_with_firecrawl(url)
        else:
            return {
                "success": False,
                "error": f"Unknown crawler type: {crawler_type}",
            }

        return {
            "success": True,
            "url": url,
            "crawler_used": crawler_type,
            "content": result["content"],
            "metadata": result.get("metadata", {}),
            "crawled_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Crawling failed: {str(e)}",
            "url": url,
        }


def _select_crawler(url: str) -> str:
    """
    根据 URL 智能选择爬虫
    """
    url_lower = url.lower()

    # 政府网站 → gecco（结构化）
    if any(domain in url_lower for domain in [".gov.", "www.gov", "政府", "www.mof", "www.miit"]):
        return CrawlerType.GECCO.value

    # 需要复杂交互 → browser-use
    if any(keyword in url_lower for keyword in ["login", "signin", "dashboard", "app."]):
        return CrawlerType.BROWSER_USE.value

    # 默认使用 crawl4ai（轻量快速）
    return CrawlerType.CRAWL4AI.value


def _crawl_with_crawl4ai(url: str) -> Dict[str, Any]:
    """
    使用 crawl4ai 爬取（轻量级，适合新闻文章）
    """
    from crawl4ai import WebCrawler

    crawler = WebCrawler()
    result = crawler.run(url)

    return {
        "content": result.markdown,
        "metadata": {
            "title": result.title,
            "links": result.links,
            "images": result.images,
        }
    }


def _crawl_with_gecco(url: str) -> Dict[str, Any]:
    """
    使用 gecco 爬取（配置化，适合结构化数据）
    TODO: 需要预定义爬虫规则
    """
    # gecco 需要预先定义爬虫类和规则
    # 这里返回基本实现框架
    import requests
    from bs4 import BeautifulSoup

    response = requests.get(url, timeout=30)
    soup = BeautifulSoup(response.content, "html.parser")

    # 提取主要内容
    content = soup.get_text(separator="\n", strip=True)

    return {
        "content": content,
        "metadata": {
            "title": soup.title.string if soup.title else "",
        }
    }


def _crawl_with_browser_use(url: str) -> Dict[str, Any]:
    """
    使用 browser-use 爬取（AI 驱动，适合复杂页面）
    browser-use 需要在独立环境运行
    """
    # browser-use 集成需要独立进程
    # 这里提供 API 调用方式
    import subprocess
    import json

    # 调用独立的 browser-use 脚本
    script_path = os.getenv("BROWSER_USE_SCRIPT", "./repos/browser-use/run_crawl.py")

    if os.path.exists(script_path):
        result = subprocess.run(
            ["python", script_path, url],
            capture_output=True,
            text=True,
            timeout=120
        )
        data = json.loads(result.stdout)
        return data
    else:
        # 降级到简单爬取
        return _crawl_with_crawl4ai(url)


def _crawl_with_firecrawl(url: str) -> Dict[str, Any]:
    """
    使用 firecrawl API（付费服务，$20-100/月）
    仅在配置了 API key 时使用
    """
    api_key = os.getenv("FIRECRAWL_API_KEY")

    if not api_key:
        raise ValueError("FIRECRAWL_API_KEY not configured. Use free crawlers instead.")

    from firecrawl import FirecrawlApp

    app = FirecrawlApp(api_key=api_key)
    result = app.scrape_url(url)

    return {
        "content": result.get("markdown", ""),
        "metadata": result.get("metadata", {}),
    }


@celery_app.task(name="app.tasks.crawler_tasks.crawl_news")
def crawl_news(url: str) -> Dict[str, Any]:
    """
    新闻文章专用爬虫
    使用 newspaper3k + gne（中文新闻）
    """
    try:
        from newspaper import Article
        from gne import GeneralNewsExtractor

        # 尝试 newspaper3k
        article = Article(url, language="zh")
        article.download()
        article.parse()

        if article.text:
            return {
                "success": True,
                "url": url,
                "title": article.title,
                "content": article.text,
                "authors": article.authors,
                "publish_date": article.publish_date.isoformat() if article.publish_date else None,
                "images": article.images,
                "method": "newspaper3k",
            }

        # 如果 newspaper3k 失败，尝试 gne
        extractor = GeneralNewsExtractor()
        html = article.html
        result = extractor.extract(html)

        return {
            "success": True,
            "url": url,
            "title": result.get("title", ""),
            "content": result.get("content", ""),
            "publish_time": result.get("publish_time", ""),
            "method": "gne",
        }

    except Exception as e:
        # 降级到通用爬虫
        return intelligent_crawl(url, crawler_type=CrawlerType.CRAWL4AI.value)


@celery_app.task(name="app.tasks.crawler_tasks.crawl_government_docs")
def crawl_government_docs(url: str) -> Dict[str, Any]:
    """
    政府文件专用爬虫
    使用 gecco 或 drissionpage（处理复杂政府网站）
    """
    try:
        from DrissionPage import ChromiumPage

        # 使用 DrissionPage 处理复杂政府网站
        page = ChromiumPage()
        page.get(url)

        # 等待页面加载
        page.wait.load_start()

        # 提取内容
        title = page.title
        content = page.text

        # 查找下载链接（PDF, DOC 等）
        download_links = []
        for link in page.ele("tag:a"):
            href = link.attr("href")
            if href and any(ext in href.lower() for ext in [".pdf", ".doc", ".docx", ".xls", ".xlsx"]):
                download_links.append(href)

        page.quit()

        return {
            "success": True,
            "url": url,
            "title": title,
            "content": content,
            "download_links": download_links,
            "method": "drissionpage",
        }

    except Exception as e:
        # 降级到 gecco 或通用爬虫
        return intelligent_crawl(url, crawler_type=CrawlerType.GECCO.value)


@celery_app.task(name="app.tasks.crawler_tasks.crawl_and_process")
def crawl_and_process(url: str, crawler_type: str = "auto") -> Dict[str, Any]:
    """
    爬取并自动处理：爬取 → 文档处理流程

    自动触发：用户提交 URL 后自动调用
    """
    from app.tasks.document_tasks import (
        vectorize_and_store,
        extract_entities,
        fulltext_index,
        save_to_db
    )
    from celery import group

    # 步骤 1: 爬取内容
    crawl_result = intelligent_crawl(url, crawler_type)

    if not crawl_result.get("success"):
        return {
            "success": False,
            "error": "Crawling failed",
            "details": crawl_result,
        }

    # 步骤 2: 构造文档数据
    doc_data = {
        "success": True,
        "file_path": url,
        "markdown": crawl_result["content"],
        "title": crawl_result.get("metadata", {}).get("title", url),
        "file_size": len(crawl_result["content"]),
        "converted_at": crawl_result["crawled_at"],
        "source": "web_crawler",
    }

    # 步骤 3: 并行处理
    parallel_tasks = group([
        vectorize_and_store.s(doc_data),
        extract_entities.s(doc_data),
        fulltext_index.s(doc_data),
        save_to_db.s(doc_data),
    ])

    results = parallel_tasks.apply_async()
    all_results = results.get()

    return {
        "success": True,
        "url": url,
        "crawl": crawl_result,
        "processing": {
            "vectorization": all_results[0],
            "entity_extraction": all_results[1],
            "fulltext_indexing": all_results[2],
            "database_save": all_results[3],
        },
        "completed_at": datetime.utcnow().isoformat(),
    }
