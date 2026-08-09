import SwiftUI

struct SettingsView: View {
    @State private var selectedTab = 0

    let tabs = ["账户", "API配置", "数据库", "系统", "关于"]

    var body: some View {
        VStack(spacing: 0) {
            // 顶部标签栏
            HStack(spacing: 4) {
                ForEach(Array(tabs.enumerated()), id: \.offset) { index, tab in
                    Button {
                        selectedTab = index
                    } label: {
                        Text(tab)
                            .font(.system(size: 13, weight: selectedTab == index ? .semibold : .medium))
                            .foregroundColor(
                                selectedTab == index ?
                                Color.fieldMindPrimary : Color.fieldMindText.opacity(0.6)
                            )
                            .padding(.horizontal, 20)
                            .padding(.vertical, 10)
                            .background(
                                selectedTab == index ?
                                Color.fieldMindPrimary.opacity(0.08) : Color.clear
                            )
                            .cornerRadius(6)
                    }
                    .buttonStyle(PlainButtonStyle())
                }

                Spacer()
            }
            .padding(.horizontal, 24)
            .padding(.vertical, 12)
            .background(Color.white)
            .overlay(
                Rectangle()
                    .fill(Color.gray.opacity(0.1))
                    .frame(height: 1),
                alignment: .bottom
            )

            // 内容区域
            ScrollView(showsIndicators: false) {
                Group {
                    switch selectedTab {
                    case 0:
                        accountSettingsView
                    case 1:
                        apiConfigurationView
                    case 2:
                        databaseConfigurationView
                    case 3:
                        systemSettingsView
                    case 4:
                        aboutView
                    default:
                        EmptyView()
                    }
                }
                .padding(24)
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .background(Color.fieldMindBackground)
        }
        .background(Color.fieldMindBackground)
    }

    // MARK: - 账户设置
    private var accountSettingsView: some View {
        VStack(alignment: .leading, spacing: 24) {
            settingSection(title: "账户信息") {
                VStack(spacing: 16) {
                    settingRow(label: "用户名", value: "研究员01")
                    Divider()
                    settingRow(label: "邮箱", value: "researcher@fieldmind.com")
                    Divider()
                    settingRow(label: "注册时间", value: "2024-03-01")
                }
            }

            settingSection(title: "密码管理") {
                Button {
                    // 修改密码
                } label: {
                    HStack {
                        Text("修改密码")
                            .font(.system(size: 12))
                            .foregroundColor(Color.fieldMindText)
                        Spacer()
                        Image(systemName: "chevron.right")
                            .font(.system(size: 10))
                            .foregroundColor(Color.fieldMindText.opacity(0.4))
                    }
                    .padding(14)
                }
                .buttonStyle(PlainButtonStyle())
            }

            settingSection(title: "数据管理") {
                VStack(spacing: 0) {
                    Button {
                        // 导出数据
                    } label: {
                        HStack {
                            Image(systemName: "square.and.arrow.down")
                                .font(.system(size: 12))
                                .foregroundColor(Color.fieldMindPrimary)
                            Text("导出我的数据")
                                .font(.system(size: 12))
                                .foregroundColor(Color.fieldMindText)
                            Spacer()
                            Image(systemName: "chevron.right")
                                .font(.system(size: 10))
                                .foregroundColor(Color.fieldMindText.opacity(0.4))
                        }
                        .padding(14)
                    }
                    .buttonStyle(PlainButtonStyle())

                    Divider()

                    Button {
                        // 清除缓存
                    } label: {
                        HStack {
                            Image(systemName: "trash")
                                .font(.system(size: 12))
                                .foregroundColor(Color.fieldMindDanger)
                            Text("清除本地缓存")
                                .font(.system(size: 12))
                                .foregroundColor(Color.fieldMindText)
                            Spacer()
                            Text("156 MB")
                                .font(.system(size: 11))
                                .foregroundColor(Color.fieldMindText.opacity(0.5))
                            Image(systemName: "chevron.right")
                                .font(.system(size: 10))
                                .foregroundColor(Color.fieldMindText.opacity(0.4))
                        }
                        .padding(14)
                    }
                    .buttonStyle(PlainButtonStyle())
                }
            }
        }
    }

    // MARK: - API配置
    private var apiConfigurationView: some View {
        VStack(alignment: .leading, spacing: 24) {
            settingSection(title: "OpenAI API") {
                VStack(alignment: .leading, spacing: 12) {
                    Text("API Key")
                        .font(.system(size: 11, weight: .semibold))
                        .foregroundColor(Color.fieldMindText.opacity(0.7))

                    SecureField("sk-...", text: .constant(""))
                        .textFieldStyle(CustomTextFieldStyle())

                    Text("用于智能对话和内容生成")
                        .font(.system(size: 10))
                        .foregroundColor(Color.fieldMindText.opacity(0.5))
                }
                .padding(14)
            }

            settingSection(title: "模型配置") {
                VStack(spacing: 16) {
                    HStack {
                        Text("默认模型")
                            .font(.system(size: 12))
                            .foregroundColor(Color.fieldMindText)
                        Spacer()
                        Picker("", selection: .constant("gpt-4")) {
                            Text("GPT-4").tag("gpt-4")
                            Text("GPT-3.5 Turbo").tag("gpt-3.5-turbo")
                        }
                        .pickerStyle(MenuPickerStyle())
                        .frame(width: 150)
                    }

                    Divider()

                    HStack {
                        VStack(alignment: .leading, spacing: 4) {
                            Text("Temperature")
                                .font(.system(size: 12))
                                .foregroundColor(Color.fieldMindText)
                            Text("控制输出的随机性")
                                .font(.system(size: 10))
                                .foregroundColor(Color.fieldMindText.opacity(0.5))
                        }
                        Spacer()
                        Text("0.7")
                            .font(.system(size: 11, design: .monospaced))
                            .foregroundColor(Color.fieldMindText.opacity(0.7))
                    }

                    Slider(value: .constant(0.7), in: 0...2)
                        .accentColor(Color.fieldMindPrimary)
                }
                .padding(14)
            }

            settingSection(title: "API使用统计") {
                VStack(spacing: 12) {
                    HStack {
                        Text("本月使用量")
                            .font(.system(size: 12))
                            .foregroundColor(Color.fieldMindText)
                        Spacer()
                        Text("12,450 tokens")
                            .font(.system(size: 11, weight: .medium, design: .monospaced))
                            .foregroundColor(Color.fieldMindPrimary)
                    }

                    HStack {
                        Text("预估费用")
                            .font(.system(size: 12))
                            .foregroundColor(Color.fieldMindText)
                        Spacer()
                        Text("$2.34")
                            .font(.system(size: 11, weight: .medium, design: .monospaced))
                            .foregroundColor(Color.fieldMindSuccess)
                    }
                }
                .padding(14)
            }
        }
    }

    // MARK: - 数据库配置
    private var databaseConfigurationView: some View {
        VStack(alignment: .leading, spacing: 24) {
            settingSection(title: "PostgreSQL") {
                VStack(alignment: .leading, spacing: 12) {
                    connectionStatusRow(service: "PostgreSQL", isConnected: true)

                    Divider()

                    settingInputRow(label: "主机", value: "localhost")
                    settingInputRow(label: "端口", value: "5432")
                    settingInputRow(label: "数据库", value: "fieldmind")
                    settingInputRow(label: "用户名", value: "postgres")

                    Button {
                        // 测试连接
                    } label: {
                        Text("测试连接")
                            .font(.system(size: 12))
                            .foregroundColor(Color.fieldMindPrimary)
                            .padding(.horizontal, 16)
                            .padding(.vertical, 8)
                            .background(Color.fieldMindPrimary.opacity(0.1))
                            .cornerRadius(6)
                    }
                    .buttonStyle(PlainButtonStyle())
                }
                .padding(14)
            }

            settingSection(title: "Qdrant (向量数据库)") {
                VStack(alignment: .leading, spacing: 12) {
                    connectionStatusRow(service: "Qdrant", isConnected: true)

                    Divider()

                    settingInputRow(label: "主机", value: "localhost")
                    settingInputRow(label: "端口", value: "6333")

                    HStack {
                        Text("集合数量")
                            .font(.system(size: 12))
                            .foregroundColor(Color.fieldMindText)
                        Spacer()
                        Text("3")
                            .font(.system(size: 11, weight: .medium))
                            .foregroundColor(Color.fieldMindSuccess)
                    }
                }
                .padding(14)
            }

            settingSection(title: "Neo4j (知识图谱)") {
                VStack(alignment: .leading, spacing: 12) {
                    connectionStatusRow(service: "Neo4j", isConnected: false)

                    Divider()

                    settingInputRow(label: "URI", value: "bolt://localhost:7687")
                    settingInputRow(label: "用户名", value: "neo4j")

                    Text("未连接：请检查Neo4j服务是否启动")
                        .font(.system(size: 10))
                        .foregroundColor(Color.fieldMindDanger)
                        .padding(.horizontal, 12)
                        .padding(.vertical, 8)
                        .background(Color.fieldMindDanger.opacity(0.08))
                        .cornerRadius(6)
                }
                .padding(14)
            }
        }
    }

    // MARK: - 系统设置
    private var systemSettingsView: some View {
        VStack(alignment: .leading, spacing: 24) {
            settingSection(title: "工作模式") {
                VStack(spacing: 16) {
                    Toggle("自动处理上传的文档", isOn: .constant(true))
                        .font(.system(size: 12))
                        .toggleStyle(SwitchToggleStyle(tint: Color.fieldMindPrimary))

                    Toggle("自动生成知识图谱", isOn: .constant(true))
                        .font(.system(size: 12))
                        .toggleStyle(SwitchToggleStyle(tint: Color.fieldMindPrimary))

                    Toggle("启用长期记忆", isOn: .constant(true))
                        .font(.system(size: 12))
                        .toggleStyle(SwitchToggleStyle(tint: Color.fieldMindPrimary))
                }
                .padding(14)
            }

            settingSection(title: "界面设置") {
                VStack(spacing: 16) {
                    HStack {
                        Text("语言")
                            .font(.system(size: 12))
                            .foregroundColor(Color.fieldMindText)
                        Spacer()
                        Picker("", selection: .constant("zh-CN")) {
                            Text("简体中文").tag("zh-CN")
                            Text("English").tag("en-US")
                        }
                        .pickerStyle(MenuPickerStyle())
                        .frame(width: 120)
                    }

                    Divider()

                    HStack {
                        Text("字体大小")
                            .font(.system(size: 12))
                            .foregroundColor(Color.fieldMindText)
                        Spacer()
                        Picker("", selection: .constant("medium")) {
                            Text("小").tag("small")
                            Text("中").tag("medium")
                            Text("大").tag("large")
                        }
                        .pickerStyle(SegmentedPickerStyle())
                        .frame(width: 150)
                    }
                }
                .padding(14)
            }

            settingSection(title: "通知设置") {
                VStack(spacing: 16) {
                    Toggle("任务完成通知", isOn: .constant(true))
                        .font(.system(size: 12))
                        .toggleStyle(SwitchToggleStyle(tint: Color.fieldMindPrimary))

                    Toggle("错误警告通知", isOn: .constant(true))
                        .font(.system(size: 12))
                        .toggleStyle(SwitchToggleStyle(tint: Color.fieldMindPrimary))

                    Toggle("后台任务提醒", isOn: .constant(false))
                        .font(.system(size: 12))
                        .toggleStyle(SwitchToggleStyle(tint: Color.fieldMindPrimary))
                }
                .padding(14)
            }

            settingSection(title: "存储设置") {
                VStack(spacing: 12) {
                    HStack {
                        Text("数据存储路径")
                            .font(.system(size: 12))
                            .foregroundColor(Color.fieldMindText)
                        Spacer()
                        Button {
                            // 选择路径
                        } label: {
                            Text("选择")
                                .font(.system(size: 11))
                                .foregroundColor(Color.fieldMindPrimary)
                        }
                        .buttonStyle(PlainButtonStyle())
                    }

                    Text("~/Documents/FieldMind")
                        .font(.system(size: 10, design: .monospaced))
                        .foregroundColor(Color.fieldMindText.opacity(0.6))
                        .frame(maxWidth: .infinity, alignment: .leading)

                    Divider()

                    HStack {
                        Text("已使用空间")
                            .font(.system(size: 12))
                            .foregroundColor(Color.fieldMindText)
                        Spacer()
                        Text("2.3 GB")
                            .font(.system(size: 11, weight: .medium))
                            .foregroundColor(Color.fieldMindSuccess)
                    }
                }
                .padding(14)
            }
        }
    }

    // MARK: - 关于
    private var aboutView: some View {
        VStack(alignment: .leading, spacing: 24) {
            // Logo和版本
            VStack(spacing: 16) {
                HStack(spacing: 12) {
                    Image(systemName: "leaf.fill")
                        .font(.system(size: 48))
                        .foregroundColor(Color.fieldMindPrimary)

                    VStack(alignment: .leading, spacing: 6) {
                        Text("FieldMind")
                            .font(.system(size: 20, weight: .bold))
                            .foregroundColor(Color.fieldMindText)

                        Text("田野调查智能助手")
                            .font(.system(size: 12))
                            .foregroundColor(Color.fieldMindText.opacity(0.7))
                    }
                }
                .frame(maxWidth: .infinity)
                .padding(24)
                .background(Color.white)
                .cornerRadius(12)

                VStack(spacing: 12) {
                    infoRow(label: "版本号", value: "1.0.0 (Build 2024.03.20)")
                    Divider()
                    infoRow(label: "系统要求", value: "macOS 14.0+")
                    Divider()
                    infoRow(label: "开发团队", value: "FieldMind Research Lab")
                }
                .padding(16)
                .background(Color.white)
                .cornerRadius(10)
            }

            // 功能说明
            settingSection(title: "核心功能") {
                VStack(alignment: .leading, spacing: 12) {
                    featureItem(icon: "doc.fill", title: "智能文档处理", description: "自动提取关键信息，构建知识体系")
                    Divider()
                    featureItem(icon: "brain", title: "AI智能助手", description: "基于长期记忆的专业对话")
                    Divider()
                    featureItem(icon: "network", title: "知识图谱", description: "可视化展示复杂关系网络")
                    Divider()
                    featureItem(icon: "doc.text.fill", title: "三层报告", description: "从信息整理到商业推演")
                }
                .padding(14)
            }

            // 链接
            settingSection(title: "帮助与支持") {
                VStack(spacing: 0) {
                    Button {
                        // 打开文档
                    } label: {
                        HStack {
                            Image(systemName: "book")
                                .font(.system(size: 12))
                                .foregroundColor(Color.fieldMindPrimary)
                            Text("使用文档")
                                .font(.system(size: 12))
                                .foregroundColor(Color.fieldMindText)
                            Spacer()
                            Image(systemName: "arrow.up.right")
                                .font(.system(size: 10))
                                .foregroundColor(Color.fieldMindText.opacity(0.4))
                        }
                        .padding(14)
                    }
                    .buttonStyle(PlainButtonStyle())

                    Divider()

                    Button {
                        // 反馈问题
                    } label: {
                        HStack {
                            Image(systemName: "exclamationmark.bubble")
                                .font(.system(size: 12))
                                .foregroundColor(Color.fieldMindPrimary)
                            Text("反馈问题")
                                .font(.system(size: 12))
                                .foregroundColor(Color.fieldMindText)
                            Spacer()
                            Image(systemName: "arrow.up.right")
                                .font(.system(size: 10))
                                .foregroundColor(Color.fieldMindText.opacity(0.4))
                        }
                        .padding(14)
                    }
                    .buttonStyle(PlainButtonStyle())

                    Divider()

                    Button {
                        // 检查更新
                    } label: {
                        HStack {
                            Image(systemName: "arrow.down.circle")
                                .font(.system(size: 12))
                                .foregroundColor(Color.fieldMindPrimary)
                            Text("检查更新")
                                .font(.system(size: 12))
                                .foregroundColor(Color.fieldMindText)
                            Spacer()
                            Image(systemName: "chevron.right")
                                .font(.system(size: 10))
                                .foregroundColor(Color.fieldMindText.opacity(0.4))
                        }
                        .padding(14)
                    }
                    .buttonStyle(PlainButtonStyle())
                }
            }

            // 版权信息
            Text("© 2024 FieldMind. All rights reserved.")
                .font(.system(size: 10))
                .foregroundColor(Color.fieldMindText.opacity(0.5))
                .frame(maxWidth: .infinity)
                .padding(.top, 20)
        }
    }

    // MARK: - 辅助视图组件
    private func settingSection<Content: View>(title: String, @ViewBuilder content: () -> Content) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(title)
                .font(.system(size: 13, weight: .bold))
                .foregroundColor(Color.fieldMindText)

            content()
                .background(Color.white)
                .cornerRadius(10)
        }
    }

    private func settingRow(label: String, value: String) -> some View {
        HStack {
            Text(label)
                .font(.system(size: 12))
                .foregroundColor(Color.fieldMindText)
            Spacer()
            Text(value)
                .font(.system(size: 12))
                .foregroundColor(Color.fieldMindText.opacity(0.7))
        }
        .padding(.horizontal, 14)
    }

    private func settingInputRow(label: String, value: String) -> some View {
        HStack {
            Text(label)
                .font(.system(size: 11))
                .foregroundColor(Color.fieldMindText.opacity(0.7))
                .frame(width: 60, alignment: .leading)

            TextField(value, text: .constant(value))
                .textFieldStyle(CustomTextFieldStyle())
        }
    }

    private func connectionStatusRow(service: String, isConnected: Bool) -> some View {
        HStack {
            Text(service)
                .font(.system(size: 12, weight: .semibold))
                .foregroundColor(Color.fieldMindText)

            Spacer()

            HStack(spacing: 6) {
                Circle()
                    .fill(isConnected ? Color.fieldMindSuccess : Color.fieldMindDanger)
                    .frame(width: 8, height: 8)

                Text(isConnected ? "已连接" : "未连接")
                    .font(.system(size: 11))
                    .foregroundColor(isConnected ? Color.fieldMindSuccess : Color.fieldMindDanger)
            }
            .padding(.horizontal, 10)
            .padding(.vertical, 5)
            .background((isConnected ? Color.fieldMindSuccess : Color.fieldMindDanger).opacity(0.1))
            .cornerRadius(5)
        }
    }

    private func infoRow(label: String, value: String) -> some View {
        HStack {
            Text(label)
                .font(.system(size: 12))
                .foregroundColor(Color.fieldMindText.opacity(0.7))
            Spacer()
            Text(value)
                .font(.system(size: 12))
                .foregroundColor(Color.fieldMindText)
        }
    }

    private func featureItem(icon: String, title: String, description: String) -> some View {
        HStack(spacing: 12) {
            Image(systemName: icon)
                .font(.system(size: 16))
                .foregroundColor(Color.fieldMindPrimary)
                .frame(width: 32, height: 32)
                .background(Color.fieldMindPrimary.opacity(0.1))
                .cornerRadius(6)

            VStack(alignment: .leading, spacing: 4) {
                Text(title)
                    .font(.system(size: 12, weight: .semibold))
                    .foregroundColor(Color.fieldMindText)

                Text(description)
                    .font(.system(size: 10))
                    .foregroundColor(Color.fieldMindText.opacity(0.6))
            }

            Spacer()
        }
    }
}
