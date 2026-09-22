import Foundation
import SwiftUI

@MainActor
class WorkflowViewModel: ObservableObject {
    @Published var workflows: [WorkflowService.WorkflowSummary] = []
    @Published var selectedWorkflow: WorkflowService.WorkflowStatusResponse?
    @Published var isLoadingList = false
    @Published var isExecuting = false
    @Published var isLoadingDetail = false
    @Published var errorMessage: String?
    @Published var successMessage: String?
    @Published var filterStatus: String? = nil

    private let service = WorkflowService.shared

    // MARK: - Methods

    func loadWorkflows() async {
        isLoadingList = true
        errorMessage = nil

        do {
            let response = try await service.listWorkflows(status: filterStatus, limit: 50)
            workflows = response.workflows
        } catch {
            errorMessage = "加载工作流列表失败: \(error.localizedDescription)"
        }

        isLoadingList = false
    }

    func executeWorkflow(workflowType: String, projectId: Int, documentIds: [Int]? = nil) async {
        isExecuting = true
        errorMessage = nil
        successMessage = nil

        do {
            let response = try await service.executeWorkflow(
                workflowType: workflowType,
                projectId: projectId,
                documentIds: documentIds
            )
            successMessage = response.message

            // 刷新列表
            await loadWorkflows()
        } catch {
            errorMessage = "执行工作流失败: \(error.localizedDescription)"
        }

        isExecuting = false
    }

    func loadWorkflowDetail(workflowId: String) async {
        isLoadingDetail = true
        errorMessage = nil

        do {
            selectedWorkflow = try await service.getWorkflowStatus(workflowId: workflowId)
        } catch {
            errorMessage = "加载工作流详情失败: \(error.localizedDescription)"
        }

        isLoadingDetail = false
    }

    func cancelWorkflow(workflowId: String) async {
        errorMessage = nil

        do {
            try await service.cancelWorkflow(workflowId: workflowId)
            successMessage = "工作流已取消"

            // 刷新列表
            await loadWorkflows()
        } catch {
            errorMessage = "取消工作流失败: \(error.localizedDescription)"
        }
    }

    func setFilterStatus(_ status: String?) {
        filterStatus = status
        Task {
            await loadWorkflows()
        }
    }

    func formatDate(_ dateString: String?) -> String {
        guard let dateString = dateString else { return "未知" }

        let formatter = ISO8601DateFormatter()
        guard let date = formatter.date(from: dateString) else { return dateString }

        let displayFormatter = DateFormatter()
        displayFormatter.dateFormat = "yyyy-MM-dd HH:mm:ss"
        return displayFormatter.string(from: date)
    }

    func statusColor(_ status: String) -> Color {
        switch status.lowercased() {
        case "completed":
            return Color.fmGreen
        case "running":
            return Color.fmPrimary
        case "failed":
            return Color.fmRed
        default:
            return Color.fmText3
        }
    }

    func statusLabel(_ status: String) -> String {
        switch status.lowercased() {
        case "completed":
            return "已完成"
        case "running":
            return "运行中"
        case "failed":
            return "失败"
        case "pending":
            return "等待中"
        default:
            return status
        }
    }
}
