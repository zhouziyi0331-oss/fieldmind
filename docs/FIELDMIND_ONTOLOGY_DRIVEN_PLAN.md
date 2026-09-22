# FieldMind 本体驱动数据治理 - 完整执行计划

生成时间：2026-08-21 14:00

---

## 📋 总体目标

构建一个**本体驱动的AI智能体数据中间层**，使 FieldMind 能够：
1. 语义化理解业务数据（而非仅向量检索）
2. 支持"规则+事实+实时数据"的联合查询
3. 具备可扩展的多源绑定能力

**与当前系统的区别**：
- 当前：chunks表 → 向量检索 → 关键词匹配
- 目标：本体模型 → 语义视图 → 多源数据绑定 → 统一查询接口

---

## 🎯 开发阶段划分（3个阶段，每个阶段独立验收）

### P0 阶段：本体模型（Schema层）—— 定义"有什么"

**时间估算**：3-4天

**核心产出**：
1. `ontology.json` - 完整的本体模型定义
2. 单元测试 - 验证本体模型的完整性
3. 文档 - 本体模型设计说明

**具体包含**：

#### 1. 实体类型清单（Entities）

基于 FieldMind 的业务领域，定义以下实体类型：

```yaml
核心实体类型（8个）：

1. Person（人物）
   - 属性：person_id, name, age, gender, role（村民/传承人/村干部/外来者）
   - 状态：active/inactive/deceased
   
2. Location（地点）
   - 属性：location_id, name, type（村/寨/田地/河流/建筑）, coordinates
   - 状态：existing/demolished/renovated
   
3. CulturalAsset（文化资产）
   - 属性：asset_id, name, type（山歌/蜡染/节庆/建筑/手工艺）, status
   - 状态：active/endangered/lost/protected
   
4. Event（事件）
   - 属性：event_id, name, type（节庆/会议/签约/选举）, date
   - 状态：planned/ongoing/completed/cancelled
   
5. Policy（政策）
   - 属性：policy_id, name, type（文件/规定/补贴）, effective_date
   - 状态：draft/effective/expired/revoked
   
6. Document（文档）
   - 属性：document_id, title, type（音频/视频/图片/文本）, upload_date
   - 状态：uploaded/processing/completed/archived
   
7. Chunk（文本块）
   - 属性：chunk_id, text, document_id, chunk_index
   - 状态：raw/processed/annotated/validated
   
8. Organization（组织）
   - 属性：org_id, name, type（政府/企业/NGO/合作社）
   - 状态：active/inactive/dissolved
```

#### 2. 关系类型及基数（Relations）

```yaml
核心关系类型（12个）：

1. belongs_to（属于）
   - Person → Location（一对多）
   - 示例：张三 属于 大坪村
   
2. lives_in（居住在）
   - Person → Location（一对一）
   - 示例：王大爷 居住在 纳孔寨
   
3. inherits（传承）
   - Person → CulturalAsset（多对多）
   - 示例：李奶奶 传承 蜡染技艺
   
4. participates_in（参与）
   - Person → Event（多对多）
   - 示例：村民 参与 六月六节庆
   
5. occurs_at（发生在）
   - Event → Location（一对一）
   - 示例：六月六 发生在 村广场
   
6. related_to（关联到）
   - CulturalAsset → Policy（多对多）
   - 示例：布依族山歌 关联到 非遗保护政策
   
7. mentioned_in（提及于）
   - Entity → Chunk（多对多）
   - 示例：王大爷 提及于 chunk_123
   
8. extracted_from（提取自）
   - Chunk → Document（多对一）
   - 示例：chunk_123 提取自 访谈录音.mp3
   
9. knows（认识）
   - Person → Person（多对多）
   - 示例：张三 认识 李四
   
10. manages（管理）
    - Person → Organization（一对多）
    - 示例：村长 管理 村委会
    
11. located_in（位于）
    - CulturalAsset → Location（一对一）
    - 示例：古寨门 位于 村口
    
12. implements（实施）
    - Organization → Policy（多对多）
    - 示例：村委会 实施 扶贫政策
```

#### 3. 状态机定义（State Machines）

```yaml
CulturalAsset 状态机：

状态：
  - active: 正在传承/使用
  - endangered: 濒危（传承人少/年轻人不学）
  - lost: 已失传
  - protected: 受保护（列入非遗名录）

转换规则：
  - active → endangered: 当 传承人数量 < 3 或 传承人平均年龄 > 60
  - endangered → protected: 当 列入非遗名录
  - endangered → lost: 当 传承人数量 = 0
  - protected → active: 当 新增传承人 > 5 且 平均年龄 < 40
  
触发条件：
  - 基于实体关系：Person -[inherits]-> CulturalAsset
  - 基于时间：每季度评估一次
```

```yaml
Document 状态机：

状态：
  - uploaded: 刚上传
  - processing: 处理中（转写/OCR/切分）
  - annotated: 已标注（维度/指标）
  - validated: 已验证（人工确认）
  - archived: 已归档

转换规则：
  - uploaded → processing: 自动触发
  - processing → annotated: 当所有chunks都有维度标注
  - annotated → validated: 人工验证通过
  - validated → archived: 超过保留期限
```

#### 4. 推理规则（Inference Rules）

```yaml
规则1：识别文化传承关系
  条件：
    - Person.age > 50
    - 同一Chunk中提到 Person 和 CulturalAsset
    - Chunk包含关键词：["传承", "教", "学", "手艺", "祖传"]
  推理：
    - 创建关系：Person -[inherits]-> CulturalAsset
    - 置信度：0.8
    
规则2：识别濒危文化资产
  条件：
    - CulturalAsset 的传承人数量 < 3
    - 或 传承人平均年龄 > 60
    - 或 Chunk中出现关键词：["失传", "不愿意学", "没人学"]
  推理：
    - 更新状态：CulturalAsset.status = endangered
    - 生成警报：Alert(type="endangered", entity=CulturalAsset)
    
规则3：识别政策关联
  条件：
    - Policy 和 CulturalAsset 出现在同一Chunk
    - 或 Policy.type = "非遗保护" 且 CulturalAsset.type = "非遗"
  推理：
    - 创建关系：CulturalAsset -[related_to]-> Policy
    - 置信度：0.9
    
规则4：识别人物关系
  条件：
    - 两个Person出现在同一Chunk
    - Chunk包含关系关键词：["认识", "朋友", "亲戚", "邻居"]
  推理：
    - 创建关系：Person -[knows]-> Person
    - 置信度：0.7
    
规则5：时间区间推理
  条件：
    - Chunk包含时间关键词
  推理：
    - 提取时间区间并关联到Entity
    - 示例："土改时期" → time_period = "1950-1952"
```

#### 5. 验收标准

**验收方式1：JSON Schema 验证**
```json
{
  "ontology_version": "1.0",
  "entities": [...],  // 8个实体类型
  "relations": [...], // 12个关系类型
  "state_machines": [...], // 至少2个状态机
  "inference_rules": [...] // 至少5个推理规则
}
```

**验收方式2：单元测试**
```python
def test_entity_types():
    # 验证8个实体类型都定义了
    assert len(ontology['entities']) == 8
    
def test_relation_cardinality():
    # 验证关系基数正确
    belongs_to = find_relation('belongs_to')
    assert belongs_to['cardinality'] == 'one_to_many'
    
def test_state_transition():
    # 验证状态转换规则
    asset = CulturalAsset(status='active')
    asset.apply_rule('endangered_check', inheritors_count=2)
    assert asset.status == 'endangered'
```

**验收方式3：文档完整性**
- [ ] 每个实体类型有清晰的业务描述
- [ ] 每个关系类型有具体示例
- [ ] 每个状态机有状态转换图
- [ ] 每个推理规则有触发条件说明

---

### P1 阶段：语义视图（View）+ 数据绑定（Binding）

**时间估算**：4-5天

**核心产出**：
1. 视图定义文件 `views/*.json`
2. 绑定配置文件 `bindings/*.json`
3. 视图测试用例

**具体包含**：

#### 1. 语义视图设计（至少6个核心视图）

```yaml
视图1：文化传承健康视图（cultural_heritage_health_view）
  intent: 查看某个文化资产的传承状况
  input:
    - cultural_asset_id: string
  output:
    - asset_name: string
    - status: enum（active/endangered/lost/protected）
    - inheritor_count: int
    - inheritor_avg_age: float
    - latest_activities: list[Event]
    - risk_factors: list[string]
  data_binding:
    - source1: graph_query（查询 CulturalAsset 及其关系）
    - source2: chunks_table（全文检索相关段落）
    - source3: vector_db（语义相似的记录）
    
视图2：人物社会网络视图（person_network_view）
  intent: 查看某个人物的社会关系网络
  input:
    - person_id: string
    - depth: int（关系深度，默认2）
  output:
    - person_info: dict
    - direct_connections: list[Person]
    - indirect_connections: list[Person]
    - communities: list[string]
    - influence_score: float
  data_binding:
    - source1: graph_query（递归查询 knows 关系）
    - source2: chunks_table（提取共同出现的段落）
    
视图3：地点文化资产视图（location_assets_view）
  intent: 查看某个地点的所有文化资产
  input:
    - location_id: string
  output:
    - location_info: dict
    - cultural_assets: list[CulturalAsset]
    - historical_events: list[Event]
    - related_policies: list[Policy]
  data_binding:
    - source1: graph_query（查询 located_in 关系）
    - source2: chunks_table（按地点筛选）
    
视图4：政策影响视图（policy_impact_view）
  intent: 查看某个政策的影响范围
  input:
    - policy_id: string
  output:
    - policy_info: dict
    - affected_locations: list[Location]
    - affected_persons: list[Person]
    - implementation_status: dict
    - related_cultural_assets: list[CulturalAsset]
  data_binding:
    - source1: graph_query（查询 implements, related_to 关系）
    - source2: chunks_table（政策相关段落）
    
视图5：时间轴视图（timeline_view）
  intent: 查看某个时间区间的所有事件
  input:
    - start_date: date
    - end_date: date
    - entity_type: string（可选）
  output:
    - events: list[Event]（按时间排序）
    - cultural_changes: list[dict]
    - policy_changes: list[dict]
  data_binding:
    - source1: chunks_table（按 time_period 筛选）
    - source2: graph_query（查询 Event 实体）
    
视图6：维度分析视图（dimension_analysis_view）
  intent: 按业务维度统计分析
  input:
    - dimension: enum（衣食住行/民俗/非遗/政策/历史）
    - aggregation: enum（count/percentage/trend）
  output:
    - dimension_stats: dict
    - top_entities: list
    - coverage_rate: float
    - time_trend: list[dict]
  data_binding:
    - source1: chunks_table（按 dimension_category 聚合）
    - source2: graph_query（统计相关实体）
```

#### 2. 数据绑定配置

```yaml
绑定类型（4种）：

1. Graph Query Binding
   channel_type: graph
   protocol: cypher
   resource: neo4j://localhost:7687
   auth: {username, password}
   timeout: 5000
   
2. SQL Binding
   channel_type: sql
   protocol: sqlite
   resource: sqlite:///data/fieldmind.db
   query_template: "SELECT * FROM chunks WHERE dimension_category = :dimension"
   
3. Vector Search Binding
   channel_type: vector
   protocol: chromadb
   resource: http://localhost:8000
   embedding_model: bge-m3
   top_k: 10
   
4. Full-text Search Binding
   channel_type: fulltext
   protocol: fts5
   resource: sqlite:///data/fieldmind.db
   query_template: "SELECT * FROM chunks WHERE text MATCH :query"
```

#### 3. 验收标准

**验收方式1：视图定义完整性**
```bash
# 检查视图文件数量
ls views/*.json | wc -l
# 预期：>=6

# 验证视图JSON格式
python -m json.tool views/cultural_heritage_health_view.json
```

**验收方式2：绑定配置测试**
```python
def test_graph_binding():
    binding = load_binding('graph_query_binding.json')
    result = binding.execute("MATCH (n:Person) RETURN n LIMIT 1")
    assert result is not None
    
def test_sql_binding():
    binding = load_binding('sql_binding.json')
    result = binding.execute("SELECT COUNT(*) FROM chunks")
    assert result[0][0] > 0
```

**验收方式3：视图查询测试**
```python
def test_cultural_heritage_view():
    view = load_view('cultural_heritage_health_view')
    result = view.query(cultural_asset_id='山歌')
    
    assert 'asset_name' in result
    assert 'status' in result
    assert 'inheritor_count' in result
```

---

### P2 阶段：CapaMesh执行层 + 治理层

**时间估算**：5-6天

**核心产出**：
1. 查询解析器
2. 执行引擎
3. 治理层（路由/缓存/降级）
4. 统一查询API

**具体包含**：

#### 1. 查询解析器（Query Parser）

```python
功能：
- 接收自然语言或结构化查询
- 识别意图（intent）
- 匹配最合适的视图
- 提取参数

示例：
输入："查看布依族山歌的传承情况"
输出：
{
  "intent": "cultural_heritage_health",
  "view_id": "cultural_heritage_health_view",
  "parameters": {
    "cultural_asset_id": "布依族山歌"
  }
}
```

#### 2. 执行引擎（Execution Engine）

```python
功能：
- 加载视图定义
- 根据绑定配置调用数据源
- 并发查询多个数据源
- 聚合结果
- 返回统一格式

执行流程：
1. 解析视图定义 → 确定需要哪些数据源
2. 并发执行所有绑定 → asyncio
3. 收集结果 → 按视图output格式组装
4. 添加evidence → 记录数据来源
5. 返回 → {data: {...}, evidence: [...], metadata: {...}}
```

#### 3. 治理层（Governance Layer）

```python
功能：
- 路由：根据负载选择数据源副本
- 缓存：热查询结果缓存（Redis）
- 降级：数据源不可用时的fallback
- 监控：记录查询耗时、成功率
- 限流：防止恶意查询

配置示例：
{
  "cache": {
    "enabled": true,
    "ttl": 300,
    "backend": "redis://localhost:6379"
  },
  "fallback": {
    "graph_unavailable": "use_sql_backup"
  },
  "rate_limit": {
    "requests_per_minute": 100
  }
}
```

#### 4. 统一查询API

```python
# API 设计

POST /api/query
Request:
{
  "query": "查看布依族山歌的传承情况",  // 自然语言
  "intent": "cultural_heritage_health",  // 或明确指定意图
  "parameters": {
    "cultural_asset_id": "布依族山歌"
  }
}

Response:
{
  "status": "success",
  "data": {
    "asset_name": "布依族山歌",
    "status": "endangered",
    "inheritor_count": 3,
    "inheritor_avg_age": 68.5,
    "latest_activities": [...],
    "risk_factors": ["年轻人不愿学", "传承人高龄"]
  },
  "evidence": [
    {
      "source": "graph_query",
      "query": "MATCH (a:CulturalAsset {name: '布依族山歌'})-[r:inherits]-(p:Person) RETURN p",
      "result_count": 3
    },
    {
      "source": "chunks_table",
      "matched_chunks": ["chunk_123", "chunk_456"],
      "keywords": ["山歌", "传承", "失传"]
    }
  ],
  "metadata": {
    "query_time": 156,
    "sources_used": 2,
    "cache_hit": false
  }
}
```

#### 5. 验收标准

**验收方式1：API功能测试**
```bash
# 测试意图识别
curl -X POST http://localhost:8000/api/query \
  -d '{"query": "布依族山歌有多少传承人"}' \
  -H "Content-Type: application/json"

# 预期：返回正确的视图结果
```

**验收方式2：多源并发测试**
```python
def test_concurrent_queries():
    # 同时查询graph和sql
    result = query_engine.execute(
        view='cultural_heritage_health_view',
        params={'cultural_asset_id': '布依族山歌'}
    )
    
    # 验证两个数据源都返回了结果
    assert len(result['evidence']) >= 2
    assert any(e['source'] == 'graph_query' for e in result['evidence'])
    assert any(e['source'] == 'chunks_table' for e in result['evidence'])
```

**验收方式3：性能测试**
```python
def test_performance():
    start = time.time()
    result = query_engine.execute(...)
    elapsed = time.time() - start
    
    # 单次查询应在1秒内完成
    assert elapsed < 1.0
```

---

## 🔍 贯穿全流程的质量保证

### 1. 每阶段的扫描检查点

**P0阶段扫描**：
- [ ] 实体类型是否覆盖核心业务概念
- [ ] 关系类型的基数定义是否合理
- [ ] 状态机是否有死锁状态
- [ ] 推理规则的触发条件是否完备

**P1阶段扫描**：
- [ ] 视图的input/output是否与本体对齐
- [ ] 绑定配置的资源地址是否可达
- [ ] 视图之间是否有重复定义
- [ ] 数据源不可用时是否有降级方案

**P2阶段扫描**：
- [ ] 并发查询是否有竞态条件
- [ ] 错误处理是否完善
- [ ] 日志记录是否充分
- [ ] API响应格式是否统一

### 2. 硬性检查清单

```python
# 每个阶段完成后运行的检查脚本

def check_ontology_completeness():
    """P0阶段检查"""
    ontology = load_ontology()
    
    # 1. 实体类型数量检查
    assert len(ontology['entities']) >= 8
    
    # 2. 每个实体必须有唯一ID字段
    for entity in ontology['entities']:
        assert entity['id_field'] is not None
        
    # 3. 关系类型必须有source和target
    for relation in ontology['relations']:
        assert 'source' in relation
        assert 'target' in relation
        
    # 4. 状态机必须有初始状态
    for sm in ontology['state_machines']:
        assert sm['initial_state'] is not None

def check_view_binding_alignment():
    """P1阶段检查"""
    views = load_all_views()
    bindings = load_all_bindings()
    
    # 1. 每个视图都有对应的绑定
    for view in views:
        assert view['view_id'] in bindings
        
    # 2. 视图的output字段与本体实体属性对齐
    for view in views:
        for field in view['output']:
            assert is_valid_ontology_property(field)

def check_api_consistency():
    """P2阶段检查"""
    # 1. 测试所有API端点
    endpoints = ['/api/query', '/api/entities', '/api/relations']
    for ep in endpoints:
        response = requests.get(f'http://localhost:8000{ep}')
        assert response.status_code in [200, 404]
        
    # 2. 测试错误处理
    response = requests.post('/api/query', json={'invalid': 'data'})
    assert response.status_code == 400
    assert 'error' in response.json()
```

---

## 📅 时间线与里程碑

| 天数 | 阶段 | 任务 | 验收标准 |
|------|------|------|---------|
| Day 1-2 | P0 | 设计实体类型和关系 | ontology.json 完成 |
| Day 3 | P0 | 定义状态机和推理规则 | 状态机测试通过 |
| Day 4 | P0 | 编写单元测试和文档 | 所有测试通过 |
| Day 5-6 | P1 | 设计6个核心视图 | views/*.json 完成 |
| Day 7-8 | P1 | 配置数据绑定 | bindings/*.json 完成 |
| Day 9 | P1 | 测试视图查询 | 视图测试通过 |
| Day 10-11 | P2 | 实现查询解析器 | 意图识别测试通过 |
| Day 12-13 | P2 | 实现执行引擎 | 多源查询测试通过 |
| Day 14 | P2 | 实现治理层 | 缓存/降级测试通过 |
| Day 15 | P2 | API集成和文档 | API文档完成 |

**总计**：15个工作日（3周）

---

## 🎯 成功标准

### 最终验收的3个关键指标

**1. 语义查询成功率 >= 90%**
```python
# 测试100个自然语言查询
queries = [
    "布依族山歌有多少传承人",
    "大坪村有哪些文化资产",
    "土改时期发生了什么事件",
    ...
]

success_count = 0
for query in queries:
    result = api.query(query)
    if result['status'] == 'success':
        success_count += 1

assert success_count / len(queries) >= 0.9
```

**2. 查询响应时间 < 1秒**
```python
# 测试20次查询的平均响应时间
times = []
for _ in range(20):
    start = time.time()
    api.query("布依族山歌有多少传承人")
    times.append(time.time() - start)

assert sum(times) / len(times) < 1.0
```

**3. 数据源覆盖率 = 100%**
```python
# 验证所有配置的数据源都能正常访问
bindings = load_all_bindings()
for binding in bindings:
    assert test_connection(binding) == True
```

---

## 🚨 风险与应对

| 风险 | 概率 | 影响 | 应对措施 |
|------|------|------|---------|
| 本体模型设计不完整 | 高 | 高 | 先做业务调研，列出所有核心概念 |
| 数据源性能瓶颈 | 中 | 高 | 增加缓存层，实现查询优化 |
| 自然语言理解不准确 | 高 | 中 | 先支持结构化查询，NLU作为增强 |
| 多源数据一致性问题 | 中 | 中 | 每个查询返回数据来源和时间戳 |
| 开发周期超预期 | 中 | 中 | 按阶段交付，每阶段独立可用 |

---

## 📝 交付物清单

### P0 阶段交付物

- [ ] `ontology/schema.json` - 本体模型定义
- [ ] `ontology/entities/` - 每个实体类型的详细定义
- [ ] `ontology/relations/` - 每个关系类型的详细定义
- [ ] `ontology/state_machines/` - 状态机定义
- [ ] `ontology/inference_rules/` - 推理规则定义
- [ ] `tests/test_ontology.py` - 单元测试
- [ ] `docs/ontology_design.md` - 设计文档

### P1 阶段交付物

- [ ] `views/*.json` - 6个视图定义文件
- [ ] `bindings/*.json` - 数据绑定配置文件
- [ ] `tests/test_views.py` - 视图测试
- [ ] `tests/test_bindings.py` - 绑定测试
- [ ] `docs/views_guide.md` - 视图使用指南

### P2 阶段交付物

- [ ] `src/query_parser.py` - 查询解析器
- [ ] `src/execution_engine.py` - 执行引擎
- [ ] `src/governance_layer.py` - 治理层
- [ ] `src/api/query_api.py` - 统一查询API
- [ ] `tests/test_integration.py` - 集成测试
- [ ] `docs/api_reference.md` - API文档
- [ ] `docs/deployment_guide.md` - 部署指南

---

## 🎓 学习资源

为了高质量完成这个计划，建议参考：

1. **本体设计**：
   - Protégé 本体编辑器教程
   - OWL (Web Ontology Language) 规范

2. **语义查询**：
   - SPARQL 查询语言
   - Cypher 图查询语言

3. **数据绑定**：
   - GraphQL DataLoader 模式
   - Apache Calcite（多源查询优化）

---

## ✅ 确认清单（请逐项确认）

在开始执行前，请确认：

- [ ] 理解了本体模型的核心概念（实体/关系/状态/规则）
- [ ] 认可3个阶段的划分和优先级
- [ ] 明确了每个阶段的验收标准
- [ ] 同意15天的时间估算
- [ ] 理解了最终成功标准（3个关键指标）
- [ ] 知道如何验证每个阶段的交付物
- [ ] 准备好提供业务领域知识（用于本体设计）

---

**请仔细审阅以上计划，如有任何疑问或需要调整的地方，请告诉我。**

**确认无误后，我将开始执行 P0 阶段：本体模型设计。**
