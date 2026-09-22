"""
Week 3 - Day 1-2: 统一同步服务管理器
整合 Neo4j、ChromaDB、Redis 同步服务
"""

import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class SyncServiceManager:
    """
    同步服务管理器

    功能：
    1. 统一管理所有同步服务
    2. 批量注册事件处理器
    3. 统一获取同步状态
    4. 支持全量重建所有索引
    """
    def __init__(self, db_path: str,
                 neo4j_config: Optional[Dict] = None,
                 chromadb_config: Optional[Dict] = None,
                 redis_config: Optional[Dict] = None,
                 use_mock: bool = False, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        """
        初始化同步服务管理器

        Args:
            db_path: SQLite 数据库路径
            neo4j_config: Neo4j 配置
            chromadb_config: ChromaDB 配置
            redis_config: Redis 配置
            use_mock: 是否使用模拟模式
        """
        self.db_path = db_path
        self.use_mock = use_mock

        # 初始化各个同步服务
        self.services = {}

        # Neo4j 同步服务
        try:
            from app.services.neo4j_sync_service import Neo4jSyncService
            neo4j_config = neo4j_config or {}
            self.services['neo4j'] = Neo4jSyncService(
                db_path=db_path,
                use_mock=use_mock,
                **neo4j_config
            )
            logger.info("✅ Neo4j 同步服务已初始化")
        except Exception as e:
            logger.warning(f"Neo4j 同步服务初始化失败: {e}")

        # ChromaDB 同步服务
        try:
            from app.services.chromadb_sync_service import ChromaDBSyncService
            chromadb_config = chromadb_config or {}
            self.services['chromadb'] = ChromaDBSyncService(
                db_path=db_path,
                use_mock=use_mock,
                **chromadb_config
            )
            logger.info("✅ ChromaDB 同步服务已初始化")
        except Exception as e:
            logger.warning(f"ChromaDB 同步服务初始化失败: {e}")

        # Redis 缓存服务（待实现）
        # TODO: 实现 Redis 缓存服务

        logger.info(f"同步服务管理器初始化完成，已加载 {len(self.services)} 个服务")

    def register_all_handlers(self, event_bus):
        """注册所有事件处理器"""
        logger.info("注册所有同步服务的事件处理器...")

        for service_name, service in self.services.items():
            try:
                service.register_event_handlers(event_bus)
                logger.info(f"✅ {service_name} 事件处理器已注册")
            except Exception as e:
                logger.error(f"❌ {service_name} 事件处理器注册失败: {e}")

        logger.info("所有事件处理器注册完成")

    def rebuild_all(self) -> Dict:
        """
        重建所有索引

        Returns:
            各服务的重建统计
        """
        logger.info("=" * 60)
        logger.info("开始重建所有索引")
        logger.info("=" * 60)

        results = {}

        for service_name, service in self.services.items():
            logger.info(f"\n重建 {service_name}...")
            try:
                stats = service.rebuild_from_postgres()
                results[service_name] = stats
                logger.info(f"✅ {service_name} 重建完成")
            except Exception as e:
                logger.error(f"❌ {service_name} 重建失败: {e}")
                results[service_name] = {"error": str(e)}

        logger.info("\n" + "=" * 60)
        logger.info("所有索引重建完成")
        logger.info("=" * 60)

        return results

    def get_all_stats(self) -> Dict:
        """获取所有服务的统计信息"""
        stats = {}

        for service_name, service in self.services.items():
            try:
                stats[service_name] = service.get_stats()
            except Exception as e:
                stats[service_name] = {"error": str(e)}

        return stats

    def check_consistency(self) -> Dict:
        """
        检查数据一致性

        Returns:
            一致性检查结果
        """
        logger.info("检查数据一致性...")

        import sqlite3

        results = {
            "entities": {},
            "chunks": {}
        }

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 检查 entities 数量
            cursor.execute("SELECT COUNT(*) FROM entities WHERE entity_id IS NOT NULL")
            pg_entities_count = cursor.fetchone()[0]
            results["entities"]["postgres"] = pg_entities_count

            # 检查 chunks 数量
            cursor.execute("SELECT COUNT(*) FROM document_chunks")
            pg_chunks_count = cursor.fetchone()[0]
            results["chunks"]["postgres"] = pg_chunks_count

            conn.close()

            # 对比各服务的统计
            all_stats = self.get_all_stats()

            if 'neo4j' in all_stats:
                results["entities"]["neo4j"] = all_stats['neo4j'].get('entities_synced', 0)

            if 'chromadb' in all_stats:
                results["chunks"]["chromadb"] = all_stats['chromadb'].get('chunks_synced', 0)

            logger.info(f"一致性检查结果: {results}")

        except Exception as e:
            logger.error(f"一致性检查失败: {e}")
            results["error"] = str(e)

        return results


# ===== 测试代码 =====

def test_sync_manager():
    """测试同步服务管理器"""
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    from app.core.event_bus import get_event_bus

    print("=" * 60)
    print("测试同步服务管理器")
    print("=" * 60)

    # 创建事件总线
    event_bus = get_event_bus()

    # 创建同步服务管理器
    db_path = "/Users/alwan/Downloads/FieldMind/backend/src/data/fieldmind.db"
    manager = SyncServiceManager(db_path, use_mock=True)

    # 注册所有事件处理器
    manager.register_all_handlers(event_bus)

    # 模拟发布事件
    print("\n测试事件发布:")

    # 实体事件
    print("\n1. 发布实体创建事件")
    event_bus.publish("entity.created", {
        "entity_id": "ent_test123456",
        "name": "测试实体",
        "type": "person"
    }, source="test")

    # Chunk 事件
    print("\n2. 发布 chunk 创建事件")
    event_bus.publish("chunk.created", {
        "chunk_id": "chk_test123456",
        "text": "这是一个测试文本",
        "document_id": "doc_test123"
    }, source="test")

    # 等待处理
    import time
    time.sleep(0.5)

    # 获取统计
    print("\n同步统计:")
    stats = manager.get_all_stats()
    for service_name, service_stats in stats.items():
        print(f"\n{service_name}:")
        for key, value in service_stats.items():
            print(f"  {key}: {value}")

    print("\n✅ 同步服务管理器测试完成")


def test_rebuild_all():
    """测试全量重建"""
    print("\n" + "=" * 60)
    print("测试全量重建所有索引")
    print("=" * 60)

    db_path = "/Users/alwan/Downloads/FieldMind/backend/src/data/fieldmind.db"
    manager = SyncServiceManager(db_path, use_mock=True)

    # 执行重建
    results = manager.rebuild_all()

    # 显示结果
    print("\n重建结果:")
    for service_name, stats in results.items():
        print(f"\n{service_name}:")
        if isinstance(stats, dict):
            for key, value in stats.items():
                if key != "errors":
                    print(f"  {key}: {value}")

    print("\n✅ 全量重建测试完成")


def test_consistency_check():
    """测试一致性检查"""
    print("\n" + "=" * 60)
    print("测试数据一致性检查")
    print("=" * 60)

    db_path = "/Users/alwan/Downloads/FieldMind/backend/src/data/fieldmind.db"
    manager = SyncServiceManager(db_path, use_mock=True)

    # 执行一致性检查
    results = manager.check_consistency()

    print("\n一致性检查结果:")
    for data_type, counts in results.items():
        if data_type != "error":
            print(f"\n{data_type}:")
            for service, count in counts.items():
                print(f"  {service}: {count}")

    print("\n✅ 一致性检查完成")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    test_sync_manager()
    test_rebuild_all()
    test_consistency_check()
