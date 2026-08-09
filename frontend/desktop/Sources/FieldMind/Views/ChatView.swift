import SwiftUI

struct ChatView: View {
    @EnvironmentObject var appState: AppState
    @ObservedObject private var dataManager = ProjectDataManager.shared
    @State private var selectedSession: ChatSession?
    @State private var messages: [ChatMessage] = []
    @State private var messageText = ""
    @State private var isLoading = false
    @State private var showNewSessionDialog = false
    @State private var selectedFramework: String?

    var body: some View {
        HSplitView {
            // 左侧：会话列表
            VStack(spacing: 0) {
                HStack {
                    Text("对话会话")
                        .font(.system(size: 16, weight: .semibold))
                    Spacer()
                    Button(action: { showNewSessionDialog = true }) {
                        Image(systemName: "plus.circle")
                    }
                    .buttonStyle(.plain)
                    .disabled(appState.currentProject == nil)
                }
                .padding()
                .background(Color(NSColor.controlBackgroundColor))

                Divider()

                if dataManager.isLoadingChat {
                    ProgressView()
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else if dataManager.chatSessions.isEmpty {
                    EmptyStateView(icon: "message", message: "暂无对话会话")
                } else {
                    ScrollView {
                        LazyVStack(spacing: 8) {
                            ForEach(dataManager.chatSessions) { session in
                                SessionRow(session: session, isSelected: selectedSession?.id == session.id)
                                    .onTapGesture {
                                        selectSession(session)
                                    }
                            }
                        }
                        .padding(12)
                    }
                }
            }
            .frame(minWidth: 250, idealWidth: 300)

            // 右侧：聊天区域
            if let session = selectedSession {
                ChatAreaView(
                    session: session,
                    messages: $messages,
                    messageText: $messageText,
                    selectedFramework: $selectedFramework,
                    isLoading: $isLoading,
                    onSend: sendMessage
                )
            } else {
                EmptyStateView(icon: "arrow.left", message: appState.currentProject == nil ? "请先选择项目" : "从左侧选择或创建对话")
            }
        }
        .sheet(isPresented: $showNewSessionDialog) {
            NewChatSessionDialog(isPresented: $showNewSessionDialog, onCreate: createSession)
        }
    }

    private func selectSession(_ session: ChatSession) {
        selectedSession = session
        messages = session.messages ?? []
    }

    private func createSession(name: String, documentIds: [Int]) {
        guard let projectId = appState.currentProject?.id else { return }

        Task {
            do {
                let newSession = try await APIService.shared.createChatSession(
                    projectId: projectId,
                    name: name,
                    documentIds: documentIds
                )
                await MainActor.run {
                    dataManager.chatSessions.insert(newSession, at: 0)
                    selectedSession = newSession
                    messages = []
                    ToastManager.shared.success("会话创建成功")
                }
            } catch {
                print("❌ 创建会话失败: \(error)")
                ToastManager.shared.error("创建会话失败")
            }
        }
    }

    private func sendMessage() {
        guard let sessionId = selectedSession?.id, !messageText.isEmpty else { return }

        let userMessageText = messageText
        messageText = ""
        isLoading = true

        // 立即显示用户消息
        let tempUserMessage = ChatMessage(
            id: -1,
            sessionId: sessionId,
            role: .user,
            content: userMessageText,
            createdAt: Date(),
            sources: nil
        )
        messages.append(tempUserMessage)

        Task {
            do {
                let response = try await APIService.shared.sendMessage(
                    sessionId: sessionId,
                    message: userMessageText,
                    framework: selectedFramework
                )
                await MainActor.run {
                    // 移除临时消息
                    messages.removeAll { $0.id == -1 }
                    // 添加真实响应
                    messages.append(contentsOf: [
                        ChatMessage(
                            id: messages.count,
                            sessionId: sessionId,
                            role: .user,
                            content: userMessageText,
                            createdAt: Date(),
                            sources: nil
                        ),
                        response
                    ])
                    isLoading = false
                }
            } catch {
                print("❌ 发送消息失败: \(error)")
                await MainActor.run {
                    messages.removeAll { $0.id == -1 }
                    isLoading = false
                    ToastManager.shared.error("发送消息失败")
                }
            }
        }
    }
}

struct SessionRow: View {
    let session: ChatSession
    let isSelected: Bool

    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: "message.fill")
                .font(.system(size: 16))
                .foregroundColor(Color(hex: "667eea"))

            VStack(alignment: .leading, spacing: 4) {
                Text(session.name)
                    .font(.system(size: 14, weight: .medium))
                    .lineLimit(1)

                Text("\(session.documentIds.count) 个数据源")
                    .font(.system(size: 11))
                    .foregroundColor(.secondary)
            }

            Spacer()
        }
        .padding(12)
        .background(isSelected ? Color(hex: "667eea").opacity(0.15) : Color.clear)
        .cornerRadius(8)
    }
}

struct ChatAreaView: View {
    let session: ChatSession
    @Binding var messages: [ChatMessage]
    @Binding var messageText: String
    @Binding var selectedFramework: String?
    @Binding var isLoading: Bool
    let onSend: () -> Void

    var body: some View {
        VStack(spacing: 0) {
            // 会话标题和框架选择
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text(session.name)
                        .font(.system(size: 16, weight: .semibold))

                    Text("\(session.documentIds.count) 个数据源")
                        .font(.system(size: 12))
                        .foregroundColor(.secondary)
                }

                Spacer()

                Menu {
                    Button("无框架") {
                        selectedFramework = nil
                    }
                    Divider()
                    Button("差序格局") {
                        selectedFramework = "fxt-differential"
                    }
                    Button("礼治秩序") {
                        selectedFramework = "fxt-ritual"
                    }
                    Button("熟人社会") {
                        selectedFramework = "fxt-acquaintance"
                    }
                } label: {
                    HStack {
                        Image(systemName: "list.bullet.clipboard")
                        Text(selectedFramework == nil ? "选择分析框架" : "已选择框架")
                            .font(.system(size: 13))
                    }
                    .padding(.horizontal, 12)
                    .padding(.vertical, 6)
                    .background(Color(NSColor.controlBackgroundColor))
                    .cornerRadius(8)
                }
                .menuStyle(BorderlessButtonMenuStyle())
            }
            .padding()
            .background(Color(NSColor.controlBackgroundColor))

            Divider()

            // 消息列表
            ScrollViewReader { proxy in
                ScrollView {
                    LazyVStack(spacing: 16) {
                        ForEach(messages) { message in
                            MessageBubble(message: message)
                                .id(message.id)
                        }

                        if isLoading {
                            HStack {
                                ProgressView()
                                    .scaleEffect(0.8)
                                Text("AI正在深度思考...")
                                    .font(.system(size: 13))
                                    .foregroundColor(.secondary)
                            }
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .padding(.horizontal, 20)
                            .id("loading")
                        }
                    }
                    .padding(20)
                }
                .onChange(of: messages.count) { _, _ in
                    if let lastMessage = messages.last {
                        withAnimation {
                            proxy.scrollTo(lastMessage.id, anchor: .bottom)
                        }
                    }
                }
                .onChange(of: isLoading) { _, loading in
                    if loading {
                        withAnimation {
                            proxy.scrollTo("loading", anchor: .bottom)
                        }
                    }
                }
            }

            Divider()

            // 输入区域
            HStack(spacing: 12) {
                TextField("输入消息...", text: $messageText, axis: .vertical)
                    .textFieldStyle(.plain)
                    .padding(12)
                    .background(Color(NSColor.controlBackgroundColor))
                    .cornerRadius(10)
                    .lineLimit(1...5)
                    .onSubmit(onSend)

                Button(action: onSend) {
                    Image(systemName: "arrow.up.circle.fill")
                        .font(.system(size: 32))
                        .foregroundColor(messageText.isEmpty ? .secondary : Color(hex: "667eea"))
                }
                .buttonStyle(.plain)
                .disabled(messageText.isEmpty || isLoading)
            }
            .padding()
        }
    }
}

struct MessageBubble: View {
    let message: ChatMessage

    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            if message.role == .assistant {
                Image(systemName: "brain.head.profile")
                    .font(.system(size: 24))
                    .foregroundColor(Color(hex: "667eea"))
                    .frame(width: 32, height: 32)
            }

            VStack(alignment: message.role == .user ? .trailing : .leading, spacing: 8) {
                Text(message.content)
                    .font(.system(size: 14))
                    .padding(12)
                    .background(
                        message.role == .user ?
                        Color(hex: "667eea").opacity(0.15) :
                        Color(NSColor.controlBackgroundColor)
                    )
                    .cornerRadius(10)
                    .frame(maxWidth: 600, alignment: message.role == .user ? .trailing : .leading)

                if let sources = message.sources, !sources.isEmpty {
                    VStack(alignment: .leading, spacing: 6) {
                        Text("数据来源:")
                            .font(.system(size: 11, weight: .medium))
                            .foregroundColor(.secondary)

                        ForEach(sources.indices, id: \.self) { index in
                            let source = sources[index]
                            Text("• \(source.documentName)")
                                .font(.system(size: 11))
                                .foregroundColor(.secondary)
                        }
                    }
                    .padding(8)
                    .frame(maxWidth: 600, alignment: .leading)
                }
            }

            if message.role == .user {
                Image(systemName: "person.circle.fill")
                    .font(.system(size: 24))
                    .foregroundColor(.secondary)
                    .frame(width: 32, height: 32)
            }
        }
        .frame(maxWidth: .infinity, alignment: message.role == .user ? .trailing : .leading)
    }
}

struct NewChatSessionDialog: View {
    @EnvironmentObject var appState: AppState
    @ObservedObject private var dataManager = ProjectDataManager.shared
    @Binding var isPresented: Bool
    let onCreate: (String, [Int]) -> Void

    @State private var sessionName = ""
    @State private var selectedDocumentIds: Set<Int> = []

    var body: some View {
        VStack(spacing: 0) {
            // 标题栏
            HStack {
                Text("创建对话会话")
                    .font(.system(size: 18, weight: .semibold))

                Spacer()

                Button(action: { isPresented = false }) {
                    Image(systemName: "xmark.circle.fill")
                        .foregroundColor(.secondary)
                        .font(.system(size: 20))
                }
                .buttonStyle(.plain)
            }
            .padding()
            .background(Color(NSColor.controlBackgroundColor))

            Divider()

            // 表单内容
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("会话名称")
                            .font(.system(size: 14, weight: .medium))

                        TextField("输入会话名称", text: $sessionName)
                            .textFieldStyle(.roundedBorder)
                    }

                    VStack(alignment: .leading, spacing: 8) {
                        Text("选择数据源")
                            .font(.system(size: 14, weight: .medium))

                        if dataManager.documents.isEmpty {
                            Text("暂无可用文档")
                                .font(.system(size: 13))
                                .foregroundColor(.secondary)
                                .frame(maxWidth: .infinity, alignment: .center)
                                .padding(40)
                        } else {
                            VStack(spacing: 8) {
                                ForEach(dataManager.documents.filter { $0.status == .completed }) { document in
                                    HStack {
                                        Toggle("", isOn: Binding(
                                            get: { selectedDocumentIds.contains(document.id) },
                                            set: { isSelected in
                                                if isSelected {
                                                    selectedDocumentIds.insert(document.id)
                                                } else {
                                                    selectedDocumentIds.remove(document.id)
                                                }
                                            }
                                        ))
                                        .toggleStyle(.checkbox)

                                        Text(document.filename)
                                            .font(.system(size: 13))

                                        Spacer()

                                        Text(document.status.rawValue)
                                            .font(.system(size: 11))
                                            .padding(.horizontal, 8)
                                            .padding(.vertical, 4)
                                            .background(Color.green.opacity(0.1))
                                            .foregroundColor(.green)
                                            .cornerRadius(4)
                                    }
                                    .padding(8)
                                    .background(Color(NSColor.controlBackgroundColor))
                                    .cornerRadius(6)
                                }
                            }
                        }
                    }
                }
                .padding(20)
            }

            Divider()

            // 按钮栏
            HStack(spacing: 12) {
                Spacer()

                Button("取消") {
                    isPresented = false
                }
                .buttonStyle(.bordered)

                Button("创建") {
                    onCreate(sessionName, Array(selectedDocumentIds))
                    isPresented = false
                }
                .buttonStyle(.borderedProminent)
                .tint(Color(hex: "667eea"))
                .disabled(sessionName.isEmpty || selectedDocumentIds.isEmpty)
            }
            .padding()
            .background(Color(NSColor.controlBackgroundColor))
        }
        .frame(width: 500, height: 500)
    }
}
