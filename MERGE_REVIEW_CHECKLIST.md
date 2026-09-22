# FieldMind 合并审查清单

生成时间: Sat Sep 19 11:21:02 CST 2026

## 📊 合并统计

- 服务文件已合并: 25
- ViewModel 文件已合并: 23
- 总计: 48

## ✅ 审查步骤

### 第一步：审查 *_Merged.swift 文件

所有合并后的文件都以 `_Merged.swift` 结尾，需要逐一审查：

#### 服务层
- [ ] BusinessAnalysisService_Merged.swift
- [ ] ChatService_Merged.swift
- [ ] ChronicleService_Merged.swift
- [ ] CitationService_Merged.swift
- [ ] DashboardService_Merged.swift
- [ ] DocumentService_Merged.swift
- [ ] FileAccessManager_Merged.swift
- [ ] FileManagerService_Merged.swift
- [ ] KeywordSearchService_Merged.swift
- [ ] KnowledgeGraphService_Merged.swift
- [ ] MemoryService_Merged.swift
- [ ] ModelConfigService_Merged.swift
- [ ] MonitoringService_Merged.swift
- [ ] PhotoService_Merged.swift
- [ ] ProjectService_Merged.swift
- [ ] ProposalService_Merged.swift
- [ ] ReportService_Merged.swift
- [ ] SOPAnalysisService_Merged.swift
- [ ] SOPService_Merged.swift
- [ ] SkillService_Merged.swift
- [ ] TableService_Merged.swift
- [ ] TimelineService_Merged.swift
- [ ] UploadFileSelectionHelper_Merged.swift
- [ ] VeinService_Merged.swift
- [ ] WorkflowService_Merged.swift

#### ViewModels
- [ ] ChatViewModel_Merged.swift
- [ ] ChronicleViewModel_Merged.swift
- [ ] CitationViewModel_Merged.swift
- [ ] ConversationViewModel_Merged.swift
- [ ] DashboardViewModel_Merged.swift
- [ ] DocumentViewModel_Merged.swift
- [ ] FileManagerViewModel_Merged.swift
- [ ] KeywordSearchViewModel_Merged.swift
- [ ] KnowledgeGraphViewModel_Merged.swift
- [ ] MemoryViewModel_Merged.swift
- [ ] ModelConfigViewModel_Merged.swift
- [ ] MonitoringViewModel_Merged.swift
- [ ] PhotoViewModel_Merged.swift
- [ ] ProjectViewModel_Merged.swift
- [ ] ProposalViewModel_Merged.swift
- [ ] ReportViewModel_Merged.swift
- [ ] SOPAnalysisViewModel_Merged.swift
- [ ] SOPViewModel_Merged.swift
- [ ] SkillViewModel_Merged.swift
- [ ] TableViewModel_Merged.swift
- [ ] TimelineViewModel_Merged.swift
- [ ] VeinViewModel_Merged.swift
- [ ] WorkflowViewModel_Merged.swift

### 第二步：对每个文件执行以下操作

1. **打开文件** - 在 Xcode 中打开
2. **审查注释区域** - 查看 "Native 版本的扩展功能" 部分
3. **整合有用功能** - 将有价值的代码移到主实现中
4. **删除注释** - 清理已整合或不需要的代码
5. **重命名文件** - 将 `*_Merged.swift` 重命名为 `*.swift`
6. **删除旧文件** - 删除原来的 `*.swift` 和 `*_Native.swift`
7. **编译测试** - ⌘+B 确保无编译错误

### 第三步：清理 Unified 目录

审查完成后，删除所有 Unified 目录：

```bash
rm -rf /Users/alwan/FieldMind/fieldmind/fieldmind/Services/Unified
rm -rf /Users/alwan/FieldMind/fieldmind/fieldmind/ViewModels/Unified
```

### 第四步：更新 UnifiedAppState

确保 UnifiedAppState.swift 使用合并后的服务：

```swift
// 检查所有服务引用
- ProjectService.shared
- DocumentService.shared
- ChatService.shared
// ... 等等
```

### 第五步：完整测试

- [ ] 项目管理功能
- [ ] 材料上传和蒸馏
- [ ] 知识库（笔记、图谱）
- [ ] AI 对话
- [ ] 时间线和报告
- [ ] 工作流和 SOP
- [ ] 后端自动启动

## 🎯 审查重点

### 需要特别关注的文件

1. **ProjectService** - 项目管理核心
2. **DocumentService** - 文档处理
3. **ChatService** - AI 对话
4. **KnowledgeGraphService** - 知识图谱
5. **TimelineService** - 时间线
6. **WorkflowService** - 工作流

### 常见合并模式

#### 模式 1：功能互补
- 主版本有 A 功能，Native 版本有 B 功能
- **操作**: 将 B 功能添加到主版本

#### 模式 2：实现不同
- 两个版本实现同一功能，但方法不同
- **操作**: 比较两种实现，选择更好的或结合两者优点

#### 模式 3：版本更新
- Native 版本是主版本的升级
- **操作**: 完全使用 Native 版本

#### 模式 4：废弃功能
- Native 版本的某些功能已过时
- **操作**: 仅保留主版本

## 📝 合并示例

### 示例：ProjectService

```swift
// ========================================
// 主实现
// ========================================
class ProjectService: ObservableObject {
    // 主版本的核心功能
    func listProjects() async throws -> [Project] {
        // ...
    }
}

// ========================================
// 从 Native 版本整合的功能
// ========================================
extension ProjectService {
    // Native 版本的额外功能
    func archiveProject(_ id: String) async throws {
        // 从 Native 版本迁移过来
    }

    func exportProject(_ id: String) async throws -> Data {
        // 从 Native 版本迁移过来
    }
}
```

## 🚀 完成后

所有审查完成后，运行：

```bash
# 1. 编译项目
cd /Users/alwan/FieldMind/fieldmind
xcodebuild -project fieldmind.xcodeproj -scheme fieldmind clean build

# 2. 如果成功，删除旧的 Native 项目
rm -rf /Users/alwan/FieldMind/frontend/fieldmind-native

# 3. 提交更改
cd /Users/alwan/FieldMind
git add .
git commit -m "深度整合完成：统一服务层和 ViewModels"

# 4. 推送
git push origin main
```

## ✅ 验收标准

- [ ] 所有 *_Merged.swift 文件已审查
- [ ] 所有 *_Native.swift 文件已删除
- [ ] Unified 目录已删除
- [ ] 项目编译无错误
- [ ] 所有功能测试通过
- [ ] 无重复代码
- [ ] 文档已更新

