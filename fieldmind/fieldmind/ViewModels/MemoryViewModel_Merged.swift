//
//  MemoryViewModel_Merged.swift
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
class MemoryViewModel: ObservableObject {
    @Published var memories: [MemoryService.MemoryResponse] = []
    @Published var stats: MemoryService.MemoryStatsResponse?
    @Published var isLoading = false
    @Published var isCreating = false
    @Published var isProcessing = false
    @Published var errorMessage: String?
    @Published var successMessage: String?
    @Published var filterType: String? = nil

    func loadMemories(projectId: Int) async {
        isLoading = true
        errorMessage = nil

        do {
            memories = try await MemoryService.shared.getProjectMemories(projectId: projectId)
            isLoading = false
        } catch {
            errorMessage = "加载记忆失败: \(error.localizedDescription)"
            isLoading = false
        }
    }

    func loadStats(projectId: Int) async {
        do {
            stats = try await MemoryService.shared.getMemoryStats(projectId: projectId)
        } catch {
            print("加载统计数据失败: \(error.localizedDescription)")
        }
    }

    func createMemory(
        projectId: Int,
        memoryType: String,
        content: String,
        summary: String?,
        sourceType: String?,
        keywords: [String]?,
        importanceScore: Double?
    ) async {
        isCreating = true
        errorMessage = nil
        successMessage = nil

        do {
            let newMemory = try await MemoryService.shared.createMemory(
                projectId: projectId,
                memoryType: memoryType,
                content: content,
                summary: summary,
                sourceType: sourceType,
                keywords: keywords,
                importanceScore: importanceScore
            )

            memories.insert(newMemory, at: 0)
            successMessage = "记忆创建成功"
            isCreating = false

            // 重新加载统计数据
            await loadStats(projectId: projectId)
        } catch {
            errorMessage = "创建记忆失败: \(error.localizedDescription)"
            isCreating = false
        }
    }

    func autoPromoteMemories(projectId: Int) async {
        isProcessing = true
        errorMessage = nil
        successMessage = nil

        do {
            try await MemoryService.shared.autoPromoteMemories(projectId: projectId)
            successMessage = "记忆自动提升完成"
            isProcessing = false

            // 重新加载数据
            await loadMemories(projectId: projectId)
            await loadStats(projectId: projectId)
        } catch {
            errorMessage = "自动提升失败: \(error.localizedDescription)"
            isProcessing = false
        }
    }

    func cleanupMemories(projectId: Int) async {
        isProcessing = true
        errorMessage = nil
        successMessage = nil

        do {
            try await MemoryService.shared.cleanupMemories(projectId: projectId)
            successMessage = "记忆清理完成"
            isProcessing = false

            // 重新加载数据
            await loadMemories(projectId: projectId)
            await loadStats(projectId: projectId)
        } catch {
            errorMessage = "清理失败: \(error.localizedDescription)"
            isProcessing = false
        }
    }

    var filteredMemories: [MemoryService.MemoryResponse] {
        if let filterType = filterType {
            return memories.filter { $0.memoryType == filterType }
        }
        return memories
    }

    func memoryTypeLabel(_ type: String) -> String {
        switch type {
        case "short_term": return "短期记忆"
        case "mid_term": return "中期记忆"
        case "long_term": return "长期记忆"
        default: return type
        }
    }

    func memoryTypeColor(_ type: String) -> Color {
        switch type {
        case "short_term": return .blue
        case "mid_term": return .orange
        case "long_term": return .purple
        default: return .gray
        }
    }

    func clearMessages() {
        errorMessage = nil
        successMessage = nil
    }
}

// ========================================
// Native 版本的扩展功能
// ========================================
// TODO: 手动审查并整合以下功能

/*

@MainActor
class MemoryViewModel: ObservableObject {
    @Published var memories: [MemoryService.MemoryResponse] = []
    @Published var stats: MemoryService.MemoryStatsResponse?
    @Published var isLoading = false
    @Published var isCreating = false
    @Published var isProcessing = false
    @Published var errorMessage: String?
    @Published var successMessage: String?
    @Published var filterType: String? = nil

    func loadMemories(projectId: Int) async {
        isLoading = true
        errorMessage = nil

        do {
            memories = try await MemoryService.shared.getProjectMemories(projectId: projectId)
            isLoading = false
        } catch {
            errorMessage = "加载记忆失败: \(error.localizedDescription)"
            isLoading = false
        }
    }

    func loadStats(projectId: Int) async {
        do {
            stats = try await MemoryService.shared.getMemoryStats(projectId: projectId)
        } catch {
            print("加载统计数据失败: \(error.localizedDescription)")
        }
    }

    func createMemory(
        projectId: Int,
        memoryType: String,
        content: String,
        summary: String?,
        sourceType: String?,
        keywords: [String]?,
        importanceScore: Double?
    ) async {
        isCreating = true
        errorMessage = nil
        successMessage = nil

        do {
            let newMemory = try await MemoryService.shared.createMemory(
                projectId: projectId,
                memoryType: memoryType,
                content: content,
                summary: summary,
                sourceType: sourceType,
                keywords: keywords,
                importanceScore: importanceScore
            )

            memories.insert(newMemory, at: 0)
            successMessage = "记忆创建成功"
            isCreating = false

            // 重新加载统计数据
            await loadStats(projectId: projectId)
        } catch {
            errorMessage = "创建记忆失败: \(error.localizedDescription)"
            isCreating = false
        }
    }

    func autoPromoteMemories(projectId: Int) async {
        isProcessing = true
        errorMessage = nil
        successMessage = nil

        do {
            try await MemoryService.shared.autoPromoteMemories(projectId: projectId)
            successMessage = "记忆自动提升完成"
            isProcessing = false

            // 重新加载数据
            await loadMemories(projectId: projectId)
            await loadStats(projectId: projectId)
        } catch {
            errorMessage = "自动提升失败: \(error.localizedDescription)"
            isProcessing = false
        }
    }

    func cleanupMemories(projectId: Int) async {
        isProcessing = true
        errorMessage = nil
        successMessage = nil

        do {
            try await MemoryService.shared.cleanupMemories(projectId: projectId)
            successMessage = "记忆清理完成"
            isProcessing = false

            // 重新加载数据
            await loadMemories(projectId: projectId)
            await loadStats(projectId: projectId)
        } catch {
            errorMessage = "清理失败: \(error.localizedDescription)"
            isProcessing = false
        }
    }

    var filteredMemories: [MemoryService.MemoryResponse] {
        if let filterType = filterType {
            return memories.filter { $0.memoryType == filterType }
        }
        return memories
    }

    func memoryTypeLabel(_ type: String) -> String {
        switch type {
        case "short_term": return "短期记忆"
        case "mid_term": return "中期记忆"
        case "long_term": return "长期记忆"
        default: return type
        }
    }

    func memoryTypeColor(_ type: String) -> Color {
        switch type {
        case "short_term": return .blue
        case "mid_term": return .orange
        case "long_term": return .purple
        default: return .gray
        }
    }

    func clearMessages() {
        errorMessage = nil
        successMessage = nil
    }
}
*/

