"""Agent共享上下文池。"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional


class ContextScope(Enum):
    GLOBAL = "global"
    PROJECT = "project"
    SESSION = "session"
    TASK = "task"


class SharedContextPool:
    """进程内上下文存储，用于Agent之间传递中间结果。"""
    def __init__(self, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self._data: Dict[str, Dict[str, Any]] = {}

    def _key(self, scope: ContextScope, key: str, owner_id: Optional[str] = None) -> str:
        owner = owner_id or "default"
        return f"{scope.value}:{owner}:{key}"

    def set(
        self,
        key: str,
        value: Any,
        scope: ContextScope = ContextScope.GLOBAL,
        owner_id: Optional[str] = None,
    ) -> None:
        self._data[self._key(scope, key, owner_id)] = {
            "value": value,
            "updated_at": datetime.utcnow(),
        }

    def get(
        self,
        key: str,
        scope: ContextScope = ContextScope.GLOBAL,
        owner_id: Optional[str] = None,
        default: Any = None,
    ) -> Any:
        item = self._data.get(self._key(scope, key, owner_id))
        return item["value"] if item else default

    def delete(
        self,
        key: str,
        scope: ContextScope = ContextScope.GLOBAL,
        owner_id: Optional[str] = None,
    ) -> bool:
        return self._data.pop(self._key(scope, key, owner_id), None) is not None

    def snapshot(self) -> Dict[str, Any]:
        return {key: value["value"] for key, value in self._data.items()}
