import SwiftUI

struct CreativeAnalysisView: View {
    @StateObject private var viewModel = CreativeAnalysisViewModel()
    @State private var keywordsText = ""
    @State private var selectedMode = "creative"

    private let modes = [
        ("creative", "创意模式"),
        ("business", "商业模式"),
        ("academic", "学术模式")
    ]

    var body: some View {
        VStack(spacing: 0) {
            // 输入区域
            inputSection

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
        .navigationTitle("在地文创分析")
        .alert("错误", isPresented: $viewModel.showError) {
            Button("确定", role: .cancel) { }
        } message: {
            Text(viewModel.errorMessage)
        }
    }

    // MARK: - 输入区域

    private var inputSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("文创分析引擎")
                .font(.headline)

            // 关键词输入
            VStack(alignment: .leading, spacing: 4) {
                Text("关键词（用逗号分隔）")
                    .font(.caption)
                    .foregroundColor(.secondary)

                TextField("如：布依族, 山歌, 传统文化", text: $keywordsText)
                    .textFieldStyle(.roundedBorder)
            }

            // 模式选择
            Picker("分析模式", selection: $selectedMode) {
                ForEach(modes, id: \.0) { mode in
                    Text(mode.1).tag(mode.0)
                }
            }
            .pickerStyle(.segmented)

            // 分析按钮
            HStack {
                Spacer()

                Button(action: performAnalysis) {
                    Label("开始分析", systemImage: "lightbulb.fill")
                }
                .disabled(keywordsText.isEmpty || viewModel.isAnalyzing)
                .buttonStyle(.borderedProminent)
            }
        }
        .padding()
        .background(Color(NSColor.controlBackgroundColor))
    }

    // MARK: - 加载视图

    private var loadingView: some View {
        VStack(spacing: 16) {
            ProgressView()
                .scaleEffect(1.5)
            Text("AI 正在深度分析中...")
                .foregroundColor(.secondary)
            Text("这可能需要 10-30 秒")
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    // MARK: - 空状态

    private var emptyStateView: some View {
        VStack(spacing: 20) {
            Image(systemName: "lightbulb.max.fill")
                .font(.system(size: 60))
                .foregroundColor(.orange)

            Text("在地文创分析引擎")
                .font(.title2)
                .fontWeight(.semibold)

            Text("基于调研数据，AI 深度思考文创可能性\n避免刻板建议，提供真正有创意的方案")
                .multilineTextAlignment(.center)
                .foregroundColor(.secondary)

            VStack(alignment: .leading, spacing: 12) {
                Text("我们提供：").font(.headline)

                HStack(spacing: 30) {
                    VStack(alignment: .leading, spacing: 8) {
                        FeatureItem(icon: "sparkles", text: "深度创意", color: .orange)
                        FeatureItem(icon: "chart.line.uptrend.xyaxis", text: "可行性评分", color: .blue)
                        FeatureItem(icon: "person.2.fill", text: "目标人群", color: .purple)
                    }

                    VStack(alignment: .leading, spacing: 8) {
                        FeatureItem(icon: "dollarsign.circle", text: "市场潜力", color: .green)
                        FeatureItem(icon: "exclamationmark.triangle", text: "风险分析", color: .red)
                        FeatureItem(icon: "star.fill", text: "独特价值", color: .yellow)
                    }
                }
            }
            .padding()
            .background(Color.orange.opacity(0.1))
            .cornerRadius(12)

            VStack(alignment: .leading, spacing: 8) {
                Text("❌ 我们避免刻板建议：").font(.subheadline).foregroundColor(.red)
                Text("• \"制作XX纪念品\"").font(.caption).foregroundColor(.secondary)
                Text("• \"举办XX表演\"").font(.caption).foregroundColor(.secondary)
                Text("• \"开发XX旅游路线\"").font(.caption).foregroundColor(.secondary)
            }
            .padding()
            .background(Color.red.opacity(0.05))
            .cornerRadius(8)
        }
        .padding(40)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    // MARK: - 结果视图

    private func resultsView(results: CreativeAnalysisResponse) -> some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                // 关键词标题
                keywordsHeader(keywords: results.keywords)

                // 文化元素
                if !results.culturalElements.isEmpty {
                    culturalElementsSection(elements: results.culturalElements)
                }

                // 创意可能性
                if !results.creativePossibilities.isEmpty {
                    creativePossibilitiesSection(possibilities: results.creativePossibilities)
                }

                // 反面模式
                if !results.antiPatterns.isEmpty {
                    antiPatternsSection(patterns: results.antiPatterns)
                }
            }
            .padding()
        }
    }

    // MARK: - 关键词标题

    private func keywordsHeader(keywords: [String]) -> some View {
        HStack {
            VStack(alignment: .leading, spacing: 8) {
                Text("分析关键词")
                    .font(.caption)
                    .foregroundColor(.secondary)
                Text(keywords.joined(separator: " • "))
                    .font(.title2)
                    .fontWeight(.bold)
            }

            Spacer()

            Button(action: {
                // TODO: 导出报告
            }) {
                Label("导出报告", systemImage: "square.and.arrow.up")
            }
        }
        .padding()
        .background(Color.orange.opacity(0.1))
        .cornerRadius(12)
    }

    // MARK: - 文化元素

    private func culturalElementsSection(elements: [CulturalElement]) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("文化元素分析")
                .font(.headline)

            ForEach(elements) { element in
                CulturalElementCard(element: element)
            }
        }
    }

    // MARK: - 创意可能性

    private func creativePossibilitiesSection(possibilities: [CreativePossibility]) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("创意可能性 (\(possibilities.count))")
                .font(.headline)

            ForEach(possibilities) { possibility in
                CreativePossibilityCard(possibility: possibility)
            }
        }
    }

    // MARK: - 反面模式

    private func antiPatternsSection(patterns: [String]) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("避免的刻板建议")
                .font(.headline)

            ForEach(patterns, id: \.self) { pattern in
                HStack {
                    Image(systemName: "xmark.circle.fill")
                        .foregroundColor(.red)
                    Text(pattern)
                        .foregroundColor(.secondary)
                }
                .padding(.vertical, 4)
            }
        }
        .padding()
        .background(Color.red.opacity(0.05))
        .cornerRadius(12)
    }

    // MARK: - 执行分析

    private func performAnalysis() {
        let keywords = keywordsText
            .split(separator: ",")
            .map { $0.trimmingCharacters(in: .whitespaces) }
            .filter { !$0.isEmpty }

        guard !keywords.isEmpty else { return }

        Task {
            await viewModel.analyzeCreative(keywords: keywords, mode: selectedMode)
        }
    }
}

// MARK: - 子组件

struct FeatureItem: View {
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

struct CulturalElementCard: View {
    let element: CulturalElement

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(element.element)
                .font(.headline)

            HStack(alignment: .top) {
                VStack(alignment: .leading, spacing: 4) {
                    Text("独特性")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    Text(element.uniqueness)
                        .font(.subheadline)
                }

                Spacer()

                VStack(alignment: .leading, spacing: 4) {
                    Text("文化意义")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    Text(element.culturalMeaning)
                        .font(.subheadline)
                }
            }
        }
        .padding()
        .background(Color(NSColor.controlBackgroundColor))
        .cornerRadius(12)
    }
}

struct CreativePossibilityCard: View {
    let possibility: CreativePossibility
    @State private var isExpanded = false

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // 标题和评分
            HStack(alignment: .top) {
                VStack(alignment: .leading, spacing: 4) {
                    Text(possibility.idea)
                        .font(.headline)
                    Text(possibility.description)
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }

                Spacer()

                FeasibilityBadge(score: possibility.feasibilityScore)
            }

            // 创新点
            HStack {
                Image(systemName: "sparkles")
                    .foregroundColor(.orange)
                Text(possibility.innovationPoint)
                    .font(.subheadline)
                    .italic()
            }
            .padding(8)
            .background(Color.orange.opacity(0.1))
            .cornerRadius(8)

            // 展开/收起按钮
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

                    DetailRow(
                        icon: "person.2.fill",
                        title: "目标人群",
                        content: possibility.targetAudience,
                        color: .purple
                    )

                    DetailRow(
                        icon: "chart.line.uptrend.xyaxis",
                        title: "市场潜力",
                        content: possibility.marketPotential,
                        color: .green
                    )

                    DetailRow(
                        icon: "star.fill",
                        title: "独特价值",
                        content: possibility.uniqueValue,
                        color: .yellow
                    )

                    // 所需资源
                    VStack(alignment: .leading, spacing: 4) {
                        HStack {
                            Image(systemName: "wrench.and.screwdriver")
                                .foregroundColor(.blue)
                            Text("所需资源")
                                .font(.caption)
                                .fontWeight(.semibold)
                        }
                        ForEach(possibility.requiredResources, id: \.self) { resource in
                            Text("• \(resource)")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                    }

                    // 风险点
                    VStack(alignment: .leading, spacing: 4) {
                        HStack {
                            Image(systemName: "exclamationmark.triangle.fill")
                                .foregroundColor(.red)
                            Text("风险点")
                                .font(.caption)
                                .fontWeight(.semibold)
                        }
                        ForEach(possibility.risks, id: \.self) { risk in
                            Text("• \(risk)")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                    }

                    // 实施难度
                    HStack {
                        Text("实施难度：")
                            .font(.caption)
                        Text(possibility.implementationDifficulty)
                            .font(.caption)
                            .fontWeight(.semibold)
                            .foregroundColor(difficultyColor(possibility.implementationDifficulty))
                    }
                }
            }
        }
        .padding()
        .background(Color(NSColor.controlBackgroundColor))
        .cornerRadius(12)
    }

    private func difficultyColor(_ difficulty: String) -> Color {
        switch difficulty.lowercased() {
        case "低", "简单", "容易": return .green
        case "中", "中等": return .orange
        case "高", "困难", "较高": return .red
        default: return .gray
        }
    }
}

struct FeasibilityBadge: View {
    let score: Int

    var body: some View {
        VStack(spacing: 2) {
            Text("\(score)")
                .font(.title2)
                .fontWeight(.bold)
                .foregroundColor(scoreColor)
            Text("可行性")
                .font(.caption2)
                .foregroundColor(.secondary)
        }
        .padding(8)
        .background(scoreColor.opacity(0.1))
        .cornerRadius(8)
    }

    private var scoreColor: Color {
        switch score {
        case 0..<50: return .red
        case 50..<70: return .orange
        case 70..<85: return .blue
        default: return .green
        }
    }
}

struct DetailRow: View {
    let icon: String
    let title: String
    let content: String
    let color: Color

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Image(systemName: icon)
                    .foregroundColor(color)
                Text(title)
                    .font(.caption)
                    .fontWeight(.semibold)
            }
            Text(content)
                .font(.caption)
                .foregroundColor(.secondary)
        }
    }
}

// MARK: - Preview

#Preview {
    CreativeAnalysisView()
        .frame(width: 900, height: 700)
}
