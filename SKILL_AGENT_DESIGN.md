# Skill与Agent深度架构设计

## 🎯 设计目标

1. **深度分析** - 使用向量语义理解，而非简单关键词匹配
2. **独立运行** - Skill和Agent各自独立，可单独测试和使用
3. **相互关联** - 数据可以在Skill和Agent之间流动
4. **真实可用** - 符合田野调查研究者的实际工作流程
5. **可扩展** - 方便添加新的理论框架和分析维度

---

## 🏗️ 整体架构

```
用户上传文档
    ↓
[EntityRelationAgent] 提取实体和关系
    ↓
[FieldDimensionAgent] 调用多个Skill进行维度分析
    ├─ Skill: community_governance (社区治理)
    ├─ Skill: livelihood_ecology (生计生态)
    └─ Skill: xiangtu_china (乡土中国理论)
    ↓
[AcademicTheoryAgent] 应用学术理论框架深度解读
    ↓
[KnowledgeGraphAgent] 构建知识图谱
    ↓
[ReportGenerationAgent] 生成分析报告
```

---

## 📦 Skill架构设计

### Skill的本质

**Skill = 分析框架 + 语义模型 + 维度定义**

每个Skill代表一种学术理论或专业分析框架：
- `xiangtu_china.py` - 费孝通《乡土中国》理论框架
- `sacred_memory.py` - 景军《神圣记忆》理论框架
- `community_governance.py` - 社区治理专业维度
- `livelihood_ecology.py` - 生计生态专业维度

### Skill的核心能力

```python
class SkillBase:
    """所有Skill的基类"""
    
    1. 维度定义 (dimensions)
       - 每个维度有理论描述、示例语句、语义向量
    
    2. 语义检索 (semantic_retrieve)
       - 用BGE向量模型找到语义相关的句子
       - 而非简单关键词匹配
    
    3. 深度分析 (deep_analyze)
       - 对检索到的内容进行深度解读
       - 可选用LLM增强
    
    4. 实体关联 (entity_linking)
       - 将分析结果与实体关系关联
       - 形成结构化知识
    
    5. 置信度评估 (confidence_score)
       - 评估分析结果的可信度
```

### Skill的输入输出

**输入**（标准化）：
```python
{
    'text_content': str,           # 待分析文本
    'entities': List[Dict],        # 实体列表（来自EntityRelationAgent）
    'relations': List[Dict],       # 关系列表
    'context': Dict                # 上下文信息
}
```

**输出**（标准化）：
```python
{
    'skill_id': 'xiangtu_china',
    'skill_name': '乡土中国理论分析',
    'dimensions': {
        'chaxu_geju': {                    # 差序格局
            'name': '差序格局',
            'theory': '费孝通理论...',
            'matched_sentences': [...],     # 语义相关的句子
            'analysis': '...',              # 深度分析
            'confidence': 0.85,
            'related_entities': [...],      # 相关实体
            'evidence': [...]               # 证据链
        }
    },
    'summary': {...},
    'confidence': 0.78
}
```

---

## 🤖 Agent架构设计

### Agent的职责划分

#### 1. EntityRelationAgent（基础层）
**职责**：提取结构化信息
- 识别实体（人物、地点、组织、事件）
- 抽取关系（权力、亲属、地理、经济、社会）
- 为后续分析提供结构化基础

**独立性**：完全独立，不依赖其他Agent
**输出**：实体列表、关系列表、实体类型字典

#### 2. FieldDimensionAgent（分析层）
**职责**：多维度专业分析
- 加载项目启用的Skill
- 调用各Skill进行维度分析
- 整合多个Skill的分析结果

**独立性**：可独立运行，但能利用EntityRelationAgent的输出增强效果
**输出**：各维度分析结果、Skill统计、Top维度

#### 3. AcademicTheoryAgent（理论层）
**职责**：学术理论深度解读
- 应用学术理论框架（费孝通、景军等）
- 从理论视角重新解读田野资料
- 发现理论与实践的对应关系

**独立性**：可独立运行，但能利用前面Agent的分析结果
**输出**：理论映射、理论验证、理论创新点

#### 4. KnowledgeGraphAgent（图谱层）
**职责**：构建知识图谱
- 整合实体、关系、维度分析、理论映射
- 构建多层次知识图谱
- 发现隐含的关联模式

**独立性**：需要前面Agent的输出，但图谱构建逻辑独立
**输出**：知识图谱（节点、边、属性）

#### 5. ReportGenerationAgent（报告层）
**职责**：生成分析报告
- 基于所有分析结果生成报告
- 支持多种报告模板（学术论文、调研报告、简报）
- 提供可视化和引用

**独立性**：需要前面所有Agent的输出
**输出**：Markdown报告、可视化图表、引用列表

---

## 🔄 数据流动设计

### 数据层次结构

```
Level 0: 原始文本
    ↓
Level 1: 结构化信息（实体、关系）[EntityRelationAgent]
    ↓
Level 2: 维度分析（多维度视角）[FieldDimensionAgent + Skills]
    ↓
Level 3: 理论映射（学术框架）[AcademicTheoryAgent]
    ↓
Level 4: 知识图谱（关联网络）[KnowledgeGraphAgent]
    ↓
Level 5: 分析报告（可视化呈现）[ReportGenerationAgent]
```

### 独立性与关联性

**独立性**：
- 每个Agent可以单独执行（提供足够输入）
- 每个Skill可以单独调用
- 测试时可以mock依赖的数据

**关联性**：
- Agent通过 `AgentCoordinator` 串联
- 前面Agent的输出作为后面Agent的输入
- Skill的输出被Agent整合

---

## 🎓 学术理论Skill设计

### xiangtu_china（费孝通《乡土中国》）

**理论维度**：
1. **差序格局** - 以己为中心的社会关系网络
2. **礼治秩序** - 基于传统和习俗的社会秩序
3. **熟人社会** - 基于长期共处的信任机制
4. **乡土本色** - 农业文明的特征

**语义向量准备**：
```python
# 为每个维度准备理论描述和示例
dimensions = {
    'chaxu_geju': {
        'theory_description': '差序格局是指...',
        'example_sentences': [
            '亲戚关系网络',
            '以家族为中心的人际关系',
            '远近亲疏的社会距离'
        ]
    }
}

# 计算维度的语义向量
for dim in dimensions:
    dim['vector'] = embedder.encode(
        dim['theory_description'] + ' ' + ' '.join(dim['example_sentences'])
    )
```

---

## 🔧 技术实现方案

### 方案：向量语义检索 + 可选LLM增强

#### 第一步：向量语义检索（必选，快速）

```python
def semantic_retrieve(text, dimension_vector, threshold=0.65):
    """基于向量相似度检索相关句子"""
    
    # 1. 分句
    sentences = split_sentences(text)
    
    # 2. 计算句子向量
    sentence_vectors = embedder.encode(sentences)
    
    # 3. 计算余弦相似度
    similarities = cosine_similarity(sentence_vectors, dimension_vector)
    
    # 4. 筛选高相似度句子
    relevant = [
        (sent, sim) 
        for sent, sim in zip(sentences, similarities) 
        if sim > threshold
    ]
    
    return sorted(relevant, key=lambda x: x[1], reverse=True)
```

#### 第二步：深度分析（可选，精准）

```python
def deep_analyze_with_llm(relevant_sentences, dimension_theory):
    """用LLM对相关内容进行深度分析"""
    
    if not relevant_sentences:
        return None
    
    prompt = f"""
作为田野调查专家，请从【{dimension_theory['name']}】维度分析以下内容。

理论框架：
{dimension_theory['description']}

田野资料：
{join(relevant_sentences)}

请分析：
1. 这些资料如何体现该理论维度？
2. 有哪些典型特征或证据？
3. 置信度如何（0-1）？

用JSON格式返回。
"""
    
    result = llm.generate(prompt)
    return parse_json(result)
```

### BGE向量模型集成

```python
from sentence_transformers import SentenceTransformer

class EmbeddingService:
    """向量编码服务（单例）"""
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = SentenceTransformer('BAAI/bge-large-zh-v1.5')
        return cls._instance
    
    def encode(self, texts):
        """批量编码文本"""
        return self._instance.encode(texts, normalize_embeddings=True)
```

---

## 📊 客户使用逻辑

### 用户视角的工作流

1. **创建项目**
   ```
   项目名称：李家村调查
   研究主题：乡村振兴中的社区治理
   ```

2. **选择分析框架**
   ```
   ☑ 社区治理分析 (community_governance)
   ☑ 生计生态分析 (livelihood_ecology)
   ☑ 乡土中国理论 (xiangtu_china)
   ☐ 满族文化分析 (manchu_culture)
   ```

3. **上传资料**
   ```
   - 访谈录音 × 5
   - 田野笔记 × 3
   - 文献资料 × 2
   ```

4. **自动分析**（后台运行）
   ```
   [1/6] 音频转录... ✓
   [2/6] 提取实体关系... ✓ (发现35个实体)
   [3/6] 多维度分析... ✓ (应用3个框架)
   [4/6] 学术理论映射... ✓
   [5/6] 构建知识图谱... ✓
   [6/6] 生成报告... ✓
   ```

5. **查看结果**
   ```
   - 知识图谱可视化
   - 多维度分析报告
   - 实体关系网络
   - 引用和证据链
   ```

---

## ✅ 验证标准

### Skill验证
- [ ] 能独立运行（单元测试通过）
- [ ] 使用向量语义检索（非关键词）
- [ ] 输出包含置信度和证据
- [ ] 处理速度 < 5秒/文档

### Agent验证
- [ ] 能独立运行（mock输入数据）
- [ ] 正确调用Skill
- [ ] 输出格式标准化
- [ ] 错误处理完善

### 集成验证
- [ ] AgentCoordinator能串联所有Agent
- [ ] 数据在Agent间正确传递
- [ ] 整体pipeline < 30秒/文档
- [ ] 生成的报告有实际价值

---

## 🚀 实施步骤

### Phase 1: 升级Skill基础设施（2-3天）
1. 创建 `SkillBase` 基类
2. 集成BGE向量模型（`EmbeddingService`）
3. 实现向量语义检索函数
4. 创建Skill单元测试框架

### Phase 2: 升级现有Skill（2天）
1. 升级 `community_governance.py` - 用向量替换关键词
2. 升级 `livelihood_ecology.py` - 用向量替换关键词
3. 为每个维度准备理论描述和示例
4. 测试验证

### Phase 3: 创建学术理论Skill（3天）
1. 实现 `xiangtu_china.py`（费孝通理论）
2. 准备4个维度的向量表示
3. 测试验证
4. （可选）实现 `sacred_memory.py`（景军理论）

### Phase 4: 优化Agent（2天）
1. 优化 `FieldDimensionAgent` - 更好地利用向量结果
2. 实现 `AcademicTheoryAgent` - 学术理论深度解读
3. 测试Agent与Skill的配合

### Phase 5: 集成测试（1天）
1. 端到端测试
2. 性能优化
3. 文档完善

---

## 💡 关键设计决策

### 为什么用向量而非关键词？
- **语义理解**：能识别同义表达（"村委会" = "村级组织"）
- **泛化能力**：能识别理论相关内容，即使没有确切关键词
- **准确性**：减少误匹配

### 为什么Skill和Agent分离？
- **复用性**：一个Skill可以被多个Agent使用
- **扩展性**：添加新Skill不需要改Agent
- **测试性**：可以独立测试
- **维护性**：职责清晰

### 为什么不全部用LLM？
- **成本**：向量检索便宜，LLM贵
- **速度**：向量检索快，LLM慢
- **可控性**：向量检索可解释，LLM黑盒
- **混合方案**：向量筛选 + LLM深度分析 = 最优

---

## 📖 参考资料

- 费孝通《乡土中国》
- 景军《神圣的记忆：都市化与祖先记忆的重建》
- BGE Embedding: https://github.com/FlagOpen/FlagEmbedding
- Sentence-Transformers: https://www.sbert.net/
