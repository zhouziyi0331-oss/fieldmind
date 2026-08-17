# FieldMind 前后端对接分析报告

## 一、问题概述

**核心问题**: 前端页面中存在大量硬编码的模拟数据（demoList），这些数据应该从后端API动态获取，而不是写死在前端代码中。

**影响范围**: 46个Swift页面文件中发现1761处硬编码中文文本，其中大部分应该是从后端数据库查询的动态数据。

---

## 二、后端API端点清单

### 2.1 已实现的后端API

#### 业态分析 (Business Analysis)
- `POST /projects/{project_id}/analyze` - 分析业态
- `GET /projects/{project_id}/formats/existing` - 获取现有业态
- `GET /projects/{project_id}/synergy` - 业态协同分析

#### 聚合分析 (Aggregate)
- `GET /projects/{project_id}/topic-distribution` - 主题分布
- `GET /projects/{project_id}/top-entities` - 顶级实体
- `GET /projects/{project_id}/word-count-stats` - 词频统计
- `GET /projects/{project_id}/timeline-distribution` - 时间线分布
- `POST /projects/{project_id}/generate-report` - 生成报告

#### 仪表盘 (Dashboard)
- `GET /dashboard/{project_id}` - 项目仪表盘
- `GET /quick-stats/{project_id}` - 快速统计

#### 批处理 (Batch Processing)
- `POST /process` - 批处理文档
- `GET /status` - 处理状态
- `POST /reprocess-failed` - 重新处理失败项
- `POST /process-project` - 处理项目

#### 对话/聊天 (Chat)
- `POST /query` - 聊天查询
- `GET /available-documents/{project_id}` - 可用文档
- `POST /projects/{project_id}/ask` - 项目问答
- `GET /projects/{project_id}/context` - 项目上下文
- `GET /projects/{project_id}/conversations` - 对话列表

#### 文档处理 (Document Processing)
- `GET /documents/{document_id}/status` - 文档状态
- `POST /documents/{document_id}/reprocess` - 重新处理
- `GET /documents/{document_id}/chunks/preview` - 分块预览
- `GET /projects/{project_id}/chunks/statistics` - 分块统计
- `POST /projects/{project_id}/semantic-search` - 语义搜索

#### 知识图谱 (Knowledge Graph)
- `GET /objects/{fid}/lineage` - 对象谱系
- `GET /objects/{fid}` - 对象详情
- `GET /projects/{project_id}/objects` - 项目对象列表
- `POST /relations/discover` - 发现关系
- `POST /projects/{project_id}/relations/discover-all` - 发现所有关系
- `GET /objects/{fid}/relations` - 对象关系
- `GET /objects/{fid}/recommend` - 推荐
- `GET /projects/{project_id}/hot-connections` - 热门连接

#### 时间线 (Timeline)
- `POST /documents/{document_id}/align-timestamps` - 对齐时间戳
- `GET /documents/{document_id}/content-at-time` - 指定时间内容
- `GET /entities/{entity_name}/timeline` - 实体时间线
- `GET /entities/{entity_name}/profile` - 实体画像
- `GET /events/{event_summary}/profile` - 事件画像
- `GET /documents/{document_id}/timestamp-validation` - 时间戳验证

#### 创意分析 (Creative Analysis)
- `POST /projects/{project_id}/analyze` - 创意分析
- `GET /projects/{project_id}/cultural-elements` - 文化元素

#### 会话管理 (Chat Sessions)
- `POST /sessions` - 创建会话
- `GET /sessions/{session_id}` - 获取会话
- `GET /projects/{project_id}/sessions` - 项目会话列表
- `POST /sessions/{session_id}/messages` - 发送消息
- `GET /sessions/{session_id}/messages` - 获取消息
- `DELETE /sessions/{session_id}` - 删除会话
- `POST /sessions/{session_id}/evolve-skill` - 技能进化

#### 搜索与引用
- `POST /search-with-citation` - 带引用搜索

---

## 三、前端页面 vs 后端API 对接情况

### 3.1 完全缺失API对接的页面

| 页面 | 硬编码数据 | 应对接的后端API | 状态 |
|------|-----------|---------------|------|
| **AgentMemoryPage.swift** | 36处硬编码 | `/api/memory/*` 相关接口 | ❌ 需要实现 |
| **AdvancedSearchPage.swift** | 55处硬编码 | `/projects/{id}/semantic-search` | ⚠️ API存在但未对接 |
| **ChroniclePage.swift** | 55处硬编码 | `/entities/{name}/timeline`, `/events/{summary}/profile` | ⚠️ API存在但未对接 |
| **CitationsPage.swift** | 127处硬编码 | `/search-with-citation` | ⚠️ API存在但未对接 |
| **ConversationsPage.swift** | 55处硬编码 | `/projects/{id}/conversations`, `/sessions/*` | ⚠️ API存在但未对接 |
| **DashboardPage.swift** | 51处硬编码 | `/dashboard/{project_id}`, `/quick-stats/{project_id}` | ⚠️ API存在但未对接 |
| **GraphExplorerPage.swift** | 58处硬编码 | `/projects/{id}/objects`, `/objects/{fid}/relations` | ⚠️ API存在但未对接 |
| **KeywordPage.swift** | 31处硬编码 | `/projects/{id}/top-entities` | ⚠️ API存在但未对接 |
| **ModelPage.swift** | 42处硬编码 | 需要新增模型管理API | ❌ 需要实现 |
| **PhotosPage.swift** | 41处硬编码 | 需要新增照片管理API | ❌ 需要实现 |
| **QualityMonitorPage.swift** | 58处硬编码 | `/api/monitoring/*` | ⚠️ API可能存在但未对接 |
| **Report3Page.swift** | 14处硬编码 | `/projects/{id}/generate-report` | ⚠️ API存在但未对接 |
| **ReportPage.swift** | 25处硬编码 | `/projects/{id}/generate-report` | ⚠️ API存在但未对接 |
| **SOPPage.swift** | 26处硬编码 | 需要新增SOP管理API | ❌ 需要实现 |
| **SOPAnalysisPage.swift** | 22处硬编码 | 需要新增SOP分析API | ❌ 需要实现 |
| **SkillPage.swift** | 28处硬编码 | `/api/skill_config/*` | ⚠️ API可能存在但未对接 |
| **TablesPage.swift** | 84处硬编码 | 需要新增表格数据API | ❌ 需要实现 |
| **TimelinePage.swift** | 49处硬编码 | `/entities/{name}/timeline`, `/documents/{id}/content-at-time` | ⚠️ API存在但未对接 |
| **UploadPage.swift** | 55处硬编码 | `/process`, `/status` | ⚠️ API存在但未对接 |
| **VeinPage.swift** | 33处硬编码 | `/projects/{id}/hot-connections`, `/objects/{fid}/relations` | ⚠️ API存在但未对接 |
| **WorkflowPage.swift** | 23处硬编码 | 需要新增Workflow API | ❌ 需要实现 |
| **BusiPage.swift** | 5处硬编码 | `/projects/{id}/analyze`, `/projects/{id}/formats/existing` | ⚠️ API存在但未对接 |

### 3.2 问题分类

#### ✅ 后端API已存在，仅需前端对接（优先级：高）
1. **DashboardPage** → `/dashboard/{project_id}`, `/quick-stats/{project_id}`
2. **BusiPage** → `/projects/{id}/analyze`, `/projects/{id}/formats/existing`
3. **AdvancedSearchPage** → `/projects/{id}/semantic-search`
4. **GraphExplorerPage** → `/projects/{id}/objects`, `/objects/{fid}/relations`
5. **TimelinePage** → `/entities/{name}/timeline`, `/documents/{id}/content-at-time`
6. **ChroniclePage** → `/entities/{name}/timeline`, `/events/{summary}/profile`
7. **ConversationsPage** → `/projects/{id}/conversations`, `/sessions/*`
8. **CitationsPage** → `/search-with-citation`
9. **KeywordPage** → `/projects/{id}/top-entities`
10. **ReportPage** → `/projects/{id}/generate-report`
11. **UploadPage** → `/process`, `/status`

#### ❌ 后端API缺失，需要实现（优先级：中）
1. **AgentMemoryPage** - 需要实现 Agent Memory 相关API
2. **ModelPage** - 需要实现模型管理API
3. **PhotosPage** - 需要实现照片/图片管理API
4. **SOPPage** - 需要实现SOP（标准操作流程）管理API
5. **SOPAnalysisPage** - 需要实现SOP分析API
6. **TablesPage** - 需要实现表格数据管理API
7. **WorkflowPage** - 需要实现工作流管理API

#### ⚠️ 需要确认后端API状态（优先级：中低）
1. **QualityMonitorPage** - 检查 `/api/monitoring/*` 是否存在
2. **SkillPage** - 检查 `/api/skill_config/*` 实现情况

---

## 四、前端架构缺失

### 4.1 缺少网络层
前端代码中**完全没有发现**以下关键组件：
- ❌ `APIClient` 或 `NetworkManager`
- ❌ HTTP 请求封装（URLSession / Alamofire）
- ❌ API Service 层
- ❌ 数据模型与后端JSON的映射

### 4.2 当前项目结构
```
Sources/
├── App/              # 应用入口
├── Components/       # UI组件
├── Config/          # 配置
├── Core/            # AppState
├── DesignSystem/    # 设计系统
├── Models/          # 数据模型（但都是硬编码demo数据）
├── Pages/           # 页面（所有页面都用demoList）
└── Views/           # 视图组件
```

**缺失的目录**：
- ❌ `Services/` - API服务层
- ❌ `Network/` - 网络请求层
- ❌ `Repositories/` - 数据仓库层

---

## 五、具体硬编码数据示例

### 5.1 BusiPage 示例
```swift
// 当前代码（硬编码）
ForEach(BusinessAnalysis.demoList) { analysis in
    BusiListItem(analysis: analysis, isSelected: selectedAnalysis?.id == analysis.id)
}

// 应该改为（从API获取）
@State private var analyses: [BusinessAnalysis] = []

Task {
    analyses = try await APIService.shared.fetchBusinessAnalyses(projectId: currentProjectId)
}
```

### 5.2 DashboardPage 示例
```swift
// 当前（硬编码）
Text("总材料数")
Text("47") // 硬编码数字

// 应该改为
@State private var dashboardData: DashboardData?

Task {
    dashboardData = try await APIService.shared.fetchDashboard(projectId: currentProjectId)
}
Text("\(dashboardData?.materialsCount ?? 0)")
```

---

## 六、修复计划

### Phase 1: 搭建网络层基础设施（1-2天）
1. ✅ 创建 `Sources/Network/APIClient.swift`
2. ✅ 创建 `Sources/Network/APIEndpoint.swift`
3. ✅ 创建 `Sources/Network/NetworkError.swift`
4. ✅ 创建 `Sources/Services/` 目录，每个功能模块一个Service

### Phase 2: 优先对接已有API的页面（3-5天）
**第一批（核心功能）**:
1. DashboardPage → DashboardService
2. BusiPage → BusinessAnalysisService
3. ConversationsPage → ChatService
4. UploadPage → DocumentService

**第二批（数据展示）**:
5. TimelinePage → TimelineService
6. GraphExplorerPage → KnowledgeGraphService
7. KeywordPage → KeywordService
8. AdvancedSearchPage → SearchService

**第三批（辅助功能）**:
9. ReportPage → ReportService
10. CitationsPage → CitationService
11. ChroniclePage → ChronicleService

### Phase 3: 实现缺失的后端API（5-7天）
1. Agent Memory API
2. Model Management API
3. Photo/Media Management API
4. SOP Management API
5. Table Data API
6. Workflow API

### Phase 4: 全面测试与Bug修复（2-3天）
1. 集成测试所有API对接
2. 错误处理与加载状态
3. 数据同步与刷新逻辑
4. 性能优化

---

## 七、代码规范建议

### 7.1 网络层设计
```swift
// APIClient.swift
class APIClient {
    static let shared = APIClient()
    private let baseURL = "http://localhost:8000/api"
    
    func request<T: Decodable>(
        _ endpoint: APIEndpoint,
        method: HTTPMethod = .get,
        body: Encodable? = nil
    ) async throws -> T {
        // 实现HTTP请求
    }
}

// APIEndpoint.swift
enum APIEndpoint {
    case dashboard(projectId: String)
    case businessAnalysis(projectId: String)
    case conversations(projectId: String)
    // ...
    
    var path: String {
        switch self {
        case .dashboard(let id): return "/dashboard/\(id)"
        case .businessAnalysis(let id): return "/projects/\(id)/analyze"
        // ...
        }
    }
}
```

### 7.2 Service层设计
```swift
// BusinessAnalysisService.swift
class BusinessAnalysisService {
    private let apiClient = APIClient.shared
    
    func fetchAnalyses(projectId: String) async throws -> [BusinessAnalysis] {
        return try await apiClient.request(.businessAnalysis(projectId: projectId))
    }
    
    func analyzeFormats(projectId: String) async throws -> BusinessAnalysisResponse {
        return try await apiClient.request(
            .businessAnalysis(projectId: projectId),
            method: .post
        )
    }
}
```

### 7.3 页面使用Service
```swift
// BusiPage.swift
struct BusiPage: View {
    @State private var analyses: [BusinessAnalysis] = []
    @State private var isLoading = false
    @State private var error: Error?
    
    private let service = BusinessAnalysisService()
    
    var body: some View {
        // UI代码
    }
    
    func loadData() async {
        isLoading = true
        defer { isLoading = false }
        
        do {
            analyses = try await service.fetchAnalyses(projectId: currentProjectId)
        } catch {
            self.error = error
        }
    }
}
```

---

## 八、立即行动项

### 🔥 紧急（今天完成）
1. 创建网络层基础架构（APIClient, APIEndpoint, NetworkError）
2. 创建Services目录结构
3. 实现DashboardService并对接DashboardPage

### ⚡ 高优先级（本周完成）
1. 对接BusinessAnalysisService → BusiPage
2. 对接ChatService → ConversationsPage, ChatPage
3. 对接DocumentService → UploadPage
4. 对接TimelineService → TimelinePage
5. 对接KnowledgeGraphService → GraphExplorerPage

### 📋 中优先级（下周完成）
1. 实现缺失的后端API
2. 对接剩余页面
3. 统一错误处理和加载状态

---

## 九、预估工作量

| 任务 | 工作量 | 优先级 |
|------|--------|--------|
| 网络层基础设施 | 1-2天 | P0 |
| 核心页面对接（4个） | 2-3天 | P0 |
| 数据页面对接（7个） | 3-4天 | P1 |
| 后端API实现 | 5-7天 | P1 |
| 测试与修复 | 2-3天 | P1 |
| **总计** | **13-19天** | - |

---

## 十、注意事项

1. **数据结构对齐**: 前端Model需要与后端API返回的JSON结构完全对齐
2. **错误处理**: 所有API调用必须有完善的错误处理和用户提示
3. **加载状态**: 需要显示加载动画，避免用户等待时的空白页面
4. **数据刷新**: 实现下拉刷新和自动刷新机制
5. **缓存策略**: 考虑对不常变化的数据进行本地缓存
6. **认证授权**: 需要实现用户登录和JWT token管理
7. **环境配置**: API地址应该可配置（开发/测试/生产环境）

---

## 十一、后续优化方向

1. 实现离线模式和本地数据持久化
2. 添加实时数据推送（WebSocket）
3. 优化大数据量的分页加载
4. 实现数据预加载和智能缓存
5. 添加性能监控和错误追踪

