import Foundation

class ProjectService {
    static let shared = ProjectService()
    private let baseURL = "http://localhost:8000"

    private init() {}

    // MARK: - Models

    struct ProjectResponse: Codable {
        let id: Int
        let name: String
        let description: String?
        let status: String
        let createdAt: String
        let updatedAt: String
        let lastActivityAt: String?
        let isArchived: Bool
        let documentCount: Int
        let contextCount: Int
        let chatSessionCount: Int

        enum CodingKeys: String, CodingKey {
            case id, name, description, status
            case createdAt = "created_at"
            case updatedAt = "updated_at"
            case lastActivityAt = "last_activity_at"
            case isArchived = "is_archived"
            case documentCount = "document_count"
            case contextCount = "context_count"
            case chatSessionCount = "chat_session_count"
        }
    }

    struct ProjectDocument: Codable {
        let id: Int
        let projectId: Int
        let filename: String
        let fileType: String
        let status: String
        let createdAt: String

        enum CodingKeys: String, CodingKey {
            case id, filename, status
            case projectId = "project_id"
            case fileType = "file_type"
            case createdAt = "created_at"
        }
    }

    struct ProjectChatSession: Codable {
        let id: Int
        let projectId: Int
        let name: String
        let updatedAt: String

        enum CodingKeys: String, CodingKey {
            case id, name
            case projectId = "project_id"
            case updatedAt = "updated_at"
        }
    }

    struct ProjectDashboardResponse: Codable {
        let project: ProjectResponse
        let recentDocuments: [ProjectDocument]
        let recentChats: [ProjectChatSession]
        let documentCount: Int
        let contextCount: Int
        let memoryCount: Int
        let chatSessionCount: Int

        enum CodingKeys: String, CodingKey {
            case project
            case recentDocuments = "recent_documents"
            case recentChats = "recent_chats"
            case documentCount = "document_count"
            case contextCount = "context_count"
            case memoryCount = "memory_count"
            case chatSessionCount = "chat_session_count"
        }
    }

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

        enum CodingKeys: String, CodingKey {
            case id, name, description, level, keywords
            case projectId = "project_id"
            case parentId = "parent_id"
            case documentIds = "document_ids"
            case createdAt = "created_at"
        }
    }

    // MARK: - API Methods

    func getProjectDashboard(projectId: Int) async throws -> ProjectDashboardResponse {
        let url = URL(string: "\(baseURL)/api/v1/projects/\(projectId)/dashboard")!
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
        return try decoder.decode(ProjectDashboardResponse.self, from: data)
    }

    func getProject(projectId: Int) async throws -> ProjectResponse {
        let url = URL(string: "\(baseURL)/api/v1/projects/\(projectId)")!
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
        return try decoder.decode(ProjectResponse.self, from: data)
    }

    func listProjects(includeArchived: Bool = false) async throws -> [ProjectResponse] {
        var urlComponents = URLComponents(string: "\(baseURL)/api/v1/projects")!
        urlComponents.queryItems = [
            URLQueryItem(name: "include_archived", value: includeArchived ? "true" : "false")
        ]

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
        return try decoder.decode([ProjectResponse].self, from: data)
    }

    func listContexts(projectId: Int) async throws -> [ProjectContext] {
        let url = URL(string: "\(baseURL)/api/v1/projects/\(projectId)/contexts")!
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
        return try decoder.decode([ProjectContext].self, from: data)
    }

    func createProject(name: String, description: String?) async throws -> ProjectResponse {
        let url = URL(string: "\(baseURL)/api/v1/projects")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        struct CreateProjectRequest: Codable {
            let name: String
            let description: String?
        }

        let requestBody = CreateProjectRequest(name: name, description: description)
        request.httpBody = try JSONEncoder().encode(requestBody)

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw URLError(.badServerResponse)
        }

        guard httpResponse.statusCode == 200 || httpResponse.statusCode == 201 else {
            throw URLError(.badServerResponse)
        }

        let decoder = JSONDecoder()
        return try decoder.decode(ProjectResponse.self, from: data)
    }

    func updateProject(projectId: Int, name: String?, description: String?, status: String?) async throws -> ProjectResponse {
        let url = URL(string: "\(baseURL)/api/v1/projects/\(projectId)")!
        var request = URLRequest(url: url)
        request.httpMethod = "PUT"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        struct UpdateProjectRequest: Codable {
            let name: String?
            let description: String?
            let status: String?
        }

        let requestBody = UpdateProjectRequest(name: name, description: description, status: status)
        request.httpBody = try JSONEncoder().encode(requestBody)

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw URLError(.badServerResponse)
        }

        guard httpResponse.statusCode == 200 else {
            throw URLError(.badServerResponse)
        }

        let decoder = JSONDecoder()
        return try decoder.decode(ProjectResponse.self, from: data)
    }

    func deleteProject(projectId: Int) async throws {
        let url = URL(string: "\(baseURL)/api/v1/projects/\(projectId)")!
        var request = URLRequest(url: url)
        request.httpMethod = "DELETE"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let (_, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw URLError(.badServerResponse)
        }

        guard httpResponse.statusCode == 200 || httpResponse.statusCode == 204 else {
            throw URLError(.badServerResponse)
        }
    }
}
