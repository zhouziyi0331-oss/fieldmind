import Foundation

// MARK: - Response Models

struct TimelineEventResponse: Codable {
    let id: String
    let date: String
    let title: String
    let description: String?
    let category: String?
    let documentIds: [Int]?
    let source: String?
    let confidence: Double?
    let tags: [String]?
    let createdAt: String

    enum CodingKeys: String, CodingKey {
        case id, date, title, description, category, source, confidence, tags
        case documentIds = "document_ids"
        case createdAt = "created_at"
    }
}

struct TimelineEventsResponse: Codable {
    let events: [TimelineEventResponse]
    let total: Int
}

struct TimelineStatsResponse: Codable {
    let totalEvents: Int
    let dateRange: DateRange?
    let categories: [String: Int]

    struct DateRange: Codable {
        let start: String
        let end: String
    }

    enum CodingKeys: String, CodingKey {
        case totalEvents = "total_events"
        case dateRange = "date_range"
        case categories
    }
}

struct BuildTimelineRequest: Codable {
    let projectId: Int
    let documentIds: [Int]?
    let forceRebuild: Bool

    enum CodingKeys: String, CodingKey {
        case projectId = "project_id"
        case documentIds = "document_ids"
        case forceRebuild = "force_rebuild"
    }
}

struct BuildTimelineResponse: Codable {
    let status: String
    let message: String
    let stats: BuildStats

    struct BuildStats: Codable {
        let documentsProcessed: Int
        let eventsCreated: Int

        enum CodingKeys: String, CodingKey {
            case documentsProcessed = "documents_processed"
            case eventsCreated = "events_created"
        }
    }
}

// MARK: - Timeline Service

class TimelineService {
    static let shared = TimelineService()
    private let apiClient = APIClient.shared

    private init() {}

    // MARK: - Build Timeline

    /// 从文档构建时间线（提取时间事件）
    func buildTimeline(projectId: Int, documentIds: [Int]? = nil, forceRebuild: Bool = false) async throws -> BuildTimelineResponse {
        let request = BuildTimelineRequest(
            projectId: projectId,
            documentIds: documentIds,
            forceRebuild: forceRebuild
        )

        return try await apiClient.request(
            .buildTimeline,
            method: .post,
            body: request
        )
    }

    // MARK: - Get Events

    /// 获取时间线事件列表
    func getTimelineEvents(
        projectId: Int,
        startDate: String? = nil,
        endDate: String? = nil,
        category: String? = nil,
        limit: Int = 100
    ) async throws -> TimelineEventsResponse {
        var queryItems: [String: String] = ["project_id": "\(projectId)", "limit": "\(limit)"]

        if let startDate = startDate {
            queryItems["start_date"] = startDate
        }
        if let endDate = endDate {
            queryItems["end_date"] = endDate
        }
        if let category = category {
            queryItems["category"] = category
        }

        return try await apiClient.request(
            .timelineEvents(queryItems: queryItems),
            method: .get
        )
    }

    // MARK: - Get Stats

    /// 获取时间线统计信息
    func getTimelineStats(projectId: Int) async throws -> TimelineStatsResponse {
        return try await apiClient.request(
            .timelineStats(projectId: projectId),
            method: .get
        )
    }

    // MARK: - Legacy API (不持久化)

    /// 获取项目时间线（旧API，实时提取）
    func getProjectTimeline(projectId: Int) async throws -> ProjectTimelineResponse {
        return try await apiClient.request(
            .projectTimeline(projectId: projectId),
            method: .get
        )
    }

    /// 获取分组的时间线数据
    func getGroupedTimeline(projectId: Int, groupBy: String = "year") async throws -> GroupedTimelineResponse {
        return try await apiClient.request(
            .groupedTimeline(projectId: projectId, groupBy: groupBy),
            method: .get
        )
    }
}

// MARK: - Legacy Response Models

struct ProjectTimelineResponse: Codable {
    let events: [LegacyTimelineEvent]
    let eventsByYear: [String: [LegacyTimelineEvent]]
    let statistics: TimelineStatistics
    let message: String?

    enum CodingKeys: String, CodingKey {
        case events
        case eventsByYear = "events_by_year"
        case statistics
        case message
    }
}

struct LegacyTimelineEvent: Codable {
    let date: String
    let dateString: String
    let description: String
    let documentId: Int
    let documentName: String
    let timestamp: Int

    enum CodingKeys: String, CodingKey {
        case date
        case dateString = "date_string"
        case description
        case documentId = "document_id"
        case documentName = "document_name"
        case timestamp
    }
}

struct TimelineStatistics: Codable {
    let totalEvents: Int
    let dateRange: DateRangeInfo?

    struct DateRangeInfo: Codable {
        let start: String?
        let end: String?
    }

    enum CodingKeys: String, CodingKey {
        case totalEvents = "total_events"
        case dateRange = "date_range"
    }
}

struct GroupedTimelineResponse: Codable {
    let groups: [TimelineGroup]
    let statistics: TimelineStatistics
}

struct TimelineGroup: Codable {
    let key: String
    let events: [LegacyTimelineEvent]
    let count: Int
}

// MARK: - API Endpoint Extension

extension APIEndpoint {
    static let buildTimeline = APIEndpoint.custom("/timeline/build")

    static func timelineEvents(queryItems: [String: String]) -> APIEndpoint {
        let urlQueryItems = queryItems.map { URLQueryItem(name: $0.key, value: $0.value) }
        return APIEndpoint.custom("/timeline/events", queryItems: urlQueryItems)
    }

    static func timelineStats(projectId: Int) -> APIEndpoint {
        return APIEndpoint.custom("/timeline/stats", queryItems: [
            URLQueryItem(name: "project_id", value: "\(projectId)")
        ])
    }

    static func projectTimeline(projectId: Int) -> APIEndpoint {
        return APIEndpoint.custom("/timeline/projects/\(projectId)/events")
    }

    static func groupedTimeline(projectId: Int, groupBy: String) -> APIEndpoint {
        return APIEndpoint.custom("/timeline/projects/\(projectId)/events/grouped", queryItems: [
            URLQueryItem(name: "group_by", value: groupBy)
        ])
    }
}
