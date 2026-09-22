import Foundation
import SwiftUI

@MainActor
class VeinViewModel: ObservableObject {
    @Published var contexts: [VeinService.ProjectContext] = []
    @Published var selectedContext: VeinService.ProjectContext?
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published var successMessage: String?

    func loadContexts(projectId: Int, level: Int? = nil) async {
        isLoading = true
        errorMessage = nil

        do {
            let result = try await VeinService.shared.listContexts(projectId: projectId, level: level)
            contexts = result
        } catch {
            errorMessage = "加载知识脉络失败: \(error.localizedDescription)"
        }

        isLoading = false
    }

    func loadContextDetail(projectId: Int, contextId: Int) async {
        errorMessage = nil

        do {
            let context = try await VeinService.shared.getContext(projectId: projectId, contextId: contextId)
            selectedContext = context
        } catch {
            errorMessage = "加载节点详情失败: \(error.localizedDescription)"
        }
    }

    var hasContexts: Bool {
        !contexts.isEmpty
    }

    func filterContexts(searchText: String) -> [VeinService.ProjectContext] {
        if searchText.isEmpty {
            return contexts
        }
        return contexts.filter { context in
            context.name.localizedCaseInsensitiveContains(searchText) ||
            (context.description?.localizedCaseInsensitiveContains(searchText) ?? false) ||
            context.keywords.contains { $0.localizedCaseInsensitiveContains(searchText) }
        }
    }

    func contextsByLevel() -> [Int: [VeinService.ProjectContext]] {
        Dictionary(grouping: contexts, by: { $0.level })
    }
}
