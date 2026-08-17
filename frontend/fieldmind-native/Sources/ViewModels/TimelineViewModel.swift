import Foundation
import SwiftUI

@MainActor
class TimelineViewModel: ObservableObject {
    // MARK: - Published Properties

    @Published var events: [TimelineEventResponse] = []
    @Published var stats: TimelineStatsResponse?
    @Published var groupedTimeline: GroupedTimelineResponse?

    @Published var isLoadingEvents = false
    @Published var isLoadingStats = false
    @Published var isBuilding = false

    @Published var errorMessage: String?
    @Published var successMessage: String?

    // MARK: - Filter State

    @Published var startDate: String?
    @Published var endDate: String?
    @Published var selectedCategory: String?

    // MARK: - Service

    private let service = TimelineService.shared

    // MARK: - Public Methods

    /// 加载时间线事件
    func loadEvents(projectId: Int, limit: Int = 100) async {
        isLoadingEvents = true
        errorMessage = nil

        do {
            let response = try await service.getTimelineEvents(
                projectId: projectId,
                startDate: startDate,
                endDate: endDate,
                category: selectedCategory,
                limit: limit
            )

            self.events = response.events
        } catch {
            self.errorMessage = "加载事件失败: \(error.localizedDescription)"
        }

        isLoadingEvents = false
    }

    /// 加载统计信息
    func loadStats(projectId: Int) async {
        isLoadingStats = true
        errorMessage = nil

        do {
            let stats = try await service.getTimelineStats(projectId: projectId)
            self.stats = stats
        } catch {
            self.errorMessage = "加载统计失败: \(error.localizedDescription)"
        }

        isLoadingStats = false
    }

    /// 构建时间线（从文档提取事件）
    func buildTimeline(projectId: Int, documentIds: [Int]? = nil, forceRebuild: Bool = false) async {
        isBuilding = true
        errorMessage = nil
        successMessage = nil

        do {
            let response = try await service.buildTimeline(
                projectId: projectId,
                documentIds: documentIds,
                forceRebuild: forceRebuild
            )

            self.successMessage = response.message

            // 重新加载数据
            await loadEvents(projectId: projectId)
            await loadStats(projectId: projectId)
        } catch {
            self.errorMessage = "构建时间线失败: \(error.localizedDescription)"
        }

        isBuilding = false
    }

    /// 加载分组时间线（旧API）
    func loadGroupedTimeline(projectId: Int, groupBy: String = "year") async {
        isLoadingEvents = true
        errorMessage = nil

        do {
            let response = try await service.getGroupedTimeline(
                projectId: projectId,
                groupBy: groupBy
            )

            self.groupedTimeline = response
        } catch {
            self.errorMessage = "加载分组时间线失败: \(error.localizedDescription)"
        }

        isLoadingEvents = false
    }

    /// 加载所有数据
    func loadAllData(projectId: Int) async {
        await loadEvents(projectId: projectId)
        await loadStats(projectId: projectId)
    }

    /// 应用过滤条件
    func applyFilters(projectId: Int, startDate: String?, endDate: String?, category: String?) async {
        self.startDate = startDate
        self.endDate = endDate
        self.selectedCategory = category

        await loadEvents(projectId: projectId)
    }

    /// 清除过滤条件
    func clearFilters(projectId: Int) async {
        self.startDate = nil
        self.endDate = nil
        self.selectedCategory = nil

        await loadEvents(projectId: projectId)
    }

    // MARK: - Helper Methods

    /// 按年份分组事件
    func eventsByYear() -> [Int: [TimelineEventResponse]] {
        var grouped: [Int: [TimelineEventResponse]] = [:]

        for event in events {
            // Parse year from date string (YYYY-MM-DD or ISO8601)
            if let year = extractYear(from: event.date) {
                if grouped[year] == nil {
                    grouped[year] = []
                }
                grouped[year]?.append(event)
            }
        }

        return grouped
    }

    /// 按类别分组事件
    func eventsByCategory() -> [String: [TimelineEventResponse]] {
        var grouped: [String: [TimelineEventResponse]] = [:]

        for event in events {
            let category = event.category ?? "uncategorized"
            if grouped[category] == nil {
                grouped[category] = []
            }
            grouped[category]?.append(event)
        }

        return grouped
    }

    /// 提取年份
    private func extractYear(from dateString: String) -> Int? {
        // Handle ISO8601 format (2024-03-15T10:30:00Z)
        if let date = ISO8601DateFormatter().date(from: dateString) {
            let calendar = Calendar.current
            return calendar.component(.year, from: date)
        }

        // Handle simple YYYY-MM-DD format
        if let year = dateString.split(separator: "-").first {
            return Int(year)
        }

        return nil
    }

    /// 获取日期范围描述
    func dateRangeDescription() -> String? {
        guard let dateRange = stats?.dateRange else { return nil }
        return "\(dateRange.start) 至 \(dateRange.end)"
    }

    /// 获取类别统计列表
    func categoryStats() -> [(category: String, count: Int)] {
        guard let categories = stats?.categories else { return [] }
        return categories.map { ($0.key, $0.value) }
            .sorted { $0.count > $1.count }
    }
}
