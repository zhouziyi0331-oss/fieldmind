"""
血缘追踪服务
记录数据流转的完整链路
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from app.core.logging import logger
from app.core.database import get_db_session
from sqlalchemy import text


class LineageTracker:
    """血缘追踪器"""



    def __init__(self, use_workflow_engine: bool = True):


        """初始化服务"""


        self.use_workflow_engine = use_workflow_engine


        


        if use_workflow_engine:


            from app.services.workflow_engine import WorkflowEngine


            self.workflow_engine = WorkflowEngine(max_workers=4)


    @staticmethod
    def record_lineage(
        project_id: int,
        source_type: str,
        source_id: str,
        target_type: str,
        target_id: str,
        transform_type: str,
        transform_description: Optional[str] = None,
        confidence: float = 1.0,
        db=None
    ) -> bool:
        """
        记录血缘关系

        Args:
            project_id: 项目ID
            source_type: 源类型（file/chunk/metric/report）
            source_id: 源ID
            target_type: 目标类型
            target_id: 目标ID
            transform_type: 转换类型（copy/extract/aggregate/derive/model）
            transform_description: 转换描述
            confidence: 置信度
            db: 数据库会话（可选，如果不传则创建新会话）

        Returns:
            bool: 是否成功
        """
        # 判断是否需要自己管理会话
        should_close = False
        if db is None:
            db = get_db_session()
            should_close = True

        try:
            sql = text("""
                INSERT INTO lineage_edges (
                    project_id, source_type, source_id,
                    target_type, target_id, transform_type,
                    transform_description, confidence, created_at
                ) VALUES (
                    :project_id, :source_type, :source_id,
                    :target_type, :target_id, :transform_type,
                    :transform_description, :confidence, :created_at
                )
            """)

            db.execute(sql, {
                "project_id": project_id,
                "source_type": source_type,
                "source_id": source_id,
                "target_type": target_type,
                "target_id": target_id,
                "transform_type": transform_type,
                "transform_description": transform_description,
                "confidence": confidence,
                "created_at": datetime.utcnow()
            })

            # 只有自己创建的会话才commit
            if should_close:
                db.commit()

            logger.info(
                f"血缘记录成功: {source_type}({source_id}) → {target_type}({target_id})",
                transform=transform_type
            )

            return True

        except Exception as e:
            # 只有自己创建的会话才rollback
            if should_close:
                db.rollback()
            logger.error(f"血缘记录失败: {e}")
            # 重新抛出异常，让编排器感知错误
            raise

        finally:
            # 只有自己创建的会话才close
            if should_close:
                db.close()

    @staticmethod
    def trace_lineage(
        target_type: str,
        target_id: str,
        max_depth: int = 10
    ) -> Dict[str, Any]:
        """
        追溯血缘链路

        Args:
            target_type: 目标类型
            target_id: 目标ID
            max_depth: 最大追溯深度

        Returns:
            Dict: 血缘链路
                {
                    "target": {"type": str, "id": str},
                    "path": [
                        {"type": str, "id": str, "transform": str},
                        ...
                    ]
                }
        """
        db = get_db_session()

        try:
            path = []
            current_type = target_type
            current_id = target_id
            depth = 0

            while depth < max_depth:
                # 查找上游节点
                sql = text("""
                    SELECT source_type, source_id, transform_type, transform_description
                    FROM lineage_edges
                    WHERE target_type = :target_type AND target_id = :target_id
                    ORDER BY created_at DESC
                    LIMIT 1
                """)

                result = db.execute(sql, {
                    "target_type": current_type,
                    "target_id": current_id
                }).fetchone()

                if not result:
                    break

                path.append({
                    "type": result[0],
                    "id": result[1],
                    "transform": result[2],
                    "description": result[3]
                })

                current_type = result[0]
                current_id = result[1]
                depth += 1

            return {
                "target": {"type": target_type, "id": target_id},
                "path": list(reversed(path)),
                "depth": len(path)
            }

        finally:
            db.close()

    @staticmethod
    def get_downstream(
        source_type: str,
        source_id: str
    ) -> list:
        """
        获取下游节点

        Args:
            source_type: 源类型
            source_id: 源ID

        Returns:
            list: 下游节点列表
        """
        db = get_db_session()

        try:
            sql = text("""
                SELECT target_type, target_id, transform_type
                FROM lineage_edges
                WHERE source_type = :source_type AND source_id = :source_id
                ORDER BY created_at
            """)

            results = db.execute(sql, {
                "source_type": source_type,
                "source_id": source_id
            }).fetchall()

            return [
                {
                    "type": row[0],
                    "id": row[1],
                    "transform": row[2]
                }
                for row in results
            ]

        finally:
            db.close()

    @staticmethod
    def record_lineage_batch(
        project_id: int,
        source_type: str,
        source_id: str,
        target_type: str,
        target_ids: List[str],
        transform_type: str,
        transform_description: str = None,
        metadata: dict = None,
        db=None
    ) -> int:
        """
        批量记录数据血缘关系（性能优化版本，避免N+1查询）

        Args:
            project_id: 项目ID
            source_type: 源类型
            source_id: 源ID
            target_type: 目标类型
            target_ids: 目标ID列表（批量）
            transform_type: 转换类型
            transform_description: 转换描述
            metadata: 额外元数据
            db: 数据库会话（可选）

        Returns:
            成功插入的记录数
        """
        from app.core.database import get_db_session
        from sqlalchemy import text
        from datetime import datetime
        import json

        if not target_ids:
            return 0

        # 判断是否需要自己管理会话
        should_close = False
        if db is None:
            db = get_db_session()
            should_close = True

        try:
            # 批量插入，使用executemany提高性能
            sql = text("""
                INSERT INTO lineage_edges (
                    project_id,
                    source_type,
                    source_id,
                    target_type,
                    target_id,
                    transform_type,
                    transform_description,
                    metadata,
                    created_at
                ) VALUES (
                    :project_id,
                    :source_type,
                    :source_id,
                    :target_type,
                    :target_id,
                    :transform_type,
                    :transform_description,
                    :metadata,
                    :created_at
                )
            """)

            # 准备批量数据 - 使用Python的datetime而非SQL的NOW()
            current_time = datetime.utcnow()
            batch_data = [
                {
                    "project_id": project_id,
                    "source_type": source_type,
                    "source_id": source_id,
                    "target_type": target_type,
                    "target_id": target_id,
                    "transform_type": transform_type,
                    "transform_description": transform_description,
                    "metadata": json.dumps(metadata) if metadata else None,
                    "created_at": current_time
                }
                for target_id in target_ids
            ]

            # 执行批量插入
            db.execute(sql, batch_data)

            # 只有自己创建的会话才commit
            if should_close:
                db.commit()

            logger.info(
                f"血缘批量记录成功: {transform_type}({source_id}) → {target_type}(批量{len(target_ids)}个)",
                transform=transform_type
            )

            return len(target_ids)

        except Exception as e:
            # 只有自己创建的会话才rollback
            if should_close:
                db.rollback()
            logger.error(f"血缘批量记录失败: {e}")
            # 重新抛出异常，让编排器感知错误
            raise

        finally:
            # 只有自己创建的会话才close
            if should_close:
                db.close()
