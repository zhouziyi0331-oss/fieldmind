import SwiftUI

struct SkillsView: View {
    @EnvironmentObject var appState: AppState
    @State private var skills: [Skill] = []
    @State private var isLoading = true
    @State private var showUploadDialog = false
    @State private var selectedSkill: Skill?

    var body: some View {
        VStack(spacing: 0) {
            // 工具栏
            HStack {
                Text("思维模型 / 技能")
                    .font(.system(size: 18, weight: .semibold))

                Spacer()

                Button(action: { showUploadDialog = true }) {
                    Label("上传技能", systemImage: "arrow.up.doc")
                }
                .buttonStyle(.borderedProminent)
                .tint(Color(hex: "9f7aea"))
            }
            .padding()
            .background(Color(NSColor.controlBackgroundColor))

            Divider()

            // 技能列表
            if isLoading {
                ProgressView("加载中...")
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else if skills.isEmpty {
                EmptyStateView(icon: "brain.head.profile", message: "暂无技能，点击上传技能文件")
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                ScrollView {
                    LazyVGrid(columns: [
                        GridItem(.adaptive(minimum: 300, maximum: 400))
                    ], spacing: 20) {
                        ForEach(skills) { skill in
                            SkillCard(skill: skill, onToggle: { newStatus in
                                toggleSkill(skill, status: newStatus)
                            }, onDelete: {
                                deleteSkill(skill)
                            })
                        }
                    }
                    .padding(24)
                }
            }
        }
        .sheet(isPresented: $showUploadDialog) {
            UploadSkillDialog(isPresented: $showUploadDialog, onUpload: { url in
                uploadSkill(fileURL: url)
            })
        }
        .onAppear(perform: loadSkills)
    }

    private func loadSkills() {
        isLoading = true

        Task {
            do {
                let fetchedSkills = try await APIService.shared.getSkills()
                await MainActor.run {
                    self.skills = fetchedSkills
                    self.isLoading = false
                }
            } catch {
                print("Error loading skills: \(error)")
                await MainActor.run {
                    self.isLoading = false
                }
            }
        }
    }

    private func uploadSkill(fileURL: URL) {
        Task {
            do {
                _ = try await APIService.shared.uploadSkill(fileURL: fileURL)
                await MainActor.run {
                    loadSkills()
                }
            } catch {
                print("Error uploading skill: \(error)")
            }
        }
    }

    private func toggleSkill(_ skill: Skill, status: SkillStatus) {
        Task {
            do {
                let updatedSkill = try await APIService.shared.toggleSkillStatus(id: skill.id, status: status)
                await MainActor.run {
                    if let index = skills.firstIndex(where: { $0.id == skill.id }) {
                        skills[index] = updatedSkill
                    }
                }
            } catch {
                print("Error toggling skill: \(error)")
            }
        }
    }

    private func deleteSkill(_ skill: Skill) {
        Task {
            do {
                try await APIService.shared.deleteSkill(id: skill.id)
                await MainActor.run {
                    skills.removeAll { $0.id == skill.id }
                }
            } catch {
                print("Error deleting skill: \(error)")
            }
        }
    }
}

struct SkillCard: View {
    let skill: Skill
    let onToggle: (SkillStatus) -> Void
    let onDelete: () -> Void

    @State private var showConfirmDialog = false

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            // 头部
            HStack {
                Image(systemName: "brain.head.profile")
                    .font(.system(size: 32))
                    .foregroundColor(Color(hex: "9f7aea"))

                Spacer()

                Menu {
                    Button("查看详情") {}
                    Divider()
                    Button("删除", role: .destructive, action: onDelete)
                } label: {
                    Image(systemName: "ellipsis.circle")
                        .font(.system(size: 18))
                        .foregroundColor(.secondary)
                }
                .menuStyle(BorderlessButtonMenuStyle())
            }

            // 技能信息
            VStack(alignment: .leading, spacing: 8) {
                Text(skill.name)
                    .font(.system(size: 18, weight: .semibold))
                    .lineLimit(1)

                if let description = skill.description {
                    Text(description)
                        .font(.system(size: 13))
                        .foregroundColor(.secondary)
                        .lineLimit(2)
                }

                HStack {
                    Text(skill.filename)
                        .font(.system(size: 11, design: .monospaced))
                        .foregroundColor(.secondary)

                    Spacer()

                    if let category = skill.category {
                        Text(category)
                            .font(.system(size: 11))
                            .padding(.horizontal, 8)
                            .padding(.vertical, 4)
                            .background(Color.secondary.opacity(0.1))
                            .cornerRadius(4)
                    }
                }
            }

            Divider()

            // 状态切换
            HStack {
                Text("启用状态")
                    .font(.system(size: 13))
                    .foregroundColor(.secondary)

                Spacer()

                Toggle("", isOn: Binding(
                    get: { skill.status == .active },
                    set: { isActive in
                        if isActive {
                            showConfirmDialog = true
                        } else {
                            onToggle(.inactive)
                        }
                    }
                ))
                .toggleStyle(.switch)
            }
        }
        .padding(20)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color(NSColor.controlBackgroundColor))
        .cornerRadius(12)
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(
                    skill.status == .active ? Color(hex: "9f7aea") : Color.secondary.opacity(0.2),
                    lineWidth: skill.status == .active ? 2 : 1
                )
        )
        .alert("确认启用技能", isPresented: $showConfirmDialog) {
            Button("取消", role: .cancel) {}
            Button("启用") {
                onToggle(.active)
            }
        } message: {
            Text("确认要启用技能 \"\(skill.name)\" 吗？启用后将在分析中使用此思维模型。")
        }
    }
}

struct UploadSkillDialog: View {
    @Binding var isPresented: Bool
    let onUpload: (URL) -> Void

    @State private var selectedFile: URL?
    @State private var showConfirmation = false

    var body: some View {
        VStack(spacing: 24) {
            Text("上传思维模型")
                .font(.system(size: 20, weight: .semibold))

            VStack(spacing: 16) {
                // 文件选择区域
                Button(action: selectFile) {
                    VStack(spacing: 16) {
                        Image(systemName: "brain.head.profile")
                            .font(.system(size: 48))
                            .foregroundColor(Color(hex: "9f7aea"))

                        Text(selectedFile?.lastPathComponent ?? "点击选择 Python 文件")
                            .font(.system(size: 14))

                        Text("支持 .py 格式的 Python 脚本文件")
                            .font(.system(size: 12))
                            .foregroundColor(.secondary)
                    }
                    .frame(maxWidth: .infinity)
                    .padding(40)
                    .background(Color(NSColor.controlBackgroundColor))
                    .cornerRadius(12)
                }
                .buttonStyle(.plain)

                // 说明
                VStack(alignment: .leading, spacing: 8) {
                    Text("技能文件要求:")
                        .font(.system(size: 13, weight: .medium))

                    VStack(alignment: .leading, spacing: 4) {
                        Text("• 必须是有效的 Python 脚本文件")
                        Text("• 包含分析函数或处理逻辑")
                        Text("• 可以包含文档字符串说明用途")
                    }
                    .font(.system(size: 12))
                    .foregroundColor(.secondary)
                }
                .padding()
                .background(Color.secondary.opacity(0.05))
                .cornerRadius(8)
            }

            if showConfirmation, let file = selectedFile {
                HStack {
                    Image(systemName: "checkmark.circle.fill")
                        .foregroundColor(Color(hex: "48bb78"))
                    Text("确认上传 \(file.lastPathComponent)?")
                        .font(.system(size: 14))
                }
                .padding()
                .background(Color(hex: "48bb78").opacity(0.1))
                .cornerRadius(8)
            }

            HStack(spacing: 12) {
                Button("取消") {
                    isPresented = false
                }
                .keyboardShortcut(.cancelAction)

                if selectedFile != nil {
                    if showConfirmation {
                        Button("确认上传") {
                            if let file = selectedFile {
                                onUpload(file)
                            }
                            isPresented = false
                        }
                        .buttonStyle(.borderedProminent)
                        .tint(Color(hex: "9f7aea"))
                        .keyboardShortcut(.defaultAction)
                    } else {
                        Button("下一步") {
                            showConfirmation = true
                        }
                        .buttonStyle(.borderedProminent)
                    }
                }
            }
        }
        .padding(24)
        .frame(width: 550)
    }

    private func selectFile() {
        let panel = NSOpenPanel()
        panel.allowsMultipleSelection = false
        panel.canChooseDirectories = false
        panel.allowedContentTypes = [.init(filenameExtension: "py")!]
        panel.allowsOtherFileTypes = false

        if panel.runModal() == .OK {
            selectedFile = panel.url
            showConfirmation = false
        }
    }
}
