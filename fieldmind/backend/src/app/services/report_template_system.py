"""
通用报告模板系统

功能：
1. 支持多种报告模板（田野调查、公司分析、市场研究等）
2. 模板可配置字段
3. 支持多种导出格式（HTML、Markdown、PDF）
4. 模板继承和复用
"""

from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
from datetime import datetime
from jinja2 import Template
import markdown
from pathlib import Path


class ReportSection(ABC):
    """报告章节基类"""

    def __init__(self, title: str, order: int = 0):
        self.title = title
        self.order = order
        self.content = ""

    @abstractmethod
    def generate(self, data: Dict[str, Any]) -> str:
        """生成章节内容"""
        pass

    def render(self, data: Dict[str, Any]) -> str:
        """渲染章节"""
        self.content = self.generate(data)
        return self.content


class ExecutiveSummarySection(ReportSection):
    """执行摘要章节"""

    def __init__(self):
        super().__init__("执行摘要", order=1)

    def generate(self, data: Dict[str, Any]) -> str:
        template = """
## {{ title }}

**项目名称**: {{ project_name }}
**调研时间**: {{ research_period }}
**核心发现**: {{ key_findings_count }} 个

### 关键洞察

{% for insight in key_insights %}
- **{{ insight.title }}**: {{ insight.description }}
{% endfor %}

### 主要建议

{% for recommendation in recommendations %}
{{ loop.index }}. {{ recommendation }}
{% endfor %}
"""
        t = Template(template)
        return t.render(**data)


class FactLayerSection(ReportSection):
    """事实层章节"""

    def __init__(self):
        super().__init__("事实层：数据汇总", order=2)

    def generate(self, data: Dict[str, Any]) -> str:
        template = """
## {{ title }}

### 数据概览

- 文档数量: {{ stats.total_documents }}
- 提及实体: {{ stats.total_entities }}
- 事实陈述: {{ stats.total_facts }}
- 数据覆盖: {{ stats.data_coverage }}%

### 核心实体

| 实体名称 | 类型 | 提及次数 | 关联维度 |
|---------|------|---------|---------|
{% for entity in top_entities %}
| {{ entity.name }} | {{ entity.type }} | {{ entity.mentions }} | {{ entity.dimensions | join(', ') }} |
{% endfor %}

### 维度分布

{% for dimension in dimensions %}
#### {{ dimension.name }}

- **关键词**: {{ dimension.keywords | join('、') }}
- **频次**: {{ dimension.frequency }}
- **覆盖率**: {{ dimension.coverage }}%

{% endfor %}
"""
        t = Template(template)
        return t.render(**data)


class InsightLayerSection(ReportSection):
    """洞察层章节"""

    def __init__(self):
        super().__init__("洞察层：模式发现", order=3)

    def generate(self, data: Dict[str, Any]) -> str:
        template = """
## {{ title }}

### 主题聚类

{% for cluster in clusters %}
#### {{ cluster.name }}

**核心观点**: {{ cluster.core_idea }}

**支持证据**:
{% for evidence in cluster.evidences %}
- {{ evidence.statement }} *（来源：{{ evidence.source }}）*
{% endfor %}

**关联实体**: {{ cluster.entities | join('、') }}

---
{% endfor %}

### 关系发现

{% for relation in relations %}
- **{{ relation.source }}** {{ relation.type }} **{{ relation.target }}**
  - 强度：{{ relation.strength }}
  - 证据数：{{ relation.evidence_count }}
{% endfor %}
"""
        t = Template(template)
        return t.render(**data)


class BusinessLayerSection(ReportSection):
    """商业层章节"""

    def __init__(self):
        super().__init__("商业层：决策建议", order=4)

    def generate(self, data: Dict[str, Any]) -> str:
        template = """
## {{ title }}

### 现状评估

{% for dimension in business_dimensions %}
#### {{ dimension.name }}

**评分**: {{ dimension.score }}/10

**优势**:
{% for strength in dimension.strengths %}
- {{ strength }}
{% endfor %}

**劣势**:
{% for weakness in dimension.weaknesses %}
- {{ weakness }}
{% endfor %}

{% endfor %}

### 机会识别

{% for opportunity in opportunities %}
#### {{ opportunity.title }}

- **潜力**: {{ opportunity.potential }}
- **可行性**: {{ opportunity.feasibility }}
- **建议**: {{ opportunity.recommendation }}

{% endfor %}

### 行动建议

{% for action in action_items %}
{{ loop.index }}. **{{ action.title }}** (优先级: {{ action.priority }})
   - 目标: {{ action.objective }}
   - 时间线: {{ action.timeline }}
   - 预期成果: {{ action.expected_outcome }}

{% endfor %}
"""
        t = Template(template)
        return t.render(**data)


class AppendixSection(ReportSection):
    """附录章节"""

    def __init__(self):
        super().__init__("附录", order=5)

    def generate(self, data: Dict[str, Any]) -> str:
        template = """
## {{ title }}

### 数据来源

{% for source in data_sources %}
- **{{ source.name }}** ({{ source.type }})
  - 上传时间: {{ source.upload_date }}
  - 处理状态: {{ source.status }}
{% endfor %}

### 方法说明

{{ methodology }}

### 术语表

{% for term in glossary %}
- **{{ term.name }}**: {{ term.definition }}
{% endfor %}
"""
        t = Template(template)
        return t.render(**data)


class ReportTemplate(ABC):
    """报告模板基类"""

    def __init__(self, template_name: str):
        self.template_name = template_name
        self.sections: List[ReportSection] = []
        self.metadata: Dict[str, Any] = {}

    def add_section(self, section: ReportSection):
        """添加章节"""
        self.sections.append(section)
        self.sections.sort(key=lambda s: s.order)

    def set_metadata(self, **kwargs):
        """设置元数据"""
        self.metadata.update(kwargs)

    @abstractmethod
    def prepare_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """准备报告数据"""
        pass

    def generate(self, raw_data: Dict[str, Any]) -> str:
        """生成完整报告"""
        # 准备数据
        prepared_data = self.prepare_data(raw_data)

        # 生成报告头部
        report_md = self._generate_header()

        # 生成各章节
        for section in self.sections:
            section_data = prepared_data.get(section.title, prepared_data)
            report_md += "\n\n" + section.render(section_data)

        # 生成报告尾部
        report_md += "\n\n" + self._generate_footer()

        return report_md

    def _generate_header(self) -> str:
        """生成报告头部"""
        header = f"""# {self.metadata.get('title', '调研报告')}

**报告类型**: {self.template_name}
**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**项目**: {self.metadata.get('project_name', 'N/A')}

---
"""
        return header

    def _generate_footer(self) -> str:
        """生成报告尾部"""
        footer = f"""
---

*本报告由 FieldMind 自动生成*
*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        return footer

    def export_html(self, content: str, output_path: str):
        """导出为 HTML"""
        html = markdown.markdown(
            content,
            extensions=['tables', 'fenced_code', 'toc']
        )

        # 添加 CSS 样式
        styled_html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.metadata.get('title', '调研报告')}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            line-height: 1.6;
            max-width: 900px;
            margin: 0 auto;
            padding: 40px 20px;
            color: #333;
        }}
        h1, h2, h3, h4 {{
            color: #2c3e50;
            margin-top: 24px;
        }}
        h1 {{
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 8px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #3498db;
            color: white;
        }}
        tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}
        blockquote {{
            border-left: 4px solid #3498db;
            padding-left: 20px;
            margin: 20px 0;
            color: #555;
        }}
        code {{
            background-color: #f8f9fa;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }}
        .metadata {{
            background-color: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 30px;
        }}
    </style>
</head>
<body>
    {html}
</body>
</html>
"""

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(styled_html)

    def export_markdown(self, content: str, output_path: str):
        """导出为 Markdown"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)


class FieldWorkReportTemplate(ReportTemplate):
    """田野调查报告模板"""

    def __init__(self):
        super().__init__("田野调查报告")

        # 添加标准章节
        self.add_section(ExecutiveSummarySection())
        self.add_section(FactLayerSection())
        self.add_section(InsightLayerSection())
        self.add_section(BusinessLayerSection())
        self.add_section(AppendixSection())

    def prepare_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """准备田野调查报告数据"""
        prepared = {
            "执行摘要": {
                "title": "执行摘要",
                "project_name": raw_data.get('project_name', '未命名项目'),
                "research_period": raw_data.get('research_period', '2026年'),
                "key_findings_count": len(raw_data.get('key_insights', [])),
                "key_insights": raw_data.get('key_insights', []),
                "recommendations": raw_data.get('recommendations', [])
            },
            "事实层：数据汇总": {
                "title": "事实层：数据汇总",
                "stats": raw_data.get('stats', {}),
                "top_entities": raw_data.get('top_entities', []),
                "dimensions": raw_data.get('dimensions', [])
            },
            "洞察层：模式发现": {
                "title": "洞察层：模式发现",
                "clusters": raw_data.get('clusters', []),
                "relations": raw_data.get('relations', [])
            },
            "商业层：决策建议": {
                "title": "商业层：决策建议",
                "business_dimensions": raw_data.get('business_dimensions', []),
                "opportunities": raw_data.get('opportunities', []),
                "action_items": raw_data.get('action_items', [])
            },
            "附录": {
                "title": "附录",
                "data_sources": raw_data.get('data_sources', []),
                "methodology": raw_data.get('methodology', ''),
                "glossary": raw_data.get('glossary', [])
            }
        }
        return prepared


class CompanyBrainReportTemplate(ReportTemplate):
    """公司大脑报告模板（预留）"""

    def __init__(self):
        super().__init__("公司分析报告")
        # TODO: 添加公司分析专用章节

    def prepare_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """准备公司分析报告数据"""
        # TODO: 实现公司分析数据准备逻辑
        return raw_data


class MarketResearchReportTemplate(ReportTemplate):
    """市场研究报告模板（预留）"""

    def __init__(self):
        super().__init__("市场研究报告")
        # TODO: 添加市场研究专用章节

    def prepare_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """准备市场研究报告数据"""
        # TODO: 实现市场研究数据准备逻辑
        return raw_data


class ReportTemplateFactory:
    """报告模板工厂"""

    _templates = {
        "field_work": FieldWorkReportTemplate,
        "company_brain": CompanyBrainReportTemplate,
        "market_research": MarketResearchReportTemplate
    }

    @classmethod
    def create(cls, template_type: str) -> ReportTemplate:
        """创建报告模板实例"""
        template_class = cls._templates.get(template_type)
        if not template_class:
            raise ValueError(f"未知的报告模板类型: {template_type}")
        return template_class()

    @classmethod
    def list_templates(cls) -> List[Dict[str, str]]:
        """列出所有可用模板"""
        return [
            {"type": "field_work", "name": "田野调查报告"},
            {"type": "company_brain", "name": "公司分析报告"},
            {"type": "market_research", "name": "市场研究报告"}
        ]


# ===== 使用示例 =====

def generate_field_work_report(project_id: int, output_format: str = 'html'):
    """生成田野调查报告"""

    # 1. 创建模板
    template = ReportTemplateFactory.create('field_work')

    # 2. 设置元数据
    template.set_metadata(
        title="某社区田野调查报告",
        project_name="社区文化调研项目",
        author="调研团队"
    )

    # 3. 准备原始数据（从数据库获取）
    raw_data = {
        "project_name": "社区文化调研项目",
        "research_period": "2026年8月-9月",
        "key_insights": [
            {
                "title": "文化传承断层",
                "description": "年轻一代对传统文化认同度较低"
            },
            {
                "title": "公共空间不足",
                "description": "社区缺乏多功能活动场所"
            }
        ],
        "recommendations": [
            "建立社区文化传习所",
            "改造现有空间为多功能活动中心",
            "组织代际交流活动"
        ],
        "stats": {
            "total_documents": 15,
            "total_entities": 48,
            "total_facts": 127,
            "data_coverage": 85
        },
        "top_entities": [
            {
                "name": "张老师",
                "type": "人物",
                "mentions": 23,
                "dimensions": ["文化", "教育"]
            },
            {
                "name": "社区活动中心",
                "type": "地点",
                "mentions": 18,
                "dimensions": ["社会", "文化"]
            }
        ],
        "dimensions": [
            {
                "name": "文化",
                "keywords": ["传统", "传承", "艺术", "节日"],
                "frequency": 45,
                "coverage": 78
            },
            {
                "name": "社会",
                "keywords": ["邻里", "交往", "活动", "组织"],
                "frequency": 38,
                "coverage": 65
            }
        ],
        "clusters": [],
        "relations": [],
        "business_dimensions": [],
        "opportunities": [],
        "action_items": [],
        "data_sources": [],
        "methodology": "采用参与式观察和深度访谈方法",
        "glossary": []
    }

    # 4. 生成报告
    report_content = template.generate(raw_data)

    # 5. 导出
    output_path = f"report_{project_id}.{output_format}"
    if output_format == 'html':
        template.export_html(report_content, output_path)
    else:
        template.export_markdown(report_content, output_path)

    return output_path


if __name__ == "__main__":
    # 测试
    print("可用报告模板:")
    for tmpl in ReportTemplateFactory.list_templates():
        print(f"  - {tmpl['name']} ({tmpl['type']})")

    print("\n生成示例报告...")
    output_file = generate_field_work_report(1, 'html')
    print(f"✅ 报告已生成: {output_file}")
