//
//  KnowledgeGraphService_Merged.swift
//  FieldMind
//
//  深度整合 - 合并自主版本和 Native 版本
//  Generated: Sat Sep 19 11:21:00 CST 2026
//

import Foundation

// ========================================
// 主实现（来自主项目）
// ========================================


/// Knowledge Graph Service - 知识图谱API对接

class KnowledgeGraphService {
    static let shared = KnowledgeGraphService()
    private let apiClient = APIClient.shared

    private init() {}

    // MARK: - Response Models

    struct EntityResponse: Codable, Identifiable {
        let id: String
        let entityType: String
        let name: String
        let aliases: [String]?
        let properties: [String: AnyCodable]?
        let description: String?
        let confidence: Double
        let mentionCount: Int
        let documentIds: [Int]?

        enum CodingKeys: String, CodingKey {
            case id
            case entityType = "entity_type"
            case name
            case aliases
            case properties
            case description
            case confidence
            case mentionCount = "mention_count"
            case documentIds = "document_ids"
        }
    }

    struct EntitiesResponse: Codable {
        let entities: [EntityResponse]
    }

    struct GraphNode: Codable, Identifiable {
        let id: Int
        let label: String
        let group: String
        let title: String?
        let value: Int?
        let shape: String?
        let color: String?
    }

    struct GraphEdge: Codable, Identifiable {
        let from: Int
        let to: Int
        let label: String?
        let arrows: String?
        let color: String?
        let width: Double?

        enum CodingKeys: String, CodingKey {
            case from, to, label, arrows, color, width
        }

        // Computed ID for Identifiable
        var id: String { "\(from)-\(to)" }
    }

    struct GraphVisualizationResponse: Codable {
        let status: String
        let nodes: [GraphNode]
        let edges: [GraphEdge]
        let stats: GraphStats
    }

    struct GraphStats: Codable {
        let nodeCount: Int
        let edgeCount: Int

        enum CodingKeys: String, CodingKey {
            case nodeCount = "node_count"
            case edgeCount = "edge_count"
        }
    }

    struct BuildGraphRequest: Codable {
        let projectId: Int
        let documentIds: [Int]?
        let forceRebuild: Bool

        enum CodingKeys: String, CodingKey {
            case projectId = "project_id"
            case documentIds = "document_ids"
            case forceRebuild = "force_rebuild"
        }
    }

    struct BuildGraphResponse: Codable {
        let status: String
        let message: String
        let stats: BuildStats
    }

    struct BuildStats: Codable {
        let documentsProcessed: Int
        let entitiesCreated: Int
        let entitiesUpdated: Int
        let relationshipsCreated: Int
        let timelineEvents: Int
        let errors: [BuildError]?

        enum CodingKeys: String, CodingKey {
            case documentsProcessed = "documents_processed"
            case entitiesCreated = "entities_created"
            case entitiesUpdated = "entities_updated"
            case relationshipsCreated = "relationships_created"
            case timelineEvents = "timeline_events"
            case errors
        }
    }

    struct BuildError: Codable {
        let documentId: Int
        let error: String

        enum CodingKeys: String, CodingKey {
            case documentId = "document_id"
            case error
        }
    }

    // MARK: - API Methods

    /// 构建知识图谱
    func buildKnowledgeGraph(
        projectId: Int,
        documentIds: [Int]? = nil,
        forceRebuild: Bool = false
    ) async throws -> BuildGraphResponse {
        let request = BuildGraphRequest(
            projectId: projectId,
            documentIds: documentIds,
            forceRebuild: forceRebuild
        )

        let endpoint = APIEndpoint.buildKnowledgeGraph
        return try await apiClient.request(endpoint, method: .post, body: request)
    }

    /// 获取实体列表
    func getEntities(
        projectId: Int,
        entityType: String? = nil,
        search: String? = nil,
        limit: Int = 100
    ) async throws -> [EntityResponse] {
        var queryItems: [URLQueryItem] = [
            URLQueryItem(name: "project_id", value: "\(projectId)"),
            URLQueryItem(name: "limit", value: "\(limit)")
        ]

        if let entityType = entityType {
            queryItems.append(URLQueryItem(name: "entity_type", value: entityType))
        }

        if let search = search, !search.isEmpty {
            queryItems.append(URLQueryItem(name: "search", value: search))
        }

        let endpoint = APIEndpoint.knowledgeGraphEntities(queryItems: queryItems)
        return try await apiClient.request(endpoint, method: .get)
    }

    /// 获取实体详情
    func getEntityDetail(entityId: String) async throws -> EntityResponse {
        let endpoint = APIEndpoint.knowledgeGraphEntityDetail(entityId: entityId)
        return try await apiClient.request(endpoint, method: .get)
    }

    /// 获取知识图谱可视化数据
    func getGraphVisualization(
        projectId: Int,
        limit: Int = 100
    ) async throws -> GraphVisualizationResponse {
        let queryItems: [URLQueryItem] = [
            URLQueryItem(name: "project_id", value: "\(projectId)"),
            URLQueryItem(name: "limit", value: "\(limit)")
        ]

        let endpoint = APIEndpoint.knowledgeGraphVisualize(queryItems: queryItems)
        return try await apiClient.request(endpoint, method: .get)
    }
}

// MARK: - AnyCodable Helper

// MARK: - API Endpoint Extensions

extension APIEndpoint {
    static let buildKnowledgeGraph = APIEndpoint.custom("/knowledge-graph/build")

    static func knowledgeGraphEntities(queryItems: [URLQueryItem]) -> APIEndpoint {
        return .custom("/knowledge-graph/entities", queryItems: queryItems)
    }

    static func knowledgeGraphEntityDetail(entityId: String) -> APIEndpoint {
        return .custom("/knowledge-graph/entities/\(entityId)")
    }

    static func knowledgeGraphVisualize(queryItems: [URLQueryItem]) -> APIEndpoint {
        return .custom("/knowledge-graph/visualize", queryItems: queryItems)
    }
}

// ========================================
// Native 版本的扩展功能
// ========================================
// TODO: 手动审查并整合以下功能

/*

/// Knowledge Graph Service - 知识图谱API对接

class KnowledgeGraphService {
    static let shared = KnowledgeGraphService()
    private let apiClient = APIClient.shared

    private init() {}

    // MARK: - Response Models

    struct EntityResponse: Codable, Identifiable {
        let id: String
        let entityType: String
        let name: String
        let aliases: [String]?
        let properties: [String: AnyCodable]?
        let description: String?
        let confidence: Double
        let mentionCount: Int
        let documentIds: [Int]?

        enum CodingKeys: String, CodingKey {
            case id
            case entityType = "entity_type"
            case name
            case aliases
            case properties
            case description
            case confidence
            case mentionCount = "mention_count"
            case documentIds = "document_ids"
        }
    }

    struct EntitiesResponse: Codable {
        let entities: [EntityResponse]
    }

    struct GraphNode: Codable, Identifiable {
        let id: Int
        let label: String
        let group: String
        let title: String?
        let value: Int?
        let shape: String?
        let color: String?
    }

    struct GraphEdge: Codable, Identifiable {
        let from: Int
        let to: Int
        let label: String?
        let arrows: String?
        let color: String?
        let width: Double?

        enum CodingKeys: String, CodingKey {
            case from, to, label, arrows, color, width
        }

        // Computed ID for Identifiable
        var id: String { "\(from)-\(to)" }
    }

    struct GraphVisualizationResponse: Codable {
        let status: String
        let nodes: [GraphNode]
        let edges: [GraphEdge]
        let stats: GraphStats
    }

    struct GraphStats: Codable {
        let nodeCount: Int
        let edgeCount: Int

        enum CodingKeys: String, CodingKey {
            case nodeCount = "node_count"
            case edgeCount = "edge_count"
        }
    }

    struct BuildGraphRequest: Codable {
        let projectId: Int
        let documentIds: [Int]?
        let forceRebuild: Bool

        enum CodingKeys: String, CodingKey {
            case projectId = "project_id"
            case documentIds = "document_ids"
            case forceRebuild = "force_rebuild"
        }
    }

    struct BuildGraphResponse: Codable {
        let status: String
        let message: String
        let stats: BuildStats
    }

    struct BuildStats: Codable {
        let documentsProcessed: Int
        let entitiesCreated: Int
        let entitiesUpdated: Int
        let relationshipsCreated: Int
        let timelineEvents: Int
        let errors: [BuildError]?

        enum CodingKeys: String, CodingKey {
            case documentsProcessed = "documents_processed"
            case entitiesCreated = "entities_created"
            case entitiesUpdated = "entities_updated"
            case relationshipsCreated = "relationships_created"
            case timelineEvents = "timeline_events"
            case errors
        }
    }

    struct BuildError: Codable {
        let documentId: Int
        let error: String

        enum CodingKeys: String, CodingKey {
            case documentId = "document_id"
            case error
        }
    }

    // MARK: - API Methods

    /// 构建知识图谱
    func buildKnowledgeGraph(
        projectId: Int,
        documentIds: [Int]? = nil,
        forceRebuild: Bool = false
    ) async throws -> BuildGraphResponse {
        let request = BuildGraphRequest(
            projectId: projectId,
            documentIds: documentIds,
            forceRebuild: forceRebuild
        )

        let endpoint = APIEndpoint.buildKnowledgeGraph
        return try await apiClient.request(endpoint, method: .post, body: request)
    }

    /// 获取实体列表
    func getEntities(
        projectId: Int,
        entityType: String? = nil,
        search: String? = nil,
        limit: Int = 100
    ) async throws -> [EntityResponse] {
        var queryItems: [URLQueryItem] = [
            URLQueryItem(name: "project_id", value: "\(projectId)"),
            URLQueryItem(name: "limit", value: "\(limit)")
        ]

        if let entityType = entityType {
            queryItems.append(URLQueryItem(name: "entity_type", value: entityType))
        }

        if let search = search, !search.isEmpty {
            queryItems.append(URLQueryItem(name: "search", value: search))
        }

        let endpoint = APIEndpoint.knowledgeGraphEntities(queryItems: queryItems)
        return try await apiClient.request(endpoint, method: .get)
    }

    /// 获取实体详情
    func getEntityDetail(entityId: String) async throws -> EntityResponse {
        let endpoint = APIEndpoint.knowledgeGraphEntityDetail(entityId: entityId)
        return try await apiClient.request(endpoint, method: .get)
    }

    /// 获取知识图谱可视化数据
    func getGraphVisualization(
        projectId: Int,
        limit: Int = 100
    ) async throws -> GraphVisualizationResponse {
        let queryItems: [URLQueryItem] = [
            URLQueryItem(name: "project_id", value: "\(projectId)"),
            URLQueryItem(name: "limit", value: "\(limit)")
        ]

        let endpoint = APIEndpoint.knowledgeGraphVisualize(queryItems: queryItems)
        return try await apiClient.request(endpoint, method: .get)
    }
}

// MARK: - AnyCodable Helper

// MARK: - API Endpoint Extensions

extension APIEndpoint {
    static let buildKnowledgeGraph = APIEndpoint.custom("/knowledge-graph/build")

    static func knowledgeGraphEntities(queryItems: [URLQueryItem]) -> APIEndpoint {
        return .custom("/knowledge-graph/entities", queryItems: queryItems)
    }

    static func knowledgeGraphEntityDetail(entityId: String) -> APIEndpoint {
        return .custom("/knowledge-graph/entities/\(entityId)")
    }

    static func knowledgeGraphVisualize(queryItems: [URLQueryItem]) -> APIEndpoint {
        return .custom("/knowledge-graph/visualize", queryItems: queryItems)
    }
}
*/

