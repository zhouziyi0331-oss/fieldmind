
# FieldMind 上传API迁移指南

## 📌 标准上传API（推荐使用）

**POST /api/v1/projects/{project_id}/documents/upload**

### 特性
- ✅ 项目隔离
- ✅ 完整的后台处理流程
- ✅ 自动标签提取
- ✅ 支持14种文件格式
- ✅ 文件去重（基于hash）
- ✅ 处理状态跟踪

### 前端调用示例

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const response = await fetch(
    `/api/v1/projects/${projectId}/documents/upload`,
    {
        method: 'POST',
        body: formData
    }
);

const result = await response.json();
console.log('文档ID:', result.id);
console.log('处理状态:', result.status);
```

### 响应格式

```json
{
    "id": 123,
    "filename": "example.pdf",
    "file_type": "pdf",
    "file_size": 1024000,
    "status": "pending",
    "processing_progress": 0,
    "tags": [...]
}
```

---

## ⚠️ 已废弃API（不推荐）

### 1. POST /api/documents/upload

**状态**: 已废弃
**原因**: 与标准API功能重复
**替代**: 使用 `/api/v1/projects/{project_id}/documents/upload`

### 2. POST /api/v1/documents/upload

**状态**: 已废弃
**原因**: 使用旧的documents表，与标签系统不兼容
**替代**: 使用 `/api/v1/projects/{project_id}/documents/upload`

---

## 📊 数据表说明

### project_documents（主力表）
- 所有新上传的文件
- 与标签系统兼容
- 支持项目隔离

### documents（旧表）
- 仅用于历史数据兼容
- 新数据不再写入
- 将在未来版本移除

---

## 🔄 迁移步骤

如果您的前端代码仍在使用旧API：

1. 将上传URL改为标准API
2. 确保传入project_id参数
3. 测试文件上传和处理流程
4. 验证标签提取功能

---

生成时间: 2026-08-21T06:37:09.439276
