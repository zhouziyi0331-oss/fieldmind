#!/usr/bin/env python3
"""
Week 6-7 Day 3: 知识资产库建设

功能：
1. 知识资产分类和标注
2. 构建全文搜索索引
3. 知识资产推荐系统
4. 知识资产 API
5. 知识资产管理界面数据
"""

import json
import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional, Set, Tuple
from collections import defaultdict, Counter
import re


class KnowledgeAssetLibrary:
    """知识资产库"""

    def __init__(self, db_path: str, patterns_file: str, skills_catalog: str, output_dir: str):
        self.db_path = db_path
        self.patterns_file = patterns_file
        self.skills_catalog = skills_catalog
        self.output_dir = output_dir

        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(f"{output_dir}/indexes", exist_ok=True)
        os.makedirs(f"{output_dir}/api_data", exist_ok=True)

    def load_data(self) -> Tuple[List[Dict], List[Dict]]:
        """加载知识模式和 Skills"""
        print("📖 加载数据...")

        # 加载知识模式
        with open(self.patterns_file, 'r', encoding='utf-8') as f:
            patterns_data = json.load(f)
        patterns = patterns_data['patterns']

        # 加载 Skills
        with open(self.skills_catalog, 'r', encoding='utf-8') as f:
            skills_data = json.load(f)
        skills = skills_data['skills']

        print(f"   ✓ 加载了 {len(patterns)} 个知识模式")
        print(f"   ✓ 加载了 {len(skills)} 个 Skills")

        return patterns, skills

    def classify_assets(self, patterns: List[Dict]) -> Dict[str, List[Dict]]:
        """知识资产分类"""
        print("\n🏷️  知识资产分类...")

        classified = {
            'by_domain': defaultdict(list),
            'by_quality': defaultdict(list),
            'by_type': defaultdict(list),
            'by_length': defaultdict(list),
        }

        for pattern in patterns:
            content = pattern['content']
            ptype = pattern['pattern_type']
            quality = pattern['confidence']

            # 按领域分类
            domain = self._classify_domain(content)
            classified['by_domain'][domain].append(pattern)
            pattern['domain'] = domain

            # 按质量分级
            quality_level = self._classify_quality(quality)
            classified['by_quality'][quality_level].append(pattern)
            pattern['quality_level'] = quality_level

            # 按类型分类
            classified['by_type'][ptype].append(pattern)

            # 按长度分类
            length_category = self._classify_length(len(content))
            classified['by_length'][length_category].append(pattern)
            pattern['length_category'] = length_category

        # 转换 defaultdict 为 dict
        result = {}
        for key, value in classified.items():
            result[key] = dict(value)

        # 统计
        print(f"   按领域分布:")
        for domain, items in sorted(result['by_domain'].items(), key=lambda x: len(x[1]), reverse=True):
            print(f"     - {domain}: {len(items)}")

        print(f"   按质量分布:")
        for quality, items in sorted(result['by_quality'].items()):
            print(f"     - {quality}: {len(items)}")

        return result

    def _classify_domain(self, content: str) -> str:
        """领域分类"""
        domain_keywords = {
            '技术开发': ['技术', '开发', '系统', '架构', '代码', 'API', '数据库', '框架', '算法', '编程'],
            '产品设计': ['产品', '功能', '需求', '用户', '体验', '设计', '界面', '交互', '原型'],
            '商业运营': ['商业', '市场', '营销', '推广', '客户', '销售', '收入', '变现', '运营'],
            '项目管理': ['管理', '团队', '项目', '流程', '制度', '协作', '沟通', '决策', '计划'],
            '数据分析': ['数据', '分析', '指标', '报表', '统计', '预测', '建模', '可视化'],
            '内容创作': ['内容', '文案', '创作', '写作', '编辑', '素材', '故事', '脚本'],
        }

        for domain, keywords in domain_keywords.items():
            if any(kw in content for kw in keywords):
                return domain

        return '通用'

    def _classify_quality(self, quality: float) -> str:
        """质量分级"""
        if quality >= 0.8:
            return '高质量'
        elif quality >= 0.7:
            return '中等质量'
        else:
            return '基础质量'

    def _classify_length(self, length: int) -> str:
        """长度分类"""
        if length >= 500:
            return '详细'
        elif length >= 200:
            return '中等'
        else:
            return '简短'

    def build_search_index(self, patterns: List[Dict]) -> Dict:
        """构建全文搜索索引"""
        print("\n🔍 构建搜索索引...")

        # 倒排索引：词 -> [chunk_ids]
        inverted_index = defaultdict(set)

        # 词频统计：chunk_id -> {word: freq}
        term_frequencies = {}

        # 文档长度：chunk_id -> length
        doc_lengths = {}

        for pattern in patterns:
            chunk_id = pattern['chunk_id']
            content = pattern['content']

            # 分词
            words = self._tokenize(content)

            # 词频统计
            word_freq = Counter(words)
            term_frequencies[chunk_id] = dict(word_freq)

            # 文档长度
            doc_lengths[chunk_id] = len(words)

            # 构建倒排索引
            for word in set(words):
                inverted_index[word].add(chunk_id)

        # 转换 set 为 list
        inverted_index_serializable = {}
        for word, chunk_ids in inverted_index.items():
            inverted_index_serializable[word] = list(chunk_ids)

        index = {
            'inverted_index': inverted_index_serializable,
            'term_frequencies': term_frequencies,
            'doc_lengths': doc_lengths,
            'total_docs': len(patterns),
            'avg_doc_length': sum(doc_lengths.values()) / len(doc_lengths) if doc_lengths else 0,
        }

        print(f"   ✓ 索引词数: {len(inverted_index_serializable)}")
        print(f"   ✓ 文档数: {index['total_docs']}")
        print(f"   ✓ 平均文档长度: {index['avg_doc_length']:.1f} 词")

        # 保存索引
        index_file = f"{self.output_dir}/indexes/search_index.json"
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)

        print(f"   ✓ 保存到: {index_file}")

        return index

    def _tokenize(self, text: str) -> List[str]:
        """简单分词"""
        # 提取中文词（2-4字）
        words = re.findall(r'[一-龥]{2,4}', text)
        # 提取英文词
        words.extend(re.findall(r'[a-zA-Z]{2,}', text.lower()))
        return words

    def build_recommendation_system(self, patterns: List[Dict]) -> Dict:
        """构建推荐系统"""
        print("\n💡 构建推荐系统...")

        # 1. 基于相似度的推荐
        similarity_graph = self._build_similarity_graph(patterns)

        # 2. 基于协同过滤的推荐（模拟）
        collaborative_recommendations = self._build_collaborative_recommendations(patterns)

        # 3. 热门推荐
        popular_items = self._build_popular_recommendations(patterns)

        recommendations = {
            'similarity_based': similarity_graph,
            'collaborative': collaborative_recommendations,
            'popular': popular_items,
        }

        # 保存
        rec_file = f"{self.output_dir}/indexes/recommendations.json"
        with open(rec_file, 'w', encoding='utf-8') as f:
            json.dump(recommendations, f, ensure_ascii=False, indent=2)

        print(f"   ✓ 保存到: {rec_file}")

        return recommendations

    def _build_similarity_graph(self, patterns: List[Dict]) -> Dict[str, List[Dict]]:
        """构建相似度图"""
        print("   构建相似度图...")

        graph = {}

        # 为每个模式提取特征
        for pattern in patterns:
            pattern['features'] = set(self._tokenize(pattern['content']))

        # 计算每个模式的 Top 5 相似模式
        for i, pattern in enumerate(patterns):
            chunk_id = pattern['chunk_id']
            similarities = []

            for j, other in enumerate(patterns):
                if i == j:
                    continue

                sim = self._jaccard_similarity(pattern['features'], other['features'])
                if sim > 0.1:  # 相似度阈值
                    similarities.append({
                        'chunk_id': other['chunk_id'],
                        'similarity': sim,
                        'title': other.get('title', '')[:50],
                        'type': other['pattern_type'],
                    })

            # 取 Top 5
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            graph[chunk_id] = similarities[:5]

        print(f"     ✓ 为 {len(graph)} 个模式生成推荐")

        return graph

    def _jaccard_similarity(self, set1: Set, set2: Set) -> float:
        """Jaccard 相似度"""
        if not set1 or not set2:
            return 0.0
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        return intersection / union if union > 0 else 0.0

    def _build_collaborative_recommendations(self, patterns: List[Dict]) -> Dict:
        """协同过滤推荐（简化版）"""
        print("   构建协同过滤推荐...")

        # 按类型和领域分组
        by_type_domain = defaultdict(list)

        for pattern in patterns:
            ptype = pattern['pattern_type']
            domain = pattern.get('domain', '通用')
            key = f"{ptype}_{domain}"
            by_type_domain[key].append(pattern['chunk_id'])

        # 为每个组推荐同类型同领域的其他内容
        recommendations = {}
        for pattern in patterns:
            chunk_id = pattern['chunk_id']
            ptype = pattern['pattern_type']
            domain = pattern.get('domain', '通用')
            key = f"{ptype}_{domain}"

            # 同类型同领域的其他内容
            candidates = [cid for cid in by_type_domain[key] if cid != chunk_id]

            # 随机选5个
            import random
            recommendations[chunk_id] = random.sample(candidates, min(5, len(candidates)))

        print(f"     ✓ 为 {len(recommendations)} 个模式生成协同推荐")

        return recommendations

    def _build_popular_recommendations(self, patterns: List[Dict]) -> List[Dict]:
        """热门推荐"""
        print("   构建热门推荐...")

        # 按质量分排序，取 Top 20
        sorted_patterns = sorted(patterns, key=lambda x: x['confidence'], reverse=True)

        popular = []
        for pattern in sorted_patterns[:20]:
            popular.append({
                'chunk_id': pattern['chunk_id'],
                'title': pattern.get('title', '')[:50],
                'type': pattern['pattern_type'],
                'quality': pattern['confidence'],
                'domain': pattern.get('domain', '通用'),
            })

        print(f"     ✓ 选取了 Top {len(popular)} 热门内容")

        return popular

    def generate_api_data(self, patterns: List[Dict], skills: List[Dict], classified: Dict) -> Dict:
        """生成 API 数据"""
        print("\n🌐 生成 API 数据...")

        api_data = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'total_patterns': len(patterns),
                'total_skills': len(skills),
                'version': '1.0',
            },
            'summary': {
                'patterns_by_domain': {k: len(v) for k, v in classified['by_domain'].items()},
                'patterns_by_quality': {k: len(v) for k, v in classified['by_quality'].items()},
                'patterns_by_type': {k: len(v) for k, v in classified['by_type'].items()},
                'skills_by_type': self._count_skills_by_type(skills),
            },
            'patterns': [],
            'skills': skills,
        }

        # 为每个模式生成 API 记录
        for pattern in patterns:
            api_record = {
                'chunk_id': pattern['chunk_id'],
                'title': pattern.get('title', '')[:100],
                'content_preview': pattern['content'][:200],
                'content_length': len(pattern['content']),
                'pattern_type': pattern['pattern_type'],
                'quality': pattern['confidence'],
                'quality_level': pattern.get('quality_level', ''),
                'domain': pattern.get('domain', '通用'),
                'length_category': pattern.get('length_category', ''),
                'metadata': pattern.get('metadata', {}),
            }
            api_data['patterns'].append(api_record)

        # 保存
        api_file = f"{self.output_dir}/api_data/knowledge_assets_api.json"
        with open(api_file, 'w', encoding='utf-8') as f:
            json.dump(api_data, f, ensure_ascii=False, indent=2)

        print(f"   ✓ 保存到: {api_file}")

        return api_data

    def _count_skills_by_type(self, skills: List[Dict]) -> Dict[str, int]:
        """统计 Skills 类型分布"""
        counter = Counter([s['skill_type'] for s in skills])
        return dict(counter)

    def generate_statistics(self, patterns: List[Dict], skills: List[Dict], classified: Dict) -> Dict:
        """生成统计报告"""
        print("\n📊 生成统计报告...")

        stats = {
            'overview': {
                'total_patterns': len(patterns),
                'total_skills': len(skills),
                'avg_pattern_quality': sum(p['confidence'] for p in patterns) / len(patterns),
                'avg_skill_quality': sum(s['quality_avg'] for s in skills) / len(skills),
            },
            'patterns': {
                'by_domain': {k: len(v) for k, v in classified['by_domain'].items()},
                'by_quality': {k: len(v) for k, v in classified['by_quality'].items()},
                'by_type': {k: len(v) for k, v in classified['by_type'].items()},
                'by_length': {k: len(v) for k, v in classified['by_length'].items()},
            },
            'skills': {
                'by_type': self._count_skills_by_type(skills),
                'avg_patterns_per_skill': sum(s['pattern_count'] for s in skills) / len(skills),
                'total_pattern_coverage': sum(s['pattern_count'] for s in skills),
            },
            'quality_distribution': self._calculate_quality_distribution(patterns),
            'top_patterns': self._get_top_patterns(patterns, 10),
            'top_skills': self._get_top_skills(skills, 10),
        }

        # 保存
        stats_file = f"{self.output_dir}/knowledge_assets_statistics.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)

        print(f"   ✓ 保存到: {stats_file}")

        return stats

    def _calculate_quality_distribution(self, patterns: List[Dict]) -> Dict:
        """计算质量分布"""
        qualities = [p['confidence'] for p in patterns]
        return {
            'min': min(qualities),
            'max': max(qualities),
            'avg': sum(qualities) / len(qualities),
            'median': sorted(qualities)[len(qualities) // 2],
        }

    def _get_top_patterns(self, patterns: List[Dict], n: int) -> List[Dict]:
        """获取 Top N 模式"""
        sorted_patterns = sorted(patterns, key=lambda x: x['confidence'], reverse=True)
        return [{
            'chunk_id': p['chunk_id'],
            'title': p.get('title', '')[:50],
            'type': p['pattern_type'],
            'quality': p['confidence'],
            'domain': p.get('domain', '通用'),
        } for p in sorted_patterns[:n]]

    def _get_top_skills(self, skills: List[Dict], n: int) -> List[Dict]:
        """获取 Top N Skills"""
        sorted_skills = sorted(skills, key=lambda x: x['quality_avg'], reverse=True)
        return [{
            'skill_name': s['skill_name'],
            'skill_title': s['skill_title'],
            'type': s['skill_type'],
            'quality': s['quality_avg'],
            'pattern_count': s['pattern_count'],
        } for s in sorted_skills[:n]]

    def generate_usage_dashboard_data(self, patterns: List[Dict], skills: List[Dict], classified: Dict, stats: Dict) -> Dict:
        """生成使用仪表板数据"""
        print("\n📈 生成使用仪表板数据...")

        dashboard = {
            'kpi': {
                'total_assets': len(patterns) + len(skills),
                'total_patterns': len(patterns),
                'total_skills': len(skills),
                'avg_quality': stats['overview']['avg_pattern_quality'],
                'high_quality_count': len(classified['by_quality'].get('高质量', [])),
                'high_quality_rate': len(classified['by_quality'].get('高质量', [])) / len(patterns) * 100,
            },
            'charts': {
                'domain_distribution': {
                    'labels': list(stats['patterns']['by_domain'].keys()),
                    'values': list(stats['patterns']['by_domain'].values()),
                },
                'quality_distribution': {
                    'labels': list(stats['patterns']['by_quality'].keys()),
                    'values': list(stats['patterns']['by_quality'].values()),
                },
                'type_distribution': {
                    'labels': list(stats['patterns']['by_type'].keys()),
                    'values': list(stats['patterns']['by_type'].values()),
                },
                'skill_type_distribution': {
                    'labels': list(stats['skills']['by_type'].keys()),
                    'values': list(stats['skills']['by_type'].values()),
                },
            },
            'top_items': {
                'top_patterns': stats['top_patterns'],
                'top_skills': stats['top_skills'],
            },
            'recommendations': {
                'featured_skills': [s for s in stats['top_skills'][:5]],
                'trending_patterns': [p for p in stats['top_patterns'][:10]],
            },
        }

        # 保存
        dashboard_file = f"{self.output_dir}/api_data/dashboard_data.json"
        with open(dashboard_file, 'w', encoding='utf-8') as f:
            json.dump(dashboard, f, ensure_ascii=False, indent=2)

        print(f"   ✓ 保存到: {dashboard_file}")

        return dashboard

    def generate_usage_guide(self) -> str:
        """生成知识资产库使用指南"""
        print("\n📖 生成使用指南...")

        guide = """# FieldMind 知识资产库使用指南

## 概览

知识资产库是 FieldMind 知识复用系统的核心组件，提供：
- 📚 知识模式（Patterns）管理
- 🎯 技能模板（Skills）库
- 🔍 全文搜索引擎
- 💡 智能推荐系统
- 🌐 RESTful API

---

## 一、知识资产分类

### 1. 按领域分类
- **技术开发**: 代码、架构、系统相关
- **产品设计**: 需求、交互、体验相关
- **商业运营**: 市场、销售、运营相关
- **项目管理**: 流程、协作、管理相关
- **数据分析**: 指标、统计、分析相关
- **内容创作**: 文案、素材、创作相关
- **通用**: 跨领域知识

### 2. 按质量分级
- **高质量** (≥0.8): 精品内容，可直接复用
- **中等质量** (0.7-0.8): 良好内容，需适度调整
- **基础质量** (<0.7): 参考内容，需大幅改进

### 3. 按类型分类
- **process**: 流程模板
- **lesson_learned**: 经验教训
- **decision**: 决策框架
- **solution**: 解决方案
- **best_practice**: 最佳实践
- **code_template**: 代码模板

### 4. 按长度分类
- **详细** (≥500字): 完整详尽
- **中等** (200-500字): 适中
- **简短** (<200字): 简明扼要

---

## 二、搜索功能

### 1. 全文搜索

使用搜索索引 `indexes/search_index.json`：

```python
import json

# 加载索引
with open('indexes/search_index.json') as f:
    index = json.load(f)

# 搜索关键词
def search(query: str) -> List[str]:
    words = tokenize(query)
    inverted_index = index['inverted_index']

    # 找到包含查询词的文档
    doc_sets = [set(inverted_index.get(word, [])) for word in words]

    # 交集：同时包含所有词
    if doc_sets:
        results = set.intersection(*doc_sets)
        return list(results)

    return []

# 示例
results = search("数据 分析 流程")
print(f"找到 {len(results)} 个相关文档")
```

### 2. 按分类筛选

```python
# 加载 API 数据
with open('api_data/knowledge_assets_api.json') as f:
    api_data = json.load(f)

# 筛选高质量技术内容
high_quality_tech = [
    p for p in api_data['patterns']
    if p['domain'] == '技术开发' and p['quality_level'] == '高质量'
]

print(f"找到 {len(high_quality_tech)} 个高质量技术内容")
```

---

## 三、推荐系统

### 1. 基于相似度推荐

```python
# 加载推荐数据
with open('indexes/recommendations.json') as f:
    recommendations = json.load(f)

# 获取相似内容
chunk_id = "chk_abc123"
similar_items = recommendations['similarity_based'].get(chunk_id, [])

print(f"与 {chunk_id} 相似的内容:")
for item in similar_items:
    print(f"  - {item['chunk_id']}: 相似度 {item['similarity']:.2f}")
```

### 2. 热门推荐

```python
popular_items = recommendations['popular']

print("热门内容 Top 10:")
for i, item in enumerate(popular_items[:10], 1):
    print(f"{i}. [{item['type']}] {item['title']} (质量: {item['quality']:.2f})")
```

---

## 四、Skills 使用

### 1. 浏览 Skills

```python
# 加载 Skills 目录
with open('skills_catalog.json') as f:
    catalog = json.load(f)

# 按类型查找
process_skills = [
    s for s in catalog['skills']
    if s['skill_type'] == 'process'
]

print(f"找到 {len(process_skills)} 个流程类 Skills")
```

### 2. 应用 Skill 模板

```python
# 加载具体 Skill
skill_name = "solution_solution_7_通过社群"
with open(f'skills/{skill_name}.json') as f:
    skill = json.load(f)

# 获取模板
template = skill['template']

# 替换占位符
filled = template.replace('{{problem}}', '如何提升用户活跃度')

# 查看参考案例
for example_id in skill['examples']:
    print(f"参考案例: {example_id}")
```

---

## 五、API 使用

### 1. 数据结构

**API 数据文件**: `api_data/knowledge_assets_api.json`

```json
{
  "metadata": {
    "generated_at": "2026-09-13T...",
    "total_patterns": 520,
    "total_skills": 8,
    "version": "1.0"
  },
  "summary": {
    "patterns_by_domain": {...},
    "patterns_by_quality": {...},
    "skills_by_type": {...}
  },
  "patterns": [...],
  "skills": [...]
}
```

### 2. RESTful API 设计（建议）

```python
# GET /api/patterns
# 获取所有知识模式
# 查询参数: domain, quality_level, pattern_type, limit, offset

# GET /api/patterns/{chunk_id}
# 获取单个知识模式详情

# GET /api/patterns/search?q=关键词
# 搜索知识模式

# GET /api/patterns/{chunk_id}/recommendations
# 获取相似推荐

# GET /api/skills
# 获取所有 Skills

# GET /api/skills/{skill_name}
# 获取单个 Skill 详情

# GET /api/dashboard
# 获取仪表板数据
```

### 3. 示例实现

```python
from flask import Flask, jsonify, request
import json

app = Flask(__name__)

# 加载数据
with open('api_data/knowledge_assets_api.json') as f:
    api_data = json.load(f)

@app.route('/api/patterns', methods=['GET'])
def get_patterns():
    domain = request.args.get('domain')
    quality_level = request.args.get('quality_level')

    patterns = api_data['patterns']

    # 筛选
    if domain:
        patterns = [p for p in patterns if p['domain'] == domain]
    if quality_level:
        patterns = [p for p in patterns if p['quality_level'] == quality_level]

    return jsonify(patterns)

@app.route('/api/patterns/<chunk_id>', methods=['GET'])
def get_pattern(chunk_id):
    for pattern in api_data['patterns']:
        if pattern['chunk_id'] == chunk_id:
            return jsonify(pattern)
    return jsonify({'error': 'Not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)
```

---

## 六、仪表板数据

**仪表板数据文件**: `api_data/dashboard_data.json`

包含：
- **KPI 指标**: 总资产数、平均质量、高质量占比
- **图表数据**: 领域分布、质量分布、类型分布
- **Top 榜单**: 热门模式、热门 Skills
- **推荐内容**: 精选 Skills、趋势模式

---

## 七、知识复用流程

### 典型工作流

```
1. 识别需求
   ↓
2. 搜索知识资产
   - 关键词搜索
   - 分类筛选
   ↓
3. 选择合适内容
   - 查看相似推荐
   - 对比多个候选
   ↓
4. 应用 Skill/Pattern
   - 填充模板
   - 查看参考案例
   ↓
5. 定制化调整
   - 适配具体场景
   - 优化内容质量
   ↓
6. 记录复用情况
   - 更新使用次数
   - 收集反馈
```

---

## 八、数据更新

### 增量更新

当有新的知识内容时：

```bash
# 1. 重新运行知识模式识别
python scripts/week6_knowledge_pattern_recognition.py

# 2. 重新生成 Skills
python scripts/week6_skill_generator_v3.py

# 3. 重新构建知识资产库
python scripts/week6_knowledge_asset_library.py
```

---

## 九、文件结构

```
knowledge_assets/
├── knowledge_patterns_*.json         # 知识模式原始数据
├── skills_catalog.json               # Skills 目录
├── knowledge_assets_statistics.json  # 统计数据
├── SKILLS_USAGE_GUIDE.md            # Skills 使用指南
├── KNOWLEDGE_ASSETS_GUIDE.md        # 本文件
│
├── skills/                          # Skills 定义（JSON）
│   ├── lesson_*.json
│   ├── decision_*.json
│   ├── process_*.json
│   └── solution_*.json
│
├── templates/                       # Skills 模板（Markdown）
│   ├── lesson_*.md
│   ├── decision_*.md
│   ├── process_*.md
│   └── solution_*.md
│
├── indexes/                         # 索引文件
│   ├── search_index.json           # 全文搜索索引
│   └── recommendations.json        # 推荐数据
│
└── api_data/                        # API 数据
    ├── knowledge_assets_api.json   # 完整 API 数据
    └── dashboard_data.json         # 仪表板数据
```

---

## 十、最佳实践

### 1. 搜索技巧
- 使用多个关键词提高精确度
- 先按分类筛选，再全文搜索
- 利用质量分级快速定位优质内容

### 2. Skill 应用
- 优先选择高质量、多案例支撑的 Skills
- 仔细阅读参考案例，理解应用场景
- 模板仅是起点，需结合实际情况调整

### 3. 推荐系统
- 相似度推荐适合深入探索某个主题
- 热门推荐适合快速了解优质内容
- 协同推荐适合发现跨领域关联

### 4. 质量保证
- 定期审查低质量内容，决定是否删除或改进
- 收集用户反馈，持续优化分类和推荐
- 建立内容贡献机制，鼓励补充高质量知识

---

## 十一、故障排查

### 问题1: 搜索结果为空
- 检查关键词是否正确
- 尝试使用更宽泛的词
- 检查索引文件是否损坏

### 问题2: 推荐不准确
- 相似度阈值可能过高/过低
- 重新运行推荐系统构建
- 检查特征提取是否正常

### 问题3: API 数据过期
- 重新运行知识资产库构建脚本
- 检查数据文件的 generated_at 时间戳

---

## 十二、技术支持

遇到问题或有改进建议，请：
1. 查看日志文件
2. 检查数据文件完整性
3. 重新运行构建脚本
4. 提交 Issue 或联系开发团队

---

**FieldMind Knowledge Reuse System**
Version 1.0
Generated: 2026-09-13
"""

        guide_file = f"{self.output_dir}/KNOWLEDGE_ASSETS_GUIDE.md"
        with open(guide_file, 'w', encoding='utf-8') as f:
            f.write(guide)

        print(f"   ✓ 保存到: {guide_file}")

        return guide_file

    def run(self):
        """执行完整流程"""
        print("=" * 70)
        print("Week 6-7 Day 3: 知识资产库建设")
        print("=" * 70)

        # 1. 加载数据
        patterns, skills = self.load_data()

        # 2. 知识资产分类
        classified = self.classify_assets(patterns)

        # 3. 构建搜索索引
        search_index = self.build_search_index(patterns)

        # 4. 构建推荐系统
        recommendations = self.build_recommendation_system(patterns)

        # 5. 生成统计报告
        stats = self.generate_statistics(patterns, skills, classified)

        # 6. 生成 API 数据
        api_data = self.generate_api_data(patterns, skills, classified)

        # 7. 生成仪表板数据
        dashboard = self.generate_usage_dashboard_data(patterns, skills, classified, stats)

        # 8. 生成使用指南
        guide_file = self.generate_usage_guide()

        # 9. 总结
        print("\n" + "=" * 70)
        print("知识资产库建设完成")
        print("=" * 70)

        print(f"\n📊 统计数据:")
        print(f"  总知识模式: {stats['overview']['total_patterns']}")
        print(f"  总 Skills: {stats['overview']['total_skills']}")
        print(f"  平均模式质量: {stats['overview']['avg_pattern_quality']:.3f}")
        print(f"  平均 Skill 质量: {stats['overview']['avg_skill_quality']:.3f}")

        print(f"\n🏷️  分类统计:")
        print(f"  领域数: {len(classified['by_domain'])}")
        print(f"  质量级别: {len(classified['by_quality'])}")
        print(f"  模式类型: {len(classified['by_type'])}")

        print(f"\n🔍 搜索索引:")
        print(f"  索引词数: {len(search_index['inverted_index'])}")
        print(f"  文档数: {search_index['total_docs']}")

        print(f"\n💡 推荐系统:")
        print(f"  相似度图: {len(recommendations['similarity_based'])} 个节点")
        print(f"  热门推荐: {len(recommendations['popular'])} 项")

        print(f"\n📁 输出文件:")
        print(f"  - 统计报告: {self.output_dir}/knowledge_assets_statistics.json")
        print(f"  - API 数据: {self.output_dir}/api_data/knowledge_assets_api.json")
        print(f"  - 仪表板数据: {self.output_dir}/api_data/dashboard_data.json")
        print(f"  - 搜索索引: {self.output_dir}/indexes/search_index.json")
        print(f"  - 推荐数据: {self.output_dir}/indexes/recommendations.json")
        print(f"  - 使用指南: {guide_file}")

        return {
            'classified': classified,
            'search_index': search_index,
            'recommendations': recommendations,
            'stats': stats,
            'api_data': api_data,
            'dashboard': dashboard,
        }


def main():
    db_path = "/Users/alwan/Downloads/FieldMind/fieldmind/backend/src/data/fieldmind.db"
    patterns_file = "/Users/alwan/Downloads/FieldMind/fieldmind/knowledge_assets/knowledge_patterns_20260913_151640.json"
    skills_catalog = "/Users/alwan/Downloads/FieldMind/fieldmind/knowledge_assets/skills_catalog.json"
    output_dir = "/Users/alwan/Downloads/FieldMind/fieldmind/knowledge_assets"

    library = KnowledgeAssetLibrary(db_path, patterns_file, skills_catalog, output_dir)
    result = library.run()

    print("\n✅ 知识资产库建设完成！")


if __name__ == "__main__":
    main()
