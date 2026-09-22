# 三层递进报告生成系统 - 完整文档

## 📋 系统概述

FieldMind 三层递进报告生成系统是一个**数据驱动、反幻觉、智能化**的报告自动生成解决方案。系统基于已处理的田野调查数据，通过动态大纲生成、深度内容分析和严格引用验证，生成三个层次的专业报告。

### 核心特性

1. **数据驱动** - 基于关键词网络、实体关系、时间线等已处理数据动态生成报告
2. **反幻觉机制** - 每个观点必须有原文引用，所有数字可追溯来源
3. **三层递进** - 从客观呈现到理论分析再到商业决策，层层深入
4. **动态大纲** - 不预设维度，根据数据画像自动发现主题
5. **专家视角** - 集成费孝通《乡土中国》等理论框架和商业SOP

---

## 🎯 三层报告体系

```
┌─────────────────────────────────────────────────────────────┐
│                   三层递进报告架构                            │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Level 1: 田野调查报告（Foundation）                         │
│  ├─ 性质：客观、数据驱动、事实呈现                            │
│  ├─ 字数：10,000+ 字                                         │
│  ├─ 核心：编年史时间线 + 关键词社区 + 实体网络                │
│  └─ 要求：所有观点有原文引用（反幻觉）                        │
│                                                               │
│                          ↓                                    │
│                                                               │
│  Level 2: 学术专家分析报告（Analysis）                        │
│  ├─ 性质：理论视角、深度解读                                  │
│  ├─ 字数：10,000+ 字                                         │
│  ├─ 核心：费孝通《乡土中国》四维度分析                        │
│  │   • 差序格局                                              │
│  │   • 礼治秩序                                              │
│  │   • 熟人社会                                              │
│  │   • 现代化冲击                                            │
│  └─ 要求：理论与材料深度对话，每个观点有理论支撑+原文依据     │
│                                                               │
│                          ↓                                    │
│                                                               │
│  Level 3: 商业市场分析报告（Decision）                        │
│  ├─ 性质：商业导向、决策支持                                  │
│  ├─ 字数：10,000+ 字                                         │
│  ├─ 核心：乡村运营SOP六维度 + SWOT + 战略建议                │
│  │   • 社区基础调研                                          │
│  │   • 文化资产评估                                          │
│  │   • 利益相关方分析                                        │
│  │   • 业态可行性                                            │
│  │   • 风险评估                                              │
│  │   • 行动路径规划                                          │
│  └─ 要求：可落地的战略建议，每个建议有理论+原文+商业逻辑支撑  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 技术架构

### 1. 数据素材提取层（DataDrivenReportBuilder）

**职责**：从数据库中提取报告所需的所有素材

```python
class ReportMaterial:
    # 基础统计
    total_documents: int
    total_chunks: int
    total_words: int
    
    # 关键词网络数据（基于前期Task 2完成的关键词网络）
    main_keywords: List[Dict]          # PageRank识别的主关键词
    keyword_communities: List[Dict]    # Louvain社区检测结果
    keyword_relations: List[Dict]      # 关键词共现关系
    
    # 实体网络数据（基于前期Task 1完成的报告关系网络）
    core_entities: Dict[str, List]     # PERSON/LOCATION/EVENT/ORGANIZATION
    entity_relations: List[Dict]        # 实体关系网络
    
    # 时间线数据（编年史）
    timeline: List[Dict]                # 按时间排序的事件
    temporal_span: Dict                 # 时间跨度统计
    
    # 原文引用池（反幻觉核心）
    citation_pool: List[Dict]           # 所有可引用的原文片段
    
    # 数据画像
    data_profile: Dict                  # 动态发现的维度
```

**核心方法**：
- `extract_report_material(project_id)` - 提取项目的完整素材
- `generate_dynamic_outline(material, level)` - 动态生成报告大纲

### 2. 内容填充引擎（ReportContentEngine）

**职责**：根据大纲章节填充内容，确保每个观点有原文引用

**核心方法**：
- `fill_section(section_outline, material, level)` - 填充单个章节
- `_fill_overview_section()` - 概述章节
- `_fill_timeline_section()` - 编年史章节
- `_fill_keyword_community_section()` - 关键词社区章节
- `_fill_entities_section()` - 实体分析章节
- `_fill_feixiaotong_section()` - 费孝通理论分析章节
- `_fill_business_sop_section()` - 商业SOP章节
- `_enhance_with_llm()` - LLM深度分析增强

### 3. 引用验证器（CitationValidator）

**职责**：反幻觉核心组件，验证引用完整性

**四重锁机制**：
1. **强制引用标记**：每个关键观点必须有`[^n]`标记
2. **引用源验证**：每个引用ID必须在citations列表中
3. **数字验证**：所有关键数字必须来自原文或计算
4. **引用覆盖率**：统计有引用支持的内容比例

**核心方法**：
- `validate_section(content, citations)` - 验证章节引用
- `validate_full_report(sections)` - 验证完整报告
- `generate_validation_report()` - 生成人类可读的验证报告

### 4. 三层报告服务（ThreeLayerReportService）

**职责**：整合所有组件，提供完整的报告生成流程

**核心方法**：
- `generate_report(project_id, level, options)` - 生成单层报告
- `generate_three_layer_reports(project_id, options)` - 生成三层完整报告
- `export_report(report, format_type)` - 导出为Markdown/HTML/JSON

---

## 📊 数据流程

```
1. 用户发起报告生成请求
   ↓
2. DataDrivenReportBuilder 提取素材
   ├─ 查询关键词网络（main_keywords, communities）
   ├─ 查询实体关系网络（persons, locations, events）
   ├─ 查询文档chunks（timeline, citation_pool）
   └─ 聚合数据画像（dynamic_dimensions）
   ↓
3. DataDrivenReportBuilder 生成动态大纲
   ├─ 分析主关键词和社区
   ├─ 确定章节数量和顺序
   └─ 为每个章节分配内容源
   ↓
4. ReportContentEngine 填充每个章节
   ├─ 从citation_pool检索相关原文
   ├─ 组织内容结构
   ├─ 添加引用标记[^n]
   └─ (可选) LLM深度分析增强
   ↓
5. CitationValidator 验证引用完整性
   ├─ 检查引用标记
   ├─ 验证数字来源
   ├─ 计算引用覆盖率
   └─ 生成验证报告
   ↓
6. ThreeLayerReportService 导出报告
   ├─ Markdown（默认）
   ├─ HTML（带样式）
   └─ JSON（原始数据）
```

---

## 🚀 API 使用指南

### 1. 预览报告素材

**查看项目数据是否充足**

```bash
GET /api/v1/projects/{project_id}/reports/material-preview
```

**响应示例**：
```json
{
  "success": true,
  "data": {
    "material_stats": {
      "total_documents": 15,
      "total_chunks": 234,
      "total_words": 45678,
      "main_keywords_count": 20,
      "keyword_communities_count": 5,
      "entities_by_type": {
        "PERSON": 12,
        "LOCATION": 8,
        "EVENT": 6,
        "ORGANIZATION": 4
      },
      "timeline_events": 234,
      "citation_pool_size": 234
    },
    "readiness": {
      "has_enough_documents": true,
      "has_keywords": true,
      "has_entities": true,
      "has_timeline": true,
      "has_citations": true
    }
  }
}
```

### 2. 预览报告大纲

**查看动态生成的大纲**

```bash
GET /api/v1/projects/{project_id}/reports/outline-preview?report_level=1
```

**响应示例**：
```json
{
  "success": true,
  "data": {
    "outline": [
      {
        "chapter": "第一章 调查概述",
        "reason": "总体介绍项目背景和数据来源",
        "min_words": 1000
      },
      {
        "chapter": "第二章 田野调查编年史",
        "reason": "按时间顺序记录234个调查事件",
        "min_words": 2000
      },
      {
        "chapter": "第三章 文化传承",
        "reason": "关键词社区分析：包含15个相关概念",
        "min_words": 1500
      }
    ],
    "estimated_sections": 7,
    "estimated_min_words": 10000
  }
}
```

### 3. 生成单层报告

**生成指定层级的报告**

```bash
POST /api/v1/projects/{project_id}/reports/generate
Content-Type: application/json

{
  "report_level": 1,
  "min_word_count": 10000,
  "include_validation": true,
  "export_formats": ["markdown", "html"]
}
```

**响应示例**：
```json
{
  "success": true,
  "data": {
    "report_id": "report_1_L1_20260917123456",
    "level": 1,
    "title": "2026年文化传承田野调查报告",
    "generated_at": "2026-09-17T12:34:56",
    "sections": [
      {
        "chapter": "第一章 调查概述",
        "content": "## 调查背景与数据来源\n\n本报告基于...",
        "word_count": 1234,
        "citations": [...],
        "citation_validation": {
          "is_valid": true,
          "citation_coverage": 0.45
        }
      }
    ],
    "total_word_count": 12345,
    "total_citations": 89,
    "validation": {
      "is_valid": true,
      "report_quality": "excellent"
    }
  }
}
```

### 4. 生成三层完整报告

**一次性生成三层报告（耗时较长）**

```bash
POST /api/v1/projects/{project_id}/reports/generate-three-layers
Content-Type: application/json

{
  "min_word_count": 10000,
  "include_validation": true
}
```

**响应示例**：
```json
{
  "success": true,
  "data": {
    "level1_report": {...},
    "level2_report": {...},
    "level3_report": {...},
    "summary": {
      "total_word_count": 35678,
      "total_citations": 234,
      "total_sections": 20
    }
  }
}
```

### 5. 导出报告

**导出为不同格式**

```bash
POST /api/v1/reports/export
Content-Type: application/json

{
  "format_type": "html",
  "report_data": {...}
}
```

---

## 🎨 报告示例

### Level 1: 田野调查报告（示例片段）

```markdown
# 2026年某村文化传承田野调查报告

---

**报告层级**：Level 1 - 田野调查报告

**生成时间**：2026-09-17 12:34:56

**项目ID**：1

**总字数**：12,345 字

**引用数**：89 条

---

## 第一章 调查概述

### 调查背景与数据来源

本报告基于对项目的系统性田野调查，共收集整理了 **15** 份文档资料，总计约 **45,678** 字。

### 数据概览

- **文档数量**：15 份
- **总字数**：45,678 字
- **文本片段**：234 个
- **提取实体**：30 个
- **识别关键词**：20 个（主关键词）

### 时间跨度

调查时间从 **2026-08-01** 至 **2026-08-31**，记录了 **234** 个调查事件。

### 主要研究主题

通过关键词网络分析（Louvain社区检测算法），本次调查自动识别出以下主要主题：

1. **文化传承**：包含 15 个相关概念（传统、习俗、节日、仪式、技艺等）
2. **社区组织**：包含 12 个相关概念（村委会、理事会、自治、协商、治理等）
3. **经济发展**：包含 10 个相关概念（产业、就业、收入、合作社、市场等）

...

## 第二章 田野调查编年史

### 调查时间轴

#### 2026-08-01 - 初访调查记录.pdf

[^1] 8月1日上午9点，调研组首次进入某村，与村支书进行了初步访谈。村支书介绍了村子的基本情况：全村共有320户，1200余人，其中常住人口约800人...

[^2] 随后，调研组参观了村文化活动中心，该中心建于2020年，占地面积约500平方米，设有图书室、多功能厅、展览厅等...

#### 2026-08-03 - 老人访谈记录.pdf

[^3] "我们村以前有个传统，每年农历三月三都要举办庙会，全村人都参加，热闹得很。"张大爷回忆道，"但这些年年轻人都出去打工了，参加的人越来越少..."

...

---

### 引用注释

[^1]: 初访调查记录.pdf, 第1段
[^2]: 初访调查记录.pdf, 第2段
[^3]: 老人访谈记录.pdf, 第5段
...
```

---

## ⚙️ 系统配置

### 前置依赖

报告生成系统依赖以下已完成的模块：

1. **关键词网络系统**（Task 2）
   - 主关键词识别（PageRank）
   - 社区检测（Louvain）
   - 关键词共现关系

2. **报告关系网络系统**（Task 1）
   - 实体提取（PERSON/LOCATION/EVENT/ORGANIZATION）
   - 实体关系构建
   - 报告引用网络

3. **智能推荐系统**（Task 3）
   - 报告推荐
   - 内容推荐

4. **网络可视化系统**（Task 3）
   - 多格式可视化支持

### 环境变量

```bash
# LLM配置（用于深度分析）
ANTHROPIC_API_KEY=your_anthropic_key  # 推荐使用Claude Opus 5
OPENAI_API_KEY=your_openai_key        # 备用

# 数据库配置
DATABASE_URL=postgresql://user:pass@host:5432/fieldmind
```

### 验证安装

```python
# 测试报告生成系统
from app.services.report_generation import ThreeLayerReportService
from app.core.database import SessionLocal

db = SessionLocal()
service = ThreeLayerReportService(db)

# 预览素材
from app.services.report_generation import DataDrivenReportBuilder
builder = DataDrivenReportBuilder(db)
material = builder.extract_report_material(project_id=1)

print(f"文档数：{material.total_documents}")
print(f"主关键词：{len(material.main_keywords)}")
print(f"实体数：{sum(len(v) for v in material.core_entities.values())}")
print(f"引用池：{len(material.citation_pool)}")
```

---

## 📚 下一步：集成Skills

### 当前缺失的Skills

报告生成系统当前使用占位内容，需要集成以下Skills：

#### 1. 费孝通Skill（Level 2报告必需）

**功能**：基于《乡土中国》理论分析田野材料

**需要实现的维度**：
- 差序格局识别
- 礼治秩序分析
- 熟人社会结构研究
- 现代化冲击评估

**集成位置**：`ReportContentEngine._fill_feixiaotong_section()`

#### 2. 商业SOP Skill（Level 3报告必需）

**功能**：乡村运营六维度评估

**需要实现的维度**：
- 社区基础调研
- 文化资产评估
- 利益相关方分析
- 业态可行性评估
- 风险评估
- 行动路径规划

**集成位置**：`ReportContentEngine._fill_business_sop_section()`

#### 3. LLM增强插件（可选）

**功能**：对已有内容进行深度分析和洞察

**约束**：
- 只能基于已有的content和citations
- 不能引入新的事实
- 必须保持原有的引用标记

**集成位置**：`ReportContentEngine._enhance_with_llm()`

---

## 🎯 使用建议

### 报告生成最佳实践

1. **数据准备充分**
   - 至少5份以上文档
   - 完成关键词提取和网络构建
   - 完成实体识别和关系构建

2. **先预览再生成**
   - 使用`/material-preview`检查数据完整性
   - 使用`/outline-preview`查看大纲是否合理

3. **分层生成**
   - 先生成Level 1，确保基础数据无误
   - 再生成Level 2，集成理论分析
   - 最后生成Level 3，提供商业建议

4. **引用验证**
   - 始终开启`include_validation: true`
   - 关注引用覆盖率（建议≥30%）
   - 修复验证报告中的问题

5. **导出多格式**
   - Markdown：便于编辑和版本控制
   - HTML：便于分享和打印
   - JSON：便于二次开发和集成

---

## 📞 技术支持

如需帮助，请提供：
1. 项目ID
2. 报告层级
3. 错误信息或问题描述
4. `/material-preview`的响应结果

---

**版本**: 1.0.0  
**最后更新**: 2026-09-17  
**文档作者**: FieldMind Team
