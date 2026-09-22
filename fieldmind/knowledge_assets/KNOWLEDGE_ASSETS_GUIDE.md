# FieldMind 知识资产库使用指南

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
