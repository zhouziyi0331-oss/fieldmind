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
            print("📊 [DashboardViewModel] 开始加载项目 \(projectId) 的统计数据")
            let response = try await dashboardService.fetchDashboardStats(projectId: String(projectId))
            print("✅ [DashboardViewModel] 成功获取统计数据: totalDocs=\(response.totalDocuments)")
            self.stats = response
            print("✅ [DashboardViewModel] stats已设置")
        } catch {
            let errorDesc = "\(error)"
            print("❌ [DashboardViewModel] 加载统计数据失败: \(errorDesc)")
            self.errorMessage = "加载统计数据失败: \(errorDesc)"
        }

        isLoadingStats = false
        print("📊 [DashboardViewModel] loadStats完成, isLoadingStats=\(isLoadingStats), stats=\(stats != nil ? "有数据" : "nil")")
    }

    /// 加载时间线数据
    func loadTimeline(projectId: Int, days: Int) async {
        isLoadingTimeline = true

        do {
            print("📈 [DashboardViewModel] 开始加载项目 \(projectId) 的时间线数据")
            let response = try await dashboardService.fetchTimeline(projectId: String(projectId), days: days)
            self.timeline = response
            print("✅ [DashboardViewModel] 成功加载时间线数据")
        } catch {
            let errorDesc = "\(error)"
            print("❌ [DashboardViewModel] 加载时间线数据失败: \(errorDesc)")
            // 时间线加载失败不显示错误，保持静默
        }

        isLoadingTimeline = false
    }

    /// 加载进度数据
    func loadProgress(projectId: Int) async {
        isLoadingProgress = true

        do {
            print("📊 [DashboardViewModel] 开始加载项目 \(projectId) 的进度数据")
            let response = try await dashboardService.fetchProgress(projectId: String(projectId))
            self.progress = response
            print("✅ [DashboardViewModel] 成功加载进度数据")
        } catch {
            let errorDesc = "\(error)"
            print("❌ [DashboardViewModel] 加载进度数据失败: \(errorDesc)")
            // 进度加载失败不显示错误，保持静默
        }

        isLoadingProgress = false
    }

    /// 刷新所有数据
    func refresh(projectId: Int) async {
        await loadAllData(projectId: projectId)
    }
}
