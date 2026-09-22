import SwiftUI

struct ReportPage: View {
    let projectId: Int

    @StateObject private var viewModel = ReportViewModel()
    @State private var showGenerateSheet = false
    @State private var selectedReportLevel = 1
    @State private var selectedDocumentIds: [Int] = []

    var body: some View {
        VStack(spacing: 0) {
            // Header
            HStack {
                Text("报告生成")
                    .font(.system(size: 22, weight: .semibold))
                    .foregroundColor(Color.fmText)

                Spacer()

                Button(action: { showGenerateSheet = true }) {
                    HStack(spacing: 6) {
                        Image(systemName: "doc.badge.plus")
                            .font(.system(size: 13))
                        Text("生成报告")
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
            if viewModel.isGenerating {
                loadingView
            } else if viewModel.reports.isEmpty {
                emptyView
            } else {
                reportListView
            }
        }
        .sheet(isPresented: $showGenerateSheet) {
            GenerateReportSheet(
                isPresented: $showGenerateSheet,
                selectedLevel: $selectedReportLevel,
                onGenerate: {
                    Task {
                        await viewModel.generateReport(
                            projectId: projectId,
                            documentIds: selectedDocumentIds.isEmpty ? nil : selectedDocumentIds,
                            reportLevel: selectedReportLevel
                        )
                        showGenerateSheet = false
                    }
                }
            )
        }
    }

    // MARK: - Loading View

    private var loadingView: some View {
        VStack(spacing: 20) {
            ProgressView()
                .scaleEffect(1.5)
            Text("正在生成报告...")
                .font(.system(size: 14))
                .foregroundColor(Color.fmText2)
            Text("这可能需要几分钟，请耐心等待")
                .font(.system(size: 12))
                .foregroundColor(Color.fmText3)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    // MARK: - Empty View

    private var emptyView: some View {
        VStack(spacing: 16) {
            Image(systemName: "doc.text")
                .font(.system(size: 48))
                .foregroundColor(Color.fmText3)
            Text("还没有生成报告")
                .font(.system(size: 16, weight: .medium))
                .foregroundColor(Color.fmText2)
            Text("点击「生成报告」按钮创建第一份报告")
                .font(.system(size: 13))
                .foregroundColor(Color.fmText3)

            Button(action: { showGenerateSheet = true }) {
                HStack(spacing: 6) {
                    Image(systemName: "doc.badge.plus")
                    Text("生成报告")
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

    // MARK: - Report List View

    private var reportListView: some View {
        ScrollView {
            VStack(spacing: 16) {
                ForEach(viewModel.reports) { report in
                    ReportCard(report: report, onDelete: {
                        viewModel.deleteReport(id: report.id)
                    })
                }
            }
            .padding(20)
        }
    }
}

// MARK: - Report Card

struct ReportCard: View {
    let report: ReportViewModel.GeneratedReport
    let onDelete: () -> Void

    @State private var isExpanded = false

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Header
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    HStack(spacing: 8) {
                        Text(report.levelName)
                            .font(.system(size: 16, weight: .semibold))
                            .foregroundColor(Color.fmText)

                        Text(report.levelDescription)
                            .font(.system(size: 12))
                            .foregroundColor(Color.fmText3)
                            .padding(.horizontal, 8)
                            .padding(.vertical, 3)
                            .background(Color.fmBg)
                            .cornerRadius(4)
                    }

                    HStack(spacing: 12) {
                        HStack(spacing: 4) {
                            Image(systemName: "doc")
                                .font(.system(size: 11))
                            Text("\(report.documentsUsed)份文档")
                                .font(.system(size: 12))
                        }
                        .foregroundColor(Color.fmText3)

                        HStack(spacing: 4) {
                            Image(systemName: report.generationMethod == "llm" ? "cpu" : "doc.text")
                                .font(.system(size: 11))
                            Text(report.generationMethod == "llm" ? "AI生成" : "模板生成")
                                .font(.system(size: 12))
                        }
                        .foregroundColor(Color.fmText3)

                        HStack(spacing: 4) {
                            Image(systemName: "clock")
                                .font(.system(size: 11))
                            Text(formatDate(report.generatedAt))
                                .font(.system(size: 12))
                        }
                        .foregroundColor(Color.fmText3)
                    }
                }

                Spacer()

                HStack(spacing: 8) {
                    Button(action: { isExpanded.toggle() }) {
                        HStack(spacing: 4) {
                            Image(systemName: isExpanded ? "chevron.up" : "chevron.down")
                                .font(.system(size: 11))
                            Text(isExpanded ? "收起" : "展开")
                                .font(.system(size: 12))
                        }
                        .foregroundColor(Color.fmPrimary)
                        .padding(.horizontal, 12)
                        .padding(.vertical, 6)
                        .background(Color.fmPrimary.opacity(0.1))
                        .cornerRadius(6)
                    }
                    .buttonStyle(PlainButtonStyle())

                    Button(action: onDelete) {
                        Image(systemName: "trash")
                            .font(.system(size: 12))
                            .foregroundColor(Color.fmRed)
                            .padding(6)
                            .background(Color.fmRed.opacity(0.1))
                            .cornerRadius(6)
                    }
                    .buttonStyle(PlainButtonStyle())
                }
            }

            // Message
            if let message = report.message {
                HStack(spacing: 6) {
                    Image(systemName: "info.circle")
                        .font(.system(size: 11))
                    Text(message)
                        .font(.system(size: 12))
                }
                .foregroundColor(Color.fmText3)
                .padding(8)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(Color.fmBg)
                .cornerRadius(6)
            }

            // Content
            if isExpanded {
                Divider()

                ScrollView {
                    Text(report.content)
                        .font(.system(size: 13))
                        .foregroundColor(Color.fmText2)
                        .textSelection(.enabled)
                        .frame(maxWidth: .infinity, alignment: .leading)
                }
                .frame(maxHeight: 600)
            }
        }
        .padding(16)
        .background(Color.white)
        .cornerRadius(12)
        .shadow(color: Color.black.opacity(0.05), radius: 8, x: 0, y: 2)
    }

    private func formatDate(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd HH:mm"
        return formatter.string(from: date)
    }
}

// MARK: - Generate Report Sheet

struct GenerateReportSheet: View {
    @Binding var isPresented: Bool
    @Binding var selectedLevel: Int
    let onGenerate: () -> Void

    var body: some View {
        VStack(spacing: 20) {
            // Header
            HStack {
                Text("生成报告")
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

            // Report level selection
            VStack(alignment: .leading, spacing: 12) {
                Text("选择报告类型")
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(Color.fmText2)

                VStack(spacing: 12) {
                    ReportLevelOption(
                        level: 1,
                        title: "一度报告",
                        description: "基于材料的直接分析（5000-8000字）",
                        details: "材料来源、文档内容展示、关键词分析、文本结构",
                        isSelected: selectedLevel == 1,
                        onSelect: { selectedLevel = 1 }
                    )

                    ReportLevelOption(
                        level: 2,
                        title: "二度报告",
                        description: "费孝通框架分析（8000-12000字）",
                        details: "社会结构分析、文化变迁、理论框架解读",
                        isSelected: selectedLevel == 2,
                        onSelect: { selectedLevel = 2 }
                    )

                    ReportLevelOption(
                        level: 3,
                        title: "三度报告",
                        description: "综合多维度分析（10000-15000字）",
                        details: "整合SOP、费孝通框架、关键词趋势的综合分析",
                        isSelected: selectedLevel == 3,
                        onSelect: { selectedLevel = 3 }
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

                Button(action: onGenerate) {
                    Text("开始生成")
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
        .frame(width: 500, height: 550)
        .background(Color.white)
    }
}

// MARK: - Report Level Option

struct ReportLevelOption: View {
    let level: Int
    let title: String
    let description: String
    let details: String
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
                        .font(.system(size: 13))
                        .foregroundColor(Color.fmText2)

                    Text(details)
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
