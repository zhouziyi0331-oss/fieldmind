# 前端页面需求文档

## 执行摘要

**设计目标**: 创建专业、简洁、高效的桌面应用前端  
**设计风格**: 折叠式布局 + 卡片化设计 + 无 emoji + 专业配色  
**技术栈**: SwiftUI (macOS)

---

## 设计原则

### 1. 视觉层次
- 清晰的信息架构
- 合理的视觉权重
- 明确的操作引导

### 2. 交互体验
- 流畅的动画过渡
- 即时的反馈响应
- 智能的状态管理

### 3. 色彩系统
- 主色调：深灰蓝 (#2D3748) - 专业沉稳
- 强调色：青绿色 (#38B2AC) - 活力清新
- 中性色：灰度色阶 - 层次分明
- 语义色：成功/警告/错误/信息

### 4. 布局原则
- 三栏布局：侧边栏 + 主内容区 + 属性面板
- 折叠式设计：所有面板可折叠
- 响应式：适配不同窗口尺寸

---

## 现有页面清单

### ✅ 已完成的页面

| 页面 | 文件 | 功能 | 完成度 |
|------|------|------|--------|
| 主视图 | MainView.swift | 应用主框架 | 100% |
| 侧边栏 | SidebarView.swift | 导航菜单 | 100% |
| 顶部栏 | TopBarView.swift | 全局操作 | 100% |
| 项目列表 | ProjectListView.swift | 项目网格展示 | 100% |
| 新建项目 | NewProjectView.swift | 项目创建表单 | 100% |
| 知识网络 | KnowledgeNetworkView.swift | 知识图谱可视化 | 100% |
| 业态分析 | BusinessAnalysisView.swift | 业态评估展示 | 100% |

---

## 缺失页面需求（5 个）

### 1. DashboardView - 数据看板

#### 功能定位
项目数据总览，快速掌握项目状态

#### 页面结构
```
┌─────────────────────────────────────────────────────────────┐
│  Dashboard - 项目名称                            [刷新] [导出] │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐  │
│  │  项目数量  │ │  文档总数  │ │ 处理进度  │ │ 知识节点  │  │
│  │    12     │ │    156    │ │   85%    │ │   2,340   │  │
│  └───────────┘ └───────────┘ └───────────┘ └───────────┘  │
│                                                               │
│  ┌────────────────────────────┐ ┌────────────────────────┐ │
│  │  文档处理趋势              │ │  知识网络分布          │ │
│  │  [折线图]                 │ │  [饼图]               │ │
│  │                            │ │                        │ │
│  └────────────────────────────┘ └────────────────────────┘ │
│                                                               │
│  ┌────────────────────────────┐ ┌────────────────────────┐ │
│  │  热门主题                  │ │  最近活动              │ │
│  │  [标签云]                 │ │  [时间线]             │ │
│  │                            │ │                        │ │
│  └────────────────────────────┘ └────────────────────────┘ │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

#### 核心组件

**1. 统计卡片 (StatCard)**
```swift
struct StatCard: View {
    let title: String
    let value: String
    let trend: Double?  // 增长率
    let icon: String?   // SF Symbol
    
    var body: some View {
        CardView {
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Text(title)
                        .font(.caption)
                        .foregroundColor(.secondary)
                    Spacer()
                    if let icon = icon {
                        Image(systemName: icon)
                    }
                }
                
                Text(value)
                    .font(.title)
                    .fontWeight(.bold)
                
                if let trend = trend {
                    HStack(spacing: 4) {
                        Image(systemName: trend >= 0 ? "arrow.up" : "arrow.down")
                        Text("\(abs(trend), specifier: "%.1f")%")
                    }
                    .font(.caption)
                    .foregroundColor(trend >= 0 ? .green : .red)
                }
            }
        }
    }
}
```

**2. 图表卡片 (ChartCard)**
```swift
struct ChartCard<Content: View>: View {
    let title: String
    let content: Content
    
    var body: some View {
        CardView {
            VStack(alignment: .leading, spacing: 12) {
                Text(title)
                    .font(.headline)
                content
                    .frame(height: 200)
            }
        }
    }
}
```

**3. 活动时间线 (ActivityTimeline)**
```swift
struct ActivityTimeline: View {
    let activities: [Activity]
    
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 12) {
                ForEach(activities) { activity in
                    HStack(alignment: .top, spacing: 12) {
                        Circle()
                            .fill(activity.type.color)
                            .frame(width: 10, height: 10)
                        
                        VStack(alignment: .leading, spacing: 4) {
                            Text(activity.title)
                                .font(.body)
                            Text(activity.timestamp)
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                    }
                }
            }
        }
    }
}
```

#### 数据源
- GET `/api/v1/dashboard/stats/{project_id}` - 统计数据
- GET `/api/v1/dashboard/progress/{project_id}` - 处理进度
- GET `/api/v1/dashboard/timeline/{project_id}` - 活动时间线

---

### 2. ProjectDetailView - 项目详情

#### 功能定位
项目全方位管理，包含文档、分析、设置

#### 页面结构
```
┌─────────────────────────────────────────────────────────────┐
│  ← 返回    项目详情                          [编辑] [删除]   │
├────────┬────────────────────────────────────────────────────┤
│        │  ┌─────────────────────────────────────────────┐  │
│  文档  │  │  项目信息                                    │  │
│  树状  │  │  名称: XXX                                   │  │
│  列表  │  │  创建时间: 2026-09-01                        │  │
│        │  │  文档数: 156 | 知识节点: 2,340              │  │
│  [可折 │  └─────────────────────────────────────────────┘  │
│   叠]  │                                                     │
│        │  ┌─────────────────────────────────────────────┐  │
│  📁根  │  │  Tab 切换                                    │  │
│   └文1 │  │  [文档] [知识网络] [业态分析] [设置]        │  │
│   └文2 │  │                                              │  │
│  📁分类│  │  当前 Tab 内容区域                           │  │
│   └文3 │  │                                              │  │
│        │  │                                              │  │
│        │  └─────────────────────────────────────────────┘  │
└────────┴────────────────────────────────────────────────────┘
```

#### 核心组件

**1. 项目信息卡片**
```swift
struct ProjectInfoCard: View {
    let project: Project
    
    var body: some View {
        CardView {
            VStack(alignment: .leading, spacing: 12) {
                HStack {
                    VStack(alignment: .leading) {
                        Text(project.name)
                            .font(.title2)
                            .fontWeight(.bold)
                        Text(project.description ?? "无描述")
                            .foregroundColor(.secondary)
                    }
                    Spacer()
                    // 项目标签
                    ForEach(project.tags, id: \.self) { tag in
                        Text(tag)
                            .font(.caption)
                            .padding(.horizontal, 8)
                            .padding(.vertical, 4)
                            .background(Color.blue.opacity(0.1))
                            .cornerRadius(4)
                    }
                }
                
                Divider()
                
                HStack(spacing: 24) {
                    InfoItem(label: "创建时间", value: project.createdAt.formatted())
                    InfoItem(label: "文档数", value: "\(project.documentCount)")
                    InfoItem(label: "知识节点", value: "\(project.nodeCount)")
                }
            }
        }
    }
}
```

**2. 文档树状视图**
```swift
struct DocumentTreeView: View {
    let documents: [Document]
    @State private var selectedDocument: Document?
    
    var body: some View {
        List(selection: $selectedDocument) {
            ForEach(groupedDocuments, id: \.key) { category, docs in
                DisclosureGroup(category) {
                    ForEach(docs) { doc in
                        DocumentTreeItem(document: doc)
                    }
                }
            }
        }
        .listStyle(.sidebar)
    }
}
```

**3. Tab 内容区**
```swift
struct ProjectTabContent: View {
    @Binding var selectedTab: Int
    let project: Project
    
    var body: some View {
        TabView(selection: $selectedTab) {
            DocumentsTabView(projectId: project.id)
                .tag(0)
            
            KnowledgeNetworkView(projectId: project.id)
                .tag(1)
            
            BusinessAnalysisView(projectId: project.id)
                .tag(2)
            
            ProjectSettingsView(project: project)
                .tag(3)
        }
    }
}
```

---

### 3. DocumentUploadView - 文档上传

#### 功能定位
文档上传、批量导入、进度追踪

#### 页面结构
```
┌─────────────────────────────────────────────────────────────┐
│  文档上传                                        [×关闭]      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                                                         │  │
│  │              [拖拽区域]                                │  │
│  │                                                         │  │
│  │      将文件拖拽到此处                                  │  │
│  │      或                                                 │  │
│  │      [选择文件] [选择文件夹]                          │  │
│  │                                                         │  │
│  │      支持格式: PDF, Word, TXT, Markdown               │  │
│  │      最大单文件: 50MB                                  │  │
│  │                                                         │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
│  上传队列 (3 个文件)                                         │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  文档1.pdf                    [进度条 75%]    [×取消]  │  │
│  │  文档2.docx                   [进度条 50%]    [×取消]  │  │
│  │  文档3.txt                    [等待中...]     [×取消]  │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
│  [暂停全部] [继续全部] [清空队列]            [开始上传]     │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

#### 核心组件

**1. 拖拽上传区域**
```swift
struct DropZone: View {
    @Binding var isDragging: Bool
    let onDrop: ([URL]) -> Void
    
    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: "arrow.down.doc")
                .font(.system(size: 48))
                .foregroundColor(.secondary)
            
            Text("将文件拖拽到此处")
                .font(.title3)
            
            Text("或")
                .foregroundColor(.secondary)
            
            HStack(spacing: 12) {
                Button("选择文件") {
                    selectFiles()
                }
                .buttonStyle(.bordered)
                
                Button("选择文件夹") {
                    selectFolder()
                }
                .buttonStyle(.bordered)
            }
            
            Text("支持格式: PDF, Word, TXT, Markdown")
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(
            RoundedRectangle(cornerRadius: 12)
                .stroke(style: StrokeStyle(lineWidth: 2, dash: [8]))
                .foregroundColor(isDragging ? .blue : .gray.opacity(0.3))
        )
        .onDrop(of: [.fileURL], isTargeted: $isDragging) { providers in
            handleDrop(providers)
        }
    }
}
```

**2. 上传队列项**
```swift
struct UploadQueueItem: View {
    let file: UploadFile
    let onCancel: () -> Void
    
    var body: some View {
        HStack {
            Image(systemName: file.icon)
            
            VStack(alignment: .leading, spacing: 4) {
                Text(file.name)
                    .font(.body)
                
                if file.status == .uploading {
                    ProgressView(value: file.progress)
                        .frame(height: 4)
                } else {
                    Text(file.status.description)
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
            
            Spacer()
            
            Text("\(Int(file.progress * 100))%")
                .font(.caption)
                .foregroundColor(.secondary)
            
            Button(action: onCancel) {
                Image(systemName: "xmark.circle.fill")
            }
            .buttonStyle(.plain)
        }
        .padding(12)
        .background(Color.gray.opacity(0.05))
        .cornerRadius(8)
    }
}
```

#### 数据源
- POST `/api/v1/documents/upload` - 上传单个文档
- POST `/api/v1/documents/batch-upload` - 批量上传
- GET `/api/v1/documents/upload-progress/{task_id}` - 查询进度

---

### 4. DocumentListView - 文档列表

#### 功能定位
文档浏览、搜索、筛选、排序

#### 页面结构
```
┌─────────────────────────────────────────────────────────────┐
│  文档列表                                                     │
├─────────────────────────────────────────────────────────────┤
│  [搜索框]  [筛选▼] [排序▼]  [卡片视图/列表视图]  [+上传]   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐          │
│  │  [缩略] │ │  [缩略] │ │  [缩略] │ │  [缩略] │          │
│  │         │ │         │ │         │ │         │          │
│  │ 文档1   │ │ 文档2   │ │ 文档3   │ │ 文档4   │          │
│  │ PDF·2MB │ │ Word·1MB│ │ TXT·500K│ │ PDF·3MB │          │
│  │ 已处理  │ │ 处理中  │ │ 已处理  │ │ 失败    │          │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘          │
│                                                               │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐          │
│  │  ...    │ │  ...    │ │  ...    │ │  ...    │          │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘          │
│                                                               │
│  共 156 个文档              [上一页] 1 / 16 [下一页]         │
└─────────────────────────────────────────────────────────────┘
```

#### 核心组件

**1. 搜索和筛选栏**
```swift
struct DocumentFilterBar: View {
    @Binding var searchText: String
    @Binding var filters: DocumentFilters
    @Binding var sortBy: SortOption
    @Binding var viewMode: ViewMode
    
    var body: some View {
        HStack(spacing: 12) {
            // 搜索框
            SearchField(text: $searchText, placeholder: "搜索文档...")
            
            // 筛选按钮
            Menu {
                ForEach(DocumentType.allCases) { type in
                    Toggle(type.name, isOn: binding(for: type))
                }
            } label: {
                Label("筛选", systemImage: "line.3.horizontal.decrease.circle")
            }
            
            // 排序按钮
            Menu {
                ForEach(SortOption.allCases) { option in
                    Button(option.name) {
                        sortBy = option
                    }
                }
            } label: {
                Label("排序", systemImage: "arrow.up.arrow.down")
            }
            
            Spacer()
            
            // 视图切换
            Picker("", selection: $viewMode) {
                Image(systemName: "square.grid.2x2").tag(ViewMode.card)
                Image(systemName: "list.bullet").tag(ViewMode.list)
            }
            .pickerStyle(.segmented)
            .frame(width: 100)
            
            // 上传按钮
            Button(action: showUpload) {
                Label("上传", systemImage: "plus")
            }
            .buttonStyle(.borderedProminent)
        }
        .padding()
    }
}
```

**2. 文档卡片**
```swift
struct DocumentCard: View {
    let document: Document
    let onTap: () -> Void
    
    var body: some View {
        Button(action: onTap) {
            VStack(alignment: .leading, spacing: 8) {
                // 缩略图
                AsyncImage(url: document.thumbnailURL) { image in
                    image.resizable()
                        .aspectRatio(contentMode: .fill)
                } placeholder: {
                    Rectangle()
                        .fill(Color.gray.opacity(0.2))
                        .overlay(
                            Image(systemName: document.typeIcon)
                                .font(.largeTitle)
                                .foregroundColor(.gray)
                        )
                }
                .frame(height: 120)
                .clipped()
                .cornerRadius(8)
                
                // 文档信息
                VStack(alignment: .leading, spacing: 4) {
                    Text(document.name)
                        .font(.body)
                        .lineLimit(2)
                    
                    HStack {
                        Text(document.type.name)
                        Text("·")
                        Text(document.fileSizeFormatted)
                    }
                    .font(.caption)
                    .foregroundColor(.secondary)
                    
                    // 状态标签
                    StatusBadge(status: document.processingStatus)
                }
                .padding(.horizontal, 8)
                .padding(.bottom, 8)
            }
        }
        .buttonStyle(.plain)
        .background(Color.white)
        .cornerRadius(12)
        .shadow(radius: 2)
    }
}
```

**3. 文档列表行**
```swift
struct DocumentListRow: View {
    let document: Document
    
    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: document.typeIcon)
                .font(.title2)
            
            VStack(alignment: .leading, spacing: 4) {
                Text(document.name)
                    .font(.body)
                Text(document.uploadedAt.formatted())
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            Spacer()
            
            Text(document.fileSizeFormatted)
                .font(.caption)
                .foregroundColor(.secondary)
            
            StatusBadge(status: document.processingStatus)
            
            Button(action: {}) {
                Image(systemName: "ellipsis")
            }
            .buttonStyle(.plain)
        }
        .padding(.vertical, 8)
    }
}
```

#### 数据源
- GET `/api/v1/documents/projects/{project_id}/documents/` - 文档列表
- GET `/api/v1/documents/{document_id}` - 文档详情
- DELETE `/api/v1/documents/{document_id}/` - 删除文档

---

### 5. ChatView - 对话界面

#### 功能定位
AI 对话、文档问答、知识检索

#### 页面结构
```
┌─────────────────────────────────────────────────────────────┐
│  AI 对话 - 会话名称                             [新会话] [×] │
├──────┬──────────────────────────────────────────────────────┤
│ 会话 │  ┌──────────────────────────────────────────────┐  │
│ 历史 │  │  你好，我是 FieldMind AI 助手                │  │
│      │  │  有什么可以帮助你的？                         │  │
│ [可  │  └──────────────────────────────────────────────┘  │
│  折  │                                                      │
│  叠] │  ┌──────────────────────────────────────────────┐  │
│      │  │  这个项目的主要内容是什么？           [用户]  │  │
│ 📝会1│  └──────────────────────────────────────────────┘  │
│ 📝会2│                                                      │
│ 📝会3│  ┌──────────────────────────────────────────────┐  │
│      │  │  根据分析，这个项目主要关注...       [AI]    │  │
│      │  │                                               │  │
│      │  │  相关文档:                                    │  │
│      │  │  • 文档1.pdf (相关度 95%)                    │  │
│      │  │  • 文档2.docx (相关度 88%)                   │  │
│      │  └──────────────────────────────────────────────┘  │
│      │                                                      │
├──────┴──────────────────────────────────────────────────────┤
│  [输入框]                             [附件] [发送]          │
└─────────────────────────────────────────────────────────────┘
```

#### 核心组件

**1. 消息气泡**
```swift
struct MessageBubble: View {
    let message: Message
    
    var body: some View {
        HStack {
            if message.isUser { Spacer() }
            
            VStack(alignment: message.isUser ? .trailing : .leading, spacing: 8) {
                Text(message.content)
                    .padding(12)
                    .background(message.isUser ? Color.blue : Color.gray.opacity(0.1))
                    .foregroundColor(message.isUser ? .white : .primary)
                    .cornerRadius(12)
                
                // 相关文档（仅 AI 消息）
                if !message.isUser && !message.relatedDocuments.isEmpty {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("相关文档:")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        
                        ForEach(message.relatedDocuments) { doc in
                            HStack {
                                Image(systemName: "doc.text")
                                Text(doc.name)
                                Spacer()
                                Text("\(Int(doc.relevance * 100))%")
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }
                            .font(.caption)
                            .padding(8)
                            .background(Color.blue.opacity(0.05))
                            .cornerRadius(6)
                        }
                    }
                }
                
                Text(message.timestamp.formatted())
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }
            .frame(maxWidth: 500, alignment: message.isUser ? .trailing : .leading)
            
            if !message.isUser { Spacer() }
        }
    }
}
```

**2. 会话历史侧边栏**
```swift
struct ChatHistorySidebar: View {
    let sessions: [ChatSession]
    @Binding var selectedSession: ChatSession?
    let onNewSession: () -> Void
    
    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            Button(action: onNewSession) {
                HStack {
                    Image(systemName: "plus")
                    Text("新会话")
                }
                .frame(maxWidth: .infinity)
            }
            .buttonStyle(.borderedProminent)
            .padding()
            
            List(sessions, selection: $selectedSession) { session in
                ChatSessionRow(session: session)
            }
            .listStyle(.sidebar)
        }
    }
}

struct ChatSessionRow: View {
    let session: ChatSession
    
    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(session.title)
                .font(.body)
                .lineLimit(1)
            Text(session.lastMessage)
                .font(.caption)
                .foregroundColor(.secondary)
                .lineLimit(2)
            Text(session.updatedAt.formatted())
                .font(.caption2)
                .foregroundColor(.secondary)
        }
        .padding(.vertical, 4)
    }
}
```

**3. 输入栏**
```swift
struct ChatInputBar: View {
    @Binding var text: String
    let onSend: () -> Void
    @State private var isAttaching = false
    
    var body: some View {
        HStack(spacing: 12) {
            Button(action: { isAttaching.toggle() }) {
                Image(systemName: "paperclip")
            }
            .buttonStyle(.plain)
            
            TextField("输入消息...", text: $text, axis: .vertical)
                .textFieldStyle(.plain)
                .lineLimit(1...5)
                .padding(8)
                .background(Color.gray.opacity(0.1))
                .cornerRadius(8)
                .onSubmit {
                    if !text.isEmpty {
                        onSend()
                    }
                }
            
            Button(action: onSend) {
                Image(systemName: "paperplane.fill")
            }
            .buttonStyle(.borderedProminent)
            .disabled(text.isEmpty)
        }
        .padding()
    }
}
```

#### 数据源
- POST `/api/v1/chat/sessions` - 创建会话
- GET `/api/v1/chat/sessions/{session_id}/messages/` - 消息历史
- POST `/api/v1/chat/sessions/{session_id}/messages` - 发送消息
- GET `/api/v1/chat/projects/{project_id}/sessions/` - 会话列表

---

## 通用组件库

### 1. 设计系统基础

#### Colors.swift
```swift
enum ColorSystem {
    // 主色调
    static let primary = Color(hex: "#2D3748")
    static let secondary = Color(hex: "#4A5568")
    static let accent = Color(hex: "#38B2AC")
    
    // 中性色（灰度）
    static let gray50 = Color(hex: "#F7FAFC")
    static let gray100 = Color(hex: "#EDF2F7")
    static let gray200 = Color(hex: "#E2E8F0")
    static let gray300 = Color(hex: "#CBD5E0")
    static let gray400 = Color(hex: "#A0AEC0")
    static let gray500 = Color(hex: "#718096")
    static let gray600 = Color(hex: "#4A5568")
    static let gray700 = Color(hex: "#2D3748")
    static let gray800 = Color(hex: "#1A202C")
    static let gray900 = Color(hex: "#171923")
    
    // 语义色
    static let success = Color(hex: "#48BB78")
    static let warning = Color(hex: "#ECC94B")
    static let error = Color(hex: "#F56565")
    static let info = Color(hex: "#4299E1")
    
    // 背景色
    static let bgPrimary = Color.white
    static let bgSecondary = gray50
    static let bgTertiary = gray100
}
```

#### Spacing.swift
```swift
enum Spacing {
    static let xs: CGFloat = 4
    static let sm: CGFloat = 8
    static let md: CGFloat = 16
    static let lg: CGFloat = 24
    static let xl: CGFloat = 32
    static let xxl: CGFloat = 48
}
```

#### Typography.swift
```swift
enum Typography {
    static let h1 = Font.system(size: 32, weight: .bold)
    static let h2 = Font.system(size: 24, weight: .semibold)
    static let h3 = Font.system(size: 20, weight: .semibold)
    static let h4 = Font.system(size: 18, weight: .semibold)
    static let body = Font.system(size: 16, weight: .regular)
    static let bodyBold = Font.system(size: 16, weight: .semibold)
    static let caption = Font.system(size: 14, weight: .regular)
    static let small = Font.system(size: 12, weight: .regular)
    static let tiny = Font.system(size: 10, weight: .regular)
}
```

### 2. 通用组件

#### CardView
```swift
struct CardView<Content: View>: View {
    let content: Content
    var padding: CGFloat = Spacing.md
    var hasShadow: Bool = true
    
    init(
        padding: CGFloat = Spacing.md,
        hasShadow: Bool = true,
        @ViewBuilder content: () -> Content
    ) {
        self.padding = padding
        self.hasShadow = hasShadow
        self.content = content()
    }
    
    var body: some View {
        content
            .padding(padding)
            .background(ColorSystem.bgPrimary)
            .cornerRadius(12)
            .shadow(
                color: hasShadow ? .black.opacity(0.05) : .clear,
                radius: 8,
                y: 2
            )
    }
}
```

#### SearchField
```swift
struct SearchField: View {
    @Binding var text: String
    let placeholder: String
    
    var body: some View {
        HStack {
            Image(systemName: "magnifyingglass")
                .foregroundColor(.secondary)
            
            TextField(placeholder, text: $text)
                .textFieldStyle(.plain)
            
            if !text.isEmpty {
                Button(action: { text = "" }) {
                    Image(systemName: "xmark.circle.fill")
                        .foregroundColor(.secondary)
                }
                .buttonStyle(.plain)
            }
        }
        .padding(Spacing.sm)
        .background(ColorSystem.bgSecondary)
        .cornerRadius(8)
    }
}
```

#### StatusBadge
```swift
struct StatusBadge: View {
    let status: ProcessingStatus
    
    var body: some View {
        Text(status.displayName)
            .font(.caption)
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(status.color.opacity(0.1))
            .foregroundColor(status.color)
            .cornerRadius(4)
    }
}

enum ProcessingStatus: String {
    case pending = "等待中"
    case processing = "处理中"
    case completed = "已完成"
    case failed = "失败"
    
    var color: Color {
        switch self {
        case .pending: return .orange
        case .processing: return .blue
        case .completed: return .green
        case .failed: return .red
        }
    }
}
```

---

## 实施时间表

| 页面 | 预计时间 | 优先级 |
|------|---------|--------|
| DashboardView | 3 小时 | P0 |
| DocumentListView | 2.5 小时 | P0 |
| DocumentUploadView | 2 小时 | P0 |
| ChatView | 3.5 小时 | P1 |
| ProjectDetailView | 3 小时 | P1 |
| **总计** | **14 小时** | |

---

## 下一步行动

1. 创建设计系统基础文件（Colors, Spacing, Typography）
2. 实现通用组件库（CardView, SearchField, StatusBadge）
3. 按优先级创建 5 个页面
4. 集成 ViewModel 和数据绑定
5. 测试和优化
