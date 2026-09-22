import SwiftUI

struct SkillPage: View {
    let projectId: Int
    @StateObject private var viewModel = SkillViewModel()
    @State private var searchText = ""

    var filteredSkills: [SkillService.SkillInfo] {
        if searchText.isEmpty {
            return viewModel.availableSkills
        }
        return viewModel.availableSkills.filter { skill in
            skill.name.localizedCaseInsensitiveContains(searchText) ||
            skill.description.localizedCaseInsensitiveContains(searchText) ||
            skill.dimensions.contains { $0.localizedCaseInsensitiveContains(searchText) }
        }
    }

    var body: some View {
        VStack(spacing: 0) {
            headerView
            Divider()

            if let errorMessage = viewModel.errorMessage {
                errorBanner(errorMessage)
            }

            if let successMessage = viewModel.successMessage {
                successBanner(successMessage)
            }

            if viewModel.isLoading {
                loadingView
            } else if viewModel.availableSkills.isEmpty {
                emptyStateView
            } else {
                contentView
            }
        }
        .task {
            await viewModel.loadSkills(projectId: projectId)
        }
    }

    private var headerView: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text("技能配置")
                    .font(.system(size: 24, weight: .semibold))
                    .foregroundColor(Color.fmText)

                Text("配置项目的智能分析技能")
                    .font(.system(size: 14))
                    .foregroundColor(Color.fmText3)
            }

            Spacer()

            Button(action: {
                Task {
                    await viewModel.saveConfig(projectId: projectId)
                }
            }) {
                HStack(spacing: 6) {
                    if viewModel.isSaving {
                        ProgressView()
                            .scaleEffect(0.7)
                            .frame(width: 14, height: 14)
                    } else {
                        Image(systemName: "checkmark.circle.fill")
                            .font(.system(size: 14))
                    }
                    Text(viewModel.isSaving ? "保存中..." : "保存配置")
                        .font(.system(size: 14, weight: .medium))
                }
                .foregroundColor(.white)
                .padding(.horizontal, 16)
                .padding(.vertical, 8)
                .background(Color.blue)
                .cornerRadius(8)
            }
            .buttonStyle(PlainButtonStyle())
            .disabled(viewModel.isSaving)
        }
        .padding(.horizontal, 24)
        .padding(.vertical, 20)
        .background(Color.fmBg)
    }

    private func errorBanner(_ message: String) -> some View {
        HStack(spacing: 12) {
            Image(systemName: "exclamationmark.triangle.fill")
                .font(.system(size: 16))
                .foregroundColor(.orange)

            Text(message)
                .font(.system(size: 14))
                .foregroundColor(Color.fmText)

            Spacer()

            Button(action: {
                viewModel.errorMessage = nil
            }) {
                Image(systemName: "xmark.circle.fill")
                    .font(.system(size: 16))
                    .foregroundColor(Color.fmText3)
            }
            .buttonStyle(PlainButtonStyle())
        }
        .padding(16)
        .background(Color.orange.opacity(0.1))
    }

    private func successBanner(_ message: String) -> some View {
        HStack(spacing: 12) {
            Image(systemName: "checkmark.circle.fill")
                .font(.system(size: 16))
                .foregroundColor(.green)

            Text(message)
                .font(.system(size: 14))
                .foregroundColor(Color.fmText)

            Spacer()

            Button(action: {
                viewModel.successMessage = nil
            }) {
                Image(systemName: "xmark.circle.fill")
                    .font(.system(size: 16))
                    .foregroundColor(Color.fmText3)
            }
            .buttonStyle(PlainButtonStyle())
        }
        .padding(16)
        .background(Color.green.opacity(0.1))
    }

    private var loadingView: some View {
        VStack(spacing: 16) {
            ProgressView()
                .scaleEffect(1.2)

            Text("加载技能配置中...")
                .font(.system(size: 14))
                .foregroundColor(Color.fmText3)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color.fmBg)
    }

    private var emptyStateView: some View {
        VStack(spacing: 16) {
            Image(systemName: "puzzlepiece.extension")
                .font(.system(size: 64))
                .foregroundColor(Color.fmText3.opacity(0.3))

            Text("暂无可用技能")
                .font(.system(size: 16, weight: .medium))
                .foregroundColor(Color.fmText)

            Text("请联系管理员配置智能分析技能")
                .font(.system(size: 14))
                .foregroundColor(Color.fmText3)

            Button(action: {
                Task {
                    await viewModel.loadSkills(projectId: projectId)
                }
            }) {
                Text("重新加载")
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(.white)
                    .padding(.horizontal, 20)
                    .padding(.vertical, 10)
                    .background(Color.blue)
                    .cornerRadius(8)
            }
            .buttonStyle(PlainButtonStyle())
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color.fmBg)
    }

    private var contentView: some View {
        VStack(spacing: 0) {
            searchBar
            Divider()
            skillsList
        }
    }

    private var searchBar: some View {
        HStack(spacing: 8) {
            Image(systemName: "magnifyingglass")
                .font(.system(size: 14))
                .foregroundColor(Color.fmText3)

            TextField("搜索技能名称、描述或维度", text: $searchText)
                .textFieldStyle(PlainTextFieldStyle())
                .font(.system(size: 14))

            if !searchText.isEmpty {
                Button(action: { searchText = "" }) {
                    Image(systemName: "xmark.circle.fill")
                        .font(.system(size: 14))
                        .foregroundColor(Color.fmText3)
                }
                .buttonStyle(PlainButtonStyle())
            }
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
        .background(Color.white)
        .cornerRadius(8)
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .stroke(Color.fmBorder, lineWidth: 1)
        )
        .padding(.horizontal, 24)
        .padding(.vertical, 16)
        .background(Color(hex: "FAFAFA"))
    }

    private var skillsList: some View {
        ScrollView {
            LazyVStack(spacing: 16) {
                if filteredSkills.isEmpty {
                    VStack(spacing: 12) {
                        Image(systemName: "magnifyingglass")
                            .font(.system(size: 48))
                            .foregroundColor(Color.fmText3.opacity(0.3))

                        Text("未找到匹配的技能")
                            .font(.system(size: 14))
                            .foregroundColor(Color.fmText3)
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 60)
                } else {
                    ForEach(filteredSkills) { skill in
                        SkillConfigCard(
                            skill: skill,
                            isEnabled: viewModel.isSkillEnabled(skill.id),
                            onToggle: {
                                viewModel.toggleSkill(skill.id)
                            }
                        )
                    }
                }
            }
            .padding(24)
        }
        .background(Color.fmBg)
    }
}

struct SkillConfigCard: View {
    let skill: SkillService.SkillInfo
    let isEnabled: Bool
    let onToggle: () -> Void

    var body: some View {
        HStack(spacing: 16) {
            // Icon
            ZStack {
                Circle()
                    .fill(isEnabled ? Color.blue.opacity(0.1) : Color.fmBg2)
                    .frame(width: 48, height: 48)

                Image(systemName: "puzzlepiece.extension.fill")
                    .font(.system(size: 20))
                    .foregroundColor(isEnabled ? .blue : Color.fmText3)
            }

            // Info
            VStack(alignment: .leading, spacing: 6) {
                HStack(spacing: 8) {
                    Text(skill.name)
                        .font(.system(size: 16, weight: .semibold))
                        .foregroundColor(Color.fmText)

                    if skill.defaultEnabled {
                        Text("推荐")
                            .font(.system(size: 11, weight: .medium))
                            .foregroundColor(.orange)
                            .padding(.horizontal, 6)
                            .padding(.vertical, 2)
                            .background(Color.orange.opacity(0.1))
                            .cornerRadius(4)
                    }
                }

                Text(skill.description)
                    .font(.system(size: 14))
                    .foregroundColor(Color.fmText2)
                    .lineLimit(2)

                if !skill.dimensions.isEmpty {
                    FlowLayout(spacing: 6) {
                        ForEach(skill.dimensions, id: \.self) { dimension in
                            Text(dimension)
                                .font(.system(size: 12))
                                .foregroundColor(Color.fmText3)
                                .padding(.horizontal, 8)
                                .padding(.vertical, 4)
                                .background(Color.fmBg2)
                                .cornerRadius(4)
                        }
                    }
                }
            }

            Spacer()

            // Toggle
            Toggle("", isOn: Binding(
                get: { isEnabled },
                set: { _ in onToggle() }
            ))
            .labelsHidden()
            .toggleStyle(SwitchToggleStyle())
        }
        .padding(16)
        .background(Color.white)
        .cornerRadius(12)
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(isEnabled ? Color.blue.opacity(0.3) : Color.fmBorder, lineWidth: isEnabled ? 2 : 1)
        )
        .shadow(color: Color.black.opacity(0.05), radius: 8, x: 0, y: 2)
    }
}
