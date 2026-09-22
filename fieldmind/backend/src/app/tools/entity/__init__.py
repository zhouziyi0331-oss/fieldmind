"""实体识别工具兼容入口。"""

from typing import Any, Dict


def extract_entities(text: str, **kwargs) -> Dict[str, Any]:
    """调用当前实体识别服务并返回统一字典格式。"""
    from app.services.entity_recognition_service import EntityRecognitionService

    entities = EntityRecognitionService().recognize_entities(text)
    items = []
    for entity in entities:
        entity_type = getattr(entity, "entity_type", "OTHER")
        items.append(
            {
                "text": getattr(entity, "text", ""),
                "type": getattr(entity_type, "value", entity_type),
                "confidence": getattr(entity, "confidence", None),
                "context": getattr(entity, "context", None),
            }
        )
    return {"entities": items, "count": len(items), "source": "EntityRecognitionService"}


__all__ = ["extract_entities"]
