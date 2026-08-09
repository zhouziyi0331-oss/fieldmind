import SwiftUI

struct BusinessAnalysisView: View {
    @StateObject private var viewModel = BusinessAnalysisViewModel()
    @EnvironmentObject var appState: AppState

    var body: some View {
        VStack(spacing: 0) {
            // 顶部操作栏
            toolbar

            Divider()

            // 内容区域
            if viewModel.isAnalyzing {
                loadingView
            } else if let results = viewModel.analysisResults {
                resultsView(results: results)
            } else {
                emptyStateView
            }
        }
        .navigationTitle("业态分析")
        .alert("错误", isPresented: $viewModel.showError) {
            Button("确定", role: .cancel) { }
        } message: {
            Text(viewModel.errorMessage)
        }
    }

    // MARK: - 工具栏

    private var toolbar: some View {
        HStack {
            Text("业态分析系统")
                .font(.headline)

            Spacer()

            Button(action: performAnalysis) {
                Label("开始分析", systemImage: "chart.bar.fill")
            }
            .disabled(viewModel.isAnalyzing)
            .buttonStyle(.borderedProminent)
        }
        .padding()
        .background(Color(NSColor.controlBackgroundColor))
    }

    // MARK: - 加载视图

    private var loadingView: some View {
        VStack(spacing: 16) {
            ProgressView()
                .scaleEffect(1.5)
            Text("AI 正在分析业态...")
                .foregroundColor(.secondary)
            Text("分析现有业态并推荐新业态")
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    // MARK: - 空状态

    private var emptyStateView: some View {
        VStack(spacing: 20) {
            Image(systemName: "chart.bar.xaxis")
                .font(.system(size: 60))
                .foregroundColor(.blue)

            Text("业态分析系统")
                .font(.title2)
                .fontWeight(.semibold)

            Text("基于调研数据，分析现有业态并建议新业态\n有理有据，含可行性评分和实施步骤")
                .multilineTextAlignment(.center)
                .foregroundColor(.secondary)

            VStack(alignment: .leading, spacing: 12) {
                Text("分析内容：").font(.headline)

                HStack(spacing: 40) {
                    VStack(alignment: .leading, spacing: 8) {
                        AnalysisFeature(icon: "building.2", text: "现有业态梳理", color: .blue)
                        AnalysisFeature(icon: "lightbulb", text: "新业态建议", color: .orange)
                        AnalysisFeature(icon: "percent", text: "可行性评分", color: .green)
                    }

                    VStack(alignment: .leading, spacing: 8) {
                        AnalysisFeature(icon: "dollarsign.circle", text: "投资收益分析", color: .green)
                        AnalysisFeature(icon: "exclamationmark.triangle", text: "风险点识别", color: .red)
                        AnalysisFeature(icon: "arrow.triangle.branch", text: "协同效应", color: .purple)
                    }
                }
            }
            .padding()
            .background(Color.blue.opacity(0.1))
            .cornerRadius(12)

            Text("点击\"开始分析\"按钮，AI 将分析您的项目数据")
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .padding(40)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    // MARK: - 结果视图

    private func resultsView(results: BusinessAnalysisResponse) -> some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                // 现有业态
                if !results.existingFormats.isEmpty {
                    existingFormatsSection(formats: results.existingFormats)
                }

                // 建议业态
                if !results.suggestedFormats.isEmpty {
                    suggestedFormatsSection(formats: results.suggestedFormats)
                }

                // 协同效应
                if !results.synergyAnalysis.isEmpty {
                    synergySection(analysis: results.synergyAnalysis)
                }

                // 建议
                if !results.recommendations.isEmpty {
                    recommendationsSection(recommendations: results.recommendations)
                }
            }
            .padding()
        }
    }

    // MARK: - 现有业态

    private func existingFormatsSection(formats: [ExistingFormat]) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("现有业态 (\(formats.count))")
                .font(.headline)

            ForEach(formats) { format in
                ExistingFormatCard(format: format)
            }
        }
    }

    // MARK: - 建议业态

    private func suggestedFormatsSection(formats: [SuggestedFormat]) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("建议的新业态 (\(formats.count))")
                    .font(.headline)

                Spacer()

                Text("按可行性排序")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }

            ForEach(formats.sorted(by: { $0.feasibilityScore > $1.feasibilityScore })) { format in
                SuggestedFormatCard(format: format)
            }
        }
    }

    // MARK: - 协同效应

    private func synergySection(analysis: String) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("业态协同效应")
                .font(.headline)

            Text(analysis)
                .font(.subheadline)
                .foregroundColor(.secondary)
                .fixedSize(horizontal: false, vertical: true)
        }
        .padding()
        .background(Color.purple.opacity(0.1))
        .cornerRadius(12)
    }

    // MARK: - 建议

    private func recommendationsSection(recommendations: [String]) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("专业建议")
                .font(.headline)

            ForEach(Array(recommendations.enumerated()), id: \.offset) { index, recommendation in
                HStack(alignment: .top, spacing: 8) {
                    Text("\(index + 1).")
                        .fontWeight(.semibold)
                        .foregroundColor(.blue)
                    Text(recommendation)
                        .foregroundColor(.secondary)
                }
            }
        }
        .padding()
        .background(Color.blue.opacity(0.05))
        .cornerRadius(12)
    }

    // MARK: - 执行分析

    private func performAnalysis() {
        viewModel.appState = appState
        Task {
            await viewModel.analyzeBusiness()
        }
    }
}

// MARK: - 子组件

struct AnalysisFeature: View {
    let icon: String
    let text: String
    let color: Color

    var body: some View {
        HStack {
            Image(systemName: icon)
                .foregroundColor(color)
                .frame(width: 24)
            Text(text)
        }
    }
}

struct ExistingFormatCard: View {
    let format: ExistingFormat

    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text(format.name)
                    .font(.headline)
                Text(format.description)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }

            Spacer()

            Text(format.status)
                .font(.system(size: 11, weight: .medium))
                .foregroundColor(.white)
                .padding(.horizontal, 8)
                .padding(.vertical, 4)
                .background(Color.blue)
                .cornerRadius(4)

            Text(format.scale)
                .font(.caption)
                .padding(.horizontal, 8)
                .padding(.vertical, 4)
                .background(Color.gray.opacity(0.2))
                .cornerRadius(4)
        }
        .padding()
        .background(Color(NSColor.controlBackgroundColor))
        .cornerRadius(12)
    }
}

struct SuggestedFormatCard: View {
    let format: SuggestedFormat
    @State private var isExpanded = false

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // 标题和评分
            HStack(alignment: .top) {
                VStack(alignment: .leading, spacing: 4) {
                    Text(format.name)
                        .font(.headline)
                    Text(format.reason)
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }

                Spacer()

                FeasibilityScore(score: format.feasibilityScore)
            }

            // 快速信息
            HStack(spacing: 16) {
                InfoPill(icon: "dollarsign.circle", text: format.investment, color: .green)
                InfoPill(icon: "chart.line.uptrend.xyaxis", text: format.revenuePotential, color: .blue)
            }

            // 展开按钮
            Button(action: { isExpanded.toggle() }) {
                HStack {
                    Text(isExpanded ? "收起详情" : "查看详情")
                    Image(systemName: isExpanded ? "chevron.up" : "chevron.down")
                }
                .font(.caption)
            }
            .buttonStyle(.plain)

            // 详细信息
            if isExpanded {
                VStack(alignment: .leading, spacing: 12) {
                    Divider()

                    // 所需条件
                    DetailSection(
                        icon: "checkmark.circle",
                        title: "所需条件",
                        items: format.requiredConditions,
                        color: .blue
                    )

                    // 证据支持
                    DetailSection(
                        icon: "doc.text",
                        title: "证据支持",
                        items: format.evidence,
                        color: .green
                    )

                    // 风险点
                    DetailSection(
                        icon: "exclamationmark.triangle",
                        title: "风险点",
                        items: format.riskPoints,
                        color: .red
                    )

                    // 实施步骤
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Image(systemName: "list.number")
                                .foregroundColor(.purple)
                            Text("实施步骤")
                                .font(.caption)
                                .fontWeight(.semibold)
                        }

                        ForEach(Array(format.implementationSteps.enumerated()), id: \.offset) { index, step in
                            HStack(alignment: .top, spacing: 8) {
                                Text("\(index + 1)")
                                    .font(.caption)
                                    .fontWeight(.bold)
                                    .foregroundColor(.white)
                                    .frame(width: 20, height: 20)
                                    .background(Color.purple)
                                    .clipShape(Circle())

                                Text(step)
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }
                        }
                    }
                }
            }
        }
        .padding()
        .background(Color(NSColor.controlBackgroundColor))
        .cornerRadius(12)
    }
}


// MARK: - 详情区块组件
struct DetailSection: View {
    let icon: String
    let title: String
    let items: [String]
    let color: Color
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: icon)
                    .foregroundColor(color)
                Text(title)
                    .font(.system(size: 16, weight: .semibold))
            }
            
            VStack(alignment: .leading, spacing: 8) {
                ForEach(items, id: \.self) { item in
                    HStack(alignment: .top, spacing: 8) {
                        Text("•")
                            .foregroundColor(color)
                        Text(item)
                            .font(.system(size: 13))
                            .foregroundColor(.secondary)
                    }
                }
            }
        }
        .padding()
        .background(Color(NSColor.controlBackgroundColor))
        .cornerRadius(8)
    }
}

// MARK: - 可行性评分组件
struct FeasibilityScore: View {
    let score: Int
    
    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: "star.fill")
                .foregroundColor(.yellow)
            Text("可行性评分:")
                .font(.system(size: 14, weight: .medium))
            Text("\(score)/100")
                .font(.system(size: 18, weight: .bold))
                .foregroundColor(scoreColor)
        }
        .padding()
        .background(Color(NSColor.controlBackgroundColor))
        .cornerRadius(8)
    }
    
    var scoreColor: Color {
        if score >= 70 {
            return .green
        } else if score >= 40 {
            return .orange
        } else {
            return .red
        }
    }
}

// MARK: - 信息徽章组件
struct InfoPill: View {
    let icon: String
    let text: String
    let color: Color
    
    var body: some View {
        HStack(spacing: 8) {
            Image(systemName: icon)
                .foregroundColor(color)
            Text(text)
                .font(.system(size: 13))
                .foregroundColor(.secondary)
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
        .background(color.opacity(0.1))
        .cornerRadius(8)
    }
}
