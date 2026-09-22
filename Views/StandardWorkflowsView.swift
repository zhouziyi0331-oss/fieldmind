"""
工作流列表视图 - 严格遵循设计标准
参考: Donezo Dashboard + Succulents 配色
"""
import SwiftUI

// MARK: - Workflows View Model
class WorkflowsViewModel: ObservableObject {
    @Published var workflows: [WorkflowItem] = [
        WorkflowItem(
            name: "数据处理管道",
            description: "完整的6步数据处理工作流：收集、处理、理解、分析、协作、复用",
            status: "活跃",
            color: Color.fmPrimary,
            runs: 142,
            successRate: 94,
            avgDuration: "3.5小时",
            lastRun: "2小时前"
        ),
        WorkflowItem(
            name: "文档智能分析",
            description: "自动化文档分析和知识提取工作流",
            status: "运行中",
            color: Color.fmSecondary,
            runs: 89,
            successRate: 91,
            avgDuration: "1.2小时",
            lastRun: "进行中"
        ),
        WorkflowItem(
            name: "月度报告生成",
            description: "自动生成月度分析报告和可视化",
            status: "已完成",
            color: Color.fmWarning,
            runs: 28,
            successRate: 100,
            avgDuration: "45分钟",
            lastRun: "1天前"
        ),
        WorkflowItem(
            name: "知识图谱构建",
            description: "从多源数据构建企业知识图谱",
            status: "活跃",
            color: Color.fmInfo,
            runs: 56,
            successRate: 88,
            avgDuration: "2.8小时",
            lastRun: "5小时前"
        ),
        WorkflowItem(
            name: "实时数据同步",
            description: "多系统间的实时数据同步工作流",
            status: "运行中",
            color: Color(hex: "9FAC24"),
            runs: 324,
            successRate: 96,
            avgDuration: "15分钟",
            lastRun: "进行中"
        ),
        WorkflowItem(
            name: "客户行为分析",
            description: "客户数据收集和行为模式分析",
            status: "计划中",
            color: Color(hex: "6FA7B6"),
            runs: 0,
            successRate: 0,
            avgDuration: "预计2小时",
            lastRun: "未运行"
        )
    ]
}

// MARK: - Main Workflows View
struct StandardWorkflowsView: View {
    @StateObject private var viewModel = WorkflowsViewModel()
    @State private var searchText = ""
    @State private var selectedStatus = "全部"

    var body: some View {
        ScrollView {
            VStack(spacing: 24) {
                // 页面标题区域
                headerSection
                    .padding(.horizontal, 24)

                // 搜索和过滤栏
                searchFilterSection
                    .padding(.horizontal, 24)

                // 工作流卡片网格（3列）
                workflowsGridSection
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
                Text("工作流")
                    .font(.system(size: 32, weight: .bold))
                    .foregroundColor(.fmTextPrimary)

                Text("管理和执行自动化工作流")
                    .font(.system(size: 16, weight: .regular))
                    .foregroundColor(.fmTextSecondary)
            }

            Spacer()

            Button(action: {}) {
                HStack(spacing: 6) {
                    Image(systemName: "plus")
                        .font(.system(size: 14))
                    Text("新建工作流")
                        .font(.system(size: 14, weight: .medium))
                }
                .foregroundColor(.white)
                .padding(.horizontal, 16)
                .padding(.vertical, 10)
                .background(Color.fmSecondary)
                .cornerRadius(8)
            }
            .buttonStyle(ScaleButtonStyle())
        }
    }

    // MARK: - Search and Filter Section
    private var searchFilterSection: some View {
        HStack(spacing: 12) {
            HStack(spacing: 8) {
                Image(systemName: "magnifyingglass")
                    .font(.system(size: 14))
                    .foregroundColor(.fmTextTertiary)

                TextField("搜索工作流...", text: $searchText)
                    .font(.system(size: 14))
                    .textFieldStyle(.plain)
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 10)
            .background(Color.white)
            .cornerRadius(8)
            .overlay(
                RoundedRectangle(cornerRadius: 8)
                    .stroke(Color.fmBorder, lineWidth: 1)
            )

            Menu {
                Button("全部") { selectedStatus = "全部" }
                Button("活跃") { selectedStatus = "活跃" }
                Button("运行中") { selectedStatus = "运行中" }
                Button("已完成") { selectedStatus = "已完成" }
                Button("计划中") { selectedStatus = "计划中" }
            } label: {
                HStack(spacing: 6) {
                    Text(selectedStatus)
                        .font(.system(size: 14, weight: .medium))
                    Image(systemName: "chevron.down")
                        .font(.system(size: 12))
                }
                .foregroundColor(.fmTextPrimary)
                .padding(.horizontal, 16)
                .padding(.vertical, 10)
                .background(Color.white)
                .cornerRadius(8)
                .overlay(
                    RoundedRectangle(cornerRadius: 8)
                        .stroke(Color.fmBorder, lineWidth: 1)
                )
            }
        }
    }

    // MARK: - Workflows Grid Section
    private var workflowsGridSection: some View {
        LazyVGrid(
            columns: Array(repeating: GridItem(.flexible(), spacing: 16), count: 3),
            spacing: 16
        ) {
            ForEach(viewModel.workflows) { workflow in
                WorkflowCard(workflow: workflow)
            }
        }
    }
}

// MARK: - Workflow Card Component
struct WorkflowCard: View {
    let workflow: WorkflowItem
    @State private var isHovered = false

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            // 顶部：图标 + 状态
            HStack {
                ZStack {
                    RoundedRectangle(cornerRadius: 12)
                        .fill(workflow.color.opacity(0.1))
                        .frame(width: 48, height: 48)

                    Image(systemName: "bolt.fill")
                        .font(.system(size: 20))
                        .foregroundColor(workflow.color)
                }

                Spacer()

                HStack(spacing: 4) {
                    if workflow.status == "运行中" {
                        Circle()
                            .fill(statusColor)
                            .frame(width: 6, height: 6)
                    }

                    Text(workflow.status)
                        .font(.system(size: 12, weight: .medium))
                        .foregroundColor(statusColor)
                }
                .padding(.horizontal, 8)
                .padding(.vertical, 4)
                .background(statusColor.opacity(0.1))
                .cornerRadius(12)
            }

            // 中部：名称和描述
            VStack(alignment: .leading, spacing: 8) {
                Text(workflow.name)
                    .font(.system(size: 18, weight: .semibold))
                    .foregroundColor(.fmTextPrimary)
                    .lineLimit(1)

                Text(workflow.description)
                    .font(.system(size: 14))
                    .foregroundColor(.fmTextSecondary)
                    .lineLimit(2)
                    .frame(height: 40, alignment: .top)
            }

            // 统计信息
            HStack(spacing: 12) {
                StatBadge(label: "运行", value: "\(workflow.runs)")
                StatBadge(label: "成功率", value: "\(workflow.successRate)%")
            }

            Divider()

            // 底部：时长和最后运行
            HStack {
                HStack(spacing: 4) {
                    Image(systemName: "clock.fill")
                        .font(.system(size: 11))
                    Text(workflow.avgDuration)
                        .font(.system(size: 12))
                }
                .foregroundColor(.fmTextTertiary)

                Spacer()

                Text("最后运行: \(workflow.lastRun)")
                    .font(.system(size: 11))
                    .foregroundColor(.fmTextTertiary)
            }
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
        .onTapGesture {
            // 导航到工作流详情
        }
    }

    private var statusColor: Color {
        switch workflow.status {
        case "活跃": return .fmSuccess
        case "运行中": return .fmInfo
        case "已完成": return .fmTextTertiary
        case "计划中": return .fmWarning
        default: return .fmTextTertiary
        }
    }
}

// MARK: - Stat Badge Component
struct StatBadge: View {
    let label: String
    let value: String

    var body: some View {
        HStack(spacing: 4) {
            Text(label)
                .font(.system(size: 11))
                .foregroundColor(.fmTextTertiary)
            Text(value)
                .font(.system(size: 12, weight: .semibold))
                .foregroundColor(.fmTextPrimary)
        }
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .background(Color.fmBgSecondary)
        .cornerRadius(6)
    }
}

// MARK: - Data Models
struct WorkflowItem: Identifiable {
    let id = UUID()
    let name: String
    let description: String
    let status: String
    let color: Color
    let runs: Int
    let successRate: Int
    let avgDuration: String
    let lastRun: String
}

// MARK: - Preview
#Preview {
    StandardWorkflowsView()
}
