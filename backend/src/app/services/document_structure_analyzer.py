"""
文档结构分析器 - Document Structure Analyzer

分析文档的层级结构（章节、段落、小节）
为每个文本块提供结构上下文

核心功能：
1. 检测文档层级（标题、章节、段落）
2. 构建文档树结构
3. 为每个文本块标注所属章节
4. 识别文档语义区域（引言、正文、结论等）
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ElementType(str, Enum):
    """文档元素类型"""
    TITLE = "title"              # 文档标题
    HEADING_1 = "heading_1"      # 一级标题
    HEADING_2 = "heading_2"      # 二级标题
    HEADING_3 = "heading_3"      # 三级标题
    HEADING_4 = "heading_4"      # 四级标题
    PARAGRAPH = "paragraph"      # 普通段落
    LIST_ITEM = "list_item"      # 列表项
    TABLE = "table"              # 表格
    CODE = "code"                # 代码块
    QUOTE = "quote"              # 引用
    FOOTNOTE = "footnote"        # 脚注


@dataclass
class DocumentElement:
    """文档元素"""
    type: ElementType
    text: str
    level: int  # 层级（0=根，1=一级标题，2=二级标题...）
    start_pos: int
    end_pos: int
    parent_id: Optional[str] = None
    element_id: Optional[str] = None
    children: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "text": self.text,
            "level": self.level,
            "start_pos": self.start_pos,
            "end_pos": self.end_pos,
            "parent_id": self.parent_id,
            "element_id": self.element_id,
            "children": self.children,
            "metadata": self.metadata
        }


@dataclass
class DocumentStructure:
    """文档结构"""
    elements: List[DocumentElement] = field(default_factory=list)
    hierarchy: Dict[str, DocumentElement] = field(default_factory=dict)
    sections: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_element(self, element_id: str) -> Optional[DocumentElement]:
        """根据ID获取元素"""
        return self.hierarchy.get(element_id)

    def get_parent_chain(self, element_id: str) -> List[DocumentElement]:
        """获取元素的父级链"""
        chain = []
        current = self.get_element(element_id)

        while current and current.parent_id:
            parent = self.get_element(current.parent_id)
            if parent:
                chain.insert(0, parent)
                current = parent
            else:
                break

        return chain

    def to_dict(self) -> Dict[str, Any]:
        return {
            "elements": [elem.to_dict() for elem in self.elements],
            "sections": self.sections,
            "metadata": self.metadata
        }


class DocumentStructureAnalyzer:
    """
    文档结构分析器

    支持多种文档格式：
    - 中文文档（章节、小节）
    - Markdown（# 标题层级）
    - 学术论文（摘要、引言、方法、结论）
    - 口述访谈（问答结构）
    """
    def __init__(self, use_workflow_engine: bool = True):

        # 中文章节模式
        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.chinese_heading_patterns = [
            # 第一章、第二节、第三部分
            (r'^第[一二三四五六七八九十百千]+[章节部篇](.*?)$', 1),
            (r'^[一二三四五六七八九十百千]+[、\.\s](.*?)$', 2),
            (r'^\d+[、\.\s](.*?)$', 2),
            (r'^\d+\.\d+[、\.\s](.*?)$', 3),
            (r'^\d+\.\d+\.\d+[、\.\s](.*?)$', 4),
        ]

        # Markdown 标题模式
        self.markdown_heading_pattern = r'^(#{1,6})\s+(.+)$'

        # 学术论文章节模式
        self.academic_sections = {
            "摘要": 1, "abstract": 1,
            "引言": 1, "introduction": 1, "背景": 1,
            "文献综述": 1, "literature review": 1,
            "方法": 1, "methodology": 1, "methods": 1,
            "结果": 1, "results": 1,
            "讨论": 1, "discussion": 1,
            "结论": 1, "conclusion": 1, "总结": 1,
            "参考文献": 1, "references": 1,
            "附录": 1, "appendix": 1
        }

        # 访谈模式
        self.interview_pattern = r'^([问答QA访][:：]|Q[:：]|A[:：])'

        logger.info("✅ 文档结构分析器初始化完成")

    def analyze(
        self,
        text: str,
        file_type: str = "text",
        hint: Optional[str] = None
    ) -> DocumentStructure:
        """
        分析文档结构

        Args:
            text: 文档文本
            file_type: 文件类型（text, markdown, academic, interview）
            hint: 提示信息（如 "markdown", "academic", "interview"）

        Returns:
            DocumentStructure
        """
        logger.info(f"📖 开始分析文档结构 (类型: {file_type}, 提示: {hint})")

        structure = DocumentStructure()

        # 根据类型选择分析方法
        if file_type == "markdown" or hint == "markdown":
            structure = self._analyze_markdown(text)
        elif file_type == "academic" or hint == "academic":
            structure = self._analyze_academic(text)
        elif file_type == "interview" or hint == "interview":
            structure = self._analyze_interview(text)
        else:
            # 自动检测
            structure = self._analyze_auto(text)

        # 构建层级关系
        self._build_hierarchy(structure)

        # 生成章节摘要
        self._generate_section_summaries(structure)

        logger.info(
            f"✅ 文档结构分析完成: "
            f"{len(structure.elements)} 个元素, "
            f"{len(structure.sections)} 个章节"
        )

        return structure

    def _analyze_markdown(self, text: str) -> DocumentStructure:
        """分析 Markdown 文档"""
        structure = DocumentStructure()
        lines = text.split('\n')
        current_pos = 0
        element_counter = 0

        for line in lines:
            line = line.rstrip()

            # 检测标题
            match = re.match(self.markdown_heading_pattern, line)
            if match:
                hashes = match.group(1)
                title_text = match.group(2)
                level = len(hashes)

                element = DocumentElement(
                    type=self._level_to_type(level),
                    text=title_text,
                    level=level,
                    start_pos=current_pos,
                    end_pos=current_pos + len(line),
                    element_id=f"elem_{element_counter}"
                )

                structure.elements.append(element)
                element_counter += 1

            current_pos += len(line) + 1  # +1 for newline

        structure.metadata = {"format": "markdown"}
        return structure

    def _analyze_academic(self, text: str) -> DocumentStructure:
        """分析学术论文"""
        structure = DocumentStructure()
        paragraphs = re.split(r'\n\s*\n', text)
        current_pos = 0
        element_counter = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                current_pos += 2
                continue

            # 检查是否是学术章节标题
            para_lower = para.lower()
            is_section = False

            for section_name, level in self.academic_sections.items():
                if para_lower.startswith(section_name):
                    element = DocumentElement(
                        type=self._level_to_type(level),
                        text=para,
                        level=level,
                        start_pos=current_pos,
                        end_pos=current_pos + len(para),
                        element_id=f"elem_{element_counter}",
                        metadata={"section_type": section_name}
                    )
                    structure.elements.append(element)
                    element_counter += 1
                    is_section = True
                    break

            if not is_section:
                # 普通段落
                element = DocumentElement(
                    type=ElementType.PARAGRAPH,
                    text=para,
                    level=99,  # 最底层
                    start_pos=current_pos,
                    end_pos=current_pos + len(para),
                    element_id=f"elem_{element_counter}"
                )
                structure.elements.append(element)
                element_counter += 1

            current_pos += len(para) + 2

        structure.metadata = {"format": "academic"}
        return structure

    def _analyze_interview(self, text: str) -> DocumentStructure:
        """分析访谈文档"""
        structure = DocumentStructure()
        paragraphs = re.split(r'\n\s*\n', text)
        current_pos = 0
        element_counter = 0
        current_qa_pair = None

        for para in paragraphs:
            para = para.strip()
            if not para:
                current_pos += 2
                continue

            # 检测问答标记
            match = re.match(self.interview_pattern, para)
            if match:
                qa_type = "question" if match.group(1)[0] in "问QQA" else "answer"

                element = DocumentElement(
                    type=ElementType.PARAGRAPH,
                    text=para,
                    level=2,
                    start_pos=current_pos,
                    end_pos=current_pos + len(para),
                    element_id=f"elem_{element_counter}",
                    metadata={"qa_type": qa_type}
                )
                structure.elements.append(element)
                element_counter += 1
            else:
                # 普通段落
                element = DocumentElement(
                    type=ElementType.PARAGRAPH,
                    text=para,
                    level=99,
                    start_pos=current_pos,
                    end_pos=current_pos + len(para),
                    element_id=f"elem_{element_counter}"
                )
                structure.elements.append(element)
                element_counter += 1

            current_pos += len(para) + 2

        structure.metadata = {"format": "interview"}
        return structure

    def _analyze_auto(self, text: str) -> DocumentStructure:
        """自动检测文档结构"""
        structure = DocumentStructure()

        # 检测是否是 Markdown
        if re.search(r'^#{1,6}\s+', text, re.MULTILINE):
            logger.info("   检测到 Markdown 格式")
            return self._analyze_markdown(text)

        # 检测是否是访谈
        if re.search(self.interview_pattern, text, re.MULTILINE):
            logger.info("   检测到访谈格式")
            return self._analyze_interview(text)

        # 检测中文章节
        paragraphs = re.split(r'\n\s*\n', text)
        current_pos = 0
        element_counter = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                current_pos += 2
                continue

            # 检测中文标题
            heading_detected = False
            for pattern, level in self.chinese_heading_patterns:
                match = re.match(pattern, para)
                if match:
                    element = DocumentElement(
                        type=self._level_to_type(level),
                        text=para,
                        level=level,
                        start_pos=current_pos,
                        end_pos=current_pos + len(para),
                        element_id=f"elem_{element_counter}"
                    )
                    structure.elements.append(element)
                    element_counter += 1
                    heading_detected = True
                    break

            if not heading_detected:
                # 普通段落
                element = DocumentElement(
                    type=ElementType.PARAGRAPH,
                    text=para,
                    level=99,
                    start_pos=current_pos,
                    end_pos=current_pos + len(para),
                    element_id=f"elem_{element_counter}"
                )
                structure.elements.append(element)
                element_counter += 1

            current_pos += len(para) + 2

        structure.metadata = {"format": "auto"}
        return structure

    def _level_to_type(self, level: int) -> ElementType:
        """将层级转换为元素类型"""
        if level == 0:
            return ElementType.TITLE
        elif level == 1:
            return ElementType.HEADING_1
        elif level == 2:
            return ElementType.HEADING_2
        elif level == 3:
            return ElementType.HEADING_3
        elif level == 4:
            return ElementType.HEADING_4
        else:
            return ElementType.PARAGRAPH

    def _build_hierarchy(self, structure: DocumentStructure):
        """构建层级关系"""
        # 构建 ID 映射
        for elem in structure.elements:
            if elem.element_id:
                structure.hierarchy[elem.element_id] = elem

        # 建立父子关系
        parent_stack = []  # (level, element_id)

        for elem in structure.elements:
            # 找到合适的父节点
            while parent_stack and parent_stack[-1][0] >= elem.level:
                parent_stack.pop()

            if parent_stack:
                parent_id = parent_stack[-1][1]
                elem.parent_id = parent_id

                # 添加到父节点的子节点列表
                parent = structure.hierarchy.get(parent_id)
                if parent:
                    parent.children.append(elem.element_id)

            # 如果是标题，加入栈
            if elem.type != ElementType.PARAGRAPH:
                parent_stack.append((elem.level, elem.element_id))

    def _generate_section_summaries(self, structure: DocumentStructure):
        """生成章节摘要"""
        for elem in structure.elements:
            if elem.type != ElementType.PARAGRAPH and elem.element_id:
                # 收集该章节下的所有段落
                section_text = self._collect_section_text(structure, elem.element_id)

                # 生成摘要（简单版本：截取前100字）
                summary = section_text[:100] + "..." if len(section_text) > 100 else section_text

                structure.sections[elem.element_id] = {
                    "title": elem.text,
                    "level": elem.level,
                    "range": (elem.start_pos, elem.end_pos),
                    "summary": summary,
                    "text_length": len(section_text),
                    "children": elem.children
                }

    def _collect_section_text(self, structure: DocumentStructure, element_id: str) -> str:
        """收集章节下的所有文本"""
        elem = structure.get_element(element_id)
        if not elem:
            return ""

        texts = []

        # 收集所有子节点的文本
        for child_id in elem.children:
            child = structure.get_element(child_id)
            if child:
                if child.type == ElementType.PARAGRAPH:
                    texts.append(child.text)
                else:
                    # 递归收集
                    texts.append(self._collect_section_text(structure, child_id))

        return "\n".join(texts)

    def get_context_for_position(
        self,
        structure: DocumentStructure,
        start_pos: int,
        end_pos: int
    ) -> Dict[str, Any]:
        """
        获取指定位置的上下文信息

        用于为 chunk 添加语义上下文
        """
        context = {
            "chapter": None,
            "section": None,
            "subsection": None,
            "parent_chain": []
        }

        # 找到包含这个位置的最近的标题元素
        containing_elements = []

        for elem in structure.elements:
            if elem.type != ElementType.PARAGRAPH:
                # 检查这个标题是否在目标位置之前
                if elem.start_pos <= start_pos:
                    containing_elements.append(elem)

        # 按层级排序
        containing_elements.sort(key=lambda e: e.level)

        # 提取章节信息
        for elem in containing_elements:
            if elem.level == 1:
                context["chapter"] = elem.text
            elif elem.level == 2:
                context["section"] = elem.text
            elif elem.level == 3:
                context["subsection"] = elem.text

            context["parent_chain"].append({
                "level": elem.level,
                "text": elem.text,
                "type": elem.type.value
            })

        return context


# 全局实例
document_structure_analyzer = DocumentStructureAnalyzer()


def analyze_document_structure(
    text: str,
    file_type: str = "text",
    hint: Optional[str] = None
) -> DocumentStructure:
    """便捷函数：分析文档结构"""
    return document_structure_analyzer.analyze(text, file_type, hint)


if __name__ == "__main__":
    # 测试代码
    print("=" * 80)
    print("🧪 文档结构分析器测试")
    print("=" * 80)

    test_text = """# 第一章：传统美食

王大爷说，杀猪菜是我们村的传统美食。

## 1.1 历史渊源

杀猪菜起源于清朝时期。

## 1.2 制作方法

需要准备以下材料：

# 第二章：节日习俗

春节是最重要的节日。
"""

    structure = analyze_document_structure(test_text, hint="markdown")

    print(f"\n✅ 分析完成:")
    print(f"   元素数: {len(structure.elements)}")
    print(f"   章节数: {len(structure.sections)}")

    for elem in structure.elements[:5]:
        print(f"   - [{elem.type.value}] {elem.text[:30]}...")

    print("=" * 80)
