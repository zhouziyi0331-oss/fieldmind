import Foundation

// MARK: - Request Models

struct ChatSessionCreate: Codable {
    let projectId: Int
    let name: String
    let documentIds: [Int]?
    let config: [String: AnyCodable]?
}

struct ChatMessageCreate: Codable {
    let content: String
}

// MARK: - Response Models

struct ChatSessionResponse: Codable, Identifiable {
    let id: Int
    let projectId: Int
    let name: String
    let documentIds: [Int]?
    let config: [String: AnyCodable]?
    let messageCount: Int
    let createdAt: String
    let lastMessageAt: String?
}

struct ChatMessageResponse: Codable, Identifiable {
    let id: Int
    let sessionId: Int
    let role: String
    let content: String
    let thinkingProcess: String?
    let sources: [String]?
    let extraData: [String: AnyCodable]?
    let createdAt: String
}

struct ChatSessionListResponse: Codable {
    let total: Int
    let sessions: [ChatSessionResponse]
}

struct ChatMessageListResponse: Codable {
    let total: Int
    let messages: [ChatMessageResponse]
}

struct SkillEvolutionResponse: Codable {
    let message: String
    let framework: [String: AnyCodable]
}

// MARK: - Chat Service

class ChatService {
    private let apiClient = APIClient.shared

    /// 创建新的对话会话
    func createSession(projectId: Int, name: String, documentIds: [Int]? = nil, config: [String: Any]? = nil) async throws -> ChatSessionResponse {
        let configCodable = config?.mapValues { AnyCodable($0) }
        let request = ChatSessionCreate(
            projectId: projectId,
            name: name,
            documentIds: documentIds,
            config: configCodable
        )

        return try await apiClient.request(
            .createSession,
            method: .post,
            body: request
        )
    }

    /// 获取对话会话详情
    func getSession(sessionId: Int) async throws -> ChatSessionResponse {
        return try await apiClient.request(
            .getSession(sessionId: String(sessionId)),
            method: .get
        )
    }

    /// 获取项目的所有对话会话
    func listProjectSessions(projectId: Int, skip: Int = 0, limit: Int = 20) async throws -> ChatSessionListResponse {
        return try await apiClient.request(
            .projectSessions(projectId: String(projectId)),
            method: .get,
            queryItems: [
                URLQueryItem(name: "skip", value: String(skip)),
                URLQueryItem(name: "limit", value: String(limit))
            ]
        )
    }

    /// 发送消息并获取AI响应
    func sendMessage(sessionId: Int, content: String) async throws -> ChatMessageResponse {
        let request = ChatMessageCreate(content: content)

        return try await apiClient.request(
            .sendMessage(sessionId: String(sessionId)),
            method: .post,
            body: request
        )
    }

    /// 获取会话的所有消息
    func getSessionMessages(sessionId: Int, skip: Int = 0, limit: Int = 50) async throws -> ChatMessageListResponse {
        return try await apiClient.request(
            .getMessages(sessionId: String(sessionId)),
            method: .get,
            queryItems: [
                URLQueryItem(name: "skip", value: String(skip)),
                URLQueryItem(name: "limit", value: String(limit))
            ]
        )
    }

    /// 删除对话会话
    func deleteSession(sessionId: Int) async throws {
        let _: EmptyResponse = try await apiClient.request(
            .deleteSession(sessionId: String(sessionId)),
            method: .delete
        )
    }

    /// 进化会话的技能框架
    func evolveSkill(sessionId: Int) async throws -> SkillEvolutionResponse {
        return try await apiClient.request(
            .evolveSkill(sessionId: String(sessionId)),
            method: .post
        )
    }
}
