import Foundation

/// PhotoService - 照片管理服务（带EXIF元数据支持）

class PhotoService {
    static let shared = PhotoService()
    private let apiClient = APIClient.shared

    private init() {}

    // MARK: - Response Models

    struct PhotoResponse: Codable, Identifiable {
        let id: String
        let filename: String
        let fileSize: Int64
        let filePath: String
        let format: String
        let width: Int
        let height: Int
        let takenAt: Date?
        let location: String?
        let device: String?
        let projectId: Int
        let tags: [String]
        let uploadedAt: Date

        enum CodingKeys: String, CodingKey {
            case id, filename, format, width, height, location, device, tags
            case fileSize = "file_size"
            case filePath = "file_path"
            case takenAt = "taken_at"
            case projectId = "project_id"
            case uploadedAt = "uploaded_at"
        }
    }

    struct PhotoListResponse: Codable {
        let photos: [PhotoResponse]
        let total: Int
        let page: Int
        let pageSize: Int

        enum CodingKeys: String, CodingKey {
            case photos, total, page
            case pageSize = "page_size"
        }
    }

    struct PhotoStatsResponse: Codable {
        let totalPhotos: Int
        let totalSize: Int
        let byDevice: [String: Int]
        let byLocation: [String: Int]
        let byFormat: [String: Int]
        let recentUploads: Int

        enum CodingKeys: String, CodingKey {
            case totalPhotos = "total_photos"
            case totalSize = "total_size"
            case byDevice = "by_device"
            case byLocation = "by_location"
            case byFormat = "by_format"
            case recentUploads = "recent_uploads"
        }
    }

    // MARK: - API Methods

    /// 获取照片列表
    func getPhotos(
        projectId: Int,
        search: String? = nil,
        dateFilter: String? = nil,
        sortBy: String = "uploaded_at",
        sortOrder: String = "desc",
        page: Int = 1,
        pageSize: Int = 50
    ) async throws -> PhotoListResponse {
        var endpoint = APIEndpoint.custom("/photos")
            .with(queryItem: "project_id", value: "\(projectId)")
            .with(queryItem: "sort_by", value: sortBy)
            .with(queryItem: "sort_order", value: sortOrder)
            .with(queryItem: "page", value: "\(page)")
            .with(queryItem: "page_size", value: "\(pageSize)")

        if let search = search, !search.isEmpty {
            endpoint = endpoint.with(queryItem: "search", value: search)
        }
        if let dateFilter = dateFilter, dateFilter != "all" {
            endpoint = endpoint.with(queryItem: "date_filter", value: dateFilter)
        }

        return try await apiClient.request(endpoint, method: .get)
    }

    /// 获取照片统计
    func getStats(projectId: Int) async throws -> PhotoStatsResponse {
        let endpoint = APIEndpoint.custom("/photos/stats/\(projectId)/")
        return try await apiClient.request(endpoint, method: .get)
    }

    /// 上传照片
    func uploadPhoto(
        projectId: Int,
        fileURL: URL,
        tags: [String]? = nil,
        locationName: String? = nil
    ) async throws -> UploadResponse {
        let boundary = UUID().uuidString
        guard let url = URL(string: "\(APIConfig.baseURL)/photos/upload") else {
            throw NetworkError.invalidURL
        }

        let securityScoped = fileURL.startAccessingSecurityScopedResource()
        defer {
            if securityScoped {
                fileURL.stopAccessingSecurityScopedResource()
            }
        }
        let fileData = try Data(contentsOf: fileURL)
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

        func appendField(_ name: String, _ value: String, to body: inout Data) {
            body.append("--\(boundary)\r\n".data(using: .utf8)!)
            body.append("Content-Disposition: form-data; name=\"\(name)\"\r\n\r\n".data(using: .utf8)!)
            body.append("\(value)\r\n".data(using: .utf8)!)
        }

        var body = Data()
        appendField("project_id", "\(projectId)", to: &body)
        if let tags, !tags.isEmpty {
            appendField("tags", tags.joined(separator: ","), to: &body)
        }
        if let locationName, !locationName.isEmpty {
            appendField("location_name", locationName, to: &body)
        }
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"file\"; filename=\"\(fileURL.lastPathComponent)\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: \(mimeType(for: fileURL.pathExtension))\r\n\r\n".data(using: .utf8)!)
        body.append(fileData)
        body.append("\r\n--\(boundary)--\r\n".data(using: .utf8)!)
        request.httpBody = body

        let (data, response) = try await URLSession.shared.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse else {
            throw NetworkError.invalidResponse
        }
        guard (200...299).contains(httpResponse.statusCode) else {
            throw NetworkError.httpError(
                statusCode: httpResponse.statusCode,
                message: String(data: data, encoding: .utf8)
            )
        }
        DebugLogger.shared.log("照片上传响应已收到", type: .success, details: "HTTP \(httpResponse.statusCode)", category: "upload.photo")
        return try APIClient.decodePayload(data, as: UploadResponse.self)
    }

    /// 删除照片
    func deletePhoto(photoId: String) async throws {
        let endpoint = APIEndpoint.custom("/photos/\(photoId)/")
        let _: EmptyResponse = try await apiClient.request(endpoint, method: .delete)
    }

    struct UploadResponse: Codable {
        let status: String
        let documentId: Int
        let filename: String

        enum CodingKeys: String, CodingKey {
            case status, filename
            case documentId = "document_id"
        }
    }

    private func mimeType(for pathExtension: String) -> String {
        switch pathExtension.lowercased() {
        case "jpg", "jpeg": return "image/jpeg"
        case "png": return "image/png"
        case "gif": return "image/gif"
        case "heic": return "image/heic"
        case "webp": return "image/webp"
        default: return "application/octet-stream"
        }
    }

}
