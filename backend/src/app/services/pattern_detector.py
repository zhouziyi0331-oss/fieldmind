"""
模式识别服务

自动从执行历史中识别可复用模式
"""
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, desc, func
import json
import numpy as np
from collections import defaultdict

from app.models.pattern_library import (
    PatternLibrary,
    PatternMatch,
    PatternCluster,
    PatternStatus,
    PatternType
)
from app.models.execution_record import ExecutionRecord, ExecutionStatus


class PatternDetector:
    """模式检测器 - 从执行历史中识别模式"""
    def __init__(self, db: Session, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.db = db

    # ==================== 模式检测 ====================

    def detect_patterns(
        self,
        project_id: int,
        min_occurrences: int = 3,
        min_confidence: float = 0.7,
        lookback_days: int = 30
    ) -> List[PatternLibrary]:
        """
        检测项目中的模式

        Args:
            project_id: 项目ID
            min_occurrences: 最小出现次数
            min_confidence: 最小置信度
            lookback_days: 回溯天数

        Returns:
            检测到的模式列表
        """
        # 获取历史成功执行
        start_date = datetime.utcnow() - timedelta(days=lookback_days)

        executions = self.db.query(ExecutionRecord).filter(
            and_(
                ExecutionRecord.project_id == project_id,
                ExecutionRecord.status == ExecutionStatus.SUCCESS,
                ExecutionRecord.quality_score >= 0.7,
                ExecutionRecord.completed_at >= start_date
            )
        ).all()

        if len(executions) < min_occurrences:
            return []

        # 检测不同类型的模式
        detected_patterns = []

        # 1. 检测序列模式
        sequence_patterns = self._detect_sequence_patterns(
            executions,
            min_occurrences
        )
        detected_patterns.extend(sequence_patterns)

        # 2. 检测条件模式
        condition_patterns = self._detect_condition_patterns(
            executions,
            min_occurrences
        )
        detected_patterns.extend(condition_patterns)

        # 3. 检测策略模式
        strategy_patterns = self._detect_strategy_patterns(
            executions,
            min_occurrences
        )
        detected_patterns.extend(strategy_patterns)

        # 过滤并保存模式
        validated_patterns = []
        for pattern_data in detected_patterns:
            if pattern_data['confidence'] >= min_confidence:
                pattern = self._create_or_update_pattern(
                    project_id,
                    pattern_data
                )
                validated_patterns.append(pattern)

        return validated_patterns

    def _detect_sequence_patterns(
        self,
        executions: List[ExecutionRecord],
        min_occurrences: int
    ) -> List[Dict[str, Any]]:
        """检测序列模式（步骤顺序）"""
        # 提取执行步骤序列
        sequences = []
        for exec_record in executions:
            if exec_record.execution_steps:
                steps = [
                    step.get('step_name', '')
                    for step in exec_record.execution_steps
                ]
                if steps:
                    sequences.append({
                        'steps': steps,
                        'execution': exec_record
                    })

        # 查找重复的序列
        sequence_counts = defaultdict(list)
        for seq_data in sequences:
            steps_key = tuple(seq_data['steps'])
            sequence_counts[steps_key].append(seq_data['execution'])

        # 构建模式
        patterns = []
        for steps, exec_list in sequence_counts.items():
            if len(exec_list) >= min_occurrences:
                pattern = self._build_sequence_pattern(
                    list(steps),
                    exec_list
                )
                patterns.append(pattern)

        return patterns

    def _build_sequence_pattern(
        self,
        steps: List[str],
        executions: List[ExecutionRecord]
    ) -> Dict[str, Any]:
        """构建序列模式"""
        # 计算统计信息
        avg_duration = np.mean([
            e.duration_seconds for e in executions
            if e.duration_seconds
        ]) if executions else 0

        avg_quality = np.mean([
            e.quality_score for e in executions
            if e.quality_score
        ]) if executions else 0

        # 提取共同特征
        common_features = self._extract_common_features(executions)

        return {
            'name': f"sequence_{hash(tuple(steps)) % 10000}",
            'type': PatternType.SEQUENCE,
            'description': f"序列模式：{' → '.join(steps[:3])}{'...' if len(steps) > 3 else ''}",
            'definition': {
                'type': 'sequence',
                'steps': [{'action': step} for step in steps],
                'preconditions': common_features.get('preconditions', []),
                'postconditions': ['has_result']
            },
            'features': common_features,
            'applicable_scenarios': self._extract_scenarios(executions),
            'confidence': min(1.0, len(executions) / 10),
            'avg_duration': avg_duration,
            'avg_quality': avg_quality,
            'source_ids': [e.id for e in executions]
        }

    def _detect_condition_patterns(
        self,
        executions: List[ExecutionRecord],
        min_occurrences: int
    ) -> List[Dict[str, Any]]:
        """检测条件模式（if-then）"""
        patterns = []

        # 按输入特征分组
        feature_groups = defaultdict(list)
        for exec_record in executions:
            if exec_record.extracted_features:
                features = exec_record.extracted_features
                input_type = features.get('input_complexity', 'unknown')
                feature_groups[input_type].append(exec_record)

        # 为每个特征组识别共同行为
        for input_type, exec_list in feature_groups.items():
            if len(exec_list) >= min_occurrences:
                pattern = self._build_condition_pattern(
                    input_type,
                    exec_list
                )
                patterns.append(pattern)

        return patterns

    def _build_condition_pattern(
        self,
        condition: str,
        executions: List[ExecutionRecord]
    ) -> Dict[str, Any]:
        """构建条件模式"""
        # 分析共同的处理方式
        common_steps = self._find_common_steps(executions)

        return {
            'name': f"condition_{condition}_{hash(condition) % 10000}",
            'type': PatternType.CONDITION,
            'description': f"条件模式：当输入为{condition}时的处理方式",
            'definition': {
                'type': 'condition',
                'if': {'input_complexity': condition},
                'then': {'steps': common_steps},
                'confidence_threshold': 0.7
            },
            'features': {'input_condition': condition},
            'applicable_scenarios': {
                'input_complexity': [condition]
            },
            'confidence': min(1.0, len(executions) / 8),
            'source_ids': [e.id for e in executions]
        }

    def _detect_strategy_patterns(
        self,
        executions: List[ExecutionRecord],
        min_occurrences: int
    ) -> List[Dict[str, Any]]:
        """检测策略模式（解决方案）"""
        patterns = []

        # 按执行类型分组
        type_groups = defaultdict(list)
        for exec_record in executions:
            exec_type = exec_record.execution_type.value
            type_groups[exec_type].append(exec_record)

        # 为每种类型识别最佳策略
        for exec_type, exec_list in type_groups.items():
            if len(exec_list) >= min_occurrences:
                # 找出高质量的执行
                high_quality = [
                    e for e in exec_list
                    if e.quality_score and e.quality_score >= 0.8
                ]

                if len(high_quality) >= min_occurrences:
                    pattern = self._build_strategy_pattern(
                        exec_type,
                        high_quality
                    )
                    patterns.append(pattern)

        return patterns

    def _build_strategy_pattern(
        self,
        strategy_name: str,
        executions: List[ExecutionRecord]
    ) -> Dict[str, Any]:
        """构建策略模式"""
        # 提取成功策略的共同点
        success_factors = []
        for exec_record in executions:
            if exec_record.extracted_features:
                factors = exec_record.extracted_features.get('success_factors', [])
                success_factors.extend(factors)

        # 统计最常见的成功因素
        factor_counts = defaultdict(int)
        for factor in success_factors:
            factor_counts[factor] += 1

        common_factors = [
            factor for factor, count in factor_counts.items()
            if count >= len(executions) * 0.5
        ]

        return {
            'name': f"strategy_{strategy_name}_{hash(strategy_name) % 10000}",
            'type': PatternType.STRATEGY,
            'description': f"策略模式：{strategy_name}的最佳实践",
            'definition': {
                'type': 'strategy',
                'approach': strategy_name,
                'success_factors': common_factors,
                'recommended_steps': self._find_common_steps(executions)
            },
            'features': {
                'strategy_type': strategy_name,
                'success_factors': common_factors
            },
            'applicable_scenarios': {
                'execution_type': [strategy_name]
            },
            'confidence': min(1.0, len(executions) / 10),
            'source_ids': [e.id for e in executions]
        }

    # ==================== 辅助方法 ====================

    def _extract_common_features(
        self,
        executions: List[ExecutionRecord]
    ) -> Dict[str, Any]:
        """提取共同特征"""
        features = {
            'input_characteristics': [],
            'output_characteristics': [],
            'complexity': 'medium',
            'preconditions': []
        }

        # 分析输入复杂度分布
        complexities = []
        for exec_record in executions:
            if exec_record.extracted_features:
                complexity = exec_record.extracted_features.get('input_complexity')
                if complexity:
                    complexities.append(complexity)

        if complexities:
            # 找出最常见的复杂度
            from collections import Counter
            most_common = Counter(complexities).most_common(1)
            if most_common:
                features['complexity'] = most_common[0][0]

        return features

    def _extract_scenarios(
        self,
        executions: List[ExecutionRecord]
    ) -> Dict[str, Any]:
        """提取适用场景"""
        return {
            'execution_types': list(set(e.execution_type.value for e in executions)),
            'typical_duration_range': {
                'min': min(e.duration_seconds for e in executions if e.duration_seconds),
                'max': max(e.duration_seconds for e in executions if e.duration_seconds)
            } if any(e.duration_seconds for e in executions) else None
        }

    def _find_common_steps(
        self,
        executions: List[ExecutionRecord]
    ) -> List[str]:
        """查找共同步骤"""
        all_steps = []
        for exec_record in executions:
            if exec_record.execution_steps:
                steps = [
                    step.get('step_name', '')
                    for step in exec_record.execution_steps
                ]
                all_steps.append(set(steps))

        if not all_steps:
            return []

        # 找出所有执行都有的步骤
        common = set.intersection(*all_steps) if all_steps else set()
        return list(common)

    def _create_or_update_pattern(
        self,
        project_id: int,
        pattern_data: Dict[str, Any]
    ) -> PatternLibrary:
        """创建或更新模式"""
        # 检查是否已存在相同模式
        existing = self.db.query(PatternLibrary).filter(
            and_(
                PatternLibrary.project_id == project_id,
                PatternLibrary.pattern_name == pattern_data['name']
            )
        ).first()

        if existing:
            # 更新现有模式
            existing.detection_count += 1
            existing.confidence_score = pattern_data['confidence']
            existing.avg_duration_seconds = pattern_data.get('avg_duration')
            existing.avg_quality_score = pattern_data.get('avg_quality')
            existing.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(existing)
            return existing

        # 创建新模式
        pattern = PatternLibrary(
            pattern_name=pattern_data['name'],
            pattern_type=pattern_data['type'],
            pattern_description=pattern_data['description'],
            project_id=project_id,
            pattern_definition=pattern_data['definition'],
            pattern_features=pattern_data['features'],
            applicable_scenarios=pattern_data['applicable_scenarios'],
            detection_count=1,
            confidence_score=pattern_data['confidence'],
            avg_duration_seconds=pattern_data.get('avg_duration'),
            avg_quality_score=pattern_data.get('avg_quality'),
            source_execution_ids=pattern_data['source_ids'],
            status=PatternStatus.DETECTED
        )

        self.db.add(pattern)
        self.db.commit()
        self.db.refresh(pattern)

        return pattern

    # ==================== 模式匹配 ====================

    def match_pattern(
        self,
        execution_id: str,
        min_match_score: float = 0.7
    ) -> List[Tuple[PatternLibrary, float]]:
        """
        为执行匹配合适的模式

        Args:
            execution_id: 执行记录ID
            min_match_score: 最小匹配分数

        Returns:
            匹配的模式列表（模式，匹配分数）
        """
        # 获取执行记录
        execution = self.db.query(ExecutionRecord).filter(
            ExecutionRecord.id == execution_id
        ).first()

        if not execution:
            return []

        # 获取项目的所有活跃模式
        patterns = self.db.query(PatternLibrary).filter(
            and_(
                PatternLibrary.project_id == execution.project_id,
                PatternLibrary.status.in_([
                    PatternStatus.VALIDATED,
                    PatternStatus.ACTIVE
                ])
            )
        ).all()

        # 计算匹配分数
        matches = []
        for pattern in patterns:
            score = self._calculate_match_score(execution, pattern)
            if score >= min_match_score:
                matches.append((pattern, score))

                # 记录匹配
                self._record_match(execution, pattern, score)

        # 按匹配分数排序
        matches.sort(key=lambda x: x[1], reverse=True)

        return matches

    def _calculate_match_score(
        self,
        execution: ExecutionRecord,
        pattern: PatternLibrary
    ) -> float:
        """计算执行和模式的匹配分数"""
        score = 0.0

        # 1. 执行类型匹配（30%）
        if execution.execution_type.value in pattern.applicable_scenarios.get('execution_types', []):
            score += 0.3

        # 2. 特征匹配（40%）
        if execution.extracted_features and pattern.pattern_features:
            exec_features = execution.extracted_features
            pattern_features = pattern.pattern_features

            # 复杂度匹配
            if exec_features.get('input_complexity') == pattern_features.get('complexity'):
                score += 0.2

            # 其他特征
            if exec_features.get('execution_type') == pattern_features.get('execution_type'):
                score += 0.2

        # 3. 历史质量（30%）
        if pattern.avg_success_rate:
            score += pattern.avg_success_rate * 0.3

        return min(1.0, score)

    def _record_match(
        self,
        execution: ExecutionRecord,
        pattern: PatternLibrary,
        match_score: float
    ):
        """记录模式匹配"""
        match = PatternMatch(
            pattern_id=pattern.id,
            execution_id=execution.id,
            user_id=execution.user_id,
            project_id=execution.project_id,
            match_score=match_score,
            match_reason={
                'matched_features': ['execution_type', 'complexity'],
                'overall_similarity': match_score
            }
        )

        self.db.add(match)
        self.db.commit()

    # ==================== 查询接口 ====================

    def get_patterns(
        self,
        project_id: int,
        pattern_type: Optional[PatternType] = None,
        status: Optional[PatternStatus] = None,
        min_confidence: float = 0.0
    ) -> List[PatternLibrary]:
        """获取模式列表"""
        query = self.db.query(PatternLibrary).filter(
            and_(
                PatternLibrary.project_id == project_id,
                PatternLibrary.confidence_score >= min_confidence
            )
        )

        if pattern_type:
            query = query.filter(PatternLibrary.pattern_type == pattern_type)

        if status:
            query = query.filter(PatternLibrary.status == status)

        return query.order_by(
            desc(PatternLibrary.confidence_score)
        ).all()

    def validate_pattern(
        self,
        pattern_id: str
    ) -> PatternLibrary:
        """验证模式"""
        pattern = self.db.query(PatternLibrary).filter(
            PatternLibrary.id == pattern_id
        ).first()

        if not pattern:
            raise ValueError(f"模式 {pattern_id} 不存在")

        pattern.status = PatternStatus.VALIDATED
        pattern.validated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(pattern)

        return pattern

    def activate_pattern(
        self,
        pattern_id: str
    ) -> PatternLibrary:
        """激活模式"""
        pattern = self.db.query(PatternLibrary).filter(
            PatternLibrary.id == pattern_id
        ).first()

        if not pattern:
            raise ValueError(f"模式 {pattern_id} 不存在")

        pattern.status = PatternStatus.ACTIVE
        pattern.activated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(pattern)

        return pattern
