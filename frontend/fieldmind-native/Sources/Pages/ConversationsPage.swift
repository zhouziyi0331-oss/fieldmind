import SwiftUI

struct ConversationsPage: View {
    let projectId: Int

    @StateObject private var viewModel = ConversationViewModel()

    @State private var searchText = ""
    @State private var sortBy = "最新对话"
    @State private var showNewConversationSheet = false
    @State private var newConversationName = ""

    let sortOptions = ["最新对话", "最早对话", "消息最多", "消息最少"]

    var filteredAndSortedSessions: [ChatSessionResponse] {
        var sessions = viewModel.filteredSessions()

        // Apply sorting
        switch sortBy {
        case "最新对话":
            sessions.sort { ($0.lastMessageAt ?? "") > ($1.lastMessageAt ?? "") }
        case "最早对话":
            sessions.sort { ($0.lastMessageAt ?? "") < ($1.lastMessageAt ?? "") }
        case "消息最多":
            sessions.sort { $0.messageCount > $1.messageCount }
        case "消息最少":
            sessions.sort { $0.messageCount < $1.messageCount }
        default:
            break
        }

        return sessions
    }

    var body: some View {
        VStack(spacing: 0) {
            // Top toolbar
            topToolbar

            Divider()

            // Main content
            if viewModel.isLoadingSessions {
                VStack(spacing: 16) {
                    ProgressView()
                    Text("加载对话列表...")
                        .font(.system(size: 14))
                        .foregroundColor(Color.fmText3)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else if let error = viewModel.errorMessage {
                VStack(spacing: 16) {
                    Image(systemName: "exclamationmark.triangle")
                        .font(.system(size: 48))
                        .foregroundColor(Color.fmRed)
                    Text(error)
                        .font(.system(size: 14))
                        .foregroundColor(Color.fmText2)
                    Button("重试") {
                        Task {
                            await viewModel.loadSessions(projectId: projectId)
                        }
                    }
                    .fmPrimary()
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else if filteredAndSortedSessions.isEmpty {
                VStack(spacing: 16) {
                    Image(systemName: "message")
                        .font(.system(size: 48))
                        .foregroundColor(Color.fmText3)
                    Text("暂无对话")
                        .font(.system(size: 15))
                        .foregroundColor(Color.fmText2)
                    Button("创建对话") {
                        showNewConversationSheet = true
                    }
                    .fmPrimary()
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                conversationsList
            }
        }
        .background(Color.white)
        .task {
            await viewModel.loadSessions(projectId: projectId)
        }
        .onChange(of: searchText) { newValue in
            viewModel.searchText = newValue
        }
        .sheet(isPresented: $showNewConversationSheet) {
            NewConversationSheet(
                projectId: projectId,
                onCreate: { name in
                    Task {
                        await viewModel.createSession(
                            projectId: projectId,
                            name: name
                        )
                        showNewConversationSheet = false
                    }
                }
            )
        }
    }

    // MARK: - Top Toolbar
    private var topToolbar: some View {
        HStack(spacing: 12) {
            // Search
            HStack(spacing: 8) {
                Image(systemName: "magnifyingglass")
                    .foregroundColor(Color.fmText3)
                    .font(.system(size: 14))
                TextField("搜索对话标题...", text: $searchText)
                    .textFieldStyle(.plain)
                    .font(.system(size: 13))

                if !searchText.isEmpty {
                    Button(action: { searchText = "" }) {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundColor(Color.fmText3)
                            .font(.system(size: 14))
                    }
                    .buttonStyle(PlainButtonStyle())
                }
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
            .background(Color.fmBg)
            .cornerRadius(8)
            .frame(width: 280)

            // Sort
            Menu {
                ForEach(sortOptions, id: \.self) { option in
                    Button(action: { sortBy = option }) {
                        HStack {
                            Text(option)
                            if sortBy == option {
                                Spacer()
                                Image(systemName: "checkmark")
                            }
                        }
                    }
                }
            } label: {
                HStack(spacing: 6) {
                    Image(systemName: "arrow.up.arrow.down")
                        .font(.system(size: 12))
                    Text(sortBy)
                        .font(.system(size: 13))
                    Image(systemName: "chevron.down")
                        .font(.system(size: 10))
                }
                .foregroundColor(Color.fmText2)
                .padding(.horizontal, 12)
                .padding(.vertical, 8)
                .background(Color.fmBg)
                .cornerRadius(8)
            }
            .menuStyle(BorderlessButtonMenuStyle())

            Spacer()

            // Result count
            Text("\(filteredAndSortedSessions.count) 个对话")
                .font(.system(size: 13))
                .foregroundColor(Color.fmText3)

            // New conversation button
            Button(action: { showNewConversationSheet = true }) {
                HStack(spacing: 6) {
                    Image(systemName: "plus")
                        .font(.system(size: 13))
                    Text("新建对话")
                        .font(.system(size: 13))
                }
                .foregroundColor(Color.white)
                .padding(.horizontal, 16)
                .padding(.vertical, 8)
                .background(Color.fmPrimary)
                .cornerRadius(8)
            }
            .buttonStyle(PlainButtonStyle())
        }
        .padding(.horizontal, 20)
        .padding(.vertical, 12)
        .background(Color.white)
    }

    // MARK: - Conversations List
    private var conversationsList: some View {
        ScrollView {
            LazyVStack(spacing: 12) {
                ForEach(filteredAndSortedSessions) { session in
                    ConversationListItem(
                        session: session,
                        onSelect: {
                            viewModel.selectedSession = session
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
                }
            }
            .padding(20)
        }
        .background(Color.fmBg.opacity(0.3))
    }
}

// MARK: - Conversation List Item
struct ConversationListItem: View {
    let session: ChatSessionResponse
    let onSelect: () -> Void
    let onDelete: () -> Void

    @State private var isHovered = false

    var body: some View {
        HStack(spacing: 16) {
            // Icon
            ZStack {
                Circle()
                    .fill(Color.fmPrimary.opacity(0.1))
                    .frame(width: 48, height: 48)

                Image(systemName: "message.fill")
                    .font(.system(size: 20))
                    .foregroundColor(Color.fmPrimary)
            }

            // Content
            VStack(alignment: .leading, spacing: 6) {
                HStack {
                    Text(session.name)
                        .font(.system(size: 15, weight: .medium))
                        .foregroundColor(Color.fmText)

                    Spacer()

                    Text(formatDate(session.lastMessageAt))
                        .font(.system(size: 12))
                        .foregroundColor(Color.fmText3)
                }

                HStack(spacing: 16) {
                    Label("\(session.messageCount) 条消息", systemImage: "bubble.left")
                        .font(.system(size: 12))
                        .foregroundColor(Color.fmText3)

                    if let documentIds = session.documentIds, !documentIds.isEmpty {
                        Label("\(documentIds.count) 个文档", systemImage: "doc")
                            .font(.system(size: 12))
                            .foregroundColor(Color.fmText3)
                    }
                }
            }

            // Actions (show on hover)
            if isHovered {
                HStack(spacing: 8) {
                    Button(action: onSelect) {
                        Image(systemName: "arrow.right.circle")
                            .font(.system(size: 18))
                            .foregroundColor(Color.fmPrimary)
                    }
                    .buttonStyle(PlainButtonStyle())

                    Button(action: onDelete) {
                        Image(systemName: "trash")
                            .font(.system(size: 18))
                            .foregroundColor(Color.fmRed)
                    }
                    .buttonStyle(PlainButtonStyle())
                }
            }
        }
        .padding(16)
        .background(Color.white)
        .cornerRadius(12)
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(isHovered ? Color.fmPrimary : Color.fmBorder, lineWidth: 1)
        )
        .onHover { hovering in
            isHovered = hovering
        }
        .onTapGesture {
            onSelect()
        }
    }

    private func formatDate(_ dateString: String?) -> String {
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

// MARK: - New Conversation Sheet
struct NewConversationSheet: View {
    let projectId: Int
    let onCreate: (String) -> Void

    @State private var conversationName = ""
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        VStack(spacing: 24) {
            HStack {
                Text("新建对话")
                    .font(.system(size: 18, weight: .semibold))
                    .foregroundColor(Color.fmText)

                Spacer()

                Button(action: { dismiss() }) {
                    Image(systemName: "xmark")
                        .font(.system(size: 14))
                        .foregroundColor(Color.fmText3)
                }
                .buttonStyle(PlainButtonStyle())
            }

            Divider()

            VStack(alignment: .leading, spacing: 8) {
                Text("对话名称")
                    .font(.system(size: 13, weight: .medium))
                    .foregroundColor(Color.fmText2)

                TextField("请输入对话名称", text: $conversationName)
                    .textFieldStyle(.plain)
                    .font(.system(size: 14))
                    .padding(12)
                    .background(Color.fmBg)
                    .cornerRadius(8)
            }

            Spacer()

            HStack(spacing: 12) {
                Button("取消") {
                    dismiss()
                }
                .fmSecondary()

                Button("创建") {
                    onCreate(conversationName.isEmpty ? "新对话" : conversationName)
                }
                .fmPrimary()
                .disabled(conversationName.trimmingCharacters(in: .whitespaces).isEmpty)
            }
        }
        .padding(24)
        .frame(width: 480, height: 280)
        .background(Color.white)
    }
}
