import SwiftUI

struct ProjectsPage: View {
    @EnvironmentObject var appState: AppState
    @State private var searchText = ""
    @State private var sortBy: SortOption = .recent
    @State private var viewMode: ViewMode = .grid

    enum SortOption: String, CaseIterable {
        case recent = "最近"
        case name = "名称"
        case materials = "材料数"
        case keywords = "关键词"
    }

    enum ViewMode {
        case grid
        case list
    }

    var filteredProjects: [Project] {
        var result = appState.projects

        // 搜索筛选
        if !searchText.isEmpty {
            result = result.filter {
                $0.name.localizedCaseInsensitiveContains(searchText) ||
                $0.description.localizedCaseInsensitiveContains(searchText)
            }
        }

        // 排序
        switch sortBy {
        case .recent:
            result.sort { $0.createdAt > $1.createdAt }
        case .name:
            result.sort { $0.name < $1.name }
        case .materials:
            result.sort { $0.stats.materialsCount > $1.stats.materialsCount }
        case .keywords:
            result.sort { $0.stats.keywordsCount > $1.stats.keywordsCount }
        }

        return result
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            // 页头
            sectionHeader

            // 工具栏
            toolbar

            Spacer().frame(height: 16)

            // 项目列表
            if filteredProjects.isEmpty {
                emptyState
            } else {
                if viewMode == .grid {
                    projectsGrid
                } else {
                    projectsList
                }
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

                Text("项目管理")
                    .font(.system(size: 14, weight: .heavy))
                    .foregroundColor(.fmText)
                    .tracking(-0.01)
            }

            Text("管理所有研究项目，快速切换工作空间")
                .font(.system(size: 10))
                .foregroundColor(.fmText3)
                .tracking(0.02)
        }
        .padding(.bottom, 16)
    }

    // MARK: - Toolbar
    private var toolbar: some View {
        HStack(spacing: 10) {
            // 搜索框
            HStack(spacing: 8) {
                Image(systemName: "magnifyingglass")
                    .font(.system(size: 11))
                    .foregroundColor(.fmText3)

                TextField("搜索项目...", text: $searchText)
                    .textFieldStyle(.plain)
                    .font(.system(size: 12))
                    .foregroundColor(.fmText)

                if !searchText.isEmpty {
                    Button(action: { searchText = "" }) {
                        Image(systemName: "xmark.circle.fill")
                            .font(.system(size: 11))
                            .foregroundColor(.fmText4)
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(EdgeInsets(top: 7, leading: 12, bottom: 7, trailing: 12))
            .background(Color.fmSurface)
            .cornerRadius(8)
            .overlay(
                RoundedRectangle(cornerRadius: 8)
                    .stroke(Color.fmBorder2, lineWidth: 1)
            )
            .frame(width: 280)

            // 排序选择
            Menu {
                ForEach(SortOption.allCases, id: \.self) { option in
                    Button(action: { sortBy = option }) {
                        HStack {
                            Text(option.rawValue)
                            if sortBy == option {
                                Image(systemName: "checkmark")
                            }
                        }
                    }
                }
            } label: {
                HStack(spacing: 6) {
                    Image(systemName: "arrow.up.arrow.down")
                        .font(.system(size: 10))
                    Text(sortBy.rawValue)
                        .font(.system(size: 11))
                }
                .foregroundColor(.fmText2)
                .padding(EdgeInsets(top: 7, leading: 12, bottom: 7, trailing: 12))
                .background(Color.fmSurface)
                .cornerRadius(8)
                .overlay(
                    RoundedRectangle(cornerRadius: 8)
                        .stroke(Color.fmBorder2, lineWidth: 1)
                )
            }

            // 视图切换
            HStack(spacing: 2) {
                Button(action: { viewMode = .grid }) {
                    Image(systemName: "square.grid.2x2")
                        .font(.system(size: 11))
                        .foregroundColor(viewMode == .grid ? .fmA1 : .fmText3)
                        .frame(width: 32, height: 28)
                        .background(viewMode == .grid ? Color.fmA1Dim : Color.clear)
                        .cornerRadius(6)
                }
                .buttonStyle(.plain)

                Button(action: { viewMode = .list }) {
                    Image(systemName: "list.bullet")
                        .font(.system(size: 11))
                        .foregroundColor(viewMode == .list ? .fmA1 : .fmText3)
                        .frame(width: 32, height: 28)
                        .background(viewMode == .list ? Color.fmA1Dim : Color.clear)
                        .cornerRadius(6)
                }
                .buttonStyle(.plain)
            }
            .padding(2)
            .background(Color.fmSurface)
            .cornerRadius(8)
            .overlay(
                RoundedRectangle(cornerRadius: 8)
                    .stroke(Color.fmBorder2, lineWidth: 1)
            )

            Spacer()

            // 统计信息
            HStack(spacing: 14) {
                StatChip(label: "总计", value: "\(appState.projects.count)", color: .fmA1)
                StatChip(label: "已筛选", value: "\(filteredProjects.count)", color: .fmA2)
            }

            // 新建项目按钮
            Button(action: {
                appState.navigateTo(.newproject)
            }) {
                HStack(spacing: 5) {
                    Image(systemName: "plus")
                        .font(.system(size: 10, weight: .bold))
                    Text("新建")
                        .font(.system(size: 11, weight: .semibold))
                }
            }
            .buttonStyle(FMButtonStyle(style: .primary, size: .small))
        }
    }

    // MARK: - Projects Grid
    private var projectsGrid: some View {
        ScrollView {
            LazyVGrid(
                columns: [
                    GridItem(.adaptive(minimum: 300, maximum: 360), spacing: 14)
                ],
                spacing: 14
            ) {
                ForEach(filteredProjects) { project in
                    ProjectGridCard(project: project)
                }
            }
        }
    }

    // MARK: - Projects List
    private var projectsList: some View {
        ScrollView {
            VStack(spacing: 0) {
                ForEach(filteredProjects) { project in
                    ProjectListRow(project: project)
                    if project.id != filteredProjects.last?.id {
                        Divider()
                            .background(Color.fmBorder)
                            .padding(.horizontal, 16)
                    }
                }
            }
        }
    }

    // MARK: - Empty State
    private var emptyState: some View {
        VStack(spacing: 16) {
            ZStack {
                Circle()
                    .fill(Color.fmA1.opacity(0.12))
                    .frame(width: 80, height: 80)

                Image(systemName: "folder.fill")
                    .font(.system(size: 36))
                    .foregroundColor(.fmA1.opacity(0.5))
            }

            VStack(spacing: 6) {
                Text(searchText.isEmpty ? "还没有项目" : "未找到匹配的项目")
                    .font(.system(size: 15, weight: .bold))
                    .foregroundColor(.fmText)

                Text(searchText.isEmpty ? "创建第一个项目开始使用 FieldMind" : "尝试调整搜索条件")
                    .font(.system(size: 11))
                    .foregroundColor(.fmText3)
            }

            if searchText.isEmpty {
                Button(action: {
                    appState.navigateTo(.newproject)
                }) {
                    HStack(spacing: 6) {
                        Image(systemName: "plus")
                            .font(.system(size: 10, weight: .bold))
                        Text("新建项目")
                            .font(.system(size: 11, weight: .semibold))
                    }
                }
                .buttonStyle(FMButtonStyle(style: .primary, size: .medium))
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

// MARK: - Project Grid Card
struct ProjectGridCard: View {
    @EnvironmentObject var appState: AppState
    let project: Project
    @State private var isHovered = false

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            // 头部：项目名称
            VStack(alignment: .leading, spacing: 6) {
                HStack(alignment: .top) {
                    Circle()
                        .fill(Color.fmA1)
                        .frame(width: 8, height: 8)

                    Text(project.name)
                        .font(.system(size: 13, weight: .bold))
                        .foregroundColor(.fmText)
                        .lineLimit(2)

                    Spacer()

                    Button(action: {}) {
                        Image(systemName: "ellipsis")
                            .font(.system(size: 11))
                            .foregroundColor(.fmText3)
                    }
                    .buttonStyle(.plain)
                    .opacity(isHovered ? 1 : 0)
                }

                Text(project.description)
                    .font(.system(size: 10))
                    .foregroundColor(.fmText3)
                    .lineLimit(2)
            }
            .padding(EdgeInsets(top: 16, leading: 16, bottom: 12, trailing: 16))

            Divider()
                .background(Color.fmBorder)
                .padding(.horizontal, 16)

            // 统计数据
            HStack(spacing: 20) {
                ProjectStat(icon: "doc.text", label: "材料", value: "\(project.stats.materialsCount)")
                ProjectStat(icon: "tag", label: "关键词", value: "\(project.stats.keywordsCount)")
            }
            .padding(EdgeInsets(top: 12, leading: 16, bottom: 12, trailing: 16))

            Divider()
                .background(Color.fmBorder)
                .padding(.horizontal, 16)

            // 底部：创建时间 + 操作按钮
            HStack {
                HStack(spacing: 4) {
                    Image(systemName: "clock")
                        .font(.system(size: 9))
                        .foregroundColor(.fmText4)

                    Text(formatDate(project.createdAt))
                        .font(.system(size: 9))
                        .foregroundColor(.fmText3)
                }

                Spacer()

                Button(action: {
                    appState.currentProject = project
                    appState.navigateTo(.overview)
                }) {
                    Text("打开")
                        .font(.system(size: 10, weight: .semibold))
                }
                .buttonStyle(FMButtonStyle(style: .outline, size: .small))
            }
            .padding(EdgeInsets(top: 12, leading: 16, bottom: 14, trailing: 16))
        }
        .background(Color.fmSurface)
        .cornerRadius(FMRadius.md)
        .overlay(
            RoundedRectangle(cornerRadius: FMRadius.md)
                .stroke(isHovered ? Color.fmA1.opacity(0.3) : Color.fmBorder2, lineWidth: 1)
        )
        .shadow(color: Color.black.opacity(isHovered ? 0.08 : 0.04), radius: 6, x: 0, y: 2)
        .scaleEffect(isHovered ? 1.02 : 1.0)
        .animation(.spring(response: 0.3, dampingFraction: 0.7), value: isHovered)
        .onHover { hovering in
            isHovered = hovering
        }
    }

    private func formatDate(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd"
        return formatter.string(from: date)
    }
}

// MARK: - Project List Row
struct ProjectListRow: View {
    @EnvironmentObject var appState: AppState
    let project: Project
    @State private var isHovered = false

    var body: some View {
        HStack(spacing: 16) {
            // 项目标识
            Circle()
                .fill(Color.fmA1)
                .frame(width: 10, height: 10)

            // 项目信息
            VStack(alignment: .leading, spacing: 4) {
                Text(project.name)
                    .font(.system(size: 12, weight: .semibold))
                    .foregroundColor(.fmText)

                Text(project.description)
                    .font(.system(size: 10))
                    .foregroundColor(.fmText3)
                    .lineLimit(1)
            }
            .frame(width: 280, alignment: .leading)

            // 统计数据
            HStack(spacing: 20) {
                HStack(spacing: 6) {
                    Image(systemName: "doc.text")
                        .font(.system(size: 10))
                        .foregroundColor(.fmText3)
                    Text("\(project.stats.materialsCount)")
                        .font(.system(size: 11, weight: .bold))
                        .foregroundColor(.fmText2)
                        .monospacedDigit()
                }
                .frame(width: 70)

                HStack(spacing: 6) {
                    Image(systemName: "tag")
                        .font(.system(size: 10))
                        .foregroundColor(.fmText3)
                    Text("\(project.stats.keywordsCount)")
                        .font(.system(size: 11, weight: .bold))
                        .foregroundColor(.fmText2)
                        .monospacedDigit()
                }
                .frame(width: 70)
            }

            Spacer()

            // 创建时间
            Text(formatDate(project.createdAt))
                .font(.system(size: 10))
                .foregroundColor(.fmText3)
                .frame(width: 90)

            // 操作按钮
            HStack(spacing: 8) {
                Button(action: {
                    appState.currentProject = project
                    appState.navigateTo(.overview)
                }) {
                    Text("打开")
                        .font(.system(size: 10, weight: .semibold))
                }
                .buttonStyle(FMButtonStyle(style: .outline, size: .small))

                Button(action: {}) {
                    Image(systemName: "ellipsis")
                        .font(.system(size: 11))
                        .foregroundColor(.fmText3)
                }
                .buttonStyle(.plain)
                .opacity(isHovered ? 1 : 0)
            }
        }
        .padding(EdgeInsets(top: 14, leading: 16, bottom: 14, trailing: 16))
        .background(isHovered ? Color.fmSurface : Color.clear)
        .onHover { hovering in
            isHovered = hovering
        }
    }

    private func formatDate(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd"
        return formatter.string(from: date)
    }
}

// MARK: - Stat Chip
struct StatChip: View {
    let label: String
    let value: String
    let color: Color

    var body: some View {
        HStack(spacing: 6) {
            Text(label)
                .font(.system(size: 11))
                .foregroundColor(.fmText3)

            Text(value)
                .font(.system(size: 12, weight: .bold))
                .foregroundColor(color)
                .monospacedDigit()
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 6)
        .background(color.opacity(0.08))
        .clipShape(RoundedRectangle(cornerRadius: 6))
    }
}

// MARK: - Project Stat
struct ProjectStat: View {
    let icon: String
    let label: String
    let value: String

    var body: some View {
        HStack(spacing: 6) {
            Image(systemName: icon)
                .font(.system(size: 11))
                .foregroundColor(.fmText3)

            VStack(alignment: .leading, spacing: 2) {
                Text(value)
                    .font(.system(size: 13, weight: .bold))
                    .foregroundColor(.fmText)
                    .monospacedDigit()

                Text(label)
                    .font(.system(size: 9))
                    .foregroundColor(.fmText4)
            }
        }
    }
}
