//
//  LLMService.swift
//  FieldMind
//
//  P3 功能集成 - LLM 深度集成服务
//  Created by Claude on 2026-09-16.
//

import Foundation

/// LLM 服务 - 统一的 AI 模型调用接口
class LLMService {
    static let shared = LLMService()

    private let baseURL: URL
    private let session: URLSession

    private init() {
        self.baseURL = URL(string: "http://localhost:8000/api/v1/llm")!
        self.session = URLSession.shared
    }

    // MARK: - Models

    struct ChatRequest: Codable {
        let messages: [Message]
        let provider: String?
        let model: String?
        let temperature: Double?
        let maxTokens: Int?

        struct Message: Codable {
            let role: String
            let content: String
        }
    }

    struct ChatResponse: Codable {
        let response: String
        let provider: String
        let model: String
        let usage: Usage
        let cost: Cost

        struct Usage: Codable {
            let promptTokens: Int
            let completionTokens: Int
            let totalTokens: Int

            enum CodingKeys: String, CodingKey {
                case promptTokens = "prompt_tokens"
                case completionTokens = "completion_tokens"
                case totalTokens = "total_tokens"
            }
        }

        struct Cost: Codable {
            let inputCost: Double
            let outputCost: Double
            let totalCost: Double

            enum CodingKeys: String, CodingKey {
                case inputCost = "input_cost"
                case outputCost = "output_cost"
                case totalCost = "total_cost"
            }
        }
    }

    struct ModelInfo: Codable {
        let name: String
        let provider: String
        let inputCostPer1k: Double
        let outputCostPer1k: Double

        enum CodingKeys: String, CodingKey {
            case name, provider
            case inputCostPer1k = "input_cost_per_1k"
            case outputCostPer1k = "output_cost_per_1k"
        }
    }

    struct CostStatistics: Codable {
        let totalCost: Double
        let totalTokens: Int
        let requestCount: Int

        enum CodingKeys: String, CodingKey {
            case totalCost = "total_cost"
            case totalTokens = "total_tokens"
            case requestCount = "request_count"
        }
    }

    // MARK: - API Methods

    /// 发送聊天消息
    func chat(messages: [ChatRequest.Message],
              provider: String? = nil,
              model: String? = nil,
              temperature: Double = 0.7,
              maxTokens: Int = 1000) async throws -> ChatResponse {

        let url = baseURL.appendingPathComponent("chat")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let chatRequest = ChatRequest(
            messages: messages,
            provider: provider,
            model: model,
            temperature: temperature,
            maxTokens: maxTokens
        )

        request.httpBody = try JSONEncoder().encode(chatRequest)

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw LLMError.serverError
        }

        return try JSONDecoder().decode(ChatResponse.self, from: data)
    }

    /// 获取可用模型列表
    func getModels() async throws -> [ModelInfo] {
        let url = baseURL.appendingPathComponent("models")

        let (data, response) = try await session.data(from: url)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw LLMError.serverError
        }

        let result = try JSONDecoder().decode([String: [ModelInfo]].self, from: data)
        return result["models"] ?? []
    }

    /// 获取成本统计
    func getCostStatistics() async throws -> CostStatistics {
        let url = baseURL.appendingPathComponent("cost")

        let (data, response) = try await session.data(from: url)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw LLMError.serverError
        }

        return try JSONDecoder().decode(CostStatistics.self, from: data)
    }

    /// 设置路由策略
    func setRoutingStrategy(_ strategy: String) async throws {
        let url = baseURL.appendingPathComponent("router/strategy")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body = ["strategy": strategy]
        request.httpBody = try JSONSerialization.data(withJSONObject: body)

        let (_, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw LLMError.serverError
        }
    }
}

// MARK: - Error Types

enum LLMError: Error {
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
