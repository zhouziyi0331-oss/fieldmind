import SwiftUI

struct ProjectSwitcher: View {
    @EnvironmentObject var appState: AppState
    @State private var showProjectList = false
    @State private var isHovered = false

    var body: some View {
        Button(action: {
            showProjectList.toggle()
        }) {
            HStack(spacing: 8) {
                // 项目图标
                ZStack {
                    Circle()
                        .fill(currentProjectColor)
                        .frame(width: 28, height: 28)

                    Image(systemName: "folder.fill")
                        .font(.system(size: 12))
                        .foregroundColor(.white)
                }

                // 项目信息
                VStack(alignment: .leading, spacing: 2) {
                    Text(appState.currentProject?.name ?? "选择项目")
                        .font(.system(size: 13, weight: .semibold))
                        .foregroundColor(.fmText)
                        .lineLimit(1)

                    if let project = appState.currentProject {
                        Text("\(project.documentCount) 文档 • \(project.keywordCount) 关键词")
                            .font(.system(size: 10))
                            .foregroundColor(.fmText3)
                    } else {
                        Text("未选择项目")
                            .font(.system(size: 10))
                            .foregroundColor(.fmText3)
                    }
                }

                Spacer()

                // 下拉图标
                Image(systemName: showProjectList ? "chevron.up" : "chevron.down")
                    .font(.system(size: 10, weight: .medium))
                    .foregroundColor(.fmText3)
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
            .background(isHovered ? Color.fmBg2 : Color.fmSurface)
            .cornerRadius(8)
        }
        .buttonStyle(.plain)
        .onHover { hovering in
            isHovered = hovering
        }
        .popover(isPresented: $showProjectList) {
            ProjectListPopover()
                .environmentObject(appState)
                .frame(width: 320, height: 480)
        }
    }

    private var currentProjectColor: Color {
        guard let project = appState.currentProject else {
            return .fmText4
        }
        // 根据项目ID生成颜色
        let colors: [Color] = [.fmA1, .green, .purple, .orange, .red, .pink]
        return colors[project.id % colors.count]
    }
}

// MARK: - Project List Popover
struct ProjectListPopover: View {
    @EnvironmentObject var appState: AppState
    @State private var searchText = ""
    @State private var isLoading = false

    var filteredProjects: [Project] {
        if searchText.isEmpty {
            return appState.projects
        }
        return appState.projects.filter { project in
            project.name.localizedCaseInsensitiveContains(searchText)
        }
    }

    var body: some View {
        VStack(spacing: 0) {
            // 头部
            headerView
                .padding(16)
                .background(Color.fmSurface)

            Divider()

            // 搜索框
            searchBar
                .padding(12)

            // 项目列表
            if isLoading {
                Spacer()
                ProgressView()
                    .scaleEffect(0.8)
                Spacer()
            } else if filteredProjects.isEmpty {
                emptyStateView
            } else {
                projectListView
            }

            Divider()

            // 底部操作
            footerView
                .padding(12)
                .background(Color.fmSurface)
        }
        .background(Color.fmBg)
        .onAppear {
            loadProjects()
        }
    }

    private var headerView: some View {
        HStack {
            Text("切换项目")
                .font(.system(size: 14, weight: .bold))
                .foregroundColor(.fmText)

            Spacer()

            Text("\(appState.projects.count) 个项目")
                .font(.system(size: 11))
                .foregroundColor(.fmText3)
        }
    }

    private var searchBar: some View {
        HStack(spacing: 8) {
            Image(systemName: "magnifyingglass")
                .font(.system(size: 12))
                .foregroundColor(.fmText3)

            TextField("搜索项目...", text: $searchText)
                .textFieldStyle(.plain)
                .font(.system(size: 12))
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 6)
        .background(Color.fmBg2)
        .cornerRadius(6)
    }

    private var projectListView: some View {
        ScrollView {
            LazyVStack(spacing: 4) {
                ForEach(filteredProjects) { project in
                    ProjectListItem(project: project)
                }
            }
            .padding(.horizontal, 8)
        }
    }

    private var emptyStateView: some View {
        VStack(spacing: 12) {
            Image(systemName: "folder.badge.questionmark")
                .font(.system(size: 32))
                .foregroundColor(.fmText4)

            Text(searchText.isEmpty ? "暂无项目" : "未找到匹配的项目")
                .font(.system(size: 12))
                .foregroundColor(.fmText3)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    private var footerView: some View {
        Button(action: {
            appState.navigateTo(.projects)
        }) {
            HStack(spacing: 6) {
                Image(systemName: "plus.circle.fill")
                    .font(.system(size: 12))
                Text("新建项目")
                    .font(.system(size: 12, weight: .medium))
            }
            .foregroundColor(.fmA1)
            .frame(maxWidth: .infinity)
            .padding(.vertical, 8)
            .background(Color.fmA1.opacity(0.1))
            .cornerRadius(6)
        }
        .buttonStyle(.plain)
    }

    private func loadProjects() {
        isLoading = true

        Task {
            do {
                let projects = try await ProjectService.shared.listProjects()
                await MainActor.run {
                    appState.projects = projects
                    isLoading = false
                }
            } catch {
                await MainActor.run {
                    isLoading = false
                    appState.showToast(message: "加载项目失败：\(error.localizedDescription)", type: .error)
                }
            }
        }
    }
}

// MARK: - Project List Item
struct ProjectListItem: View {
    @EnvironmentObject var appState: AppState
    let project: Project
    @State private var isHovered = false

    private var isSelected: Bool {
        appState.currentProject?.id == project.id
    }

    var body: some View {
        Button(action: {
            selectProject()
        }) {
            HStack(spacing: 10) {
                // 项目颜色指示器
                ZStack {
                    Circle()
                        .fill(projectColor)
                        .frame(width: 32, height: 32)

                    Image(systemName: "folder.fill")
                        .font(.system(size: 13))
                        .foregroundColor(.white)
                }

                // 项目信息
                VStack(alignment: .leading, spacing: 4) {
                    Text(project.name)
                        .font(.system(size: 12, weight: .medium))
                        .foregroundColor(.fmText)
                        .lineLimit(1)

                    HStack(spacing: 8) {
                        Label("\(project.documentCount)", systemImage: "doc")
                        Label("\(project.keywordCount)", systemImage: "tag")
                    }
                    .font(.system(size: 10))
                    .foregroundColor(.fmText3)
                }

                Spacer()

                // 选中指示器
                if isSelected {
                    Image(systemName: "checkmark.circle.fill")
                        .font(.system(size: 16))
                        .foregroundColor(.fmA1)
                }
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 10)
            .background(isSelected ? Color.fmA1.opacity(0.1) : (isHovered ? Color.fmBg2 : Color.clear))
            .cornerRadius(8)
        }
        .buttonStyle(.plain)
        .onHover { hovering in
            isHovered = hovering
        }
    }

    private var projectColor: Color {
        let colors: [Color] = [.fmA1, .green, .purple, .orange, .red, .pink]
        return colors[project.id % colors.count]
    }

    private func selectProject() {
        appState.currentProject = project
        appState.navigateTo(.overview)
        appState.showToast(message: "已切换到项目：\(project.name)", type: .success)
    }
}
