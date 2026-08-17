"""
Plugin Registry - 插件注册表系统

扫描、解析、管理GitHub插件，构建能力映射表。
为SuperAgent提供插件发现和动态加载能力。

设计理念:
1. 自动扫描 - 无需手动注册，自动发现repos/下所有插件
2. 能力映射 - 插件→能力、能力→插件双向索引
3. 延迟加载 - 只加载元数据，需要时再加载实际模块
4. 版本管理 - 追踪插件版本和依赖关系
5. 健康检查 - 验证插件可用性和兼容性
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import importlib.util
import sys

logger = logging.getLogger(__name__)


class PluginType(Enum):
    """插件类型枚举"""
    KNOWLEDGE_GRAPH = "knowledge_graph"      # 知识图谱: graphrag, graphiti, cognee
    SEARCH_CRAWLER = "search_crawler"        # 搜索爬虫: crawl4ai, firecrawl, browser-use
    RAG_MEMORY = "rag_memory"                # RAG记忆: ragflow, LightRAG, mem0
    NLP_PROCESSING = "nlp_processing"        # NLP处理: HanLP, pyhanlp
    DOCUMENT_CONVERSION = "document_conversion"  # 文档转换: markitdown, PDF-Guru
    VISUALIZATION = "visualization"          # 可视化: mind-map, nvd3, rawgraphs-app
    DATABASE = "database"                     # 数据库: neo4j, duckdb
    UTILITY = "utility"                       # 工具: Pillow, exif-reader, gecco
    RESOURCES = "resources"                   # 资源库: awesome-*, funNLP
    OTHER = "other"                          # 其他


class PluginStatus(Enum):
    """插件状态枚举"""
    DISCOVERED = "discovered"      # 已发现
    SCANNED = "scanned"           # 已扫描
    LOADED = "loaded"             # 已加载
    ACTIVE = "active"             # 活跃
    INACTIVE = "inactive"         # 不活跃
    ERROR = "error"               # 错误
    DEPRECATED = "deprecated"     # 已弃用


@dataclass
class PluginCapability:
    """插件能力定义"""
    capability_id: str              # 能力ID: "entity_extraction", "web_crawl"
    category: str                   # 能力分类: "knowledge", "search", "processing"
    description: str                # 能力描述
    input_types: List[str]          # 输入类型: ["text", "url", "file"]
    output_types: List[str]         # 输出类型: ["entities", "graph", "document"]
    parameters: Dict[str, Any] = field(default_factory=dict)  # 参数配置
    performance_hints: Dict[str, Any] = field(default_factory=dict)  # 性能提示


@dataclass
class PluginMetadata:
    """插件元数据"""
    plugin_id: str                  # 插件ID (目录名)
    plugin_name: str                # 插件名称
    plugin_type: PluginType         # 插件类型
    version: str = "unknown"        # 版本
    description: str = ""           # 描述
    repo_path: str = ""             # 仓库路径
    main_module: Optional[str] = None  # 主模块路径
    capabilities: List[PluginCapability] = field(default_factory=list)  # 能力列表
    dependencies: List[str] = field(default_factory=list)  # 依赖列表
    languages: List[str] = field(default_factory=list)  # 编程语言
    status: PluginStatus = PluginStatus.DISCOVERED  # 状态
    last_updated: datetime = field(default_factory=datetime.now)  # 最后更新
    metadata: Dict[str, Any] = field(default_factory=dict)  # 额外元数据

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data["plugin_type"] = self.plugin_type.value
        data["status"] = self.status.value
        data["last_updated"] = self.last_updated.isoformat()
        return data


@dataclass
class CapabilityIndex:
    """能力索引"""
    capability_id: str
    category: str
    providers: List[str] = field(default_factory=list)  # 提供此能力的插件ID列表
    priority_order: List[str] = field(default_factory=list)  # 优先级排序


class PluginRegistry:
    """
    插件注册表 - 核心管理系统

    职责:
    1. 扫描插件目录，自动发现插件
    2. 解析插件元数据（README、package.json、setup.py等）
    3. 构建能力映射表（插件→能力、能力→插件）
    4. 提供插件查询接口
    5. 管理插件生命周期
    """

    def __init__(self, repos_dir: str = "/Users/alwan/FieldMind/repos"):
        """
        初始化插件注册表

        Args:
            repos_dir: 插件仓库根目录
        """
        self.repos_dir = Path(repos_dir)
        self._plugins: Dict[str, PluginMetadata] = {}  # plugin_id -> metadata
        self._capability_index: Dict[str, CapabilityIndex] = {}  # capability_id -> index
        self._type_index: Dict[PluginType, List[str]] = {}  # type -> plugin_ids
        self._loaded_modules: Dict[str, Any] = {}  # plugin_id -> module

        logger.info(f"PluginRegistry initialized with repos_dir: {self.repos_dir}")

    # ==================== 扫描与发现 ====================

    def scan_all_plugins(self) -> Dict[str, PluginMetadata]:
        """
        扫描所有插件

        Returns:
            扫描到的插件元数据字典
        """
        logger.info(f"Starting plugin scan in {self.repos_dir}")

        if not self.repos_dir.exists():
            logger.error(f"Repos directory not found: {self.repos_dir}")
            return {}

        plugin_dirs = [d for d in self.repos_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]
        logger.info(f"Found {len(plugin_dirs)} potential plugin directories")

        for plugin_dir in plugin_dirs:
            try:
                metadata = self._scan_plugin(plugin_dir)
                if metadata:
                    self._register_plugin(metadata)
            except Exception as e:
                logger.error(f"Error scanning plugin {plugin_dir.name}: {e}")

        self._build_indexes()
        logger.info(f"Plugin scan complete. Registered {len(self._plugins)} plugins")

        return self._plugins

    def _scan_plugin(self, plugin_dir: Path) -> Optional[PluginMetadata]:
        """
        扫描单个插件

        Args:
            plugin_dir: 插件目录路径

        Returns:
            插件元数据，如果扫描失败则返回None
        """
        plugin_id = plugin_dir.name
        logger.debug(f"Scanning plugin: {plugin_id}")

        # 基础元数据
        metadata = PluginMetadata(
            plugin_id=plugin_id,
            plugin_name=plugin_id,
            plugin_type=self._infer_plugin_type(plugin_id),
            repo_path=str(plugin_dir),
            status=PluginStatus.DISCOVERED
        )

        # 解析README获取描述
        readme_path = self._find_readme(plugin_dir)
        if readme_path:
            metadata.description = self._extract_description(readme_path)

        # 解析package.json (Node.js项目)
        package_json = plugin_dir / "package.json"
        if package_json.exists():
            self._parse_package_json(package_json, metadata)

        # 解析setup.py (Python项目)
        setup_py = plugin_dir / "setup.py"
        if setup_py.exists():
            self._parse_setup_py(setup_py, metadata)

        # 解析pyproject.toml (现代Python项目)
        pyproject_toml = plugin_dir / "pyproject.toml"
        if pyproject_toml.exists():
            self._parse_pyproject_toml(pyproject_toml, metadata)

        # 推断能力
        metadata.capabilities = self._infer_capabilities(metadata)

        # 检测编程语言
        metadata.languages = self._detect_languages(plugin_dir)

        metadata.status = PluginStatus.SCANNED

        return metadata

    def _infer_plugin_type(self, plugin_id: str) -> PluginType:
        """根据插件ID推断类型"""
        plugin_lower = plugin_id.lower()

        # 知识图谱
        if any(kw in plugin_lower for kw in ["graph", "kg", "knowledge"]):
            return PluginType.KNOWLEDGE_GRAPH

        # 搜索爬虫
        if any(kw in plugin_lower for kw in ["crawl", "spider", "browser", "firecrawl"]):
            return PluginType.SEARCH_CRAWLER

        # RAG记忆
        if any(kw in plugin_lower for kw in ["rag", "mem", "memory", "quivr", "khoj"]):
            return PluginType.RAG_MEMORY

        # NLP处理
        if any(kw in plugin_lower for kw in ["nlp", "hanlp", "pyhanlp"]):
            return PluginType.NLP_PROCESSING

        # 文档转换
        if any(kw in plugin_lower for kw in ["pdf", "markdown", "markitdown", "document"]):
            return PluginType.DOCUMENT_CONVERSION

        # 可视化
        if any(kw in plugin_lower for kw in ["visual", "chart", "graph", "nvd3", "rawgraph", "mind-map"]):
            return PluginType.VISUALIZATION

        # 数据库
        if any(kw in plugin_lower for kw in ["neo4j", "duckdb", "db", "database"]):
            return PluginType.DATABASE

        # 资源库
        if plugin_lower.startswith("awesome-") or "fun" in plugin_lower:
            return PluginType.RESOURCES

        # 工具
        if any(kw in plugin_lower for kw in ["pillow", "exif", "gecco", "transfer"]):
            return PluginType.UTILITY

        return PluginType.OTHER

    def _infer_capabilities(self, metadata: PluginMetadata) -> List[PluginCapability]:
        """
        根据插件类型和元数据推断能力

        Args:
            metadata: 插件元数据

        Returns:
            能力列表
        """
        capabilities = []
        plugin_type = metadata.plugin_type
        plugin_id = metadata.plugin_id.lower()

        # 知识图谱类型
        if plugin_type == PluginType.KNOWLEDGE_GRAPH:
            if "graphrag" in plugin_id:
                capabilities.extend([
                    PluginCapability(
                        capability_id="graph_rag",
                        category="knowledge",
                        description="Graph-based RAG with community detection",
                        input_types=["text", "documents"],
                        output_types=["graph", "entities", "communities"]
                    ),
                    PluginCapability(
                        capability_id="entity_extraction",
                        category="knowledge",
                        description="Extract entities and relationships",
                        input_types=["text"],
                        output_types=["entities", "relations"]
                    )
                ])
            elif "graphiti" in plugin_id:
                capabilities.append(
                    PluginCapability(
                        capability_id="temporal_graph",
                        category="knowledge",
                        description="Temporal knowledge graph construction",
                        input_types=["events", "text"],
                        output_types=["temporal_graph"]
                    )
                )
            elif "cognee" in plugin_id:
                capabilities.append(
                    PluginCapability(
                        capability_id="cognitive_graph",
                        category="knowledge",
                        description="Cognitive knowledge graph",
                        input_types=["text", "documents"],
                        output_types=["graph", "insights"]
                    )
                )
            elif "neo4j" in plugin_id:
                capabilities.append(
                    PluginCapability(
                        capability_id="graph_database",
                        category="storage",
                        description="Neo4j graph database operations",
                        input_types=["cypher", "graph_data"],
                        output_types=["query_results", "graph"]
                    )
                )

        # 搜索爬虫类型
        elif plugin_type == PluginType.SEARCH_CRAWLER:
            if "crawl4ai" in plugin_id:
                capabilities.append(
                    PluginCapability(
                        capability_id="ai_web_crawl",
                        category="search",
                        description="AI-powered web crawling",
                        input_types=["url", "urls"],
                        output_types=["html", "markdown", "structured_data"]
                    )
                )
            elif "firecrawl" in plugin_id:
                capabilities.append(
                    PluginCapability(
                        capability_id="fast_web_crawl",
                        category="search",
                        description="Fast web crawling with API",
                        input_types=["url"],
                        output_types=["markdown", "cleaned_html"]
                    )
                )
            elif "browser-use" in plugin_id:
                capabilities.append(
                    PluginCapability(
                        capability_id="browser_automation",
                        category="search",
                        description="Browser automation for complex scraping",
                        input_types=["url", "actions"],
                        output_types=["html", "screenshots", "data"]
                    )
                )
            elif "gecco" in plugin_id:
                capabilities.append(
                    PluginCapability(
                        capability_id="template_scraping",
                        category="search",
                        description="Template-based web scraping",
                        input_types=["url", "template"],
                        output_types=["structured_data"]
                    )
                )

        # RAG记忆类型
        elif plugin_type == PluginType.RAG_MEMORY:
            if "ragflow" in plugin_id:
                capabilities.extend([
                    PluginCapability(
                        capability_id="enterprise_rag",
                        category="rag",
                        description="Enterprise-grade RAG system",
                        input_types=["documents", "query"],
                        output_types=["answers", "chunks", "sources"]
                    ),
                    PluginCapability(
                        capability_id="document_parsing",
                        category="processing",
                        description="Advanced document parsing",
                        input_types=["pdf", "docx", "html"],
                        output_types=["text", "chunks", "metadata"]
                    )
                ])
            elif "lightrag" in plugin_id:
                capabilities.append(
                    PluginCapability(
                        capability_id="lightweight_rag",
                        category="rag",
                        description="Lightweight RAG implementation",
                        input_types=["text", "query"],
                        output_types=["answers", "context"]
                    )
                )
            elif "mem0" in plugin_id:
                capabilities.append(
                    PluginCapability(
                        capability_id="persistent_memory",
                        category="memory",
                        description="Persistent memory for AI agents",
                        input_types=["interactions", "facts"],
                        output_types=["memory", "context"]
                    )
                )
            elif "quivr" in plugin_id or "khoj" in plugin_id:
                capabilities.append(
                    PluginCapability(
                        capability_id="personal_rag",
                        category="rag",
                        description="Personal knowledge assistant",
                        input_types=["documents", "notes", "query"],
                        output_types=["answers", "sources"]
                    )
                )

        # NLP处理类型
        elif plugin_type == PluginType.NLP_PROCESSING:
            capabilities.extend([
                PluginCapability(
                    capability_id="chinese_nlp",
                    category="nlp",
                    description="Chinese NLP processing",
                    input_types=["text"],
                    output_types=["tokens", "pos", "ner", "dependencies"]
                ),
                PluginCapability(
                    capability_id="word_segmentation",
                    category="nlp",
                    description="Chinese word segmentation",
                    input_types=["text"],
                    output_types=["tokens"]
                )
            ])

        # 文档转换类型
        elif plugin_type == PluginType.DOCUMENT_CONVERSION:
            if "markitdown" in plugin_id:
                capabilities.append(
                    PluginCapability(
                        capability_id="universal_markdown",
                        category="conversion",
                        description="Convert any document to markdown",
                        input_types=["pdf", "docx", "pptx", "xlsx", "html"],
                        output_types=["markdown"]
                    )
                )
            elif "pdf" in plugin_id:
                capabilities.append(
                    PluginCapability(
                        capability_id="pdf_processing",
                        category="conversion",
                        description="Advanced PDF processing",
                        input_types=["pdf"],
                        output_types=["text", "images", "tables", "markdown"]
                    )
                )

        # 可视化类型
        elif plugin_type == PluginType.VISUALIZATION:
            if "mind-map" in plugin_id:
                capabilities.append(
                    PluginCapability(
                        capability_id="mindmap_generation",
                        category="visualization",
                        description="Generate mind maps",
                        input_types=["text", "structure"],
                        output_types=["mindmap", "svg", "png"]
                    )
                )
            elif "nvd3" in plugin_id or "rawgraph" in plugin_id:
                capabilities.append(
                    PluginCapability(
                        capability_id="data_visualization",
                        category="visualization",
                        description="Create data visualizations",
                        input_types=["data", "csv", "json"],
                        output_types=["charts", "graphs", "svg"]
                    )
                )

        # 数据库类型
        elif plugin_type == PluginType.DATABASE:
            if "duckdb" in plugin_id:
                capabilities.append(
                    PluginCapability(
                        capability_id="analytical_database",
                        category="storage",
                        description="In-process analytical database",
                        input_types=["sql", "dataframe"],
                        output_types=["query_results", "tables"]
                    )
                )

        # 工具类型
        elif plugin_type == PluginType.UTILITY:
            if "pillow" in plugin_id:
                capabilities.append(
                    PluginCapability(
                        capability_id="image_processing",
                        category="utility",
                        description="Image processing operations",
                        input_types=["image"],
                        output_types=["image", "thumbnail", "converted"]
                    )
                )
            elif "exif" in plugin_id:
                capabilities.append(
                    PluginCapability(
                        capability_id="exif_extraction",
                        category="utility",
                        description="Extract EXIF metadata from images",
                        input_types=["image"],
                        output_types=["metadata", "exif"]
                    )
                )

        return capabilities

    # ==================== 解析辅助方法 ====================

    def _find_readme(self, plugin_dir: Path) -> Optional[Path]:
        """查找README文件"""
        for name in ["README.md", "README.MD", "readme.md", "README", "README.txt"]:
            readme = plugin_dir / name
            if readme.exists():
                return readme
        return None

    def _extract_description(self, readme_path: Path, max_length: int = 500) -> str:
        """从README提取描述（第一段非标题文本）"""
        try:
            with open(readme_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                description_lines = []
                skip_badges = True

                for line in lines:
                    line = line.strip()

                    # 跳过空行、标题、badge
                    if not line or line.startswith('#') or '[!' in line or '![' in line:
                        if description_lines:  # 遇到第一个空行后停止
                            break
                        continue

                    if skip_badges and ('badge' in line.lower() or 'shield' in line.lower()):
                        continue

                    skip_badges = False
                    description_lines.append(line)

                    if len(' '.join(description_lines)) > max_length:
                        break

                description = ' '.join(description_lines)[:max_length]
                return description if description else "No description available"
        except Exception as e:
            logger.debug(f"Error extracting description from {readme_path}: {e}")
            return "No description available"

    def _parse_package_json(self, package_json: Path, metadata: PluginMetadata):
        """解析package.json"""
        try:
            with open(package_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
                metadata.version = data.get('version', 'unknown')
                if not metadata.description and 'description' in data:
                    metadata.description = data['description']
                if 'dependencies' in data:
                    metadata.dependencies = list(data['dependencies'].keys())
                metadata.metadata['package_json'] = True
        except Exception as e:
            logger.debug(f"Error parsing package.json for {metadata.plugin_id}: {e}")

    def _parse_setup_py(self, setup_py: Path, metadata: PluginMetadata):
        """解析setup.py（简单提取）"""
        try:
            with open(setup_py, 'r', encoding='utf-8') as f:
                content = f.read()
                # 简单提取version
                if 'version=' in content:
                    import re
                    match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
                    if match:
                        metadata.version = match.group(1)
                metadata.metadata['setup_py'] = True
        except Exception as e:
            logger.debug(f"Error parsing setup.py for {metadata.plugin_id}: {e}")

    def _parse_pyproject_toml(self, pyproject_toml: Path, metadata: PluginMetadata):
        """解析pyproject.toml"""
        try:
            # 简单解析（避免引入toml库）
            with open(pyproject_toml, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'version =' in content:
                    import re
                    match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
                    if match:
                        metadata.version = match.group(1)
                metadata.metadata['pyproject_toml'] = True
        except Exception as e:
            logger.debug(f"Error parsing pyproject.toml for {metadata.plugin_id}: {e}")

    def _detect_languages(self, plugin_dir: Path) -> List[str]:
        """检测编程语言"""
        languages = set()

        # 检查常见文件后缀
        for file in plugin_dir.rglob('*'):
            if not file.is_file():
                continue

            suffix = file.suffix.lower()
            if suffix in ['.py']:
                languages.add('Python')
            elif suffix in ['.js', '.jsx', '.ts', '.tsx']:
                languages.add('JavaScript/TypeScript')
            elif suffix in ['.go']:
                languages.add('Go')
            elif suffix in ['.rs']:
                languages.add('Rust')
            elif suffix in ['.java']:
                languages.add('Java')
            elif suffix in ['.cpp', '.cc', '.cxx', '.c']:
                languages.add('C/C++')

        return list(languages)

    # ==================== 注册与索引 ====================

    def _register_plugin(self, metadata: PluginMetadata):
        """注册插件到内部字典"""
        self._plugins[metadata.plugin_id] = metadata
        logger.debug(f"Registered plugin: {metadata.plugin_id} ({metadata.plugin_type.value})")

    def _build_indexes(self):
        """构建能力索引和类型索引"""
        logger.info("Building capability and type indexes...")

        # 清空现有索引
        self._capability_index.clear()
        self._type_index.clear()

        # 构建类型索引
        for plugin_id, metadata in self._plugins.items():
            plugin_type = metadata.plugin_type
            if plugin_type not in self._type_index:
                self._type_index[plugin_type] = []
            self._type_index[plugin_type].append(plugin_id)

        # 构建能力索引
        for plugin_id, metadata in self._plugins.items():
            for capability in metadata.capabilities:
                cap_id = capability.capability_id

                if cap_id not in self._capability_index:
                    self._capability_index[cap_id] = CapabilityIndex(
                        capability_id=cap_id,
                        category=capability.category
                    )

                self._capability_index[cap_id].providers.append(plugin_id)

        # 设置优先级排序（基于插件流行度/质量的启发式规则）
        for cap_id, index in self._capability_index.items():
            index.priority_order = self._sort_by_priority(index.providers, cap_id)

        logger.info(f"Built indexes: {len(self._capability_index)} capabilities, {len(self._type_index)} types")

    def _sort_by_priority(self, provider_ids: List[str], capability_id: str) -> List[str]:
        """
        根据优先级排序插件

        启发式规则:
        1. graphrag > graphiti > cognee (知识图谱)
        2. crawl4ai > firecrawl > browser-use (爬虫)
        3. ragflow > LightRAG > mem0 (RAG)
        4. markitdown > PDF-Guru (文档转换)
        """
        priority_map = {
            # 知识图谱
            "graphrag": 10,
            "graphiti": 9,
            "cognee": 8,

            # 爬虫
            "crawl4ai": 10,
            "firecrawl": 9,
            "browser-use": 8,

            # RAG
            "ragflow": 10,
            "LightRAG": 9,
            "mem0": 8,

            # 文档转换
            "markitdown": 10,
            "PDF-Guru": 9,

            # NLP
            "HanLP": 10,
            "pyhanlp": 9,
        }

        return sorted(provider_ids, key=lambda pid: priority_map.get(pid, 5), reverse=True)

    # ==================== 查询接口 ====================

    def get_plugin(self, plugin_id: str) -> Optional[PluginMetadata]:
        """获取插件元数据"""
        return self._plugins.get(plugin_id)

    def get_all_plugins(self) -> Dict[str, PluginMetadata]:
        """获取所有插件"""
        return self._plugins.copy()

    def get_plugins_by_type(self, plugin_type: PluginType) -> List[PluginMetadata]:
        """根据类型获取插件"""
        plugin_ids = self._type_index.get(plugin_type, [])
        return [self._plugins[pid] for pid in plugin_ids]

    def get_plugins_by_capability(self, capability_id: str) -> List[PluginMetadata]:
        """根据能力获取插件（按优先级排序）"""
        index = self._capability_index.get(capability_id)
        if not index:
            return []

        return [self._plugins[pid] for pid in index.priority_order if pid in self._plugins]

    def get_capability_index(self) -> Dict[str, CapabilityIndex]:
        """获取能力索引"""
        return self._capability_index.copy()

    def search_plugins(self, keyword: str) -> List[PluginMetadata]:
        """搜索插件（按名称或描述）"""
        keyword_lower = keyword.lower()
        results = []

        for metadata in self._plugins.values():
            if (keyword_lower in metadata.plugin_id.lower() or
                keyword_lower in metadata.description.lower()):
                results.append(metadata)

        return results

    # ==================== 导出与统计 ====================

    def export_registry(self, output_path: str):
        """导出注册表到JSON文件"""
        data = {
            "total_plugins": len(self._plugins),
            "scan_time": datetime.now().isoformat(),
            "plugins": {pid: metadata.to_dict() for pid, metadata in self._plugins.items()},
            "capability_index": {
                cap_id: {
                    "category": index.category,
                    "providers": index.providers,
                    "priority_order": index.priority_order
                }
                for cap_id, index in self._capability_index.items()
            },
            "type_index": {
                ptype.value: plugin_ids
                for ptype, plugin_ids in self._type_index.items()
            }
        }

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"Registry exported to {output_path}")

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = {
            "total_plugins": len(self._plugins),
            "by_type": {},
            "by_status": {},
            "total_capabilities": len(self._capability_index),
            "by_language": {}
        }

        # 按类型统计
        for ptype, plugin_ids in self._type_index.items():
            stats["by_type"][ptype.value] = len(plugin_ids)

        # 按状态统计
        for metadata in self._plugins.values():
            status = metadata.status.value
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1

        # 按语言统计
        for metadata in self._plugins.values():
            for lang in metadata.languages:
                stats["by_language"][lang] = stats["by_language"].get(lang, 0) + 1

        return stats

    def print_summary(self):
        """打印注册表摘要"""
        stats = self.get_statistics()

        print("\n" + "="*60)
        print("Plugin Registry Summary")
        print("="*60)
        print(f"Total Plugins: {stats['total_plugins']}")
        print(f"Total Capabilities: {stats['total_capabilities']}")

        print("\nBy Type:")
        for ptype, count in sorted(stats['by_type'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {ptype:25s}: {count}")

        print("\nBy Language:")
        for lang, count in sorted(stats['by_language'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {lang:25s}: {count}")

        print("\nTop Capabilities:")
        sorted_caps = sorted(
            self._capability_index.items(),
            key=lambda x: len(x[1].providers),
            reverse=True
        )[:10]

        for cap_id, index in sorted_caps:
            providers_str = ", ".join(index.priority_order[:3])
            print(f"  {cap_id:30s}: {len(index.providers)} providers ({providers_str})")

        print("="*60 + "\n")


# ==================== 工厂函数 ====================

_registry_instance: Optional[PluginRegistry] = None

def get_plugin_registry(repos_dir: Optional[str] = None) -> PluginRegistry:
    """
    获取插件注册表单例

    Args:
        repos_dir: 插件仓库目录（可选，默认使用标准路径）

    Returns:
        PluginRegistry实例
    """
    global _registry_instance

    if _registry_instance is None:
        if repos_dir:
            _registry_instance = PluginRegistry(repos_dir)
        else:
            _registry_instance = PluginRegistry()

    return _registry_instance


# ==================== CLI入口 ====================

if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 创建注册表并扫描
    registry = PluginRegistry()
    registry.scan_all_plugins()

    # 打印摘要
    registry.print_summary()

    # 导出到JSON
    output_path = "/Users/alwan/FieldMind/backend/plugin_registry.json"
    registry.export_registry(output_path)

    print(f"\nRegistry data exported to: {output_path}")
