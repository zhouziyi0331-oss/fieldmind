import SwiftUI

struct WorkflowsView: View {
    @State private var workflows: [Workflow] = []
    @State private var selectedWorkflow: Workflow?
    @State private var showNewWorkflowSheet = false
    @State private var isLoading = false

    var body: some View {
        HStack(spacing: 0) {
            // 左侧：工作流列表
            workflowListSidebar
                .frame(width: 280)

            // 右侧：工作流详情或空状态
            if let workflow = selectedWorkflow {
                workflowDetailView(workflow: workflow)
            } else {
                emptyStateView
            }
        }
        .background(Color.fieldMindBackground)
        .sheet(isPresented: $showNewWorkflowSheet) {
            NewWorkflowSheet(onSave: { workflow in
                createWorkflow(workflow: workflow)
            })
        }
        .onAppear {
            loadWorkflows()
        }
    }

    // MARK: - 左侧工作流列表
    private var workflowListSidebar: some View {
        VStack(spacing: 0) {
            // 标题和新建按钮
            HStack(spacing: 12) {
                Text("工作流模板")
                    .font(.system(size: 14, weight: .bold))
                    .foregroundColor(Color.fieldMindText)

                Spacer()

                Button {
                    showNewWorkflowSheet = true
                } label: {
                    Image(systemName: "plus.circle.fill")
                        .font(.system(size: 18))
                        .foregroundColor(Color.fieldMindPrimary)
                }
                .buttonStyle(PlainButtonStyle())
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 14)
            .background(Color.white)
            .overlay(
                Rectangle()
                    .fill(Color.gray.opacity(0.1))
                    .frame(height: 1),
                alignment: .bottom
            )

            // 工作流分类和列表
            if isLoading {
                Spacer()
                ProgressView()
                    .scaleEffect(0.8)
                Spacer()
            } else {
                ScrollView(showsIndicators: false) {
                    VStack(spacing: 16) {
                        // 预设工作流
                        workflowSection(
                            title: "预设工作流",
                            workflows: workflows.filter { $0.isPreset }
                        )

                        // 自定义工作流
                        workflowSection(
                            title: "自定义工作流",
                            workflows: workflows.filter { !$0.isPreset }
                        )
                    }
                    .padding(12)
                }
            }
        }
        .background(Color.white)
        .overlay(
            Rectangle()
                .fill(Color.gray.opacity(0.1))
                .frame(width: 1),
            alignment: .trailing
        )
    }

    private func workflowSection(title: String, workflows: [Workflow]) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(title)
                .font(.system(size: 11, weight: .semibold))
                .foregroundColor(Color.fieldMindText.opacity(0.6))
                .padding(.horizontal, 4)

            ForEach(workflows) { workflow in
                workflowListItem(workflow: workflow)
            }
        }
    }

    private func workflowListItem(workflow: Workflow) -> some View {
        Button {
            selectedWorkflow = workflow
        } label: {
            VStack(alignment: .leading, spacing: 8) {
                HStack(spacing: 8) {
                    Image(systemName: workflow.icon)
                        .font(.system(size: 14))
                        .foregroundColor(Color.fieldMindPrimary)
                        .frame(width: 20)

                    Text(workflow.name)
                        .font(.system(size: 12, weight: .medium))
                        .foregroundColor(Color.fieldMindText)
                        .lineLimit(1)

                    Spacer()

                    if workflow.isPreset {
                        Image(systemName: "star.fill")
                            .font(.system(size: 9))
                            .foregroundColor(Color.fieldMindSuccess)
                    }
                }

                Text(workflow.description)
                    .font(.system(size: 10))
                    .foregroundColor(Color.fieldMindText.opacity(0.6))
                    .lineLimit(2)

                HStack(spacing: 8) {
                    Label("\(workflow.stepCount)步骤", systemImage: "list.number")
                        .font(.system(size: 10))
                        .foregroundColor(Color.fieldMindText.opacity(0.5))

                    if let usageCount = workflow.usageCount {
                        Label("\(usageCount)次", systemImage: "arrow.clockwise")
                            .font(.system(size: 10))
                            .foregroundColor(Color.fieldMindText.opacity(0.5))
                    }
                }
            }
            .padding(12)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(
                selectedWorkflow?.id == workflow.id ?
                Color.fieldMindPrimary.opacity(0.08) : Color.fieldMindBackground
            )
            .cornerRadius(7)
            .overlay(
                RoundedRectangle(cornerRadius: 7)
                    .stroke(
                        selectedWorkflow?.id == workflow.id ?
                        Color.fieldMindPrimary.opacity(0.3) : Color.clear,
                        lineWidth: 1
                    )
            )
        }
        .buttonStyle(PlainButtonStyle())
    }

    // MARK: - 工作流详情视图
    private func workflowDetailView(workflow: Workflow) -> some View {
        ScrollView(showsIndicators: false) {
            VStack(alignment: .leading, spacing: 24) {
                // 顶部操作栏
                HStack {
                    Button {
                        selectedWorkflow = nil
                    } label: {
                        HStack(spacing: 6) {
                            Image(systemName: "chevron.left")
                                .font(.system(size: 11))
                            Text("返回列表")
                                .font(.system(size: 12))
                        }
                        .foregroundColor(Color.fieldMindText.opacity(0.6))
                    }
                    .buttonStyle(PlainButtonStyle())

                    Spacer()

                    HStack(spacing: 12) {
                        Button {
                            executeWorkflow(workflow: workflow)
                        } label: {
                            HStack(spacing: 6) {
                                Image(systemName: "play.fill")
                                    .font(.system(size: 11))
                                Text("执行工作流")
                                    .font(.system(size: 12, weight: .medium))
                            }
                            .foregroundColor(.white)
                            .padding(.horizontal, 16)
                            .padding(.vertical, 8)
                            .background(Color.fieldMindPrimary)
                            .cornerRadius(6)
                        }
                        .buttonStyle(PlainButtonStyle())

                        if !workflow.isPreset {
                            Menu {
                                Button("编辑工作流") {
                                    // 编辑
                                }
                                Button("复制工作流") {
                                    // 复制
                                }
                                Divider()
                                Button("删除工作流") {
                                    deleteWorkflow(workflow: workflow)
                                }
                            } label: {
                                Image(systemName: "ellipsis")
                                    .font(.system(size: 14))
                                    .foregroundColor(Color.fieldMindText.opacity(0.6))
                                    .frame(width: 32, height: 32)
                                    .background(Color.fieldMindBackground)
                                    .cornerRadius(6)
                            }
                            .menuStyle(BorderlessButtonMenuStyle())
                        }
                    }
                }

                // 工作流信息卡片
                VStack(alignment: .leading, spacing: 16) {
                    HStack(spacing: 12) {
                        Image(systemName: workflow.icon)
                            .font(.system(size: 24))
                            .foregroundColor(Color.fieldMindPrimary)
                            .frame(width: 40, height: 40)
                            .background(Color.fieldMindPrimary.opacity(0.1))
                            .cornerRadius(8)

                        VStack(alignment: .leading, spacing: 4) {
                            Text(workflow.name)
                                .font(.system(size: 16, weight: .bold))
                                .foregroundColor(Color.fieldMindText)

                            if workflow.isPreset {
                                HStack(spacing: 6) {
                                    Image(systemName: "star.fill")
                                        .font(.system(size: 9))
                                    Text("预设工作流")
                                        .font(.system(size: 10))
                                }
                                .foregroundColor(Color.fieldMindSuccess)
                                .padding(.horizontal, 8)
                                .padding(.vertical, 4)
                                .background(Color.fieldMindSuccess.opacity(0.1))
                                .cornerRadius(4)
                            }
                        }
                    }

                    Text(workflow.description)
                        .font(.system(size: 12))
                        .foregroundColor(Color.fieldMindText.opacity(0.8))
                        .lineSpacing(4)

                    HStack(spacing: 20) {
                        VStack(alignment: .leading, spacing: 4) {
                            Text("步骤数")
                                .font(.system(size: 10))
                                .foregroundColor(Color.fieldMindText.opacity(0.6))
                            Text("\(workflow.stepCount)")
                                .font(.system(size: 14, weight: .semibold))
                                .foregroundColor(Color.fieldMindText)
                        }

                        if let usageCount = workflow.usageCount {
                            VStack(alignment: .leading, spacing: 4) {
                                Text("使用次数")
                                    .font(.system(size: 10))
                                    .foregroundColor(Color.fieldMindText.opacity(0.6))
                                Text("\(usageCount)")
                                    .font(.system(size: 14, weight: .semibold))
                                    .foregroundColor(Color.fieldMindText)
                            }
                        }

                        if let avgDuration = workflow.avgDuration {
                            VStack(alignment: .leading, spacing: 4) {
                                Text("平均时长")
                                    .font(.system(size: 10))
                                    .foregroundColor(Color.fieldMindText.opacity(0.6))
                                Text(avgDuration)
                                    .font(.system(size: 14, weight: .semibold))
                                    .foregroundColor(Color.fieldMindText)
                            }
                        }
                    }
                }
                .padding(20)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(Color.white)
                .cornerRadius(10)

                // 工作流步骤
                VStack(alignment: .leading, spacing: 14) {
                    Text("工作流步骤")
                        .font(.system(size: 14, weight: .bold))
                        .foregroundColor(Color.fieldMindText)

                    VStack(spacing: 0) {
                        ForEach(Array(workflow.steps.enumerated()), id: \.offset) { index, step in
                            workflowStepItem(step: step, index: index, isLast: index == workflow.steps.count - 1)
                        }
                    }
                    .padding(16)
                    .background(Color.white)
                    .cornerRadius(10)
                }

                // 执行历史
                if let history = workflow.executionHistory, !history.isEmpty {
                    VStack(alignment: .leading, spacing: 14) {
                        Text("执行历史")
                            .font(.system(size: 14, weight: .bold))
                            .foregroundColor(Color.fieldMindText)

                        VStack(spacing: 8) {
                            ForEach(history) { execution in
                                executionHistoryItem(execution: execution)
                            }
                        }
                    }
                }
            }
            .padding(24)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color.fieldMindBackground)
    }

    private func workflowStepItem(step: WorkflowStep, index: Int, isLast: Bool) -> some View {
        VStack(spacing: 0) {
            HStack(alignment: .top, spacing: 12) {
                // 步骤序号
                VStack(spacing: 0) {
                    Text("\(index + 1)")
                        .font(.system(size: 12, weight: .bold))
                        .foregroundColor(.white)
                        .frame(width: 28, height: 28)
                        .background(Color.fieldMindPrimary)
                        .clipShape(Circle())

                    if !isLast {
                        Rectangle()
                            .fill(Color.fieldMindPrimary.opacity(0.2))
                            .frame(width: 2, height: 40)
                    }
                }

                // 步骤内容
                VStack(alignment: .leading, spacing: 8) {
                    Text(step.title)
                        .font(.system(size: 13, weight: .semibold))
                        .foregroundColor(Color.fieldMindText)

                    Text(step.description)
                        .font(.system(size: 11))
                        .foregroundColor(Color.fieldMindText.opacity(0.7))
                        .lineSpacing(3)

                    if let action = step.action {
                        HStack(spacing: 6) {
                            Image(systemName: "gearshape")
                                .font(.system(size: 9))
                            Text(action)
                                .font(.system(size: 10))
                        }
                        .foregroundColor(Color.fieldMindAuxiliary)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(Color.fieldMindAuxiliary.opacity(0.1))
                        .cornerRadius(4)
                    }
                }
                .padding(.bottom, isLast ? 0 : 12)

                Spacer()
            }
        }
    }

    private func executionHistoryItem(execution: WorkflowExecution) -> some View {
        HStack(spacing: 12) {
            Image(systemName: execution.status == "成功" ? "checkmark.circle.fill" : "xmark.circle.fill")
                .font(.system(size: 16))
                .foregroundColor(execution.status == "成功" ? Color.fieldMindSuccess : Color.fieldMindDanger)

            VStack(alignment: .leading, spacing: 4) {
                Text(execution.executedAt)
                    .font(.system(size: 12, weight: .medium))
                    .foregroundColor(Color.fieldMindText)

                HStack(spacing: 12) {
                    Label(execution.duration, systemImage: "clock")
                        .font(.system(size: 10))
                        .foregroundColor(Color.fieldMindText.opacity(0.6))

                    if let project = execution.projectName {
                        Label(project, systemImage: "folder")
                            .font(.system(size: 10))
                            .foregroundColor(Color.fieldMindText.opacity(0.6))
                    }
                }
            }

            Spacer()

            Text(execution.status)
                .font(.system(size: 10))
                .foregroundColor(execution.status == "成功" ? Color.fieldMindSuccess : Color.fieldMindDanger)
                .padding(.horizontal, 8)
                .padding(.vertical, 4)
                .background(
                    (execution.status == "成功" ? Color.fieldMindSuccess : Color.fieldMindDanger).opacity(0.1)
                )
                .cornerRadius(4)
        }
        .padding(12)
        .background(Color.fieldMindBackground)
        .cornerRadius(7)
    }

    // MARK: - 空状态视图
    private var emptyStateView: some View {
        VStack(spacing: 20) {
            Image(systemName: "arrow.triangle.branch")
                .font(.system(size: 64))
                .foregroundColor(Color.fieldMindText.opacity(0.2))

            Text("选择工作流查看详情")
                .font(.system(size: 14))
                .foregroundColor(Color.fieldMindText.opacity(0.6))

            Text("工作流可以自动化执行多个任务")
                .font(.system(size: 12))
                .foregroundColor(Color.fieldMindText.opacity(0.4))
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color.fieldMindBackground)
    }

    // MARK: - 数据操作
    private func loadWorkflows() {
        isLoading = true

        Task {
            do {
                let response = try await APIService.shared.getWorkflows(workflowType: nil, activeOnly: true)

                await MainActor.run {
                    // 转换API响应为视图模型
                    workflows = response.workflows.map { wf in
                        Workflow(
                            id: wf.id,
                            name: wf.name,
                            description: wf.description ?? "",
                            icon: iconForWorkflowType(wf.workflowType),
                            isPreset: true,
                            stepCount: wf.stepCount,
                            usageCount: wf.usageCount,
                            avgDuration: wf.avgDuration,
                            steps: [],  // 步骤信息需要从详情获取
                            executionHistory: wf.executionHistory.map { exec in
                                WorkflowExecution(
                                    id: exec.id,
                                    executedAt: formatDate(exec.executedAt),
                                    duration: formatDuration(exec.durationSeconds),
                                    status: exec.status == "completed" ? "成功" :
                                            exec.status == "failed" ? "失败" : "运行中",
                                    projectName: exec.projectName ?? "未知项目"
                                )
                            }
                        )
                    }
                    isLoading = false
                }
            } catch {
                await MainActor.run {
                    errorMessage = "加载工作流失败: \(error.localizedDescription)"
                    showError = true
                    isLoading = false
                }
            }
        }
    }

    private func iconForWorkflowType(_ type: String) -> String {
        switch type {
        case "document":
            return "mappin.and.ellipse"
        case "audio":
            return "waveform.circle"
        case "crawler":
            return "network"
        case "report":
            return "doc.text"
        default:
            return "gearshape.2"
        }
    }

    private func formatDate(_ isoDate: String) -> String {
        let formatter = ISO8601DateFormatter()
        if let date = formatter.date(from: isoDate) {
            let displayFormatter = DateFormatter()
            displayFormatter.dateFormat = "yyyy-MM-dd HH:mm"
            return displayFormatter.string(from: date)
        }
        return isoDate
    }

    private func formatDuration(_ seconds: Double?) -> String {
        guard let seconds = seconds else { return "未知" }
        let minutes = Int(seconds / 60)
        let secs = Int(seconds.truncatingRemainder(dividingBy: 60))
        if minutes > 0 {
            return "\(minutes)分\(secs)秒"
        } else {
            return "\(secs)秒"
        }
    }

    // 保留旧的假数据作为fallback（如果API失败）
    private func loadWorkflowsFallback() {
        workflows = [
            Workflow(
                id: "fallback-1",
                name: "田野调查完整流程",
                description: "从文档导入、信息提取、知识图谱构建到报告生成的完整流程",
                icon: "mappin.and.ellipse",
                isPreset: true,
                stepCount: 6,
                usageCount: 0,
                avgDuration: "未知",
                steps: [
                    WorkflowStep(
                        title: "导入田野调查材料",
                        description: "上传田野调查笔记、访谈录音、照片等材料",
                        action: "文档导入"
                    ),
                    WorkflowStep(
                        title: "自动转写音视频",
                        description: "对访谈录音进行自动转写并生成文字稿",
                        action: "音视频转写"
                    ),
                    WorkflowStep(
                        title: "提取知识脉络",
                        description: "从材料中提取关键事件、人物、地点等信息",
                        action: "知识提取"
                    ),
                    WorkflowStep(
                        title: "构建关系图谱",
                        description: "自动构建人物、事件、地点之间的关系网络",
                        action: "图谱构建"
                    ),
                    WorkflowStep(
                        title: "生成编年史",
                        description: "按时间线整理所有事件",
                        action: "时间线生成"
                    ),
                    WorkflowStep(
                        title: "生成一度报告",
                        description: "自动生成信息整理报告",
                        action: "报告生成"
                    )
                ],
                executionHistory: []
            ),
            Workflow(
                id: "fallback-2",
                name: "产业分析工作流",
                description: "网络爬虫采集行业信息，结合本地材料进行产业分析",
                icon: "chart.line.uptrend.xyaxis",
                isPreset: true,
                stepCount: 4,
                usageCount: 0,
                avgDuration: "未知",
                steps: [
                    WorkflowStep(
                        title: "启动网络爬虫",
                        description: "从行业网站采集相关信息",
                        action: "爬虫采集"
                    ),
                    WorkflowStep(
                        title: "导入爬取结果",
                        description: "将采集的信息导入项目",
                        action: "数据导入"
                    ),
                    WorkflowStep(
                        title: "行业分析",
                        description: "使用行业分析框架分析市场",
                        action: "业态分析"
                    ),
                    WorkflowStep(
                        title: "生成三度报告",
                        description: "生成商业推演报告",
                        action: "报告生成"
                    )
                ],
                executionHistory: []
            )
        ]
        isLoading = false
    }

    private func createWorkflow(workflow: Workflow) {
        Task {
            do {
                // 构建steps数组
                let steps = workflow.steps.map { step in
                    [
                        "order": workflow.steps.firstIndex(where: { $0.title == step.title })! + 1,
                        "name": step.title,
                        "task": step.action,
                        "description": step.description
                    ] as [String : Any]
                }

                let _ = try await APIService.shared.createWorkflow(
                    name: workflow.name,
                    description: workflow.description,
                    workflowType: "document",
                    steps: steps,
                    config: nil
                )

                await MainActor.run {
                    showNewWorkflowSheet = false
                    loadWorkflows()
                }
            } catch {
                await MainActor.run {
                    errorMessage = "创建工作流失败: \(error.localizedDescription)"
                    showError = true
                }
            }
        }
    }

    private func executeWorkflow(workflow: Workflow) {
        Task {
            do {
                let _ = try await APIService.shared.executeWorkflow(
                    workflowId: workflow.id,
                    projectId: nil,
                    inputData: [:]
                )

                await MainActor.run {
                    print("工作流执行已启动: \(workflow.name)")
                    loadWorkflows()  // 刷新执行历史
                }
            } catch {
                await MainActor.run {
                    errorMessage = "执行工作流失败: \(error.localizedDescription)"
                    showError = true
                }
            }
        }
    }

    private func deleteWorkflow(workflow: Workflow) {
        Task {
            do {
                try await APIService.shared.deleteWorkflow(workflowId: workflow.id)

                await MainActor.run {
                    workflows.removeAll { $0.id == workflow.id }
                    selectedWorkflow = nil
                }
            } catch {
                await MainActor.run {
                    errorMessage = "删除工作流失败: \(error.localizedDescription)"
                    showError = true
                }
            }
        }
    }
}

// MARK: - 数据模型
struct Workflow: Identifiable {
    let id: String
    let name: String
    let description: String
    let icon: String
    let isPreset: Bool
    let stepCount: Int
    let usageCount: Int?
    let avgDuration: String?
    let steps: [WorkflowStep]
    let executionHistory: [WorkflowExecution]?
}

struct WorkflowStep {
    let title: String
    let description: String
    let action: String?
}

struct WorkflowExecution: Identifiable {
    let id: String
    let executedAt: String
    let duration: String
    let status: String
    let projectName: String?
}

// MARK: - 新建工作流表单
struct NewWorkflowSheet: View {
    let onSave: (Workflow) -> Void
    @Environment(\.dismiss) var dismiss

    @State private var name = ""
    @State private var description = ""
    @State private var selectedIcon = "arrow.triangle.branch"

    let availableIcons = [
        "arrow.triangle.branch", "mappin.and.ellipse", "chart.line.uptrend.xyaxis",
        "books.vertical", "doc.text.magnifyingglass", "network"
    ]

    var body: some View {
        VStack(spacing: 0) {
            // 标题栏
            HStack {
                Text("新建工作流")
                    .font(.system(size: 16, weight: .bold))
                    .foregroundColor(Color.fieldMindText)

                Spacer()

                Button("取消") {
                    dismiss()
                }
                .font(.system(size: 12))
                .foregroundColor(Color.fieldMindText.opacity(0.6))
            }
            .padding(20)
            .background(Color.white)
            .overlay(
                Rectangle()
                    .fill(Color.gray.opacity(0.1))
                    .frame(height: 1),
                alignment: .bottom
            )

            ScrollView(showsIndicators: false) {
                VStack(alignment: .leading, spacing: 20) {
                    // 工作流名称
                    VStack(alignment: .leading, spacing: 8) {
                        Text("工作流名称")
                            .font(.system(size: 12, weight: .semibold))
                            .foregroundColor(Color.fieldMindText)

                        TextField("例如：田野调查完整流程", text: $name)
                            .textFieldStyle(CustomTextFieldStyle())
                    }

                    // 工作流描述
                    VStack(alignment: .leading, spacing: 8) {
                        Text("工作流描述")
                            .font(.system(size: 12, weight: .semibold))
                            .foregroundColor(Color.fieldMindText)

                        TextField("描述这个工作流的用途", text: $description)
                            .textFieldStyle(CustomTextFieldStyle())
                    }

                    // 图标选择
                    VStack(alignment: .leading, spacing: 8) {
                        Text("选择图标")
                            .font(.system(size: 12, weight: .semibold))
                            .foregroundColor(Color.fieldMindText)

                        HStack(spacing: 12) {
                            ForEach(availableIcons, id: \.self) { icon in
                                Button {
                                    selectedIcon = icon
                                } label: {
                                    Image(systemName: icon)
                                        .font(.system(size: 20))
                                        .foregroundColor(
                                            selectedIcon == icon ?
                                            .white : Color.fieldMindPrimary
                                        )
                                        .frame(width: 44, height: 44)
                                        .background(
                                            selectedIcon == icon ?
                                            Color.fieldMindPrimary : Color.fieldMindPrimary.opacity(0.1)
                                        )
                                        .cornerRadius(8)
                                }
                                .buttonStyle(PlainButtonStyle())
                            }
                        }
                    }

                    // 保存按钮
                    Button {
                        let workflow = Workflow(
                            id: UUID().uuidString,
                            name: name,
                            description: description,
                            icon: selectedIcon,
                            isPreset: false,
                            stepCount: 0,
                            usageCount: 0,
                            avgDuration: nil,
                            steps: [],
                            executionHistory: nil
                        )
                        onSave(workflow)
                        dismiss()
                    } label: {
                        Text("创建工作流")
                            .font(.system(size: 13, weight: .medium))
                            .foregroundColor(.white)
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 12)
                            .background(
                                name.isEmpty || description.isEmpty ?
                                Color.gray.opacity(0.3) : Color.fieldMindPrimary
                            )
                            .cornerRadius(7)
                    }
                    .buttonStyle(PlainButtonStyle())
                    .disabled(name.isEmpty || description.isEmpty)
                }
                .padding(20)
            }
        }
        .frame(width: 500, height: 450)
        .background(Color.fieldMindBackground)
    }
}
