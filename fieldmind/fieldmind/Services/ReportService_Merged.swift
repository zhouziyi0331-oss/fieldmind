//
//  ReportService_Merged.swift
//  FieldMind
//
//  深度整合 - 合并自主版本和 Native 版本
//  Generated: Sat Sep 19 11:21:01 CST 2026
//

import Foundation

// ========================================
// 主实现（来自主项目）
// ========================================



class ReportService {
    static let shared = ReportService()
    private var baseURL: String { APIConfig.serverURL }

    private init() {}

    // MARK: - Models

    struct ReportRequest: Codable {
        let projectId: Int
        let documentIds: [Int]?
        let reportLevel: Int

        enum CodingKeys: String, CodingKey {
            case projectId = "project_id"
            case documentIds = "document_ids"
            case reportLevel = "report_level"
        }
    }

    struct ReportResponse: Codable {
        let success: Bool
        let reportLevel: Int
        let reportContent: String
        let documentsUsed: Int
        let generationMethod: String
        let message: String?

        enum CodingKeys: String, CodingKey {
            case success
            case reportLevel = "report_level"
            case reportContent = "report_content"
            case documentsUsed = "documents_used"
            case generationMethod = "generation_method"
            case message
        }
    }

    struct ReportPreviewResponse: Codable {
        let preview: String
        let estimatedLength: Int
        let sections: [String]

        enum CodingKeys: String, CodingKey {
            case preview
            case estimatedLength = "estimated_length"
            case sections
        }
    }

    // MARK: - API Methods

    func generateReport(projectId: Int, documentIds: [Int]?, reportLevel: Int) async throws -> ReportResponse {
        let url = URL(string: "\(baseURL)/api/reports/generate")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let requestBody = ReportRequest(
            projectId: projectId,
            documentIds: documentIds,
            reportLevel: reportLevel
        )
        request.httpBody = try JSONEncoder().encode(requestBody)

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw NSError(domain: "ReportService", code: -1, userInfo: [NSLocalizedDescriptionKey: "Invalid response"])
        }

        guard httpResponse.statusCode == 200 else {
            throw NSError(domain: "ReportService", code: httpResponse.statusCode,
                         userInfo: [NSLocalizedDescriptionKey: "HTTP \(httpResponse.statusCode)"])
        }

        return try JSONDecoder().decode(ReportResponse.self, from: data)
    }

    func previewReport(reportLevel: Int) async throws -> ReportPreviewResponse {
        let url = URL(string: "\(baseURL)/api/reports/preview/\(reportLevel)")!
        var request = URLRequest(url: url)
        request.httpMethod = "GET"

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw NSError(domain: "ReportService", code: -1, userInfo: [NSLocalizedDescriptionKey: "Invalid response"])
        }

        guard httpResponse.statusCode == 200 else {
            throw NSError(domain: "ReportService", code: httpResponse.statusCode,
                         userInfo: [NSLocalizedDescriptionKey: "HTTP \(httpResponse.statusCode)"])
        }

        return try JSONDecoder().decode(ReportPreviewResponse.self, from: data)
    }
}

// ========================================
// Native 版本的扩展功能
// ========================================
// TODO: 手动审查并整合以下功能

/*


class ReportService {
    static let shared = ReportService()
    private var baseURL: String { APIConfig.serverURL }

    private init() {}

    // MARK: - Models

    struct ReportRequest: Codable {
        let projectId: Int
        let documentIds: [Int]?
        let reportLevel: Int

        enum CodingKeys: String, CodingKey {
            case projectId = "project_id"
            case documentIds = "document_ids"
            case reportLevel = "report_level"
        }
    }

    struct ReportResponse: Codable {
        let success: Bool
        let reportLevel: Int
        let reportContent: String
        let documentsUsed: Int
        let generationMethod: String
        let message: String?

        enum CodingKeys: String, CodingKey {
            case success
            case reportLevel = "report_level"
            case reportContent = "report_content"
            case documentsUsed = "documents_used"
            case generationMethod = "generation_method"
            case message
        }
    }

    struct ReportPreviewResponse: Codable {
        let preview: String
        let estimatedLength: Int
        let sections: [String]

        enum CodingKeys: String, CodingKey {
            case preview
            case estimatedLength = "estimated_length"
            case sections
        }
    }

    // MARK: - API Methods

    func generateReport(projectId: Int, documentIds: [Int]?, reportLevel: Int) async throws -> ReportResponse {
        let url = URL(string: "\(baseURL)/api/reports/generate")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let requestBody = ReportRequest(
            projectId: projectId,
            documentIds: documentIds,
            reportLevel: reportLevel
        )
        request.httpBody = try JSONEncoder().encode(requestBody)

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw NSError(domain: "ReportService", code: -1, userInfo: [NSLocalizedDescriptionKey: "Invalid response"])
        }

        guard httpResponse.statusCode == 200 else {
            throw NSError(domain: "ReportService", code: httpResponse.statusCode,
                         userInfo: [NSLocalizedDescriptionKey: "HTTP \(httpResponse.statusCode)"])
        }

        return try JSONDecoder().decode(ReportResponse.self, from: data)
    }

    func previewReport(reportLevel: Int) async throws -> ReportPreviewResponse {
        let url = URL(string: "\(baseURL)/api/reports/preview/\(reportLevel)")!
        var request = URLRequest(url: url)
        request.httpMethod = "GET"

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw NSError(domain: "ReportService", code: -1, userInfo: [NSLocalizedDescriptionKey: "Invalid response"])
        }

        guard httpResponse.statusCode == 200 else {
            throw NSError(domain: "ReportService", code: httpResponse.statusCode,
                         userInfo: [NSLocalizedDescriptionKey: "HTTP \(httpResponse.statusCode)"])
        }

        return try JSONDecoder().decode(ReportPreviewResponse.self, from: data)
    }
}
*/

