import SwiftUI
import Charts

// MARK: - SOP Analysis Card
struct SOPAnalysisCard: View {
    let analysis: SOPAnalysisService.SOPAnalysis

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            // Header with title and score
            HStack(alignment: .top, spacing: 12) {
                // Icon
                ZStack {
                    Circle()
                        .fill(Color.blue.opacity(0.1))
                        .frame(width: 48, height: 48)
                    Image(systemName: "chart.line.uptrend.xyaxis")
                        .font(.system(size: 24))
                        .foregroundColor(.blue)
                }

                VStack(alignment: .leading, spacing: 6) {
                    HStack(spacing: 8) {
                        Text(analysis.sopTitle)
                            .font(.system(size: 16, weight: .semibold))
                            .foregroundColor(Color.fmText)

                        Text(analysis.category)
                            .font(.system(size: 12))
                            .foregroundColor(Color.fmText2)
                            .padding(.horizontal, 8)
                            .padding(.vertical, 3)
                            .background(Color.blue.opacity(0.1))
                            .cornerRadius(4)
                    }

                    HStack(spacing: 16) {
                        Label {
                            Text("\(analysis.timeRange)")
                                .font(.system(size: 13))
                                .foregroundColor(Color.fmText3)
                        } icon: {
                            Image(systemName: "calendar")
                                .font(.system(size: 11))
                                .foregroundColor(Color.fmText3)
                        }

                        Label {
                            Text(analysis.timeRange)
                                .font(.system(size: 13))
                                .foregroundColor(Color.fmText3)
                        } icon: {
                            Image(systemName: "clock")
                                .font(.system(size: 11))
                                .foregroundColor(Color.fmText3)
                        }
                    }
                }

                Spacer()

                // Overall score
                VStack(spacing: 4) {
                    Text(String(format: "%.1f", analysis.overallScore))
                        .font(.system(size: 32, weight: .bold))
                        .foregroundColor(scoreColor(analysis.overallScore))
                    Text("综合评分")
                        .font(.system(size: 12))
                        .foregroundColor(Color.fmText3)
                }
            }
            .padding(16)

            Divider()

            // Metrics grid
            HStack(spacing: 0) {
                MetricItem(
                    label: "使用次数",
                    value: "\(analysis.metrics.totalUsage)",
                    icon: "arrow.triangle.2.circlepath",
                    color: .blue
                )

                Divider()
                    .frame(height: 40)

                MetricItem(
                    label: "成功率",
                    value: String(format: "%.1f%%", analysis.metrics.successRate * 100),
                    icon: "checkmark.circle",
                    color: .green
                )

                Divider()
                    .frame(height: 40)

                MetricItem(
                    label: "平均用时",
                    value: String(format: "%.1f 分钟", analysis.metrics.avgDuration),
                    icon: "clock",
                    color: .orange
                )

                Divider()
                    .frame(height: 40)

                MetricItem(
                    label: "错误率",
                    value: String(format: "%.1f%%", analysis.metrics.errorRate * 100),
                    icon: "exclamationmark.triangle",
                    color: .purple
                )
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 12)

            Divider()

            // Issues and suggestions summary
            HStack(spacing: 24) {
                HStack(spacing: 8) {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .font(.system(size: 14))
                        .foregroundColor(.orange)
                    Text("\(analysis.issues.count) 个问题")
                        .font(.system(size: 13))
                        .foregroundColor(Color.fmText2)
                }

                HStack(spacing: 8) {
                    Image(systemName: "lightbulb.fill")
                        .font(.system(size: 14))
                        .foregroundColor(.blue)
                    Text("\(analysis.recommendations.count) 条建议")
                        .font(.system(size: 13))
                        .foregroundColor(Color.fmText2)
                }

                Spacer()

                Text("查看详情 →")
                    .font(.system(size: 13))
                    .foregroundColor(.blue)
            }
            .padding(16)
        }
        .background(Color.white)
        .cornerRadius(8)
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .stroke(Color.fmBorder, lineWidth: 1)
        )
        .shadow(color: Color.black.opacity(0.04), radius: 4, x: 0, y: 2)
    }

    func scoreColor(_ score: Double) -> Color {
        if score >= 90 { return .green }
        if score >= 80 { return .blue }
        if score >= 70 { return .orange }
        return .red
    }
}

// MARK: - Metric Item
struct MetricItem: View {
    let label: String
    let value: String
    let icon: String
    let color: Color

    var body: some View {
        HStack(spacing: 8) {
            Image(systemName: icon)
                .font(.system(size: 14))
                .foregroundColor(color)

            VStack(alignment: .leading, spacing: 2) {
                Text(label)
                    .font(.system(size: 11))
                    .foregroundColor(Color.fmText3)
                Text(value)
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundColor(Color.fmText)
            }
        }
        .frame(maxWidth: .infinity)
    }
}

// MARK: - SOP Analysis Detail Sheet
struct SOPAnalysisDetailSheet: View {
    let analysis: SOPAnalysisService.SOPAnalysis
    @Environment(\.dismiss) var dismiss

    var body: some View {
        VStack(spacing: 0) {
            // Header
            HStack {
                VStack(alignment: .leading, spacing: 8) {
                    Text(analysis.sopTitle)
                        .font(.system(size: 20, weight: .semibold))
                        .foregroundColor(Color.fmText)

                    HStack(spacing: 12) {
                        Text(analysis.category)
                            .font(.system(size: 13))
                            .foregroundColor(Color.fmText2)
                            .padding(.horizontal, 8)
                            .padding(.vertical, 3)
                            .background(Color.blue.opacity(0.1))
                            .cornerRadius(4)

                        Text(analysis.timeRange)
                            .font(.system(size: 13))
                            .foregroundColor(Color.fmText3)

                        Text("•")
                            .foregroundColor(Color.fmText3)

                        Text("分析时间: \(analysis.timeRange)")
                            .font(.system(size: 13))
                            .foregroundColor(Color.fmText3)
                    }
                }

                Spacer()

                // Overall score
                VStack(spacing: 4) {
                    Text(String(format: "%.1f", analysis.overallScore))
                        .font(.system(size: 36, weight: .bold))
                        .foregroundColor(scoreColor(analysis.overallScore))
                    Text("综合评分")
                        .font(.system(size: 13))
                        .foregroundColor(Color.fmText3)
                }
                .padding(.horizontal, 20)

                Button(action: { dismiss() }) {
                    Image(systemName: "xmark")
                        .font(.system(size: 14))
                        .foregroundColor(Color.fmText3)
                        .frame(width: 28, height: 28)
                        .background(Color(NSColor.controlBackgroundColor))
                        .cornerRadius(14)
                }
                .buttonStyle(PlainButtonStyle())
            }
            .padding(20)
            .background(Color.white)

            Divider()

            ScrollView {
                VStack(spacing: 24) {
                    // Performance metrics
                    AnalysisSection(title: "性能指标", icon: "gauge") {
                        LazyVGrid(columns: [
                            GridItem(.flexible()),
                            GridItem(.flexible()),
                            GridItem(.flexible()),
                            GridItem(.flexible())
                        ], spacing: 16) {
                            PerformanceMetricCard(
                                title: "完成率",
                                value: analysis.metrics.completionRate,
                                icon: "speedometer",
                                color: .blue
                            )
                            PerformanceMetricCard(
                                title: "成功率",
                                value: analysis.metrics.successRate,
                                icon: "star.fill",
                                color: .green
                            )
                            PerformanceMetricCard(
                                title: "错误率",
                                value: analysis.metrics.errorRate,
                                icon: "exclamationmark.triangle",
                                color: .purple
                            )
                            PerformanceMetricCard(
                                title: "完成率",
                                value: analysis.metrics.completionRate,
                                icon: "checkmark.circle.fill",
                                color: .pink
                            )
                        }
                    }

                    // Issues
                    if !analysis.issues.isEmpty {
                        AnalysisSection(title: "发现的问题", icon: "exclamationmark.triangle") {
                            VStack(spacing: 12) {
                                ForEach(analysis.issues) { issue in
                                    IssueCard(issue: issue)
                                }
                            }
                        }
                    }

                    // Recommendations
                    if !analysis.recommendations.isEmpty {
                        AnalysisSection(title: "优化建议", icon: "lightbulb") {
                            VStack(alignment: .leading, spacing: 12) {
                                ForEach(analysis.recommendations, id: \.self) { recommendation in
                                    HStack(alignment: .top, spacing: 12) {
                                        Image(systemName: "lightbulb.fill")
                                            .font(.system(size: 14))
                                            .foregroundColor(.orange)
                                            .padding(.top, 2)

                                        Text(recommendation)
                                            .font(.system(size: 13))
                                            .foregroundColor(Color.fmText2)
                                            .lineSpacing(3)
                                    }
                                    .padding(12)
                                    .background(Color.orange.opacity(0.05))
                                    .cornerRadius(8)
                                }
                            }
                        }
                    }
                }
                .padding(20)
            }
            .background(Color.fmBg)

            Divider()

            // Footer
            HStack(spacing: 12) {
                Spacer()

                Button(action: {}) {
                    HStack(spacing: 6) {
                        Image(systemName: "arrow.down.doc")
                            .font(.system(size: 13))
                        Text("导出报告")
                            .font(.system(size: 14))
                    }
                    .foregroundColor(Color.fmText2)
                    .padding(.horizontal, 16)
                    .padding(.vertical, 8)
                    .background(Color.white)
                    .cornerRadius(6)
                    .overlay(
                        RoundedRectangle(cornerRadius: 6)
                            .stroke(Color.fmBorder, lineWidth: 1)
                    )
                }
                .buttonStyle(PlainButtonStyle())

                Button(action: {}) {
                    HStack(spacing: 6) {
                        Image(systemName: "square.and.pencil")
                            .font(.system(size: 13))
                        Text("优化 SOP")
                            .font(.system(size: 14))
                    }
                    .foregroundColor(.white)
                    .padding(.horizontal, 16)
                    .padding(.vertical, 8)
                    .background(Color.blue)
                    .cornerRadius(6)
                }
                .buttonStyle(PlainButtonStyle())
            }
            .padding(16)
            .background(Color.white)
        }
        .frame(width: 1000, height: 800)
    }

    func scoreColor(_ score: Double) -> Color {
        if score >= 90 { return .green }
        if score >= 80 { return .blue }
        if score >= 70 { return .orange }
        return .red
    }
}

// MARK: - Analysis Section
struct AnalysisSection<Content: View>: View {
    let title: String
    let icon: String
    let content: Content

    init(title: String, icon: String, @ViewBuilder content: () -> Content) {
        self.title = title
        self.icon = icon
        self.content = content()
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(spacing: 8) {
                Image(systemName: icon)
                    .font(.system(size: 14))
                    .foregroundColor(.blue)
                Text(title)
                    .font(.system(size: 15, weight: .semibold))
                    .foregroundColor(Color.fmText)
            }

            content
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(16)
        .background(Color.white)
        .cornerRadius(8)
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .stroke(Color.fmBorder, lineWidth: 1)
        )
    }
}

// MARK: - Performance Metric Card
struct PerformanceMetricCard: View {
    let title: String
    let value: Double
    let icon: String
    let color: Color

    var body: some View {
        VStack(spacing: 8) {
            ZStack {
                Circle()
                    .stroke(color.opacity(0.2), lineWidth: 8)
                    .frame(width: 80, height: 80)

                Circle()
                    .trim(from: 0, to: value / 100)
                    .stroke(color, lineWidth: 8)
                    .frame(width: 80, height: 80)
                    .rotationEffect(.degrees(-90))

                VStack(spacing: 2) {
                    Image(systemName: icon)
                        .font(.system(size: 16))
                        .foregroundColor(color)
                    Text(String(format: "%.0f", value))
                        .font(.system(size: 18, weight: .bold))
                        .foregroundColor(Color.fmText)
                }
            }

            Text(title)
                .font(.system(size: 13))
                .foregroundColor(Color.fmText2)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 12)
    }
}

// MARK: - Trend Chart View
struct TrendChartView: View {
    let trends: [SOPAnalysis.TrendData]

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            // Usage count chart
            VStack(alignment: .leading, spacing: 8) {
                Text("使用次数趋势")
                    .font(.system(size: 13, weight: .medium))
                    .foregroundColor(Color.fmText2)

                Chart(trends) { trend in
                    LineMark(
                        x: .value("月份", trend.date),
                        y: .value("使用次数", trend.usageCount)
                    )
                    .foregroundStyle(Color.blue)
                    .interpolationMethod(.catmullRom)

                    PointMark(
                        x: .value("月份", trend.date),
                        y: .value("使用次数", trend.usageCount)
                    )
                    .foregroundStyle(Color.blue)
                }
                .frame(height: 120)
                .chartYAxis {
                    AxisMarks(position: .leading)
                }
            }

            Divider()

            // Success rate chart
            VStack(alignment: .leading, spacing: 8) {
                Text("成功率趋势")
                    .font(.system(size: 13, weight: .medium))
                    .foregroundColor(Color.fmText2)

                Chart(trends) { trend in
                    LineMark(
                        x: .value("月份", trend.date),
                        y: .value("成功率", trend.successRate * 100)
                    )
                    .foregroundStyle(Color.green)
                    .interpolationMethod(.catmullRom)

                    PointMark(
                        x: .value("月份", trend.date),
                        y: .value("成功率", trend.successRate * 100)
                    )
                    .foregroundStyle(Color.green)
                }
                .frame(height: 120)
                .chartYScale(domain: 80...100)
                .chartYAxis {
                    AxisMarks(position: .leading) { value in
                        AxisValueLabel {
                            if let intValue = value.as(Double.self) {
                                Text("\(Int(intValue))%")
                            }
                        }
                    }
                }
            }
        }
    }
}

// MARK: - Comparison Row
struct ComparisonRow: View {
    let comparison: SOPAnalysis.Comparison

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(comparison.metric)
                    .font(.system(size: 13, weight: .medium))
                    .foregroundColor(Color.fmText)

                Spacer()

                Text(comparison.ranking)
                    .font(.system(size: 12))
                    .foregroundColor(.blue)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 3)
                    .background(Color.blue.opacity(0.1))
                    .cornerRadius(4)
            }

            HStack(spacing: 16) {
                ComparisonBar(
                    label: "当前值",
                    value: comparison.currentValue,
                    maxValue: max(comparison.currentValue, comparison.avgValue, comparison.bestValue),
                    color: .blue
                )

                ComparisonBar(
                    label: "平均值",
                    value: comparison.avgValue,
                    maxValue: max(comparison.currentValue, comparison.avgValue, comparison.bestValue),
                    color: .gray
                )

                ComparisonBar(
                    label: "最佳值",
                    value: comparison.bestValue,
                    maxValue: max(comparison.currentValue, comparison.avgValue, comparison.bestValue),
                    color: .green
                )
            }
        }
        .padding(12)
        .background(Color(NSColor.controlBackgroundColor).opacity(0.3))
        .cornerRadius(6)
    }
}

// MARK: - Comparison Bar
struct ComparisonBar: View {
    let label: String
    let value: Double
    let maxValue: Double
    let color: Color

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                Text(label)
                    .font(.system(size: 11))
                    .foregroundColor(Color.fmText3)
                Spacer()
                Text(String(format: "%.0f", value))
                    .font(.system(size: 12, weight: .medium))
                    .foregroundColor(Color.fmText)
            }

            GeometryReader { geometry in
                ZStack(alignment: .leading) {
                    Rectangle()
                        .fill(Color.fmBorder.opacity(0.3))
                        .frame(height: 6)
                        .cornerRadius(3)

                    Rectangle()
                        .fill(color)
                        .frame(width: geometry.size.width * (value / maxValue), height: 6)
                        .cornerRadius(3)
                }
            }
            .frame(height: 6)
        }
        .frame(maxWidth: .infinity)
    }
}

// MARK: - Issue Card
struct IssueCard: View {
    let issue: SOPAnalysisService.SOPIssue

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(alignment: .top, spacing: 12) {
                Image(systemName: "exclamationmark.triangle.fill")
                    .font(.system(size: 16))
                    .foregroundColor(severityColor(issue.severity))

                VStack(alignment: .leading, spacing: 6) {
                    HStack(spacing: 8) {
                        Text(issue.type)
                            .font(.system(size: 14, weight: .medium))
                            .foregroundColor(Color.fmText)

                        Text(issue.severity)
                            .font(.system(size: 11))
                            .foregroundColor(.white)
                            .padding(.horizontal, 6)
                            .padding(.vertical, 2)
                            .background(severityColor(issue.severity))
                            .cornerRadius(3)
                    }

                    Text(issue.description)
                        .font(.system(size: 13))
                        .foregroundColor(Color.fmText2)
                        .lineSpacing(3)

                    HStack(spacing: 12) {
                        if let stepNumber = issue.stepNumber {
                            Label("步骤 \(stepNumber)", systemImage: "number")
                                .font(.system(size: 12))
                                .foregroundColor(Color.fmText3)
                        }

                        Label("出现 \(issue.occurrenceCount) 次", systemImage: "arrow.clockwise")
                            .font(.system(size: 12))
                            .foregroundColor(Color.fmText3)
                    }
                }
            }
        }
        .padding(16)
        .background(Color.white)
        .cornerRadius(8)
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .stroke(severityColor(issue.severity).opacity(0.3), lineWidth: 1)
        )
    }

    private func severityColor(_ severity: String) -> Color {
        switch severity {
        case "高": return .red
        case "中": return .orange
        case "低": return .yellow
        default: return .gray
        }
    }
}
