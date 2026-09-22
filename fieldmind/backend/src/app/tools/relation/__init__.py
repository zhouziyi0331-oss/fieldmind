"""关系抽取工具兼容入口。"""

from typing import Any, Dict, List


def extract_relations(
    text: str,
    entities: List[Dict[str, Any]] | None = None,
    **kwargs,
) -> Dict[str, Any]:
    """调用当前关系服务，统一返回 triples。"""
    from app.services.relation_extraction_service import RelationExtractionService

    relations = RelationExtractionService().extract_relations(text, [])
    triples = []
    for relation in relations:
        subject = getattr(relation, "source", getattr(relation, "subject", ""))
        predicate = getattr(
            relation,
            "relation_type",
            getattr(relation, "predicate", "related_to"),
        )
        object_name = getattr(relation, "target", getattr(relation, "object", ""))
        triples.append(
            {
                "subject": subject,
                "predicate": getattr(predicate, "value", predicate),
                "object": object_name,
            }
        )
    return {"triples": triples, "count": len(triples), "source": "RelationExtractionService"}


__all__ = ["extract_relations"]
