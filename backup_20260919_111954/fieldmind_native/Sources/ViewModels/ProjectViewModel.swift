import Foundation
import SwiftUI

@MainActor
class ProjectViewModel: ObservableObject {
    @Published var dashboard: ProjectService.ProjectDashboardResponse?
    @Published var contexts: [ProjectService.ProjectContext] = []
    @Published var isLoadingDashboard = false
    @Published var isLoadingContexts = false
    @Published var errorMessage: String?
    @Published var successMessage: String?

    func loadDashboard(projectId: Int) async {
        isLoadingDashboard = true
        errorMessage = nil

        do {
            let result = try await ProjectService.shared.getProjectDashboard(projectId: projectId)
            dashboard = result
        } catch {
            errorMessage = "加载项目数据失败: \(error.localizedDescription)"
        }

        isLoadingDashboard = false
    }

    func loadContexts(projectId: Int) async {
        isLoadingContexts = true
        errorMessage = nil

        do {
            let result = try await ProjectService.shared.listContexts(projectId: projectId)
            contexts = result
        } catch {
            errorMessage = "加载知识脉络失败: \(error.localizedDescription)"
        }

        isLoadingContexts = false
    }

    var hasDashboard: Bool {
        dashboard != nil
    }

    var hasContexts: Bool {
        !contexts.isEmpty
    }
}
