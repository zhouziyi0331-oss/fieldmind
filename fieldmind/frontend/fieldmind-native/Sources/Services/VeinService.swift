import Foundation


class VeinService {
    static let shared = VeinService()
    private var baseURL: String { APIConfig.serverURL }

    private init() {}

    // MARK: - Models

    struct ProjectContext: Codable {
        let id: Int
        let projectId: Int
        let name: String
        let description: String?
        let level: Int
        let parentId: Int?
        let keywords: [String]
        let documentIds: [Int]
        let createdAt: String
        let updatedAt: String

        enum CodingKeys: String, CodingKey {
            case id, name, description, level, keywords
            case projectId = "project_id"
            case parentId = "parent_id"
            case documentIds = "document_ids"
            case createdAt = "created_at"
            case updatedAt = "updated_at"
        }
    }

    struct ContextsResponse: Codable {
        let contexts: [ProjectContext]
        let totalCount: Int

        enum CodingKeys: String, CodingKey {
            case contexts
            case totalCount = "total_count"
        }
    }

    // MARK: - API Methods

    func listContexts(projectId: Int, level: Int? = nil, parentId: Int? = nil) async throws -> [ProjectContext] {
        var urlComponents = URLComponents(string: "\(baseURL)/api/v1/projects/\(projectId)/contexts")!
        var queryItems: [URLQueryItem] = []

        if let level = level {
            queryItems.append(URLQueryItem(name: "level", value: "\(level)"))
        }
        if let parentId = parentId {
            queryItems.append(URLQueryItem(name: "parent_id", value: "\(parentId)"))
        }

        if !queryItems.isEmpty {
            urlComponents.queryItems = queryItems
        }

        var request = URLRequest(url: urlComponents.url!)
        request.httpMethod = "GET"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw URLError(.badServerResponse)
        }

        guard httpResponse.statusCode == 200 else {
            throw URLError(.badServerResponse)
        }

        let decoder = JSONDecoder()
        return try decoder.decode([ProjectContext].self, from: data)
    }

    func getContext(projectId: Int, contextId: Int) async throws -> ProjectContext {
        let url = URL(string: "\(baseURL)/api/v1/projects/\(projectId)/contexts/\(contextId)")!
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw URLError(.badServerResponse)
        }

        guard httpResponse.statusCode == 200 else {
            throw URLError(.badServerResponse)
        }

        let decoder = JSONDecoder()
        return try decoder.decode(ProjectContext.self, from: data)
    }
}
