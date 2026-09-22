# P1 优先级任务执行计划

**开始时间**: 2026-09-09  
**预计时间**: 6-8 小时

---

## 🎯 P1 任务概览

| 任务 | 完成度 | 缺失内容 | 优先级 |
|------|--------|---------|--------|
| P1-1: 知识脉络可视化 | 42% | build_knowledge_graph, extract_relations, 前端页面 | 最高 |
| P1-2: 三层报告生成 | 66% | level1_report, level3_report | 高 |

---

## 📋 P1-1: 理解层知识脉络

### 目标
从 chunks 表自动聚合出知识图谱，在前端用力导向图展示

### 需要补充

#### 后端（3 小时）
1. **完善 `knowledge_graph_service.py`**
   - ✅ 已有：extract_entities()
   - ❌ 缺失：build_knowledge_graph()
   - ❌ 缺失：extract_relations()

2. **创建 `keyword_extraction.py`**
   - ❌ 整个文件缺失
   - 需要：extract_keywords() - TF-IDF 提取

3. **API 端点**
   - GET /api/v1/knowledge-graph/{project_id}
   - 返回节点和边的数据

#### 前端（2 小时）
4. **KnowledgeNetworkView 增强**
   - 集成 D3.js 力导向图
   - 交互：点击节点展开详情
   - 侧边面板：显示支撑材料

---

## 📋 P1-2: 分析层三层报告

### 目标
完整实现三层报告生成和展示

### 需要补充

#### 后端（2 小时）
1. **完善 `reports_real.py`**
   - ✅ 已有：generate_level2_report()
   - ❌ 缺失：generate_level1_report() - 事实报告
   - ❌ 缺失：generate_level3_report() - 商业报告

2. **报告模板**
   - Level 1: 时间线、人物、事件、地点
   - Level 3: 可行性评估、行动建议

#### 前端（1 小时）
3. **ReportView 增强**
   - 三层报告可展开/收起
   - 可单独下载
   - 生成进度显示

---

## 🚀 执行顺序

### 第一步: P1-1 后端（3 小时）
1. 创建 `keyword_extraction.py`
2. 完善 `knowledge_graph_service.py`
3. 添加 API 端点

### 第二步: P1-2 后端（2 小时）
4. 实现 level1_report
5. 实现 level3_report

### 第三步: 前端集成（3 小时）
6. 知识脉络 D3.js 可视化
7. 三层报告页面

---

## 📊 数据流设计

### 知识脉络数据流
```
chunks 表
  ↓
keyword_extraction.extract_keywords()
  ↓ 写入
keywords 表
  ↓
knowledge_graph_service.build_knowledge_graph()
  ↓ 聚合
{
  "nodes": [
    {"id": "文化传承", "type": "dimension", "count": 45},
    {"id": "非遗保护", "type": "sub_dimension", "count": 23}
  ],
  "edges": [
    {"source": "文化传承", "target": "非遗保护", "weight": 0.8}
  ]
}
  ↓
前端 D3.js 渲染
```

### 三层报告数据流
```
项目 ID
  ↓
generate_level1_report()
  ├─ 查询 chunks 按时间排序
  ├─ 提取人物、事件、地点
  └─ 生成时间线
  ↓
generate_level2_report()
  ├─ 调用 Skill（费孝通框架）
  └─ 输出理论分析
  ↓
generate_level3_report()
  ├─ 调用商业 Skill
  └─ 输出可行性评估
```

---

## 🧪 验证标准

### P1-1 验证
- [ ] 上传文档后自动提取关键词
- [ ] keywords 表有数据
- [ ] 知识图谱 API 返回节点和边
- [ ] 前端能显示力导向图
- [ ] 点击节点能看到详情

### P1-2 验证
- [ ] 三层报告都能生成
- [ ] Level 1 有时间线和关键信息
- [ ] Level 2 有理论分析
- [ ] Level 3 有商业建议
- [ ] 前端能展开/收起/下载

---

**下一步**: 立即开始 P1-1 后端实现

是否开始执行？
