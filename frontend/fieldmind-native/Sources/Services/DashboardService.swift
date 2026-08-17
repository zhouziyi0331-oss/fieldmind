import Foundation

// MARK: - Dashboard Response Models

struct DashboardStats: Codable {
    let totalDocuments: Int
    let completedDocuments: Int
    let processingDocuments: Int
    let failedDocuments: Int
    let totalWords: Int
    let totalChunks: Int
    let skillsAnalyzed: Int
    let totalDimensions: Int
    let totalKeywords: Int
    let topKeywords: [KeywordItem]
    let vectorizedDocuments: Int
    let vectorCount: Int
    let chatSessions: Int
    let chatMessages: Int
    let reportsGenerated: Int
    let lastActivity: String?
    let documentsThisWeek: Int
    let projectName: String
    let projectCreated: String
}

struct KeywordItem: Codable {
    let keyword: String
    let weight: Double
}

struct TimelineResponse: Codable {
    let timeline: [TimelinePoint]
    let totalDays: Int
}

struct TimelinePoint: Codable {
    let date: String
    let documents: Int
}

struct ProgressResponse: Codable {
    let uploadProgress: Int
    let processingProgress: Int
    let vectorizationProgress: Int?
    let analysisProgress: Int
    let overallProgress: Int
}

// MARK: - Dashboard Service

class DashboardService {
    private let apiClient = APIClient.shared

    /// 获取项目仪表盘统计数据
    func fetchDashboardStats(projectId: String) async throws -> DashboardStats {
        return try await apiClient.request(
            .dashboardStats(projectId: projectId),
            method: .get
        )
    }

    /// 获取项目时间线数据
    func fetchTimeline(projectId: String, days: Int = 7) async throws -> TimelineResponse {
        let queryItems = [URLQueryItem(name: "days", value: String(days))]
        return try await apiClient.request(
            .dashboardTimeline(projectId: projectId),
            method: .get,
            queryItems: queryItems
        )
    }

    /// 获取项目进度指标
    func fetchProgress(projectId: String) async throws -> ProgressResponse {
        return try await apiClient.request(
            .dashboardProgress(projectId: projectId),
            method: .get
        )
    }
}

// MARK: - API Endpoint Extension

extension APIEndpoint {
    static func dashboardStats(projectId: String) -> APIEndpoint {
        return .custom("/dashboard/stats/\(projectId)")
    }

    static func dashboardTimeline(projectId: String) -> APIEndpoint {
        return .custom("/dashboard/timeline/\(projectId)")
    }

    static func dashboardProgress(projectId: String) -> APIEndpoint {
        return .custom("/dashboard/progress/\(projectId)")
    }
}
