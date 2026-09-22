//
//  ProjectViewModel_Merged.swift
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

// ========================================
// Native 版本的扩展功能
// ========================================
// TODO: 手动审查并整合以下功能

/*

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
*/

