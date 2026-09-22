# Xcode 重新编译步骤

## 🎯 确保看到最新代码改动

### 方法 1：Clean Build（推荐）
```bash
1. 在 Xcode 菜单栏：Product → Clean Build Folder
   或按快捷键：Shift + Command + K

2. 等待清理完成（几秒钟）

3. 重新编译：Product → Build
   或按快捷键：Command + B

4. 运行：Product → Run
   或按快捷键：Command + R
```

### 方法 2：删除 DerivedData（彻底清理）
```bash
1. 在 Xcode 菜单栏：Xcode → Settings → Locations

2. 点击 DerivedData 路径旁边的箭头图标
   （会打开 Finder 显示缓存文件夹）

3. 关闭 Xcode

4. 在 Finder 中删除你的项目文件夹
   （通常是 FieldMind-xxxxx）

5. 重新打开 Xcode 项目文件

6. 编译运行：Command + R
```

### 方法 3：命令行编译（终极方案）
```bash
# 进入项目目录
cd /Users/alwan/FieldMind/frontend/fieldmind-native

# 清理构建缓存
swift package clean

# 重新构建
swift build

# 或者用 xcodebuild
xcodebuild clean -scheme FieldMind
xcodebuild build -scheme FieldMind
```

---

## ✅ 验证改动是否生效

### 检查点 1：查看代码
在 Xcode 中打开 `DocumentService.swift:84`，应该看到：
```swift
func uploadDocument(
    projectId: Int,
    fileURL: URL,
    autoProcess: Bool = true,
    progressHandler: ((Double) -> Void)? = nil  // ⬅️ 这行是新加的
) async throws -> DocumentUploadResponse
```

### 检查点 2：查看上传视图
打开 `DocumentUploadView.swift:65`，应该看到：
```swift
_ = try await DocumentService.shared.uploadDocument(
    projectId: 1,
    fileURL: file.url,
    autoProcess: true,
    progressHandler: { progress in  // ⬅️ 真实进度回调
        DispatchQueue.main.async {
            self.uploadQueue[index].progress = progress
        }
    }
)
```

### 检查点 3：运行时测试
1. 启动应用
2. 上传一个 **大文件**（比如 10MB+）
3. 观察进度条：
   - ✅ **真实进度**：会显示 3%, 8%, 15%, 42%... 逐步增长
   - ❌ **假进度**：会匀速从 0% 到 100%，不管文件大小

---

## 📁 已修改的文件

### 1. DocumentService.swift
**位置：** `frontend/fieldmind-native/Sources/Services/DocumentService.swift`
**改动：**
- 第 84-88 行：添加 `progressHandler` 参数
- 第 143-175 行：使用 `URLSessionUploadTask` + KVO 追踪真实进度

### 2. DocumentUploadView.swift  
**位置：** `Views/DocumentUploadView.swift`
**改动：**
- 第 62-89 行：删除 `Timer.scheduledTimer` 假进度
- 改用真实的 `DocumentService.shared.uploadDocument()`

### 3. SWIFT_REAL_PROGRESS_FIX.md
**位置：** `FieldMind/SWIFT_REAL_PROGRESS_FIX.md`
**内容：** 完整的技术文档和实现说明

---

## 🚨 如果还是看不到改动

### 可能的原因
1. **打开了错误的项目**
   - 确认路径：`/Users/alwan/FieldMind/frontend/fieldmind-native/`
   - 不是：`/Users/alwan/FieldMind/frontend/desktop/`

2. **Git 分支不对**
   ```bash
   cd /Users/alwan/FieldMind
   git branch  # 应该在 main 分支
   git log --oneline -1  # 应该显示 6c728b84
   ```

3. **文件没有加入 Xcode 项目**
   - 在 Xcode 左侧 Project Navigator 中查看文件是否存在
   - 如果显示为红色/灰色，右键 → Add Files to "FieldMind"

---

## 📞 快速验证命令

```bash
# 1. 确认文件存在
ls -la /Users/alwan/FieldMind/frontend/fieldmind-native/Sources/Services/DocumentService.swift

# 2. 确认改动已提交
cd /Users/alwan/FieldMind
git show 6c728b84 --stat

# 3. 查看当前代码内容
grep -A 5 "func uploadDocument" /Users/alwan/FieldMind/frontend/fieldmind-native/Sources/Services/DocumentService.swift
```
