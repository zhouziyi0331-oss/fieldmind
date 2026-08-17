import Foundation

// MARK: - Response Models

struct DocumentUploadResponse: Codable {
    let id: Int
    let filename: String
    let fileType: String
    let fileSize: Int64
    let status: String
    let message: String?
}

struct DocumentResponse: Codable, Identifiable {
    let id: Int
    let projectId: Int
    let filename: String
    let originalFilename: String
    let fileType: String
    let filePath: String
    let fileSize: Int64
    let status: String
    let wordCount: Int?
    let errorMessage: String?
    let extraData: [String: AnyCodable]?
    let createdAt: String
    let updatedAt: String?
}

struct DocumentListResponse: Codable {
    let total: Int
    let documents: [DocumentResponse]
}

struct DocumentStatusResponse: Codable, Identifiable {
    let id: Int
    let filename: String
    let status: String
    let chunkCount: Int
    let vectorized: Bool
    let skillsCompleted: Bool
    let createdAt: String?
    let wordCount: Int?
    let fileType: String
    let errorMessage: String?
}

struct AggregatedKeywordResponse: Codable {
    let keyword: String
    let count: Int
    let weight: Double
    let documentIds: [Int]
}

struct KnowledgeBaseStatusResponse: Codable {
    let totalDocuments: Int
    let statusBreakdown: StatusBreakdown
    let vectorizedDocuments: Int
    let totalChunks: Int
    let readyForQuery: Bool

    struct StatusBreakdown: Codable {
        let pending: Int
        let processing: Int
        let completed: Int
        let failed: Int
    }
}

// MARK: - Document Service

class DocumentService {
    static let shared = DocumentService()
    private let apiClient = APIClient.shared

    private init() {}

    /// 上传文档到项目
    func uploadDocument(projectId: Int, fileURL: URL, autoProcess: Bool = true) async throws -> DocumentUploadResponse {
        let boundary = UUID().uuidString
        var request = URLRequest(url: URL(string: "\(APIConfig.baseURL)/documents/upload")!)
        request.httpMethod = "POST"
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

        // 读取文件数据
        let fileData = try Data(contentsOf: fileURL)
        let filename = fileURL.lastPathComponent
        let mimeType = mimeType(for: fileURL.pathExtension)

        // 构建multipart body
        var body = Data()

        // 添加project_id字段
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"project_id\"\r\n\r\n".data(using: .utf8)!)
        body.append("\(projectId)\r\n".data(using: .utf8)!)

        // 添加auto_process字段
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"auto_process\"\r\n\r\n".data(using: .utf8)!)
        body.append("\(autoProcess)\r\n".data(using: .utf8)!)

        // 添加文件字段
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"file\"; filename=\"\(filename)\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: \(mimeType)\r\n\r\n".data(using: .utf8)!)
        body.append(fileData)
        body.append("\r\n".data(using: .utf8)!)

        // 结束boundary
        body.append("--\(boundary)--\r\n".data(using: .utf8)!)

        request.httpBody = body

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw NetworkError.invalidResponse
        }

        guard (200...299).contains(httpResponse.statusCode) else {
            if let errorResponse = try? JSONDecoder().decode(ErrorResponse.self, from: data) {
                throw NetworkError.serverError(errorResponse.detail ?? errorResponse.message ?? "Unknown error")
            }
            throw NetworkError.httpError(statusCode: httpResponse.statusCode, message: nil)
        }

        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        return try decoder.decode(DocumentUploadResponse.self, from: data)
    }

    /// 获取项目的所有文档
    func listProjectDocuments(projectId: Int, skip: Int = 0, limit: Int = 50, status: String? = nil) async throws -> DocumentListResponse {
        var queryItems = [
            URLQueryItem(name: "skip", value: "\(skip)"),
            URLQueryItem(name: "limit", value: "\(limit)")
        ]
        if let status = status {
            queryItems.append(URLQueryItem(name: "status", value: status))
        }

        return try await apiClient.request(
            .custom("/documents/projects/\(projectId)/documents", queryItems: queryItems),
            method: .get
        )
    }

    /// 获取文档详情
    func getDocument(documentId: Int) async throws -> DocumentResponse {
        return try await apiClient.request(.getDocument(documentId: documentId), method: .get)
    }

    /// 删除文档
    func deleteDocument(documentId: Int) async throws {
        let _: EmptyResponse = try await apiClient.request(.deleteDocument(documentId: documentId), method: .delete)
    }

    /// 获取文档处理状态列表（用于轮询）
    func getDocumentsStatus(projectId: Int) async throws -> [DocumentStatusResponse] {
        return try await apiClient.request(
            .custom("/documents/status", queryItems: [
                URLQueryItem(name: "project_id", value: "\(projectId)")
            ]),
            method: .get
        )
    }

    /// 获取知识库状态统计
    func getKnowledgeBaseStatus() async throws -> KnowledgeBaseStatusResponse {
        return try await apiClient.request(
            .custom("/documents/knowledge-base/status"),
            method: .get
        )
    }

    /// 获取聚合的关键词
    func getAggregatedKeywords(projectId: Int, topN: Int = 50) async throws -> [AggregatedKeywordResponse] {
        return try await apiClient.request(
            .custom("/documents/aggregate/keywords", queryItems: [
                URLQueryItem(name: "project_id", value: "\(projectId)"),
                URLQueryItem(name: "top_n", value: "\(topN)")
            ]),
            method: .get
        )
    }

    // MARK: - Helper Methods

    private func mimeType(for pathExtension: String) -> String {
        switch pathExtension.lowercased() {
        case "pdf": return "application/pdf"
        case "doc": return "application/msword"
        case "docx": return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        case "xls": return "application/vnd.ms-excel"
        case "xlsx": return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        case "ppt": return "application/vnd.ms-powerpoint"
        case "pptx": return "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        case "txt": return "text/plain"
        case "md": return "text/markdown"
        case "html": return "text/html"
        case "csv": return "text/csv"
        case "json": return "application/json"
        case "xml": return "application/xml"
        case "mp3": return "audio/mpeg"
        case "wav": return "audio/wav"
        case "m4a": return "audio/mp4"
        case "mp4": return "video/mp4"
        case "mov": return "video/quicktime"
        default: return "application/octet-stream"
        }
    }
}

// MARK: - API Endpoint Extension

extension APIEndpoint {
    static func getDocument(documentId: Int) -> APIEndpoint {
        return .custom("/documents/\(documentId)")
    }

    static func deleteDocument(documentId: Int) -> APIEndpoint {
        return .custom("/documents/\(documentId)")
    }
}

