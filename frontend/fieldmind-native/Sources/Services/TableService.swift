import Foundation

class TableService {
    static let shared = TableService()
    private let baseURL = "http://localhost:8000"

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
        let preview: [[String]]?
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
        var components = URLComponents(string: "\(baseURL)/api/v1/projects/\(projectId)/tables")!
        var queryItems: [URLQueryItem] = []

        if let format = format, format != "全部类型" {
            queryItems.append(URLQueryItem(name: "format", value: format))
        }

        if !queryItems.isEmpty {
            components.queryItems = queryItems
        }

        let url = components.url!
        let (data, response) = try await URLSession.shared.data(from: url)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw URLError(.badServerResponse)
        }

        guard httpResponse.statusCode == 200 else {
            throw URLError(.badServerResponse)
        }

        let decoder = JSONDecoder()
        return try decoder.decode(TablesResponse.self, from: data)
    }

    func getTable(projectId: Int, tableId: Int) async throws -> TableData {
        let url = URL(string: "\(baseURL)/api/v1/projects/\(projectId)/tables/\(tableId)")!
        let (data, response) = try await URLSession.shared.data(from: url)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw URLError(.badServerResponse)
        }

        guard httpResponse.statusCode == 200 else {
            throw URLError(.badServerResponse)
        }

        let decoder = JSONDecoder()
        return try decoder.decode(TableData.self, from: data)
    }

    func getStatistics(projectId: Int) async throws -> TableStatistics {
        let url = URL(string: "\(baseURL)/api/v1/projects/\(projectId)/tables/statistics")!
        let (data, response) = try await URLSession.shared.data(from: url)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw URLError(.badServerResponse)
        }

        guard httpResponse.statusCode == 200 else {
            throw URLError(.badServerResponse)
        }

        let decoder = JSONDecoder()
        return try decoder.decode(TableStatistics.self, from: data)
    }

    func deleteTable(projectId: Int, tableId: Int) async throws {
        let url = URL(string: "\(baseURL)/api/v1/projects/\(projectId)/tables/\(tableId)")!
        var request = URLRequest(url: url)
        request.httpMethod = "DELETE"

        let (_, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw URLError(.badServerResponse)
        }

        guard httpResponse.statusCode == 200 || httpResponse.statusCode == 204 else {
            throw URLError(.badServerResponse)
        }
    }

    func uploadTable(projectId: Int, filename: String, format: String, data: Data, tags: [String]?, description: String?) async throws -> TableData {
        let url = URL(string: "\(baseURL)/api/v1/projects/\(projectId)/tables/upload")!
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

        let decoder = JSONDecoder()
        return try decoder.decode(TableData.self, from: responseData)
    }
}
