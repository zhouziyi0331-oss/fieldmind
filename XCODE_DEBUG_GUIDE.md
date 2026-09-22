# Xcode 调试指南 - 修复 FieldMind API 响应解析问题

## 🎯 问题概述

三个核心问题：
1. **照片API** - 解码失败: 缺失键 'file_size' 路径: photos.Index 0
2. **表格API** - 解码失败: 缺失键 'project_id' 路径: tables.Index 0
3. **文件树API** - 解码失败: 缺失键 'total_files' 路径

## 📋 使用 Xcode 调试步骤

### 步骤1：打开项目
```bash
cd /Users/alwan/FieldMind/frontend/fieldmind-native
open Package.swift
```

这会用 Xcode 打开项目。

### 步骤2：清理并重新构建
1. 在 Xcode 菜单栏：**Product → Clean Build Folder** (或按 `Cmd + Shift + K`)
2. 等待清理完成
3. **Product → Build** (或按 `Cmd + B`)
4. 确认编译成功（无错误）

### 步骤3：运行并查看控制台
1. **Product → Run** (或按 `Cmd + R`)
2. 应用会启动
3. 在 Xcode 底部，点击 **Show the Debug area** (或按 `Cmd + Shift + Y`)
4. 你会看到控制台输出

### 步骤4：触发问题并查看日志

在运行的应用中：
1. 访问**照片管理**页面
2. 访问**表格管理**页面
3. 访问**文件管理器**页面

在 Xcode 控制台中，你应该会看到详细的日志：

```
🔍 [APIClient] 原始响应: {"success":true,"data":{"photos":[...]...
⚠️ [APIClient] 直接解码失败，尝试提取data字段
🔍 [APIClient] JSON keys: success, data, error, metadata
🔍 [APIClient] success字段: true
✅ [APIClient] 找到success=true和data字段
✅ [APIClient] 从data字段解码成功
```

或者如果还有错误：

```
❌ [APIClient] 从data字段解码失败: ...
   缺失键: 'file_size'
```

### 步骤5：根据日志判断

#### 情况A：看到 "✅ 从data字段解码成功"
**说明修复生效了！** 问题应该已解决。

#### 情况B：看到 "❌ 从data字段解码失败: 缺失键 'file_size'"
**说明还有问题。** 请执行步骤6。

#### 情况C：完全没有看到 [APIClient] 日志
**说明代码没有执行。** 可能是：
- 编译的不是最新代码
- 应用使用了缓存版本
- 需要完全重启 Xcode

### 步骤6：如果还有问题 - 设置断点调试

1. 在 Xcode 左侧，打开文件：
   `Sources/Network/APIClient.swift`

2. 找到 `decodePayload` 方法（大约第105行）

3. 在这一行左侧点击，添加断点：
   ```swift
   private static func decodePayload<T: Decodable>(_ data: Data, as type: T.Type, decoder: JSONDecoder) throws -> T {
   ```

4. 重新运行应用 (`Cmd + R`)

5. 当访问照片/表格页面时，程序会暂停在断点处

6. 在调试区域，你可以：
   - 查看变量值
   - 单步执行代码 (`F6` 逐行，`F7` 进入函数)
   - 查看 `data` 的实际内容

### 步骤7：检查实际返回的JSON

在断点处，在控制台输入：

```swift
po String(data: data, encoding: .utf8)
```

这会显示后端返回的原始JSON。复制这段JSON，我可以帮你分析。

## 🔍 我已经修改的文件

### 1. APIClient.swift
**位置**: `Sources/Network/APIClient.swift`

**关键修改**:
- 第99-102行：统一使用 `convertFromSnakeCase` 策略
- 第105-180行：增强的 `decodePayload` 方法，添加详细日志

### 2. PhotoService.swift
**位置**: `Sources/Services/PhotoService.swift`

**关键代码** (第27-34行)：
```swift
enum CodingKeys: String, CodingKey {
    case id, filename, format, width, height, location, device, tags
    case fileSize = "file_size"      // ← 映射 snake_case
    case filePath = "file_path"
    case takenAt = "taken_at"
    case projectId = "project_id"
    case uploadedAt = "uploaded_at"
}
```

这个映射应该能正确处理后端的 `file_size` 字段。

## 🚨 预期结果

### 如果修复成功
- ✅ 照片管理页面正常显示照片列表
- ✅ 表格管理页面正常显示表格列表
- ✅ 文件管理器显示文件树
- ✅ 文档字数根据状态显示（待处理/处理中/实际字数）

### 如果还有问题
请复制 Xcode 控制台的完整错误日志（特别是 `[APIClient]` 开头的部分），或者使用断点查看实际的响应数据，然后告诉我。

## 💡 额外提示

1. **如果 Xcode 太慢**，可以使用命令行查看日志：
   ```bash
   cd /Users/alwan/FieldMind/frontend/fieldmind-native
   swift run 2>&1 | grep -E "APIClient|解码"
   ```

2. **如果怀疑缓存问题**：
   ```bash
   rm -rf ~/Library/Developer/Xcode/DerivedData/FieldMindNative-*
   ```
   然后重新在 Xcode 中构建。

3. **查看后端实际返回的数据**（确认格式）：
   ```bash
   curl "http://127.0.0.1:8013/api/photos?project_id=1" | python3 -m json.tool
   ```

---

**下一步**: 打开 Xcode，运行应用，查看控制台日志，然后告诉我结果。
