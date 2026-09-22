"""
Dashboard 视图 - Succulents 设计系统
多肉植物主题设计
"""
import SwiftUI
import Charts

// MARK: - Dashboard ViewModel
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
        ActivityItem(icon: "checkmark.circle.fill", title: "工作流已执行", time: "2小时前", color: Color.fmSuccess),
        ActivityItem(icon: "doc.badge.plus", title: "文档已上传", time: "5小时前", color: Color.fmInfo),
        ActivityItem(icon: "chart.bar.fill", title: "分析已完成", time: "1天前", color: Color.fmWarning)
    ]

    func refresh() {
        isLoading = true
        DispatchQueue.main.asyncAfter(deadline: .now() + 1) {
            self.isLoading = false
        }
    }
}

// MARK: - Main Dashboard View
struct SucculentsDashboardView: View {
    @StateObject private var viewModel = DashboardViewModel()

    var body: some View {
        ScrollView {
            VStack(spacing: 24) {
                // Header
                headerSection

                // Stats Grid
                statsGrid

                // Charts Section
                HStack(spacing: 16) {
                    activityChartSection
                    recentActivitySection
                }

                Spacer()
            }
            .padding(24)
        }
        .background(Color.fmBgSecondary)
    }

    // MARK: - Header Section
    private var headerSection: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text("仪表盘")
                    .font(.system(size: 32, weight: .bold))
                    .foregroundColor(.fmTextPrimary)

                Text("欢迎回来！这是您的概览")
                    .font(.system(size: 16))
                    .foregroundColor(.fmTextSecondary)
            }

            Spacer()

            Button(action: viewModel.refresh) {
                HStack(spacing: 6) {
                    Image(systemName: "arrow.clockwise")
                        .font(.system(size: 14))
                    Text("刷新")
                        .font(.system(size: 14))
                }
                .padding(.horizontal, 16)
                .padding(.vertical, 8)
                .background(Color.fmBgElevated)
                .cornerRadius(8)
                .overlay(
                    RoundedRectangle(cornerRadius: 8)
                        .stroke(Color.fmBorder, lineWidth: 1)
                )
            }
            .buttonStyle(.plain)
        }
    }

    // MARK: - Stats Grid
    private var statsGrid: some View {
        LazyVGrid(columns: Array(repeating: GridItem(.flexible(), spacing: 16), count: 4), spacing: 16) {
            StatCardView(
                title: "总项目",
                value: "\(viewModel.projectCount)",
                change: "+12%",
                icon: "folder.fill",
                color: Color.fmPrimary,
                isPositive: true
            )

            StatCardView(
                title: "工作流",
                value: "\(viewModel.workflowCount)",
                change: "+24%",
                icon: "bolt.fill",
                color: Color.fmSecondary,
                isPositive: true
            )

            StatCardView(
                title: "文档",
                value: "\(viewModel.documentCount)",
                change: "+8%",
                icon: "doc.fill",
                color: Color.fmWarning,
                isPositive: true
            )

            StatCardView(
                title: "资产",
                value: "\(viewModel.assetCount)",
                change: "-3%",
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
            .frame(height: 280)
            .chartYAxis {
                AxisMarks(position: .leading)
            }
        }
        .padding(20)
        .background(Color.fmBgElevated)
        .cornerRadius(12)
        .fmCardShadow()
    }

    // MARK: - Recent Activity Section
    private var recentActivitySection: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("最近活动")
                .font(.system(size: 18, weight: .semibold))
                .foregroundColor(.fmTextPrimary)

            VStack(spacing: 12) {
                ForEach(viewModel.recentActivities) { activity in
                    ActivityRowView(activity: activity)
                }
            }

            Spacer()
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(20)
        .background(Color.fmBgElevated)
        .cornerRadius(12)
        .fmCardShadow()
    }
}

// MARK: - Stat Card View
struct StatCardView: View {
    let title: String
    let value: String
    let change: String
    let icon: String
    let color: Color
    let isPositive: Bool

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text(title)
                    .font(.system(size: 14))
                    .foregroundColor(.fmTextSecondary)

                Spacer()

                ZStack {
                    Circle()
                        .fill(color.opacity(0.1))
                        .frame(width: 40, height: 40)

                    Image(systemName: icon)
                        .foregroundColor(color)
                        .font(.system(size: 16))
                }
            }

            Text(value)
                .font(.system(size: 32, weight: .bold))
                .foregroundColor(.fmTextPrimary)

            HStack(spacing: 4) {
                Image(systemName: isPositive ? "arrow.up" : "arrow.down")
                    .font(.system(size: 12))
                Text(change)
                    .font(.system(size: 14))
                Text("较上月")
                    .font(.system(size: 14))
                    .foregroundColor(.fmTextSecondary)
            }
            .foregroundColor(isPositive ? .fmSuccess : .fmError)
        }
        .padding(20)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color.fmBgElevated)
        .cornerRadius(12)
        .fmCardShadow()
    }
}

// MARK: - Activity Row View
struct ActivityRowView: View {
    let activity: ActivityItem

    var body: some View {
        HStack(spacing: 12) {
            ZStack {
                Circle()
                    .fill(activity.color.opacity(0.1))
                    .frame(width: 32, height: 32)

                Image(systemName: activity.icon)
                    .font(.system(size: 14))
                    .foregroundColor(activity.color)
            }

            VStack(alignment: .leading, spacing: 2) {
                Text(activity.title)
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(.fmTextPrimary)

                Text(activity.time)
                    .font(.system(size: 12))
                    .foregroundColor(.fmTextTertiary)
            }

            Spacer()
        }
        .padding(.vertical, 8)
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
    let time: String
    let color: Color
}

// MARK: - Preview
#Preview {
    SucculentsDashboardView()
}
