import Foundation
import SwiftUI

@MainActor
class KeywordSearchViewModel: ObservableObject {
    @Published var searchResults: KeywordSearchResponse?
    @Published var isSearching = false
    @Published var showError = false
    @Published var errorMessage = ""

    private let apiService = APIService.shared

    func searchKeyword(_ keyword: String) async {
        isSearching = true
        defer { isSearching = false }

        do {
            // 获取当前项目 ID（从 AppState 或其他地方）
            guard let projectId = AppState().currentProject?.id else {
                showError(message: "请先选择一个项目")
                return
            }

            let results = try await apiService.searchKeyword(
                projectId: projectId,
                keyword: keyword,
                includeVideos: true,
                includeAudios: true,
                includeDocuments: true
            )

            self.searchResults = results
        } catch {
            showError(message: "搜索失败: \(error.localizedDescription)")
        }
    }

    func clearResults() {
        searchResults = nil
    }

    private func showError(message: String) {
        errorMessage = message
        showError = true
    }
}
