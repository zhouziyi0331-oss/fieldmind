//
//  DistillationService.swift
//  FieldMind - 知识蒸馏网络服务
//
//  与 Python Backend 的 /api/v1/distillation 端点通信
//

import Foundation
import Combine

// MARK: - 数据模型

/// 蒸馏作业状态
enum DistillationStatus: String, Codable {
    case pending = "PENDING"
    case normalizing = "NORMALIZING"
    case stage0 = "STAGE0_ANALYZING"
    case stage1 = "STAGE1_EXTRACTING"
    case stage1_5 = "STAGE1_5_VERIFYING"
    case stage2 = "STAGE2_BUILDING"
    case knowledgeExtracting = "KNOWLEDGE_EXTRACTING"
    case testing = "TESTING"
    case freezing = "FREEZING"
    case completed = "COMPLETED"
    case failed = "FAILED"

    var displayName: String {
        switch self {
        case .pending: return "等待中"
        case .normalizing: return "标准化中"
        case .stage0: return "分析书籍结构"
        case .stage1: return "提取候选方法"
        case .stage1_5: return "三重验证"
        case .stage2: return "构建 RIA++"
        case .knowledgeExtracting: return "提取知识单元"
        case .testing: return "压力测试"
        case .freezing: return "冻结归档"
        case .completed: return "✅ 完成"
        case .failed: return "❌ 失败"
        }
    }

    var progress: Double {
        switch self {
        case .pending: return 0.0
        case .normalizing: return 0.1
        case .stage0: return 0.2
        case .stage1: return 0.4
        case .stage1_5: return 0.5
        case .stage2: return 0.6
        case .knowledgeExtracting: return 0.7
        case .testing: return 0.85
        case .freezing: return 0.95
        case .completed: return 1.0
        case .failed: return 0.0
        }
    }
}

/// 源类型
enum SourceKind: String, Codable {
    case book = "book"
    case article = "article"
    case paper = "paper"
    case video = "video"
    case audio = "audio"
}

/// 蒸馏作业
struct DistillationJob: Codable, Identifiable {
    let id: String
    let generationId: String
    let status: DistillationStatus
    let sourceKind: SourceKind
    let title: String
    let author: String?
    let sourceUrl: String?
    let sourceHash: String?
    let createdAt: String
    let updatedAt: String
    let completedAt: String?
    let errorMessage: String?
    let progress: Double?

    enum CodingKeys: String, CodingKey {
        case id, status, title, author, progress
        case generationId = "generation_id"
        case sourceKind = "source_kind"
        case sourceUrl = "source_url"
        case sourceHash = "source_hash"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
        case completedAt = "completed_at"
        case errorMessage = "error_message"
    }
}

/// 知识单元
struct KnowledgeUnit: Codable, Identifiable {
    let id: String
    let jobId: String
    let knowledgeType: String
    let content: String
    let evidence: String?
    let chapterTitle: String?
    let confidence: Double?

    enum CodingKeys: String, CodingKey {
        case id, content, evidence, confidence
        case jobId = "job_id"
        case knowledgeType = "knowledge_type"
        case chapterTitle = "chapter_title"
    }
}

/// 方法单元（RIA++）
struct MethodUnit: Codable, Identifiable {
    let id: String
    let jobId: String
    let methodName: String
    let reading: String
    let interpretation: String
    let applicationPast: String?
    let applicationFuture: String?
    let execution: String?
    let boundary: String?
    let confidence: Double?
    let testCasesPassed: Int?

    enum CodingKeys: String, CodingKey {
        case id, reading, interpretation, execution, boundary, confidence
        case jobId = "job_id"
        case methodName = "method_name"
        case applicationPast = "application_past"
        case applicationFuture = "application_future"
        case testCasesPassed = "test_cases_passed"
    }
}

/// 系统统计
struct DistillationStats: Codable {
    let totalJobs: Int
    let completedJobs: Int
    let pendingJobs: Int
    let failedJobs: Int
    let totalKnowledge: Int
    let totalMethods: Int

    enum CodingKeys: String, CodingKey {
        case totalJobs = "total_jobs"
        case completedJobs = "completed_jobs"
        case pendingJobs = "pending_jobs"
        case failedJobs = "failed_jobs"
        case totalKnowledge = "total_knowledge"
        case totalMethods = "total_methods"
    }
}

// MARK: - 网络服务

class DistillationService: ObservableObject {
    static let shared = DistillationService()

    private let baseURL: String
    private var cancellables = Set<AnyCancellable>()

    @Published var isLoading = false
    @Published var errorMessage: String?

    init(baseURL: String = "http://localhost:8000") {
        self.baseURL = baseURL
    }

    // MARK: - 创建蒸馏任务（文件上传）

    func uploadAndDistill(
        fileURL: URL,
        sourceKind: SourceKind,
        title: String,
        author: String?
    ) -> AnyPublisher<DistillationJob, Error> {
        let endpoint = "\(baseURL)/api/v1/distillation/upload"

        var request = URLRequest(url: URL(string: endpoint)!)
        request.httpMethod = "POST"

        let boundary = UUID().uuidString
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

        var body = Data()

        // 添加文件
        if let fileData = try? Data(contentsOf: fileURL) {
            body.append("--\(boundary)\r\n".data(using: .utf8)!)
            body.append("Content-Disposition: form-data; name=\"file\"; filename=\"\(fileURL.lastPathComponent)\"\r\n".data(using: .utf8)!)
            body.append("Content-Type: application/octet-stream\r\n\r\n".data(using: .utf8)!)
            body.append(fileData)
            body.append("\r\n".data(using: .utf8)!)
        }

        // 添加元数据
        let metadata: [String: Any] = [
            "title": title,
            "author": author ?? "",
            "source_kind": sourceKind.rawValue
        ]

        if let jsonData = try? JSONSerialization.data(withJSONObject: metadata) {
            body.append("--\(boundary)\r\n".data(using: .utf8)!)
            body.append("Content-Disposition: form-data; name=\"metadata\"\r\n".data(using: .utf8)!)
            body.append("Content-Type: application/json\r\n\r\n".data(using: .utf8)!)
            body.append(jsonData)
            body.append("\r\n".data(using: .utf8)!)
        }

        body.append("--\(boundary)--\r\n".data(using: .utf8)!)
        request.httpBody = body

        return URLSession.shared.dataTaskPublisher(for: request)
            .map(\.data)
            .decode(type: DistillationJob.self, decoder: JSONDecoder())
            .receive(on: DispatchQueue.main)
            .eraseToAnyPublisher()
    }

    // MARK: - 创建蒸馏任务（URL）

    func distillFromURL(
        url: String,
        sourceKind: SourceKind,
        title: String,
        author: String?
    ) -> AnyPublisher<DistillationJob, Error> {
        let endpoint = "\(baseURL)/api/v1/distillation/url"

        var request = URLRequest(url: URL(string: endpoint)!)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body: [String: Any] = [
            "url": url,
            "title": title,
            "author": author ?? "",
            "source_kind": sourceKind.rawValue
        ]

        request.httpBody = try? JSONSerialization.data(withJSONObject: body)

        return URLSession.shared.dataTaskPublisher(for: request)
            .map(\.data)
            .decode(type: DistillationJob.self, decoder: JSONDecoder())
            .receive(on: DispatchQueue.main)
            .eraseToAnyPublisher()
    }

    // MARK: - 查询作业状态

    func getJobStatus(jobId: String) -> AnyPublisher<DistillationJob, Error> {
        let endpoint = "\(baseURL)/api/v1/distillation/jobs/\(jobId)"

        return URLSession.shared.dataTaskPublisher(for: URL(string: endpoint)!)
            .map(\.data)
            .decode(type: DistillationJob.self, decoder: JSONDecoder())
            .receive(on: DispatchQueue.main)
            .eraseToAnyPublisher()
    }

    // MARK: - 列出所有作业

    func listJobs(limit: Int = 50) -> AnyPublisher<[DistillationJob], Error> {
        let endpoint = "\(baseURL)/api/v1/distillation/jobs?limit=\(limit)"

        return URLSession.shared.dataTaskPublisher(for: URL(string: endpoint)!)
            .map(\.data)
            .decode(type: [DistillationJob].self, decoder: JSONDecoder())
            .receive(on: DispatchQueue.main)
            .eraseToAnyPublisher()
    }

    // MARK: - 获取知识单元

    func getKnowledge(jobId: String) -> AnyPublisher<[KnowledgeUnit], Error> {
        let endpoint = "\(baseURL)/api/v1/distillation/jobs/\(jobId)/knowledge"

        return URLSession.shared.dataTaskPublisher(for: URL(string: endpoint)!)
            .map(\.data)
            .decode(type: [KnowledgeUnit].self, decoder: JSONDecoder())
            .receive(on: DispatchQueue.main)
            .eraseToAnyPublisher()
    }

    // MARK: - 获取方法单元

    func getMethods(jobId: String) -> AnyPublisher<[MethodUnit], Error> {
        let endpoint = "\(baseURL)/api/v1/distillation/jobs/\(jobId)/methods"

        return URLSession.shared.dataTaskPublisher(for: URL(string: endpoint)!)
            .map(\.data)
            .decode(type: [MethodUnit].self, decoder: JSONDecoder())
            .receive(on: DispatchQueue.main)
            .eraseToAnyPublisher()
    }

    // MARK: - 获取系统统计

    func getStats() -> AnyPublisher<DistillationStats, Error> {
        let endpoint = "\(baseURL)/api/v1/distillation/stats"

        return URLSession.shared.dataTaskPublisher(for: URL(string: endpoint)!)
            .map(\.data)
            .decode(type: DistillationStats.self, decoder: JSONDecoder())
            .receive(on: DispatchQueue.main)
            .eraseToAnyPublisher()
    }

    // MARK: - 删除作业

    func deleteJob(jobId: String) -> AnyPublisher<Void, Error> {
        let endpoint = "\(baseURL)/api/v1/distillation/jobs/\(jobId)"

        var request = URLRequest(url: URL(string: endpoint)!)
        request.httpMethod = "DELETE"

        return URLSession.shared.dataTaskPublisher(for: request)
            .map { _ in () }
            .receive(on: DispatchQueue.main)
            .eraseToAnyPublisher()
    }

    // MARK: - 轮询作业状态直到完成

    func pollJobUntilComplete(jobId: String, interval: TimeInterval = 3.0) -> AnyPublisher<DistillationJob, Error> {
        Timer.publish(every: interval, on: .main, in: .common)
            .autoconnect()
            .flatMap { _ in self.getJobStatus(jobId: jobId) }
            .prefix { job in
                job.status != .completed && job.status != .failed
            }
            .append(self.getJobStatus(jobId: jobId))
            .eraseToAnyPublisher()
    }
}
