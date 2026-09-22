"""
仪表盘视图 - 严格遵循设计标准
参考: Donezo Dashboard + Succulents 配色
"""
import SwiftUI
import Charts

// MARK: - Dashboard View Model
class DashboardViewModel: ObservableObject {
    @Published var projectCount: Int = 42
    @Published var workflowCount: Int = 1247
    @Published var documentCount: Int = 3856
    @Published var assetCount: Int = 289
    @Published var isLoading: Bool = false

    @Published var chartData: [ChartDataPoint] = [
        ChartDataPoint(day: "周一", value: 120),
        ChartDataPoint(day: "周二", value: 200),
        ChartDataPoint(day: "周三", value: 150),
        ChartDataPoint(day: "周四", value: 80),
        ChartDataPoint(day: "周五", value: 70),
        ChartDataPoint(day: "周六", value: 110),
        ChartDataPoint(day: "周日", value: 130)
    ]

    @Published var recentActivities: [ActivityItem] = [
        ActivityItem(icon: "checkmark.circle.fill", title: "工作流已执行", subtitle: "数据处理管道", time: "2小时前", color: Color.fmSuccess),
        ActivityItem(icon: "doc.badge.plus", title: "文档已上传", subtitle: "15个新文件", time: "5小时前", color: Color.fmInfo),
        ActivityItem(icon: "chart.bar.fill", title: "分析已完成", subtitle: "月度报告", time: "1天前", color: Color.fmWarning)
    ]

    func refresh() {
        isLoading = true
        DispatchQueue.main.asyncAfter(deadline: .now() + 1) {
            self.isLoading = false
        }
    }
}

// MARK: - Main Dashboard View
struct StandardDashboardView: View {
    @StateObject private var viewModel = DashboardViewModel()

    var body: some View {
        ScrollView {
            VStack(spacing: 24) {
                // 页面标题区域
                headerSection
                    .padding(.horizontal, 24)

                // 统计卡片网格（4列）
                statsGridSection
                    .padding(.horizontal, 24)

                // 图表和活动区域
                HStack(alignment: .top, spacing: 16) {
                    // 活动趋势图表
                    activityChartSection
                        .frame(maxWidth: .infinity)

                    // 最近活动列表
                    recentActivitySection
                        .frame(width: 320)
                }
                .padding(.horizontal, 24)

                Spacer()
            }
            .padding(.vertical, 24)
        }
        .background(Color.fmBgSecondary)
    }

    // MARK: - Header Section
    private var headerSection: some View {
        HStack(alignment: .top) {
            VStack(alignment: .leading, spacing: 4) {
                Text("仪表盘")
                    .font(.system(size: 32, weight: .bold))
                    .foregroundColor(.fmTextPrimary)

                Text("欢迎回来！这是您的概览")
                    .font(.system(size: 16, weight: .regular))
                    .foregroundColor(.fmTextSecondary)
            }

            Spacer()

            HStack(spacing: 12) {
                Button(action: viewModel.refresh) {
                    HStack(spacing: 6) {
                        Image(systemName: "arrow.clockwise")
                            .font(.system(size: 14))
                        Text("刷新")
                            .font(.system(size: 14, weight: .medium))
                    }
                    .foregroundColor(.fmTextPrimary)
                    .padding(.horizontal, 16)
                    .padding(.vertical, 10)
                    .background(Color.white)
                    .overlay(
                        RoundedRectangle(cornerRadius: 8)
                            .stroke(Color.fmBorder, lineWidth: 1)
                    )
                    .cornerRadius(8)
                }
                .buttonStyle(ScaleButtonStyle())

                Button(action: {}) {
                    HStack(spacing: 6) {
                        Image(systemName: "square.and.arrow.up")
                            .font(.system(size: 14))
                        Text("导出")
                            .font(.system(size: 14, weight: .medium))
                    }
                    .foregroundColor(.white)
                    .padding(.horizontal, 16)
                    .padding(.vertical, 10)
                    .background(Color.fmPrimary)
                    .cornerRadius(8)
                }
                .buttonStyle(ScaleButtonStyle())
            }
        }
    }

    // MARK: - Stats Grid Section
    private var statsGridSection: some View {
        LazyVGrid(
            columns: Array(repeating: GridItem(.flexible(), spacing: 16), count: 4),
            spacing: 16
        ) {
            StatCard(
                title: "总项目",
                value: "\(viewModel.projectCount)",
                change: "+12%",
                changeLabel: "较上月",
                icon: "folder.fill",
                color: Color.fmPrimary,
                isPositive: true
            )

            StatCard(
                title: "工作流",
                value: "\(viewModel.workflowCount)",
                change: "+24%",
                changeLabel: "较上月",
                icon: "bolt.fill",
                color: Color.fmSecondary,
                isPositive: true
            )

            StatCard(
                title: "文档",
                value: "\(viewModel.documentCount)",
                change: "+8%",
                changeLabel: "较上月",
                icon: "doc.fill",
                color: Color.fmWarning,
                isPositive: true
            )

            StatCard(
                title: "资产",
                value: "\(viewModel.assetCount)",
                change: "-3%",
                changeLabel: "较上月",
                icon: "cube.fill",
                color: Color.fmError,
                isPositive: false
            )
        }
    }

    // MARK: - Activity Chart Section
    private var activityChartSection: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("活动概览")
                .font(.system(size: 18, weight: .semibold))
                .foregroundColor(.fmTextPrimary)

            Chart(viewModel.chartData) { item in
                BarMark(
                    x: .value("Day", item.day),
                    y: .value("Value", item.value)
                )
                .foregroundStyle(Color.fmPrimary)
                .cornerRadius(8)
            }
            .frame(height: 300)
            .chartYAxis {
                AxisMarks(position: .leading) { value in
                    AxisGridLine(stroke: StrokeStyle(lineWidth: 1, dash: [2, 2]))
                        .foregroundStyle(Color.fmBorder)
                    AxisValueLabel()
                        .font(.system(size: 12))
                        .foregroundStyle(Color.fmTextSecondary)
                }
            }
            .chartXAxis {
                AxisMarks { value in
                    AxisValueLabel()
                        .font(.system(size: 12))
                        .foregroundStyle(Color.fmTextSecondary)
                }
            }
        }
        .padding(20)
        .background(Color.white)
        .cornerRadius(12)
        .shadow(color: Color.black.opacity(0.05), radius: 4, x: 0, y: 2)
    }

    // MARK: - Recent Activity Section
    private var recentActivitySection: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("最近活动")
                .font(.system(size: 18, weight: .semibold))
                .foregroundColor(.fmTextPrimary)

            VStack(spacing: 0) {
                ForEach(Array(viewModel.recentActivities.enumerated()), id: \.element.id) { index, activity in
                    ActivityRow(activity: activity)

                    if index < viewModel.recentActivities.count - 1 {
                        Divider()
                            .padding(.vertical, 8)
                    }
                }
            }

            Spacer()
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(20)
        .background(Color.white)
        .cornerRadius(12)
        .shadow(color: Color.black.opacity(0.05), radius: 4, x: 0, y: 2)
    }
}

// MARK: - Stat Card Component
struct StatCard: View {
    let title: String
    let value: String
    let change: String
    let changeLabel: String
    let icon: String
    let color: Color
    let isPositive: Bool

    @State private var isHovered = false

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text(title)
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(.fmTextSecondary)

                Spacer()

                ZStack {
                    RoundedRectangle(cornerRadius: 12)
                        .fill(color.opacity(0.1))
                        .frame(width: 48, height: 48)

                    Image(systemName: icon)
                        .font(.system(size: 20))
                        .foregroundColor(color)
                }
            }

            Text(value)
                .font(.system(size: 32, weight: .bold))
                .foregroundColor(.fmTextPrimary)

            HStack(spacing: 4) {
                Image(systemName: isPositive ? "arrow.up" : "arrow.down")
                    .font(.system(size: 12, weight: .semibold))
                Text(change)
                    .font(.system(size: 14, weight: .medium))
                Text(changeLabel)
                    .font(.system(size: 14))
                    .foregroundColor(.fmTextSecondary)
            }
            .foregroundColor(isPositive ? .fmSuccess : .fmError)
        }
        .padding(20)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color.white)
        .cornerRadius(12)
        .shadow(
            color: Color.black.opacity(isHovered ? 0.1 : 0.05),
            radius: isHovered ? 8 : 4,
            x: 0,
            y: isHovered ? 4 : 2
        )
        .offset(y: isHovered ? -2 : 0)
        .animation(.easeInOut(duration: 0.2), value: isHovered)
        .onHover { hovering in
            isHovered = hovering
        }
    }
}

// MARK: - Activity Row Component
struct ActivityRow: View {
    let activity: ActivityItem

    var body: some View {
        HStack(spacing: 12) {
            ZStack {
                Circle()
                    .fill(activity.color.opacity(0.1))
                    .frame(width: 40, height: 40)

                Image(systemName: activity.icon)
                    .font(.system(size: 16))
                    .foregroundColor(activity.color)
            }

            VStack(alignment: .leading, spacing: 4) {
                Text(activity.title)
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundColor(.fmTextPrimary)

                Text(activity.subtitle)
                    .font(.system(size: 12))
                    .foregroundColor(.fmTextSecondary)
            }

            Spacer()

            Text(activity.time)
                .font(.system(size: 11))
                .foregroundColor(.fmTextTertiary)
        }
        .padding(.vertical, 4)
    }
}

// MARK: - Data Models
struct ChartDataPoint: Identifiable {
    let id = UUID()
    let day: String
    let value: Int
}

struct ActivityItem: Identifiable {
    let id = UUID()
    let icon: String
    let title: String
    let subtitle: String
    let time: String
    let color: Color
}

// MARK: - Custom Button Style
struct ScaleButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .scaleEffect(configuration.isPressed ? 0.98 : 1.0)
            .animation(.easeInOut(duration: 0.1), value: configuration.isPressed)
    }
}

// MARK: - Preview
#Preview {
    StandardDashboardView()
}
