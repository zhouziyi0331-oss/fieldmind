//
//  SOPAnalysisViewModel_Merged.swift
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
class SOPAnalysisViewModel: ObservableObject {
    @Published var analyses: [SOPAnalysisService.SOPAnalysis] = []
    @Published var summary: SOPAnalysisService.SOPSummary?
    @Published var selectedAnalysis: SOPAnalysisService.SOPAnalysis?
    @Published var isLoading = false
    @Published var isLoadingSummary = false
    @Published var isGenerating = false
    @Published var errorMessage: String?
    @Published var successMessage: String?

    func loadAnalyses(projectId: Int, category: String? = nil, timeRange: String? = nil) async {
        isLoading = true
        errorMessage = nil

        do {
            let response = try await SOPAnalysisService.shared.listAnalyses(
                projectId: projectId,
                category: category,
                timeRange: timeRange
            )
            analyses = response.analyses
        } catch {
            errorMessage = "加载分析列表失败: \(error.localizedDescription)"
        }

        isLoading = false
    }

    func loadAnalysisDetail(projectId: Int, analysisId: Int) async {
        errorMessage = nil

        do {
            selectedAnalysis = try await SOPAnalysisService.shared.getAnalysis(projectId: projectId, analysisId: analysisId)
        } catch {
            errorMessage = "加载分析详情失败: \(error.localizedDescription)"
        }
    }

    func loadSummary(projectId: Int) async {
        isLoadingSummary = true
        errorMessage = nil

        do {
            summary = try await SOPAnalysisService.shared.getSummary(projectId: projectId)
        } catch {
            errorMessage = "加载统计概览失败: \(error.localizedDescription)"
        }

        isLoadingSummary = false
    }

    func generateAnalysis(projectId: Int, sopId: Int, timeRange: String) async {
        isGenerating = true
        errorMessage = nil
        successMessage = nil

        do {
            let newAnalysis = try await SOPAnalysisService.shared.generateAnalysis(
                projectId: projectId,
                sopId: sopId,
                timeRange: timeRange
            )
            analyses.insert(newAnalysis, at: 0)
            successMessage = "分析生成成功"
        } catch {
            errorMessage = "生成分析失败: \(error.localizedDescription)"
        }

        isGenerating = false
    }

    func filterAnalyses(searchText: String, category: String, sortBy: String) -> [SOPAnalysisService.SOPAnalysis] {
        var filtered = analyses

        // Filter by search text
        if !searchText.isEmpty {
            filtered = filtered.filter { analysis in
                analysis.sopTitle.localizedCaseInsensitiveContains(searchText) ||
                analysis.category.localizedCaseInsensitiveContains(searchText)
            }
        }

        // Filter by category
        if category != "全部分类" {
            filtered = filtered.filter { $0.category == category }
        }

        // Sort
        filtered.sort { first, second in
            switch sortBy {
            case "totalUsage":
                return first.metrics.totalUsage > second.metrics.totalUsage
            case "successRate":
                return first.metrics.successRate > second.metrics.successRate
            default:
                return first.overallScore > second.overallScore
            }
        }

        return filtered
    }

    func getCategoryStats() -> [String: Int] {
        Dictionary(grouping: analyses, by: { $0.category })
            .mapValues { $0.count }
    }

    var hasAnalyses: Bool {
        !analyses.isEmpty
    }

    var hasSummary: Bool {
        summary != nil
    }
}

// ========================================
// Native 版本的扩展功能
// ========================================
// TODO: 手动审查并整合以下功能

/*

@MainActor
class SOPAnalysisViewModel: ObservableObject {
    @Published var analyses: [SOPAnalysisService.SOPAnalysis] = []
    @Published var summary: SOPAnalysisService.SOPSummary?
    @Published var selectedAnalysis: SOPAnalysisService.SOPAnalysis?
    @Published var isLoading = false
    @Published var isLoadingSummary = false
    @Published var isGenerating = false
    @Published var errorMessage: String?
    @Published var successMessage: String?

    func loadAnalyses(projectId: Int, category: String? = nil, timeRange: String? = nil) async {
        isLoading = true
        errorMessage = nil

        do {
            let response = try await SOPAnalysisService.shared.listAnalyses(
                projectId: projectId,
                category: category,
                timeRange: timeRange
            )
            analyses = response.analyses
        } catch {
            errorMessage = "加载分析列表失败: \(error.localizedDescription)"
        }

        isLoading = false
    }

    func loadAnalysisDetail(projectId: Int, analysisId: Int) async {
        errorMessage = nil

        do {
            selectedAnalysis = try await SOPAnalysisService.shared.getAnalysis(projectId: projectId, analysisId: analysisId)
        } catch {
            errorMessage = "加载分析详情失败: \(error.localizedDescription)"
        }
    }

    func loadSummary(projectId: Int) async {
        isLoadingSummary = true
        errorMessage = nil

        do {
            summary = try await SOPAnalysisService.shared.getSummary(projectId: projectId)
        } catch {
            errorMessage = "加载统计概览失败: \(error.localizedDescription)"
        }

        isLoadingSummary = false
    }

    func generateAnalysis(projectId: Int, sopId: Int, timeRange: String) async {
        isGenerating = true
        errorMessage = nil
        successMessage = nil

        do {
            let newAnalysis = try await SOPAnalysisService.shared.generateAnalysis(
                projectId: projectId,
                sopId: sopId,
                timeRange: timeRange
            )
            analyses.insert(newAnalysis, at: 0)
            successMessage = "分析生成成功"
        } catch {
            errorMessage = "生成分析失败: \(error.localizedDescription)"
        }

        isGenerating = false
    }

    func filterAnalyses(searchText: String, category: String, sortBy: String) -> [SOPAnalysisService.SOPAnalysis] {
        var filtered = analyses

        // Filter by search text
        if !searchText.isEmpty {
            filtered = filtered.filter { analysis in
                analysis.sopTitle.localizedCaseInsensitiveContains(searchText) ||
                analysis.category.localizedCaseInsensitiveContains(searchText)
            }
        }

        // Filter by category
        if category != "全部分类" {
            filtered = filtered.filter { $0.category == category }
        }

        // Sort
        filtered.sort { first, second in
            switch sortBy {
            case "totalUsage":
                return first.metrics.totalUsage > second.metrics.totalUsage
            case "successRate":
                return first.metrics.successRate > second.metrics.successRate
            default:
                return first.overallScore > second.overallScore
            }
        }

        return filtered
    }

    func getCategoryStats() -> [String: Int] {
        Dictionary(grouping: analyses, by: { $0.category })
            .mapValues { $0.count }
    }

    var hasAnalyses: Bool {
        !analyses.isEmpty
    }

    var hasSummary: Bool {
        summary != nil
    }
}
*/

