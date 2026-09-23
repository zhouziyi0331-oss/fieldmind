# FieldMind 蒸馏功能实现计划

## 一、核心理念

**蒸馏 ≠ 结构化**

| 层级 | 作用 | 产出 | 用户感受 |
|------|------|------|---------|
| 结构化 | 数据摆整齐 | chunks、entities、events | "数据整齐了，但我还得自己看" |
| **蒸馏** | **数据变智慧** | **洞察、原话、模型、建议** | **"它帮我读懂了，而且能直接用"** |

---

## 二、蒸馏的6类产物

### 1. 核心洞察 (Insight)
- **定义**: 从材料中提炼的关键结论
- **示例**: "土地流转是当前村落最核心的经济矛盾"
- **提取逻辑**: 高频关键词 + 情绪峰值 + 事件密度高的区域

### 2. 经典原话 (Quote)
- **定义**: 田野中最有代表性的原话
- **示例**: 王大爷："山歌是布依族的根，但年轻人不学了"
- **提取逻辑**: 包含核心实体 + 情绪强度高 + 有代表性表述

### 3. 思维模型 (Model)
- **定义**: 结合理论框架的分析逻辑
- **示例**: "用费孝通差序格局解释村民对土地流转的态度"
- **提取逻辑**: 调用理论 Skill + 匹配已有实体关系

### 4. 案例与应用 (Case)
- **定义**: 可迁移的实践案例
- **示例**: "山歌研学营：即兴对唱 → 沉浸式研学课程"
- **提取逻辑**: 匹配商业 Skill + 匹配可行性评分

### 5. 行动建议 (Action)
- **定义**: 基于洞察的具体行动
- **示例**: "优先推进山歌研学营，6个月内启动试点"
- **提取逻辑**: 缺口分析 + 趋势分析 + 优先级排序

### 6. 方法论沉淀 (Method)
- **定义**: 本次调研的方法可复用
- **示例**: "本次采用'三维度事件判定法'，建议下次沿用"
- **提取逻辑**: 记录本次使用的分析框架和参数

---

## 三、实现架构

### 3.1 数据流
```
原始文件
    ↓
【结构化层】chunks + entities + relations + events
    ↓
【蒸馏层】候选提取 → 价值判断 → 形式化 → 溯源绑定
    ↓
蒸馏产物 (6类知识单元)
    ↓
【应用层】报告生成 / 对话问答 / 资产沉淀
```

### 3.2 蒸馏引擎的5个步骤
1. **候选提取**: 用规则+LLM找出可能的蒸馏候选
2. **价值判断**: 这个候选值不值得蒸馏？
3. **形式化**: 把候选整理成标准格式的蒸馏单元
4. **溯源绑定**: 每个蒸馏单元绑定来源 chunk
5. **存储与索引**: 存入数据库，建立索引

---

## 四、数据库设计

### 4.1 蒸馏产物表
```sql
CREATE TABLE distilled_units (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    unit_type TEXT NOT NULL,              -- 'insight'/'quote'/'model'/'case'/'action'/'method'
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    source_chunks TEXT,                   -- JSON: [chunk_id1, chunk_id2, ...]
    credibility REAL,                     -- 可信度评分 0-1
    confidence REAL,                      -- 蒸馏置信度 0-1
    metadata TEXT,                        -- JSON: 额外元数据
    created_at TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);
```

### 4.2 蒸馏产物关联表
```sql
CREATE TABLE distilled_unit_relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    distilled_unit_id INTEGER NOT NULL,
    related_type TEXT NOT NULL,           -- 'entity'/'event'/'chunk'
    related_id INTEGER NOT NULL,
    relation_type TEXT,                   -- 'evidence'/'related'/'contradicts'
    strength REAL,                        -- 关联强度 0-1
    FOREIGN KEY (distilled_unit_id) REFERENCES distilled_units(id)
);
```

---

## 五、实现步骤

### Phase 1: 数据库与基础架构 (1-2小时)
- [ ] 创建数据表
- [ ] 创建蒸馏服务基础类
- [ ] 实现基本的CRUD操作

### Phase 2: 蒸馏引擎核心 (3-4小时)
- [ ] 实现核心洞察提取
- [ ] 实现经典原话提取
- [ ] 实现思维模型匹配
- [ ] 实现案例与应用生成
- [ ] 实现行动建议生成
- [ ] 实现方法论沉淀

### Phase 3: API端点 (1-2小时)
- [ ] POST /api/projects/{id}/distill - 启动蒸馏
- [ ] GET /api/projects/{id}/distilled-units - 获取蒸馏结果
- [ ] GET /api/distilled-units/{id} - 获取单个蒸馏产物
- [ ] GET /api/distilled-units/{id}/sources - 获取来源

### Phase 4: 前端展示 (2-3小时)
- [ ] 蒸馏结果页面
- [ ] 6类产物分类展示
- [ ] 溯源追踪功能
- [ ] 导出蒸馏报告

### Phase 5: 测试与优化 (1-2小时)
- [ ] 单元测试
- [ ] 集成测试
- [ ] 性能优化

---

## 六、验收标准

1. ✅ 完成一个项目后，可以启动蒸馏
2. ✅ 蒸馏页面显示6类产物
3. ✅ 每条产物可溯源到具体chunk和原始文件
4. ✅ 每条产物有可信度评分
5. ✅ 可一键沉淀到资产库
6. ✅ 蒸馏产物可在对话中被调用

---

## 七、预期效果

用户完成田野调研后：

```
之前：看到一堆结构化数据，"数据整齐了，但我还得自己看"
现在：看到提炼好的洞察、原话、建议，"它帮我读懂了，而且能直接用"
```

**这才是真正的智能！**

