# RAG系统和技能系统整合规划

**日期**: 2026-08-29  
**任务**: Phase 3 - RAG系统和技能系统完整整合  
**预计时间**: 4-6小时

---

## 📋 现状分析

### RAG系统现有模块
1. `rag_engine.py` - 基础RAG引擎（ChromaDB + HuggingFace）
2. `lightrag_service.py` - LightRAG知识图谱
3. `graphrag_service.py` - GraphRAG多尺度图谱
4. `ragflow_service.py` - RAGFlow服务
5. `deep_rag_service.py` - 深度RAG
6. `rag_retrieval_service.py` - RAG检索服务
7. `rag_engine_adapter.py` - RAG引擎适配器

### 技能系统现有模块
1. `unified_skills_service.py` - 统一技能服务（已有）
2. `skill_generator.py` - 技能生成器
3. `skill_optimizer.py` - 技能优化器
4. `skill_evolution_service.py` - 技能进化服务
5. `skill_sandbox.py` - 技能沙盒
6. `skills_integration_service.py` - 技能集成服务

### 已完成的相关模块
- ✅ `skill_chat_adapter.py` - 技能对话适配器（Day 1）
- ✅ `memory_aggregator.py` - 8源记忆整合（Day 1）

---

## 🎯 整合目标

### 1. 统一RAG引擎 (UnifiedRAGEngine)
**目标**: 整合所有RAG服务到统一接口

**功能**:
- 多源RAG整合（LightRAG, GraphRAG, RAGFlow等）
- 智能路由（根据查询类型选择最佳RAG）
- 结果融合和排序
- 缓存机制
- 性能监控

**输入**:
```python
{
    'query': str,
    'sources': ['lightrag', 'graphrag', 'base'],
    'mode': 'hybrid',  # local/global/hybrid
    'top_k': int,
    'project_id': int
}
```

**输出**:
```python
{
    'results': [...],
    'sources_used': [...],
    'processing_time': float,
    'metadata': {...}
}
```

### 2. 统一技能系统 (UnifiedSkillSystem)
**目标**: 整合手动技能和自动生成技能

**功能**:
- 技能注册和管理
- 技能生成（从执行追踪）
- 技能优化
- 技能版本管理
- 技能沙盒执行
- 技能推荐

**组件**:
- SkillRegistry - 技能注册中心
- SkillGenerator - 技能生成器
- SkillOptimizer - 技能优化器
- SkillExecutor - 技能执行器

### 3. RAG + 技能集成
**目标**: RAG检索结果驱动技能选择

**场景**:
1. 用户查询 → RAG检索 → 根据结果推荐技能
2. 技能执行 → RAG增强 → 更好的执行结果
3. 技能生成 → 从RAG知识中学习

---

## 📐 架构设计

```
UnifiedAIService
├─ chat (Enhanced Chat V2) ✅
├─ agents (Super Agents V2) ✅
├─ rag (Unified RAG Engine) ⬅️ 新增
│   ├─ BaseRAG
│   ├─ LightRAG
│   ├─ GraphRAG
│   ├─ RAGFlow
│   ├─ DeepRAG
│   └─ RAGRouter (智能路由)
└─ skills (Unified Skill System) ⬅️ 新增
    ├─ SkillRegistry
    ├─ SkillGenerator
    ├─ SkillOptimizer
    ├─ SkillExecutor
    └─ SkillRecommender
```

---

## 🔧 实现步骤

### Step 1: 分析现有代码（1小时）
- [ ] 深度分析rag_engine.py
- [ ] 深度分析lightrag_service.py
- [ ] 深度分析graphrag_service.py
- [ ] 深度分析unified_skills_service.py
- [ ] 深度分析skill_generator.py
- [ ] 识别核心功能和冗余代码

### Step 2: 创建UnifiedRAGEngine（2小时）
- [ ] 创建BaseRAGInterface抽象类
- [ ] 创建RAGRouter智能路由器
- [ ] 整合LightRAG
- [ ] 整合GraphRAG
- [ ] 整合基础RAG引擎
- [ ] 实现结果融合算法
- [ ] 实现缓存机制

### Step 3: 完善UnifiedSkillSystem（1.5小时）
- [ ] 扩展现有unified_skills_service
- [ ] 整合skill_generator
- [ ] 整合skill_optimizer
- [ ] 实现技能版本管理
- [ ] 实现技能推荐引擎

### Step 4: RAG-Skill集成（1小时）
- [ ] RAG结果驱动技能推荐
- [ ] 技能执行的RAG增强
- [ ] 从RAG知识学习生成技能

### Step 5: 测试和优化（0.5小时）
- [ ] 单元测试
- [ ] 集成测试
- [ ] 性能优化

---

## 📊 预期成果

### 代码量
- UnifiedRAGEngine: ~800行
- RAGRouter: ~300行
- UnifiedSkillSystem扩展: ~500行
- 集成层: ~200行
- 测试: ~400行
- **总计**: ~2,200行

### 文件清单
1. `app/core/unified_rag_engine.py` - 统一RAG引擎
2. `app/core/rag_router.py` - RAG路由器
3. `app/services/unified_skill_system_v2.py` - 统一技能系统V2
4. `app/core/rag_skill_integration.py` - RAG-技能集成层
5. `tests/test_rag_integration.py` - RAG测试
6. `tests/test_skill_system_integration.py` - 技能系统测试

### 文档
1. `RAG_SYSTEM_INTEGRATION_COMPLETE.md` - RAG整合报告
2. `SKILL_SYSTEM_INTEGRATION_COMPLETE.md` - 技能系统整合报告

---

## 🎨 设计原则

1. **统一接口** - 所有RAG源实现相同接口
2. **智能路由** - 根据查询自动选择最佳RAG
3. **结果融合** - 多源结果智能融合
4. **性能优先** - 缓存、并行、异步
5. **可扩展** - 新RAG源只需实现接口
6. **完整保留** - 不删除任何有用功能

---

## 🚀 开始执行

准备好开始第一步：**分析现有代码**

您准备好了吗？
