import SwiftUI

struct ReportsView: View {
    @EnvironmentObject var appState: AppState
    @ObservedObject private var dataManager = ProjectDataManager.shared
    @State private var selectedReport: ReportResponse?
    @State private var showNewReportForm = false
    @State private var isGenerating = false

    var body: some View {
        HStack(spacing: 0) {
            // 左侧：报告列表
            reportListSidebar
                .frame(width: 280)

            // 右侧：新建表单或报告详情
            if let report = selectedReport {
                reportDetailView(report: report)
            } else {
                if showNewReportForm {
                    newReportFormView
                } else {
                    emptyStateView
                }
            }
        }
        .background(Color.fieldMindBackground)
    }

    // MARK: - 左侧报告列表
    private var reportListSidebar: some View {
        VStack(spacing: 0) {
            // 标题和新建按钮
            HStack(spacing: 12) {
                Text("报告列表")
                    .font(.system(size: 14, weight: .bold))
                    .foregroundColor(Color.fieldMindText)

                Spacer()

                Button {
                    selectedReport = nil
                    showNewReportForm = true
                } label: {
                    Image(systemName: "plus.circle.fill")
                        .font(.system(size: 18))
                        .foregroundColor(Color.fieldMindPrimary)
                }
                .buttonStyle(PlainButtonStyle())
                .disabled(appState.currentProject == nil)
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

            // 报告列表
            if dataManager.isLoadingReports {
                Spacer()
                ProgressView()
                    .scaleEffect(0.8)
                Spacer()
            } else if dataManager.reports.isEmpty {
                Spacer()
                VStack(spacing: 8) {
                    Image(systemName: "doc.text")
                        .font(.system(size: 32))
                        .foregroundColor(Color.fieldMindText.opacity(0.3))
                    Text("暂无报告")
                        .font(.system(size: 12))
                        .foregroundColor(Color.fieldMindText.opacity(0.5))
                }
                Spacer()
            } else {
                ScrollView(showsIndicators: false) {
                    VStack(spacing: 8) {
                        ForEach(dataManager.reports) { report in
                            reportListItem(report: report)
                        }
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

    private func reportListItem(report: ReportResponse) -> some View {
        Button {
            selectedReport = report
            showNewReportForm = false
        } label: {
            VStack(alignment: .leading, spacing: 8) {
                HStack(spacing: 8) {
                    // 报告类型标签
                    Text(report.layerLabel)
                        .font(.system(size: 10, weight: .medium))
                        .foregroundColor(.white)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(report.layerColor)
                        .cornerRadius(4)

                    Spacer()

                    // 状态标签
                    Text(report.status)
                        .font(.system(size: 10))
                        .foregroundColor(report.statusColor)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(report.statusColor.opacity(0.1))
                        .cornerRadius(4)
                }

                Text(report.title)
                    .font(.system(size: 13, weight: .medium))
                    .foregroundColor(Color.fieldMindText)
                    .lineLimit(2)
                    .multilineTextAlignment(.leading)

                HStack(spacing: 12) {
                    Label(report.createdAt, systemImage: "clock")
                        .font(.system(size: 10))
                        .foregroundColor(Color.fieldMindText.opacity(0.6))

                    if let wordCount = report.wordCount {
                        Label("\(wordCount)字", systemImage: "doc.text")
                            .font(.system(size: 10))
                            .foregroundColor(Color.fieldMindText.opacity(0.6))
                    }
                }
            }
            .padding(12)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(
                selectedReport?.id == report.id ?
                Color.fieldMindPrimary.opacity(0.08) : Color.fieldMindBackground
            )
            .cornerRadius(7)
            .overlay(
                RoundedRectangle(cornerRadius: 7)
                    .stroke(
                        selectedReport?.id == report.id ?
                        Color.fieldMindPrimary.opacity(0.3) : Color.clear,
                        lineWidth: 1
                    )
            )
        }
        .buttonStyle(PlainButtonStyle())
    }

    // MARK: - 新建报告表单
    private var newReportFormView: some View {
        NewReportFormView(
            onCancel: {
                showNewReportForm = false
            },
            onSubmit: { config in
                createReport(config: config)
            }
        )
    }

    // MARK: - 报告详情视图
    private func reportDetailView(report: ReportResponse) -> some View {
        ReportDetailView(
            report: report,
            onClose: {
                selectedReport = nil
            },
            onDelete: {
                deleteReport(report: report)
            },
            onRegenerate: {
                regenerateReport(report: report)
            }
        )
    }

    // MARK: - 空状态视图
    private var emptyStateView: some View {
        VStack(spacing: 20) {
            Image(systemName: "doc.text.magnifyingglass")
                .font(.system(size: 64))
                .foregroundColor(Color.fieldMindText.opacity(0.2))

            Text("选择报告查看详情")
                .font(.system(size: 14))
                .foregroundColor(Color.fieldMindText.opacity(0.6))

            Text("或点击左上角 + 创建新报告")
                .font(.system(size: 12))
                .foregroundColor(Color.fieldMindText.opacity(0.4))
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color.fieldMindBackground)
    }

    // MARK: - 数据操作
    private func createReport(config: ReportConfig) {
        guard appState.currentProject?.id != nil else { return }

        isGenerating = true

        Task {
            do {
                let reportType = config.layer == 1 ? "summary" : (config.layer == 2 ? "analysis" : "business")

                let include: [String: Bool] = [
                    "charts": config.includeCharts,
                    "references": config.includeReferences,
                    "statistics": true
                ]

                let dataSources: [String: [String]] = [
                    "documents": [],
                    "contexts": [],
                    "timeline": []
                ]

                let response = try await APIService.shared.generateReport(
                    title: config.title ?? "新报告",
                    reportType: reportType,
                    timeRange: nil,
                    include: include,
                    dataSources: dataSources,
                    format: config.format.lowercased()
                )

                await MainActor.run {
                    print("✅ 报告生成任务已提交: \(response.reportId)")
                    ToastManager.shared.success("报告生成任务已提交")
                    showNewReportForm = false
                    isGenerating = false
                    dataManager.loadReports()
                }
            } catch {
                print("❌ 创建报告失败: \(error)")
                ToastManager.shared.error("创建报告失败")
                await MainActor.run {
                    isGenerating = false
                }
            }
        }
    }

    private func deleteReport(report: ReportResponse) {
        Task {
            do {
                let urlString = "http://localhost:8000/api/v1/reports/\(report.id)"
                guard let url = URL(string: urlString) else { return }

                var request = URLRequest(url: url)
                request.httpMethod = "DELETE"

                let (_, _) = try await URLSession.shared.data(for: request)

                await MainActor.run {
                    dataManager.reports.removeAll { $0.id == report.id }
                    selectedReport = nil
                    print("✅ 报告已删除")
                    ToastManager.shared.success("报告已删除")
                }
            } catch {
                print("❌ 删除报告失败: \(error)")
                ToastManager.shared.error("删除报告失败")
            }
        }
    }

    private func regenerateReport(report: ReportResponse) {
        guard appState.currentProject?.id != nil else { return }

        Task {
            do {
                let reportType = report.layer == 1 ? "summary" : (report.layer == 2 ? "analysis" : "business")

                let include: [String: Bool] = [
                    "charts": true,
                    "references": true,
                    "statistics": true
                ]

                let dataSources: [String: [String]] = [
                    "documents": [],
                    "contexts": [],
                    "timeline": []
                ]

                _ = try await APIService.shared.generateReport(
                    title: report.title,
                    reportType: reportType,
                    timeRange: nil,
                    include: include,
                    dataSources: dataSources,
                    format: "docx"
                )

                await MainActor.run {
                    print("✅ 报告重新生成任务已提交")
                    ToastManager.shared.success("报告重新生成任务已提交")
                    dataManager.loadReports()
                }
            } catch {
                print("❌ 重新生成报告失败: \(error)")
                ToastManager.shared.error("重新生成报告失败")
            }
        }
    }
}

// MARK: - 报告数据模型
struct Report: Identifiable {
    let id: String
    let title: String
    let layer: Int
    let status: String
    let createdAt: String
    let wordCount: Int?
    let projectName: String

    var layerLabel: String {
        switch layer {
        case 1: return "一度报告"
        case 2: return "二度报告"
        case 3: return "三度报告"
        default: return "报告"
        }
    }

    var layerColor: Color {
        switch layer {
        case 1: return Color.fieldMindPrimary
        case 2: return Color.fieldMindSuccess
        case 3: return Color(hex: "D4A574")
        default: return Color.fieldMindNeutral
        }
    }

    var statusColor: Color {
        switch status {
        case "已生成": return Color.fieldMindSuccess
        case "生成中": return Color.fieldMindPrimary
        case "失败": return Color.fieldMindDanger
        default: return Color.fieldMindText.opacity(0.6)
        }
    }
}

// MARK: - 新建报告表单
struct NewReportFormView: View {
    let onCancel: () -> Void
    let onSubmit: (ReportConfig) -> Void

    @State private var reportTitle = ""
    @State private var reportLayer = 1
    @State private var selectedSkills: [String] = []
    @State private var reportStyle = "学术型"
    @State private var exportFormat = "PDF"
    @State private var includeCharts = true
    @State private var includeReferences = true

    @State private var availableSkills: [String] = []
    @State private var isLoadingSkills = false

    var body: some View {
        ScrollView(showsIndicators: false) {
            VStack(alignment: .leading, spacing: 24) {
                // 标题
                HStack {
                    Text("生成新报告")
                        .font(.system(size: 16, weight: .bold))
                        .foregroundColor(Color.fieldMindText)

                    Spacer()

                    Button("取消") {
                        onCancel()
                    }
                    .font(.system(size: 12))
                    .foregroundColor(Color.fieldMindText.opacity(0.6))
                }

                // 报告标题
                VStack(alignment: .leading, spacing: 12) {
                    Text("报告标题")
                        .font(.system(size: 12, weight: .semibold))
                        .foregroundColor(Color.fieldMindText)

                    TextField("输入报告标题", text: $reportTitle)
                        .textFieldStyle(.roundedBorder)
                        .font(.system(size: 13))
                }

                Divider()

                // 报告层次选择
                VStack(alignment: .leading, spacing: 12) {
                    Text("报告层次")
                        .font(.system(size: 12, weight: .semibold))
                        .foregroundColor(Color.fieldMindText)

                    VStack(spacing: 10) {
                        reportLayerOption(
                            layer: 1,
                            icon: "1.circle.fill",
                            title: "一度报告 · 信息整理",
                            description: "事实梳理、时间线、关键人物地点"
                        )

                        reportLayerOption(
                            layer: 2,
                            icon: "2.circle.fill",
                            title: "二度报告 · 学术分析",
                            description: "理论框架、学术观点、研究价值"
                        )

                        reportLayerOption(
                            layer: 3,
                            icon: "3.circle.fill",
                            title: "三度报告 · 商业推演",
                            description: "产业机会、市场潜力、开发建议"
                        )
                    }
                }

                Divider()

                // SKILL配置
                if reportLayer >= 2 {
                    VStack(alignment: .leading, spacing: 12) {
                        Text("SKILL 配置")
                            .font(.system(size: 12, weight: .semibold))
                            .foregroundColor(Color.fieldMindText)

                        Text(reportLayer == 2 ? "二度报告使用的框架" : "三度报告使用的思维")
                            .font(.system(size: 11))
                            .foregroundColor(Color.fieldMindText.opacity(0.6))

                        if isLoadingSkills {
                            HStack {
                                ProgressView()
                                    .scaleEffect(0.7)
                                Text("加载可用技能中...")
                                    .font(.system(size: 11))
                                    .foregroundColor(Color.fieldMindText.opacity(0.6))
                            }
                            .padding(.vertical, 8)
                        } else if availableSkills.isEmpty {
                            Text("暂无可用技能")
                                .font(.system(size: 11))
                                .foregroundColor(Color.fieldMindText.opacity(0.5))
                                .padding(.vertical, 8)
                        } else {
                            FlowLayout(spacing: 8) {
                                ForEach(availableSkills, id: \.self) { skill in
                                    skillChip(skill: skill)
                                }
                            }
                        }
                    }

                    Divider()
                }

                // 报告风格
                VStack(alignment: .leading, spacing: 12) {
                    Text("报告风格")
                        .font(.system(size: 12, weight: .semibold))
                        .foregroundColor(Color.fieldMindText)

                    HStack(spacing: 12) {
                        ForEach(["学术型", "商业型", "综合型"], id: \.self) { style in
                            Button {
                                reportStyle = style
                            } label: {
                                Text(style)
                                    .font(.system(size: 12))
                                    .foregroundColor(
                                        reportStyle == style ?
                                        .white : Color.fieldMindText
                                    )
                                    .padding(.horizontal, 16)
                                    .padding(.vertical, 8)
                                    .background(
                                        reportStyle == style ?
                                        Color.fieldMindPrimary : Color.fieldMindBackground
                                    )
                                    .cornerRadius(6)
                            }
                            .buttonStyle(PlainButtonStyle())
                        }
                    }
                }

                Divider()

                // 导出格式
                VStack(alignment: .leading, spacing: 12) {
                    Text("导出格式")
                        .font(.system(size: 12, weight: .semibold))
                        .foregroundColor(Color.fieldMindText)

                    HStack(spacing: 12) {
                        ForEach(["PDF", "Markdown", "Word"], id: \.self) { format in
                            Button {
                                exportFormat = format
                            } label: {
                                Text(format)
                                    .font(.system(size: 12))
                                    .foregroundColor(
                                        exportFormat == format ?
                                        .white : Color.fieldMindText
                                    )
                                    .padding(.horizontal, 16)
                                    .padding(.vertical, 8)
                                    .background(
                                        exportFormat == format ?
                                        Color.fieldMindPrimary : Color.fieldMindBackground
                                    )
                                    .cornerRadius(6)
                            }
                            .buttonStyle(PlainButtonStyle())
                        }
                    }
                }

                Divider()

                // 附加选项
                VStack(alignment: .leading, spacing: 12) {
                    Text("附加选项")
                        .font(.system(size: 12, weight: .semibold))
                        .foregroundColor(Color.fieldMindText)

                    Toggle("包含图表和可视化", isOn: $includeCharts)
                        .font(.system(size: 12))
                        .toggleStyle(SwitchToggleStyle(tint: Color.fieldMindPrimary))

                    Toggle("包含引用文献", isOn: $includeReferences)
                        .font(.system(size: 12))
                        .toggleStyle(SwitchToggleStyle(tint: Color.fieldMindPrimary))
                }

                // 生成按钮
                Button {
                    let config = ReportConfig(
                        title: reportTitle.isEmpty ? nil : reportTitle,
                        layer: reportLayer,
                        skills: selectedSkills,
                        style: reportStyle,
                        format: exportFormat,
                        includeCharts: includeCharts,
                        includeReferences: includeReferences
                    )
                    onSubmit(config)
                } label: {
                    HStack(spacing: 8) {
                        Image(systemName: "sparkles")
                            .font(.system(size: 12))
                        Text("开始生成报告")
                            .font(.system(size: 13, weight: .medium))
                    }
                    .foregroundColor(.white)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 12)
                    .background(Color.fieldMindPrimary)
                    .cornerRadius(7)
                }
                .buttonStyle(PlainButtonStyle())
            }
            .padding(24)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color.fieldMindBackground)
        .onAppear {
            loadAvailableSkills()
        }
    }

    private func loadAvailableSkills() {
        isLoadingSkills = true
        Task {
            do {
                let response = try await APIService.shared.getSkills(status: "active", category: nil)
                await MainActor.run {
                    availableSkills = response.skills.map { $0.name }
                    isLoadingSkills = false
                }
            } catch {
                print("Error loading skills: \(error)")
                await MainActor.run {
                    // Fallback到最小技能集
                    availableSkills = ["基础分析框架", "综合研究方法"]
                    isLoadingSkills = false
                }
            }
        }
    }

    private func reportLayerOption(layer: Int, icon: String, title: String, description: String) -> some View {
        Button {
            reportLayer = layer
        } label: {
            HStack(spacing: 12) {
                Image(systemName: icon)
                    .font(.system(size: 20))
                    .foregroundColor(
                        reportLayer == layer ?
                        Color.fieldMindPrimary : Color.fieldMindText.opacity(0.4)
                    )
                    .frame(width: 28)

                VStack(alignment: .leading, spacing: 4) {
                    Text(title)
                        .font(.system(size: 13, weight: .medium))
                        .foregroundColor(Color.fieldMindText)

                    Text(description)
                        .font(.system(size: 11))
                        .foregroundColor(Color.fieldMindText.opacity(0.6))
                }

                Spacer()

                if reportLayer == layer {
                    Image(systemName: "checkmark.circle.fill")
                        .font(.system(size: 18))
                        .foregroundColor(Color.fieldMindPrimary)
                }
            }
            .padding(14)
            .background(
                reportLayer == layer ?
                Color.fieldMindPrimary.opacity(0.06) : Color.white
            )
            .cornerRadius(7)
            .overlay(
                RoundedRectangle(cornerRadius: 7)
                    .stroke(
                        reportLayer == layer ?
                        Color.fieldMindPrimary.opacity(0.3) : Color.gray.opacity(0.15),
                        lineWidth: 1
                    )
            )
        }
        .buttonStyle(PlainButtonStyle())
    }

    private func skillChip(skill: String) -> some View {
        Button {
            if selectedSkills.contains(skill) {
                selectedSkills.removeAll { $0 == skill }
            } else {
                selectedSkills.append(skill)
            }
        } label: {
            Text(skill)
                .font(.system(size: 11))
                .foregroundColor(
                    selectedSkills.contains(skill) ?
                    .white : Color.fieldMindText
                )
                .padding(.horizontal, 12)
                .padding(.vertical, 6)
                .background(
                    selectedSkills.contains(skill) ?
                    Color.fieldMindSuccess : Color.white
                )
                .cornerRadius(5)
                .overlay(
                    RoundedRectangle(cornerRadius: 5)
                        .stroke(
                            selectedSkills.contains(skill) ?
                            Color.clear : Color.gray.opacity(0.2),
                            lineWidth: 1
                        )
                )
        }
        .buttonStyle(PlainButtonStyle())
    }
}

// MARK: - 报告详情视图
struct ReportDetailView: View {
    let report: ReportResponse
    let onClose: () -> Void
    let onDelete: () -> Void
    let onRegenerate: () -> Void

    var body: some View {
        ScrollView(showsIndicators: false) {
            VStack(alignment: .leading, spacing: 24) {
                // 顶部操作栏
                HStack {
                    Button {
                        onClose()
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
                            onRegenerate()
                        } label: {
                            HStack(spacing: 6) {
                                Image(systemName: "arrow.clockwise")
                                    .font(.system(size: 11))
                                Text("重新生成")
                                    .font(.system(size: 12))
                            }
                            .foregroundColor(Color.fieldMindPrimary)
                            .padding(.horizontal, 12)
                            .padding(.vertical, 7)
                            .background(Color.fieldMindPrimary.opacity(0.1))
                            .cornerRadius(6)
                        }
                        .buttonStyle(PlainButtonStyle())

                        Button {
                            // 导出
                        } label: {
                            HStack(spacing: 6) {
                                Image(systemName: "square.and.arrow.down")
                                    .font(.system(size: 11))
                                Text("下载")
                                    .font(.system(size: 12))
                            }
                            .foregroundColor(.white)
                            .padding(.horizontal, 12)
                            .padding(.vertical, 7)
                            .background(Color.fieldMindPrimary)
                            .cornerRadius(6)
                        }
                        .buttonStyle(PlainButtonStyle())

                        Menu {
                            Button("删除报告") {
                                onDelete()
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

                // 报告标题卡片
                VStack(alignment: .leading, spacing: 16) {
                    HStack(spacing: 10) {
                        Text(report.layerLabel)
                            .font(.system(size: 11, weight: .medium))
                            .foregroundColor(.white)
                            .padding(.horizontal, 10)
                            .padding(.vertical, 5)
                            .background(report.layerColor)
                            .cornerRadius(5)

                        Text(report.status)
                            .font(.system(size: 11))
                            .foregroundColor(report.statusColor)
                            .padding(.horizontal, 10)
                            .padding(.vertical, 5)
                            .background(report.statusColor.opacity(0.1))
                            .cornerRadius(5)
                    }

                    Text(report.title)
                        .font(.system(size: 18, weight: .bold))
                        .foregroundColor(Color.fieldMindText)

                    HStack(spacing: 20) {
                        Label(report.createdAt, systemImage: "calendar")
                            .font(.system(size: 11))
                            .foregroundColor(Color.fieldMindText.opacity(0.6))

                        if let wordCount = report.wordCount {
                            Label("\(wordCount) 字", systemImage: "doc.text")
                                .font(.system(size: 11))
                                .foregroundColor(Color.fieldMindText.opacity(0.6))
                        }

                        Label(report.projectName ?? "未知项目", systemImage: "folder")
                            .font(.system(size: 11))
                            .foregroundColor(Color.fieldMindText.opacity(0.6))
                    }
                }
                .padding(20)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(Color.white)
                .cornerRadius(10)

                // 报告预览区域
                VStack(alignment: .leading, spacing: 14) {
                    Text("报告预览")
                        .font(.system(size: 14, weight: .bold))
                        .foregroundColor(Color.fieldMindText)

                    Text("报告内容加载中...")
                        .font(.system(size: 12))
                        .foregroundColor(Color.fieldMindText.opacity(0.6))
                        .padding(16)
                        .frame(maxWidth: .infinity, alignment: .center)
                        .background(Color.white)
                        .cornerRadius(7)
                }
            }
            .padding(24)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color.fieldMindBackground)
    }
}

// MARK: - 报告配置
struct ReportConfig {
    let title: String?
    let layer: Int
    let skills: [String]
    let style: String
    let format: String
    let includeCharts: Bool
    let includeReferences: Bool
}
