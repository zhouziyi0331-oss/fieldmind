import SwiftUI

// MARK: - Memory Card

struct MemoryCard: View {
    let memory: AgentMemory
    @State private var isHovered = false

    var body: some View {
        HStack(alignment: .top, spacing: 16) {
            // Agent icon
            ZStack {
                Circle()
                    .fill(agentTypeColor(memory.agentType).opacity(0.15))
                    .frame(width: 48, height: 48)

                Image(systemName: agentTypeIcon(memory.agentType))
                    .font(.system(size: 20))
                    .foregroundColor(agentTypeColor(memory.agentType))
            }

            VStack(alignment: .leading, spacing: 8) {
                // Header: title with badges
                HStack(spacing: 8) {
                    Text(memory.title)
                        .font(.system(size: 15, weight: .medium))
                        .foregroundColor(Color.fmText)
                        .lineLimit(1)

                    if memory.isPinned {
                        Image(systemName: "pin.fill")
                            .font(.system(size: 10))
                            .foregroundColor(Color.fmBlue)
                    }

                    if memory.isArchived {
                        Text("已归档")
                            .font(.system(size: 10))
                            .foregroundColor(Color.fmText3)
                            .padding(.horizontal, 6)
                            .padding(.vertical, 2)
                            .background(Color.fmBorder)
                            .cornerRadius(4)
                    }

                    Spacer()

                    // Importance badge
                    HStack(spacing: 3) {
                        Image(systemName: importanceIcon(memory.importance))
                            .font(.system(size: 9))
                        Text(String(format: "%.2f", memory.importance))
                            .font(.system(size: 11))
                    }
                    .foregroundColor(importanceColor(memory.importance))
                    .padding(.horizontal, 8)
                    .padding(.vertical, 3)
                    .background(importanceColor(memory.importance).opacity(0.1))
                    .cornerRadius(4)
                }

                // Agent name and memory type
                HStack(spacing: 8) {
                    Text(memory.agentName)
                        .font(.system(size: 12))
                        .foregroundColor(agentTypeColor(memory.agentType))
                        .padding(.horizontal, 8)
                        .padding(.vertical, 3)
                        .background(agentTypeColor(memory.agentType).opacity(0.1))
                        .cornerRadius(4)

                    Text(memory.memoryType)
                        .font(.system(size: 12))
                        .foregroundColor(Color.fmText3)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 3)
                        .background(Color.fmBorder)
                        .cornerRadius(4)

                    if let projectName = memory.projectName {
                        HStack(spacing: 3) {
                            Image(systemName: "folder")
                                .font(.system(size: 9))
                            Text(projectName)
                                .font(.system(size: 12))
                        }
                        .foregroundColor(Color.fmText3)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 3)
                        .background(Color.fmBorder)
                        .cornerRadius(4)
                    }
                }

                // Content preview
                Text(memory.content)
                    .font(.system(size: 13))
                    .foregroundColor(Color.fmText2)
                    .lineLimit(2)
                    .fixedSize(horizontal: false, vertical: true)

                // Tags
                if !memory.tags.isEmpty {
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 6) {
                            ForEach(memory.tags, id: \.self) { tag in
                                Text(tag)
                                    .font(.system(size: 11))
                                    .foregroundColor(Color.fmText3)
                                    .padding(.horizontal, 8)
                                    .padding(.vertical, 3)
                                    .background(Color.fmBg2)
                                    .cornerRadius(4)
                            }
                        }
                    }
                }

                // Footer: timestamp, token count, related count
                HStack(spacing: 16) {
                    HStack(spacing: 4) {
                        Image(systemName: "clock")
                            .font(.system(size: 10))
                        Text(formatTimestamp(memory.timestamp))
                            .font(.system(size: 12))
                    }
                    .foregroundColor(Color.fmText3)

                    if let tokenCount = memory.tokenCount {
                        HStack(spacing: 4) {
                            Image(systemName: "doc.text")
                                .font(.system(size: 10))
                            Text("\(tokenCount) tokens")
                                .font(.system(size: 12))
                        }
                        .foregroundColor(Color.fmText3)
                    }

                    if !memory.relatedMemories.isEmpty {
                        HStack(spacing: 4) {
                            Image(systemName: "link")
                                .font(.system(size: 10))
                            Text("\(memory.relatedMemories.count) 个关联")
                                .font(.system(size: 12))
                        }
                        .foregroundColor(Color.fmText3)
                    }

                    Spacer()

                    Text(memory.context)
                        .font(.system(size: 11, weight: .medium))
                        .foregroundColor(Color.fmText3)
                        .lineLimit(1)
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

    private func agentTypeIcon(_ type: String) -> String {
        switch type {
        case "对话助手": return "message.fill"
        case "数据分析": return "chart.bar.xaxis"
        case "文本处理": return "doc.text.fill"
        case "可视化生成": return "chart.pie.fill"
        case "报告撰写": return "doc.richtext.fill"
        default: return "brain.head.profile"
        }
    }

    private func agentTypeColor(_ type: String) -> Color {
        switch type {
        case "对话助手": return Color.fmBlue
        case "数据分析": return Color.fmPurple
        case "文本处理": return Color.fmGreen
        case "可视化生成": return Color.fmOrange
        case "报告撰写": return Color(red: 0.8, green: 0.4, blue: 0.6)  // Pink
        default: return Color.fmText3
        }
    }

    private func importanceIcon(_ importance: String) -> String {
        switch importance {
        case "高": return "exclamationmark.triangle.fill"
        case "中": return "info.circle.fill"
        case "低": return "minus.circle.fill"
        default: return "circle.fill"
        }
    }

    private func importanceIcon(_ importance: Double) -> String {
        importanceIcon(importance >= 0.8 ? "高" : (importance >= 0.5 ? "中" : "低"))
    }

    private func importanceColor(_ importance: String) -> Color {
        switch importance {
        case "高": return .fmError
        case "中": return Color.fmOrange
        case "低": return Color.fmText3
        default: return Color.fmText3
        }
    }

    private func importanceColor(_ importance: Double) -> Color {
        importanceColor(importance >= 0.8 ? "高" : (importance >= 0.5 ? "中" : "低"))
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

// MARK: - Memory Detail Sheet

struct MemoryDetailSheet: View {
    let memory: AgentMemory
    @Environment(\.dismiss) var dismiss

    var body: some View {
        VStack(spacing: 0) {
            // Header
            HStack(spacing: 16) {
                ZStack {
                    Circle()
                        .fill(agentTypeColor(memory.agentType).opacity(0.15))
                        .frame(width: 64, height: 64)

                    Image(systemName: agentTypeIcon(memory.agentType))
                        .font(.system(size: 28))
                        .foregroundColor(agentTypeColor(memory.agentType))
                }

                VStack(alignment: .leading, spacing: 6) {
                    HStack(spacing: 8) {
                        Text(memory.title)
                            .font(.system(size: 20, weight: .semibold))
                            .foregroundColor(Color.fmText)

                        if memory.isPinned {
                            Image(systemName: "pin.fill")
                                .font(.system(size: 12))
                                .foregroundColor(Color.fmBlue)
                        }

                        if memory.isArchived {
                            Text("已归档")
                                .font(.system(size: 11))
                                .foregroundColor(Color.fmText3)
                                .padding(.horizontal, 8)
                                .padding(.vertical, 3)
                                .background(Color.fmBorder)
                                .cornerRadius(4)
                        }
                    }

                    HStack(spacing: 8) {
                        Text(memory.agentName)
                            .font(.system(size: 13))
                            .foregroundColor(agentTypeColor(memory.agentType))
                            .padding(.horizontal, 8)
                            .padding(.vertical, 4)
                            .background(agentTypeColor(memory.agentType).opacity(0.1))
                            .cornerRadius(4)

                        Text(memory.memoryType)
                            .font(.system(size: 13))
                            .foregroundColor(Color.fmText3)
                            .padding(.horizontal, 8)
                            .padding(.vertical, 4)
                            .background(Color.fmBorder)
                            .cornerRadius(4)

                        HStack(spacing: 4) {
                            Image(systemName: importanceIcon(memory.importance))
                                .font(.system(size: 10))
                            Text(String(format: "%.2f", memory.importance))
                                .font(.system(size: 12))
                        }
                        .foregroundColor(importanceColor(memory.importance))
                        .padding(.horizontal, 10)
                        .padding(.vertical, 4)
                        .background(importanceColor(memory.importance).opacity(0.1))
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
                    // Memory content
                    MemorySection(icon: "doc.text", title: "记忆内容") {
                        Text(memory.content)
                            .font(.system(size: 14))
                            .foregroundColor(Color.fmText2)
                            .lineSpacing(4)
                    }

                    // Context
                    MemorySection(icon: "info.circle", title: "上下文") {
                        Text(memory.context)
                            .font(.system(size: 14))
                            .foregroundColor(Color.fmText2)
                    }

                    // Project info
                    if let projectName = memory.projectName {
                        MemorySection(icon: "folder", title: "关联项目") {
                            HStack(spacing: 8) {
                                Text(projectName)
                                    .font(.system(size: 14))
                                    .foregroundColor(Color.fmBlue)
                                    .padding(.horizontal, 12)
                                    .padding(.vertical, 8)
                                    .background(Color.fmBlue.opacity(0.1))
                                    .cornerRadius(6)

                                Spacer()
                            }
                        }
                    }

                    // Tags
                    if !memory.tags.isEmpty {
                        MemorySection(icon: "tag", title: "标签") {
                            FlowLayout(spacing: 8) {
                                ForEach(memory.tags, id: \.self) { tag in
                                    Text(tag)
                                        .font(.system(size: 13))
                                        .foregroundColor(Color.fmText)
                                        .padding(.horizontal, 12)
                                        .padding(.vertical, 6)
                                        .background(Color.fmBg2)
                                        .cornerRadius(6)
                                }
                            }
                        }
                    }

                    // Related memories
                    if !memory.relatedMemories.isEmpty {
                        MemorySection(icon: "link", title: "关联记忆") {
                            VStack(alignment: .leading, spacing: 8) {
                                ForEach(memory.relatedMemories, id: \.self) { relatedId in
                                    if let relatedMemory = AgentMemory.demoList.first(where: { $0.id == relatedId }) {
                                        HStack(spacing: 12) {
                                            Circle()
                                                .fill(agentTypeColor(relatedMemory.agentType).opacity(0.2))
                                                .frame(width: 8, height: 8)

                                            VStack(alignment: .leading, spacing: 2) {
                                                Text(relatedMemory.title)
                                                    .font(.system(size: 13, weight: .medium))
                                                    .foregroundColor(Color.fmBlue)

                                                Text("\(relatedMemory.agentName) • \(relatedMemory.memoryType)")
                                                    .font(.system(size: 12))
                                                    .foregroundColor(Color.fmText3)
                                            }

                                            Spacer()

                                            Image(systemName: "arrow.right")
                                                .font(.system(size: 11))
                                                .foregroundColor(Color.fmText3)
                                        }
                                        .padding(12)
                                        .background(Color.fmBg2)
                                        .cornerRadius(6)
                                    }
                                }
                            }
                        }
                    }

                    // Metadata
                    MemorySection(icon: "gearshape.2", title: "技术信息") {
                        VStack(spacing: 8) {
                            InfoRow(label: "时间戳", value: formatFullTimestamp(memory.timestamp))

                            if let tokenCount = memory.tokenCount {
                                InfoRow(label: "Token 占用", value: "\(tokenCount) tokens")
                            }

                            InfoRow(label: "Agent 类型", value: memory.agentType)
                            InfoRow(label: "记忆类型", value: memory.memoryType)
                            InfoRow(label: "重要性", value: String(format: "%.2f", memory.importance))
                            InfoRow(label: "固定状态", value: memory.isPinned ? "已固定" : "未固定")
                            InfoRow(label: "归档状态", value: memory.isArchived ? "已归档" : "活跃")

                            if !memory.metadata.isEmpty {
                                Divider()
                                    .background(Color.fmBorder)
                                    .padding(.vertical, 4)

                                ForEach(memory.metadata.sorted(by: { $0.key < $1.key }), id: \.key) { key, value in
                                    InfoRow(label: key, value: value)
                                }
                            }
                        }
                    }
                }
                .padding(24)
            }
            .background(Color.fmBg)

            Divider()
                .background(Color.fmBorder)

            // Footer actions
            HStack(spacing: 12) {
                Button(action: {}) {
                    HStack(spacing: 6) {
                        Image(systemName: memory.isPinned ? "pin.slash" : "pin")
                        Text(memory.isPinned ? "取消固定" : "固定")
                    }
                    .font(.system(size: 13))
                    .foregroundColor(Color.fmText)
                    .frame(height: 32)
                    .padding(.horizontal, 16)
                    .background(Color.fmBg2)
                    .cornerRadius(6)
                    .overlay(
                        RoundedRectangle(cornerRadius: 6)
                            .stroke(Color.fmBorder, lineWidth: 1)
                    )
                }
                .buttonStyle(.plain)

                Button(action: {}) {
                    HStack(spacing: 6) {
                        Image(systemName: memory.isArchived ? "tray.and.arrow.up" : "archivebox")
                        Text(memory.isArchived ? "取消归档" : "归档")
                    }
                    .font(.system(size: 13))
                    .foregroundColor(Color.fmText)
                    .frame(height: 32)
                    .padding(.horizontal, 16)
                    .background(Color.fmBg2)
                    .cornerRadius(6)
                    .overlay(
                        RoundedRectangle(cornerRadius: 6)
                            .stroke(Color.fmBorder, lineWidth: 1)
                    )
                }
                .buttonStyle(.plain)

                Spacer()

                Button(action: {}) {
                    HStack(spacing: 6) {
                        Image(systemName: "trash")
                        Text("删除记忆")
                    }
                    .font(.system(size: 13))
                    .foregroundColor(.white)
                    .frame(height: 32)
                    .padding(.horizontal, 16)
                    .background(Color.fmRed)
                    .cornerRadius(6)
                }
                .buttonStyle(.plain)

                Text("版本 \(memory.id)")
                    .font(.system(size: 12))
                    .foregroundColor(Color.fmText3)
                    .padding(.leading, 8)
            }
            .padding(.horizontal, 24)
            .padding(.vertical, 16)
            .background(Color.fmBg)
        }
        .frame(width: 900, height: 700)
    }

    private func agentTypeIcon(_ type: String) -> String {
        switch type {
        case "对话助手": return "message.fill"
        case "数据分析": return "chart.bar.xaxis"
        case "文本处理": return "doc.text.fill"
        case "可视化生成": return "chart.pie.fill"
        case "报告撰写": return "doc.richtext.fill"
        default: return "brain.head.profile"
        }
    }

    private func agentTypeColor(_ type: String) -> Color {
        switch type {
        case "对话助手": return Color.fmBlue
        case "数据分析": return Color.fmPurple
        case "文本处理": return Color.fmGreen
        case "可视化生成": return Color.fmOrange
        case "报告撰写": return Color(red: 0.8, green: 0.4, blue: 0.6)
        default: return Color.fmText3
        }
    }

    private func importanceIcon(_ importance: String) -> String {
        switch importance {
        case "高": return "exclamationmark.triangle.fill"
        case "中": return "info.circle.fill"
        case "低": return "minus.circle.fill"
        default: return "circle.fill"
        }
    }

    private func importanceIcon(_ importance: Double) -> String {
        importanceIcon(importance >= 0.8 ? "高" : (importance >= 0.5 ? "中" : "低"))
    }

    private func importanceColor(_ importance: String) -> Color {
        switch importance {
        case "高": return .fmError
        case "中": return Color.fmOrange
        case "低": return Color.fmText3
        default: return Color.fmText3
        }
    }

    private func importanceColor(_ importance: Double) -> Color {
        importanceColor(importance >= 0.8 ? "高" : (importance >= 0.5 ? "中" : "低"))
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

// MARK: - Memory Section

struct MemorySection<Content: View>: View {
    let icon: String
    let title: String
    let content: Content

    init(icon: String, title: String, @ViewBuilder content: () -> Content) {
        self.icon = icon
        self.title = title
        self.content = content()
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(spacing: 8) {
                Image(systemName: icon)
                    .font(.system(size: 14))
                    .foregroundColor(Color.fmBlue)
                Text(title)
                    .font(.system(size: 15, weight: .semibold))
                    .foregroundColor(Color.fmText)
            }

            content
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}

// MARK: - Memory Timeline View

struct MemoryTimelineView: View {
    let memories: [AgentMemory]

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            ForEach(Array(memories.enumerated()), id: \.element.id) { index, memory in
                HStack(alignment: .top, spacing: 16) {
                    // Timeline indicator
                    VStack(spacing: 0) {
                        Circle()
                            .fill(agentTypeColor(memory.agentType))
                            .frame(width: 12, height: 12)

                        if index < memories.count - 1 {
                            Rectangle()
                                .fill(Color.fmBorder)
                                .frame(width: 2)
                                .frame(minHeight: 80)
                        }
                    }
                    .frame(width: 12)

                    VStack(alignment: .leading, spacing: 8) {
                        // Time label
                        Text(formatTimelineTimestamp(memory.timestamp))
                            .font(.system(size: 12, weight: .medium))
                            .foregroundColor(Color.fmText3)

                        // Memory card
                        MemoryCard(memory: memory)
                    }
                    .padding(.bottom, 20)
                }
            }
        }
    }

    private func agentTypeColor(_ type: String) -> Color {
        switch type {
        case "对话助手": return Color.fmBlue
        case "数据分析": return Color.fmPurple
        case "文本处理": return Color.fmGreen
        case "可视化生成": return Color.fmOrange
        case "报告撰写": return Color(red: 0.8, green: 0.4, blue: 0.6)
        default: return Color.fmText3
        }
    }

    private func formatTimelineTimestamp(_ timestamp: String) -> String {
        let formatter = ISO8601DateFormatter()
        if let date = formatter.date(from: timestamp) {
            let displayFormatter = DateFormatter()
            displayFormatter.dateFormat = "yyyy-MM-dd HH:mm"
            return displayFormatter.string(from: date)
        }
        return timestamp
    }
}

// MARK: - Memory Graph Placeholder

struct MemoryGraphPlaceholder: View {
    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: "circle.hexagongrid.fill")
                .font(.system(size: 64))
                .foregroundColor(Color.fmText3)

            Text("记忆关系图谱")
                .font(.system(size: 18, weight: .semibold))
                .foregroundColor(Color.fmText)

            Text("此功能正在开发中，将展示记忆之间的关联网络")
                .font(.system(size: 14))
                .foregroundColor(Color.fmText2)
                .multilineTextAlignment(.center)

            Button(action: {}) {
                Text("敬请期待")
                    .font(.system(size: 13))
                    .foregroundColor(.white)
                    .frame(height: 32)
                    .padding(.horizontal, 24)
                    .background(Color.fmBlue)
                    .cornerRadius(6)
            }
            .buttonStyle(.plain)
            .disabled(true)
            .opacity(0.6)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color.fmBg2.opacity(0.3))
        .cornerRadius(12)
    }
}
