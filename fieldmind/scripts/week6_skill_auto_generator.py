#!/usr/bin/env python3
"""
Week 6-7 Day 2: Skill 自动生成器
从识别的知识模式中自动生成可复用的 Skill 模板

功能：
1. 读取 knowledge_patterns.json
2. 按类型和主题聚类相似模式
3. 生成参数化的 Skill 模板
4. 创建 Skill 库目录结构
5. 生成 Skill 使用文档
"""

import json
import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional, Set
from collections import defaultdict
import re


class SkillAutoGenerator:
    """Skill 自动生成器"""

    def __init__(self, db_path: str, patterns_file: str, output_dir: str):
        self.db_path = db_path
        self.patterns_file = patterns_file
        self.output_dir = output_dir
        self.skills_generated = []

        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(f"{output_dir}/skills", exist_ok=True)
        os.makedirs(f"{output_dir}/templates", exist_ok=True)

    def load_patterns(self) -> List[Dict]:
        """加载知识模式"""
        print("📖 加载知识模式...")
        with open(self.patterns_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        patterns = data['patterns']
        print(f"   ✓ 加载了 {len(patterns)} 个知识模式")
        return patterns

    def cluster_by_topic(self, patterns: List[Dict]) -> Dict[str, List[Dict]]:
        """按主题聚类模式"""
        print("\n🔍 按主题聚类模式...")

        clusters = defaultdict(list)

        for pattern in patterns:
            # 提取关键词作为主题
            content = pattern['content']
            chunk_id = pattern['chunk_id']

            # 从数据库获取更多元数据
            metadata = self._get_chunk_metadata(chunk_id)

            # 基于维度分类和关键词聚类
            dimension = metadata.get('dimension_category', 'general')
            keywords = metadata.get('keywords', [])

            # 生成主题标签
            topic = self._generate_topic_label(dimension, keywords, content)

            pattern['topic'] = topic
            pattern['metadata'].update(metadata)
            clusters[topic].append(pattern)

        print(f"   ✓ 聚类为 {len(clusters)} 个主题")
        for topic, items in sorted(clusters.items(), key=lambda x: len(x[1]), reverse=True)[:10]:
            print(f"     - {topic}: {len(items)} 个模式")

        return dict(clusters)

    def _get_chunk_metadata(self, chunk_id: str) -> Dict:
        """从数据库获取 chunk 元数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT dimension_category, keywords, context_type,
                   speaker_id, quality_score, confidence_level
            FROM document_chunks
            WHERE chunk_id = ?
        """, (chunk_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            keywords_str = row[1] or '[]'
            try:
                keywords = json.loads(keywords_str)
            except:
                keywords = []

            return {
                'dimension_category': row[0] or 'general',
                'keywords': keywords,
                'context_type': row[2],
                'speaker_id': row[3],
                'quality_score': row[4] or 0.0,
                'confidence_level': row[5]
            }

        return {}

    def _generate_topic_label(self, dimension: str, keywords: List[str], content: str) -> str:
        """生成主题标签"""
        # 维度映射
        dimension_map = {
            'technical': '技术',
            'product': '产品',
            'business': '商业',
            'management': '管理',
            'market': '市场'
        }

        dim_label = dimension_map.get(dimension, '通用')

        # 提取核心主题词
        if keywords and len(keywords) > 0:
            # 取前3个关键词
            topic_words = keywords[:3]
            topic_str = '_'.join([kw['word'] for kw in topic_words if isinstance(kw, dict)])
            return f"{dim_label}_{topic_str}"

        # 如果没有关键词，从内容中提取
        # 简单提取：取前10个字作为主题
        content_sample = content[:10].replace('\n', '').replace(' ', '')
        return f"{dim_label}_{content_sample}"

    def generate_skill_from_cluster(self, topic: str, patterns: List[Dict]) -> Optional[Dict]:
        """从聚类生成 Skill"""

        # 至少需要3个模式才生成 Skill
        if len(patterns) < 3:
            return None

        pattern_type = patterns[0]['pattern_type']

        # 根据模式类型生成不同的 Skill
        if pattern_type == 'process':
            return self._generate_process_skill(topic, patterns)
        elif pattern_type == 'lesson_learned':
            return self._generate_lesson_skill(topic, patterns)
        elif pattern_type == 'decision':
            return self._generate_decision_skill(topic, patterns)
        elif pattern_type == 'solution':
            return self._generate_solution_skill(topic, patterns)
        elif pattern_type == 'best_practice':
            return self._generate_best_practice_skill(topic, patterns)
        elif pattern_type == 'code_template':
            return self._generate_code_skill(topic, patterns)

        return None

    def _generate_process_skill(self, topic: str, patterns: List[Dict]) -> Dict:
        """生成流程类 Skill"""

        # 提取共同步骤
        steps = []
        for p in patterns[:5]:  # 取前5个高质量的
            content = p['content']
            # 提取步骤标记
            step_markers = re.findall(r'(第[一二三四五六七八九十\d]+步|步骤\d+|[一二三四五六七八九十\d]+\.|首先|其次|然后|最后)', content)
            if step_markers:
                steps.extend(step_markers)

        skill_name = f"process_{topic}"
        skill_title = f"流程：{topic}"

        return {
            'skill_id': f"skill_{self._generate_id()}",
            'skill_name': skill_name,
            'skill_title': skill_title,
            'skill_type': 'process',
            'topic': topic,
            'pattern_count': len(patterns),
            'description': f"基于 {len(patterns)} 个实际案例总结的流程模板",
            'parameters': {
                'context': {'type': 'string', 'description': '应用场景'},
                'goal': {'type': 'string', 'description': '目标结果'},
                'constraints': {'type': 'array', 'description': '约束条件'}
            },
            'template': self._create_process_template(patterns),
            'examples': [p['chunk_id'] for p in patterns[:3]],
            'quality_avg': sum(p['metadata']['quality_score'] for p in patterns) / len(patterns)
        }

    def _generate_lesson_skill(self, topic: str, patterns: List[Dict]) -> Dict:
        """生成经验教训类 Skill"""

        skill_name = f"lesson_{topic}"
        skill_title = f"经验：{topic}"

        return {
            'skill_id': f"skill_{self._generate_id()}",
            'skill_name': skill_name,
            'skill_title': skill_title,
            'skill_type': 'lesson_learned',
            'topic': topic,
            'pattern_count': len(patterns),
            'description': f"基于 {len(patterns)} 个实际经验的总结与反思",
            'parameters': {
                'situation': {'type': 'string', 'description': '类似场景'},
                'challenge': {'type': 'string', 'description': '面临的挑战'}
            },
            'template': self._create_lesson_template(patterns),
            'examples': [p['chunk_id'] for p in patterns[:3]],
            'quality_avg': sum(p['metadata']['quality_score'] for p in patterns) / len(patterns)
        }

    def _generate_decision_skill(self, topic: str, patterns: List[Dict]) -> Dict:
        """生成决策类 Skill"""

        skill_name = f"decision_{topic}"
        skill_title = f"决策：{topic}"

        return {
            'skill_id': f"skill_{self._generate_id()}",
            'skill_name': skill_name,
            'skill_title': skill_title,
            'skill_type': 'decision',
            'topic': topic,
            'pattern_count': len(patterns),
            'description': f"基于 {len(patterns)} 个实际决策的框架模板",
            'parameters': {
                'options': {'type': 'array', 'description': '可选方案'},
                'criteria': {'type': 'array', 'description': '评估标准'},
                'constraints': {'type': 'array', 'description': '约束条件'}
            },
            'template': self._create_decision_template(patterns),
            'examples': [p['chunk_id'] for p in patterns[:3]],
            'quality_avg': sum(p['metadata']['quality_score'] for p in patterns) / len(patterns)
        }

    def _generate_solution_skill(self, topic: str, patterns: List[Dict]) -> Dict:
        """生成解决方案类 Skill"""

        skill_name = f"solution_{topic}"
        skill_title = f"解决方案：{topic}"

        return {
            'skill_id': f"skill_{self._generate_id()}",
            'skill_name': skill_name,
            'skill_title': skill_title,
            'skill_type': 'solution',
            'topic': topic,
            'pattern_count': len(patterns),
            'description': f"基于 {len(patterns)} 个实际案例的解决方案模板",
            'parameters': {
                'problem': {'type': 'string', 'description': '问题描述'},
                'context': {'type': 'string', 'description': '问题场景'},
                'requirements': {'type': 'array', 'description': '需求列表'}
            },
            'template': self._create_solution_template(patterns),
            'examples': [p['chunk_id'] for p in patterns[:3]],
            'quality_avg': sum(p['metadata']['quality_score'] for p in patterns) / len(patterns)
        }

    def _generate_best_practice_skill(self, topic: str, patterns: List[Dict]) -> Dict:
        """生成最佳实践类 Skill"""

        skill_name = f"best_practice_{topic}"
        skill_title = f"最佳实践：{topic}"

        return {
            'skill_id': f"skill_{self._generate_id()}",
            'skill_name': skill_name,
            'skill_title': skill_title,
            'skill_type': 'best_practice',
            'topic': topic,
            'pattern_count': len(patterns),
            'description': f"基于 {len(patterns)} 个高质量案例的最佳实践",
            'parameters': {
                'domain': {'type': 'string', 'description': '应用领域'},
                'objective': {'type': 'string', 'description': '优化目标'}
            },
            'template': self._create_best_practice_template(patterns),
            'examples': [p['chunk_id'] for p in patterns[:3]],
            'quality_avg': sum(p['metadata']['quality_score'] for p in patterns) / len(patterns)
        }

    def _generate_code_skill(self, topic: str, patterns: List[Dict]) -> Dict:
        """生成代码模板类 Skill"""

        skill_name = f"code_{topic}"
        skill_title = f"代码模板：{topic}"

        return {
            'skill_id': f"skill_{self._generate_id()}",
            'skill_name': skill_name,
            'skill_title': skill_title,
            'skill_type': 'code_template',
            'topic': topic,
            'pattern_count': len(patterns),
            'description': f"基于 {len(patterns)} 个实际代码的模板",
            'parameters': {
                'language': {'type': 'string', 'description': '编程语言'},
                'framework': {'type': 'string', 'description': '框架/库'},
                'use_case': {'type': 'string', 'description': '使用场景'}
            },
            'template': self._create_code_template(patterns),
            'examples': [p['chunk_id'] for p in patterns[:3]],
            'quality_avg': sum(p['metadata']['quality_score'] for p in patterns) / len(patterns)
        }

    def _create_process_template(self, patterns: List[Dict]) -> str:
        """创建流程模板"""
        template = """# {{skill_title}}

## 适用场景
{{context}}

## 目标
{{goal}}

## 步骤

### 准备阶段
1. 明确目标和约束条件
2. 收集必要资源
3. 评估可行性

### 执行阶段
"""

        # 从实际案例中提取步骤
        for i, p in enumerate(patterns[:3], 1):
            content_preview = p['content'][:100].replace('\n', ' ')
            template += f"{i}. [参考案例 {i}] {content_preview}...\n"

        template += """
### 验证阶段
1. 检查结果是否达到目标
2. 记录经验教训
3. 优化流程

## 参考案例
"""
        for i, p in enumerate(patterns[:3], 1):
            template += f"- 案例 {i}: {p['chunk_id']}\n"

        return template

    def _create_lesson_template(self, patterns: List[Dict]) -> str:
        """创建经验教训模板"""
        template = """# {{skill_title}}

## 背景场景
{{situation}}

## 面临的挑战
{{challenge}}

## 关键经验

"""

        for i, p in enumerate(patterns[:3], 1):
            content_preview = p['content'][:150].replace('\n', ' ')
            template += f"### 经验 {i}\n{content_preview}...\n\n"

        template += """
## 适用场景
- 场景1: [描述]
- 场景2: [描述]

## 注意事项
- [关键注意点1]
- [关键注意点2]

## 参考案例
"""
        for i, p in enumerate(patterns[:3], 1):
            template += f"- {p['chunk_id']}\n"

        return template

    def _create_decision_template(self, patterns: List[Dict]) -> str:
        """创建决策模板"""
        template = """# {{skill_title}}

## 决策场景
[描述需要决策的场景]

## 可选方案
{{#each options}}
- 方案{{@index}}: {{this}}
{{/each}}

## 评估标准
{{#each criteria}}
- {{this}}
{{/each}}

## 决策框架

### 1. 明确目标
[目标描述]

### 2. 分析约束
{{#each constraints}}
- {{this}}
{{/each}}

### 3. 方案对比
"""

        for i, p in enumerate(patterns[:2], 1):
            content_preview = p['content'][:100].replace('\n', ' ')
            template += f"参考 {i}: {content_preview}...\n\n"

        template += """
### 4. 做出决策
[决策逻辑]

### 5. 验证与调整
[验证方法]

## 参考案例
"""
        for i, p in enumerate(patterns[:3], 1):
            template += f"- {p['chunk_id']}\n"

        return template

    def _create_solution_template(self, patterns: List[Dict]) -> str:
        """创建解决方案模板"""
        template = """# {{skill_title}}

## 问题描述
{{problem}}

## 问题场景
{{context}}

## 解决方案

### 方案概述
"""

        for i, p in enumerate(patterns[:2], 1):
            content_preview = p['content'][:120].replace('\n', ' ')
            template += f"{i}. {content_preview}...\n"

        template += """
### 实施步骤
1. [步骤1]
2. [步骤2]
3. [步骤3]

### 预期效果
- [效果1]
- [效果2]

### 风险与应对
- 风险1: [应对措施]
- 风险2: [应对措施]

## 参考案例
"""
        for i, p in enumerate(patterns[:3], 1):
            template += f"- {p['chunk_id']}\n"

        return template

    def _create_best_practice_template(self, patterns: List[Dict]) -> str:
        """创建最佳实践模板"""
        template = """# {{skill_title}}

## 应用领域
{{domain}}

## 优化目标
{{objective}}

## 最佳实践

"""

        for i, p in enumerate(patterns[:3], 1):
            content_preview = p['content'][:150].replace('\n', ' ')
            template += f"### 实践 {i}\n{content_preview}...\n\n"

        template += """
## 实施建议
1. [建议1]
2. [建议2]
3. [建议3]

## 常见陷阱
- [陷阱1及避免方法]
- [陷阱2及避免方法]

## 衡量标准
- 指标1: [描述]
- 指标2: [描述]

## 参考案例
"""
        for i, p in enumerate(patterns[:3], 1):
            template += f"- {p['chunk_id']}\n"

        return template

    def _create_code_template(self, patterns: List[Dict]) -> str:
        """创建代码模板"""
        template = """# {{skill_title}}

## 语言/框架
{{language}} / {{framework}}

## 使用场景
{{use_case}}

## 代码模板

```python
# 基础结构
"""

        # 从第一个模式提取代码片段
        if patterns:
            content = patterns[0]['content']
            # 提取代码块
            code_blocks = re.findall(r'```[\w]*\n(.*?)\n```', content, re.DOTALL)
            if code_blocks:
                template += code_blocks[0][:500]  # 限制长度

        template += """
```

## 使用说明
1. [步骤1]
2. [步骤2]
3. [步骤3]

## 参数说明
- param1: [描述]
- param2: [描述]

## 注意事项
- [注意点1]
- [注意点2]

## 参考案例
"""
        for i, p in enumerate(patterns[:3], 1):
            template += f"- {p['chunk_id']}\n"

        return template

    def _generate_id(self) -> str:
        """生成12位 ID"""
        import uuid
        return uuid.uuid4().hex[:12]

    def save_skill(self, skill: Dict):
        """保存 Skill 到文件"""
        skill_file = f"{self.output_dir}/skills/{skill['skill_name']}.json"
        with open(skill_file, 'w', encoding='utf-8') as f:
            json.dump(skill, f, ensure_ascii=False, indent=2)

        # 同时保存模板文件
        template_file = f"{self.output_dir}/templates/{skill['skill_name']}.md"
        with open(template_file, 'w', encoding='utf-8') as f:
            f.write(skill['template'])

        self.skills_generated.append(skill)

    def generate_skills_catalog(self):
        """生成 Skills 目录"""
        catalog = {
            'generated_at': datetime.now().isoformat(),
            'total_skills': len(self.skills_generated),
            'by_type': defaultdict(int),
            'by_topic': defaultdict(list),
            'skills': []
        }

        for skill in self.skills_generated:
            catalog['by_type'][skill['skill_type']] += 1
            catalog['by_topic'][skill['topic']].append(skill['skill_name'])

            catalog['skills'].append({
                'skill_id': skill['skill_id'],
                'skill_name': skill['skill_name'],
                'skill_title': skill['skill_title'],
                'skill_type': skill['skill_type'],
                'topic': skill['topic'],
                'pattern_count': skill['pattern_count'],
                'quality_avg': skill['quality_avg'],
                'description': skill['description']
            })

        # 转换 defaultdict 为 dict
        catalog['by_type'] = dict(catalog['by_type'])
        catalog['by_topic'] = dict(catalog['by_topic'])

        # 保存目录
        catalog_file = f"{self.output_dir}/skills_catalog.json"
        with open(catalog_file, 'w', encoding='utf-8') as f:
            json.dump(catalog, f, ensure_ascii=False, indent=2)

        return catalog

    def generate_usage_doc(self, catalog: Dict):
        """生成使用文档"""
        doc = f"""# FieldMind Skills 库使用指南

生成时间: {catalog['generated_at']}

## 概述

本 Skills 库从 {sum(catalog['by_type'].values())} 个知识模式中自动生成了 {catalog['total_skills']} 个可复用的 Skill 模板。

## Skills 分类统计

"""

        for skill_type, count in sorted(catalog['by_type'].items(), key=lambda x: x[1], reverse=True):
            type_names = {
                'process': '流程类',
                'lesson_learned': '经验教训类',
                'decision': '决策类',
                'solution': '解决方案类',
                'best_practice': '最佳实践类',
                'code_template': '代码模板类'
            }
            type_name = type_names.get(skill_type, skill_type)
            doc += f"- **{type_name}**: {count} 个\n"

        doc += f"\n## Skills 列表\n\n"

        # 按类型分组列出
        skills_by_type = defaultdict(list)
        for skill in catalog['skills']:
            skills_by_type[skill['skill_type']].append(skill)

        for skill_type, skills in sorted(skills_by_type.items()):
            type_names = {
                'process': '流程类',
                'lesson_learned': '经验教训类',
                'decision': '决策类',
                'solution': '解决方案类',
                'best_practice': '最佳实践类',
                'code_template': '代码模板类'
            }
            type_name = type_names.get(skill_type, skill_type)
            doc += f"\n### {type_name}\n\n"

            for skill in sorted(skills, key=lambda x: x['quality_avg'], reverse=True):
                doc += f"#### {skill['skill_title']}\n\n"
                doc += f"- **ID**: `{skill['skill_id']}`\n"
                doc += f"- **名称**: `{skill['skill_name']}`\n"
                doc += f"- **描述**: {skill['description']}\n"
                doc += f"- **基于模式数**: {skill['pattern_count']}\n"
                doc += f"- **平均质量分**: {skill['quality_avg']:.2f}\n"
                doc += f"- **主题**: {skill['topic']}\n"
                doc += f"- **模板文件**: `templates/{skill['skill_name']}.md`\n"
                doc += f"- **定义文件**: `skills/{skill['skill_name']}.json`\n\n"

        doc += """
## 使用方法

### 1. 查找 Skill

根据需求场景，在上述分类中找到合适的 Skill。

### 2. 查看模板

打开对应的 `templates/{skill_name}.md` 文件，查看详细模板。

### 3. 应用 Skill

将模板中的占位符替换为实际内容：
- `{{context}}`: 替换为实际场景
- `{{goal}}`: 替换为实际目标
- `{{options}}`: 替换为实际选项
- 等等

### 4. 参考原始案例

每个 Skill 都包含 `examples` 字段，列出了生成该 Skill 的原始 chunk_id，
可以在数据库中查询这些 chunk 的完整内容作为参考。

## API 使用示例

```python
# 加载 Skills 目录
import json
with open('skills_catalog.json') as f:
    catalog = json.load(f)

# 查找特定类型的 Skills
process_skills = [s for s in catalog['skills'] if s['skill_type'] == 'process']

# 加载具体 Skill
with open(f"skills/{skill_name}.json") as f:
    skill = json.load(f)

# 获取模板
template = skill['template']

# 填充参数
filled = template.replace('{{context}}', my_context)
                 .replace('{{goal}}', my_goal)
```

## 质量保证

- 所有 Skills 都基于至少 3 个实际知识模式生成
- 每个 Skill 都有质量平均分（基于原始模式的质量分）
- 建议优先使用质量分 > 0.8 的 Skills

## 更新机制

随着知识库的增长，可以定期重新运行 Skill 生成器：

```bash
python week6_skill_auto_generator.py
```

这将基于最新的知识模式更新 Skills 库。

---

**FieldMind Knowledge Reuse System**
Generated by Skill Auto Generator v1.0
"""

        doc_file = f"{self.output_dir}/SKILLS_USAGE_GUIDE.md"
        with open(doc_file, 'w', encoding='utf-8') as f:
            f.write(doc)

        return doc_file

    def run(self):
        """执行完整生成流程"""
        print("=" * 70)
        print("Week 6-7 Day 2: Skill 自动生成")
        print("=" * 70)

        # 1. 加载模式
        patterns = self.load_patterns()

        # 2. 按主题聚类
        clusters = self.cluster_by_topic(patterns)

        # 3. 为每个聚类生成 Skill
        print("\n🔨 生成 Skills...")
        generated_count = 0
        skipped_count = 0

        for topic, patterns_in_cluster in clusters.items():
            skill = self.generate_skill_from_cluster(topic, patterns_in_cluster)
            if skill:
                self.save_skill(skill)
                generated_count += 1
                print(f"   ✓ {skill['skill_name']} ({len(patterns_in_cluster)} 个模式)")
            else:
                skipped_count += 1

        print(f"\n   总计生成: {generated_count} 个 Skills")
        print(f"   跳过: {skipped_count} 个聚类（模式数 < 3）")

        # 4. 生成目录
        print("\n📚 生成 Skills 目录...")
        catalog = self.generate_skills_catalog()
        print(f"   ✓ 目录文件: {self.output_dir}/skills_catalog.json")

        # 5. 生成使用文档
        print("\n📖 生成使用指南...")
        doc_file = self.generate_usage_doc(catalog)
        print(f"   ✓ 使用指南: {doc_file}")

        # 6. 生成统计报告
        print("\n" + "=" * 70)
        print("生成完成统计")
        print("=" * 70)
        print(f"总 Skills 数: {catalog['total_skills']}")
        print("\n按类型分布:")
        for skill_type, count in sorted(catalog['by_type'].items(), key=lambda x: x[1], reverse=True):
            type_names = {
                'process': '流程类',
                'lesson_learned': '经验教训类',
                'decision': '决策类',
                'solution': '解决方案类',
                'best_practice': '最佳实践类',
                'code_template': '代码模板类'
            }
            type_name = type_names.get(skill_type, skill_type)
            print(f"  {type_name}: {count}")

        print(f"\n平均质量分: {sum(s['quality_avg'] for s in catalog['skills']) / len(catalog['skills']):.3f}")
        print(f"最高质量分: {max(s['quality_avg'] for s in catalog['skills']):.3f}")
        print(f"最低质量分: {min(s['quality_avg'] for s in catalog['skills']):.3f}")

        print("\n输出文件:")
        print(f"  - Skills 定义: {self.output_dir}/skills/ ({generated_count} 个文件)")
        print(f"  - Skills 模板: {self.output_dir}/templates/ ({generated_count} 个文件)")
        print(f"  - Skills 目录: {self.output_dir}/skills_catalog.json")
        print(f"  - 使用指南: {doc_file}")

        return catalog


def main():
    # 配置路径
    db_path = "/Users/alwan/Downloads/FieldMind/fieldmind/backend/src/data/fieldmind.db"
    patterns_file = "/Users/alwan/Downloads/FieldMind/fieldmind/knowledge_assets/knowledge_patterns_20260913_151640.json"
    output_dir = "/Users/alwan/Downloads/FieldMind/fieldmind/knowledge_assets"

    # 创建生成器
    generator = SkillAutoGenerator(db_path, patterns_file, output_dir)

    # 执行生成
    catalog = generator.run()

    print("\n✅ Skill 自动生成完成！")


if __name__ == "__main__":
    main()
