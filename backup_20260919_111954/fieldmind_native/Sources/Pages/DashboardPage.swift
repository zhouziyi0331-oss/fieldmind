import SwiftUI
import Charts

struct DashboardPage: View {
    @EnvironmentObject var appState: AppState
    @StateObject private var viewModel = DashboardViewModel()
    @State private var timeRange: TimeRange = .week
    @State private var selectedMetric: String? = nil

    enum TimeRange: String, CaseIterable {
        case day = "今日"
        case week = "本周"
        case month = "本月"
        case year = "本年"
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            // 页头
            sectionHeader

            // 时间范围选择器
            timeRangeSelector

            Spacer().frame(height: 16)

            // 错误提示
            if let errorMessage = viewModel.errorMessage {
                HStack {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .foregroundStyle(Color.fmRed)
                    Text(errorMessage)
                        .font(.system(size: 13))
                        .foregroundStyle(Color.fmRed)
                    Spacer()
                    Button("关闭") {
                        viewModel.errorMessage = nil
                    }
                    .font(.system(size: 12, weight: .medium))
                    .foregroundStyle(Color.fmRed)
                }
                .padding(12)
                .background(Color.fmRed.opacity(0.1))
                .clipShape(RoundedRectangle(cornerRadius: 8))
                .padding(.bottom, 16)
            }

            // 加载状态
            if viewModel.isLoadingStats && viewModel.stats == nil {
                VStack(spacing: 16) {
                    ProgressView()
                    Text("加载中...")
                        .font(.system(size: 13))
                        .foregroundStyle(Color.fmN6)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            }
            // 内容区：网格布局
            else if let stats = viewModel.stats {
                ScrollView {
                    VStack(spacing: 14) {
                        // 第一行：关键指标卡片
                        keyMetricsRow(stats: stats)

                        // 第二行：材料统计 + 关键词增长
                        HStack(spacing: 14) {
                            materialStatsChart
                                .frame(maxWidth: .infinity)
                            keywordGrowthChart(stats: stats)
                                .frame(maxWidth: .infinity)
                        }

                        // 第三行：处理进度 + 状态分布
                        HStack(spacing: 14) {
                            progressChart
                                .frame(maxWidth: .infinity)
                            statusDistribution(stats: stats)
                                .frame(maxWidth: .infinity)
                        }

                        // 第四行：顶级关键词
                        topKeywordsSection(stats: stats)
                    }
                }
            }
        }
        .task {
            if let projectId = appState.currentProject?.id {
                await viewModel.loadAllData(projectId: projectId)
            }
        }
    }

    // MARK: - Section Header
    private var sectionHeader: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack(spacing: 7) {
                Circle()
                    .fill(Color.fmA1)
                    .frame(width: 6, height: 6)
                    .shadow(color: Color.fmA1, radius: 4)

                Text("数据看板")
                    .font(.system(size: 14, weight: .heavy))
                    .foregroundColor(.fmText)
                    .tracking(-0.01)
            }

            Text("项目全局数据可视化，趋势分析与智能洞察")
                .font(.system(size: 10))
                .foregroundColor(.fmText3)
                .tracking(0.02)
        }
        .padding(.bottom, 16)
    }

    // MARK: - Time Range Selector
    private var timeRangeSelector: some View {
        HStack(spacing: 6) {
            ForEach(TimeRange.allCases, id: \.self) { range in
                Button(action: { timeRange = range }) {
                    Text(range.rawValue)
                        .font(.system(size: 11, weight: timeRange == range ? .semibold : .regular))
                        .foregroundColor(timeRange == range ? .white : .fmText2)
                        .padding(EdgeInsets(top: 6, leading: 14, bottom: 6, trailing: 14))
                        .background(timeRange == range ? Color.fmA1 : Color.fmSurface)
                        .cornerRadius(8)
                }
                .buttonStyle(.plain)
            }

            Spacer()

            // 导出按钮
            Button(action: {}) {
                HStack(spacing: 5) {
                    Image(systemName: "square.and.arrow.up")
                        .font(.system(size: 10))
                    Text("导出")
                        .font(.system(size: 11))
                }
            }
            .buttonStyle(FMButtonStyle(style: .outline, size: .small))
        }
    }

    // MARK: - Key Metrics Row
    private func keyMetricsRow(stats: DashboardStats) -> some View {
        HStack(spacing: 14) {
            MetricCard(
                title: "总文档数",
                value: "\(stats.totalDocuments)",
                change: "+\(stats.documentsThisWeek)",
                changeType: .positive,
                icon: "doc.text.fill",
                color: .fmA1
            )

            MetricCard(
                title: "关键词库",
                value: "\(stats.totalKeywords)",
                change: "",
                changeType: .neutral,
                icon: "tag.fill",
                color: .fmA2
            )

            MetricCard(
                title: "处理完成",
                value: "\(stats.completedDocuments)",
                change: "",
                changeType: .positive,
                icon: "checkmark.circle.fill",
                color: .fmA3
            )

            MetricCard(
                title: "向量化",
                value: "\(stats.vectorizedDocuments)",
                change: "",
                changeType: .positive,
                icon: "cube.fill",
                color: .fmA5
            )
        }
    }

    // MARK: - Material Stats Chart
    private var materialStatsChart: some View {
        FMCard {
            VStack(alignment: .leading, spacing: 0) {
                HStack {
                    Text("材料统计")
                        .font(.system(size: 13, weight: .bold))
                        .foregroundColor(.fmText)

                    Spacer()

                    HStack(spacing: 4) {
                        Circle()
                            .fill(Color.fmA1)
                            .frame(width: 6, height: 6)
                        Text("音频")
                            .font(.system(size: 9))
                            .foregroundColor(.fmText3)

                        Circle()
                            .fill(Color.fmA2)
                            .frame(width: 6, height: 6)
                        Text("视频")
                            .font(.system(size: 9))
                            .foregroundColor(.fmText3)

                        Circle()
                            .fill(Color.fmA5)
                            .frame(width: 6, height: 6)
                        Text("文档")
                            .font(.system(size: 9))
                            .foregroundColor(.fmText3)
                    }
                }
                .padding(EdgeInsets(top: 16, leading: 16, bottom: 12, trailing: 16))

                // 柱状图
                Chart {
                    ForEach(materialStatsData, id: \.date) { item in
                        BarMark(
                            x: .value("日期", item.date, unit: .day),
                            y: .value("音频", item.audio)
                        )
                        .foregroundStyle(Color.fmA1)

                        BarMark(
                            x: .value("日期", item.date, unit: .day),
                            y: .value("视频", item.video)
                        )
                        .foregroundStyle(Color.fmA2)

                        BarMark(
                            x: .value("日期", item.date, unit: .day),
                            y: .value("文档", item.document)
                        )
                        .foregroundStyle(Color.fmA5)
                    }
                }
                .chartXAxis {
                    AxisMarks(values: .stride(by: .day)) { _ in
                        AxisGridLine(stroke: StrokeStyle(lineWidth: 0.5))
                            .foregroundStyle(Color.fmBorder.opacity(0.3))
                        AxisTick(stroke: StrokeStyle(lineWidth: 0))
                        AxisValueLabel(format: .dateTime.month().day(), centered: true)
                            .font(.system(size: 9))
                            .foregroundStyle(Color.fmText3)
                    }
                }
                .chartYAxis {
                    AxisMarks { _ in
                        AxisGridLine(stroke: StrokeStyle(lineWidth: 0.5))
                            .foregroundStyle(Color.fmBorder.opacity(0.3))
                        AxisValueLabel()
                            .font(.system(size: 9))
                            .foregroundStyle(Color.fmText3)
                    }
                }
                .frame(height: 180)
                .padding(EdgeInsets(top: 8, leading: 12, bottom: 16, trailing: 12))
            }
        }
    }

    // MARK: - Keyword Growth Chart
    private func keywordGrowthChart(stats: DashboardStats) -> some View {
        FMCard {
            VStack(alignment: .leading, spacing: 0) {
                HStack {
                    Text("关键词统计")
                        .font(.system(size: 13, weight: .bold))
                        .foregroundColor(.fmText)

                    Spacer()

                    Text("累计 \(stats.totalKeywords)")
                        .font(.system(size: 10, weight: .bold))
                        .foregroundColor(.fmA2)
                }
                .padding(EdgeInsets(top: 16, leading: 16, bottom: 12, trailing: 16))

                // 关键词统计信息
                VStack(alignment: .leading, spacing: 12) {
                    HStack {
                        VStack(alignment: .leading, spacing: 4) {
                            Text("总关键词")
                                .font(.system(size: 10))
                                .foregroundColor(.fmText3)
                            Text("\(stats.totalKeywords)")
                                .font(.system(size: 20, weight: .bold))
                                .foregroundColor(.fmText)
                        }

                        Spacer()

                        VStack(alignment: .leading, spacing: 4) {
                            Text("总分块")
                                .font(.system(size: 10))
                                .foregroundColor(.fmText3)
                            Text("\(stats.totalChunks)")
                                .font(.system(size: 20, weight: .bold))
                                .foregroundColor(.fmText)
                        }

                        Spacer()

                        VStack(alignment: .leading, spacing: 4) {
                            Text("向量数")
                                .font(.system(size: 10))
                                .foregroundColor(.fmText3)
                            Text("\(stats.vectorCount)")
                                .font(.system(size: 20, weight: .bold))
                                .foregroundColor(.fmText)
                        }
                    }
                    .padding(16)
                    .background(Color.fmA2.opacity(0.05))
                    .clipShape(RoundedRectangle(cornerRadius: 8))
                }
                .padding(EdgeInsets(top: 8, leading: 12, bottom: 16, trailing: 12))
            }
        }
    }

    // MARK: - Processing Time Chart
    private var processingTimeChart: some View {
        FMCard {
            VStack(alignment: .leading, spacing: 0) {
                HStack {
                    Text("处理进度")
                        .font(.system(size: 13, weight: .bold))
                        .foregroundColor(.fmText)

                    Spacer()

                    if let progress = viewModel.progress {
                        Text("\(progress.overallProgress)%")
                            .font(.system(size: 10, weight: .bold))
                            .foregroundColor(.fmA5)
                    }
                }
                .padding(EdgeInsets(top: 16, leading: 16, bottom: 12, trailing: 16))

                if let progress = viewModel.progress {
                    VStack(spacing: 12) {
                        progressBar(label: "处理完成", value: progress.processingProgress, color: .fmA1)
                        progressBar(label: "向量化", value: progress.vectorizationProgress ?? 0, color: .fmA2)
                        progressBar(label: "分析完成", value: progress.analysisProgress, color: .fmA3)
                        progressBar(label: "总体进度", value: progress.overallProgress, color: .fmA5)
                    }
                    .padding(EdgeInsets(top: 8, leading: 16, bottom: 16, trailing: 16))
                } else {
                    ProgressView()
                        .padding(EdgeInsets(top: 8, leading: 16, bottom: 16, trailing: 16))
                }
            }
        }
    }

    private func progressBar(label: String, value: Int, color: Color) -> some View {
        VStack(spacing: 6) {
            HStack {
                Text(label)
                    .font(.system(size: 11, weight: .medium))
                    .foregroundColor(.fmText2)

                Spacer()

                Text("\(value)%")
                    .font(.system(size: 11, weight: .bold))
                    .foregroundColor(color)
                    .monospacedDigit()
            }

            GeometryReader { geometry in
                ZStack(alignment: .leading) {
                    RoundedRectangle(cornerRadius: 4)
                        .fill(Color.fmSurface2)
                        .frame(height: 8)

                    RoundedRectangle(cornerRadius: 4)
                        .fill(color)
                        .frame(
                            width: geometry.size.width * (Double(value) / 100.0),
                            height: 8
                        )
                }
            }
            .frame(height: 8)
        }
    }

    // MARK: - Progress Chart (keeping old name for compatibility)
    private var progressChart: some View {
        processingTimeChart
    }

    // MARK: - Active Hours Chart
    private var activeHoursChart: some View {
        FMCard {
            VStack(alignment: .leading, spacing: 0) {
                HStack {
                    Text("活跃时段分布")
                        .font(.system(size: 13, weight: .bold))
                        .foregroundColor(.fmText)

                    Spacer()

                    Text("峰值 14:00-16:00")
                        .font(.system(size: 10, weight: .bold))
                        .foregroundColor(.fmA3)
                }
                .padding(EdgeInsets(top: 16, leading: 16, bottom: 12, trailing: 16))

                // 折线图
                Chart(activeHoursData, id: \.hour) { item in
                    LineMark(
                        x: .value("时段", item.hour),
                        y: .value("活跃度", item.activity)
                    )
                    .foregroundStyle(Color.fmA3)
                    .lineStyle(StrokeStyle(lineWidth: 2.5))
                    .symbol(Circle().strokeBorder(lineWidth: 2))
                    .symbolSize(40)
                }
                .chartXAxis {
                    AxisMarks(values: .stride(by: 3)) { _ in
                        AxisGridLine(stroke: StrokeStyle(lineWidth: 0.5))
                            .foregroundStyle(Color.fmBorder.opacity(0.3))
                        AxisValueLabel()
                            .font(.system(size: 9))
                            .foregroundStyle(Color.fmText3)
                    }
                }
                .chartYAxis {
                    AxisMarks { _ in
                        AxisGridLine(stroke: StrokeStyle(lineWidth: 0.5))
                            .foregroundStyle(Color.fmBorder.opacity(0.3))
                        AxisValueLabel()
                            .font(.system(size: 9))
                            .foregroundStyle(Color.fmText3)
                    }
                }
                .frame(height: 180)
                .padding(EdgeInsets(top: 8, leading: 12, bottom: 16, trailing: 12))
            }
        }
    }

    // MARK: - Material Type Distribution
    private var materialTypeDistribution: some View {
        FMCard {
            VStack(alignment: .leading, spacing: 0) {
                HStack {
                    Text("材料类型分布")
                        .font(.system(size: 13, weight: .bold))
                        .foregroundColor(.fmText)

                    Spacer()
                }
                .padding(EdgeInsets(top: 16, leading: 16, bottom: 12, trailing: 16))

                HStack(spacing: 20) {
                    // 饼图
                    Chart(materialTypeData, id: \.type) { item in
                        SectorMark(
                            angle: .value("数量", item.count),
                            innerRadius: .ratio(0.5),
                            angularInset: 1.5
                        )
                        .foregroundStyle(item.color)
                    }
                    .frame(width: 140, height: 140)

                    // 图例
                    VStack(alignment: .leading, spacing: 8) {
                        ForEach(materialTypeData, id: \.type) { item in
                            HStack(spacing: 8) {
                                Circle()
                                    .fill(item.color)
                                    .frame(width: 8, height: 8)

                                VStack(alignment: .leading, spacing: 2) {
                                    Text(item.type)
                                        .font(.system(size: 10, weight: .medium))
                                        .foregroundColor(.fmText2)

                                    HStack(spacing: 4) {
                                        Text("\(item.count)")
                                            .font(.system(size: 12, weight: .bold))
                                            .foregroundColor(.fmText)
                                        let totalCount = materialTypeData.reduce(0) { $0 + $1.count }
                                        Text("(\(totalCount > 0 ? Int(Double(item.count) / Double(totalCount) * 100) : 0)%)")
                                            .font(.system(size: 9))
                                            .foregroundColor(.fmText3)
                                    }
                                }

                                Spacer()
                            }
                        }
                    }
                }
                .padding(EdgeInsets(top: 0, leading: 16, bottom: 16, trailing: 16))
            }
        }
    }

    // MARK: - Status Distribution
    private func statusDistribution(stats: DashboardStats) -> some View {
        FMCard {
            VStack(alignment: .leading, spacing: 0) {
                HStack {
                    Text("处理状态分布")
                        .font(.system(size: 13, weight: .bold))
                        .foregroundColor(.fmText)

                    Spacer()
                }
                .padding(EdgeInsets(top: 16, leading: 16, bottom: 12, trailing: 16))

                let statusData = [
                    StatusItem(status: "已完成", count: stats.completedDocuments, color: .fmA2),
                    StatusItem(status: "处理中", count: stats.processingDocuments, color: .fmA3),
                    StatusItem(status: "失败", count: stats.failedDocuments, color: .fmRed)
                ]

                VStack(spacing: 10) {
                    ForEach(statusData, id: \.status) { item in
                        VStack(spacing: 6) {
                            HStack {
                                Text(item.status)
                                    .font(.system(size: 11, weight: .medium))
                                    .foregroundColor(.fmText2)

                                Spacer()

                                Text("\(item.count)")
                                    .font(.system(size: 13, weight: .bold))
                                    .foregroundColor(item.color)
                                    .monospacedDigit()
                            }

                            GeometryReader { geometry in
                                ZStack(alignment: .leading) {
                                    RoundedRectangle(cornerRadius: 4)
                                        .fill(Color.fmSurface2)
                                        .frame(height: 8)

                                    RoundedRectangle(cornerRadius: 4)
                                        .fill(item.color)
                                        .frame(
                                            width: stats.totalDocuments > 0 ? geometry.size.width * (Double(item.count) / Double(stats.totalDocuments)) : 0,
                                            height: 8
                                        )
                                }
                            }
                            .frame(height: 8)
                        }
                    }
                }
                .padding(EdgeInsets(top: 0, leading: 16, bottom: 16, trailing: 16))
            }
        }
    }

    // MARK: - Top Keywords Section
    private func topKeywordsSection(stats: DashboardStats) -> some View {
        FMCard {
            VStack(alignment: .leading, spacing: 0) {
                HStack {
                    Text("热门关键词")
                        .font(.system(size: 13, weight: .bold))
                        .foregroundColor(.fmText)

                    Spacer()

                    Text("Top \(min(stats.topKeywords.count, 10))")
                        .font(.system(size: 10, weight: .bold))
                        .foregroundColor(.fmA2)
                }
                .padding(EdgeInsets(top: 16, leading: 16, bottom: 12, trailing: 16))

                if stats.topKeywords.isEmpty {
                    VStack(spacing: 8) {
                        Image(systemName: "tag")
                            .font(.system(size: 32))
                            .foregroundColor(.fmN3)
                        Text("暂无关键词数据")
                            .font(.system(size: 12))
                            .foregroundColor(.fmN6)
                    }
                    .frame(maxWidth: .infinity)
                    .padding(32)
                } else {
                    LazyVGrid(columns: [
                        GridItem(.flexible()),
                        GridItem(.flexible()),
                        GridItem(.flexible()),
                        GridItem(.flexible()),
                        GridItem(.flexible())
                    ], spacing: 8) {
                        ForEach(stats.topKeywords.prefix(10), id: \.keyword) { item in
                            HStack(spacing: 6) {
                                Text(item.keyword)
                                    .font(.system(size: 11, weight: .medium))
                                    .foregroundColor(.fmText)
                                    .lineLimit(1)

                                Text("\(Int(item.weight))")
                                    .font(.system(size: 10, weight: .bold))
                                    .foregroundColor(.fmA2)
                                    .monospacedDigit()
                            }
                            .padding(.horizontal, 10)
                            .padding(.vertical, 6)
                            .background(Color.fmA2.opacity(0.08))
                            .clipShape(RoundedRectangle(cornerRadius: 6))
                        }
                    }
                    .padding(EdgeInsets(top: 8, leading: 16, bottom: 16, trailing: 16))
                }
            }
        }
    }

    // MARK: - Mock Data (kept for timeline chart)
    private var materialStatsData: [MaterialStatsItem] {
        // 使用timeline数据或默认数据
        if let timeline = viewModel.timeline {
            return timeline.timeline.map { point in
                let formatter = ISO8601DateFormatter()
                let date = formatter.date(from: point.date) ?? Date()
                return MaterialStatsItem(
                    date: date,
                    audio: point.documents / 3,
                    video: point.documents / 3,
                    document: point.documents / 3
                )
            }
        } else {
            let calendar = Calendar.current
            let today = Date()
            return (0..<7).map { dayOffset in
                let date = calendar.date(byAdding: .day, value: -dayOffset, to: today)!
                return MaterialStatsItem(
                    date: date,
                    audio: 0,
                    video: 0,
                    document: 0
                )
            }.reversed()
        }
    }

    private var activeHoursData: [HourActivityItem] {
        return (0..<24).map { hour in
            HourActivityItem(hour: hour, activity: Int.random(in: 10...100))
        }
    }

    private var materialTypeData: [MaterialTypeItem] {
        return [
            MaterialTypeItem(type: "文档", count: 45, color: .fmA1),
            MaterialTypeItem(type: "音频", count: 28, color: .fmA2),
            MaterialTypeItem(type: "视频", count: 15, color: .fmA3),
            MaterialTypeItem(type: "图片", count: 32, color: .fmGreen)
        ]
    }
}

// MARK: - Metric Card
struct MetricCard: View {
    let title: String
    let value: String
    let change: String
    let changeType: ChangeType
    let icon: String
    let color: Color

    enum ChangeType {
        case positive, negative, neutral
    }

    var body: some View {
        FMCard {
            VStack(alignment: .leading, spacing: 10) {
                HStack {
                    ZStack {
                        Circle()
                            .fill(color.opacity(0.15))
                            .frame(width: 36, height: 36)

                        Image(systemName: icon)
                            .font(.system(size: 16, weight: .medium))
                            .foregroundColor(color)
                    }

                    Spacer()

                    HStack(spacing: 3) {
                        Image(systemName: changeType == .positive ? "arrow.up.right" : "arrow.down.right")
                            .font(.system(size: 8, weight: .bold))
                        Text(change)
                            .font(.system(size: 10, weight: .semibold))
                    }
                    .foregroundColor(changeType == .positive ? .fmA2 : .fmText3)
                    .padding(EdgeInsets(top: 3, leading: 6, bottom: 3, trailing: 6))
                    .background(changeType == .positive ? Color.fmA2.opacity(0.1) : Color.fmSurface2)
                    .cornerRadius(8)
                }

                VStack(alignment: .leading, spacing: 4) {
                    Text(value)
                        .font(.system(size: 22, weight: .heavy))
                        .foregroundColor(.fmText)
                        .monospacedDigit()

                    Text(title)
                        .font(.system(size: 10))
                        .foregroundColor(.fmText3)
                }
            }
            .padding(14)
        }
    }
}

// MARK: - Data Models
struct MaterialStatsItem {
    let date: Date
    let audio: Int
    let video: Int
    let document: Int
}

struct StatusItem {
    let status: String
    let count: Int
    let color: Color
}

struct HourActivityItem {
    let hour: Int
    let activity: Int
}

struct MaterialTypeItem {
    let type: String
    let count: Int
    let color: Color
}
