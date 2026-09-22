import Foundation
import SwiftUI

/// CitationViewModel - 文献引用管理状态管理
@MainActor
class CitationViewModel: ObservableObject {
    @Published var citations: [CitationService.CitationResponse] = []
    @Published var stats: CitationService.CitationStatsResponse?
    @Published var selectedCitation: CitationService.CitationResponse?

    @Published var isLoadingCitations = false
    @Published var isLoadingStats = false
    @Published var errorMessage: String?
    @Published var successMessage: String?

    // Filters
    @Published var searchText: String = ""
    @Published var selectedProject: String = "全部项目"
    @Published var selectedType: String = "全部类型"
    @Published var selectedSort: String = "最新添加"

    private let service = CitationService.shared

    // MARK: - API Methods

    /// 加载引用列表
    func loadCitations(projectId: Int, page: Int = 1, pageSize: Int = 100) async {
        isLoadingCitations = true
        errorMessage = nil

        do {
            let sortBy: String
            let sortOrder: String

            switch selectedSort {
            case "最新添加":
                sortBy = "added_at"
                sortOrder = "desc"
            case "最早添加":
                sortBy = "added_at"
                sortOrder = "asc"
            case "标题A-Z":
                sortBy = "title"
                sortOrder = "asc"
            case "标题Z-A":
                sortBy = "title"
                sortOrder = "desc"
            case "引用次数":
                sortBy = "cited_count"
                sortOrder = "desc"
            default:
                sortBy = "added_at"
                sortOrder = "desc"
            }

            let response = try await service.getCitations(
                projectId: projectId,
                search: searchText.isEmpty ? nil : searchText,
                citationType: selectedType == "全部类型" ? nil : selectedType,
                tags: nil,
                sortBy: sortBy,
                sortOrder: sortOrder,
                page: page,
                pageSize: pageSize
            )

            citations = response.citations
            isLoadingCitations = false
        } catch {
            errorMessage = "加载引用失败: \(error.localizedDescription)"
            isLoadingCitations = false
        }
    }

    /// 加载统计数据
    func loadStats(projectId: Int) async {
        isLoadingStats = true

        do {
            stats = try await service.getStats(projectId: projectId)
            isLoadingStats = false
        } catch {
            print("⚠️ 加载统计失败: \(error)")
            isLoadingStats = false
        }
    }

    /// 加载所有数据
    func loadAllData(projectId: Int) async {
        await loadCitations(projectId: projectId)
        await loadStats(projectId: projectId)
    }

    /// 创建引用
    func createCitation(
        title: String,
        authors: [String],
        year: String?,
        publication: String?,
        publisher: String?,
        doi: String?,
        url: String?,
        abstract: String?,
        notes: String?,
        citationType: String,
        tags: [String],
        projectId: Int
    ) async -> Bool {
        do {
            let request = CitationService.CitationCreateRequest(
                title: title,
                authors: authors,
                year: year,
                publication: publication,
                publisher: publisher,
                doi: doi,
                isbn: nil,
                url: url,
                abstract: abstract,
                notes: notes,
                citationType: citationType,
                tags: tags,
                projectId: projectId,
                bibtex: nil,
                extraMetadata: [:]
            )

            let newCitation = try await service.createCitation(request: request)
            citations.insert(newCitation, at: 0)
            successMessage = "引用已添加"
            return true
        } catch {
            errorMessage = "创建引用失败: \(error.localizedDescription)"
            return false
        }
    }

    /// 更新引用
    func updateCitation(
        citationId: Int,
        title: String,
        authors: [String],
        year: String?,
        publication: String?,
        publisher: String?,
        doi: String?,
        url: String?,
        abstract: String?,
        notes: String?,
        citationType: String,
        tags: [String],
        projectId: Int
    ) async -> Bool {
        do {
            let request = CitationService.CitationCreateRequest(
                title: title,
                authors: authors,
                year: year,
                publication: publication,
                publisher: publisher,
                doi: doi,
                isbn: nil,
                url: url,
                abstract: abstract,
                notes: notes,
                citationType: citationType,
                tags: tags,
                projectId: projectId,
                bibtex: nil,
                extraMetadata: [:]
            )

            let updated = try await service.updateCitation(citationId: citationId, request: request)
            if let index = citations.firstIndex(where: { $0.id == citationId }) {
                citations[index] = updated
            }
            successMessage = "引用已更新"
            return true
        } catch {
            errorMessage = "更新引用失败: \(error.localizedDescription)"
            return false
        }
    }

    /// 删除引用
    func deleteCitation(citationId: Int) async -> Bool {
        do {
            try await service.deleteCitation(citationId: citationId)
            citations.removeAll { $0.id == citationId }
            successMessage = "引用已删除"
            return true
        } catch {
            errorMessage = "删除引用失败: \(error.localizedDescription)"
            return false
        }
    }

    /// 批量删除引用
    func batchDeleteCitations(citationIds: [Int]) async -> Bool {
        var allSuccess = true
        for id in citationIds {
            let success = await deleteCitation(citationId: id)
            if !success {
                allSuccess = false
            }
        }
        if allSuccess {
            successMessage = "已删除 \(citationIds.count) 条引用"
        }
        return allSuccess
    }

    // MARK: - Helper Methods

    /// 过滤引用（客户端额外过滤）
    func filteredCitations() -> [CitationService.CitationResponse] {
        var result = citations

        // 项目筛选（如果有多项目支持）
        if selectedProject != "全部项目" {
            // 暂时不实现，因为后端已经按project_id筛选
        }

        return result
    }

    /// 按类型分组
    func citationsByType() -> [String: [CitationService.CitationResponse]] {
        Dictionary(grouping: citations, by: { $0.citationType })
    }

    /// 按年份分组
    func citationsByYear() -> [String: [CitationService.CitationResponse]] {
        Dictionary(grouping: citations.filter { $0.year != nil }, by: { $0.year! })
    }

    /// 类型统计
    func typeStats() -> [(type: String, count: Int)] {
        let grouped = citationsByType()
        return grouped.map { (type: $0.key, count: $0.value.count) }
            .sorted { $0.count > $1.count }
    }

    /// 格式化文献类型
    func formatCitationType(_ type: String) -> String {
        type  // 已经是中文
    }

    /// 文献类型图标
    func citationTypeIcon(_ type: String) -> String {
        switch type {
        case "学术论文": return "doc.text"
        case "书籍": return "book.closed"
        case "报告": return "doc.richtext"
        case "网页": return "globe"
        case "其他": return "doc"
        default: return "doc"
        }
    }

    /// 文献类型颜色
    func citationTypeColor(_ type: String) -> String {
        switch type {
        case "学术论文": return "3B82F6"  // Blue
        case "书籍": return "10B981"      // Green
        case "报告": return "F59E0B"      // Amber
        case "网页": return "8B5CF6"      // Purple
        case "其他": return "6B7280"      // Gray
        default: return "6B7280"
        }
    }

    /// 清除消息
    func clearMessages() {
        errorMessage = nil
        successMessage = nil
    }
}
