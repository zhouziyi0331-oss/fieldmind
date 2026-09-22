import SwiftUI

struct ChatPage: View {
    @EnvironmentObject var appState: AppState
    @StateObject private var viewModel = ChatViewModel()
    @State private var messageText = ""
    @State private var showNewSessionDialog = false
    @State private var newSessionName = ""

    var body: some View {
        HStack(spacing: 0) {
            // 左侧：对话列表
            sessionsList
                .frame(width: 280)

            Divider()
                .background(Color.fmBorder)

            // 右侧：聊天区域
            if let session = viewModel.currentSession {
                chatArea(session: session)
            } else {
                emptyState
            }
        }
        .sheet(isPresented: $showNewSessionDialog) {
            newSessionSheet
        }
        .task {
            if let projectId = appState.currentProject?.id {
                await viewModel.loadSessions(projectId: projectId)
            }
        }
    }

    // MARK: - Sessions List
    private var sessionsList: some View {
        VStack(spacing: 0) {
            // 头部
            VStack(alignment: .leading, spacing: 4) {
                HStack(spacing: 7) {
                    Circle()
                        .fill(Color.fmA1)
                        .frame(width: 6, height: 6)
                        .shadow(color: Color.fmA1, radius: 4)

                    Text("AI 对话")
                        .font(.system(size: 14, weight: .heavy))
                        .foregroundColor(.fmText)
                        .tracking(-0.01)
                }

                Text("智能问答，材料深度解读")
                    .font(.system(size: 10))
                    .foregroundColor(.fmText3)
                    .tracking(0.02)
            }
            .padding(EdgeInsets(top: 16, leading: 16, bottom: 12, trailing: 16))

            // 新建对话按钮
            Button(action: { showNewSessionDialog = true }) {
                HStack {
                    Image(systemName: "plus.circle.fill")
                        .font(.system(size: 13))
                    Text("新建对话")
                        .font(.system(size: 12, weight: .semibold))
                }
                .frame(maxWidth: .infinity)
            }
            .buttonStyle(FMButtonStyle(style: .primary, size: .medium))
            .padding(.horizontal, 16)
            .padding(.bottom, 12)

            Divider()
                .background(Color.fmBorder)
                .padding(.bottom, 8)

            // 对话列表
            if viewModel.isLoadingSessions && viewModel.sessions.isEmpty {
                VStack {
                    ProgressView()
                        .scaleEffect(0.8)
                    Text("加载中...")
                        .font(.system(size: 12))
                        .foregroundColor(.fmText3)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else if viewModel.sessions.isEmpty {
                VStack(spacing: 12) {
                    Image(systemName: "bubble.left.and.bubble.right")
                        .font(.system(size: 32))
                        .foregroundColor(.fmText3)
                    Text("暂无对话")
                        .font(.system(size: 12))
                        .foregroundColor(.fmText3)
                    Text("点击上方按钮创建新对话")
                        .font(.system(size: 11))
                        .foregroundColor(.fmText3)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
                .padding()
            } else {
                ScrollView {
                    VStack(spacing: 4) {
                        ForEach(viewModel.sessions) { session in
                            SessionRow(
                                session: session,
                                isSelected: viewModel.currentSession?.id == session.id,
                                onSelect: {
                                    Task {
                                        await viewModel.loadMessages(sessionId: session.id)
                                    }
                                },
                                onDelete: {
                                    Task {
                                        await viewModel.deleteSession(sessionId: session.id)
                                    }
                                }
                            )
                            .padding(.horizontal, 10)
                        }
                    }
                    .padding(.bottom, 10)
                }
            }
        }
        .background(Color.fmSurface)
    }

    // MARK: - Chat Area
    private func chatArea(session: ChatSessionResponse) -> some View {
        VStack(spacing: 0) {
            // 聊天头部
            chatHeader(session: session)

            Divider()
                .background(Color.fmBorder)

            // 消息列表
            if viewModel.isLoadingMessages && viewModel.messages.isEmpty {
                VStack {
                    ProgressView()
                    Text("加载消息中...")
                        .font(.system(size: 13))
                        .foregroundColor(.fmText2)
                        .padding(.top, 8)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                ScrollViewReader { proxy in
                    ScrollView {
                        VStack(spacing: 16) {
                            ForEach(viewModel.messages) { message in
                                MessageBubble(message: message)
                                    .id(message.id)
                            }

                            // AI 输入中指示器
                            if viewModel.isSendingMessage {
                                HStack {
                                    TypingIndicator()
                                    Spacer()
                                }
                                .padding(.horizontal, 20)
                            }
                        }
                        .padding(20)
                    }
                    .onChange(of: viewModel.messages.count) { oldValue, newValue in
                        if let lastMessage = viewModel.messages.last {
                            withAnimation {
                                proxy.scrollTo(lastMessage.id, anchor: .bottom)
                            }
                        }
                    }
                }
            }

            Divider()
                .background(Color.fmBorder)

            // 输入框
            messageInput
        }
    }

    // MARK: - Chat Header
    private func chatHeader(session: ChatSessionResponse) -> some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text(session.name)
                    .font(.system(size: 13, weight: .bold))
                    .foregroundColor(.fmText)

                Text("\(session.messageCount) 条消息")
                    .font(.system(size: 11))
                    .foregroundColor(.fmText3)
            }

            Spacer()

            // 进化技能按钮
            Button(action: {
                Task {
                    await viewModel.evolveSkill()
                }
            }) {
                HStack(spacing: 4) {
                    Image(systemName: "brain.head.profile")
                        .font(.system(size: 12))
                    Text("进化技能")
                        .font(.system(size: 11))
                }
                .foregroundColor(.fmPrimary)
                .padding(.horizontal, 10)
                .padding(.vertical, 6)
                .background(Color.fmPrimary.opacity(0.1))
                .cornerRadius(4)
            }
            .buttonStyle(.plain)
        }
        .padding(.horizontal, 20)
        .padding(.vertical, 12)
        .background(Color.white)
    }

    // MARK: - Message Input
    private var messageInput: some View {
        HStack(alignment: .bottom, spacing: 12) {
            // 文本输入框
            TextEditor(text: $messageText)
                .frame(minHeight: 36, maxHeight: 120)
                .padding(8)
                .background(Color.fmBg)
                .cornerRadius(6)
                .overlay(
                    RoundedRectangle(cornerRadius: 6)
                        .stroke(Color.fmBorder, lineWidth: 1)
                )
                .disabled(viewModel.isSendingMessage)

            // 发送按钮
            Button(action: sendMessage) {
                Image(systemName: "arrow.up.circle.fill")
                    .font(.system(size: 28))
                    .foregroundColor(messageText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ? .fmText3 : .fmPrimary)
            }
            .buttonStyle(.plain)
            .disabled(messageText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || viewModel.isSendingMessage)
        }
        .padding(12)
        .background(Color.white)
    }

    // MARK: - Empty State
    private var emptyState: some View {
        VStack(spacing: 16) {
            Image(systemName: "bubble.left.and.bubble.right")
                .font(.system(size: 56))
                .foregroundColor(.fmText3)
            Text("选择或创建对话开始聊天")
                .font(.system(size: 15))
                .foregroundColor(.fmText2)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color.fmBg.opacity(0.3))
    }

    // MARK: - New Session Sheet
    private var newSessionSheet: some View {
        VStack(spacing: 20) {
            Text("新建对话")
                .font(.system(size: 16, weight: .semibold))
                .foregroundColor(.fmText)

            VStack(alignment: .leading, spacing: 8) {
                Text("对话名称")
                    .font(.system(size: 13))
                    .foregroundColor(.fmText2)

                TextField("请输入对话名称", text: $newSessionName)
                    .textFieldStyle(.plain)
                    .padding(10)
                    .background(Color.fmBg)
                    .cornerRadius(6)
                    .overlay(
                        RoundedRectangle(cornerRadius: 6)
                            .stroke(Color.fmBorder, lineWidth: 1)
                    )
            }

            HStack(spacing: 12) {
                Button("取消") {
                    showNewSessionDialog = false
                    newSessionName = ""
                }
                .buttonStyle(FMButtonStyle(style: .secondary, size: .medium))

                Button("创建") {
                    Task {
                        if let projectId = appState.currentProject?.id {
                            await viewModel.createNewSession(
                                projectId: projectId,
                                name: newSessionName.isEmpty ? "新对话" : newSessionName
                            )
                        }
                        showNewSessionDialog = false
                        newSessionName = ""
                    }
                }
                .buttonStyle(FMButtonStyle(style: .primary, size: .medium))
            }
        }
        .padding(24)
        .frame(width: 400)
    }

    // MARK: - Actions
    private func sendMessage() {
        let content = messageText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !content.isEmpty else { return }

        messageText = ""

        Task {
            await viewModel.sendMessage(content: content)
        }
    }
}

// MARK: - Session Row

struct SessionRow: View {
    let session: ChatSessionResponse
    let isSelected: Bool
    let onSelect: () -> Void
    let onDelete: () -> Void

    @State private var isHovering = false

    var body: some View {
        Button(action: onSelect) {
            HStack(spacing: 10) {
                VStack(alignment: .leading, spacing: 6) {
                    Text(session.name)
                        .font(.system(size: 12, weight: .medium))
                        .foregroundColor(.fmText)
                        .lineLimit(1)

                    HStack(spacing: 6) {
                        Text("\(session.messageCount) 条消息")
                            .font(.system(size: 10))
                            .foregroundColor(.fmText3)

                        if let lastMessageAt = session.lastMessageAt {
                            Text("•")
                                .font(.system(size: 10))
                                .foregroundColor(.fmText3)
                            Text(formatDate(lastMessageAt))
                                .font(.system(size: 10))
                                .foregroundColor(.fmText3)
                        }
                    }
                }

                Spacer()

                if isHovering {
                    Button(action: onDelete) {
                        Image(systemName: "trash")
                            .font(.system(size: 11))
                            .foregroundColor(.fmError)
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(10)
            .background(isSelected ? Color.fmBlue.opacity(0.08) : Color.clear)
            .cornerRadius(6)
            .overlay(
                RoundedRectangle(cornerRadius: 6)
                    .stroke(isSelected ? Color.fmBlue : Color.clear, lineWidth: 2)
            )
        }
        .buttonStyle(.plain)
        .onHover { hovering in
            isHovering = hovering
        }
    }

    private func formatDate(_ dateString: String) -> String {
        let formatter = ISO8601DateFormatter()
        guard let date = formatter.date(from: dateString) else {
            return dateString
        }

        let now = Date()
        let calendar = Calendar.current

        if calendar.isDateInToday(date) {
            let timeFormatter = DateFormatter()
            timeFormatter.timeStyle = .short
            return timeFormatter.string(from: date)
        } else if calendar.isDateInYesterday(date) {
            return "昨天"
        } else {
            let dateFormatter = DateFormatter()
            dateFormatter.dateFormat = "MM/dd"
            return dateFormatter.string(from: date)
        }
    }
}

// MARK: - Message Bubble

struct MessageBubble: View {
    let message: ChatMessageResponse

    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            if message.role == "user" {
                Spacer()
            }

            VStack(alignment: message.role == "user" ? .trailing : .leading, spacing: 8) {
                // Message content
                Text(message.content)
                    .font(.system(size: 13))
                    .foregroundColor(message.role == "user" ? .white : .fmText)
                    .padding(12)
                    .background(message.role == "user" ? Color.fmPrimary : Color.fmBg)
                    .cornerRadius(12)

                // Thinking process (for assistant messages)
                if let thinking = message.thinkingProcess, !thinking.isEmpty {
                    DisclosureGroup("思考过程") {
                        Text(thinking)
                            .font(.system(size: 12))
                            .foregroundColor(.fmText2)
                            .padding(10)
                    }
                    .font(.system(size: 11))
                    .foregroundColor(.fmText3)
                    .padding(10)
                    .background(Color.fmBg.opacity(0.5))
                    .cornerRadius(8)
                }

                // Sources (for assistant messages)
                if let sources = message.sources, !sources.isEmpty {
                    VStack(alignment: .leading, spacing: 6) {
                        Text("引用来源")
                            .font(.system(size: 11, weight: .medium))
                            .foregroundColor(.fmText3)

                        ForEach(sources, id: \.self) { source in
                            HStack(spacing: 6) {
                                Image(systemName: "doc.text")
                                    .font(.system(size: 10))
                                Text(source)
                                    .font(.system(size: 11))
                            }
                            .foregroundColor(.fmText3)
                        }
                    }
                    .padding(10)
                    .background(Color.fmBg.opacity(0.5))
                    .cornerRadius(8)
                }

                // Timestamp
                Text(formatDate(message.createdAt))
                    .font(.system(size: 10))
                    .foregroundColor(.fmText3)
            }
            .frame(maxWidth: 500, alignment: message.role == "user" ? .trailing : .leading)

            if message.role == "assistant" {
                Spacer()
            }
        }
    }

    private func formatDate(_ dateString: String) -> String {
        let formatter = ISO8601DateFormatter()
        guard let date = formatter.date(from: dateString) else {
            return dateString
        }

        let timeFormatter = DateFormatter()
        timeFormatter.timeStyle = .short
        return timeFormatter.string(from: date)
    }
}

// MARK: - Typing Indicator

struct TypingIndicator: View {
    @State private var bounce = false

    var body: some View {
        HStack(spacing: 6) {
            ForEach(0..<3) { index in
                Circle()
                    .fill(Color.fmText3)
                    .frame(width: 6, height: 6)
                    .offset(y: bounce ? -5 : 0)
                    .animation(
                        Animation.easeInOut(duration: 0.5)
                            .repeatForever()
                            .delay(Double(index) * 0.15),
                        value: bounce
                    )
            }
        }
        .padding(10)
        .background(Color.fmBg)
        .cornerRadius(12)
        .onAppear {
            bounce = true
        }
    }
}
