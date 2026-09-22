//
//  CollaborationService.swift
//  FieldMind
//
//  P3 功能集成 - 实时协作编辑服务
//  Created by Claude on 2026-09-16.
//

import Foundation

/// 实时协作编辑服务 - 支持多用户同时编辑
class CollaborationService {
    static let shared = CollaborationService()

    private let baseURL: URL
    private let session: URLSession
    private var webSocketTask: URLSessionWebSocketTask?

    private init() {
        self.baseURL = URL(string: "http://localhost:8000/api/v1/collaboration")!
        self.session = URLSession.shared
    }

    // MARK: - Models

    struct Session: Codable {
        let sessionId: String
        let documentId: String
        let creatorId: Int
        let content: String
        let users: [User]
        let createdAt: String

        enum CodingKeys: String, CodingKey {
            case sessionId = "session_id"
            case documentId = "document_id"
            case creatorId = "creator_id"
            case content, users
            case createdAt = "created_at"
        }

        struct User: Codable {
            let userId: Int
            let username: String
            let color: String
            let cursor: Cursor?

            enum CodingKeys: String, CodingKey {
                case userId = "user_id"
                case username, color, cursor
            }

            struct Cursor: Codable {
                let position: Int
                let selection: [Int]?
            }
        }
    }

    struct CreateSessionRequest: Codable {
        let documentId: String
        let initialContent: String

        enum CodingKeys: String, CodingKey {
            case documentId = "document_id"
            case initialContent = "initial_content"
        }
    }

    struct Operation: Codable {
        let type: String
        let position: Int
        let content: String?
        let length: Int?
        let attributes: [String: String]?
    }

    // MARK: - API Methods

    /// 创建协作会话
    func createSession(documentId: String, initialContent: String) async throws -> Session {
        let url = baseURL.appendingPathComponent("sessions")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body = CreateSessionRequest(documentId: documentId, initialContent: initialContent)
        request.httpBody = try JSONEncoder().encode(body)

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw CollaborationError.serverError
        }

        let result = try JSONDecoder().decode([String: Session].self, from: data)
        guard let session = result["session"] else {
            throw CollaborationError.decodingError
        }

        return session
    }

    /// 获取会话信息
    func getSession(sessionId: String) async throws -> Session {
        let url = baseURL.appendingPathComponent("sessions/\(sessionId)")

        let (data, response) = try await session.data(from: url)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw CollaborationError.serverError
        }

        let result = try JSONDecoder().decode([String: Session].self, from: data)
        guard let session = result["session"] else {
            throw CollaborationError.decodingError
        }

        return session
    }

    /// 加入会话
    func joinSession(sessionId: String, userId: Int, username: String) async throws {
        let url = baseURL.appendingPathComponent("sessions/\(sessionId)/join")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body: [String: Any] = [
            "user_id": userId,
            "username": username
        ]
        request.httpBody = try JSONSerialization.data(withJSONObject: body)

        let (_, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw CollaborationError.serverError
        }
    }

    /// 离开会话
    func leaveSession(sessionId: String, userId: Int) async throws {
        let url = baseURL.appendingPathComponent("sessions/\(sessionId)/leave")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body = ["user_id": userId]
        request.httpBody = try JSONSerialization.data(withJSONObject: body)

        let (_, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw CollaborationError.serverError
        }
    }

    /// 应用操作
    func applyOperation(sessionId: String, userId: Int, operation: Operation) async throws -> [String: Any] {
        let url = baseURL.appendingPathComponent("sessions/\(sessionId)/operations")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body: [String: Any] = [
            "user_id": userId,
            "operation": try operation.toDictionary()
        ]
        request.httpBody = try JSONSerialization.data(withJSONObject: body)

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw CollaborationError.serverError
        }

        return try JSONSerialization.jsonObject(with: data) as? [String: Any] ?? [:]
    }

    // MARK: - WebSocket Connection

    /// 连接 WebSocket 进行实时同步
    func connectWebSocket(sessionId: String, onMessage: @escaping (String) -> Void) {
        let wsURL = URL(string: "ws://localhost:8000/api/v1/collaboration/ws/\(sessionId)")!
        webSocketTask = session.webSocketTask(with: wsURL)
        webSocketTask?.resume()

        receiveMessage(onMessage: onMessage)
    }

    /// 发送 WebSocket 消息
    func sendWebSocketMessage(_ message: String) {
        let message = URLSessionWebSocketTask.Message.string(message)
        webSocketTask?.send(message) { error in
            if let error = error {
                print("WebSocket 发送错误: \(error)")
            }
        }
    }

    /// 断开 WebSocket 连接
    func disconnectWebSocket() {
        webSocketTask?.cancel(with: .goingAway, reason: nil)
        webSocketTask = nil
    }

    private func receiveMessage(onMessage: @escaping (String) -> Void) {
        webSocketTask?.receive { [weak self] result in
            switch result {
            case .success(let message):
                switch message {
                case .string(let text):
                    onMessage(text)
                case .data(let data):
                    if let text = String(data: data, encoding: .utf8) {
                        onMessage(text)
                    }
                @unknown default:
                    break
                }
                // 继续接收下一条消息
                self?.receiveMessage(onMessage: onMessage)
            case .failure(let error):
                print("WebSocket 接收错误: \(error)")
            }
        }
    }
}

// MARK: - Error Types

enum CollaborationError: Error {
    case invalidURL
    case serverError
    case decodingError
    case networkError
    case webSocketError

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
        case .webSocketError:
            return "WebSocket 连接错误"
        }
    }
}

// MARK: - Helpers

extension CollaborationService.Operation {
    func toDictionary() throws -> [String: Any] {
        var dict: [String: Any] = [
            "type": type,
            "position": position
        ]
        if let content = content {
            dict["content"] = content
        }
        if let length = length {
            dict["length"] = length
        }
        if let attributes = attributes {
            dict["attributes"] = attributes
        }
        return dict
    }
}
