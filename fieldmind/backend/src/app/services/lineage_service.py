"""
数据血缘追踪服务

提供数据血缘关系的记录、查询和可视化功能
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.orm import selectinload

from app.models.data_lineage import (
    DataLineage,
    DataVersion,
    SourceFile,
    LineageQueryCache
)


class DataLineageService:
    """数据血缘服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_lineage(
        self,
        project_id: int,
        source_type: str,
        source_id: str,
        target_type: str,
        target_id: str,
        operation: str,
        transformation: Optional[Dict[str, Any]] = None,
        actor_id: Optional[int] = None,
        actor_type: str = "user"
    ) -> DataLineage:
        """
        创建数据血缘记录

        Args:
            project_id: 项目ID
            source_type: 源数据类型（file, document, dataset, model等）
            source_id: 源数据ID
            target_type: 目标数据类型
            target_id: 目标数据ID
            operation: 操作类型（extract, transform, load, analyze等）
            transformation: 转换规则/步骤的JSON描述
            actor_id: 操作者ID
            actor_type: 操作者类型（user, ai, system）

        Returns:
            创建的血缘记录
        """
        lineage = DataLineage(
            project_id=project_id,
            source_type=source_type,
            source_id=source_id,
            target_type=target_type,
            target_id=target_id,
            operation=operation,
            transformation=transformation or {},
            actor_id=actor_id,
            actor_type=actor_type,
            created_at=datetime.utcnow()
        )

        self.db.add(lineage)
        await self.db.commit()
        await self.db.refresh(lineage)

        # 清除相关查询缓存
        await self._invalidate_cache(source_id, target_id)

        return lineage

    async def get_upstream_lineage(
        self,
        target_type: str,
        target_id: str,
        max_depth: int = 5,
        include_transformations: bool = True
    ) -> List[Dict[str, Any]]:
        """
        获取上游血缘（追溯数据来源）

        Args:
            target_type: 目标数据类型
            target_id: 目标数据ID
            max_depth: 最大追溯深度
            include_transformations: 是否包含转换详情

        Returns:
            上游血缘链路列表
        """
        # 尝试从缓存读取
        cache = await self._get_cache(target_id, "upstream")
        if cache and not cache.is_expired():
            return cache.result_data

        # 递归查询上游
        lineage_chain = []
        visited = set()

        async def _trace_upstream(node_type: str, node_id: str, depth: int):
            if depth > max_depth or (node_type, node_id) in visited:
                return

            visited.add((node_type, node_id))

            # 查询直接上游
            result = await self.db.execute(
                select(DataLineage)
                .where(
                    and_(
                        DataLineage.target_type == node_type,
                        DataLineage.target_id == node_id
                    )
                )
                .order_by(desc(DataLineage.created_at))
            )
            upstreams = result.scalars().all()

            for lineage in upstreams:
                node_data = {
                    "source_type": lineage.source_type,
                    "source_id": lineage.source_id,
                    "target_type": lineage.target_type,
                    "target_id": lineage.target_id,
                    "operation": lineage.operation,
                    "depth": depth,
                    "created_at": lineage.created_at.isoformat(),
                    "actor_id": lineage.actor_id,
                    "actor_type": lineage.actor_type
                }

                if include_transformations:
                    node_data["transformation"] = lineage.transformation

                lineage_chain.append(node_data)

                # 递归追溯
                await _trace_upstream(
                    lineage.source_type,
                    lineage.source_id,
                    depth + 1
                )

        await _trace_upstream(target_type, target_id, 0)

        # 缓存结果
        await self._set_cache(target_id, "upstream", lineage_chain)

        return lineage_chain

    async def get_downstream_lineage(
        self,
        source_type: str,
        source_id: str,
        max_depth: int = 5,
        include_transformations: bool = True
    ) -> List[Dict[str, Any]]:
        """
        获取下游血缘（追踪数据影响）

        Args:
            source_type: 源数据类型
            source_id: 源数据ID
            max_depth: 最大追踪深度
            include_transformations: 是否包含转换详情

        Returns:
            下游血缘链路列表
        """
        # 尝试从缓存读取
        cache = await self._get_cache(source_id, "downstream")
        if cache and not cache.is_expired():
            return cache.result_data

        # 递归查询下游
        lineage_chain = []
        visited = set()

        async def _trace_downstream(node_type: str, node_id: str, depth: int):
            if depth > max_depth or (node_type, node_id) in visited:
                return

            visited.add((node_type, node_id))

            # 查询直接下游
            result = await self.db.execute(
                select(DataLineage)
                .where(
                    and_(
                        DataLineage.source_type == node_type,
                        DataLineage.source_id == node_id
                    )
                )
                .order_by(desc(DataLineage.created_at))
            )
            downstreams = result.scalars().all()

            for lineage in downstreams:
                node_data = {
                    "source_type": lineage.source_type,
                    "source_id": lineage.source_id,
                    "target_type": lineage.target_type,
                    "target_id": lineage.target_id,
                    "operation": lineage.operation,
                    "depth": depth,
                    "created_at": lineage.created_at.isoformat(),
                    "actor_id": lineage.actor_id,
                    "actor_type": lineage.actor_type
                }

                if include_transformations:
                    node_data["transformation"] = lineage.transformation

                lineage_chain.append(node_data)

                # 递归追踪
                await _trace_downstream(
                    lineage.target_type,
                    lineage.target_id,
                    depth + 1
                )

        await _trace_downstream(source_type, source_id, 0)

        # 缓存结果
        await self._set_cache(source_id, "downstream", lineage_chain)

        return lineage_chain

    async def get_full_lineage_graph(
        self,
        node_type: str,
        node_id: str,
        max_depth: int = 3
    ) -> Dict[str, Any]:
        """
        获取完整血缘图（上游+下游）

        Args:
            node_type: 节点数据类型
            node_id: 节点数据ID
            max_depth: 最大深度

        Returns:
            血缘图数据（包含nodes和edges）
        """
        upstream = await self.get_upstream_lineage(node_type, node_id, max_depth, False)
        downstream = await self.get_downstream_lineage(node_type, node_id, max_depth, False)

        # 构建图结构
        nodes = {}
        edges = []

        # 添加中心节点
        center_key = f"{node_type}:{node_id}"
        nodes[center_key] = {
            "id": center_key,
            "type": node_type,
            "data_id": node_id,
            "label": f"{node_type} {node_id}",
            "is_center": True
        }

        # 处理上游
        for lineage in upstream:
            source_key = f"{lineage['source_type']}:{lineage['source_id']}"
            target_key = f"{lineage['target_type']}:{lineage['target_id']}"

            if source_key not in nodes:
                nodes[source_key] = {
                    "id": source_key,
                    "type": lineage['source_type'],
                    "data_id": lineage['source_id'],
                    "label": f"{lineage['source_type']} {lineage['source_id']}",
                    "depth": lineage['depth'],
                    "direction": "upstream"
                }

            if target_key not in nodes:
                nodes[target_key] = {
                    "id": target_key,
                    "type": lineage['target_type'],
                    "data_id": lineage['target_id'],
                    "label": f"{lineage['target_type']} {lineage['target_id']}",
                    "depth": lineage['depth'],
                    "direction": "upstream"
                }

            edges.append({
                "source": source_key,
                "target": target_key,
                "operation": lineage['operation'],
                "created_at": lineage['created_at'],
                "direction": "upstream"
            })

        # 处理下游
        for lineage in downstream:
            source_key = f"{lineage['source_type']}:{lineage['source_id']}"
            target_key = f"{lineage['target_type']}:{lineage['target_id']}"

            if source_key not in nodes:
                nodes[source_key] = {
                    "id": source_key,
                    "type": lineage['source_type'],
                    "data_id": lineage['source_id'],
                    "label": f"{lineage['source_type']} {lineage['source_id']}",
                    "depth": lineage['depth'],
                    "direction": "downstream"
                }

            if target_key not in nodes:
                nodes[target_key] = {
                    "id": target_key,
                    "type": lineage['target_type'],
                    "data_id": lineage['target_id'],
                    "label": f"{lineage['target_type']} {lineage['target_id']}",
                    "depth": lineage['depth'],
                    "direction": "downstream"
                }

            edges.append({
                "source": source_key,
                "target": target_key,
                "operation": lineage['operation'],
                "created_at": lineage['created_at'],
                "direction": "downstream"
            })

        return {
            "center_node": center_key,
            "nodes": list(nodes.values()),
            "edges": edges,
            "stats": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "upstream_count": len(upstream),
                "downstream_count": len(downstream)
            }
        }

    async def create_data_version(
        self,
        data_type: str,
        data_id: str,
        version: str,
        content_hash: str,
        size_bytes: Optional[int] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
        parent_version_id: Optional[int] = None
    ) -> DataVersion:
        """
        创建数据版本记录

        Args:
            data_type: 数据类型
            data_id: 数据ID
            version: 版本号
            content_hash: 内容哈希（用于检测变更）
            size_bytes: 数据大小（字节）
            extra_metadata: 额外元数据
            parent_version_id: 父版本ID（用于版本链）

        Returns:
            创建的版本记录
        """
        data_version = DataVersion(
            data_type=data_type,
            data_id=data_id,
            version=version,
            content_hash=content_hash,
            size_bytes=size_bytes,
            extra_metadata=extra_metadata or {},
            parent_version_id=parent_version_id,
            created_at=datetime.utcnow()
        )

        self.db.add(data_version)
        await self.db.commit()
        await self.db.refresh(data_version)

        return data_version

    async def get_data_versions(
        self,
        data_type: str,
        data_id: str,
        limit: int = 20
    ) -> List[DataVersion]:
        """
        获取数据的版本历史

        Args:
            data_type: 数据类型
            data_id: 数据ID
            limit: 返回版本数量限制

        Returns:
            版本列表（按时间倒序）
        """
        result = await self.db.execute(
            select(DataVersion)
            .where(
                and_(
                    DataVersion.data_type == data_type,
                    DataVersion.data_id == data_id
                )
            )
            .order_by(desc(DataVersion.created_at))
            .limit(limit)
        )

        return result.scalars().all()

    async def register_source_file(
        self,
        project_id: int,
        file_path: str,
        file_hash: str,
        file_size: int,
        file_type: str,
        extracted_entities: Optional[Dict[str, Any]] = None
    ) -> SourceFile:
        """
        注册源文件

        Args:
            project_id: 项目ID
            file_path: 文件路径
            file_hash: 文件哈希
            file_size: 文件大小（字节）
            file_type: 文件类型（pdf, docx, txt等）
            extracted_entities: 提取的实体信息

        Returns:
            源文件记录
        """
        # 检查是否已存在
        result = await self.db.execute(
            select(SourceFile).where(
                and_(
                    SourceFile.project_id == project_id,
                    SourceFile.file_path == file_path
                )
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            # 更新现有记录
            existing.file_hash = file_hash
            existing.file_size = file_size
            existing.extracted_entities = extracted_entities or {}
            existing.last_processed = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(existing)
            return existing

        # 创建新记录
        source_file = SourceFile(
            project_id=project_id,
            file_path=file_path,
            file_hash=file_hash,
            file_size=file_size,
            file_type=file_type,
            extracted_entities=extracted_entities or {},
            first_seen=datetime.utcnow(),
            last_processed=datetime.utcnow()
        )

        self.db.add(source_file)
        await self.db.commit()
        await self.db.refresh(source_file)

        return source_file

    async def get_source_files(
        self,
        project_id: int,
        file_type: Optional[str] = None
    ) -> List[SourceFile]:
        """
        获取项目的源文件列表

        Args:
            project_id: 项目ID
            file_type: 可选，筛选文件类型

        Returns:
            源文件列表
        """
        conditions = [SourceFile.project_id == project_id]
        if file_type:
            conditions.append(SourceFile.file_type == file_type)

        result = await self.db.execute(
            select(SourceFile)
            .where(and_(*conditions))
            .order_by(desc(SourceFile.last_processed))
        )

        return result.scalars().all()

    async def get_impact_analysis(
        self,
        source_type: str,
        source_id: str
    ) -> Dict[str, Any]:
        """
        影响分析：评估修改某数据会影响哪些下游

        Args:
            source_type: 源数据类型
            source_id: 源数据ID

        Returns:
            影响分析结果
        """
        downstream = await self.get_downstream_lineage(source_type, source_id, max_depth=10)

        # 按类型统计影响
        impact_by_type = {}
        affected_ids = set()

        for lineage in downstream:
            target_type = lineage['target_type']
            target_id = lineage['target_id']

            if target_type not in impact_by_type:
                impact_by_type[target_type] = []

            impact_by_type[target_type].append({
                "id": target_id,
                "operation": lineage['operation'],
                "depth": lineage['depth']
            })
            affected_ids.add(f"{target_type}:{target_id}")

        return {
            "source": f"{source_type}:{source_id}",
            "total_affected": len(affected_ids),
            "impact_by_type": impact_by_type,
            "max_depth": max(([l['depth'] for l in downstream] or [0])),
            "analysis_time": datetime.utcnow().isoformat()
        }

    # ==================== 私有辅助方法 ====================

    async def _get_cache(
        self,
        data_id: str,
        query_type: str
    ) -> Optional[LineageQueryCache]:
        """获取缓存"""
        result = await self.db.execute(
            select(LineageQueryCache).where(
                and_(
                    LineageQueryCache.data_id == data_id,
                    LineageQueryCache.query_type == query_type
                )
            )
        )
        return result.scalar_one_or_none()

    async def _set_cache(
        self,
        data_id: str,
        query_type: str,
        result_data: Any,
        ttl_seconds: int = 3600
    ):
        """设置缓存"""
        cache = await self._get_cache(data_id, query_type)

        if cache:
            cache.result_data = result_data
            cache.cached_at = datetime.utcnow()
            cache.ttl_seconds = ttl_seconds
        else:
            cache = LineageQueryCache(
                data_id=data_id,
                query_type=query_type,
                result_data=result_data,
                cached_at=datetime.utcnow(),
                ttl_seconds=ttl_seconds
            )
            self.db.add(cache)

        await self.db.commit()

    async def _invalidate_cache(self, *data_ids: str):
        """清除缓存"""
        for data_id in data_ids:
            await self.db.execute(
                f"DELETE FROM lineage_query_cache WHERE data_id = '{data_id}'"
            )
        await self.db.commit()
