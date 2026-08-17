import Foundation
import SwiftUI

@MainActor
class DashboardViewModel: ObservableObject {
    @Published var stats: DashboardStats?
    @Published var timeline: TimelineResponse?
    @Published var progress: ProgressResponse?
    @Published var isLoadingStats = false
    @Published var isLoadingTimeline = false
    @Published var isLoadingProgress = false
    @Published var errorMessage: String?

    private let dashboardService = DashboardService()

    /// 加载所有仪表盘数据
    func loadAllData(projectId: Int) async {
        await loadStats(projectId: projectId)
        await loadTimeline(projectId: projectId, days: 7)
        await loadProgress(projectId: projectId)
    }

    /// 加载统计数据
    func loadStats(projectId: Int) async {
        isLoadingStats = true
        errorMessage = nil

        do {
            let response = try await dashboardService.fetchDashboardStats(projectId: String(projectId))
            self.stats = response
        } catch {
            self.errorMessage = "加载统计数据失败: \(error.localizedDescription)"
        }

        isLoadingStats = false
    }

    /// 加载时间线数据
    func loadTimeline(projectId: Int, days: Int) async {
        isLoadingTimeline = true

        do {
            let response = try await dashboardService.fetchTimeline(projectId: String(projectId), days: days)
            self.timeline = response
        } catch {
            // 时间线加载失败不显示错误，保持静默
        }

        isLoadingTimeline = false
    }

    /// 加载进度数据
    func loadProgress(projectId: Int) async {
        isLoadingProgress = true

        do {
            let response = try await dashboardService.fetchProgress(projectId: String(projectId))
            self.progress = response
        } catch {
            // 进度加载失败不显示错误，保持静默
        }

        isLoadingProgress = false
    }

    /// 刷新所有数据
    func refresh(projectId: Int) async {
        await loadAllData(projectId: projectId)
    }
}
