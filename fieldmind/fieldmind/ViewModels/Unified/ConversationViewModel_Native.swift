import Foundation

/// Conversation ViewModel - 管理对话会话数据
@MainActor
class ConversationViewModel: ObservableObject {
    @Published var sessions: [ChatSessionResponse] = []
    @Published var selectedSession: ChatSessionResponse?
    @Published var messages: [ChatMessageResponse] = []

    @Published var isLoadingSessions = false
    @Published var isLoadingMessages = false
    @Published var isSending = false
    @Published var errorMessage: String?
    @Published var successMessage: String?

    // 筛选条件
    @Published var searchText: String = ""
    @Published var selectedProjectId: Int?

    private let chatService = ChatService()

    // MARK: - Session Management

    /// 加载项目的所有对话会话
    func loadSessions(projectId: Int) async {
        isLoadingSessions = true
        errorMessage = nil

        do {
            let response = try await chatService.listProjectSessions(
                projectId: projectId,
                skip: 0,
                limit: 100
            )
            sessions = response.sessions
            successMessage = nil
        } catch {
            errorMessage = "加载对话列表失败: \(error.localizedDescription)"
            print("❌ ConversationViewModel.loadSessions error: \(error)")
        }

        isLoadingSessions = false
    }

    /// 创建新的对话会话
    func createSession(projectId: Int, name: String, documentIds: [Int]? = nil) async {
        errorMessage = nil

        do {
            let newSession = try await chatService.createSession(
                projectId: projectId,
                name: name,
                documentIds: documentIds
            )
            sessions.insert(newSession, at: 0)
            selectedSession = newSession
            successMessage = "对话创建成功"
        } catch {
            errorMessage = "创建对话失败: \(error.localizedDescription)"
            print("❌ ConversationViewModel.createSession error: \(error)")
        }
    }

    /// 删除对话会话
    func deleteSession(sessionId: Int) async {
        errorMessage = nil

        do {
            try await chatService.deleteSession(sessionId: sessionId)
            sessions.removeAll { $0.id == sessionId }
            if selectedSession?.id == sessionId {
                selectedSession = nil
                messages = []
            }
            successMessage = "对话已删除"
        } catch {
            errorMessage = "删除对话失败: \(error.localizedDescription)"
            print("❌ ConversationViewModel.deleteSession error: \(error)")
        }
    }

    // MARK: - Message Management

    /// 加载会话的所有消息
    func loadMessages(sessionId: Int) async {
        isLoadingMessages = true
        errorMessage = nil

        do {
            let response = try await chatService.getSessionMessages(
                sessionId: sessionId,
                skip: 0,
                limit: 100
            )
            messages = response.messages

            // 更新选中的会话
            if let session = sessions.first(where: { $0.id == sessionId }) {
                selectedSession = session
            }
        } catch {
            errorMessage = "加载消息失败: \(error.localizedDescription)"
            print("❌ ConversationViewModel.loadMessages error: \(error)")
        }

        isLoadingMessages = false
    }

    /// 发送消息
    func sendMessage(sessionId: Int, content: String) async {
        guard !content.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return }

        isSending = true
        errorMessage = nil

        do {
            let response = try await chatService.sendMessage(
                sessionId: sessionId,
                content: content
            )
            messages.append(response)

            // 更新会话的消息计数和最后消息时间
            if sessions.firstIndex(where: { $0.id == sessionId }) != nil {
                // 注意：这里需要重新加载会话以获取最新的messageCount和lastMessageAt
                // 但为了简化，我们先不做
            }

            successMessage = nil
        } catch {
            errorMessage = "发送消息失败: \(error.localizedDescription)"
            print("❌ ConversationViewModel.sendMessage error: \(error)")
        }

        isSending = false
    }

    // MARK: - Computed Properties

    /// 获取过滤后的会话列表（客户端搜索）
    func filteredSessions() -> [ChatSessionResponse] {
        guard !searchText.isEmpty else { return sessions }

        let lowercased = searchText.lowercased()
        return sessions.filter { session in
            session.name.lowercased().contains(lowercased)
        }
    }

    /// 按项目分组
    func sessionsByProject() -> [Int: [ChatSessionResponse]] {
        Dictionary(grouping: sessions) { $0.projectId }
    }

    /// 格式化会话最后消息时间
    func formatLastMessageTime(_ dateString: String?) -> String {
        guard let dateString = dateString else { return "无消息" }

        let formatter = ISO8601DateFormatter()
        guard let date = formatter.date(from: dateString) else { return dateString }

        let now = Date()
        let calendar = Calendar.current
        let components = calendar.dateComponents([.day, .hour, .minute], from: date, to: now)

        if let days = components.day, days > 0 {
            if days == 1 { return "昨天" }
            if days < 7 { return "\(days)天前" }
            if days < 30 { return "\(days / 7)周前" }
            return "\(days / 30)个月前"
        } else if let hours = components.hour, hours > 0 {
            return "\(hours)小时前"
        } else if let minutes = components.minute, minutes > 0 {
            return "\(minutes)分钟前"
        } else {
            return "刚刚"
        }
    }
}
