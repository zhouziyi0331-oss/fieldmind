# FieldMind 完整工作流设计与修复方案

## 核心问题分析

### 1. 当前问题
- ❌ 功能模块孤立，缺乏连贯的使用流程
- ❌ 页面间没有数据流转和状态同步
- ❌ 用户操作后缺乏实时反馈
- ❌ 侧边栏项目切换后，各页面数据不刷新
- ❌ 上传文档后没有任务进度显示
- ❌ 分析结果无法保存和查看历史记录
- ❌ 缺乏系统性的工作流引导

### 2. 设计目标
- ✅ 建立清晰的用户工作流：创建项目 → 上传文档 → 分析 → 生成报告
- ✅ 页面间实时数据同步
- ✅ 侧边栏显示当前项目的实时状态
- ✅ 所有操作都有明确的反馈和结果展示
- ✅ 支持任务队列和进度追踪

---

## 完整工作流设计

### 阶段1: 项目初始化
```
用户登录 
  → 看到项目列表页面
  → 创建新项目（填写名称、描述、研究目标）
  → 自动切换到该项目
  → 侧边栏显示项目名称
  → Dashboard显示项目概览（0个文档、0个分析）
```

### 阶段2: 数据导入
```
进入"材料导入"页面
  → 上传文档（支持批量）
  → 实时显示上传进度
  → 文档自动进入处理队列
  → 侧边栏显示"处理中"任务数量
  → 处理完成后弹出通知
  → 文档列表实时更新
```

### 阶段3: 数据分析
```
方式1: 从文档列表进入
  → 选中文档
  → 点击"分析"按钮
  → 选择分析类型（关键词/文创/业态）
  → 查看分析结果
  → 保存分析到项目

方式2: 从分析页面进入
  → 进入"关键词检索"页面
  → 输入关键词
  → 查看所有匹配结果（文档+时间戳）
  → 点击结果跳转到原文
```

### 阶段4: 结果查看
```
Dashboard概览
  → 显示所有已完成的分析
  → 显示Top关键词词云
  → 显示文档处理状态
  → 快速入口到各分析页面

侧边栏任务面板
  → 显示正在处理的任务
  → 显示任务进度
  → 点击查看任务详情
```

### 阶段5: 报告生成
```
进入"调研报告"页面
  → 选择要包含的分析结果
  → 选择报告模板
  → 生成报告预览
  → 导出为Word/PDF
```

---

## 需要修复的关键问题

### 问题1: 侧边栏项目切换无效
**现象**: 切换项目后，各页面显示的还是旧项目数据

**原因**: 
- ProjectDataManager没有正确响应项目切换
- 各View没有监听currentProject变化

**修复方案**:
1. 在AppState的currentProject didSet中触发全局通知
2. 所有View监听项目变化并重新加载数据
3. 添加loading状态，避免数据闪烁

### 问题2: 上传文档无反馈
**现象**: 上传后看不到进度，不知道是否成功

**修复方案**:
1. 添加上传进度条
2. 上传成功后显示Toast通知
3. 自动刷新文档列表
4. 如果开启后台处理，显示"处理中"状态

### 问题3: 分析结果无法持久化
**现象**: 分析完关闭页面，结果就丢失了

**修复方案**:
1. 后端添加分析结果存储表
2. 每次分析完成自动保存
3. Dashboard显示历史分析列表
4. 支持查看和对比历史分析

### 问题4: 侧边栏缺少任务状态
**现象**: 看不到后台任务的进度

**修复方案**:
1. 侧边栏底部添加"任务中心"图标
2. 显示进行中任务的数量badge
3. 点击展开任务面板
4. 实时更新任务进度

### 问题5: 页面间缺少跳转
**现象**: 分析结果无法跳转到原文档

**修复方案**:
1. 关键词检索结果添加"跳转"按钮
2. 点击后切换到文档页面并高亮关键词
3. 视频/音频结果支持跳转到指定时间点

---

## 数据流架构重构

### 全局状态管理 (AppState)
```swift
class AppState: ObservableObject {
    // 用户状态
    @Published var currentUser: User?
    @Published var isAuthenticated = false
    
    // 项目状态
    @Published var currentProject: Project? {
        didSet { onProjectChanged() }
    }
    @Published var projects: [Project] = []
    
    // 页面状态
    @Published var selectedPage: NavigationPage = .dashboard
    
    // 任务状态 (NEW)
    @Published var activeTasks: [BackgroundTask] = []
    @Published var taskNotifications: [TaskNotification] = []
    
    // 全局通知
    private var projectChangeSubject = PassthroughSubject<Project?, Never>()
    
    func onProjectChanged() {
        // 通知所有订阅者
        projectChangeSubject.send(currentProject)
        
        // 重置相关数据
        ProjectDataManager.shared.switchProject(to: currentProject)
        
        // 加载任务列表
        loadActiveTasks()
    }
}
```

### 项目数据管理器 (ProjectDataManager)
```swift
class ProjectDataManager: ObservableObject {
    static let shared = ProjectDataManager()
    
    // 当前项目数据
    @Published var documents: [Document] = []
    @Published var analyses: [Analysis] = []
    @Published var keywords: [KeywordData] = []
    
    // 加载状态
    @Published var isLoadingDocuments = false
    @Published var isLoadingAnalyses = false
    
    func switchProject(to project: Project?) {
        guard let project = project else {
            clearData()
            return
        }
        
        // 加载项目数据
        Task {
            await loadDocuments(projectId: project.id)
            await loadAnalyses(projectId: project.id)
            await loadKeywords(projectId: project.id)
        }
    }
}
```

### 任务管理器 (TaskManager - NEW)
```swift
class TaskManager: ObservableObject {
    static let shared = TaskManager()
    
    @Published var tasks: [BackgroundTask] = []
    
    struct BackgroundTask: Identifiable {
        let id: String
        let type: TaskType
        let projectId: Int
        let status: TaskStatus
        let progress: Double
        let createdAt: Date
        
        enum TaskType {
            case documentProcessing(documentId: Int)
            case keywordSearch(keyword: String)
            case creativeAnalysis
            case businessAnalysis
        }
        
        enum TaskStatus {
            case pending
            case processing
            case completed
            case failed(Error)
        }
    }
    
    func addTask(_ task: BackgroundTask) {
        tasks.append(task)
    }
    
    func updateTask(id: String, status: TaskStatus, progress: Double) {
        if let index = tasks.firstIndex(where: { $0.id == id }) {
            tasks[index].status = status
            tasks[index].progress = progress
        }
    }
}
```

---

## 具体修复步骤

### Step 1: 创建任务管理系统
- [ ] 后端添加任务状态追踪API
- [ ] 前端创建TaskManager单例
- [ ] 实现WebSocket实时更新

### Step 2: 修复项目切换逻辑
- [ ] AppState.currentProject触发全局通知
- [ ] 所有View监听项目变化
- [ ] 添加loading状态

### Step 3: 完善文档上传流程
- [ ] 添加上传进度显示
- [ ] 添加任务队列展示
- [ ] 完成后自动刷新列表

### Step 4: 添加分析结果持久化
- [ ] 后端创建分析结果表
- [ ] 保存所有分析记录
- [ ] Dashboard显示历史分析

### Step 5: 实现页面间跳转
- [ ] 分析结果添加"查看详情"按钮
- [ ] 支持跨页面导航和参数传递
- [ ] 高亮显示目标内容

### Step 6: 完善侧边栏
- [ ] 添加任务中心入口
- [ ] 显示badge数量
- [ ] 任务面板弹窗

---

## 优先级排序

### P0 (立即修复)
1. 项目切换后数据刷新
2. 文档上传进度显示
3. 基础的错误处理和Toast提示

### P1 (高优先级)
4. 任务状态追踪
5. 分析结果持久化
6. Dashboard数据展示

### P2 (中优先级)
7. 页面间跳转
8. 侧边栏任务中心
9. WebSocket实时通知

### P3 (低优先级)
10. 报告生成和导出
11. 高级搜索和过滤
12. 数据可视化图表

---

**下一步行动**: 从P0开始，逐个实现并测试

