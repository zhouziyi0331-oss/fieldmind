import SwiftUI
import Combine

/// 项目数据管理器 - 管理每个项目的独立数据
class ProjectDataManager: ObservableObject {
    static let shared = ProjectDataManager()

    // 当前项目的数据
    @Published var documents: [Document] = []
    @Published var contexts: [Context] = []
    @Published var chatSessions: [ChatSession] = []
    @Published var timeline: Timeline?
    @Published var graph: KnowledgeGraph?
    @Published var graphStatistics: GraphStatistics?
    @Published var dashboardStats: DashboardStatsResponse?
    @Published var reports: [ReportResponse] = []
    @Published var skills: [Skill] = []

    // 加载状态
    @Published var isLoadingDocuments = false
    @Published var isLoadingContexts = false
    @Published var isLoadingTimeline = false
    @Published var isLoadingGraph = false
    @Published var isLoadingDashboard = false
    @Published var isLoadingReports = false
    @Published var isLoadingChat = false

    private var currentProjectId: Int?
    private var cancellables = Set<AnyCancellable>()

    private init() {}

    /// 切换项目时重置并加载新项目数据
    func switchProject(to project: Project?) {
        // 如果项目为空，清空所有数据
        guard let project = project else {
            currentProjectId = nil
            resetAllData()
            return
        }

        // 如果是同一个项目，不需要重新加载
        guard project.id != currentProjectId else { return }

        currentProjectId = project.id

        // 清空旧数据
        resetAllData()

        // 加载新项目的所有数据
        loadAllProjectData(projectId: project.id)
    }

    /// 重置所有数据
    private func resetAllData() {
        documents = []
        contexts = []
        chatSessions = []
        timeline = nil
        graph = nil
        graphStatistics = nil
        dashboardStats = nil
        reports = []
    }

    /// 加载项目的所有数据
    func loadAllProjectData(projectId: Int) {
        loadDocuments(projectId: projectId)
        loadContexts(projectId: projectId)
        loadTimeline(projectId: projectId)
        loadGraph(projectId: projectId)
        loadDashboardStats(projectId: projectId)
        loadReports()
        loadChatSessions(projectId: projectId)
    }

    // MARK: - 刷新数据（WebSocket 通知触发）

    func refreshDocuments() {
        guard let projectId = currentProjectId else { return }
        loadDocuments(projectId: projectId)
    }

    func refreshAllData() {
        guard let projectId = currentProjectId else { return }
        loadAllProjectData(projectId: projectId)
    }

    // MARK: - 文档

    func loadDocuments(projectId: Int) {
        isLoadingDocuments = true
        Task {
            do {
                let docs = try await APIService.shared.getDocuments(projectId: projectId)
                await MainActor.run {
                    self.documents = docs
                    self.isLoadingDocuments = false
                }
            } catch {
                print("加载文档失败: \(error)")
                await MainActor.run {
                    self.isLoadingDocuments = false
                }
            }
        }
    }

    func uploadDocument(projectId: Int, fileURL: URL) async throws -> DocumentUploadResponse {
        let response = try await APIService.shared.uploadDocument(projectId: projectId, fileURL: fileURL)

        // 上传成功后，等待处理完成
        if let taskId = response.taskId {
            try await waitForDocumentProcessing(taskId: taskId)
        }

        // 刷新所有数据
        await MainActor.run {
            refreshAllData()
        }

        return response
    }

    private func waitForDocumentProcessing(taskId: String) async throws {
        var attempts = 0
        let maxAttempts = 60 // 最多等待60秒

        while attempts < maxAttempts {
            try await Task.sleep(nanoseconds: 1_000_000_000) // 等待1秒

            let status = try await APIService.shared.getDocumentStatus(taskId: taskId)

            if status.ready {
                if let result = status.result, result.success {
                    return
                } else {
                    throw NSError(domain: "DocumentProcessing", code: -1, userInfo: [NSLocalizedDescriptionKey: "文档处理失败"])
                }
            }

            attempts += 1
        }

        throw NSError(domain: "DocumentProcessing", code: -2, userInfo: [NSLocalizedDescriptionKey: "文档处理超时"])
    }

    func deleteDocument(id: Int) async throws {
        try await APIService.shared.deleteDocument(id: id)
        await MainActor.run {
            documents.removeAll { $0.id == id }
            refreshAllData()
        }
    }

    func processDocument(id: Int) async throws {
        // 触发文档处理
        try await APIService.shared.processDocument(id: id)
        // 刷新文档列表
        if let projectId = currentProjectId {
            loadDocuments(projectId: projectId)
        }
    }

    // MARK: - 知识脉络

    func loadContexts(projectId: Int) {
        isLoadingContexts = true
        Task {
            do {
                let ctxs = try await APIService.shared.getContexts(projectId: projectId)
                await MainActor.run {
                    self.contexts = ctxs
                    self.isLoadingContexts = false
                }
            } catch {
                print("加载知识脉络失败: \(error)")
                await MainActor.run {
                    self.isLoadingContexts = false
                }
            }
        }
    }

    func createContext(projectId: Int, name: String, description: String?, keywords: [String], level: Int, parentId: Int?) async throws -> Context {
        let context = try await APIService.shared.createContext(
            projectId: projectId,
            name: name,
            description: description,
            keywords: keywords,
            level: level,
            parentId: parentId
        )

        await MainActor.run {
            contexts.append(context)
        }

        return context
    }

    // MARK: - 编年史

    func loadTimeline(projectId: Int) {
        isLoadingTimeline = true
        Task {
            do {
                let tl = try await APIService.shared.getTimeline(projectId: projectId)
                await MainActor.run {
                    self.timeline = tl
                    self.isLoadingTimeline = false
                }
            } catch {
                print("加载编年史失败: \(error)")
                await MainActor.run {
                    self.isLoadingTimeline = false
                }
            }
        }
    }

    func generateTimeline(projectId: Int, documentIds: [Int]?) async throws -> Timeline {
        let tl = try await APIService.shared.generateTimeline(projectId: projectId, documentIds: documentIds)
        await MainActor.run {
            self.timeline = tl
        }
        return tl
    }

    // MARK: - 知识图谱

    func loadGraph(projectId: Int) {
        isLoadingGraph = true
        Task {
            do {
                let stats = try await APIService.shared.getGraphStatistics(projectId: projectId)
                await MainActor.run {
                    self.graphStatistics = stats
                    self.isLoadingGraph = false
                }

                // 如果有数据，加载完整图谱
                if stats.nodeCount > 0 {
                    let viz = try await APIService.shared.getGraphVisualization(limit: 200)
                    await MainActor.run {
                        // 转换为KnowledgeGraph格式
                        // TODO: 实现转换逻辑
                    }
                }
            } catch {
                print("加载知识图谱失败: \(error)")
                await MainActor.run {
                    self.isLoadingGraph = false
                }
            }
        }
    }

    // 便捷方法 - 加载当前项目的图谱数据
    func loadGraphData() {
        guard let projectId = currentProjectId else { return }
        loadGraph(projectId: projectId)
    }

    func buildGraph(projectId: Int, documentIds: [Int]?) async throws -> KnowledgeGraph {
        let graph = try await APIService.shared.buildGraph(projectId: projectId, documentIds: documentIds)
        await MainActor.run {
            self.graph = graph
        }
        return graph
    }

    // MARK: - 数据看板

    func loadDashboardStats(projectId: Int) {
        isLoadingDashboard = true
        Task {
            do {
                let stats = try await APIService.shared.getDashboardStats(projectId: projectId)
                await MainActor.run {
                    self.dashboardStats = stats
                    self.isLoadingDashboard = false
                }
            } catch {
                print("加载数据看板失败: \(error)")
                await MainActor.run {
                    self.isLoadingDashboard = false
                }
            }
        }
    }

    // MARK: - 报告

    func loadReports() {
        isLoadingReports = true
        Task {
            do {
                let rpts = try await APIService.shared.getReports(page: 1, limit: 50)
                await MainActor.run {
                    self.reports = rpts
                    self.isLoadingReports = false
                }
            } catch {
                print("加载报告失败: \(error)")
                await MainActor.run {
                    self.isLoadingReports = false
                }
            }
        }
    }

    func generateReport(title: String, reportType: String, timeRange: [String: String]?, include: [String: Bool], dataSources: [String: [String]], format: String) async throws -> ReportGenerateResponse {
        let response = try await APIService.shared.generateReport(
            title: title,
            reportType: reportType,
            timeRange: timeRange,
            include: include,
            dataSources: dataSources,
            format: format
        )

        // 刷新报告列表
        loadReports()

        return response
    }

    func deleteReport(reportId: String) async throws {
        // TODO: 实现删除报告API
        await MainActor.run {
            reports.removeAll { $0.id == reportId }
        }
    }

    // MARK: - 聊天会话

    func loadChatSessions(projectId: Int) {
        Task {
            do {
                let sessions = try await APIService.shared.getChatSessions(projectId: projectId)
                await MainActor.run {
                    self.chatSessions = sessions
                }
            } catch {
                print("加载聊天会话失败: \(error)")
            }
        }
    }

    func createChatSession(projectId: Int, name: String, documentIds: [Int]) async throws -> ChatSession {
        let session = try await APIService.shared.createChatSession(projectId: projectId, name: name, documentIds: documentIds)
        await MainActor.run {
            chatSessions.append(session)
        }
        return session
    }

    func sendMessage(sessionId: Int, message: String, framework: String?) async throws -> ChatMessage {
        return try await APIService.shared.sendMessage(sessionId: sessionId, message: message, framework: framework)
    }

    // MARK: - 技能

    func loadSkills() {
        Task {
            do {
                let sklls = try await APIService.shared.getSkills()
                await MainActor.run {
                    self.skills = sklls
                }
            } catch {
                print("加载技能失败: \(error)")
            }
        }
    }

    func executeSkill(skillId: Int, projectId: Int, parameters: [String: String]?) async throws -> SkillExecuteResponse {
        return try await APIService.shared.executeSkill(skillId: skillId, projectId: projectId, parameters: parameters)
    }
}
