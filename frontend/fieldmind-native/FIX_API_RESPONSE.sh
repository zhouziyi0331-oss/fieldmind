#!/bin/bash
# FieldMind Native 桌面应用 - API响应格式深度修复脚本

echo "=================================="
echo "🔧 FieldMind Native 深度修复"
echo "=================================="
echo ""

# 修复内容概述
cat << 'EOF'

## 🎯 问题根源分析

根据深度诊断，发现了真正的问题所在：

### 问题1：照片和表格"数据解析失败"

**Swift APIClient 的解析逻辑**（APIClient.swift 第105-116行）：

```swift
private static func decodePayload<T: Decodable>(_ data: Data, as type: T.Type, decoder: JSONDecoder) throws -> T {
    do {
        return try decoder.decode(T.self, from: data)  // 先尝试直接解码整个响应
    } catch {
        // 失败后，尝试提取 data 字段
        guard let object = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let nested = object["data"],
              JSONSerialization.isValidJSONObject(nested) else {
            throw error
        }
        return try decoder.decode(T.self, from: JSONSerialization.data(withJSONObject: nested))
    }
}
```

**后端返回格式**：
```json
{
  "success": true,
  "data": {
    "photos": [...],
    "total": 10
  },
  "error": null,
  "metadata": {...}
}
```

**Swift期望的数据结构**：
```swift
struct PhotoListResponse: Codable {
    let photos: [PhotoResponse]
    let total: Int
    let page: Int
    let pageSize: Int
}
```

**问题**：
1. 第一次尝试直接解码整个响应失败（因为多了success, error, metadata字段）
2. 第二次尝试提取data字段，但可能因为某些原因失败
3. 导致抛出"数据解析失败"错误

### 问题2：文件字数显示错误

**文件管理器显示的字数字段**：
```swift
struct FileNodeResponse: Codable {
    let id: String
    let name: String
    let type: String
    let size: Int64
    let wordCount: Int?  // ← 这个字段
    // ...
}
```

**后端返回**：
- 文档上传后，`word_count` 字段为0或null
- 只有处理完成后才会更新
- 前端直接显示这个值，不检查文档状态

## ✅ 修复方案

### 修复1：优化 APIClient 解析逻辑

需要增强 Swift 端的解析容错性，确保能正确提取 data 字段。

### 修复2：修复 PhotoService 的 API 路径

当前代码：
```swift
var endpoint = APIEndpoint.custom("/photos")  // ❌
```

应该改为：
```swift
var endpoint = APIEndpoint.photos  // ✅ 使用正确的端点定义
```

### 修复3：FileManagerService 字数显示逻辑

需要在显示层检查文档状态，而不是直接显示 word_count。

## 🔧 具体修复步骤

EOF

echo ""
echo "正在检查修复文件..."
echo ""

# 检查需要修复的文件
NATIVE_DIR="/Users/alwan/FieldMind/frontend/fieldmind-native/Sources"

if [ ! -d "$NATIVE_DIR" ]; then
    echo "❌ 找不到 fieldmind-native 目录"
    exit 1
fi

echo "✅ 找到 fieldmind-native 目录"
echo ""

# 列出需要修复的文件
echo "需要修复的文件："
echo "  1. Network/APIClient.swift - 增强解析容错性"
echo "  2. Services/PhotoService.swift - 修复API路径"
echo "  3. Services/FileManagerService.swift - 优化字数显示"
echo "  4. Network/APIEndpoint.swift - 添加正确的端点定义"
echo ""

echo "=================================="
echo "📋 修复方案详细说明"
echo "=================================="
echo ""

cat << 'EOF'

### 修复1：APIClient.swift 增强解析

在 decodePayload 方法中添加更详细的日志和更强的容错：

```swift
private static func decodePayload<T: Decodable>(_ data: Data, as type: T.Type, decoder: JSONDecoder) throws -> T {
    // 先打印原始响应用于调试
    if let jsonString = String(data: data, encoding: .utf8) {
        print("🔍 [APIClient] 原始响应: \(jsonString.prefix(500))")
    }

    do {
        // 尝试直接解码
        let result = try decoder.decode(T.self, from: data)
        print("✅ [APIClient] 直接解码成功")
        return result
    } catch let directError {
        print("⚠️ [APIClient] 直接解码失败: \(directError)")

        // 尝试提取 data 字段
        guard let object = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            print("❌ [APIClient] JSON序列化失败")
            throw directError
        }

        print("🔍 [APIClient] JSON keys: \(object.keys)")

        // 检查是否有 success 和 data 字段
        if let success = object["success"] as? Bool, success == true,
           let nested = object["data"] {
            print("✅ [APIClient] 找到 success=true 和 data 字段")

            guard JSONSerialization.isValidJSONObject(nested) else {
                print("❌ [APIClient] data 字段不是有效的JSON对象")
                throw directError
            }

            do {
                let dataJSON = try JSONSerialization.data(withJSONObject: nested)
                let result = try decoder.decode(T.self, from: dataJSON)
                print("✅ [APIClient] 从 data 字段解码成功")
                return result
            } catch let dataError {
                print("❌ [APIClient] 从 data 字段解码失败: \(dataError)")
                throw dataError
            }
        }

        print("❌ [APIClient] 未找到有效的 success/data 结构")
        throw directError
    }
}
```

### 修复2：PhotoService.swift 修复API路径

当前问题：
```swift
var endpoint = APIEndpoint.custom("/photos")  // 第79行
```

修复为：
```swift
var endpoint = APIEndpoint.custom("/photos")
    .with(queryItem: "project_id", value: "\(projectId)")
    // ... 其他参数
```

并确保 APIEndpoint 正确定义：
```swift
// APIEndpoint.swift
enum APIEndpoint {
    case photos
    case photoStats(Int)
    case custom(String)

    var path: String {
        switch self {
        case .photos:
            return "/photos"  // APIConfig.baseURL 会添加 /api 前缀
        case .photoStats(let projectId):
            return "/photos/stats/\(projectId)"
        case .custom(let path):
            return path
        }
    }
}
```

### 修复3：文件字数显示逻辑

需要在 UI 层面根据文档状态决定显示内容：

```swift
// FileNodeResponse 添加状态字段
struct FileNodeResponse: Codable {
    let id: String
    let name: String
    let type: String
    let size: Int64
    let wordCount: Int?
    let status: String?  // ← 添加这个字段
    // ...
}

// UI 显示逻辑
func displayWordCount(for file: FileNodeResponse) -> String {
    guard file.type == "document" else { return "-" }

    switch file.status {
    case "completed":
        return file.wordCount?.formatted() ?? "0"
    case "processing":
        return "处理中..."
    case "pending":
        return "待处理"
    default:
        return "-"
    }
}
```

### 修复4：后端API确保返回 status 字段

确保后端在文件树响应中包含文档状态：

```python
# backend/src/app/api/file_manager.py
def _build_node(doc: ProjectDocument) -> dict:
    return {
        "id": str(doc.id),
        "name": doc.filename,
        "type": "file",
        "size": doc.file_size or 0,
        "word_count": doc.word_count or 0,
        "status": doc.status,  # ← 确保返回这个字段
        "file_type": doc.file_type,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
    }
```

EOF

echo ""
echo "=================================="
echo "🚀 执行修复"
echo "=================================="
echo ""

echo "⚠️  注意：以下修复需要手动执行"
echo ""
echo "步骤1：打开 Xcode 项目"
echo "  cd /Users/alwan/FieldMind/frontend/fieldmind-native"
echo "  open Package.swift"
echo ""
echo "步骤2：修改 APIClient.swift"
echo "  增强 decodePayload 方法的日志和容错"
echo ""
echo "步骤3：修改 PhotoService.swift"
echo "  确认 API 路径正确"
echo ""
echo "步骤4：修改 FileManagerService.swift"
echo "  添加 status 字段到 FileNodeResponse"
echo ""
echo "步骤5：修改文件管理器 UI"
echo "  根据状态显示字数"
echo ""
echo "步骤6：重新编译运行"
echo "  Command + R 重新运行应用"
echo ""

echo "=================================="
echo "✅ 修复方案已生成"
echo "=================================="
