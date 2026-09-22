//
//  ChronicleViewModel_Merged.swift
//  FieldMind
//
//  深度整合 - 合并自主版本和 Native 版本
//  Generated: Sat Sep 19 11:21:01 CST 2026
//

import Foundation

// ========================================
// 主实现（来自主项目）
// ========================================


/// Chronicle ViewModel - 管理事件编年数据
@MainActor
class ChronicleViewModel: ObservableObject {
    @Published var events: [TimelineEventResponse] = []
    @Published var stats: TimelineStatsResponse?
    @Published var isLoadingEvents = false
    @Published var isLoadingStats = false
    @Published var errorMessage: String?
    @Published var successMessage: String?

    // 筛选条件
    @Published var searchText: String = ""
    @Published var selectedCategory: String?
    @Published var startDate: String?
    @Published var endDate: String?

    private let timelineService = TimelineService.shared

    // MARK: - Data Loading

    /// 加载事件列表
    func loadEvents(projectId: Int, limit: Int = 200) async {
        isLoadingEvents = true
        errorMessage = nil

        do {
            let response = try await timelineService.getTimelineEvents(
                projectId: projectId,
                startDate: startDate,
                endDate: endDate,
                category: selectedCategory,
                limit: limit
            )
            events = response.events
            successMessage = nil
        } catch {
            errorMessage = "加载事件失败: \(error.localizedDescription)"
            print("❌ ChronicleViewModel.loadEvents error: \(error)")
        }

        isLoadingEvents = false
    }

    /// 加载统计信息
    func loadStats(projectId: Int) async {
        isLoadingStats = true

        do {
            stats = try await timelineService.getTimelineStats(projectId: projectId)
        } catch {
            print("⚠️ ChronicleViewModel.loadStats error: \(error)")
        }

        isLoadingStats = false
    }

    /// 加载所有数据（事件+统计）
    func loadAllData(projectId: Int) async {
        await loadEvents(projectId: projectId)
        await loadStats(projectId: projectId)
    }

    /// 应用筛选条件
    func applyFilters(projectId: Int, searchText: String?, startDate: String?, endDate: String?, category: String?) async {
        self.searchText = searchText ?? ""
        self.startDate = startDate
        self.endDate = endDate
        self.selectedCategory = category

        await loadEvents(projectId: projectId)
    }

    /// 清除筛选条件
    func clearFilters(projectId: Int) async {
        searchText = ""
        startDate = nil
        endDate = nil
        selectedCategory = nil

        await loadEvents(projectId: projectId)
    }

    // MARK: - Computed Properties

    /// 获取过滤后的事件（客户端搜索）
    func filteredEvents() -> [TimelineEventResponse] {
        guard !searchText.isEmpty else { return events }

        let lowercased = searchText.lowercased()
        return events.filter { event in
            event.title.lowercased().contains(lowercased) ||
            (event.description?.lowercased().contains(lowercased) ?? false)
        }
    }

    /// 按年份分组
    func eventsByYear() -> [Int: [TimelineEventResponse]] {
        let filtered = filteredEvents()
        var grouped: [Int: [TimelineEventResponse]] = [:]

        for event in filtered {
            let year = extractYear(from: event.date)
            grouped[year, default: []].append(event)
        }

        return grouped
    }

    /// 按类别分组
    func eventsByCategory() -> [String: [TimelineEventResponse]] {
        let filtered = filteredEvents()
        var grouped: [String: [TimelineEventResponse]] = [:]

        for event in filtered {
            let category = event.category ?? "未分类"
            grouped[category, default: []].append(event)
        }

        return grouped
    }

    /// 获取年份列表（降序）
    func getYears() -> [Int] {
        let grouped = eventsByYear()
        return grouped.keys.sorted(by: >)
    }

    /// 获取类别统计
    func categoryStats() -> [(category: String, count: Int)] {
        let grouped = eventsByCategory()
        return grouped.map { (category: $0.key, count: $0.value.count) }
            .sorted { $0.count > $1.count }
    }

    /// 获取日期范围描述
    func dateRangeDescription() -> String? {
        guard let start = startDate, let end = endDate else { return nil }
        return "\(start) 至 \(end)"
    }

    // MARK: - Helper Methods

    /// 从日期字符串提取年份
    private func extractYear(from dateString: String) -> Int {
        // 尝试 ISO8601 格式（yyyy-MM-ddTHH:mm:ss）
        if let date = ISO8601DateFormatter().date(from: dateString) {
            return Calendar.current.component(.year, from: date)
        }

        // 尝试简单格式（yyyy-MM-dd）
        let components = dateString.split(separator: "-")
        if let firstComponent = components.first, let year = Int(firstComponent) {
            return year
        }

        // 默认当前年份
        return Calendar.current.component(.year, from: Date())
    }
}

// ========================================
// Native 版本的扩展功能
// ========================================
// TODO: 手动审查并整合以下功能

/*

/// Chronicle ViewModel - 管理事件编年数据
@MainActor
class ChronicleViewModel: ObservableObject {
    @Published var events: [TimelineEventResponse] = []
    @Published var stats: TimelineStatsResponse?
    @Published var isLoadingEvents = false
    @Published var isLoadingStats = false
    @Published var errorMessage: String?
    @Published var successMessage: String?

    // 筛选条件
    @Published var searchText: String = ""
    @Published var selectedCategory: String?
    @Published var startDate: String?
    @Published var endDate: String?

    private let timelineService = TimelineService.shared

    // MARK: - Data Loading

    /// 加载事件列表
    func loadEvents(projectId: Int, limit: Int = 200) async {
        isLoadingEvents = true
        errorMessage = nil

        do {
            let response = try await timelineService.getTimelineEvents(
                projectId: projectId,
                startDate: startDate,
                endDate: endDate,
                category: selectedCategory,
                limit: limit
            )
            events = response.events
            successMessage = nil
        } catch {
            errorMessage = "加载事件失败: \(error.localizedDescription)"
            print("❌ ChronicleViewModel.loadEvents error: \(error)")
        }

        isLoadingEvents = false
    }

    /// 加载统计信息
    func loadStats(projectId: Int) async {
        isLoadingStats = true

        do {
            stats = try await timelineService.getTimelineStats(projectId: projectId)
        } catch {
            print("⚠️ ChronicleViewModel.loadStats error: \(error)")
        }

        isLoadingStats = false
    }

    /// 加载所有数据（事件+统计）
    func loadAllData(projectId: Int) async {
        await loadEvents(projectId: projectId)
        await loadStats(projectId: projectId)
    }

    /// 应用筛选条件
    func applyFilters(projectId: Int, searchText: String?, startDate: String?, endDate: String?, category: String?) async {
        self.searchText = searchText ?? ""
        self.startDate = startDate
        self.endDate = endDate
        self.selectedCategory = category

        await loadEvents(projectId: projectId)
    }

    /// 清除筛选条件
    func clearFilters(projectId: Int) async {
        searchText = ""
        startDate = nil
        endDate = nil
        selectedCategory = nil

        await loadEvents(projectId: projectId)
    }

    // MARK: - Computed Properties

    /// 获取过滤后的事件（客户端搜索）
    func filteredEvents() -> [TimelineEventResponse] {
        guard !searchText.isEmpty else { return events }

        let lowercased = searchText.lowercased()
        return events.filter { event in
            event.title.lowercased().contains(lowercased) ||
            (event.description?.lowercased().contains(lowercased) ?? false)
        }
    }

    /// 按年份分组
    func eventsByYear() -> [Int: [TimelineEventResponse]] {
        let filtered = filteredEvents()
        var grouped: [Int: [TimelineEventResponse]] = [:]

        for event in filtered {
            let year = extractYear(from: event.date)
            grouped[year, default: []].append(event)
        }

        return grouped
    }

    /// 按类别分组
    func eventsByCategory() -> [String: [TimelineEventResponse]] {
        let filtered = filteredEvents()
        var grouped: [String: [TimelineEventResponse]] = [:]

        for event in filtered {
            let category = event.category ?? "未分类"
            grouped[category, default: []].append(event)
        }

        return grouped
    }

    /// 获取年份列表（降序）
    func getYears() -> [Int] {
        let grouped = eventsByYear()
        return grouped.keys.sorted(by: >)
    }

    /// 获取类别统计
    func categoryStats() -> [(category: String, count: Int)] {
        let grouped = eventsByCategory()
        return grouped.map { (category: $0.key, count: $0.value.count) }
            .sorted { $0.count > $1.count }
    }

    /// 获取日期范围描述
    func dateRangeDescription() -> String? {
        guard let start = startDate, let end = endDate else { return nil }
        return "\(start) 至 \(end)"
    }

    // MARK: - Helper Methods

    /// 从日期字符串提取年份
    private func extractYear(from dateString: String) -> Int {
        // 尝试 ISO8601 格式（yyyy-MM-ddTHH:mm:ss）
        if let date = ISO8601DateFormatter().date(from: dateString) {
            return Calendar.current.component(.year, from: date)
        }

        // 尝试简单格式（yyyy-MM-dd）
        let components = dateString.split(separator: "-")
        if let firstComponent = components.first, let year = Int(firstComponent) {
            return year
        }

        // 默认当前年份
        return Calendar.current.component(.year, from: Date())
    }
}
*/

