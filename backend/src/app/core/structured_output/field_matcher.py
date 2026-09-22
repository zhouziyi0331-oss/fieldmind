"""
模糊字段匹配

处理 LLM 输出字段名不匹配的情况
"""
from typing import Dict, Any, List
from pydantic import BaseModel
import re


def match_fields_fuzzy(
    llm_output: Dict[str, Any],
    model_class: type[BaseModel]
) -> Dict[str, Any]:
    """模糊匹配字段名

    处理策略：
    1. 精确匹配
    2. 小写匹配
    3. 下划线/驼峰转换
    4. 编辑距离匹配

    Args:
        llm_output: LLM 输出的字典
        model_class: 目标 Pydantic 模型

    Returns:
        匹配后的字典
    """
    model_fields = model_class.model_fields
    matched = {}

    for llm_key, llm_value in llm_output.items():
        matched_field = _find_matching_field(llm_key, list(model_fields.keys()))

        if matched_field:
            matched[matched_field] = llm_value
        else:
            # 未匹配的字段也保留（Pydantic 会忽略额外字段）
            matched[llm_key] = llm_value

    return matched


def _find_matching_field(target: str, candidates: List[str]) -> str | None:
    """找到最匹配的字段名

    Args:
        target: 目标字段名
        candidates: 候选字段名列表

    Returns:
        最匹配的字段名，如果没有匹配返回 None
    """
    # 1. 精确匹配
    if target in candidates:
        return target

    # 2. 小写匹配
    target_lower = target.lower()
    for candidate in candidates:
        if candidate.lower() == target_lower:
            return candidate

    # 3. 下划线/驼峰转换匹配
    target_snake = to_snake_case(target)
    target_camel = to_camel_case(target)

    for candidate in candidates:
        candidate_snake = to_snake_case(candidate)
        candidate_camel = to_camel_case(candidate)

        if (target_snake == candidate_snake or
            target_camel == candidate_camel or
            target == candidate_snake or
            target == candidate_camel or
            target_snake == candidate or
            target_camel == candidate):
            return candidate

    # 4. 编辑距离匹配（阈值 0.8）
    from difflib import SequenceMatcher

    best_match = None
    best_score = 0.0
    threshold = 0.8

    for candidate in candidates:
        score = SequenceMatcher(None, target_lower, candidate.lower()).ratio()
        if score > best_score and score >= threshold:
            best_score = score
            best_match = candidate

    return best_match


def to_snake_case(text: str) -> str:
    """转换为 snake_case

    Examples:
        "userName" -> "user_name"
        "UserName" -> "user_name"
        "user_name" -> "user_name"
    """
    # 在大写字母前插入下划线
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', text)
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
    return s2.lower()


def to_camel_case(text: str) -> str:
    """转换为 camelCase

    Examples:
        "user_name" -> "userName"
        "UserName" -> "userName"
        "userName" -> "userName"
    """
    # 如果已经是 camelCase，直接返回
    if '_' not in text and text[0].islower():
        return text

    # 分割并转换
    components = text.split('_')
    # 第一个组件小写，其余首字母大写
    return components[0].lower() + ''.join(x.title() for x in components[1:])


def to_pascal_case(text: str) -> str:
    """转换为 PascalCase

    Examples:
        "user_name" -> "UserName"
        "userName" -> "UserName"
    """
    if '_' in text:
        components = text.split('_')
        return ''.join(x.title() for x in components)
    else:
        return text[0].upper() + text[1:] if text else text
