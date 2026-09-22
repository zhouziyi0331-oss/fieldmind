# 知识脉络和在地业态分析 - 完整实施指南

## 📋 目录

1. [系统概述](#系统概述)
2. [已完成的功能](#已完成的功能)
3. [快速启动](#快速启动)
4. [API 文档](#api-文档)
5. [数据增强说明](#数据增强说明)
6. [前端使用指南](#前端使用指南)
7. [配置和定制](#配置和定制)
8. [故障排查](#故障排查)

---

## 系统概述

### 核心价值

**知识脉络**：把"散落的关键词"变成"可探索的知识结构"
- 自动从材料中提取 6 个大脉络（文化传承、经济结构、社会组织、政策支持、在地业态、历史脉络）
- 每个大脉络下自动聚合子脉络
- 基于真实文档交叉计算脉络间关联

**在地业态分析**：让"田野数据自己说话"，不是套话
- 现有业态得分 = 覆盖度(40%) + 情感值(30%) + 趋势(30%)
- 可能业态可行性 = 关键词频次(25%) + 情感值(20%) + 政策匹配(25%) + 资源可用性(30%)
- 每个推演都有材料依据，可溯源

---

## 已完成的功能

### ✅ 后端 API（7个端点）

1. **知识脉络全景** - `GET /api/v1/projects/{project_id}/knowledge-network`
2. **节点详情** - `GET /api/v1/projects/{project_id}/knowledge-network/nodes/{node_id}`
3. **现有业态分析** - `GET /api/v1/projects/{project_id}/business-analysis/existing`
4. **可能业态推演** - `GET /api/v1/projects/{project_id}/business-analysis/potential`
5. **AI 综合评估** - `POST /api/v1/projects/{project_id}/business-analysis/ai-evaluation`
6. **数据增强** - `POST /api/v1/projects/{project_id}/enrich`
7. **增强状态查询** - `GET /api/v1/projects/{project_id}/enrichment-status`

### ✅ 前端页面（2个完整页面）

1. **知识脉络页面** (`KnowledgeNetworkView.swift`)
   - 顶部统计卡片
   - 网络节点可视化
   - 点击节点展开侧边详情面板

2. **在地业态分析页面** (`BusinessAnalysisView.swift`)
   - Tab 1: 现有业态（评分卡片 + 可持续性进度条）
   - Tab 2: 可能业态（可行性评分 + 推演逻辑）
   - Tab 3: AI 综合评估（评估文本 + 建议 + 风险）

### ✅ 数据增强服务

- **自动 NLP 处理** (`KnowledgeEnhancementService`)
  - 自动分类到 6 个大脉络
  - 提取关键词和实体（使用 jieba 分词）
  - 提取时空上下文
  - 计算情感极性

- **示例数据生成**
  - 如果项目没有数据，自动创建 12 条示例 chunks
  - 示例数据涵盖所有 6 个大脉络

### ✅ 业态数据库配置

- **8 个现有业态**：传统农业、蜡染手工艺、外出务工、民宿旅游、传统节庆、特色种养、农家乐、电商销售
- **20+ 个可能业态推演规则**：涵盖山歌、蜡染、节庆、传承人、民宿、农产品、合作社等关键词

---

## 快速启动

### 1. 安装依赖

```bash
cd /Users/alwan/FieldMind/backend/src

# 安装 Python 依赖
pip install jieba sqlalchemy fastapi uvicorn
```

### 2. 启动后端服务

```bash
cd /Users/alwan/FieldMind/backend/src
python api_server.py
```

服务启动后，访问：
- API 文档: http://localhost:8000/docs
- 主页: http://localhost:8000

### 3. 运行测试脚本

```bash
cd /Users/alwan/FieldMind
chmod +x test_knowledge_business.sh
./test_knowledge_business.sh
```

### 4. 启动前端应用

```bash
cd /Users/alwan/FieldMind/frontend/fieldmind-native
swift build
open FieldMind.app  # 或通过 Xcode 运行
```

---

## API 文档

### 1. 数据增强（必须先执行）

#### POST `/api/v1/projects/{project_id}/enrich`

**功能**：为项目自动补充 NLP 增强数据

**请求示例**：
```bash
curl -X POST http://localhost:8000/api/v1/projects/1/enrich
```

**响应示例**：
```json
{
  "success": true,
  "data": {
    "message": "数据增强完成",
    "created_chunks": 12,
    "enrichment_stats": {
      "total": 12,
      "enriched": 12,
      "skipped": 0
    }
  }
}
```

### 2. 知识脉络全景

#### GET `/api/v1/projects/{project_id}/knowledge-network`

**响应示例**：
```json
{
  "success": true,
  "data": {
    "statistics": {
      "dimension_count": 6,
      "sub_dimension_count": 12,
      "material_count": 12,
      "keyword_count": 45
    },
    "nodes": [
      {
        "id": 1,
        "name": "文化传承",
        "type": "dimension",
        "category": "文化传承",
        "material_count": 3,
        "chunk_count": 3,
        "keyword_count": 8,
        "sub_dimension_count": 2,
        "color": "#FF6B6B",
        "size": 130
      }
    ],
    "edges": [
      {
        "source": 1,
        "target": 2,
        "weight": 3,
        "label": "3份材料"
      }
    ]
  }
}
```

### 3. 现有业态分析

#### GET `/api/v1/projects/{project_id}/business-analysis/existing`

**响应示例**：
```json
{
  "success": true,
  "data": {
    "businesses": [
      {
        "name": "传统农业",
        "description": "以山地种植为主的传统农业生产",
        "score": 62.5,
        "sustainability": 62.5,
        "coverage": 58.3,
        "emotion": 45.0,
        "trend": 40.0,
        "frequency": 7,
        "tags": ["核心业态"],
        "supporting_materials": [...],
        "material_count": 2
      }
    ]
  }
}
```

### 4. 可能业态推演

#### GET `/api/v1/projects/{project_id}/business-analysis/potential`

**响应示例**：
```json
{
  "success": true,
  "data": {
    "potential_businesses": [
      {
        "name": "山歌研学营",
        "description": "以布依族山歌为核心的文化研学体验",
        "feasibility_score": 82.0,
        "keyword_frequency": 5,
        "emotion_score": 55.0,
        "policy_support": 45.0,
        "resource_availability": 60.0,
        "reasoning": "关键词「山歌」在材料中出现 5 次，结合传承人、传统、非遗等要素...",
        "supporting_materials": [...],
        "base_keyword": "山歌",
        "material_count": 2
      }
    ]
  }
}
```

### 5. AI 综合评估

#### POST `/api/v1/projects/{project_id}/business-analysis/ai-evaluation`

**请求体**：
```json
{
  "business_type": "existing",
  "business_name": "传统农业"
}
```

**响应示例**：
```json
{
  "success": true,
  "data": {
    "evaluation": "「传统农业」具备一定的发展基础，但需要注意风险。\n\n基于 2 份材料的交叉分析...",
    "suggestions": [
      "建议先进行小规模试点，验证市场反馈后再扩大规模。"
    ],
    "risks": [
      "⚠️ 支撑材料较少，建议补充更多调研数据。"
    ],
    "data_evidence": {
      "material_count": 2,
      "score": 62.5,
      "supporting_materials": [...]
    }
  }
}
```

---

## 数据增强说明

### 自动分类规则

系统会根据文本内容自动分类到 6 个大脉络：

| 大脉络 | 关键词示例 | 子脉络示例 |
|--------|-----------|-----------|
| 文化传承 | 文化、传统、习俗、非遗、山歌、蜡染 | 山歌传承、手工艺、传统节庆 |
| 经济结构 | 经济、收入、生计、农业、土地、务工 | 传统农业、外出务工、土地流转 |
| 社会组织 | 村委会、党支部、合作社、组织、治理 | 村级组织、经济组织、群众组织 |
| 政策支持 | 政策、政府、支持、扶贫、补贴、项目 | 乡村振兴、脱贫攻坚、文化保护 |
| 在地业态 | 业态、经营、产业、民宿、餐饮、文创 | 民宿旅游、餐饮服务、手工艺品 |
| 历史脉络 | 历史、过去、祖先、传说、迁徙、由来 | 迁徙历史、发展沿革、历史事件 |

### 实体提取

使用 jieba 分词自动提取：
- **人名** (nr)：传承人、村长、书记
- **地名** (ns)：村寨、县城、景点
- **组织** (nt)：村委会、合作社、协会
- **概念** (nz)：山歌、蜡染、节日

### 情感分析

根据正面词和负面词计算情感极性（-1 到 1）：
- **正面词**：好、发展、增长、改善、提升、成功、繁荣
- **负面词**：难、困难、问题、减少、衰退、流失、断层

---

## 前端使用指南

### 知识脉络页面

1. **查看统计概览**
   - 顶部显示 4 个统计卡片：大脉络数、子脉络数、支撑材料数、关键词数

2. **浏览知识网络**
   - 节点以网格形式展示
   - 节点大小表示材料数量
   - 节点颜色表示脉络类型

3. **查看详情**
   - 点击任意节点
   - 右侧展开详情面板
   - 显示：关键词列表、子脉络、关联脉络、核心议题、材料列表

### 在地业态分析页面

#### Tab 1: 现有业态

- **业态卡片**：显示业态名称、评分、描述
- **评分圆环**：直观显示综合得分（0-100）
- **指标条**：覆盖度、情感值、趋势
- **支撑材料**：显示材料数量
- **查看AI评估**：点击按钮切换到 AI 评估页

#### Tab 2: 可能业态

- **业态卡片**：显示业态名称、可行性评分、描述
- **推演逻辑**：显示为什么推荐这个业态
- **可行性指标**：情感、政策、资源三个维度
- **依据材料**：显示支撑材料数量

#### Tab 3: AI 综合评估

- **评估文本**：基于数据的综合分析
- **建议列表**：具体的实施建议
- **风险提示**：需要注意的风险点
- **数据依据**：支撑材料数量和综合得分
- **导出报告**：一键导出分析报告（待实现）

---

## 配置和定制

### 1. 修改业态数据库

编辑文件：`/Users/alwan/FieldMind/backend/src/app/config/business_database.py`

#### 添加新的现有业态

```python
EXISTING_BUSINESS_DATABASE = {
    "你的业态名称": {
        "keywords": ["关键词1", "关键词2", "关键词3"],
        "description": "业态描述",
        "sustainability_factors": {
            "positive": ["正面因素1", "正面因素2"],
            "negative": ["负面因素1", "负面因素2"]
        }
    },
    # ... 其他业态
}
```

#### 添加新的业态推演规则

```python
POTENTIAL_BUSINESS_RULES = {
    "触发关键词": {
        "trigger_frequency": 5,  # 至少出现次数
        "potential_businesses": [
            {
                "name": "业态名称",
                "description": "业态描述",
                "base_score": 75,
                "required_keywords": ["必需关键词1", "必需关键词2"],
                "supporting_factors": ["支撑因素1", "支撑因素2"],
                "implementation_difficulty": "中等",
                "investment_range": "10-30万元",
                "return_cycle": "2-3年",
                "key_resources": ["资源1", "资源2"]
            }
        ]
    }
}
```

### 2. 调整权重配置

```python
# 可行性评估权重
FEASIBILITY_WEIGHTS = {
    "keyword_frequency": 0.25,      # 关键词频次权重
    "emotion_score": 0.20,          # 情感倾向权重
    "policy_support": 0.25,         # 政策支持权重
    "resource_availability": 0.30   # 资源可用性权重
}

# 可持续性评估权重
SUSTAINABILITY_WEIGHTS = {
    "coverage": 0.35,    # 覆盖度权重
    "emotion": 0.35,     # 情感倾向权重
    "trend": 0.30        # 时间趋势权重
}
```

### 3. 扩展领域分类

编辑文件：`/Users/alwan/FieldMind/backend/src/app/services/knowledge_enhancement_service.py`

在 `DOMAIN_KEYWORDS` 字典中添加新的领域：

```python
DOMAIN_KEYWORDS = {
    "新领域名称": {
        "keywords": ["关键词1", "关键词2", ...],
        "subcategories": {
            "子类别1": ["关键词1", "关键词2"],
            "子类别2": ["关键词3", "关键词4"]
        }
    },
    # ... 其他领域
}
```

---

## 故障排查

### 问题1：API 返回空数据

**原因**：项目没有 chunks 数据

**解决方案**：
```bash
# 执行数据增强，会自动创建示例数据
curl -X POST http://localhost:8000/api/v1/projects/1/enrich
```

### 问题2：分类不准确

**原因**：关键词库不完整或权重不合适

**解决方案**：
1. 检查 `knowledge_enhancement_service.py` 中的 `DOMAIN_KEYWORDS`
2. 添加更多领域特定的关键词
3. 调整分类逻辑的权重

### 问题3：业态推演没有结果

**原因**：关键词出现频次不足

**解决方案**：
1. 降低 `trigger_frequency` 阈值（默认 5 次）
2. 添加更多同义词到 `required_keywords`
3. 检查材料中是否真的包含相关内容

### 问题4：前端无法加载数据

**原因**：API 地址配置错误

**解决方案**：
检查 `APIConfig.baseURL` 是否正确：
- `KnowledgeNetworkViewModel.swift`
- `BusinessAnalysisViewModel.swift`

默认地址：`http://localhost:8000`

### 问题5：中文分词效果不好

**原因**：jieba 默认词典不包含领域词汇

**解决方案**：
系统已自动加载自定义词典（在 `_load_custom_dict` 方法中）。如需添加更多词汇：
```python
jieba.add_word("你的专业词汇")
```

---

## 性能优化建议

1. **批量处理**：数据增强使用批量处理（默认 100 条/批）
2. **缓存结果**：知识网络API 可以添加缓存（TTL 5-10 分钟）
3. **异步处理**：大项目的数据增强可以改为异步任务
4. **索引优化**：为 `domain_tags` 和 `key_entities` 字段添加 JSON 索引

---

## 后续扩展建议

1. **可视化增强**
   - 使用 D3.js 实现真正的力导向图
   - 添加节点拖拽和缩放功能
   - 支持按时间轴动态展示脉络演变

2. **AI 能力提升**
   - 集成真实的 LLM API（如 OpenAI、Claude）
   - 使用更专业的 NLP 模型（如 BERT、RoBERTa）
   - 添加实体关系抽取

3. **业态数据库扩展**
   - 支持从外部配置文件加载业态规则
   - 添加业态成功案例库
   - 集成外部市场数据

4. **报告生成**
   - 实现分析报告导出（PDF/Word）
   - 添加可视化图表导出
   - 支持自定义报告模板

5. **多项目对比**
   - 跨项目的业态对比分析
   - 区域业态热力图
   - 最佳实践推荐

---

## 联系和支持

如有问题，请检查：
1. 后端日志：`/Users/alwan/FieldMind/backend/src/logs/`
2. API 文档：http://localhost:8000/docs
3. 测试脚本输出

---

**🎉 恭喜！你已经完成了知识脉络和在地业态分析系统的部署！**
