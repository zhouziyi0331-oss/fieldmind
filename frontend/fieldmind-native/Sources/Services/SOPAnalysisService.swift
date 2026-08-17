import Foundation

class SOPAnalysisService {
    static let shared = SOPAnalysisService()
    private let baseURL = "http://localhost:8000"

    private init() {}

    // MARK: - Models

    struct SOPAnalysis: Codable, Identifiable {
        let id: Int
        let projectId: Int
        let sopId: Int
        let sopTitle: String
        let category: String
        let overallScore: Double
        let metrics: SOPMetrics
        let issues: [SOPIssue]
        let recommendations: [String]
        let timeRange: String
        let analyzedAt: String

        enum CodingKeys: String, CodingKey {
            case id, category, metrics, issues, recommendations
            case projectId = "project_id"
            case sopId = "sop_id"
            case sopTitle = "sop_title"
            case overallScore = "overall_score"
            case timeRange = "time_range"
            case analyzedAt = "analyzed_at"
        }
    }

    struct SOPMetrics: Codable {
        let totalUsage: Int
        let successRate: Double
        let avgDuration: Double
        let completionRate: Double
        let errorRate: Double

        enum CodingKeys: String, CodingKey {
            case successRate = "success_rate"
            case avgDuration = "avg_duration"
            case completionRate = "completion_rate"
            case errorRate = "error_rate"
            case totalUsage = "total_usage"
        }
    }

    struct SOPIssue: Codable, Identifiable {
        let id: Int
        let type: String
        let severity: String
        let description: String
        let stepNumber: Int?
        let occurrenceCount: Int

        enum CodingKeys: String, CodingKey {
            case id, type, severity, description
            case stepNumber = "step_number"
            case occurrenceCount = "occurrence_count"
        }
    }

    struct AnalysisResponse: Codable {
        let analyses: [SOPAnalysis]
        let total: Int
    }

    struct SOPSummary: Codable {
        let totalSOPs: Int
        let avgScore: Double
        let totalUsage: Int
        let avgSuccessRate: Double

        enum CodingKeys: String, CodingKey {
            case totalSOPs = "total_sops"
            case avgScore = "avg_score"
            case totalUsage = "total_usage"
            case avgSuccessRate = "avg_success_rate"
        }
    }

    // MARK: - API Methods

    func listAnalyses(projectId: Int, category: String? = nil, timeRange: String? = nil) async throws -> AnalysisResponse {
        var components = URLComponents(string: "\(baseURL)/api/v1/projects/\(projectId)/sop-analysis")!
        var queryItems: [URLQueryItem] = []

        if let category = category, category != "全部分类" {
            queryItems.append(URLQueryItem(name: "category", value: category))
        }
        if let timeRange = timeRange, timeRange != "全部" {
            queryItems.append(URLQueryItem(name: "time_range", value: timeRange))
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
        return try decoder.decode(AnalysisResponse.self, from: data)
    }

    func getAnalysis(projectId: Int, analysisId: Int) async throws -> SOPAnalysis {
        let url = URL(string: "\(baseURL)/api/v1/projects/\(projectId)/sop-analysis/\(analysisId)")!
        let (data, response) = try await URLSession.shared.data(from: url)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw URLError(.badServerResponse)
        }

        guard httpResponse.statusCode == 200 else {
            throw URLError(.badServerResponse)
        }

        let decoder = JSONDecoder()
        return try decoder.decode(SOPAnalysis.self, from: data)
    }

    func getSummary(projectId: Int) async throws -> SOPSummary {
        let url = URL(string: "\(baseURL)/api/v1/projects/\(projectId)/sop-analysis/summary")!
        let (data, response) = try await URLSession.shared.data(from: url)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw URLError(.badServerResponse)
        }

        guard httpResponse.statusCode == 200 else {
            throw URLError(.badServerResponse)
        }

        let decoder = JSONDecoder()
        return try decoder.decode(SOPSummary.self, from: data)
    }

    func generateAnalysis(projectId: Int, sopId: Int, timeRange: String) async throws -> SOPAnalysis {
        let url = URL(string: "\(baseURL)/api/v1/projects/\(projectId)/sop-analysis/generate")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body: [String: Any] = [
            "sop_id": sopId,
            "time_range": timeRange
        ]

        request.httpBody = try JSONSerialization.data(withJSONObject: body)

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw URLError(.badServerResponse)
        }

        guard httpResponse.statusCode == 200 || httpResponse.statusCode == 201 else {
            throw URLError(.badServerResponse)
        }

        let decoder = JSONDecoder()
        return try decoder.decode(SOPAnalysis.self, from: data)
    }
}
