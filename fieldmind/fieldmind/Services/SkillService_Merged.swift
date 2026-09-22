//
//  SkillService_Merged.swift
//  FieldMind
//
//  深度整合 - 合并自主版本和 Native 版本
//  Generated: Sat Sep 19 11:21:01 CST 2026
//

import Foundation

// ========================================
// 主实现（来自主项目）
// ========================================



class SkillService {
    static let shared = SkillService()
    private var baseURL: String { APIConfig.serverURL }

    private init() {}

    // MARK: - Models

    struct SkillInfo: Codable, Identifiable {
        let id: String
        let name: String
        let description: String
        let dimensions: [String]
        let defaultEnabled: Bool

        enum CodingKeys: String, CodingKey {
            case id, name, description, dimensions
            case defaultEnabled = "default_enabled"
        }
    }

    struct AvailableSkillsResponse: Codable {
        let skills: [SkillInfo]
        let total: Int
    }

    struct SkillConfigResponse: Codable {
        let projectId: Int
        let enabledSkills: [String]
        let availableSkills: [SkillInfo]

        enum CodingKeys: String, CodingKey {
            case projectId = "project_id"
            case enabledSkills = "enabled_skills"
            case availableSkills = "available_skills"
        }
    }

    struct SkillConfigRequest: Codable {
        let projectId: Int
        let enabledSkills: [String]

        enum CodingKeys: String, CodingKey {
            case projectId = "project_id"
            case enabledSkills = "enabled_skills"
        }
    }

    // MARK: - API Methods

    func getAvailableSkills() async throws -> AvailableSkillsResponse {
        let url = URL(string: "\(baseURL)/api/skills/available")!
        var request = URLRequest(url: url)
        request.httpMethod = "GET"

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw URLError(.badServerResponse)
        }

        guard httpResponse.statusCode == 200 else {
            throw URLError(.badServerResponse)
        }

        return try JSONDecoder().decode(AvailableSkillsResponse.self, from: data)
    }

    func getSkillConfig(projectId: Int) async throws -> SkillConfigResponse {
        let url = URL(string: "\(baseURL)/api/skills/config/\(projectId)")!
        var request = URLRequest(url: url)
        request.httpMethod = "GET"

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw URLError(.badServerResponse)
        }

        guard httpResponse.statusCode == 200 else {
            throw URLError(.badServerResponse)
        }

        return try JSONDecoder().decode(SkillConfigResponse.self, from: data)
    }

    func updateSkillConfig(projectId: Int, enabledSkills: [String]) async throws -> SkillConfigResponse {
        let url = URL(string: "\(baseURL)/api/skills/config")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let configRequest = SkillConfigRequest(projectId: projectId, enabledSkills: enabledSkills)
        request.httpBody = try JSONEncoder().encode(configRequest)

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw URLError(.badServerResponse)
        }

        guard httpResponse.statusCode == 200 else {
            throw URLError(.badServerResponse)
        }

        return try JSONDecoder().decode(SkillConfigResponse.self, from: data)
    }
}

// ========================================
// Native 版本的扩展功能
// ========================================
// TODO: 手动审查并整合以下功能

/*


class SkillService {
    static let shared = SkillService()
    private var baseURL: String { APIConfig.serverURL }

    private init() {}

    // MARK: - Models

    struct SkillInfo: Codable, Identifiable {
        let id: String
        let name: String
        let description: String
        let dimensions: [String]
        let defaultEnabled: Bool

        enum CodingKeys: String, CodingKey {
            case id, name, description, dimensions
            case defaultEnabled = "default_enabled"
        }
    }

    struct AvailableSkillsResponse: Codable {
        let skills: [SkillInfo]
        let total: Int
    }

    struct SkillConfigResponse: Codable {
        let projectId: Int
        let enabledSkills: [String]
        let availableSkills: [SkillInfo]

        enum CodingKeys: String, CodingKey {
            case projectId = "project_id"
            case enabledSkills = "enabled_skills"
            case availableSkills = "available_skills"
        }
    }

    struct SkillConfigRequest: Codable {
        let projectId: Int
        let enabledSkills: [String]

        enum CodingKeys: String, CodingKey {
            case projectId = "project_id"
            case enabledSkills = "enabled_skills"
        }
    }

    // MARK: - API Methods

    func getAvailableSkills() async throws -> AvailableSkillsResponse {
        let url = URL(string: "\(baseURL)/api/skills/available")!
        var request = URLRequest(url: url)
        request.httpMethod = "GET"

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw URLError(.badServerResponse)
        }

        guard httpResponse.statusCode == 200 else {
            throw URLError(.badServerResponse)
        }

        return try JSONDecoder().decode(AvailableSkillsResponse.self, from: data)
    }

    func getSkillConfig(projectId: Int) async throws -> SkillConfigResponse {
        let url = URL(string: "\(baseURL)/api/skills/config/\(projectId)")!
        var request = URLRequest(url: url)
        request.httpMethod = "GET"

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw URLError(.badServerResponse)
        }

        guard httpResponse.statusCode == 200 else {
            throw URLError(.badServerResponse)
        }

        return try JSONDecoder().decode(SkillConfigResponse.self, from: data)
    }

    func updateSkillConfig(projectId: Int, enabledSkills: [String]) async throws -> SkillConfigResponse {
        let url = URL(string: "\(baseURL)/api/skills/config")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let configRequest = SkillConfigRequest(projectId: projectId, enabledSkills: enabledSkills)
        request.httpBody = try JSONEncoder().encode(configRequest)

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw URLError(.badServerResponse)
        }

        guard httpResponse.statusCode == 200 else {
            throw URLError(.badServerResponse)
        }

        return try JSONDecoder().decode(SkillConfigResponse.self, from: data)
    }
}
*/

