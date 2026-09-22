"""
项目列表视图 - 严格遵循设计标准
参考: Donezo Dashboard + Succulents 配色
"""
import SwiftUI

// MARK: - Projects View Model
class ProjectsViewModel: ObservableObject {
    @Published var projects: [ProjectItem] = [
        ProjectItem(
            name: "数据分析项目",
            description: "综合数据分析工作流程，包含数据收集、处理和可视化",
            status: "活跃",
            color: Color.fmPrimary,
            members: 5,
            tasks: 24,
            completedTasks: 18,
            updated: "2小时前"
        ),
        ProjectItem(
            name: "机器学习管道",
            description: "端到端机器学习数据处理管道",
            status: "进行中",
            color: Color.fmSecondary,
            members: 3,
            tasks: 18,
            completedTasks: 12,
            updated: "5小时前"
        ),
        ProjectItem(
            name: "研究文档库",
            description: "学术研究知识管理系统",
            status: "活跃",
            color: Color.fmWarning,
            members: 7,
            tasks: 32,
            completedTasks: 28,
            updated: "1天前"
        ),
        ProjectItem(
            name: "客户数据整合",
            description: "多源客户数据整合与分析",
            status: "计划中",
            color: Color.fmInfo,
            members: 4,
            tasks: 15,
            completedTasks: 5,
            updated: "3天前"
        ),
        ProjectItem(
            name: "报告自动化",
            description: "自动化报告生成系统",
            status: "活跃",
            color: Color(hex: "9FAC24"),
            members: 2,
            tasks: 12,
            completedTasks: 10,
            updated: "12小时前"
        ),
        ProjectItem(
            name: "知识图谱构建",
            description: "企业知识图谱构建项目",
            status: "进行中",
            color: Color(hex: "6FA7B6"),
            members: 6,
            tasks: 28,
            completedTasks: 15,
            updated: "6小时前"
        )
    ]
}

// MARK: - Main Projects View
struct StandardProjectsView: View {
    @StateObject private var viewModel = ProjectsViewModel()
    @State private var searchText = ""

    var body: some View {
        ScrollView {
            VStack(spacing: 24) {
                // 页面标题区域
                headerSection
                    .padding(.horizontal, 24)

                // 搜索和过滤栏
                searchFilterSection
                    .padding(.horizontal, 24)

                // 项目卡片网格（3列）
                projectsGridSection
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
                Text("项目")
                    .font(.system(size: 32, weight: .bold))
                    .foregroundColor(.fmTextPrimary)

                Text("管理您的知识项目")
                    .font(.system(size: 16, weight: .regular))
                    .foregroundColor(.fmTextSecondary)
            }

            Spacer()

            Button(action: {}) {
                HStack(spacing: 6) {
                    Image(systemName: "plus")
                        .font(.system(size: 14))
                    Text("新建项目")
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

    // MARK: - Search and Filter Section
    private var searchFilterSection: some View {
        HStack(spacing: 12) {
            HStack(spacing: 8) {
                Image(systemName: "magnifyingglass")
                    .font(.system(size: 14))
                    .foregroundColor(.fmTextTertiary)

                TextField("搜索项目...", text: $searchText)
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
                Button("全部项目") {}
                Button("活跃项目") {}
                Button("进行中") {}
                Button("已完成") {}
            } label: {
                HStack(spacing: 6) {
                    Text("状态")
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

            Menu {
                Button("最近更新") {}
                Button("名称") {}
                Button("成员数") {}
            } label: {
                HStack(spacing: 6) {
                    Text("排序")
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

    // MARK: - Projects Grid Section
    private var projectsGridSection: some View {
        LazyVGrid(
            columns: Array(repeating: GridItem(.flexible(), spacing: 16), count: 3),
            spacing: 16
        ) {
            ForEach(viewModel.projects) { project in
                ProjectCard(project: project)
            }
        }
    }
}

// MARK: - Project Card Component
struct ProjectCard: View {
    let project: ProjectItem
    @State private var isHovered = false

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            // 顶部：图标 + 状态
            HStack {
                ZStack {
                    RoundedRectangle(cornerRadius: 12)
                        .fill(project.color.opacity(0.1))
                        .frame(width: 48, height: 48)

                    Image(systemName: "folder.fill")
                        .font(.system(size: 20))
                        .foregroundColor(project.color)
                }

                Spacer()

                Text(project.status)
                    .font(.system(size: 12, weight: .medium))
                    .foregroundColor(statusColor)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(statusColor.opacity(0.1))
                    .cornerRadius(12)
            }

            // 中部：项目名称和描述
            VStack(alignment: .leading, spacing: 8) {
                Text(project.name)
                    .font(.system(size: 18, weight: .semibold))
                    .foregroundColor(.fmTextPrimary)
                    .lineLimit(1)

                Text(project.description)
                    .font(.system(size: 14))
                    .foregroundColor(.fmTextSecondary)
                    .lineLimit(2)
                    .frame(height: 40, alignment: .top)
            }

            // 进度条
            VStack(alignment: .leading, spacing: 6) {
                HStack {
                    Text("进度")
                        .font(.system(size: 12))
                        .foregroundColor(.fmTextTertiary)
                    Spacer()
                    Text("\(project.completedTasks)/\(project.tasks)")
                        .font(.system(size: 12, weight: .medium))
                        .foregroundColor(.fmTextSecondary)
                }

                GeometryReader { geometry in
                    ZStack(alignment: .leading) {
                        RoundedRectangle(cornerRadius: 4)
                            .fill(Color.fmGray200)
                            .frame(height: 6)

                        RoundedRectangle(cornerRadius: 4)
                            .fill(project.color)
                            .frame(width: geometry.size.width * progressPercentage, height: 6)
                    }
                }
                .frame(height: 6)
            }

            Divider()

            // 底部：成员、任务、更新时间
            HStack(spacing: 16) {
                Label("\(project.members)", systemImage: "person.2.fill")
                    .font(.system(size: 12))
                    .foregroundColor(.fmTextTertiary)

                Label("\(project.tasks)", systemImage: "checkmark.circle.fill")
                    .font(.system(size: 12))
                    .foregroundColor(.fmTextTertiary)

                Spacer()

                Text(project.updated)
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
            // 导航到项目详情
        }
    }

    private var statusColor: Color {
        switch project.status {
        case "活跃": return .fmSuccess
        case "进行中": return .fmInfo
        case "计划中": return .fmWarning
        case "已完成": return .fmTextTertiary
        default: return .fmTextTertiary
        }
    }

    private var progressPercentage: CGFloat {
        guard project.tasks > 0 else { return 0 }
        return CGFloat(project.completedTasks) / CGFloat(project.tasks)
    }
}

// MARK: - Data Models
struct ProjectItem: Identifiable {
    let id = UUID()
    let name: String
    let description: String
    let status: String
    let color: Color
    let members: Int
    let tasks: Int
    let completedTasks: Int
    let updated: String
}

// MARK: - Preview
#Preview {
    StandardProjectsView()
}
