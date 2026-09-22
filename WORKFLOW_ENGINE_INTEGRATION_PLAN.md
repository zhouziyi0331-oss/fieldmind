# WorkflowEngine 全面植入计划 - Stage 8

**目标**: 将WorkflowEngine覆盖率从1.6%提升到>50%  
**预计时间**: 2-3天  
**优先级**: P0 - 核心架构升级

---

## 当前状态分析

### 已实现的WorkflowEngine功能
- ✅ **workflow_engine.py** (313行) - DAG引擎核心
- ✅ **workflow_templates.py** - 4个预定义模板
  - document_processing_workflow
  - knowledge_graph_workflow
  - full_analysis_workflow
  - report_generation_workflow
- ✅ **workflow_service.py** - 工作流CRUD服务

### 当前使用情况
- 📊 **服务文件总数**: 304个
- 📊 **已使用WorkflowEngine**: ~3个 (workflow_templates.py)
- 📊 **覆盖率**: 1.6%

---

## 植入策略

### 阶段1: 核心文档处理流 (P0, 1天)

#### 目标服务 (15个)
1. **document_processor.py** - 文档处理主流程
2. **pdf_processor.py** - PDF处理
3. **audio_processor.py** - 音频处理
4. **video_processor.py** - 视频处理
5. **table_processor.py** - 表格处理
6. **ocr_service.py** - OCR处理
7. **semantic_embedding.py** - 语义嵌入
8. **vectorization_service.py** - 向量化
9. **chunk_service.py** - 文档分块
10. **entity_extraction_service.py** - 实体提取
11. **keyword_extraction_service.py** - 关键词提取
12. **document_normalization/normalization_service.py** - 文档规范化
13. **knowledge_pipeline/orchestrator.py** - 知识流水线编排
14. **knowledge_pipeline/step1_cleaning.py** - 文本清洗
15. **knowledge_pipeline/step2_structure.py** - 结构分析

#### 植入模式
```python
from app.services.workflow_engine import workflow_engine, WorkflowDefinition

class DocumentProcessor:
    def process_document(self, doc_id: str, options: dict):
        # 定义工作流
        workflow = WorkflowDefinition(
            workflow_id=f"doc_process_{doc_id}",
            name="Document Processing Workflow"
        )
        
        # 添加任务节点
        workflow.add_task(
            task_id="extract_text",
            func=self._extract_text,
            args=(doc_id,),
            dependencies=[]
        )
        
        workflow.add_task(
            task_id="normalize",
            func=self._normalize_content,
            args=(doc_id,),
            dependencies=["extract_text"]
        )
        
        workflow.add_task(
            task_id="vectorize",
            func=self._vectorize_content,
            args=(doc_id,),
            dependencies=["normalize"]
        )
        
        # 执行工作流
        execution = workflow_engine.execute_workflow(workflow)
        return execution.result
```

---

### 阶段2: 知识图谱构建流 (P0, 半天)

#### 目标服务 (10个)
1. **knowledge_graph_service.py** - 知识图谱主服务
2. **neo4j_service.py** - Neo4j图数据库
3. **entity_relationship_service.py** - 实体关系
4. **timeline_service.py** - 时间线构建
5. **fact_federation_service.py** - 事实联邦
6. **knowledge_pipeline/step3_entity.py** - 实体提取
7. **knowledge_pipeline/step4_event.py** - 事件提取
8. **knowledge_pipeline/step5_relation.py** - 关系发现
9. **knowledge_pipeline/step6_ontology.py** - 本体构建
10. **knowledge_pipeline/step7_inference.py** - 逻辑推理

---

### 阶段3: 报告生成流 (P1, 半天)

#### 目标服务 (8个)
1. **report_generator.py** - 报告生成主服务
2. **three_layer_report_service.py** - 三层报告
3. **field_investigation_skill.py** - 田野调查技能
4. **xiangtu_china_skill.py** - 乡土中国技能
5. **social_memory_skill.py** - 社会记忆技能
6. **business_sop_skill.py** - 商业SOP技能
7. **commercial_feasibility_skill.py** - 商业可行性技能
8. **knowledge_pipeline/step9_reader.py** - Reader生成

---

### 阶段4: 分析与推荐流 (P1, 半天)

#### 目标服务 (7个)
1. **intelligent_agent.py** - 智能Agent
2. **enhanced_chat_service.py** - 增强对话
3. **rag_engine.py** - RAG检索
4. **recommendation_service.py** - 智能推荐
5. **analysis_service.py** - 数据分析
6. **topic_clustering_service.py** - 主题聚类
7. **tfidf_keyword_extractor.py** - TF-IDF提取

---

### 阶段5: 协作与权限流 (P2, 半天)

#### 目标服务 (5个)
1. **collaboration_service.py** - 协作服务
2. **permission_service.py** - 权限管理
3. **audit_service.py** - 审计日志
4. **notification_service.py** - 通知服务
5. **websocket_manager.py** - WebSocket管理

---

## 植入检查清单

### 每个服务需要完成
- [ ] 识别核心处理流程
- [ ] 拆分为独立任务节点
- [ ] 定义任务依赖关系
- [ ] 创建WorkflowDefinition
- [ ] 替换原有线性调用为workflow_engine.execute_workflow()
- [ ] 添加错误处理和重试逻辑
- [ ] 更新单元测试

### 质量标准
- 每个工作流至少包含3个任务节点
- 所有任务节点有明确的依赖关系
- 支持并行执行（无依赖的任务）
- 有完整的上下文传递
- 支持失败重试（retry_count > 0）

---

## 预期收益

### 性能提升
- **并行执行**: 无依赖任务自动并行，预计提速30-50%
- **资源利用**: 多worker并发，CPU利用率提升
- **失败恢复**: 自动重试机制，减少人工干预

### 可维护性
- **依赖可视化**: DAG图清晰展示任务依赖
- **模块解耦**: 任务节点独立，易于测试和替换
- **统一监控**: 所有工作流统一监控和日志

### 可扩展性
- **新功能**: 只需添加新任务节点，不影响现有流程
- **灵活组合**: 任务节点可重复使用，快速构建新工作流
- **动态调整**: 运行时调整任务顺序和依赖

---

## 执行时间表

| 阶段 | 目标服务数 | 预计时间 | 优先级 |
|------|-----------|---------|--------|
| 阶段1: 文档处理流 | 15个 | 1天 | P0 |
| 阶段2: 知识图谱流 | 10个 | 0.5天 | P0 |
| 阶段3: 报告生成流 | 8个 | 0.5天 | P1 |
| 阶段4: 分析推荐流 | 7个 | 0.5天 | P1 |
| 阶段5: 协作权限流 | 5个 | 0.5天 | P2 |
| **总计** | **45个** | **3天** | - |

### 覆盖率提升
- 当前: 3/304 = 1.6%
- 目标: 48/304 = 15.8%
- 扩展目标 (如果继续): >50% = 152+服务

---

## 风险与缓解

### 风险1: 破坏现有功能
**缓解**: 
- 每个服务修改后立即测试
- 保留原有实现作为fallback
- 分阶段部署，逐步验证

### 风险2: 性能回退
**缓解**:
- 对比植入前后性能指标
- 调整worker数量和并发度
- 监控内存和CPU使用

### 风险3: 复杂度增加
**缓解**:
- 提供清晰的文档和示例
- 标准化植入模式
- Code Review确保质量

---

## 下一步行动

1. **立即开始**: 阶段1 - 文档处理流 (15个服务)
2. **优先修改**: document_processor.py, knowledge_pipeline/orchestrator.py
3. **测试验证**: 每完成5个服务进行一次集成测试
4. **文档更新**: 记录每个工作流的DAG结构

---

**创建时间**: 2026-09-18 01:15  
**负责人**: Claude Code  
**状态**: 📋 计划完成，等待执行
