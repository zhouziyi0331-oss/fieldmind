"""
FieldMind 统一 ID 生成器
Week 2 - Day 1: 实现 ID 生成规范
"""

import uuid
import re
from typing import Literal

# ID 类型定义
IDType = Literal[
    "project", "document", "chunk", "entity", "relation",
    "skill", "knowledge_asset", "user", "workflow", "task",
    "report", "session", "message", "tag", "annotation"
]

# ID 前缀映射
ID_PREFIXES = {
    "project": "proj",
    "document": "doc",
    "chunk": "chk",
    "entity": "ent",
    "relation": "rel",
    "skill": "sk",
    "knowledge_asset": "ka",
    "user": "usr",
    "workflow": "wf",
    "task": "tsk",
    "report": "rpt",
    "session": "ses",
    "message": "msg",
    "tag": "tag",
    "annotation": "ann",
}

def generate_id(entity_type: IDType) -> str:
    """
    生成统一格式的全局唯一 ID

    格式: {type_prefix}_{12位uuid}
    示例: ent_a1b2c3d4e5f6

    Args:
        entity_type: 实体类型

    Returns:
        统一格式的 ID

    Raises:
        ValueError: 如果 entity_type 不在支持列表中
    """
    if entity_type not in ID_PREFIXES:
        raise ValueError(f"不支持的实体类型: {entity_type}. 支持的类型: {list(ID_PREFIXES.keys())}")

    prefix = ID_PREFIXES[entity_type]
    unique_part = uuid.uuid4().hex[:12]

    return f"{prefix}_{unique_part}"


def validate_id(id_string: str) -> bool:
    """
    验证 ID 格式是否正确

    Args:
        id_string: 要验证的 ID

    Returns:
        True 如果格式正确，否则 False
    """
    # 格式: {prefix}_{12位十六进制}
    pattern = r'^[a-z]{2,4}_[a-f0-9]{12}$'
    return bool(re.match(pattern, id_string))


def extract_type_from_id(id_string: str) -> str:
    """
    从 ID 中提取实体类型

    Args:
        id_string: ID 字符串

    Returns:
        实体类型名称

    Raises:
        ValueError: 如果 ID 格式不正确
    """
    if not validate_id(id_string):
        raise ValueError(f"无效的 ID 格式: {id_string}")

    prefix = id_string.split('_')[0]

    # 反向查找类型
    for entity_type, type_prefix in ID_PREFIXES.items():
        if type_prefix == prefix:
            return entity_type

    raise ValueError(f"未知的 ID 前缀: {prefix}")


def parse_old_id(old_id) -> dict:
    """
    解析旧的 ID 格式，用于迁移

    Args:
        old_id: 旧格式的 ID (可能是 int, UUID 或其他格式)

    Returns:
        包含旧 ID 信息的字典
    """
    result = {
        "old_id": old_id,
        "old_id_type": type(old_id).__name__,
        "is_integer": isinstance(old_id, int),
        "is_uuid": False,
        "is_string": isinstance(old_id, str)
    }

    # 检查是否是 UUID 格式
    if isinstance(old_id, str):
        try:
            uuid.UUID(old_id)
            result["is_uuid"] = True
        except ValueError:
            pass

    return result


# ===== 测试函数 =====

def test_generate_id():
    """测试 ID 生成"""
    print("=" * 60)
    print("测试 ID 生成器")
    print("=" * 60)

    # 测试各种类型
    test_types = ["project", "document", "chunk", "entity", "relation", "skill"]

    for entity_type in test_types:
        new_id = generate_id(entity_type)
        is_valid = validate_id(new_id)
        extracted_type = extract_type_from_id(new_id)

        status = "✅" if is_valid and extracted_type == entity_type else "❌"
        print(f"{status} {entity_type:15} → {new_id:20} (valid: {is_valid}, type: {extracted_type})")

    print()


def test_validate_id():
    """测试 ID 验证"""
    print("=" * 60)
    print("测试 ID 验证器")
    print("=" * 60)

    test_cases = [
        ("ent_a1b2c3d4e5f6", True, "正确格式"),
        ("chk_123456789abc", True, "正确格式"),
        ("invalid_id", False, "缺少前缀"),
        ("ent_12345", False, "UUID 部分太短"),
        ("ent_a1b2c3d4e5f6x", False, "UUID 部分太长"),
        ("ENT_a1b2c3d4e5f6", False, "前缀大写"),
        ("ent_A1B2C3D4E5F6", False, "UUID 部分大写"),
        ("123", False, "纯数字"),
    ]

    for test_id, expected, description in test_cases:
        result = validate_id(test_id)
        status = "✅" if result == expected else "❌"
        print(f"{status} {test_id:20} → {result:5} (期望: {expected:5}) - {description}")

    print()


def test_parse_old_id():
    """测试旧 ID 解析"""
    print("=" * 60)
    print("测试旧 ID 解析")
    print("=" * 60)

    old_ids = [
        123,
        "550e8400-e29b-41d4-a716-446655440000",
        "some_string_id",
        456789,
    ]

    for old_id in old_ids:
        info = parse_old_id(old_id)
        print(f"旧 ID: {old_id}")
        print(f"  类型: {info['old_id_type']}")
        print(f"  是整数: {info['is_integer']}")
        print(f"  是 UUID: {info['is_uuid']}")
        print()


if __name__ == "__main__":
    test_generate_id()
    test_validate_id()
    test_parse_old_id()

    print("=" * 60)
    print("✅ ID 生成器实现完成")
    print("=" * 60)
