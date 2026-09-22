"""
Dashboard 视图
参考 metabase 的 Dashboard 设计 + 使用 FieldMind 设计系统
"""
import SwiftUI

// MARK: - Dashboard ViewModel
class DashboardViewModel: ObservableObject {
    @Published var projectCount: Int = 0
    @Published var documentCount: Int = 0
    @Published var nodeCount: Int = 0
    @Published var processProgress: Double = 0.0

    @Published var processedTrend: [Double] = []
    @Published var networkDistribution: [ChartData] = []
    @Published var recentActivities: [Activity] = []

    @Published var isLoading: Bool = false

    init() {
        loadData()
    }

    func loadData() {
        isLoading = true

        // TODO: 调用 API 获取真实数据
        // GET /api/v1/dashboard/stats/{project_id}

        // 模拟数据
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            self.projectCount = 12
            self.documentCount = 156
            self.nodeCount = 2340
            self.processProgress = 0.85

            self.processedTrend = [10, 25, 40, 55, 80, 120, 156]

            self.networkDistribution = [
                ChartData(label: "文化传承", value: 450),
                ChartData(label: "经济结构", value: 380),
                ChartData(label: "社会组织", value: 320),
                ChartData(label: "政策支持", value: 290),
                ChartData(label: "在地业态", value: 500),
                ChartData(label: "历史脉络", value: 400)
            ]

            self.recentActivities = [
                Activity(title: "文档上传完成", time: "5 分钟前", type: .success),
                Activity(title: "知识提取完成", time: "15 分钟前", type: .info),
                Activity(title: "新建项目", time: "1 小时前", type: .success),
                Activity(title: "批量处理启动", time: "2 小时前", type: .info)
            ]

            self.isLoading = false
        }
    }

    func refresh() {
        loadData()
    }
}

// MARK: - 数据模型
struct ChartData: Identifiable {
    let id = UUID()
    let label: String
    let value: Double
}

struct Activity: Identifiable {
    let id = UUID()
    let title: String
    let time: String
    let type: ActivityType
}

enum ActivityType {
    case success, info, warning, error

    var color: Color {
        switch self {
        case .success: return .fmSuccess
        case .info: return .fmInfo
        case .warning: return .fmWarning
        case .error: return .fmError
        }
    }
}

// MARK: - Dashboard View
struct DashboardView: View {
    @StateObject var viewModel = DashboardViewModel()
    let projectId: Int

    var body: some View {
        ScrollView {
            VStack(spacing: 24) {
                // 顶部操作栏 - Succulents 风格
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
                            Text("刷新")
                        }
                        .font(.system(size: 14))
                    }
                    .buttonStyle(.bordered)

                    Button(action: {}) {
                        HStack(spacing: 6) {
                            Image(systemName: "square.and.arrow.up")
                            Text("导出")
                        }
                        .font(.system(size: 14))
                    }
                    .buttonStyle(.bordered)
                }
                .padding(.horizontal, 24)

                // 统计卡片网格
                LazyVGrid(
                    columns: [
                        GridItem(.flexible()),
                        GridItem(.flexible()),
                        GridItem(.flexible()),
                        GridItem(.flexible())
                    ],
                    spacing: Spacing.lg
                ) {
                    FMStatCard(
                        title: "项目数量",
                        value: "\(viewModel.projectCount)",
                        trend: 8.3,
                        icon: "folder.fill"
                    )

                    FMStatCard(
                        title: "文档总数",
                        value: "\(viewModel.documentCount)",
                        trend: 15.2,
                        icon: "doc.fill"
                    )

                    FMStatCard(
                        title: "处理进度",
                        value: "\(Int(viewModel.processProgress * 100))%",
                        trend: nil,
                        icon: "gauge"
                    )

                    FMStatCard(
                        title: "知识节点",
                        value: "\(viewModel.nodeCount)",
                        trend: 22.5,
                        icon: "circle.grid.3x3.fill"
                    )
                }
                .padding(.horizontal, Spacing.lg)

                // 图表区域
                LazyVGrid(
                    columns: [
                        GridItem(.flexible()),
                        GridItem(.flexible())
                    ],
                    spacing: Spacing.lg
                ) {
                    // 文档处理趋势
                    ChartCard(title: "文档处理趋势") {
                        LineChartView(data: viewModel.processedTrend)
                    }

                    // 知识网络分布
                    ChartCard(title: "知识网络分布") {
                        PieChartView(data: viewModel.networkDistribution)
                    }
                }
                .padding(.horizontal, Spacing.lg)

                // 底部区域
                HStack(alignment: .top, spacing: Spacing.lg) {
                    // 热门主题
                    ChartCard(title: "热门主题") {
                        TagCloudView()
                    }
                    .frame(maxWidth: .infinity)

                    // 最近活动
                    FMCard {
                        VStack(alignment: .leading, spacing: Spacing.md) {
                            Text("最近活动")
                                .font(Typography.h4)

                            ForEach(viewModel.recentActivities) { activity in
                                ActivityRow(activity: activity)
                            }
                        }
                    }
                    .frame(maxWidth: .infinity)
                }
                .padding(.horizontal, Spacing.lg)
                .padding(.bottom, Spacing.lg)
            }
            .padding(.top, Spacing.lg)
        }
        .background(Color.fmBgSecondary)
    }
}

// MARK: - 图表卡片
struct ChartCard<Content: View>: View {
    let title: String
    let content: Content

    init(title: String, @ViewBuilder content: () -> Content) {
        self.title = title
        self.content = content()
    }

    var body: some View {
        FMCard {
            VStack(alignment: .leading, spacing: Spacing.md) {
                Text(title)
                    .font(Typography.h4)
                    .foregroundColor(.fmTextPrimary)

                content
                    .frame(height: 200)
            }
        }
    }
}

// MARK: - 活动行
struct ActivityRow: View {
    let activity: Activity

    var body: some View {
        HStack(alignment: .top, spacing: Spacing.sm) {
            Circle()
                .fill(activity.type.color)
                .frame(width: 10, height: 10)
                .padding(.top, 4)

            VStack(alignment: .leading, spacing: 4) {
                Text(activity.title)
                    .font(Typography.body)
                    .foregroundColor(.fmTextPrimary)

                Text(activity.time)
                    .font(Typography.caption)
                    .foregroundColor(.fmTextSecondary)
            }

            Spacer()
        }
    }
}

// MARK: - 占位符图表视图
struct LineChartView: View {
    let data: [Double]

    var body: some View {
        GeometryReader { geometry in
            Path { path in
                guard !data.isEmpty else { return }

                let maxValue = data.max() ?? 1
                let stepX = geometry.size.width / CGFloat(data.count - 1)
                let stepY = geometry.size.height / maxValue

                path.move(to: CGPoint(x: 0, y: geometry.size.height - data[0] * stepY))

                for (index, value) in data.enumerated() {
                    let x = CGFloat(index) * stepX
                    let y = geometry.size.height - value * stepY
                    path.addLine(to: CGPoint(x: x, y: y))
                }
            }
            .stroke(Color.fmAccent, lineWidth: 2)
        }
    }
}

struct PieChartView: View {
    let data: [ChartData]

    var body: some View {
        HStack {
            // 饼图占位符
            Circle()
                .fill(Color.fmAccent.opacity(0.2))
                .overlay(
                    Text("饼图")
                        .font(Typography.caption)
                        .foregroundColor(.fmTextSecondary)
                )

            // 图例
            VStack(alignment: .leading, spacing: 8) {
                ForEach(data.prefix(4)) { item in
                    HStack {
                        Circle()
                            .fill(Color.fmAccent)
                            .frame(width: 8, height: 8)
                        Text(item.label)
                            .font(Typography.small)
                        Spacer()
                        Text("\(Int(item.value))")
                            .font(Typography.small)
                            .foregroundColor(.fmTextSecondary)
                    }
                }
            }
        }
    }
}

struct TagCloudView: View {
    let tags = ["乡村振兴", "非遗保护", "文化传承", "产业发展", "社区营造", "生态保护"]

    var body: some View {
        VStack(alignment: .leading, spacing: Spacing.sm) {
            ForEach(tags, id: \.self) { tag in
                Text(tag)
                    .font(Typography.body)
                    .padding(.horizontal, 12)
                    .padding(.vertical, 6)
                    .background(Color.fmAccent.opacity(0.1))
                    .foregroundColor(.fmAccent)
                    .cornerRadius(16)
            }
        }
    }
}

// MARK: - 预览
struct DashboardView_Previews: PreviewProvider {
    static var previews: some View {
        DashboardView(projectId: 1)
    }
}
