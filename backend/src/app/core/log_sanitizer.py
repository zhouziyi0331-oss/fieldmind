"""
日志脱敏工具
用于在日志中自动脱敏敏感信息
"""

import re
from typing import Any, Dict, List


# 敏感字段列表
SENSITIVE_FIELDS = {
    'password',
    'passwd',
    'pwd',
    'secret',
    'token',
    'api_key',
    'apikey',
    'access_token',
    'refresh_token',
    'auth_token',
    'authorization',
    'credential',
    'private_key',
    'session_id',
    'cookie',
    'csrf_token',
}


def sanitize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    脱敏字典中的敏感字段

    Args:
        data: 原始字典

    Returns:
        脱敏后的字典
    """
    if not isinstance(data, dict):
        return data

    sanitized = {}
    for key, value in data.items():
        key_lower = key.lower()

        # 检查是否为敏感字段
        if any(sensitive in key_lower for sensitive in SENSITIVE_FIELDS):
            # 脱敏处理
            if isinstance(value, str) and value:
                sanitized[key] = mask_string(value)
            else:
                sanitized[key] = "***REDACTED***"
        elif isinstance(value, dict):
            # 递归处理嵌套字典
            sanitized[key] = sanitize_dict(value)
        elif isinstance(value, list):
            # 递归处理列表
            sanitized[key] = [
                sanitize_dict(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            sanitized[key] = value

    return sanitized


def mask_string(value: str, visible_chars: int = 4) -> str:
    """
    部分遮蔽字符串，只显示前后几个字符

    Args:
        value: 原始字符串
        visible_chars: 可见字符数

    Returns:
        遮蔽后的字符串，如 "abc***xyz"
    """
    if len(value) <= visible_chars * 2:
        return "***"

    return f"{value[:visible_chars]}***{value[-visible_chars:]}"


def sanitize_url(url: str) -> str:
    """
    脱敏URL中的敏感信息（如query参数中的token）

    Args:
        url: 原始URL

    Returns:
        脱敏后的URL
    """
    # 匹配query参数中的敏感字段
    pattern = r'([?&])(' + '|'.join(SENSITIVE_FIELDS) + r')=([^&]+)'

    def replacer(match):
        prefix = match.group(1)
        key = match.group(2)
        value = match.group(3)
        return f"{prefix}{key}={mask_string(value, 2)}"

    return re.sub(pattern, replacer, url, flags=re.IGNORECASE)


def sanitize_log_message(message: str) -> str:
    """
    脱敏日志消息中的敏感信息

    Args:
        message: 原始消息

    Returns:
        脱敏后的消息
    """
    # 匹配 key=value 或 key: value 模式
    patterns = [
        r'(' + '|'.join(SENSITIVE_FIELDS) + r')=([^\s,;]+)',
        r'(' + '|'.join(SENSITIVE_FIELDS) + r'):\s*([^\s,;]+)',
    ]

    result = message
    for pattern in patterns:
        def replacer(match):
            key = match.group(1)
            value = match.group(2)
            masked = mask_string(value, 2)
            sep = '=' if '=' in match.group(0) else ': '
            return f"{key}{sep}{masked}"

        result = re.sub(pattern, replacer, result, flags=re.IGNORECASE)

    return result


class SensitiveDataFilter:
    """
    Loguru 过滤器，用于自动脱敏日志中的敏感信息
    """

    def __call__(self, record: dict) -> bool:
        """
        过滤器回调，在日志记录前自动脱敏

        Args:
            record: loguru的日志记录

        Returns:
            始终返回True（不过滤日志，只修改内容）
        """
        # 脱敏消息内容
        if 'message' in record:
            record['message'] = sanitize_log_message(record['message'])

        # 脱敏extra字段
        if 'extra' in record and isinstance(record['extra'], dict):
            record['extra'] = sanitize_dict(record['extra'])

        return True


# 导出
__all__ = [
    'sanitize_dict',
    'mask_string',
    'sanitize_url',
    'sanitize_log_message',
    'SensitiveDataFilter',
    'SENSITIVE_FIELDS',
]
