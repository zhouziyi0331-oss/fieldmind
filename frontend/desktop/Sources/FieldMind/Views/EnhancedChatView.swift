import SwiftUI

struct EnhancedChatView: View {
    @EnvironmentObject var appState: AppState
    @ObservedObject private var dataManager = ProjectDataManager.shared

    @State private var currentSessionId: String?
    @State private var messages: [EnhancedChatMessage] = []
    @State private var inputText = ""
    @State private var isLoading = false
    @State private var showSettings = false

    // 增强功能配置
    @State private var useLongMemory = true
    @State private var useDeepThinking = false
    @State private var selectedSkill: Skill?
    @State private var memoryConfig = MemoryChatConfig(
        searchDepth: 10,
        relevanceThreshold: 0.7,
        maxContextTokens: 8000
    )

    @State private var showThinkingProcess = false
    @State private var currentThinking: String?
    @State private var showSources = false
    @State private var currentSources: [ChatSource] = []

    var body: some View {
        VStack(spacing: 0) {
            // 工具栏
            toolbar

            Divider()

            // 消息列表
            ScrollViewReader { proxy in
                ScrollView {
                    LazyVStack(spacing: 16) {
                        ForEach(messages) { message in
                            messageRow(message: message)
                                .id(message.id)
                        }
                    }
                    .padding(24)
                }
                .onChange(of: messages.count) { _, _ in
                    if let lastMessage = messages.last {
                        withAnimation {
                            proxy.scrollTo(lastMessage.id, anchor: .bottom)
                        }
                    }
                }
            }

            Divider()

            // 输入框
            inputArea
        }
        .sheet(isPresented: $showSettings) {
            ChatSettingsView(
                useLongMemory: $useLongMemory,
                useDeepThinking: $useDeepThinking,
                selectedSkill: $selectedSkill,
                memoryConfig: $memoryConfig
            )
        }
        .sheet(isPresented: $showThinkingProcess) {
            ThinkingProcessView(thinkingProcess: currentThinking ?? "")
        }
        .sheet(isPresented: $showSources) {
            SourcesView(sources: currentSources)
        }
        .onAppear {
            if currentSessionId == nil {
                createNewSession()
            }
        }
    }

    // MARK: - 工具栏

    private var toolbar: some View {
        HStack {
            Text("AI对话")
                .font(.system(size: 18, weight: .semibold))

            if let project = appState.currentProject {
                Text("· \(project.name)")
                    .font(.system(size: 14))
                    .foregroundColor(.gray)
            }

            Spacer()

            // 功能指示器
            HStack(spacing: 8) {
                if useLongMemory {
                    Label("长记忆", systemImage: "brain.head.profile")
                        .font(.system(size: 11))
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(Color.blue.opacity(0.1))
                        .foregroundColor(.blue)
                        .cornerRadius(4)
                }

                if useDeepThinking {
                    Label("深度思考", systemImage: "sparkles")
                        .font(.system(size: 11))
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(Color.purple.opacity(0.1))
                        .foregroundColor(.purple)
                        .cornerRadius(4)
                }

                if let skill = selectedSkill {
                    Label(skill.name, systemImage: "brain")
                        .font(.system(size: 11))
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(Color.orange.opacity(0.1))
                        .foregroundColor(.orange)
                        .cornerRadius(4)
                }
            }

            Button(action: { showSettings.toggle() }) {
                Image(systemName: "gearshape")
                    .font(.system(size: 16))
            }
            .buttonStyle(.plain)
            .help("对话设置")

            Button(action: createNewSession) {
                Image(systemName: "plus.message")
                    .font(.system(size: 16))
            }
            .buttonStyle(.plain)
            .help("新建对话")
        }
        .padding()
        .background(Color(NSColor.controlBackgroundColor))
    }

    // MARK: - 消息行

    private func messageRow(message: EnhancedChatMessage) -> some View {
        HStack(alignment: .top, spacing: 12) {
            if message.role == "user" {
                Spacer()
            }

            // 头像
            Image(systemName: message.role == "user" ? "person.circle.fill" : "brain.head.profile")
                .font(.system(size: 32))
                .foregroundColor(message.role == "user" ? Color.blue : Color.purple)

            // 消息内容
            VStack(alignment: .leading, spacing: 8) {
                Text(message.content)
                    .font(.system(size: 14))
                    .foregroundColor(Color.fieldMindText)
                    .textSelection(.enabled)

                // AI消息的附加信息
                if message.role == "assistant" {
                    HStack(spacing: 12) {
                        // 模型信息
                        if let metadata = message.metadata {
                            Text(metadata.model)
                                .font(.system(size: 10))
                                .foregroundColor(.gray)

                            Text("· \(metadata.processingTime, specifier: "%.2f")s")
                                .font(.system(size: 10))
                                .foregroundColor(.gray)

                            Text("· \(metadata.tokens.output) tokens")
                                .font(.system(size: 10))
                                .foregroundColor(.gray)
                        }

                        // 思考过程按钮
                        if message.thinkingProcess != nil {
                            Button(action: {
                                currentThinking = message.thinkingProcess
                                showThinkingProcess = true
                            }) {
                                Label("查看思考过程", systemImage: "sparkles")
                                    .font(.system(size: 10))
                                    .foregroundColor(.purple)
                            }
                            .buttonStyle(.plain)
                        }

                        // 来源按钮
                        if let sources = message.sources, !sources.isEmpty {
                            Button(action: {
                                currentSources = sources
                                showSources = true
                            }) {
                                Label("\(sources.count)个来源", systemImage: "doc.text")
                                    .font(.system(size: 10))
                                    .foregroundColor(.blue)
                            }
                            .buttonStyle(.plain)
                        }
                    }
                }

                // 时间戳
                Text(formatDate(message.createdAt))
                    .font(.system(size: 10))
                    .foregroundColor(.gray)
            }
            .padding(12)
            .background(message.role == "user" ? Color.blue.opacity(0.1) : Color.purple.opacity(0.05))
            .cornerRadius(8)
            .frame(maxWidth: 600)

            if message.role == "assistant" {
                Spacer()
            }
        }
    }

    // MARK: - 输入区域

    private var inputArea: some View {
        HStack(alignment: .bottom, spacing: 12) {
            // 多行文本输入
            TextEditor(text: $inputText)
                .font(.system(size: 14))
                .frame(minHeight: 40, maxHeight: 120)
                .padding(8)
                .background(Color(NSColor.textBackgroundColor))
                .cornerRadius(8)
                .overlay(
                    RoundedRectangle(cornerRadius: 8)
                        .stroke(Color.gray.opacity(0.3), lineWidth: 1)
                )

            // 发送按钮
            Button(action: sendMessage) {
                Image(systemName: "paperplane.fill")
                    .font(.system(size: 16))
                    .foregroundColor(.white)
                    .frame(width: 40, height: 40)
                    .background(inputText.isEmpty || isLoading ? Color.gray : Color.blue)
                    .cornerRadius(8)
            }
            .buttonStyle(.plain)
            .disabled(inputText.isEmpty || isLoading)
        }
        .padding()
        .background(Color(NSColor.controlBackgroundColor))
    }

    // MARK: - 操作方法

    private func createNewSession() {
        guard let projectId = appState.currentProject?.id else {
            ToastManager.shared.error("请先选择项目")
            return
        }

        currentSessionId = UUID().uuidString
        messages = []
        ToastManager.shared.success("已创建新对话")
    }

    private func sendMessage() {
        guard !inputText.isEmpty else { return }
        guard let sessionId = currentSessionId else {
            createNewSession()
            return
        }
        guard let projectId = appState.currentProject?.id else {
            ToastManager.shared.error("请先选择项目")
            return
        }

        let userMessage = inputText
        inputText = ""

        // 添加用户消息
        let userMsg = EnhancedChatMessage(
            id: UUID().uuidString,
            sessionId: sessionId,
            role: "user",
            content: userMessage,
            sources: nil,
            metadata: nil,
            thinkingProcess: nil,
            createdAt: Date()
        )
        messages.append(userMsg)

        isLoading = true

        Task {
            do {
                // 构建技能配置
                var skillConfig: SkillChatConfig?
                if let skill = selectedSkill {
                    skillConfig = SkillChatConfig(
                        skillId: skill.id,
                        skillName: skill.name,
                        workflowPrompt: skill.description,
                        parameters: nil
                    )
                }

                // 调用增强AI对话API
                let response = try await APIService.shared.sendEnhancedMessage(
                    sessionId: sessionId,
                    message: userMessage,
                    projectId: projectId,
                    useLongMemory: useLongMemory,
                    useDeepThinking: useDeepThinking,
                    skillConfig: skillConfig,
                    memoryConfig: memoryConfig
                )

                await MainActor.run {
                    // 添加AI消息
                    let aiMsg = EnhancedChatMessage(
                        id: response.assistantMessageId,
                        sessionId: sessionId,
                        role: "assistant",
                        content: response.answer,
                        sources: response.sources,
                        metadata: response.metadata,
                        thinkingProcess: response.thinkingProcess,
                        createdAt: Date()
                    )
                    messages.append(aiMsg)
                    isLoading = false
                }

            } catch {
                await MainActor.run {
                    isLoading = false
                    ToastManager.shared.error("发送失败: \(error.localizedDescription)")
                }
            }
        }
    }

    private func formatDate(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "HH:mm"
        return formatter.string(from: date)
    }
}

// MARK: - 设置视图

struct ChatSettingsView: View {
    @Binding var useLongMemory: Bool
    @Binding var useDeepThinking: Bool
    @Binding var selectedSkill: Skill?
    @Binding var memoryConfig: MemoryChatConfig

    @ObservedObject private var dataManager = ProjectDataManager.shared
    @Environment(\.dismiss) var dismiss

    var body: some View {
        VStack(spacing: 0) {
            // 标题
            HStack {
                Text("对话设置")
                    .font(.system(size: 18, weight: .semibold))
                Spacer()
                Button("完成") {
                    dismiss()
                }
            }
            .padding()
            .background(Color(NSColor.controlBackgroundColor))

            Divider()

            // 设置选项
            ScrollView {
                VStack(alignment: .leading, spacing: 24) {
                    // 基础功能
                    VStack(alignment: .leading, spacing: 12) {
                        Text("基础功能")
                            .font(.system(size: 16, weight: .semibold))

                        Toggle("启用长记忆系统", isOn: $useLongMemory)
                        Text("使用向量检索和对话历史，提供更准确的上下文")
                            .font(.system(size: 12))
                            .foregroundColor(.gray)

                        Toggle("启用深度思考", isOn: $useDeepThinking)
                        Text("AI将进行更深入的推理，响应时间会增加")
                            .font(.system(size: 12))
                            .foregroundColor(.gray)
                    }

                    Divider()

                    // 技能模型
                    VStack(alignment: .leading, spacing: 12) {
                        Text("技能模型")
                            .font(.system(size: 16, weight: .semibold))

                        if dataManager.skills.isEmpty {
                            Text("暂无可用技能")
                                .font(.system(size: 14))
                                .foregroundColor(.gray)
                        } else {
                            Picker("选择技能", selection: $selectedSkill) {
                                Text("无技能").tag(nil as Skill?)
                                ForEach(dataManager.skills.filter { $0.status == .active }) { skill in
                                    Text(skill.name).tag(skill as Skill?)
                                }
                            }
                        }
                    }

                    Divider()

                    // 记忆配置
                    if useLongMemory {
                        VStack(alignment: .leading, spacing: 12) {
                            Text("记忆配置")
                                .font(.system(size: 16, weight: .semibold))

                            VStack(alignment: .leading, spacing: 8) {
                                Text("检索深度: \(memoryConfig.searchDepth)")
                                    .font(.system(size: 14))
                                Slider(value: Binding(
                                    get: { Double(memoryConfig.searchDepth) },
                                    set: { memoryConfig = MemoryChatConfig(
                                        searchDepth: Int($0),
                                        relevanceThreshold: memoryConfig.relevanceThreshold,
                                        maxContextTokens: memoryConfig.maxContextTokens
                                    )}
                                ), in: 5...20, step: 1)
                            }

                            VStack(alignment: .leading, spacing: 8) {
                                Text("相关度阈值: \(memoryConfig.relevanceThreshold, specifier: "%.2f")")
                                    .font(.system(size: 14))
                                Slider(value: Binding(
                                    get: { memoryConfig.relevanceThreshold },
                                    set: { memoryConfig = MemoryChatConfig(
                                        searchDepth: memoryConfig.searchDepth,
                                        relevanceThreshold: $0,
                                        maxContextTokens: memoryConfig.maxContextTokens
                                    )}
                                ), in: 0.5...0.95, step: 0.05)
                            }

                            VStack(alignment: .leading, spacing: 8) {
                                Text("最大上下文: \(memoryConfig.maxContextTokens) tokens")
                                    .font(.system(size: 14))
                                Slider(value: Binding(
                                    get: { Double(memoryConfig.maxContextTokens) },
                                    set: { memoryConfig = MemoryChatConfig(
                                        searchDepth: memoryConfig.searchDepth,
                                        relevanceThreshold: memoryConfig.relevanceThreshold,
                                        maxContextTokens: Int($0)
                                    )}
                                ), in: 4000...16000, step: 1000)
                            }
                        }
                    }
                }
                .padding(24)
            }
        }
        .frame(width: 500, height: 600)
    }
}

// MARK: - 思考过程视图

struct ThinkingProcessView: View {
    let thinkingProcess: String
    @Environment(\.dismiss) var dismiss

    var body: some View {
        VStack(spacing: 0) {
            HStack {
                Label("AI思考过程", systemImage: "sparkles")
                    .font(.system(size: 18, weight: .semibold))
                Spacer()
                Button("关闭") {
                    dismiss()
                }
            }
            .padding()
            .background(Color(NSColor.controlBackgroundColor))

            Divider()

            ScrollView {
                Text(thinkingProcess)
                    .font(.system(size: 14, design: .monospaced))
                    .foregroundColor(Color.fieldMindText)
                    .textSelection(.enabled)
                    .padding(24)
            }
        }
        .frame(width: 600, height: 500)
    }
}

// MARK: - 来源视图

struct SourcesView: View {
    let sources: [ChatSource]
    @Environment(\.dismiss) var dismiss

    var body: some View {
        VStack(spacing: 0) {
            HStack {
                Label("参考来源", systemImage: "doc.text")
                    .font(.system(size: 18, weight: .semibold))
                Spacer()
                Button("关闭") {
                    dismiss()
                }
            }
            .padding()
            .background(Color(NSColor.controlBackgroundColor))

            Divider()

            ScrollView {
                LazyVStack(spacing: 16) {
                    ForEach(sources, id: \.documentId) { source in
                        VStack(alignment: .leading, spacing: 8) {
                            HStack {
                                Text(source.documentName)
                                    .font(.system(size: 14, weight: .semibold))
                                Spacer()
                                Text("相关度: \(source.relevanceScore, specifier: "%.2f")")
                                    .font(.system(size: 12))
                                    .foregroundColor(.gray)
                            }

                            Text(source.chunkText)
                                .font(.system(size: 13))
                                .foregroundColor(Color.fieldMindText)
                                .textSelection(.enabled)
                        }
                        .padding(16)
                        .background(Color.white)
                        .cornerRadius(8)
                        .shadow(color: Color.black.opacity(0.05), radius: 2, x: 0, y: 1)
                    }
                }
                .padding(24)
            }
        }
        .frame(width: 700, height: 600)
    }
}
