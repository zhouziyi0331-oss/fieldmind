# FieldMind 数据治理验证清单

## 📋 立即执行的验证步骤

### 第一步：启动后端服务

```bash
cd /Users/alwan/FieldMind/backend/src
python3 app/main_simple.py
```

等待看到：
```
✅ 数据库初始化成功
🚀 FieldMind Backend (Simple) 启动中...
📝 API文档: http://127.0.0.1:8000/docs
```

---

### 第二步：验证数据库字段（强制验收标准1）

打开新终端，运行：

```bash
cd /Users/alwan/FieldMind/backend/src
sqlite3 data/fieldmind.db "PRAGMA table_info(document_chunks);" | grep -E "dimension|time_period|location|culture_code|keywords|confidence"
```

**预期结果**：应该看到7个业务维度字段
```
dimension_category|TEXT
dimension_sub_category|TEXT
time_period|TEXT
location|TEXT
culture_code|TEXT
keywords_matched|TEXT
confidence_score|FLOAT
```

---

### 第三步：验证维度分布（强制验收标准2）

```bash
curl -s http://localhost:8000/api/governance/validation/dimension-distribution | python3 -m json.tool
```

**预期结果**：应该看到6个维度的分布
```json
{
  "coverage_rate": 83.1,
  "distribution": [
    {"dimension": "衣食住行", "count": 411, "percentage": 32.0},
    {"dimension": "民俗", "count": 308, "percentage": 24.0},
    {"dimension": "非物质文化遗产", "count": 283, "percentage": 22.0},
    ...
  ],
  "verdict": "✅ 通过"
}
```

---

### 第四步：验证chunk连续性（强制验收标准3）

```bash
curl -s http://localhost:8000/api/governance/validation/chunk-continuity | python3 -m json.tool
```

**预期结果**：应该看到文档连续性报告
```json
{
  "total_documents": 47,
  "problem_documents": 3,
  "verdict": "⚠️ 3个文档不连续"
}
```

---

### 第五步：查看完整验证报告

```bash
curl -s http://localhost:8000/api/governance/validation/full-report | python3 -m json.tool
```

**预期结果**：包含3个验证的完整报告

---

### 第六步：查看前端看板

打开浏览器访问：
```
http://localhost:8000/governance_dashboard.html
```

**预期看到**：
- ✅ 总览统计（4个数字卡片）
- ✅ 维度分布图（6个彩色卡片）
- ✅ 覆盖率进度条
- ✅ 连续性检查表格
- ✅ 缺失分析列表

---

### 第七步：SQL直接验证（终极验证）

```bash
cd /Users/alwan/FieldMind/backend/src
sqlite3 data/fieldmind.db
```

在sqlite提示符下运行：

```sql
-- 1. 查看维度分布
SELECT dimension_category, COUNT(*) as count
FROM document_chunks
GROUP BY dimension_category;

-- 2. 查看具体记录（看到完整字段）
SELECT 
    chunk_id,
    substr(text, 1, 30) as text_preview,
    dimension_category,
    dimension_sub_category,
    time_period,
    location,
    culture_code,
    keywords_matched,
    confidence_score
FROM document_chunks
LIMIT 3;

-- 3. 按维度筛选（验证可以按维度查询）
SELECT COUNT(*) 
FROM document_chunks 
WHERE dimension_category = '非物质文化遗产';

-- 退出
.quit
```

---

## ✅ 验收标准对照表

| 标准 | 验证方式 | 通过条件 |
|------|---------|---------|
| **1. 维度覆盖** | `PRAGMA table_info` | 看到7个业务维度字段 |
| **2. 业务字段标注** | SQL查询维度分布 | 每个维度都有数据，不是全空 |
| **3. 分段完整性** | API连续性检查 | 能检测出不连续的文档 |
| **4. 跨文件溯源** | SQL查看具体记录 | 能看到关键词、时间、地点 |
| **5. 维度筛选** | SQL按维度查询 | 能筛选出特定维度的记录 |

---

## 🚨 如果验证失败

### 问题1：看不到业务维度字段
```bash
# 运行迁移
cd /Users/alwan/FieldMind/backend/src
alembic upgrade head
```

### 问题2：字段是空的
```
说明：需要重新上传文件，让系统自动标注
或者：对现有数据运行批量标注脚本
```

### 问题3：API返回错误
```bash
# 查看错误日志
tail -f /Users/alwan/FieldMind/backend/src/logs/fieldmind.log
```

---

## 📊 数据治理完成的标志

当你看到以下所有结果时，数据治理才算真正完成：

✅ 数据库有7个业务维度字段
✅ SQL查询能看到6个维度的分布
✅ 每个维度都有数据（不是全NULL）
✅ API能返回维度分布统计
✅ 前端看板能显示维度卡片
✅ SQL能按维度筛选数据
✅ 能看到匹配的关键词（可追溯）

---

## 🎯 现在开始验证

请按照上面的步骤，从第一步开始执行。

遇到任何问题，告诉我具体的错误信息。
