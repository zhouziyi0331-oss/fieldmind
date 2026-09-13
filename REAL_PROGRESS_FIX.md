# 真实进度追踪修复方案

## 🎯 问题总结

之前多个页面使用**假的进度动画**：
- 使用 `setInterval` 和 `Math.random()` 模拟进度
- 进度条不反映真实的上传/处理状态
- 用户无法知道实际完成了多少

## ✅ 修复方案

### 1. **上传进度 - 使用 axios 的 onUploadProgress**

**核心实现** (fieldmind.ts:97-109)：
```typescript
upload: (projectId: number, file: File, onProgress?: (progress: number) => void) => {
  const formData = new FormData()
  formData.append('file', file)
  return apiClient.post(`/api/v1/projects/${projectId}/documents/upload`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (progressEvent) => {
      if (progressEvent.total && onProgress) {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
        onProgress(percentCompleted)  // 真实进度：1%, 5%, 10%, ... 100%
      }
    },
  })
}
```

### 2. **批处理进度 - 轮询任务状态**

**核心实现**：
```typescript
const startProcessing = async () => {
  // 创建批处理任务
  const response = await batchService.createJob(projectId, documentIds)
  const jobId = response.job_id

  // 轮询任务状态获取真实进度
  const pollInterval = setInterval(async () => {
    const jobStatus = await batchService.getJob(jobId)
    const currentProgress = Math.round(
      (jobStatus.processed_documents / jobStatus.total_documents) * 100
    )
    setProgress(currentProgress)  // 真实进度基于已处理文档数

    if (currentProgress >= 100 || jobStatus.status === 'completed') {
      clearInterval(pollInterval)
    }
  }, 2000)
}
```

## 📋 已修复的页面

### ✅ 1. Documents.tsx
- **修改前**: 使用 `Math.random() * 15` 假进度
- **修改后**: 调用 `documentsService.upload()` 获取真实上传进度
- **效果**: 显示实际上传的字节数进度（1%, 5%, 10%...）

### ✅ 2. Upload.tsx
- **修改前**: `setInterval(() => p += 20)` 假进度
- **修改后**: 使用真实的 `documentsService.upload()` API
- **效果**: 每个文件显示真实的网络传输进度

### ✅ 3. upload/UploadPage.tsx
- **修改前**: `setInterval(() => p += 20)` 假进度
- **修改后**: 使用真实的 `documentsService.upload()` API
- **效果**: 真实反映文件上传状态

### ✅ 4. workflows/steps/ProcessStepPage.tsx
- **修改前**: `setInterval(() => p += 10)` 假进度
- **修改后**: 创建批处理任务并轮询真实状态
- **效果**: 显示实际已处理文档数量的进度

### ℹ️ 5. Monitoring.tsx
- **保持不变**: 使用 `setInterval` 每5秒刷新监控数据
- **原因**: 这是正常的数据轮询，不是假进度条

## 🔑 关键技术点

### 1. **axios onUploadProgress**
```typescript
axios.post(url, data, {
  onUploadProgress: (progressEvent) => {
    const percent = (progressEvent.loaded / progressEvent.total) * 100
    // progressEvent.loaded: 已上传字节数
    // progressEvent.total: 总字节数
  }
})
```

### 2. **任务状态轮询**
```typescript
const pollInterval = setInterval(async () => {
  const status = await api.getTaskStatus(taskId)
  const progress = (status.completed / status.total) * 100
  
  if (status.completed === status.total) {
    clearInterval(pollInterval) // 完成后停止轮询
  }
}, 2000) // 每2秒检查一次
```

### 3. **文件上传速度和剩余时间计算**
```typescript
const startTime = Date.now()
const elapsed = (Date.now() - startTime) / 1000 // 秒
const uploadedBytes = (file.size * progress) / 100
const speed = uploadedBytes / elapsed // bytes/s
const remaining = (file.size - uploadedBytes) / speed // 秒
```

## 🎨 用户体验改进

### 修复前：
- ❌ 进度条快速跳到100%，但文件还在上传
- ❌ 显示"处理中"但实际卡住了
- ❌ 无法判断是否真的在处理

### 修复后：
- ✅ 进度条准确反映上传/处理状态
- ✅ 显示实时速度 (KB/s, MB/s)
- ✅ 显示剩余时间 (5秒, 2分钟)
- ✅ 大文件上传可以看到逐步增长 (1% → 5% → 10% → ...)

## 📊 真实进度的数据来源

| 场景 | 数据来源 | 更新方式 |
|------|---------|---------|
| 文件上传 | `progressEvent.loaded / progressEvent.total` | axios 自动回调 |
| 批处理 | `job.processed_documents / job.total_documents` | 轮询 API |
| OCR识别 | `task.progress` 字段 | 轮询 API |
| 文档处理 | `document.processing_status` | WebSocket 推送 |

## 🚀 部署说明

所有修复已应用到：
- `/frontend/src/pages/Documents.tsx`
- `/frontend/src/pages/Upload.tsx`
- `/frontend/src/pages/upload/UploadPage.tsx`
- `/frontend/src/pages/workflows/steps/ProcessStepPage.tsx`

核心 API 服务：
- `/frontend/src/services/fieldmind.ts` (已支持 onUploadProgress)

## 🎉 结果

现在所有上传和处理操作都显示**真实的进度**：
- 上传进度 = 实际传输的字节数 / 文件总大小
- 处理进度 = 已处理的文档数 / 总文档数
- 不再有假动画卡在某个百分比

用户可以准确判断：
- ✅ 任务是否真的在进行
- ✅ 还需要等待多久
- ✅ 是否遇到了问题（进度停止）
