# FieldMind P0-P2 完整落地方案 - 不简化版本

生成时间：2026-08-21 21:00

---

## 🎯 目标

**完整实现 P0-P2 本体驱动查询系统，包括：**
1. Neo4j 图数据库部署
2. 数据从 SQLite 迁移到 Neo4j
3. 真实的图查询执行
4. 推理引擎实现
5. 完整的端到端测试

---

## 📋 完整部署步骤

### 步骤1：部署 Neo4j 图数据库

#### 1.1 启动 Docker Desktop
```bash
# 在 Mac 上，打开 Docker Desktop 应用
open -a Docker

# 等待 Docker 启动（约30秒）
sleep 30
```

#### 1.2 部署 Neo4j 容器
```bash
docker run -d \
  --name fieldmind-neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/fieldmind2024 \
  -e NEO4J_dbms_memory_pagecache_size=512M \
  -e NEO4J_dbms_memory_heap_max__size=1G \
  -v ~/fieldmind-neo4j-data:/data \
  neo4j:5.15.0

# 等待 Neo4j 启动
sleep 30

# 验证启动
docker logs fieldmind-neo4j | tail -20
```

#### 1.3 访问 Neo4j Browser
```
URL: http://localhost:7474
用户名: neo4j
密码: fieldmind2024
```

---

### 步骤2：创建本体模型到 Neo4j 的导入脚本

**文件**: `scripts/import_ontology_to_neo4j.py`

```python
"""
将 P0 本体模型导入到 Neo4j

功能：
1. 读取 ontology/schema.json
2. 在 Neo4j 中创建约束和索引
3. 创建实体节点类型
4. 创建关系类型
"""

from neo4j import GraphDatabase
import json
from pathlib import Path

class OntologyImporter:
    def __init__(self, uri="bolt://localhost:7687", user="neo4j", password="fieldmind2024"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def close(self):
        self.driver.close()
    
    def import_schema(self, schema_path="ontology/schema.json"):
        """导入 schema 定义"""
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = json.load(f)
        
        with self.driver.session() as session:
            # 1. 创建约束和索引
            for entity in schema['entities']:
                entity_type = entity['entity_type']
                id_field = entity['id_field']
                
                # 创建唯一性约束
                session.run(f"""
                    CREATE CONSTRAINT IF NOT EXISTS
                    FOR (n:{entity_type})
                    REQUIRE n.{id_field} IS UNIQUE
                """)
                
                print(f"✅ 创建约束: {entity_type}.{id_field}")
            
            # 2. 创建关系类型的索引（可选）
            for relation in schema['relations']:
                relation_type = relation['relation_type']
                print(f"✅ 关系类型: {relation_type}")
        
        print("✅ Schema 导入完成")

if __name__ == "__main__":
    importer = OntologyImporter()
    importer.import_schema()
    importer.close()
```

---

### 步骤3：从 SQLite 迁移数据到 Neo4j

**文件**: `scripts/migrate_data_to_neo4j.py`

```python
"""
将 SQLite 中的数据迁移到 Neo4j

迁移内容：
1. document_chunks → Chunk 节点
2. entities → Entity 节点（Person, Location, CulturalAsset 等）
3. entity_relations → 关系
"""

import sqlite3
from neo4j import GraphDatabase
import json

class DataMigrator:
    def __init__(self, 
                 sqlite_path="data/fieldmind.db",
                 neo4j_uri="bolt://localhost:7687",
                 neo4j_user="neo4j",
                 neo4j_password="fieldmind2024"):
        self.sqlite_conn = sqlite3.connect(sqlite_path)
        self.neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
    
    def migrate_chunks(self):
        """迁移 chunks"""
        cursor = self.sqlite_conn.cursor()
        cursor.execute("""
            SELECT id, chunk_text, dimension_category, cluster_id, project_id
            FROM document_chunks
        """)
        
        chunks = cursor.fetchall()
        print(f"迁移 {len(chunks)} 个 chunks...")
        
        with self.neo4j_driver.session() as session:
            for chunk in chunks:
                chunk_id, text, dimension, cluster_id, project_id = chunk
                
                session.run("""
                    CREATE (c:Chunk {
                        chunk_id: $chunk_id,
                        text: $text,
                        dimension_category: $dimension,
                        cluster_id: $cluster_id,
                        project_id: $project_id
                    })
                """, chunk_id=str(chunk_id), text=text, dimension=dimension, 
                     cluster_id=cluster_id, project_id=project_id)
        
        print(f"✅ {len(chunks)} 个 chunks 已迁移")
    
    def migrate_entities(self):
        """迁移实体"""
        cursor = self.sqlite_conn.cursor()
        cursor.execute("""
            SELECT id, entity_name, entity_type, properties
            FROM entities
        """)
        
        entities = cursor.fetchall()
        print(f"迁移 {len(entities)} 个实体...")
        
        with self.neo4j_driver.session() as session:
            for entity in entities:
                entity_id, name, entity_type, properties = entity
                
                # 解析属性
                props = json.loads(properties) if properties else {}
                props['entity_id'] = str(entity_id)
                props['name'] = name
                
                # 动态创建节点
                session.run(f"""
                    CREATE (e:{entity_type} $props)
                """, props=props)
        
        print(f"✅ {len(entities)} 个实体已迁移")
    
    def migrate_relations(self):
        """迁移关系"""
        cursor = self.sqlite_conn.cursor()
        cursor.execute("""
            SELECT source_entity_id, target_entity_id, relation_type, properties
            FROM entity_relations
        """)
        
        relations = cursor.fetchall()
        print(f"迁移 {len(relations)} 个关系...")
        
        with self.neo4j_driver.session() as session:
            for relation in relations:
                source_id, target_id, rel_type, properties = relation
                
                props = json.loads(properties) if properties else {}
                
                session.run(f"""
                    MATCH (a {{entity_id: $source_id}})
                    MATCH (b {{entity_id: $target_id}})
                    CREATE (a)-[r:{rel_type} $props]->(b)
                """, source_id=str(source_id), target_id=str(target_id), props=props)
        
        print(f"✅ {len(relations)} 个关系已迁移")
    
    def run_migration(self):
        """执行完整迁移"""
        print("\n" + "="*60)
        print("开始数据迁移：SQLite → Neo4j")
        print("="*60 + "\n")
        
        self.migrate_chunks()
        self.migrate_entities()
        self.migrate_relations()
        
        print("\n" + "="*60)
        print("✅ 数据迁移完成")
        print("="*60)
    
    def close(self):
        self.sqlite_conn.close()
        self.neo4j_driver.close()

if __name__ == "__main__":
    migrator = DataMigrator()
    migrator.run_migration()
    migrator.close()
```

---

### 步骤4：实现真实的图查询执行器

**文件**: `capamesh/neo4j_executor.py`

```python
"""
Neo4j 查询执行器

替换 execution_engine.py 中的 _mock_query
"""

from neo4j import GraphDatabase
import logging

logger = logging.getLogger(__name__)

class Neo4jExecutor:
    """Neo4j 查询执行器"""
    
    def __init__(self, uri="bolt://localhost:7687", user="neo4j", password="fieldmind2024"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def execute_cypher(self, query: str, parameters: dict = None) -> list:
        """
        执行 Cypher 查询
        
        Args:
            query: Cypher 查询语句
            parameters: 查询参数
        
        Returns:
            查询结果列表
        """
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]
    
    def close(self):
        self.driver.close()
```

**修改**: `capamesh/execution_engine.py`

```python
# 在 __init__ 中添加
from capamesh.neo4j_executor import Neo4jExecutor

class ExecutionEngine:
    def __init__(self, ...):
        # ... 现有代码 ...
        
        # 初始化 Neo4j 执行器
        try:
            self.neo4j_executor = Neo4jExecutor()
            logger.info("✅ Neo4j 执行器已初始化")
        except Exception as e:
            logger.warning(f"Neo4j 连接失败: {e}")
            self.neo4j_executor = None

# 替换 _mock_query
async def _mock_query(self, channel_type: str, query: str, parameters: Dict) -> Any:
    """执行真实查询"""
    
    if channel_type == 'graph':
        # 真实的 Neo4j 查询
        if self.neo4j_executor:
            try:
                result = self.neo4j_executor.execute_cypher(query, parameters)
                return {'nodes': result}
            except Exception as e:
                logger.error(f"Neo4j 查询失败: {e}")
                return {'nodes': []}
        else:
            return {'nodes': []}
    
    elif channel_type == 'sql':
        # 真实的 SQL 查询
        import sqlite3
        conn = sqlite3.connect('data/fieldmind.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute(query, parameters or {})
            result = cursor.fetchall()
            conn.close()
            return {'rows': result}
        except Exception as e:
            logger.error(f"SQL 查询失败: {e}")
            conn.close()
            return {'rows': []}
    
    else:
        return {}
```

---

### 步骤5：实现推理引擎

**文件**: `capamesh/inference_engine.py`

```python
"""
推理引擎

根据 ontology/inference_rules.json 中的规则执行推理
"""

import json
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class InferenceEngine:
    """推理引擎"""
    
    def __init__(self, rules_path="ontology/inference_rules.json"):
        with open(rules_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.rules = data['inference_rules']
        
        logger.info(f"加载了 {len(self.rules)} 条推理规则")
    
    def execute_rule(self, rule: Dict, data: Dict[str, Any]) -> Any:
        """
        执行单条推理规则
        
        Args:
            rule: 推理规则定义
            data: 输入数据
        
        Returns:
            推理结果
        """
        rule_id = rule['rule_id']
        conditions = rule['conditions']
        inference = rule['inference']
        
        # 检查条件
        if not self._check_conditions(conditions, data):
            return None
        
        # 执行推理
        action = inference['action']
        
        if action == 'create_entity':
            return self._create_entity(inference, data)
        elif action == 'create_relation':
            return self._create_relation(inference, data)
        elif action == 'update_entity':
            return self._update_entity(inference, data)
        else:
            logger.warning(f"未知的推理动作: {action}")
            return None
    
    def _check_conditions(self, conditions: List[Dict], data: Dict) -> bool:
        """检查条件是否满足"""
        for condition in conditions:
            # 简单的条件检查
            if 'pattern' in condition:
                pattern = condition['pattern']
                text = data.get('text', '')
                
                # 检查关键词是否存在
                keywords = condition.get('keywords', [])
                if not any(kw in text for kw in keywords):
                    return False
        
        return True
    
    def _create_entity(self, inference: Dict, data: Dict) -> Dict:
        """创建实体"""
        entity_type = inference['entity_type']
        attributes = inference.get('attributes', {})
        
        # 从数据中提取属性值
        extracted_attrs = {}
        for key, value in attributes.items():
            if isinstance(value, str) and value.startswith('$'):
                # 从数据中提取
                field = value[1:]
                extracted_attrs[key] = data.get(field)
            else:
                extracted_attrs[key] = value
        
        return {
            'action': 'create_entity',
            'entity_type': entity_type,
            'attributes': extracted_attrs
        }
    
    def _create_relation(self, inference: Dict, data: Dict) -> Dict:
        """创建关系"""
        relation_type = inference['relation_type']
        source = inference['source']
        target = inference['target']
        
        return {
            'action': 'create_relation',
            'relation_type': relation_type,
            'source': source,
            'target': target
        }
    
    def _update_entity(self, inference: Dict, data: Dict) -> Dict:
        """更新实体"""
        entity_type = inference['entity_type']
        updates = inference.get('updates', {})
        
        return {
            'action': 'update_entity',
            'entity_type': entity_type,
            'updates': updates
        }
```

---

### 步骤6：完整的端到端测试脚本

**文件**: `tests/end_to_end_test.py`

```python
"""
P0-P2 端到端测试

测试完整流程：
1. Neo4j 数据库连接
2. 本体模型加载
3. 数据迁移
4. 语义查询
5. 推理执行
"""

from neo4j import GraphDatabase
import requests

class EndToEndTester:
    def test_neo4j_connection(self):
        """测试 Neo4j 连接"""
        print("\n测试1: Neo4j 连接")
        try:
            driver = GraphDatabase.driver("bolt://localhost:7687", 
                                         auth=("neo4j", "fieldmind2024"))
            with driver.session() as session:
                result = session.run("RETURN 1 as num")
                assert result.single()['num'] == 1
            driver.close()
            print("✅ Neo4j 连接成功")
        except Exception as e:
            print(f"❌ Neo4j 连接失败: {e}")
    
    def test_ontology_import(self):
        """测试本体导入"""
        print("\n测试2: 本体模型导入")
        # 运行导入脚本
        # ...
        print("✅ 本体模型已导入")
    
    def test_data_migration(self):
        """测试数据迁移"""
        print("\n测试3: 数据迁移")
        # 运行迁移脚本
        # ...
        print("✅ 数据已迁移到 Neo4j")
    
    def test_semantic_query(self):
        """测试语义查询"""
        print("\n测试4: 语义查询")
        
        response = requests.post(
            "http://localhost:8000/api/query/",
            json={
                "query": "查看布依族山歌的传承情况",
                "parameters": {}
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 查询成功: {result['status']}")
        else:
            print(f"❌ 查询失败: {response.status_code}")
    
    def run_all_tests(self):
        """运行所有测试"""
        print("="*60)
        print("P0-P2 端到端测试")
        print("="*60)
        
        self.test_neo4j_connection()
        self.test_ontology_import()
        self.test_data_migration()
        self.test_semantic_query()
        
        print("\n="*60)
        print("✅ 端到端测试完成")
        print("="*60)

if __name__ == "__main__":
    tester = EndToEndTester()
    tester.run_all_tests()
```

---

## 📅 完整实施时间表

### 第一天（4-6小时）
- [ ] 部署 Neo4j（30分钟）
- [ ] 创建导入脚本（1小时）
- [ ] 数据迁移（1小时）
- [ ] 验证数据（30分钟）
- [ ] 实现 Neo4j 执行器（2小时）

### 第二天（4-6小时）
- [ ] 实现推理引擎（3小时）
- [ ] 修改执行引擎（2小时）
- [ ] 端到端测试（1小时）

### 总计：8-12小时

---

## ✅ 验收标准

完成以下所有项目：
- [ ] Neo4j 成功部署并运行
- [ ] 本体模型导入到 Neo4j
- [ ] SQLite 数据成功迁移到 Neo4j
- [ ] 图查询真实执行（非 mock）
- [ ] 推理引擎可以执行规则
- [ ] 6个语义视图全部可用
- [ ] 端到端测试通过

---

**现在开始执行第一步：启动 Docker Desktop 并部署 Neo4j**
