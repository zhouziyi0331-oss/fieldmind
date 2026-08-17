import Foundation

class MonitoringService {
    static let shared = MonitoringService()
    private let baseURL = "http://localhost:8000"

    private init() {}

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
        let totalLines: Int

        enum CodingKeys: String, CodingKey {
            case lines
            case totalLines = "total_lines"
        }
    }

    // MARK: - API Methods

    func getHealth() async throws -> HealthResponse {
        let url = URL(string: "\(baseURL)/monitoring/health")!
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
