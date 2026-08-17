import SwiftUI

@MainActor
class BusinessAnalysisViewModel: ObservableObject {
    @Published var analysisResult: BusinessAnalysisResponse?
    @Published var isLoading = false
    @Published var isAnalyzing = false
    @Published var errorMessage: String?
    @Published var successMessage: String?

    func analyzeBusinessFormats(projectId: Int) async {
        isAnalyzing = true
        errorMessage = nil
        successMessage = nil

        do {
            let result = try await BusinessAnalysisService.shared.analyzeBusinessFormats(projectId: projectId)
            analysisResult = result
            successMessage = "业态分析完成"
        } catch {
            errorMessage = "分析失败: \(error.localizedDescription)"
        }

        isAnalyzing = false
    }

    func clearAnalysis() {
        analysisResult = nil
        errorMessage = nil
        successMessage = nil
    }

    var hasResults: Bool {
        analysisResult != nil
    }
}
