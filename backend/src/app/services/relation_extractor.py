"""
关系提取服务
从文本中提取实体之间的关系
"""

import re
from typing import List, Dict, Any, Tuple, Optional
from app.core.logging import logger


class RelationExtractor:
    """关系提取器"""



    def __init__(self, use_workflow_engine: bool = True):


        """初始化服务"""


        self.use_workflow_engine = use_workflow_engine


        


        if use_workflow_engine:


            from app.services.workflow_engine import WorkflowEngine


            self.workflow_engine = WorkflowEngine(max_workers=4)


    # 关系模式定义
    RELATION_PATTERNS = {
        "位于": [
            r"(.+?)(?:位于|在)(.+?)(?:市|省|县|区|镇|村)",
            r"(.+?)(?:的|地处)(.+?)(?:地区|区域)"
        ],
        "属于": [
            r"(.+?)(?:属于|隶属于|是)(.+?)(?:的|之一)",
        ],
        "担任": [
            r"(.+?)(?:担任|任|是)(.+?)(?:职务|职位|工作)",
        ],
        "包含": [
            r"(.+?)(?:包含|包括|有)(.+?)(?:等|和)",
        ],
        "发生于": [
            r"(.+?)(?:发生在|在)(.+?)(?:年|月|日|时期)",
        ]
    }

    def extract(
        self,
        text: str,
        entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        提取关系

        Args:
            text: 文本内容
            entities: 已识别的实体列表

        Returns:
            List[Dict]: 关系列表
                [
                    {
                        "source": "十八洞村",
                        "relation": "位于",
                        "target": "湖南省",
                        "confidence": 0.8
                    }
                ]
        """
        relations = []

        # 方法1: 基于模式的关系提取
        pattern_relations = self._extract_by_patterns(text)
        relations.extend(pattern_relations)

        # 方法2: 基于实体共现的关系提取
        cooccurrence_relations = self._extract_by_cooccurrence(text, entities)
        relations.extend(cooccurrence_relations)

        # 去重
        relations = self._deduplicate_relations(relations)

        return relations

    def _extract_by_patterns(self, text: str) -> List[Dict[str, Any]]:
        """基于模式提取关系"""
        relations = []

        for relation_type, patterns in self.RELATION_PATTERNS.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text)

                for match in matches:
                    if len(match.groups()) >= 2:
                        source = match.group(1).strip()
                        target = match.group(2).strip()

                        if source and target and len(source) < 50 and len(target) < 50:
                            relations.append({
                                "source": source,
                                "relation": relation_type,
                                "target": target,
                                "confidence": 0.7,
                                "method": "pattern"
                            })

        return relations

    def _extract_by_cooccurrence(
        self,
        text: str,
        entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """基于实体共现提取关系"""
        relations = []

        # 窗口大小（字符数）
        window_size = 100

        # 检查每对实体
        for i, entity1 in enumerate(entities):
            for entity2 in entities[i+1:]:
                # 检查两个实体是否在一个窗口内
                distance = abs(entity1['start'] - entity2['start'])

                if distance <= window_size:
                    # 提取两个实体之间的文本
                    start = min(entity1['end'], entity2['end'])
                    end = max(entity1['start'], entity2['start'])

                    if start < end:
                        between_text = text[start:end]

                        # 简单推断关系类型
                        relation_type = self._infer_relation_type(
                            entity1, entity2, between_text
                        )

                        if relation_type:
                            relations.append({
                                "source": entity1['text'],
                                "relation": relation_type,
                                "target": entity2['text'],
                                "confidence": 0.5,
                                "method": "cooccurrence"
                            })

        return relations

    def _infer_relation_type(
        self,
        entity1: Dict[str, Any],
        entity2: Dict[str, Any],
        between_text: str
    ) -> Optional[str]:
        """推断关系类型"""

        # 根据实体类型组合推断
        type_pair = (entity1['type'], entity2['type'])

        # 人 - 地点
        if type_pair in [('PERSON', 'LOCATION'), ('LOCATION', 'PERSON')]:
            if '来自' in between_text or '住在' in between_text:
                return "来自"
            elif '工作' in between_text or '任职' in between_text:
                return "工作于"

        # 组织 - 地点
        elif type_pair in [('ORGANIZATION', 'LOCATION'), ('LOCATION', 'ORGANIZATION')]:
            if '位于' in between_text or '在' in between_text:
                return "位于"

        # 人 - 组织
        elif type_pair in [('PERSON', 'ORGANIZATION'), ('ORGANIZATION', 'PERSON')]:
            if '任' in between_text or '担任' in between_text:
                return "任职于"

        # 时间 - 其他
        elif 'DATE' in type_pair:
            return "发生于"

        return None

    def _deduplicate_relations(
        self,
        relations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """去重关系"""
        unique = {}

        for rel in relations:
            key = (rel['source'], rel['relation'], rel['target'])

            # 保留置信度高的
            if key not in unique or rel['confidence'] > unique[key]['confidence']:
                unique[key] = rel

        return list(unique.values())


class RelationValidator:
    """关系验证器"""

    @staticmethod
    def validate(relation: Dict[str, Any]) -> bool:
        """
        验证关系是否合理

        Args:
            relation: 关系字典

        Returns:
            bool: 是否有效
        """
        # 检查必需字段
        if not all(k in relation for k in ['source', 'relation', 'target']):
            return False

        # 检查文本长度
        if len(relation['source']) > 100 or len(relation['target']) > 100:
            return False

        # 检查是否自指
        if relation['source'] == relation['target']:
            return False

        return True
