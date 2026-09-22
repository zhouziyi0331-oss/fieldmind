"""
对话视图
AI 对话 + 会话管理 + 文档引用
"""
import SwiftUI

// MARK: - ViewModel
class ChatViewModel: ObservableObject {
    @Published var messages: [ChatMessage] = []
    @Published var sessions: [ChatSession] = []
    @Published var selectedSession: ChatSession?
    @Published var inputText: String = ""
    @Published var isLoading: Bool = false

    func loadSessions(projectId: Int) {
        // TODO: 调用 API
        // GET /api/v1/chat/projects/{project_id}/sessions/

        // 模拟数据
        sessions = [
            ChatSession(title: "项目概况咨询", lastMessage: "这个项目主要关注什么？", updatedAt: Date()),
            ChatSession(title: "数据分析讨论", lastMessage: "知识网络的核心节点有哪些？", updatedAt: Date().addingTimeInterval(-3600)),
            ChatSession(title: "报告生成", lastMessage: "生成一份完整的田野报告", updatedAt: Date().addingTimeInterval(-7200))
        ]
        selectedSession = sessions.first
        loadMessages()
    }

    func loadMessages() {
        guard let session = selectedSession else { return }

        // TODO: 调用 API
        // GET /api/v1/chat/sessions/{session_id}/messages/

        // 模拟数据
        messages = [
            ChatMessage(content: "你好，我是 FieldMind AI 助手，有什么可以帮助你的？", isUser: false),
            ChatMessage(content: "这个项目的主要内容是什么？", isUser: true),
            ChatMessage(
                content: "根据分析，这个项目主要关注乡村文化传承与产业发展。从文档中提取了以下关键信息：\n\n1. 文化传承：非遗保护、传统工艺\n2. 产业发展：特色农业、乡村旅游\n3. 社区营造：居民参与、合作社组织",
                isUser: false,
                relatedDocuments: [
                    RelatedDocument(name: "田野笔记001.pdf", relevance: 0.95),
                    RelatedDocument(name: "访谈记录.docx", relevance: 0.88)
                ]
            )
        ]
    }

    func sendMessage() {
        guard !inputText.isEmpty else { return }

        let userMessage = ChatMessage(content: inputText, isUser: true)
        messages.append(userMessage)

        let userInput = inputText
        inputText = ""
        isLoading = true

        // TODO: 调用 API
        // POST /api/v1/chat/sessions/{session_id}/messages

        // 模拟 AI 响应
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.5) {
            let aiResponse = ChatMessage(
                content: "这是 AI 对「\(userInput)」的回答...",
                isUser: false
            )
            self.messages.append(aiResponse)
            self.isLoading = false
        }
    }

    func createNewSession() {
        // TODO: 调用 API
        // POST /api/v1/chat/sessions

        let newSession = ChatSession(
            title: "新对话",
            lastMessage: "",
            updatedAt: Date()
        )
        sessions.insert(newSession, at: 0)
        selectedSession = newSession
        messages = []
    }
}

// MARK: - 数据模型
struct ChatMessage: Identifiable {
    let id = UUID()
    let content: String
    let isUser: Bool
    let timestamp: Date
    let relatedDocuments: [RelatedDocument]?

    init(content: String, isUser: Bool, relatedDocuments: [RelatedDocument]? = nil) {
        self.content = content
        self.isUser = isUser
        self.timestamp = Date()
        self.relatedDocuments = relatedDocuments
    }
}

struct RelatedDocument: Identifiable {
    let id = UUID()
    let name: String
    let relevance: Double
}

struct ChatSession: Identifiable {
    let id = UUID()
    let title: String
    let lastMessage: String
    let updatedAt: Date
}

// MARK: - 主视图
struct ChatView: View {
    @StateObject var viewModel = ChatViewModel()
    let projectId: Int

    var body: some View {
        HSplitView {
            // 左侧：会话历史
            ChatHistorySidebar(
                sessions: viewModel.sessions,
                selectedSession: $viewModel.selectedSession,
                onNewSession: viewModel.createNewSession
            )
            .frame(minWidth: 200, idealWidth: 250, maxWidth: 300)

            // 右侧：对话区域
            VStack(spacing: 0) {
                // 顶部标题栏
                HStack {
                    Text(viewModel.selectedSession?.title ?? "对话")
                        .font(Typography.h3)

                    Spacer()

                    Button {
                        // TODO: 对话设置
                    } label: {
                        Image(systemName: "gear")
                    }
                    .buttonStyle(.plain)
                }
                .padding(Spacing.lg)
                .background(Color.fmBgPrimary)

                Divider()

                // 消息列表
                ScrollView {
                    ScrollViewReader { proxy in
                        LazyVStack(spacing: Spacing.lg) {
                            ForEach(viewModel.messages) { message in
                                MessageBubble(message: message)
                                    .id(message.id)
                            }

                            if viewModel.isLoading {
                                HStack {
                                    ProgressView()
                                        .scaleEffect(0.8)
                                    Text("思考中...")
                                        .font(Typography.caption)
                                        .foregroundColor(.fmTextSecondary)
                                }
                                .frame(maxWidth: .infinity, alignment: .leading)
                                .padding(.leading, Spacing.lg)
                            }
                        }
                        .padding(Spacing.lg)
                        .onChange(of: viewModel.messages.count) { _ in
                            if let lastMessage = viewModel.messages.last {
                                withAnimation {
                                    proxy.scrollTo(lastMessage.id, anchor: .bottom)
                                }
                            }
                        }
                    }
                }
                .background(Color.fmBgSecondary)

                // 输入栏
                ChatInputBar(
                    text: $viewModel.inputText,
                    isLoading: viewModel.isLoading,
                    onSend: viewModel.sendMessage
                )
            }
        }
        .onAppear {
            viewModel.loadSessions(projectId: projectId)
        }
    }
}

// MARK: - 会话历史侧边栏
struct ChatHistorySidebar: View {
    let sessions: [ChatSession]
    @Binding var selectedSession: ChatSession?
    let onNewSession: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            Button {
                onNewSession()
            } label: {
                HStack {
                    Image(systemName: "plus")
                    Text("新对话")
                }
                .frame(maxWidth: .infinity)
                .padding(Spacing.md)
            }
            .buttonStyle(.borderedProminent)
            .padding(Spacing.md)

            Divider()

            List(sessions, selection: $selectedSession) { session in
                ChatSessionRow(session: session)
            }
            .listStyle(.sidebar)
        }
        .background(Color.fmBgPrimary)
    }
}

struct ChatSessionRow: View {
    let session: ChatSession

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(session.title)
                .font(Typography.body)
                .foregroundColor(.fmTextPrimary)
                .lineLimit(1)

            if !session.lastMessage.isEmpty {
                Text(session.lastMessage)
                    .font(Typography.caption)
                    .foregroundColor(.fmTextSecondary)
                    .lineLimit(2)
            }

            Text(session.updatedAt, style: .relative)
                .font(Typography.small)
                .foregroundColor(.fmTextTertiary)
        }
        .padding(.vertical, 6)
    }
}

// MARK: - 消息气泡
struct MessageBubble: View {
    let message: ChatMessage

    var body: some View {
        HStack(alignment: .top) {
            if message.isUser { Spacer(minLength: 100) }

            VStack(alignment: message.isUser ? .trailing : .leading, spacing: Spacing.sm) {
                // 消息内容
                Text(message.content)
                    .font(Typography.body)
                    .padding(Spacing.md)
                    .background(message.isUser ? Color.fmAccent : Color.fmBgPrimary)
                    .foregroundColor(message.isUser ? .white : .fmTextPrimary)
                    .cornerRadius(12)

                // 相关文档（仅 AI 消息）
                if !message.isUser, let docs = message.relatedDocuments, !docs.isEmpty {
                    VStack(alignment: .leading, spacing: 6) {
                        Text("相关文档:")
                            .font(Typography.caption)
                            .foregroundColor(.fmTextSecondary)

                        ForEach(docs) { doc in
                            HStack {
                                Image(systemName: "doc.text")
                                    .font(.caption)
                                Text(doc.name)
                                    .font(Typography.caption)
                                Spacer()
                                Text("\(Int(doc.relevance * 100))%")
                                    .font(Typography.small)
                                    .foregroundColor(.fmTextSecondary)
                            }
                            .padding(Spacing.sm)
                            .background(Color.fmAccent.opacity(0.05))
                            .cornerRadius(6)
                        }
                    }
                    .frame(maxWidth: 400)
                }

                // 时间戳
                Text(message.timestamp, style: .time)
                    .font(Typography.small)
                    .foregroundColor(.fmTextTertiary)
            }

            if !message.isUser { Spacer(minLength: 100) }
        }
    }
}

// MARK: - 输入栏
struct ChatInputBar: View {
    @Binding var text: String
    let isLoading: Bool
    let onSend: () -> Void

    var body: some View {
        HStack(spacing: Spacing.md) {
            Button {
                // TODO: 附件功能
            } label: {
                Image(systemName: "paperclip")
            }
            .buttonStyle(.plain)
            .disabled(isLoading)

            TextField("输入消息...", text: $text, axis: .vertical)
                .textFieldStyle(.plain)
                .lineLimit(1...5)
                .font(Typography.body)
                .padding(Spacing.sm)
                .background(Color.fmBgSecondary)
                .cornerRadius(8)
                .onSubmit {
                    if !text.isEmpty && !isLoading {
                        onSend()
                    }
                }
                .disabled(isLoading)

            Button {
                onSend()
            } label: {
                Image(systemName: "paperplane.fill")
            }
            .buttonStyle(.borderedProminent)
            .disabled(text.isEmpty || isLoading)
        }
        .padding(Spacing.lg)
        .background(Color.fmBgPrimary)
    }
}

// MARK: - 预览
struct ChatView_Previews: PreviewProvider {
    static var previews: some View {
        ChatView(projectId: 1)
            .frame(width: 1000, height: 700)
    }
}
