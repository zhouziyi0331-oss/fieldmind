//
//  DocumentService_Merged.swift
//  FieldMind
//
//  深度整合 - 合并自主版本和 Native 版本
//  Generated: Sat Sep 19 11:21:00 CST 2026
//

import Foundation

// ========================================
// 主实现（来自主项目）
// ========================================


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

private struct DocumentStatusEnvelope: Codable {
    let data: [DocumentStatusResponse]
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

    /// 上传文档到项目（带真实进度回调）
    func uploadDocument(
        projectId: Int,
        fileURL: URL,
        autoProcess: Bool = true,
        progressHandler: ((Double) -> Void)? = nil
    ) async throws -> DocumentUploadResponse {
        let boundary = UUID().uuidString
        var request = URLRequest(url: URL(string: "\(APIConfig.baseURL)/documents/upload")!)
        request.httpMethod = "POST"
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

        // NSOpenPanel 和拖拽产生的 URL 可能是安全作用域 URL。
        let securityScoped = fileURL.startAccessingSecurityScopedResource()
        defer {
            if securityScoped {
                fileURL.stopAccessingSecurityScopedResource()
            }
        }
        let fileData: Data
        do {
            fileData = try Data(contentsOf: fileURL)
        } catch {
            DebugLogger.shared.log("读取上传文件失败", type: .error, details: "文件=\(fileURL.path)\n错误=\(error.localizedDescription)", category: "upload")
            throw error
        }
        defer {
            if fileURL.path.hasPrefix(FileManager.default.temporaryDirectory.path),
               fileURL.lastPathComponent.hasPrefix("fieldmind-drop-") {
                try? FileManager.default.removeItem(at: fileURL)
            }
        }
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

        // 使用自定义 URLSession 以支持进度追踪
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 300 // 5分钟超时（大文件）
        let session = URLSession(configuration: config, delegate: nil, delegateQueue: nil)

        // 创建上传任务（带进度追踪）
        let totalBytes = Int64(body.count)

        let (data, response) = try await withCheckedThrowingContinuation { continuation in
            let task = session.uploadTask(with: request, from: body) { data, response, error in
                if let error = error {
                    continuation.resume(throwing: error)
                    return
                }
                guard let data = data, let response = response else {
                    continuation.resume(throwing: NetworkError.invalidResponse)
                    return
                }
                continuation.resume(returning: (data, response))
            }

            // 使用 KVO 监听上传进度
            let observation = task.progress.observe(\.fractionCompleted) { progress, _ in
                DispatchQueue.main.async {
                    progressHandler?(progress.fractionCompleted)
                }
            }

            task.resume()

            // 任务完成后移除观察者
            Task {
                _ = await task.value
                observation.invalidate()
            }
        }

        guard let httpResponse = response as? HTTPURLResponse else {
            throw NetworkError.invalidResponse
        }

        guard (200...299).contains(httpResponse.statusCode) else {
            if let errorResponse = try? JSONDecoder().decode(ErrorResponse.self, from: data) {
                throw NetworkError.serverError(errorResponse.detail ?? errorResponse.message ?? "Unknown error")
            }
            throw NetworkError.httpError(statusCode: httpResponse.statusCode, message: nil)
        }

        // 上传完成，设置进度为100%
        DispatchQueue.main.async {
            progressHandler?(1.0)
        }

        return try APIClient.decodePayload(data, as: DocumentUploadResponse.self)
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
            .custom("/documents/projects/\(projectId)/documents/", queryItems: queryItems),
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
        let response: DocumentStatusEnvelope = try await apiClient.request(
            .custom("/documents/list/status", queryItems: [
                URLQueryItem(name: "project_id", value: "\(projectId)")
            ]),
            method: .get
        )
        return response.data
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

// ========================================
// Native 版本的扩展功能
// ========================================
// TODO: 手动审查并整合以下功能

/*

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

private struct DocumentStatusEnvelope: Codable {
    let data: [DocumentStatusResponse]
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

    /// 上传文档到项目（带真实进度回调）
    func uploadDocument(
        projectId: Int,
        fileURL: URL,
        autoProcess: Bool = true,
        progressHandler: ((Double) -> Void)? = nil
    ) async throws -> DocumentUploadResponse {
        let boundary = UUID().uuidString
        var request = URLRequest(url: URL(string: "\(APIConfig.baseURL)/documents/upload")!)
        request.httpMethod = "POST"
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

        // NSOpenPanel 和拖拽产生的 URL 可能是安全作用域 URL。
        let securityScoped = fileURL.startAccessingSecurityScopedResource()
        defer {
            if securityScoped {
                fileURL.stopAccessingSecurityScopedResource()
            }
        }
        let fileData: Data
        do {
            fileData = try Data(contentsOf: fileURL)
        } catch {
            DebugLogger.shared.log("读取上传文件失败", type: .error, details: "文件=\(fileURL.path)\n错误=\(error.localizedDescription)", category: "upload")
            throw error
        }
        defer {
            if fileURL.path.hasPrefix(FileManager.default.temporaryDirectory.path),
               fileURL.lastPathComponent.hasPrefix("fieldmind-drop-") {
                try? FileManager.default.removeItem(at: fileURL)
            }
        }
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

        // 使用自定义 URLSession 以支持进度追踪
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 300 // 5分钟超时（大文件）
        let session = URLSession(configuration: config, delegate: nil, delegateQueue: nil)

        // 创建上传任务（带进度追踪）
        let totalBytes = Int64(body.count)

        let (data, response) = try await withCheckedThrowingContinuation { continuation in
            let task = session.uploadTask(with: request, from: body) { data, response, error in
                if let error = error {
                    continuation.resume(throwing: error)
                    return
                }
                guard let data = data, let response = response else {
                    continuation.resume(throwing: NetworkError.invalidResponse)
                    return
                }
                continuation.resume(returning: (data, response))
            }

            // 使用 KVO 监听上传进度
            let observation = task.progress.observe(\.fractionCompleted) { progress, _ in
                DispatchQueue.main.async {
                    progressHandler?(progress.fractionCompleted)
                }
            }

            task.resume()

            // 任务完成后移除观察者
            Task {
                _ = await task.value
                observation.invalidate()
            }
        }

        guard let httpResponse = response as? HTTPURLResponse else {
            throw NetworkError.invalidResponse
        }

        guard (200...299).contains(httpResponse.statusCode) else {
            if let errorResponse = try? JSONDecoder().decode(ErrorResponse.self, from: data) {
                throw NetworkError.serverError(errorResponse.detail ?? errorResponse.message ?? "Unknown error")
            }
            throw NetworkError.httpError(statusCode: httpResponse.statusCode, message: nil)
        }

        // 上传完成，设置进度为100%
        DispatchQueue.main.async {
            progressHandler?(1.0)
        }

        return try APIClient.decodePayload(data, as: DocumentUploadResponse.self)
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
            .custom("/documents/projects/\(projectId)/documents/", queryItems: queryItems),
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
        let response: DocumentStatusEnvelope = try await apiClient.request(
            .custom("/documents/list/status", queryItems: [
                URLQueryItem(name: "project_id", value: "\(projectId)")
            ]),
            method: .get
        )
        return response.data
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
*/

