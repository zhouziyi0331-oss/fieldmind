"""
Execution Engine - 执行引擎

功能：
1. 加载视图定义和绑定配置
2. 根据视图执行多源查询
3. 并发执行查询（asyncio）
4. 聚合结果
5. 执行推理逻辑
6. 返回统一格式
"""

import json
import logging
import asyncio
import time
import sqlite3
import os
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
from neo4j import GraphDatabase
from .inference_engine import create_inference_engine

# 导入向量搜索、全文搜索和缓存服务
try:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from app.services.vector_store_service import create_vector_store
    from app.services.fulltext_search_service import create_fulltext_search_service
    from app.services.cache_service import create_cache_service
    VECTOR_SEARCH_AVAILABLE = True
except ImportError:
    VECTOR_SEARCH_AVAILABLE = False

logger = logging.getLogger(__name__)


class ExecutionEngine:
    """执行引擎"""

    def __init__(self, views_dir: str = "views", bindings_dir: str = "bindings"):
        """
        初始化执行引擎

        Args:
            views_dir: 视图定义目录
            bindings_dir: 绑定配置目录
        """
        self.views_dir = Path(views_dir)
        self.bindings_dir = Path(bindings_dir)

        self.views = {}
        self.bindings = {}
        self.binding_instances = {}

        # 数据源连接
        self.neo4j_driver = None
        self.sqlite_conn = None

        # 推理引擎
        self.inference_engine = create_inference_engine()

        # 向量搜索、全文搜索和缓存服务
        self.vector_store = None
        self.fulltext_search = None
        self.cache_service = None

        if VECTOR_SEARCH_AVAILABLE:
            try:
                self.vector_store = create_vector_store()
                self.fulltext_search = create_fulltext_search_service()
                self.cache_service = create_cache_service()
                logger.info("✅ 向量搜索、全文搜索和缓存服务已加载")
            except Exception as e:
                logger.warning(f"⚠️ 扩展服务加载失败: {e}")

        # 从环境变量读取配置
        self.neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD", "fieldmind123")
        self.sqlite_db_path = os.getenv("SQLITE_DB_PATH", "data/fieldmind.db")

        self._load_views()
        self._load_bindings()
        self._initialize_bindings()
        self._initialize_datasources()

    def _load_views(self):
        """加载所有视图定义"""
        if not self.views_dir.exists():
            logger.error(f"Views directory not found: {self.views_dir}")
            return

        for view_file in self.views_dir.glob("*.json"):
            try:
                with open(view_file, 'r', encoding='utf-8') as f:
                    view = json.load(f)
                    view_id = view.get('view_id')
                    if view_id:
                        self.views[view_id] = view
                        logger.info(f"Loaded view: {view_id}")
            except Exception as e:
                logger.error(f"Error loading view {view_file}: {e}")

        logger.info(f"Loaded {len(self.views)} views")

    def _load_bindings(self):
        """加载所有绑定配置"""
        if not self.bindings_dir.exists():
            logger.error(f"Bindings directory not found: {self.bindings_dir}")
            return

        for binding_file in self.bindings_dir.glob("*.json"):
            try:
                with open(binding_file, 'r', encoding='utf-8') as f:
                    binding = json.load(f)
                    binding_id = binding.get('binding_id')
                    if binding_id:
                        self.bindings[binding_id] = binding
                        logger.info(f"Loaded binding: {binding_id}")
            except Exception as e:
                logger.error(f"Error loading binding {binding_file}: {e}")

        logger.info(f"Loaded {len(self.bindings)} bindings")

    def _initialize_bindings(self):
        """初始化绑定实例（连接到数据源）"""
        # 这里暂时不实际连接，只是记录配置
        # 实际连接会在第一次使用时建立
        for binding_id, binding_config in self.bindings.items():
            channel_type = binding_config.get('channel_type')
            self.binding_instances[binding_id] = {
                'config': binding_config,
                'channel_type': channel_type,
                'initialized': False,
                'connection': None
            }

        logger.info(f"Initialized {len(self.binding_instances)} binding instances")

    def _initialize_datasources(self):
        """初始化数据源连接"""
        try:
            # 初始化 Neo4j
            self.neo4j_driver = GraphDatabase.driver(
                self.neo4j_uri,
                auth=(self.neo4j_user, self.neo4j_password)
            )
            logger.info(f"✅ Neo4j连接成功: {self.neo4j_uri}")
        except Exception as e:
            logger.error(f"❌ Neo4j连接失败: {e}")
            self.neo4j_driver = None

        try:
            # 初始化 SQLite
            if os.path.exists(self.sqlite_db_path):
                self.sqlite_conn = sqlite3.connect(self.sqlite_db_path)
                self.sqlite_conn.row_factory = sqlite3.Row
                logger.info(f"✅ SQLite连接成功: {self.sqlite_db_path}")
            else:
                logger.warning(f"⚠️  SQLite数据库不存在: {self.sqlite_db_path}")
        except Exception as e:
            logger.error(f"❌ SQLite连接失败: {e}")
            self.sqlite_conn = None

    def close(self):
        """关闭所有数据源连接"""
        if self.neo4j_driver:
            self.neo4j_driver.close()
            logger.info("Neo4j连接已关闭")

        if self.sqlite_conn:
            self.sqlite_conn.close()
            logger.info("SQLite连接已关闭")

    async def execute(self, view_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行视图查询（支持缓存）

        Args:
            view_id: 视图ID
            parameters: 查询参数

        Returns:
            {
                'status': 'success' | 'error',
                'view_id': str,
                'data': {...},  # 视图定义的output结构
                'evidence': [...],  # 数据来源记录
                'metadata': {
                    'query_time_ms': int,
                    'sources_used': int,
                    'cache_hit': bool
                }
            }
        """
        start_time = time.time()

        if view_id not in self.views:
            return {
                'status': 'error',
                'error': f'View not found: {view_id}',
                'metadata': {
                    'query_time_ms': int((time.time() - start_time) * 1000)
                }
            }

        view = self.views[view_id]

        # 尝试从缓存获取结果
        cache_hit = False
        if self.cache_service and self.cache_service.enabled:
            cached_result = self.cache_service.get_cached_view_result(view_id, parameters)
            if cached_result is not None:
                logger.info(f"✅ 缓存命中: {view_id}")
                cached_result['metadata']['cache_hit'] = True
                cached_result['metadata']['query_time_ms'] = int((time.time() - start_time) * 1000)
                return cached_result

        try:
            # 1. 执行所有数据绑定
            binding_results = await self._execute_bindings(view, parameters)

            # 2. 组装输出数据
            output_data = self._assemble_output(view, binding_results)

            # 3. 执行推理逻辑
            if 'inference_logic' in view:
                output_data = await self._execute_inference(view, output_data)

            # 4. 收集证据
            evidence = self._collect_evidence(binding_results)

            elapsed_ms = int((time.time() - start_time) * 1000)

            result = {
                'status': 'success',
                'view_id': view_id,
                'data': output_data,
                'evidence': evidence,
                'metadata': {
                    'query_time_ms': elapsed_ms,
                    'sources_used': len(binding_results),
                    'cache_hit': cache_hit,
                    'timestamp': datetime.utcnow().isoformat()
                }
            }

            # 缓存结果
            if self.cache_service and self.cache_service.enabled:
                self.cache_service.cache_view_result(view_id, parameters, result, ttl=600)

            return result

        except Exception as e:
            logger.error(f"Error executing view {view_id}: {e}", exc_info=True)
            elapsed_ms = int((time.time() - start_time) * 1000)

            return {
                'status': 'error',
                'view_id': view_id,
                'error': str(e),
                'metadata': {
                    'query_time_ms': elapsed_ms
                }
            }

    async def _execute_bindings(self, view: Dict, parameters: Dict) -> Dict[str, Any]:
        """
        执行所有数据绑定（并发）

        Returns:
            {
                'binding_id': {
                    'status': 'success' | 'error',
                    'data': Any,
                    'query': str,
                    'duration_ms': int
                }
            }
        """
        data_bindings = view.get('data_bindings', [])
        execution_strategy = view.get('execution_strategy', {})
        parallel = execution_strategy.get('parallel_bindings', True)

        if parallel:
            # 并发执行
            tasks = [
                self._execute_single_binding(binding_def, parameters)
                for binding_def in data_bindings
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        else:
            # 串行执行
            results = []
            for binding_def in data_bindings:
                result = await self._execute_single_binding(binding_def, parameters)
                results.append(result)

        # 组织结果
        binding_results = {}
        for i, binding_def in enumerate(data_bindings):
            binding_id = binding_def.get('binding_id')
            result = results[i]

            if isinstance(result, Exception):
                binding_results[binding_id] = {
                    'status': 'error',
                    'error': str(result),
                    'duration_ms': 0
                }
            else:
                binding_results[binding_id] = result

        return binding_results

    async def _execute_single_binding(self, binding_def: Dict, parameters: Dict) -> Dict[str, Any]:
        """
        执行单个数据绑定

        Args:
            binding_def: 视图中的绑定定义
            parameters: 查询参数

        Returns:
            {
                'status': 'success',
                'data': Any,
                'query': str,
                'channel_type': str,
                'duration_ms': int
            }
        """
        start_time = time.time()

        binding_id = binding_def.get('binding_id')
        channel_type = binding_def.get('channel_type')
        query_template = binding_def.get('query_template')
        output_mapping = binding_def.get('output_mapping', {})

        try:
            # 模拟查询执行（实际实现需要连接真实数据源）
            # TODO: 根据 channel_type 调用相应的数据源
            data = await self._mock_query(channel_type, query_template, parameters)

            duration_ms = int((time.time() - start_time) * 1000)

            return {
                'status': 'success',
                'binding_id': binding_id,
                'channel_type': channel_type,
                'data': data,
                'query': query_template,
                'output_mapping': output_mapping,
                'duration_ms': duration_ms
            }

        except Exception as e:
            logger.error(f"Error executing binding {binding_id}: {e}")
            duration_ms = int((time.time() - start_time) * 1000)

            return {
                'status': 'error',
                'binding_id': binding_id,
                'error': str(e),
                'duration_ms': duration_ms
            }

    async def _mock_query(self, channel_type: str, query: str, parameters: Dict) -> Any:
        """
        执行真实查询

        支持：
        - graph: 连接 Neo4j，执行 Cypher
        - sql: 连接 SQLite，执行 SQL
        - vector: 连接 ChromaDB，执行向量检索
        - fulltext: 连接 SQLite FTS5，执行全文搜索
        """
        if channel_type == 'graph':
            return await self._execute_neo4j_query(query, parameters)
        elif channel_type == 'sql':
            return await self._execute_sqlite_query(query, parameters)
        elif channel_type == 'vector':
            return await self._execute_vector_query(query, parameters)
        elif channel_type == 'fulltext':
            return await self._execute_fulltext_query(query, parameters)
        else:
            return {}

    async def _execute_neo4j_query(self, query: str, parameters: Dict) -> Dict[str, Any]:
        """
        执行 Neo4j Cypher 查询

        Args:
            query: Cypher 查询语句
            parameters: 查询参数

        Returns:
            {
                'nodes': [...],
                'relationships': [...],
                'records': [...]
            }
        """
        if not self.neo4j_driver:
            logger.error("Neo4j driver not initialized")
            return {'nodes': [], 'relationships': [], 'records': []}

        try:
            # 在线程池中执行同步的 Neo4j 查询
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._run_neo4j_query_sync,
                query,
                parameters
            )
            return result
        except Exception as e:
            logger.error(f"Neo4j query error: {e}")
            return {'nodes': [], 'relationships': [], 'records': [], 'error': str(e)}

    def _run_neo4j_query_sync(self, query: str, parameters: Dict) -> Dict[str, Any]:
        """同步执行 Neo4j 查询"""
        with self.neo4j_driver.session() as session:
            result = session.run(query, parameters)
            records = []
            nodes = []
            relationships = []

            for record in result:
                # 转换记录为字典
                record_dict = {}
                for key in record.keys():
                    value = record[key]

                    # 处理 Neo4j 节点
                    if hasattr(value, 'labels'):  # Node
                        node_dict = dict(value)
                        node_dict['_labels'] = list(value.labels)
                        node_dict['_id'] = value.id
                        nodes.append(node_dict)
                        record_dict[key] = node_dict

                    # 处理 Neo4j 关系
                    elif hasattr(value, 'type'):  # Relationship
                        rel_dict = dict(value)
                        rel_dict['_type'] = value.type
                        rel_dict['_id'] = value.id
                        relationships.append(rel_dict)
                        record_dict[key] = rel_dict

                    # 处理列表
                    elif isinstance(value, list):
                        processed_list = []
                        for item in value:
                            if hasattr(item, 'labels'):  # Node in list
                                node_dict = dict(item)
                                node_dict['_labels'] = list(item.labels)
                                node_dict['_id'] = item.id
                                nodes.append(node_dict)
                                processed_list.append(node_dict)
                            else:
                                processed_list.append(item)
                        record_dict[key] = processed_list

                    # 其他类型直接保存
                    else:
                        record_dict[key] = value

                records.append(record_dict)

            return {
                'nodes': nodes,
                'relationships': relationships,
                'records': records,
                'count': len(records)
            }

    async def _execute_sqlite_query(self, query: str, parameters: Dict) -> Dict[str, Any]:
        """
        执行 SQLite 查询

        Args:
            query: SQL 查询语句
            parameters: 查询参数

        Returns:
            {
                'rows': [...],
                'columns': [...],
                'count': int
            }
        """
        if not self.sqlite_conn:
            logger.error("SQLite connection not initialized")
            return {'rows': [], 'columns': [], 'count': 0}

        try:
            # 在线程池中执行同步的 SQLite 查询
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._run_sqlite_query_sync,
                query,
                parameters
            )
            return result
        except Exception as e:
            logger.error(f"SQLite query error: {e}")
            return {'rows': [], 'columns': [], 'count': 0, 'error': str(e)}

    def _run_sqlite_query_sync(self, query: str, parameters: Dict) -> Dict[str, Any]:
        """同步执行 SQLite 查询（线程安全）"""
        # 为每个查询创建新连接以避免线程问题
        conn = sqlite3.connect(self.sqlite_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            # 将参数从字典格式转换为命名参数
            cursor.execute(query, parameters)

            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description] if cursor.description else []

            # 转换 Row 对象为字典
            rows_dict = [dict(row) for row in rows]

            return {
                'rows': rows_dict,
                'columns': columns,
                'count': len(rows_dict)
            }
        finally:
            conn.close()

    async def _execute_vector_query(self, query: str, parameters: Dict) -> Dict[str, Any]:
        """
        执行向量检索

        Args:
            query: 查询文本
            parameters: 查询参数（如n_results, where等）

        Returns:
            {
                'ids': [...],
                'documents': [...],
                'metadatas': [...],
                'distances': [...]
            }
        """
        if not self.vector_store:
            logger.warning("向量存储服务未初始化")
            return {'ids': [[]], 'documents': [[]], 'metadatas': [[]], 'distances': [[]]}

        try:
            # 从参数中提取配置
            n_results = parameters.get('n_results', 10)
            where = parameters.get('where', None)
            where_document = parameters.get('where_document', None)

            # 执行向量搜索
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                self.vector_store.search,
                query,
                n_results,
                where,
                where_document
            )

            return results

        except Exception as e:
            logger.error(f"向量检索失败: {e}")
            return {'ids': [[]], 'documents': [[]], 'metadatas': [[]], 'distances': [[]], 'error': str(e)}

    async def _execute_fulltext_query(self, query: str, parameters: Dict) -> Dict[str, Any]:
        """
        执行全文搜索

        Args:
            query: 查询文本
            parameters: 查询参数（如limit, highlight等）

        Returns:
            {
                'results': [
                    {
                        'chunk_id': int,
                        'text': str,
                        'rank': float
                    },
                    ...
                ]
            }
        """
        if not self.fulltext_search:
            logger.warning("全文搜索服务未初始化")
            return {'results': []}

        try:
            # 从参数中提取配置
            limit = parameters.get('limit', 10)
            highlight = parameters.get('highlight', True)

            # 执行全文搜索
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                self.fulltext_search.search,
                query,
                limit,
                highlight
            )

            return {'results': results, 'count': len(results)}

        except Exception as e:
            logger.error(f"全文搜索失败: {e}")
            return {'results': [], 'error': str(e)}

    def _assemble_output(self, view: Dict, binding_results: Dict) -> Dict[str, Any]:
        """
        根据视图定义组装输出数据

        Args:
            view: 视图定义
            binding_results: 绑定执行结果

        Returns:
            视图定义的 output 结构
        """
        output_schema = view.get('output', {})
        output_data = {}

        for field_name, field_def in output_schema.items():
            source = field_def.get('source')
            field_type = field_def.get('type')

            # 根据 source 从 binding_results 中提取数据
            if source == 'graph_query':
                # 从图查询结果中提取
                output_data[field_name] = self._extract_from_graph(
                    binding_results, field_name, field_def
                )
            elif source == 'sql_query':
                # 从SQL查询结果中提取
                output_data[field_name] = self._extract_from_sql(
                    binding_results, field_name, field_def
                )
            elif source == 'computed':
                # 计算字段，稍后在推理阶段处理
                output_data[field_name] = None
            elif source == 'inference':
                # 推理字段，稍后在推理阶段处理
                output_data[field_name] = None
            else:
                # 默认
                output_data[field_name] = None

        return output_data

    def _extract_from_graph(self, binding_results: Dict, field_name: str, field_def: Dict) -> Any:
        """从图查询结果中提取字段"""
        # 查找匹配的绑定结果
        for binding_id, result in binding_results.items():
            if result.get('channel_type') == 'graph' and result.get('status') == 'success':
                # 根据 output_mapping 提取数据
                mapping = result.get('output_mapping', {})
                if field_name in mapping:
                    return result.get('data', {})

        return None

    def _extract_from_sql(self, binding_results: Dict, field_name: str, field_def: Dict) -> Any:
        """从SQL查询结果中提取字段"""
        for binding_id, result in binding_results.items():
            if result.get('channel_type') == 'sql' and result.get('status') == 'success':
                mapping = result.get('output_mapping', {})
                if field_name in mapping:
                    return result.get('data', {})

        return None

    async def _execute_inference(self, view: Dict, output_data: Dict) -> Dict[str, Any]:
        """
        执行推理逻辑

        Args:
            view: 视图定义
            output_data: 当前输出数据

        Returns:
            更新后的输出数据
        """
        return await self.inference_engine.execute_inference(view, output_data)

    def _collect_evidence(self, binding_results: Dict) -> List[Dict]:
        """
        收集证据（数据来源记录）

        Returns:
            [
                {
                    'source': 'graph_query',
                    'binding_id': 'graph_asset_info',
                    'query': 'MATCH ...',
                    'duration_ms': 123,
                    'status': 'success'
                }
            ]
        """
        evidence = []

        for binding_id, result in binding_results.items():
            evidence.append({
                'binding_id': binding_id,
                'source': result.get('channel_type'),
                'query': result.get('query'),
                'duration_ms': result.get('duration_ms'),
                'status': result.get('status')
            })

        return evidence


def create_engine(views_dir: str = "views", bindings_dir: str = "bindings") -> ExecutionEngine:
    """工厂方法：创建执行引擎"""
    return ExecutionEngine(views_dir, bindings_dir)
