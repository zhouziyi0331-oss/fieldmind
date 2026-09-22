import Foundation

// MARK: - Response Models

struct BusinessAnalysisResponse: Codable {
    let projectId: Int
    let existingFormats: [ExistingFormat]
    let suggestedFormats: [SuggestedFormat]
    let synergyAnalysis: String
    let recommendations: [String]
}

struct ExistingFormat: Codable, Identifiable {
    var id: String { name }
    let name: String
    let status: String
    let scale: String
    let description: String
}

struct SuggestedFormat: Codable, Identifiable {
    var id: String { name }
    let name: String
    let feasibilityScore: Int
    let reason: String
    let investment: String
    let revenuePotential: String
    let riskPoints: [String]
    let requiredConditions: [String]
    let evidence: [String]
    let implementationSteps: [String]
}

struct ExistingFormatsResponse: Codable {
    let projectId: Int
    let existingFormats: [ExistingFormat]
}

struct SynergyResponse: Codable {
    let projectId: Int
    let synergy: String
}

// MARK: - Business Analysis Service


class BusinessAnalysisService {
    static let shared = BusinessAnalysisService()
    private var baseURL: String { APIConfig.serverURL }

    private init() {}

    /// 执行完整业态分析
    func analyzeBusinessFormats(projectId: Int) async throws -> BusinessAnalysisResponse {
        let url = URL(string: "\(baseURL)/projects/\(projectId)/analyze")!
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
        return try decoder.decode(BusinessAnalysisResponse.self, from: data)
    }
}
