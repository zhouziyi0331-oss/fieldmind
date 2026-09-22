# FieldMind 系统现状诊断与补充计划

**检测时间**: 2026-09-09  
**整体完成度**: 47%

---

## 📊 六大层级现状

| 层级 | 完成度 | 关键缺失 |
|------|--------|---------|
| **复用层** | 80% | get_skill_by_name 函数 |
| **分析层** | 66% | level1/level3 报告生成 |
| **采集层** | 50% | 批量上传、文件上传服务 |
| **理解层** | 42% | 知识图谱构建、关系提取、关键词提取 |
| **处理层** | 33% | chunking_service、text_quantification |
| **协同层** | 14% | RAG 引擎、对话流、conversation 模型 |

---

## 🎯 P0 优先级任务（必须立即补）

### P0-1: 处理层闭环（完成度 33% → 100%）

**缺失模块**：
- ❌ `app/services/chunking_service.py` - 文本切分服务
- ❌ `app/services/text_quantification.py` - 文本量化服务

**已有模块**：
- ✅ `background_tasks.py` - 有 process_document_async
- ✅ `document_converter.py` - 文档转换

**需要补充**：
1. 创建 `chunking_service.py`
   - chunk_text() - 切分文本
   - create_chunks_from_document() - 从文档创建 chunks
   - 写入 chunks 表

2. 创建 `text_quantification.py`
   - quantify_text() - 计算 15+ 指标
   - calculate_sentiment() - 情感分析
   - 更新 chunks 表的量化字段

3. 修改 `background_tasks.py`
   - 集成 chunking_service
   - 集成 text_quantification
   - 完整的处理链路

---

### P0-2: 采集层批量上传（完成度 50% → 100%）

**缺失模块**：
- ❌ `app/services/file_upload_service.py` - 文件上传服务
- ❌ `documents.py` 中的 upload_documents_batch()

**已有模块**：
- ✅ `documents.py` - 有 upload_document (单文件)

**需要补充**：
1. 创建 `file_upload_service.py`
   - 批量上传处理
   - 文件队列管理
   - 自动触发处理

2. 在 `documents.py` 添加
   - upload_documents_batch() API 端点
   - 支持 50+ 文件同时上传

---

## 🎯 P1 优先级任务（核心差异化）

### P1-1: 理解层知识脉络（完成度 42% → 100%）

**缺失功能**：
- ❌ `knowledge_graph_service.py` 中的：
  - build_knowledge_graph() - 构建知识图谱
  - extract_relations() - 关系提取
- ❌ `keyword_extraction.py` - 整个文件缺失

**已有模块**：
- ✅ `knowledge_graph_service.py` - 有 extract_entities
- ✅ `entity_extraction.py`

**需要补充**：
1. 创建 `keyword_extraction.py`
   - extract_keywords() - TF-IDF 关键词提取
   - 写入 keywords 表

2. 完善 `knowledge_graph_service.py`
   - build_knowledge_graph() - 从 chunks 聚合图谱
   - extract_relations() - 提取实体关系

3. 前端：知识脉络页面
   - D3.js 力导向图
   - 大脉络/子脉络展示

---

### P1-2: 分析层三层报告（完成度 66% → 100%）

**缺失功能**：
- ❌ `reports_real.py` 中的：
  - generate_level1_report() - 事实报告
  - generate_level3_report() - 商业报告

**已有模块**：
- ✅ generate_level2_report() - 洞察报告
- ✅ business_analysis_service.py

**需要补充**：
1. 实现 `generate_level1_report()`
   - 时间线、人物、事件、地点
   - 纯事实，不分析

2. 实现 `generate_level3_report()`
   - 商业可行性评估
   - 行动建议

3. 报告展示页面
   - 三层报告可展开/收起
   - 可下载 HTML

---

## 🎯 P2 优先级任务（可信度和复用性）

### P2-1: 协同层 RAG 引擎（完成度 14% → 100%）

**缺失模块**：
- ❌ `app/services/rag_engine.py` - 整个文件缺失
- ❌ `app/models/conversation.py` - 整个文件缺失
- ❌ `chat.py` 中的 chat() 和 chat_stream()

**需要补充**：
1. 创建 `rag_engine.py`
   - search_relevant_chunks() - 向量检索
   - build_context() - 构建上下文
   - 溯源信息绑定

2. 创建 `conversation.py` 模型
   - 对话历史记录
   - 溯源链路

3. 完善 `chat.py`
   - chat() - 对话接口
   - chat_stream() - 流式输出

---

### P2-2: 溯源回溯完整链路

**需要补充**：
1. 数据库字段
   - chunks 表添加 source_file_id, timestamp
   - reports 表添加 source_chunk_ids

2. 后端 API
   - /api/trace/{conclusion_id} - 追溯结论来源

3. 前端
   - 点击结论 → 展开溯源树

---

## 📅 执行计划

### 第一周（P0）
- Day 1-2: 处理层闭环（chunking + quantification）
- Day 3-4: 采集层批量上传
- Day 5: 测试验证

### 第二周（P1）
- Day 1-2: 理解层知识脉络
- Day 3-4: 分析层三层报告
- Day 5: 测试验证

### 第三周（P2）
- Day 1-3: 协同层 RAG 引擎
- Day 4-5: 溯源回溯链路

---

## 🔧 架构设计原则

### 通用化设计
- 处理引擎不绑定"田野调查"领域
- 实体类型可配置（人物/事件/地点/组织...）
- 报告模板可切换

### 扩展接口预留
- 工作流模板化
- Skill 系统可配置
- 外部数据源接入能力

---

**下一步**: 请确认是否立即开始执行 P0-1（处理层闭环）
