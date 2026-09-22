import SwiftUI

struct AgentMemoryPage: View {
    let projectId: Int
    @StateObject private var viewModel = MemoryViewModel()
    @State private var searchText = ""
    @State private var selectedMemory: MemoryService.MemoryResponse?
    @State private var showCreateSheet = false
    @State private var showStatsSheet = false

    var filteredMemories: [MemoryService.MemoryResponse] {
        var result = viewModel.filteredMemories

        if !searchText.isEmpty {
            result = result.filter { memory in
                memory.content.localizedCaseInsensitiveContains(searchText) ||
                (memory.summary?.localizedCaseInsensitiveContains(searchText) ?? false) ||
                (memory.sourceType?.localizedCaseInsensitiveContains(searchText) ?? false)
            }
        }

        return result.sorted { $0.createdAt > $1.createdAt }
    }

    var body: some View {
        VStack(spacing: 0) {
            // Header
            HStack {
                Text("Agent 记忆")
                    .font(.system(size: 22, weight: .semibold))
                    .foregroundColor(Color.fmText)

                Spacer()

                Button(action: { showStatsSheet = true }) {
                    HStack(spacing: 4) {
                        Image(systemName: "chart.bar")
                        Text("统计")
                    }
                    .font(.system(size: 13))
                    .foregroundColor(Color.fmText)
                    .frame(height: 28)
                    .padding(.horizontal, 12)
                    .background(Color.fmBg2)
                    .cornerRadius(6)
                    .overlay(
                        RoundedRectangle(cornerRadius: 6)
                            .stroke(Color.fmBorder, lineWidth: 1)
                    )
                }
                .buttonStyle(.plain)

                Button(action: {
                    Task { await viewModel.autoPromoteMemories(projectId: projectId) }
                }) {
                    HStack(spacing: 4) {
                        Image(systemName: "arrow.up.circle")
                        Text("自动提升")
                    }
                    .font(.system(size: 13))
                    .foregroundColor(Color.fmText)
                    .frame(height: 28)
                    .padding(.horizontal, 12)
                    .background(Color.fmBg2)
                    .cornerRadius(6)
                    .overlay(
                        RoundedRectangle(cornerRadius: 6)
                            .stroke(Color.fmBorder, lineWidth: 1)
                    )
                }
                .buttonStyle(.plain)
                .disabled(viewModel.isProcessing)

                Button(action: { showCreateSheet = true }) {
                    HStack(spacing: 4) {
                        Image(systemName: "plus")
                        Text("创建记忆")
                    }
                    .font(.system(size: 13))
                    .foregroundColor(.white)
                    .frame(height: 28)
                    .padding(.horizontal, 12)
                    .background(Color.fmBlue)
                    .cornerRadius(6)
                }
                .buttonStyle(.plain)
            }
            .padding(.horizontal, 20)
            .padding(.vertical, 16)
            .background(Color.fmBg)

            Divider()
                .background(Color.fmBorder)

            // Filter bar
            HStack(spacing: 12) {
                // Search
                HStack(spacing: 6) {
                    Image(systemName: "magnifyingglass")
                        .font(.system(size: 13))
                        .foregroundColor(Color.fmText3)
                    TextField("搜索记忆内容...", text: $searchText)
                        .textFieldStyle(.plain)
                        .font(.system(size: 13))
                }
                .padding(.horizontal, 10)
                .frame(width: 300, height: 30)
                .background(Color.fmBg2)
                .cornerRadius(6)
                .overlay(
                    RoundedRectangle(cornerRadius: 6)
                        .stroke(Color.fmBorder, lineWidth: 1)
                )

                // Memory type filter buttons
                Button(action: { viewModel.filterType = nil }) {
                    Text("全部记忆")
                        .font(.system(size: 13))
                        .foregroundColor(viewModel.filterType == nil ? .white : Color.fmText)
                        .frame(height: 30)
                        .padding(.horizontal, 12)
                        .background(viewModel.filterType == nil ? Color.fmBlue : Color.fmBg2)
                        .cornerRadius(6)
                        .overlay(
                            RoundedRectangle(cornerRadius: 6)
                                .stroke(viewModel.filterType == nil ? Color.clear : Color.fmBorder, lineWidth: 1)
                        )
                }
                .buttonStyle(.plain)

                Button(action: { viewModel.filterType = "short_term" }) {
                    Text("短期记忆")
                        .font(.system(size: 13))
                        .foregroundColor(viewModel.filterType == "short_term" ? .white : Color.fmText)
                        .frame(height: 30)
                        .padding(.horizontal, 12)
                        .background(viewModel.filterType == "short_term" ? viewModel.memoryTypeColor("short_term") : Color.fmBg2)
                        .cornerRadius(6)
                        .overlay(
                            RoundedRectangle(cornerRadius: 6)
                                .stroke(viewModel.filterType == "short_term" ? Color.clear : Color.fmBorder, lineWidth: 1)
                        )
                }
                .buttonStyle(.plain)

                Button(action: { viewModel.filterType = "mid_term" }) {
                    Text("中期记忆")
                        .font(.system(size: 13))
                        .foregroundColor(viewModel.filterType == "mid_term" ? .white : Color.fmText)
                        .frame(height: 30)
                        .padding(.horizontal, 12)
                        .background(viewModel.filterType == "mid_term" ? viewModel.memoryTypeColor("mid_term") : Color.fmBg2)
                        .cornerRadius(6)
                        .overlay(
                            RoundedRectangle(cornerRadius: 6)
                                .stroke(viewModel.filterType == "mid_term" ? Color.clear : Color.fmBorder, lineWidth: 1)
                        )
                }
                .buttonStyle(.plain)

                Button(action: { viewModel.filterType = "long_term" }) {
                    Text("长期记忆")
                        .font(.system(size: 13))
                        .foregroundColor(viewModel.filterType == "long_term" ? .white : Color.fmText)
                        .frame(height: 30)
                        .padding(.horizontal, 12)
                        .background(viewModel.filterType == "long_term" ? viewModel.memoryTypeColor("long_term") : Color.fmBg2)
                        .cornerRadius(6)
                        .overlay(
                            RoundedRectangle(cornerRadius: 6)
                                .stroke(viewModel.filterType == "long_term" ? Color.clear : Color.fmBorder, lineWidth: 1)
                        )
                }
                .buttonStyle(.plain)

                Spacer()
            }
            .padding(.horizontal, 20)
            .padding(.vertical, 12)
            .background(Color.fmBg)

            Divider()
                .background(Color.fmBorder)

            // Success/Error messages
            if let successMessage = viewModel.successMessage {
                HStack {
                    Image(systemName: "checkmark.circle.fill")
                        .foregroundColor(.green)
                    Text(successMessage)
                        .font(.system(size: 13))
                        .foregroundColor(Color.fmText)
                    Spacer()
                    Button(action: { viewModel.clearMessages() }) {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundColor(Color.fmText3)
                    }
                    .buttonStyle(.plain)
                }
                .padding(.horizontal, 20)
                .padding(.vertical, 10)
                .background(Color.green.opacity(0.1))
            }

            if let errorMessage = viewModel.errorMessage {
                HStack {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .foregroundColor(.red)
                    Text(errorMessage)
                        .font(.system(size: 13))
                        .foregroundColor(Color.fmText)
                    Spacer()
                    Button(action: { viewModel.clearMessages() }) {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundColor(Color.fmText3)
                    }
                    .buttonStyle(.plain)
                }
                .padding(.horizontal, 20)
                .padding(.vertical, 10)
                .background(Color.red.opacity(0.1))
            }

            // Content area
            if viewModel.isLoading {
                VStack(spacing: 12) {
                    ProgressView()
                        .scaleEffect(1.2)
                    Text("加载记忆中...")
                        .font(.system(size: 14))
                        .foregroundColor(Color.fmText2)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
                .background(Color.fmBg)
            } else if filteredMemories.isEmpty {
                VStack(spacing: 16) {
                    Image(systemName: "brain.head.profile")
                        .font(.system(size: 56))
                        .foregroundColor(Color.fmText3)

                    Text(searchText.isEmpty ? "暂无记忆数据" : "没有找到匹配的记忆")
                        .font(.system(size: 16, weight: .medium))
                        .foregroundColor(Color.fmText)

                    Text(searchText.isEmpty ? "点击「创建记忆」按钮添加第一条记忆" : "尝试修改搜索条件或选择其他记忆类型")
                        .font(.system(size: 13))
                        .foregroundColor(Color.fmText2)

                    if searchText.isEmpty {
                        Button(action: { showCreateSheet = true }) {
                            HStack(spacing: 6) {
                                Image(systemName: "plus.circle.fill")
                                Text("创建记忆")
                            }
                            .font(.system(size: 14))
                            .foregroundColor(.white)
                            .padding(.horizontal, 20)
                            .padding(.vertical, 10)
                            .background(Color.fmBlue)
                            .cornerRadius(8)
                        }
                        .buttonStyle(.plain)
                    }
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
                .background(Color.fmBg)
            } else {
                ScrollView {
                    LazyVStack(spacing: 12) {
                        ForEach(filteredMemories) { memory in
                            MemoryBackendCard(memory: memory, viewModel: viewModel)
                                .onTapGesture {
                                    selectedMemory = memory
                                }
                        }
                    }
                    .padding(20)
                }
                .background(Color.fmBg)
            }
        }
        .sheet(isPresented: $showCreateSheet) {
            CreateMemorySheet(projectId: projectId, viewModel: viewModel)
        }
        .sheet(isPresented: $showStatsSheet) {
            MemoryStatsSheet(projectId: projectId, viewModel: viewModel)
        }
        .sheet(item: $selectedMemory) { memory in
            MemoryBackendDetailSheet(memory: memory)
        }
        .task {
            await viewModel.loadMemories(projectId: projectId)
            await viewModel.loadStats(projectId: projectId)
        }
    }
}

// MARK: - Memory Card for Backend Data

struct MemoryBackendCard: View {
    let memory: MemoryService.MemoryResponse
    let viewModel: MemoryViewModel
    @State private var isHovered = false

    var body: some View {
        HStack(alignment: .top, spacing: 16) {
            // Memory type icon
            ZStack {
                Circle()
                    .fill(viewModel.memoryTypeColor(memory.memoryType).opacity(0.15))
                    .frame(width: 48, height: 48)

                Image(systemName: memoryTypeIcon(memory.memoryType))
                    .font(.system(size: 20))
                    .foregroundColor(viewModel.memoryTypeColor(memory.memoryType))
            }

            VStack(alignment: .leading, spacing: 8) {
                // Header
                HStack(spacing: 8) {
                    Text(viewModel.memoryTypeLabel(memory.memoryType))
                        .font(.system(size: 15, weight: .medium))
                        .foregroundColor(Color.fmText)

                    Text("ID: \(memory.id)")
                        .font(.system(size: 11))
                        .foregroundColor(Color.fmText3)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(Color.fmBorder)
                        .cornerRadius(4)

                    Spacer()

                    // Relevance score
                    HStack(spacing: 3) {
                        Image(systemName: "star.fill")
                            .font(.system(size: 9))
                        Text("\(memory.relevanceScore)")
                            .font(.system(size: 11))
                    }
                    .foregroundColor(Color.fmOrange)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 3)
                    .background(Color.fmOrange.opacity(0.1))
                    .cornerRadius(4)
                }

                // Source type
                if let sourceType = memory.sourceType {
                    Text(sourceType)
                        .font(.system(size: 12))
                        .foregroundColor(Color.fmText3)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 3)
                        .background(Color.fmBorder)
                        .cornerRadius(4)
                }

                // Content preview
                if let summary = memory.summary {
                    Text(summary)
                        .font(.system(size: 13, weight: .medium))
                        .foregroundColor(Color.fmText)
                        .lineLimit(1)
                }

                Text(memory.content)
                    .font(.system(size: 13))
                    .foregroundColor(Color.fmText2)
                    .lineLimit(2)

                // Footer
                HStack(spacing: 16) {
                    HStack(spacing: 4) {
                        Image(systemName: "clock")
                            .font(.system(size: 10))
                        Text(formatTimestamp(memory.createdAt))
                            .font(.system(size: 12))
                    }
                    .foregroundColor(Color.fmText3)

                    HStack(spacing: 4) {
                        Image(systemName: "eye")
                            .font(.system(size: 10))
                        Text("访问 \(memory.accessCount) 次")
                            .font(.system(size: 12))
                    }
                    .foregroundColor(Color.fmText3)

                    Spacer()
                }
            }
        }
        .padding(16)
        .background(Color.fmBg2)
        .cornerRadius(8)
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .stroke(isHovered ? Color.fmBlue : Color.fmBorder, lineWidth: 1)
        )
        .shadow(color: isHovered ? Color.black.opacity(0.08) : Color.clear, radius: 8, x: 0, y: 2)
        .scaleEffect(isHovered ? 1.005 : 1.0)
        .animation(.easeInOut(duration: 0.15), value: isHovered)
        .onHover { hovering in
            isHovered = hovering
        }
    }

    private func memoryTypeIcon(_ type: String) -> String {
        switch type {
        case "short_term": return "clock"
        case "mid_term": return "calendar"
        case "long_term": return "archivebox.fill"
        default: return "brain.head.profile"
        }
    }

    private func formatTimestamp(_ timestamp: String) -> String {
        let formatter = ISO8601DateFormatter()
        if let date = formatter.date(from: timestamp) {
            let displayFormatter = DateFormatter()
            displayFormatter.dateFormat = "MM-dd HH:mm"
            return displayFormatter.string(from: date)
        }
        return timestamp
    }
}

// MARK: - Create Memory Sheet

struct CreateMemorySheet: View {
    let projectId: Int
    let viewModel: MemoryViewModel
    @Environment(\.dismiss) var dismiss

    @State private var memoryType = "short_term"
    @State private var content = ""
    @State private var summary = ""
    @State private var sourceType = ""
    @State private var keywordsText = ""
    @State private var importanceScore = 5.0

    var body: some View {
        VStack(spacing: 0) {
            // Header
            HStack {
                Text("创建记忆")
                    .font(.system(size: 18, weight: .semibold))
                    .foregroundColor(Color.fmText)

                Spacer()

                Button(action: { dismiss() }) {
                    Image(systemName: "xmark.circle.fill")
                        .font(.system(size: 22))
                        .foregroundColor(Color.fmText3)
                }
                .buttonStyle(.plain)
            }
            .padding(20)
            .background(Color.fmBg)

            Divider()
                .background(Color.fmBorder)

            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    // Memory type
                    VStack(alignment: .leading, spacing: 8) {
                        Text("记忆类型")
                            .font(.system(size: 13, weight: .medium))
                            .foregroundColor(Color.fmText)

                        HStack(spacing: 12) {
                            ForEach(["short_term", "mid_term", "long_term"], id: \.self) { type in
                                Button(action: { memoryType = type }) {
                                    Text(viewModel.memoryTypeLabel(type))
                                        .font(.system(size: 13))
                                        .foregroundColor(memoryType == type ? .white : Color.fmText)
                                        .padding(.horizontal, 16)
                                        .padding(.vertical, 8)
                                        .background(memoryType == type ? viewModel.memoryTypeColor(type) : Color.fmBg2)
                                        .cornerRadius(6)
                                        .overlay(
                                            RoundedRectangle(cornerRadius: 6)
                                                .stroke(memoryType == type ? Color.clear : Color.fmBorder, lineWidth: 1)
                                        )
                                }
                                .buttonStyle(.plain)
                            }
                        }
                    }

                    // Content
                    VStack(alignment: .leading, spacing: 8) {
                        Text("记忆内容 *")
                            .font(.system(size: 13, weight: .medium))
                            .foregroundColor(Color.fmText)

                        TextEditor(text: $content)
                            .font(.system(size: 13))
                            .frame(height: 120)
                            .padding(8)
                            .background(Color.fmBg2)
                            .cornerRadius(6)
                            .overlay(
                                RoundedRectangle(cornerRadius: 6)
                                    .stroke(Color.fmBorder, lineWidth: 1)
                            )
                    }

                    // Summary
                    VStack(alignment: .leading, spacing: 8) {
                        Text("摘要")
                            .font(.system(size: 13, weight: .medium))
                            .foregroundColor(Color.fmText)

                        TextField("简短描述...", text: $summary)
                            .textFieldStyle(.plain)
                            .font(.system(size: 13))
                            .padding(10)
                            .background(Color.fmBg2)
                            .cornerRadius(6)
                            .overlay(
                                RoundedRectangle(cornerRadius: 6)
                                    .stroke(Color.fmBorder, lineWidth: 1)
                            )
                    }

                    // Source type
                    VStack(alignment: .leading, spacing: 8) {
                        Text("来源类型")
                            .font(.system(size: 13, weight: .medium))
                            .foregroundColor(Color.fmText)

                        TextField("如：对话、文档、分析等", text: $sourceType)
                            .textFieldStyle(.plain)
                            .font(.system(size: 13))
                            .padding(10)
                            .background(Color.fmBg2)
                            .cornerRadius(6)
                            .overlay(
                                RoundedRectangle(cornerRadius: 6)
                                    .stroke(Color.fmBorder, lineWidth: 1)
                            )
                    }

                    // Keywords
                    VStack(alignment: .leading, spacing: 8) {
                        Text("关键词")
                            .font(.system(size: 13, weight: .medium))
                            .foregroundColor(Color.fmText)

                        TextField("用逗号分隔多个关键词", text: $keywordsText)
                            .textFieldStyle(.plain)
                            .font(.system(size: 13))
                            .padding(10)
                            .background(Color.fmBg2)
                            .cornerRadius(6)
                            .overlay(
                                RoundedRectangle(cornerRadius: 6)
                                    .stroke(Color.fmBorder, lineWidth: 1)
                            )
                    }

                    // Importance score
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Text("重要性评分")
                                .font(.system(size: 13, weight: .medium))
                                .foregroundColor(Color.fmText)

                            Spacer()

                            Text(String(format: "%.1f", importanceScore))
                                .font(.system(size: 13))
                                .foregroundColor(Color.fmBlue)
                        }

                        Slider(value: $importanceScore, in: 0...10, step: 0.5)
                            .accentColor(Color.fmBlue)
                    }
                }
                .padding(20)
            }
            .background(Color.fmBg)

            Divider()
                .background(Color.fmBorder)

            // Footer
            HStack(spacing: 12) {
                Button(action: { dismiss() }) {
                    Text("取消")
                        .font(.system(size: 13))
                        .foregroundColor(Color.fmText)
                        .frame(height: 36)
                        .frame(maxWidth: .infinity)
                        .background(Color.fmBg2)
                        .cornerRadius(6)
                        .overlay(
                            RoundedRectangle(cornerRadius: 6)
                                .stroke(Color.fmBorder, lineWidth: 1)
                        )
                }
                .buttonStyle(.plain)

                Button(action: {
                    Task {
                        let keywords = keywordsText.isEmpty ? nil : keywordsText.split(separator: ",").map { String($0.trimmingCharacters(in: .whitespaces)) }
                        await viewModel.createMemory(
                            projectId: projectId,
                            memoryType: memoryType,
                            content: content,
                            summary: summary.isEmpty ? nil : summary,
                            sourceType: sourceType.isEmpty ? nil : sourceType,
                            keywords: keywords,
                            importanceScore: importanceScore
                        )
                        dismiss()
                    }
                }) {
                    Text("创建")
                        .font(.system(size: 13))
                        .foregroundColor(.white)
                        .frame(height: 36)
                        .frame(maxWidth: .infinity)
                        .background(content.isEmpty ? Color.fmText3 : Color.fmBlue)
                        .cornerRadius(6)
                }
                .buttonStyle(.plain)
                .disabled(content.isEmpty || viewModel.isCreating)
            }
            .padding(.horizontal, 20)
            .padding(.vertical, 16)
            .background(Color.fmBg)
        }
        .frame(width: 600, height: 700)
    }
}

// MARK: - Memory Stats Sheet

struct MemoryStatsSheet: View {
    let projectId: Int
    let viewModel: MemoryViewModel
    @Environment(\.dismiss) var dismiss

    var body: some View {
        VStack(spacing: 0) {
            // Header
            HStack {
                Text("记忆统计")
                    .font(.system(size: 18, weight: .semibold))
                    .foregroundColor(Color.fmText)

                Spacer()

                Button(action: { dismiss() }) {
                    Image(systemName: "xmark.circle.fill")
                        .font(.system(size: 22))
                        .foregroundColor(Color.fmText3)
                }
                .buttonStyle(.plain)
            }
            .padding(20)
            .background(Color.fmBg)

            Divider()
                .background(Color.fmBorder)

            if let stats = viewModel.stats {
                ScrollView {
                    VStack(spacing: 20) {
                        // Total memories
                        HStack(spacing: 20) {
                            MemoryStatCard(
                                title: "总记忆数",
                                value: "\(stats.totalMemories)",
                                icon: "brain.head.profile",
                                color: Color.fmBlue
                            )

                            MemoryStatCard(
                                title: "总访问次数",
                                value: "\(stats.totalAccessCount)",
                                icon: "eye.fill",
                                color: Color.fmOrange
                            )
                        }

                        // By type
                        VStack(alignment: .leading, spacing: 12) {
                            Text("按类型分布")
                                .font(.system(size: 15, weight: .semibold))
                                .foregroundColor(Color.fmText)

                            HStack(spacing: 12) {
                                MemoryStatCard(
                                    title: "短期记忆",
                                    value: "\(stats.shortTermCount)",
                                    icon: "clock",
                                    color: viewModel.memoryTypeColor("short_term")
                                )

                                MemoryStatCard(
                                    title: "中期记忆",
                                    value: "\(stats.midTermCount)",
                                    icon: "calendar",
                                    color: viewModel.memoryTypeColor("mid_term")
                                )

                                MemoryStatCard(
                                    title: "长期记忆",
                                    value: "\(stats.longTermCount)",
                                    icon: "archivebox.fill",
                                    color: viewModel.memoryTypeColor("long_term")
                                )
                            }
                        }

                        // By source
                        if !stats.bySourceType.isEmpty {
                            VStack(alignment: .leading, spacing: 12) {
                                Text("按来源类型")
                                    .font(.system(size: 15, weight: .semibold))
                                    .foregroundColor(Color.fmText)

                                VStack(spacing: 8) {
                                    ForEach(Array(stats.bySourceType.sorted(by: { $0.value > $1.value })), id: \.key) { key, value in
                                        HStack {
                                            Text(key)
                                                .font(.system(size: 13))
                                                .foregroundColor(Color.fmText)

                                            Spacer()

                                            Text("\(value)")
                                                .font(.system(size: 13, weight: .medium))
                                                .foregroundColor(Color.fmBlue)
                                        }
                                        .padding(12)
                                        .background(Color.fmBg2)
                                        .cornerRadius(6)
                                    }
                                }
                            }
                        }
                    }
                    .padding(20)
                }
                .background(Color.fmBg)
            } else {
                VStack(spacing: 12) {
                    ProgressView()
                    Text("加载统计数据...")
                        .font(.system(size: 13))
                        .foregroundColor(Color.fmText2)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
                .background(Color.fmBg)
            }
        }
        .frame(width: 700, height: 600)
        .task {
            await viewModel.loadStats(projectId: projectId)
        }
    }
}

struct MemoryStatCard: View {
    let title: String
    let value: String
    let icon: String
    let color: Color

    var body: some View {
        VStack(spacing: 12) {
            Image(systemName: icon)
                .font(.system(size: 32))
                .foregroundColor(color)

            Text(value)
                .font(.system(size: 24, weight: .bold))
                .foregroundColor(Color.fmText)

            Text(title)
                .font(.system(size: 13))
                .foregroundColor(Color.fmText2)
        }
        .frame(maxWidth: .infinity)
        .padding(20)
        .background(color.opacity(0.1))
        .cornerRadius(12)
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(color.opacity(0.2), lineWidth: 1)
        )
    }
}

// MARK: - Memory Detail Sheet

struct MemoryBackendDetailSheet: View {
    let memory: MemoryService.MemoryResponse
    @Environment(\.dismiss) var dismiss

    var body: some View {
        VStack(spacing: 0) {
            // Header
            HStack(spacing: 16) {
                ZStack {
                    Circle()
                        .fill(memoryTypeColor(memory.memoryType).opacity(0.15))
                        .frame(width: 64, height: 64)

                    Image(systemName: memoryTypeIcon(memory.memoryType))
                        .font(.system(size: 28))
                        .foregroundColor(memoryTypeColor(memory.memoryType))
                }

                VStack(alignment: .leading, spacing: 6) {
                    HStack(spacing: 8) {
                        Text(memoryTypeLabel(memory.memoryType))
                            .font(.system(size: 20, weight: .semibold))
                            .foregroundColor(Color.fmText)

                        Text("ID: \(memory.id)")
                            .font(.system(size: 12))
                            .foregroundColor(Color.fmText3)
                            .padding(.horizontal, 8)
                            .padding(.vertical, 3)
                            .background(Color.fmBorder)
                            .cornerRadius(4)
                    }

                    HStack(spacing: 12) {
                        if let sourceType = memory.sourceType {
                            Text(sourceType)
                                .font(.system(size: 13))
                                .foregroundColor(Color.fmText3)
                                .padding(.horizontal, 8)
                                .padding(.vertical, 4)
                                .background(Color.fmBorder)
                                .cornerRadius(4)
                        }

                        HStack(spacing: 4) {
                            Image(systemName: "star.fill")
                                .font(.system(size: 10))
                            Text("相关度: \(memory.relevanceScore)")
                                .font(.system(size: 12))
                        }
                        .foregroundColor(Color.fmOrange)
                        .padding(.horizontal, 10)
                        .padding(.vertical, 4)
                        .background(Color.fmOrange.opacity(0.1))
                        .cornerRadius(4)
                    }
                }

                Spacer()

                Button(action: { dismiss() }) {
                    Image(systemName: "xmark.circle.fill")
                        .font(.system(size: 24))
                        .foregroundColor(Color.fmText3)
                }
                .buttonStyle(.plain)
            }
            .padding(24)
            .background(Color.fmBg)

            Divider()
                .background(Color.fmBorder)

            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    // Summary
                    if let summary = memory.summary {
                        MemorySection(icon: "text.quote", title: "摘要") {
                            Text(summary)
                                .font(.system(size: 14, weight: .medium))
                                .foregroundColor(Color.fmText)
                        }
                    }

                    // Content
                    MemorySection(icon: "doc.text", title: "记忆内容") {
                        Text(memory.content)
                            .font(.system(size: 14))
                            .foregroundColor(Color.fmText2)
                            .lineSpacing(4)
                    }

                    // Metadata
                    MemorySection(icon: "info.circle", title: "详细信息") {
                        VStack(spacing: 8) {
                            InfoRow(label: "项目ID", value: "\(memory.projectId)")
                            InfoRow(label: "记忆类型", value: memoryTypeLabel(memory.memoryType))
                            InfoRow(label: "相关度评分", value: "\(memory.relevanceScore)")
                            InfoRow(label: "访问次数", value: "\(memory.accessCount)")
                            InfoRow(label: "创建时间", value: formatFullTimestamp(memory.createdAt))

                            if let sourceType = memory.sourceType {
                                InfoRow(label: "来源类型", value: sourceType)
                            }
                        }
                    }
                }
                .padding(24)
            }
            .background(Color.fmBg)
        }
        .frame(width: 800, height: 600)
    }

    private func memoryTypeIcon(_ type: String) -> String {
        switch type {
        case "short_term": return "clock"
        case "mid_term": return "calendar"
        case "long_term": return "archivebox.fill"
        default: return "brain.head.profile"
        }
    }

    private func memoryTypeColor(_ type: String) -> Color {
        switch type {
        case "short_term": return .blue
        case "mid_term": return .orange
        case "long_term": return .purple
        default: return .gray
        }
    }

    private func memoryTypeLabel(_ type: String) -> String {
        switch type {
        case "short_term": return "短期记忆"
        case "mid_term": return "中期记忆"
        case "long_term": return "长期记忆"
        default: return type
        }
    }

    private func formatFullTimestamp(_ timestamp: String) -> String {
        let formatter = ISO8601DateFormatter()
        if let date = formatter.date(from: timestamp) {
            let displayFormatter = DateFormatter()
            displayFormatter.dateFormat = "yyyy-MM-dd HH:mm:ss"
            return displayFormatter.string(from: date)
        }
        return timestamp
    }
}
