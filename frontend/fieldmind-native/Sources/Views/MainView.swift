import SwiftUI

struct MainView: View {
    @EnvironmentObject var appState: AppState
    @State private var showDebugWindow = true

    var body: some View {
        HStack(spacing: 0) {
            // 侧边栏
            SidebarView()
                .frame(width: appState.isSidebarCollapsed ? 60 : 240)
                .zIndex(10)

            // 主内容区
            VStack(spacing: 0) {
                // 顶部栏
                TopBarView()

                // 页面内容
                ScrollView {
                    PageContentView()
                        .padding(EdgeInsets(top: 20, leading: 24, bottom: 20, trailing: 24))
                }
                .background(Color.fmBg)
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .overlay(alignment: .topTrailing) {
            // Toast 通知
            if appState.showToast {
                ToastView(
                    message: appState.toastMessage,
                    type: appState.toastType
                )
                .padding(EdgeInsets(top: 70, leading: 0, bottom: 0, trailing: 24))
                .transition(.move(edge: .top).combined(with: .opacity))
            }
        }
        .overlay(alignment: .topLeading) {
            // 调试窗口
            if showDebugWindow {
                DebugWindow()
            }
        }
        .onAppear {
            DebugLogger.shared.log("🚀 应用启动", type: .info)
        }
    }
}

// MARK: - Page Content Router
struct PageContentView: View {
    @EnvironmentObject var appState: AppState

    private var projectId: Int {
        if let id = appState.currentProject?.id, let intId = Int(id) {
            return intId
        }
        return 2 // 默认项目ID（贵州布依族山歌调研）
    }

    var body: some View {
        Group {
            switch appState.currentPage {
            // 核心功能页面
            case .overview:
                OverviewPage(projectId: projectId)
            case .newproject:
                NewProjectPage()
            case .projects:
                ProjectsPage()
            case .projectDetail:
                ProjectDetailPage(projectId: projectId)

            // 材料管理页面
            case .import, .upload:
                UploadPage()
            case .fileManager:
                FileManagerPage(projectId: projectId)
            case .photos:
                PhotosPage(projectId: projectId)
            case .tables:
                TablesPage(projectId: projectId)

            // 知识处理页面
            case .keyword:
                KeywordPage(projectId: projectId)
            case .chat:
                ChatPage()
            case .conversations:
                ConversationsPage(projectId: projectId)
            case .citations:
                CitationsPage_NEW(projectId: projectId)

            // 可视化分析页面
            case .dashboard:
                DashboardPage()
            case .vein:
                VeinPage(projectId: projectId)
            case .chronicle:
                ChroniclePage(projectId: projectId)
            case .timeline:
                TimelinePage(projectId: projectId)
            case .graphExplorer:
                GraphExplorerPage(projectId: projectId)

            // 报告生成页面
            case .report:
                ReportPage(projectId: projectId)
            case .report3:
                Report3Page(projectId: projectId)
            case .busi:
                BusiPage(projectId: projectId)

            // 工作流页面
            case .sop:
                SOPPage(projectId: projectId)
            case .sopAnalysis:
                SOPAnalysisPage(projectId: projectId)
            case .workflow:
                WorkflowPage(projectId: projectId)

            // 高级功能页面
            case .skill:
                SkillPage(projectId: projectId)
            case .agentMemory:
                AgentMemoryPage(projectId: projectId)
            case .advancedSearch:
                AdvancedSearchPage(projectId: projectId)
            case .qualityMonitor:
                QualityMonitorPage(projectId: projectId)
            case .model:
                ModelPage()
            case .settings:
                SettingsPage()
            }
        }
    }
}

// MARK: - Placeholder Page (临时页面，逐步替换)
struct PlaceholderPage: View {
    let pageType: PageType

    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: "hammer.fill")
                .font(.system(size: 48))
                .foregroundColor(.fmText3)

            Text(pageType.title)
                .font(FMFont.title)
                .foregroundColor(.fmText)

            Text("此页面正在开发中...")
                .font(FMFont.body)
                .foregroundColor(.fmText3)

            Text("共有 30 个页面需要逐一完成")
                .font(.system(size: 11))
                .foregroundColor(.fmText4)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color.fmBg)
    }
}
