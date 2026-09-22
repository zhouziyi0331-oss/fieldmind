import Foundation


class WorkflowService {
    static let shared = WorkflowService()
    private var baseURL: String { APIConfig.serverURL }

    private init() {}

    // MARK: - Models

    struct WorkflowExecuteRequest: Codable {
        let workflowType: String
        let projectId: Int
        let documentIds: [Int]?
        let params: [String: String]?

        enum CodingKeys: String, CodingKey {
            case workflowType = "workflow_type"
            case projectId = "project_id"
            case documentIds = "document_ids"
            case params
        }
    }

    struct WorkflowExecutionResponse: Codable {
        let workflowId: String
        let workflowName: String
        let status: String
        let message: String

        enum CodingKeys: String, CodingKey {
            case workflowId = "workflow_id"
            case workflowName = "workflow_name"
            case status
            case message
        }
    }

    struct WorkflowStatusResponse: Codable {
        let workflowId: String
        let workflowName: String
        let status: String
        let startTime: String?
        let endTime: String?
        let taskResults: [String: TaskResult]
        let metadata: [String: String]

        enum CodingKeys: String, CodingKey {
            case workflowId = "workflow_id"
            case workflowName = "workflow_name"
            case status
            case startTime = "start_time"
            case endTime = "end_time"
            case taskResults = "task_results"
            case metadata
        }
    }

    struct TaskResult: Codable {
        let status: String
        let result: String?
        let error: String?
        let duration: Double?
    }

    struct WorkflowListResponse: Codable {
        let total: Int
        let workflows: [WorkflowSummary]
    }

    struct WorkflowSummary: Codable, Identifiable {
        let workflowId: String
        let workflowName: String
        let status: String
        let startTime: String?
        let endTime: String?
        let createdAt: String
        let taskCount: Int
        let completedTasks: Int
        let failedTasks: Int

        var id: String { workflowId }

        enum CodingKeys: String, CodingKey {
            case workflowId = "workflow_id"
            case workflowName = "workflow_name"
            case status
            case startTime = "start_time"
            case endTime = "end_time"
            case createdAt = "created_at"
            case taskCount = "task_count"
            case completedTasks = "completed_tasks"
            case failedTasks = "failed_tasks"
        }
    }

    // MARK: - API Methods

    func executeWorkflow(workflowType: String, projectId: Int, documentIds: [Int]? = nil) async throws -> WorkflowExecutionResponse {
        let url = URL(string: "\(baseURL)/api/workflows/execute")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let requestBody = WorkflowExecuteRequest(
            workflowType: workflowType,
            projectId: projectId,
            documentIds: documentIds,
            params: nil
        )
        request.httpBody = try JSONEncoder().encode(requestBody)

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw NSError(domain: "WorkflowService", code: -1, userInfo: [NSLocalizedDescriptionKey: "Invalid response"])
        }

        guard httpResponse.statusCode == 200 else {
            throw NSError(domain: "WorkflowService", code: httpResponse.statusCode,
                         userInfo: [NSLocalizedDescriptionKey: "HTTP \(httpResponse.statusCode)"])
        }

        return try JSONDecoder().decode(WorkflowExecutionResponse.self, from: data)
    }

    func getWorkflowStatus(workflowId: String) async throws -> WorkflowStatusResponse {
        let url = URL(string: "\(baseURL)/api/workflows/\(workflowId)")!
        var request = URLRequest(url: url)
        request.httpMethod = "GET"

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw NSError(domain: "WorkflowService", code: -1, userInfo: [NSLocalizedDescriptionKey: "Invalid response"])
        }

        guard httpResponse.statusCode == 200 else {
            throw NSError(domain: "WorkflowService", code: httpResponse.statusCode,
                         userInfo: [NSLocalizedDescriptionKey: "HTTP \(httpResponse.statusCode)"])
        }

        return try JSONDecoder().decode(WorkflowStatusResponse.self, from: data)
    }

    func listWorkflows(status: String? = nil, limit: Int = 50) async throws -> WorkflowListResponse {
        var urlComponents = URLComponents(string: "\(baseURL)/api/workflows/")!
        var queryItems: [URLQueryItem] = []

        if let status = status {
            queryItems.append(URLQueryItem(name: "status", value: status))
        }
        queryItems.append(URLQueryItem(name: "limit", value: "\(limit)"))

        urlComponents.queryItems = queryItems

        let url = urlComponents.url!
        var request = URLRequest(url: url)
        request.httpMethod = "GET"

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw NSError(domain: "WorkflowService", code: -1, userInfo: [NSLocalizedDescriptionKey: "Invalid response"])
        }

        guard httpResponse.statusCode == 200 else {
            throw NSError(domain: "WorkflowService", code: httpResponse.statusCode,
                         userInfo: [NSLocalizedDescriptionKey: "HTTP \(httpResponse.statusCode)"])
        }

        return try JSONDecoder().decode(WorkflowListResponse.self, from: data)
    }

    func cancelWorkflow(workflowId: String) async throws {
        let url = URL(string: "\(baseURL)/api/workflows/\(workflowId)/cancel")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"

        let (_, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw NSError(domain: "WorkflowService", code: -1, userInfo: [NSLocalizedDescriptionKey: "Invalid response"])
        }

        guard httpResponse.statusCode == 200 else {
            throw NSError(domain: "WorkflowService", code: httpResponse.statusCode,
                         userInfo: [NSLocalizedDescriptionKey: "HTTP \(httpResponse.statusCode)"])
        }
    }
}
