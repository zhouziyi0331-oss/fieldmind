"""
代码文件采集插件
"""

from typing import Dict, Any
from app.agents.ingestion_agent import IngestionPlugin
from app.core.logging import logger


class CodePlugin(IngestionPlugin):
    """代码文件采集插件"""

    @property
    def plugin_name(self) -> str:
        return "CodePlugin"

    @property
    def supported_formats(self) -> list:
        return [
            # Python
            "py", "pyw", "pyx",
            # JavaScript/TypeScript
            "js", "jsx", "ts", "tsx",
            # Java/Kotlin
            "java", "kt", "kts",
            # C/C++
            "c", "cpp", "cc", "cxx", "h", "hpp",
            # Go
            "go",
            # Rust
            "rs",
            # Ruby
            "rb",
            # PHP
            "php",
            # Shell
            "sh", "bash",
            # SQL
            "sql",
            # 其他
            "r", "swift", "scala", "m", "lua"
        ]

    def ingest(self, file_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """采集代码文件"""
        try:
            from pathlib import Path

            # 尝试多种编码读取
            encodings = ['utf-8', 'gbk', 'latin-1']
            code_content = None
            used_encoding = None

            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        code_content = f.read()
                    used_encoding = encoding
                    break
                except UnicodeDecodeError:
                    continue

            if code_content is None:
                raise ValueError("无法识别代码文件编码")

            # 识别语言
            file_ext = Path(file_path).suffix[1:].lower()
            language = self._identify_language(file_ext)

            # 分析代码结构
            code_stats = self._analyze_code(code_content, language)

            # 生成文本描述
            text_lines = [
                f"=== 代码文件分析 ===",
                f"语言: {language}",
                f"总行数: {code_stats['total_lines']}",
                f"代码行数: {code_stats['code_lines']}",
                f"注释行数: {code_stats['comment_lines']}",
                f"空行数: {code_stats['blank_lines']}",
                "",
                "=== 代码内容 ===",
                code_content
            ]

            full_text = "\n".join(text_lines)

            # 元数据
            structured_metadata = {
                "format": "code",
                "language": language,
                "encoding": used_encoding,
                "total_lines": code_stats['total_lines'],
                "code_lines": code_stats['code_lines'],
                "comment_lines": code_stats['comment_lines'],
                "blank_lines": code_stats['blank_lines'],
                "total_words": len(code_content.replace(" ", "")),
            }

            return {
                "raw_text": full_text,
                "structured_metadata": structured_metadata,
                "content_type": "code",
                "extraction_method": "code_parser",
                "confidence": 1.0
            }

        except Exception as e:
            logger.error(f"代码文件采集失败: {e}")
            raise

    def _identify_language(self, ext: str) -> str:
        """识别编程语言"""
        language_map = {
            'py': 'Python',
            'pyw': 'Python',
            'pyx': 'Python',
            'js': 'JavaScript',
            'jsx': 'JavaScript',
            'ts': 'TypeScript',
            'tsx': 'TypeScript',
            'java': 'Java',
            'kt': 'Kotlin',
            'kts': 'Kotlin',
            'c': 'C',
            'cpp': 'C++',
            'cc': 'C++',
            'cxx': 'C++',
            'h': 'C/C++ Header',
            'hpp': 'C++ Header',
            'go': 'Go',
            'rs': 'Rust',
            'rb': 'Ruby',
            'php': 'PHP',
            'sh': 'Shell',
            'bash': 'Bash',
            'sql': 'SQL',
            'r': 'R',
            'swift': 'Swift',
            'scala': 'Scala',
            'm': 'Objective-C',
            'lua': 'Lua',
        }
        return language_map.get(ext, 'Unknown')

    def _analyze_code(self, code: str, language: str) -> Dict[str, int]:
        """分析代码统计"""
        lines = code.split('\n')

        total_lines = len(lines)
        blank_lines = 0
        comment_lines = 0
        code_lines = 0

        # 简单的注释检测（基于语言）
        if language in ['Python', 'Shell', 'Bash', 'Ruby']:
            comment_char = '#'
        elif language in ['JavaScript', 'TypeScript', 'Java', 'C', 'C++', 'Go', 'Rust', 'PHP', 'Kotlin', 'Swift', 'Scala']:
            comment_char = '//'
        elif language == 'SQL':
            comment_char = '--'
        else:
            comment_char = '#'

        for line in lines:
            stripped = line.strip()
            if not stripped:
                blank_lines += 1
            elif stripped.startswith(comment_char):
                comment_lines += 1
            else:
                code_lines += 1

        return {
            'total_lines': total_lines,
            'code_lines': code_lines,
            'comment_lines': comment_lines,
            'blank_lines': blank_lines,
        }
