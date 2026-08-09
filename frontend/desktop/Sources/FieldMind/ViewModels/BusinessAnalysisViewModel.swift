import Foundation
import SwiftUI

@MainActor
class BusinessAnalysisViewModel: ObservableObject {
    @Published var analysisResults: BusinessAnalysisResponse?
    @Published var isAnalyzing = false
    @Published var showError = false
    @Published var errorMessage = ""

    private let apiService = APIService.shared
    var appState: AppState?

    func analyzeBusiness() async {
        isAnalyzing = true
        defer { isAnalyzing = false }

        do {
            // 获取当前项目 ID
            guard let projectId = appState?.currentProject?.id else {
                showError(message: "请先选择一个项目")
                return
            }

            let results = try await apiService.analyzeBusiness(projectId: projectId)

            self.analysisResults = results
        } catch {
            showError(message: "分析失败: \(error.localizedDescription)")
        }
    }

    func clearResults() {
        analysisResults = nil
    }

    private func showError(message: String) {
        errorMessage = message
        showError = true
    }
}
