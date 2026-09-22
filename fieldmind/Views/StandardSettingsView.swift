"""
设置视图 - 严格遵循设计标准
参考: Donezo Dashboard + Succulents 配色
"""
import SwiftUI

// MARK: - Settings View Model
class SettingsViewModel: ObservableObject {
    @Published var emailNotifications = true
    @Published var pushNotifications = false
    @Published var darkMode = false
    @Published var autoSave = true
    @Published var language = "简体中文"
    @Published var timezone = "Asia/Shanghai"
}

// MARK: - Main Settings View
struct StandardSettingsView: View {
    @StateObject private var viewModel = SettingsViewModel()
    @State private var selectedTab = "偏好设置"

    let tabs = ["个人资料", "账户", "偏好设置", "通知", "安全", "关于"]

    var body: some View {
        HStack(spacing: 0) {
            // 左侧边栏
            sidebarSection
                .frame(width: 220)

            // 主内容区域
            ScrollView {
                VStack(spacing: 24) {
                    contentSection
                        .padding(24)
                }
            }
            .frame(maxWidth: .infinity)
            .background(Color.fmBgSecondary)
        }
    }

    // MARK: - Sidebar Section
    private var sidebarSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            // 标题
            Text("设置")
                .font(.system(size: 20, weight: .bold))
                .foregroundColor(.fmTextPrimary)
                .padding(.horizontal, 16)
                .padding(.top, 24)
                .padding(.bottom, 16)

            // 导航列表
            ForEach(tabs, id: \.self) { tab in
                Button(action: {
                    selectedTab = tab
                }) {
                    HStack {
                        Image(systemName: iconForTab(tab))
                            .font(.system(size: 14))
                            .frame(width: 20)

                        Text(tab)
                            .font(.system(size: 14, weight: selectedTab == tab ? .medium : .regular))

                        Spacer()
                    }
                    .foregroundColor(selectedTab == tab ? .white : .fmTextPrimary)
                    .padding(.horizontal, 16)
                    .padding(.vertical, 10)
                    .background(selectedTab == tab ? Color.fmPrimary : Color.clear)
                    .cornerRadius(8)
                }
                .buttonStyle(.plain)
                .padding(.horizontal, 8)
            }

            Spacer()
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color.white)
    }

    // MARK: - Content Section
    private var contentSection: some View {
        VStack(spacing: 0) {
            switch selectedTab {
            case "偏好设置":
                preferencesContent
            case "通知":
                notificationsContent
            case "个人资料":
                profileContent
            case "账户":
                accountContent
            case "安全":
                securityContent
            case "关于":
                aboutContent
            default:
                preferencesContent
            }
        }
    }

    // MARK: - Preferences Content
    private var preferencesContent: some View {
        VStack(alignment: .leading, spacing: 24) {
            // 标题
            VStack(alignment: .leading, spacing: 4) {
                Text("偏好设置")
                    .font(.system(size: 24, weight: .bold))
                    .foregroundColor(.fmTextPrimary)

                Text("自定义您的使用体验")
                    .font(.system(size: 14))
                    .foregroundColor(.fmTextSecondary)
            }

            // 设置卡片
            VStack(spacing: 0) {
                SettingRow(
                    icon: "moon.fill",
                    title: "深色模式",
                    subtitle: "使用深色主题界面",
                    color: Color.fmTextPrimary,
                    isOn: $viewModel.darkMode
                )

                Divider()
                    .padding(.leading, 56)

                SettingRow(
                    icon: "square.and.arrow.down.fill",
                    title: "自动保存",
                    subtitle: "自动保存您的工作进度",
                    color: Color.fmInfo,
                    isOn: $viewModel.autoSave
                )

                Divider()
                    .padding(.leading, 56)

                // 语言选择
                HStack {
                    HStack(spacing: 12) {
                        ZStack {
                            Circle()
                                .fill(Color.fmSecondary.opacity(0.1))
                                .frame(width: 40, height: 40)

                            Image(systemName: "globe")
                                .font(.system(size: 16))
                                .foregroundColor(.fmSecondary)
                        }

                        VStack(alignment: .leading, spacing: 2) {
                            Text("语言")
                                .font(.system(size: 14, weight: .medium))
                                .foregroundColor(.fmTextPrimary)

                            Text("选择界面语言")
                                .font(.system(size: 13))
                                .foregroundColor(.fmTextSecondary)
                        }
                    }

                    Spacer()

                    Menu {
                        Button("简体中文") { viewModel.language = "简体中文" }
                        Button("English") { viewModel.language = "English" }
                        Button("日本語") { viewModel.language = "日本語" }
                    } label: {
                        HStack(spacing: 6) {
                            Text(viewModel.language)
                                .font(.system(size: 14))
                            Image(systemName: "chevron.down")
                                .font(.system(size: 12))
                        }
                        .foregroundColor(.fmTextPrimary)
                        .padding(.horizontal, 12)
                        .padding(.vertical, 6)
                        .background(Color.fmBgSecondary)
                        .cornerRadius(6)
                    }
                }
                .padding(16)
            }
            .background(Color.white)
            .cornerRadius(12)
            .shadow(color: Color.black.opacity(0.05), radius: 4, x: 0, y: 2)

            // 保存按钮
            HStack {
                Spacer()

                Button("取消") {}
                    .buttonStyle(.bordered)

                Button("保存更改") {}
                    .buttonStyle(.borderedProminent)
                    .tint(.fmPrimary)
            }
        }
    }

    // MARK: - Notifications Content
    private var notificationsContent: some View {
        VStack(alignment: .leading, spacing: 24) {
            VStack(alignment: .leading, spacing: 4) {
                Text("通知设置")
                    .font(.system(size: 24, weight: .bold))
                    .foregroundColor(.fmTextPrimary)

                Text("管理您的通知偏好")
                    .font(.system(size: 14))
                    .foregroundColor(.fmTextSecondary)
            }

            VStack(spacing: 0) {
                SettingRow(
                    icon: "envelope.fill",
                    title: "邮件通知",
                    subtitle: "接收重要事件的邮件通知",
                    color: Color.fmPrimary,
                    isOn: $viewModel.emailNotifications
                )

                Divider()
                    .padding(.leading, 56)

                SettingRow(
                    icon: "bell.fill",
                    title: "推送通知",
                    subtitle: "在桌面显示通知消息",
                    color: Color.fmWarning,
                    isOn: $viewModel.pushNotifications
                )
            }
            .background(Color.white)
            .cornerRadius(12)
            .shadow(color: Color.black.opacity(0.05), radius: 4, x: 0, y: 2)
        }
    }

    // MARK: - Profile Content
    private var profileContent: some View {
        VStack(alignment: .leading, spacing: 24) {
            VStack(alignment: .leading, spacing: 4) {
                Text("个人资料")
                    .font(.system(size: 24, weight: .bold))
                    .foregroundColor(.fmTextPrimary)

                Text("管理您的个人信息")
                    .font(.system(size: 14))
                    .foregroundColor(.fmTextSecondary)
            }

            // 头像和基本信息
            HStack(spacing: 20) {
                ZStack {
                    Circle()
                        .fill(Color.fmPrimary.opacity(0.1))
                        .frame(width: 80, height: 80)

                    Text("JD")
                        .font(.system(size: 28, weight: .bold))
                        .foregroundColor(.fmPrimary)
                }

                VStack(alignment: .leading, spacing: 8) {
                    Text("John Doe")
                        .font(.system(size: 20, weight: .semibold))
                        .foregroundColor(.fmTextPrimary)

                    Text("john.doe@example.com")
                        .font(.system(size: 14))
                        .foregroundColor(.fmTextSecondary)

                    Button("更换头像") {}
                        .font(.system(size: 13, weight: .medium))
                        .buttonStyle(.bordered)
                }
            }
            .padding(20)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(Color.white)
            .cornerRadius(12)
            .shadow(color: Color.black.opacity(0.05), radius: 4, x: 0, y: 2)
        }
    }

    // MARK: - Account Content
    private var accountContent: some View {
        VStack(alignment: .leading, spacing: 24) {
            Text("账户设置")
                .font(.system(size: 24, weight: .bold))
                .foregroundColor(.fmTextPrimary)

            Text("账户管理功能")
                .font(.system(size: 14))
                .foregroundColor(.fmTextSecondary)
        }
    }

    // MARK: - Security Content
    private var securityContent: some View {
        VStack(alignment: .leading, spacing: 24) {
            Text("安全设置")
                .font(.system(size: 24, weight: .bold))
                .foregroundColor(.fmTextPrimary)

            Text("保护您的账户安全")
                .font(.system(size: 14))
                .foregroundColor(.fmTextSecondary)
        }
    }

    // MARK: - About Content
    private var aboutContent: some View {
        VStack(alignment: .leading, spacing: 24) {
            Text("关于 FieldMind")
                .font(.system(size: 24, weight: .bold))
                .foregroundColor(.fmTextPrimary)

            VStack(alignment: .leading, spacing: 12) {
                Text("版本 2.0.0")
                    .font(.system(size: 14))
                    .foregroundColor(.fmTextSecondary)

                Text("© 2024 FieldMind. All rights reserved.")
                    .font(.system(size: 13))
                    .foregroundColor(.fmTextTertiary)
            }
            .padding(20)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(Color.white)
            .cornerRadius(12)
            .shadow(color: Color.black.opacity(0.05), radius: 4, x: 0, y: 2)
        }
    }

    // MARK: - Helper Functions
    private func iconForTab(_ tab: String) -> String {
        switch tab {
        case "个人资料": return "person.fill"
        case "账户": return "creditcard.fill"
        case "偏好设置": return "slider.horizontal.3"
        case "通知": return "bell.fill"
        case "安全": return "lock.fill"
        case "关于": return "info.circle.fill"
        default: return "gear"
        }
    }
}

// MARK: - Setting Row Component
struct SettingRow: View {
    let icon: String
    let title: String
    let subtitle: String
    let color: Color
    @Binding var isOn: Bool

    var body: some View {
        HStack {
            HStack(spacing: 12) {
                ZStack {
                    Circle()
                        .fill(color.opacity(0.1))
                        .frame(width: 40, height: 40)

                    Image(systemName: icon)
                        .font(.system(size: 16))
                        .foregroundColor(color)
                }

                VStack(alignment: .leading, spacing: 2) {
                    Text(title)
                        .font(.system(size: 14, weight: .medium))
                        .foregroundColor(.fmTextPrimary)

                    Text(subtitle)
                        .font(.system(size: 13))
                        .foregroundColor(.fmTextSecondary)
                }
            }

            Spacer()

            Toggle("", isOn: $isOn)
                .labelsHidden()
                .tint(.fmPrimary)
        }
        .padding(16)
    }
}

// MARK: - Preview
#Preview {
    StandardSettingsView()
}
