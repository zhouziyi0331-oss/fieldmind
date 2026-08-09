import SwiftUI

struct ProjectsView: View {
    @EnvironmentObject var appState: AppState
    @State private var projects: [Project] = []
    @State private var isLoading = true
    @State private var showCreateDialog = false
    @State private var selectedProject: Project?

    var body: some View {
        VStack(spacing: 0) {
            // 工具栏
            HStack {
                Spacer()

                Button {
                    showCreateDialog = true
                } label: {
                    HStack(spacing: 6) {
                        Image(systemName: "plus")
                            .font(.system(size: 11))
                        Text("新建项目")
                            .font(.system(size: 12, weight: .medium))
                    }
                    .foregroundColor(.white)
                    .padding(.horizontal, 16)
                    .padding(.vertical, 8)
                    .background(Color.fieldMindPrimary)
                    .cornerRadius(6)
                }
                .buttonStyle(PlainButtonStyle())
            }
            .padding(.horizontal, 24)
            .padding(.vertical, 16)
            .background(Color.white)
            .overlay(
                Rectangle()
                    .fill(Color.gray.opacity(0.1))
                    .frame(height: 1),
                alignment: .bottom
            )

            // 项目列表
            if isLoading {
                ProgressView("加载中...")
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else if projects.isEmpty {
                EmptyStateView(icon: "folder", message: "暂无项目，点击上方按钮创建")
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                ScrollView(showsIndicators: false) {
                    LazyVGrid(columns: [
                        GridItem(.adaptive(minimum: 280, maximum: 320))
                    ], spacing: 16) {
                        ForEach(projects) { project in
                            ProjectCard(project: project)
                                .onTapGesture {
                                    appState.selectProject(project)
                                    selectedProject = project
                                }
                        }
                    }
                    .padding(24)
                }
                .background(Color.fieldMindBackground)
            }
        }
        .sheet(isPresented: $showCreateDialog) {
            CreateProjectFormView()
        }
        .onAppear(perform: loadProjects)
    }

    private func loadProjects() {
        isLoading = true

        Task {
            do {
                let fetchedProjects = try await APIService.shared.getProjects()
                await MainActor.run {
                    self.projects = fetchedProjects
                    self.isLoading = false
                }
            } catch {
                print("Error loading projects: \(error)")
                await MainActor.run {
                    self.isLoading = false
                }
            }
        }
    }
}

struct ProjectCard: View {
    let project: Project
    @EnvironmentObject var appState: AppState
    @State private var showingEditDialog = false
    @State private var showingDeleteAlert = false

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // 头部
            HStack {
                Image(systemName: "folder.fill")
                    .font(.system(size: 24))
                    .foregroundColor(Color.fieldMindPrimary)

                Spacer()

                Menu {
                    Button("打开") {
                        appState.selectProject(project)
                    }
                    Button("编辑") {
                        showingEditDialog = true
                    }
                    Divider()
                    Button("删除", role: .destructive) {
                        showingDeleteAlert = true
                    }
                } label: {
                    Image(systemName: "ellipsis")
                        .font(.system(size: 14))
                        .foregroundColor(Color.fieldMindText.opacity(0.5))
                }
                .menuStyle(BorderlessButtonMenuStyle())
            }

            // 项目信息
            VStack(alignment: .leading, spacing: 6) {
                Text(project.name)
                    .font(.system(size: 12, weight: .bold))
                    .foregroundColor(Color.fieldMindText)
                    .lineLimit(1)

                if let description = project.description {
                    Text(description)
                        .font(.system(size: 11))
                        .foregroundColor(Color.fieldMindText.opacity(0.6))
                        .lineLimit(2)
                }
            }

            // 统计信息
            HStack(spacing: 16) {
                HStack(spacing: 4) {
                    Image(systemName: "doc.fill")
                        .font(.system(size: 10))
                        .foregroundColor(Color.fieldMindAuxiliary)
                    Text("\(project.documents)")
                        .font(.system(size: 11))
                        .foregroundColor(Color.fieldMindText.opacity(0.6))
                }

                HStack(spacing: 4) {
                    Image(systemName: "network")
                        .font(.system(size: 10))
                        .foregroundColor(Color.fieldMindSuccess)
                    Text("\(project.contexts)")
                        .font(.system(size: 11))
                        .foregroundColor(Color.fieldMindText.opacity(0.6))
                }
            }

            // 时间
            Text(formatDate(project.updatedAt))
                .font(.system(size: 10))
                .foregroundColor(Color.fieldMindText.opacity(0.4))
        }
        .padding(14)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color.white)
        .cornerRadius(10)
        .overlay(
            RoundedRectangle(cornerRadius: 10)
                .stroke(Color.fieldMindText.opacity(0.08), lineWidth: 1)
        )
        .alert("确认删除", isPresented: $showingDeleteAlert) {
            Button("取消", role: .cancel) { }
            Button("删除", role: .destructive) {
                deleteProject()
            }
        } message: {
            Text("确定要删除项目 \"\(project.name)\" 吗？此操作不可撤销。")
        }
    }

    private func deleteProject() {
        Task {
            do {
                try await appState.deleteProject(id: project.id)
                ToastManager.shared.success("项目已删除")
            } catch {
                ToastManager.shared.error("删除失败: \(error.localizedDescription)")
            }
        }
    }

    private func formatDate(_ date: Date) -> String {
        let formatter = RelativeDateTimeFormatter()
        formatter.unitsStyle = .short
        return "更新于 " + formatter.localizedString(for: date, relativeTo: Date())
    }
}
