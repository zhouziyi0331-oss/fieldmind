//
//  UnifiedAppState.swift
//  FieldMind
//
//  统一应用状态管理 - 所有功能的中央状态树
//

import SwiftUI
import Combine

/// 统一的全局应用状态管理器
/// 这是整个应用的唯一真相来源（Single Source of Truth）
class UnifiedAppState: ObservableObject {

    // MARK: - 单例
    static let shared = UnifiedAppState()

    // MARK: - 核心服务层
    @Published var backendService: BackendService
    @Published var databaseService: DatabaseService
    @Published var syncService: SyncService

    // MARK: - 业务状态管理

    // 1. 项目系统
    @Published var currentProject: Project?
    @Published var projects: [Project] = []

    // 2. 材料管理
    @Published var materials: [Material] = []
    @Published var documents: [Document] = []
    @Published var uploadProgress: UploadProgress?

    // 3. 知识蒸馏系统
    @Published var distillationJobs: [DistillationJob] = []
    @Published var knowledgeUnits: [ExtractedKnowledge] = []
    @Published var methodUnits: [ExtractedMethod] = []
    @Published var activeDistillation: DistillationJob?

    // 4. 知识库系统（Obsidian 风格）
    @Published var vaultService: KnowledgeVaultService
    @Published var notes: [Note] = []
    @Published var graphNodes: [GraphNode] = []
    @Published var currentNote: Note?

    // 5. 关键词与实体
    @Published var keywords: [Keyword] = []
    @Published var entities: [Entity] = []
    @Published var entityRelations: [EntityRelation] = []

    // 6. AI 对话系统
    @Published var conversations: [Conversation] = []
    @Published var currentConversation: Conversation?
    @Published var chatMessages: [ChatMessage] = []

    // 7. 时间线与编年史
    @Published var timelines: [Timeline] = []
    @Published var chronicles: [Chronicle] = []
    @Published var timelineEvents: [TimelineEvent] = []

    // 8. 分析与报告
    @Published var reports: [AnalysisReport] = []
    @Published var dashboards: [DashboardData] = []
    @Published var veins: [KnowledgeVein] = []

    // 9. 工作流系统
    @Published var workflows: [Workflow] = []
    @Published var sops: [SOP] = []
    @Published var skills: [Skill] = []
    @Published var executionRecords: [ExecutionRecord] = []

    // 10. 质量监控
    @Published var qualityMetrics: QualityMetrics?
    @Published var monitoringAlerts: [MonitoringAlert] = []

    // MARK: - UI 状态
    @Published var currentPage: PageType = .overview
    @Published var isSidebarCollapsed: Bool = false
    @Published var isLoading: Bool = false
    @Published var errorMessage: String?

    // Toast 通知
    @Published var showToast: Bool = false
    @Published var toastMessage: String = ""
    @Published var toastType: ToastType = .info

    // MARK: - 数据更新通知
    @Published var lastDataUpdate: Date = Date()
    @Published var lastSyncTime: Date?

    // MARK: - Combine Cancellables
    private var cancellables = Set<AnyCancellable>()

    // MARK: - 初始化
    private init() {
        self.backendService = BackendService.shared
        self.databaseService = DatabaseService.shared
        self.syncService = SyncService.shared
        self.vaultService = KnowledgeVaultService.shared

        setupBindings()
        loadInitialData()
    }

    // MARK: - 数据绑定
    private func setupBindings() {
        // 监听知识库变化
        vaultService.$notes
            .assign(to: &$notes)

        vaultService.$graphNodes
            .assign(to: &$graphNodes)

        // 监听后端状态
        backendService.$isRunning
            .sink { [weak self] isRunning in
                if isRunning {
                    self?.loadProjectsFromBackend()
                }
            }
            .store(in: &cancellables)
    }

    // MARK: - 初始数据加载
    private func loadInitialData() {
        Task {
            await loadProjectsFromBackend()
        }
    }

    // MARK: - 项目管理

    func loadProjectsFromBackend() async {
        isLoading = true
        defer { isLoading = false }

        do {
            let loadedProjects = try await ProjectService.shared.listProjects()
            await MainActor.run {
                self.projects = loadedProjects
                if !loadedProjects.isEmpty && currentProject == nil {
                    self.currentProject = loadedProjects[0]
                }
                showToast(message: "✅ 加载了 \(loadedProjects.count) 个项目", type: .success)
            }
        } catch {
            await MainActor.run {
                showToast(message: "❌ 加载项目失败: \(error.localizedDescription)", type: .error)
            }
        }
    }

    func switchProject(_ project: Project) {
        currentProject = project
        // 切换项目时重新加载相关数据
        Task {
            await loadProjectData(project)
        }
    }

    func loadProjectData(_ project: Project) async {
        // 并行加载项目相关的所有数据
        async let materials = loadMaterialsForProject(project.id)
        async let keywords = loadKeywordsForProject(project.id)
        async let timelines = loadTimelinesForProject(project.id)
        async let reports = loadReportsForProject(project.id)

        _ = await (materials, keywords, timelines, reports)

        await MainActor.run {
            notifyDataUpdated()
        }
    }

    // MARK: - 材料管理 + 蒸馏深度整合

    /// 上传材料并自动触发蒸馏
    func uploadMaterialWithDistillation(
        fileURL: URL,
        projectId: String,
        autoDistill: Bool = true
    ) async throws -> (Material, DistillationJob?) {
        // 1. 上传材料
        let material = try await uploadMaterial(fileURL: fileURL, projectId: projectId)

        var distillationJob: DistillationJob? = nil

        // 2. 自动触发蒸馏
        if autoDistill {
            distillationJob = try await triggerDistillation(materialId: material.id)

            // 3. 监听蒸馏完成
            Task {
                await pollDistillationUntilComplete(jobId: distillationJob!.id)
            }
        }

        return (material, distillationJob)
    }

    private func uploadMaterial(fileURL: URL, projectId: String) async throws -> Material {
        // TODO: 实现材料上传逻辑
        // 调用后端 API
        let material = Material(id: UUID().uuidString, name: fileURL.lastPathComponent, projectId: projectId)

        await MainActor.run {
            self.materials.append(material)
        }

        return material
    }

    private func triggerDistillation(materialId: String) async throws -> DistillationJob {
        // 调用蒸馏服务
        let job = DistillationJob(
            id: UUID().uuidString,
            sourceId: materialId,
            status: .pending,
            progress: 0.0
        )

        await MainActor.run {
            self.distillationJobs.append(job)
            self.activeDistillation = job
        }

        return job
    }

    private func pollDistillationUntilComplete(jobId: String) async {
        // 轮询蒸馏状态直到完成
        while true {
            guard let job = distillationJobs.first(where: { $0.id == jobId }) else { break }

            if job.status == .completed {
                // 蒸馏完成，处理结果
                await handleDistillationComplete(jobId: jobId)
                break
            } else if job.status == .failed {
                await MainActor.run {
                    showToast(message: "❌ 蒸馏失败", type: .error)
                }
                break
            }

            // 等待 3 秒后继续轮询
            try? await Task.sleep(nanoseconds: 3_000_000_000)
        }
    }

    private func handleDistillationComplete(jobId: String) async {
        // 1. 获取蒸馏结果
        guard let job = distillationJobs.first(where: { $0.id == jobId }) else { return }

        // 2. 创建知识库笔记
        await createNotesFromKnowledge(jobId: jobId)

        // 3. 提取实体和关键词
        await extractEntitiesFromKnowledge(jobId: jobId)

        // 4. 生成 SOP（如果有方法单元）
        await generateSOPsFromMethods(jobId: jobId)

        // 5. 更新知识图谱
        await updateKnowledgeGraph()

        await MainActor.run {
            showToast(message: "✅ 知识蒸馏完成并已整合", type: .success)
            notifyDataUpdated()
        }
    }

    // MARK: - 知识单元 → 笔记自动转换

    private func createNotesFromKnowledge(jobId: String) async {
        let knowledge = knowledgeUnits.filter { $0.jobId == jobId }

        for unit in knowledge {
            let note = vaultService.createNote(
                title: unit.title,
                content: unit.content,
                tags: unit.tags + ["distilled", "knowledge-unit"]
            )

            // 建立关联
            await linkKnowledgeToNote(knowledgeId: unit.id, noteId: note.id)
        }
    }

    // MARK: - 方法单元 → SOP 自动生成

    private func generateSOPsFromMethods(jobId: String) async {
        let methods = methodUnits.filter { $0.jobId == jobId }

        for method in methods {
            if method.isReusable {
                let sop = generateSOPFromMethod(method: method)
                await MainActor.run {
                    self.sops.append(sop)
                }

                // 建立关联
                await linkMethodToSOP(methodId: method.id, sopId: sop.id)
            }
        }
    }

    private func generateSOPFromMethod(method: ExtractedMethod) -> SOP {
        return SOP(
            id: UUID().uuidString,
            title: method.title,
            description: method.interpretation,
            steps: parseStepsFromExecution(method.execution),
            triggers: [method.futureTrigger],
            boundaries: [method.boundary]
        )
    }

    private func parseStepsFromExecution(_ execution: String) -> [SOPStep] {
        // 解析执行步骤
        let lines = execution.components(separatedBy: "\n")
        return lines.enumerated().map { index, line in
            SOPStep(order: index + 1, description: line)
        }
    }

    // MARK: - AI 对话 → 笔记保存

    func createNoteFromConversation(conversationId: String) async throws -> Note {
        guard let conversation = conversations.first(where: { $0.id == conversationId }) else {
            throw AppError.conversationNotFound
        }

        // 提取对话中的关键内容
        let content = extractKeyInsightsFromConversation(conversation)

        // 创建笔记
        let note = vaultService.createNote(
            title: "对话见解 - \(conversation.title)",
            content: content,
            tags: ["conversation", "insight"]
        )

        // 建立关联
        await linkNoteToConversation(noteId: note.id, conversationId: conversationId)

        await MainActor.run {
            showToast(message: "✅ 已保存为笔记", type: .success)
        }

        return note
    }

    private func extractKeyInsightsFromConversation(_ conversation: Conversation) -> String {
        // TODO: 使用 LLM 提取关键见解
        return conversation.messages.map { $0.content }.joined(separator: "\n\n")
    }

    // MARK: - 知识图谱统一视图

    func updateKnowledgeGraph() async {
        // 整合所有数据源到统一图谱
        var nodes: [GraphNode] = []
        var edges: [GraphEdge] = []

        // 1. 笔记节点
        nodes += notes.map { note in
            GraphNode(id: note.id.uuidString, type: .note, title: note.title, data: note)
        }

        // 2. 知识单元节点
        nodes += knowledgeUnits.map { knowledge in
            GraphNode(id: knowledge.id.uuidString, type: .knowledge, title: knowledge.title, data: knowledge)
        }

        // 3. 实体节点
        nodes += entities.map { entity in
            GraphNode(id: entity.id, type: .entity, title: entity.name, data: entity)
        }

        // 4. 方法节点
        nodes += methodUnits.map { method in
            GraphNode(id: method.id.uuidString, type: .method, title: method.title, data: method)
        }

        // 5. SOP 节点
        nodes += sops.map { sop in
            GraphNode(id: sop.id, type: .sop, title: sop.title, data: sop)
        }

        // TODO: 构建边（关系）

        await MainActor.run {
            // 更新图谱
            vaultService.updateGraph()
        }
    }

    // MARK: - 跨模块关联管理

    private func linkKnowledgeToNote(knowledgeId: UUID, noteId: UUID) async {
        // TODO: 存储到数据库
        await databaseService.createLink(
            sourceType: "knowledge",
            sourceId: knowledgeId.uuidString,
            targetType: "note",
            targetId: noteId.uuidString,
            linkType: "generated_from"
        )
    }

    private func linkMethodToSOP(methodId: UUID, sopId: String) async {
        await databaseService.createLink(
            sourceType: "method",
            sourceId: methodId.uuidString,
            targetType: "sop",
            targetId: sopId,
            linkType: "compiled_to"
        )
    }

    private func linkNoteToConversation(noteId: UUID, conversationId: String) async {
        await databaseService.createLink(
            sourceType: "note",
            sourceId: noteId.uuidString,
            targetType: "conversation",
            targetId: conversationId,
            linkType: "extracted_from"
        )
    }

    // MARK: - 实体提取

    private func extractEntitiesFromKnowledge(jobId: String) async {
        // TODO: 从知识单元中提取实体
    }

    // MARK: - 数据加载辅助方法

    private func loadMaterialsForProject(_ projectId: String) async {
        // TODO: 实现
    }

    private func loadKeywordsForProject(_ projectId: String) async {
        // TODO: 实现
    }

    private func loadTimelinesForProject(_ projectId: String) async {
        // TODO: 实现
    }

    private func loadReportsForProject(_ projectId: String) async {
        // TODO: 实现
    }

    // MARK: - 通知系统

    @MainActor
    func notifyDataUpdated() {
        lastDataUpdate = Date()
    }

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

    // MARK: - 页面导航

    func navigateTo(_ page: PageType) {
        withAnimation(.easeInOut(duration: 0.25)) {
            currentPage = page
        }
    }
}

// MARK: - 辅助数据结构

struct UploadProgress {
    var fileName: String
    var progress: Double
    var totalBytes: Int64
    var uploadedBytes: Int64
}

struct GraphNode {
    let id: String
    let type: GraphNodeType
    let title: String
    let data: Any
}

enum GraphNodeType {
    case note
    case knowledge
    case entity
    case method
    case sop
    case skill
    case timeline
}

struct GraphEdge {
    let source: String
    let target: String
    let type: String
}

enum AppError: Error {
    case conversationNotFound
    case materialNotFound
    case distillationFailed
}

// MARK: - 服务占位符（待实现完整版本）

class DatabaseService: ObservableObject {
    static let shared = DatabaseService()

    func createLink(sourceType: String, sourceId: String, targetType: String, targetId: String, linkType: String) async {
        // TODO: 实现数据库链接创建
    }
}

class SyncService: ObservableObject {
    static let shared = SyncService()
}

// MARK: - 数据模型占位符

struct Material: Identifiable {
    let id: String
    let name: String
    let projectId: String
}

struct Document: Identifiable {
    let id: String
    let title: String
}

struct Entity: Identifiable {
    let id: String
    let name: String
}

struct EntityRelation {
    let sourceId: String
    let targetId: String
    let type: String
}

struct Timeline: Identifiable {
    let id: String
    let title: String
}

struct Chronicle: Identifiable {
    let id: String
    let title: String
}

struct TimelineEvent: Identifiable {
    let id: String
    let timestamp: Date
}

struct AnalysisReport: Identifiable {
    let id: String
    let title: String
}

struct DashboardData: Identifiable {
    let id: String
}

struct KnowledgeVein: Identifiable {
    let id: String
    let title: String
}

struct Workflow: Identifiable {
    let id: String
    let title: String
}

struct SOP: Identifiable {
    let id: String
    let title: String
    let description: String
    let steps: [SOPStep]
    let triggers: [String]
    let boundaries: [String]
}

struct SOPStep {
    let order: Int
    let description: String
}

struct Skill: Identifiable {
    let id: String
    let name: String
}

struct ExecutionRecord: Identifiable {
    let id: String
}

struct QualityMetrics {
    var totalItems: Int
    var qualityScore: Double
}

struct MonitoringAlert: Identifiable {
    let id: String
    let message: String
}

struct ChatMessage: Identifiable {
    let id: String
    let content: String
}

struct Conversation: Identifiable {
    let id: String
    let title: String
    let messages: [ChatMessage]
}

struct Keyword: Identifiable {
    let id: String
    let text: String

    static var demoList: [Keyword] = []
}

extension Material {
    static var demoList: [Material] = []
}
