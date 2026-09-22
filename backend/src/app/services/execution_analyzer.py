"""
执行分析服务

自动分析执行结果，提取特征，识别成功模式
"""
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, desc, func
import json
import hashlib

from app.models.execution_record import (
    ExecutionRecord,
    ExecutionStatus,
    ExecutionType,
    SuccessPattern
)


class ExecutionAnalyzer:
    """执行分析器 - 分析执行结果并提取特征"""
    def __init__(self, db: Session, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.db = db

    # ==================== 执行记录管理 ====================

    def record_execution(
        self,
        user_id: int,
        project_id: int,
        execution_type: ExecutionType,
        execution_name: str,
        input_data: Dict[str, Any],
        workflow_id: Optional[str] = None,
        skill_id: Optional[int] = None,
        task_id: Optional[str] = None,
        execution_description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ExecutionRecord:
        """
        记录执行开始

        Args:
            user_id: 用户ID
            project_id: 项目ID
            execution_type: 执行类型
            execution_name: 执行名称
            input_data: 输入数据
            workflow_id: 可选，工作流ID
            skill_id: 可选，技能ID
            task_id: 可选，任务ID
            execution_description: 可选，执行描述
            metadata: 可选，元数据

        Returns:
            创建的执行记录
        """
        record = ExecutionRecord(
            user_id=user_id,
            project_id=project_id,
            execution_type=execution_type,
            execution_name=execution_name,
            execution_description=execution_description,
            workflow_id=workflow_id,
            skill_id=skill_id,
            task_id=task_id,
            input_data=input_data,
            status=ExecutionStatus.RUNNING,
            started_at=datetime.utcnow(),
            metadata=metadata or {}
        )

        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)

        return record

    def update_execution_progress(
        self,
        execution_id: str,
        execution_steps: List[Dict[str, Any]]
    ) -> ExecutionRecord:
        """
        更新执行进度

        Args:
            execution_id: 执行记录ID
            execution_steps: 执行步骤列表

        Returns:
            更新后的执行记录
        """
        record = self.db.query(ExecutionRecord).filter(
            ExecutionRecord.id == execution_id
        ).first()

        if not record:
            raise ValueError(f"执行记录 {execution_id} 不存在")

        record.execution_steps = execution_steps
        record.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(record)

        return record

    def complete_execution(
        self,
        execution_id: str,
        status: ExecutionStatus,
        output_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        error_stack: Optional[str] = None,
        metrics: Optional[Dict[str, Any]] = None
    ) -> ExecutionRecord:
        """
        完成执行并记录结果

        Args:
            execution_id: 执行记录ID
            status: 执行状态
            output_data: 输出数据
            error_message: 错误信息
            error_stack: 错误堆栈
            metrics: 执行指标（duration, cpu_usage, memory_usage等）

        Returns:
            更新后的执行记录
        """
        record = self.db.query(ExecutionRecord).filter(
            ExecutionRecord.id == execution_id
        ).first()

        if not record:
            raise ValueError(f"执行记录 {execution_id} 不存在")

        # 更新状态和结果
        record.status = status
        record.output_data = output_data
        record.error_message = error_message
        record.error_stack = error_stack
        record.completed_at = datetime.utcnow()

        # 计算执行时长
        if record.started_at:
            duration = (record.completed_at - record.started_at).total_seconds()
            record.duration_seconds = duration

        # 更新指标
        if metrics:
            record.cpu_usage_percent = metrics.get('cpu_usage')
            record.memory_usage_mb = metrics.get('memory_usage')
            record.api_calls_count = metrics.get('api_calls', 0)
            record.tokens_used = metrics.get('tokens_used', 0)

        # 自动评估质量
        quality_score = self._calculate_quality_score(record)
        record.quality_score = quality_score

        # 提取特征
        features = self._extract_features(record)
        record.extracted_features = features

        record.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(record)

        # 如果是成功执行，尝试识别模式
        if status == ExecutionStatus.SUCCESS and quality_score and quality_score > 0.7:
            self._try_identify_pattern(record)

        return record

    # ==================== 结果分析 ====================

    def _calculate_quality_score(self, record: ExecutionRecord) -> float:
        """
        计算执行质量分数

        Args:
            record: 执行记录

        Returns:
            质量分数（0-1）
        """
        score = 0.0

        # 1. 状态得分（40%）
        if record.status == ExecutionStatus.SUCCESS:
            score += 0.4
        elif record.status == ExecutionStatus.PARTIAL_SUCCESS:
            score += 0.2
        else:
            score += 0.0

        # 2. 性能得分（30%）
        if record.duration_seconds:
            # 假设理想执行时间为30秒，超过会扣分
            if record.duration_seconds <= 30:
                score += 0.3
            elif record.duration_seconds <= 60:
                score += 0.2
            elif record.duration_seconds <= 120:
                score += 0.1

        # 3. 输出质量得分（30%）
        if record.output_data:
            # 检查输出数据的完整性
            if isinstance(record.output_data, dict):
                if record.output_data.get('result'):
                    score += 0.15
                if record.output_data.get('confidence', 0) > 0.7:
                    score += 0.15

        return min(1.0, score)

    def _extract_features(self, record: ExecutionRecord) -> Dict[str, Any]:
        """
        从执行记录中提取特征

        Args:
            record: 执行记录

        Returns:
            提取的特征字典
        """
        features = {
            "execution_type": record.execution_type.value,
            "duration_category": self._categorize_duration(record.duration_seconds),
            "input_complexity": self._analyze_input_complexity(record.input_data),
            "has_error": record.error_message is not None,
            "step_count": len(record.execution_steps) if record.execution_steps else 0,
        }

        # 成功因素
        success_factors = []
        failure_factors = []

        if record.status == ExecutionStatus.SUCCESS:
            # 分析成功原因
            if record.duration_seconds and record.duration_seconds < 60:
                success_factors.append("fast_execution")
            if record.quality_score and record.quality_score > 0.8:
                success_factors.append("high_quality")
            if record.execution_steps:
                success_factors.append("complete_steps")
        else:
            # 分析失败原因
            if record.error_message:
                failure_factors.append("has_error")
            if record.duration_seconds and record.duration_seconds > 300:
                failure_factors.append("timeout")

        features["success_factors"] = success_factors
        features["failure_factors"] = failure_factors

        return features

    def _categorize_duration(self, duration: Optional[float]) -> str:
        """分类执行时长"""
        if not duration:
            return "unknown"
        if duration < 10:
            return "very_fast"
        elif duration < 30:
            return "fast"
        elif duration < 60:
            return "medium"
        elif duration < 180:
            return "slow"
        else:
            return "very_slow"

    def _analyze_input_complexity(self, input_data: Dict[str, Any]) -> str:
        """分析输入复杂度"""
        if not input_data:
            return "empty"

        # 简单的复杂度估算
        data_size = len(json.dumps(input_data))

        if data_size < 100:
            return "simple"
        elif data_size < 1000:
            return "medium"
        else:
            return "complex"

    # ==================== 模式识别 ====================

    def _try_identify_pattern(self, record: ExecutionRecord):
        """
        尝试从成功执行中识别模式

        Args:
            record: 执行记录
        """
        # 查找相似的成功执行
        similar_executions = self._find_similar_executions(record)

        if len(similar_executions) >= 3:  # 至少需要3次相似的成功执行
            # 创建或更新模式
            self._create_or_update_pattern(record, similar_executions)

    def _find_similar_executions(
        self,
        record: ExecutionRecord,
        limit: int = 10
    ) -> List[ExecutionRecord]:
        """
        查找相似的执行记录

        Args:
            record: 参考执行记录
            limit: 返回数量

        Returns:
            相似执行记录列表
        """
        # 查询相同类型、相同项目的成功执行
        similar = self.db.query(ExecutionRecord).filter(
            and_(
                ExecutionRecord.project_id == record.project_id,
                ExecutionRecord.execution_type == record.execution_type,
                ExecutionRecord.status == ExecutionStatus.SUCCESS,
                ExecutionRecord.quality_score > 0.7,
                ExecutionRecord.id != record.id
            )
        ).order_by(
            desc(ExecutionRecord.completed_at)
        ).limit(limit).all()

        # 计算相似度并过滤
        filtered = []
        for exec_record in similar:
            similarity = self._calculate_similarity(record, exec_record)
            if similarity > 0.7:
                filtered.append(exec_record)

        return filtered

    def _calculate_similarity(
        self,
        record1: ExecutionRecord,
        record2: ExecutionRecord
    ) -> float:
        """
        计算两个执行记录的相似度

        Args:
            record1: 执行记录1
            record2: 执行记录2

        Returns:
            相似度（0-1）
        """
        similarity = 0.0

        # 1. 执行类型相同
        if record1.execution_type == record2.execution_type:
            similarity += 0.3

        # 2. 步骤数量相近
        steps1 = len(record1.execution_steps) if record1.execution_steps else 0
        steps2 = len(record2.execution_steps) if record2.execution_steps else 0
        if steps1 == steps2:
            similarity += 0.3
        elif abs(steps1 - steps2) <= 2:
            similarity += 0.15

        # 3. 特征相似
        if record1.extracted_features and record2.extracted_features:
            features1 = record1.extracted_features
            features2 = record2.extracted_features

            if features1.get('input_complexity') == features2.get('input_complexity'):
                similarity += 0.2

            if features1.get('duration_category') == features2.get('duration_category'):
                similarity += 0.2

        return similarity

    def _create_or_update_pattern(
        self,
        record: ExecutionRecord,
        similar_executions: List[ExecutionRecord]
    ):
        """
        创建或更新成功模式

        Args:
            record: 当前执行记录
            similar_executions: 相似执行记录列表
        """
        # 生成模式签名
        pattern_signature = self._generate_pattern_signature(
            record,
            similar_executions
        )

        # 计算签名哈希
        signature_hash = hashlib.md5(
            json.dumps(pattern_signature, sort_keys=True).encode()
        ).hexdigest()

        # 查找是否已存在相同模式
        existing_pattern = self.db.query(SuccessPattern).filter(
            and_(
                SuccessPattern.project_id == record.project_id,
                SuccessPattern.pattern_type == record.execution_type.value
            )
        ).all()

        # 简单匹配（实际应该用更复杂的算法）
        pattern = None
        for p in existing_pattern:
            if self._patterns_match(pattern_signature, p.pattern_signature):
                pattern = p
                break

        if pattern:
            # 更新现有模式
            pattern.occurrence_count += 1
            pattern.success_count += 1
            pattern.last_observed_at = datetime.utcnow()

            # 更新置信度
            pattern.confidence_score = pattern.success_count / pattern.occurrence_count

            # 添加源执行ID
            source_ids = pattern.source_execution_ids
            if record.id not in source_ids:
                source_ids.append(record.id)
                pattern.source_execution_ids = source_ids

        else:
            # 创建新模式
            pattern = SuccessPattern(
                pattern_name=f"{record.execution_type.value}_{signature_hash[:8]}",
                pattern_description=f"成功执行模式：{record.execution_name}",
                pattern_type=record.execution_type.value,
                project_id=record.project_id,
                user_id=record.user_id,
                pattern_signature=pattern_signature,
                applicable_contexts=self._extract_applicable_contexts(
                    record,
                    similar_executions
                ),
                occurrence_count=len(similar_executions) + 1,
                success_count=len(similar_executions) + 1,
                confidence_score=1.0,
                source_execution_ids=[r.id for r in similar_executions] + [record.id]
            )
            self.db.add(pattern)

        self.db.commit()

    def _generate_pattern_signature(
        self,
        record: ExecutionRecord,
        similar_executions: List[ExecutionRecord]
    ) -> Dict[str, Any]:
        """生成模式签名"""
        all_records = [record] + similar_executions

        # 提取共同特征
        common_features = {
            "execution_type": record.execution_type.value,
            "typical_duration": sum(
                r.duration_seconds for r in all_records if r.duration_seconds
            ) / len(all_records),
            "typical_steps": len(record.execution_steps) if record.execution_steps else 0,
        }

        return common_features

    def _extract_applicable_contexts(
        self,
        record: ExecutionRecord,
        similar_executions: List[ExecutionRecord]
    ) -> Dict[str, Any]:
        """提取适用场景"""
        return {
            "execution_type": record.execution_type.value,
            "min_quality_score": 0.7,
            "typical_input_complexity": record.extracted_features.get('input_complexity')
            if record.extracted_features else "unknown"
        }

    def _patterns_match(
        self,
        signature1: Dict[str, Any],
        signature2: Dict[str, Any]
    ) -> bool:
        """判断两个模式签名是否匹配"""
        if signature1.get('execution_type') != signature2.get('execution_type'):
            return False

        # 简单匹配逻辑
        return True

    # ==================== 查询接口 ====================

    def get_execution_records(
        self,
        project_id: int,
        execution_type: Optional[ExecutionType] = None,
        status: Optional[ExecutionStatus] = None,
        limit: int = 100
    ) -> List[ExecutionRecord]:
        """获取执行记录列表"""
        query = self.db.query(ExecutionRecord).filter(
            ExecutionRecord.project_id == project_id
        )

        if execution_type:
            query = query.filter(ExecutionRecord.execution_type == execution_type)

        if status:
            query = query.filter(ExecutionRecord.status == status)

        return query.order_by(desc(ExecutionRecord.started_at)).limit(limit).all()

    def get_success_patterns(
        self,
        project_id: int,
        pattern_type: Optional[str] = None,
        min_confidence: float = 0.7
    ) -> List[SuccessPattern]:
        """获取成功模式列表"""
        query = self.db.query(SuccessPattern).filter(
            and_(
                SuccessPattern.project_id == project_id,
                SuccessPattern.confidence_score >= min_confidence
            )
        )

        if pattern_type:
            query = query.filter(SuccessPattern.pattern_type == pattern_type)

        return query.order_by(
            desc(SuccessPattern.confidence_score)
        ).all()
