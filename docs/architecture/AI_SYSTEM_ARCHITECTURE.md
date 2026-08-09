# 真实AI智能系统架构设计

## 核心原则
1. **数据驱动**：所有分析必须基于用户上传的真实数据
2. **AI生成**：使用LLM进行真实推理，不使用预设模板
3. **自主学习**：从分析结果中提取模式，生成新Skill
4. **语义理解**：深度向量分析，发现隐含关联
5. **工作流自动化**：智能编排，自动重试，状态管理

## 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    用户上传文档/任务                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              工作流引擎 (Workflow Engine)                     │
│  • 自动编排步骤  • 依赖管理  • 失败重试  • 状态持久化          │
└──────────────┬──────────────────────────────────────────────┘
               │
               ├──────────────┬──────────────┬─────────────────┐
               ▼              ▼              ▼                 ▼
       ┌──────────┐   ┌──────────┐   ┌──────────┐     ┌──────────┐
       │ 文档处理  │   │ 向量分析  │   │  LLM分析  │     │ 学习引擎  │
       └──────────┘   └──────────┘   └──────────┘     └──────────┘

### 1. 文档处理引擎
- 文本提取 (PDF/DOC/TXT)
- 实体识别 (HanLP)
- 知识图谱构建 (Neo4j)
- 元数据提取

### 2. 向量语义分析引擎
- 文本向量化 (SentenceTransformer)
- **语义聚类** (KMeans/DBSCAN/HDBSCAN)
- **相似度矩阵计算**
- **主题提取** (BERTopic)
- **跨文档关联发现**
- **异常检测**

### 3. LLM分析引擎
- 集成 OpenAI/Anthropic/本地模型
- 基于真实数据的Prompt构建
- 流式生成分析报告
- 多轮对话式深度分析
- 引用溯源

### 4. 自主学习引擎
- 分析模式提取
- 知识图谱更新
- Skill自动生成
- 思维模型演化
- 反馈循环优化

### 5. 工作流引擎
- DAG任务编排
- 步骤依赖管理
- 失败自动重试
- 状态持久化
- 进度实时追踪
```

## 模块详细设计

### Module 1: 向量语义分析引擎

```python
# app/services/semantic_analyzer.py

class SemanticAnalyzer:
    """真实的语义分析引擎"""
    
    async def analyze_documents(self, documents: List[Document]) -> SemanticAnalysisResult:
        """
        深度语义分析流程：
        1. 向量化所有文档
        2. 语义聚类发现主题
        3. 计算文档相似度矩阵
        4. 提取主题关键词
        5. 发现跨文档关联
        6. 异常文档检测
        7. 生成可视化数据
        """
        
        # 1. 向量化
        vectors, chunks = await self._vectorize_all(documents)
        
        # 2. 聚类分析 (使用多种算法对比)
        kmeans_clusters = self._kmeans_clustering(vectors, n_clusters='auto')
        dbscan_clusters = self._dbscan_clustering(vectors)
        hdbscan_clusters = self._hdbscan_clustering(vectors)
        
        # 3. 主题提取 (BERTopic)
        topics = await self._extract_topics(chunks, vectors)
        
        # 4. 相似度矩阵
        similarity_matrix = self._compute_similarity_matrix(vectors)
        
        # 5. 跨文档关联
        cross_doc_relations = self._find_cross_document_relations(
            similarity_matrix, 
            documents,
            threshold=0.7
        )
        
        # 6. 异常检测
        outliers = self._detect_outliers(vectors)
        
        return SemanticAnalysisResult(
            clusters=kmeans_clusters,
            topics=topics,
            similarity_matrix=similarity_matrix,
            cross_relations=cross_doc_relations,
            outliers=outliers,
            vectors=vectors
        )
```

### Module 2: LLM驱动的分析器

```python
# app/services/llm_analyzer.py

class LLMAnalyzer:
    """基于LLM的真实数据分析"""
    
    def __init__(self):
        self.llm_client = self._init_llm()  # OpenAI/Anthropic/本地
    
    async def generate_tier1_analysis(
        self, 
        documents: List[Document],
        entities: List[Entity],
        semantic_result: SemanticAnalysisResult
    ) -> str:
        """
        Tier1分析：基于真实数据的信息整理
        不使用模板，完全由LLM根据数据生成
        """
        
        # 构建真实数据Prompt
        prompt = self._build_tier1_prompt(
            documents=documents,
            entities=entities,
            clusters=semantic_result.clusters,
            topics=semantic_result.topics,
            relations=semantic_result.cross_relations
        )
        
        # LLM生成分析
        analysis = await self.llm_client.generate(
            prompt=prompt,
            max_tokens=8000,
            temperature=0.3,
            stream=True  # 流式生成
        )
        
        # 添加引用溯源
        analysis_with_citations = self._add_citations(analysis, documents)
        
        return analysis_with_citations
    
    async def generate_tier2_analysis(
        self,
        tier1_analysis: str,
        documents: List[Document],
        knowledge_graph: KnowledgeGraph,
        semantic_result: SemanticAnalysisResult
    ) -> str:
        """
        Tier2分析：学术深度分析
        让LLM基于真实数据应用理论框架
        """
        
        prompt = f"""
你是一位社会学专家。基于以下真实数据进行学术深度分析：

## 文档内容摘要
{self._summarize_documents(documents)}

## 实体关系网络
{self._describe_knowledge_graph(knowledge_graph)}

## 语义主题
{self._describe_topics(semantic_result.topics)}

## 文档聚类结果
{self._describe_clusters(semantic_result.clusters)}

## 任务要求
1. 识别数据中体现的社会学现象
2. 判断适用的理论框架（如费孝通理论、社会网络理论等）
3. 深入分析数据与理论的对应关系
4. 提出学术见解和研究价值
5. 所有论述必须引用具体数据支撑

请生成8000-15000字的学术分析报告。
"""
        
        analysis = await self.llm_client.generate(prompt, max_tokens=15000)
        return analysis
    
    async def generate_tier3_analysis(
        self,
        tier1_analysis: str,
        tier2_analysis: str,
        market_data: Dict,  # 实时爬取的市场数据
        documents: List[Document]
    ) -> str:
        """
        Tier3分析：商业价值分析
        基于真实数据+实时市场数据
        """
        
        prompt = f"""
你是一位商业分析专家。基于以下真实信息进行商业价值分析：

## 项目数据
{self._extract_business_elements(documents)}

## 学术分析洞察
{tier2_analysis[:3000]}  # 提取关键洞察

## 实时市场数据
{market_data}  # 从公开API获取的真实市场数据

## 任务要求
1. 分析项目的商业潜力
2. 提出可行的商业模式
3. 评估市场机会和竞争态势
4. 提供投资价值分析
5. 所有数据必须有来源，所有结论必须有依据

请生成10000-20000字的商业分析报告。
"""
        
        analysis = await self.llm_client.generate(prompt, max_tokens=20000)
        return analysis
```

### Module 3: 自主学习引擎

```python
# app/services/learning_engine.py

class LearningEngine:
    """自主学习与Skill生成系统"""
    
    async def learn_from_analysis(
        self,
        analysis_results: Dict,
        feedback: Optional[Dict] = None
    ) -> List[NewSkill]:
        """
        从分析结果中学习新模式
        """
        
        # 1. 提取分析中的有效模式
        patterns = await self._extract_patterns(analysis_results)
        
        # 2. 识别重复出现的分析逻辑
        recurring_logic = self._identify_recurring_logic(patterns)
        
        # 3. 生成新的Skill定义
        new_skills = []
        for logic in recurring_logic:
            skill_definition = await self._generate_skill_definition(logic)
            skill_code = await self._generate_skill_code(skill_definition)
            
            new_skill = NewSkill(
                name=skill_definition.name,
                description=skill_definition.description,
                code=skill_code,
                trigger_conditions=skill_definition.triggers,
                confidence_score=self._calculate_confidence(logic)
            )
            
            # 4. 验证Skill有效性
            if await self._validate_skill(new_skill):
                new_skills.append(new_skill)
        
        # 5. 注册到Skill库
        for skill in new_skills:
            await self.skill_registry.register(skill)
        
        return new_skills
    
    async def _extract_patterns(self, analysis_results: Dict) -> List[Pattern]:
        """使用LLM提取分析模式"""
        
        prompt = f"""
分析以下分析结果，提取其中的分析模式和逻辑：

{json.dumps(analysis_results, ensure_ascii=False, indent=2)}

请识别：
1. 使用了哪些分析方法
2. 数据处理流程
3. 推理逻辑链
4. 可复用的分析框架

以JSON格式返回提取的模式。
"""
        
        patterns_json = await self.llm_client.generate(prompt, response_format="json")
        return [Pattern(**p) for p in json.loads(patterns_json)]
    
    async def evolve_thinking_models(self):
        """思维模型演化"""
        
        # 1. 收集所有成功的分析案例
        successful_cases = await self.db.get_successful_analyses()
        
        # 2. 提取思维模式
        thinking_patterns = []
        for case in successful_cases:
            pattern = await self._extract_thinking_pattern(case)
            thinking_patterns.append(pattern)
        
        # 3. 聚类相似思维模式
        clustered_patterns = self._cluster_thinking_patterns(thinking_patterns)
        
        # 4. 生成元思维模型
        for cluster in clustered_patterns:
            meta_model = await self._generate_meta_thinking_model(cluster)
            await self.thinking_model_registry.register(meta_model)
```

### Module 4: 工作流引擎

```python
# app/services/workflow_engine.py

class WorkflowEngine:
    """自动化工作流引擎"""
    
    def __init__(self):
        self.state_store = StateStore()  # Redis/PostgreSQL
        self.task_queue = TaskQueue()    # Celery/RQ
    
    async def execute_workflow(
        self,
        workflow_def: WorkflowDefinition,
        input_data: Dict
    ) -> WorkflowResult:
        """
        执行自动化工作流
        """
        
        # 1. 创建工作流实例
        workflow_instance = await self._create_instance(workflow_def, input_data)
        
        # 2. 解析依赖关系，构建DAG
        dag = self._build_dag(workflow_def.steps)
        
        # 3. 按拓扑顺序执行
        for step in dag.topological_sort():
            try:
                # 检查依赖是否完成
                if not await self._check_dependencies(step, workflow_instance):
                    await self._wait_for_dependencies(step, workflow_instance)
                
                # 执行步骤
                result = await self._execute_step(step, workflow_instance)
                
                # 保存状态
                await self.state_store.save_step_result(
                    workflow_instance.id,
                    step.id,
                    result
                )
                
            except Exception as e:
                # 失败重试
                if step.retry_policy:
                    await self._retry_step(step, workflow_instance, e)
                else:
                    await self._handle_failure(step, workflow_instance, e)
        
        return await self._finalize_workflow(workflow_instance)
    
    async def _execute_step(
        self,
        step: WorkflowStep,
        workflow_instance: WorkflowInstance
    ) -> StepResult:
        """执行单个步骤"""
        
        # 获取步骤输入
        step_input = await self._get_step_input(step, workflow_instance)
        
        # 根据步骤类型执行
        if step.type == StepType.DOCUMENT_PROCESSING:
            result = await self.doc_processor.process(step_input)
        
        elif step.type == StepType.SEMANTIC_ANALYSIS:
            result = await self.semantic_analyzer.analyze(step_input)
        
        elif step.type == StepType.LLM_ANALYSIS:
            result = await self.llm_analyzer.generate(step_input)
        
        elif step.type == StepType.LEARNING:
            result = await self.learning_engine.learn(step_input)
        
        return StepResult(
            step_id=step.id,
            status="completed",
            output=result,
            timestamp=datetime.now()
        )
```

## 技术栈

### 后端核心
- **FastAPI**: 异步API框架
- **SQLAlchemy**: ORM
- **Celery**: 异步任务队列
- **Redis**: 缓存和状态存储

### AI/ML组件
- **SentenceTransformer**: 向量化
- **scikit-learn**: 聚类算法 (KMeans, DBSCAN)
- **HDBSCAN**: 层次密度聚类
- **BERTopic**: 主题建模
- **HanLP**: 中文NLP
- **OpenAI API / Anthropic Claude API**: LLM分析
- **LangChain**: LLM应用框架

### 向量存储
- **ChromaDB**: 向量数据库
- **Faiss**: 高性能向量检索

### 知识图谱
- **Neo4j**: 图数据库

### 工作流
- **Apache Airflow** (可选): 复杂工作流编排
- 或自研轻量级DAG引擎

## 实现路线图

### Phase 1: 向量语义分析引擎 (Week 1-2)
- [ ] 实现多种聚类算法
- [ ] 集成BERTopic主题提取
- [ ] 相似度矩阵计算
- [ ] 跨文档关联发现
- [ ] 可视化接口

### Phase 2: LLM集成 (Week 2-3)
- [ ] OpenAI/Claude API集成
- [ ] Prompt工程框架
- [ ] 流式生成支持
- [ ] 引用溯源系统
- [ ] 成本控制

### Phase 3: 自主学习引擎 (Week 3-4)
- [ ] 模式提取算法
- [ ] Skill代码生成
- [ ] 思维模型演化
- [ ] 反馈循环

### Phase 4: 工作流引擎 (Week 4-5)
- [ ] DAG构建
- [ ] 状态管理
- [ ] 失败重试
- [ ] 进度追踪

### Phase 5: 重构三层分析器 (Week 5-6)
- [ ] Tier1数据驱动重构
- [ ] Tier2学术分析重构
- [ ] Tier3商业分析重构
- [ ] 实时数据集成

### Phase 6: 测试与优化 (Week 6-7)
- [ ] 单元测试
- [ ] 集成测试
- [ ] 性能优化
- [ ] 准确性验证

## 成本估算

### LLM API调用成本
- **Tier1分析**: ~8K tokens输出 × $0.015/1K = $0.12/次
- **Tier2分析**: ~15K tokens输出 × $0.015/1K = $0.23/次
- **Tier3分析**: ~20K tokens输出 × $0.015/1K = $0.30/次
- **学习引擎**: ~5K tokens × $0.015/1K = $0.08/次

**单次完整分析成本**: ~$0.73

### 开源替代方案
- 使用本地部署的开源模型 (Llama 3, Mistral, Qwen)
- 成本降为零，但需要GPU资源

## 下一步行动

1. **立即开始**: 实现向量语义分析引擎
2. **配置LLM**: 选择API提供商并配置
3. **重构分析器**: 移除模板代码，改为LLM驱动
4. **构建工作流**: 实现自动化编排
5. **添加学习**: 实现Skill自动生成

---

这是一个真正的AI智能系统，每个模块都基于真实数据和AI推理，不使用任何预设模板。
