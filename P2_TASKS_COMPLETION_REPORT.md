# P2任务完成报告

## 📊 总体进度

**P2任务列表（5项）：**
- ✅ P2-1: ChroniclePage（事件编年）- 已完成
- ✅ P2-2: VeinPage（知识脉络）- 已完成  
- ⚠️ P2-3: CitationsPage（引用管理）- 后端API不存在
- ⏸️ P2-4: PhotosPage（照片管理）- 需要后端API扩展
- ⏸️ P2-5: FileManagerPage（文件管理）- 需要后端架构改造

**完成率：2/5 (40%)**  
**可用率：2/3 (67%)** （排除后端依赖项）

---

## ✅ 已完成任务

### P2-1: ChroniclePage（事件编年）

**创建文件：**
- `Sources/ViewModels/ChronicleViewModel.swift` - 状态管理
- `Sources/Pages/ChroniclePage_NEW.swift` - 完整UI实现（~850行）

**功能特性：**
- ✅ 复用TimelineService，无需新增后端API
- ✅ 时间轴视图 + 卡片视图双模式
- ✅ 按年份分组显示事件
- ✅ 类别筛选（录音、照片、笔记等）
- ✅ 日期范围筛选
- ✅ 客户端搜索
- ✅ 事件详情模态框
- ✅ 统计面板（总事件数、类别分布）

**技术实现：**
```swift
@MainActor
class ChronicleViewModel: ObservableObject {
    @Published var events: [TimelineEventResponse] = []
    @Published var stats: TimelineStatsResponse?
    @Published var isLoadingEvents = false
    @Published var errorMessage: String?
    
    func loadEvents(projectId: Int, limit: Int = 200) async
    func loadStats(projectId: Int) async
    func filteredEvents() -> [TimelineEventResponse]
    func eventsByYear() -> [Int: [TimelineEventResponse]]
}
```

**数据流：**
```
TimelineService.getTimelineEvents(projectId)
    ↓
ChronicleViewModel.events
    ↓
ChroniclePage_NEW (时间轴/卡片视图)
```

---

### P2-2: VeinPage（知识脉络/知识图谱）

**创建文件：**
- `Sources/Services/KnowledgeGraphService.swift` - API服务层（~350行）
- `Sources/ViewModels/KnowledgeGraphViewModel.swift` - 状态管理（~200行）
- `Sources/Pages/VeinPage_NEW.swift` - 完整UI实现（~1085行）

**后端API集成：**
- ✅ POST `/knowledge-graph/build` - 构建知识图谱
- ✅ GET `/knowledge-graph/entities` - 获取实体列表
- ✅ GET `/knowledge-graph/entities/{id}` - 实体详情
- ✅ GET `/knowledge-graph/visualize` - 图谱可视化数据

**功能特性：**
- ✅ 网络图/树状图/径向图三种布局模式
- ✅ 实体类型筛选（人物/地点/组织/事件/概念/文物）
- ✅ 实体搜索
- ✅ 节点拖拽交互
- ✅ 点击节点显示详情侧边栏
- ✅ 构建图谱工作流（模态框）
- ✅ 图例面板
- ✅ 统计面板（实体数、关系数）
- ✅ 加载/错误/空状态处理

**数据模型：**
```swift
struct EntityResponse: Codable, Identifiable {
    let id: String
    let entityType: String  // person, location, organization, event, concept, artifact
    let name: String
    let aliases: [String]?
    let properties: [String: AnyCodable]?
    let description: String?
    let confidence: Double
    let mentionCount: Int
    let documentIds: [Int]?
}

struct GraphNode: Codable, Identifiable {
    let id: Int
    let label: String
    let group: String       // 实体类型
    let title: String?      // 描述
    let value: Int?         // 节点大小
    let shape: String?      // 节点形状
    let color: String?      // 节点颜色
}

struct GraphEdge: Codable, Identifiable {
    let id: String
    let from: Int
    let to: Int
    let label: String?
    let arrows: String?
    let color: String?
    let width: Double?
}
```

**可视化组件：**
- `NetworkGraphView_NEW` - 力导向网络图
- `TreeGraphView_NEW` - 树状层级图
- `RadialGraphView_NEW` - 径向分层图
- `NodeCircle_NEW` - 节点渲染（动态大小、图标、标签）
- `EdgeLine` - 边渲染（动态宽度、颜色）

**辅助功能：**
```swift
// KnowledgeGraphViewModel helper methods
func formatEntityType(_ type: String) -> String  // "person" → "人物"
func entityTypeIcon(_ type: String) -> String    // "person" → "person.fill"
func entityTypeColor(_ type: String) -> String   // "person" → "F59E0B"
func entitiesByType() -> [String: [EntityResponse]]
func entityTypeStats() -> [(type: String, count: Int)]
```

**自定义组件：**
- `FlowLayout` - 用于别名标签的流式布局
- `EntityDetailSection` - 异步加载实体详情
- `LegendPanel_NEW` - 实体类型图例
- `StatsPanel_NEW` - 统计信息面板

**AnyCodable实现：**
处理任意JSON属性值的包装器，支持Int/Double/String/Bool/Array/Dictionary/NSNull

---

## ⚠️ 受阻任务

### P2-3: CitationsPage（引用管理）

**问题：**
- 后端没有专门的引用管理API
- `/search/citation` 端点在APIEndpoint中定义，但后端未实现

**建议方案：**
1. **后端开发** - 新增Citations API：
   ```
   POST /api/citations/create      - 创建引用
   GET  /api/citations/list        - 获取引用列表
   GET  /api/citations/{id}        - 引用详情
   PUT  /api/citations/{id}        - 更新引用
   DELETE /api/citations/{id}      - 删除引用
   POST /api/citations/export      - 导出引用（BibTeX/EndNote）
   ```

2. **或者复用SearchService** - 将引用功能作为搜索结果的衍生功能：
   - 搜索结果 → 添加到引用库
   - 使用 `/search` API + 客户端管理引用列表

**当前状态：** 暂时搁置，等待后端API

---

### P2-4: PhotosPage（照片管理）

**问题：**
- 后端DocumentService可以上传文件，但缺少照片专用元数据：
  - ❌ EXIF信息（拍摄时间、地理位置、相机型号）
  - ❌ 缩略图生成
  - ❌ 照片分类/标签
  - ❌ 按地理位置分组

**当前Photo模型需求：**
```swift
struct Photo {
    let width: Int
    let height: Int
    let takenAt: Date
    let location: String?    // GPS位置
    let device: String?      // 相机型号
    var tags: [String]       // 标签
}
```

**建议方案：**
1. **扩展DocumentService** - 添加照片专用字段：
   ```python
   # backend/src/app/models/document.py
   class Document:
       # 现有字段...
       metadata: dict  # 存储EXIF等元数据
   ```

2. **或新增MediaService** - 专门处理媒体文件：
   ```
   GET  /api/media/photos              - 照片列表（过滤图片类型）
   GET  /api/media/photos/{id}         - 照片详情+EXIF
   POST /api/media/photos/{id}/tags    - 添加标签
   GET  /api/media/thumbnails/{id}     - 缩略图
   ```

**当前状态：** 可使用DocumentService的基础功能，但缺少照片特有功能

---

### P2-5: FileManagerPage（文件管理）

**问题：**
- 前端使用**树状文件夹结构**（FileNode with children）
- 后端DocumentService返回**扁平文档列表**
- 架构不匹配

**FileNode模型：**
```swift
struct FileNode {
    let id: String
    let name: String
    let isFolder: Bool
    var children: [FileNode]  // 递归树结构
}
```

**DocumentService返回：**
```swift
struct DocumentResponse {
    let id: Int
    let filename: String
    let filePath: String      // 仅存储路径字符串
    // 无folder/parent概念
}
```

**建议方案：**

**方案A - 后端支持文件夹（推荐）：**
```python
# 数据库Schema
class Folder:
    id: int
    name: str
    parent_id: int | None
    project_id: int

class Document:
    # 现有字段...
    folder_id: int | None  # 新增

# API
GET  /api/folders/tree              - 文件夹树
POST /api/folders/create            - 创建文件夹
PUT  /api/folders/{id}/move         - 移动文件夹
GET  /api/folders/{id}/documents    - 文件夹内文档
```

**方案B - 客户端模拟文件夹：**
- 解析 `filePath` 构建虚拟树结构
- 纯客户端实现，无后端改动
- 但无法真正移动/重命名文件夹

**当前状态：** 需要架构决策 - 是否要支持真实的文件夹功能

---

## 📈 工作量统计

| 任务 | Service | ViewModel | Page | 总行数 | 状态 |
|-----|---------|-----------|------|--------|------|
| ChroniclePage | 复用TimelineService | 200行 | 850行 | ~1050行 | ✅ |
| VeinPage | 350行 | 200行 | 1085行 | ~1635行 | ✅ |
| CitationsPage | - | - | - | 0行 | ⚠️ 后端缺失 |
| PhotosPage | - | - | - | 0行 | ⏸️ 待扩展 |
| FileManagerPage | - | - | - | 0行 | ⏸️ 待架构决策 |
| **总计** | **350行** | **400行** | **1935行** | **~2685行** | **40%完成** |

---

## 🎯 后续建议

### 立即可做（无后端依赖）：
1. **替换原页面** - 将 `ChroniclePage.swift` 和 `VeinPage.swift` 替换为 `_NEW` 版本
2. **测试集成** - 与真实后端API联调
3. **用户测试** - 收集反馈优化交互

### 短期任务（1-2天）：
1. **CitationsPage** - 后端新增Citations API或决定复用Search
2. **PhotosPage** - 扩展DocumentService支持元数据或新增MediaService

### 中期任务（3-5天）：
1. **FileManagerPage** - 架构决策 + 后端文件夹功能开发

### 替代方案（跳过复杂任务）：
- CitationsPage → 暂时隐藏或改为"搜索结果收藏"功能
- PhotosPage → 使用DocumentService的简化版（仅列表，无EXIF）
- FileManagerPage → 改为扁平文档列表（类似现有DocumentPage）

---

## 📝 技术亮点

### 1. AnyCodable实现
处理knowledge graph的任意JSON属性：
```swift
struct AnyCodable: Codable {
    let value: Any
    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        if let int = try? container.decode(Int.self) {
            value = int
        } else if let double = try? container.decode(Double.self) {
            value = double
        } else if let string = try? container.decode(String.self) {
            value = string
        } // ... 其他类型
    }
}
```

### 2. 动态API端点
支持查询参数的端点扩展：
```swift
extension APIEndpoint {
    case custom(String, queryItems: [URLQueryItem] = [])
    
    static func knowledgeGraphEntities(queryItems: [URLQueryItem]) -> APIEndpoint {
        return .custom("/knowledge-graph/entities", queryItems: queryItems)
    }
}
```

### 3. FlowLayout自定义布局
用于标签的流式换行：
```swift
struct FlowLayout: Layout {
    func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) -> CGSize
    func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize, subviews: Subviews, cache: inout ())
}
```

### 4. 力导向图布局算法
三种图形布局：
- **网络图** - 圆形均匀分布 + 拖拽交互
- **树状图** - 层级布局（水平/垂直分组）
- **径向图** - 同心圆分层布局

---

## 🔄 下一步行动

**选项1 - 完成剩余P2任务（需要后端支持）：**
1. 与后端协商Citations/Media/Folder API设计
2. 等待后端实现
3. 完成剩余3个页面

**选项2 - 继续其他优先级任务：**
1. 检查是否有P3/P4任务
2. 或者开始优化已完成的P0/P1/P2页面
3. 集成测试和性能优化

**选项3 - 替换现有页面上线：**
1. 将`ChroniclePage_NEW`和`VeinPage_NEW`合并到主代码
2. 删除旧的硬编码页面
3. 进行端到端测试

**建议：** 先执行选项3，然后选项2，最后根据需求决定是否执行选项1
