import Foundation


class MemoryService {
    static let shared = MemoryService()
    private var baseURL: String { APIConfig.serverURL }

    private init() {}

    // MARK: - Models

    struct MemoryCreateRequest: Codable {
        let projectId: Int
        let memoryType: String
        let content: String
        let summary: String?
        let sourceType: String?
        let sourceId: String?
        let keywords: [String]?
        let importanceScore: Double?

        enum CodingKeys: String, CodingKey {
            case projectId = "project_id"
            case memoryType = "memory_type"
            case content
            case summary
            case sourceType = "source_type"
            case sourceId = "source_id"
            case keywords
            case importanceScore = "importance_score"
        }
    }

    struct MemoryResponse: Codable, Identifiable {
        let id: Int
        let projectId: Int
        let memoryType: String
        let content: String
        let summary: String?
        let sourceType: String?
        let relevanceScore: Int
        let accessCount: Int
        let createdAt: String

        enum CodingKeys: String, CodingKey {
            case id
            case projectId = "project_id"
            case memoryType = "memory_type"
            case content
            case summary
            case sourceType = "source_type"
            case relevanceScore = "relevance_score"
            case accessCount = "access_count"
            case createdAt = "created_at"
        }
    }

    struct MemoryStatsResponse: Codable {
        let projectId: Int
        let totalMemories: Int
        let byType: [String: TypeStats]
        let totalAccessCount: Int
        let topMemories: [TopMemory]?

        struct TypeStats: Codable {
            let count: Int
            let totalAccess: Int

            enum CodingKeys: String, CodingKey {
                case count
                case totalAccess = "total_access"
            }
        }

        struct TopMemory: Codable {
            let id: Int
            let summary: String
            let accessCount: Int
            let memoryType: String

            enum CodingKeys: String, CodingKey {
                case id
                case summary
                case accessCount = "access_count"
                case memoryType = "memory_type"
            }
        }

        enum CodingKeys: String, CodingKey {
            case projectId = "project_id"
            case totalMemories = "total_memories"
            case byType = "by_type"
            case totalAccessCount = "total_access_count"
            case topMemories = "top_memories"
        }

        // Computed properties for convenience
        var shortTermCount: Int {
            byType["short_term"]?.count ?? 0
        }

        var midTermCount: Int {
            byType["mid_term"]?.count ?? 0
        }

        var longTermCount: Int {
            byType["long_term"]?.count ?? 0
        }

        var bySourceType: [String: Int] {
            // This would need to be computed from individual memories
            // For now return empty, can be enhanced later
            [:]
        }
    }

    // MARK: - API Methods

    func createMemory(
        projectId: Int,
        memoryType: String,
        content: String,
        summary: String? = nil,
        sourceType: String? = nil,
        keywords: [String]? = nil,
        importanceScore: Double? = nil
    ) async throws -> MemoryResponse {
        let url = URL(string: "\(baseURL)/api/memory/create")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let requestBody = MemoryCreateRequest(
            projectId: projectId,
            memoryType: memoryType,
            content: content,
            summary: summary,
            sourceType: sourceType,
            sourceId: nil,
            keywords: keywords,
            importanceScore: importanceScore
        )
        request.httpBody = try JSONEncoder().encode(requestBody)

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw NSError(domain: "MemoryService", code: -1, userInfo: [NSLocalizedDescriptionKey: "Invalid response"])
        }

        guard httpResponse.statusCode == 200 else {
            throw NSError(domain: "MemoryService", code: httpResponse.statusCode,
                         userInfo: [NSLocalizedDescriptionKey: "HTTP \(httpResponse.statusCode)"])
        }

        return try JSONDecoder().decode(MemoryResponse.self, from: data)
    }

    func getProjectMemories(projectId: Int) async throws -> [MemoryResponse] {
        let url = URL(string: "\(baseURL)/api/memory/project/\(projectId)")!
        var request = URLRequest(url: url)
        request.httpMethod = "GET"

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw NSError(domain: "MemoryService", code: -1, userInfo: [NSLocalizedDescriptionKey: "Invalid response"])
        }

        guard httpResponse.statusCode == 200 else {
            throw NSError(domain: "MemoryService", code: httpResponse.statusCode,
                         userInfo: [NSLocalizedDescriptionKey: "HTTP \(httpResponse.statusCode)"])
        }

        return try JSONDecoder().decode([MemoryResponse].self, from: data)
    }

    func getMemory(memoryId: Int) async throws -> MemoryResponse {
        let url = URL(string: "\(baseURL)/api/memory/\(memoryId)")!
        var request = URLRequest(url: url)
        request.httpMethod = "GET"

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw NSError(domain: "MemoryService", code: -1, userInfo: [NSLocalizedDescriptionKey: "Invalid response"])
        }

        guard httpResponse.statusCode == 200 else {
            throw NSError(domain: "MemoryService", code: httpResponse.statusCode,
                         userInfo: [NSLocalizedDescriptionKey: "HTTP \(httpResponse.statusCode)"])
        }

        return try JSONDecoder().decode(MemoryResponse.self, from: data)
    }

    func getMemoryStats(projectId: Int) async throws -> MemoryStatsResponse {
        let url = URL(string: "\(baseURL)/api/memory/stats/\(projectId)")!
        var request = URLRequest(url: url)
        request.httpMethod = "GET"

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw NSError(domain: "MemoryService", code: -1, userInfo: [NSLocalizedDescriptionKey: "Invalid response"])
        }

        guard httpResponse.statusCode == 200 else {
            throw NSError(domain: "MemoryService", code: httpResponse.statusCode,
                         userInfo: [NSLocalizedDescriptionKey: "HTTP \(httpResponse.statusCode)"])
        }

        return try JSONDecoder().decode(MemoryStatsResponse.self, from: data)
    }

    func autoPromoteMemories(projectId: Int) async throws {
        let url = URL(string: "\(baseURL)/api/memory/auto-promote/\(projectId)")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"

        let (_, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw NSError(domain: "MemoryService", code: -1, userInfo: [NSLocalizedDescriptionKey: "Invalid response"])
        }

        guard httpResponse.statusCode == 200 else {
            throw NSError(domain: "MemoryService", code: httpResponse.statusCode,
                         userInfo: [NSLocalizedDescriptionKey: "HTTP \(httpResponse.statusCode)"])
        }
    }

    func cleanupMemories(projectId: Int) async throws {
        let url = URL(string: "\(baseURL)/api/memory/cleanup/\(projectId)")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"

        let (_, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw NSError(domain: "MemoryService", code: -1, userInfo: [NSLocalizedDescriptionKey: "Invalid response"])
        }

        guard httpResponse.statusCode == 200 else {
            throw NSError(domain: "MemoryService", code: httpResponse.statusCode,
                         userInfo: [NSLocalizedDescriptionKey: "HTTP \(httpResponse.statusCode)"])
        }
    }
}
