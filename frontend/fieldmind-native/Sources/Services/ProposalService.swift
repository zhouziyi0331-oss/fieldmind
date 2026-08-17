import Foundation

class ProposalService {
    static let shared = ProposalService()
    private let baseURL = "http://localhost:8000"

    private init() {}

    // MARK: - Models

    struct ProposalTemplate: Codable, Identifiable {
        let id: String
        let name: String
        let description: String
        let sections: [String]
    }

    struct TemplatesResponse: Codable {
        let templates: [ProposalTemplate]
    }

    struct GenerateProposalRequest: Codable {
        let proposalType: String
        let includeBudget: Bool
        let includeRisk: Bool

        enum CodingKeys: String, CodingKey {
            case proposalType = "proposal_type"
            case includeBudget = "include_budget"
            case includeRisk = "include_risk"
        }
    }

    struct ProposalSection: Codable {
        let title: String
        let content: String
    }

    struct ProposalData: Codable {
        let title: String
        let proposalType: String
        let generatedAt: String
        let sections: [ProposalSection]

        enum CodingKeys: String, CodingKey {
            case title
            case proposalType = "proposal_type"
            case generatedAt = "generated_at"
            case sections
        }
    }

    struct GenerateProposalResponse: Codable {
        let success: Bool
        let proposal: ProposalData
    }

    // MARK: - API Methods

    func generateProposal(projectId: Int, proposalType: String, includeBudget: Bool, includeRisk: Bool) async throws -> GenerateProposalResponse {
        let url = URL(string: "\(baseURL)/proposal/projects/\(projectId)/generate")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let requestBody = GenerateProposalRequest(
            proposalType: proposalType,
            includeBudget: includeBudget,
            includeRisk: includeRisk
        )

        let encoder = JSONEncoder()
        request.httpBody = try encoder.encode(requestBody)

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw URLError(.badServerResponse)
        }

        guard httpResponse.statusCode == 200 else {
            throw URLError(.badServerResponse)
        }

        let decoder = JSONDecoder()
        return try decoder.decode(GenerateProposalResponse.self, from: data)
    }

    func getTemplates(projectId: Int) async throws -> TemplatesResponse {
        let url = URL(string: "\(baseURL)/proposal/projects/\(projectId)/templates")!
        var request = URLRequest(url: url)
        request.httpMethod = "GET"

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw URLError(.badServerResponse)
        }

        guard httpResponse.statusCode == 200 else {
            throw URLError(.badServerResponse)
        }

        let decoder = JSONDecoder()
        return try decoder.decode(TemplatesResponse.self, from: data)
    }
}
