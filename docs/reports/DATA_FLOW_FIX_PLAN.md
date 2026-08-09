# FieldMind 数据流通修复方案

## 核心问题诊断

### 问题1：流水线孤立运行，功能不协同
**现状**：
- `background_tasks.py` 处理流程：文档提取 → 向量化 → 动态发现 → 完成
- 各功能独立完成后没有触发下一步深化
- 例如：提取实体后，不会自动构建知识图谱；知识图谱完成后，不会自动生成产业分析

**修复**：
1. 在 `background_tasks.py` 的 `process_document_async` 末尾添加工作流触发器
2. 文档处理完成 → 自动触发知识图谱构建
3. 知识图谱完成 → 自动触发产业分析生成
4. 产业分析完成 → 自动更新Dashboard统计

### 问题2：没有数据审核机制
**现状**：
- 第234行直接标记 `doc.status = "completed"`，没有验证
- AI生成的分析没有防幻觉检测
- 没有引用来源验证

**修复**：
1. 添加数据质量检查器 `DataQualityChecker`
2. 在标记completed前运行验证：
   - 检查是否有幻觉数字
   - 检查是否有引用来源
   - 检查实体是否来自原文
3. 如果验证失败，标记为 `review_needed` 而不是 `completed`
4. 前端显示时只展示 `quality_approved` 的数据

### 问题3：项目隔离不完全
**现状**：
- 中间件存在但不强制
- 很多查询没有加 `project_id` 过滤

**修复**：
1. 修改所有数据库查询，强制添加 `project_id` 过滤
2. 在 `background_tasks.py` 的所有查询加项目隔离
3. 确保知识图谱、实体、统计都按项目隔离

### 问题4：数据没有在各个板块流通
**现状**：
- 文档处理的结果存在 `project_documents` 表
- Dashboard、知识图谱、产业分析各自查询，但数据可能不一致

**修复**：
1. 添加数据同步机制
2. 文档处理完成后更新：
   - `projects` 表的统计字段
   - `entities` 表（用于知识图谱）
   - `fact_statements` 表（用于引用来源）
3. Dashboard从统一的聚合表读取，而不是实时计算

## 修复步骤

### Step 1: 添加数据质量检查器
文件：`app/services/data_quality_checker.py` (新建)

功能：
- 检测AI幻觉
- 验证引用来源
- 检查数据完整性

### Step 2: 修改 background_tasks.py
位置：第234行前

添加：
```python
# 数据质量检查
quality_checker = DataQualityChecker()
quality_result = quality_checker.check_document(doc, db)

if quality_result['passed']:
    doc.status = "completed"
    doc.quality_level = "approved"
else:
    doc.status = "review_needed"
    doc.quality_level = "pending_review"
    doc.extra_data['quality_issues'] = quality_result['issues']
```

### Step 3: 添加工作流触发器
位置：第255行后（处理完成后）

添加：
```python
# 自动触发下一阶段工作流
if doc.status == "completed" and doc.quality_level == "approved":
    trigger_next_workflows(doc, db)
```

### Step 4: 实现工作流串联函数
文件：`app/services/workflow_chain.py` (新建)

功能：
```python
def trigger_next_workflows(document, db):
    """
    文档处理完成后，自动触发：
    1. 知识图谱构建（如果项目有5+个文档）
    2. 产业分析生成（如果知识图谱已完成）
    3. Dashboard统计更新
    """
```

### Step 5: 强制项目隔离
修改所有查询：
- `app/api/v1/project_documents.py` - 所有查询加 `project_id`
- `app/services/knowledge_graph_service.py` - 查询加 `project_id`
- `app/main.py` 兼容路由 - 确保所有统计查询隔离

### Step 6: 数据流通打通
在 `trigger_next_workflows` 中实现：
1. 更新 `projects` 表统计
2. 同步到 `entities` 表
3. 生成 `fact_statements`
4. 刷新Dashboard缓存

## 预期效果

修复后的流程：
```
用户上传文档
  ↓
[后台处理] 提取文本、向量化、实体识别
  ↓
[数据质量检查] 防幻觉、验证来源
  ↓ (如果通过)
标记为 completed + approved
  ↓
[自动触发] 更新项目统计
  ↓
[自动触发] 构建知识图谱（如果达到阈值）
  ↓
[自动触发] 生成产业分析
  ↓
[自动触发] 刷新Dashboard
  ↓
前端显示最新数据
```

每一步都：
✅ 项目隔离
✅ 数据验证
✅ 自动深化
✅ 全局流通
