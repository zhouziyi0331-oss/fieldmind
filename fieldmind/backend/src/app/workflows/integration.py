"""
工具集成器 - 管理所有外部工具的集成和智能路由
"""

from typing import Dict, List, Any, Optional, Callable
from enum import Enum
import logging
import os

logger = logging.getLogger(__name__)


class ToolCategory(Enum):
    """工具类别"""
    CRAWLER = "crawler"
    NLP = "nlp"
    VECTOR_DB = "vector_db"
    GRAPH_DB = "graph_db"
    SEARCH = "search"
    LLM = "llm"
    DOCUMENT = "document"
    VISUALIZATION = "visualization"


class ToolRegistry:
    """工具注册表 - 管理所有可用工具"""

    def __init__(self):
        self.tools: Dict[ToolCategory, Dict[str, Dict]] = {
            category: {} for category in ToolCategory
        }
        self._register_all_tools()

    def _register_all_tools(self):
        """注册所有工具"""
        # 爬虫工具
        self.register_tool(ToolCategory.CRAWLER, "crawl4ai", {
            "name": "crawl4ai",
            "description": "通用网页爬取工具",
            "paid_api": False,
            "use_cases": ["通用网页", "博客", "论坛"],
            "priority": 3,
        })

        self.register_tool(ToolCategory.CRAWLER, "gecco", {
            "name": "gecco",
            "description": "政府网站专用爬虫",
            "paid_api": False,
            "use_cases": ["政府网站", "公告", "政策文件"],
            "priority": 5,
        })

        self.register_tool(ToolCategory.CRAWLER, "browser-use", {
            "name": "browser-use",
            "description": "浏览器自动化工具",
            "paid_api": False,
            "use_cases": ["需要登录", "JavaScript渲染", "复杂交互"],
            "priority": 4,
        })

        self.register_tool(ToolCategory.CRAWLER, "firecrawl", {
            "name": "firecrawl",
            "description": "Firecrawl API爬取服务",
            "paid_api": True,
            "use_cases": ["API调用", "快速爬取"],
            "priority": 2,
        })

        self.register_tool(ToolCategory.CRAWLER, "newspaper3k", {
            "name": "newspaper3k",
            "description": "新闻文章提取工具",
            "paid_api": False,
            "use_cases": ["新闻网站", "文章提取"],
            "priority": 5,
        })

        self.register_tool(ToolCategory.CRAWLER, "gne", {
            "name": "gne",
            "description": "通用新闻提取器（中文优化）",
            "paid_api": False,
            "use_cases": ["中文新闻", "文章提取"],
            "priority": 5,
        })

        self.register_tool(ToolCategory.CRAWLER, "drissionpage", {
            "name": "drissionpage",
            "description": "动态网页爬取工具",
            "paid_api": False,
            "use_cases": ["动态内容", "AJAX加载"],
            "priority": 3,
        })

        # NLP工具
        self.register_tool(ToolCategory.NLP, "hanlp", {
            "name": "HanLP",
            "description": "中文自然语言处理工具包",
            "paid_api": False,
            "use_cases": ["命名实体识别", "依存句法分析", "语义角色标注"],
            "priority": 5,
        })

        self.register_tool(ToolCategory.NLP, "openai", {
            "name": "OpenAI API",
            "description": "OpenAI NLP服务",
            "paid_api": True,
            "use_cases": ["实体识别", "文本分类"],
            "priority": 2,
        })

        # 向量数据库
        self.register_tool(ToolCategory.VECTOR_DB, "chromadb", {
            "name": "ChromaDB",
            "description": "本地向量数据库",
            "paid_api": False,
            "use_cases": ["向量存储", "语义检索"],
            "priority": 5,
        })

        self.register_tool(ToolCategory.VECTOR_DB, "pinecone", {
            "name": "Pinecone",
            "description": "云端向量数据库",
            "paid_api": True,
            "use_cases": ["大规模向量检索"],
            "priority": 2,
        })

        # 图数据库
        self.register_tool(ToolCategory.GRAPH_DB, "neo4j", {
            "name": "Neo4j",
            "description": "图数据库（社区版）",
            "paid_api": False,
            "use_cases": ["知识图谱", "关系查询"],
            "priority": 5,
        })

        # 搜索引擎
        self.register_tool(ToolCategory.SEARCH, "whoosh", {
            "name": "Whoosh",
            "description": "纯Python全文搜索引擎",
            "paid_api": False,
            "use_cases": ["全文检索", "关键词搜索"],
            "priority": 5,
        })

        self.register_tool(ToolCategory.SEARCH, "elasticsearch", {
            "name": "Elasticsearch",
            "description": "分布式搜索引擎",
            "paid_api": False,
            "use_cases": ["大规模搜索", "日志分析"],
            "priority": 3,
        })

        # LLM工具
        self.register_tool(ToolCategory.LLM, "ollama", {
            "name": "Ollama",
            "description": "本地LLM运行环境",
            "paid_api": False,
            "use_cases": ["本地推理", "零成本运行"],
            "priority": 5,
            "models": ["qwen2.5", "llama3", "mistral"],
        })

        self.register_tool(ToolCategory.LLM, "openai", {
            "name": "OpenAI API",
            "description": "OpenAI GPT服务",
            "paid_api": True,
            "use_cases": ["高质量生成", "复杂推理"],
            "priority": 3,
        })

        self.register_tool(ToolCategory.LLM, "anthropic", {
            "name": "Anthropic Claude",
            "description": "Anthropic Claude服务",
            "paid_api": True,
            "use_cases": ["长文本处理", "复杂推理"],
            "priority": 3,
        })

        # 文档处理
        self.register_tool(ToolCategory.DOCUMENT, "markitdown", {
            "name": "markitdown",
            "description": "文档转Markdown工具",
            "paid_api": False,
            "use_cases": ["PDF转换", "Word转换", "PPT转换"],
            "priority": 5,
        })

        self.register_tool(ToolCategory.DOCUMENT, "whisper", {
            "name": "Whisper",
            "description": "语音识别工具（本地版）",
            "paid_api": False,
            "use_cases": ["音频转文字", "语音识别"],
            "priority": 5,
        })

        self.register_tool(ToolCategory.DOCUMENT, "sentence-transformers", {
            "name": "sentence-transformers",
            "description": "文本向量化工具",
            "paid_api": False,
            "use_cases": ["文本嵌入", "语义相似度"],
            "priority": 5,
        })

        # 可视化工具
        self.register_tool(ToolCategory.VISUALIZATION, "pyecharts", {
            "name": "pyecharts",
            "description": "Python图表生成库",
            "paid_api": False,
            "use_cases": ["柱状图", "折线图", "饼图", "热力图"],
            "priority": 5,
        })

        self.register_tool(ToolCategory.VISUALIZATION, "folium", {
            "name": "folium",
            "description": "地图可视化库",
            "paid_api": False,
            "use_cases": ["地理数据", "地图标注"],
            "priority": 5,
        })

        self.register_tool(ToolCategory.VISUALIZATION, "wordcloud", {
            "name": "wordcloud",
            "description": "词云生成库",
            "paid_api": False,
            "use_cases": ["词频可视化", "文本分析"],
            "priority": 5,
        })

        self.register_tool(ToolCategory.VISUALIZATION, "pyvis", {
            "name": "pyvis",
            "description": "网络图可视化库",
            "paid_api": False,
            "use_cases": ["知识图谱可视化", "关系网络"],
            "priority": 5,
        })

    def register_tool(
        self,
        category: ToolCategory,
        tool_id: str,
        config: Dict[str, Any]
    ):
        """注册工具"""
        self.tools[category][tool_id] = config
        logger.info(f"注册工具: {category.value}/{tool_id}")

    def get_tool(self, category: ToolCategory, tool_id: str) -> Optional[Dict]:
        """获取工具配置"""
        return self.tools[category].get(tool_id)

    def list_tools(
        self,
        category: Optional[ToolCategory] = None,
        paid_only: bool = False,
        free_only: bool = False
    ) -> Dict[str, List[Dict]]:
        """列出工具"""
        result = {}

        categories = [category] if category else list(ToolCategory)

        for cat in categories:
            tools = self.tools[cat].values()

            # 过滤
            if paid_only:
                tools = [t for t in tools if t.get("paid_api", False)]
            if free_only:
                tools = [t for t in tools if not t.get("paid_api", False)]

            result[cat.value] = list(tools)

        return result

    def get_best_tool(
        self,
        category: ToolCategory,
        use_case: str,
        prefer_free: bool = True
    ) -> Optional[str]:
        """根据用例选择最佳工具"""
        tools = self.tools[category].values()

        # 过滤匹配用例的工具
        matched_tools = [
            t for t in tools
            if use_case in t.get("use_cases", [])
        ]

        if not matched_tools:
            return None

        # 优先选择免费工具
        if prefer_free:
            free_tools = [t for t in matched_tools if not t.get("paid_api", False)]
            if free_tools:
                matched_tools = free_tools

        # 按优先级排序
        matched_tools.sort(key=lambda t: t.get("priority", 0), reverse=True)

        return matched_tools[0]["name"]


class IntelligentRouter:
    """智能路由器 - 根据任务特征自动选择最佳工具"""

    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    def route_crawler(self, url: str, prefer_free: bool = True) -> str:
        """智能路由爬虫工具"""
        url_lower = url.lower()

        # 政府网站
        if any(domain in url_lower for domain in [".gov.", "www.gov", "政府"]):
            return "gecco"

        # 新闻网站
        if any(kw in url_lower for kw in ["news", "article", "新闻", "xinhua", "people"]):
            return "newspaper3k"

        # 需要登录
        if any(kw in url_lower for kw in ["login", "signin", "auth"]):
            return "browser-use"

        # 复杂JavaScript
        if any(kw in url_lower for kw in ["app", "react", "vue", "angular"]):
            return "drissionpage"

        # 默认使用crawl4ai
        return "crawl4ai"

    def route_nlp(self, task: str, text_length: int, prefer_free: bool = True) -> str:
        """智能路由NLP工具"""
        # 中文任务优先使用HanLP
        if task in ["ner", "pos", "dep", "srl", "sentiment"]:
            return "hanlp"

        # 复杂任务且文本较短可以考虑付费API
        if not prefer_free and text_length < 2000:
            return "openai"

        return "hanlp"

    def route_llm(
        self,
        task: str,
        context_length: int,
        prefer_free: bool = True
    ) -> str:
        """智能路由LLM工具"""
        # 优先使用本地Ollama
        if prefer_free:
            return "ollama"

        # 长文本任务
        if context_length > 8000:
            return "anthropic"

        # 短文本任务
        return "openai"

    def route_vector_db(self, dataset_size: int, prefer_free: bool = True) -> str:
        """智能路由向量数据库"""
        # 小数据集使用本地ChromaDB
        if prefer_free or dataset_size < 100000:
            return "chromadb"

        # 大数据集使用Pinecone
        return "pinecone"

    def route_visualization(self, chart_type: str) -> str:
        """智能路由可视化工具"""
        if chart_type in ["map", "geo"]:
            return "folium"
        elif chart_type in ["wordcloud", "text"]:
            return "wordcloud"
        elif chart_type in ["network", "graph"]:
            return "pyvis"
        else:
            return "pyecharts"


class ToolIntegration:
    """工具集成器 - 提供统一的工具调用接口"""

    def __init__(self):
        self.registry = ToolRegistry()
        self.router = IntelligentRouter(self.registry)

    # ==================== 爬虫工具集成 ====================

    def crawl_url(
        self,
        url: str,
        crawler: Optional[str] = None,
        prefer_free: bool = True
    ) -> Dict[str, Any]:
        """统一爬取接口"""
        if not crawler:
            crawler = self.router.route_crawler(url, prefer_free)

        logger.info(f"使用爬虫 {crawler} 爬取: {url}")

        if crawler == "crawl4ai":
            return self._crawl_with_crawl4ai(url)
        elif crawler == "gecco":
            return self._crawl_with_gecco(url)
        elif crawler == "browser-use":
            return self._crawl_with_browser_use(url)
        elif crawler == "newspaper3k":
            return self._crawl_with_newspaper(url)
        elif crawler == "gne":
            return self._crawl_with_gne(url)
        elif crawler == "drissionpage":
            return self._crawl_with_drissionpage(url)
        else:
            raise ValueError(f"未知爬虫: {crawler}")

    def _crawl_with_crawl4ai(self, url: str) -> Dict[str, Any]:
        """使用crawl4ai爬取"""
        try:
            from crawl4ai import WebCrawler
            crawler = WebCrawler()
            result = crawler.run(url)
            return {
                "success": True,
                "markdown": result.markdown,
                "html": result.html,
                "metadata": {
                    "title": result.title,
                    "url": url,
                    "crawler": "crawl4ai"
                }
            }
        except Exception as e:
            logger.error(f"crawl4ai爬取失败: {e}")
            return {"success": False, "error": str(e)}

    def _crawl_with_newspaper(self, url: str) -> Dict[str, Any]:
        """使用newspaper3k提取新闻"""
        try:
            from newspaper import Article
            article = Article(url, language='zh')
            article.download()
            article.parse()

            markdown = f"# {article.title}\n\n"
            markdown += f"**作者**: {', '.join(article.authors)}\n\n"
            markdown += f"**发布时间**: {article.publish_date}\n\n"
            markdown += f"{article.text}\n"

            return {
                "success": True,
                "markdown": markdown,
                "metadata": {
                    "title": article.title,
                    "authors": article.authors,
                    "publish_date": str(article.publish_date),
                    "url": url,
                    "crawler": "newspaper3k"
                }
            }
        except Exception as e:
            logger.error(f"newspaper3k提取失败: {e}")
            return {"success": False, "error": str(e)}

    def _crawl_with_gne(self, url: str) -> Dict[str, Any]:
        """使用gne提取新闻"""
        try:
            import requests
            from gne import GeneralNewsExtractor

            response = requests.get(url, timeout=10)
            extractor = GeneralNewsExtractor()
            result = extractor.extract(response.text)

            markdown = f"# {result['title']}\n\n"
            markdown += f"**发布时间**: {result['publish_time']}\n\n"
            markdown += f"**作者**: {result['author']}\n\n"
            markdown += f"{result['content']}\n"

            return {
                "success": True,
                "markdown": markdown,
                "metadata": {
                    "title": result["title"],
                    "author": result["author"],
                    "publish_time": result["publish_time"],
                    "url": url,
                    "crawler": "gne"
                }
            }
        except Exception as e:
            logger.error(f"gne提取失败: {e}")
            return {"success": False, "error": str(e)}

    def _crawl_with_gecco(self, url: str) -> Dict[str, Any]:
        """使用gecco爬取政府网站"""
        # gecco需要预先配置规则，这里返回占位符
        logger.warning("gecco需要配置规则文件，使用fallback")
        return self._crawl_with_crawl4ai(url)

    def _crawl_with_browser_use(self, url: str) -> Dict[str, Any]:
        """使用browser-use进行浏览器自动化"""
        logger.warning("browser-use需要Agent驱动，使用fallback")
        return self._crawl_with_crawl4ai(url)

    def _crawl_with_drissionpage(self, url: str) -> Dict[str, Any]:
        """使用drissionpage爬取动态网页"""
        logger.warning("drissionpage需要额外配置，使用fallback")
        return self._crawl_with_crawl4ai(url)

    # ==================== NLP工具集成 ====================

    def extract_entities(
        self,
        text: str,
        tool: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """统一实体识别接口"""
        if not tool:
            tool = self.router.route_nlp("ner", len(text))

        logger.info(f"使用工具 {tool} 进行实体识别")

        if tool == "hanlp":
            return self._extract_entities_hanlp(text)
        elif tool == "openai":
            return self._extract_entities_openai(text)
        else:
            raise ValueError(f"未知NLP工具: {tool}")

    def _extract_entities_hanlp(self, text: str) -> List[Dict[str, str]]:
        """使用HanLP提取实体"""
        try:
            import hanlp
            ner = hanlp.load(hanlp.pretrained.ner.MSRA_NER_BERT_BASE_ZH)
            entities = ner(text)

            result = []
            for entity, label in entities:
                result.append({
                    "text": entity,
                    "label": label,
                    "source": "hanlp"
                })
            return result
        except Exception as e:
            logger.error(f"HanLP实体识别失败: {e}")
            return []

    def _extract_entities_openai(self, text: str) -> List[Dict[str, str]]:
        """使用OpenAI提取实体"""
        logger.warning("OpenAI实体识别需要API key，返回空结果")
        return []

    # ==================== LLM工具集成 ====================

    def generate_text(
        self,
        prompt: str,
        model: Optional[str] = None,
        prefer_free: bool = True
    ) -> str:
        """统一文本生成接口"""
        if not model:
            model = self.router.route_llm("generation", len(prompt), prefer_free)

        logger.info(f"使用模型 {model} 生成文本")

        if model == "ollama":
            return self._generate_with_ollama(prompt)
        elif model == "openai":
            return self._generate_with_openai(prompt)
        elif model == "anthropic":
            return self._generate_with_anthropic(prompt)
        else:
            raise ValueError(f"未知LLM: {model}")

    def _generate_with_ollama(self, prompt: str) -> str:
        """使用Ollama生成文本"""
        try:
            import requests
            response = requests.post(
                os.getenv("OLLAMA_API_URL", "http://localhost:11434") + "/api/generate",
                json={
                    "model": "qwen2.5",
                    "prompt": prompt,
                    "stream": False
                },
                timeout=60
            )
            return response.json()["response"]
        except Exception as e:
            logger.error(f"Ollama生成失败: {e}")
            return ""

    def _generate_with_openai(self, prompt: str) -> str:
        """使用OpenAI生成文本"""
        logger.warning("OpenAI需要API key，返回空结果")
        return ""

    def _generate_with_anthropic(self, prompt: str) -> str:
        """使用Anthropic生成文本"""
        logger.warning("Anthropic需要API key，返回空结果")
        return ""


# ==================== 全局实例 ====================

# 工具注册表实例
tool_registry = ToolRegistry()

# 智能路由器实例
intelligent_router = IntelligentRouter(tool_registry)

# 工具集成器实例
tool_integration = ToolIntegration()
