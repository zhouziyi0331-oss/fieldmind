# FieldMind 完整重建计划

## 📊 当前架构诊断

### 现状：空壳问题
| 组件 | 状态 | 问题 |
|------|------|------|
| **6个CrewAI Agents** | 🔴 空壳 | crew_config.py存在但从未被调用 |
| **4种Crew工作流** | 🔴 空壳 | 编排逻辑存在但无入口 |
| **6个"内置"Skills** | 🔴 假数据 | builtin/*.py文件不存在，只是数据库占位符 |
| **2个真实Skills** | 🟡 初级 | community_governance.py, livelihood_ecology.py存在但简陋 |
| **文档处理流程** | 🟢 基础 | 转录→分词→向量化工作，但未用Agent/Skill |

### 实际工作流程（background_tasks.py）
```
上传文件 → 识别类型 → 提取内容（Whisper/OCR/文本）
  → jieba分词 → BGE向量化 → 存入ChromaDB
  → 动态发现引擎（主题/实体）→ 质量检查 → 完成
```

**问题：没有任何Skill分析、没有任何Agent协作**

---

## 🎯 目标架构

### 三层架构：Skills → Agents → Workflows

```
┌─────────────────────────────────────────────────────────┐
│  Layer 3: Workflow Orchestration (CrewAI)              │
│  ┌───────────┬───────────┬───────────┬───────────┐    │
│  │ 文档处理流 │ 研究报告流 │ RAG查询流 │ 自主协作流 │    │
│  └───────────┴───────────┴───────────┴───────────┘    │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│  Layer 2: Intelligent Agents (6个专业Agent)             │
│  ┌──────────┬──────────┬──────────┬──────────┐        │
│  │ 转录专员  │ 实体识别 │ 关系抽取 │ 网络搜索 │        │
│  │          │ 专员     │ 专员     │ 专员     │        │
│  └──────────┴──────────┴──────────┴──────────┘        │
│  ┌──────────┬──────────┐                              │
│  │ 总结专员  │ 协调专员 │                              │
│  └──────────┴──────────┘                              │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│  Layer 1: Analysis Skills (6个学术/方法论Skills)         │
│  ┌──────────┬──────────┬──────────┬──────────┐        │
│  │ 乡土中国  │ 满族文化 │ 神圣记忆 │ 多村SOP  │        │
│  │ (费孝通) │ (项链)   │ (景军)   │          │        │
│  └──────────┴──────────┴──────────┴──────────┘        │
│  ┌──────────┬──────────┐                              │
│  │ 商业可行性│ 文献市场 │                              │
│  └──────────┴──────────┘                              │
└─────────────────────────────────────────────────────────┘
```

---

## 📝 完整实施计划（共3个阶段）

---

## 🔧 **阶段1：Skills层实现（6个独立Skill）**

### ✅ 已完成的Skills（4个）
```
backend/src/app/services/skills/
├── heritage_dadi.py               ✅ 大地遗产方法论（已实现）
├── business_feasibility.py        ✅ 商业可行性验证（已实现）
├── multi_village_sop.py           ✅ 多村联动SOP（已实现）
└── literature_market_research.py  ✅ 文献市场研究（已实现）
```

### 🔨 待实现的Skills（2个）
```
backend/src/app/services/skills/
├── xiangtu_china.py          # 🆕 费孝通《乡土中国》
└── sacred_memory.py          # 🆕 景军《神圣记忆》
```

### 为什么先做Skills？
- **自下而上**：Skills是基础分析能力，Agents调用Skills
- **独立测试**：每个Skill独立运行，不依赖Agent框架
- **可复用**：既能独立运行，也能被Agent调用

### 1.1 创建剩余2个真实的Skill文件

#### 每个Skill的标准结构
```python
"""
Skill名称 - 学术理论框架
"""
from typing import Dict, List, Any

class SkillName:
    """Skill描述"""
    
    def __init__(self):
        self.dimensions = {
            "dimension1": {
                "name": "维度名称",
                "keywords": ["关键词1", "关键词2"],
                "description": "维度描述"
            },
            # ... 更多维度
        }
    
    def analyze(self, text: str, metadata: Dict = None) -> Dict[str, Any]:
        """
        分析文本内容
        
        Args:
            text: 待分析文本
            metadata: 元数据（文档ID、项目ID等）
        
        Returns:
            分析结果字典
        """
        results = {
            "skill_name": "技能名称",
            "matched_dimensions": [],
            "insights": [],
            "confidence": 0.0
        }
        
        # 维度匹配逻辑
        for dim_id, dim_info in self.dimensions.items():
            matches = self._match_dimension(text, dim_info)
            if matches:
                results["matched_dimensions"].append({
                    "dimension": dim_id,
                    "matches": matches
                })
        
        return results
    
    def _match_dimension(self, text: str, dimension: Dict) -> List[Dict]:
        """匹配单个维度"""
        # 实现关键词匹配、上下文提取等
        pass

# 导出analyze函数供外部调用
def analyze(text: str, metadata: Dict = None) -> Dict[str, Any]:
    skill = SkillName()
    return skill.analyze(text, metadata)
```

### 1.2 已实现Skills概览（4个）

#### **✅ Skill 1: heritage_dadi.py - 大地遗产方法论**
已实现，基于大地遗产公司真实方法论文档
- **维度**：文化遗产识别、价值评估、保护策略、活化利用
- **测试状态**：通过，40个匹配，0.719置信度

#### **✅ Skill 2: business_feasibility.py - 商业可行性验证**
已实现，基于乡村文化遗产商业可行性验证方法论
- **维度**：资源扫描、价值判断、概念方案、可行性验证
- **测试状态**：通过，101个匹配，0.693置信度

#### **✅ Skill 3: multi_village_sop.py - 多村联动SOP**
已实现，基于多村落田野调查标准操作流程
- **维度**：基础调研、文化资产、利益相关方、业态评估、风险识别、行动规划
- **测试状态**：通过，40个匹配，0.708置信度

#### **✅ Skill 4: literature_market_research.py - 文献市场研究**
已实现，基于文献和市场调研方法论
- **维度**：行业趋势、竞品分析、政策环境、成功案例
- **测试状态**：通过，40个匹配，0.750置信度

---

### 1.3 待实现Skills详细设计（2个）

#### **🆕 Skill 5: xiangtu_china.py - 费孝通《乡土中国》**
**学术背景**：中国社会学经典著作，分析传统乡土社会结构
**维度**：
- 差序格局（家族关系网络）
- 礼治秩序（规则与人情）
- 熟人社会（信任机制）
- 长老统治（权力结构）
- 男女有别（性别角色）
- 现代化冲击（传统vs现代）

**关键词库**：宗族、血缘、面子、人情、礼俗、乡规民约、家族网络、长老、宗法...

**应用场景**：分析田野调查中的社会结构、权力关系、人际网络

#### **🆕 Skill 6: sacred_memory.py - 景军《神圣记忆》**
**学术背景**：景军教授关于记忆、仪式与身份认同的研究
**维度**：
- 集体记忆（共同历史叙事）
- 仪式实践（纪念活动）
- 身份建构（群体认同）
- 历史叙事（过去的意义）

**关键词库**：纪念、祭祀、传说、口述历史、历史事件、仪式、象征、认同、记忆...

**应用场景**：分析社区历史记忆、文化传承、集体身份认同

### 1.4 将Skills接入文档处理流程

**修改：background_tasks.py**
在向量化完成后，自动调用所有激活的Skills进行分析：

```python
# 在 process_document_async() 中，向量化完成后添加：
if content and doc.extra_data.get('pipeline_completed'):
    # 调用所有激活的Skills
    skill_results = execute_all_skills(content, document_id, doc.project_id, db)
    doc.extra_data['skill_analysis'] = skill_results
    db.commit()
```

**新增函数：execute_all_skills()**
```python
def execute_all_skills(content: str, document_id: int, project_id: int, db: Session) -> Dict:
    """
    执行所有激活的Skills
    """
    # 获取项目启用的Skills
    project = db.query(Project).filter(Project.id == project_id).first()
    enabled_skills = project.settings.get('enabled_skills', [])
    
    results = {}
    for skill_name in enabled_skills:
        try:
            skill_result = execute_skill_analysis(skill_name, document_id, content, project_id, db)
            results[skill_name] = skill_result
        except Exception as e:
            logger.error(f"Skill {skill_name} 分析失败: {e}")
            results[skill_name] = {"error": str(e)}
    
    return results
```

### 1.5 测试每个Skill

为每个Skill创建测试文件：
```
backend/tests/skills/
├── test_heritage_dadi.py              ✅ 已测试通过
├── test_business_feasibility.py       ✅ 已测试通过
├── test_multi_village_sop.py          ✅ 已测试通过
├── test_literature_market_research.py ✅ 已测试通过
├── test_xiangtu_china.py              🆕 待创建
└── test_sacred_memory.py              🆕 待创建
```

---

## 🤖 **阶段2：Agents层实现（6个智能Agent）**

### 为什么第二步做Agents？
- **Skills已就绪**：Agents可以调用Skills进行分析
- **独立但协作**：每个Agent有明确职责，但能相互配合
- **CrewAI集成**：为下一步的Workflow做准备

### 2.1 修改crew_config.py，增强Agent能力

#### **Agent 1: 转录专员 (TranscriptAgent)**
- **职责**：处理音频/视频转录，识别方言
- **工具**：Whisper API
- **输入**：音频文件路径
- **输出**：带时间戳的转录文本

#### **Agent 2: 实体识别专员 (EntityAgent)**
- **职责**：NER命名实体识别
- **工具**：HanLP/jieba + 自定义实体库
- **输入**：文本内容
- **输出**：实体列表（人名、地名、机构、时间）

#### **Agent 3: 关系抽取专员 (RelationAgent)**
- **职责**：构建知识图谱，识别实体关系
- **工具**：依存句法分析、规则模板
- **输入**：文本 + 实体列表
- **输出**：关系三元组（主体-关系-客体）

#### **Agent 4: 网络搜索专员 (SearchAgent)**
- **职责**：互联网信息检索
- **工具**：SearchTool（集成搜索API）
- **输入**：查询关键词
- **输出**：相关网页/文档列表

#### **Agent 5: 总结专员 (SummaryAgent)**
- **职责**：生成研究报告
- **工具**：调用Skills进行理论分析
- **输入**：文本 + 实体 + 关系
- **输出**：结构化报告

#### **Agent 6: 协调专员 (CoordinatorAgent)**
- **职责**：任务分配、流程控制
- **工具**：任务队列、状态管理
- **输入**：总体目标
- **输出**：子任务分配结果

### 2.2 为每个Agent创建独立的Service类

**新建目录结构**：
```
backend/src/app/services/agents/
├── __init__.py
├── transcript_agent.py
├── entity_agent.py
├── relation_agent.py
├── search_agent.py
├── summary_agent.py
└── coordinator_agent.py
```

**标准Agent结构**：
```python
"""
Agent名称 - 职责描述
"""
from typing import Dict, Any, List
from crewai import Agent, Task

class AgentName:
    """Agent描述"""
    
    def __init__(self, llm_config: Dict = None):
        self.llm_config = llm_config or self._default_llm_config()
        self.agent = self._create_agent()
    
    def _default_llm_config(self) -> Dict:
        """默认LLM配置"""
        return {
            "model": "qwen2.5:7b",
            "base_url": "http://localhost:11434"
        }
    
    def _create_agent(self) -> Agent:
        """创建CrewAI Agent"""
        return Agent(
            role="角色名称",
            goal="目标描述",
            backstory="背景故事",
            verbose=True,
            allow_delegation=False,
            llm=self.llm_config
        )
    
    def execute(self, input_data: Any) -> Dict[str, Any]:
        """
        执行Agent任务
        
        Args:
            input_data: 输入数据
        
        Returns:
            执行结果
        """
        task = Task(
            description=f"处理输入: {input_data}",
            agent=self.agent,
            expected_output="期望的输出格式"
        )
        
        result = self.agent.execute_task(task)
        return self._format_result(result)
    
    def _format_result(self, raw_result: Any) -> Dict:
        """格式化结果"""
        return {
            "agent": self.__class__.__name__,
            "result": raw_result,
            "timestamp": datetime.now().isoformat()
        }
```

### 2.3 将Agents接入文档处理流程

**修改：background_tasks.py**
在Skills分析完成后，根据需要调用相应的Agents：

```python
# 在 execute_all_skills() 后添加：
if doc.extra_data.get('skill_analysis'):
    # 调用实体识别Agent
    from app.services.agents.entity_agent import EntityAgent
    entity_agent = EntityAgent()
    entities = entity_agent.execute(content)
    doc.extra_data['entities'] = entities
    
    # 调用关系抽取Agent
    from app.services.agents.relation_agent import RelationAgent
    relation_agent = RelationAgent()
    relations = relation_agent.execute({
        "text": content,
        "entities": entities
    })
    doc.extra_data['relations'] = relations
    
    db.commit()
```

---

## 🔄 **阶段3：Workflows层实现（4种协作流程）**

### 为什么最后做Workflows？
- **Skills和Agents已就绪**：有了基础能力和智能处理
- **编排协作**：将多个Agent组合成完整流程
- **真实应用场景**：解决实际的复杂任务

### 3.1 四种Workflow定义

#### **Workflow 1: 文档处理流 (DocumentProcessingCrew)**
```
输入：上传的文档/音频/视频
流程：转录专员 → 实体识别专员 → 关系抽取专员 → 总结专员
输出：结构化文档（文本+实体+关系+报告）

应用场景：
- 田野调查访谈录音转文字+分析
- 文献资料提取知识图谱
```

#### **Workflow 2: 研究报告流 (ResearchReportCrew)**
```
输入：研究主题/问题
流程：网络搜索专员 → 实体识别专员 → Skills分析 → 总结专员
输出：完整研究报告

应用场景：
- 案头研究：搜索相关政策、案例、文献
- 竞品分析：调研同类项目
```

#### **Workflow 3: RAG查询流 (RAGQueryCrew)**
```
输入：用户提问
流程：实体识别专员（提取查询实体）→ 向量检索（从知识库找相关文档）
      → 关系抽取专员（找实体关系）→ 总结专员（生成答案）
输出：基于知识库的准确答案

应用场景：
- 项目知识库问答
- 跨文档信息整合
```

#### **Workflow 4: 自主协作流 (AutonomousCrew)**
```
输入：复杂目标（如"完成某村落的完整田野调查报告"）
流程：协调专员分解任务 → 动态分配给各专员 → 协调专员整合结果
输出：完整项目成果

应用场景：
- 多村落联动调研
- 大型项目综合分析
```

### 3.2 创建Workflow Service

**新建文件**：`backend/src/app/services/workflows/workflow_orchestrator.py`

```python
"""
Workflow编排器 - 调度CrewAI工作流
"""
from typing import Dict, Any, List
from crewai import Crew, Process
from app.services.agents.transcript_agent import TranscriptAgent
from app.services.agents.entity_agent import EntityAgent
# ... 导入所有Agents

class WorkflowOrchestrator:
    """工作流编排器"""
    
    def __init__(self):
        # 初始化所有Agents
        self.transcript_agent = TranscriptAgent()
        self.entity_agent = EntityAgent()
        # ...
    
    def run_document_processing(self, file_path: str) -> Dict:
        """运行文档处理流"""
        crew = self._create_document_crew(file_path)
        result = crew.kickoff()
        return self._format_crew_result(result)
    
    def run_research_report(self, query: str) -> Dict:
        """运行研究报告流"""
        crew = self._create_research_crew(query)
        result = crew.kickoff()
        return self._format_crew_result(result)
    
    # ... 其他Workflow方法
    
    def _create_document_crew(self, file_path: str) -> Crew:
        """创建文档处理Crew"""
        from crewai import Task
        
        # 定义任务序列
        tasks = [
            Task(
                description=f"转录文档 {file_path}",
                agent=self.transcript_agent.agent,
                expected_output="转录文本"
            ),
            Task(
                description="识别实体",
                agent=self.entity_agent.agent,
                expected_output="实体列表"
            ),
            # ... 更多任务
        ]
        
        return Crew(
            agents=[self.transcript_agent.agent, self.entity_agent.agent],
            tasks=tasks,
            process=Process.sequential,
            verbose=True
        )
```

### 3.3 暴露Workflow API

**新建API路由**：`backend/src/app/api/v1/workflows.py`

```python
@router.post("/workflows/document-processing")
async def run_document_workflow(
    document_id: int,
    db: Session = Depends(get_db)
):
    """触发文档处理工作流"""
    orchestrator = WorkflowOrchestrator()
    result = orchestrator.run_document_processing(document_id)
    return result

@router.post("/workflows/research-report")
async def run_research_workflow(
    query: str,
    db: Session = Depends(get_db)
):
    """触发研究报告工作流"""
    orchestrator = WorkflowOrchestrator()
    result = orchestrator.run_research_report(query)
    return result
```

---

## 🧹 **阶段4：清理虚假内容**

在所有真实功能实现后，清理假数据：

### 4.1 删除假的"内置"Skills数据
```python
# 删除 skills.py 第132-193行的假数据创建逻辑
# 改为从真实文件目录读取Skills
```

### 4.2 更新Skill加载逻辑
```python
# skills.py 改为动态扫描 services/skills/ 目录
# 自动注册所有可用的Skill类
```

### 4.3 删除未使用的旧代码
- 删除 `community_governance.py` 和 `livelihood_ecology.py`（已被新Skill替代）
- 清理 `skill_config.py` 中的硬编码Skill列表

---

## 📦 **每个阶段的交付物**

### 阶段1交付：
- [x] 4个Skill Python文件（heritage_dadi.py等）**已完成**
- [x] 4个Skill测试文件 **已完成**
- [ ] 2个新Skill Python文件（xiangtu_china.py, sacred_memory.py）
- [ ] 2个新Skill测试文件
- [ ] Skills接入文档处理流程（6个全部接入）
- [ ] Skill配置API更新（读取真实文件）

### 阶段2交付：
- [ ] 6个Agent Service类（transcript_agent.py等）
- [ ] Agents接入文档处理流程
- [ ] Agent测试用例
- [ ] Agent API接口（独立调用）

### 阶段3交付：
- [ ] WorkflowOrchestrator编排器
- [ ] 4种Workflow实现
- [ ] Workflow API接口
- [ ] Workflow测试场景

### 阶段4交付：
- [ ] 清理假数据代码
- [ ] 更新文档和注释
- [ ] 完整集成测试

---

## 🧪 **测试策略**

### 单元测试（每层独立）
- **Skills**：给定文本，验证维度匹配正确性
- **Agents**：给定输入，验证输出格式和内容
- **Workflows**：给定场景，验证流程完整性

### 集成测试（端到端）
- 上传田野调查访谈录音 → 全流程处理 → 生成结构化报告
- 提出研究问题 → 搜索+分析 → 生成研究报告
- 知识库问答 → RAG检索 → 生成答案

---

## 📊 **里程碑时间估算**

| 阶段 | 内容 | 预估工作量 | 关键挑战 |
|------|------|-----------|---------|
| **阶段1** | 6个Skills实现 | 每个2-3小时 | 学术理论框架准确性 |
| **阶段2** | 6个Agents实现 | 每个1-2小时 | CrewAI集成调试 |
| **阶段3** | 4个Workflows | 每个2-3小时 | 多Agent协作编排 |
| **阶段4** | 清理虚假内容 | 1-2小时 | 不破坏现有功能 |
| **测试** | 全面测试 | 4-6小时 | 端到端场景覆盖 |

**总计：约30-40小时的扎实开发**

---

## ✅ **质量标准**

每个组件必须满足：
1. **独立可运行**：单独测试通过
2. **有真实内容**：不是空函数或假数据
3. **有完整文档**：注释清晰，说明输入输出
4. **有测试覆盖**：至少有2-3个测试用例
5. **能被集成**：上层可以正确调用

---

## 🚀 **下一步行动**

你确认这个计划后，我将开始：
**从阶段1开始，逐个实现6个Skills**

第一个Skill：`xiangtu_china.py`（费孝通《乡土中国》）
- 定义6个维度
- 实现关键词匹配和上下文提取
- 编写测试用例
- 接入文档处理流程

**你同意这个计划吗？需要调整哪些部分？**
