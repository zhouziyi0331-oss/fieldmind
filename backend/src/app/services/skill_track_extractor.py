"""
技能轨提取服务 - 仓颉v2.0.0 + second-brain-balanced-skills-v1

遵循规范：
- 04-仓颉技能轨生产规范.md
- 10-技能充分提取与质量标准.md
- 12-技能中文表达规范.md
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import hashlib
import json
import logging
from datetime import datetime

from app.models.sbpack import SkillItem, ProducerSnapshot

logger = logging.getLogger(__name__)


class SkillTrackExtractor:
    """
    技能轨提取器

    实现仓颉v2.0.0五类提取器：
    1. 框架提取器 - 系统性方法论
    2. 原则提取器 - 指导性原则
    3. 案例提取器 - 具体实践案例
    4. 反例提取器 - 失败模式和边界
    5. 术语提取器 - 领域特定概念

    质量标准：
    - V1: 原文支持充分（两路线之一）
    - V2: 可迁移且可执行
    - V3: 具有具体方法价值
    """

    # 仓颉v2.0.0版本信息
    CANGJIE_VERSION = "v2.0.0"
    CANGJIE_COMMIT = "149cb39f559cafcb82910f8662b3f4e3b9ee5574"
    CANGJIE_UPSTREAM_HASH = "e634c0e443e9625fb1f6a9b65dbf8d59087366a893aa16d452691f689f5b002e"

    # 策略名称
    STRATEGY = "second-brain-balanced-skills-v1"

    def __init__(self, db: Session):
        self.db = db
        self.producer_name = "skill_track_extractor"
        self.producer_version = "1.0.0"

    def extract(self, package_id: int,
                normalized_text: str,
                chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        从规范化文本中提取技能

        参数:
            package_id: SBPACK包ID
            normalized_text: 规范化原文
            chunks: 文本块

        返回:
            技能列表
        """
        logger.info(f"开始技能轨提取，package_id={package_id}")

        # 记录输入快照
        input_snapshot = self._create_input_snapshot(normalized_text, chunks)

        # 阶段1: 五类扫描，生成候选池
        candidates = []

        # 1. 框架提取
        framework_candidates = self._extract_frameworks(chunks)
        candidates.extend(framework_candidates)

        # 2. 原则提取
        principle_candidates = self._extract_principles(chunks)
        candidates.extend(principle_candidates)

        # 3. 案例提取
        case_candidates = self._extract_cases(chunks)
        candidates.extend(case_candidates)

        # 4. 反例提取
        counterexample_candidates = self._extract_counterexamples(chunks)
        candidates.extend(counterexample_candidates)

        # 5. 术语提取
        term_candidates = self._extract_terms(chunks)
        candidates.extend(term_candidates)

        logger.info(f"五类扫描完成，候选数={len(candidates)}")

        # 阶段2: 三项验证
        verified_skills = []

        for candidate in candidates:
            # V1: 原文支持充分
            v1_result = self._verify_v1(candidate, chunks)
            if not v1_result["passed"]:
                candidate["rejection_reason"] = f"V1未通过: {v1_result['reason']}"
                continue

            # V2: 可迁移且可执行
            v2_result = self._verify_v2(candidate)
            if not v2_result["passed"]:
                candidate["rejection_reason"] = f"V2未通过: {v2_result['reason']}"
                continue

            # V3: 具有具体方法价值
            v3_result = self._verify_v3(candidate)
            if not v3_result["passed"]:
                candidate["rejection_reason"] = f"V3未通过: {v3_result['reason']}"
                continue

            # 通过所有验证
            candidate["v1_passed"] = True
            candidate["v2_passed"] = True
            candidate["v3_passed"] = True
            candidate["v1_evidence_route"] = v1_result.get("route", "A")

            verified_skills.append(candidate)

        logger.info(f"三项验证完成，通过数={len(verified_skills)}")

        # 阶段3: 生成RIA++结构
        skills_with_ria = []

        for skill in verified_skills:
            ria_skill = self._build_ria_structure(skill, chunks)
            skills_with_ria.append(ria_skill)

        # 阶段4: 生成压力测试
        final_skills = []

        for skill in skills_with_ria:
            # 生成压力测试
            pressure_tests = self._generate_pressure_tests(skill, skills_with_ria)
            skill["pressure_tests"] = pressure_tests

            # 生成canonical SKILL.md
            canonical_content = self._generate_skill_md(skill)
            skill["canonical_content"] = canonical_content
            skill["canonical_sha256"] = hashlib.sha256(canonical_content.encode()).hexdigest()

            final_skills.append(skill)

        # 记录输出快照
        output_snapshot = self._create_output_snapshot(final_skills, candidates)

        # 保存生产者快照
        self._save_producer_snapshot(package_id, input_snapshot, output_snapshot)

        logger.info(f"技能轨提取完成，最终技能数={len(final_skills)}")

        return final_skills

    # ==================== 五类提取器 ====================

    def _extract_frameworks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """框架提取器 - 系统性方法论"""
        candidates = []

        # 框架标识词
        FRAMEWORK_INDICATORS = [
            "方法", "流程", "步骤", "框架", "系统",
            "如何", "怎样", "方式", "策略", "模型",
            "第一步", "第二步", "首先", "然后", "最后",
            "framework", "method", "process", "approach", "system"
        ]

        for chunk in chunks:
            text = chunk.get("content", "")
            chunk_id = chunk.get("id")

            # 检查是否包含框架标识
            has_indicator = any(indicator in text for indicator in FRAMEWORK_INDICATORS)

            # 检查是否包含步骤序列
            has_steps = self._detect_steps(text)

            if (has_indicator or has_steps) and len(text) > 50:
                candidate = {
                    "candidate_id": f"framework_{chunk_id}_{self._hash_short(text[:50])}",
                    "type": "framework",
                    "title": self._extract_title(text),
                    "source_chunks": [chunk_id],
                    "raw_content": text,
                    "evidence_type": "framework"
                }
                candidates.append(candidate)

        return candidates

    def _extract_principles(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """原则提取器 - 指导性原则"""
        candidates = []

        PRINCIPLE_INDICATORS = [
            "原则", "法则", "规律", "准则", "定律",
            "应该", "必须", "不应该", "禁止",
            "关键是", "重要的是", "核心在于",
            "principle", "rule", "law", "guideline"
        ]

        for chunk in chunks:
            text = chunk.get("content", "")
            chunk_id = chunk.get("id")

            has_indicator = any(indicator in text for indicator in PRINCIPLE_INDICATORS)

            if has_indicator and len(text) > 30:
                candidate = {
                    "candidate_id": f"principle_{chunk_id}_{self._hash_short(text[:50])}",
                    "type": "principle",
                    "title": self._extract_title(text),
                    "source_chunks": [chunk_id],
                    "raw_content": text,
                    "evidence_type": "principle"
                }
                candidates.append(candidate)

        return candidates

    def _extract_cases(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """案例提取器 - 具体实践案例"""
        candidates = []

        CASE_INDICATORS = [
            "案例", "例子", "实例", "例如", "比如",
            "曾经", "有一次", "那时候", "经历", "故事",
            "case", "example", "instance", "for example"
        ]

        for chunk in chunks:
            text = chunk.get("content", "")
            chunk_id = chunk.get("id")

            has_indicator = any(indicator in text for indicator in CASE_INDICATORS)

            if has_indicator and len(text) > 40:
                candidate = {
                    "candidate_id": f"case_{chunk_id}_{self._hash_short(text[:50])}",
                    "type": "case",
                    "title": self._extract_title(text),
                    "source_chunks": [chunk_id],
                    "raw_content": text,
                    "evidence_type": "case"
                }
                candidates.append(candidate)

        return candidates

    def _extract_counterexamples(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """反例提取器 - 失败模式"""
        candidates = []

        COUNTER_INDICATORS = [
            "反例", "失败", "错误", "陷阱", "误区",
            "不要", "避免", "禁止", "常见错误",
            "counterexample", "failure", "mistake", "pitfall"
        ]

        for chunk in chunks:
            text = chunk.get("content", "")
            chunk_id = chunk.get("id")

            has_indicator = any(indicator in text for indicator in COUNTER_INDICATORS)

            if has_indicator and len(text) > 30:
                candidate = {
                    "candidate_id": f"counter_{chunk_id}_{self._hash_short(text[:50])}",
                    "type": "counterexample",
                    "title": self._extract_title(text),
                    "source_chunks": [chunk_id],
                    "raw_content": text,
                    "evidence_type": "counterexample"
                }
                candidates.append(candidate)

        return candidates

    def _extract_terms(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """术语提取器 - 领域特定概念"""
        candidates = []

        # 术语通常以定义形式出现
        TERM_INDICATORS = [
            "是指", "指的是", "定义为", "称为",
            "所谓", "即", "也就是说"
        ]

        for chunk in chunks:
            text = chunk.get("content", "")
            chunk_id = chunk.get("id")

            has_indicator = any(indicator in text for indicator in TERM_INDICATORS)

            # 术语定义通常较短
            if has_indicator and 20 < len(text) < 150:
                candidate = {
                    "candidate_id": f"term_{chunk_id}_{self._hash_short(text[:50])}",
                    "type": "term",
                    "title": self._extract_title(text),
                    "source_chunks": [chunk_id],
                    "raw_content": text,
                    "evidence_type": "term"
                }
                candidates.append(candidate)

        return candidates

    # ==================== 三项验证 ====================

    def _verify_v1(self, candidate: Dict[str, Any],
                  chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        V1验证：原文支持充分

        两条路线之一：
        A: 两个独立语境支持同一方法
        B: 单处完整论述（方法+条件+应用）
        """
        source_chunks = candidate.get("source_chunks", [])

        # 路线A: 检查是否有多个独立证据
        if len(source_chunks) >= 2:
            return {
                "passed": True,
                "route": "A",
                "reason": f"发现{len(source_chunks)}个独立证据"
            }

        # 路线B: 检查单处是否完整
        if len(source_chunks) == 1:
            chunk_id = source_chunks[0]
            chunk = next((c for c in chunks if c.get("id") == chunk_id), None)

            if chunk:
                text = chunk.get("content", "")

                # 检查是否包含方法、条件、应用
                has_method = len(text) > 50  # 简化判断
                has_condition = any(kw in text for kw in ["如果", "当", "在...情况下", "条件"])
                has_application = any(kw in text for kw in ["应用", "实践", "使用", "例如"])

                if has_method and (has_condition or has_application):
                    return {
                        "passed": True,
                        "route": "B",
                        "reason": "单处完整论述，包含方法和应用依据"
                    }

        return {
            "passed": False,
            "reason": "原文支持不足，既无独立证据也无完整论述"
        }

    def _verify_v2(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        """V2验证：可迁移且可执行"""
        raw_content = candidate.get("raw_content", "")

        # 检查是否包含可执行的步骤或方法
        has_steps = self._detect_steps(raw_content)
        has_action_verbs = any(verb in raw_content for verb in [
            "做", "执行", "实施", "操作", "应用",
            "分析", "判断", "选择", "评估", "检查"
        ])

        # 检查是否仅是建议而非方法
        is_only_suggestion = all(word in raw_content for word in ["建议", "可以"]) and \
                            not has_steps

        if has_steps or (has_action_verbs and not is_only_suggestion):
            return {
                "passed": True,
                "reason": "包含可执行的方法或步骤"
            }

        return {
            "passed": False,
            "reason": "缺少可执行的方法，仅有解释或建议"
        }

    def _verify_v3(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        """V3验证：具有具体方法价值"""
        raw_content = candidate.get("raw_content", "")
        title = candidate.get("title", "")

        # 排除一般常识
        GENERIC_PHRASES = [
            "努力", "坚持", "认真", "仔细", "多思考",
            "注意", "重视", "加强", "提高"
        ]

        is_generic = any(phrase in title or phrase in raw_content for phrase in GENERIC_PHRASES)

        # 检查是否有具体判断规则或机制
        has_specific_rule = any(kw in raw_content for kw in [
            "具体", "判断", "标准", "指标", "规则",
            "机制", "原理", "模型", "公式", "算法"
        ])

        if not is_generic and has_specific_rule:
            return {
                "passed": True,
                "reason": "包含具体判断规则或方法价值"
            }

        if is_generic:
            return {
                "passed": False,
                "reason": "属于一般常识，缺少独特方法价值"
            }

        return {
            "passed": False,
            "reason": "缺少足够的具体性和方法价值"
        }

    # ==================== RIA++构建 ====================

    def _build_ria_structure(self, skill: Dict[str, Any],
                            chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """构建RIA++结构"""
        raw_content = skill.get("raw_content", "")
        skill_type = skill.get("type", "")

        # R: Rationale - 为什么需要这个技能
        rationale = self._extract_rationale(raw_content, skill_type)

        # I: Interpretation - 核心逻辑
        interpretation = self._extract_interpretation(raw_content)

        # A1: Application Original - 原始应用场景
        application_original = self._extract_original_application(raw_content)

        # A2: Application Future - 未来可扩展应用
        application_future = self._generate_future_application(raw_content, skill_type)

        # E: Execution - 执行步骤
        execution = self._extract_execution_steps(raw_content)

        # B: Boundaries - 不适用场景
        boundaries = self._extract_boundaries(raw_content)

        skill.update({
            "rationale": rationale,
            "interpretation": interpretation,
            "application_original": application_original,
            "application_future": application_future,
            "execution": execution,
            "boundaries": boundaries
        })

        return skill

    def _extract_rationale(self, text: str, skill_type: str) -> str:
        """提取rationale"""
        # 根据技能类型生成rationale
        type_rationales = {
            "framework": "提供系统性的方法框架，帮助结构化解决问题",
            "principle": "提供指导性原则，帮助做出正确决策",
            "case": "提供实践案例，帮助理解具体应用",
            "counterexample": "识别失败模式，帮助避免常见错误",
            "term": "理解关键概念，帮助准确沟通和思考"
        }

        return type_rationales.get(skill_type, "解决特定问题的方法")

    def _extract_interpretation(self, text: str) -> str:
        """提取interpretation"""
        # 简化版：返回核心内容
        return text[:500] if len(text) > 500 else text

    def _extract_original_application(self, text: str) -> str:
        """提取原始应用场景"""
        # 查找应用相关内容
        application_keywords = ["应用", "使用", "实践", "场景", "例如", "比如"]

        for keyword in application_keywords:
            if keyword in text:
                idx = text.find(keyword)
                return text[idx:idx+200]

        return "原文描述的应用场景"

    def _generate_future_application(self, text: str, skill_type: str) -> str:
        """生成未来应用"""
        return f"可以扩展到相似场景和领域，需要根据具体情况调整"

    def _extract_execution_steps(self, text: str) -> List[str]:
        """提取执行步骤"""
        steps = []

        # 检测步骤标记
        step_markers = ["第一", "第二", "第三", "首先", "然后", "接着", "最后"]

        sentences = text.split("。")
        for sentence in sentences:
            if any(marker in sentence for marker in step_markers):
                steps.append(sentence.strip())

        if not steps:
            # 如果没有明确步骤，将内容分段
            steps = [text[i:i+100] for i in range(0, min(len(text), 300), 100)]

        return steps[:10]  # 最多10个步骤

    def _extract_boundaries(self, text: str) -> str:
        """提取边界"""
        boundary_keywords = ["不适用", "不能", "禁止", "避免", "例外", "限制"]

        for keyword in boundary_keywords:
            if keyword in text:
                idx = text.find(keyword)
                return text[idx:idx+150]

        return "超出特定条件时需要谨慎使用"

    # ==================== 压力测试生成 ====================

    def _generate_pressure_tests(self, skill: Dict[str, Any],
                                 all_skills: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成压力测试"""
        tests = {
            "should_trigger": [],
            "should_not_trigger": [],
            "boundary_cases": []
        }

        skill_title = skill.get("title", "")
        skill_type = skill.get("type", "")

        # 生成should_trigger测试
        tests["should_trigger"].append(f"明确需要{skill_title}的场景")
        tests["should_trigger"].append(f"典型的{skill_type}应用情况")

        # 生成should_not_trigger测试
        tests["should_not_trigger"].append(f"不需要{skill_title}的常规场景")
        tests["should_not_trigger"].append(f"与{skill_title}无关的任务")

        # 生成boundary_cases测试
        tests["boundary_cases"].append(f"{skill_title}边界模糊的场景")

        # 添加兄弟技能混淆测试
        similar_skills = [s for s in all_skills if s.get("type") == skill_type and s.get("title") != skill_title]
        if similar_skills and len(similar_skills) > 0:
            sibling = similar_skills[0]
            tests["boundary_cases"].append(f"容易与'{sibling.get('title')}'混淆的场景")

        return tests

    # ==================== SKILL.md生成 ====================

    def _generate_skill_md(self, skill: Dict[str, Any]) -> str:
        """生成canonical SKILL.md"""
        skill_id = skill.get("candidate_id", "")
        name = skill.get("title", "")
        description = f"{name} - {skill.get('type', '')}"[:300]  # 最多300字符

        md_content = f"""---
name: {skill_id}
display_name: {name}
description: {description}
version: 1.0.0
cangjie_version: {self.CANGJIE_VERSION}
strategy: {self.STRATEGY}
---

# {name}

## Rationale (R)

{skill.get('rationale', '')}

## Interpretation (I)

{skill.get('interpretation', '')}

## Application - Original (A1)

{skill.get('application_original', '')}

## Application - Future (A2)

{skill.get('application_future', '')}

## Execution (E)

"""

        # 添加执行步骤
        for i, step in enumerate(skill.get('execution', []), 1):
            md_content += f"{i}. {step}\n"

        md_content += f"""

## Boundaries (B)

{skill.get('boundaries', '')}

## Evidence

- Source Chunks: {', '.join(map(str, skill.get('source_chunks', [])))}
- Evidence Type: {skill.get('evidence_type', '')}
- V1 Route: {skill.get('v1_evidence_route', 'A')}

## Verification

- V1 Passed: {skill.get('v1_passed', False)}
- V2 Passed: {skill.get('v2_passed', False)}
- V3 Passed: {skill.get('v3_passed', False)}

## Pressure Tests

### Should Trigger

"""

        for test in skill.get('pressure_tests', {}).get('should_trigger', []):
            md_content += f"- {test}\n"

        md_content += "\n### Should Not Trigger\n\n"

        for test in skill.get('pressure_tests', {}).get('should_not_trigger', []):
            md_content += f"- {test}\n"

        md_content += "\n### Boundary Cases\n\n"

        for test in skill.get('pressure_tests', {}).get('boundary_cases', []):
            md_content += f"- {test}\n"

        return md_content

    # ==================== 辅助方法 ====================

    def _detect_steps(self, text: str) -> bool:
        """检测是否包含步骤序列"""
        step_patterns = [
            "第一", "第二", "第三", "第四", "第五",
            "首先", "然后", "接着", "最后",
            "1.", "2.", "3.",
            "步骤1", "步骤2"
        ]

        count = sum(1 for pattern in step_patterns if pattern in text)
        return count >= 2

    def _extract_title(self, text: str) -> str:
        """提取标题"""
        # 取前50字符作为标题
        title = text[:50].strip()
        if len(text) > 50:
            title += "..."
        return title

    def _hash_short(self, text: str) -> str:
        """生成短哈希"""
        return hashlib.sha256(text.encode()).hexdigest()[:8]

    def _create_input_snapshot(self, normalized_text: str,
                              chunks: List[Dict[str, Any]]) -> str:
        """创建输入快照"""
        snapshot = {
            "normalized_text_length": len(normalized_text),
            "normalized_text_hash": hashlib.sha256(normalized_text.encode()).hexdigest(),
            "chunk_count": len(chunks),
            "cangjie_version": self.CANGJIE_VERSION,
            "strategy": self.STRATEGY,
            "timestamp": datetime.utcnow().isoformat()
        }
        return json.dumps(snapshot, ensure_ascii=False)

    def _create_output_snapshot(self, final_skills: List[Dict[str, Any]],
                               candidates: List[Dict[str, Any]]) -> str:
        """创建输出快照"""
        snapshot = {
            "candidate_count": len(candidates),
            "final_skill_count": len(final_skills),
            "candidate_types": {},
            "skill_ids": [s.get("candidate_id") for s in final_skills],
            "timestamp": datetime.utcnow().isoformat()
        }

        # 统计候选类型
        for candidate in candidates:
            c_type = candidate.get("type", "unknown")
            snapshot["candidate_types"][c_type] = snapshot["candidate_types"].get(c_type, 0) + 1

        return json.dumps(snapshot, ensure_ascii=False)

    def _save_producer_snapshot(self, package_id: int,
                                input_snapshot: str,
                                output_snapshot: str):
        """保存生产者快照"""
        combined = input_snapshot + output_snapshot
        snapshot_hash = hashlib.sha256(combined.encode()).hexdigest()

        snapshot = ProducerSnapshot(
            package_id=package_id,
            role="skill_track",
            input_snapshot=input_snapshot,
            output_snapshot=output_snapshot,
            model_name=self.producer_name,
            model_version=self.producer_version,
            snapshot_hash=snapshot_hash
        )

        self.db.add(snapshot)
        self.db.commit()

        logger.info(f"技能轨生产者快照已保存，hash={snapshot_hash[:16]}...")
