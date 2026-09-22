import SwiftUI
import Charts

struct ProjectDetailPage: View {
    let projectId: Int
    @StateObject private var viewModel = ProjectViewModel()
    @State private var selectedTab = "overview"

    var body: some View {
        VStack(spacing: 0) {
            if let errorMessage = viewModel.errorMessage {
                errorBanner(errorMessage)
            }

            if viewModel.isLoadingDashboard {
                loadingView
            } else if let dashboard = viewModel.dashboard {
                contentView(dashboard)
            } else {
                emptyStateView
            }
        }
        .task {
            await viewModel.loadDashboard(projectId: projectId)
            await viewModel.loadContexts(projectId: projectId)
        }
    }

    private func contentView(_ dashboard: ProjectService.ProjectDashboardResponse) -> some View {
        VStack(spacing: 0) {
            headerView(dashboard.project)
            Divider()

            // Tab Bar
            HStack(spacing: 0) {
                ProjectDetailTabButton(title: "项目概况", icon: "info.circle", isSelected: selectedTab == "overview") {
                    selectedTab = "overview"
                }
                ProjectDetailTabButton(title: "最近材料", icon: "folder", isSelected: selectedTab == "materials") {
                    selectedTab = "materials"
                }
                ProjectDetailTabButton(title: "知识脉络", icon: "network", isSelected: selectedTab == "contexts") {
                    selectedTab = "contexts"
                }
                ProjectDetailTabButton(title: "最近对话", icon: "message", isSelected: selectedTab == "chats") {
                    selectedTab = "chats"
                }
                Spacer()
            }
            .padding(.horizontal, 24)
            .padding(.top, 12)
            .background(Color.fmBg)

            Divider()

            // Content
            ScrollView {
                if selectedTab == "overview" {
                    overviewTabView(dashboard)
                } else if selectedTab == "materials" {
                    materialsTabView(dashboard.recentDocuments)
                } else if selectedTab == "contexts" {
                    contextsTabView
                } else {
                    chatsTabView(dashboard.recentChats)
                }
            }
        }
    }

    // MARK: - Header

    private func headerView(_ project: Project) -> some View {
        HStack(spacing: 16) {
            // Icon
            Image(systemName: "folder.fill.badge.gearshape")
                .font(.system(size: 24, weight: .semibold))
                .foregroundColor(.white)
                .frame(width: 56, height: 56)
                .background(
                    LinearGradient(
                        colors: [Color(hex: "42A5F5"), Color(hex: "1E88E5")],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                )
                .cornerRadius(14)

            // Project info
            VStack(alignment: .leading, spacing: 6) {
                HStack(spacing: 8) {
                    Text(project.name)
                        .font(.system(size: 18, weight: .semibold))
                        .foregroundColor(.fmText)
                        .lineLimit(1)

                    HStack(spacing: 4) {
                        Image(systemName: statusIcon(project.status))
                            .font(.system(size: 10))
                        Text(project.status)
                            .font(.system(size: 11, weight: .medium))
                    }
                    .foregroundColor(Color(hex: statusColor(project.status)))
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(Color(hex: statusColor(project.status)).opacity(0.1))
                    .cornerRadius(6)
                }

                HStack(spacing: 16) {
                    HStack(spacing: 4) {
                        Image(systemName: "calendar")
                            .font(.system(size: 11))
                        Text("创建于 \(formatDate(project.createdAt))")
                            .font(.system(size: 12))
                    }
                    .foregroundColor(.fmText3)

                    HStack(spacing: 4) {
                        Image(systemName: "clock")
                            .font(.system(size: 11))
                        Text("更新于 \(formatDate(project.updatedAt))")
                            .font(.system(size: 12))
                    }
                    .foregroundColor(.fmText3)
                }
            }

            Spacer()

            // Stats summary
            HStack(spacing: 20) {
                statBadge(icon: "doc", count: project.documentCount, label: "文档")
                statBadge(icon: "network", count: project.contextCount, label: "脉络")
                statBadge(icon: "message", count: project.chatSessionCount, label: "对话")
            }
        }
        .padding(.horizontal, 24)
        .padding(.vertical, 16)
        .background(Color.white)
    }

    private func statBadge(icon: String, count: Int, label: String) -> some View {
        VStack(spacing: 4) {
            HStack(spacing: 4) {
                Image(systemName: icon)
                    .font(.system(size: 12))
                Text("\(count)")
                    .font(.system(size: 16, weight: .semibold))
            }
            .foregroundColor(.fmText)

            Text(label)
                .font(.system(size: 11))
                .foregroundColor(.fmText3)
        }
    }

    // MARK: - Overview Tab

    private func overviewTabView(_ dashboard: ProjectService.ProjectDashboardResponse) -> some View {
        VStack(spacing: 24) {
            // Stats cards
            statsCardsView(dashboard)

            // Description section
            if let description = dashboard.project.description {
                descriptionSectionView(description)
            }

            // Quick stats
            quickStatsView(dashboard)
        }
        .padding(24)
    }

    private func statsCardsView(_ dashboard: ProjectService.ProjectDashboardResponse) -> some View {
        HStack(spacing: 16) {
            ProjectDetailStatCard(
                title: "文档总数",
                value: "\(dashboard.documentCount)",
                icon: "doc.on.doc",
                color: "42A5F5"
            )

            ProjectDetailStatCard(
                title: "知识脉络",
                value: "\(dashboard.contextCount)",
                icon: "network",
                color: "66BB6A"
            )

            ProjectDetailStatCard(
                title: "记忆数量",
                value: "\(dashboard.memoryCount)",
                icon: "brain",
                color: "FFA726"
            )

            ProjectDetailStatCard(
                title: "对话会话",
                value: "\(dashboard.chatSessionCount)",
                icon: "message.fill",
                color: "AB47BC"
            )
        }
    }

    private func descriptionSectionView(_ description: String) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "text.alignleft")
                    .font(.system(size: 16, weight: .medium))
                    .foregroundColor(Color(hex: "007AFF"))

                Text("项目描述")
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundColor(.fmText)

                Spacer()
            }

            Text(description)
                .font(.system(size: 14))
                .foregroundColor(.fmText2)
                .lineSpacing(6)
        }
        .padding(20)
        .background(Color.fmBg)
        .cornerRadius(12)
    }

    private func quickStatsView(_ dashboard: ProjectService.ProjectDashboardResponse) -> some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                Image(systemName: "chart.bar")
                    .font(.system(size: 16, weight: .medium))
                    .foregroundColor(Color(hex: "007AFF"))

                Text("快速统计")
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundColor(.fmText)

                Spacer()
            }

            VStack(spacing: 12) {
                quickStatRow(label: "最近文档", value: "\(dashboard.recentDocuments.count)")
                quickStatRow(label: "最近对话", value: "\(dashboard.recentChats.count)")
                quickStatRow(label: "项目状态", value: dashboard.project.status)
            }
        }
        .padding(20)
        .background(Color.fmBg)
        .cornerRadius(12)
    }

    private func quickStatRow(label: String, value: String) -> some View {
        HStack {
            Text(label)
                .font(.system(size: 14))
                .foregroundColor(.fmText2)
            Spacer()
            Text(value)
                .font(.system(size: 14, weight: .medium))
                .foregroundColor(.fmText)
        }
    }

    // MARK: - Materials Tab

    private func materialsTabView(_ documents: [ProjectService.ProjectDocument]) -> some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("最近文档")
                .font(.system(size: 18, weight: .semibold))
                .foregroundColor(.fmText)
                .padding(.horizontal, 24)
                .padding(.top, 24)

            if documents.isEmpty {
                emptySection(
                    icon: "doc",
                    title: "暂无文档",
                    message: "该项目还没有上传任何文档"
                )
            } else {
                VStack(spacing: 12) {
                    ForEach(documents, id: \.id) { doc in
                        documentRow(doc)
                    }
                }
                .padding(.horizontal, 24)
            }
        }
        .padding(.bottom, 24)
    }

    private func documentRow(_ doc: ProjectService.ProjectDocument) -> some View {
        HStack(spacing: 12) {
            Image(systemName: fileIcon(doc.fileType))
                .font(.system(size: 20))
                .foregroundColor(Color(hex: "42A5F5"))
                .frame(width: 40, height: 40)
                .background(Color(hex: "E3F2FD"))
                .cornerRadius(8)

            VStack(alignment: .leading, spacing: 4) {
                Text(doc.filename)
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(.fmText)

                HStack(spacing: 8) {
                    Text(doc.fileType.uppercased())
                        .font(.system(size: 11))
                        .foregroundColor(.fmText3)

                    Text("•")
                        .foregroundColor(.fmText3)

                    Text(formatDate(doc.createdAt))
                        .font(.system(size: 11))
                        .foregroundColor(.fmText3)
                }
            }

            Spacer()

            statusBadge(doc.status)
        }
        .padding(12)
        .background(Color.white)
        .cornerRadius(8)
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .stroke(Color.fmBorder, lineWidth: 1)
        )
    }

    // MARK: - Contexts Tab

    private var contextsTabView: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("知识脉络")
                .font(.system(size: 18, weight: .semibold))
                .foregroundColor(.fmText)
                .padding(.horizontal, 24)
                .padding(.top, 24)

            if viewModel.isLoadingContexts {
                ProgressView()
                    .frame(maxWidth: .infinity, maxHeight: 200)
            } else if viewModel.contexts.isEmpty {
                emptySection(
                    icon: "network",
                    title: "暂无知识脉络",
                    message: "该项目还没有创建知识脉络节点"
                )
            } else {
                VStack(spacing: 12) {
                    ForEach(viewModel.contexts, id: \.id) { context in
                        contextRow(context)
                    }
                }
                .padding(.horizontal, 24)
            }
        }
        .padding(.bottom, 24)
    }

    private func contextRow(_ context: ProjectService.ProjectContext) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: "circle.fill")
                    .font(.system(size: 8))
                    .foregroundColor(levelColor(context.level))

                Text(context.name)
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(.fmText)

                Spacer()

                Text("Level \(context.level)")
                    .font(.system(size: 11))
                    .foregroundColor(.fmText3)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(Color.fmBg2)
                    .cornerRadius(4)
            }

            if let description = context.description {
                Text(description)
                    .font(.system(size: 13))
                    .foregroundColor(.fmText2)
                    .lineLimit(2)
            }

            if !context.keywords.isEmpty {
                HStack(spacing: 6) {
                    ForEach(context.keywords.prefix(5), id: \.self) { keyword in
                        Text(keyword)
                            .font(.system(size: 11))
                            .foregroundColor(Color(hex: "42A5F5"))
                            .padding(.horizontal, 8)
                            .padding(.vertical, 4)
                            .background(Color(hex: "E3F2FD"))
                            .cornerRadius(4)
                    }
                }
            }
        }
        .padding(12)
        .background(Color.white)
        .cornerRadius(8)
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .stroke(Color.fmBorder, lineWidth: 1)
        )
    }

    // MARK: - Chats Tab

    private func chatsTabView(_ chats: [ProjectService.ProjectChatSession]) -> some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("最近对话")
                .font(.system(size: 18, weight: .semibold))
                .foregroundColor(.fmText)
                .padding(.horizontal, 24)
                .padding(.top, 24)

            if chats.isEmpty {
                emptySection(
                    icon: "message",
                    title: "暂无对话",
                    message: "该项目还没有创建对话会话"
                )
            } else {
                VStack(spacing: 12) {
                    ForEach(chats, id: \.id) { chat in
                        chatRow(chat)
                    }
                }
                .padding(.horizontal, 24)
            }
        }
        .padding(.bottom, 24)
    }

    private func chatRow(_ chat: ProjectService.ProjectChatSession) -> some View {
        HStack(spacing: 12) {
            Image(systemName: "message.fill")
                .font(.system(size: 20))
                .foregroundColor(Color(hex: "AB47BC"))
                .frame(width: 40, height: 40)
                .background(Color(hex: "F3E5F5"))
                .cornerRadius(8)

            VStack(alignment: .leading, spacing: 4) {
                Text(chat.name)
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(.fmText)

                Text("更新于 \(formatDate(chat.updatedAt))")
                    .font(.system(size: 11))
                    .foregroundColor(.fmText3)
            }

            Spacer()

            Image(systemName: "chevron.right")
                .font(.system(size: 12))
                .foregroundColor(.fmText3)
        }
        .padding(12)
        .background(Color.white)
        .cornerRadius(8)
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .stroke(Color.fmBorder, lineWidth: 1)
        )
    }

    // MARK: - Empty States

    private var emptyStateView: some View {
        VStack(spacing: 16) {
            Image(systemName: "folder.badge.questionmark")
                .font(.system(size: 48))
                .foregroundColor(.fmText3)

            Text("项目数据加载失败")
                .font(.system(size: 16, weight: .medium))
                .foregroundColor(.fmText2)

            Button(action: {
                Task {
                    await viewModel.loadDashboard(projectId: projectId)
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
            .buttonStyle(.plain)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color.fmBg)
    }

    private func emptySection(icon: String, title: String, message: String) -> some View {
        VStack(spacing: 12) {
            Image(systemName: icon)
                .font(.system(size: 36))
                .foregroundColor(.fmText3)

            Text(title)
                .font(.system(size: 15, weight: .medium))
                .foregroundColor(.fmText2)

            Text(message)
                .font(.system(size: 13))
                .foregroundColor(.fmText3)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 60)
    }

    private var loadingView: some View {
        VStack(spacing: 16) {
            ProgressView()
                .scaleEffect(1.2)

            Text("加载项目数据...")
                .font(.system(size: 14))
                .foregroundColor(.fmText3)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color.fmBg)
    }

    private func errorBanner(_ message: String) -> some View {
        HStack(spacing: 12) {
            Image(systemName: "exclamationmark.triangle.fill")
                .foregroundColor(.red)
            Text(message)
                .font(.system(size: 13))
                .foregroundColor(.fmText)
            Spacer()
        }
        .padding(12)
        .background(Color.red.opacity(0.1))
        .cornerRadius(8)
        .padding(.horizontal, 24)
        .padding(.vertical, 12)
    }

    // MARK: - Helper Functions

    private func formatDate(_ dateString: String) -> String {
        let formatter = ISO8601DateFormatter()
        if let date = formatter.date(from: dateString) {
            let displayFormatter = DateFormatter()
            displayFormatter.dateFormat = "yyyy-MM-dd"
            return displayFormatter.string(from: date)
        }
        return dateString
    }

    private func statusIcon(_ status: String) -> String {
        switch status.lowercased() {
        case "active": return "play.circle.fill"
        case "archived": return "archivebox.fill"
        case "completed": return "checkmark.circle.fill"
        default: return "circle.fill"
        }
    }

    private func statusColor(_ status: String) -> String {
        switch status.lowercased() {
        case "active": return "66BB6A"
        case "archived": return "94A3B8"
        case "completed": return "42A5F5"
        default: return "FFA726"
        }
    }

    private func fileIcon(_ fileType: String) -> String {
        switch fileType.lowercased() {
        case "pdf": return "doc.richtext"
        case "docx", "doc": return "doc.text"
        case "xlsx", "xls": return "tablecells"
        case "pptx", "ppt": return "rectangle.on.rectangle"
        case "txt": return "doc.plaintext"
        default: return "doc"
        }
    }

    private func statusBadge(_ status: String) -> some View {
        Text(status)
            .font(.system(size: 11, weight: .medium))
            .foregroundColor(status == "completed" ? Color(hex: "66BB6A") : Color(hex: "FFA726"))
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background((status == "completed" ? Color(hex: "66BB6A") : Color(hex: "FFA726")).opacity(0.1))
            .cornerRadius(4)
    }

    private func levelColor(_ level: Int) -> Color {
        switch level {
        case 1: return Color(hex: "42A5F5")
        case 2: return Color(hex: "66BB6A")
        case 3: return Color(hex: "FFA726")
        default: return Color(hex: "AB47BC")
        }
    }
}

// MARK: - Supporting Views

struct ProjectDetailTabButton: View {
    let title: String
    let icon: String
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: 6) {
                Image(systemName: icon)
                    .font(.system(size: 13))
                Text(title)
                    .font(.system(size: 14, weight: isSelected ? .semibold : .regular))
            }
            .foregroundColor(isSelected ? Color(hex: "007AFF") : Color.fmText3)
            .padding(.horizontal, 16)
            .padding(.vertical, 10)
            .background(isSelected ? Color(hex: "007AFF").opacity(0.08) : Color.clear)
            .cornerRadius(8)
        }
        .buttonStyle(.plain)
    }
}

struct ProjectDetailStatCard: View {
    let title: String
    let value: String
    let icon: String
    let color: String

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: icon)
                    .font(.system(size: 18))
                    .foregroundColor(Color(hex: color))
                Spacer()
            }

            VStack(alignment: .leading, spacing: 4) {
                Text(value)
                    .font(.system(size: 24, weight: .bold))
                    .foregroundColor(.fmText)

                Text(title)
                    .font(.system(size: 13))
                    .foregroundColor(.fmText3)
            }
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color.white)
        .cornerRadius(12)
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(Color.fmBorder, lineWidth: 1)
        )
    }
}
