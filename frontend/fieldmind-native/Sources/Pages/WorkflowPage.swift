import SwiftUI

struct WorkflowPage: View {
    let projectId: Int

    @StateObject private var viewModel = WorkflowViewModel()
    @State private var showExecuteSheet = false
    @State private var selectedWorkflowType = "document_processing"

    var body: some View {
        VStack(spacing: 0) {
            // Header
            HStack {
                Text("工作流管理")
                    .font(.system(size: 22, weight: .semibold))
                    .foregroundColor(Color.fmText)

                Spacer()

                // Filter buttons
                HStack(spacing: 8) {
                    FilterButton(
                        title: "全部",
                        isSelected: viewModel.filterStatus == nil,
                        action: { viewModel.setFilterStatus(nil) }
                    )
                    FilterButton(
                        title: "运行中",
                        isSelected: viewModel.filterStatus == "running",
                        action: { viewModel.setFilterStatus("running") }
                    )
                    FilterButton(
                        title: "已完成",
                        isSelected: viewModel.filterStatus == "completed",
                        action: { viewModel.setFilterStatus("completed") }
                    )
                    FilterButton(
                        title: "失败",
                        isSelected: viewModel.filterStatus == "failed",
                        action: { viewModel.setFilterStatus("failed") }
                    )
                }

                Button(action: { showExecuteSheet = true }) {
                    HStack(spacing: 6) {
                        Image(systemName: "play.circle")
                            .font(.system(size: 13))
                        Text("执行工作流")
                            .font(.system(size: 13, weight: .medium))
                    }
                    .foregroundColor(.white)
                    .padding(.horizontal, 16)
                    .padding(.vertical, 8)
                    .background(Color.fmPrimary)
                    .cornerRadius(8)
                }
                .buttonStyle(PlainButtonStyle())
            }
            .padding(20)

            Divider()

            // Success message
            if let success = viewModel.successMessage {
                HStack {
                    Image(systemName: "checkmark.circle.fill")
                        .foregroundColor(Color.fmGreen)
                    Text(success)
                        .font(.system(size: 13))
                        .foregroundColor(Color.fmText2)
                    Spacer()
                    Button("关闭") {
                        viewModel.successMessage = nil
                    }
                    .font(.system(size: 12))
                }
                .padding(12)
                .background(Color.fmGreen.opacity(0.1))
                .cornerRadius(8)
                .padding(.horizontal, 20)
                .padding(.top, 12)
            }

            // Error message
            if let error = viewModel.errorMessage {
                HStack {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .foregroundColor(Color.fmRed)
                    Text(error)
                        .font(.system(size: 13))
                        .foregroundColor(Color.fmText2)
                    Spacer()
                    Button("关闭") {
                        viewModel.errorMessage = nil
                    }
                    .font(.system(size: 12))
                }
                .padding(12)
                .background(Color.fmRed.opacity(0.1))
                .cornerRadius(8)
                .padding(.horizontal, 20)
                .padding(.top, 12)
            }

            // Main content
            if viewModel.isLoadingList {
                loadingView
            } else if viewModel.workflows.isEmpty {
                emptyView
            } else {
                workflowListView
            }
        }
        .sheet(isPresented: $showExecuteSheet) {
            ExecuteWorkflowSheet(
                isPresented: $showExecuteSheet,
                selectedType: $selectedWorkflowType,
                onExecute: {
                    Task {
                        await viewModel.executeWorkflow(
                            workflowType: selectedWorkflowType,
                            projectId: projectId
                        )
                        showExecuteSheet = false
                    }
                }
            )
        }
        .task {
            await viewModel.loadWorkflows()
        }
    }

    // MARK: - Loading View

    private var loadingView: some View {
        VStack(spacing: 16) {
            ProgressView()
                .scaleEffect(1.5)
            Text("加载工作流中...")
                .font(.system(size: 14))
                .foregroundColor(Color.fmText2)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    // MARK: - Empty View

    private var emptyView: some View {
        VStack(spacing: 16) {
            Image(systemName: "flowchart")
                .font(.system(size: 48))
                .foregroundColor(Color.fmText3)
            Text("还没有执行过工作流")
                .font(.system(size: 16, weight: .medium))
                .foregroundColor(Color.fmText2)
            Text("点击「执行工作流」按钮创建第一个工作流")
                .font(.system(size: 13))
                .foregroundColor(Color.fmText3)

            Button(action: { showExecuteSheet = true }) {
                HStack(spacing: 6) {
                    Image(systemName: "play.circle")
                    Text("执行工作流")
                }
                .font(.system(size: 13, weight: .medium))
                .foregroundColor(.white)
                .padding(.horizontal, 20)
                .padding(.vertical, 10)
                .background(Color.fmPrimary)
                .cornerRadius(8)
            }
            .buttonStyle(PlainButtonStyle())
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    // MARK: - Workflow List View

    private var workflowListView: some View {
        ScrollView {
            VStack(spacing: 16) {
                ForEach(viewModel.workflows) { workflow in
                    WorkflowExecutionCard(workflow: workflow, viewModel: viewModel)
                }
            }
            .padding(20)
        }
    }
}

// MARK: - Filter Button

struct FilterButton: View {
    let title: String
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Text(title)
                .font(.system(size: 12))
                .foregroundColor(isSelected ? .white : Color.fmText2)
                .padding(.horizontal, 12)
                .padding(.vertical, 6)
                .background(isSelected ? Color.fmPrimary : Color.fmBg)
                .cornerRadius(6)
        }
        .buttonStyle(PlainButtonStyle())
    }
}

// MARK: - Workflow Card

struct WorkflowExecutionCard: View {
    let workflow: WorkflowService.WorkflowSummary
    @ObservedObject var viewModel: WorkflowViewModel

    @State private var showDetail = false

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Header
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text(workflow.workflowName)
                        .font(.system(size: 16, weight: .semibold))
                        .foregroundColor(Color.fmText)

                    Text("ID: \(workflow.workflowId)")
                        .font(.system(size: 11))
                        .foregroundColor(Color.fmText3)
                        .fontDesign(.monospaced)
                }

                Spacer()

                // Status badge
                HStack(spacing: 4) {
                    Circle()
                        .fill(viewModel.statusColor(workflow.status))
                        .frame(width: 6, height: 6)
                    Text(viewModel.statusLabel(workflow.status))
                        .font(.system(size: 12, weight: .medium))
                        .foregroundColor(viewModel.statusColor(workflow.status))
                }
                .padding(.horizontal, 10)
                .padding(.vertical, 5)
                .background(viewModel.statusColor(workflow.status).opacity(0.1))
                .cornerRadius(12)
            }

            // Stats
            HStack(spacing: 20) {
                WorkflowStatItem(
                    icon: "checkmark.circle",
                    label: "已完成",
                    value: "\(workflow.completedTasks)/\(workflow.taskCount)",
                    color: Color.fmGreen
                )

                if workflow.failedTasks > 0 {
                    WorkflowStatItem(
                        icon: "xmark.circle",
                        label: "失败",
                        value: "\(workflow.failedTasks)",
                        color: Color.fmRed
                    )
                }

                Spacer()

                // Timestamps
                VStack(alignment: .trailing, spacing: 2) {
                    if let startTime = workflow.startTime {
                        HStack(spacing: 4) {
                            Image(systemName: "clock")
                                .font(.system(size: 10))
                            Text("开始: \(viewModel.formatDate(startTime))")
                                .font(.system(size: 11))
                        }
                        .foregroundColor(Color.fmText3)
                    }

                    if let endTime = workflow.endTime {
                        HStack(spacing: 4) {
                            Image(systemName: "clock.badge.checkmark")
                                .font(.system(size: 10))
                            Text("结束: \(viewModel.formatDate(endTime))")
                                .font(.system(size: 11))
                        }
                        .foregroundColor(Color.fmText3)
                    }
                }
            }

            // Actions
            HStack(spacing: 8) {
                Button(action: { showDetail.toggle() }) {
                    HStack(spacing: 4) {
                        Image(systemName: "info.circle")
                            .font(.system(size: 11))
                        Text("查看详情")
                            .font(.system(size: 12))
                    }
                    .foregroundColor(Color.fmPrimary)
                    .padding(.horizontal, 12)
                    .padding(.vertical, 6)
                    .background(Color.fmPrimary.opacity(0.1))
                    .cornerRadius(6)
                }
                .buttonStyle(PlainButtonStyle())

                if workflow.status.lowercased() == "running" {
                    Button(action: {
                        Task {
                            await viewModel.cancelWorkflow(workflowId: workflow.workflowId)
                        }
                    }) {
                        HStack(spacing: 4) {
                            Image(systemName: "stop.circle")
                                .font(.system(size: 11))
                            Text("取消")
                                .font(.system(size: 12))
                        }
                        .foregroundColor(Color.fmRed)
                        .padding(.horizontal, 12)
                        .padding(.vertical, 6)
                        .background(Color.fmRed.opacity(0.1))
                        .cornerRadius(6)
                    }
                    .buttonStyle(PlainButtonStyle())
                }
            }

            // Detail view
            if showDetail {
                Divider()
                    .padding(.vertical, 4)

                if viewModel.isLoadingDetail {
                    HStack {
                        ProgressView()
                            .scaleEffect(0.8)
                        Text("加载详情中...")
                            .font(.system(size: 12))
                            .foregroundColor(Color.fmText3)
                    }
                } else if let detail = viewModel.selectedWorkflow, detail.workflowId == workflow.workflowId {
                    WorkflowDetailView(detail: detail, viewModel: viewModel)
                }
            }
        }
        .padding(16)
        .background(Color.white)
        .cornerRadius(12)
        .shadow(color: Color.black.opacity(0.05), radius: 8, x: 0, y: 2)
        .onChange(of: showDetail) { newValue in
            if newValue {
                Task {
                    await viewModel.loadWorkflowDetail(workflowId: workflow.workflowId)
                }
            }
        }
    }
}

// MARK: - Workflow Stat Item

struct WorkflowStatItem: View {
    let icon: String
    let label: String
    let value: String
    let color: Color

    var body: some View {
        HStack(spacing: 6) {
            Image(systemName: icon)
                .font(.system(size: 12))
                .foregroundColor(color)
            VStack(alignment: .leading, spacing: 2) {
                Text(label)
                    .font(.system(size: 10))
                    .foregroundColor(Color.fmText3)
                Text(value)
                    .font(.system(size: 13, weight: .medium))
                    .foregroundColor(color)
            }
        }
    }
}

// MARK: - Workflow Detail View

struct WorkflowDetailView: View {
    let detail: WorkflowService.WorkflowStatusResponse
    @ObservedObject var viewModel: WorkflowViewModel

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("任务详情")
                .font(.system(size: 13, weight: .semibold))
                .foregroundColor(Color.fmText2)

            ForEach(Array(detail.taskResults.keys.sorted()), id: \.self) { taskName in
                if let taskResult = detail.taskResults[taskName] {
                    TaskResultRow(taskName: taskName, result: taskResult, viewModel: viewModel)
                }
            }
        }
        .padding(12)
        .background(Color.fmBg)
        .cornerRadius(8)
    }
}

// MARK: - Task Result Row

struct TaskResultRow: View {
    let taskName: String
    let result: WorkflowService.TaskResult
    @ObservedObject var viewModel: WorkflowViewModel

    var body: some View {
        HStack(spacing: 8) {
            Image(systemName: statusIcon)
                .font(.system(size: 12))
                .foregroundColor(viewModel.statusColor(result.status))

            VStack(alignment: .leading, spacing: 2) {
                Text(taskName)
                    .font(.system(size: 12, weight: .medium))
                    .foregroundColor(Color.fmText)

                if let error = result.error {
                    Text(error)
                        .font(.system(size: 11))
                        .foregroundColor(Color.fmRed)
                }
            }

            Spacer()

            if let duration = result.duration {
                Text(String(format: "%.2fs", duration))
                    .font(.system(size: 11))
                    .foregroundColor(Color.fmText3)
            }
        }
        .padding(8)
        .background(Color.white)
        .cornerRadius(6)
    }

    private var statusIcon: String {
        switch result.status.lowercased() {
        case "completed":
            return "checkmark.circle.fill"
        case "failed":
            return "xmark.circle.fill"
        case "running":
            return "arrow.2.circlepath"
        default:
            return "circle"
        }
    }
}

// MARK: - Execute Workflow Sheet

struct ExecuteWorkflowSheet: View {
    @Binding var isPresented: Bool
    @Binding var selectedType: String
    let onExecute: () -> Void

    var body: some View {
        VStack(spacing: 20) {
            // Header
            HStack {
                Text("执行工作流")
                    .font(.system(size: 18, weight: .semibold))
                    .foregroundColor(Color.fmText)
                Spacer()
                Button(action: { isPresented = false }) {
                    Image(systemName: "xmark.circle.fill")
                        .font(.system(size: 20))
                        .foregroundColor(Color.fmText3)
                }
                .buttonStyle(PlainButtonStyle())
            }

            Divider()

            // Workflow type selection
            VStack(alignment: .leading, spacing: 12) {
                Text("选择工作流类型")
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(Color.fmText2)

                VStack(spacing: 12) {
                    WorkflowTypeOption(
                        type: "document_processing",
                        title: "文档处理",
                        description: "向量化 + 实体提取 + 关键词分析",
                        isSelected: selectedType == "document_processing",
                        onSelect: { selectedType = "document_processing" }
                    )

                    WorkflowTypeOption(
                        type: "knowledge_graph",
                        title: "知识图谱构建",
                        description: "实体 + 关系 + 时间线可视化",
                        isSelected: selectedType == "knowledge_graph",
                        onSelect: { selectedType = "knowledge_graph" }
                    )

                    WorkflowTypeOption(
                        type: "full_analysis",
                        title: "完整分析",
                        description: "文档处理 + 知识图谱 + 报告生成",
                        isSelected: selectedType == "full_analysis",
                        onSelect: { selectedType = "full_analysis" }
                    )
                }
            }

            Spacer()

            // Action buttons
            HStack(spacing: 12) {
                Button(action: { isPresented = false }) {
                    Text("取消")
                        .font(.system(size: 13, weight: .medium))
                        .foregroundColor(Color.fmText2)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 10)
                        .background(Color.fmBg)
                        .cornerRadius(8)
                }
                .buttonStyle(PlainButtonStyle())

                Button(action: onExecute) {
                    Text("开始执行")
                        .font(.system(size: 13, weight: .medium))
                        .foregroundColor(.white)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 10)
                        .background(Color.fmPrimary)
                        .cornerRadius(8)
                }
                .buttonStyle(PlainButtonStyle())
            }
        }
        .padding(24)
        .frame(width: 480, height: 450)
        .background(Color.white)
    }
}

// MARK: - Workflow Type Option

struct WorkflowTypeOption: View {
    let type: String
    let title: String
    let description: String
    let isSelected: Bool
    let onSelect: () -> Void

    var body: some View {
        Button(action: onSelect) {
            HStack(alignment: .top, spacing: 12) {
                ZStack {
                    Circle()
                        .stroke(isSelected ? Color.fmPrimary : Color.fmBorder, lineWidth: 2)
                        .frame(width: 20, height: 20)
                    if isSelected {
                        Circle()
                            .fill(Color.fmPrimary)
                            .frame(width: 12, height: 12)
                    }
                }
                .padding(.top, 2)

                VStack(alignment: .leading, spacing: 4) {
                    Text(title)
                        .font(.system(size: 14, weight: .semibold))
                        .foregroundColor(Color.fmText)

                    Text(description)
                        .font(.system(size: 12))
                        .foregroundColor(Color.fmText3)
                }

                Spacer()
            }
            .padding(12)
            .background(isSelected ? Color.fmPrimary.opacity(0.05) : Color.fmBg)
            .cornerRadius(8)
            .overlay(
                RoundedRectangle(cornerRadius: 8)
                    .stroke(isSelected ? Color.fmPrimary : Color.clear, lineWidth: 2)
            )
        }
        .buttonStyle(PlainButtonStyle())
    }
}
