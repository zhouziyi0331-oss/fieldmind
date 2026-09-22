"""
设置页面 - Succulents 设计系统
"""
import SwiftUI

struct SucculentsSettingsView: View {
    @State private var notifications = true
    @State private var darkMode = false
    @State private var autoSave = true

    var body: some View {
        ScrollView {
            HStack(alignment: .top, spacing: 24) {
                // Sidebar
                VStack(alignment: .leading, spacing: 8) {
                    ForEach(["个人资料", "账户", "偏好设置", "通知", "安全"], id: \.self) { item in
                        Button(action: {}) {
                            Text(item)
                                .font(.system(size: 14))
                                .foregroundColor(item == "偏好设置" ? .white : .fmTextPrimary)
                                .frame(maxWidth: .infinity, alignment: .leading)
                                .padding(.horizontal, 16)
                                .padding(.vertical, 10)
                                .background(item == "偏好设置" ? Color.fmPrimary : Color.clear)
                                .cornerRadius(8)
                        }
                        .buttonStyle(.plain)
                    }
                }
                .frame(width: 200)
                .padding(16)
                .background(Color.fmBgElevated)
                .cornerRadius(12)

                // Main Content
                VStack(spacing: 24) {
                    VStack(alignment: .leading, spacing: 16) {
                        Text("偏好设置")
                            .font(.system(size: 24, weight: .bold))

                        Divider()

                        SettingRow(title: "邮件通知", subtitle: "接收邮件更新", isOn: $notifications)
                        SettingRow(title: "深色模式", subtitle: "使用深色主题", isOn: $darkMode)
                        SettingRow(title: "自动保存", subtitle: "自动保存更改", isOn: $autoSave)
                    }
                    .padding(24)
                    .background(Color.fmBgElevated)
                    .cornerRadius(12)

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
            .padding(24)
        }
        .background(Color.fmBgSecondary)
    }
}

struct SettingRow: View {
    let title: String
    let subtitle: String
    @Binding var isOn: Bool

    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text(title)
                    .font(.system(size: 16, weight: .medium))
                Text(subtitle)
                    .font(.system(size: 14))
                    .foregroundColor(.fmTextSecondary)
            }
            Spacer()
            Toggle("", isOn: $isOn)
                .labelsHidden()
        }
        .padding(.vertical, 8)
    }
}

#Preview {
    SucculentsSettingsView()
}
