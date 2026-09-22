"""
项目列表页面 - Succulents 设计系统
"""
import SwiftUI

struct SucculentsProjectsView: View {
    @StateObject private var viewModel = ProjectsViewModel()

    var body: some View {
        ScrollView {
            VStack(spacing: 24) {
                // Header
                HStack {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("项目")
                            .font(.system(size: 32, weight: .bold))
                            .foregroundColor(.fmTextPrimary)

                        Text("管理您的知识项目")
                            .font(.system(size: 16))
                            .foregroundColor(.fmTextSecondary)
                    }

                    Spacer()

                    Button(action: {}) {
                        HStack(spacing: 6) {
                            Image(systemName: "plus")
                            Text("新建项目")
                        }
                        .font(.system(size: 14, weight: .medium))
                        .foregroundColor(.white)
                        .padding(.horizontal, 16)
                        .padding(.vertical, 10)
                        .background(Color.fmPrimary)
                        .cornerRadius(8)
                    }
                    .buttonStyle(.plain)
                }
                .padding(.horizontal, 24)

                // Projects Grid
                LazyVGrid(columns: Array(repeating: GridItem(.flexible(), spacing: 16), count: 3), spacing: 16) {
                    ForEach(viewModel.projects) { project in
                        ProjectCardView(project: project)
                    }
                }
                .padding(.horizontal, 24)
            }
            .padding(.vertical, 24)
        }
        .background(Color.fmBgSecondary)
    }
}

struct ProjectCardView: View {
    let project: ProjectItem

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                ZStack {
                    RoundedRectangle(cornerRadius: 12)
                        .fill(project.color.opacity(0.15))
                        .frame(width: 48, height: 48)

                    Image(systemName: "folder.fill")
                        .font(.system(size: 20))
                        .foregroundColor(project.color)
                }

                Spacer()

                Text(project.status)
                    .font(.system(size: 12))
                    .foregroundColor(.fmSuccess)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(Color.fmSuccess.opacity(0.1))
                    .cornerRadius(12)
            }

            Text(project.name)
                .font(.system(size: 18, weight: .semibold))
                .foregroundColor(.fmTextPrimary)

            Text(project.description)
                .font(.system(size: 14))
                .foregroundColor(.fmTextSecondary)
                .lineLimit(2)

            Divider()
                .padding(.vertical, 4)

            HStack {
                Label("\(project.members)", systemImage: "person.2.fill")
                    .font(.system(size: 12))
                    .foregroundColor(.fmTextTertiary)

                Spacer()

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
        .background(Color.fmBgElevated)
        .cornerRadius(12)
        .fmCardShadow()
    }
}

class ProjectsViewModel: ObservableObject {
    @Published var projects: [ProjectItem] = [
        ProjectItem(name: "数据分析项目", description: "综合数据分析工作流", status: "活跃", color: Color.fmPrimary, members: 5, tasks: 24, updated: "2小时前"),
        ProjectItem(name: "机器学习管道", description: "机器学习数据处理", status: "进行中", color: Color.fmSecondary, members: 3, tasks: 18, updated: "5小时前"),
        ProjectItem(name: "研究文档库", description: "研究知识库", status: "活跃", color: Color.fmWarning, members: 7, tasks: 32, updated: "1天前")
    ]
}

struct ProjectItem: Identifiable {
    let id = UUID()
    let name: String
    let description: String
    let status: String
    let color: Color
    let members: Int
    let tasks: Int
    let updated: String
}

#Preview {
    SucculentsProjectsView()
}
