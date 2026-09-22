import SwiftUI

struct MenuBarPopoverView: View {
    @EnvironmentObject var appState: AppState
    @State private var searchText = ""

    var body: some View {
        VStack(spacing: 0) {
            // 头部
            headerView
                .padding(16)
                .background(Color.fmSurface)

            Divider()

            // 快速访问区域
            if appState.currentProject != nil {
                quickAccessView
                    .padding(.vertical, 12)
            } else {
                emptyStateView
                    .padding(.vertical, 40)
            }

            Spacer()

            Divider()

            // 底部操作
            footerView
                .padding(12)
                .background(Color.fmSurface)
        }
        .background(Color.fmBg)
        .frame(width: 400, height: 600)
    }

    private var headerView: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: "brain.head.profile")
                    .font(.system(size: 20, weight: .semibold))
                    .foregroundColor(.fmA1)

                Text("FieldMind")
                    .font(.system(size: 16, weight: .bold))
                    .foregroundColor(.fmText)

                Spacer()

                Button(action: {
                    MenuBarManager.shared.showMainWindow()
                }) {
                    Image(systemName: "arrow.up.left.and.arrow.down.right")
                        .font(.system(size: 12))
                        .foregroundColor(.fmText3)
                }
                .buttonStyle(.plain)
                .help("打开主窗口")
            }

            if let project = appState.currentProject {
                Text(project.name)
                    .font(.system(size: 13))
                    .foregroundColor(.fmText2)
            }
        }
    }

    private var quickAccessView: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 12) {
                // 快速操作按钮
                quickActionsSection

                Divider()
                    .padding(.vertical, 8)

                // 最近的会话
                recentSessionsSection
            }
            .padding(.horizontal, 16)
        }
    }

    private var quickActionsSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("快速操作")
                .font(.system(size: 11, weight: .semibold))
                .foregroundColor(.fmText3)
                .textCase(.uppercase)

            VStack(spacing: 6) {
                QuickActionButton(
                    icon: "message.fill",
                    title: "新建对话",
                    action: {
                        MenuBarManager.shared.navigateTo(.chat)
                    }
                )

                QuickActionButton(
                    icon: "doc.fill.badge.plus",
                    title: "上传文档",
                    action: {
                        MenuBarManager.shared.navigateTo(.upload)
                    }
                )

                QuickActionButton(
                    icon: "magnifyingglass",
                    title: "搜索知识库",
                    action: {
                        MenuBarManager.shared.navigateTo(.advancedSearch)
                    }
                )
            }
        }
    }

    private var recentSessionsSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("最近会话")
                .font(.system(size: 11, weight: .semibold))
                .foregroundColor(.fmText3)
                .textCase(.uppercase)

            Text("暂无最近会话")
                .font(.system(size: 12))
                .foregroundColor(.fmText3)
                .frame(maxWidth: .infinity, alignment: .center)
                .padding(.vertical, 20)
        }
    }

    private var emptyStateView: some View {
        VStack(spacing: 16) {
            Image(systemName: "folder.badge.questionmark")
                .font(.system(size: 48))
                .foregroundColor(.fmText4)

            Text("未选择项目")
                .font(.system(size: 14, weight: .medium))
                .foregroundColor(.fmText2)

            Text("请在主窗口中选择或创建项目")
                .font(.system(size: 12))
                .foregroundColor(.fmText3)
                .multilineTextAlignment(.center)

            Button(action: {
                MenuBarManager.shared.showMainWindow()
            }) {
                Text("打开主窗口")
                    .font(.system(size: 12, weight: .medium))
                    .foregroundColor(.white)
                    .padding(.horizontal, 16)
                    .padding(.vertical, 8)
                    .background(Color.fmA1)
                    .cornerRadius(6)
            }
            .buttonStyle(.plain)
        }
    }

    private var footerView: some View {
        HStack(spacing: 12) {
            Button(action: {
                MenuBarManager.shared.showMainWindow()
            }) {
                HStack(spacing: 6) {
                    Image(systemName: "square.grid.2x2")
                        .font(.system(size: 12))
                    Text("主窗口")
                        .font(.system(size: 11))
                }
                .foregroundColor(.fmText2)
                .frame(maxWidth: .infinity)
                .padding(.vertical, 8)
                .background(Color.fmBg2)
                .cornerRadius(6)
            }
            .buttonStyle(.plain)

            Button(action: {
                NSApp.terminate(nil)
            }) {
                HStack(spacing: 6) {
                    Image(systemName: "power")
                        .font(.system(size: 12))
                    Text("退出")
                        .font(.system(size: 11))
                }
                .foregroundColor(.fmText2)
                .frame(maxWidth: .infinity)
                .padding(.vertical, 8)
                .background(Color.fmBg2)
                .cornerRadius(6)
            }
            .buttonStyle(.plain)
        }
    }
}

// MARK: - Quick Action Button
struct QuickActionButton: View {
    let icon: String
    let title: String
    let action: () -> Void

    @State private var isHovered = false

    var body: some View {
        Button(action: action) {
            HStack(spacing: 12) {
                Image(systemName: icon)
                    .font(.system(size: 14))
                    .foregroundColor(.fmA1)
                    .frame(width: 20)

                Text(title)
                    .font(.system(size: 13))
                    .foregroundColor(.fmText)

                Spacer()

                Image(systemName: "chevron.right")
                    .font(.system(size: 10))
                    .foregroundColor(.fmText4)
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 10)
            .background(isHovered ? Color.fmBg2 : Color.clear)
            .cornerRadius(6)
        }
        .buttonStyle(.plain)
        .onHover { hovering in
            isHovered = hovering
        }
    }
}
