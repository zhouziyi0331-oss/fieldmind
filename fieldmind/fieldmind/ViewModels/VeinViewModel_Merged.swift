//
//  VeinViewModel_Merged.swift
//  FieldMind
//
//  深度整合 - 合并自主版本和 Native 版本
//  Generated: Sat Sep 19 11:21:01 CST 2026
//

import Foundation
import SwiftUI

// ========================================
// 主实现（来自主项目）
// ========================================


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

// ========================================
// Native 版本的扩展功能
// ========================================
// TODO: 手动审查并整合以下功能

/*

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
*/

