"""
SearchAgent - 搜索专员Agent

⚠️ 已废弃：此Agent将在v2.0中移除，请使用 app.tools.search.web_search

负责互联网信息检索、网页内容提取、结果过滤和排序
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import re
import time

from .base_agent import AgentBase, AgentRole, AgentTask, AgentResult
from app.utils.deprecation import deprecated

logger = logging.getLogger(__name__)


@deprecated(
    reason="旧Agent架构已被6-Agent v2替代",
    replacement="app.tools.search.web_search",
    version="2.0"
)
class SearchAgent(AgentBase):
    """搜索专员 - 负责互联网信息检索"""

    def __init__(self, agent_id: Optional[str] = None):
        super().__init__(agent_id)
        self.max_results = 10
        self.timeout = 10
        self._init_search_engine()

    @property
    def role(self) -> AgentRole:
        return AgentRole.SEARCH

    @property
    def name(self) -> str:
        return "搜索专员"

    @property
    def description(self) -> str:
        return "负责互联网信息检索、网页内容提取、结果过滤和排序"

    @property
    def capabilities(self) -> List[str]:
        return [
            "互联网关键词搜索",
            "网页内容提取与解析",
            "搜索结果过滤和排序",
            "多地区搜索支持",
            "安全搜索控制"
        ]

    def _initialize_tools(self):
        """初始化搜索工具"""
        self.tools = {
            'search': 'Internet search capability',
            'content_extract': 'Web page content extraction',
            'result_filter': 'Search result filtering and ranking'
        }

    def _init_search_engine(self):
        """初始化搜索引擎（使用DuckDuckGo）"""
        try:
            # 尝试新的ddgs包
            from ddgs import DDGS
            self.search_engine = DDGS()
            self.search_available = True
            self.use_new_api = True
            logger.info("DDGS search engine initialized (new API)")
        except ImportError:
            try:
                # 尝试旧的duckduckgo_search包
                from duckduckgo_search import DDGS
                self.search_engine = DDGS()
                self.search_available = True
                self.use_new_api = False
                logger.info("DuckDuckGo search engine initialized (old API)")
            except ImportError:
                logger.warning("Neither ddgs nor duckduckgo-search installed, search will be limited")
                self.search_engine = None
                self.search_available = False
                self.use_new_api = False

    def _execute_task_impl(self, task: AgentTask) -> Dict[str, Any]:
        """
        执行搜索任务

        task.input_data:
          - query: 搜索查询（必需）
          - max_results: 最大结果数（默认10）
          - region: 地区代码（默认wt-wt，世界范围）
          - safesearch: 安全搜索级别（moderate/strict/off，默认moderate）
          - extract_content: 是否提取网页内容（默认False）
        """
        query = task.input_data.get('query', '')
        if not query or not query.strip():
            raise ValueError('搜索查询不能为空')

        # 获取参数
        max_results = task.input_data.get('max_results', self.max_results)
        region = task.input_data.get('region', 'wt-wt')
        safesearch = task.input_data.get('safesearch', 'moderate')
        extract_content = task.input_data.get('extract_content', False)

        logger.info(f"Executing search for: {query} (max_results={max_results})")

        # 执行搜索
        search_results = self._search(query, max_results, region, safesearch)

        if not search_results:
            raise RuntimeError(f'搜索未返回结果: {query}')

        # 提取网页内容（如果需要）
        if extract_content:
            search_results = self._extract_contents(search_results)

        return {
            'query': query,
            'results': search_results,
            'total_results': len(search_results),
            'timestamp': datetime.now().isoformat()
        }

    def _search(self, query: str, max_results: int, region: str, safesearch: str) -> List[Dict[str, Any]]:
        """执行真实的搜索"""
        if not self.search_available or self.search_engine is None:
            logger.error("Search engine not available")
            return []

        try:
            results = []

            if self.use_new_api:
                # 新的ddgs API: text(query, ...)
                search_results = self.search_engine.text(
                    query=query,
                    region=region,
                    safesearch=safesearch,
                    max_results=max_results
                )
            else:
                # 旧的duckduckgo_search API: text(keywords, ...)
                search_results = self.search_engine.text(
                    keywords=query,
                    region=region,
                    safesearch=safesearch,
                    max_results=max_results
                )

            # 处理结果
            for idx, result in enumerate(search_results):
                if idx >= max_results:
                    break

                results.append({
                    'title': result.get('title', ''),
                    'url': result.get('href') or result.get('link', ''),
                    'snippet': result.get('body') or result.get('snippet', ''),
                    'rank': idx + 1
                })

            logger.info(f"Found {len(results)} search results for query: {query}")
            return results

        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            return []

    def _extract_contents(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """提取搜索结果的网页内容"""
        import requests
        from bs4 import BeautifulSoup

        for result in results:
            url = result.get('url', '')
            if not url:
                continue

            try:
                # 获取网页内容
                response = requests.get(
                    url,
                    timeout=self.timeout,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                )
                response.raise_for_status()

                # 解析HTML
                soup = BeautifulSoup(response.content, 'html.parser')

                # 移除脚本和样式
                for script in soup(['script', 'style', 'nav', 'footer', 'header']):
                    script.decompose()

                # 提取文本
                text = soup.get_text(separator=' ', strip=True)
                # 清理多余空白
                text = re.sub(r'\s+', ' ', text).strip()

                # 限制长度
                if len(text) > 5000:
                    text = text[:5000] + '...'

                result['content'] = text
                result['content_length'] = len(text)

                logger.info(f"Extracted content from {url} ({len(text)} chars)")

                # 避免请求过快
                time.sleep(0.5)

            except Exception as e:
                logger.warning(f"Failed to extract content from {url}: {str(e)}")
                result['content'] = ''
                result['content_error'] = str(e)

        return results

    def search_sync(self, query: str, max_results: int = 10, extract_content: bool = False) -> Dict[str, Any]:
        """同步搜索方法（便于直接调用）"""
        task = AgentTask(
            task_id=f"search_{datetime.now().timestamp()}",
            task_type="search",
            input_data={
                'query': query,
                'max_results': max_results,
                'extract_content': extract_content
            },
            priority=5
        )

        result = self.execute_task(task)
        return result.output_data
