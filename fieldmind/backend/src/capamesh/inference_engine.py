"""
Inference Engine - 推理引擎

功能：
1. 执行视图中定义的推理逻辑
2. 支持多种推理类型：
   - aggregation: 聚合计算
   - scoring: 评分计算
   - classification: 分类判断
   - derivation: 派生字段计算
3. 基于依赖关系按顺序执行推理
"""

import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class InferenceEngine:
    """推理引擎"""

    def __init__(self):
        """初始化推理引擎"""
        self.inference_functions = {
            'aggregation': self._execute_aggregation,
            'scoring': self._execute_scoring,
            'classification': self._execute_classification,
            'derivation': self._execute_derivation,
            'computation': self._execute_computation,
        }

    async def execute_inference(self, view: Dict, output_data: Dict) -> Dict[str, Any]:
        """
        执行视图中的所有推理逻辑

        Args:
            view: 视图定义
            output_data: 当前输出数据

        Returns:
            更新后的输出数据
        """
        inference_logic = view.get('inference_logic', {})

        # 按依赖关系排序推理逻辑
        sorted_logic = self._topological_sort(inference_logic)

        # 依次执行推理
        for logic_name in sorted_logic:
            logic_def = inference_logic[logic_name]
            logic_type = logic_def.get('type')
            depends_on = logic_def.get('depends_on', [])

            # 检查依赖是否满足
            dependencies_met = all(
                output_data.get(dep) is not None
                for dep in depends_on
            )

            if not dependencies_met:
                logger.warning(f"依赖未满足，跳过推理: {logic_name}")
                continue

            # 执行推理
            try:
                inference_func = self.inference_functions.get(logic_type)
                if inference_func:
                    result = await inference_func(logic_def, output_data)
                    # 将结果写回 output_data
                    target_field = logic_def.get('target_field', logic_name)
                    output_data[target_field] = result
                    logger.info(f"✅ 推理完成: {logic_name} -> {target_field}")
                else:
                    logger.warning(f"未知的推理类型: {logic_type}")
            except Exception as e:
                logger.error(f"推理执行错误 {logic_name}: {e}", exc_info=True)

        return output_data

    def _topological_sort(self, inference_logic: Dict) -> List[str]:
        """
        拓扑排序推理逻辑，确保按依赖顺序执行

        Args:
            inference_logic: 推理逻辑定义

        Returns:
            排序后的推理逻辑名称列表
        """
        # 简单实现：按依赖深度排序
        def get_depth(logic_name: str, visited: set = None) -> int:
            if visited is None:
                visited = set()

            if logic_name in visited:
                return 0  # 避免循环依赖

            visited.add(logic_name)

            logic_def = inference_logic.get(logic_name, {})
            depends_on = logic_def.get('depends_on', [])

            if not depends_on:
                return 0

            max_depth = 0
            for dep in depends_on:
                if dep in inference_logic:
                    depth = get_depth(dep, visited.copy())
                    max_depth = max(max_depth, depth + 1)

            return max_depth

        # 计算每个推理的深度并排序
        logic_with_depth = [
            (logic_name, get_depth(logic_name))
            for logic_name in inference_logic.keys()
        ]

        logic_with_depth.sort(key=lambda x: x[1])

        return [name for name, _ in logic_with_depth]

    async def _execute_aggregation(self, logic_def: Dict, output_data: Dict) -> Any:
        """
        执行聚合推理

        示例：
        {
            "type": "aggregation",
            "depends_on": ["related_assets"],
            "operation": "count",
            "source_field": "related_assets"
        }
        """
        operation = logic_def.get('operation', 'count')
        source_field = logic_def.get('source_field')

        if not source_field or source_field not in output_data:
            return None

        data = output_data[source_field]

        if operation == 'count':
            if isinstance(data, list):
                return len(data)
            elif isinstance(data, dict):
                return len(data.get('records', []))
            else:
                return 0

        elif operation == 'sum':
            if isinstance(data, list):
                sum_field = logic_def.get('sum_field')
                if sum_field:
                    return sum(item.get(sum_field, 0) for item in data if isinstance(item, dict))
                return sum(data)
            return 0

        elif operation == 'average':
            if isinstance(data, list):
                avg_field = logic_def.get('avg_field')
                if avg_field:
                    values = [item.get(avg_field, 0) for item in data if isinstance(item, dict)]
                    return sum(values) / len(values) if values else 0
                return sum(data) / len(data) if data else 0
            return 0

        elif operation == 'max':
            if isinstance(data, list):
                max_field = logic_def.get('max_field')
                if max_field:
                    values = [item.get(max_field, 0) for item in data if isinstance(item, dict)]
                    return max(values) if values else 0
                return max(data) if data else 0
            return 0

        elif operation == 'min':
            if isinstance(data, list):
                min_field = logic_def.get('min_field')
                if min_field:
                    values = [item.get(min_field, 0) for item in data if isinstance(item, dict)]
                    return min(values) if values else 0
                return min(data) if data else 0
            return 0

        return None

    async def _execute_scoring(self, logic_def: Dict, output_data: Dict) -> float:
        """
        执行评分推理

        示例：
        {
            "type": "scoring",
            "depends_on": ["protection_level", "endangered_status"],
            "formula": "protection_level * 0.6 + endangered_status * 0.4",
            "weights": {
                "protection_level": 0.6,
                "endangered_status": 0.4
            }
        }
        """
        formula = logic_def.get('formula')
        weights = logic_def.get('weights', {})
        depends_on = logic_def.get('depends_on', [])

        # 简单的加权评分
        if weights:
            score = 0.0
            total_weight = 0.0

            for field, weight in weights.items():
                if field in output_data and output_data[field] is not None:
                    value = output_data[field]
                    # 尝试转换为数值
                    try:
                        numeric_value = float(value)
                        score += numeric_value * weight
                        total_weight += weight
                    except (ValueError, TypeError):
                        pass

            # 归一化
            return score / total_weight if total_weight > 0 else 0.0

        # 如果有公式，可以在这里实现更复杂的计算
        # 暂时返回简单平均
        values = []
        for field in depends_on:
            if field in output_data and output_data[field] is not None:
                try:
                    values.append(float(output_data[field]))
                except (ValueError, TypeError):
                    pass

        return sum(values) / len(values) if values else 0.0

    async def _execute_classification(self, logic_def: Dict, output_data: Dict) -> str:
        """
        执行分类推理

        示例：
        {
            "type": "classification",
            "depends_on": ["risk_score"],
            "rules": [
                {"condition": "risk_score >= 8", "result": "高危"},
                {"condition": "risk_score >= 5", "result": "中危"},
                {"condition": "risk_score >= 0", "result": "低危"}
            ]
        }
        """
        rules = logic_def.get('rules', [])
        default_result = logic_def.get('default', '未知')

        # 按顺序检查规则
        for rule in rules:
            condition = rule.get('condition')
            result = rule.get('result')

            if not condition:
                continue

            # 简单条件评估
            try:
                # 替换条件中的字段名为实际值
                eval_condition = condition
                for field, value in output_data.items():
                    if field in eval_condition:
                        eval_condition = eval_condition.replace(field, str(value))

                # 评估条件
                if eval(eval_condition):
                    return result
            except Exception as e:
                logger.warning(f"条件评估失败: {condition}, 错误: {e}")
                continue

        return default_result

    async def _execute_derivation(self, logic_def: Dict, output_data: Dict) -> Any:
        """
        执行派生字段推理

        示例：
        {
            "type": "derivation",
            "depends_on": ["inheritors"],
            "operation": "extract_field",
            "source_field": "inheritors",
            "extract_field": "name"
        }
        """
        operation = logic_def.get('operation')
        source_field = logic_def.get('source_field')

        if not source_field or source_field not in output_data:
            return None

        data = output_data[source_field]

        if operation == 'extract_field':
            extract_field = logic_def.get('extract_field')
            if isinstance(data, dict) and 'records' in data:
                records = data['records']
                if isinstance(records, list):
                    return [record.get(extract_field) for record in records if isinstance(record, dict)]
            elif isinstance(data, list):
                return [item.get(extract_field) for item in data if isinstance(item, dict)]

        elif operation == 'filter':
            filter_condition = logic_def.get('filter_condition', {})
            if isinstance(data, list):
                filtered = []
                for item in data:
                    if isinstance(item, dict):
                        match = all(
                            item.get(key) == value
                            for key, value in filter_condition.items()
                        )
                        if match:
                            filtered.append(item)
                return filtered

        elif operation == 'transform':
            transform_func = logic_def.get('transform_function')
            # 可以在这里实现更复杂的转换逻辑
            return data

        return None

    async def _execute_computation(self, logic_def: Dict, output_data: Dict) -> Any:
        """
        执行计算推理

        示例：
        {
            "type": "computation",
            "depends_on": ["field1", "field2"],
            "expression": "field1 + field2"
        }
        """
        expression = logic_def.get('expression')

        if not expression:
            return None

        try:
            # 替换表达式中的字段名为实际值
            eval_expression = expression
            for field, value in output_data.items():
                if field in eval_expression:
                    # 安全替换：添加引号处理字符串
                    if isinstance(value, str):
                        eval_expression = eval_expression.replace(field, f'"{value}"')
                    else:
                        eval_expression = eval_expression.replace(field, str(value))

            # 评估表达式
            result = eval(eval_expression)
            return result
        except Exception as e:
            logger.error(f"计算表达式错误: {expression}, 错误: {e}")
            return None


def create_inference_engine() -> InferenceEngine:
    """工厂方法：创建推理引擎"""
    return InferenceEngine()
