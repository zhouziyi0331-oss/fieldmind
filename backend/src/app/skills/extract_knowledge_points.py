"""
FieldMind Skill: 知识点提取
基于SBPACK 2.0知识轨规范，从来源材料中提取独立可验证的知识点
"""

SKILL_NAME = "extract_knowledge_points"
SKILL_VERSION = "2.0.0"
SKILL_DESCRIPTION = "提取可独立判断的概念、主张、原则、机制和论证"

PROMPT_TEMPLATE = """
你是专业的知识提取专家，遵循SBPACK 2.0知识轨规范。

# 任务
从规范化来源中提取可独立判断的知识点。

# 来源材料
{source_content}

# 提取规则

## 知识点标准
知识点回答"是什么、为什么、何时成立、证据与边界是什么"：
1. 只提取原文直接支持的内容
2. 明确区分：原文陈述 vs 作者观点 vs 蒸馏器推断
3. 不包含完整执行步骤（有步骤的是技能，不是知识）
4. 每个知识点必须可以独立判断真伪

## 必需字段
每个知识点必须包含：

### statement (核心主张)
- 一句话说明"是什么"
- 明确、可验证
- 例："敏捷开发强调小步快跑和持续反馈"

### explanation (解释)
- 为什么这个主张成立
- 背后的原理或逻辑
- 100-300字

### whyItMatters (重要性)
- 为什么要知道这个
- 对读者的价值
- 50-150字

### scope (适用范围)
- 在什么情况下成立
- 适用的领域/场景
- 例：["软件项目", "团队规模<10人"]

### conditions (前提条件)
- 这个知识成立需要什么条件
- 例：["团队有经验", "需求可迭代"]

### boundaries (边界)
- 不适用的情况
- 例：["大型基础设施项目", "固定需求项目"]

### counterexamples (反例)
- 什么情况下这个知识不成立
- 例：["瀑布模型更适合的场景"]

### evidenceRefs (证据引用)
- 原文中支持这个知识点的位置
- 格式：[{source: "chunk_123", position: "第5段"}]

### confidence (置信度)
- 0.0-1.0
- 基于证据强度

### claimAttribution (主张归属)
- "原文直接陈述" | "作者观点" | "作者报告的事实" | "蒸馏器推断"

## 禁止事项
❌ 不得凭记忆补充
❌ 不得把技能步骤当知识点
❌ 不得把摘要/术语表直接改名为知识点
❌ 不得为凑数量而硬造知识点
❌ 不得包含"如何执行"的内容

## 输出格式
JSON数组，每个元素是一个知识点：

```json
[
  {{
    "statement": "...",
    "explanation": "...",
    "whyItMatters": "...",
    "scope": ["...", "..."],
    "conditions": ["...", "..."],
    "boundaries": ["...", "..."],
    "counterexamples": ["..."],
    "evidenceRefs": [
      {{"source": "chunk_1", "position": "第3段", "quote": "原文引用"}}
    ],
    "confidence": 0.9,
    "claimAttribution": "原文直接陈述"
  }}
]
```

请基于提供的来源材料提取知识点。
"""

def extract_knowledge_points(chunks, project_id, db):
    """
    知识点提取主函数

    Args:
        chunks: 文档块列表
        project_id: 项目ID
        db: 数据库会话

    Returns:
        知识点列表
    """
    knowledge_points = []

    # 1. 规范化来源
    normalized_content = normalize_source(chunks)

    # 2. 提取知识点候选
    candidates = extract_candidates(normalized_content)

    # 3. 验证每个候选
    for candidate in candidates:
        if validate_knowledge_point(candidate):
            knowledge_points.append(candidate)

    # 4. 去重和质量检查
    knowledge_points = deduplicate_and_check(knowledge_points)

    return knowledge_points


def normalize_source(chunks):
    """规范化来源内容"""
    normalized = []
    for chunk in chunks:
        normalized.append({
            "id": chunk.id,
            "text": chunk.text,
            "metadata": {
                "page": chunk.page_number,
                "speaker": chunk.speaker,
                "timestamp": chunk.timestamp_start
            }
        })
    return normalized


def validate_knowledge_point(candidate):
    """
    验证知识点是否符合标准

    检查项：
    1. 是否有完整必需字段
    2. 是否包含执行步骤（有则不合格）
    3. 是否可独立判断
    4. 是否有证据支持
    """
    required_fields = [
        "statement", "explanation", "whyItMatters",
        "scope", "conditions", "boundaries",
        "counterexamples", "evidenceRefs"
    ]

    # 检查必需字段
    for field in required_fields:
        if field not in candidate or not candidate[field]:
            return False

    # 检查是否包含执行步骤（技能特征）
    execution_keywords = ["第一步", "然后", "接下来", "最后", "执行", "操作"]
    if any(kw in candidate["explanation"] for kw in execution_keywords):
        return False

    # 检查证据
    if not candidate["evidenceRefs"] or len(candidate["evidenceRefs"]) == 0:
        return False

    return True


def deduplicate_and_check(knowledge_points):
    """去重和质量检查"""
    # 简单去重：基于statement相似度
    unique_points = []
    seen_statements = set()

    for point in knowledge_points:
        statement = point["statement"].lower().strip()
        if statement not in seen_statements:
            unique_points.append(point)
            seen_statements.add(statement)

    return unique_points


# Skill元数据
SKILL_METADATA = {
    "name": SKILL_NAME,
    "version": SKILL_VERSION,
    "description": SKILL_DESCRIPTION,
    "category": "knowledge_extraction",
    "protocol": "SBPACK-2.0",
    "input_fields": ["chunks", "project_id"],
    "output_fields": ["knowledge_points"],
    "requires_llm": True,
    "recommended_model": "claude-sonnet-3-5",
    "estimated_tokens": 4000,
    "quality_gates": [
        "必需字段完整性",
        "无执行步骤混入",
        "证据可溯源",
        "去重检查"
    ]
}
