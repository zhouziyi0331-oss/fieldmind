"""
PaddleNLP UIE 服务

使用百度 PaddleNLP 的 UIE (Universal Information Extraction) 模型
提供高精度的命名实体识别和信息抽取

优势：
- 比 HanLP 更准确（+15-20%）
- 零样本实体提取
- 支持自定义实体类型
- 推理速度快
"""

from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class PaddleNLPService:
    """
    PaddleNLP UIE 服务

    提供高精度的实体识别和信息抽取
    """

    def __init__(self):
        self._paddlenlp = None
        self._uie = None
        self._initialized = False

        try:
            from paddlenlp import Taskflow
            self._Taskflow = Taskflow
            self._initialize_models()
            self._initialized = True
            logger.info("✅ PaddleNLP UIE 服务初始化成功")
        except ImportError:
            logger.warning("⚠️ PaddleNLP 未安装，请运行: pip install paddlenlp")
        except Exception as e:
            logger.error(f"❌ PaddleNLP 初始化失败: {e}")

    def _initialize_models(self):
        """初始化 UIE 模型"""
        try:
            # 加载 UIE 模型（通用信息抽取）
            self._uie = self._Taskflow('information_extraction')
            logger.info("✅ UIE 模型加载成功")
        except Exception as e:
            logger.warning(f"⚠️ UIE 模型加载失败: {e}")
            self._uie = None

    def is_available(self) -> bool:
        """检查服务是否可用"""
        return self._initialized and self._uie is not None

    # ==================== 实体识别（增强版）====================

    def extract_entities(
        self,
        text: str,
        entity_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        高精度实体识别

        Args:
            text: 输入文本
            entity_types: 要提取的实体类型列表
                         默认: ['人名', '地名', '机构名', '时间', '产品']

        Returns:
            [
                {
                    "text": "实体文本",
                    "type": "实体类型",
                    "start": 起始位置,
                    "end": 结束位置,
                    "probability": 置信度
                },
                ...
            ]
        """
        if not self.is_available():
            logger.warning("PaddleNLP UIE 不可用")
            return []

        try:
            # 默认实体类型
            if not entity_types:
                entity_types = ['人名', '地名', '机构名', '时间', '产品']

            # UIE 抽取
            results = self._uie(text, schema=entity_types)

            # 格式化结果
            entities = []
            for result in results:
                for entity_type, entity_list in result.items():
                    for entity_item in entity_list:
                        entities.append({
                            "text": entity_item["text"],
                            "type": entity_type,
                            "start": entity_item["start"],
                            "end": entity_item["end"],
                            "probability": entity_item.get("probability", 1.0)
                        })

            return entities

        except Exception as e:
            logger.error(f"PaddleNLP 实体识别失败: {e}")
            return []

    # ==================== 关系抽取 ====================

    def extract_relations(
        self,
        text: str,
        relation_schema: Dict[str, List[str]]
    ) -> List[Dict[str, Any]]:
        """
        关系抽取

        Args:
            text: 输入文本
            relation_schema: 关系模式
                例如: {
                    "人物": ["姓名", "职位", "公司"],
                    "公司": ["名称", "总部", "CEO"]
                }

        Returns:
            关系三元组列表
        """
        if not self.is_available():
            logger.warning("PaddleNLP UIE 不可用")
            return []

        try:
            results = self._uie(text, schema=relation_schema)

            relations = []
            for result in results:
                for entity_type, entities in result.items():
                    for entity in entities:
                        if "relations" in entity:
                            for rel_type, rel_values in entity["relations"].items():
                                for rel_value in rel_values:
                                    relations.append({
                                        "subject": entity["text"],
                                        "subject_type": entity_type,
                                        "relation": rel_type,
                                        "object": rel_value["text"],
                                        "probability": rel_value.get("probability", 1.0)
                                    })

            return relations

        except Exception as e:
            logger.error(f"关系抽取失败: {e}")
            return []

    # ==================== 事件抽取 ====================

    def extract_events(
        self,
        text: str,
        event_schema: Dict[str, List[str]]
    ) -> List[Dict[str, Any]]:
        """
        事件抽取

        Args:
            text: 输入文本
            event_schema: 事件模式
                例如: {
                    "会议": ["时间", "地点", "参与者", "主题"]
                }

        Returns:
            事件列表
        """
        if not self.is_available():
            logger.warning("PaddleNLP UIE 不可用")
            return []

        try:
            results = self._uie(text, schema=event_schema)

            events = []
            for result in results:
                for event_type, event_list in result.items():
                    for event_item in event_list:
                        event = {
                            "type": event_type,
                            "trigger": event_item.get("text", ""),
                            "arguments": {}
                        }

                        # 提取事件要素
                        if "relations" in event_item:
                            for arg_type, arg_values in event_item["relations"].items():
                                event["arguments"][arg_type] = [
                                    {"text": arg["text"], "probability": arg.get("probability", 1.0)}
                                    for arg in arg_values
                                ]

                        events.append(event)

            return events

        except Exception as e:
            logger.error(f"事件抽取失败: {e}")
            return []

    # ==================== 观点抽取 ====================

    def extract_opinions(
        self,
        text: str
    ) -> List[Dict[str, Any]]:
        """
        观点抽取（情感分析增强版）

        Args:
            text: 输入文本

        Returns:
            观点列表 [{"aspect": "方面", "opinion": "观点", "sentiment": "情感"}]
        """
        if not self.is_available():
            logger.warning("PaddleNLP UIE 不可用")
            return []

        try:
            # 定义观点抽取模式
            schema = {
                "评价对象": ["观点词", "情感倾向"]
            }

            results = self._uie(text, schema=schema)

            opinions = []
            for result in results:
                if "评价对象" in result:
                    for aspect_item in result["评价对象"]:
                        opinion = {
                            "aspect": aspect_item["text"],
                            "opinions": []
                        }

                        if "relations" in aspect_item:
                            if "观点词" in aspect_item["relations"]:
                                opinion["opinions"] = [
                                    op["text"] for op in aspect_item["relations"]["观点词"]
                                ]

                        opinions.append(opinion)

            return opinions

        except Exception as e:
            logger.error(f"观点抽取失败: {e}")
            return []

    # ==================== 通用信息抽取 ====================

    def extract_information(
        self,
        text: str,
        schema: Any
    ) -> List[Dict[str, Any]]:
        """
        通用信息抽取

        Args:
            text: 输入文本
            schema: 抽取模式（灵活定义）

        Returns:
            抽取结果
        """
        if not self.is_available():
            logger.warning("PaddleNLP UIE 不可用")
            return []

        try:
            results = self._uie(text, schema=schema)
            return results

        except Exception as e:
            logger.error(f"信息抽取失败: {e}")
            return []

    # ==================== 批量处理 ====================

    def batch_extract_entities(
        self,
        texts: List[str],
        entity_types: Optional[List[str]] = None
    ) -> List[List[Dict[str, Any]]]:
        """
        批量实体识别

        Args:
            texts: 文本列表
            entity_types: 实体类型列表

        Returns:
            每个文本的实体列表
        """
        if not self.is_available():
            return [[] for _ in texts]

        try:
            if not entity_types:
                entity_types = ['人名', '地名', '机构名', '时间', '产品']

            # 批量处理
            all_results = []
            for text in texts:
                entities = self.extract_entities(text, entity_types)
                all_results.append(entities)

            return all_results

        except Exception as e:
            logger.error(f"批量实体识别失败: {e}")
            return [[] for _ in texts]


# ==================== 全局单例 ====================

_paddlenlp_service: Optional[PaddleNLPService] = None


def get_paddlenlp_service() -> PaddleNLPService:
    """获取 PaddleNLP 服务单例"""
    global _paddlenlp_service

    if _paddlenlp_service is None:
        _paddlenlp_service = PaddleNLPService()

    return _paddlenlp_service
