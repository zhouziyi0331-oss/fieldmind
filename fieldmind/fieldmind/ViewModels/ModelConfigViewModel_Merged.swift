//
//  ModelConfigViewModel_Merged.swift
//  FieldMind
//
//  深度整合 - 合并自主版本和 Native 版本
//  Generated: Sat Sep 19 11:21:01 CST 2026
//

import Foundation

// ========================================
// 主实现（来自主项目）
// ========================================


@MainActor
class ModelConfigViewModel: ObservableObject {
    @Published var models: [ModelConfigService.AIModel] = []
    @Published var configs: [ModelConfigService.ModelConfig] = []
    @Published var usageStats: [ModelConfigService.ModelUsage] = []
    @Published var totalCost: Double = 0.0
    @Published var totalCalls: Int = 0
    @Published var isLoadingModels = false
    @Published var isLoadingConfigs = false
    @Published var isLoadingUsage = false
    @Published var errorMessage: String?
    @Published var successMessage: String?

    func loadModels(provider: String? = nil, configuredOnly: Bool = false) async {
        isLoadingModels = true
        errorMessage = nil

        do {
            let response = try await ModelConfigService.shared.listModels(provider: provider, configuredOnly: configuredOnly)
            models = response.models
        } catch {
            errorMessage = "加载模型列表失败: \(error.localizedDescription)"
        }

        isLoadingModels = false
    }

    func loadConfigs(modelId: Int? = nil) async {
        isLoadingConfigs = true
        errorMessage = nil

        do {
            let response = try await ModelConfigService.shared.listConfigs(modelId: modelId)
            configs = response.configs
        } catch {
            errorMessage = "加载配置列表失败: \(error.localizedDescription)"
        }

        isLoadingConfigs = false
    }

    func loadUsageStats(startDate: String? = nil, endDate: String? = nil) async {
        isLoadingUsage = true
        errorMessage = nil

        do {
            let response = try await ModelConfigService.shared.getUsageStats(startDate: startDate, endDate: endDate)
            usageStats = response.usage
            totalCost = response.totalCost
            totalCalls = response.totalCalls
        } catch {
            errorMessage = "加载使用统计失败: \(error.localizedDescription)"
        }

        isLoadingUsage = false
    }

    func setActiveModel(modelId: Int) async {
        errorMessage = nil
        successMessage = nil

        do {
            let updatedModel = try await ModelConfigService.shared.setActiveModel(modelId: modelId)

            // Update local models list
            if let index = models.firstIndex(where: { $0.id == modelId }) {
                // Deactivate all other models
                models = models.map { model in
                    let updated = model
                    return updated
                }
                models[index] = updatedModel
            }

            successMessage = "模型已激活"
        } catch {
            errorMessage = "激活模型失败: \(error.localizedDescription)"
        }
    }

    func filterModels(searchText: String, provider: String) -> [ModelConfigService.AIModel] {
        var filtered = models

        if !searchText.isEmpty {
            filtered = filtered.filter { model in
                model.name.localizedCaseInsensitiveContains(searchText) ||
                model.description.localizedCaseInsensitiveContains(searchText) ||
                model.provider.localizedCaseInsensitiveContains(searchText)
            }
        }

        if provider != "全部" {
            filtered = filtered.filter { $0.provider == provider }
        }

        return filtered
    }

    var activeModel: ModelConfigService.AIModel? {
        models.first { $0.isActive }
    }

    var hasModels: Bool {
        !models.isEmpty
    }

    var hasConfigs: Bool {
        !configs.isEmpty
    }

    var hasUsageStats: Bool {
        !usageStats.isEmpty
    }
}

// ========================================
// Native 版本的扩展功能
// ========================================
// TODO: 手动审查并整合以下功能

/*

@MainActor
class ModelConfigViewModel: ObservableObject {
    @Published var models: [ModelConfigService.AIModel] = []
    @Published var configs: [ModelConfigService.ModelConfig] = []
    @Published var usageStats: [ModelConfigService.ModelUsage] = []
    @Published var totalCost: Double = 0.0
    @Published var totalCalls: Int = 0
    @Published var isLoadingModels = false
    @Published var isLoadingConfigs = false
    @Published var isLoadingUsage = false
    @Published var errorMessage: String?
    @Published var successMessage: String?

    func loadModels(provider: String? = nil, configuredOnly: Bool = false) async {
        isLoadingModels = true
        errorMessage = nil

        do {
            let response = try await ModelConfigService.shared.listModels(provider: provider, configuredOnly: configuredOnly)
            models = response.models
        } catch {
            errorMessage = "加载模型列表失败: \(error.localizedDescription)"
        }

        isLoadingModels = false
    }

    func loadConfigs(modelId: Int? = nil) async {
        isLoadingConfigs = true
        errorMessage = nil

        do {
            let response = try await ModelConfigService.shared.listConfigs(modelId: modelId)
            configs = response.configs
        } catch {
            errorMessage = "加载配置列表失败: \(error.localizedDescription)"
        }

        isLoadingConfigs = false
    }

    func loadUsageStats(startDate: String? = nil, endDate: String? = nil) async {
        isLoadingUsage = true
        errorMessage = nil

        do {
            let response = try await ModelConfigService.shared.getUsageStats(startDate: startDate, endDate: endDate)
            usageStats = response.usage
            totalCost = response.totalCost
            totalCalls = response.totalCalls
        } catch {
            errorMessage = "加载使用统计失败: \(error.localizedDescription)"
        }

        isLoadingUsage = false
    }

    func setActiveModel(modelId: Int) async {
        errorMessage = nil
        successMessage = nil

        do {
            let updatedModel = try await ModelConfigService.shared.setActiveModel(modelId: modelId)

            // Update local models list
            if let index = models.firstIndex(where: { $0.id == modelId }) {
                // Deactivate all other models
                models = models.map { model in
                    let updated = model
                    return updated
                }
                models[index] = updatedModel
            }

            successMessage = "模型已激活"
        } catch {
            errorMessage = "激活模型失败: \(error.localizedDescription)"
        }
    }

    func filterModels(searchText: String, provider: String) -> [ModelConfigService.AIModel] {
        var filtered = models

        if !searchText.isEmpty {
            filtered = filtered.filter { model in
                model.name.localizedCaseInsensitiveContains(searchText) ||
                model.description.localizedCaseInsensitiveContains(searchText) ||
                model.provider.localizedCaseInsensitiveContains(searchText)
            }
        }

        if provider != "全部" {
            filtered = filtered.filter { $0.provider == provider }
        }

        return filtered
    }

    var activeModel: ModelConfigService.AIModel? {
        models.first { $0.isActive }
    }

    var hasModels: Bool {
        !models.isEmpty
    }

    var hasConfigs: Bool {
        !configs.isEmpty
    }

    var hasUsageStats: Bool {
        !usageStats.isEmpty
    }
}
*/

