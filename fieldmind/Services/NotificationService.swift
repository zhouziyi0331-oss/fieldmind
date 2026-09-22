//
//  NotificationService.swift
//  FieldMind
//
//  P3 功能集成 - 通知系统服务
//  Created by Claude on 2026-09-16.
//

import Foundation

/// 通知系统服务 - 多渠道通知管理
class NotificationService {
    static let shared = NotificationService()

    private let baseURL: URL
    private let session: URLSession

    private init() {
        self.baseURL = URL(string: "http://localhost:8000/api/v1/notifications")!
        self.session = URLSession.shared
    }

    // MARK: - Models

    struct Notification: Codable {
        let notificationId: String
        let userId: Int
        let title: String
        let message: String
        let type: String
        let priority: String
        let channels: [String]
        let metadata: [String: String]
        let isRead: Bool
        let createdAt: String
        let readAt: String?

        enum CodingKeys: String, CodingKey {
            case notificationId = "notification_id"
            case userId = "user_id"
            case title, message, type, priority, channels, metadata
            case isRead = "is_read"
            case createdAt = "created_at"
            case readAt = "read_at"
        }
    }

    struct SendNotificationRequest: Codable {
        let userId: Int
        let title: String
        let message: String
        let notificationType: String
        let priority: String
        let channels: [String]
        let metadata: [String: String]

        enum CodingKeys: String, CodingKey {
            case userId = "user_id"
            case title, message
            case notificationType = "notification_type"
            case priority, channels, metadata
        }
    }

    // MARK: - API Methods

    /// 发送通知
    func sendNotification(userId: Int,
                         title: String,
                         message: String,
                         type: String = "info",
                         priority: String = "normal",
                         channels: [String] = ["in_app"],
                         metadata: [String: String] = [:]) async throws -> Notification {
        let url = baseURL.appendingPathComponent("send")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body = SendNotificationRequest(
            userId: userId,
            title: title,
            message: message,
            notificationType: type,
            priority: priority,
            channels: channels,
            metadata: metadata
        )
        request.httpBody = try JSONEncoder().encode(body)

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw NotificationError.serverError
        }

        let result = try JSONDecoder().decode([String: Notification].self, from: data)
        guard let notification = result["notification"] else {
            throw NotificationError.decodingError
        }

        return notification
    }

    /// 获取通知列表
    func getNotifications(unreadOnly: Bool = false, limit: Int = 50) async throws -> [Notification] {
        var components = URLComponents(url: baseURL, resolvingAgainstBaseURL: true)!
        components.queryItems = [
            URLQueryItem(name: "unread_only", value: String(unreadOnly)),
            URLQueryItem(name: "limit", value: String(limit))
        ]

        guard let url = components.url else {
            throw NotificationError.invalidURL
        }

        let (data, response) = try await session.data(from: url)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw NotificationError.serverError
        }

        let result = try JSONDecoder().decode([String: [Notification]].self, from: data)
        return result["notifications"] ?? []
    }

    /// 获取未读数量
    func getUnreadCount() async throws -> Int {
        let url = baseURL.appendingPathComponent("unread/count")

        let (data, response) = try await session.data(from: url)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw NotificationError.serverError
        }

        let result = try JSONDecoder().decode([String: Int].self, from: data)
        return result["unread_count"] ?? 0
    }

    /// 标记为已读
    func markAsRead(notificationId: String) async throws {
        let url = baseURL.appendingPathComponent("\(notificationId)/read")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"

        let (_, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw NotificationError.serverError
        }
    }

    /// 标记所有为已读
    func markAllAsRead() async throws -> Int {
        let url = baseURL.appendingPathComponent("read-all")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw NotificationError.serverError
        }

        let result = try JSONDecoder().decode([String: Int].self, from: data)
        return result["count"] ?? 0
    }

    /// 删除通知
    func deleteNotification(notificationId: String) async throws {
        let url = baseURL.appendingPathComponent(notificationId)
        var request = URLRequest(url: url)
        request.httpMethod = "DELETE"

        let (_, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw NotificationError.serverError
        }
    }

    /// 获取统计信息
    func getStatistics() async throws -> [String: Any] {
        let url = baseURL.appendingPathComponent("statistics")

        let (data, response) = try await session.data(from: url)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw NotificationError.serverError
        }

        return try JSONSerialization.jsonObject(with: data) as? [String: Any] ?? [:]
    }
}

// MARK: - Error Types

enum NotificationError: Error {
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
