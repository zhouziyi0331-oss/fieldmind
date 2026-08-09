import SwiftUI
import Combine

class AppState: ObservableObject {
    @Published var isAuthenticated = false
    @Published var currentUser: User?
    @Published var currentProject: Project? {
        didSet {
            if let project = currentProject {
                // 切换项目时，通知ProjectDataManager加载新项目数据
                ProjectDataManager.shared.switchProject(to: project)

                // 连接到项目的 WebSocket，接收实时通知
                WebSocketService.shared.connect(projectId: project.id)
            } else {
                // 如果没有项目，断开 WebSocket
                WebSocketService.shared.disconnect()
            }
        }
    }
    @Published var selectedPage: NavigationPage = .dashboard
    @Published var projects: [Project] = []

    private var cancellables = Set<AnyCancellable>()

    enum NavigationPage: String, CaseIterable {
        case dashboard = "概览"
        case projects = "项目管理"
        case contexts = "知识脉络"
        case documents = "材料导入"
        case chat = "智能对话"
        case keywordSearch = "关键词检索" // ⭐ NEW
        case timeline = "编年史"
        case graph = "关系图谱"
        case skills = "思维模型"
        case frameworks = "二度分析"
        case reports = "调研报告"
        case creativeAnalysis = "文创分析" // ⭐ NEW
        case businessAnalysis = "业态分析" // ⭐ NEW (重命名原来的 industryAnalysis)
        case crawler = "高级搜索"
        case audioVideo = "音视频"
        case workflows = "工作流复用"
        case agentMemory = "Agent记忆"
        case settings = "设置"

        var icon: String {
            switch self {
            case .dashboard: return "chart.bar.fill"
            case .projects: return "folder.fill"
            case .contexts: return "network"
            case .documents: return "doc.fill"
            case .chat: return "message.fill"
            case .keywordSearch: return "magnifyingglass" // ⭐ NEW
            case .timeline: return "clock.fill"
            case .graph: return "point.3.connected.trianglepath.dotted"
            case .skills: return "brain.head.profile"
            case .frameworks: return "list.bullet.clipboard"
            case .reports: return "doc.text.fill"
            case .creativeAnalysis: return "lightbulb.fill" // ⭐ NEW
            case .businessAnalysis: return "chart.line.uptrend.xyaxis" // ⭐ NEW
            case .crawler: return "magnifyingglass.circle.fill"
            case .audioVideo: return "waveform.circle.fill"
            case .workflows: return "arrow.triangle.branch"
            case .agentMemory: return "brain"
            case .settings: return "gearshape.fill"
            }
        }
    }

    init() {
        // 加载已保存的认证状态
        loadAuthState()
    }

    private func loadAuthState() {
        APIService.shared.loadAuthToken()
        // 如果有token，尝试获取当前用户
        Task {
            do {
                let user = try await APIService.shared.getCurrentUser()
                await MainActor.run {
                    self.currentUser = user
                    self.isAuthenticated = true
                    loadProjects()
                }
            } catch {
                // Token无效或过期，忽略错误
                print("加载认证状态失败: \(error)")
            }
        }
    }

    func login(user: User, token: String) {
        self.currentUser = user
        self.isAuthenticated = true
        APIService.shared.setAuthToken(token)
        loadProjects()
    }

    func logout() {
        self.currentUser = nil
        self.isAuthenticated = false
        self.currentProject = nil
        self.projects = []
        APIService.shared.setAuthToken(nil)
    }

    func selectProject(_ project: Project) {
        self.currentProject = project
    }

    func loadProjects() {
        Task {
            do {
                let projectList = try await APIService.shared.getProjects()
                await MainActor.run {
                    self.projects = projectList
                    // 如果还没有选中项目，选择第一个
                    if self.currentProject == nil, let firstProject = projectList.first {
                        self.selectProject(firstProject)
                    }
                }
            } catch {
                print("加载项目列表失败: \(error)")
            }
        }
    }

    func createProject(name: String, description: String?) async throws -> Project {
        let project = try await APIService.shared.createProject(name: name, description: description)
        await MainActor.run {
            projects.append(project)
            selectProject(project)
        }
        return project
    }

    func deleteProject(id: Int) async throws {
        try await APIService.shared.deleteProject(id: id)
        await MainActor.run {
            projects.removeAll { $0.id == id }
            if currentProject?.id == id {
                currentProject = projects.first
            }
        }
    }
}
