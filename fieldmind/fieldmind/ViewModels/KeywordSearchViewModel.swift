import Foundation
import SwiftUI

@MainActor
class KeywordSearchViewModel: ObservableObject {
    @Published var searchResults: KeywordSearchService.SearchResponse?
    @Published var topKeywords: [KeywordSearchService.KeywordInfo] = []
    @Published var isSearching = false
    @Published var isLoadingKeywords = false
    @Published var errorMessage: String?
    @Published var successMessage: String?
    @Published var hasSearched = false

    // Search filters
    @Published var includeVideos = true
    @Published var includeAudios = true
    @Published var includeDocuments = true

    func searchKeyword(projectId: Int, keyword: String) async {
        guard !keyword.trimmingCharacters(in: .whitespaces).isEmpty else {
            errorMessage = "请输入搜索关键词"
            return
        }

        isSearching = true
        errorMessage = nil
        hasSearched = false

        do {
            let response = try await KeywordSearchService.shared.searchKeyword(
                projectId: projectId,
                keyword: keyword,
                includeVideos: includeVideos,
                includeAudios: includeAudios,
                includeDocuments: includeDocuments
            )
            searchResults = response
            hasSearched = true

            if response.totalMentions == 0 {
                successMessage = "未找到相关结果"
            } else {
                successMessage = "找到 \(response.totalMentions) 处提及"
            }
        } catch {
            errorMessage = "搜索失败: \(error.localizedDescription)"
            searchResults = nil
        }

        isSearching = false
    }

    func loadTopKeywords(projectId: Int, limit: Int = 50) async {
        isLoadingKeywords = true
        errorMessage = nil

        do {
            let response = try await KeywordSearchService.shared.getTopKeywords(
                projectId: projectId,
                limit: limit
            )
            topKeywords = response.keywords
        } catch {
            errorMessage = "加载热门关键词失败: \(error.localizedDescription)"
        }

        isLoadingKeywords = false
    }

    func clearSearch() {
        searchResults = nil
        hasSearched = false
        errorMessage = nil
        successMessage = nil
    }

    // Computed properties
    var totalResults: Int {
        searchResults?.totalMentions ?? 0
    }

    var videoCount: Int {
        searchResults?.videoTimestamps.count ?? 0
    }

    var audioCount: Int {
        searchResults?.audioTimestamps.count ?? 0
    }

    var documentCount: Int {
        searchResults?.documents.count ?? 0
    }

    var hasResults: Bool {
        guard let results = searchResults else { return false }
        return results.totalMentions > 0
    }
}
