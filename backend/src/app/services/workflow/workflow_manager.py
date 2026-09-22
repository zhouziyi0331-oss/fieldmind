"""
工作流管理服务

提供可视化工作流的后端支持：
- 工作流定义管理
- 工作流模板库
- 工作流执行引擎
- 可视化数据结构
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class WorkflowDefinition:
    """工作流定义"""

    def __init__(
        self,
        workflow_id: str,
        name: str,
        description: str = "",
        nodes: List[Dict] = None,
        edges: List[Dict] = None,
        metadata: Dict = None
    ):
        self.workflow_id = workflow_id
        self.name = name
        self.description = description
        self.nodes = nodes or []
        self.edges = edges or []
        self.metadata = metadata or {}
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "description": self.description,
            "nodes": self.nodes,
            "edges": self.edges,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowDefinition':
        """从字典创建"""
        return cls(
            workflow_id=data["workflow_id"],
            name=data["name"],
            description=data.get("description", ""),
            nodes=data.get("nodes", []),
            edges=data.get("edges", []),
            metadata=data.get("metadata", {})
        )


class WorkflowManager:
    """
    工作流管理器

    管理工作流的创建、编辑、执行
    """
    def __init__(self, db=None, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.db = db
        logger.info("📊 工作流管理器已初始化")

    # ==================== 工作流定义管理 ====================

    def create_workflow(
        self,
        name: str,
        description: str = "",
        nodes: List[Dict] = None,
        edges: List[Dict] = None,
        project_id: int = None,
        user_id: int = None
    ) -> Dict[str, Any]:
        """
        创建工作流

        Args:
            name: 工作流名称
            description: 描述
            nodes: 节点列表
            edges: 连接列表
            project_id: 项目ID
            user_id: 用户ID

        Returns:
            工作流信息
        """
        import uuid

        workflow_id = f"wf_{uuid.uuid4().hex[:12]}"

        workflow = {
            "workflow_id": workflow_id,
            "name": name,
            "description": description,
            "nodes": nodes or [],
            "edges": edges or [],
            "project_id": project_id,
            "created_by": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "version": 1,
            "status": "draft"
        }

        # 保存到数据库
        if self.db:
            self._save_workflow_to_db(workflow)

        logger.info(f"✅ 工作流已创建: {workflow_id}")
        return workflow

    def update_workflow(
        self,
        workflow_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        nodes: Optional[List[Dict]] = None,
        edges: Optional[List[Dict]] = None,
        user_id: int = None
    ) -> Dict[str, Any]:
        """
        更新工作流

        Args:
            workflow_id: 工作流ID
            name: 新名称
            description: 新描述
            nodes: 新节点列表
            edges: 新连接列表
            user_id: 用户ID

        Returns:
            更新后的工作流
        """
        # 从数据库获取工作流
        workflow = self._get_workflow_from_db(workflow_id)

        if not workflow:
            raise ValueError(f"工作流不存在: {workflow_id}")

        # 更新字段
        if name is not None:
            workflow["name"] = name
        if description is not None:
            workflow["description"] = description
        if nodes is not None:
            workflow["nodes"] = nodes
        if edges is not None:
            workflow["edges"] = edges

        workflow["updated_at"] = datetime.utcnow().isoformat()
        workflow["updated_by"] = user_id
        workflow["version"] = workflow.get("version", 1) + 1

        # 保存更新
        if self.db:
            self._save_workflow_to_db(workflow)

        logger.info(f"✅ 工作流已更新: {workflow_id}")
        return workflow

    def delete_workflow(
        self,
        workflow_id: str,
        user_id: int = None
    ) -> bool:
        """
        删除工作流

        Args:
            workflow_id: 工作流ID
            user_id: 用户ID

        Returns:
            是否成功
        """
        if self.db:
            self._delete_workflow_from_db(workflow_id)

        logger.info(f"✅ 工作流已删除: {workflow_id}")
        return True

    def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """获取工作流"""
        return self._get_workflow_from_db(workflow_id)

    def list_workflows(
        self,
        project_id: Optional[int] = None,
        user_id: Optional[int] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        列出工作流

        Args:
            project_id: 项目ID
            user_id: 用户ID
            limit: 数量限制

        Returns:
            工作流列表
        """
        if self.db:
            return self._list_workflows_from_db(project_id, user_id, limit)

        return []

    # ==================== 工作流验证 ====================

    def validate_workflow(
        self,
        nodes: List[Dict],
        edges: List[Dict]
    ) -> Dict[str, Any]:
        """
        验证工作流定义

        检查：
        - 节点是否有效
        - 连接是否合法
        - 是否有循环依赖
        - 起始节点和结束节点

        Returns:
            {"valid": bool, "errors": [...], "warnings": [...]}
        """
        errors = []
        warnings = []

        # 检查节点
        if not nodes:
            errors.append("工作流必须包含至少一个节点")

        node_ids = set()
        for node in nodes:
            node_id = node.get("id")
            if not node_id:
                errors.append("节点缺少 ID")
            elif node_id in node_ids:
                errors.append(f"重复的节点 ID: {node_id}")
            else:
                node_ids.add(node_id)

            # 检查节点类型
            if not node.get("type"):
                errors.append(f"节点 {node_id} 缺少类型")

        # 检查连接
        for edge in edges:
            source = edge.get("source")
            target = edge.get("target")

            if not source or source not in node_ids:
                errors.append(f"连接的源节点不存在: {source}")
            if not target or target not in node_ids:
                errors.append(f"连接的目标节点不存在: {target}")

        # 检查是否有起始节点
        if nodes:
            has_start = any(node.get("type") == "start" for node in nodes)
            if not has_start:
                warnings.append("工作流没有起始节点")

            has_end = any(node.get("type") == "end" for node in nodes)
            if not has_end:
                warnings.append("工作流没有结束节点")

        # 检查循环依赖
        if self._has_cycle(nodes, edges):
            errors.append("工作流存在循环依赖")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

    def _has_cycle(self, nodes: List[Dict], edges: List[Dict]) -> bool:
        """检测是否有循环"""
        # 构建邻接表
        graph = {}
        for node in nodes:
            graph[node["id"]] = []

        for edge in edges:
            source = edge.get("source")
            target = edge.get("target")
            if source and target:
                graph[source].append(target)

        # DFS 检测循环
        visited = set()
        rec_stack = set()

        def has_cycle_util(node_id):
            visited.add(node_id)
            rec_stack.add(node_id)

            for neighbor in graph.get(node_id, []):
                if neighbor not in visited:
                    if has_cycle_util(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node_id)
            return False

        for node_id in graph:
            if node_id not in visited:
                if has_cycle_util(node_id):
                    return True

        return False

    # ==================== 工作流执行 ====================

    def execute_workflow(
        self,
        workflow_id: str,
        input_data: Dict[str, Any],
        user_id: int = None
    ) -> Dict[str, Any]:
        """
        执行工作流

        Args:
            workflow_id: 工作流ID
            input_data: 输入数据
            user_id: 用户ID

        Returns:
            执行结果
        """
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"工作流不存在: {workflow_id}")

        # 验证工作流
        validation = self.validate_workflow(
            workflow["nodes"],
            workflow["edges"]
        )
        if not validation["valid"]:
            raise ValueError(f"工作流无效: {validation['errors']}")

        # 执行工作流
        execution_id = f"exec_{datetime.utcnow().timestamp()}"

        result = {
            "execution_id": execution_id,
            "workflow_id": workflow_id,
            "status": "running",
            "started_at": datetime.utcnow().isoformat(),
            "nodes_executed": [],
            "current_node": None,
            "output": None
        }

        # TODO: 实现实际的执行逻辑
        logger.info(f"🚀 工作流执行启动: {execution_id}")

        return result

    # ==================== 数据库操作 ====================

    def _save_workflow_to_db(self, workflow: Dict):
        """保存工作流到数据库"""
        # TODO: 实现数据库保存
        pass

    def _get_workflow_from_db(self, workflow_id: str) -> Optional[Dict]:
        """从数据库获取工作流"""
        # TODO: 实现数据库查询
        return None

    def _delete_workflow_from_db(self, workflow_id: str):
        """从数据库删除工作流"""
        # TODO: 实现数据库删除
        pass

    def _list_workflows_from_db(
        self,
        project_id: Optional[int],
        user_id: Optional[int],
        limit: int
    ) -> List[Dict]:
        """从数据库列出工作流"""
        # TODO: 实现数据库查询
        return []


# ==================== 全局单例 ====================

_workflow_manager: Optional[WorkflowManager] = None


def get_workflow_manager(db=None) -> WorkflowManager:
    """获取工作流管理器单例"""
    global _workflow_manager

    if _workflow_manager is None:
        _workflow_manager = WorkflowManager(db)

    return _workflow_manager
