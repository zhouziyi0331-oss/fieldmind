import SwiftUI

struct MainAppView: View {
    @EnvironmentObject var appState: AppState

    var body: some View {
        GeometryReader { geometry in
            HStack(spacing: 0) {
                // 左侧边栏 - 固定210px宽度
                SidebarView()
                    .frame(width: 210)

                // 主内容区
                VStack(spacing: 0) {
                    // 顶部导航栏 - 固定50px高度
                    TopNavigationBar()
                        .frame(height: 50)

                    // 主要内容页面
                    contentView
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                }
            }
        }
        .background(Color.fieldMindBackground)
        .withToast()
    }

    @ViewBuilder
    private var contentView: some View {
        switch appState.selectedPage {
        case .dashboard:
            DashboardView()
        case .projects:
            ProjectsView()
        case .contexts:
            ContextsView()
        case .documents:
            DocumentsView()
        case .chat:
            ChatView()
        case .keywordSearch: // ⭐ NEW
            KeywordSearchView()
        case .timeline:
            TimelineView()
        case .graph:
            GraphView()
        case .skills:
            SkillsView()
        case .frameworks:
            FrameworksView()
        case .reports:
            ReportsView()
        case .creativeAnalysis: // ⭐ NEW
            CreativeAnalysisView()
        case .businessAnalysis: // ⭐ NEW
            BusinessAnalysisView()
        case .crawler:
            CrawlerView()
        case .audioVideo:
            AudioVideoView()
        case .workflows:
            WorkflowsView()
        case .agentMemory:
            AgentMemoryView()
        case .settings:
            SettingsView()
        }
    }
}

struct SidebarView: View {
    @EnvironmentObject var appState: AppState

    var body: some View {
        ZStack {
            // 渐变背景
            LinearGradient(
                colors: [
                    Color.fieldMindPrimary,
                    Color(hex: "1278A0")
                ],
                startPoint: .top,
                endPoint: .bottom
            )

            VStack(spacing: 0) {
                // Logo 区域
                HStack(spacing: 10) {
                    Image(systemName: "leaf.fill")
                        .font(.system(size: 22, weight: .semibold))
                        .foregroundColor(.white)

                    Text("FieldMind")
                        .font(.system(size: 16, weight: .bold))
                        .foregroundColor(.white)
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.horizontal, 16)
                .padding(.vertical, 16)

                // 导航菜单
                ScrollView(showsIndicators: false) {
                    VStack(spacing: 2) {
                        ForEach(AppState.NavigationPage.allCases, id: \.self) { page in
                            NavigationMenuItem(page: page)
                        }
                    }
                    .padding(.vertical, 8)
                    .padding(.horizontal, 12)
                }

                Spacer()

                // 任务中心按钮
                TaskCenterButton()
                    .padding(.horizontal, 12)
                    .padding(.vertical, 8)

                Divider()
                    .background(Color.white.opacity(0.2))

                // 项目选择器
                VStack(spacing: 0) {
                    Divider()
                        .background(Color.white.opacity(0.2))

                    Menu {
                        ForEach(appState.projects) { project in
                            Button(action: {
                                appState.selectProject(project)
                            }) {
                                HStack {
                                    Text(project.name)
                                    if appState.currentProject?.id == project.id {
                                        Image(systemName: "checkmark")
                                    }
                                }
                            }
                        }

                        Divider()

                        Button(action: {
                            appState.selectedPage = .projects
                        }) {
                            Label("管理项目", systemImage: "folder.badge.plus")
                        }
                    } label: {
                        HStack(spacing: 8) {
                            Image(systemName: "folder.fill")
                                .font(.system(size: 12))
                                .foregroundColor(.white.opacity(0.8))

                            if let project = appState.currentProject {
                                Text(project.name)
                                    .font(.system(size: 12, weight: .medium))
                                    .foregroundColor(.white)
                                    .lineLimit(1)
                            } else {
                                Text("选择项目")
                                    .font(.system(size: 12, weight: .medium))
                                    .foregroundColor(.white.opacity(0.6))
                            }

                            Spacer()

                            Image(systemName: "chevron.up.chevron.down")
                                .font(.system(size: 10))
                                .foregroundColor(.white.opacity(0.6))
                        }
                        .padding(.horizontal, 16)
                        .padding(.vertical, 12)
                        .contentShape(Rectangle())
                    }
                    .buttonStyle(.plain)
                    .menuStyle(.borderlessButton)
                }
            }
        }
        .frame(width: 210)
    }
}

struct NavigationMenuItem: View {
    @EnvironmentObject var appState: AppState
    let page: AppState.NavigationPage

    var body: some View {
        Button(action: {
            appState.selectedPage = page
        }) {
            HStack(spacing: 10) {
                Image(systemName: page.icon)
                    .font(.system(size: 14))
                    .frame(width: 16)

                Text(page.rawValue)
                    .font(.system(size: 13, weight: .medium))

                Spacer()
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 10)
            .background(
                appState.selectedPage == page ?
                Color.white.opacity(0.2) : Color.clear
            )
            .cornerRadius(6)
            .foregroundColor(.white)
        }
        .buttonStyle(PlainButtonStyle())
    }
}

struct TopNavigationBar: View {
    @EnvironmentObject var appState: AppState
    @State private var showUserMenu = false

    var body: some View {
        HStack(spacing: 0) {
            // 页面标题
            Text(appState.selectedPage.rawValue)
                .font(.system(size: 13, weight: .bold))
                .foregroundColor(Color.fieldMindText)
                .padding(.leading, 24)

            Spacer()

            // 用户菜单
            if let user = appState.currentUser {
                Menu {
                    Text(user.username)
                        .font(.system(size: 12))

                    Divider()

                    Button("设置") {
                        // TODO: 打开设置
                    }

                    Button("退出登录") {
                        handleLogout()
                    }
                } label: {
                    HStack(spacing: 6) {
                        Image(systemName: "person.circle.fill")
                            .font(.system(size: 16))
                            .foregroundColor(Color.fieldMindPrimary)

                        Text(user.username)
                            .font(.system(size: 12, weight: .medium))
                            .foregroundColor(Color.fieldMindText)

                        Image(systemName: "chevron.down")
                            .font(.system(size: 9))
                            .foregroundColor(Color.fieldMindText.opacity(0.6))
                    }
                    .padding(.horizontal, 12)
                    .padding(.vertical, 6)
                    .background(Color.white)
                    .cornerRadius(6)
                }
                .menuStyle(BorderlessButtonMenuStyle())
                .padding(.trailing, 24)
            }
        }
        .frame(height: 50)
        .background(Color.white)
        .overlay(
            Rectangle()
                .fill(Color.gray.opacity(0.1))
                .frame(height: 1),
            alignment: .bottom
        )
    }

    private func handleLogout() {
        Task {
            do {
                try await APIService.shared.logout()
                await MainActor.run {
                    appState.logout()
                }
            } catch {
                print("Logout error: \(error)")
                await MainActor.run {
                    appState.logout()
                }
            }
        }
    }
}
