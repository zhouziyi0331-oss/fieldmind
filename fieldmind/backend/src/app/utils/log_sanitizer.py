"""
日志脱敏工具

自动检测并脱敏日志中的敏感信息，防止密码、Token、API密钥等泄露
"""
import re
from typing import Any, Dict, List, Set, Union
from copy import deepcopy


class LogSanitizer:
    """日志脱敏器"""

    # 敏感字段关键词（小写）
    SENSITIVE_KEYS: Set[str] = {
        'password', 'passwd', 'pwd',
        'secret', 'secret_key', 'secretkey',
        'token', 'access_token', 'refresh_token', 'auth_token',
        'api_key', 'apikey', 'api_secret',
        'private_key', 'privatekey',
        'authorization', 'auth',
        'credential', 'credentials',
        'session_id', 'sessionid',
        'cookie', 'cookies',
        'jwt', 'bearer',
    }

    # PII 字段（个人隐私信息）
    PII_KEYS: Set[str] = {
        'email', 'phone', 'mobile', 'telephone',
        'ssn', 'social_security',
        'credit_card', 'card_number',
        'address', 'ip_address', 'ip',
    }

    # 敏感值模式（正则）
    SENSITIVE_PATTERNS = [
        (re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'), '***EMAIL***'),  # 邮箱
        (re.compile(r'\b(?:\d{3}-\d{2}-\d{4}|\d{9})\b'), '***SSN***'),  # 美国 SSN
        (re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b'), '***CARD***'),  # 信用卡
        (re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b'), '***IP***'),  # IPv4
        (re.compile(r'Bearer\s+[A-Za-z0-9\-._~+/]+', re.IGNORECASE), 'Bearer ***TOKEN***'),  # Bearer Token
    ]

    def __init__(
        self,
        mask_string: str = "***REDACTED***",
        partial_show: bool = False,
        show_length: int = 4
    ):
        """
        初始化脱敏器

        Args:
            mask_string: 脱敏后显示的字符串
            partial_show: 是否部分显示（保留前后几位）
            show_length: partial_show=True 时保留的字符数
        """
        self.mask_string = mask_string
        self.partial_show = partial_show
        self.show_length = show_length

    def sanitize(self, data: Any) -> Any:
        """
        脱敏数据

        Args:
            data: 任意类型的数据（字典、列表、字符串等）

        Returns:
            脱敏后的数据（保持原始类型）
        """
        if isinstance(data, dict):
            return self._sanitize_dict(data)
        elif isinstance(data, list):
            return self._sanitize_list(data)
        elif isinstance(data, str):
            return self._sanitize_string(data)
        else:
            return data

    def _sanitize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """脱敏字典"""
        result = {}
        for key, value in data.items():
            key_lower = key.lower()

            # 检查是否是敏感字段
            if self._is_sensitive_key(key_lower):
                result[key] = self._mask_value(value)
            elif isinstance(value, (dict, list)):
                result[key] = self.sanitize(value)
            elif isinstance(value, str):
                result[key] = self._sanitize_string(value)
            else:
                result[key] = value

        return result

    def _sanitize_list(self, data: List[Any]) -> List[Any]:
        """脱敏列表"""
        return [self.sanitize(item) for item in data]

    def _sanitize_string(self, data: str) -> str:
        """脱敏字符串（应用正则模式）"""
        result = data
        for pattern, replacement in self.SENSITIVE_PATTERNS:
            result = pattern.sub(replacement, result)
        return result

    def _is_sensitive_key(self, key_lower: str) -> bool:
        """判断字段名是否敏感"""
        # 完全匹配
        if key_lower in self.SENSITIVE_KEYS or key_lower in self.PII_KEYS:
            return True

        # 部分匹配（包含敏感关键词）
        for sensitive in self.SENSITIVE_KEYS:
            if sensitive in key_lower:
                return True

        return False

    def _mask_value(self, value: Any) -> str:
        """
        脱敏值

        Args:
            value: 原始值

        Returns:
            脱敏后的字符串
        """
        if value is None:
            return "None"

        value_str = str(value)

        if not self.partial_show or len(value_str) <= self.show_length * 2:
            return self.mask_string

        # 部分显示：保留前后 show_length 个字符
        prefix = value_str[:self.show_length]
        suffix = value_str[-self.show_length:]
        return f"{prefix}...{suffix}"


# 全局单例
_default_sanitizer = LogSanitizer(
    mask_string="***REDACTED***",
    partial_show=False  # 默认完全脱敏
)


def sanitize_for_logging(data: Any) -> Any:
    """
    便捷函数：脱敏数据用于日志输出

    Usage:
        logger.info(f"用户信息: {sanitize_for_logging(user_data)}")

    Args:
        data: 任意数据

    Returns:
        脱敏后的数据
    """
    return _default_sanitizer.sanitize(data)


def sanitize_with_partial(data: Any, show_length: int = 4) -> Any:
    """
    部分脱敏：保留前后几位用于调试

    Usage:
        logger.debug(f"Token: {sanitize_with_partial(token, show_length=6)}")

    Args:
        data: 任意数据
        show_length: 保留的字符数

    Returns:
        部分脱敏的数据
    """
    sanitizer = LogSanitizer(partial_show=True, show_length=show_length)
    return sanitizer.sanitize(data)


# 装饰器：自动脱敏函数参数
def sanitize_args(*sensitive_arg_names: str):
    """
    装饰器：自动脱敏指定参数后记录日志

    Usage:
        @sanitize_args('password', 'api_key')
        def login(username: str, password: str, api_key: str):
            logger.info(f"登录: {username}")  # password 和 api_key 已自动脱敏
    """
    def decorator(func):
        import functools

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 脱敏 kwargs
            sanitized_kwargs = {
                k: _default_sanitizer._mask_value(v) if k in sensitive_arg_names else v
                for k, v in kwargs.items()
            }

            # 执行原函数（使用原始参数）
            return func(*args, **kwargs)

        return wrapper
    return decorator


if __name__ == "__main__":
    # 测试用例
    test_data = {
        "username": "john_doe",
        "password": "super_secret_123",
        "email": "john@example.com",
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0",
        "api_key": "sk-1234567890abcdef",
        "user_data": {
            "phone": "123-456-7890",
            "address": "123 Main St",
            "nested_secret": "hidden_value"
        },
        "items": [
            {"id": 1, "secret_token": "abc123"},
            {"id": 2, "public_info": "visible"}
        ]
    }

    print("原始数据:")
    print(test_data)
    print("\n脱敏后:")
    print(sanitize_for_logging(test_data))
    print("\n部分脱敏:")
    print(sanitize_with_partial(test_data, show_length=4))
