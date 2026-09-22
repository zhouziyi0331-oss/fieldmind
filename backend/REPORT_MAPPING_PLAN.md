# 报告映射功能实施计划

## 📋 当前状态

### ✅ 已有基础设施
1. **数据模型**: 
   - `analysis_reports` 表 (三层报告系统: tier1/tier2/tier3)
   - `reports` 表 (通用报告: research/summary/analysis)
   
2. **报告生成器**:
   - `three_layer_report_system.py` - Level 1/3 生成器
   - Level 1: 事实层 (时间线、人物、事件、地点)
   - Level 3: 商业层 (SWOT、可行性、行动计划)
   - **缺失**: Level 2 (洞察层) 只有占位符

3. **相关服务**:
   - `dynamic_report_generator.py`
   - `report_governance_summary_generator.py`
   - `report_template_system.py`
   - `llm_report_generator.py`

### ❌ 缺失部分
- **报告与文档的映射关系**: 没有独立的映射表或清晰的查询逻辑
- **报告与编年史/关键词的集成**: 未连接已实现的 timeline_events 和 document_keywords
- **Level 2 洞察层**: 理论分析、模式发现功能未实现

---

## 🎯 实施目标

### 阶段 1: 核心映射关系 (30分钟)
建立报告与文档、编年史、关键词之间的清晰映射

**任务**:
1. **验证现有映射字段**
   - `analysis_reports.document_ids` (JSON)
   - `analysis_reports.entity_ids` (JSON)
   - `reports.data_sources` (JSON: document_ids, categories)
   
2. **创建映射查询服务** `report_mapping_service.py`
   ```python
   class ReportMappingService:
       def get_report_documents(report_id) -> List[Document]
       def get_report_timeline_events(report_id) -> List[TimelineEvent]
       def get_report_keywords(report_id) -> List[DocumentKeyword]
       def get_document_reports(document_id) -> List[Report]
   ```

3. **增强报告生成器** - 集成编年史和关键词
   - Level 1: 使用 `timeline_events` 表生成时间线（替代当前文档上传时间）
   - Level 1: 使用 `document_keywords` 表生成关键主题
   - Level 3: 使用关键词权重分析优势/劣势

**产出**:
- `report_mapping_service.py` (新建)
- `three_layer_report_system.py` (增强)
- 映射关系测试脚本

---

### 阶段 2: 验证三个报告 (检查实际内容)
检查 Level 1/2/3 报告生成器的实际输出质量

**任务**:
1. **生成测试报告** - 针对项目1（36个文档）
   ```bash
   python test_three_layer_report.py --project-id 1
   ```

2. **验证数据完整性**
   - Level 1: 时间线是否包含真实的 timeline_events？
   - Level 1: 关键人物是否来自知识图谱 entities？
   - Level 3: SWOT 分析是否有实际内容还是占位符？

3. **补充缺失功能**
   - 如果 Level 2 完全缺失 → 实现基础版本
   - 如果 Level 3 只有硬编码示例 → 改为数据驱动

**产出**:
- 测试报告生成脚本
- 功能补全清单
- 示例报告输出 (JSON/Markdown)

---

### 阶段 3: Level 2 洞察层实现 (可选扩展)
如果 Level 2 完全缺失或不可用

**任务**:
1. **模式发现**
   - 高频关键词组合分析
   - 时间线事件聚类（按类型、时间段）
   - 实体关系网络中的中心节点

2. **理论分析框架**
   - 费孝通差序格局分析（如果适用于人类学项目）
   - 通用 SOP 分析框架

**产出**:
- `Level2ReportGenerator` 类实现
- 与 Level 1/3 集成

---

## 📊 数据流设计

```
文档上传
  ↓
[文档处理流水线]
  ├─ 阶段6: 编年史提取 → timeline_events 表
  ├─ 阶段7: 关键词提取 → document_keywords 表
  └─ 知识图谱构建 → entities, relationships 表
  ↓
[报告生成]
  ├─ Level 1 (事实层)
  │   ├─ 读取: timeline_events (真实时间线)
  │   ├─ 读取: entities (人物/地点)
  │   └─ 读取: document_keywords (关键主题)
  │
  ├─ Level 2 (洞察层)
  │   ├─ 分析: 关键词共现模式
  │   ├─ 分析: 事件时序关系
  │   └─ 发现: 实体关系网络
  │
  └─ Level 3 (商业层)
      ├─ SWOT: 基于关键词权重和实体频次
      ├─ 可行性: 基于数据完整性和实体覆盖度
      └─ 行动计划: 基于时间线阶段划分
```

---

## ✅ 验收标准

### 阶段 1
- [ ] `ReportMappingService` 可查询报告的所有关联数据
- [ ] 生成的 Level 1 报告包含真实的 timeline_events（非文档上传时间）
- [ ] 生成的 Level 1 报告包含 document_keywords 关键主题摘要

### 阶段 2
- [ ] 成功生成项目1的完整三层报告
- [ ] Level 1 包含 79 个真实时间线事件
- [ ] Level 1 包含 Top 20 关键词（从 858 个中提取）
- [ ] Level 3 SWOT 分析基于真实数据（非硬编码示例）

### 阶段 3 (可选)
- [ ] Level 2 实现至少 2 种模式分析
- [ ] Level 2 生成 5+ 条洞察

---

## 🕐 时间估算

| 阶段 | 任务 | 预计时间 |
|-----|------|---------|
| 1.1 | 验证映射字段 | 5分钟 |
| 1.2 | 实现 ReportMappingService | 15分钟 |
| 1.3 | 增强 Level 1 生成器 | 10分钟 |
| 2.1 | 生成测试报告 | 5分钟 |
| 2.2 | 验证输出质量 | 10分钟 |
| 2.3 | 补充缺失功能 | 10分钟 |
| 3   | Level 2 实现（可选） | 30-60分钟 |

**总计**: 55分钟（不含 Level 2）或 85-115分钟（含 Level 2）

---

## 🚀 下一步行动

### 立即开始
```bash
# 1. 验证数据库状态
sqlite3 fieldmind.db "SELECT COUNT(*) FROM timeline_events"
sqlite3 fieldmind.db "SELECT COUNT(*) FROM document_keywords"

# 2. 检查报告表结构
sqlite3 fieldmind.db ".schema analysis_reports"

# 3. 创建映射服务
# 实现 report_mapping_service.py
```

### 待确认
- 是否需要实现完整的 Level 2 洞察层？
- 报告导出格式优先级：JSON / Markdown / HTML / DOCX？
- 是否需要报告版本管理（同一数据源生成多次）？

---

## 📝 备注

**与编年史/关键词的关系**:
- 报告映射是**消费者**：读取编年史和关键词数据生成报告
- 不修改编年史/关键词功能，只添加查询和聚合逻辑

**与其他模块的依赖**:
- 依赖已完成：文档处理流水线、编年史提取、关键词提取
- 不依赖：插件系统、技能系统（报告生成独立运行）
