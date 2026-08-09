# 🔧 基础设施修复方案 - 执行清单

**诊断时间**: 2026-08-05 16:30  
**核心问题**: 前后端通信协议缺失 + 数据一致性问题

---

## 🚨 **扫描发现的问题**

### 1. 数据一致性严重问题 ❌
- **现象**: 43个completed文档，只有6个在ChromaDB中有向量
- **影响**: 37个文档"假装完成"，实际无法搜索
- **根本原因**: background_tasks只改status，未执行向量化

### 2. 结构化数据严重不足 ⚠️
- **现象**: structured_insights只有1条记录
- **影响**: 数据分析功能无法使用
- **原因**: 大部分文档未经过数据治理Pipeline

### 3. API返回格式不统一 ⚠️
- **现象**: 有的接口返回list，有的返回dict
- **影响**: 前端需要判断类型，容易出错
- **原因**: 未使用统一的响应格式

---

## ✅ **已完成的基础设施**

### 1. 统一数据契约 ✅
- **文件**: `app/contracts.py`
- **功能**: 定义所有API的请求/响应格式
- **使用**: `success_response()`, `error_response()`

### 2. 全局异常拦截器 ✅
- **文件**: `app/main.py`
- **功能**: 自动捕获所有异常，返回500 + 详细错误
- **效果**: 杀死"假装成功"

### 3. 诊断扫描脚本 ✅
- **文件**: `/tmp/debug_scan.py`
- **功能**: 自动检测5大连接问题
- **输出**: 清晰的✅/❌状态

---

## 🔧 **立即执行的修复步骤**

### 第1步: 批量修复数据一致性（最优先）

**目标**: 让37个"假完成"文档真正完成向量化

```bash
# 运行批量重处理脚本
python3 /tmp/batch_reprocess_36_42.py
```

**预期结果**:
- 所有completed文档都有向量
- structured_insights表填充数据

**验证**:
```bash
python3 /tmp/debug_scan.py
# 检查"数据一致性检查"是否通过
```

---

### 第2步: 修复API返回格式（统一契约）

**目标**: 所有API使用统一响应格式

**修改文件**: `app/api/documents.py` 等所有API文件

**示例修改**:
```python
# ❌ 错误做法
@router.get("/documents/{id}")
def get_document(id: int):
    doc = db.query(Document).get(id)
    return doc  # 直接返回对象

# ✅ 正确做法
from app.contracts import success_response, error_response, ErrorCodes

@router.get("/documents/{id}")
def get_document(id: int):
    doc = db.query(Document).get(id)
    if not doc:
        return error_response(ErrorCodes.NOT_FOUND, "文档不存在")

    return success_response({
        "id": doc.id,
        "filename": doc.filename,
        "status": doc.status,
        # ... 其他字段
    })
```

---

### 第3步: 前端统一请求拦截器

**目标**: 自动处理错误，统一数据格式

**创建文件**: `fieldmind-web/src/services/request.ts`

```typescript
// 统一请求封装
async function request(url: string, options: RequestInit = {}) {
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      }
    });

    const data = await response.json();

    // 检查响应格式
    if (data.code !== 0) {
      // 错误处理
      alert(data.message || '请求失败');
      throw new Error(data.message);
    }

    return data.data;  // 返回实际数据
  } catch (error) {
    console.error('请求失败:', error);
    throw error;
  }
}

// 使用示例
const documents = await request('/api/documents');
```

---

### 第4步: 数据库事务规范化

**目标**: 确保commit()不丢失

**检查文件**: `app/services/background_tasks.py`

**添加强制规范**:
```python
def process_document_async(document_id: int):
    db = SessionLocal()

    try:
        # 1. 更新状态为processing
        doc.status = "processing"
        db.commit()  # ✅ 立即提交，让前端看到

        # 2. Whisper转写
        content = whisper.transcribe(...)
        doc.text_content = content
        db.commit()  # ✅ 每个阶段都提交

        # 3. 向量化
        chromadb.add(...)
        db.commit()  # ✅ 确保状态一致

        # 4. 最终状态
        doc.status = "completed"
        db.commit()

    except Exception as e:
        db.rollback()  # ✅ 失败回滚
        doc.status = "failed"
        doc.error_message = str(e)
        db.commit()
        raise  # ✅ 重新抛出，触发全局异常处理器

    finally:
        db.close()
```

---

## 📊 **修复进度跟踪**

| 任务 | 状态 | 验证方式 |
|------|------|----------|
| 统一数据契约 | ✅ 完成 | contracts.py存在 |
| 全局异常拦截 | ✅ 完成 | main.py有exception_handler |
| 诊断扫描脚本 | ✅ 完成 | debug_scan.py可运行 |
| 批量修复数据 | ⏳ 待执行 | 运行batch_reprocess |
| 统一API格式 | ⏳ 待执行 | 修改所有API |
| 前端拦截器 | ⏳ 待执行 | 创建request.ts |
| 事务规范化 | ⏳ 待执行 | 检查background_tasks |

---

## 🎯 **验收标准**

### 标准1: 数据一致性
```bash
python3 /tmp/debug_scan.py
# 输出: ✅ 数据一致性检查通过
```

### 标准2: API契约
```bash
curl http://localhost:8000/api/documents/1
# 输出: {"code": 0, "message": "success", "data": {...}}
```

### 标准3: 异常处理
```bash
# 故意触发错误
curl http://localhost:8000/api/documents/999999
# 输出: {"code": 404, "message": "文档不存在", "data": null}
# 终端输出: 完整堆栈信息
```

### 标准4: 前端正常工作
- 上传文件 → 立即显示"上传中"
- 3秒后刷新 → 状态变为"处理中"
- 完成后 → 状态变为"已完成"
- 点击文档 → 显示详情（不是空白）

---

## 🚀 **立即执行（优先级排序）**

### P0 - 数据修复（今天必须完成）
```bash
python3 /tmp/batch_reprocess_36_42.py
```

### P1 - API统一（明天完成）
修改所有API接口使用contracts.py

### P2 - 前端优化（后天完成）
创建统一请求拦截器

---

## 📞 **问题定位指南**

### 如果上传后看不到文档
1. 打开终端，看是否有红色错误
2. 运行 `python3 /tmp/debug_scan.py`
3. 检查 `数据一致性检查` 部分

### 如果前端显示空白
1. 按F12打开Console
2. 看是否有红色错误
3. 检查Network标签，看API返回了什么
4. 对比返回格式与前端预期

### 如果API返回500
1. 看终端的完整堆栈
2. 找到第一行带文件名的错误
3. 打开那个文件，定位到那一行
4. 检查是否缺少try-except或commit()

---

**创建时间**: 2026-08-05 16:30  
**核心方法**: 双端连通性诊断 + 统一契约  
**下一步**: 运行batch_reprocess修复数据  
**目标**: 消灭"假装成功"，建立真实连接
