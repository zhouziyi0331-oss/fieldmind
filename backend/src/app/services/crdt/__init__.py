"""
CRDT (Conflict-free Replicated Data Type) package

实时协作编辑服务
"""
from app.services.crdt.document_sync import (
    DocumentSyncService,
    DocumentState,
    Operation,
    OperationType,
    OperationTransformer
)
from app.services.crdt.collaboration_manager import (
    CollaborationManager,
    UserCursor,
    CollaborationSession
)

__all__ = [
    "DocumentSyncService",
    "DocumentState",
    "Operation",
    "OperationType",
    "OperationTransformer",
    "CollaborationManager",
    "UserCursor",
    "CollaborationSession"
]
