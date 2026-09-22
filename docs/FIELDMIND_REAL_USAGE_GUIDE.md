# FieldMind 真实使用指南 - 从零到落地

生成时间：2026-08-21 19:30

---

## 🎯 系统现状

### 已完成的功能
✅ 数据库表结构完整（58个字段的 document_chunks）
✅ TF-IDF 关键词提取服务
✅ 无监督聚类服务
✅ API 路由已注册
✅ 数据治理字段已添加

### 当前问题
❌ 数据库中只有2个 chunks（不够测试）
❌ TF-IDF 和聚类还没有自动触发
❌ 需要上传真实文件来测试完整流程

---

## 📋 立即可执行的步骤

### 步骤1：启动后端服务

```bash
cd /Users/alwan/FieldMind/backend/src
python app/main_simple.py
```

**预期看到**：
```
🚀 FieldMind Backend (Simple) 启动中...
📝 API文档: http://127.0.0.1:8000/docs
✅ 数据库初始化成功
```

---

### 步骤2：上传一个测试文件

**方式A：通过 API（推荐）**

```bash
# 准备一个测试文件（文本或音频）
# 假设你有一个 test.txt 文件

curl -X POST http://localhost:8000/api/documents/upload \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test.txt" \
  -F "project_id=1"
```

**方式B：通过前端界面**
- 打开 http://localhost:8000/docs
- 找到 POST /api/documents/upload
- 点击 "Try it out"
- 上传文件

---

### 步骤3：手动触发 TF-IDF 和聚类

**等文件处理完成后，手动运行后处理**：

```bash
cd /Users/alwan/FieldMind/backend/src

# 方法1：通过 Python 脚本
python -c "
from app.services.document_processing_integration import process_existing_project
process_existing_project(1)  # 项目ID=1
"

# 方法2：通过 API
curl -X POST http://localhost:8000/api/topics/auto-analyze/1
```

---

### 步骤4：查看结果

#### 4.1 查看关键词
```bash
# 查看项目的 Top 50 关键词
curl http://localhost:8000/api/topics/keywords/project/1?top_n=50

# 预期响应：
{
  "status": "success",
  "project_id": 1,
  "keywords": [
    {"keyword": "山歌", "total_tfidf_score": 12.34, "total_frequency": 23},
    {"keyword": "传承", "total_tfidf_score": 10.56, "total_frequency": 18}
  ]
}
```

#### 4.2 查看聚类结果
```bash
# 查看项目的聚类
curl http://localhost:8000/api/topics/clusters/1

# 预期响应：
{
  "status": "success",
  "project_id": 1,
  "n_clusters": 3,
  "clusters": [
    {
      "cluster_id": 0,
      "cluster_label": "山歌/传承/文化",
      "chunk_count": 15,
      "top_keywords": ["山歌", "传承", "文化", "唱歌", "老人"]
    }
  ]
}
```

#### 4.3 查看某个聚类的 chunks
```bash
curl http://localhost:8000/api/topics/clusters/1/0/chunks
```

---

### 步骤5：验证数据库

```bash
cd /Users/alwan/FieldMind/backend/src

# 检查 chunks 数量
sqlite3 data/fieldmind.db "SELECT COUNT(*) FROM document_chunks WHERE project_id = 1;"

# 检查关键词
sqlite3 data/fieldmind.db "SELECT COUNT(*) FROM chunk_keywords;"

# 查看前5个关键词
sqlite3 data/fieldmind.db "
SELECT keyword, tfidf_score, frequency 
FROM chunk_keywords 
ORDER BY tfidf_score DESC 
LIMIT 5;
"

# 检查聚类
sqlite3 data/fieldmind.db "SELECT * FROM topic_clusters WHERE project_id = 1;"
```

---

## 🔧 如果遇到问题

### 问题1：API 返回 404

**原因**：路由没有正确注册

**解决**：
```bash
# 检查路由是否注册
cd /Users/alwan/FieldMind/backend/src
grep "topic_analysis" app/main_simple.py

# 如果没有，重新启动服务
pkill -f "python app/main_simple.py"
python app/main_simple.py
```

### 问题2：TF-IDF 提取失败

**原因**：chunks 数量不足

**解决**：
```bash
# 检查 chunks 数量
sqlite3 data/fieldmind.db "SELECT COUNT(*) FROM document_chunks;"

# 如果 < 2，需要上传更多文件
```

### 问题3：聚类失败

**原因**：chunks 数量 < 5

**解决**：上传更多文件，或者修改最小聚类数量

### 问题4：jieba 分词报错

**原因**：jieba 未安装

**解决**：
```bash
pip install jieba
```

### 问题5：scikit-learn 报错

**原因**：sklearn 未安装

**解决**：
```bash
pip install scikit-learn
```

---

## 📊 完整测试流程

### 准备测试数据

创建一个测试文件 `test_data.txt`，包含多段不同主题的文本：

```
布依族的山歌是祖传的宝贝，老人们都会唱，但年轻人不太愿意学了。传承人越来越少，这是个大问题。

我们村的房屋都是木结构的吊脚楼，很有特色。以前住的是茅草房，现在政府补贴盖了瓦房。

政府的乡村振兴政策给了很多补贴，修路、通水、通电都有资金支持。村里变化很大。

六月六是我们的传统节日，全村人都会聚在一起，唱歌跳舞，非常热闹。这个习俗已经传了几百年了。

现在村里的年轻人都外出打工了，留下的都是老人和小孩。交通不方便，去镇上要走两个小时。
```

### 执行完整流程

```bash
# 1. 启动服务
cd /Users/alwan/FieldMind/backend/src
python app/main_simple.py &

# 2. 上传文件
curl -X POST http://localhost:8000/api/documents/upload \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test_data.txt" \
  -F "project_id=1"

# 3. 等待几秒，让文件处理完成
sleep 5

# 4. 执行 TF-IDF 和聚类
curl -X POST http://localhost:8000/api/topics/auto-analyze/1

# 5. 等待处理完成
sleep 10

# 6. 查看结果
curl http://localhost:8000/api/topics/keywords/project/1?top_n=20
curl http://localhost:8000/api/topics/clusters/1
```

---

## 🎯 下一步：自动化集成

### 修改文档处理流程，自动触发

**文件**：`app/services/document_processing_pipeline_complete.py`

**在 process_document 方法的最后添加**：

```python
# 在保存 chunks 后
try:
    from app.services.document_processing_integration import DocumentProcessingIntegration
    integrator = DocumentProcessingIntegration()
    integrator.post_process_chunks(project_id, document_id)
except Exception as e:
    logger.error(f"后处理失败: {e}")
```

这样以后上传文件就会自动执行 TF-IDF 和聚类。

---

## 📱 前端集成建议

### 新增页面：主题发现

**路径**：`/topics`

**功能**：
1. 显示项目的关键词词云
2. 显示聚类列表
3. 点击聚类查看 chunks
4. 手动触发重新聚类

**API 调用**：
```javascript
// 获取关键词
fetch('/api/topics/keywords/project/1?top_n=50')

// 获取聚类
fetch('/api/topics/clusters/1')

// 获取聚类的 chunks
fetch('/api/topics/clusters/1/0/chunks')

// 触发聚类
fetch('/api/topics/cluster', {
  method: 'POST',
  body: JSON.stringify({project_id: 1, n_clusters: 5})
})
```

---

## ✅ 验收标准

完成以下所有步骤，系统才算真正可用：

- [ ] 上传文件成功
- [ ] 文件被切分成 chunks（至少5个）
- [ ] TF-IDF 关键词提取成功（chunk_keywords 表有数据）
- [ ] 聚类成功（topic_clusters 表有数据）
- [ ] API 可以查询关键词
- [ ] API 可以查询聚类结果
- [ ] 前端可以展示词云
- [ ] 前端可以展示聚类

---

**现在的优先级：上传一个真实的测试文件，让系统有足够的数据来测试！**
