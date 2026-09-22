"""
邮件采集插件
"""

from typing import Dict, Any
from app.agents.ingestion_agent import IngestionPlugin
from app.core.logging import logger


class EmailPlugin(IngestionPlugin):
    """邮件采集插件"""

    @property
    def plugin_name(self) -> str:
        return "EmailPlugin"

    @property
    def supported_formats(self) -> list:
        return ["eml", "msg"]

    def ingest(self, file_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """采集邮件文件"""
        try:
            import email
            from email import policy

            with open(file_path, 'rb') as f:
                msg = email.message_from_binary_file(f, policy=policy.default)

            # 提取元数据
            structured_metadata = {
                "from": msg.get('From', ''),
                "to": msg.get('To', ''),
                "subject": msg.get('Subject', ''),
                "date": msg.get('Date', ''),
                "cc": msg.get('Cc', ''),
            }

            # 提取正文
            body_parts = []

            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    if content_type == 'text/plain':
                        body = part.get_payload(decode=True)
                        if body:
                            body_parts.append(body.decode('utf-8', errors='ignore'))
            else:
                body = msg.get_payload(decode=True)
                if body:
                    body_parts.append(body.decode('utf-8', errors='ignore'))

            # 构建文本
            text_lines = [
                f"发件人: {structured_metadata['from']}",
                f"收件人: {structured_metadata['to']}",
                f"主题: {structured_metadata['subject']}",
                f"日期: {structured_metadata['date']}",
                "",
                "正文:",
            ]
            text_lines.extend(body_parts)

            full_text = "\n".join(text_lines)

            # 统计
            structured_metadata["total_words"] = len(full_text.replace(" ", ""))
            structured_metadata["has_attachments"] = any(
                part.get_content_disposition() == 'attachment'
                for part in msg.walk()
            ) if msg.is_multipart() else False
            structured_metadata["language"] = self._detect_language(full_text)

            return {
                "raw_text": full_text,
                "structured_metadata": structured_metadata,
                "content_type": "email",
                "extraction_method": "email_parser",
                "confidence": 0.95
            }

        except Exception as e:
            logger.error(f"邮件采集失败: {e}")
            raise

    def _detect_language(self, text: str) -> str:
        chinese_chars = sum(1 for c in text if '一' <= c <= '鿿')
        total_chars = len(text)
        if total_chars > 0 and chinese_chars / total_chars > 0.3:
            return "zh"
        return "en"
