import Foundation

class ModelConfigService {
    static let shared = ModelConfigService()
    private let baseURL = "http://localhost:8000"

    private init() {}

    // MARK: - Models

    struct AIModel: Codable, Identifiable {
        let id: Int
        let name: String
        let provider: String
        let modelType: String
        let description: String
        let isConfigured: Bool
        let isActive: Bool
        let maxTokens: Int
        let costPer1kTokens: Double
        let capabilities: [String]
        let createdAt: String
        let updatedAt: String

        enum CodingKeys: String, CodingKey {
            case id, name, provider, description, capabilities
            case modelType = "model_type"
            case isConfigured = "is_configured"
            case isActive = "is_active"
            case maxTokens = "max_tokens"
            case costPer1kTokens = "cost_per_1k_tokens"
            case createdAt = "created_at"
            case updatedAt = "updated_at"
        }
    }

    struct ModelConfig: Codable, Identifiable {
        let id: Int
        let modelId: Int
        let name: String
        let temperature: Double
        let topP: Double
        let maxTokens: Int
        let isDefault: Bool
        let createdAt: String
        let updatedAt: String

        enum CodingKeys: String, CodingKey {
            case id, name, temperature
            case modelId = "model_id"
            case topP = "top_p"
            case maxTokens = "max_tokens"
            case isDefault = "is_default"
            case createdAt = "created_at"
            case updatedAt = "updated_at"
        }
    }

    struct ModelUsage: Codable, Identifiable {
        let id: Int
        let modelId: Int
        let date: String
        let callCount: Int
        let totalTokens: Int
        let cost: Double
        let avgLatency: Double

        enum CodingKeys: String, CodingKey {
            case id, date, cost
            case modelId = "model_id"
            case callCount = "call_count"
            case totalTokens = "total_tokens"
            case avgLatency = "avg_latency"
        }
    }

    struct ModelsResponse: Codable {
        let models: [AIModel]
        let total: Int
    }

    struct ConfigsResponse: Codable {
        let configs: [ModelConfig]
        let total: Int
    }

    struct UsageResponse: Codable {
        let usage: [ModelUsage]
        let totalCost: Double
        let totalCalls: Int

        enum CodingKeys: String, CodingKey {
            case usage
            case totalCost = "total_cost"
            case totalCalls = "total_calls"
        }
    }

    // MARK: - API Methods

    func listModels(provider: String? = nil, configuredOnly: Bool = false) async throws -> ModelsResponse {
        var components = URLComponents(string: "\(baseURL)/api/v1/models")!
        var queryItems: [URLQueryItem] = []

        if let provider = provider, provider != "全部" {
            queryItems.append(URLQueryItem(name: "provider", value: provider))
        }
        if configuredOnly {
            queryItems.append(URLQueryItem(name: "configured_only", value: "true"))
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
        return try decoder.decode(ModelsResponse.self, from: data)
    }

    func listConfigs(modelId: Int? = nil) async throws -> ConfigsResponse {
        var components = URLComponents(string: "\(baseURL)/api/v1/model-configs")!

        if let modelId = modelId {
            components.queryItems = [URLQueryItem(name: "model_id", value: String(modelId))]
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
        return try decoder.decode(ConfigsResponse.self, from: data)
    }

    func getUsageStats(startDate: String? = nil, endDate: String? = nil) async throws -> UsageResponse {
        var components = URLComponents(string: "\(baseURL)/api/v1/models/usage")!
        var queryItems: [URLQueryItem] = []

        if let startDate = startDate {
            queryItems.append(URLQueryItem(name: "start_date", value: startDate))
        }
        if let endDate = endDate {
            queryItems.append(URLQueryItem(name: "end_date", value: endDate))
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
        return try decoder.decode(UsageResponse.self, from: data)
    }

    func setActiveModel(modelId: Int) async throws -> AIModel {
        let url = URL(string: "\(baseURL)/api/v1/models/\(modelId)/activate")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw URLError(.badServerResponse)
        }

        guard httpResponse.statusCode == 200 else {
            throw URLError(.badServerResponse)
        }

        let decoder = JSONDecoder()
        return try decoder.decode(AIModel.self, from: data)
    }
}
