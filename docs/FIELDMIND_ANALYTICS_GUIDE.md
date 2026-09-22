# 🎯 FieldMind 数据分析系统 - 完整使用指南

**最后更新**: 2026-08-05 15:30  
**系统状态**: ✅ 完整功能已实现  
**核心突破**: 从"向量检索"到"数据分析"

---

## 📋 快速导航

1. [系统架构](#系统架构)
2. [立即开始](#立即开始)
3. [核心功能](#核心功能)
4. [API文档](#api文档)
5. [验收测试](#验收测试)
6. [故障排查](#故障排查)
7. [进阶配置](#进阶配置)

---

## 🏗️ 系统架构

### 数据流程图

```
┌─────────────┐
│ 音频/文档上传│
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Whisper转写 │
│ 或文档提取   │
└──────┬──────┘
       │
       ▼
┌──────────────────────────┐
│ 🆕 数据治理层              │
│ ┌────────────────────┐   │
│ │ 1. 文本清洗         │   │
│ │    去除填充词        │   │
│ │    标点归一化        │   │
│ └────────────────────┘   │
│ ┌────────────────────┐   │
│ │ 2. 主题分类         │   │
│ │    衣食住行社交...   │   │
│ └────────────────────┘   │
│ ┌────────────────────┐   │
│ │ 3. 实体抽取         │   │
│ │    人名/地名        │   │
│ └────────────────────┘   │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ 双写存储                  │
│ ┌──────────┐┌──────────┐│
│ │PostgreSQL││ChromaDB  ││
│ │结构化数据││向量数据   ││
│ └──────────┘└──────────┘│
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ 数据分析                  │
│ ┌──────────────────────┐│
│ │ SQL聚合查询           ││
│ │ COUNT/SUM/AVG/ORDER BY││
│ └──────────────────────┘│
│ ┌──────────────────────┐│
│ │ 报告生成              ││
│ │ 硬数据 + LLM撰写      ││
│ └──────────────────────┘│
└───────────────────────────┘
```

### 核心模块

| 模块 | 文件 | 功能 |
|------|------|------|
| 数据治理 | `app/services/data_curation.py` | 文本清洗、主题分类、实体抽取 |
| 结构化模型 | `app/models/structured_insight.py` | 3张分析表定义 |
| 数据分析API | `app/api/analytics.py` | SQL聚合查询接口 |
| Pipeline | `app/services/document_processing_pipeline_complete.py` | 集成数据治理层 |

---

## 🚀 立即开始

### 1. 安装依赖（如果未安装）

```bash
cd /Users/alwan/FieldMind-Rebuild/fieldmind-backend
pip install snownlp python-dateutil arrow regex ftfy
```

### 2. 创建数据库表

```bash
python3 create_analytics_tables.py
```

**预期输出**:
```
✅ 表创建成功！
✅ 所有必需表已创建
```

### 3. 启动后端

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. 批量重新处理历史文档（填充结构化数据）

```bash
python3 /tmp/batch_reprocess_36_42.py
```

### 5. 验证系统

```bash
# 运行核弹级验收测试
python3 /tmp/nuclear_validation_test.py

# 测试API
curl http://localhost:8000/api/analytics/projects/1/topic-distribution
```

---

## 🎯 核心功能

### 1. 数据治理（Data Curation）

**自动执行**，无需手动调用。

#### 文本清洗

**功能**:
- 去除填充词：嗯、啊、那个、就是说、你知道...
- 标点归一化：中文引号→英文引号
- 去除多余空格

**示例**:
```python
输入: "嗯，那个，我觉得这个杀猪菜啊，就是说，是我们村的传统美食，你知道吗？"
输出: "杀猪菜,是我们村的传统美食,吗?"
```

#### 主题分类

**7大主题**:
- **衣**: 服装、纺织、刺绣、布料
- **食**: 饮食、烹饪、杀猪菜、宴席
- **住**: 房子、建房、祠堂、村舍
- **行**: 交通、出行、道路、桥
- **社交**: 婚礼、丧事、祭祀、节日
- **经济**: 钱、收入、买卖、生意
- **信仰**: 神、庙、祭祀、风水

**扩展**:
如需添加新主题，编辑 `app/services/data_curation.py`:
```python
TOPIC_KEYWORDS = {
    '衣': [...],
    '食': [...],
    '新主题': ['关键词1', '关键词2', ...],  # 添加这里
}
```

#### 实体抽取

**自动提取**:
- **人名**: 基于jieba词性标注（nr标签）
- **地名**: 基于jieba词性标注（ns标签）

**准确率**: 取决于jieba分词质量，中文人名识别率约70-80%

### 2. 结构化存储

#### structured_insights 表（主表）

**每条记录**: 一个文本片段的结构化信息

**关键字段**:
```sql
- original_text: 原始文本
- cleaned_text: 清洗后文本
- topics: 主题标签（逗号分隔）"衣,食"
- persons: 人名列表（逗号分隔）"王大爷,李婶"
- locations: 地名列表
- start_time/end_time: 音频时间戳（秒）
- word_count: 字数
```

**查询示例**:
```bash
sqlite3 data/fieldmind.db \
  "SELECT cleaned_text, topics, persons FROM structured_insights WHERE topics LIKE '%食%' LIMIT 5;"
```

#### topic_statistics 表（主题统计）

**用途**: 快速查询"项目1中各主题的频次"

**查询示例**:
```bash
sqlite3 data/fieldmind.db \
  "SELECT topic, count FROM topic_statistics WHERE project_id=1 ORDER BY count DESC;"
```

#### entity_statistics 表（实体统计）

**用途**: 快速查询"项目1中被提及最多的人物"

**查询示例**:
```bash
sqlite3 data/fieldmind.db \
  "SELECT entity_name, count FROM entity_statistics WHERE project_id=1 AND entity_type='person' ORDER BY count DESC LIMIT 10;"
```

---

## 📡 API文档

所有API基于 **SQL聚合查询**，而非向量检索。

### 1. 主题分布

**端点**: `GET /api/analytics/projects/{project_id}/topic-distribution`

**请求**:
```bash
curl http://localhost:8000/api/analytics/projects/1/topic-distribution
```

**响应**:
```json
{
  "project_id": 1,
  "topics": [
    {"topic": "食", "count": 45, "percentage": 35.7},
    {"topic": "衣", "count": 23, "percentage": 18.3},
    {"topic": "住", "count": 18, "percentage": 14.3}
  ],
  "total": 126
}
```

**SQL查询**:
```sql
SELECT topic, count 
FROM topic_statistics 
WHERE project_id = 1 
ORDER BY count DESC;
```

### 2. Top实体

**端点**: `GET /api/analytics/projects/{project_id}/top-entities`

**参数**:
- `entity_type`: `person` 或 `location`
- `top_k`: 返回前N个（默认10）

**请求**:
```bash
curl "http://localhost:8000/api/analytics/projects/1/top-entities?entity_type=person&top_k=10"
```

**响应**:
```json
{
  "entity_type": "person",
  "entities": [
    {"name": "王大爷", "count": 15},
    {"name": "李婶", "count": 12}
  ],
  "total": 2
}
```

### 3. 字数统计

**端点**: `GET /api/analytics/projects/{project_id}/word-count-stats`

**响应**:
```json
{
  "total_words": 12450,
  "avg_words_per_chunk": 45.6,
  "total_chunks": 273
}
```

**SQL查询**:
```sql
SELECT 
  SUM(word_count) as total_words,
  AVG(word_count) as avg_words,
  COUNT(*) as total_chunks
FROM structured_insights 
WHERE project_id = 1;
```

### 4. 时间线分布

**端点**: `GET /api/analytics/projects/{project_id}/timeline-distribution`

**用途**: 查询音频内容的时间分布

**响应**:
```json
{
  "documents": [
    {
      "document_id": 40,
      "timeline": [
        {"time": 0.5, "topics": ["食"]},
        {"time": 15.2, "topics": ["衣", "经济"]}
      ]
    }
  ]
}
```

### 5. 生成报告

**端点**: `POST /api/analytics/projects/{project_id}/generate-report`

**参数**:
- `report_type`: `overview`（综合）、`topic`（主题）、`entity`（实体）

**请求**:
```bash
curl -X POST http://localhost:8000/api/analytics/projects/1/generate-report
```

**核心流程**:
```
1. SQL查询统计数字（硬数据）
   ↓
2. （可选）ChromaDB检索典型引用
   ↓
3. 组合Prompt：硬数据 + 强制约束
   ↓
4. LLM基于数据撰写（禁止编造）
```

**强制约束**:
```
1. 报告中的所有数字必须来自上述统计数据，禁止自行推算
2. 不要编造不存在的案例或引用
3. 如果某个维度无数据，明确说明"该维度暂无数据"
```

---

## 💣 验收测试（核弹级3问）

### 测试1: 聚合（问数字）

**问题**: 
> 在目前上传的所有材料中，提到'衣'的有多少处？提到'食'的有多少处？列出按主题的频次排名。

**期望答案**:
```
食: 45次 (35.7%)
衣: 23次 (18.3%)
住: 18次 (14.3%)
行: 12次 (9.5%)

总计: 126次提及
```

**错误答案**:
```
❌ "材料中多次提到饮食和服装相关内容，可以看出这是田野调查的重要主题..."
（没有具体数字，泛泛而谈）
```

**验证方式**:
```bash
curl http://localhost:8000/api/analytics/projects/1/topic-distribution
```

### 测试2: Top实体

**问题**:
> 被提及最多的人物是谁？分别被提及多少次？

**期望答案**:
```
1. 王大爷: 15次
2. 李婶: 12次
3. 张师傅: 8次
```

**错误答案**:
```
❌ "材料中多次提到王大爷，他是村里的重要人物..."
（没有具体次数）
```

**验证方式**:
```bash
curl "http://localhost:8000/api/analytics/projects/1/top-entities?entity_type=person&top_k=10"
```

### 测试3: 时间戳统计

**问题**:
> 王大爷在音频里一共说了多少句话？主要集中在哪个时间段？

**期望答案**:
```
王大爷共说了15句话
时间分布：
- 0-30秒: 3句
- 60-90秒: 8句
- 120-150秒: 4句

主要集中在60-90秒时间段
```

**错误答案**:
```
❌ "王大爷说了比较多的话，主要是在前半段..."
（使用"比较多"、"前半段"等模糊表述）
```

**验证方式**:
```bash
python3 /tmp/nuclear_validation_test.py
```

---

## 🔧 故障排查

### 问题1: 表不存在

**错误**: `no such table: structured_insights`

**解决**:
```bash
python3 create_analytics_tables.py
```

### 问题2: 无统计数据

**错误**: API返回 `"topics": []` 或 `"entities": []`

**原因**: 文档尚未处理，或Pipeline未执行数据治理

**解决**:
```bash
# 方案1: 批量重新处理历史文档
python3 /tmp/batch_reprocess_36_42.py

# 方案2: 上传新文档（会自动执行数据治理）
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@test.mp3" \
  -F "project_id=1"
```

### 问题3: 人名识别不准

**原因**: jieba分词未识别为人名（nr标签）

**解决方案1**: 添加自定义词典
```python
# 在 app/services/data_curation.py 顶部添加
import jieba
jieba.load_userdict('/path/to/custom_dict.txt')
```

**custom_dict.txt 格式**:
```
王大爷 10 nr
李婶 10 nr
张师傅 10 nr
```

**解决方案2**: 使用更强的NER模型（如BERT-NER）

### 问题4: 主题分类不准

**原因**: 关键词库不完善

**解决**:
编辑 `app/services/data_curation.py`:
```python
TOPIC_KEYWORDS = {
    '食': [
        '吃', '食物', '饮食', '做饭', '烹饪', '菜', '肉', '粮食',
        # 添加更多关键词
        '炒菜', '煮饭', '蒸', '炖', '煎', '炸', '烤',
    ],
}
```

### 问题5: API返回500错误

**检查日志**:
```bash
tail -f /tmp/backend_clean.log | grep ERROR
```

**常见原因**:
- 数据库连接失败
- SQL查询语法错误
- 缺少必要字段

---

## 🎓 进阶配置

### 1. 添加新的主题类别

**编辑**: `app/services/data_curation.py`

```python
TOPIC_KEYWORDS = {
    '衣': [...],
    '食': [...],
    # 新增：教育主题
    '教育': ['学校', '老师', '学生', '读书', '上学', '课堂'],
}
```

**重新处理**:
```bash
python3 /tmp/batch_reprocess_36_42.py
```

### 2. 自定义文本清洗规则

**编辑**: `app/services/data_curation.py`

```python
class TextCleaner:
    FILLER_WORDS = [
        '嗯', '啊', '呃', '哦',
        # 添加更多填充词
        '其实吧', '怎么说呢', '这样的话',
    ]
```

### 3. 集成更强的实体识别模型

**替换jieba为BERT-NER**:

```python
# 安装
pip install transformers torch

# 修改 EntityExtractor
from transformers import pipeline

class EntityExtractor:
    def __init__(self):
        self.ner = pipeline("ner", model="ckiplab/bert-base-chinese-ner")

    def extract_persons(self, text):
        entities = self.ner(text)
        persons = [e['word'] for e in entities if e['entity'].endswith('PER')]
        return list(set(persons))
```

### 4. 添加情感分析维度

**安装**:
```bash
pip install snownlp
```

**集成**:
```python
from snownlp import SnowNLP

class SentimentAnalyzer:
    @staticmethod
    def analyze(text):
        s = SnowNLP(text)
        score = s.sentiments  # 0-1，越接近1越积极
        if score > 0.6:
            return 'positive'
        elif score < 0.4:
            return 'negative'
        else:
            return 'neutral'
```

**在数据治理中集成**:
```python
# 在 DataCurationPipeline.process() 中添加
sentiment = SentimentAnalyzer.analyze(cleaned_text)
structured_record['sentiment'] = sentiment
```

**新增字段**:
```python
# 在 StructuredInsight 模型中添加
sentiment = Column(String(20), nullable=True)  # positive/negative/neutral
```

---

## 📚 参考资料

### 核心文档
- [数据分析系统改造完成报告](DATA_ANALYSIS_TRANSFORMATION_COMPLETE.md)
- [完整修复报告](FINAL_COMPLETE_REPORT.md)
- [音频转写Pipeline修复](AUDIO_PIPELINE_FIX_COMPLETE.md)

### 关键文件
- 数据治理: `app/services/data_curation.py`
- 数据模型: `app/models/structured_insight.py`
- 分析API: `app/api/analytics.py`
- Pipeline: `app/services/document_processing_pipeline_complete.py`

### 测试脚本
- 健康检查: `health_check.py`
- 核弹级验收: `/tmp/nuclear_validation_test.py`
- 完整测试: `/tmp/test_analytics_system.py`
- 批量重处理: `/tmp/batch_reprocess_36_42.py`

---

## 🎯 最佳实践

### 1. 数据质量保证
- **上传前**: 确保音频清晰、文档格式正确
- **处理后**: 运行验收测试，检查统计数字是否合理
- **定期维护**: 扩充主题关键词库、更新实体词典

### 2. 性能优化
- **批量处理**: 使用批量重处理脚本，而非逐个上传
- **索引优化**: 在高频查询字段上添加索引
- **缓存策略**: 对统计结果添加缓存（可选）

### 3. 报告生成
- **硬数据优先**: 所有数字必须来自SQL
- **软证据辅助**: 典型引用来自ChromaDB（可选）
- **强制约束**: Prompt中必须包含"禁止编造"指令

---

## 🆘 获取帮助

### 快速诊断
```bash
# 1. 运行健康检查
python3 health_check.py

# 2. 运行核弹级验收
python3 /tmp/nuclear_validation_test.py

# 3. 查看日志
tail -f /tmp/backend_clean.log | grep -E "ERROR|TRACE"

# 4. 检查数据库
sqlite3 data/fieldmind.db "SELECT COUNT(*) FROM structured_insights;"
```

### 常见问题速查

| 问题 | 命令 |
|------|------|
| 表不存在 | `python3 create_analytics_tables.py` |
| 无统计数据 | `python3 /tmp/batch_reprocess_36_42.py` |
| API 500错误 | `tail -f /tmp/backend_clean.log \| grep ERROR` |
| 人名识别不准 | 添加自定义词典 `jieba.load_userdict()` |

---

**最后更新**: 2026-08-05 15:30  
**系统版本**: 2.0 (数据分析系统)  
**维护者**: FieldMind Team
