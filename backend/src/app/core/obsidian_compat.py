"""
Obsidian兼容层 - 核心数据结构

使FieldMind原生支持Obsidian的所有数据格式和功能：
- Markdown作为第一公民
- Frontmatter元数据
- 双向链接 [[]]
- 标签系统 #tag
- 块引用 ^blockid
- 嵌入 ![[]]
"""
import re
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from datetime import datetime
import yaml
import hashlib


class MarkdownNote:
    """
    Obsidian兼容的Markdown笔记

    数据库中直接存储完整的Markdown内容，而不是分散的字段
    """

    def __init__(self, content: str, path: Optional[str] = None):
        self.raw_content = content
        self.path = path
        self._frontmatter = None
        self._body = None
        self._parse()

    def _parse(self):
        """解析Markdown内容"""
        # 解析frontmatter
        if self.raw_content.startswith('---'):
            parts = self.raw_content.split('---', 2)
            if len(parts) >= 3:
                try:
                    self._frontmatter = yaml.safe_load(parts[1])
                    self._body = parts[2].strip()
                except yaml.YAMLError:
                    self._frontmatter = {}
                    self._body = self.raw_content
            else:
                self._frontmatter = {}
                self._body = self.raw_content
        else:
            self._frontmatter = {}
            self._body = self.raw_content

    @property
    def frontmatter(self) -> Dict[str, Any]:
        """获取frontmatter元数据"""
        return self._frontmatter or {}

    @property
    def body(self) -> str:
        """获取正文内容"""
        return self._body or self.raw_content

    @property
    def title(self) -> str:
        """提取标题"""
        # 优先从frontmatter获取
        if 'title' in self.frontmatter:
            return self.frontmatter['title']

        # 从第一个H1标题获取
        match = re.search(r'^#\s+(.+)$', self.body, re.MULTILINE)
        if match:
            return match.group(1).strip()

        # 从文件名获取
        if self.path:
            return Path(self.path).stem

        return "Untitled"

    @property
    def tags(self) -> List[str]:
        """提取所有标签"""
        tags = set()

        # 从frontmatter获取
        if 'tags' in self.frontmatter:
            fm_tags = self.frontmatter['tags']
            if isinstance(fm_tags, list):
                tags.update(fm_tags)
            elif isinstance(fm_tags, str):
                tags.add(fm_tags)

        # 从正文中提取 #tag
        inline_tags = re.findall(r'#([a-zA-Z0-9_/-]+)', self.body)
        tags.update(inline_tags)

        return list(tags)

    def extract_wikilinks(self) -> List[Dict[str, str]]:
        """
        提取所有双向链接 [[link]]

        返回格式：
        [
            {"target": "note name", "alias": "display text", "type": "link"},
            {"target": "note name", "alias": None, "type": "embed"}
        ]
        """
        links = []

        # 普通链接 [[target]] 或 [[target|alias]]
        pattern = r'(?<!!)\[\[([^\]|]+)(?:\|([^\]]+))?\]\]'
        for match in re.finditer(pattern, self.body):
            links.append({
                "target": match.group(1).strip(),
                "alias": match.group(2).strip() if match.group(2) else None,
                "type": "link"
            })

        # 嵌入 ![[target]]
        pattern = r'!\[\[([^\]|]+)(?:\|([^\]]+))?\]\]'
        for match in re.finditer(pattern, self.body):
            links.append({
                "target": match.group(1).strip(),
                "alias": match.group(2).strip() if match.group(2) else None,
                "type": "embed"
            })

        return links

    def extract_block_refs(self) -> List[str]:
        """
        提取所有块引用标记 ^blockid
        """
        pattern = r'\^([a-zA-Z0-9-]+)$'
        blocks = []
        for line in self.body.split('\n'):
            match = re.search(pattern, line.strip())
            if match:
                blocks.append(match.group(1))
        return blocks

    def extract_external_links(self) -> List[Dict[str, str]]:
        """提取外部链接 [text](url)"""
        pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        links = []
        for match in re.finditer(pattern, self.body):
            links.append({
                "text": match.group(1),
                "url": match.group(2)
            })
        return links

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "title": self.title,
            "content": self.raw_content,
            "frontmatter": self.frontmatter,
            "body": self.body,
            "tags": self.tags,
            "wikilinks": self.extract_wikilinks(),
            "block_refs": self.extract_block_refs(),
            "external_links": self.extract_external_links()
        }

    @staticmethod
    def create(title: str, content: str, metadata: Optional[Dict] = None) -> 'MarkdownNote':
        """创建新的Markdown笔记"""
        frontmatter_str = ""
        if metadata:
            frontmatter_str = "---\n" + yaml.dump(metadata, allow_unicode=True) + "---\n\n"

        full_content = f"{frontmatter_str}# {title}\n\n{content}"
        return MarkdownNote(full_content)


class WikiLinkResolver:
    """
    双向链接解析器

    维护笔记之间的链接关系图
    """

    def __init__(self):
        self.notes: Dict[str, MarkdownNote] = {}
        self.link_graph: Dict[str, List[str]] = {}  # source -> [targets]
        self.backlink_graph: Dict[str, List[str]] = {}  # target -> [sources]

    def add_note(self, note_id: str, note: MarkdownNote):
        """添加笔记到图中"""
        self.notes[note_id] = note

        # 构建链接图
        links = note.extract_wikilinks()
        targets = [link['target'] for link in links]
        self.link_graph[note_id] = targets

        # 更新反向链接
        for target in targets:
            if target not in self.backlink_graph:
                self.backlink_graph[target] = []
            self.backlink_graph[target].append(note_id)

    def resolve_link(self, source_id: str, target_name: str) -> Optional[str]:
        """
        解析链接目标

        支持：
        - 完整匹配
        - 部分匹配
        - 别名匹配
        """
        # 完整匹配
        for note_id, note in self.notes.items():
            if note.title == target_name:
                return note_id

        # 部分匹配（忽略大小写）
        target_lower = target_name.lower()
        for note_id, note in self.notes.items():
            if target_lower in note.title.lower():
                return note_id

        return None

    def get_backlinks(self, note_id: str) -> List[str]:
        """获取指向该笔记的所有链接"""
        note = self.notes.get(note_id)
        if not note:
            return []

        return self.backlink_graph.get(note.title, [])

    def get_outgoing_links(self, note_id: str) -> List[str]:
        """获取该笔记指向的所有链接"""
        return self.link_graph.get(note_id, [])

    def get_unresolved_links(self, note_id: str) -> List[str]:
        """获取无法解析的链接"""
        unresolved = []
        note = self.notes.get(note_id)
        if not note:
            return []

        for link in note.extract_wikilinks():
            if not self.resolve_link(note_id, link['target']):
                unresolved.append(link['target'])

        return unresolved

    def build_graph_data(self) -> Dict[str, Any]:
        """
        构建可视化图数据

        返回格式适用于前端图可视化库（如D3.js, Cytoscape.js）
        """
        nodes = []
        edges = []

        # 构建节点
        for note_id, note in self.notes.items():
            nodes.append({
                "id": note_id,
                "label": note.title,
                "tags": note.tags,
                "type": note.frontmatter.get('type', 'note')
            })

        # 构建边
        edge_id = 0
        for source_id, targets in self.link_graph.items():
            for target_name in targets:
                target_id = self.resolve_link(source_id, target_name)
                if target_id:
                    edges.append({
                        "id": f"e{edge_id}",
                        "source": source_id,
                        "target": target_id
                    })
                    edge_id += 1

        return {
            "nodes": nodes,
            "edges": edges
        }


class BlockReference:
    """
    块引用处理器

    支持 ^blockid 引用
    """

    @staticmethod
    def generate_block_id() -> str:
        """生成唯一的块ID"""
        return hashlib.md5(
            f"{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:8]

    @staticmethod
    def add_block_ref(text: str) -> Tuple[str, str]:
        """
        为文本块添加引用标记

        返回: (带标记的文本, 块ID)
        """
        block_id = BlockReference.generate_block_id()
        marked_text = f"{text} ^{block_id}"
        return marked_text, block_id

    @staticmethod
    def extract_block(content: str, block_id: str) -> Optional[str]:
        """从内容中提取指定的块"""
        pattern = rf'(.+?)\s+\^{block_id}$'
        for line in content.split('\n'):
            match = re.search(pattern, line)
            if match:
                return match.group(1).strip()
        return None

    @staticmethod
    def resolve_block_ref(content: str, ref: str) -> Optional[str]:
        """
        解析块引用
        格式: [[note name#^blockid]]
        """
        if '#^' in ref:
            parts = ref.split('#^')
            note_name = parts[0]
            block_id = parts[1]
            # TODO: 需要从数据库查询对应笔记
            return f"Block reference: {note_name}#^{block_id}"
        return None


class ObsidianDataStore:
    """
    Obsidian数据存储

    在FieldMind数据库中以Obsidian原生格式存储数据
    """

    def __init__(self, db_session):
        self.db = db_session
        self.resolver = WikiLinkResolver()

    def create_note(self, title: str, content: str, metadata: Optional[Dict] = None) -> MarkdownNote:
        """创建Obsidian兼容的笔记"""
        note = MarkdownNote.create(title, content, metadata)
        return note

    def parse_note(self, content: str, path: Optional[str] = None) -> MarkdownNote:
        """解析已有的笔记"""
        return MarkdownNote(content, path)

    def build_link_graph(self, notes: List[MarkdownNote]):
        """构建所有笔记的链接图"""
        for i, note in enumerate(notes):
            self.resolver.add_note(str(i), note)

    def get_graph_data(self) -> Dict[str, Any]:
        """获取可视化图数据"""
        return self.resolver.build_graph_data()
