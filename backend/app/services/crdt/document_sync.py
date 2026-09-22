"""
CRDT (Conflict-free Replicated Data Type) 文档同步服务

使用 Operational Transformation (OT) 实现实时协作编辑
"""
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import uuid


class OperationType(str, Enum):
    """操作类型"""
    INSERT = "insert"
    DELETE = "delete"
    RETAIN = "retain"
    FORMAT = "format"


@dataclass
class Operation:
    """文档操作"""
    op_type: OperationType
    position: int
    content: Optional[str] = None
    length: Optional[int] = None
    attributes: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.now)
    user_id: int = 0
    operation_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "op_type": self.op_type.value,
            "position": self.position,
            "content": self.content,
            "length": self.length,
            "attributes": self.attributes,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "operation_id": self.operation_id
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Operation":
        """从字典创建"""
        return cls(
            op_type=OperationType(data["op_type"]),
            position=data["position"],
            content=data.get("content"),
            length=data.get("length"),
            attributes=data.get("attributes"),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            user_id=data["user_id"],
            operation_id=data["operation_id"]
        )


@dataclass
class DocumentState:
    """文档状态"""
    document_id: str
    content: str
    version: int
    operations: List[Operation] = field(default_factory=list)
    active_users: Set[int] = field(default_factory=set)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def apply_operation(self, operation: Operation) -> None:
        """应用操作到文档"""
        if operation.op_type == OperationType.INSERT:
            # 插入文本
            pos = operation.position
            content = operation.content or ""
            self.content = self.content[:pos] + content + self.content[pos:]

        elif operation.op_type == OperationType.DELETE:
            # 删除文本
            pos = operation.position
            length = operation.length or 0
            self.content = self.content[:pos] + self.content[pos + length:]

        # 记录操作
        self.operations.append(operation)
        self.version += 1
        self.updated_at = datetime.now()

    def get_snapshot(self) -> Dict[str, Any]:
        """获取文档快照"""
        return {
            "document_id": self.document_id,
            "content": self.content,
            "version": self.version,
            "active_users": list(self.active_users),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class OperationTransformer:
    """
    操作转换器

    实现 Operational Transformation 算法，解决并发编辑冲突
    """

    @staticmethod
    def transform(op1: Operation, op2: Operation) -> tuple[Operation, Operation]:
        """
        转换两个并发操作

        Args:
            op1: 第一个操作
            op2: 第二个操作

        Returns:
            (op1', op2'): 转换后的操作对
        """
        # INSERT vs INSERT
        if op1.op_type == OperationType.INSERT and op2.op_type == OperationType.INSERT:
            if op1.position < op2.position:
                # op1 在 op2 之前，op2 位置需要后移
                op2_prime = Operation(
                    op_type=op2.op_type,
                    position=op2.position + len(op1.content or ""),
                    content=op2.content,
                    user_id=op2.user_id,
                    operation_id=op2.operation_id
                )
                return op1, op2_prime
            elif op1.position > op2.position:
                # op2 在 op1 之前，op1 位置需要后移
                op1_prime = Operation(
                    op_type=op1.op_type,
                    position=op1.position + len(op2.content or ""),
                    content=op1.content,
                    user_id=op1.user_id,
                    operation_id=op1.operation_id
                )
                return op1_prime, op2
            else:
                # 同一位置，使用 user_id 作为 tie-breaker
                if op1.user_id < op2.user_id:
                    op2_prime = Operation(
                        op_type=op2.op_type,
                        position=op2.position + len(op1.content or ""),
                        content=op2.content,
                        user_id=op2.user_id,
                        operation_id=op2.operation_id
                    )
                    return op1, op2_prime
                else:
                    op1_prime = Operation(
                        op_type=op1.op_type,
                        position=op1.position + len(op2.content or ""),
                        content=op1.content,
                        user_id=op1.user_id,
                        operation_id=op1.operation_id
                    )
                    return op1_prime, op2

        # INSERT vs DELETE
        elif op1.op_type == OperationType.INSERT and op2.op_type == OperationType.DELETE:
            if op1.position <= op2.position:
                # INSERT 在 DELETE 之前，DELETE 位置后移
                op2_prime = Operation(
                    op_type=op2.op_type,
                    position=op2.position + len(op1.content or ""),
                    length=op2.length,
                    user_id=op2.user_id,
                    operation_id=op2.operation_id
                )
                return op1, op2_prime
            elif op1.position > op2.position + (op2.length or 0):
                # INSERT 在 DELETE 之后，INSERT 位置前移
                op1_prime = Operation(
                    op_type=op1.op_type,
                    position=op1.position - (op2.length or 0),
                    content=op1.content,
                    user_id=op1.user_id,
                    operation_id=op1.operation_id
                )
                return op1_prime, op2
            else:
                # INSERT 在 DELETE 范围内，调整位置
                op1_prime = Operation(
                    op_type=op1.op_type,
                    position=op2.position,
                    content=op1.content,
                    user_id=op1.user_id,
                    operation_id=op1.operation_id
                )
                return op1_prime, op2

        # DELETE vs INSERT
        elif op1.op_type == OperationType.DELETE and op2.op_type == OperationType.INSERT:
            op2_prime, op1_prime = OperationTransformer.transform(op2, op1)
            return op1_prime, op2_prime

        # DELETE vs DELETE
        elif op1.op_type == OperationType.DELETE and op2.op_type == OperationType.DELETE:
            op1_pos = op1.position
            op1_len = op1.length or 0
            op2_pos = op2.position
            op2_len = op2.length or 0

            if op1_pos + op1_len <= op2_pos:
                # op1 完全在 op2 之前
                op2_prime = Operation(
                    op_type=op2.op_type,
                    position=op2_pos - op1_len,
                    length=op2_len,
                    user_id=op2.user_id,
                    operation_id=op2.operation_id
                )
                return op1, op2_prime
            elif op2_pos + op2_len <= op1_pos:
                # op2 完全在 op1 之前
                op1_prime = Operation(
                    op_type=op1.op_type,
                    position=op1_pos - op2_len,
                    length=op1_len,
                    user_id=op1.user_id,
                    operation_id=op1.operation_id
                )
                return op1_prime, op2
            else:
                # 有重叠，需要合并
                start = min(op1_pos, op2_pos)
                end = max(op1_pos + op1_len, op2_pos + op2_len)

                if op1_pos <= op2_pos:
                    # op1 先执行
                    overlap = min(op1_pos + op1_len, op2_pos + op2_len) - op2_pos
                    op2_prime = Operation(
                        op_type=op2.op_type,
                        position=op1_pos,
                        length=max(0, op2_len - overlap),
                        user_id=op2.user_id,
                        operation_id=op2.operation_id
                    )
                    return op1, op2_prime
                else:
                    # op2 先执行
                    overlap = min(op1_pos + op1_len, op2_pos + op2_len) - op1_pos
                    op1_prime = Operation(
                        op_type=op1.op_type,
                        position=op2_pos,
                        length=max(0, op1_len - overlap),
                        user_id=op1.user_id,
                        operation_id=op1.operation_id
                    )
                    return op1_prime, op2

        # 默认不转换
        return op1, op2


class DocumentSyncService:
    """
    文档同步服务

    管理文档状态和操作同步
    """

    def __init__(self):
        """初始化服务"""
        self.documents: Dict[str, DocumentState] = {}
        self.pending_operations: Dict[str, List[Operation]] = {}

    def create_document(self, document_id: str, initial_content: str = "") -> DocumentState:
        """
        创建新文档

        Args:
            document_id: 文档 ID
            initial_content: 初始内容

        Returns:
            文档状态
        """
        doc = DocumentState(
            document_id=document_id,
            content=initial_content,
            version=0
        )
        self.documents[document_id] = doc
        self.pending_operations[document_id] = []
        return doc

    def get_document(self, document_id: str) -> Optional[DocumentState]:
        """获取文档"""
        return self.documents.get(document_id)

    def apply_operation(
        self,
        document_id: str,
        operation: Operation,
        client_version: int
    ) -> tuple[bool, Optional[DocumentState], List[Operation]]:
        """
        应用操作到文档

        Args:
            document_id: 文档 ID
            operation: 要应用的操作
            client_version: 客户端版本号

        Returns:
            (成功标志, 更新后的文档状态, 需要应用的转换后操作列表)
        """
        doc = self.documents.get(document_id)
        if not doc:
            return False, None, []

        # 检查版本
        if client_version < doc.version:
            # 客户端版本落后，需要转换操作
            transformed_ops = self._transform_operation(document_id, operation, client_version)
            return True, doc, transformed_ops
        elif client_version == doc.version:
            # 版本一致，直接应用
            doc.apply_operation(operation)
            return True, doc, [operation]
        else:
            # 客户端版本超前，添加到待处理队列
            self.pending_operations[document_id].append(operation)
            return False, doc, []

    def _transform_operation(
        self,
        document_id: str,
        operation: Operation,
        from_version: int
    ) -> List[Operation]:
        """
        转换操作以适应当前文档状态

        Args:
            document_id: 文档 ID
            operation: 要转换的操作
            from_version: 起始版本

        Returns:
            转换后的操作列表
        """
        doc = self.documents[document_id]

        # 获取从 from_version 到当前版本的所有操作
        server_ops = doc.operations[from_version:]

        # 依次对每个服务器操作进行转换
        transformed_op = operation
        for server_op in server_ops:
            transformed_op, _ = OperationTransformer.transform(transformed_op, server_op)

        return [transformed_op]

    def join_document(self, document_id: str, user_id: int) -> Optional[DocumentState]:
        """
        用户加入文档编辑

        Args:
            document_id: 文档 ID
            user_id: 用户 ID

        Returns:
            文档状态
        """
        doc = self.documents.get(document_id)
        if doc:
            doc.active_users.add(user_id)
        return doc

    def leave_document(self, document_id: str, user_id: int) -> None:
        """
        用户离开文档编辑

        Args:
            document_id: 文档 ID
            user_id: 用户 ID
        """
        doc = self.documents.get(document_id)
        if doc and user_id in doc.active_users:
            doc.active_users.remove(user_id)

    def get_active_users(self, document_id: str) -> List[int]:
        """获取文档的活跃用户"""
        doc = self.documents.get(document_id)
        return list(doc.active_users) if doc else []
