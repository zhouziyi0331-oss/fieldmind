"""
Step 2: 结构分析服务
Structure Analysis Service

功能：
1. 多维特征提取（格式、语言、语义）
2. 篇章结构识别（标题、章节、段落、对话）
3. 层次构建（语义连贯性）
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)


class StructureType(str, Enum):
    """结构类型"""
    DOCUMENT = "document"  # 文档根节点
    CHAPTER = "chapter"  # 章
    SECTION = "section"  # 节
    SUBSECTION = "subsection"  # 小节
    PARAGRAPH = "paragraph"  # 段落
    DIALOGUE = "dialogue"  # 对话
    LIST = "list"  # 列表
    TABLE = "table"  # 表格
    CODE = "code"  # 代码块
    QUOTE = "quote"  # 引用


class LanguageType(str, Enum):
    """语言类型"""
    CHINESE = "chinese"
    ENGLISH = "english"
    MIXED = "mixed"
    OTHER = "other"


@dataclass
class StructureNode:
    """结构节点"""
    id: str
    type: StructureType
    title: Optional[str] = None
    content: str = ""
    level: int = 0  # 层级深度
    order: int = 0  # 同级顺序
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)

    # 特征
    features: Dict[str, Any] = field(default_factory=dict)

    # 元数据
    start_position: int = 0
    end_position: int = 0
    line_start: int = 0
    line_end: int = 0


@dataclass
class StructureTree:
    """结构树"""
    root: StructureNode
    nodes: Dict[str, StructureNode] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def flatten(self) -> List[StructureNode]:
        """扁平化树结构"""
        result = []

        def traverse(node_id: str):
            if node_id in self.nodes:
                node = self.nodes[node_id]
                result.append(node)
                for child_id in node.children_ids:
                    traverse(child_id)

        traverse(self.root.id)
        return result


class FormatFeatureExtractor:
    """格式特征提取器"""

    def extract(self, text: str) -> Dict[str, Any]:
        """提取格式特征"""
        lines = text.split('\n')

        features = {
            'total_lines': len(lines),
            'total_chars': len(text),
            'avg_line_length': sum(len(l) for l in lines) / len(lines) if lines else 0,
            'empty_lines': sum(1 for l in lines if not l.strip()),
            'has_numbering': self._detect_numbering(lines),
            'has_bullets': self._detect_bullets(lines),
            'indentation_levels': self._detect_indentation(lines),
            'dialogue_markers': self._detect_dialogue_markers(text),
        }

        return features

    def _detect_numbering(self, lines: List[str]) -> bool:
        """检测编号"""
        patterns = [
            r'^\d+[\.、]',  # 1. 或 1、
            r'^第[一二三四五六七八九十百千万]+[章节条]',  # 第一章
            r'^\([一二三四五]\)',  # (一)
            r'^[IVXLCDM]+\.',  # 罗马数字
        ]

        count = 0
        for line in lines:
            line = line.strip()
            for pattern in patterns:
                if re.match(pattern, line):
                    count += 1
                    break

        return count >= 3

    def _detect_bullets(self, lines: List[str]) -> bool:
        """检测项目符号"""
        bullet_chars = ['•', '·', '-', '*', '○', '●', '■', '□']
        count = sum(1 for l in lines if any(l.strip().startswith(c) for c in bullet_chars))
        return count >= 3

    def _detect_indentation(self, lines: List[str]) -> int:
        """检测缩进层级数"""
        indents = set()
        for line in lines:
            if line and line[0] == ' ':
                spaces = len(line) - len(line.lstrip())
                indents.add(spaces)
        return len(indents)

    def _detect_dialogue_markers(self, text: str) -> int:
        """检测对话标记数量"""
        markers = ['"', '"', '"', '「', '」', '『', '』']
        count = sum(text.count(m) for m in markers)
        return count


class LanguageFeatureExtractor:
    """语言特征提取器"""

    def extract(self, text: str) -> Dict[str, Any]:
        """提取语言特征"""
        chinese_chars = len(re.findall(r'[一-鿿]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        total_chars = len(text.strip())

        chinese_ratio = chinese_chars / total_chars if total_chars else 0
        english_ratio = english_chars / total_chars if total_chars else 0

        # 判断语言类型
        if chinese_ratio > 0.5:
            language = LanguageType.CHINESE
        elif english_ratio > 0.5:
            language = LanguageType.ENGLISH
        elif chinese_ratio > 0.2 and english_ratio > 0.2:
            language = LanguageType.MIXED
        else:
            language = LanguageType.OTHER

        features = {
            'language': language.value,
            'chinese_ratio': chinese_ratio,
            'english_ratio': english_ratio,
            'chinese_chars': chinese_chars,
            'english_chars': english_chars,
            'sentence_count': self._count_sentences(text),
            'word_count': self._count_words(text, language),
        }

        return features

    def _count_sentences(self, text: str) -> int:
        """句子计数"""
        separators = ['。', '！', '？', '.', '!', '?', '\n']
        count = 0
        for sep in separators:
            count += text.count(sep)
        return max(count, 1)

    def _count_words(self, text: str, language: LanguageType) -> int:
        """词汇计数"""
        if language == LanguageType.CHINESE:
            # 中文按字符数
            return len(re.findall(r'[一-鿿]', text))
        else:
            # 英文按单词数
            return len(re.findall(r'\b\w+\b', text))


class SemanticFeatureExtractor:
    """语义特征提取器"""

    def extract(self, text: str) -> Dict[str, Any]:
        """提取语义特征"""
        features = {
            'topic_keywords': self._extract_keywords(text),
            'entity_density': self._calculate_entity_density(text),
            'coherence_score': self._calculate_coherence(text),
            'formality_score': self._calculate_formality(text),
        }

        return features

    def _extract_keywords(self, text: str, top_k: int = 10) -> List[str]:
        """提取关键词（简化版）"""
        # 实际应使用 TF-IDF 或其他算法
        # 这里简化为提取高频词
        words = re.findall(r'[一-鿿]{2,}', text)
        from collections import Counter
        freq = Counter(words)
        return [word for word, _ in freq.most_common(top_k)]

    def _calculate_entity_density(self, text: str) -> float:
        """计算实体密度（人名、地名等）"""
        # 简单的启发式方法
        person_markers = ['先生', '女士', '老师', '教授', '博士', '先生', '同志']
        place_markers = ['市', '省', '县', '区', '镇', '村', '街道', '路']

        entity_count = 0
        for marker in person_markers + place_markers:
            entity_count += text.count(marker)

        total_chars = len(text)
        return entity_count / (total_chars / 100) if total_chars else 0

    def _calculate_coherence(self, text: str) -> float:
        """计算连贯性（基于连接词）"""
        connectors = ['因此', '所以', '但是', '然而', '而且', '并且', '首先', '其次', '最后', '总之']
        connector_count = sum(text.count(c) for c in connectors)
        sentences = max(len(re.split(r'[。！？]', text)), 1)
        return min(connector_count / sentences, 1.0)

    def _calculate_formality(self, text: str) -> float:
        """计算正式度"""
        formal_markers = ['根据', '依据', '鉴于', '综上所述', '据此', '由此可见']
        informal_markers = ['呀', '啊', '呢', '哦', '嘛', '吧']

        formal_count = sum(text.count(m) for m in formal_markers)
        informal_count = sum(text.count(m) for m in informal_markers)

        if formal_count + informal_count == 0:
            return 0.5

        return formal_count / (formal_count + informal_count)


class TitleDetector:
    """标题检测器"""

    def detect(self, lines: List[str]) -> List[Dict[str, Any]]:
        """检测标题"""
        titles = []

        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            title_info = self._is_title(line, i, lines)
            if title_info:
                titles.append(title_info)

        return titles

    def _is_title(self, line: str, line_num: int, all_lines: List[str]) -> Optional[Dict[str, Any]]:
        """判断是否为标题"""
        # 规则1：章节编号
        chapter_pattern = r'^第[一二三四五六七八九十百千万\d]+[章节]'
        if re.match(chapter_pattern, line):
            return {
                'line': line_num,
                'text': line,
                'level': 1,
                'type': 'chapter',
                'confidence': 1.0
            }

        # 规则2：数字编号
        number_pattern = r'^(\d+\.)+\d*\s+'
        if re.match(number_pattern, line):
            dots = line.split()[0].count('.')
            return {
                'line': line_num,
                'text': line,
                'level': min(dots + 1, 4),
                'type': 'section',
                'confidence': 0.9
            }

        # 规则3：短行 + 后续有内容
        if len(line) < 30 and line_num < len(all_lines) - 1:
            next_line = all_lines[line_num + 1].strip()
            if len(next_line) > len(line):
                return {
                    'line': line_num,
                    'text': line,
                    'level': 2,
                    'type': 'section',
                    'confidence': 0.6
                }

        # 规则4：全大写（英文）
        if line.isupper() and len(line.split()) <= 10:
            return {
                'line': line_num,
                'text': line,
                'level': 2,
                'type': 'section',
                'confidence': 0.8
            }

        return None


class SectionDetector:
    """章节检测器"""

    def detect(self, lines: List[str], titles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """检测章节"""
        sections = []

        title_lines = {t['line'] for t in titles}

        current_section = {
            'start': 0,
            'end': 0,
            'type': 'section',
            'content_lines': []
        }

        for i, line in enumerate(lines):
            if i in title_lines:
                # 结束当前章节
                if current_section['content_lines']:
                    current_section['end'] = i - 1
                    sections.append(current_section.copy())

                # 开始新章节
                current_section = {
                    'start': i,
                    'end': i,
                    'type': 'section',
                    'content_lines': []
                }
            else:
                current_section['content_lines'].append(i)

        # 最后一个章节
        if current_section['content_lines']:
            current_section['end'] = len(lines) - 1
            sections.append(current_section)

        return sections


class ParagraphDetector:
    """段落检测器"""

    def detect(self, lines: List[str]) -> List[Dict[str, Any]]:
        """检测段落"""
        paragraphs = []
        current_para = []

        for i, line in enumerate(lines):
            line = line.strip()

            if not line:
                # 空行分隔段落
                if current_para:
                    paragraphs.append({
                        'lines': current_para,
                        'type': 'paragraph',
                        'start': current_para[0],
                        'end': current_para[-1]
                    })
                    current_para = []
            else:
                current_para.append(i)

        # 最后一个段落
        if current_para:
            paragraphs.append({
                'lines': current_para,
                'type': 'paragraph',
                'start': current_para[0],
                'end': current_para[-1]
            })

        return paragraphs


class DialogueDetector:
    """对话检测器"""

    def detect(self, text: str) -> List[Dict[str, Any]]:
        """检测对话"""
        dialogues = []

        # 检测引号对话
        quote_patterns = [
            (r'"([^"]+)"', '"'),
            (r'"([^"]+)"', '"'),
            (r'「([^」]+)」', '「'),
            (r'『([^』]+)』', '『'),
        ]

        for pattern, marker in quote_patterns:
            for match in re.finditer(pattern, text):
                dialogues.append({
                    'text': match.group(1),
                    'position': match.start(),
                    'marker': marker,
                    'type': 'dialogue'
                })

        # 检测冒号对话（"某某说："）
        colon_pattern = r'(.{1,10})[说道讲问答][:：]([^。！？\n]{5,})'
        for match in re.finditer(colon_pattern, text):
            dialogues.append({
                'speaker': match.group(1),
                'text': match.group(2),
                'position': match.start(),
                'type': 'dialogue_colon'
            })

        return dialogues


class HierarchyBuilder:
    """层次构建器"""

    def build(
        self,
        text: str,
        titles: List[Dict[str, Any]],
        sections: List[Dict[str, Any]],
        paragraphs: List[Dict[str, Any]]
    ) -> StructureTree:
        """构建层次结构树"""
        lines = text.split('\n')

        # 创建根节点
        root = StructureNode(
            id="root",
            type=StructureType.DOCUMENT,
            title="Document",
            level=0
        )

        nodes = {"root": root}

        # 构建章节树
        for i, title in enumerate(titles):
            node_id = f"title_{i}"
            node = StructureNode(
                id=node_id,
                type=StructureType.CHAPTER if title['level'] == 1 else StructureType.SECTION,
                title=title['text'],
                level=title['level'],
                order=i,
                parent_id="root",
                line_start=title['line'],
                line_end=title['line']
            )
            nodes[node_id] = node
            root.children_ids.append(node_id)

        # 构建段落节点
        for i, para in enumerate(paragraphs):
            node_id = f"para_{i}"
            para_lines = para['lines']
            content = '\n'.join(lines[j] for j in para_lines if j < len(lines))

            node = StructureNode(
                id=node_id,
                type=StructureType.PARAGRAPH,
                content=content,
                level=2,
                order=i,
                parent_id="root",  # 简化版，实际应关联到对应章节
                line_start=para['start'],
                line_end=para['end']
            )
            nodes[node_id] = node
            root.children_ids.append(node_id)

        return StructureTree(root=root, nodes=nodes)


class StructureAnalysisService:
    """结构分析服务"""

    def __init__(self):
        self.format_extractor = FormatFeatureExtractor()
        self.language_extractor = LanguageFeatureExtractor()
        self.semantic_extractor = SemanticFeatureExtractor()
        self.title_detector = TitleDetector()
        self.section_detector = SectionDetector()
        self.paragraph_detector = ParagraphDetector()
        self.dialogue_detector = DialogueDetector()
        self.hierarchy_builder = HierarchyBuilder()

    async def analyze(self, text: str) -> StructureTree:
        """
        结构分析

        Args:
            text: 清洗后的文本

        Returns:
            结构树
        """
        logger.info(f"开始结构分析，文本长度: {len(text)} 字符")

        lines = text.split('\n')

        # 1. 多维特征提取（并行）
        format_features, language_features, semantic_features = await asyncio.gather(
            asyncio.to_thread(self.format_extractor.extract, text),
            asyncio.to_thread(self.language_extractor.extract, text),
            asyncio.to_thread(self.semantic_extractor.extract, text)
        )
        logger.info(f"✅ 特征提取完成")

        # 2. 结构检测（并行）
        titles = await asyncio.to_thread(self.title_detector.detect, lines)
        paragraphs = await asyncio.to_thread(self.paragraph_detector.detect, lines)
        dialogues = await asyncio.to_thread(self.dialogue_detector.detect, text)
        logger.info(f"✅ 结构检测完成：标题 {len(titles)}, 段落 {len(paragraphs)}, 对话 {len(dialogues)}")

        # 3. 章节检测
        sections = await asyncio.to_thread(self.section_detector.detect, lines, titles)
        logger.info(f"✅ 章节检测完成：{len(sections)} 个章节")

        # 4. 构建层次结构
        tree = await asyncio.to_thread(
            self.hierarchy_builder.build,
            text, titles, sections, paragraphs
        )

        # 5. 添加元数据
        tree.metadata = {
            'format_features': format_features,
            'language_features': language_features,
            'semantic_features': semantic_features,
            'title_count': len(titles),
            'section_count': len(sections),
            'paragraph_count': len(paragraphs),
            'dialogue_count': len(dialogues),
        }

        logger.info(f"✅ 结构分析完成，共 {len(tree.nodes)} 个节点")

        return tree
