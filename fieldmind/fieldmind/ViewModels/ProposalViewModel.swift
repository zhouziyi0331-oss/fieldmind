import SwiftUI

@MainActor
class ProposalViewModel: ObservableObject {
    @Published var templates: [ProposalService.ProposalTemplate] = []
    @Published var generatedProposal: ProposalService.ProposalData?
    @Published var isLoadingTemplates = false
    @Published var isGenerating = false
    @Published var errorMessage: String?
    @Published var successMessage: String?

    // Generation options
    @Published var selectedTemplateId = "government"
    @Published var includeBudget = true
    @Published var includeRisk = true

    func loadTemplates(projectId: Int) async {
        isLoadingTemplates = true
        errorMessage = nil

        do {
            let response = try await ProposalService.shared.getTemplates(projectId: projectId)
            templates = response.templates
        } catch {
            errorMessage = "加载模板失败: \(error.localizedDescription)"
        }

        isLoadingTemplates = false
    }

    func generateProposal(projectId: Int) async {
        isGenerating = true
        errorMessage = nil
        successMessage = nil

        do {
            let response = try await ProposalService.shared.generateProposal(
                projectId: projectId,
                proposalType: selectedTemplateId,
                includeBudget: includeBudget,
                includeRisk: includeRisk
            )
            generatedProposal = response.proposal
            successMessage = "提案生成成功"
        } catch {
            errorMessage = "生成提案失败: \(error.localizedDescription)"
        }

        isGenerating = false
    }

    func clearProposal() {
        generatedProposal = nil
        errorMessage = nil
        successMessage = nil
    }

    var hasProposal: Bool {
        generatedProposal != nil
    }
}
