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
    let total: Int
    let days: Int

    // 为了兼容前端代码，提供一个计算属性
    var totalDays: Int { days }
}

struct TimelinePoint: Codable {
    let date: String
    let documents: Int
}

struct ProgressResponse: Codable {
    let total: Int
    let completed: Int
    let processing: Int
    let pending: Int
    let failed: Int
    let progress: Double

    // 为了兼容前端代码，提供计算属性
    var uploadProgress: Int { completed }
    var processingProgress: Int { processing }
    var vectorizationProgress: Int? { pending }
    var analysisProgress: Int { failed }
    var overallProgress: Int { Int(progress * 100) }
}

// MARK: - Dashboard Service

class DashboardService {
    private let apiClient = APIClient.shared

    /// 获取项目仪表盘统计数据
    func fetchDashboardStats(projectId: String) async throws -> DashboardStats {
        // 先获取后端简化的响应
        print("📊 [DashboardService] 开始获取项目 \(projectId) 的统计数据...")

        do {
            let stats: DashboardStats = try await apiClient.request(
                .dashboardStats(projectId: projectId),
                method: .get
            )

            print("✅ [DashboardService] 成功获取后端数据: totalDocs=\(stats.totalDocuments)")
            return stats
        } catch {
            print("❌ [DashboardService] 获取统计数据失败: \(error)")
            throw error
        }
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
