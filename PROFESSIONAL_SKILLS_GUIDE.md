# 专业视角 Skills 使用指南

## 概述

基于你提供的《乡土中国》和《神堂记忆》理论框架，我已将两个专业分析 Skill 完全融入 FieldMind 系统：

1. **XiangtuChinaSkill** - 乡土中国视角的田野调查与发展指导
2. **SocialMemorySkill** - 社会记忆视角的文化遗产分析

---

## 一、文件位置

### 核心 Skill 文件

```
backend/src/app/services/report_generation/skills/
├── xiangtu_china_skill.py          # 乡土中国 Skill
├── social_memory_skill.py          # 社会记忆 Skill
├── field_investigation_skill.py    # Level 1 田野调查（已优化）
└── business_sop_skill.py           # Level 3 商业分析（已优化）
```

### 测试文件

```
test_professional_skills.py              # 专业 Skills 集成测试
professional_skills_report.md            # 测试生成的完整报告
professional_skills_test_summary.md      # 测试总结
```

---

## 二、技术架构

### 2.1 XiangtuChinaSkill 架构

```python
class XiangtuChinaSkill:
    """
    基于费孝通《乡土中国》的认知框架
    """
    
    # 核心方法
    def analyze_xiangtu_society(self, report_material)
        # 分析乡土社会特征
        # 返回: xiangtu_features, health_diagnosis, dimension_analysis
    
    def identify_opportunities(self, xiangtu_analysis)
        # 识别基于乡土资源的商业机会
        # 返回: List[XiangtuOpportunity]
    
    def generate_report(self, report_material)
        # 生成完整的乡土中国视角报告
        # 返回: markdown 格式报告文本
```

**核心数据结构**：

```python
@dataclass
class XiangtuDimension:
    dimension: str           # 社会结构/文化传统/物质遗产/经济生活
    key_findings: List[str]  # 核心发现
    xiangtu_logic: str       # 乡土逻辑解读
    development_potential: str

@dataclass
class XiangtuOpportunity:
    resource_type: str         # 熟人网络/礼治秩序/血缘认同等
    transformation_path: str   # 转化路径
    practical_approach: str    # 实践路径
    risk_mitigation: str       # 风险防范
```

### 2.2 SocialMemorySkill 架构

```python
class SocialMemorySkill:
    """
    基于景军《神堂记忆》的社会记忆理论
    """
    
    # 核心方法
    def analyze_memory_system(self, report_material)
        # 分析村落的社会记忆系统
        # 返回: memory_carriers, memory_types, memory_health, memory_subjects
    
    def identify_memory_opportunities(self, memory_analysis, report_material)
        # 识别基于社会记忆的发展机会
        # 返回: List[MemoryOpportunity]
    
    def generate_report(self, report_material)
        # 生成社会记忆视角的文化遗产分析报告
        # 返回: markdown 格式报告文本
```

**核心数据结构**：

```python
@dataclass
class MemoryCarrier:
    carrier_type: str        # 物质/仪式/文本/口头
    carrier_name: str        # 载体名称
    memory_content: str      # 承载的记忆内容
    emotional_intensity: str # 情感强度
    shareability: str        # 共享性

@dataclass
class MemoryType:
    type_name: str                # 历史记忆/仪式记忆/族谱记忆等
    key_elements: List[str]       # 核心要素
    memory_subjects: List[str]    # 记忆主体
    transformation_potential: str # 转化潜力
    commercial_direction: str     # 商业化方向

@dataclass
class MemoryOpportunity:
    memory_asset: str          # 记忆资产
    transformation_path: str   # 转化路径
    experience_design: str     # 体验设计
    cultural_innovation: str   # 文化创新点
```

---

## 三、使用方法

### 3.1 基础使用

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.services.report_generation.data_driven_report_builder import DataDrivenReportBuilder
from app.services.report_generation.skills.xiangtu_china_skill import XiangtuChinaSkill
from app.services.report_generation.skills.social_memory_skill import SocialMemorySkill

# 1. 初始化数据库连接
DATABASE_URL = "sqlite:///backend/src/data/fieldmind.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

# 2. 提取项目数据
builder = DataDrivenReportBuilder(db=session)
material_obj = builder.extract_report_material(project_id=2)

# 3. 转换为字典格式
material = {
    'main_keywords': material_obj.main_keywords,
    'keyword_communities': material_obj.keyword_communities,
    'core_entities': material_obj.core_entities,
    'entity_relations': material_obj.entity_relations,
    'timeline': material_obj.timeline,
    'citation_pool': material_obj.citation_pool,
    'data_profile': material_obj.data_profile
}

# 4. 使用乡土中国 Skill
xiangtu_skill = XiangtuChinaSkill()
xiangtu_analysis = xiangtu_skill.analyze_xiangtu_society(material)
xiangtu_opportunities = xiangtu_skill.identify_opportunities(xiangtu_analysis)
xiangtu_report = xiangtu_skill.generate_report(material)

# 5. 使用社会记忆 Skill
memory_skill = SocialMemorySkill()
memory_analysis = memory_skill.analyze_memory_system(material)
memory_opportunities = memory_skill.identify_memory_opportunities(memory_analysis, material)
memory_report = memory_skill.generate_report(material)
```

### 3.2 快速测试

```bash
# 运行完整测试
cd /Users/alwan/FieldMind
python3 test_professional_skills.py

# 查看生成的报告
cat professional_skills_report.md
```

---

## 四、四个 Skills 的定位与关系

### 4.1 功能矩阵

| Skill | 视角 | 输出重点 | 适用场景 | 字数规模 |
|-------|------|----------|----------|----------|
| **Level 1 田野调查** | 内容运营 | 文化资源挖掘与转化 | 项目启动、资源盘点 | 1800+字/章 |
| **Level 3 商业分析** | 商业可行性 | 市场机会与实施路径 | 投资决策、运营规划 | 450+字/章 |
| **乡土中国** | 社会结构 | 乡土逻辑与健康度诊断 | 深度调研、理论支撑 | 1700+字 |
| **社会记忆** | 文化记忆 | 记忆系统与激活方案 | 文化价值挖掘、IP设计 | 2900+字 |

### 4.2 使用策略

**按项目阶段组合使用**：

```
前期调研阶段：
├── Level 1 田野调查（资源盘点）
├── 乡土中国 Skill（社会结构分析）
└── 社会记忆 Skill（文化价值挖掘）

中期规划阶段：
├── Level 3 商业分析（商业可行性）
└── 乡土中国 Skill（发展机会识别）

深度研究阶段：
├── 乡土中国 Skill（理论框架）
└── 社会记忆 Skill（学术水准分析）
```

**按报告类型组合使用**：

- **投资人报告**: Level 1 + Level 3
- **学术研究报告**: 乡土中国 + 社会记忆
- **完整可行性报告**: 全部四个 Skills

---

## 五、理论框架

### 5.1 乡土中国的七个核心概念

| 概念 | 核心内涵 | 实践提问 |
|------|----------|----------|
| **乡土本色** | 离不了泥土的生产与生活方式 | 土地关系如何？人口流动性如何？ |
| **差序格局** | 以己为中心的人际关系网络 | 权力结构如何？谁有影响力？ |
| **礼治秩序** | 依赖礼治而非法治 | 纠纷如何解决？村规民约内容？ |
| **家族血缘** | 血缘维系社会网络 | 宗族结构如何？家族作用？ |
| **长老统治** | 年长者拥有文化权威 | 长老在村务中的角色？ |
| **无讼传统** | 追求和谐，内部调解 | 矛盾调解机制？对打官司的态度？ |
| **男女有别** | 性别分工与角色差异 | 性别分工如何？女性参与度？ |

### 5.2 神堂记忆的六种记忆类型

| 记忆类型 | 定义 | 对应资源 | 转化方向 |
|----------|------|----------|----------|
| **社会记忆** | 社群共享的集体性认知 | 村落集体叙事 | 整体文化定位 |
| **历史记忆** | 重大历史事件的群体记忆 | 变迁史、事件遗址 | 历史故事线 |
| **仪式记忆** | 通过仪式传承的记忆 | 节庆、祭祀仪式 | 体验性产品 |
| **族谱记忆** | 血缘谱系维系的记忆 | 族谱、祠堂 | 家族文化旅游 |
| **苦难记忆** | 集体创伤记忆 | 移民、灾难遗迹 | 文化深度叙事 |
| **文化象征记忆** | 附着于符号的记忆 | 庙宇、图腾 | 文化IP设计 |

---

## 六、核心方法论

### 6.1 从乡土中国到神堂记忆的整合

```
《乡土中国》→ 理解村落"是什么"（社会结构、运行逻辑）
《神堂记忆》→ 理解村落"记得什么"（集体记忆、文化意义）

整合视角 = 形（结构） + 魂（记忆）
```

**三个维度的融合**：

1. **结构 + 内容**: 用乡土中国理解社会结构，用神堂记忆挖掘记忆内容
2. **静态 + 动态**: 用乡土中国看礼治秩序，用神堂记忆看记忆的政治
3. **事实 + 意义**: 用乡土中国理解"是什么"，用神堂记忆理解"怎么被记住"

### 6.2 从资源管理到记忆运营

```
传统模式：管理文化遗产资源
↓
大地遗产方法论：内容运营（资源→内容→产品）
↓
专业 Skills 升级：记忆运营（资源→记忆→体验）
```

**四个转变**：

- 不是做"文物保护" → 而是做**记忆激活**
- 不是开发"旅游产品" → 而是设计**记忆体验**
- 不是建设"文化空间" → 而是营造**记忆之场**
- 不是打造"文化IP" → 而是转化**记忆符号**

---

## 七、测试结果

### 7.1 音寨布依族村测试数据

**数据规模**：
- 关键词: 20 个
- 实体: 7 个
- 引用池: 66 chunks (21,932 字)
- 时间线: 8 事件

**生成结果**：

| Skill | 识别特征 | 生成机会 | 报告字数 |
|-------|----------|----------|----------|
| 乡土中国 | 2 个乡土特征 | 2 个发展机会 | 1,767 字 |
| 社会记忆 | 2 个记忆载体，2 种记忆类型 | 2 个记忆机会 | 2,881 字 |
| **合计** | - | - | **4,648 字** |

### 7.2 与现有 Skills 的对比

| 指标 | Level 1 | Level 3 | 乡土中国 | 社会记忆 |
|------|---------|---------|----------|----------|
| 优化前 | 458 字 | 169 字 | - | - |
| 优化后 | 1,887 字 | 446 字 | 1,767 字 | 2,881 字 |
| 提升幅度 | +312% | +164% | 新增 | 新增 |
| 达标状态 | ✓ | △ | ✓ | ✓ |

---

## 八、下一步建议

### 8.1 进一步优化方向

**Level 3 商业分析优化**：
- 目标：从 446 字提升到 800+ 字
- 方法：扩展机会分析部分，增加更多引用支撑

**专业 Skills 增强**：
- 增加更多理论透镜（如涂尔干的集体欢腾、哈布瓦赫的集体记忆）
- 优化关键词分类算法，提高特征识别准确度
- 增加可视化输出（社会关系图、记忆地图）

### 8.2 系统集成建议

**API 层集成**：
```python
# backend/src/app/api/routes/reports.py

@router.post("/reports/professional-analysis")
async def generate_professional_analysis(
    project_id: int,
    skill_type: str  # "xiangtu" | "memory" | "both"
):
    # 调用专业 Skills 生成报告
    pass
```

**前端界面集成**：
- 在报告生成页面添加"专业分析"选项
- 支持选择单个或组合使用专业 Skills
- 提供理论框架说明和使用指引

---

## 九、常见问题

### Q1: 专业 Skills 和 Level 1/3 有什么区别？

**A**: 定位不同：
- Level 1/3 = **实用导向**，面向项目执行
- 专业 Skills = **理论深度**，面向深度研究和理论支撑

### Q2: 什么时候使用专业 Skills？

**A**: 三种场景：
1. 需要学术水准的项目分析报告时
2. 团队培训，理解乡土社会和社会记忆理论时
3. 为投资决策提供深度理论支撑时

### Q3: 专业 Skills 能否单独使用？

**A**: 可以。但建议：
- 与 Level 1 配合使用：Level 1 提供资源盘点，专业 Skills 提供理论分析
- 两个专业 Skills 组合使用：形成完整的"结构+记忆"双重视角

### Q4: 如何保证专业 Skills 的理论准确性？

**A**: 
- 基于《乡土中国》和《神堂记忆》原著构建理论框架
- 所有理论概念都有明确来源和定义
- 分析结果基于真实田野数据，有引用支撑

---

## 十、技术支持

### 文件结构

```
FieldMind/
├── backend/src/app/services/report_generation/
│   └── skills/
│       ├── xiangtu_china_skill.py       # 604 行
│       ├── social_memory_skill.py       # 604 行
│       ├── field_investigation_skill.py # 优化版
│       └── business_sop_skill.py        # 优化版
├── test_professional_skills.py          # 测试脚本
├── professional_skills_report.md        # 示例报告
└── PROFESSIONAL_SKILLS_GUIDE.md         # 本文档
```

### 依赖项

```python
# 核心依赖
from typing import Dict, List, Any
from dataclasses import dataclass
from sqlalchemy.orm import Session

# 数据提取
from app.services.report_generation.data_driven_report_builder import (
    DataDrivenReportBuilder,
    ReportMaterial
)
```

### 联系方式

如有问题或建议，请联系项目维护者。

---

**文档版本**: v1.0  
**最后更新**: 2024-09-17  
**维护者**: FieldMind Development Team
