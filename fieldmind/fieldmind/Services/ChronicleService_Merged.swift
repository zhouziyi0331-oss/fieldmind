//
//  ChronicleService_Merged.swift
//  FieldMind
//
//  深度整合 - 合并自主版本和 Native 版本
//  Generated: Sat Sep 19 11:21:00 CST 2026
//

import Foundation

// ========================================
// 主实现（来自主项目）
// ========================================



class ChronicleService {
    static let shared = ChronicleService()
    private var baseURL: String { APIConfig.serverURL }

    private init() {}

    // MARK: - Models

    struct ChronicleEvent: Codable, Identifiable {
        let id: Int
        let projectId: Int
        let title: String
        let description: String
        let category: String
        let eventDate: String
        let location: String?
        let participants: [String]
        let tags: [String]
        let relatedDocuments: [Int]
        let images: [String]
        let createdAt: String
        let updatedAt: String

        enum CodingKeys: String, CodingKey {
            case id, title, description, category, location, participants, tags, images
            case projectId = "project_id"
            case eventDate = "event_date"
            case relatedDocuments = "related_documents"
            case createdAt = "created_at"
            case updatedAt = "updated_at"
        }
    }

    struct EventsResponse: Codable {
        let events: [ChronicleEvent]
        let total: Int
    }

    // MARK: - API Methods

    func listEvents(projectId: Int, category: String? = nil, startDate: String? = nil, endDate: String? = nil) async throws -> EventsResponse {
        var components = URLComponents(string: "\(baseURL)/api/v1/projects/\(projectId)/events")!
        var queryItems: [URLQueryItem] = []

        if let category = category, category != "全部分类" {
            queryItems.append(URLQueryItem(name: "category", value: category))
        }
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
        return try decoder.decode(EventsResponse.self, from: data)
    }

    func getEvent(projectId: Int, eventId: Int) async throws -> ChronicleEvent {
        let url = URL(string: "\(baseURL)/api/v1/projects/\(projectId)/events/\(eventId)")!
        let (data, response) = try await URLSession.shared.data(from: url)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw URLError(.badServerResponse)
        }

        guard httpResponse.statusCode == 200 else {
            throw URLError(.badServerResponse)
        }

        let decoder = JSONDecoder()
        return try decoder.decode(ChronicleEvent.self, from: data)
    }

    func createEvent(projectId: Int, title: String, description: String, category: String, eventDate: String, location: String?, participants: [String], tags: [String]) async throws -> ChronicleEvent {
        let url = URL(string: "\(baseURL)/api/v1/projects/\(projectId)/events")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body: [String: Any] = [
            "title": title,
            "description": description,
            "category": category,
            "event_date": eventDate,
            "location": location as Any,
            "participants": participants,
            "tags": tags
        ]

        request.httpBody = try JSONSerialization.data(withJSONObject: body)

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw URLError(.badServerResponse)
        }

        guard httpResponse.statusCode == 200 || httpResponse.statusCode == 201 else {
            throw URLError(.badServerResponse)
        }

        let decoder = JSONDecoder()
        return try decoder.decode(ChronicleEvent.self, from: data)
    }
}

// ========================================
// Native 版本的扩展功能
// ========================================
// TODO: 手动审查并整合以下功能

/*


class ChronicleService {
    static let shared = ChronicleService()
    private var baseURL: String { APIConfig.serverURL }

    private init() {}

    // MARK: - Models

    struct ChronicleEvent: Codable, Identifiable {
        let id: Int
        let projectId: Int
        let title: String
        let description: String
        let category: String
        let eventDate: String
        let location: String?
        let participants: [String]
        let tags: [String]
        let relatedDocuments: [Int]
        let images: [String]
        let createdAt: String
        let updatedAt: String

        enum CodingKeys: String, CodingKey {
            case id, title, description, category, location, participants, tags, images
            case projectId = "project_id"
            case eventDate = "event_date"
            case relatedDocuments = "related_documents"
            case createdAt = "created_at"
            case updatedAt = "updated_at"
        }
    }

    struct EventsResponse: Codable {
        let events: [ChronicleEvent]
        let total: Int
    }

    // MARK: - API Methods

    func listEvents(projectId: Int, category: String? = nil, startDate: String? = nil, endDate: String? = nil) async throws -> EventsResponse {
        var components = URLComponents(string: "\(baseURL)/api/v1/projects/\(projectId)/events")!
        var queryItems: [URLQueryItem] = []

        if let category = category, category != "全部分类" {
            queryItems.append(URLQueryItem(name: "category", value: category))
        }
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
        return try decoder.decode(EventsResponse.self, from: data)
    }

    func getEvent(projectId: Int, eventId: Int) async throws -> ChronicleEvent {
        let url = URL(string: "\(baseURL)/api/v1/projects/\(projectId)/events/\(eventId)")!
        let (data, response) = try await URLSession.shared.data(from: url)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw URLError(.badServerResponse)
        }

        guard httpResponse.statusCode == 200 else {
            throw URLError(.badServerResponse)
        }

        let decoder = JSONDecoder()
        return try decoder.decode(ChronicleEvent.self, from: data)
    }

    func createEvent(projectId: Int, title: String, description: String, category: String, eventDate: String, location: String?, participants: [String], tags: [String]) async throws -> ChronicleEvent {
        let url = URL(string: "\(baseURL)/api/v1/projects/\(projectId)/events")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body: [String: Any] = [
            "title": title,
            "description": description,
            "category": category,
            "event_date": eventDate,
            "location": location as Any,
            "participants": participants,
            "tags": tags
        ]

        request.httpBody = try JSONSerialization.data(withJSONObject: body)

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw URLError(.badServerResponse)
        }

        guard httpResponse.statusCode == 200 || httpResponse.statusCode == 201 else {
            throw URLError(.badServerResponse)
        }

        let decoder = JSONDecoder()
        return try decoder.decode(ChronicleEvent.self, from: data)
    }
}
*/

