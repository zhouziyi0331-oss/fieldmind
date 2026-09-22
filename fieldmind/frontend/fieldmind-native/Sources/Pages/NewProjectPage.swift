import SwiftUI

struct NewProjectPage: View {
    @EnvironmentObject var appState: AppState
    @State private var projectName = ""
    @State private var projectDescription = ""
    @State private var selectedTemplate: ProjectTemplate = .blank
    @State private var selectedColor: ProjectColor = .blue
    @State private var enableAI = true
    @State private var enableAutoKeyword = true
    @State private var enableAutoTranscript = true
    @State private var isCreating = false

    enum ProjectTemplate: String, CaseIterable {
        case blank = "空白项目"
        case research = "学术研究"
        case interview = "访谈调研"
        case meeting = "会议记录"
        case course = "课程学习"

        var icon: String {
            switch self {
            case .blank: return "doc"
            case .research: return "book.fill"
            case .interview: return "mic.fill"
            case .meeting: return "person.3.fill"
            case .course: return "graduationcap.fill"
            }
        }

        var description: String {
            switch self {
            case .blank: return "从零开始，自由配置"
            case .research: return "适合论文、研究项目"
            case .interview: return "访谈录音自动整理"
            case .meeting: return "会议纪要智能生成"
            case .course: return "课程笔记系统化"
            }
        }
    }

    enum ProjectColor: String, CaseIterable {
        case blue = "蓝色"
        case green = "绿色"
        case purple = "紫色"
        case orange = "橙色"
        case red = "红色"
        case pink = "粉色"

        var color: Color {
            switch self {
            case .blue: return .fmA1
            case .green: return .fmA2
            case .purple: return Color(hex: "9b87f5")
            case .orange: return Color(hex: "f59e0b")
            case .red: return Color(hex: "ef4444")
            case .pink: return Color(hex: "ec4899")
            }
        }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            // 页头
            sectionHeader

            Spacer().frame(height: 20)

            // 表单区域
            ScrollView {
                VStack(spacing: 20) {
                    // 基本信息
                    basicInfoSection

                    // 模板选择
                    templateSection

                    // 项目颜色
                    colorSection

                    // AI 功能配置
                    aiSettingsSection

                    // 操作按钮
                    actionButtons
                }
                .frame(maxWidth: 800)
            }
        }
    }

    // MARK: - Section Header
    private var sectionHeader: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack(spacing: 7) {
                Circle()
                    .fill(Color.fmA1)
                    .frame(width: 6, height: 6)
                    .shadow(color: Color.fmA1, radius: 4)

                Text("新建项目")
                    .font(.system(size: 14, weight: .heavy))
                    .foregroundColor(.fmText)
                    .tracking(-0.01)
            }

            Text("创建新的研究项目，开启智能材料管理")
                .font(.system(size: 10))
                .foregroundColor(.fmText3)
                .tracking(0.02)
        }
        .padding(.bottom, 8)
    }

    // MARK: - Basic Info Section
    private var basicInfoSection: some View {
        FMCard {
            VStack(alignment: .leading, spacing: 16) {
                Text("基本信息")
                    .font(.system(size: 13, weight: .bold))
                    .foregroundColor(.fmText)

                // 项目名称
                VStack(alignment: .leading, spacing: 6) {
                    HStack {
                        Text("项目名称")
                            .font(.system(size: 11, weight: .medium))
                            .foregroundColor(.fmText2)

                        Text("*")
                            .font(.system(size: 11, weight: .bold))
                            .foregroundColor(.red)
                    }

                    TextField("例如：2024 用户访谈研究", text: $projectName)
                        .textFieldStyle(.plain)
                        .font(.system(size: 12))
                        .foregroundColor(.fmText)
                        .padding(EdgeInsets(top: 9, leading: 12, bottom: 9, trailing: 12))
                        .background(Color.fmSurface2)
                        .cornerRadius(8)
                        .overlay(
                            RoundedRectangle(cornerRadius: 8)
                                .stroke(projectName.isEmpty ? Color.fmBorder2 : Color.fmA1, lineWidth: 1)
                        )
                }

                // 项目描述
                VStack(alignment: .leading, spacing: 6) {
                    Text("项目描述")
                        .font(.system(size: 11, weight: .medium))
                        .foregroundColor(.fmText2)

                    ZStack(alignment: .topLeading) {
                        if projectDescription.isEmpty {
                            Text("简要描述项目目标和内容...")
                                .font(.system(size: 12))
                                .foregroundColor(.fmText4)
                                .padding(EdgeInsets(top: 9, leading: 12, bottom: 0, trailing: 0))
                        }

                        TextEditor(text: $projectDescription)
                            .font(.system(size: 12))
                            .foregroundColor(.fmText)
                            .scrollContentBackground(.hidden)
                            .frame(height: 80)
                            .padding(EdgeInsets(top: 4, leading: 8, bottom: 4, trailing: 8))
                    }
                    .background(Color.fmSurface2)
                    .cornerRadius(8)
                    .overlay(
                        RoundedRectangle(cornerRadius: 8)
                            .stroke(Color.fmBorder2, lineWidth: 1)
                    )
                }
            }
            .padding(18)
        }
    }

    // MARK: - Template Section
    private var templateSection: some View {
        FMCard {
            VStack(alignment: .leading, spacing: 16) {
                HStack {
                    Text("选择模板")
                        .font(.system(size: 13, weight: .bold))
                        .foregroundColor(.fmText)

                    Spacer()

                    Text("可在创建后修改")
                        .font(.system(size: 9))
                        .foregroundColor(.fmText4)
                }

                LazyVGrid(
                    columns: [
                        GridItem(.flexible(), spacing: 12),
                        GridItem(.flexible(), spacing: 12),
                        GridItem(.flexible(), spacing: 12)
                    ],
                    spacing: 12
                ) {
                    ForEach(ProjectTemplate.allCases, id: \.self) { template in
                        TemplateCard(
                            template: template,
                            isSelected: selectedTemplate == template,
                            action: { selectedTemplate = template }
                        )
                    }
                }
            }
            .padding(18)
        }
    }

    // MARK: - Color Section
    private var colorSection: some View {
        FMCard {
            VStack(alignment: .leading, spacing: 16) {
                Text("项目颜色")
                    .font(.system(size: 13, weight: .bold))
                    .foregroundColor(.fmText)

                HStack(spacing: 12) {
                    ForEach(ProjectColor.allCases, id: \.self) { color in
                        ColorOption(
                            color: color,
                            isSelected: selectedColor == color,
                            action: { selectedColor = color }
                        )
                    }
                }
            }
            .padding(18)
        }
    }

    // MARK: - AI Settings Section
    private var aiSettingsSection: some View {
        FMCard {
            VStack(alignment: .leading, spacing: 16) {
                HStack {
                    Text("AI 功能配置")
                        .font(.system(size: 13, weight: .bold))
                        .foregroundColor(.fmText)

                    Spacer()

                    Toggle("", isOn: $enableAI)
                        .toggleStyle(.switch)
                        .tint(.fmA1)
                        .scaleEffect(0.8)
                }

                if enableAI {
                    VStack(spacing: 12) {
                        AIFeatureToggle(
                            isOn: $enableAutoTranscript,
                            title: "自动语音转录",
                            description: "音视频材料自动转为文字",
                            icon: "waveform"
                        )

                        AIFeatureToggle(
                            isOn: $enableAutoKeyword,
                            title: "智能关键词提炼",
                            description: "自动识别并提取核心关键词",
                            icon: "tag.fill"
                        )
                    }
                    .padding(EdgeInsets(top: 8, leading: 12, bottom: 8, trailing: 12))
                    .background(Color.fmSurface2)
                    .cornerRadius(10)
                }
            }
            .padding(18)
        }
    }

    // MARK: - Action Buttons
    private var actionButtons: some View {
        HStack(spacing: 12) {
            Button(action: {
                appState.navigateTo(.projects)
            }) {
                Text("取消")
                    .font(.system(size: 12, weight: .semibold))
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(FMButtonStyle(style: .outline, size: .medium))

            Button(action: createProject) {
                HStack(spacing: 6) {
                    if isCreating {
                        ProgressView()
                            .scaleEffect(0.7)
                            .tint(.white)
                    } else {
                        Image(systemName: "checkmark")
                            .font(.system(size: 11, weight: .bold))
                    }

                    Text(isCreating ? "创建中..." : "创建项目")
                        .font(.system(size: 12, weight: .semibold))
                }
                .frame(maxWidth: .infinity)
            }
            .buttonStyle(FMButtonStyle(style: .primary, size: .medium))
            .disabled(projectName.isEmpty || isCreating)
        }
        .padding(.top, 10)
    }

    // MARK: - Actions
    private func createProject() {
        guard !projectName.isEmpty else { return }

        isCreating = true

        Task {
            do {
                let response = try await ProjectService.shared.createProject(
                    name: projectName,
                    description: projectDescription.isEmpty ? nil : projectDescription
                )

                await MainActor.run {
                    // 直接使用API返回的Project对象
                    appState.projects.insert(response, at: 0)
                    appState.currentProject = response
                    isCreating = false

                    appState.showToast(message: "项目创建成功：\(projectName)", type: .success)
                    appState.navigateTo(.overview)
                }
            } catch {
                await MainActor.run {
                    isCreating = false
                    appState.showToast(message: "创建失败：\(error.localizedDescription)", type: .error)
                }
            }
        }
    }
}

// MARK: - Template Card
struct TemplateCard: View {
    let template: NewProjectPage.ProjectTemplate
    let isSelected: Bool
    let action: () -> Void
    @State private var isHovered = false

    var body: some View {
        Button(action: action) {
            VStack(spacing: 10) {
                ZStack {
                    RoundedRectangle(cornerRadius: 12)
                        .fill(isSelected ? Color.fmA1.opacity(0.15) : Color.fmSurface2)
                        .frame(height: 60)

                    Image(systemName: template.icon)
                        .font(.system(size: 24, weight: .medium))
                        .foregroundColor(isSelected ? .fmA1 : .fmText3)
                }

                VStack(spacing: 4) {
                    Text(template.rawValue)
                        .font(.system(size: 11, weight: .semibold))
                        .foregroundColor(isSelected ? .fmA1 : .fmText)

                    Text(template.description)
                        .font(.system(size: 9))
                        .foregroundColor(.fmText3)
                        .multilineTextAlignment(.center)
                        .lineLimit(2)
                }
            }
            .padding(12)
            .background(Color.fmSurface)
            .cornerRadius(10)
            .overlay(
                RoundedRectangle(cornerRadius: 10)
                    .stroke(isSelected ? Color.fmA1 : (isHovered ? Color.fmBorder : Color.fmBorder2), lineWidth: isSelected ? 2 : 1)
            )
            .scaleEffect(isHovered ? 1.02 : 1.0)
            .animation(.spring(response: 0.3, dampingFraction: 0.7), value: isHovered)
        }
        .buttonStyle(.plain)
        .onHover { hovering in
            isHovered = hovering
        }
    }
}

// MARK: - Color Option
struct ColorOption: View {
    let color: NewProjectPage.ProjectColor
    let isSelected: Bool
    let action: () -> Void
    @State private var isHovered = false

    var body: some View {
        Button(action: action) {
            VStack(spacing: 6) {
                ZStack {
                    Circle()
                        .fill(color.color)
                        .frame(width: 40, height: 40)

                    if isSelected {
                        Image(systemName: "checkmark")
                            .font(.system(size: 16, weight: .bold))
                            .foregroundColor(.white)
                    }
                }
                .overlay(
                    Circle()
                        .stroke(isSelected ? Color.white : Color.clear, lineWidth: 3)
                )
                .shadow(color: color.color.opacity(isSelected ? 0.4 : 0.2), radius: 6, x: 0, y: 2)

                Text(color.rawValue)
                    .font(.system(size: 9))
                    .foregroundColor(isSelected ? .fmText : .fmText3)
            }
            .scaleEffect(isHovered ? 1.1 : 1.0)
            .animation(.spring(response: 0.3, dampingFraction: 0.7), value: isHovered)
        }
        .buttonStyle(.plain)
        .onHover { hovering in
            isHovered = hovering
        }
    }
}

// MARK: - AI Feature Toggle
struct AIFeatureToggle: View {
    @Binding var isOn: Bool
    let title: String
    let description: String
    let icon: String

    var body: some View {
        HStack(spacing: 12) {
            ZStack {
                Circle()
                    .fill(isOn ? Color.fmA1.opacity(0.15) : Color.fmSurface)
                    .frame(width: 36, height: 36)

                Image(systemName: icon)
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(isOn ? .fmA1 : .fmText3)
            }

            VStack(alignment: .leading, spacing: 3) {
                Text(title)
                    .font(.system(size: 11, weight: .semibold))
                    .foregroundColor(.fmText)

                Text(description)
                    .font(.system(size: 9))
                    .foregroundColor(.fmText3)
            }

            Spacer()

            Toggle("", isOn: $isOn)
                .toggleStyle(.switch)
                .tint(.fmA1)
                .scaleEffect(0.8)
        }
    }
}
