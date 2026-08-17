# FieldMind Agent & Skill 架构重构方案

## 🎯 目标

将空壳架构变成真实可用的多Agent协作系统，用于田野调查资料的深度分析。

---

## 📐 整体架构

```
文档上传
    ↓
基础处理层（已实现）
├── 文本提取（Whisper/OCR/解析器）
├── 关键词提取（jieba）
├── 向量化（BGE嵌入）
└── 动态发现（主题聚类/实体识别）
    ↓
多Agent分析层（待实现）★
├── Agent 1: 实体关系分析专员
├── Agent 2: 学术理论映射专员
├── Agent 3: 田野维度解构专员
├── Agent 4: 知识图谱构建专员
├── Agent 5: 报告生成专员
└── Agent 6: 协调专员
    ↓
Skill应用层（待实现）★
├── 学术理论Skill（费孝通、景军等）
├── 方法论Skill（多村落SOP）
├── 维度分析Skill（治理、生计、文化）
└── 业态分析Skill（商业可行性、市场研究）
    ↓
结果存储 & 前端展示
```

---

## 🤖 Agent 层设计（6个专业Agent）

### Agent 1: 实体关系分析专员 (EntityRelationAgent)

**职责**：从文本中识别人物、地点、组织、事件，并分析它们之间的关系

**输入**：
- 文档文本内容
- 动态发现引擎提取的实体列表

**处理逻辑**：
1. 基于动态发现的实体，进行深度关系抽取
2. 识别关系类型：亲属关系、权力关系、经济关系、地理关系等
3. 构建初步的关系网络

**输出**：
```json
{
  "entities": [
    {"name": "张书记", "type": "人物", "role": "村支书"},
    {"name": "李家村", "type": "地点", "category": "行政村"}
  ],
  "relations": [
    {
      "source": "张书记",
      "target": "李家村", 
      "relation": "管理",
      "confidence": 0.92
    }
  ]
}
```

**技术实现**：
- 使用LLM进行关系抽取（基于prompt工程）
- 利用已有的动态发现结果，避免重复计算
- 支持中文社会学领域的特殊关系类型

---

### Agent 2: 学术理论映射专员 (AcademicTheoryAgent)

**职责**：将田野资料映射到学术理论框架（费孝通、景军等）

**输入**：
- 文档文本内容
- 实体关系分析结果
- 启用的学术理论Skill列表

**处理逻辑**：
1. 根据启用的Skill，加载对应的理论框架
2. 分析文本中哪些段落体现了理论概念
3. 提取理论维度的证据片段

**输出**：
```json
{
  "theory": "费孝通·乡土中国",
  "dimensions": [
    {
      "concept": "差序格局",
      "matched": true,
      "evidence": [
        "村里办事都是找熟人，关系近的先办..."
      ],
      "confidence": 0.88
    }
  ]
}
```

**技术实现**：
- 加载Skill定义的理论维度
- 使用语义相似度 + LLM判断匹配
- 返回可解释的证据链

---

### Agent 3: 田野维度解构专员 (FieldDimensionAgent)

**职责**：按照田野调查的标准维度解构内容（治理、生计、文化、生态等）

**输入**：
- 文档文本内容
- 启用的维度分析Skill列表

**处理逻辑**：
1. 按维度切分文本内容
2. 识别每个维度的关键信息
3. 提取结构化数据

**输出**：
```json
{
  "dimensions": {
    "governance": {
      "power_structure": ["村委会", "党支部"],
      "decision_making": ["村民大会", "投票"],
      "key_figures": ["张书记", "李村长"]
    },
    "livelihood": {
      "income_sources": ["务工", "种植"],
      "main_crops": ["水稻", "玉米"]
    }
  }
}
```

**技术实现**：
- 调用community_governance、livelihood_ecology等Skill
- 从简单关键词匹配升级为语义理解
- 支持自定义维度扩展

---

### Agent 4: 知识图谱构建专员 (KnowledgeGraphAgent)

**职责**：整合前面Agent的结果，构建结构化知识图谱

**输入**：
- 实体关系分析结果
- 学术理论映射结果
- 田野维度解构结果

**处理逻辑**：
1. 合并去重实体和关系
2. 添加理论标签和维度标签
3. 构建Neo4j兼容的图谱结构

**输出**：
```json
{
  "nodes": [...],
  "edges": [...],
  "metadata": {
    "theory_tags": ["差序格局", "礼治秩序"],
    "dimension_tags": ["社区治理", "权力结构"]
  }
}
```

**技术实现**：
- 标准化实体ID（消歧）
- 支持多层关系（实体-理论-维度）
- 输出可导入Neo4j的格式

---

### Agent 5: 报告生成专员 (ReportGenerationAgent)

**职责**：基于分析结果生成可读的田野调查报告

**输入**：
- 知识图谱
- 所有前序Agent的分析结果

**处理逻辑**：
1. 提取核心发现
2. 按学术写作规范组织内容
3. 生成结构化报告

**输出**：
```markdown
# 李家村田野调查报告

## 一、社区治理结构
本村的权力结构呈现典型的"双轨制"特征...

## 二、生计模式分析  
主要收入来源为外出务工（占65%）...

## 三、理论分析
从费孝通"差序格局"理论来看...
```

**技术实现**：
- 使用LLM生成连贯叙述
- 支持多种报告模板（学术论文、调研简报、政策建议）
- 保留数据来源的引用链接

---

### Agent 6: 协调专员 (CoordinatorAgent)

**职责**：管理整个多Agent流程，决定调用哪些Agent和Skill

**输入**：
- 项目配置（启用的Skill列表）
- 文档元数据

**处理逻辑**：
1. 根据文档类型和项目设置，决定Agent执行顺序
2. 处理Agent之间的数据传递
3. 监控执行状态和错误处理

**输出**：
- 完整的分析pipeline结果
- 执行日志和性能指标

---

## 🛠️ Skill 层设计（独立可插拔）

### Skill 结构规范

每个Skill是一个独立的Python模块，包含：

```python
# skills/xiangtu_china.py

SKILL_META = {
    "id": "xiangtu_china",
    "name": "费孝通·乡土中国",
    "version": "1.0.0",
    "category": "academic_theory",
    "author": "FieldMind Team"
}

THEORY_DIMENSIONS = {
    "differential_mode": {
        "name": "差序格局",
        "description": "以己为中心的同心圆式社会关系",
        "keywords": ["关系", "熟人", "圈子", "远近亲疏"],
        "semantic_concepts": [
            "人际关系的亲疏远近",
            "以自我为中心的社会网络",
            "差别对待的行为模式"
        ]
    },
    # ... 更多维度
}

def analyze(text: str, entities: list, context: dict) -> dict:
    """
    分析文本是否体现该理论
    
    Args:
        text: 文档文本
        entities: 实体列表（从Agent 1获取）
        context: 上下文信息
    
    Returns:
        匹配结果和证据
    """
    results = {}
    
    for dim_id, dim_info in THEORY_DIMENSIONS.items():
        # 1. 关键词匹配（基础）
        keyword_matches = [kw for kw in dim_info["keywords"] if kw in text]
        
        # 2. 语义相似度匹配（进阶）
        semantic_score = calculate_semantic_similarity(
            text, 
            dim_info["semantic_concepts"]
        )
        
        # 3. 提取证据片段
        evidence = extract_evidence_sentences(text, dim_info)
        
        results[dim_id] = {
            "matched": len(keyword_matches) > 0 or semantic_score > 0.7,
            "confidence": max(len(keyword_matches) * 0.1, semantic_score),
            "evidence": evidence,
            "keyword_matches": keyword_matches
        }
    
    return results
```

---

### 待实现的6个Skill

#### 1. xiangtu_china.py - 费孝通《乡土中国》
- **维度**：差序格局、礼治秩序、熟人社会、长老统治、男女有别、现代化冲击
- **适用场景**：农村社会结构分析

#### 2. manchu_culture.py - 项链《消逝的满族》
- **维度**：萨满教传统、满族身份认同、文化传承、现代性冲突
- **适用场景**：少数民族文化研究

#### 3. sacred_memory.py - 景军《神圣记忆》
- **维度**：集体记忆、仪式实践、身份建构、历史叙事
- **适用场景**：记忆与认同研究

#### 4. multi_village_sop.py - 多村落调查SOP
- **维度**：基础调研、文化资产、利益相关方、业态评估、风险识别、行动规划
- **适用场景**：乡村振兴项目

#### 5. business_feasibility.py - 商业可行性分析
- **维度**：市场需求、资源禀赋、运营能力、财务模型、风险评估
- **适用场景**：乡村产业项目

#### 6. literature_market_research.py - 文献市场研究
- **维度**：行业趋势、竞品分析、政策环境、成功案例
- **适用场景**：案头研究阶段

---

## 🔄 执行流程设计

### 完整Pipeline

```python
# 在 background_tasks.py 中集成

def process_document_with_agents(document_id: int, project_id: int):
    """带Agent分析的完整文档处理流程"""
    
    # 第1-4步：基础处理（已实现）
    # - 文本提取
    # - 关键词提取
    # - 向量化
    # - 动态发现
    
    # 第5步：启动多Agent分析（新增）
    if should_enable_agents(project_id):
        agent_coordinator = AgentCoordinator(project_id)
        
        # 获取项目启用的Skill配置
        enabled_skills = get_project_skills(project_id)
        
        # 执行Agent流程
        agent_results = agent_coordinator.run(
            document_id=document_id,
            text_content=content,
            entities=dynamic_discovery_entities,
            enabled_skills=enabled_skills
        )
        
        # 保存Agent分析结果
        save_agent_results(document_id, agent_results)
```

### Agent执行顺序

```
1. EntityRelationAgent（必执行）
       ↓
2. AcademicTheoryAgent（如果启用了学术Skill）
       ↓
3. FieldDimensionAgent（如果启用了维度Skill）
       ↓
4. KnowledgeGraphAgent（整合前面结果）
       ↓
5. ReportGenerationAgent（可选，按需生成报告）
```

---

## 📊 数据存储设计

### 扩展ProjectDocument表

```python
# models/project.py 新增字段

class ProjectDocument(Base):
    # ... 现有字段
    
    # Agent分析结果
    agent_analysis = Column(JSON, nullable=True)
    # 结构：
    # {
    #   "entity_relations": {...},      # Agent 1结果
    #   "academic_mapping": {...},      # Agent 2结果  
    #   "field_dimensions": {...},      # Agent 3结果
    #   "knowledge_graph": {...},       # Agent 4结果
    #   "generated_report": "..."       # Agent 5结果
    # }
    
    # Skill应用记录
    applied_skills = Column(JSON, nullable=True)
    # 结构：
    # {
    #   "xiangtu_china": {"matched": true, "confidence": 0.88, ...},
    #   "multi_village_sop": {"matched": true, ...}
    # }
```

---

## 🎯 实施计划（按优先级）

### Phase 1: 基础设施（第1-2天）

- [ ] 创建Agent基类和协调器框架
- [ ] 实现Skill加载和管理机制
- [ ] 扩展数据库schema

### Phase 2: 核心Agent实现（第3-7天）

- [ ] Agent 1: EntityRelationAgent（关系抽取）
- [ ] Agent 3: FieldDimensionAgent（维度解构）  
- [ ] Agent 4: KnowledgeGraphAgent（图谱构建）
- [ ] Agent 6: CoordinatorAgent（协调器）

### Phase 3: Skill实现（第8-12天）

- [ ] community_governance.py（升级现有）
- [ ] livelihood_ecology.py（升级现有）
- [ ] xiangtu_china.py（新建）
- [ ] multi_village_sop.py（新建）
- [ ] business_feasibility.py（新建）

### Phase 4: 高级功能（第13-15天）

- [ ] Agent 2: AcademicTheoryAgent（理论映射）
- [ ] Agent 5: ReportGenerationAgent（报告生成）
- [ ] manchu_culture.py（新建）
- [ ] sacred_memory.py（新建）

### Phase 5: 集成和测试（第16-20天）

- [ ] 集成到background_tasks.py
- [ ] 前端展示组件
- [ ] 端到端测试
- [ ] 性能优化

---

## 🔧 技术选型

### LLM调用
- 使用现有的Ollama配置（qwen2.5:7b）
- 支持OpenAI API兼容接口
- 实现prompt模板管理

### 向量检索
- 复用现有BGE嵌入模型
- 用于语义相似度计算

### 知识图谱
- 暂时存储为JSON（轻量级）
- 预留Neo4j导出接口（未来扩展）

---

## ✅ 质量标准

每个Agent和Skill必须满足：

1. **独立性**：可单独测试和运行
2. **可观测性**：输出详细日志和中间结果
3. **可配置性**：支持参数调整和开关
4. **可解释性**：返回证据和置信度
5. **性能指标**：处理速度 < 10秒/文档

---

## 📝 文档规范

每个实现需要配套：
- 代码注释（中文）
- 单元测试
- 使用示例
- 性能基准

---

**最后更新时间**：2026-08-11
**状态**：架构设计完成，等待逐步实施
