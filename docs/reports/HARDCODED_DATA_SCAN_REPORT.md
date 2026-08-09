# FieldMind 硬编码假数据扫描报告

## 📊 扫描概览

**扫描时间**: 2024-08-07  
**扫描范围**: FieldMind-Rebuild (Mac桌面应用 + Web前端)  
**发现问题**: 大量硬编码假数据、固定动画、静态UI

---

## 🔴 严重问题：硬编码假数据列表

### 1️⃣ WorkflowsView.swift (Line 462-594)

**文件位置**: `FieldMind-Rebuild/fieldmind-desktop/Sources/FieldMind/Views/WorkflowsView.swift`

**问题**: `loadWorkflows()` 函数使用 `DispatchQueue.main.asyncAfter` 模拟延迟，返回3个完全硬编码的假工作流

**假数据内容**:
```swift
// Line 462-594: 硬编码的3个假工作流
workflows = [
    Workflow(
        id: "1",
        name: "田野调查完整流程",
        description: "从文档导入、信息提取、知识图谱构建到报告生成的完整流程",
        stepCount: 6,
        usageCount: 15,  // ❌ 假数据
        avgDuration: "25分钟",  // ❌ 假数据
        steps: [...],  // ❌ 6个硬编码步骤
        executionHistory: [
            WorkflowExecution(
                id: "1",
                executedAt: "2024-03-20 14:30",  // ❌ 假时间
                duration: "23分钟",
                projectName: "贵州布依族村落"  // ❌ 假项目名
            )
        ]
    ),
    // ... 另外2个假工作流
]
```

**应该做什么**: 调用真实API `GET /api/v1/workflows/`

---

### 2️⃣ ReportsView.swift (Line 375-378)

**文件位置**: `FieldMind-Rebuild/fieldmind-desktop/Sources/FieldMind/Views/ReportsView.swift`

**问题**: SKILL配置使用硬编码的假框架名称

**假数据内容**:
```swift
// Line 375-378: 硬编码的假SKILL列表
let availableSkills = [
    "乡土中国",           // ❌ 假框架
    "项链·消逝的满族",     // ❌ 假框架
    "景军·神圣记忆",       // ❌ 假框架
    "多村落 SOP",          // ❌ 假框架
    "商业可行性分析",      // ❌ 假框架
    "文献市场研究"         // ❌ 假框架
]
```

**应该做什么**: 调用真实API `GET /api/v1/skills/` 动态获取

---

### 3️⃣ IndustryAnalysisView.swift (Line 212-249)

**文件位置**: `FieldMind-Rebuild/fieldmind-desktop/Sources/FieldMind/Views/IndustryAnalysisView.swift`

**问题**: `loadAnalyses()` 返回2个完全硬编码的假业态分析

**假数据内容**:
```swift
// Line 212-249: 硬编码的假业态分析
analyses = [
    IndustryAnalysis(
        id: "1",
        title: "贵州布依族文化旅游产业分析",  // ❌ 假标题
        industryType: "文化旅游",
        region: "贵州",
        status: "已完成",
        createdAt: "2024-03-20",  // ❌ 假时间
        marketSize: "120亿元",     // ❌ 假数据
        growthRate: "15.5%",       // ❌ 假数据
        opportunities: [
            "民族文化资源丰富，差异化明显",  // ❌ 假文本
            "乡村振兴政策支持",
            "都市人群对深度体验需求增长"
        ],
        threats: [
            "同质化竞争加剧",  // ❌ 假文本
            "基础设施投入大",
            "文化传承人老龄化"
        ]
    )
]
```

**应该做什么**: 调用真实API `GET /api/v1/industry/`

---

### 4️⃣ IndustryAnalysisView.swift (Line 301-308)

**文件位置**: `FieldMind-Rebuild/fieldmind-desktop/Sources/FieldMind/Views/IndustryAnalysisView.swift`

**问题**: 行业类型和分析维度硬编码

**假数据内容**:
```swift
// Line 301-308: 硬编码的行业类型和分析维度
let availableIndustryTypes = [
    "文化旅游", "特色农业", "手工艺品",  // ❌ 固定列表
    "民宿经济", "文创产业", "生态农业"
]

let availableDimensions = [
    "市场规模", "竞争格局", "发展趋势", "机会识别",  // ❌ 固定列表
    "政策环境", "技术趋势", "消费者洞察"
]
```

**应该做什么**: 从配置文件或数据库动态加载

---

### 5️⃣ ProjectDetailPage.tsx (Line 52-95)

**文件位置**: `FieldMind-Rebuild/fieldmind-web/src/pages/ProjectDetailPage.tsx`

**问题**: 功能模块使用硬编码的图标和描述

**假数据内容**:
```typescript
// Line 52-95: 硬编码的模块列表
const modules = [
  {
    name: '材料库',
    icon: '📚',  // ❌ 固定emoji
    description: `${summary?.total_docs || 0} 个文档`,  // 部分动态
    path: `/projects/${projectId}/documents`,
    color: 'bg-blue-500',  // ❌ 固定颜色
  },
  {
    name: 'AI对话',
    icon: '💬',
    description: `${project?.chat_session_count || 0} 个会话`,
    path: `/projects/${projectId}/chat`,
    color: 'bg-green-500',
  },
  // ... 另外4个硬编码模块
]
```

**影响**: 图标、颜色无法自定义，固定不变

---

### 6️⃣ AgentMemoryView.swift - 假角色数据

**文件位置**: `FieldMind-Rebuild/fieldmind-desktop/Sources/FieldMind/Views/AgentMemoryView.swift`

**问题**: `loadAgentRoles()` 必定包含硬编码的假角色（推测，TODO标记存在）

**应该做什么**: 调用真实API `GET /api/v1/agent/roles`

---

## 🟡 中度问题：TODO标记未实现的API调用

### Swift文件中的TODO标记

| 文件 | 行号 | TODO内容 | 影响 |
|------|------|----------|------|
| WorkflowsView.swift | 460 | `// TODO: 调用后端API /api/v1/workflows/` | 工作流数据全是假的 |
| WorkflowsView.swift | 598 | `// TODO: 调用后端API POST /api/v1/workflows/` | 无法创建工作流 |
| WorkflowsView.swift | 604 | `// TODO: 调用后端API POST /api/v1/workflows/{id}/execute` | 无法执行工作流 |
| WorkflowsView.swift | 609 | `// TODO: 调用后端API DELETE /api/v1/workflows/{id}` | 删除工作流不生效 |
| IndustryAnalysisView.swift | 210 | `// TODO: 调用后端API /api/v1/industry/` | 业态分析数据全是假的 |
| IndustryAnalysisView.swift | 253 | `// TODO: 调用后端API /api/v1/industry/` | 无法创建分析 |
| IndustryAnalysisView.swift | 259 | `// TODO: 调用后端API DELETE /api/v1/industry/{id}` | 删除分析不生效 |

---

## 🟢 轻度问题：假动画和固定文本

### 1. 假延迟动画

**位置**: 所有 `DispatchQueue.main.asyncAfter(deadline: .now() + 0.5)`

```swift
// 假装在加载数据，实际只是延迟0.5秒显示假数据
DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
    workflows = [/* 假数据 */]
    isLoading = false
}
```

**影响**: 用户以为在加载真实数据，实际是假演示

---

### 2. 固定的Placeholder文本

**位置**: 
- `RegisterPage.tsx` Line 92-140
- `LoginPage.tsx` Line 56-71
- `ChatPage.tsx` Line 297-341

```typescript
placeholder="请输入用户名"
placeholder="your@email.com"
placeholder="至少6位"
placeholder="输入您的问题... (基于项目资料的深度AI对话)"
placeholder="例如：方言调研讨论"
```

**影响**: 小问题，但所有placeholder都是中文硬编码，无法国际化

---

## 📋 修复优先级

### 🔥 P0 - 立即修复（数据完全造假）

1. **WorkflowsView.swift**: 替换假数据为真实API调用
2. **IndustryAnalysisView.swift**: 替换假数据为真实API调用
3. **ReportsView.swift**: SKILL列表从API动态获取

### ⚡ P1 - 尽快修复（部分功能不可用）

4. **AgentMemoryView.swift**: 实现角色配置API
5. **所有删除/创建操作**: 连接到真实后端

### 💡 P2 - 优化体验（固定文本和配置）

6. **行业类型和分析维度**: 改为配置文件
7. **模块图标和颜色**: 支持自定义
8. **Placeholder文本**: 提取到i18n文件

---

## 🛠️ 修复方案建议

### 方案1: 逐个文件修复（推荐）

```swift
// 修复前 (WorkflowsView.swift Line 459-594)
private func loadWorkflows() {
    isLoading = true
    DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
        workflows = [/* 135行假数据 */]
        isLoading = false
    }
}

// 修复后
private func loadWorkflows() {
    isLoading = true
    Task {
        do {
            let response = try await APIService.shared.getWorkflows()
            await MainActor.run {
                workflows = response
                isLoading = false
            }
        } catch {
            print("❌ 加载工作流失败: \(error)")
            await MainActor.run {
                isLoading = false
                ToastManager.shared.error("加载失败")
            }
        }
    }
}
```

### 方案2: 创建统一的Mock标志

```swift
// Config.swift
struct AppConfig {
    static let USE_MOCK_DATA = false  // 开发时true，生产时false
}

// 使用
if AppConfig.USE_MOCK_DATA {
    // 返回假数据
} else {
    // 调用真实API
}
```

---

## 📊 统计总结

| 类型 | 数量 | 严重程度 |
|------|------|----------|
| 硬编码假数据对象 | 6处 | 🔴 严重 |
| TODO未实现API | 10+ | 🟡 中等 |
| 假延迟动画 | 3处 | 🟢 轻度 |
| 固定配置列表 | 5处 | 🟢 轻度 |
| 硬编码Placeholder | 10+ | 🟢 轻度 |

**总计**: 扫描发现 **30+** 处硬编码问题

---

## ✅ 验收标准

修复完成后，应满足：

1. ✅ 所有数据从后端API获取，无假数据
2. ✅ 所有TODO标记已实现或删除
3. ✅ 无 `DispatchQueue.main.asyncAfter` 假延迟
4. ✅ 配置项（行业类型、分析维度等）可动态配置
5. ✅ 用户可区分"真实数据"和"示例数据"

---

## 🎯 下一步行动

1. **确认后端API**: 检查 `/api/v1/workflows/`, `/api/v1/industry/`, `/api/v1/skills/` 是否已实现
2. **实现APIService方法**: 在 `APIService.swift` 中添加对应方法
3. **逐个替换**: 按优先级从P0开始修复
4. **添加加载状态**: 真实网络请求需要proper loading UI
5. **错误处理**: 网络失败时的友好提示

---

**报告生成时间**: 2024-08-07  
**扫描工具**: 人工审查 + grep搜索  
**建议修复时间**: 2-3天（P0优先）
