# FieldMind P0-P2 完整落地报告 - 不简化版本

生成时间：2026-08-21 22:00

---

## 🎯 执行摘要

### 当前状态
- ✅ Neo4j 已部署并运行
- ✅ 本体模型已导入（8个实体类型，12个关系类型）
- ✅ 2个 chunks 已迁移到 Neo4j
- ⚠️ 实体和关系表不存在，需要补充数据采集

### 核心问题
**数据库中缺少实体和关系数据**

当前 SQLite 数据库有：
- ✅ document_chunks 表（2条数据）
- ✅ entities 表（0条数据）
- ❌ entity_relations 表（不存在）
- ✅ object_relations 表（存在但结构不同）

---

## 📊 已完成的工作

### 1. Neo4j 部署 ✅

**容器信息**：
```
容器名: fieldmind-neo4j
镜像: neo4j:5.15.0
端口: 7474 (Web UI), 7687 (Bolt)
认证: neo4j / fieldmind2024
数据卷: ~/fieldmind-neo4j-data
```

**验证**：
```bash
docker ps | grep neo4j
# 输出：4ff72cc7f818   neo4j:5.15.0
```

### 2. 本体模型导入 ✅

**已创建的约束**：
- Person.person_id - UNIQUE
- Location.location_id - UNIQUE
- CulturalAsset.asset_id - UNIQUE
- Event.event_id - UNIQUE
- Policy.policy_id - UNIQUE
- Document.document_id - UNIQUE
- Chunk.chunk_id - UNIQUE
- Organization.org_id - UNIQUE

**已定义的关系类型**：
1. Person -[belongs_to]-> Location
2. Person -[lives_in]-> Location
3. Person -[inherits]-> CulturalAsset
4. Person -[participates_in]-> Event
5. Event -[occurs_at]-> Location
6. CulturalAsset -[related_to]-> Policy
7. Entity -[mentioned_in]-> Chunk
8. Chunk -[extracted_from]-> Document
9. Person -[knows]-> Person
10. Person -[manages]-> Organization
11. CulturalAsset -[located_in]-> Location
12. Organization -[implements]-> Policy

### 3. Chunks 迁移 ✅

**已迁移**：2个 chunks 到 Neo4j

**验证**：
```cypher
MATCH (c:Chunk) RETURN count(c)
// 返回: 2
```

---

## ⚠️ 当前问题和解决方案

### 问题1：实体表为空

**现状**：
```sql
SELECT COUNT(*) FROM entities;
-- 返回: 0
```

**原因**：还没有运行实体抽取

**解决方案**：需要实现实体抽取流程

#### 方案A：基于规则的实体抽取（快速）
```python
# 从 chunks 中提取实体
# 规则：
# - 人名：姓氏 + 大爷/奶奶/师傅
# - 地点：XX村/寨/镇
# - 文化资产：XX山歌/蜡染/刺绣
```

#### 方案B：基于 NER 的实体抽取（准确）
```python
# 使用 NLP 模型
# - spaCy
# - HanLP
# - 自定义训练的模型
```

### 问题2：关系表不存在

**现状**：
```sql
SELECT name FROM sqlite_master WHERE type='table' AND name='entity_relations';
-- 返回: (空)
```

**存在的表**：
- object_relations（字段不同）
- document_relations（字段不同）

**解决方案**：需要统一关系表结构

#### 创建标准的关系表
```sql
CREATE TABLE entity_relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_entity_id VARCHAR(36) NOT NULL,
    target_entity_id VARCHAR(36) NOT NULL,
    relation_type VARCHAR(50) NOT NULL,
    properties JSON,
    confidence FLOAT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_entity_id) REFERENCES entities(id),
    FOREIGN KEY (target_entity_id) REFERENCES entities(id)
);
```

### 问题3：Chunk 关键词已迁移但实体未关联

**现状**：
- chunk_keywords 表有5条数据
- 但这些关键词没有转换为实体

**解决方案**：将关键词转换为实体

```python
# 对每个关键词
# 1. 判断类型（人/地点/文化资产）
# 2. 创建实体
# 3. 创建 mentioned_in 关系
```

---

## 🚀 完整实施路径（不简化）

### 阶段1：数据采集和实体抽取（必需）

#### 步骤1.1：实现实体抽取服务

**文件**：`app/services/entity_extraction_service.py`

**功能**：
- 从 chunks 中抽取实体
- 支持人名、地点、文化资产、事件、政策、组织
- 使用规则 + NLP 混合方法
- 存储到 entities 表

**实现要点**：
```python
class EntityExtractionService:
    def extract_from_chunk(self, chunk_text):
        """
        从文本中抽取实体
        
        返回：
        [
            {
                'entity_type': 'Person',
                'name': '王大爷',
                'confidence': 0.95
            },
            ...
        ]
        """
        pass
    
    def save_to_db(self, entities):
        """保存到 entities 表"""
        pass
```

#### 步骤1.2：实现关系抽取服务

**文件**：`app/services/relation_extraction_service.py`

**功能**：
- 从文本中抽取实体关系
- 支持12种关系类型
- 存储到 entity_relations 表

**实现要点**：
```python
class RelationExtractionService:
    def extract_from_chunk(self, chunk_text, entities):
        """
        从文本中抽取关系
        
        返回：
        [
            {
                'source_entity_id': 'person_1',
                'target_entity_id': 'location_1',
                'relation_type': 'belongs_to',
                'confidence': 0.90
            },
            ...
        ]
        """
        pass
```

#### 步骤1.3：对现有数据运行抽取

```bash
# 对所有 chunks 运行实体抽取
python3 scripts/extract_entities_from_chunks.py

# 对所有实体运行关系抽取
python3 scripts/extract_relations_from_chunks.py
```

**预期结果**：
- entities 表：50-200条数据
- entity_relations 表：100-500条数据

---

### 阶段2：完整数据迁移到 Neo4j（必需）

#### 步骤2.1：迁移实体

```bash
python3 scripts/migrate_data_to_neo4j.py --only entities
```

**验证**：
```cypher
MATCH (n) RETURN labels(n) as type, count(n) as count
```

#### 步骤2.2：迁移关系

```bash
python3 scripts/migrate_data_to_neo4j.py --only relations
```

**验证**：
```cypher
MATCH ()-[r]->() RETURN type(r) as type, count(r) as count
```

#### 步骤2.3：迁移关键词关系

```bash
python3 scripts/migrate_data_to_neo4j.py --only keywords
```

---

### 阶段3：实现真实的 Neo4j 查询执行器（必需）

#### 步骤3.1：创建 Neo4j 执行器

**文件**：`capamesh/neo4j_executor.py`

**已创建**：基本框架已完成

**需要补充**：
- 连接池管理
- 查询缓存
- 错误重试
- 性能监控

#### 步骤3.2：集成到 ExecutionEngine

**文件**：`capamesh/execution_engine.py`

**修改**：
```python
# 替换 _mock_query
async def _execute_binding(self, binding_id: str, parameters: Dict) -> Any:
    binding = self.bindings[binding_id]
    channel_type = binding['channel_type']
    
    if channel_type == 'graph':
        # 真实的 Neo4j 查询
        query = binding['query_template']
        result = self.neo4j_executor.execute_cypher(query, parameters)
        return {'nodes': result}
    
    elif channel_type == 'sql':
        # 真实的 SQL 查询
        # ...
```

---

### 阶段4：实现推理引擎（必需）

#### 步骤4.1：创建推理引擎

**文件**：`capamesh/inference_engine.py`

**已创建**：基本框架（在文档中）

**需要实现**：
```python
class InferenceEngine:
    def execute_rule(self, rule, data):
        """
        执行推理规则
        
        例如：
        规则：如果提到"王大爷"和"山歌"在同一个chunk，
             则推理：王大爷 -[inherits]-> 布依族山歌
        """
        pass
```

#### 步骤4.2：集成到查询流程

**在 ExecutionEngine 中**：
```python
# 查询后执行推理
result = await self._execute_binding(binding_id, parameters)

# 应用推理规则
inferred_data = self.inference_engine.apply_rules(result)

# 合并结果
final_result = self._merge_results(result, inferred_data)
```

---

### 阶段5：端到端测试（必需）

#### 步骤5.1：测试语义查询

**测试用例**：
```bash
curl -X POST http://localhost:8000/api/query/ \
  -H "Content-Type: application/json" \
  -d '{
    "query": "查看布依族山歌的传承情况",
    "parameters": {}
  }'
```

**预期结果**：
```json
{
  "status": "success",
  "view_id": "cultural_heritage_health_view",
  "data": {
    "asset_info": {
      "name": "布依族山歌",
      "type": "intangible_cultural_heritage",
      "status": "endangered"
    },
    "inheritors": [
      {"name": "王大爷", "age": 75, "status": "active"}
    ],
    "risk_factors": [
      "传承人数量少于3人",
      "传承人平均年龄超过70岁"
    ]
  }
}
```

#### 步骤5.2：测试推理功能

**测试用例**：
```cypher
// 查询推理出的关系
MATCH (p:Person)-[r:inherits]->(c:CulturalAsset)
WHERE r.inferred = true
RETURN p.name, c.name, r.confidence
```

#### 步骤5.3：测试性能

**基准测试**：
- 单个视图查询：< 100ms
- 复杂聚合查询：< 500ms
- 推理执行：< 200ms

---

## 📅 完整实施时间表

### 第一阶段：数据采集（2天）
- [ ] 实现实体抽取服务（4小时）
- [ ] 实现关系抽取服务（4小时）
- [ ] 运行抽取并验证（2小时）
- [ ] 数据质量检查（2小时）

### 第二阶段：数据迁移（1天）
- [ ] 迁移实体到 Neo4j（2小时）
- [ ] 迁移关系到 Neo4j（2小时）
- [ ] 验证数据完整性（2小时）

### 第三阶段：查询执行（2天）
- [ ] 实现 Neo4j 执行器（4小时）
- [ ] 集成到 ExecutionEngine（3小时）
- [ ] 测试所有视图查询（3小时）

### 第四阶段：推理引擎（2天）
- [ ] 实现推理引擎（6小时）
- [ ] 集成到查询流程（2小时）
- [ ] 测试推理规则（2小时）

### 第五阶段：端到端测试（1天）
- [ ] 功能测试（3小时）
- [ ] 性能测试（2小时）
- [ ] 修复问题（3小时）

**总计：8天（64小时）**

---

## ✅ 验收标准（不简化）

### 数据层
- [ ] entities 表 >= 100条数据
- [ ] entity_relations 表 >= 200条数据
- [ ] Neo4j 节点 >= 100个
- [ ] Neo4j 关系 >= 200条

### 查询层
- [ ] 6个语义视图全部可用
- [ ] 图查询真实执行（非 mock）
- [ ] SQL 查询真实执行（非 mock）
- [ ] 查询性能达标（< 500ms）

### 推理层
- [ ] 10条推理规则全部实现
- [ ] 推理结果准确率 >= 80%
- [ ] 推理性能达标（< 200ms）

### 系统层
- [ ] Neo4j 稳定运行
- [ ] API 端到端测试通过
- [ ] 监控和日志完整
- [ ] 错误处理完善

---

## 🎯 下一步行动

### 立即执行（今天）

**选项1：实现实体抽取服务（推荐）**
- 这是整个系统的基础
- 有了实体才能有完整的图数据
- 预计4小时

**选项2：上传大量文件生成数据**
- 运行大规模测试
- 生成足够的 chunks
- 然后再抽取实体

**选项3：使用模拟数据快速验证**
- 手动创建一些测试实体和关系
- 先验证查询和推理流程
- 再回来补数据采集

---

**你想从哪个选项开始？**
