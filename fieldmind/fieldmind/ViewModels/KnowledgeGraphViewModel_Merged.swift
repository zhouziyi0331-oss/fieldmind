//
//  KnowledgeGraphViewModel_Merged.swift
//  FieldMind
//
//  深度整合 - 合并自主版本和 Native 版本
//  Generated: Sat Sep 19 11:21:01 CST 2026
//

import Foundation

// ========================================
// 主实现（来自主项目）
// ========================================


/// Knowledge Graph ViewModel - 管理知识图谱数据
@MainActor
class KnowledgeGraphViewModel: ObservableObject {
    @Published var entities: [KnowledgeGraphService.EntityResponse] = []
    @Published var graphData: KnowledgeGraphService.GraphVisualizationResponse?
    @Published var selectedEntity: KnowledgeGraphService.EntityResponse?

    @Published var isLoadingEntities = false
    @Published var isLoadingGraph = false
    @Published var isBuilding = false
    @Published var errorMessage: String?
    @Published var successMessage: String?

    // 筛选条件
    @Published var searchText: String = ""
    @Published var selectedEntityType: String?

    private let service = KnowledgeGraphService.shared

    // MARK: - Data Loading

    /// 加载实体列表
    func loadEntities(projectId: Int, limit: Int = 100) async {
        isLoadingEntities = true
        errorMessage = nil

        do {
            entities = try await service.getEntities(
                projectId: projectId,
                entityType: selectedEntityType,
                search: searchText.isEmpty ? nil : searchText,
                limit: limit
            )
            successMessage = nil
        } catch {
            errorMessage = "加载实体失败: \(error.localizedDescription)"
            print("❌ KnowledgeGraphViewModel.loadEntities error: \(error)")
        }

        isLoadingEntities = false
    }

    /// 加载图谱可视化数据
    func loadGraphVisualization(projectId: Int, limit: Int = 100) async {
        isLoadingGraph = true
        errorMessage = nil

        do {
            graphData = try await service.getGraphVisualization(
                projectId: projectId,
                limit: limit
            )
            successMessage = nil
        } catch {
            errorMessage = "加载图谱失败: \(error.localizedDescription)"
            print("❌ KnowledgeGraphViewModel.loadGraphVisualization error: \(error)")
        }

        isLoadingGraph = false
    }

    /// 构建知识图谱
    func buildKnowledgeGraph(projectId: Int, documentIds: [Int]? = nil, forceRebuild: Bool = false) async {
        isBuilding = true
        errorMessage = nil

        do {
            let response = try await service.buildKnowledgeGraph(
                projectId: projectId,
                documentIds: documentIds,
                forceRebuild: forceRebuild
            )
            successMessage = response.message

            // 构建完成后重新加载数据
            await loadAllData(projectId: projectId)
        } catch {
            errorMessage = "构建图谱失败: \(error.localizedDescription)"
            print("❌ KnowledgeGraphViewModel.buildKnowledgeGraph error: \(error)")
        }

        isBuilding = false
    }

    /// 加载实体详情
    func loadEntityDetail(entityId: String) async {
        do {
            selectedEntity = try await service.getEntityDetail(entityId: entityId)
        } catch {
            errorMessage = "加载实体详情失败: \(error.localizedDescription)"
            print("❌ KnowledgeGraphViewModel.loadEntityDetail error: \(error)")
        }
    }

    /// 加载所有数据
    func loadAllData(projectId: Int) async {
        await loadEntities(projectId: projectId)
        await loadGraphVisualization(projectId: projectId)
    }

    /// 应用筛选
    func applyFilters(projectId: Int, searchText: String?, entityType: String?) async {
        self.searchText = searchText ?? ""
        self.selectedEntityType = entityType

        await loadEntities(projectId: projectId)
    }

    /// 清除筛选
    func clearFilters(projectId: Int) async {
        searchText = ""
        selectedEntityType = nil

        await loadEntities(projectId: projectId)
    }

    // MARK: - Computed Properties

    /// 获取过滤后的实体（客户端搜索）
    func filteredEntities() -> [KnowledgeGraphService.EntityResponse] {
        guard !searchText.isEmpty else { return entities }

        let lowercased = searchText.lowercased()
        return entities.filter { entity in
            entity.name.lowercased().contains(lowercased) ||
            (entity.aliases?.joined(separator: " ").lowercased().contains(lowercased) ?? false) ||
            (entity.description?.lowercased().contains(lowercased) ?? false)
        }
    }

    /// 按类型分组
    func entitiesByType() -> [String: [KnowledgeGraphService.EntityResponse]] {
        let filtered = filteredEntities()
        return Dictionary(grouping: filtered) { $0.entityType }
    }

    /// 获取实体类型统计
    func entityTypeStats() -> [(type: String, count: Int)] {
        let grouped = entitiesByType()
        return grouped.map { (type: $0.key, count: $0.value.count) }
            .sorted { $0.count > $1.count }
    }

    /// 获取所有实体类型
    func getAllEntityTypes() -> [String] {
        let types = Set(entities.map { $0.entityType })
        return Array(types).sorted()
    }

    /// 格式化实体类型显示名称
    func formatEntityType(_ type: String) -> String {
        switch type {
        case "person": return "人物"
        case "location": return "地点"
        case "organization": return "组织"
        case "event": return "事件"
        case "concept": return "概念"
        case "artifact": return "物品"
        case "custom": return "自定义"
        default: return type
        }
    }

    /// 获取实体类型图标
    func entityTypeIcon(_ type: String) -> String {
        switch type {
        case "person": return "person.fill"
        case "location": return "mappin.circle.fill"
        case "organization": return "building.2.fill"
        case "event": return "calendar"
        case "concept": return "lightbulb.fill"
        case "artifact": return "cube.fill"
        default: return "circle.fill"
        }
    }

    /// 获取实体类型颜色
    func entityTypeColor(_ type: String) -> String {
        switch type {
        case "person": return "3B82F6"  // blue
        case "location": return "10B981"  // green
        case "organization": return "8B5CF6"  // purple
        case "event": return "F59E0B"  // amber
        case "concept": return "EC4899"  // pink
        case "artifact": return "14B8A6"  // teal
        default: return "64748B"  // gray
        }
    }
}

// ========================================
// Native 版本的扩展功能
// ========================================
// TODO: 手动审查并整合以下功能

/*

/// Knowledge Graph ViewModel - 管理知识图谱数据
@MainActor
class KnowledgeGraphViewModel: ObservableObject {
    @Published var entities: [KnowledgeGraphService.EntityResponse] = []
    @Published var graphData: KnowledgeGraphService.GraphVisualizationResponse?
    @Published var selectedEntity: KnowledgeGraphService.EntityResponse?

    @Published var isLoadingEntities = false
    @Published var isLoadingGraph = false
    @Published var isBuilding = false
    @Published var errorMessage: String?
    @Published var successMessage: String?

    // 筛选条件
    @Published var searchText: String = ""
    @Published var selectedEntityType: String?

    private let service = KnowledgeGraphService.shared

    // MARK: - Data Loading

    /// 加载实体列表
    func loadEntities(projectId: Int, limit: Int = 100) async {
        isLoadingEntities = true
        errorMessage = nil

        do {
            entities = try await service.getEntities(
                projectId: projectId,
                entityType: selectedEntityType,
                search: searchText.isEmpty ? nil : searchText,
                limit: limit
            )
            successMessage = nil
        } catch {
            errorMessage = "加载实体失败: \(error.localizedDescription)"
            print("❌ KnowledgeGraphViewModel.loadEntities error: \(error)")
        }

        isLoadingEntities = false
    }

    /// 加载图谱可视化数据
    func loadGraphVisualization(projectId: Int, limit: Int = 100) async {
        isLoadingGraph = true
        errorMessage = nil

        do {
            graphData = try await service.getGraphVisualization(
                projectId: projectId,
                limit: limit
            )
            successMessage = nil
        } catch {
            errorMessage = "加载图谱失败: \(error.localizedDescription)"
            print("❌ KnowledgeGraphViewModel.loadGraphVisualization error: \(error)")
        }

        isLoadingGraph = false
    }

    /// 构建知识图谱
    func buildKnowledgeGraph(projectId: Int, documentIds: [Int]? = nil, forceRebuild: Bool = false) async {
        isBuilding = true
        errorMessage = nil

        do {
            let response = try await service.buildKnowledgeGraph(
                projectId: projectId,
                documentIds: documentIds,
                forceRebuild: forceRebuild
            )
            successMessage = response.message

            // 构建完成后重新加载数据
            await loadAllData(projectId: projectId)
        } catch {
            errorMessage = "构建图谱失败: \(error.localizedDescription)"
            print("❌ KnowledgeGraphViewModel.buildKnowledgeGraph error: \(error)")
        }

        isBuilding = false
    }

    /// 加载实体详情
    func loadEntityDetail(entityId: String) async {
        do {
            selectedEntity = try await service.getEntityDetail(entityId: entityId)
        } catch {
            errorMessage = "加载实体详情失败: \(error.localizedDescription)"
            print("❌ KnowledgeGraphViewModel.loadEntityDetail error: \(error)")
        }
    }

    /// 加载所有数据
    func loadAllData(projectId: Int) async {
        await loadEntities(projectId: projectId)
        await loadGraphVisualization(projectId: projectId)
    }

    /// 应用筛选
    func applyFilters(projectId: Int, searchText: String?, entityType: String?) async {
        self.searchText = searchText ?? ""
        self.selectedEntityType = entityType

        await loadEntities(projectId: projectId)
    }

    /// 清除筛选
    func clearFilters(projectId: Int) async {
        searchText = ""
        selectedEntityType = nil

        await loadEntities(projectId: projectId)
    }

    // MARK: - Computed Properties

    /// 获取过滤后的实体（客户端搜索）
    func filteredEntities() -> [KnowledgeGraphService.EntityResponse] {
        guard !searchText.isEmpty else { return entities }

        let lowercased = searchText.lowercased()
        return entities.filter { entity in
            entity.name.lowercased().contains(lowercased) ||
            (entity.aliases?.joined(separator: " ").lowercased().contains(lowercased) ?? false) ||
            (entity.description?.lowercased().contains(lowercased) ?? false)
        }
    }

    /// 按类型分组
    func entitiesByType() -> [String: [KnowledgeGraphService.EntityResponse]] {
        let filtered = filteredEntities()
        return Dictionary(grouping: filtered) { $0.entityType }
    }

    /// 获取实体类型统计
    func entityTypeStats() -> [(type: String, count: Int)] {
        let grouped = entitiesByType()
        return grouped.map { (type: $0.key, count: $0.value.count) }
            .sorted { $0.count > $1.count }
    }

    /// 获取所有实体类型
    func getAllEntityTypes() -> [String] {
        let types = Set(entities.map { $0.entityType })
        return Array(types).sorted()
    }

    /// 格式化实体类型显示名称
    func formatEntityType(_ type: String) -> String {
        switch type {
        case "person": return "人物"
        case "location": return "地点"
        case "organization": return "组织"
        case "event": return "事件"
        case "concept": return "概念"
        case "artifact": return "物品"
        case "custom": return "自定义"
        default: return type
        }
    }

    /// 获取实体类型图标
    func entityTypeIcon(_ type: String) -> String {
        switch type {
        case "person": return "person.fill"
        case "location": return "mappin.circle.fill"
        case "organization": return "building.2.fill"
        case "event": return "calendar"
        case "concept": return "lightbulb.fill"
        case "artifact": return "cube.fill"
        default: return "circle.fill"
        }
    }

    /// 获取实体类型颜色
    func entityTypeColor(_ type: String) -> String {
        switch type {
        case "person": return "3B82F6"  // blue
        case "location": return "10B981"  // green
        case "organization": return "8B5CF6"  // purple
        case "event": return "F59E0B"  // amber
        case "concept": return "EC4899"  // pink
        case "artifact": return "14B8A6"  // teal
        default: return "64748B"  // gray
        }
    }
}
*/

