"""
Query Parser - 查询解析器

功能：
1. 接收自然语言或结构化查询
2. 识别用户意图（intent）
3. 匹配最合适的视图
4. 提取和验证参数
"""

import json
import logging
from typing import Dict, Optional, List, Any
from pathlib import Path
import re

logger = logging.getLogger(__name__)


class QueryParser:
    """查询解析器"""

    def __init__(self, views_dir: str = "views"):
        """
        初始化查询解析器

        Args:
            views_dir: 视图定义文件目录
        """
        self.views_dir = Path(views_dir)
        self.views = {}
        self.intent_keywords = {}

        self._load_views()
        self._build_intent_index()

    def _load_views(self):
        """加载所有视图定义"""
        if not self.views_dir.exists():
            logger.error(f"Views directory not found: {self.views_dir}")
            return

        for view_file in self.views_dir.glob("*.json"):
            try:
                with open(view_file, 'r', encoding='utf-8') as f:
                    view = json.load(f)
                    view_id = view.get('view_id')
                    if view_id:
                        self.views[view_id] = view
                        logger.info(f"Loaded view: {view_id}")
            except Exception as e:
                logger.error(f"Error loading view {view_file}: {e}")

        logger.info(f"Loaded {len(self.views)} views")

    def _build_intent_index(self):
        """构建意图关键词索引"""
        for view_id, view in self.views.items():
            keywords = view.get('keywords', [])
            intent = view.get('intent', '')

            # 从intent中提取关键词
            intent_words = intent.split()
            all_keywords = keywords + intent_words

            self.intent_keywords[view_id] = set(all_keywords)

        logger.info(f"Built intent index for {len(self.intent_keywords)} views")

    def parse(self, query: str or Dict) -> Dict[str, Any]:
        """
        解析查询

        Args:
            query: 自然语言查询或结构化查询

        Returns:
            解析结果，包含：
            - view_id: 匹配的视图ID
            - intent: 识别的意图
            - parameters: 提取的参数
            - confidence: 匹配置信度
        """
        if isinstance(query, dict):
            # 结构化查询
            return self._parse_structured(query)
        else:
            # 自然语言查询
            return self._parse_natural_language(query)

    def _parse_structured(self, query: Dict) -> Dict[str, Any]:
        """
        解析结构化查询

        Args:
            query: {
                "intent": "cultural_heritage_health",  # 可选
                "view_id": "cultural_heritage_health_view",  # 可选
                "parameters": {...}
            }
        """
        view_id = query.get('view_id')
        intent = query.get('intent')
        parameters = query.get('parameters', {})

        # 如果指定了view_id，直接使用
        if view_id and view_id in self.views:
            return {
                'view_id': view_id,
                'intent': intent or self.views[view_id].get('intent'),
                'parameters': parameters,
                'confidence': 1.0,
                'method': 'structured'
            }

        # 如果指定了intent，尝试匹配
        if intent:
            view_id = self._match_intent_to_view(intent)
            if view_id:
                return {
                    'view_id': view_id,
                    'intent': intent,
                    'parameters': parameters,
                    'confidence': 0.9,
                    'method': 'structured'
                }

        # 无法解析
        return {
            'view_id': None,
            'intent': intent,
            'parameters': parameters,
            'confidence': 0.0,
            'error': 'Cannot match intent to any view',
            'method': 'structured'
        }

    def _parse_natural_language(self, query: str) -> Dict[str, Any]:
        """
        解析自然语言查询

        Args:
            query: 自然语言查询，如"查看布依族山歌的传承情况"
        """
        # 1. 关键词匹配
        matched_views = self._match_keywords(query)

        if not matched_views:
            return {
                'view_id': None,
                'intent': None,
                'parameters': {},
                'confidence': 0.0,
                'error': 'No matching view found',
                'method': 'natural_language'
            }

        # 2. 选择最佳匹配
        best_match = matched_views[0]
        view_id = best_match['view_id']
        view = self.views[view_id]

        # 3. 提取参数
        parameters = self._extract_parameters(query, view)

        return {
            'view_id': view_id,
            'intent': view.get('intent'),
            'parameters': parameters,
            'confidence': best_match['score'],
            'method': 'natural_language',
            'matched_keywords': best_match['matched_keywords']
        }

    def _match_keywords(self, query: str) -> List[Dict]:
        """
        基于关键词匹配视图

        Returns:
            匹配结果列表，按得分排序
        """
        results = []

        for view_id, keywords in self.intent_keywords.items():
            matched = []
            score = 0

            for keyword in keywords:
                if keyword and keyword in query:
                    matched.append(keyword)
                    score += len(keyword)  # 长关键词权重更高

            if matched:
                results.append({
                    'view_id': view_id,
                    'matched_keywords': matched,
                    'score': score / (len(query) + 1)  # 归一化
                })

        # 按得分排序
        results.sort(key=lambda x: x['score'], reverse=True)
        return results

    def _match_intent_to_view(self, intent: str) -> Optional[str]:
        """将intent字符串映射到view_id"""
        # 简单映射规则
        intent_mapping = {
            'cultural_heritage_health': 'cultural_heritage_health_view',
            'person_network': 'person_network_view',
            'location_assets': 'location_assets_view',
            'policy_impact': 'policy_impact_view',
            'timeline': 'timeline_view',
            'dimension_analysis': 'dimension_analysis_view'
        }

        return intent_mapping.get(intent)

    def _extract_parameters(self, query: str, view: Dict) -> Dict[str, Any]:
        """
        从查询中提取参数

        Args:
            query: 自然语言查询
            view: 视图定义
        """
        parameters = {}
        view_input = view.get('input', {})
        required_params = view_input.get('required', [])

        for param_def in required_params:
            param_name = param_def['name']
            param_type = param_def['type']

            # 根据参数名称尝试提取
            value = self._extract_param_value(query, param_name, param_type)
            if value:
                parameters[param_name] = value

        return parameters

    def _extract_param_value(self, query: str, param_name: str, param_type: str) -> Any:
        """
        提取单个参数值

        简单规则：
        - cultural_asset_id: 提取文化资产名称
        - person_id: 提取人名
        - location_id: 提取地名
        - policy_id: 提取政策名称
        - dimension: 提取维度名称
        """
        # 文化资产
        if 'asset' in param_name:
            # 匹配常见文化资产名称模式
            patterns = [
                r'([^\s]{2,6}(山歌|蜡染|刺绣|建筑|节庆))',
                r'(布依族|苗族|侗族)[\s的]*([^\s]{2,6})',
            ]
            for pattern in patterns:
                match = re.search(pattern, query)
                if match:
                    return match.group(0)

        # 人物
        if 'person' in param_name:
            # 匹配人名模式
            patterns = [
                r'([王李张刘陈杨赵黄周吴]\w{1,2})',
                r'(\w{2,3}(大爷|奶奶|师傅|村长|主任))',
            ]
            for pattern in patterns:
                match = re.search(pattern, query)
                if match:
                    return match.group(1)

        # 地点
        if 'location' in param_name:
            # 匹配地名模式
            patterns = [
                r'(\w{2,6}(村|寨|镇|乡|县))',
            ]
            for pattern in patterns:
                match = re.search(pattern, query)
                if match:
                    return match.group(1)

        # 政策
        if 'policy' in param_name:
            patterns = [
                r'(非遗|文化遗产|乡村振兴|扶贫)(保护)?政策',
                r'(\w{2,8}政策)',
            ]
            for pattern in patterns:
                match = re.search(pattern, query)
                if match:
                    return match.group(0)

        # 维度
        if 'dimension' in param_name:
            dimensions = ['衣食住行', '民俗', '非物质文化遗产', '物质文化遗产', '政策', '历史']
            for dim in dimensions:
                if dim in query:
                    return dim

        return None

    def validate_parameters(self, view_id: str, parameters: Dict) -> Dict[str, Any]:
        """
        验证参数

        Returns:
            {
                'valid': bool,
                'errors': List[str],
                'warnings': List[str]
            }
        """
        if view_id not in self.views:
            return {
                'valid': False,
                'errors': [f'View not found: {view_id}'],
                'warnings': []
            }

        view = self.views[view_id]
        view_input = view.get('input', {})
        required_params = view_input.get('required', [])
        optional_params = view_input.get('optional', [])

        errors = []
        warnings = []

        # 检查必需参数
        for param_def in required_params:
            param_name = param_def['name']
            if param_name not in parameters:
                errors.append(f'Missing required parameter: {param_name}')

        # 检查参数类型和枚举值
        all_params = required_params + optional_params
        for param_def in all_params:
            param_name = param_def['name']
            if param_name in parameters:
                value = parameters[param_name]
                param_type = param_def['type']

                # 类型检查（简单）
                if param_type == 'integer' and not isinstance(value, int):
                    try:
                        parameters[param_name] = int(value)
                    except:
                        errors.append(f'Parameter {param_name} must be integer')

                if param_type == 'boolean' and not isinstance(value, bool):
                    if value in ['true', 'True', '1']:
                        parameters[param_name] = True
                    elif value in ['false', 'False', '0']:
                        parameters[param_name] = False
                    else:
                        errors.append(f'Parameter {param_name} must be boolean')

                # 枚举值检查
                if 'enum' in param_def:
                    if value not in param_def['enum']:
                        errors.append(f'Parameter {param_name} must be one of: {param_def["enum"]}')

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

    def get_view(self, view_id: str) -> Optional[Dict]:
        """获取视图定义"""
        return self.views.get(view_id)

    def list_views(self) -> List[Dict]:
        """列出所有视图"""
        return [
            {
                'view_id': view_id,
                'name': view.get('name'),
                'intent': view.get('intent'),
                'keywords': view.get('keywords', [])
            }
            for view_id, view in self.views.items()
        ]


def create_parser(views_dir: str = "views") -> QueryParser:
    """工厂方法：创建查询解析器"""
    return QueryParser(views_dir)
