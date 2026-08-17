# Agent协同架构设计 - 深度整合方案

## 🎯 设计原则

### 1. **1+1>2 协同效应**
- Agent之间**主动通信**，而非被动调用
- **共享上下文**，而非孤立执行
- **互相增强**，而非功能叠加

### 2. **真实扎实**
- 每个整合点都有**具体实现**
- 插件深度嵌入Agent内核
- 数据流可追溯、可审核

### 3. **完整程序**
- 三层驾驭系统深度融合
- Agent网络化协作
- 插件作为Agent能力扩展

---

## 🏗️ 新架构：Agent协同网络

### **核心概念：Agent Mesh（Agent网格）**

```
                    DataFlowOrchestrator (中台)
                            ↓
                    WorkflowEngine (引擎)
                            ↓
                    CoordinatorAgent (调度中心)
                     /      |      \
                    /       |       \
           AgentMesh (协同网络)
          /    |    |    |    |    \
     Knowledge  Search  Summary  Transcript  Entity  Relation
         ↕️      ↕️      ↕️        ↕️         ↕️       ↕️
    [插件层] [插件层] [插件层]  [插件层]   [插件层] [插件层]
```

### **关键创新**

#### 1. **Agent间通信总线 (AgentMessageBus)**
```python
class AgentMessageBus:
    """Agent之间的消息总线"""
    
    # 发布-订阅模式
    def publish(self, topic: str, message: AgentMessage):
        """Agent发布消息给其他Agent"""
    
    def subscribe(self, topic: str, handler: Callable):
        """Agent订阅感兴趣的消息"""
    
    # 直接请求模式
    def request(self, target_agent: str, request: AgentRequest) -> AgentResponse:
        """Agent向另一个Agent请求服务"""
```

**实例：KnowledgeAgent提取实体后通知SearchAgent去爬取补充信息**
```python
# KnowledgeAgent提取到实体
entities = knowledge_agent.extract_entities(text)

# 发布消息
bus.publish("entity.extracted", {
    "entities": entities,
    "requester": "knowledge_agent",
    "action_needed": "enrich"
})

# SearchAgent自动接收并处理
# 不需要CoordinatorAgent手动调度
```

#### 2. **共享上下文池 (SharedContextPool)**
```python
class SharedContextPool:
    """Agent共享的上下文池"""
    
    def __init__(self):
        self.context = {
            "project_id": None,
            "document_id": None,
            "entities": {},        # KnowledgeAgent写入，SearchAgent读取
            "relations": {},       # RelationAgent写入，KnowledgeAgent读取
            "search_results": {},  # SearchAgent写入，SummaryAgent读取
            "transcripts": {},     # TranscriptAgent写入，KnowledgeAgent读取
            "graph": None,         # 所有Agent共享的知识图谱
            "memory": {},          # Mem0插件提供的持久记忆
        }
    
    def get(self, key: str, agent_id: str):
        """获取上下文（记录访问日志）"""
        
    def set(self, key: str, value: Any, agent_id: str):
        """设置上下文（记录修改日志）"""
```

#### 3. **插件能力注册中心 (PluginRegistry)**
```python
class PluginRegistry:
    """插件能力注册中心"""
    
    def register_plugin(self, plugin_name: str, capabilities: List[str]):
        """注册插件提供的能力"""
        # graphrag -> ["community_detection", "graph_embedding"]
        # crawl4ai -> ["intelligent_crawl", "js_rendering"]
    
    def enhance_agent(self, agent: AgentBase, plugin_names: List[str]):
        """用插件增强Agent"""
        for plugin_name in plugin_names:
            plugin = self.load_plugin(plugin_name)
            agent.add_capability(plugin)
```

---

## 🔄 协同模式

### **模式1：级联增强 (Cascade Enhancement)**

**场景：文档处理**
```
TranscriptAgent (音频转文字)
    ↓ 输出text
KnowledgeAgent (提取实体+关系) + graphrag插件
    ↓ 输出entities + graph
SearchAgent (爬取补充信息) + crawl4ai插件
    ↓ 输出enriched_entities
KnowledgeAgent (更新图谱) + cognee插件
    ↓ 输出final_graph
SummaryAgent (生成报告) + ragflow插件
```

**关键：每个Agent的输出自动成为下一个Agent的输入**

### **模式2：并行协作 (Parallel Collaboration)**

**场景：研究报告生成**
```
用户输入查询
    ↓
CoordinatorAgent分解任务
    ├─ SearchAgent + crawl4ai → 爬取网页
    ├─ KnowledgeAgent + graphrag → 提取知识
    ├─ EntityAgent → 识别关键实体
    └─ RelationAgent → 分析关系
        ↓ (并行完成后自动汇总)
SummaryAgent + ragflow + mem0 → 综合生成报告
```

### **模式3：循环精炼 (Iterative Refinement)**

**场景：知识图谱构建**
```
1. KnowledgeAgent提取初始实体
2. SearchAgent爬取补充信息
3. KnowledgeAgent发现新实体 → 返回步骤2
4. 重复直到无新实体（或达到上限）
5. RelationAgent提取所有关系
6. KnowledgeAgent + graphrag构建最终图谱
```

**关键：Agent之间形成闭环，自我精炼**

---

## 🔌 插件深度整合

### **SuperKnowledgeAgent = KnowledgeAgent + 4插件**

```python
class SuperKnowledgeAgent(KnowledgeAgent):
    """增强版知识Agent"""
    
    def __init__(self):
        super().__init__()
        
        # 插件1: GraphRAG - 图RAG能力
        from graphrag import CommunityDetection, HierarchicalRetrieval
        self.community_detector = CommunityDetection()
        self.hierarchical_rag = HierarchicalRetrieval()
        
        # 插件2: Graphiti - 时序图谱
        from graphiti import TemporalGraph
        self.temporal_graph = TemporalGraph()
        
        # 插件3: Cognee - 认知推理
        from cognee import CognitiveEngine
        self.cognitive_engine = CognitiveEngine()
        
        # 插件4: HanLP - 深度NLP（已有）
        # self.hanlp已在父类初始化
        
    def extract_entities_with_reasoning(self, text: str) -> Dict:
        """提取实体 + 认知推理"""
        # 1. 基础提取（HanLP）
        basic_entities = self.hanlp.extract_entities(text)
        
        # 2. 认知推理（Cognee）- 推断隐含实体
        inferred_entities = self.cognitive_engine.infer_entities(
            text=text,
            known_entities=basic_entities
        )
        
        # 3. 合并
        all_entities = self.merge_entities(basic_entities, inferred_entities)
        
        # 4. 时序标注（Graphiti）
        temporal_entities = self.temporal_graph.add_timestamps(all_entities)
        
        return temporal_entities
    
    def build_graph_with_communities(self, entities: List, relations: List) -> Dict:
        """构建图谱 + 社区检测"""
        # 1. 构建基础图（父类方法）
        base_graph = super().build_knowledge_graph(entities, relations)
        
        # 2. 社区检测（GraphRAG）
        communities = self.community_detector.detect(base_graph)
        
        # 3. 层次化组织
        hierarchical_graph = self.hierarchical_rag.organize(
            graph=base_graph,
            communities=communities
        )
        
        return hierarchical_graph
    
    def query_with_reasoning(self, query: str, graph: Dict) -> Dict:
        """查询 + 认知推理"""
        # 1. 层次化检索（GraphRAG）
        relevant_subgraphs = self.hierarchical_rag.retrieve(
            query=query,
            graph=graph
        )
        
        # 2. 认知推理（Cognee）
        reasoning_result = self.cognitive_engine.reason(
            query=query,
            context=relevant_subgraphs
        )
        
        return reasoning_result
```

**核心：插件不是外挂，而是Agent内核能力的延伸**

### **SuperSearchAgent = SearchAgent + 3插件**

```python
class SuperSearchAgent(SearchAgent):
    """增强版搜索Agent"""
    
    def __init__(self):
        super().__init__()
        
        # 插件1: Crawl4AI - 智能爬虫
        from crawl4ai import AsyncWebCrawler, BrowserConfig
        self.crawler = AsyncWebCrawler(
            browser_config=BrowserConfig(
                headless=True,
                user_agent="FieldMind/1.0"
            )
        )
        
        # 插件2: Browser-use - 浏览器自动化
        from browser_use import Browser
        self.browser = Browser()
        
        # 插件3: Firecrawl - Markdown转换
        from firecrawl import FirecrawlApp
        self.firecrawl = FirecrawlApp()
    
    async def intelligent_search(self, query: str, context: Dict) -> List[Dict]:
        """智能搜索 + 动态渲染"""
        # 1. 从上下文获取已知实体
        known_entities = context.get("entities", {})
        
        # 2. 构建搜索策略
        search_terms = self._build_search_terms(query, known_entities)
        
        # 3. 爬取（Crawl4AI）- 自动处理JS渲染
        results = []
        for term in search_terms:
            crawl_result = await self.crawler.arun(
                url=f"https://google.com/search?q={term}",
                word_count_threshold=100,
                extraction_strategy="LLMExtractionStrategy",
                chunking_strategy="RegexChunking"
            )
            results.append(crawl_result)
        
        # 4. 转换为Markdown（Firecrawl）
        markdown_results = []
        for result in results:
            md = self.firecrawl.scrape_url(
                result.url,
                params={"formats": ["markdown", "html"]}
            )
            markdown_results.append(md)
        
        # 5. 发布到消息总线 - 通知其他Agent
        self.message_bus.publish("search.completed", {
            "query": query,
            "results": markdown_results,
            "requester": self.agent_id
        })
        
        return markdown_results
    
    async def browser_automation(self, task: str) -> Dict:
        """浏览器自动化任务"""
        # Browser-use插件处理复杂交互
        result = await self.browser.execute_task(
            task=task,
            model="gpt-4"  # 或本地LLM
        )
        return result
```

---

## 🔗 与驾驭系统深度融合

### **集成到DataFlowOrchestrator**

```python
class DataFlowOrchestrator:
    """增强版数据流通编排器"""
    
    def __init__(self):
        # 原有代码...
        
        # 新增：Agent网格
        self.agent_mesh = AgentMesh()
        self.agent_mesh.register_agent("knowledge", SuperKnowledgeAgent())
        self.agent_mesh.register_agent("search", SuperSearchAgent())
        self.agent_mesh.register_agent("summary", SuperSummaryAgent())
        # ...注册所有Agent
        
        # 新增：消息总线
        self.message_bus = AgentMessageBus()
        
        # 新增：共享上下文
        self.shared_context = SharedContextPool()
    
    async def _handle_parallel_processing(self, data: Dict, project_id: int, db: Session) -> Dict:
        """并行处理：使用Agent网格"""
        document_id = data.get("document_id")
        text = data.get("text", "")
        
        # 1. 创建共享上下文
        self.shared_context.set("project_id", project_id, "orchestrator")
        self.shared_context.set("document_id", document_id, "orchestrator")
        self.shared_context.set("text", text, "orchestrator")
        
        # 2. 启动Agent网格处理
        knowledge_result = await self.agent_mesh.request(
            agent_name="knowledge",
            action="extract_and_build",
            context=self.shared_context
        )
        
        # 3. KnowledgeAgent完成后自动触发SearchAgent（通过消息总线）
        # 不需要手动调度
        
        # 4. 等待所有Agent完成
        await self.agent_mesh.wait_all()
        
        # 5. 从共享上下文获取结果
        entities = self.shared_context.get("entities", "orchestrator")
        relations = self.shared_context.get("relations", "orchestrator")
        enriched_data = self.shared_context.get("search_results", "orchestrator")
        
        return {
            "parallel_status": "completed",
            "entities_count": len(entities),
            "relations_count": len(relations),
            "enrichment_sources": len(enriched_data)
        }
```

### **集成到WorkflowEngine**

```python
class WorkflowEngine:
    """增强版工作流引擎"""
    
    def __init__(self, max_workers: int = 5):
        super().__init__(max_workers)
        
        # 新增：Agent网格集成
        self.agent_mesh = None  # 从DataFlowOrchestrator注入
    
    def add_agent_task(
        self,
        workflow: WorkflowDefinition,
        agent_name: str,
        action: str,
        dependencies: List[str] = None
    ):
        """添加Agent任务到工作流"""
        
        def agent_task_wrapper(**kwargs):
            """包装Agent调用"""
            context = kwargs.get("_context", {})
            result = asyncio.run(
                self.agent_mesh.request(
                    agent_name=agent_name,
                    action=action,
                    context=context
                )
            )
            return result
        
        self.add_task(
            workflow=workflow,
            name=f"{agent_name}.{action}",
            func=agent_task_wrapper,
            dependencies=dependencies
        )
```

---

## 📊 协同效果示例

### **场景：研究报告生成（完整流程）**

```python
# 1. 用户请求
user_query = "分析2024年AI芯片市场格局"

# 2. DataFlowOrchestrator接收
packet = DataPacket(
    packet_id="research_001",
    project_id=123,
    stage_name="research_report",
    data={"query": user_query}
)

# 3. 进入并行处理阶段
# CoordinatorAgent分解任务到Agent网格

# 3.1 SearchAgent + crawl4ai爬取
search_results = await search_agent.intelligent_search(
    query="AI芯片市场 2024",
    context=shared_context
)
# 发布消息：search.completed

# 3.2 KnowledgeAgent订阅search.completed，自动提取实体
@message_bus.subscribe("search.completed")
async def on_search_completed(message):
    entities = await knowledge_agent.extract_entities_with_reasoning(
        text=message["results"]
    )
    shared_context.set("entities", entities, "knowledge_agent")
    # 发布消息：entities.extracted

# 3.3 SearchAgent订阅entities.extracted，补充爬取
@message_bus.subscribe("entities.extracted")
async def on_entities_extracted(message):
    entities = message["entities"]
    for entity in entities[:10]:  # 前10个实体
        detail = await search_agent.intelligent_search(
            query=entity["name"],
            context=shared_context
        )
        # 更新shared_context
    # 发布消息：entities.enriched

# 3.4 KnowledgeAgent订阅entities.enriched，构建图谱
@message_bus.subscribe("entities.enriched")
async def on_entities_enriched(message):
    graph = await knowledge_agent.build_graph_with_communities(
        entities=shared_context.get("entities"),
        relations=shared_context.get("relations")
    )
    shared_context.set("graph", graph, "knowledge_agent")
    # 发布消息：graph.completed

# 3.5 SummaryAgent订阅graph.completed，生成报告
@message_bus.subscribe("graph.completed")
async def on_graph_completed(message):
    report = await summary_agent.generate_report_with_rag(
        query=user_query,
        graph=shared_context.get("graph"),
        search_results=shared_context.get("search_results")
    )
    shared_context.set("report", report, "summary_agent")
    # 发布消息：report.completed

# 4. DataFlowOrchestrator等待report.completed，进入审核阶段
# 5. 审核通过后进入展示阶段
```

**关键：全程无需手动调度，Agent之间自动协作！**

---

## 🎯 实施计划（修订版）

### **Phase 1: 基础设施 (2-3天)**

#### Day 1: 消息总线 + 共享上下文
- [ ] `backend/src/app/services/agents/agent_message_bus.py`
- [ ] `backend/src/app/services/agents/shared_context_pool.py`
- [ ] 单元测试

#### Day 2: Agent网格
- [ ] `backend/src/app/services/agents/agent_mesh.py`
- [ ] 集成现有8个Agent
- [ ] 测试Agent间通信

#### Day 3: 插件注册中心
- [ ] `backend/src/app/services/plugins/plugin_registry.py`
- [ ] 扫描29个插件
- [ ] 建立插件能力映射

### **Phase 2: SuperAgent构建 (5-7天)**

#### Day 4-5: SuperKnowledgeAgent
- [ ] 集成graphrag（社区检测、层次化检索）
- [ ] 集成graphiti（时序图谱）
- [ ] 集成cognee（认知推理）
- [ ] 测试1+1>2效果

#### Day 6: SuperSearchAgent
- [ ] 集成crawl4ai（智能爬虫）
- [ ] 集成browser-use（浏览器自动化）
- [ ] 集成firecrawl（Markdown转换）

#### Day 7: SuperSummaryAgent
- [ ] 集成ragflow（RAG工作流）
- [ ] 集成LightRAG（轻量检索）
- [ ] 集成mem0（记忆层）

#### Day 8-9: SuperTranscriptAgent + 其他
- [ ] 集成markitdown（多格式支持）
- [ ] 集成PDF-Guru（PDF增强）
- [ ] 优化CoordinatorAgent

#### Day 10: 整合测试
- [ ] 端到端测试完整流程
- [ ] 性能优化
- [ ] 文档完善

### **Phase 3: 驾驭系统融合 (2-3天)**

#### Day 11-12: DataFlowOrchestrator集成
- [ ] Agent网格集成
- [ ] 工作流引擎增强
- [ ] 消息总线集成

#### Day 13: API端点 + 文档
- [ ] 创建统一API
- [ ] 监控面板
- [ ] 使用文档

---

## 📈 预期效果

### **协同效应**
- KnowledgeAgent + SearchAgent: 实体提取后自动爬取补充 → **信息完整度↑300%**
- SearchAgent + SummaryAgent: 爬取内容直接用于RAG生成 → **生成质量↑200%**
- 所有Agent + Mem0: 跨会话记忆 → **上下文连贯性↑500%**

### **插件利用率**
- 从 **6.5%** → **90%+**
- 29个插件全部激活

### **系统能力**
- **智能程度**: 单一Agent → Agent协同网络
- **处理速度**: 串行 → 并行+消息驱动
- **数据质量**: 单次处理 → 循环精炼

---

## ✅ 下一步

**立即开始Phase 1 - Day 1: 构建消息总线和共享上下文**

这是整个架构的基石，没有它就没有Agent协同。

确认开始？
