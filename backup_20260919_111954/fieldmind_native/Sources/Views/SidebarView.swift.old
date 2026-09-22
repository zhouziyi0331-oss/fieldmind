import SwiftUI

struct SidebarView: View {
    @EnvironmentObject var appState: AppState
    @State private var searchText = ""

    var body: some View {
        ZStack(alignment: .trailing) {
            VStack(spacing: 0) {
                // 顶部操作区
                sidebarHeader
                    .padding(EdgeInsets(top: 14, leading: 12, bottom: 12, trailing: 12))
                    .background(
                        Rectangle()
                            .fill(Color.clear)
                            .border(width: 1, edges: [.bottom], color: Color.fmSbBorder)
                    )

                // 品牌区
                if !appState.isSidebarCollapsed {
                    brandSection
                        .padding(EdgeInsets(top: 22, leading: 16, bottom: 18, trailing: 16))
                        .background(
                            Rectangle()
                                .fill(Color.clear)
                                .border(width: 1, edges: [.bottom], color: Color.fmSbBorder)
                        )
                }

                // 导航菜单
                ScrollView(showsIndicators: false) {
                    VStack(spacing: 1) {
                        navigationItems
                    }
                    .padding(EdgeInsets(top: 12, leading: 8, bottom: 12, trailing: 8))
                }

                // 底部用户信息
                userSection
                    .padding(EdgeInsets(top: 12, leading: 16, bottom: 12, trailing: 16))
                    .background(
                        Rectangle()
                            .fill(Color.clear)
                            .border(width: 1, edges: [.top], color: Color.fmSbBorder)
                    )
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .background(
                LinearGradient(
                    colors: [Color.fmSbBg, Color.fmSbBg2],
                    startPoint: .top,
                    endPoint: .bottom
                )
            )

            // 折叠按钮
            toggleButton
        }
    }

    // MARK: - 顶部操作区
    private var sidebarHeader: some View {
        VStack(spacing: 10) {
            HStack(spacing: 8) {
                if !appState.isSidebarCollapsed {
                    Text("FieldMind")
                        .font(.system(size: 15, weight: .heavy))
                        .foregroundColor(.fmSbText)
                        .tracking(-0.02)
                }

                Spacer()

                // 新对话按钮
                if !appState.isSidebarCollapsed {
                    Button(action: {
                        appState.navigateTo(.chat)
                    }) {
                        HStack(spacing: 4) {
                            Text("+")
                                .font(.system(size: 16, weight: .light))
                            Text("新对话")
                                .font(.system(size: 11, weight: .semibold))
                        }
                        .foregroundColor(.white)
                        .padding(EdgeInsets(top: 5, leading: 11, bottom: 5, trailing: 11))
                        .background(Color.white.opacity(0.22))
                        .cornerRadius(18)
                        .overlay(
                            RoundedRectangle(cornerRadius: 18)
                                .stroke(Color.white.opacity(0.3), lineWidth: 1)
                        )
                    }
                    .buttonStyle(.plain)
                }
            }

            // 搜索框
            if !appState.isSidebarCollapsed {
                HStack(spacing: 6) {
                    Image(systemName: "magnifyingglass")
                        .font(.system(size: 13))
                        .foregroundColor(.white.opacity(0.6))

                    TextField("搜索...", text: $searchText)
                        .textFieldStyle(.plain)
                        .font(.system(size: 11))
                        .foregroundColor(.white)
                }
                .padding(EdgeInsets(top: 7, leading: 10, bottom: 7, trailing: 10))
                .background(Color.white.opacity(0.12))
                .cornerRadius(8)
                .overlay(
                    RoundedRectangle(cornerRadius: 8)
                        .stroke(Color.white.opacity(0.16), lineWidth: 1)
                )
            }
        }
    }

    // MARK: - 品牌区
    private var brandSection: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack(spacing: 10) {
                // Logo
                ZStack {
                    RoundedRectangle(cornerRadius: 7)
                        .fill(Color.white.opacity(0.2))
                        .frame(width: 30, height: 30)
                        .shadow(color: .black.opacity(0.15), radius: 7, x: 0, y: 0)

                    Image(systemName: "brain")
                        .font(.system(size: 14, weight: .medium))
                        .foregroundColor(.white)
                }

                VStack(alignment: .leading, spacing: 1) {
                    Text("FieldMind")
                        .font(.system(size: 13, weight: .heavy))
                        .foregroundColor(.fmSbText)
                        .tracking(-0.01)

                    Text("KNOWLEDGE ENGINE")
                        .font(.system(size: 9))
                        .foregroundColor(.fmSbText3)
                        .tracking(0.08)
                }
            }

            // Live 状态
            HStack(spacing: 5) {
                Circle()
                    .fill(Color.fmA2)
                    .frame(width: 6, height: 6)
                    .shadow(color: Color.fmA2, radius: 3)

                Text("LIVE")
                    .font(.system(size: 9, weight: .bold))
                    .foregroundColor(.fmA2)
                    .tracking(0.06)
            }
        }
    }

    // MARK: - 导航菜单
    private var navigationItems: some View {
        Group {
            SidebarSection(title: "核心功能")

            SidebarItem(icon: "house.fill", title: "项目概览", page: .overview)
            SidebarItem(icon: "plus.square.fill", title: "新建项目", page: .newproject)
            SidebarItem(icon: "square.grid.2x2.fill", title: "项目列表", page: .projects)

            SidebarSection(title: "材料管理")

            SidebarItem(icon: "arrow.up.doc.fill", title: "材料上传", page: .upload)
            SidebarItem(icon: "folder.fill", title: "文件管理器", page: .fileManager)
            SidebarItem(icon: "photo.fill", title: "照片管理", page: .photos)
            SidebarItem(icon: "tablecells.fill", title: "表格管理", page: .tables)

            SidebarSection(title: "知识处理")

            SidebarItem(icon: "tag.fill", title: "关键词引擎", page: .keyword, badge: "128")
            SidebarItem(icon: "message.fill", title: "AI 对话", page: .chat)
            SidebarItem(icon: "bubble.left.and.bubble.right.fill", title: "对话历史", page: .conversations)
            SidebarItem(icon: "quote.bubble.fill", title: "引用管理", page: .citations)

            SidebarSection(title: "可视化分析")

            SidebarItem(icon: "chart.bar.fill", title: "可视化看板", page: .dashboard)
            SidebarItem(icon: "point.3.connected.trianglepath.dotted", title: "知识脉络", page: .vein)
            SidebarItem(icon: "timeline.selection", title: "编年史", page: .chronicle)
            SidebarItem(icon: "clock.fill", title: "时间线", page: .timeline)
            SidebarItem(icon: "network", title: "知识图谱", page: .graphExplorer)

            SidebarSection(title: "报告生成")

            SidebarItem(icon: "doc.text.fill", title: "调研报告", page: .report)
            SidebarItem(icon: "doc.richtext.fill", title: "调研报告3", page: .report3)
            SidebarItem(icon: "building.2.fill", title: "业态分析", page: .busi)

            SidebarSection(title: "工作流")

            SidebarItem(icon: "list.bullet.rectangle.fill", title: "SOP 管理", page: .sop)
            SidebarItem(icon: "chart.line.uptrend.xyaxis", title: "SOP 分析", page: .sopAnalysis)
            SidebarItem(icon: "arrow.triangle.branch", title: "工作流复用", page: .workflow)

            SidebarSection(title: "高级功能")

            SidebarItem(icon: "bolt.fill", title: "Skill 生态", page: .skill, badge: "3")
            SidebarItem(icon: "memorychip.fill", title: "Agent 记忆", page: .agentMemory)
            SidebarItem(icon: "magnifyingglass", title: "高级搜索", page: .advancedSearch)
            SidebarItem(icon: "checkmark.seal.fill", title: "质量监控", page: .qualityMonitor)
            SidebarItem(icon: "cpu.fill", title: "模型管理", page: .model)
            SidebarItem(icon: "gearshape.fill", title: "设置", page: .settings)
        }
    }

    // MARK: - 用户信息
    private var userSection: some View {
        HStack(spacing: 8) {
            // 头像
            ZStack {
                Circle()
                    .fill(Color.white.opacity(0.2))
                    .frame(width: 26, height: 26)
                    .overlay(
                        Circle()
                            .stroke(Color.white.opacity(0.3), lineWidth: 1)
                    )

                Text(String(appState.user.avatar.prefix(1)))
                    .font(.system(size: 10, weight: .bold))
                    .foregroundColor(.white)
            }

            if !appState.isSidebarCollapsed {
                VStack(alignment: .leading, spacing: 0) {
                    Text(appState.user.name)
                        .font(.system(size: 11, weight: .semibold))
                        .foregroundColor(.fmSbText)

                    Text(appState.user.role)
                        .font(.system(size: 9))
                        .foregroundColor(.fmSbText3)
                }
            }

            Spacer()
        }
    }

    // MARK: - 折叠按钮
    private var toggleButton: some View {
        Button(action: {
            withAnimation(.easeInOut(duration: 0.3)) {
                appState.isSidebarCollapsed.toggle()
            }
        }) {
            ZStack {
                Circle()
                    .fill(Color.white)
                    .frame(width: 36, height: 36)
                    .shadow(color: .black.opacity(0.15), radius: 6, x: 0, y: 2)
                    .overlay(
                        Circle()
                            .stroke(Color.fmA1, lineWidth: 2)
                    )

                Image(systemName: appState.isSidebarCollapsed ? "chevron.right" : "chevron.left")
                    .font(.system(size: 14, weight: .bold))
                    .foregroundColor(.fmA1)
            }
        }
        .buttonStyle(.plain)
        .offset(x: 18, y: 0)
    }
}

// MARK: - Sidebar Section
struct SidebarSection: View {
    let title: String
    @EnvironmentObject var appState: AppState

    var body: some View {
        if !appState.isSidebarCollapsed {
            Text(title)
                .font(.system(size: 9, weight: .bold))
                .foregroundColor(.fmSbText3)
                .tracking(0.1)
                .padding(EdgeInsets(top: 10, leading: 8, bottom: 4, trailing: 8))
        }
    }
}

// MARK: - Sidebar Item
struct SidebarItem: View {
    @EnvironmentObject var appState: AppState

    let icon: String
    let title: String
    let page: PageType
    var badge: String? = nil

    private var isActive: Bool {
        appState.currentPage == page
    }

    var body: some View {
        Button(action: {
            appState.navigateTo(page)
        }) {
            HStack(spacing: 8) {
                Image(systemName: icon)
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(isActive ? .fmSbText : .fmSbText2)
                    .frame(width: 14)

                if !appState.isSidebarCollapsed {
                    Text(title)
                        .font(.system(size: 12, weight: .medium))
                        .foregroundColor(isActive ? .fmSbText : .fmSbText2)

                    Spacer()

                    if let badge = badge {
                        Text(badge)
                            .font(.system(size: 9, weight: .bold))
                            .foregroundColor(Color(hex: "D4E84A"))
                            .padding(EdgeInsets(top: 1, leading: 6, bottom: 1, trailing: 6))
                            .background(Color.fmA2.opacity(0.3))
                            .cornerRadius(10)
                            .overlay(
                                RoundedRectangle(cornerRadius: 10)
                                    .stroke(Color.fmA2.opacity(0.4), lineWidth: 1)
                            )
                    }
                }
            }
            .padding(EdgeInsets(top: 8, leading: 10, bottom: 8, trailing: 10))
            .background(
                Group {
                    if isActive {
                        RoundedRectangle(cornerRadius: 7)
                            .fill(Color.fmSbActiveBg)
                            .overlay(
                                RoundedRectangle(cornerRadius: 7)
                                    .stroke(Color.fmSbActiveBorder, lineWidth: 1)
                            )
                            .overlay(alignment: .leading) {
                                Rectangle()
                                    .fill(Color.fmA2)
                                    .frame(width: 3, height: 16)
                                    .cornerRadius(3)
                                    .shadow(color: Color.fmA2, radius: 4)
                            }
                    } else {
                        Color.clear
                    }
                }
            )
        }
        .buttonStyle(.plain)
    }
}

// MARK: - Border Extension
extension View {
    func border(width: CGFloat, edges: [Edge], color: Color) -> some View {
        overlay(
            GeometryReader { geometry in
                Path { path in
                    for edge in edges {
                        switch edge {
                        case .top:
                            path.move(to: CGPoint(x: 0, y: 0))
                            path.addLine(to: CGPoint(x: geometry.size.width, y: 0))
                        case .bottom:
                            path.move(to: CGPoint(x: 0, y: geometry.size.height))
                            path.addLine(to: CGPoint(x: geometry.size.width, y: geometry.size.height))
                        case .leading:
                            path.move(to: CGPoint(x: 0, y: 0))
                            path.addLine(to: CGPoint(x: 0, y: geometry.size.height))
                        case .trailing:
                            path.move(to: CGPoint(x: geometry.size.width, y: 0))
                            path.addLine(to: CGPoint(x: geometry.size.width, y: geometry.size.height))
                        }
                    }
                }
                .stroke(color, lineWidth: width)
            }
        )
    }
}
