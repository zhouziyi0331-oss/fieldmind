import SwiftUI

struct OverviewPage: View {
    let projectId: Int
    @StateObject private var dashboardViewModel = DashboardViewModel()
    @StateObject private var projectViewModel = ProjectViewModel()
    @EnvironmentObject var appState: AppState

    var body: some View {
        ScrollView {
            VStack(spacing: 28) {
                if dashboardViewModel.isLoadingStats {
                    loadingView
                } else if let stats = dashboardViewModel.stats {
                    heroSection(stats: stats)
                    statsGrid(stats: stats)
                    workflowSection
                    twoColumnSection(stats: stats)
                } else {
                    emptyStateView
                }
            }
            .padding(24)
        }
        .task {
            await loadData()
        }
        .onChange(of: appState.lastDocumentUpdate) { _ in
            Task {
                DebugLogger.shared.log("🔄 概览页检测到数据更新，重新加载...", type: .info)
                await loadData()
            }
        }
    }

    // MARK: - Hero Section
    private func heroSection(stats: DashboardStats) -> some View {
        VStack(spacing: 12) {
            HStack {
                VStack(alignment: .leading, spacing: 6) {
                    Text("当前项目 · 2024")
                        .font(.system(size: 10, weight: .semibold))
                        .foregroundColor(.fmText3)
                        .tracking(0.06)

                    Text(stats.projectName)
                        .font(.system(size: 24, weight: .heavy))
                        .foregroundColor(.fmText)
                        .tracking(-0.02)
                        .lineSpacing(4)

                    Text("知识管理与分析平台")
                        .font(.system(size: 12))
                        .foregroundColor(.fmText2)
                        .lineSpacing(4)
                }

                Spacer()
            }

            // 统计数字
            HStack(spacing: 20) {
                HeroStat(value: "\(stats.totalDocuments)", label: "已处理材料")
                HeroStat(value: "\(stats.totalKeywords)", label: "提炼关键词")
                HeroStat(value: "\(stats.skillsAnalyzed)", label: "技能分析")
                HeroStat(value: "\(stats.chatSessions)", label: "对话会话")
                HeroStat(value: "\(stats.vectorizedDocuments)", label: "向量化文档")
            }
        }
        .padding(EdgeInsets(top: 28, leading: 32, bottom: 28, trailing: 32))
        .frame(maxWidth: .infinity)
        .background(
            LinearGradient(
                colors: [Color.fmA1.opacity(0.05), Color.fmA5.opacity(0.03)],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
        )
        .cornerRadius(FMRadius.lg)
    }

    // MARK: - Stats Grid
    private func statsGrid(stats: DashboardStats) -> some View {
        HStack(spacing: 14) {
            StatCard(
                icon: "doc.fill",
                label: "文档总数",
                value: "\(stats.totalDocuments)",
                delta: "本周 +\(stats.documentsThisWeek)",
                theme: .a1
            )

            StatCard(
                icon: "checkmark.circle.fill",
                label: "已完成",
                value: "\(stats.completedDocuments)",
                delta: "\(stats.processingDocuments) 处理中",
                theme: .a2
            )

            StatCard(
                icon: "cube.fill",
                label: "向量化",
                value: "\(stats.vectorizedDocuments)",
                delta: "\(stats.vectorCount) 向量",
                theme: .a5
            )

            StatCard(
                icon: "message.fill",
                label: "聊天消息",
                value: "\(stats.chatMessages)",
                delta: "\(stats.chatSessions) 会话",
                theme: .a4
            )
        }
    }

    // MARK: - Workflow Section
    private var workflowSection: some View {
        VStack(alignment: .leading, spacing: 14) {
            HStack {
                Text("核心工作流")
                    .font(.system(size: 16, weight: .heavy))
                    .foregroundColor(.fmText)

                Spacer()

                Text("快速访问常用功能")
                    .font(.system(size: 11))
                    .foregroundColor(.fmText3)
            }

            HStack(spacing: 12) {
                VStack(alignment: .leading, spacing: 10) {
                    Image(systemName: "arrow.down.doc.fill")
                        .font(.system(size: 24))
                        .foregroundColor(.fmA1)
                    Text("导入材料")
                        .font(.system(size: 13, weight: .semibold))
                        .foregroundColor(.fmText)
                    Text("上传音频、视频、文档")
                        .font(.system(size: 10))
                        .foregroundColor(.fmText3)
                        .lineLimit(2)
                }
                .padding(16)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(Color.fmBg2)
                .cornerRadius(FMRadius.md)

                VStack(alignment: .leading, spacing: 10) {
                    Image(systemName: "waveform")
                        .font(.system(size: 24))
                        .foregroundColor(.fmA2)
                    Text("AI 分析")
                        .font(.system(size: 13, weight: .semibold))
                        .foregroundColor(.fmText)
                    Text("自动转录与关键词提取")
                        .font(.system(size: 10))
                        .foregroundColor(.fmText3)
                        .lineLimit(2)
                }
                .padding(16)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(Color.fmBg2)
                .cornerRadius(FMRadius.md)

                VStack(alignment: .leading, spacing: 10) {
                    Image(systemName: "message.fill")
                        .font(.system(size: 24))
                        .foregroundColor(.fmA5)
                    Text("智能对话")
                        .font(.system(size: 13, weight: .semibold))
                        .foregroundColor(.fmText)
                    Text("深度问答与知识探索")
                        .font(.system(size: 10))
                        .foregroundColor(.fmText3)
                        .lineLimit(2)
                }
                .padding(16)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(Color.fmBg2)
                .cornerRadius(FMRadius.md)

                VStack(alignment: .leading, spacing: 10) {
                    Image(systemName: "chart.bar.fill")
                        .font(.system(size: 24))
                        .foregroundColor(.fmA4)
                    Text("生成报告")
                        .font(.system(size: 13, weight: .semibold))
                        .foregroundColor(.fmText)
                    Text("可视化分析与导出")
                        .font(.system(size: 10))
                        .foregroundColor(.fmText3)
                        .lineLimit(2)
                }
                .padding(16)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(Color.fmBg2)
                .cornerRadius(FMRadius.md)
            }
        }
    }

    // MARK: - Two Column Section
    private func twoColumnSection(stats: DashboardStats) -> some View {
        HStack(alignment: .top, spacing: 16) {
            // 左侧：关键词云
            VStack(alignment: .leading, spacing: 12) {
                Text("热门关键词")
                    .font(.system(size: 14, weight: .heavy))
                    .foregroundColor(.fmText)

                if stats.topKeywords.isEmpty {
                    Text("暂无关键词数据")
                        .font(.system(size: 12))
                        .foregroundColor(.fmText3)
                        .frame(maxWidth: .infinity, alignment: .center)
                        .padding(40)
                } else {
                    FlowLayout(spacing: 8) {
                        ForEach(stats.topKeywords.prefix(15), id: \.keyword) { item in
                            Text(item.keyword)
                                .font(.system(size: fontSize(item.weight), weight: .medium))
                                .foregroundColor(Color.fmText)
                                .padding(.horizontal, 12)
                                .padding(.vertical, 6)
                                .background(Color.fmA1.opacity(opacity(item.weight)))
                                .cornerRadius(16)
                        }
                    }
                }
            }
            .padding(20)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(Color.fmBg2)
            .cornerRadius(FMRadius.lg)

            // 右侧：最近活动
            VStack(alignment: .leading, spacing: 12) {
                Text("系统信息")
                    .font(.system(size: 14, weight: .heavy))
                    .foregroundColor(.fmText)

                VStack(spacing: 8) {
                    InfoRow(label: "项目创建", value: formatDate(stats.projectCreated))
                    InfoRow(label: "最近活动", value: stats.lastActivity ?? "无")
                    InfoRow(label: "总词数", value: "\(stats.totalWords)")
                    InfoRow(label: "分块数", value: "\(stats.totalChunks)")
                    InfoRow(label: "报告数", value: "\(stats.reportsGenerated)")
                    InfoRow(label: "维度数", value: "\(stats.totalDimensions)")
                }
            }
            .padding(20)
            .frame(width: 280)
            .background(Color.fmBg2)
            .cornerRadius(FMRadius.lg)
        }
    }

    // MARK: - Loading View
    private var loadingView: some View {
        VStack(spacing: 16) {
            ProgressView()
                .scaleEffect(1.2)
            Text("加载中...")
                .font(.system(size: 14))
                .foregroundColor(Color.fmText3)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .padding(100)
    }

    // MARK: - Empty State
    private var emptyStateView: some View {
        VStack(spacing: 20) {
            Image(systemName: "chart.bar.doc.horizontal")
                .font(.system(size: 56))
                .foregroundColor(Color.fmText3.opacity(0.5))

            VStack(spacing: 8) {
                Text("无法加载概览数据")
                    .font(.system(size: 18, weight: .semibold))
                    .foregroundColor(Color.fmText)

                if let error = dashboardViewModel.errorMessage {
                    Text(error)
                        .font(.system(size: 14))
                        .foregroundColor(Color.fmText3)
                }
            }

            Button(action: {
                Task { await loadData() }
            }) {
                Text("重试")
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(.white)
                    .padding(.horizontal, 20)
                    .padding(.vertical, 10)
                    .background(Color.fmA1)
                    .cornerRadius(8)
            }
            .buttonStyle(PlainButtonStyle())
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .padding(100)
    }

    // MARK: - Load Data
    private func loadData() async {
        await dashboardViewModel.loadAllData(projectId: projectId)
    }

    private func formatDate(_ dateString: String) -> String {
        let formatter = ISO8601DateFormatter()
        if let date = formatter.date(from: dateString) {
            let displayFormatter = DateFormatter()
            displayFormatter.dateFormat = "yyyy-MM-dd"
            return displayFormatter.string(from: date)
        }
        return dateString
    }

    private func fontSize(_ weight: Double) -> CGFloat {
        10 + (weight * 6)
    }

    private func opacity(_ weight: Double) -> Double {
        0.08 + (weight * 0.15)
    }
}

// MARK: - Hero Stat
struct HeroStat: View {
    let value: String
    let label: String

    var body: some View {
        VStack(spacing: 4) {
            Text(value)
                .font(.system(size: 20, weight: .heavy))
                .foregroundColor(.fmText)
            Text(label)
                .font(.system(size: 10))
                .foregroundColor(.fmText3)
                .tracking(0.03)
        }
    }
}

// MARK: - Stat Card
struct StatCard: View {
    let icon: String
    let label: String
    let value: String
    let delta: String
    let theme: StatTheme

    enum StatTheme {
        case a1, a2, a3, a4, a5

        var color: Color {
            switch self {
            case .a1: return .fmA1
            case .a2: return .fmA2
            case .a3: return .fmA3
            case .a4: return .fmA4
            case .a5: return .fmA5
            }
        }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack(spacing: 10) {
                Image(systemName: icon)
                    .font(.system(size: 18, weight: .medium))
                    .foregroundColor(theme.color)

                Spacer()
            }

            Text(value)
                .font(.system(size: 28, weight: .heavy))
                .foregroundColor(.fmText)

            Text(label)
                .font(.system(size: 11, weight: .semibold))
                .foregroundColor(.fmText2)
                .tracking(0.02)

            Text(delta)
                .font(.system(size: 10))
                .foregroundColor(.fmText3)
        }
        .padding(EdgeInsets(top: 18, leading: 18, bottom: 18, trailing: 18))
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(
            RoundedRectangle(cornerRadius: FMRadius.lg)
                .fill(theme.color.opacity(0.06))
        )
        .overlay(
            RoundedRectangle(cornerRadius: FMRadius.lg)
                .strokeBorder(theme.color.opacity(0.15), lineWidth: 1)
        )
    }
}

