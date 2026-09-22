import Foundation
import SwiftUI

@MainActor
class MonitoringViewModel: ObservableObject {
    @Published var health: MonitoringService.HealthResponse?
    @Published var metrics: MonitoringService.MetricsResponse?
    @Published var logs: [String] = []
    @Published var isLoadingHealth = false
    @Published var isLoadingMetrics = false
    @Published var isLoadingLogs = false
    @Published var errorMessage: String?

    func loadHealth() async {
        isLoadingHealth = true
        errorMessage = nil

        do {
            health = try await MonitoringService.shared.getHealth()
        } catch {
            errorMessage = "加载健康状态失败: \(error.localizedDescription)"
        }

        isLoadingHealth = false
    }

    func loadMetrics() async {
        isLoadingMetrics = true
        errorMessage = nil

        do {
            metrics = try await MonitoringService.shared.getMetrics()
        } catch {
            errorMessage = "加载系统指标失败: \(error.localizedDescription)"
        }

        isLoadingMetrics = false
    }

    func loadLogs(lines: Int = 100) async {
        isLoadingLogs = true
        errorMessage = nil

        do {
            let response = try await MonitoringService.shared.getRecentLogs(lines: lines)
            logs = response.lines
        } catch {
            errorMessage = "加载日志失败: \(error.localizedDescription)"
        }

        isLoadingLogs = false
    }

    func refreshAll() async {
        await loadHealth()
        await loadMetrics()
        await loadLogs(lines: 100)
    }

    // Computed properties
    var systemStatus: String {
        health?.status ?? "unknown"
    }

    var isHealthy: Bool {
        health?.status == "healthy"
    }

    var cpuUsage: Double {
        metrics?.system.cpuPercent ?? 0
    }

    var memoryUsage: Double {
        metrics?.system.memoryPercent ?? 0
    }

    var diskUsage: Double {
        metrics?.system.diskPercent ?? 0
    }

    var statusColor: Color {
        switch systemStatus {
        case "healthy": return .green
        case "degraded": return .orange
        default: return .red
        }
    }
}
