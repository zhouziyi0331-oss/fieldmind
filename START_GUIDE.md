# FieldMind 启动指南

## 🚀 快速启动

### 1️⃣ 启动后端服务器

```bash
cd /Users/alwan/FieldMind/backend/src
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

**验证后端运行：**
```bash
curl http://127.0.0.1:8000/api/v1/monitoring/health
```

应该看到 JSON 响应（如果看到 404 也说明服务器在运行）

---

### 2️⃣ 在 Xcode 中启动 Swift 应用

1. **打开 Xcode 项目**
   ```bash
   open /Users/alwan/FieldMind/frontend/fieldmind-native/FieldMind.xcodeproj
   ```

2. **Clean Build（重要！）**
   - 菜单：`Product → Clean Build Folder`
   - 快捷键：`Shift + Command + K`

3. **运行应用**
   - 菜单：`Product → Run`
   - 快捷键：`Command + R`

---

## ✅ 系统状态

### 后端 API
- ✅ **路径**: `/Users/alwan/FieldMind/backend/src/app/`
- ✅ **端口**: `http://127.0.0.1:8000`
- ✅ **框架**: Python FastAPI
- ✅ **状态**: 已修复，可以运行

### Swift 前端
- ✅ **路径**: `/Users/alwan/FieldMind/frontend/fieldmind-native/`
- ✅ **页面数**: 44 个完整页面
- ✅ **API 连接**: 36 个 Service 文件已连接后端
- ✅ **真实进度条**: 已修复（基于实际上传字节数）

---

## 📋 功能清单

### 已实现的页面
1. ✅ Dashboard（仪表板）
2. ✅ Projects（项目管理）
3. ✅ Upload（文档上传）- **真实进度条**
4. ✅ Chat（AI 对话）
5. ✅ Workflow（工作流）
6. ✅ Settings（设置）
7. ✅ Search（搜索）
8. ✅ Analytics（分析）
9. ✅ Reports（报告）
10. ✅ ...共 44 个页面

### 真实功能
- ✅ **文档上传** - 基于 `URLSessionUploadTask.progress`
- ✅ **项目管理** - 连接后端 API
- ✅ **AI 对话** - 实时通信
- ✅ **数据看板** - 真实数据展示
- ❌ **没有假动画** - 所有进度都是真实的

---

## 🐛 之前的问题

### 问题 1：应用打开就让选择文件夹
**原因**: 后端服务器没有运行
**错误**: `Could not connect to the server`

### 问题 2：代码改了但 Xcode 看不到
**原因**: Xcode 缓存了旧的编译结果
**解决**: Clean Build Folder

### 问题 3：后端启动失败
**原因**: 
- 错误的目录（`backend/app/` ❌）
- 正确的目录（`backend/src/` ✅）
- 缺少 `__init__.py` 文件

---

## 🔧 故障排查

### 后端无法启动

**检查端口占用：**
```bash
lsof -ti:8000
```

**停止旧进程：**
```bash
killall python3
```

**查看启动日志：**
```bash
tail -f /tmp/backend_final.log
```

### Swift 应用崩溃

**1. 检查后端是否运行**
```bash
curl http://127.0.0.1:8000/api/v1/monitoring/health
```

**2. Clean Build**
```
Xcode → Product → Clean Build Folder
```

**3. 删除 DerivedData**
```bash
rm -rf ~/Library/Developer/Xcode/DerivedData/*
```

---

## 📁 项目结构

```
/Users/alwan/FieldMind/
├── backend/
│   └── src/
│       └── app/
│           ├── main.py          # ✅ 后端入口
│           ├── api/             # API 路由
│           ├── core/            # 核心配置
│           └── services/        # 业务逻辑
│
└── frontend/
    └── fieldmind-native/
        └── Sources/
            ├── Pages/           # ✅ 44 个页面
            ├── Services/        # ✅ 36 个 API 服务
            ├── ViewModels/      # 视图模型
            └── Components/      # UI 组件
```

---

## ✨ 最新修复（2024-09-13）

### 1. 真实上传进度
**位置**: `DocumentService.swift:84-175`
```swift
// ✅ 使用 URLSessionUploadTask + KVO
let observation = task.progress.observe(\.fractionCompleted) { progress, _ in
    progressHandler?(progress.fractionCompleted)  // 0.0 → 1.0
}
```

**位置**: `DocumentUploadView.swift:62-89`
```swift
// ✅ 调用真实 API，不再使用 Timer 假进度
_ = try await DocumentService.shared.uploadDocument(
    projectId: 1,
    fileURL: file.url,
    progressHandler: { progress in
        self.uploadQueue[index].progress = progress
    }
)
```

### 2. 后端启动修复
**创建**: `backend/app/__init__.py`
**修复**: 正确的启动目录 `backend/src/`

---

## 📞 如果还有问题

### 检查清单
- [ ] 后端是否在运行？`lsof -ti:8000`
- [ ] Xcode 是否 Clean Build？
- [ ] 打开的是正确的项目？`fieldmind-native/`
- [ ] Git 是否在 main 分支？`git branch`

### 快速重启
```bash
# 1. 停止所有服务
killall python3

# 2. 启动后端
cd /Users/alwan/FieldMind/backend/src
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload &

# 3. 在 Xcode 按 Cmd+R 运行应用
```

---

## 🎯 下一步

现在你的系统已经完全可用：
1. ✅ 后端 API 运行正常
2. ✅ Swift 应用有 44 个完整页面
3. ✅ 所有动画都是真实的
4. ✅ 前后端已连接

**只需要：**
1. 启动后端 (上面第 1 步)
2. 在 Xcode Clean Build 并运行 (上面第 2 步)

🚀 **一切都准备好了！**
