"""
爬虫API路由 - 集成智能爬虫调度
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from pydantic import BaseModel, HttpUrl
from datetime import datetime

from app.schemas.response import success_response, error_response

# from app.tasks.crawler_tasks import (
#     intelligent_crawl,
#     crawl_news,
#     crawl_government_docs,
#     crawl_and_process,
# )
# from app.celery_app import celery_app

router = APIRouter()


class CrawlRequest(BaseModel):
    url: HttpUrl
    crawler_type: str = "auto"  # auto, crawl4ai, gecco, browser-use, firecrawl
    auto_process: bool = True  # 是否自动进入文档处理流程


class BatchCrawlRequest(BaseModel):
    urls: List[HttpUrl]
    crawler_type: str = "auto"
    auto_process: bool = True


@router.post("/crawl")
async def crawl_url(request: CrawlRequest) -> Dict[str, Any]:
    """
    爬取单个 URL

    智能选择爬虫：
    - crawl4ai: 静态页面、新闻文章
    - gecco: 政府网站、结构化数据
    - browser-use: 需要 JS 渲染、登录
    - firecrawl: 大规模爬取（需付费）

    自动触发（当 auto_process=True）：
    爬取 → 向量化 → 实体提取 → 知识图谱
    """
    try:
        url = str(request.url)

        if request.auto_process:
            # 爬取并自动处理
            task = crawl_and_process.delay(url, request.crawler_type)
            message = "爬取任务已启动，完成后自动进入文档处理流程"
        else:
            # 仅爬取
            task = intelligent_crawl.delay(url, request.crawler_type)
            message = "爬取任务已启动"

        return success_response(
            data={
                "url": url,
                "crawler_type": request.crawler_type,
                "auto_process": request.auto_process,
                "task_id": task.id,
                "status_url": f"/api/v1/crawler/status/{task.id}",
                "submitted_at": datetime.utcnow().isoformat(),
            },
            message=message
        )

    except Exception as e:
        return error_response(
            code="CRAWL_TASK_FAILED",
            message=f"爬取任务提交失败: {str(e)}"
        )


@router.post("/batch-crawl")
async def batch_crawl_urls(request: BatchCrawlRequest) -> Dict[str, Any]:
    """
    批量爬取 URLs
    """
    try:
        tasks = []

        for url in request.urls:
            url_str = str(url)

            if request.auto_process:
                task = crawl_and_process.delay(url_str, request.crawler_type)
            else:
                task = intelligent_crawl.delay(url_str, request.crawler_type)

            tasks.append({
                "url": url_str,
                "task_id": task.id,
            })

        return success_response(
            data={
                "total": len(tasks),
                "crawler_type": request.crawler_type,
                "auto_process": request.auto_process,
                "tasks": tasks,
                "submitted_at": datetime.utcnow().isoformat(),
            },
            message=f"已提交 {len(tasks)} 个爬取任务"
        )

    except Exception as e:
        return error_response(
            code="BATCH_CRAWL_FAILED",
            message=f"批量爬取失败: {str(e)}"
        )


@router.post("/news")
async def crawl_news_article(url: HttpUrl, auto_process: bool = True) -> Dict[str, Any]:
    """
    爬取新闻文章（专用）
    使用 newspaper3k + gne（中文新闻）
    """
    try:
        url_str = str(url)

        if auto_process:
            task = crawl_and_process.delay(url_str, "news")
        else:
            task = crawl_news.delay(url_str)

        return success_response(
            data={
                "url": url_str,
                "method": "newspaper3k + gne",
                "task_id": task.id,
                "status_url": f"/api/v1/crawler/status/{task.id}",
            },
            message="新闻爬取任务已启动"
        )

    except Exception as e:
        return error_response(
            code="NEWS_CRAWL_FAILED",
            message=f"新闻爬取失败: {str(e)}"
        )


@router.post("/government")
async def crawl_government_document(url: HttpUrl, auto_process: bool = True) -> Dict[str, Any]:
    """
    爬取政府文件（专用）
    使用 gecco 或 drissionpage
    """
    try:
        url_str = str(url)

        if auto_process:
            task = crawl_and_process.delay(url_str, "government")
        else:
            task = crawl_government_docs.delay(url_str)

        return success_response(
            data={
                "url": url_str,
                "method": "gecco + drissionpage",
                "task_id": task.id,
                "status_url": f"/api/v1/crawler/status/{task.id}",
            },
            message="政府文件爬取任务已启动"
        )

    except Exception as e:
        return error_response(
            code="GOVERNMENT_CRAWL_FAILED",
            message=f"政府文件爬取失败: {str(e)}"
        )


@router.get("/status/{task_id}/")
async def get_crawl_status(task_id: str) -> Dict[str, Any]:
    """
    查询爬取任务状态
    """
    try:
        task = celery_app.AsyncResult(task_id)

        response = {
            "task_id": task_id,
            "state": task.state,
            "ready": task.ready(),
        }

        if task.ready():
            if task.successful():
                response["result"] = task.result
            else:
                response["error"] = str(task.info)

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"状态查询失败: {str(e)}")


@router.get("/supported-crawlers")
async def get_supported_crawlers() -> Dict[str, Any]:
    """
    获取支持的爬虫列表
    """
    return success_response(
        data={
            "crawlers": [
                {
                    "type": "crawl4ai",
                    "name": "Crawl4AI",
                    "description": "轻量级爬虫，适合静态页面和新闻文章",
                    "free": True,
                    "speed": "fast",
                },
                {
                    "type": "gecco",
                    "name": "Gecco",
                    "description": "配置化爬虫，适合结构化数据和政府网站",
                    "free": True,
                    "speed": "medium",
                },
                {
                    "type": "browser-use",
                    "name": "Browser-Use",
                    "description": "AI驱动浏览器自动化，适合复杂交互页面",
                    "free": True,
                    "speed": "slow",
                },
                {
                    "type": "firecrawl",
                    "name": "Firecrawl",
                    "description": "企业级爬虫服务，适合大规模爬取",
                    "free": False,
                    "pricing": "$20-100/月",
                    "speed": "fast",
                },
            ],
            "recommendation": {
                "news": "crawl4ai (newspaper3k + gne)",
                "government": "gecco + drissionpage",
                "static_pages": "crawl4ai",
                "complex_pages": "browser-use",
                "large_scale": "firecrawl (付费)",
            }
        }
    )
