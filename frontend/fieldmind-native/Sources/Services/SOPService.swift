import Foundation

class SOPService {
    static let shared = SOPService()
    private let baseURL = "http://localhost:8000"
    private init() {}

    // MARK: - Models

    struct SOP: Codable, Identifiable {
        let id: Int
        let projectId: Int
        let title: String
        let category: String
        let status: String
        let author: String
        let version: String
        let lastModified: String
        let usedCount: Int
        let successRate: Double
        let description: String
        let tags: [String]
        let steps: [SOPStep]
    }

    struct SOPStep: Codable, Identifiable {
        let id: Int
        let stepNumber: Int
        let title: String
        let description: String
        let estimatedTime: Int?
        let required: Bool
    }

    struct SOPStatistics: Codable {
        let totalSOPs: Int
        let publishedSOPs: Int
        let draftSOPs: Int
        let totalUsage: Int
        let avgSuccessRate: Double
    }

    struct SOPsResponse: Codable {
        let sops: [SOP]
        let total: Int
        let statistics: SOPStatistics
    }

    struct SOPUsageLog: Codable, Identifiable {
        let id: Int
        let sopId: Int
        let userId: String
        let executedAt: String
        let success: Bool
        let duration: Int
        let notes: String?
    }

    // MARK: - API Methods

    func listSOPs(projectId: Int, category: String?, status: String?, search: String?) async throws -> SOPsResponse {
        var components = URLComponents(string: "\(baseURL)/api/v1/projects/\(projectId)/sops")!
        var queryItems: [URLQueryItem] = []

        if let category = category, category != "全部分类" {
            queryItems.append(URLQueryItem(name: "category", value: category))
        }
        if let status = status, status != "全部状态" {
            queryItems.append(URLQueryItem(name: "status", value: status))
        }
        if let search = search, !search.isEmpty {
            queryItems.append(URLQueryItem(name: "search", value: search))
        }

        if !queryItems.isEmpty {
            components.queryItems = queryItems
        }

        let request = URLRequest(url: components.url!)
        let (data, _) = try await URLSession.shared.data(for: request)
        return try JSONDecoder().decode(SOPsResponse.self, from: data)
    }

    func getSOPDetail(projectId: Int, sopId: Int) async throws -> SOP {
        let url = URL(string: "\(baseURL)/api/v1/projects/\(projectId)/sops/\(sopId)")!
        let (data, _) = try await URLSession.shared.data(from: url)
        return try JSONDecoder().decode(SOP.self, from: data)
    }

    func createSOP(projectId: Int, title: String, category: String, description: String, steps: [SOPStep], tags: [String]) async throws -> SOP {
        let url = URL(string: "\(baseURL)/api/v1/projects/\(projectId)/sops")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body: [String: Any] = [
            "title": title,
            "category": category,
            "description": description,
            "steps": steps.map { step in
                [
                    "stepNumber": step.stepNumber,
                    "title": step.title,
                    "description": step.description,
                    "estimatedTime": step.estimatedTime as Any,
                    "required": step.required
                ]
            },
            "tags": tags
        ]
        request.httpBody = try JSONSerialization.data(withJSONObject: body)

        let (data, _) = try await URLSession.shared.data(for: request)
        return try JSONDecoder().decode(SOP.self, from: data)
    }

    func updateSOPStatus(projectId: Int, sopId: Int, status: String) async throws -> SOP {
        let url = URL(string: "\(baseURL)/api/v1/projects/\(projectId)/sops/\(sopId)/status")!
        var request = URLRequest(url: url)
        request.httpMethod = "PUT"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body = ["status": status]
        request.httpBody = try JSONSerialization.data(withJSONObject: body)

        let (data, _) = try await URLSession.shared.data(for: request)
        return try JSONDecoder().decode(SOP.self, from: data)
    }

    func deleteSOP(projectId: Int, sopId: Int) async throws {
        let url = URL(string: "\(baseURL)/api/v1/projects/\(projectId)/sops/\(sopId)")!
        var request = URLRequest(url: url)
        request.httpMethod = "DELETE"
        let (_, _) = try await URLSession.shared.data(for: request)
    }

    func getSOPUsageLogs(projectId: Int, sopId: Int, limit: Int?) async throws -> [SOPUsageLog] {
        var components = URLComponents(string: "\(baseURL)/api/v1/projects/\(projectId)/sops/\(sopId)/usage")!
        if let limit = limit {
            components.queryItems = [URLQueryItem(name: "limit", value: "\(limit)")]
        }

        let request = URLRequest(url: components.url!)
        let (data, _) = try await URLSession.shared.data(for: request)
        let response = try JSONDecoder().decode([String: [SOPUsageLog]].self, from: data)
        return response["logs"] ?? []
    }
}
