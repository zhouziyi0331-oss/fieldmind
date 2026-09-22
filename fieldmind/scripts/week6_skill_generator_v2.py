#!/usr/bin/env python3
"""
Week 6-7 Day 2: Skill 自动生成器 V2
直接基于 knowledge_patterns.json 生成 Skills，不依赖数据库元数据

功能：
1. 读取 knowledge_patterns.json
2. 按类型和内容聚类
3. 生成参数化的 Skill 模板
4. 创建 Skill 库和使用文档
"""

import json
import os
import re
from datetime import datetime
from typing import List, Dict, Optional
from collections import defaultdict


class SkillGenerator:
    """Skill 生成器（基于模式文件）"""

    def __init__(self, patterns_file: str, output_dir: str):
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

        # 统计
        stats = data.get('stats', {})
        by_type = stats.get('by_type', {})
        print(f"   按类型分布:")
        for ptype, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True):
            print(f"     - {ptype}: {count}")

        return patterns

    def extract_keywords_from_content(self, content: str) -> List[str]:
        """从内容中提取关键词"""
        # 简单的关键词提取：高频词
        words = re.findall(r'[一-龥]+', content)
        word_freq = defaultdict(int)
        for word in words:
            if len(word) >= 2:  # 至少2个字
                word_freq[word] += 1

        # 返回频率最高的前5个词
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:5]]

    def cluster_patterns(self, patterns: List[Dict]) -> Dict[str, List[Dict]]:
        """按类型和主题聚类"""
        print("\n🔍 按类型和主题聚类...")

        clusters = defaultdict(list)

        for pattern in patterns:
            pattern_type = pattern['pattern_type']
            content = pattern['content']

            # 提取关键词作为主题
            keywords = self.extract_keywords_from_content(content)

            # 生成主题标签：类型_关键词
            if keywords:
                topic = f"{pattern_type}_{keywords[0]}"
            else:
                topic = f"{pattern_type}_general"

            pattern['extracted_keywords'] = keywords
            clusters[topic].append(pattern)

        print(f"   ✓ 聚类为 {len(clusters)} 个主题")

        # 显示最大的聚类
        top_clusters = sorted(clusters.items(), key=lambda x: len(x[1]), reverse=True)[:10]
        print(f"   Top 10 聚类:")
        for topic, items in top_clusters:
            print(f"     - {topic}: {len(items)} 个模式")

        return dict(clusters)

    def generate_skill(self, topic: str, patterns: List[Dict]) -> Optional[Dict]:
        """从聚类生成 Skill"""

        # 至少需要3个模式
        if len(patterns) < 3:
            return None

        pattern_type = patterns[0]['pattern_type']

        # 根据类型生成不同的 Skill
        generators = {
            'process': self._gen_process_skill,
            'lesson_learned': self._gen_lesson_skill,
            'decision': self._gen_decision_skill,
            'solution': self._gen_solution_skill,
            'best_practice': self._gen_best_practice_skill,
            'code_template': self._gen_code_skill,
        }

        generator = generators.get(pattern_type)
        if generator:
            return generator(topic, patterns)

        return None

    def _gen_process_skill(self, topic: str, patterns: List[Dict]) -> Dict:
        """生成流程 Skill"""

        skill_name = f"process_{self._clean_topic(topic)}"
        skill_title = f"流程：{topic.replace('process_', '')}"

        # 计算平均质量
        avg_quality = sum(p['confidence'] for p in patterns) / len(patterns)

        template = self._create_process_template(patterns)

        return {
            'skill_id': f"skill_{self._gen_id()}",
            'skill_name': skill_name,
            'skill_title': skill_title,
            'skill_type': 'process',
            'topic': topic,
            'pattern_count': len(patterns),
            'quality_avg': avg_quality,
            'description': f"基于 {len(patterns)} 个实际案例的流程模板",
            'parameters': {
                'context': {'type': 'string', 'description': '应用场景'},
                'goal': {'type': 'string', 'description': '目标结果'},
            },
            'template': template,
            'examples': [p['chunk_id'] for p in patterns[:5]],
        }

    def _gen_lesson_skill(self, topic: str, patterns: List[Dict]) -> Dict:
        """生成经验教训 Skill"""

        skill_name = f"lesson_{self._clean_topic(topic)}"
        skill_title = f"经验：{topic.replace('lesson_learned_', '')}"

        avg_quality = sum(p['confidence'] for p in patterns) / len(patterns)
        template = self._create_lesson_template(patterns)

        return {
            'skill_id': f"skill_{self._gen_id()}",
            'skill_name': skill_name,
            'skill_title': skill_title,
            'skill_type': 'lesson_learned',
            'topic': topic,
            'pattern_count': len(patterns),
            'quality_avg': avg_quality,
            'description': f"基于 {len(patterns)} 个实际经验的总结",
            'parameters': {
                'situation': {'type': 'string', 'description': '类似场景'},
                'challenge': {'type': 'string', 'description': '面临挑战'},
            },
            'template': template,
            'examples': [p['chunk_id'] for p in patterns[:5]],
        }

    def _gen_decision_skill(self, topic: str, patterns: List[Dict]) -> Dict:
        """生成决策 Skill"""

        skill_name = f"decision_{self._clean_topic(topic)}"
        skill_title = f"决策：{topic.replace('decision_', '')}"

        avg_quality = sum(p['confidence'] for p in patterns) / len(patterns)
        template = self._create_decision_template(patterns)

        return {
            'skill_id': f"skill_{self._gen_id()}",
            'skill_name': skill_name,
            'skill_title': skill_title,
            'skill_type': 'decision',
            'topic': topic,
            'pattern_count': len(patterns),
            'quality_avg': avg_quality,
            'description': f"基于 {len(patterns)} 个实际决策的框架",
            'parameters': {
                'options': {'type': 'array', 'description': '可选方案'},
                'criteria': {'type': 'array', 'description': '评估标准'},
            },
            'template': template,
            'examples': [p['chunk_id'] for p in patterns[:5]],
        }

    def _gen_solution_skill(self, topic: str, patterns: List[Dict]) -> Dict:
        """生成解决方案 Skill"""

        skill_name = f"solution_{self._clean_topic(topic)}"
        skill_title = f"解决方案：{topic.replace('solution_', '')}"

        avg_quality = sum(p['confidence'] for p in patterns) / len(patterns)
        template = self._create_solution_template(patterns)

        return {
            'skill_id': f"skill_{self._gen_id()}",
            'skill_name': skill_name,
            'skill_title': skill_title,
            'skill_type': 'solution',
            'topic': topic,
            'pattern_count': len(patterns),
            'quality_avg': avg_quality,
            'description': f"基于 {len(patterns)} 个实际案例的解决方案",
            'parameters': {
                'problem': {'type': 'string', 'description': '问题描述'},
                'context': {'type': 'string', 'description': '问题场景'},
            },
            'template': template,
            'examples': [p['chunk_id'] for p in patterns[:5]],
        }

    def _gen_best_practice_skill(self, topic: str, patterns: List[Dict]) -> Dict:
        """生成最佳实践 Skill"""

        skill_name = f"best_practice_{self._clean_topic(topic)}"
        skill_title = f"最佳实践：{topic.replace('best_practice_', '')}"

        avg_quality = sum(p['confidence'] for p in patterns) / len(patterns)
        template = self._create_best_practice_template(patterns)

        return {
            'skill_id': f"skill_{self._gen_id()}",
            'skill_name': skill_name,
            'skill_title': skill_title,
            'skill_type': 'best_practice',
            'topic': topic,
            'pattern_count': len(patterns),
            'quality_avg': avg_quality,
            'description': f"基于 {len(patterns)} 个高质量案例的最佳实践",
            'parameters': {
                'domain': {'type': 'string', 'description': '应用领域'},
                'objective': {'type': 'string', 'description': '优化目标'},
            },
            'template': template,
            'examples': [p['chunk_id'] for p in patterns[:5]],
        }

    def _gen_code_skill(self, topic: str, patterns: List[Dict]) -> Dict:
        """生成代码模板 Skill"""

        skill_name = f"code_{self._clean_topic(topic)}"
        skill_title = f"代码：{topic.replace('code_template_', '')}"

        avg_quality = sum(p['confidence'] for p in patterns) / len(patterns)
        template = self._create_code_template(patterns)

        return {
            'skill_id': f"skill_{self._gen_id()}",
            'skill_name': skill_name,
            'skill_title': skill_title,
            'skill_type': 'code_template',
            'topic': topic,
            'pattern_count': len(patterns),
            'quality_avg': avg_quality,
            'description': f"基于 {len(patterns)} 个实际代码的模板",
            'parameters': {
                'language': {'type': 'string', 'description': '编程语言'},
                'use_case': {'type': 'string', 'description': '使用场景'},
            },
            'template': template,
            'examples': [p['chunk_id'] for p in patterns[:5]],
        }

    def _create_process_template(self, patterns: List[Dict]) -> str:
        """创建流程模板"""
        template = f"""# {{{{skill_title}}}}

## 适用场景
{{{{context}}}}

## 目标
{{{{goal}}}}

## 流程步骤

"""
        # 从案例中提取步骤
        for i, p in enumerate(patterns[:3], 1):
            content = p['content'][:200].replace('\n', ' ')
            template += f"### 步骤 {i}\n{content}...\n\n"

        template += """
## 关键要点
- 要点1: [从案例中总结]
- 要点2: [从案例中总结]
- 要点3: [从案例中总结]

## 参考案例
"""
        for i, p in enumerate(patterns[:5], 1):
            template += f"- 案例 {i}: {p['chunk_id']}\n"

        return template

    def _create_lesson_template(self, patterns: List[Dict]) -> str:
        """创建经验教训模板"""
        template = f"""# {{{{skill_title}}}}

## 背景场景
{{{{situation}}}}

## 面临挑战
{{{{challenge}}}}

## 关键经验

"""
        for i, p in enumerate(patterns[:3], 1):
            content = p['content'][:200].replace('\n', ' ')
            template += f"### 经验 {i}\n{content}...\n\n"

        template += """
## 避免的陷阱
- 陷阱1: [描述]
- 陷阱2: [描述]

## 参考案例
"""
        for i, p in enumerate(patterns[:5], 1):
            template += f"- {p['chunk_id']}\n"

        return template

    def _create_decision_template(self, patterns: List[Dict]) -> str:
        """创建决策模板"""
        template = f"""# {{{{skill_title}}}}

## 决策场景
[描述需要决策的场景]

## 方案评估

"""
        for i, p in enumerate(patterns[:3], 1):
            content = p['content'][:200].replace('\n', ' ')
            template += f"### 方案 {i}\n{content}...\n\n"

        template += """
## 评估标准
{{{{#each criteria}}}}
- {{{{this}}}}
{{{{/each}}}}

## 参考案例
"""
        for i, p in enumerate(patterns[:5], 1):
            template += f"- {p['chunk_id']}\n"

        return template

    def _create_solution_template(self, patterns: List[Dict]) -> str:
        """创建解决方案模板"""
        template = f"""# {{{{skill_title}}}}

## 问题描述
{{{{problem}}}}

## 解决方案

"""
        for i, p in enumerate(patterns[:3], 1):
            content = p['content'][:200].replace('\n', ' ')
            template += f"### 方案 {i}\n{content}...\n\n"

        template += """
## 实施步骤
1. [步骤1]
2. [步骤2]
3. [步骤3]

## 参考案例
"""
        for i, p in enumerate(patterns[:5], 1):
            template += f"- {p['chunk_id']}\n"

        return template

    def _create_best_practice_template(self, patterns: List[Dict]) -> str:
        """创建最佳实践模板"""
        template = f"""# {{{{skill_title}}}}

## 应用领域
{{{{domain}}}}

## 优化目标
{{{{objective}}}}

## 最佳实践

"""
        for i, p in enumerate(patterns[:3], 1):
            content = p['content'][:200].replace('\n', ' ')
            template += f"### 实践 {i}\n{content}...\n\n"

        template += """
## 衡量指标
- 指标1: [描述]
- 指标2: [描述]

## 参考案例
"""
        for i, p in enumerate(patterns[:5], 1):
            template += f"- {p['chunk_id']}\n"

        return template

    def _create_code_template(self, patterns: List[Dict]) -> str:
        """创建代码模板"""
        template = f"""# {{{{skill_title}}}}

## 编程语言
{{{{language}}}}

## 使用场景
{{{{use_case}}}}

## 代码示例

```python
# 从实际案例中提取的代码模板
"""

        # 提取第一个案例中的代码
        if patterns:
            content = patterns[0]['content']
            code_blocks = re.findall(r'```[\w]*\n(.*?)\n```', content, re.DOTALL)
            if code_blocks:
                template += code_blocks[0][:300]

        template += """
```

## 使用说明
1. [步骤1]
2. [步骤2]

## 参考案例
"""
        for i, p in enumerate(patterns[:5], 1):
            template += f"- {p['chunk_id']}\n"

        return template

    def _clean_topic(self, topic: str) -> str:
        """清理主题名称，用于文件名"""
        # 移除特殊字符，只保留字母数字和下划线
        cleaned = re.sub(r'[^\w一-龥_]', '_', topic)
        # 限制长度
        if len(cleaned) > 50:
            cleaned = cleaned[:50]
        return cleaned

    def _gen_id(self) -> str:
        """生成12位ID"""
        import uuid
        return uuid.uuid4().hex[:12]

    def save_skill(self, skill: Dict):
        """保存 Skill"""
        # 保存 JSON 定义
        skill_file = f"{self.output_dir}/skills/{skill['skill_name']}.json"
        with open(skill_file, 'w', encoding='utf-8') as f:
            json.dump(skill, f, ensure_ascii=False, indent=2)

        # 保存模板
        template_file = f"{self.output_dir}/templates/{skill['skill_name']}.md"
        with open(template_file, 'w', encoding='utf-8') as f:
            f.write(skill['template'])

        self.skills_generated.append(skill)

    def generate_catalog(self) -> Dict:
        """生成目录"""
        catalog = {
            'generated_at': datetime.now().isoformat(),
            'total_skills': len(self.skills_generated),
            'by_type': defaultdict(int),
            'skills': []
        }

        for skill in self.skills_generated:
            catalog['by_type'][skill['skill_type']] += 1
            catalog['skills'].append({
                'skill_id': skill['skill_id'],
                'skill_name': skill['skill_name'],
                'skill_title': skill['skill_title'],
                'skill_type': skill['skill_type'],
                'topic': skill['topic'],
                'pattern_count': skill['pattern_count'],
                'quality_avg': skill['quality_avg'],
                'description': skill['description'],
            })

        catalog['by_type'] = dict(catalog['by_type'])

        # 保存目录
        catalog_file = f"{self.output_dir}/skills_catalog.json"
        with open(catalog_file, 'w', encoding='utf-8') as f:
            json.dump(catalog, f, ensure_ascii=False, indent=2)

        return catalog

    def generate_usage_guide(self, catalog: Dict):
        """生成使用指南"""
        doc = f"""# FieldMind Skills 库使用指南

生成时间: {catalog['generated_at']}

## 概览

从 520 个知识模式中生成了 **{catalog['total_skills']}** 个可复用 Skill。

## 分类统计

"""
        type_names = {
            'process': '流程类',
            'lesson_learned': '经验教训类',
            'decision': '决策类',
            'solution': '解决方案类',
            'best_practice': '最佳实践类',
            'code_template': '代码模板类',
        }

        for stype, count in sorted(catalog['by_type'].items(), key=lambda x: x[1], reverse=True):
            type_name = type_names.get(stype, stype)
            print(f"- **{type_name}**: {count} 个")

        doc += "\n## Skills 列表\n\n"

        # 按类型分组
        skills_by_type = defaultdict(list)
        for skill in catalog['skills']:
            skills_by_type[skill['skill_type']].append(skill)

        for stype, skills in sorted(skills_by_type.items()):
            type_name = type_names.get(stype, stype)
            doc += f"\n### {type_name}\n\n"

            for skill in sorted(skills, key=lambda x: x['quality_avg'], reverse=True):
                doc += f"#### {skill['skill_title']}\n\n"
                doc += f"- **ID**: `{skill['skill_id']}`\n"
                doc += f"- **名称**: `{skill['skill_name']}`\n"
                doc += f"- **描述**: {skill['description']}\n"
                doc += f"- **基于模式数**: {skill['pattern_count']}\n"
                doc += f"- **平均质量**: {skill['quality_avg']:.3f}\n"
                doc += f"- **模板**: `templates/{skill['skill_name']}.md`\n"
                doc += f"- **定义**: `skills/{skill['skill_name']}.json`\n\n"

        doc += """
## 使用方法

### 1. 浏览目录
查看 `skills_catalog.json` 了解所有可用 Skills。

### 2. 选择 Skill
根据需求选择合适的 Skill 类型和主题。

### 3. 查看模板
打开 `templates/{skill_name}.md` 查看具体模板。

### 4. 应用模板
将模板中的占位符替换为实际内容。

### 5. 参考原始案例
每个 Skill 包含 `examples` 字段，列出原始 chunk_id。

## 示例代码

```python
import json

# 加载目录
with open('skills_catalog.json') as f:
    catalog = json.load(f)

# 查找流程类 Skills
process_skills = [s for s in catalog['skills']
                  if s['skill_type'] == 'process']

# 加载具体 Skill
with open('skills/process_xxx.json') as f:
    skill = json.load(f)

# 获取模板
template = skill['template']
```

---
**FieldMind Knowledge Reuse System**
Generated by Skill Generator V2
"""

        guide_file = f"{self.output_dir}/SKILLS_USAGE_GUIDE.md"
        with open(guide_file, 'w', encoding='utf-8') as f:
            f.write(doc)

        return guide_file

    def run(self):
        """执行完整流程"""
        print("=" * 70)
        print("Week 6-7 Day 2: Skill 自动生成")
        print("=" * 70)

        # 1. 加载模式
        patterns = self.load_patterns()

        # 2. 聚类
        clusters = self.cluster_patterns(patterns)

        # 3. 生成 Skills
        print("\n🔨 生成 Skills...")
        generated = 0
        skipped = 0

        for topic, cluster_patterns in clusters.items():
            skill = self.generate_skill(topic, cluster_patterns)
            if skill:
                self.save_skill(skill)
                generated += 1
                print(f"   ✓ {skill['skill_name']} ({len(cluster_patterns)} 个模式)")
            else:
                skipped += 1

        print(f"\n   总计: {generated} 个 Skills 生成")
        print(f"   跳过: {skipped} 个聚类（模式数 < 3）")

        # 4. 生成目录
        print("\n📚 生成目录...")
        catalog = self.generate_catalog()
        print(f"   ✓ {self.output_dir}/skills_catalog.json")

        # 5. 生成使用指南
        print("\n📖 生成使用指南...")
        guide = self.generate_usage_guide(catalog)
        print(f"   ✓ {guide}")

        # 6. 统计
        print("\n" + "=" * 70)
        print("生成完成")
        print("=" * 70)
        print(f"总 Skills 数: {catalog['total_skills']}")
        print("\n按类型分布:")

        type_names = {
            'process': '流程类',
            'lesson_learned': '经验教训类',
            'decision': '决策类',
            'solution': '解决方案类',
            'best_practice': '最佳实践类',
            'code_template': '代码模板类',
        }

        for stype, count in sorted(catalog['by_type'].items(), key=lambda x: x[1], reverse=True):
            type_name = type_names.get(stype, stype)
            print(f"  {type_name}: {count}")

        if catalog['skills']:
            avg_q = sum(s['quality_avg'] for s in catalog['skills']) / len(catalog['skills'])
            max_q = max(s['quality_avg'] for s in catalog['skills'])
            min_q = min(s['quality_avg'] for s in catalog['skills'])
            print(f"\n质量分布:")
            print(f"  平均: {avg_q:.3f}")
            print(f"  最高: {max_q:.3f}")
            print(f"  最低: {min_q:.3f}")

        print(f"\n输出文件:")
        print(f"  - Skills 定义: {self.output_dir}/skills/ ({generated} 个)")
        print(f"  - Skills 模板: {self.output_dir}/templates/ ({generated} 个)")
        print(f"  - Skills 目录: {self.output_dir}/skills_catalog.json")
        print(f"  - 使用指南: {guide}")

        return catalog


def main():
    patterns_file = "/Users/alwan/Downloads/FieldMind/fieldmind/knowledge_assets/knowledge_patterns_20260913_151640.json"
    output_dir = "/Users/alwan/Downloads/FieldMind/fieldmind/knowledge_assets"

    generator = SkillGenerator(patterns_file, output_dir)
    catalog = generator.run()

    print("\n✅ Skill 自动生成完成！")


if __name__ == "__main__":
    main()
