import Foundation


class KeywordSearchService {
    static let shared = KeywordSearchService()
    private var baseURL: String { APIConfig.serverURL }

    private init() {}

    // MARK: - Models

    struct SearchRequest: Codable {
        let keyword: String
        let includeVideos: Bool
        let includeAudios: Bool
        let includeDocuments: Bool

        enum CodingKeys: String, CodingKey {
            case keyword
            case includeVideos = "include_videos"
            case includeAudios = "include_audios"
            case includeDocuments = "include_documents"
        }
    }

    struct VideoTimestamp: Codable, Identifiable {
        let videoId: Int
        let filename: String
        let timestamp: String
        let timestampSeconds: Double
        let context: String
        let matchPosition: Int

        var id: Int { videoId }

        enum CodingKeys: String, CodingKey {
            case videoId = "video_id"
            case filename
            case timestamp
            case timestampSeconds = "timestamp_seconds"
            case context
            case matchPosition = "match_position"
        }
    }

    struct AudioTimestamp: Codable, Identifiable {
        let audioId: Int
        let filename: String
        let timestamp: String
        let timestampSeconds: Double
        let context: String
        let matchPosition: Int

        var id: Int { audioId }

        enum CodingKeys: String, CodingKey {
            case audioId = "audio_id"
            case filename
            case timestamp
            case timestampSeconds = "timestamp_seconds"
            case context
            case matchPosition = "match_position"
        }
    }

    struct DocumentMatch: Codable, Identifiable {
        let docId: Int
        let filename: String
        let matches: [[String: String]]  // Changed from [String: Any] to match JSON

        var id: Int { docId }

        enum CodingKeys: String, CodingKey {
            case docId = "doc_id"
            case filename
            case matches
        }
    }

    struct SearchResponse: Codable {
        let keyword: String
        let totalMentions: Int
        let documents: [DocumentMatch]
        let videoTimestamps: [VideoTimestamp]
        let audioTimestamps: [AudioTimestamp]
        let timeline: [[String: String]]  // Simplified timeline structure
        let relatedKeywords: [String]

        enum CodingKeys: String, CodingKey {
            case keyword
            case totalMentions = "total_mentions"
            case documents
            case videoTimestamps = "video_timestamps"
            case audioTimestamps = "audio_timestamps"
            case timeline
            case relatedKeywords = "related_keywords"
        }
    }

    struct TopKeywordsResponse: Codable {
        let projectId: Int
        let keywords: [KeywordInfo]

        enum CodingKeys: String, CodingKey {
            case projectId = "project_id"
            case keywords
        }
    }

    struct KeywordInfo: Codable, Identifiable {
        let keyword: String
        let count: Int

        var id: String { keyword }
    }

    struct KeywordTimelineResponse: Codable {
        let keyword: String
        let timeline: [[String: String]]
    }

    // MARK: - API Methods

    func searchKeyword(
        projectId: Int,
        keyword: String,
        includeVideos: Bool = true,
        includeAudios: Bool = true,
        includeDocuments: Bool = true
    ) async throws -> SearchResponse {
        let url = URL(string: "\(baseURL)/api/keyword-search/projects/\(projectId)/search")!

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let searchRequest = SearchRequest(
            keyword: keyword,
            includeVideos: includeVideos,
            includeAudios: includeAudios,
            includeDocuments: includeDocuments
        )
        request.httpBody = try JSONEncoder().encode(searchRequest)

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw URLError(.badServerResponse)
        }

        guard httpResponse.statusCode == 200 else {
            throw URLError(.badServerResponse)
        }

        return try JSONDecoder().decode(SearchResponse.self, from: data)
    }

    func getTopKeywords(projectId: Int, limit: Int = 50) async throws -> TopKeywordsResponse {
        let url = URL(string: "\(baseURL)/api/keyword-search/projects/\(projectId)/keywords/top?limit=\(limit)")!

        var request = URLRequest(url: url)
        request.httpMethod = "GET"

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw URLError(.badServerResponse)
        }

        guard httpResponse.statusCode == 200 else {
            throw URLError(.badServerResponse)
        }

        return try JSONDecoder().decode(TopKeywordsResponse.self, from: data)
    }

    func getKeywordTimeline(projectId: Int, keyword: String) async throws -> KeywordTimelineResponse {
        let encodedKeyword = keyword.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? keyword
        let url = URL(string: "\(baseURL)/api/keyword-search/projects/\(projectId)/keywords/timeline?keyword=\(encodedKeyword)")!

        var request = URLRequest(url: url)
        request.httpMethod = "GET"

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw URLError(.badServerResponse)
        }

        guard httpResponse.statusCode == 200 else {
            throw URLError(.badServerResponse)
        }

        return try JSONDecoder().decode(KeywordTimelineResponse.self, from: data)
    }
}
