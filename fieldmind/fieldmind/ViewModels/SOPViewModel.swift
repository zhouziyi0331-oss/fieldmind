import Foundation

@MainActor
class SOPViewModel: ObservableObject {
    @Published var sops: [SOPService.SOP] = []
    @Published var statistics: SOPService.SOPStatistics?
    @Published var selectedSOP: SOPService.SOP?
    @Published var isLoading = false
    @Published var isCreating = false
    @Published var errorMessage: String?
    @Published var successMessage: String?

    private let service = SOPService.shared

    var hasSOPs: Bool {
        !sops.isEmpty
    }

    func loadSOPs(projectId: Int, category: String?, status: String?, search: String?) async {
        isLoading = true
        errorMessage = nil

        do {
            let response = try await service.listSOPs(
                projectId: projectId,
                category: category,
                status: status,
                search: search
            )
            sops = response.sops
            statistics = response.statistics
        } catch {
            errorMessage = "加载SOP失败: \(error.localizedDescription)"
        }

        isLoading = false
    }

    func loadSOPDetail(projectId: Int, sopId: Int) async {
        do {
            let sop = try await service.getSOPDetail(projectId: projectId, sopId: sopId)
            selectedSOP = sop
        } catch {
            errorMessage = "加载SOP详情失败: \(error.localizedDescription)"
        }
    }

    func createSOP(
        projectId: Int,
        title: String,
        category: String,
        description: String,
        steps: [SOPService.SOPStep],
        tags: [String]
    ) async {
        isCreating = true
        errorMessage = nil

        do {
            let newSOP = try await service.createSOP(
                projectId: projectId,
                title: title,
                category: category,
                description: description,
                steps: steps,
                tags: tags
            )
            sops.insert(newSOP, at: 0)
            successMessage = "SOP创建成功"
        } catch {
            errorMessage = "创建SOP失败: \(error.localizedDescription)"
        }

        isCreating = false
    }

    func updateSOPStatus(projectId: Int, sopId: Int, status: String) async {
        do {
            let updatedSOP = try await service.updateSOPStatus(
                projectId: projectId,
                sopId: sopId,
                status: status
            )
            if let index = sops.firstIndex(where: { $0.id == sopId }) {
                sops[index] = updatedSOP
            }
            successMessage = "状态更新成功"
        } catch {
            errorMessage = "更新状态失败: \(error.localizedDescription)"
        }
    }

    func deleteSOP(projectId: Int, sopId: Int) async {
        do {
            try await service.deleteSOP(projectId: projectId, sopId: sopId)
            sops.removeAll { $0.id == sopId }
            successMessage = "SOP删除成功"
        } catch {
            errorMessage = "删除SOP失败: \(error.localizedDescription)"
        }
    }

    func filterSOPs(searchText: String, category: String, status: String, sortBy: String) -> [SOPService.SOP] {
        var filtered = sops

        // Apply search filter
        if !searchText.isEmpty {
            filtered = filtered.filter { sop in
                sop.title.localizedCaseInsensitiveContains(searchText) ||
                sop.author.localizedCaseInsensitiveContains(searchText) ||
                sop.tags.contains { $0.localizedCaseInsensitiveContains(searchText) }
            }
        }

        // Apply category filter
        if category != "全部分类" {
            filtered = filtered.filter { $0.category == category }
        }

        // Apply status filter
        if status != "全部状态" {
            filtered = filtered.filter { $0.status == status }
        }

        // Apply sorting
        filtered.sort { sop1, sop2 in
            switch sortBy {
            case "usedCount":
                return sop1.usedCount > sop2.usedCount
            case "title":
                return sop1.title < sop2.title
            default:  // "lastModified"
                return sop1.lastModified > sop2.lastModified
            }
        }

        return filtered
    }
}
