# FieldMind macOS App 快速启动指南

## 前置要求

- macOS 13.0 (Ventura) 或更高版本
- Xcode 15.0+
- Swift 5.9+
- 后端服务已启动（参见 backend/QUICKSTART.md）

## 1. 项目配置

### 1.1 打开项目

```bash
cd /Users/alwan/Desktop/FieldMindApp
open FieldMind.xcodeproj
```

### 1.2 配置后端地址

编辑 `Sources/FieldMind/Services/APIService.swift`，确认 baseURL：

```swift
private let baseURL = "http://localhost:8000"
```

如果后端部署在其他地址，修改此配置。

## 2. 构建与运行

### 2.1 在 Xcode 中运行

1. 选择 **FieldMind** scheme
2. 选择目标设备：**My Mac (Designed for iPad)** 或 **My Mac**
3. 点击 Run (⌘R)

### 2.2 命令行构建

```bash
xcodebuild -project FieldMind.xcodeproj \
  -scheme FieldMind \
  -configuration Debug \
  -destination 'platform=macOS' \
  build
```

## 3. 功能测试清单

### 3.1 基础对话测试

1. 启动应用
2. 创建或选择一个项目
3. 进入 **对话** 标签
4. 发送消息："你好，介绍一下自己"
5. 验证收到 AI 回复

### 3.2 增强对话测试

1. 点击右上角 **设置** 图标
2. 启用 **长记忆模式**
3. 发送消息："记住这个信息：项目代号是 Alpha-2024"
4. 发送新消息："我之前提到的项目代号是什么？"
5. 验证 AI 能够回忆起之前的信息

### 3.3 深度思考模式测试

1. 在设置中启用 **深度思考模式**
2. 发送复杂问题："设计一个支持百万级用户的实时聊天系统架构"
3. 点击回复中的 **查看思考过程** 按钮
4. 验证显示 AI 的推理步骤

### 3.4 技能模式测试

1. 在设置中点击 **选择技能**
2. 选择 "代码审查" 技能
3. 发送代码片段进行分析
4. 验证 AI 以专业代码审查的方式回复

### 3.5 记忆搜索测试

1. 点击右上角 **记忆搜索** 图标（🔍）
2. 输入搜索关键词："架构设计"
3. 查看相关历史记忆结果
4. 点击结果跳转到原对话

### 3.6 文档上传与 RAG 测试

1. 进入 **文档** 标签
2. 上传技术文档（PDF/TXT/MD）
3. 等待向量化完成
4. 在对话中提问文档相关内容
5. 验证 AI 引用文档作为来源

### 3.7 流式响应测试

1. 发送较长问题："详细解释 TCP 三次握手的过程"
2. 观察 AI 回复逐字显示（打字机效果）
3. 验证可以在响应过程中停止

### 3.8 项目隔离测试

1. 创建项目 A，发送消息："项目 A 的主题是人工智能"
2. 创建项目 B，发送消息："项目 B 的主题是区块链"
3. 切回项目 A，询问："这个项目的主题是什么？"
4. 验证 AI 只回忆项目 A 的记忆，不混淆项目 B

## 4. 配置选项

### 4.1 记忆配置

在 **设置 → 记忆配置** 中调整：

- **搜索深度** (1-20)：控制检索多少条历史记忆
- **相关性阈值** (0.5-0.95)：过滤低相关性记忆
- **最大上下文令牌** (1000-32000)：控制记忆上下文长度

推荐配置：
- 日常对话：深度 5，阈值 0.7，令牌 4000
- 深度研究：深度 15，阈值 0.65，令牌 16000
- 快速问答：深度 3，阈值 0.75，令牌 2000

### 4.2 技能配置

创建自定义技能（编辑 `app/config/skills.yaml`）：

```yaml
skills:
  - name: "代码审查"
    icon: "doc.text.magnifyingglass"
    prompt: |
      你是一位资深软件工程师，专注于代码质量和最佳实践。
      审查代码时关注：
      1. 代码可读性和维护性
      2. 性能优化机会
      3. 安全隐患
      4. 设计模式应用
      
  - name: "架构设计"
    icon: "building.2"
    prompt: |
      你是一位系统架构师，擅长设计可扩展、高可用的系统。
      设计架构时考虑：
      1. 业务需求和技术约束
      2. 可扩展性和性能
      3. 安全性和合规性
      4. 成本效益
```

## 5. 性能优化

### 5.1 内存管理

- 定期清理过期会话（设置 → 清理缓存）
- 限制单次加载的消息数量
- 启用消息分页加载

### 5.2 网络优化

- 使用流式响应减少等待时间
- 启用请求缓存（重复查询）
- 配置合理的超时时间（默认 30 秒）

### 5.3 向量检索优化

- 调整相关性阈值避免无关结果
- 使用合适的搜索深度（不是越多越好）
- 为大型文档库启用索引优化

## 6. 故障排查

### 问题：无法连接后端

**解决方案：**
1. 确认后端服务运行中：`curl http://localhost:8000/health`
2. 检查防火墙设置
3. 验证 `APIService.swift` 中的 baseURL 配置

### 问题：记忆功能无响应

**解决方案：**
1. 确认后端 `.env` 中 `LONG_MEMORY_ENABLED=true`
2. 检查向量数据库是否初始化
3. 查看后端日志：`tail -f logs/fieldmind.log`

### 问题：深度思考模式报错

**解决方案：**
1. 确认使用的是支持 thinking 的 Claude 模型
2. 检查 Anthropic API 额度
3. 降低 `THINKING_BUDGET_TOKENS` 参数

### 问题：文档向量化失败

**解决方案：**
1. 检查文档格式是否支持
2. 确认文件大小未超限（默认 10MB）
3. 验证 `sentence-transformers` 模型已下载

### 问题：回复速度慢

**解决方案：**
1. 减少记忆搜索深度
2. 关闭深度思考模式（日常对话不需要）
3. 检查网络延迟
4. 考虑使用更快的 Claude 模型（如 Haiku）

## 7. 数据结构

### 7.1 消息格式

```swift
struct Message {
    let id: UUID
    let sessionId: String
    let role: String  // "user" 或 "assistant"
    let content: String
    let timestamp: Date
    let metadata: MessageMetadata?
}

struct MessageMetadata {
    let thinkingProcess: String?
    let sources: [ChatSource]
    let tokensUsed: TokenUsage
    let modelUsed: String
}
```

### 7.2 会话管理

```swift
struct ChatSession {
    let id: String
    let projectId: Int?
    let title: String
    let createdAt: Date
    let updatedAt: Date
    var messages: [Message]
}
```

## 8. API 集成示例

### 8.1 发送增强消息

```swift
let response = try await apiService.sendEnhancedMessage(
    sessionId: session.id,
    message: userInput,
    projectId: currentProject?.id,
    useLongMemory: true,
    useDeepThinking: false,
    skillConfig: SkillChatConfig(
        skillName: "代码审查",
        workflowPrompt: "关注代码质量..."
    ),
    memoryConfig: MemoryChatConfig(
        searchDepth: 10,
        relevanceThreshold: 0.7,
        maxContextTokens: 8000
    )
)
```

### 8.2 搜索记忆

```swift
let results = try await apiService.searchMemory(
    query: "量子计算",
    projectId: currentProject?.id,
    topK: 5
)
```

### 8.3 获取记忆统计

```swift
let stats = try await apiService.getMemoryStatistics(
    projectId: currentProject?.id
)

print("短期记忆: \(stats.shortTermCount)")
print("中期记忆: \(stats.midTermCount)")
print("长期记忆: \(stats.longTermCount)")
```

## 9. 开发调试

### 9.1 启用详细日志

在 `main.swift` 中：

```swift
#if DEBUG
APIService.shared.enableDebugLogging = true
#endif
```

### 9.2 模拟数据测试

使用 `PreviewProvider` 进行 UI 测试：

```swift
struct EnhancedChatView_Previews: PreviewProvider {
    static var previews: some View {
        EnhancedChatView(session: .mock)
            .environmentObject(ProjectManager.shared)
    }
}
```

### 9.3 单元测试

```bash
xcodebuild test \
  -project FieldMind.xcodeproj \
  -scheme FieldMind \
  -destination 'platform=macOS'
```

## 10. 生产部署

### 10.1 构建 Release 版本

```bash
xcodebuild -project FieldMind.xcodeproj \
  -scheme FieldMind \
  -configuration Release \
  -destination 'platform=macOS' \
  -archivePath FieldMind.xcarchive \
  archive
```

### 10.2 代码签名

1. 在 Xcode 中配置 **Signing & Capabilities**
2. 选择开发团队
3. 启用自动签名管理

### 10.3 导出应用

```bash
xcodebuild -exportArchive \
  -archivePath FieldMind.xcarchive \
  -exportPath ./build \
  -exportOptionsPlist ExportOptions.plist
```

## 11. 完整功能清单

✅ **基础对话**
✅ **长记忆系统** - 三层记忆架构
✅ **深度思考模式** - Extended Thinking
✅ **技能模式** - 领域专用对话
✅ **记忆搜索** - 向量相似度检索
✅ **文档 RAG** - 文档问答
✅ **流式响应** - 实时打字效果
✅ **项目隔离** - 独立记忆空间
✅ **思考过程可视化** - 查看 AI 推理
✅ **来源引用** - 显示文档来源
✅ **令牌统计** - 成本监控

## 12. 下一步

1. **自定义技能** - 创建适合您领域的 AI 助手
2. **优化提示词** - 提高对话质量
3. **集成更多功能** - 语音输入、图像理解等
4. **性能监控** - 跟踪响应时间和准确性
5. **用户反馈** - 收集真实使用数据

## 技术支持

- 完整文档: [LONG_MEMORY_COMPLETE.md](../LONG_MEMORY_COMPLETE.md)
- 架构说明: [LONG_MEMORY_IMPLEMENTATION.md](../LONG_MEMORY_IMPLEMENTATION.md)
- 后端指南: [backend/QUICKSTART.md](../../FieldMind-Rebuild/fieldmind-backend/QUICKSTART.md)
- API 文档: http://localhost:8000/docs
