import Foundation

/// CitationService - 文献引用管理服务
class CitationService {
    static let shared = CitationService()
    private let apiClient = APIClient.shared

    private init() {}

    // MARK: - Response Models

    struct CitationResponse: Codable, Identifiable {
        let id: Int
        let title: String
        let authors: [String]
        let year: String?
        let publication: String?
        let publisher: String?
        let doi: String?
        let isbn: String?
        let url: String?
        let abstract: String?
        let notes: String?
        let citationType: String
        let tags: [String]
        let projectId: Int
        let citedCount: Int
        let addedAt: Date
        let updatedAt: Date
        let bibtex: String?

        enum CodingKeys: String, CodingKey {
            case id, title, authors, year, publication, publisher, doi, isbn, url, abstract, notes, tags, bibtex
            case citationType = "citation_type"
            case projectId = "project_id"
            case citedCount = "cited_count"
            case addedAt = "added_at"
            case updatedAt = "updated_at"
        }
    }

    struct CitationListResponse: Codable {
        let citations: [CitationResponse]
        let total: Int
        let page: Int
        let pageSize: Int

        enum CodingKeys: String, CodingKey {
            case citations, total, page
            case pageSize = "page_size"
        }
    }

    struct CitationStatsResponse: Codable {
        let totalCitations: Int
        let byType: [String: Int]
        let byYear: [String: Int]
        let topTags: [TagStat]
        let recentAdditions: Int

        enum CodingKeys: String, CodingKey {
            case totalCitations = "total_citations"
            case byType = "by_type"
            case byYear = "by_year"
            case topTags = "top_tags"
            case recentAdditions = "recent_additions"
        }

        struct TagStat: Codable {
            let tag: String
            let count: Int
        }
    }

    struct CitationCreateRequest: Codable {
        let title: String
        let authors: [String]
        let year: String?
        let publication: String?
        let publisher: String?
        let doi: String?
        let isbn: String?
        let url: String?
        let abstract: String?
        let notes: String?
        let citationType: String
        let tags: [String]
        let projectId: Int
        let bibtex: String?
        let extraMetadata: [String: String]

        enum CodingKeys: String, CodingKey {
            case title, authors, year, publication, publisher, doi, isbn, url, abstract, notes, tags, bibtex
            case citationType = "citation_type"
            case projectId = "project_id"
            case extraMetadata = "extra_metadata"
        }
    }

    // MARK: - API Methods

    /// 获取引用列表
    func getCitations(
        projectId: Int,
        search: String? = nil,
        citationType: String? = nil,
        tags: String? = nil,
        sortBy: String = "added_at",
        sortOrder: String = "desc",
        page: Int = 1,
        pageSize: Int = 20
    ) async throws -> CitationListResponse {
        var endpoint = APIEndpoint.custom("/citations")
            .with(queryItem: "project_id", value: "\(projectId)")
            .with(queryItem: "sort_by", value: sortBy)
            .with(queryItem: "sort_order", value: sortOrder)
            .with(queryItem: "page", value: "\(page)")
            .with(queryItem: "page_size", value: "\(pageSize)")

        if let search = search, !search.isEmpty {
            endpoint = endpoint.with(queryItem: "search", value: search)
        }
        if let citationType = citationType, citationType != "全部类型" {
            endpoint = endpoint.with(queryItem: "citation_type", value: citationType)
        }
        if let tags = tags, !tags.isEmpty {
            endpoint = endpoint.with(queryItem: "tags", value: tags)
        }

        return try await apiClient.request(endpoint, method: .get)
    }

    /// 获取单个引用详情
    func getCitation(citationId: Int) async throws -> CitationResponse {
        let endpoint = APIEndpoint.custom("/citations/\(citationId)")
        return try await apiClient.request(endpoint, method: .get)
    }

    /// 创建引用
    func createCitation(request: CitationCreateRequest) async throws -> CitationResponse {
        let endpoint = APIEndpoint.custom("/citations")
        return try await apiClient.request(endpoint, method: .post, body: request)
    }

    /// 更新引用
    func updateCitation(citationId: Int, request: CitationCreateRequest) async throws -> CitationResponse {
        let endpoint = APIEndpoint.custom("/citations/\(citationId)")
        return try await apiClient.request(endpoint, method: .put, body: request)
    }

    /// 删除引用
    func deleteCitation(citationId: Int) async throws {
        let endpoint = APIEndpoint.custom("/citations/\(citationId)")
        let _: EmptyResponse = try await apiClient.request(endpoint, method: .delete)
    }

    /// 获取引用统计
    func getStats(projectId: Int) async throws -> CitationStatsResponse {
        let endpoint = APIEndpoint.custom("/citations/stats/\(projectId)")
        return try await apiClient.request(endpoint, method: .get)
    }

    /// 批量创建引用
    func batchCreateCitations(citations: [CitationCreateRequest]) async throws -> BatchCreateResponse {
        let endpoint = APIEndpoint.custom("/citations/batch")
        return try await apiClient.request(endpoint, method: .post, body: citations)
    }

    struct BatchCreateResponse: Codable {
        let createdCount: Int
        let createdIds: [Int]
        let errors: [BatchError]

        enum CodingKeys: String, CodingKey {
            case createdCount = "created_count"
            case createdIds = "created_ids"
            case errors
        }

        struct BatchError: Codable {
            let index: Int
            let error: String
        }
    }
}
