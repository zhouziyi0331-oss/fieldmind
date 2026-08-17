"""
Graph Persistence Service
图谱持久化服务

整合所有版本的持久化功能:
- 文件存储 (JSON, Pickle)
- 数据库存储 (SQLite, PostgreSQL)
- 增量更新和版本控制
- 批量加载和缓存优化
"""

import json
import pickle
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class GraphPersistenceService:
    """
    统一图谱持久化服务
    支持多种存储后端
    """

    def __init__(
        self,
        storage_type: str = 'json',
        storage_path: Optional[str] = None,
        db_connection_string: Optional[str] = None
    ):
        """
        Args:
            storage_type: 'json', 'pickle', 'sqlite', 'postgresql'
            storage_path: 文件存储路径 (for json/pickle)
            db_connection_string: 数据库连接字符串 (for sqlite/postgresql)
        """
        self.storage_type = storage_type
        self.storage_path = Path(storage_path) if storage_path else Path('./knowledge_graphs')
        self.db_connection_string = db_connection_string

        # Initialize storage
        if storage_type in ['json', 'pickle']:
            self.storage_path.mkdir(parents=True, exist_ok=True)
        elif storage_type in ['sqlite', 'postgresql']:
            self._init_database()

        # Cache
        self._cache: Dict[str, Dict[str, Any]] = {}

    def save_graph(
        self,
        graph_id: str,
        graph_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        保存图谱

        Args:
            graph_id: 图谱唯一标识
            graph_data: 图谱数据
            metadata: 元数据 (可选)

        Returns:
            是否成功
        """
        try:
            # Add metadata
            save_data = {
                'graph_id': graph_id,
                'data': graph_data,
                'metadata': metadata or {},
                'saved_at': datetime.now().isoformat(),
                'version': self._get_next_version(graph_id)
            }

            # Save to storage
            if self.storage_type == 'json':
                return self._save_json(graph_id, save_data)
            elif self.storage_type == 'pickle':
                return self._save_pickle(graph_id, save_data)
            elif self.storage_type == 'sqlite':
                return self._save_to_sqlite(graph_id, save_data)
            elif self.storage_type == 'postgresql':
                return self._save_to_postgresql(graph_id, save_data)
            else:
                raise ValueError(f"Unsupported storage type: {self.storage_type}")

        except Exception as e:
            logger.error(f"Failed to save graph {graph_id}: {e}")
            return False

    def load_graph(
        self,
        graph_id: str,
        version: Optional[int] = None,
        use_cache: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        加载图谱

        Args:
            graph_id: 图谱ID
            version: 版本号 (None = 最新版本)
            use_cache: 是否使用缓存

        Returns:
            图谱数据 or None
        """
        # Check cache
        cache_key = f"{graph_id}_v{version}" if version else graph_id
        if use_cache and cache_key in self._cache:
            return self._cache[cache_key]

        try:
            # Load from storage
            if self.storage_type == 'json':
                data = self._load_json(graph_id, version)
            elif self.storage_type == 'pickle':
                data = self._load_pickle(graph_id, version)
            elif self.storage_type == 'sqlite':
                data = self._load_from_sqlite(graph_id, version)
            elif self.storage_type == 'postgresql':
                data = self._load_from_postgresql(graph_id, version)
            else:
                raise ValueError(f"Unsupported storage type: {self.storage_type}")

            # Cache
            if use_cache and data:
                self._cache[cache_key] = data

            return data

        except Exception as e:
            logger.error(f"Failed to load graph {graph_id}: {e}")
            return None

    def delete_graph(self, graph_id: str) -> bool:
        """删除图谱（所有版本）"""
        try:
            if self.storage_type == 'json':
                return self._delete_json(graph_id)
            elif self.storage_type == 'pickle':
                return self._delete_pickle(graph_id)
            elif self.storage_type == 'sqlite':
                return self._delete_from_sqlite(graph_id)
            elif self.storage_type == 'postgresql':
                return self._delete_from_postgresql(graph_id)
            else:
                return False

        except Exception as e:
            logger.error(f"Failed to delete graph {graph_id}: {e}")
            return False

    def list_graphs(self) -> List[Dict[str, Any]]:
        """
        列出所有图谱

        Returns:
            [
                {
                    'graph_id': 'doc123',
                    'versions': 3,
                    'latest_version': 3,
                    'saved_at': '2024-01-01T12:00:00',
                    'node_count': 100,
                    'edge_count': 250
                },
                ...
            ]
        """
        try:
            if self.storage_type in ['json', 'pickle']:
                return self._list_file_graphs()
            elif self.storage_type == 'sqlite':
                return self._list_sqlite_graphs()
            elif self.storage_type == 'postgresql':
                return self._list_postgresql_graphs()
            else:
                return []

        except Exception as e:
            logger.error(f"Failed to list graphs: {e}")
            return []

    def update_graph(
        self,
        graph_id: str,
        updates: Dict[str, Any],
        incremental: bool = True
    ) -> bool:
        """
        更新图谱

        Args:
            graph_id: 图谱ID
            updates: 更新内容 {'nodes': [...], 'edges': [...]}
            incremental: 增量更新 (True) 或全量替换 (False)

        Returns:
            是否成功
        """
        if incremental:
            # Load existing graph
            existing = self.load_graph(graph_id)
            if not existing:
                logger.error(f"Graph {graph_id} not found for incremental update")
                return False

            # Merge updates
            graph_data = existing['data']

            if 'nodes' in updates:
                existing_node_ids = {n['id'] for n in graph_data.get('nodes', [])}
                for node in updates['nodes']:
                    if node['id'] not in existing_node_ids:
                        graph_data.setdefault('nodes', []).append(node)

            if 'edges' in updates:
                existing_edges = {
                    (e['source'], e['target'], e.get('type'))
                    for e in graph_data.get('edges', [])
                }
                for edge in updates['edges']:
                    edge_key = (edge['source'], edge['target'], edge.get('type'))
                    if edge_key not in existing_edges:
                        graph_data.setdefault('edges', []).append(edge)

            # Save updated graph
            return self.save_graph(graph_id, graph_data, existing.get('metadata'))

        else:
            # Full replacement
            return self.save_graph(graph_id, updates)

    def get_graph_versions(self, graph_id: str) -> List[int]:
        """获取图谱的所有版本号"""
        try:
            if self.storage_type in ['json', 'pickle']:
                return self._get_file_versions(graph_id)
            elif self.storage_type == 'sqlite':
                return self._get_sqlite_versions(graph_id)
            elif self.storage_type == 'postgresql':
                return self._get_postgresql_versions(graph_id)
            else:
                return []

        except Exception as e:
            logger.error(f"Failed to get versions for {graph_id}: {e}")
            return []

    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()

    # File storage implementations

    def _save_json(self, graph_id: str, data: Dict[str, Any]) -> bool:
        """保存为 JSON 文件"""
        version = data['version']
        file_path = self.storage_path / f"{graph_id}_v{version}.json"

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # Also save as latest
        latest_path = self.storage_path / f"{graph_id}_latest.json"
        with open(latest_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved graph {graph_id} v{version} to {file_path}")
        return True

    def _load_json(self, graph_id: str, version: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """从 JSON 文件加载"""
        if version is None:
            file_path = self.storage_path / f"{graph_id}_latest.json"
        else:
            file_path = self.storage_path / f"{graph_id}_v{version}.json"

        if not file_path.exists():
            return None

        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _delete_json(self, graph_id: str) -> bool:
        """删除 JSON 文件"""
        deleted = False
        for file_path in self.storage_path.glob(f"{graph_id}_*.json"):
            file_path.unlink()
            deleted = True
        return deleted

    def _save_pickle(self, graph_id: str, data: Dict[str, Any]) -> bool:
        """保存为 Pickle 文件"""
        version = data['version']
        file_path = self.storage_path / f"{graph_id}_v{version}.pkl"

        with open(file_path, 'wb') as f:
            pickle.dump(data, f)

        # Latest
        latest_path = self.storage_path / f"{graph_id}_latest.pkl"
        with open(latest_path, 'wb') as f:
            pickle.dump(data, f)

        return True

    def _load_pickle(self, graph_id: str, version: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """从 Pickle 文件加载"""
        if version is None:
            file_path = self.storage_path / f"{graph_id}_latest.pkl"
        else:
            file_path = self.storage_path / f"{graph_id}_v{version}.pkl"

        if not file_path.exists():
            return None

        with open(file_path, 'rb') as f:
            return pickle.load(f)

    def _delete_pickle(self, graph_id: str) -> bool:
        """删除 Pickle 文件"""
        deleted = False
        for file_path in self.storage_path.glob(f"{graph_id}_*.pkl"):
            file_path.unlink()
            deleted = True
        return deleted

    def _list_file_graphs(self) -> List[Dict[str, Any]]:
        """列出文件存储的图谱"""
        extension = '.json' if self.storage_type == 'json' else '.pkl'
        graphs = {}

        for file_path in self.storage_path.glob(f"*_latest{extension}"):
            graph_id = file_path.stem.replace('_latest', '')

            # Load metadata
            data = self._load_json(graph_id) if self.storage_type == 'json' else self._load_pickle(graph_id)
            if data:
                graphs[graph_id] = {
                    'graph_id': graph_id,
                    'versions': len(self._get_file_versions(graph_id)),
                    'latest_version': data.get('version', 1),
                    'saved_at': data.get('saved_at', ''),
                    'node_count': len(data.get('data', {}).get('nodes', [])),
                    'edge_count': len(data.get('data', {}).get('edges', []))
                }

        return list(graphs.values())

    def _get_file_versions(self, graph_id: str) -> List[int]:
        """获取文件版本号"""
        extension = '.json' if self.storage_type == 'json' else '.pkl'
        versions = []

        for file_path in self.storage_path.glob(f"{graph_id}_v*{extension}"):
            version_str = file_path.stem.split('_v')[1]
            versions.append(int(version_str))

        return sorted(versions)

    def _get_next_version(self, graph_id: str) -> int:
        """获取下一个版本号"""
        existing_versions = self.get_graph_versions(graph_id)
        return max(existing_versions, default=0) + 1

    # Database storage implementations

    def _init_database(self):
        """初始化数据库"""
        if self.storage_type == 'sqlite':
            self._init_sqlite()
        elif self.storage_type == 'postgresql':
            self._init_postgresql()

    def _init_sqlite(self):
        """初始化 SQLite 数据库"""
        import sqlite3

        db_path = self.db_connection_string or str(self.storage_path / 'knowledge_graphs.db')
        self.storage_path.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_graphs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                graph_id TEXT NOT NULL,
                version INTEGER NOT NULL,
                data TEXT NOT NULL,
                metadata TEXT,
                saved_at TEXT NOT NULL,
                UNIQUE(graph_id, version)
            )
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_graph_id ON knowledge_graphs(graph_id)
        ''')

        conn.commit()
        conn.close()

    def _init_postgresql(self):
        """初始化 PostgreSQL 数据库"""
        # Placeholder for PostgreSQL initialization
        pass

    def _save_to_sqlite(self, graph_id: str, data: Dict[str, Any]) -> bool:
        """保存到 SQLite"""
        import sqlite3

        db_path = self.db_connection_string or str(self.storage_path / 'knowledge_graphs.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO knowledge_graphs (graph_id, version, data, metadata, saved_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            graph_id,
            data['version'],
            json.dumps(data['data']),
            json.dumps(data.get('metadata', {})),
            data['saved_at']
        ))

        conn.commit()
        conn.close()
        return True

    def _load_from_sqlite(self, graph_id: str, version: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """从 SQLite 加载"""
        import sqlite3

        db_path = self.db_connection_string or str(self.storage_path / 'knowledge_graphs.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        if version is None:
            cursor.execute('''
                SELECT data, metadata, saved_at, version
                FROM knowledge_graphs
                WHERE graph_id = ?
                ORDER BY version DESC
                LIMIT 1
            ''', (graph_id,))
        else:
            cursor.execute('''
                SELECT data, metadata, saved_at, version
                FROM knowledge_graphs
                WHERE graph_id = ? AND version = ?
            ''', (graph_id, version))

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                'graph_id': graph_id,
                'data': json.loads(row[0]),
                'metadata': json.loads(row[1]),
                'saved_at': row[2],
                'version': row[3]
            }

        return None

    def _delete_from_sqlite(self, graph_id: str) -> bool:
        """从 SQLite 删除"""
        import sqlite3

        db_path = self.db_connection_string or str(self.storage_path / 'knowledge_graphs.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('DELETE FROM knowledge_graphs WHERE graph_id = ?', (graph_id,))

        conn.commit()
        conn.close()
        return True

    def _list_sqlite_graphs(self) -> List[Dict[str, Any]]:
        """列出 SQLite 中的图谱"""
        import sqlite3

        db_path = self.db_connection_string or str(self.storage_path / 'knowledge_graphs.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT
                graph_id,
                MAX(version) as latest_version,
                COUNT(*) as versions,
                MAX(saved_at) as saved_at
            FROM knowledge_graphs
            GROUP BY graph_id
        ''')

        graphs = []
        for row in cursor.fetchall():
            # Load latest to get counts
            cursor.execute('''
                SELECT data FROM knowledge_graphs
                WHERE graph_id = ?
                ORDER BY version DESC
                LIMIT 1
            ''', (row[0],))

            data_row = cursor.fetchone()
            if data_row:
                graph_data = json.loads(data_row[0])
                graphs.append({
                    'graph_id': row[0],
                    'latest_version': row[1],
                    'versions': row[2],
                    'saved_at': row[3],
                    'node_count': len(graph_data.get('nodes', [])),
                    'edge_count': len(graph_data.get('edges', []))
                })

        conn.close()
        return graphs

    def _get_sqlite_versions(self, graph_id: str) -> List[int]:
        """获取 SQLite 中的版本"""
        import sqlite3

        db_path = self.db_connection_string or str(self.storage_path / 'knowledge_graphs.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT version FROM knowledge_graphs
            WHERE graph_id = ?
            ORDER BY version
        ''', (graph_id,))

        versions = [row[0] for row in cursor.fetchall()]

        conn.close()
        return versions

    def _save_to_postgresql(self, graph_id: str, data: Dict[str, Any]) -> bool:
        """保存到 PostgreSQL (placeholder)"""
        raise NotImplementedError("PostgreSQL support not yet implemented")

    def _load_from_postgresql(self, graph_id: str, version: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """从 PostgreSQL 加载 (placeholder)"""
        raise NotImplementedError("PostgreSQL support not yet implemented")

    def _delete_from_postgresql(self, graph_id: str) -> bool:
        """从 PostgreSQL 删除 (placeholder)"""
        raise NotImplementedError("PostgreSQL support not yet implemented")

    def _list_postgresql_graphs(self) -> List[Dict[str, Any]]:
        """列出 PostgreSQL 中的图谱 (placeholder)"""
        raise NotImplementedError("PostgreSQL support not yet implemented")

    def _get_postgresql_versions(self, graph_id: str) -> List[int]:
        """获取 PostgreSQL 中的版本 (placeholder)"""
        raise NotImplementedError("PostgreSQL support not yet implemented")
