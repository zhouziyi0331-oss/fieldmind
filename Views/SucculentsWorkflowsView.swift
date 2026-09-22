"""
工作流列表页面 - Succulents 设计系统
"""
import SwiftUI

struct SucculentsWorkflowsView: View {
    @StateObject private var viewModel = WorkflowsViewModel()

    var body: some View {
        ScrollView {
            VStack(spacing: 24) {
                // Header
                HStack {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("工作流")
                            .font(.system(size: 32, weight: .bold))
                            .foregroundColor(.fmTextPrimary)

                        Text("管理和执行工作流")
                            .font(.system(size: 16))
                            .foregroundColor(.fmTextSecondary)
                    }

                    Spacer()

                    Button(action: {}) {
                        HStack(spacing: 6) {
                            Image(systemName: "plus")
                            Text("新建工作流")
                        }
                        .font(.system(size: 14, weight: .medium))
                        .foregroundColor(.white)
                        .padding(.horizontal, 16)
                        .padding(.vertical, 10)
                        .background(Color.fmSecondary)
                        .cornerRadius(8)
                    }
                    .buttonStyle(.plain)
                }
                .padding(.horizontal, 24)

                // Workflows Grid
                LazyVGrid(columns: Array(repeating: GridItem(.flexible(), spacing: 16), count: 3), spacing: 16) {
                    ForEach(viewModel.workflows) { workflow in
                        WorkflowCardView(workflow: workflow)
                    }
                }
                .padding(.horizontal, 24)
            }
            .padding(.vertical, 24)
        }
        .background(Color.fmBgSecondary)
    }
}

struct WorkflowCardView: View {
    let workflow: WorkflowItem

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                ZStack {
                    RoundedRectangle(cornerRadius: 12)
                        .fill(workflow.color.opacity(0.15))
                        .frame(width: 48, height: 48)

                    Image(systemName: "bolt.fill")
                        .font(.system(size: 20))
                        .foregroundColor(workflow.color)
                }

                Spacer()

                Text(workflow.status)
                    .font(.system(size: 12))
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(statusColor(workflow.status).opacity(0.1))
                    .foregroundColor(statusColor(workflow.status))
                    .cornerRadius(12)
            }

            Text(workflow.name)
                .font(.system(size: 18, weight: .semibold))
                .foregroundColor(.fmTextPrimary)

            Text(workflow.description)
                .font(.system(size: 14))
                .foregroundColor(.fmTextSecondary)
                .lineLimit(2)

            Divider()
                .padding(.vertical, 4)

            HStack {
                Text("\(workflow.runs) 次运行")
                    .font(.system(size: 12))
                    .foregroundColor(.fmTextTertiary)

                Spacer()

                Text("最后运行: 2小时前")
                    .font(.system(size: 11))
                    .foregroundColor(.fmTextTertiary)
            }
        }
        .padding(20)
        .background(Color.fmBgElevated)
        .cornerRadius(12)
        .fmCardShadow()
    }

    func statusColor(_ status: String) -> Color {
        switch status {
        case "活跃": return .fmSuccess
        case "运行中": return .fmInfo
        default: return .fmTextTertiary
        }
    }
}

class WorkflowsViewModel: ObservableObject {
    @Published var workflows: [WorkflowItem] = [
        WorkflowItem(name: "数据处理管道", description: "完整的6步工作流", status: "活跃", color: Color.fmPrimary, runs: 42),
        WorkflowItem(name: "文档分析", description: "自动化文档处理", status: "运行中", color: Color.fmSecondary, runs: 28),
        WorkflowItem(name: "知识构建器", description: "构建知识库", status: "已完成", color: Color.fmWarning, runs: 15)
    ]
}

struct WorkflowItem: Identifiable {
    let id = UUID()
    let name: String
    let description: String
    let status: String
    let color: Color
    let runs: Int
}

#Preview {
    SucculentsWorkflowsView()
}
