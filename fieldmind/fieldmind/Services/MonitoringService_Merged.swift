//
//  MonitoringService_Merged.swift
//  FieldMind
//
//  深度整合 - 合并自主版本和 Native 版本
//  Generated: Sat Sep 19 11:21:00 CST 2026
//

import Foundation

// ========================================
// 主实现（来自主项目）
// ========================================



class MonitoringService {
    static let shared = MonitoringService()
    private var baseURL: String { APIConfig.baseURL }

    private init() {}
    private(set) var lastRequestURL: String?

    // MARK: - Models

    struct HealthResponse: Codable {
        let status: String
        let timestamp: String
        let components: ComponentsHealth

        struct ComponentsHealth: Codable {
            let api: String
            let database: String
            let disk: String
        }
    }

    struct MetricsResponse: Codable {
        let timestamp: String
        let system: SystemMetrics
        let process: ProcessMetrics

        struct SystemMetrics: Codable {
            let cpuPercent: Double
            let memoryPercent: Double
            let memoryAvailableGb: Double
            let diskPercent: Double
            let diskFreeGb: Double

            enum CodingKeys: String, CodingKey {
                case cpuPercent = "cpu_percent"
                case memoryPercent = "memory_percent"
                case memoryAvailableGb = "memory_available_gb"
                case diskPercent = "disk_percent"
                case diskFreeGb = "disk_free_gb"
            }
        }

        struct ProcessMetrics: Codable {
            let pid: Int
            let memoryMb: Double
            let numThreads: Int

            enum CodingKeys: String, CodingKey {
                case pid
                case memoryMb = "memory_mb"
                case numThreads = "num_threads"
            }
        }
    }

    struct LogsResponse: Codable {
        let lines: [String]
        let logs: [String]
        let events: [RemoteLogEvent]
        let totalLines: Int
        let logFile: String?

        enum CodingKeys: String, CodingKey {
            case lines
            case logs
            case events
            case totalLines = "total_lines"
            case logFile = "log_file"
        }

        init(from decoder: Decoder) throws {
            let container = try decoder.container(keyedBy: CodingKeys.self)
            lines = try container.decodeIfPresent([String].self, forKey: .lines)
                ?? container.decodeIfPresent([String].self, forKey: .logs)
                ?? []
            logs = try container.decodeIfPresent([String].self, forKey: .logs) ?? lines
            events = try container.decodeIfPresent([RemoteLogEvent].self, forKey: .events) ?? []
            totalLines = try container.decodeIfPresent(Int.self, forKey: .totalLines) ?? lines.count
            logFile = try container.decodeIfPresent(String.self, forKey: .logFile)
        }
    }

    struct RemoteLogEvent: Codable, Identifiable {
        let id = UUID()
        let timestamp: Date?
        let level: String
        let source: String
        let category: String
        let message: String
        let details: String?
        let requestID: String?
        let requestURL: String?
        let statusCode: Int?

        enum CodingKeys: String, CodingKey {
            case timestamp, level, source, category, message, details
            case requestID = "request_id"
            case requestURL = "request_url"
            case statusCode = "status_code"
        }

        init(from decoder: Decoder) throws {
            let c = try decoder.container(keyedBy: CodingKeys.self)
            level = try c.decodeIfPresent(String.self, forKey: .level) ?? "INFO"
            source = try c.decodeIfPresent(String.self, forKey: .source) ?? "backend"
            category = try c.decodeIfPresent(String.self, forKey: .category) ?? "system"
            message = try c.decodeIfPresent(String.self, forKey: .message) ?? ""
            details = try c.decodeIfPresent(String.self, forKey: .details)
            requestID = try c.decodeIfPresent(String.self, forKey: .requestID)
            requestURL = try c.decodeIfPresent(String.self, forKey: .requestURL)
            statusCode = try c.decodeIfPresent(Int.self, forKey: .statusCode)
            if let value = try c.decodeIfPresent(String.self, forKey: .timestamp) {
                timestamp = MonitoringService.parseDate(value)
            } else {
                timestamp = nil
            }
        }
    }

    private static func parseDate(_ value: String) -> Date? {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        return formatter.date(from: value) ?? {
            formatter.formatOptions = [.withInternetDateTime]
            return formatter.date(from: value)
        }()
    }

    // MARK: - API Methods

    func getHealth() async throws -> HealthResponse {
        let url = URL(string: "\(baseURL)/monitoring/health")!
        lastRequestURL = url.absoluteString
        var request = URLRequest(url: url)
        request.httpMethod = "GET"

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw URLError(.badServerResponse)
        }

        guard httpResponse.statusCode == 200 else {
            throw URLError(.badServerResponse)
        }

        return try JSONDecoder().decode(HealthResponse.self, from: data)
    }

    func getMetrics() async throws -> MetricsResponse {
        let url = URL(string: "\(baseURL)/monitoring/metrics")!
        lastRequestURL = url.absoluteString
        var request = URLRequest(url: url)
        request.httpMethod = "GET"

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw URLError(.badServerResponse)
        }

        guard httpResponse.statusCode == 200 else {
            throw URLError(.badServerResponse)
        }

        return try JSONDecoder().decode(MetricsResponse.self, from: data)
    }

    func getRecentLogs(lines: Int = 100) async throws -> LogsResponse {
        let url = URL(string: "\(baseURL)/monitoring/logs/recent?lines=\(lines)")!
        lastRequestURL = url.absoluteString
        var request = URLRequest(url: url)
        request.httpMethod = "GET"

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw URLError(.badServerResponse)
        }

        guard httpResponse.statusCode == 200 else {
            throw URLError(.badServerResponse)
        }

        return try JSONDecoder().decode(LogsResponse.self, from: data)
    }
}

// ========================================
// Native 版本的扩展功能
// ========================================
// TODO: 手动审查并整合以下功能

/*


class MonitoringService {
    static let shared = MonitoringService()
    private var baseURL: String { APIConfig.baseURL }

    private init() {}
    private(set) var lastRequestURL: String?

    // MARK: - Models

    struct HealthResponse: Codable {
        let status: String
        let timestamp: String
        let components: ComponentsHealth

        struct ComponentsHealth: Codable {
            let api: String
            let database: String
            let disk: String
        }
    }

    struct MetricsResponse: Codable {
        let timestamp: String
        let system: SystemMetrics
        let process: ProcessMetrics

        struct SystemMetrics: Codable {
            let cpuPercent: Double
            let memoryPercent: Double
            let memoryAvailableGb: Double
            let diskPercent: Double
            let diskFreeGb: Double

            enum CodingKeys: String, CodingKey {
                case cpuPercent = "cpu_percent"
                case memoryPercent = "memory_percent"
                case memoryAvailableGb = "memory_available_gb"
                case diskPercent = "disk_percent"
                case diskFreeGb = "disk_free_gb"
            }
        }

        struct ProcessMetrics: Codable {
            let pid: Int
            let memoryMb: Double
            let numThreads: Int

            enum CodingKeys: String, CodingKey {
                case pid
                case memoryMb = "memory_mb"
                case numThreads = "num_threads"
            }
        }
    }

    struct LogsResponse: Codable {
        let lines: [String]
        let logs: [String]
        let events: [RemoteLogEvent]
        let totalLines: Int
        let logFile: String?

        enum CodingKeys: String, CodingKey {
            case lines
            case logs
            case events
            case totalLines = "total_lines"
            case logFile = "log_file"
        }

        init(from decoder: Decoder) throws {
            let container = try decoder.container(keyedBy: CodingKeys.self)
            lines = try container.decodeIfPresent([String].self, forKey: .lines)
                ?? container.decodeIfPresent([String].self, forKey: .logs)
                ?? []
            logs = try container.decodeIfPresent([String].self, forKey: .logs) ?? lines
            events = try container.decodeIfPresent([RemoteLogEvent].self, forKey: .events) ?? []
            totalLines = try container.decodeIfPresent(Int.self, forKey: .totalLines) ?? lines.count
            logFile = try container.decodeIfPresent(String.self, forKey: .logFile)
        }
    }

    struct RemoteLogEvent: Codable, Identifiable {
        let id = UUID()
        let timestamp: Date?
        let level: String
        let source: String
        let category: String
        let message: String
        let details: String?
        let requestID: String?
        let requestURL: String?
        let statusCode: Int?

        enum CodingKeys: String, CodingKey {
            case timestamp, level, source, category, message, details
            case requestID = "request_id"
            case requestURL = "request_url"
            case statusCode = "status_code"
        }

        init(from decoder: Decoder) throws {
            let c = try decoder.container(keyedBy: CodingKeys.self)
            level = try c.decodeIfPresent(String.self, forKey: .level) ?? "INFO"
            source = try c.decodeIfPresent(String.self, forKey: .source) ?? "backend"
            category = try c.decodeIfPresent(String.self, forKey: .category) ?? "system"
            message = try c.decodeIfPresent(String.self, forKey: .message) ?? ""
            details = try c.decodeIfPresent(String.self, forKey: .details)
            requestID = try c.decodeIfPresent(String.self, forKey: .requestID)
            requestURL = try c.decodeIfPresent(String.self, forKey: .requestURL)
            statusCode = try c.decodeIfPresent(Int.self, forKey: .statusCode)
            if let value = try c.decodeIfPresent(String.self, forKey: .timestamp) {
                timestamp = MonitoringService.parseDate(value)
            } else {
                timestamp = nil
            }
        }
    }

    private static func parseDate(_ value: String) -> Date? {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        return formatter.date(from: value) ?? {
            formatter.formatOptions = [.withInternetDateTime]
            return formatter.date(from: value)
        }()
    }

    // MARK: - API Methods

    func getHealth() async throws -> HealthResponse {
        let url = URL(string: "\(baseURL)/monitoring/health")!
        lastRequestURL = url.absoluteString
        var request = URLRequest(url: url)
        request.httpMethod = "GET"

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw URLError(.badServerResponse)
        }

        guard httpResponse.statusCode == 200 else {
            throw URLError(.badServerResponse)
        }

        return try JSONDecoder().decode(HealthResponse.self, from: data)
    }

    func getMetrics() async throws -> MetricsResponse {
        let url = URL(string: "\(baseURL)/monitoring/metrics")!
        lastRequestURL = url.absoluteString
        var request = URLRequest(url: url)
        request.httpMethod = "GET"

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw URLError(.badServerResponse)
        }

        guard httpResponse.statusCode == 200 else {
            throw URLError(.badServerResponse)
        }

        return try JSONDecoder().decode(MetricsResponse.self, from: data)
    }

    func getRecentLogs(lines: Int = 100) async throws -> LogsResponse {
        let url = URL(string: "\(baseURL)/monitoring/logs/recent?lines=\(lines)")!
        lastRequestURL = url.absoluteString
        var request = URLRequest(url: url)
        request.httpMethod = "GET"

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw URLError(.badServerResponse)
        }

        guard httpResponse.statusCode == 200 else {
            throw URLError(.badServerResponse)
        }

        return try JSONDecoder().decode(LogsResponse.self, from: data)
    }
}
*/

