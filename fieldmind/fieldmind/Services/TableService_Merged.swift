//
//  TableService_Merged.swift
//  FieldMind
//
//  深度整合 - 合并自主版本和 Native 版本
//  Generated: Sat Sep 19 11:21:01 CST 2026
//

import Foundation

// ========================================
// 主实现（来自主项目）
// ========================================



class TableService {
    static let shared = TableService()
    private let apiClient = APIClient.shared

    private init() {}

    // MARK: - Models

    struct TableData: Codable, Identifiable {
        let id: Int
        let projectId: Int
        let filename: String
        let format: String
        let fileSize: Int
        let rowCount: Int
        let columnCount: Int
        let columns: [String]
        let preview: [[AnyCodable]]?
        let tags: [String]
        let description: String?
        let uploadedAt: String
        let updatedAt: String

        enum CodingKeys: String, CodingKey {
            case id, filename, format, tags, description, columns, preview
            case projectId = "project_id"
            case fileSize = "file_size"
            case rowCount = "row_count"
            case columnCount = "column_count"
            case uploadedAt = "uploaded_at"
            case updatedAt = "updated_at"
        }
    }

    struct TablesResponse: Codable {
        let tables: [TableData]
        let total: Int

        // 自定义解码，兼容两种响应格式
        init(from decoder: Decoder) throws {
            let container = try decoder.container(keyedBy: CodingKeys.self)

            // 直接尝试解码 tables 和 total
            if let tables = try? container.decode([TableData].self, forKey: .tables),
               let total = try? container.decode(Int.self, forKey: .total) {
                self.tables = tables
                self.total = total
            } else {
                // 如果失败，说明可能被包装了，但 APIClient 应该已经解包
                self.tables = []
                self.total = 0
            }
        }

        enum CodingKeys: String, CodingKey {
            case tables, total
        }
    }

    struct TableStatistics: Codable {
        let totalTables: Int
        let totalRows: Int
        let totalSize: Int
        let formatCounts: [String: Int]

        enum CodingKeys: String, CodingKey {
            case totalTables = "total_tables"
            case totalRows = "total_rows"
            case totalSize = "total_size"
            case formatCounts = "format_counts"
        }
    }

    // MARK: - API Methods

    func listTables(projectId: Int, format: String? = nil) async throws -> TablesResponse {
        var endpoint = APIEndpoint.custom("/v1/projects/\(projectId)/tables")
        if let format = format, format != "全部类型" {
            endpoint = endpoint.with(queryItem: "format", value: format)
        }
        return try await apiClient.request(endpoint, method: .get)
    }

    func getTable(projectId: Int, tableId: Int) async throws -> TableData {
        return try await apiClient.request(.custom("/v1/projects/\(projectId)/tables/\(tableId)"), method: .get)
    }

    func getStatistics(projectId: Int) async throws -> TableStatistics {
        return try await apiClient.request(.custom("/v1/projects/\(projectId)/tables/statistics"), method: .get)
    }

    func deleteTable(projectId: Int, tableId: Int) async throws {
        let _: EmptyResponse = try await apiClient.request(
            .custom("/v1/projects/\(projectId)/tables/\(tableId)"),
            method: .delete
        )
    }

    func uploadTable(projectId: Int, filename: String, format: String, data: Data, tags: [String]?, description: String?) async throws -> TableData {
        let url = URL(string: "\(APIConfig.baseURL)/v1/projects/\(projectId)/tables/upload")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"

        let boundary = UUID().uuidString
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

        var body = Data()

        // Add file data
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"file\"; filename=\"\(filename)\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: application/octet-stream\r\n\r\n".data(using: .utf8)!)
        body.append(data)
        body.append("\r\n".data(using: .utf8)!)

        // Add format
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"format\"\r\n\r\n".data(using: .utf8)!)
        body.append("\(format)\r\n".data(using: .utf8)!)

        // Add tags if provided
        if let tags = tags {
            for tag in tags {
                body.append("--\(boundary)\r\n".data(using: .utf8)!)
                body.append("Content-Disposition: form-data; name=\"tags\"\r\n\r\n".data(using: .utf8)!)
                body.append("\(tag)\r\n".data(using: .utf8)!)
            }
        }

        // Add description if provided
        if let description = description {
            body.append("--\(boundary)\r\n".data(using: .utf8)!)
            body.append("Content-Disposition: form-data; name=\"description\"\r\n\r\n".data(using: .utf8)!)
            body.append("\(description)\r\n".data(using: .utf8)!)
        }

        body.append("--\(boundary)--\r\n".data(using: .utf8)!)

        request.httpBody = body

        let (responseData, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw URLError(.badServerResponse)
        }

        guard httpResponse.statusCode == 200 || httpResponse.statusCode == 201 else {
            throw URLError(.badServerResponse)
        }

        return try APIClient.decodePayload(responseData, as: TableData.self)
    }
}

// ========================================
// Native 版本的扩展功能
// ========================================
// TODO: 手动审查并整合以下功能

/*


class TableService {
    static let shared = TableService()
    private let apiClient = APIClient.shared

    private init() {}

    // MARK: - Models

    struct TableData: Codable, Identifiable {
        let id: Int
        let projectId: Int
        let filename: String
        let format: String
        let fileSize: Int
        let rowCount: Int
        let columnCount: Int
        let columns: [String]
        let preview: [[AnyCodable]]?
        let tags: [String]
        let description: String?
        let uploadedAt: String
        let updatedAt: String

        enum CodingKeys: String, CodingKey {
            case id, filename, format, tags, description, columns, preview
            case projectId = "project_id"
            case fileSize = "file_size"
            case rowCount = "row_count"
            case columnCount = "column_count"
            case uploadedAt = "uploaded_at"
            case updatedAt = "updated_at"
        }
    }

    struct TablesResponse: Codable {
        let tables: [TableData]
        let total: Int

        // 自定义解码，兼容两种响应格式
        init(from decoder: Decoder) throws {
            let container = try decoder.container(keyedBy: CodingKeys.self)

            // 直接尝试解码 tables 和 total
            if let tables = try? container.decode([TableData].self, forKey: .tables),
               let total = try? container.decode(Int.self, forKey: .total) {
                self.tables = tables
                self.total = total
            } else {
                // 如果失败，说明可能被包装了，但 APIClient 应该已经解包
                self.tables = []
                self.total = 0
            }
        }

        enum CodingKeys: String, CodingKey {
            case tables, total
        }
    }

    struct TableStatistics: Codable {
        let totalTables: Int
        let totalRows: Int
        let totalSize: Int
        let formatCounts: [String: Int]

        enum CodingKeys: String, CodingKey {
            case totalTables = "total_tables"
            case totalRows = "total_rows"
            case totalSize = "total_size"
            case formatCounts = "format_counts"
        }
    }

    // MARK: - API Methods

    func listTables(projectId: Int, format: String? = nil) async throws -> TablesResponse {
        var endpoint = APIEndpoint.custom("/v1/projects/\(projectId)/tables")
        if let format = format, format != "全部类型" {
            endpoint = endpoint.with(queryItem: "format", value: format)
        }
        return try await apiClient.request(endpoint, method: .get)
    }

    func getTable(projectId: Int, tableId: Int) async throws -> TableData {
        return try await apiClient.request(.custom("/v1/projects/\(projectId)/tables/\(tableId)"), method: .get)
    }

    func getStatistics(projectId: Int) async throws -> TableStatistics {
        return try await apiClient.request(.custom("/v1/projects/\(projectId)/tables/statistics"), method: .get)
    }

    func deleteTable(projectId: Int, tableId: Int) async throws {
        let _: EmptyResponse = try await apiClient.request(
            .custom("/v1/projects/\(projectId)/tables/\(tableId)"),
            method: .delete
        )
    }

    func uploadTable(projectId: Int, filename: String, format: String, data: Data, tags: [String]?, description: String?) async throws -> TableData {
        let url = URL(string: "\(APIConfig.baseURL)/v1/projects/\(projectId)/tables/upload")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"

        let boundary = UUID().uuidString
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

        var body = Data()

        // Add file data
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"file\"; filename=\"\(filename)\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: application/octet-stream\r\n\r\n".data(using: .utf8)!)
        body.append(data)
        body.append("\r\n".data(using: .utf8)!)

        // Add format
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"format\"\r\n\r\n".data(using: .utf8)!)
        body.append("\(format)\r\n".data(using: .utf8)!)

        // Add tags if provided
        if let tags = tags {
            for tag in tags {
                body.append("--\(boundary)\r\n".data(using: .utf8)!)
                body.append("Content-Disposition: form-data; name=\"tags\"\r\n\r\n".data(using: .utf8)!)
                body.append("\(tag)\r\n".data(using: .utf8)!)
            }
        }

        // Add description if provided
        if let description = description {
            body.append("--\(boundary)\r\n".data(using: .utf8)!)
            body.append("Content-Disposition: form-data; name=\"description\"\r\n\r\n".data(using: .utf8)!)
            body.append("\(description)\r\n".data(using: .utf8)!)
        }

        body.append("--\(boundary)--\r\n".data(using: .utf8)!)

        request.httpBody = body

        let (responseData, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw URLError(.badServerResponse)
        }

        guard httpResponse.statusCode == 200 || httpResponse.statusCode == 201 else {
            throw URLError(.badServerResponse)
        }

        return try APIClient.decodePayload(responseData, as: TableData.self)
    }
}
*/

