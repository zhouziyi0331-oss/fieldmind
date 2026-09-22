//
//  KnowledgeGraphService.swift
//  FieldMind
//
//  P3 功能集成 - 交互式知识图谱服务
//  Created by Claude on 2026-09-16.
//

import Foundation

/// 知识图谱服务 - 交互式图谱可视化
class KnowledgeGraphService {
    static let shared = KnowledgeGraphService()

    private let baseURL: URL
    private let session: URLSession

    private init() {
        self.baseURL = URL(string: "http://localhost:8000/api/v1/knowledge-graph")!
        self.session = URLSession.shared
    }

    // MARK: - Models

    struct Node: Codable {
        let nodeId: String
        let nodeType: String
        let label: String
        let properties: [String: String]

        enum CodingKeys: String, CodingKey {
            case nodeId = "node_id"
            case nodeType = "node_type"
            case label, properties
        }
    }

    struct Edge: Codable {
        let edgeId: String
        let fromNode: String
        let toNode: String
        let relationshipType: String

        enum CodingKeys: String, CodingKey {
            case edgeId = "edge_id"
            case fromNode = "from_node"
            case toNode = "to_node"
            case relationshipType = "relationship_type"
        }
    }

    struct VisualizationData: Codable {
        let nodes: [VisualNode]
        let edges: [VisualEdge]

        struct VisualNode: Codable {
            let id: String
            let label: String
            let type: String
            let x: Double
            let y: Double
            let size: Double
            let color: String
        }

        struct VisualEdge: Codable {
            let id: String
            let from: String
            let to: String
            let label: String
            let color: String
        }
    }

    struct CreateNodeRequest: Codable {
        let nodeType: String
        let label: String
        let properties: [String: String]

        enum CodingKeys: String, CodingKey {
            case nodeType = "node_type"
            case label, properties
        }
    }

    struct CreateEdgeRequest: Codable {
        let fromNode: String
        let toNode: String
        let relationshipType: String

        enum CodingKeys: String, CodingKey {
            case fromNode = "from_node"
            case toNode = "to_node"
            case relationshipType = "relationship_type"
        }
    }

    // MARK: - API Methods

    /// 创建节点
    func createNode(projectId: String, nodeType: String, label: String, properties: [String: String] = [:]) async throws -> Node {
        let url = baseURL.appendingPathComponent("projects/\(projectId)/nodes")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body = CreateNodeRequest(nodeType: nodeType, label: label, properties: properties)
        request.httpBody = try JSONEncoder().encode(body)

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw KnowledgeGraphError.serverError
        }

        let result = try JSONDecoder().decode([String: Node].self, from: data)
        guard let node = result["node"] else {
            throw KnowledgeGraphError.decodingError
        }

        return node
    }

    /// 获取节点
    func getNode(projectId: String, nodeId: String) async throws -> Node {
        let url = baseURL.appendingPathComponent("projects/\(projectId)/nodes/\(nodeId)")

        let (data, response) = try await session.data(from: url)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw KnowledgeGraphError.serverError
        }

        let result = try JSONDecoder().decode([String: Node].self, from: data)
        guard let node = result["node"] else {
            throw KnowledgeGraphError.decodingError
        }

        return node
    }

    /// 删除节点
    func deleteNode(projectId: String, nodeId: String) async throws {
        let url = baseURL.appendingPathComponent("projects/\(projectId)/nodes/\(nodeId)")
        var request = URLRequest(url: url)
        request.httpMethod = "DELETE"

        let (_, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw KnowledgeGraphError.serverError
        }
    }

    /// 创建边
    func createEdge(projectId: String, fromNode: String, toNode: String, relationshipType: String) async throws -> Edge {
        let url = baseURL.appendingPathComponent("projects/\(projectId)/edges")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body = CreateEdgeRequest(fromNode: fromNode, toNode: toNode, relationshipType: relationshipType)
        request.httpBody = try JSONEncoder().encode(body)

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw KnowledgeGraphError.serverError
        }

        let result = try JSONDecoder().decode([String: Edge].self, from: data)
        guard let edge = result["edge"] else {
            throw KnowledgeGraphError.decodingError
        }

        return edge
    }

    /// 获取可视化数据
    func getVisualization(projectId: String, layout: String = "force_directed") async throws -> VisualizationData {
        var components = URLComponents(url: baseURL.appendingPathComponent("projects/\(projectId)/visualization"), resolvingAgainstBaseURL: true)!
        components.queryItems = [URLQueryItem(name: "layout", value: layout)]

        guard let url = components.url else {
            throw KnowledgeGraphError.invalidURL
        }

        let (data, response) = try await session.data(from: url)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw KnowledgeGraphError.serverError
        }

        return try JSONDecoder().decode(VisualizationData.self, from: data)
    }

    /// 搜索节点
    func searchNodes(projectId: String, query: String) async throws -> [Node] {
        var components = URLComponents(url: baseURL.appendingPathComponent("projects/\(projectId)/search"), resolvingAgainstBaseURL: true)!
        components.queryItems = [URLQueryItem(name: "query", value: query)]

        guard let url = components.url else {
            throw KnowledgeGraphError.invalidURL
        }

        let (data, response) = try await session.data(from: url)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw KnowledgeGraphError.serverError
        }

        let result = try JSONDecoder().decode([String: [Node]].self, from: data)
        return result["nodes"] ?? []
    }

    /// 获取统计信息
    func getStatistics(projectId: String) async throws -> [String: Any] {
        let url = baseURL.appendingPathComponent("projects/\(projectId)/statistics")

        let (data, response) = try await session.data(from: url)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw KnowledgeGraphError.serverError
        }

        return try JSONSerialization.jsonObject(with: data) as? [String: Any] ?? [:]
    }
}

// MARK: - Error Types

enum KnowledgeGraphError: Error {
    case invalidURL
    case serverError
    case decodingError
    case networkError

    var localizedDescription: String {
        switch self {
        case .invalidURL:
            return "无效的 URL"
        case .serverError:
            return "服务器错误"
        case .decodingError:
            return "数据解析错误"
        case .networkError:
            return "网络连接错误"
        }
    }
}
