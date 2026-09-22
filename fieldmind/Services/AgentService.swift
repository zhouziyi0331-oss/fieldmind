//
//  AgentService.swift
//  FieldMind
//
//  P3 功能集成 - Agent 系统服务
//  Created by Claude on 2026-09-16.
//

import Foundation

/// Agent 系统服务 - 智能任务执行
class AgentService {
    static let shared = AgentService()

    private let baseURL: URL
    private let session: URLSession

    private init() {
        self.baseURL = URL(string: "http://localhost:8000/api/v1/agents")!
        self.session = URLSession.shared
    }

    // MARK: - Models

    struct Agent: Codable {
        let agentId: String
        let name: String
        let agentType: String
        let description: String?
        let status: String
        let createdAt: String

        enum CodingKeys: String, CodingKey {
            case agentId = "agent_id"
            case name
            case agentType = "agent_type"
            case description, status
            case createdAt = "created_at"
        }
    }

    struct CreateAgentRequest: Codable {
        let name: String
        let agentType: String
        let description: String?
        let tools: [String]?

        enum CodingKeys: String, CodingKey {
            case name
            case agentType = "agent_type"
            case description, tools
        }
    }

    struct ExecuteRequest: Codable {
        let task: String
        let context: [String: String]?
    }

    struct ExecutionResult: Codable {
        let result: String
        let steps: [String]
        let toolsUsed: [String]
        let success: Bool

        enum CodingKeys: String, CodingKey {
            case result, steps
            case toolsUsed = "tools_used"
            case success
        }
    }

    struct Tool: Codable {
        let name: String
        let description: String
        let parameters: [String: String]
    }

    // MARK: - API Methods

    /// 创建 Agent
    func createAgent(name: String, type: String, description: String? = nil, tools: [String]? = nil) async throws -> Agent {
        let url = baseURL.appendingPathComponent("create")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body = CreateAgentRequest(name: name, agentType: type, description: description, tools: tools)
        request.httpBody = try JSONEncoder().encode(body)

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw AgentError.serverError
        }

        let result = try JSONDecoder().decode([String: Agent].self, from: data)
        guard let agent = result["agent"] else {
            throw AgentError.decodingError
        }

        return agent
    }

    /// 获取 Agent
    func getAgent(agentId: String) async throws -> Agent {
        let url = baseURL.appendingPathComponent(agentId)

        let (data, response) = try await session.data(from: url)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw AgentError.serverError
        }

        let result = try JSONDecoder().decode([String: Agent].self, from: data)
        guard let agent = result["agent"] else {
            throw AgentError.decodingError
        }

        return agent
    }

    /// 列出所有 Agent
    func listAgents() async throws -> [Agent] {
        let (data, response) = try await session.data(from: baseURL)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw AgentError.serverError
        }

        let result = try JSONDecoder().decode([String: [Agent]].self, from: data)
        return result["agents"] ?? []
    }

    /// 删除 Agent
    func deleteAgent(agentId: String) async throws {
        let url = baseURL.appendingPathComponent(agentId)
        var request = URLRequest(url: url)
        request.httpMethod = "DELETE"

        let (_, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw AgentError.serverError
        }
    }

    /// 执行 Agent 任务
    func execute(agentId: String, task: String, context: [String: String]? = nil) async throws -> ExecutionResult {
        let url = baseURL.appendingPathComponent("\(agentId)/execute")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body = ExecuteRequest(task: task, context: context)
        request.httpBody = try JSONEncoder().encode(body)

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw AgentError.serverError
        }

        return try JSONDecoder().decode(ExecutionResult.self, from: data)
    }

    /// 获取可用工具列表
    func getTools() async throws -> [Tool] {
        let url = baseURL.appendingPathComponent("tools")

        let (data, response) = try await session.data(from: url)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw AgentError.serverError
        }

        let result = try JSONDecoder().decode([String: [Tool]].self, from: data)
        return result["tools"] ?? []
    }
}

// MARK: - Error Types

enum AgentError: Error {
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
