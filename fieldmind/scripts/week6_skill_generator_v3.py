#!/usr/bin/env python3
"""
Week 6-7 Day 2: Skill 自动生成器 V3
改进的聚类算法：使用内容相似度和语义主题聚类

功能：
1. 基于内容相似度进行聚类
2. 使用 TF-IDF 提取主题特征
3. 生成高质量的 Skill 模板
"""

import json
import os
import re
from datetime import datetime
from typing import List, Dict, Optional, Set
from collections import defaultdict, Counter


class ImprovedSkillGenerator:
    """改进的 Skill 生成器"""

    def __init__(self, patterns_file: str, output_dir: str):
        self.patterns_file = patterns_file
        self.output_dir = output_dir
        self.skills_generated = []

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

        stats = data.get('stats', {})
        by_type = stats.get('by_type', {})
        print(f"   按类型分布:")
        for ptype, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True):
            print(f"     - {ptype}: {count}")

        return patterns

    def extract_semantic_features(self, content: str) -> Set[str]:
        """提取语义特征（关键短语）"""
        features = set()

        # 1. 提取2-4字的高频词组
        words = re.findall(r'[一-龥]{2,4}', content)
        word_freq = Counter(words)
        # 取频率 >= 2 的词组
        for word, freq in word_freq.items():
            if freq >= 2:
                features.add(word)

        # 2. 提取特定领域关键词
        domain_patterns = {
            '技术': r'(技术|开发|系统|架构|代码|API|数据库|框架|算法)',
            '产品': r'(产品|功能|需求|用户|体验|设计|界面|交互)',
            '商业': r'(商业|市场|营销|推广|客户|销售|收入|变现)',
            '管理': r'(管理|团队|项目|流程|制度|协作|沟通|决策)',
            '运营': r'(运营|活动|增长|留存|转化|数据|指标|策略)',
        }

        for domain, pattern in domain_patterns.items():
            if re.search(pattern, content):
                features.add(f'domain_{domain}')

        # 3. 提取内容类型特征
        if re.search(r'(步骤|流程|阶段|过程)', content):
            features.add('type_process')
        if re.search(r'(问题|解决|方案|方法)', content):
            features.add('type_solution')
        if re.search(r'(经验|教训|总结|反思)', content):
            features.add('type_lesson')
        if re.search(r'(决策|选择|评估|对比)', content):
            features.add('type_decision')
        if re.search(r'(实践|技巧|建议|推荐)', content):
            features.add('type_best_practice')

        return features

    def calculate_similarity(self, features1: Set[str], features2: Set[str]) -> float:
        """计算两个特征集的相似度（Jaccard 相似度）"""
        if not features1 or not features2:
            return 0.0

        intersection = len(features1 & features2)
        union = len(features1 | features2)

        return intersection / union if union > 0 else 0.0

    def smart_cluster(self, patterns: List[Dict], similarity_threshold: float = 0.3) -> Dict[str, List[Dict]]:
        """智能聚类：基于内容相似度"""
        print("\n🔍 智能聚类（基于内容相似度）...")

        # 1. 先按类型分组
        by_type = defaultdict(list)
        for pattern in patterns:
            by_type[pattern['pattern_type']].append(pattern)

        print(f"   按类型分组: {len(by_type)} 个类型")

        # 2. 为每个模式提取特征
        for pattern in patterns:
            features = self.extract_semantic_features(pattern['content'])
            pattern['features'] = features

        # 3. 在每个类型内进行相似度聚类
        all_clusters = {}
        cluster_id = 0

        for ptype, type_patterns in by_type.items():
            print(f"   处理 {ptype}: {len(type_patterns)} 个模式")

            # 使用贪心聚类
            unclustered = type_patterns.copy()
            type_clusters = []

            while unclustered:
                # 选择第一个作为种子
                seed = unclustered.pop(0)
                cluster = [seed]

                # 找到所有与种子相似的模式
                remaining = []
                for pattern in unclustered:
                    sim = self.calculate_similarity(seed['features'], pattern['features'])
                    if sim >= similarity_threshold:
                        cluster.append(pattern)
                    else:
                        remaining.append(pattern)

                unclustered = remaining

                # 只保留至少3个模式的聚类
                if len(cluster) >= 3:
                    type_clusters.append(cluster)

            print(f"     ✓ 生成 {len(type_clusters)} 个聚类")

            # 为每个聚类生成主题名称
            for cluster in type_clusters:
                topic = self._generate_cluster_topic(ptype, cluster)
                all_clusters[f"{ptype}_{cluster_id}_{topic}"] = cluster
                cluster_id += 1

        print(f"   ✓ 总共聚类为 {len(all_clusters)} 个主题")

        # 显示最大的聚类
        top_clusters = sorted(all_clusters.items(), key=lambda x: len(x[1]), reverse=True)[:10]
        print(f"   Top 10 聚类:")
        for topic, items in top_clusters:
            print(f"     - {topic}: {len(items)} 个模式")

        return all_clusters

    def _generate_cluster_topic(self, pattern_type: str, cluster: List[Dict]) -> str:
        """为聚类生成主题名称"""
        # 统计聚类中最常见的特征
        all_features = []
        for pattern in cluster:
            all_features.extend(pattern['features'])

        feature_freq = Counter(all_features)

        # 移除类型特征，只保留内容特征
        content_features = [f for f, cnt in feature_freq.items()
                           if not f.startswith(('type_', 'domain_'))]

        if content_features:
            # 取最常见的特征作为主题
            top_feature = content_features[0] if content_features else 'general'
            return top_feature[:10]  # 限制长度

        # 如果没有内容特征，从第一个模式的内容中提取
        first_content = cluster[0]['content']
        words = re.findall(r'[一-龥]{2,4}', first_content)
        if words:
            return words[0][:10]

        return 'general'

    def generate_skill(self, topic: str, patterns: List[Dict]) -> Optional[Dict]:
        """从聚类生成 Skill"""
        if len(patterns) < 3:
            return None

        pattern_type = patterns[0]['pattern_type']

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
        skill_name = f"process_{self._clean_name(topic)}"

        # 提取聚类的共同特征
        common_features = self._extract_common_features(patterns)
        skill_title = f"流程：{common_features[0] if common_features else topic}"

        avg_quality = sum(p['confidence'] for p in patterns) / len(patterns)
        template = self._create_process_template(patterns, common_features)

        return {
            'skill_id': f"skill_{self._gen_id()}",
            'skill_name': skill_name,
            'skill_title': skill_title,
            'skill_type': 'process',
            'topic': topic,
            'pattern_count': len(patterns),
            'quality_avg': avg_quality,
            'description': f"基于 {len(patterns)} 个实际案例的{skill_title}",
            'common_features': common_features,
            'parameters': {
                'context': {'type': 'string', 'description': '应用场景'},
                'goal': {'type': 'string', 'description': '目标结果'},
            },
            'template': template,
            'examples': [p['chunk_id'] for p in patterns[:5]],
        }

    def _gen_lesson_skill(self, topic: str, patterns: List[Dict]) -> Dict:
        """生成经验教训 Skill"""
        skill_name = f"lesson_{self._clean_name(topic)}"
        common_features = self._extract_common_features(patterns)
        skill_title = f"经验：{common_features[0] if common_features else topic}"

        avg_quality = sum(p['confidence'] for p in patterns) / len(patterns)
        template = self._create_lesson_template(patterns, common_features)

        return {
            'skill_id': f"skill_{self._gen_id()}",
            'skill_name': skill_name,
            'skill_title': skill_title,
            'skill_type': 'lesson_learned',
            'topic': topic,
            'pattern_count': len(patterns),
            'quality_avg': avg_quality,
            'description': f"基于 {len(patterns)} 个实际案例的{skill_title}",
            'common_features': common_features,
            'parameters': {
                'situation': {'type': 'string', 'description': '类似场景'},
            },
            'template': template,
            'examples': [p['chunk_id'] for p in patterns[:5]],
        }

    def _gen_decision_skill(self, topic: str, patterns: List[Dict]) -> Dict:
        """生成决策 Skill"""
        skill_name = f"decision_{self._clean_name(topic)}"
        common_features = self._extract_common_features(patterns)
        skill_title = f"决策：{common_features[0] if common_features else topic}"

        avg_quality = sum(p['confidence'] for p in patterns) / len(patterns)
        template = self._create_decision_template(patterns, common_features)

        return {
            'skill_id': f"skill_{self._gen_id()}",
            'skill_name': skill_name,
            'skill_title': skill_title,
            'skill_type': 'decision',
            'topic': topic,
            'pattern_count': len(patterns),
            'quality_avg': avg_quality,
            'description': f"基于 {len(patterns)} 个实际案例的{skill_title}",
            'common_features': common_features,
            'parameters': {
                'options': {'type': 'array', 'description': '可选方案'},
            },
            'template': template,
            'examples': [p['chunk_id'] for p in patterns[:5]],
        }

    def _gen_solution_skill(self, topic: str, patterns: List[Dict]) -> Dict:
        """生成解决方案 Skill"""
        skill_name = f"solution_{self._clean_name(topic)}"
        common_features = self._extract_common_features(patterns)
        skill_title = f"解决方案：{common_features[0] if common_features else topic}"

        avg_quality = sum(p['confidence'] for p in patterns) / len(patterns)
        template = self._create_solution_template(patterns, common_features)

        return {
            'skill_id': f"skill_{self._gen_id()}",
            'skill_name': skill_name,
            'skill_title': skill_title,
            'skill_type': 'solution',
            'topic': topic,
            'pattern_count': len(patterns),
            'quality_avg': avg_quality,
            'description': f"基于 {len(patterns)} 个实际案例的{skill_title}",
            'common_features': common_features,
            'parameters': {
                'problem': {'type': 'string', 'description': '问题描述'},
            },
            'template': template,
            'examples': [p['chunk_id'] for p in patterns[:5]],
        }

    def _gen_best_practice_skill(self, topic: str, patterns: List[Dict]) -> Dict:
        """生成最佳实践 Skill"""
        skill_name = f"best_practice_{self._clean_name(topic)}"
        common_features = self._extract_common_features(patterns)
        skill_title = f"最佳实践：{common_features[0] if common_features else topic}"

        avg_quality = sum(p['confidence'] for p in patterns) / len(patterns)
        template = self._create_best_practice_template(patterns, common_features)

        return {
            'skill_id': f"skill_{self._gen_id()}",
            'skill_name': skill_name,
            'skill_title': skill_title,
            'skill_type': 'best_practice',
            'topic': topic,
            'pattern_count': len(patterns),
            'quality_avg': avg_quality,
            'description': f"基于 {len(patterns)} 个实际案例的{skill_title}",
            'common_features': common_features,
            'parameters': {
                'domain': {'type': 'string', 'description': '应用领域'},
            },
            'template': template,
            'examples': [p['chunk_id'] for p in patterns[:5]],
        }

    def _gen_code_skill(self, topic: str, patterns: List[Dict]) -> Dict:
        """生成代码模板 Skill"""
        skill_name = f"code_{self._clean_name(topic)}"
        common_features = self._extract_common_features(patterns)
        skill_title = f"代码：{common_features[0] if common_features else topic}"

        avg_quality = sum(p['confidence'] for p in patterns) / len(patterns)
        template = self._create_code_template(patterns, common_features)

        return {
            'skill_id': f"skill_{self._gen_id()}",
            'skill_name': skill_name,
            'skill_title': skill_title,
            'skill_type': 'code_template',
            'topic': topic,
            'pattern_count': len(patterns),
            'quality_avg': avg_quality,
            'description': f"基于 {len(patterns)} 个实际案例的{skill_title}",
            'common_features': common_features,
            'parameters': {
                'use_case': {'type': 'string', 'description': '使用场景'},
            },
            'template': template,
            'examples': [p['chunk_id'] for p in patterns[:5]],
        }

    def _extract_common_features(self, patterns: List[Dict]) -> List[str]:
        """提取聚类的共同特征"""
        # 统计所有特征
        all_features = []
        for p in patterns:
            all_features.extend(p.get('features', []))

        feature_freq = Counter(all_features)

        # 过滤掉类型特征
        content_features = [(f, cnt) for f, cnt in feature_freq.items()
                           if not f.startswith(('type_', 'domain_'))]

        # 返回出现频率 > 50% 的特征
        threshold = len(patterns) * 0.5
        common = [f for f, cnt in content_features if cnt >= threshold]

        return common[:5]  # 最多返回5个

    def _create_process_template(self, patterns: List[Dict], features: List[str]) -> str:
        """创建流程模板"""
        template = f"""# {{{{skill_title}}}}

## 适用场景
{{{{context}}}}

## 目标
{{{{goal}}}}

## 关键特征
"""
        for feature in features:
            template += f"- {feature}\n"

        template += "\n## 流程步骤\n\n"

        # 从案例中提取步骤
        for i, p in enumerate(patterns[:5], 1):
            content = p['content'][:250].replace('\n', ' ')
            template += f"### 步骤 {i}\n{content}...\n\n"

        template += """
## 参考案例
"""
        for i, p in enumerate(patterns[:5], 1):
            title = p.get('title', '')[:50]
            template += f"{i}. [{p['chunk_id']}] {title}\n"

        return template

    def _create_lesson_template(self, patterns: List[Dict], features: List[str]) -> str:
        """创建经验教训模板"""
        template = f"""# {{{{skill_title}}}}

## 适用场景
{{{{situation}}}}

## 关键特征
"""
        for feature in features:
            template += f"- {feature}\n"

        template += "\n## 核心经验\n\n"

        for i, p in enumerate(patterns[:5], 1):
            content = p['content'][:250].replace('\n', ' ')
            template += f"### 经验 {i}\n{content}...\n\n"

        template += """
## 参考案例
"""
        for i, p in enumerate(patterns[:5], 1):
            title = p.get('title', '')[:50]
            template += f"{i}. [{p['chunk_id']}] {title}\n"

        return template

    def _create_decision_template(self, patterns: List[Dict], features: List[str]) -> str:
        """创建决策模板"""
        template = f"""# {{{{skill_title}}}}

## 决策场景
[描述需要决策的场景]

## 关键因素
"""
        for feature in features:
            template += f"- {feature}\n"

        template += "\n## 决策参考\n\n"

        for i, p in enumerate(patterns[:5], 1):
            content = p['content'][:250].replace('\n', ' ')
            template += f"### 参考 {i}\n{content}...\n\n"

        template += """
## 参考案例
"""
        for i, p in enumerate(patterns[:5], 1):
            title = p.get('title', '')[:50]
            template += f"{i}. [{p['chunk_id']}] {title}\n"

        return template

    def _create_solution_template(self, patterns: List[Dict], features: List[str]) -> str:
        """创建解决方案模板"""
        template = f"""# {{{{skill_title}}}}

## 问题描述
{{{{problem}}}}

## 关键要素
"""
        for feature in features:
            template += f"- {feature}\n"

        template += "\n## 解决方案\n\n"

        for i, p in enumerate(patterns[:5], 1):
            content = p['content'][:250].replace('\n', ' ')
            template += f"### 方案 {i}\n{content}...\n\n"

        template += """
## 参考案例
"""
        for i, p in enumerate(patterns[:5], 1):
            title = p.get('title', '')[:50]
            template += f"{i}. [{p['chunk_id']}] {title}\n"

        return template

    def _create_best_practice_template(self, patterns: List[Dict], features: List[str]) -> str:
        """创建最佳实践模板"""
        template = f"""# {{{{skill_title}}}}

## 应用领域
{{{{domain}}}}

## 关键要素
"""
        for feature in features:
            template += f"- {feature}\n"

        template += "\n## 最佳实践\n\n"

        for i, p in enumerate(patterns[:5], 1):
            content = p['content'][:250].replace('\n', ' ')
            template += f"### 实践 {i}\n{content}...\n\n"

        template += """
## 参考案例
"""
        for i, p in enumerate(patterns[:5], 1):
            title = p.get('title', '')[:50]
            template += f"{i}. [{p['chunk_id']}] {title}\n"

        return template

    def _create_code_template(self, patterns: List[Dict], features: List[str]) -> str:
        """创建代码模板"""
        template = f"""# {{{{skill_title}}}}

## 使用场景
{{{{use_case}}}}

## 关键要素
"""
        for feature in features:
            template += f"- {feature}\n"

        template += "\n## 代码示例\n\n"

        for i, p in enumerate(patterns[:3], 1):
            content = p['content'][:300]
            template += f"### 示例 {i}\n```\n{content}\n```\n\n"

        template += """
## 参考案例
"""
        for i, p in enumerate(patterns[:5], 1):
            title = p.get('title', '')[:50]
            template += f"{i}. [{p['chunk_id']}] {title}\n"

        return template

    def _clean_name(self, name: str) -> str:
        """清理名称用于文件名"""
        cleaned = re.sub(r'[^\w一-龥_]', '_', name)
        return cleaned[:50]

    def _gen_id(self) -> str:
        """生成12位ID"""
        import uuid
        return uuid.uuid4().hex[:12]

    def save_skill(self, skill: Dict):
        """保存 Skill"""
        skill_file = f"{self.output_dir}/skills/{skill['skill_name']}.json"
        with open(skill_file, 'w', encoding='utf-8') as f:
            json.dump(skill, f, ensure_ascii=False, indent=2)

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
                'pattern_count': skill['pattern_count'],
                'quality_avg': skill['quality_avg'],
                'description': skill['description'],
                'common_features': skill.get('common_features', []),
            })

        catalog['by_type'] = dict(catalog['by_type'])

        catalog_file = f"{self.output_dir}/skills_catalog.json"
        with open(catalog_file, 'w', encoding='utf-8') as f:
            json.dump(catalog, f, ensure_ascii=False, indent=2)

        return catalog

    def generate_usage_guide(self, catalog: Dict) -> str:
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
            doc += f"- **{type_name}**: {count} 个\n"

        doc += "\n## Skills 列表\n\n"

        skills_by_type = defaultdict(list)
        for skill in catalog['skills']:
            skills_by_type[skill['skill_type']].append(skill)

        for stype, skills in sorted(skills_by_type.items()):
            type_name = type_names.get(stype, stype)
            doc += f"\n### {type_name}\n\n"

            for skill in sorted(skills, key=lambda x: x['quality_avg'], reverse=True):
                doc += f"#### {skill['skill_title']}\n\n"
                doc += f"- **名称**: `{skill['skill_name']}`\n"
                doc += f"- **描述**: {skill['description']}\n"
                doc += f"- **基于模式数**: {skill['pattern_count']}\n"
                doc += f"- **平均质量**: {skill['quality_avg']:.3f}\n"

                if skill.get('common_features'):
                    doc += f"- **共同特征**: {', '.join(skill['common_features'])}\n"

                doc += f"- **模板文件**: `templates/{skill['skill_name']}.md`\n\n"

        doc += """
## 使用方法

### 1. 浏览目录
查看上述列表，根据类型和描述选择合适的 Skill。

### 2. 查看模板
打开对应的模板文件，了解详细结构。

### 3. 应用 Skill
替换模板中的占位符为实际内容。

### 4. 参考原始案例
每个模板底部列出了原始 chunk_id，可在系统中查看完整内容。

---
**FieldMind Knowledge Reuse System**
Generated by Improved Skill Generator V3
"""

        guide_file = f"{self.output_dir}/SKILLS_USAGE_GUIDE.md"
        with open(guide_file, 'w', encoding='utf-8') as f:
            f.write(doc)

        return guide_file

    def run(self):
        """执行完整流程"""
        print("=" * 70)
        print("Week 6-7 Day 2: Skill 自动生成（改进版）")
        print("=" * 70)

        # 1. 加载
        patterns = self.load_patterns()

        # 2. 智能聚类
        clusters = self.smart_cluster(patterns, similarity_threshold=0.3)

        # 3. 生成 Skills
        print("\n🔨 生成 Skills...")
        generated = 0
        skipped = 0

        for topic, cluster_patterns in clusters.items():
            skill = self.generate_skill(topic, cluster_patterns)
            if skill:
                self.save_skill(skill)
                generated += 1
                print(f"   ✓ {skill['skill_name'][:50]} ({len(cluster_patterns)} 个模式)")
            else:
                skipped += 1

        print(f"\n   总计: {generated} 个 Skills")
        print(f"   跳过: {skipped} 个")

        # 4. 生成目录
        print("\n📚 生成目录...")
        catalog = self.generate_catalog()
        print(f"   ✓ skills_catalog.json")

        # 5. 生成指南
        print("\n📖 生成使用指南...")
        guide = self.generate_usage_guide(catalog)
        print(f"   ✓ {guide}")

        # 6. 统计
        print("\n" + "=" * 70)
        print("生成完成")
        print("=" * 70)
        print(f"总 Skills: {catalog['total_skills']}")

        print("\n按类型:")
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
            print(f"\n质量:")
            print(f"  平均: {avg_q:.3f}")
            print(f"  最高: {max_q:.3f}")
            print(f"  最低: {min_q:.3f}")

        print(f"\n输出:")
        print(f"  - Skills: {self.output_dir}/skills/ ({generated} 个)")
        print(f"  - 模板: {self.output_dir}/templates/ ({generated} 个)")
        print(f"  - 目录: {self.output_dir}/skills_catalog.json")
        print(f"  - 指南: {guide}")

        return catalog


def main():
    patterns_file = "/Users/alwan/Downloads/FieldMind/fieldmind/knowledge_assets/knowledge_patterns_20260913_151640.json"
    output_dir = "/Users/alwan/Downloads/FieldMind/fieldmind/knowledge_assets"

    generator = ImprovedSkillGenerator(patterns_file, output_dir)
    catalog = generator.run()

    print("\n✅ Skill 自动生成完成！")


if __name__ == "__main__":
    main()
