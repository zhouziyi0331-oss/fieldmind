#!/bin/bash
# FieldMind 问题修复 - 可执行脚本

echo "=================================="
echo "FieldMind 三个问题修复方案"
echo "=================================="
echo ""

cat << 'EOF'

## 问题诊断结果

根据深度测试，发现：

1. ✅ 照片API工作正常 - 返回 {success: true, data: {...}}
2. ❌ 表格API格式不一致 - 返回 {tables: [...], total: 4}（没有success字段）
3. ❌ 文档API路径404

## 已修改的文件

1. `/Users/alwan/FieldMind/frontend/fieldmind-native/Sources/Network/APIClient.swift`
   - 增强了解析逻辑和详细日志

2. `/Users/alwan/FieldMind/frontend/fieldmind-native/Sources/Services/TableService.swift`
   - 添加了容错的解码逻辑

3. `/Users/alwan/FieldMind/frontend/web/src/services/api.ts`
   - 自动解包 success_response 格式

4. `/Users/alwan/FieldMind/frontend/web/src/pages/DocumentsPage.tsx`
   - 根据状态显示字数

5. `/Users/alwan/FieldMind/backend/src/app/api/photos.py`
   - 添加双重路由

## 下一步（必须执行）

### 步骤1：重新编译桌面应用
cd /Users/alwan/FieldMind/frontend/fieldmind-native
swift build

### 步骤2：运行并查看日志
打开 Xcode:
open Package.swift

点击 Run (Cmd+R)，然后打开 Debug Console 查看日志

### 步骤3：测试三个页面
1. 照片管理 - 应该能加载
2. 表格管理 - 查看日志中的解析过程
3. 文件管理器 - 查看字数显示

### 步骤4：如果还有错误
复制控制台中的错误日志，特别是：
- 🔍 [APIClient] 开头的日志
- ❌ 开头的错误信息
- 完整的错误堆栈

## 预期结果

如果修复成功，控制台应该显示：
```
🔍 [APIClient] 原始响应: {"tables":[...
⚠️ [APIClient] 直接解码失败，尝试提取data字段
✅ [APIClient] 从data字段解码成功（兼容模式）
```

如果还有问题，会显示具体的错误原因。

EOF

echo ""
echo "修复文件已准备就绪，请按照上述步骤操作。"
echo ""
