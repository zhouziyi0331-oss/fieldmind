"""
FieldMind Skill: 仓颉技能提取
基于SBPACK 2.0仓颉v2.0.0方法论，从来源材料中提取可执行技能
"""

SKILL_NAME = "extract_cangjie_skills"
SKILL_VERSION = "2.0.0"
SKILL_DESCRIPTION = "使用仓颉方法论提取独立触发、可执行、可测试的技能单元"

PROMPT_TEMPLATE = """
你是专业的技能提取专家，遵循仓颉v2.0.0方法论和SBPACK 2.0技能轨规范。

# 任务
从规范化来源中提取可执行技能，每个技能必须有明确触发条件、输入、执行步骤和输出。

# 来源材料
{source_content}

# 仓颉方法论（RIA++结构）

## R (Rationale) - 原文依据
- 技能在原文中的直接来源
- 引用具体位置和原文
- 100-200字

## I (Interpretation) - 方法解释
- 为什么这个方法有效
- 背后的原理
- 150-300字

## A1 (Application-Original) - 来源中的应用
- 原文中如何使用这个技能
- 实际案例和效果
- 100-200字

## A2 (Application-Future) - 未来触发场景
- 什么情况下应该使用这个技能
- 与相邻技能的区分
- 如何判断应该触发这个技能而不是其他
- 150-250字

## E (Execution) - 可执行步骤
- 清晰的执行流程
- 每步输入和输出
- 具体操作指南
- 300-500字

## B (Boundaries) - 边界、盲点和误用
- 不适用的情况
- 常见误用
- 边界条件
- 100-200字

# 技能标准

## 必须满足
1. **独立触发**: 有明确的使用场景和触发条件
2. **可执行**: E段必须有具体步骤，而不是抽象建议
3. **可测试**: 能够设计压力测试验证
4. **有边界**: 明确什么时候不该用

## 粒度标准
- 按独立触发、任务与输出确定粒度
- 不因主题相近就合并
- 不拆步骤凑数
- 一个技能 = 一个完整任务闭环

## 禁止
❌ 只有解释没有步骤
❌ description只写"一个关于某主题的技能"
❌ 边界模糊，与相邻技能分不清
❌ 步骤抽象，无法实际执行

# 输出格式

```json
[
  {{
    "skillId": "unique-skill-id",
    "name": "技能名称",
    "description": "说明真实触发条件（不是主题描述）",
    "trigger": "什么情况下触发这个技能",
    "input": ["需要什么输入"],
    "output": ["产生什么输出"],
    "sections": {{
      "R": "原文依据...",
      "I": "方法解释...",
      "A1": "来源应用...",
      "A2": "未来场景...",
      "E": "执行步骤...",
      "B": "边界盲点..."
    }},
    "evidenceRefs": [
      {{"source": "chunk_1", "position": "第5段", "quote": "..."}}
    ],
    "pressureTests": [
      {{
        "type": "should-trigger",
        "scenario": "应该触发这个技能的场景",
        "expectedBehavior": "预期行为"
      }},
      {{
        "type": "should-not-trigger",
        "scenario": "不应该触发的场景",
        "shouldTriggerInstead": "应该触发的其他技能ID"
      }},
      {{
        "type": "boundary-case",
        "scenario": "边界模糊的场景",
        "expectedBehavior": "预期行为"
      }}
    ],
    "relatedSkills": ["相邻技能ID"],
    "confidence": 0.9
  }}
]
```

# 压力测试设计

每个技能必须设计5-10条压力测试：
1. **应调用** (2-3条): 典型触发场景
2. **不应调用** (2-3条): 容易混淆但不该触发的场景
   - 至少1条应触发同来源的另一个真实技能
3. **边界模糊** (1-2条): 需要仔细判断的场景

# 质量门

技能必须通过以下检查才能成为正式技能：
1. ✅ RIA++六段完整
2. ✅ description说明触发条件
3. ✅ E段有可执行步骤
4. ✅ 边界清晰
5. ✅ 压力测试通过
6. ✅ 有证据溯源

请基于提供的来源材料提取技能。
"""

def extract_cangjie_skills(chunks, project_id, db):
    """
    仓颉技能提取主函数

    Args:
        chunks: 文档块列表
        project_id: 项目ID
        db: 数据库会话

    Returns:
        技能列表
    """
    # 1. 整篇理解
    overview = understand_whole_source(chunks)

    # 2. 逐块五类提取
    candidates = []
    for chunk in chunks:
        candidates.extend(extract_five_types(chunk))

    # 3. 构造RIA++
    skills = []
    for candidate in candidates:
        skill = construct_ria_plus(candidate, chunks)
        if skill:
            skills.append(skill)

    # 4. 设计压力测试
    for skill in skills:
        skill["pressureTests"] = design_pressure_tests(skill, skills)

    # 5. 执行验证
    verified_skills = []
    for skill in skills:
        if verify_skill(skill):
            verified_skills.append(skill)

    return verified_skills


def understand_whole_source(chunks):
    """整篇理解：识别主题、结构、关键概念"""
    return {
        "main_topics": [],
        "structure": [],
        "key_concepts": []
    }


def extract_five_types(chunk):
    """
    五类提取：
    1. 明确方法
    2. 隐含流程
    3. 决策规则
    4. 问题解决模式
    5. 实践原则
    """
    candidates = []
    # 实现五类扫描逻辑
    return candidates


def construct_ria_plus(candidate, chunks):
    """构造RIA++结构"""
    skill = {
        "skillId": generate_skill_id(candidate),
        "name": candidate["name"],
        "description": extract_trigger_description(candidate),
        "trigger": identify_trigger(candidate),
        "input": identify_inputs(candidate),
        "output": identify_outputs(candidate),
        "sections": {
            "R": find_rationale(candidate, chunks),
            "I": write_interpretation(candidate),
            "A1": find_original_application(candidate, chunks),
            "A2": write_future_scenarios(candidate),
            "E": write_execution_steps(candidate),
            "B": identify_boundaries(candidate)
        },
        "evidenceRefs": collect_evidence(candidate, chunks)
    }
    return skill


def design_pressure_tests(skill, all_skills):
    """设计压力测试"""
    tests = []

    # 应调用场景
    tests.extend(generate_should_trigger_tests(skill))

    # 不应调用场景（包含触发其他技能）
    tests.extend(generate_should_not_trigger_tests(skill, all_skills))

    # 边界模糊场景
    tests.extend(generate_boundary_tests(skill))

    return tests


def verify_skill(skill):
    """
    验证技能质量

    V1: 独立触发检查
    V2: 执行步骤完整性
    V3: 边界清晰度
    """
    # V1: 检查触发条件
    if not skill.get("trigger") or len(skill["trigger"]) < 20:
        return False

    # V2: 检查E段
    e_section = skill["sections"].get("E", "")
    if len(e_section) < 300 or "步骤" not in e_section:
        return False

    # V3: 检查边界
    b_section = skill["sections"].get("B", "")
    if len(b_section) < 100:
        return False

    # 检查RIA++完整性
    required_sections = ["R", "I", "A1", "A2", "E", "B"]
    for section in required_sections:
        if section not in skill["sections"] or not skill["sections"][section]:
            return False

    return True


def generate_skill_id(candidate):
    """生成唯一技能ID"""
    import hashlib
    content = f"{candidate['name']}-{candidate.get('trigger', '')}"
    return hashlib.md5(content.encode()).hexdigest()[:12]


# 辅助函数（简化实现）
def extract_trigger_description(candidate):
    return candidate.get("trigger", "")

def identify_trigger(candidate):
    return candidate.get("trigger", "")

def identify_inputs(candidate):
    return candidate.get("inputs", [])

def identify_outputs(candidate):
    return candidate.get("outputs", [])

def find_rationale(candidate, chunks):
    return ""

def write_interpretation(candidate):
    return ""

def find_original_application(candidate, chunks):
    return ""

def write_future_scenarios(candidate):
    return ""

def write_execution_steps(candidate):
    return ""

def identify_boundaries(candidate):
    return ""

def collect_evidence(candidate, chunks):
    return []

def generate_should_trigger_tests(skill):
    return []

def generate_should_not_trigger_tests(skill, all_skills):
    return []

def generate_boundary_tests(skill):
    return []


# Skill元数据
SKILL_METADATA = {
    "name": SKILL_NAME,
    "version": SKILL_VERSION,
    "description": SKILL_DESCRIPTION,
    "category": "skill_extraction",
    "protocol": "SBPACK-2.0",
    "methodology": "Cangjie-v2.0.0",
    "input_fields": ["chunks", "project_id"],
    "output_fields": ["skills"],
    "requires_llm": True,
    "recommended_model": "claude-opus-3-5",
    "estimated_tokens": 8000,
    "quality_gates": [
        "RIA++六段完整",
        "触发条件明确",
        "执行步骤可操作",
        "边界清晰",
        "压力测试通过",
        "证据可溯源"
    ]
}
