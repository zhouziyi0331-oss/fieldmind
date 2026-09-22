import SwiftUI
import Combine

/// 全局应用状态管理
class AppState: ObservableObject {
    // MARK: - 导航状态
    @Published var currentPage: PageType = .overview
    @Published var isSidebarCollapsed: Bool = false

    // MARK: - 项目状态
    @Published var currentProject: Project? = nil
    @Published var projects: [Project] = []

    // MARK: - 用户状态
    @Published var user: User = User(
        name: "研究员",
        role: "田野工作者",
        avatar: "田"
    )

    // MARK: - 数据状态
    @Published var materials: [Material] = []
    @Published var keywords: [Keyword] = []
    @Published var conversations: [Conversation] = []

    // MARK: - UI状态
    @Published var showToast: Bool = false
    @Published var toastMessage: String = ""
    @Published var toastType: ToastType = .info

    // MARK: - 上传状态
    @Published var isUploading: Bool = false
    @Published var uploadProgress: Double = 0.0
    @Published var uploadingFileName: String = ""

    // MARK: - 数据刷新通知
    /// 当文档处理完成后触发，通知所有页面刷新数据
    @Published var lastDocumentUpdate: Date = Date()

    init() {
        loadDemoData()
        Task {
            await loadProjectsFromAPI()
        }
    }

    // MARK: - 通知数据更新
    @MainActor
    func notifyDocumentUpdated() {
        lastDocumentUpdate = Date()
        DebugLogger.shared.log("📢 通知所有页面刷新数据", type: .info)
    }

    // MARK: - 页面导航
    func navigateTo(_ page: PageType) {
        withAnimation(.easeInOut(duration: 0.25)) {
            currentPage = page
        }
    }

    // MARK: - Toast 通知
    func showToast(message: String, type: ToastType = .info) {
        toastMessage = message
        toastType = type
        withAnimation {
            showToast = true
        }

        DispatchQueue.main.asyncAfter(deadline: .now() + 3) {
            withAnimation {
                self.showToast = false
            }
        }
    }

    // MARK: - 项目切换
    func switchProject(_ project: Project) {
        withAnimation {
            currentProject = project
        }
        // 触发数据重新加载
        loadProjectData(project)
    }

    // MARK: - 数据加载
    private func loadDemoData() {
        // 加载演示数据
        materials = Material.demoList
        keywords = Keyword.demoList
    }

    private func loadProjectData(_ project: Project) {
    }

    // MARK: - 从API加载项目列表
    func loadProjectsFromAPI() async {
        DebugLogger.shared.log("📋 开始加载项目列表...", type: .info)

        do {
            // 项目列表接口返回分页 envelope，不能按裸数组解码。
            let response = try await ProjectService.shared.listProjects()

            await MainActor.run {
                // 直接使用API返回的Project模型
                self.projects = response

                // 设置第一个项目为当前项目
                if !self.projects.isEmpty {
                    self.currentProject = self.projects[0]
                    DebugLogger.shared.log("✅ 加载了 \(self.projects.count) 个项目，当前项目: \(self.projects[0].name) (ID: \(self.projects[0].id))", type: .success)
                } else {
                    DebugLogger.shared.log("⚠️ 后端返回了空项目列表", type: .warning)
                }
            }
        } catch {
            DebugLogger.shared.log("❌ 加载项目失败: \(error.localizedDescription)", type: .error)
            print("加载项目失败: \(error.localizedDescription)")
        }
    }
}

// MARK: - 页面类型枚举
enum PageType: String, CaseIterable {
    case overview = "overview"
    case newproject = "newproject"
    case projects = "projects"
    case projectDetail = "project-detail"

    case `import` = "import"
    case upload = "upload"
    case fileManager = "file-manager"
    case photos = "photos"
    case tables = "tables"

    case keyword = "keyword"
    case chat = "chat"
    case conversations = "conversations"
    case citations = "citations"

    case dashboard = "dashboard"
    case vein = "vein"
    case chronicle = "chronicle"
    case timeline = "timeline"
    case graphExplorer = "graph-explorer"

    case report = "report"
    case report3 = "report3"
    case busi = "busi"

    case sop = "sop"
    case sopAnalysis = "sop-analysis"
    case workflow = "workflow"

    case skill = "skill"
    case agentMemory = "agent-memory"
    case advancedSearch = "advanced-search"
    case qualityMonitor = "quality-monitor"
    case model = "model"
    case settings = "settings"

    var title: String {
        switch self {
        case .overview: return "项目概览"
        case .newproject: return "新建项目"
        case .projects: return "项目列表"
        case .projectDetail: return "项目详情"
        case .import: return "材料导入"
        case .upload: return "文件上传"
        case .fileManager: return "文件管理器"
        case .photos: return "照片管理"
        case .tables: return "表格管理"
        case .keyword: return "关键词引擎"
        case .chat: return "AI 对话"
        case .conversations: return "对话历史"
        case .citations: return "引用管理"
        case .dashboard: return "可视化看板"
        case .vein: return "知识脉络"
        case .chronicle: return "编年史"
        case .timeline: return "时间线"
        case .graphExplorer: return "知识图谱"
        case .report: return "调研报告"
        case .report3: return "调研报告3"
        case .busi: return "业态分析报告"
        case .sop: return "SOP 管理"
        case .sopAnalysis: return "SOP 分析"
        case .workflow: return "工作流复用"
        case .skill: return "Skill 生态"
        case .agentMemory: return "Agent 记忆"
        case .advancedSearch: return "高级搜索"
        case .qualityMonitor: return "质量监控"
        case .model: return "模型管理"
        case .settings: return "设置"
        }
    }

    var requiresProject: Bool {
        switch self {
        case .newproject, .projects, .chat, .dashboard, .model, .settings:
            return false
        default:
            return true
        }
    }
}

// MARK: - Toast 类型
enum ToastType {
    case info
    case success
    case warning
    case error

    var color: Color {
        switch self {
        case .info: return .fmA1
        case .success: return .fmA2
        case .warning: return Color(hex: "F39C12")
        case .error: return Color(hex: "C0392B")
        }
    }

    var icon: String {
        switch self {
        case .info: return "info.circle.fill"
        case .success: return "checkmark.circle.fill"
        case .warning: return "exclamationmark.triangle.fill"
        case .error: return "xmark.circle.fill"
        }
    }
}
