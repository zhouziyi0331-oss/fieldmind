import SwiftUI

struct SettingsPage: View {
    @EnvironmentObject private var fileAccessManager: FileAccessManager
    @State private var selectedCategory: SettingsCategory = .general
    @State private var searchText = ""
    @State private var showResetAlert = false
    @State private var showClearCacheAlert = false

    // Settings values (mutable state for demo)
    @State private var settingsValues: [String: SettingsItem.SettingsValue] = [:]

    var filteredCategories: [SettingsCategory] {
        if searchText.isEmpty {
            return SettingsCategory.allCases
        }
        return SettingsCategory.allCases.filter { category in
            let items = SettingsData.getSettings(for: category)
            return items.contains { item in
                item.title.localizedCaseInsensitiveContains(searchText) ||
                item.description.localizedCaseInsensitiveContains(searchText)
            }
        }
    }

    var filteredSettings: [SettingsItem] {
        let items = SettingsData.getSettings(for: selectedCategory)
        if searchText.isEmpty {
            return items
        }
        return items.filter { item in
            item.title.localizedCaseInsensitiveContains(searchText) ||
            item.description.localizedCaseInsensitiveContains(searchText)
        }
    }

    var body: some View {
        HStack(spacing: 0) {
            // Left sidebar - categories
            sidebarView

            Divider()

            // Right content - settings
            contentView
        }
    }

    // MARK: - Sidebar

    var sidebarView: some View {
        VStack(alignment: .leading, spacing: 0) {
            // Header
            VStack(alignment: .leading, spacing: 8) {
                HStack(spacing: 8) {
                    Image(systemName: "gearshape.2")
                        .font(.system(size: 20, weight: .semibold))
                        .foregroundColor(Color(hex: "007AFF"))

                    Text("设置")
                        .font(.system(size: 20, weight: .semibold))
                        .foregroundColor(.fmText)
                }

                // Search box
                HStack(spacing: 8) {
                    Image(systemName: "magnifyingglass")
                        .font(.system(size: 12))
                        .foregroundColor(.fmText3)

                    TextField("搜索设置项", text: $searchText)
                        .textFieldStyle(.plain)
                        .font(.system(size: 13))
                }
                .padding(.horizontal, 12)
                .padding(.vertical, 8)
                .background(Color.fmBg2)
                .cornerRadius(8)
            }
            .padding(20)

            Divider()

            // Categories list
            ScrollView {
                VStack(spacing: 4) {
                    ForEach(filteredCategories) { category in
                        CategoryButton(
                            category: category,
                            isSelected: selectedCategory == category
                        ) {
                            selectedCategory = category
                        }
                    }
                }
                .padding(.vertical, 12)
                .padding(.horizontal, 12)
            }
        }
        .frame(width: 240)
        .background(Color.fmBg)
    }

    // MARK: - Content

    var contentView: some View {
        VStack(alignment: .leading, spacing: 0) {
            // Header
            HStack(spacing: 12) {
                Image(systemName: selectedCategory.icon)
                    .font(.system(size: 24, weight: .medium))
                    .foregroundColor(Color(hex: "007AFF"))
                    .frame(width: 48, height: 48)
                    .background(Color(hex: "007AFF").opacity(0.1))
                    .cornerRadius(12)

                VStack(alignment: .leading, spacing: 4) {
                    Text(selectedCategory.rawValue)
                        .font(.system(size: 20, weight: .semibold))
                        .foregroundColor(.fmText)

                    Text(categoryDescription(selectedCategory))
                        .font(.system(size: 13))
                        .foregroundColor(.fmText2)
                }

                Spacer()
            }
            .padding(24)

            Divider()

            // Settings list
            ScrollView {
                if filteredSettings.isEmpty {
                    emptyStateView
                } else {
                    VStack(spacing: 16) {
                        ForEach(filteredSettings) { item in
                            SettingsItemRow(
                                item: item,
                                value: settingsValues[item.id] ?? item.value,
                                onValueChange: { newValue in
                                    settingsValues[item.id] = newValue
                                },
                                onAction: {
                                    handleAction(item)
                                }
                            )
                        }
                    }
                    .padding(24)
                }
            }
        }
        .background(Color.white)
        .alert("重置设置", isPresented: $showResetAlert) {
            Button("取消", role: .cancel) { }
            Button("重置", role: .destructive) {
                // Reset all settings
                settingsValues.removeAll()
            }
        } message: {
            Text("确定要恢复所有设置到默认值吗？此操作不可撤销。")
        }
        .alert("清除缓存", isPresented: $showClearCacheAlert) {
            Button("取消", role: .cancel) { }
            Button("清除", role: .destructive) {
                // Clear cache
            }
        } message: {
            Text("确定要删除所有缓存数据吗？")
        }
    }

    var emptyStateView: some View {
        VStack(spacing: 16) {
            Image(systemName: "magnifyingglass")
                .font(.system(size: 48))
                .foregroundColor(.fmText3)

            Text("未找到匹配的设置项")
                .font(.system(size: 15, weight: .medium))
                .foregroundColor(.fmText2)

            Text("尝试使用其他关键词搜索")
                .font(.system(size: 13))
                .foregroundColor(.fmText3)
        }
        .frame(maxWidth: .infinity)
        .padding(.top, 80)
    }

    // MARK: - Helpers

    func categoryDescription(_ category: SettingsCategory) -> String {
        switch category {
        case .general: return "应用程序通用设置"
        case .model: return "AI 模型和 API 配置"
        case .data: return "数据存储和缓存管理"
        case .appearance: return "界面外观和语言设置"
        case .advanced: return "高级选项和调试工具"
        case .about: return "版本信息和反馈渠道"
        }
    }

    func handleAction(_ item: SettingsItem) {
        switch item.id {
        case "authorize_files":
            let didAuthorize = fileAccessManager.authorizeCommonFolder()
            if didAuthorize {
                ToastManager.shared.success("文件夹授权成功：\(fileAccessManager.authorizationSummary)")
            } else {
                ToastManager.shared.info("未完成文件夹授权")
            }
        case "reset_settings":
            showResetAlert = true
        case "clear_cache":
            showClearCacheAlert = true
        case "export_data":
            // Handle export
            print("Export data")
        case "website":
            // Open website
            print("Open website")
        case "feedback":
            // Open feedback
            print("Open feedback")
        case "license":
            // Show license
            print("Show license")
        case "check_update":
            // Check for updates
            print("Check for updates")
        default:
            break
        }
    }
}

// MARK: - Category Button

struct CategoryButton: View {
    let category: SettingsCategory
    let isSelected: Bool
    let action: () -> Void

    @State private var isHovered = false

    var body: some View {
        Button(action: action) {
            HStack(spacing: 12) {
                Image(systemName: category.icon)
                    .font(.system(size: 16, weight: .medium))
                    .foregroundColor(isSelected ? Color(hex: "007AFF") : .fmText2)
                    .frame(width: 32, height: 32)
                    .background(isSelected ? Color(hex: "007AFF").opacity(0.1) : (isHovered ? Color.fmBg2 : Color.clear))
                    .cornerRadius(8)

                Text(category.name)
                    .font(.system(size: 14, weight: isSelected ? .medium : .regular))
                    .foregroundColor(isSelected ? .fmText : .fmText2)

                Spacer()

                if isSelected {
                    RoundedRectangle(cornerRadius: 2)
                        .fill(Color(hex: "007AFF"))
                        .frame(width: 3)
                }
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
            .background(isSelected ? Color(hex: "007AFF").opacity(0.05) : (isHovered ? Color.fmBg2 : Color.clear))
            .cornerRadius(8)
        }
        .buttonStyle(.plain)
        .onHover { hovering in
            isHovered = hovering
        }
    }
}

// MARK: - Settings Item Row

struct SettingsItemRow: View {
    let item: SettingsItem
    let value: SettingsItem.SettingsValue
    let onValueChange: (SettingsItem.SettingsValue) -> Void
    let onAction: () -> Void

    var body: some View {
        HStack(alignment: .top, spacing: 16) {
            // Icon
            Image(systemName: item.icon ?? "gearshape")
                .font(.system(size: 18, weight: .medium))
                .foregroundColor(Color(hex: "007AFF"))
                .frame(width: 40, height: 40)
                .background(Color(hex: "007AFF").opacity(0.1))
                .cornerRadius(10)

            // Content
            VStack(alignment: .leading, spacing: 8) {
                Text(item.title)
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(.fmText)

                Text(item.description)
                    .font(.system(size: 13))
                    .foregroundColor(.fmText2)
                    .fixedSize(horizontal: false, vertical: true)

                // Control based on type
                controlView
            }

            Spacer()
        }
        .padding(16)
        .background(Color.fmBg)
        .cornerRadius(12)
    }

    @ViewBuilder
    var controlView: some View {
        switch item.type {
        case .toggle:
            if case .bool(let isOn) = value {
                SettingsToggle(isOn: isOn) { newValue in
                    onValueChange(.bool(newValue))
                }
            }

        case .text:
            if case .string(let text) = value {
                SettingsTextField(text: text) { newValue in
                    onValueChange(.string(newValue))
                }
            }

        case .number:
            if case .int(let number) = value {
                SettingsNumberField(value: number) { newValue in
                    onValueChange(.int(newValue))
                }
            }

        case .select:
            EmptyView()

        case .selection:
            if case .selection(let current, let options) = value {
                SettingsMenuPicker(current: current, options: options) { newValue in
                    onValueChange(.selection(newValue, options))
                }
            }

        case .action:
            SettingsActionButton(title: "执行", action: onAction)

        case .info:
            EmptyView()
        }
    }
}

// MARK: - Settings Controls

struct SettingsToggle: View {
    let isOn: Bool
    let onChange: (Bool) -> Void

    var body: some View {
        Toggle("", isOn: Binding(
            get: { isOn },
            set: { onChange($0) }
        ))
        .toggleStyle(SwitchToggleStyle(tint: Color(hex: "007AFF")))
        .labelsHidden()
    }
}

struct SettingsTextField: View {
    let text: String
    let onChange: (String) -> Void

    @State private var editableText: String

    init(text: String, onChange: @escaping (String) -> Void) {
        self.text = text
        self.onChange = onChange
        self._editableText = State(initialValue: text)
    }

    var body: some View {
        TextField("", text: $editableText, onCommit: {
            onChange(editableText)
        })
        .textFieldStyle(.plain)
        .font(.system(size: 13))
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
        .background(Color.white)
        .cornerRadius(6)
        .overlay(
            RoundedRectangle(cornerRadius: 6)
                .stroke(Color.fmBorder, lineWidth: 1)
        )
        .frame(maxWidth: 400)
    }
}

struct SettingsNumberField: View {
    let value: Int
    let onChange: (Int) -> Void

    @State private var editableValue: String

    init(value: Int, onChange: @escaping (Int) -> Void) {
        self.value = value
        self.onChange = onChange
        self._editableValue = State(initialValue: "\(value)")
    }

    var body: some View {
        HStack(spacing: 8) {
            TextField("", text: $editableValue, onCommit: {
                if let intValue = Int(editableValue) {
                    onChange(intValue)
                } else {
                    editableValue = "\(value)"
                }
            })
            .textFieldStyle(.plain)
            .font(.system(size: 13))
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
            .background(Color.white)
            .cornerRadius(6)
            .overlay(
                RoundedRectangle(cornerRadius: 6)
                    .stroke(Color.fmBorder, lineWidth: 1)
            )
            .frame(width: 100)

            // Stepper buttons
            VStack(spacing: 2) {
                Button(action: {
                    let newValue = value + 1
                    editableValue = "\(newValue)"
                    onChange(newValue)
                }) {
                    Image(systemName: "chevron.up")
                        .font(.system(size: 10))
                        .foregroundColor(.fmText2)
                        .frame(width: 24, height: 14)
                }
                .buttonStyle(.plain)

                Button(action: {
                    let newValue = max(0, value - 1)
                    editableValue = "\(newValue)"
                    onChange(newValue)
                }) {
                    Image(systemName: "chevron.down")
                        .font(.system(size: 10))
                        .foregroundColor(.fmText2)
                        .frame(width: 24, height: 14)
                }
                .buttonStyle(.plain)
            }
            .background(Color.fmBg2)
            .cornerRadius(4)
        }
    }
}

struct SettingsMenuPicker: View {
    let current: String
    let options: [String]
    let onChange: (String) -> Void

    var body: some View {
        Menu {
            ForEach(options, id: \.self) { option in
                Button(action: {
                    onChange(option)
                }) {
                    HStack {
                        Text(option)
                        if option == current {
                            Image(systemName: "checkmark")
                        }
                    }
                }
            }
        } label: {
            HStack(spacing: 8) {
                Text(current)
                    .font(.system(size: 13))
                    .foregroundColor(.fmText)

                Image(systemName: "chevron.up.chevron.down")
                    .font(.system(size: 11))
                    .foregroundColor(.fmText3)
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
            .background(Color.white)
            .cornerRadius(6)
            .overlay(
                RoundedRectangle(cornerRadius: 6)
                    .stroke(Color.fmBorder, lineWidth: 1)
            )
        }
        .menuStyle(.borderlessButton)
        .frame(maxWidth: 200, alignment: .leading)
    }
}

struct SettingsActionButton: View {
    let title: String
    let action: () -> Void

    @State private var isHovered = false

    var body: some View {
        Button(action: action) {
            Text(title)
                .font(.system(size: 13, weight: .medium))
                .foregroundColor(.white)
                .padding(.horizontal, 20)
                .padding(.vertical, 8)
                .background(Color(hex: "007AFF"))
                .cornerRadius(6)
        }
        .buttonStyle(.plain)
        .scaleEffect(isHovered ? 1.02 : 1.0)
        .animation(.easeInOut(duration: 0.15), value: isHovered)
        .onHover { hovering in
            isHovered = hovering
        }
    }
}
