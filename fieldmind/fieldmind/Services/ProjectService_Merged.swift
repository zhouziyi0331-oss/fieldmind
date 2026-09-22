//
//  ProjectService_Merged.swift
//  FieldMind
//
//  深度整合 - 合并自主版本和 Native 版本
//  Generated: Sat Sep 19 11:21:00 CST 2026
//

import Foundation

// ========================================
// 主实现（来自主项目）
// ========================================



class ProjectService {
    static let shared = ProjectService()
    private let apiClient = APIClient.shared
    private var baseURL: String { APIConfig.serverURL }

    private init() {}

    // MARK: - Backend Response Models
    struct ProjectListResponse: Codable {
        let data: [BackendProject]
        let total: Int
        let page: Int
        let pageSize: Int
        let hasNext: Bool
        let hasPrev: Bool
    }

    struct BackendProject: Codable {
        let id: Int
        let name: String
        let description: String?
        let documents: Int?
        let contexts: Int?
        let documentCount: Int?
        let contextCount: Int?
        let createdAt: String?
        let updatedAt: String?

        enum CodingKeys: String, CodingKey {
            case id, name, description, documents, contexts
            case documentCount = "document_count"
            case contextCount = "context_count"
            case createdAt = "created_at"
            case updatedAt = "updated_at"
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
        let project: Project
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

    func getProject(projectId: Int) async throws -> Project {
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
        return try decoder.decode(Project.self, from: data)
    }

    func listProjects(includeArchived: Bool = false) async throws -> [Project] {
        let queryItems = [
            URLQueryItem(name: "include_archived", value: includeArchived ? "true" : "false")
        ]

        let endpoint = APIEndpoint.custom("/v1/projects/", queryItems: queryItems)
        do {
            let listResponse: ProjectListResponse = try await apiClient.request(endpoint, method: .get)
            return makeProjects(from: listResponse.data)
        } catch {
            // 兼容尚未重启的旧后端：它可能直接返回完整项目数组。
            let rawProjects: [BackendProject] = try await apiClient.request(endpoint, method: .get)
            return makeProjects(from: rawProjects)
        }
    }

    private func makeProjects(from backendProjects: [BackendProject]) -> [Project] {
        // 将后端简化的项目数据转换为前端完整的 Project 模型
        return backendProjects.map { backendProject in
            Project(
                id: backendProject.id,
                name: backendProject.name,
                description: backendProject.description,
                status: "active",
                documentCount: backendProject.documents ?? backendProject.documentCount ?? 0,
                contextCount: backendProject.contexts ?? backendProject.contextCount ?? 0,
                chatSessionCount: 0,
                entityCount: 0,
                keywordCount: 0,
                isArchived: false,
                createdAt: backendProject.createdAt ?? "",
                updatedAt: backendProject.updatedAt ?? backendProject.createdAt ?? "",
                lastActivityAt: nil,
                settings: nil
            )
        }
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

    func createProject(name: String, description: String?) async throws -> Project {
        let url = URL(string: "\(baseURL)/api/v1/projects/")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        struct CreateProjectRequest: Codable {
            let name: String
            let description: String?
        }

        struct CreateProjectResponse: Codable {
            let id: Int
            let name: String
            let description: String?
            let documents: Int
            let contexts: Int
            let createdAt: String
            let updatedAt: String

            enum CodingKeys: String, CodingKey {
                case id, name, description, documents, contexts
                case createdAt = "created_at"
                case updatedAt = "updated_at"
            }
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
        let createResponse = try decoder.decode(CreateProjectResponse.self, from: data)

        // 转换为完整的Project模型
        return Project(
            id: createResponse.id,
            name: createResponse.name,
            description: createResponse.description,
            status: "active",
            documentCount: createResponse.documents,
            contextCount: createResponse.contexts,
            chatSessionCount: 0,
            entityCount: 0,
            keywordCount: 0,
            isArchived: false,
            createdAt: createResponse.createdAt,
            updatedAt: createResponse.updatedAt,
            lastActivityAt: nil,
            settings: nil
        )
    }

    func updateProject(projectId: Int, name: String?, description: String?, status: String?) async throws -> Project {
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
        return try decoder.decode(Project.self, from: data)
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

// ========================================
// Native 版本的扩展功能
// ========================================
// TODO: 手动审查并整合以下功能

/*


class ProjectService {
    static let shared = ProjectService()
    private let apiClient = APIClient.shared
    private var baseURL: String { APIConfig.serverURL }

    private init() {}

    // MARK: - Backend Response Models
    struct ProjectListResponse: Codable {
        let data: [BackendProject]
        let total: Int
        let page: Int
        let pageSize: Int
        let hasNext: Bool
        let hasPrev: Bool
    }

    struct BackendProject: Codable {
        let id: Int
        let name: String
        let description: String?
        let documents: Int?
        let contexts: Int?
        let documentCount: Int?
        let contextCount: Int?
        let createdAt: String?
        let updatedAt: String?

        enum CodingKeys: String, CodingKey {
            case id, name, description, documents, contexts
            case documentCount = "document_count"
            case contextCount = "context_count"
            case createdAt = "created_at"
            case updatedAt = "updated_at"
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
        let project: Project
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

    func getProject(projectId: Int) async throws -> Project {
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
        return try decoder.decode(Project.self, from: data)
    }

    func listProjects(includeArchived: Bool = false) async throws -> [Project] {
        let queryItems = [
            URLQueryItem(name: "include_archived", value: includeArchived ? "true" : "false")
        ]

        let endpoint = APIEndpoint.custom("/v1/projects/", queryItems: queryItems)
        do {
            let listResponse: ProjectListResponse = try await apiClient.request(endpoint, method: .get)
            return makeProjects(from: listResponse.data)
        } catch {
            // 兼容尚未重启的旧后端：它可能直接返回完整项目数组。
            let rawProjects: [BackendProject] = try await apiClient.request(endpoint, method: .get)
            return makeProjects(from: rawProjects)
        }
    }

    private func makeProjects(from backendProjects: [BackendProject]) -> [Project] {
        // 将后端简化的项目数据转换为前端完整的 Project 模型
        return backendProjects.map { backendProject in
            Project(
                id: backendProject.id,
                name: backendProject.name,
                description: backendProject.description,
                status: "active",
                documentCount: backendProject.documents ?? backendProject.documentCount ?? 0,
                contextCount: backendProject.contexts ?? backendProject.contextCount ?? 0,
                chatSessionCount: 0,
                entityCount: 0,
                keywordCount: 0,
                isArchived: false,
                createdAt: backendProject.createdAt ?? "",
                updatedAt: backendProject.updatedAt ?? backendProject.createdAt ?? "",
                lastActivityAt: nil,
                settings: nil
            )
        }
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

    func createProject(name: String, description: String?) async throws -> Project {
        let url = URL(string: "\(baseURL)/api/v1/projects/")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        struct CreateProjectRequest: Codable {
            let name: String
            let description: String?
        }

        struct CreateProjectResponse: Codable {
            let id: Int
            let name: String
            let description: String?
            let documents: Int
            let contexts: Int
            let createdAt: String
            let updatedAt: String

            enum CodingKeys: String, CodingKey {
                case id, name, description, documents, contexts
                case createdAt = "created_at"
                case updatedAt = "updated_at"
            }
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
        let createResponse = try decoder.decode(CreateProjectResponse.self, from: data)

        // 转换为完整的Project模型
        return Project(
            id: createResponse.id,
            name: createResponse.name,
            description: createResponse.description,
            status: "active",
            documentCount: createResponse.documents,
            contextCount: createResponse.contexts,
            chatSessionCount: 0,
            entityCount: 0,
            keywordCount: 0,
            isArchived: false,
            createdAt: createResponse.createdAt,
            updatedAt: createResponse.updatedAt,
            lastActivityAt: nil,
            settings: nil
        )
    }

    func updateProject(projectId: Int, name: String?, description: String?, status: String?) async throws -> Project {
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
        return try decoder.decode(Project.self, from: data)
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
*/

