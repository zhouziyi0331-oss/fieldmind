import Foundation

// MARK: - Project Model
struct Project: Identifiable, Codable {
    let id: Int
    let name: String
    let description: String?
    let status: String
    let documentCount: Int
    let contextCount: Int
    let chatSessionCount: Int
    let entityCount: Int
    let keywordCount: Int
    let isArchived: Bool
    let createdAt: String
    let updatedAt: String
    let lastActivityAt: String?
    let settings: ProjectSettings?
    // 移除 CodingKeys，让 convertFromSnakeCase 自动处理
}

struct ProjectSettings: Codable {
    let stats: Stats?

    struct Stats: Codable {
        let totalDocuments: Int?
        let completedDocuments: Int?
        let totalWords: Int?
        let totalEntities: Int?
        // 移除 CodingKeys，让 convertFromSnakeCase 自动处理
    }
}

// MARK: - User Model
struct User: Codable {
    let name: String
    let role: String
    let avatar: String
}

// MARK: - Material Model
struct Material: Identifiable, Codable {
    let id: String
    let name: String
    let type: MaterialType
    let size: String
    let uploadDate: Date
    var isProcessed: Bool
    var status: MaterialStatus?
    var progress: Double?
    var error: String?

    var uploadedAt: Date { uploadDate }
    var duration: String? { nil }
    var keywordCount: Int { 0 }

    init(
        id: String,
        name: String,
        type: MaterialType,
        size: String,
        duration: String?,
        keywordCount: Int,
        status: MaterialStatus,
        uploadedAt: Date
    ) {
        self.id = id
        self.name = name
        self.type = type
        self.size = size
        self.uploadDate = uploadedAt
        self.isProcessed = status == .completed
        self.status = status
        self.progress = status == .completed ? 1.0 : 0.0
        self.error = nil
    }

    init(
        id: String,
        name: String,
        type: MaterialType,
        size: String,
        uploadDate: Date,
        isProcessed: Bool,
        status: MaterialStatus?,
        progress: Double?,
        error: String?
    ) {
        self.id = id
        self.name = name
        self.type = type
        self.size = size
        self.uploadDate = uploadDate
        self.isProcessed = isProcessed
        self.status = status
        self.progress = progress
        self.error = error
    }

    enum MaterialStatus: String, Codable {
        case pending = "pending"
        case processing = "processing"
        case completed = "completed"
        case failed = "failed"

        var displayName: String {
            switch self {
            case .pending: return "待处理"
            case .processing: return "处理中"
            case .completed: return "已完成"
            case .failed: return "失败"
            }
        }
    }

    static let demoList: [Material] = [
        Material(id: "1", name: "田野访谈录音.mp3", type: .audio, size: "24.5 MB", uploadDate: Date(), isProcessed: true, status: .completed, progress: 1.0, error: nil),
        Material(id: "2", name: "调研笔记.txt", type: .text, size: "12 KB", uploadDate: Date(), isProcessed: true, status: .completed, progress: 1.0, error: nil),
        Material(id: "3", name: "现场照片.jpg", type: .image, size: "3.2 MB", uploadDate: Date(), isProcessed: false, status: .pending, progress: 0.0, error: nil)
    ]
}

enum MaterialType: String, Codable {
    case text = "text"
    case audio = "audio"
    case video = "video"
    case image = "image"
    case document = "document"
    case spreadsheet = "spreadsheet"

    var icon: String {
        switch self {
        case .text: return "doc.text"
        case .audio: return "waveform"
        case .video: return "video"
        case .image: return "photo"
        case .document: return "doc"
        case .spreadsheet: return "tablecells"
        }
    }

    var displayName: String {
        switch self {
        case .text: return "文本"
        case .audio: return "音频"
        case .video: return "视频"
        case .image: return "图片"
        case .document: return "文档"
        case .spreadsheet: return "表格"
        }
    }
}

// MARK: - Keyword Model
struct Keyword: Identifiable, Codable {
    let id: String
    let text: String
    let weight: Double
    let category: String?

    static let demoList: [Keyword] = [
        Keyword(id: "1", text: "田野调查", weight: 0.95, category: "方法"),
        Keyword(id: "2", text: "民族志", weight: 0.88, category: "理论"),
        Keyword(id: "3", text: "访谈", weight: 0.82, category: "方法"),
        Keyword(id: "4", text: "参与观察", weight: 0.76, category: "方法")
    ]
}

// MARK: - Conversation Model
struct Conversation: Identifiable, Codable {
    let id: String
    let title: String
    let createdAt: Date
    var messages: [Message]
}

struct Message: Identifiable, Codable {
    let id: String
    let content: String
    let role: MessageRole
    let timestamp: Date
}

enum MessageRole: String, Codable {
    case user = "user"
    case assistant = "assistant"
    case system = "system"
}

// MARK: - AI Model
struct AIModel: Identifiable, Codable {
    let id: String
    let name: String
    let provider: String
    let type: String
    let status: ModelStatus
    var config: ModelConfig?
    let color: String
    let icon: String

    var isActive: Bool { status == .active }
    var modelId: String { id }
    var isConfigured: Bool { config != nil }
    var description: String { "\(provider) \(type)" }
    var capabilities: [String] { [] }
    var contextWindow: Int { config?.maxTokens ?? 0 }
    var maxOutput: Int { config?.maxTokens ?? 0 }
    var performance: ModelPerformance { .empty }
    var pricing: ModelPricing { .empty }

    struct ModelPerformance {
        let totalCalls: Int
        let avgLatency: Double
        let successRate: Double
        let totalTokens: Int
        static let empty = ModelPerformance(totalCalls: 0, avgLatency: 0, successRate: 0, totalTokens: 0)
    }

    struct ModelPricing {
        let inputPrice: Double
        let outputPrice: Double
        let unit: String
        static let empty = ModelPricing(inputPrice: 0, outputPrice: 0, unit: "1K tokens")
    }
}

enum ModelStatus: String, Codable {
    case active = "active"
    case inactive = "inactive"
    case error = "error"
}

struct ModelConfig: Codable {
    var temperature: Double
    var maxTokens: Int
    var topP: Double
    var frequencyPenalty: Double
    var presencePenalty: Double
    var useCase: String
    var name: String
    var lastModified: String { "" }
    var systemPrompt: String? { nil }
}

// MARK: - Search Models
struct SearchResult: Identifiable, Codable {
    let id: String
    let title: String
    let content: String
    let source: String
    let relevance: Double
    let timestamp: Date
    let highlights: [String]
    let type: String
    let score: Double
    let snippet: String
    let projectName: String?
    let tags: [String]

    var fileType: String? { type.isEmpty ? nil : type }
    var metadata: [String: String] { [:] }
}

struct SavedSearch: Identifiable, Codable {
    let id: String
    let query: String
    let filters: [String: String]
    let savedAt: Date
    let name: String
    var isPinned: Bool
    let description: String

    var lastUsed: Date? { savedAt }
    var useCount: Int { 0 }
}

struct SearchHistory: Identifiable, Codable {
    let id: String
    let query: String
    let timestamp: String
    let resultCount: Int
}

// MARK: - Agent Memory
struct AgentMemory: Identifiable, Codable {
    let id: String
    let content: String
    let type: MemoryType
    let importance: Double
    let createdAt: Date
    let relatedMemories: [String]
    var tags: [String]
    let agentName: String
    let context: String
    let agentType: String
    let title: String

    var isPinned: Bool { false }
    var isArchived: Bool { false }
    var timestamp: String { ISO8601DateFormatter().string(from: createdAt) }
    var projectName: String? { nil }
    var projectId: Int { 0 }
    var memoryType: String { type.rawValue }
    var tokenCount: Int? { nil }
    var metadata: [String: String] { [:] }

    enum MemoryType: String, Codable {
        case shortTerm = "short_term"
        case longTerm = "long_term"
        case episodic = "episodic"
        case semantic = "semantic"
    }

    static let demoList: [AgentMemory] = [
        AgentMemory(
            id: "1",
            content: "用户询问了关于田野调查方法的问题",
            type: .shortTerm,
            importance: 0.8,
            createdAt: Date(),
            relatedMemories: [],
            tags: ["田野调查", "方法论"],
            agentName: "研究助手",
            context: "对话上下文",
            agentType: "assistant",
            title: "田野调查方法咨询"
        )
    ]
}

// MARK: - Chronicle Event
struct ChronicleEvent: Identifiable, Codable {
    let id: String
    let title: String
    let description: String
    let timestamp: Date
    let type: EventType
    let relatedItems: [String]
    let category: String
    let date: String

    var tags: [String] { [] }
    var project: String { "当前项目" }
    var location: String? { nil }
    var participants: [String] { relatedItems }
    var materials: [String] { relatedItems }
    var importance: Int { 0 }

    enum EventType: String, Codable {
        case upload = "upload"
        case analysis = "analysis"
        case conversation = "conversation"
        case milestone = "milestone"
    }
}

// MARK: - File Status
enum FileStatus: String, Codable {
    case pending = "pending"
    case processing = "processing"
    case completed = "completed"
    case failed = "failed"

    var displayName: String {
        switch self {
        case .pending: return "待处理"
        case .processing: return "处理中"
        case .completed: return "已完成"
        case .failed: return "失败"
        }
    }
}

// MARK: - Quality Models
struct QualityCheckTask: Identifiable, Codable {
    let id: String
    let name: String
    let description: String
    let status: TaskStatus
    let priority: Int
    let assignee: String?
    let dueDate: Date?
    let frequency: String
    let category: String

    var lastRun: String? { nil }
    var nextRun: String? { nil }
    var duration: String? { nil }
    var issuesFound: Int { 0 }

    enum TaskStatus: String, Codable, CaseIterable {
        case idle = "idle"
        case running = "running"
        case pending = "pending"
        case inProgress = "in_progress"
        case completed = "completed"
        case failed = "failed"

        init?(rawValue: String) {
            switch rawValue.lowercased() {
            case "pending": self = .pending
            case "in_progress", "in-progress": self = .inProgress
            case "completed": self = .completed
            case "failed": self = .failed
            default: self = .pending
            }
        }
    }
}

struct QualityIssue: Identifiable, Codable {
    let id: String
    let title: String
    let description: String
    let severity: Severity
    let status: IssueStatus
    let createdAt: Date
    let type: String

    var projectName: String? { nil }
    var timestamp: String { ISO8601DateFormatter().string(from: createdAt) }
    var category: String { type }
    var affectedItems: Int { 0 }
    var suggestedAction: String { "请检查相关数据并重新运行质量检查。" }

    enum Severity: String, Codable, CaseIterable {
        case low = "low"
        case medium = "medium"
        case high = "high"
        case critical = "critical"

        init?(rawValue: String) {
            switch rawValue.lowercased() {
            case "low": self = .low
            case "medium": self = .medium
            case "high": self = .high
            case "critical": self = .critical
            default: self = .low
            }
        }
    }

    enum IssueStatus: String, Codable, CaseIterable {
        case new = "new"
        case reviewing = "reviewing"
        case fixing = "fixing"
        case open = "open"
        case inProgress = "in_progress"
        case resolved = "resolved"
        case closed = "closed"

        init?(rawValue: String) {
            switch rawValue.lowercased() {
            case "new": self = .new
            case "reviewing": self = .reviewing
            case "fixing": self = .fixing
            case "open": self = .open
            case "in_progress", "in-progress", "inprogress": self = .inProgress
            case "resolved": self = .resolved
            case "closed": self = .closed
            default: return nil
            }
        }
    }
}

struct QualityMetric: Identifiable, Codable {
    let id: String
    let name: String
    let value: Double
    let unit: String
    let threshold: Double
    let status: MetricStatus

    var icon: String { "checkmark.shield" }
    var change: Double { 0 }
    var description: String { "\(name)：\(String(format: "%.1f", value))\(unit)" }

    enum MetricStatus: String, Codable, CaseIterable {
        case excellent = "excellent"
        case good = "good"
        case warning = "warning"
        case critical = "critical"

        init?(rawValue: String) {
            switch rawValue.lowercased() {
            case "good": self = .good
            case "warning": self = .warning
            case "critical": self = .critical
            default: self = .good
            }
        }
    }
}

// MARK: - Report
struct Report: Identifiable, Codable {
    let id: String
    let title: String
    let description: String
    let type: ReportType
    let createdAt: Date
    let author: String
    let content: String
    let date: String
    let sections: [ReportSection]?
    let attachments: [ReportAttachment]?

    var status: String { "草稿" }
    var project: String { "当前项目" }
    var summary: String { description }
    var tags: [String] { [] }
    var stats: ReportStats { ReportStats(wordCount: content.count, viewCount: 0, exportCount: 0, lastModified: date) }

    struct ReportStats {
        let wordCount: Int
        let viewCount: Int
        let exportCount: Int
        let lastModified: String
    }

    enum ReportType: String, Codable {
        case summary = "summary"
        case analysis = "analysis"
        case progress = "progress"
        case custom = "custom"
    }

    struct ReportSection: Identifiable, Codable {
        let id: String
        let title: String
        let content: String
        let order: Int
    }

    struct ReportAttachment: Identifiable, Codable {
        let id: String
        let name: String
        let url: String
        let type: String
        let size: String
    }
}

// MARK: - SOP Analysis
struct SOPAnalysis: Identifiable, Codable {
    let id: String
    let title: String
    let description: String
    let steps: [SOPStep]
    let status: String
    let progress: Double

    struct TrendData: Identifiable, Codable {
        let id: String
        let date: String
        let usageCount: Int
        let successRate: Double
    }

    struct Comparison: Codable {
        let metric: String
        let currentValue: Double
        let avgValue: Double
        let bestValue: Double
        let ranking: String
    }

    struct SOPStep: Identifiable, Codable {
        let id: String
        let title: String
        let description: String
        let order: Int
        let isCompleted: Bool
    }
}

// MARK: - Settings
enum SettingsCategory: String, CaseIterable, Identifiable, Codable {
    case general
    case model
    case data
    case appearance
    case advanced
    case about

    var id: String { rawValue }

    var name: String {
        switch self {
        case .general: return "通用设置"
        case .model: return "模型设置"
        case .data: return "数据设置"
        case .appearance: return "外观设置"
        case .advanced: return "高级设置"
        case .about: return "关于 FieldMind"
        }
    }

    var icon: String {
        switch self {
        case .general: return "gearshape"
        case .model: return "cpu"
        case .data: return "externaldrive"
        case .appearance: return "paintbrush"
        case .advanced: return "wrench.and.screwdriver"
        case .about: return "info.circle"
        }
    }
}

struct SettingsItem: Identifiable, Codable {
    let id: String
    let name: String
    let description: String
    let type: SettingType
    var value: SettingsValue
    let icon: String?

    var title: String { name }

    enum SettingType: String, Codable {
        case toggle = "toggle"
        case text = "text"
        case select = "select"
        case selection = "selection"
        case number = "number"
        case action = "action"
        case info = "info"
    }

    enum SettingsValue: Codable {
        case string(String)
        case bool(Bool)
        case int(Int)
        case double(Double)
        case selection(String, [String])

        init(from decoder: Decoder) throws {
            let container = try decoder.singleValueContainer()
            if let value = try? container.decode(Bool.self) {
                self = .bool(value)
            } else if let value = try? container.decode(Int.self) {
                self = .int(value)
            } else if let value = try? container.decode(Double.self) {
                self = .double(value)
            } else if let value = try? container.decode(String.self) {
                self = .string(value)
            } else {
                self = .string("")
            }
        }

        func encode(to encoder: Encoder) throws {
            var container = encoder.singleValueContainer()
            switch self {
            case .string(let value): try container.encode(value)
            case .bool(let value): try container.encode(value)
            case .int(let value): try container.encode(value)
            case .double(let value): try container.encode(value)
            case .selection(let value, _): try container.encode(value)
            }
        }
    }
}

enum SettingsData {
    static func getSettings(for category: SettingsCategory) -> [SettingsItem] {
        switch category {
        case .general:
            return [
                SettingsItem(id: "auto_process", name: "自动处理上传文件", description: "上传后自动运行统一解析、结构化和标签链路", type: .toggle, value: .bool(true), icon: "bolt.horizontal"),
                SettingsItem(id: "language", name: "界面语言", description: "选择应用界面语言", type: .selection, value: .selection("中文", ["中文", "English"]), icon: "globe")
            ]
        case .model:
            return [SettingsItem(id: "model_endpoint", name: "模型服务地址", description: "统一使用当前 API 服务地址", type: .text, value: .string(APIConfig.serverURL), icon: "network")]
        case .data:
            return [
                SettingsItem(id: "authorize_files", name: "授权文件访问", description: "选择一个或多个文件夹，让 FieldMind 能持续读取其中的材料", type: .action, value: .string(""), icon: "folder.badge.gearshape"),
                SettingsItem(id: "export_data", name: "导出数据", description: "导出当前项目的结构化数据和分析结果", type: .action, value: .string(""), icon: "square.and.arrow.up"),
                SettingsItem(id: "clear_cache", name: "清理缓存", description: "清理可重建的临时处理缓存", type: .action, value: .string(""), icon: "trash")
            ]
        case .appearance:
            return [SettingsItem(id: "compact_mode", name: "紧凑布局", description: "减少列表间距以显示更多内容", type: .toggle, value: .bool(false), icon: "rectangle.compress.vertical")]
        case .advanced:
            return [
                SettingsItem(id: "check_update", name: "检查更新", description: "检查当前正版桌面端是否有新版本", type: .action, value: .string(""), icon: "arrow.clockwise"),
                SettingsItem(id: "reset_settings", name: "恢复默认设置", description: "恢复本地界面配置，不删除项目数据", type: .action, value: .string(""), icon: "arrow.counterclockwise")
            ]
        case .about:
            return [SettingsItem(id: "license", name: "版本信息", description: "FieldMind Native 3.0", type: .info, value: .string("3.0"), icon: "info.circle")]
        }
    }
}

// MARK: - Skill
struct Skill: Identifiable, Codable {
    let id: String
    let name: String
    let description: String
    let category: String
    let status: SkillStatus
    let version: String
    let icon: String
    let isOfficial: Bool

    var isPremium: Bool { !isOfficial }
    var isInstalled: Bool { false }
    var rating: Double { 0 }
    var tags: [String] { [category] }
    var reviewCount: Int { 0 }
    var downloadCount: Int { 0 }
    var author: String { isOfficial ? "FieldMind" : "社区" }
    var detailedDescription: String { description }
    var features: [String] { [] }
    var usageExamples: [String] { [] }
    var requirements: [String] { [] }
    var dependencies: [String] { [] }
    var fileSize: String { "由服务端提供" }
    var compatibility: String { "macOS" }
    var lastUpdated: String { "" }
    var changelog: String { "当前版本已接入统一数据处理链路。" }

    enum SkillStatus: String, Codable {
        case active = "active"
        case inactive = "inactive"
        case deprecated = "deprecated"
    }
}

// MARK: - Team Member
struct TeamMember: Identifiable, Codable {
    let id: String
    let name: String
    let role: String
    let email: String
    let avatar: String?
    let status: MemberStatus

    enum MemberStatus: String, Codable {
        case active = "active"
        case inactive = "inactive"
        case invited = "invited"
    }
}

// MARK: - Workflow Template
struct WorkflowTemplate: Identifiable, Codable {
    let id: String
    let name: String
    let description: String
    let steps: [WorkflowStep]
    let category: String
    let icon: String
    let isFavorite: Bool

    var complexity: String { steps.count > 6 ? "复杂" : (steps.count > 3 ? "中等" : "简单") }
    var tags: [String] { [category] }
    var usageCount: Int { 0 }
    var rating: Double { 0 }
    var estimatedTime: String { "按步骤执行" }
    var createdBy: String { "FieldMind" }
    var createdAt: String { "" }
    var lastModified: String { "" }
    var isPublic: Bool { false }
    var components: [WorkflowComponent] {
        steps.map {
            WorkflowComponent(
                id: $0.id,
                name: $0.title,
                type: $0.type,
                stepNumber: $0.order,
                description: $0.description
            )
        }
    }
    var inputRequirements: [String] { [] }
    var outputs: [String] { [] }
    var estimatedDuration: String { estimatedTime }
    var outputDescription: String { "输出统一结构化分析结果。" }

    struct WorkflowComponent: Identifiable {
        let id: String
        let name: String
        let type: String
        let stepNumber: Int
        let description: String
        var configuration: String { "默认配置" }
        var estimatedDuration: String { "自动" }
    }

    struct WorkflowStep: Identifiable, Codable {
        let id: String
        let title: String
        let description: String
        let order: Int
        let type: String
    }
}
