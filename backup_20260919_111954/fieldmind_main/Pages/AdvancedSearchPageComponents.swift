import SwiftUI

// MARK: - FilterSection
struct FilterSection<Content: View>: View {
    let title: String
    let icon: String
    let content: Content

    init(title: String, icon: String, @ViewBuilder content: () -> Content) {
        self.title = title
        self.icon = icon
        self.content = content()
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(spacing: 6) {
                Image(systemName: icon)
                    .font(.system(size: 12))
                    .foregroundColor(.fmText2)
                Text(title)
                    .font(.system(size: 12, weight: .medium))
                    .foregroundColor(.fmText)
            }

            content
        }
    }
}

// MARK: - SearchFilterChip
struct SearchFilterChip: View {
    let label: String
    let isSelected: Bool
    let onToggle: () -> Void

    var body: some View {
        Button(action: onToggle) {
            Text(label)
                .font(.system(size: 11))
                .foregroundColor(isSelected ? .white : .fmText2)
                .padding(.horizontal, 10)
                .padding(.vertical, 5)
                .background(isSelected ? Color.fmBlue : Color.fmBg)
                .cornerRadius(12)
                .overlay(
                    RoundedRectangle(cornerRadius: 12)
                        .stroke(isSelected ? Color.clear : Color.fmBorder, lineWidth: 1)
                )
        }
        .buttonStyle(PlainButtonStyle())
    }
}

// MARK: - FilterCheckbox
struct FilterCheckbox: View {
    let label: String
    let isSelected: Bool
    let onToggle: () -> Void

    var body: some View {
        Button(action: onToggle) {
            HStack(spacing: 8) {
                Image(systemName: isSelected ? "checkmark.square.fill" : "square")
                    .font(.system(size: 14))
                    .foregroundColor(isSelected ? .fmBlue : .fmText3)

                Text(label)
                    .font(.system(size: 12))
                    .foregroundColor(.fmText)
                    .lineLimit(1)

                Spacer()
            }
        }
        .buttonStyle(PlainButtonStyle())
    }
}

// MARK: - SearchResultCard
struct SearchResultCard: View {
    let result: SearchResult
    let searchQuery: String
    let onTap: () -> Void

    @State private var isHovered = false

    var body: some View {
        Button(action: onTap) {
            VStack(alignment: .leading, spacing: 12) {
                // Header: type icon, title, score
                HStack(alignment: .top, spacing: 12) {
                    // Type icon
                    typeIconView
                        .frame(width: 40, height: 40)

                    VStack(alignment: .leading, spacing: 6) {
                        // Title
                        Text(result.title)
                            .font(.system(size: 15, weight: .medium))
                            .foregroundColor(.fmText)
                            .lineLimit(2)

                        // Badges: type, project, source
                        HStack(spacing: 6) {
                            // Type badge
                            Text(result.type)
                                .font(.system(size: 10))
                                .foregroundColor(.white)
                                .padding(.horizontal, 6)
                                .padding(.vertical, 3)
                                .background(typeColor)
                                .cornerRadius(4)

                            // Project badge
                            if let projectName = result.projectName {
                                HStack(spacing: 3) {
                                    Image(systemName: "folder.fill")
                                        .font(.system(size: 8))
                                    Text(projectName)
                                        .font(.system(size: 10))
                                }
                                .foregroundColor(.fmText2)
                                .padding(.horizontal, 6)
                                .padding(.vertical, 3)
                                .background(Color.fmBg2)
                                .cornerRadius(4)
                            }

                            // Source badge
                            HStack(spacing: 3) {
                                Image(systemName: "arrow.right.circle.fill")
                                    .font(.system(size: 8))
                                Text(result.source)
                                    .font(.system(size: 10))
                            }
                            .foregroundColor(.fmText3)
                            .padding(.horizontal, 6)
                            .padding(.vertical, 3)
                            .background(Color.fmBg)
                            .cornerRadius(4)
                        }
                    }

                    Spacer()

                    // Score
                    VStack(spacing: 2) {
                        Text(String(format: "%.1f", result.score))
                            .font(.system(size: 16, weight: .bold))
                            .foregroundColor(scoreColor)
                        Text("相关性")
                            .font(.system(size: 9))
                            .foregroundColor(.fmText3)
                    }
                    .padding(.horizontal, 10)
                    .padding(.vertical, 6)
                    .background(scoreColor.opacity(0.1))
                    .cornerRadius(8)
                }

                // Snippet with highlights
                if !result.snippet.isEmpty {
                    highlightedSnippet
                        .font(.system(size: 13))
                        .foregroundColor(.fmText2)
                        .lineSpacing(4)
                        .lineLimit(3)
                }

                // Tags
                if !result.tags.isEmpty {
                    FlowLayout(spacing: 6) {
                        ForEach(result.tags, id: \.self) { tag in
                            HStack(spacing: 3) {
                                Image(systemName: "tag.fill")
                                    .font(.system(size: 8))
                                Text(tag)
                                    .font(.system(size: 10))
                            }
                            .foregroundColor(.fmText3)
                            .padding(.horizontal, 6)
                            .padding(.vertical, 3)
                            .background(Color.fmBg2)
                            .cornerRadius(4)
                        }
                    }
                }

                Divider()

                // Footer: timestamp, file info
                HStack(spacing: 16) {
                    HStack(spacing: 4) {
                        Image(systemName: "clock")
                            .font(.system(size: 11))
                        Text(formatTimestamp(result.timestamp))
                            .font(.system(size: 11))
                    }
                    .foregroundColor(.fmText3)

                    if let fileType = result.fileType {
                        HStack(spacing: 4) {
                            Image(systemName: "doc.fill")
                                .font(.system(size: 11))
                            Text(fileType.uppercased())
                                .font(.system(size: 11))
                        }
                        .foregroundColor(.fmText3)
                    }

                    if let fileSize = result.metadata["fileSize"] {
                        HStack(spacing: 4) {
                            Image(systemName: "externaldrive")
                                .font(.system(size: 11))
                            Text(fileSize)
                                .font(.system(size: 11))
                        }
                        .foregroundColor(.fmText3)
                    }

                    Spacer()

                    // Highlights count
                    if !result.highlights.isEmpty {
                        HStack(spacing: 4) {
                            Image(systemName: "highlighter")
                                .font(.system(size: 11))
                            Text("\(result.highlights.count) 个匹配")
                                .font(.system(size: 11))
                        }
                        .foregroundColor(.fmBlue)
                    }
                }
            }
            .padding(16)
            .background(isHovered ? Color.fmBg2 : Color.white)
            .cornerRadius(8)
            .overlay(
                RoundedRectangle(cornerRadius: 8)
                    .stroke(isHovered ? Color.fmBlue : Color.fmBorder, lineWidth: isHovered ? 2 : 1)
            )
            .shadow(color: isHovered ? Color.black.opacity(0.1) : Color.clear, radius: 8, x: 0, y: 4)
            .scaleEffect(isHovered ? 1.005 : 1.0)
            .animation(.easeInOut(duration: 0.2), value: isHovered)
        }
        .buttonStyle(PlainButtonStyle())
        .onHover { hovering in
            isHovered = hovering
        }
    }

    private var typeIconView: some View {
        ZStack {
            Circle()
                .fill(typeColor.opacity(0.15))

            Image(systemName: typeIcon)
                .font(.system(size: 18))
                .foregroundColor(typeColor)
        }
    }

    private var typeIcon: String {
        switch result.type {
        case "文件": return "doc.text.fill"
        case "对话": return "message.fill"
        case "引用": return "quote.bubble.fill"
        case "照片": return "photo.fill"
        case "表格": return "tablecells.fill"
        case "SOP": return "list.bullet.clipboard.fill"
        case "报告": return "doc.richtext.fill"
        default: return "doc.fill"
        }
    }

    private var typeColor: Color {
        switch result.type {
        case "文件": return .fmBlue
        case "对话": return .fmGreen
        case "引用": return .fmPurple
        case "照片": return .fmOrange
        case "表格": return .fmDocTable
        case "SOP": return .fmDocSOP
        case "报告": return .fmDocReport
        default: return .fmText2
        }
    }

    private var scoreColor: Color {
        if result.score >= 90 {
            return .fmSuccess
        } else if result.score >= 75 {
            return .fmBlue
        } else if result.score >= 60 {
            return .fmOrange
        } else {
            return .fmText3
        }
    }

    private var highlightedSnippet: Text {
        var text = Text("")
        let snippetText = result.snippet

        // Simple highlight: bold the keywords
        var remainingText = snippetText
        for highlight in result.highlights {
            if let range = remainingText.range(of: highlight) {
                let beforeHighlight = String(remainingText[..<range.lowerBound])
                text = text + Text(beforeHighlight)
                text = text + Text(highlight).bold().foregroundColor(.fmBlue)
                remainingText = String(remainingText[range.upperBound...])
            }
        }
        text = text + Text(remainingText)

        return text
    }

    private func formatTimestamp(_ timestamp: String) -> String {
        let formatter = ISO8601DateFormatter()
        guard let date = formatter.date(from: timestamp) else { return timestamp }

        let displayFormatter = DateFormatter()
        displayFormatter.dateFormat = "yyyy-MM-dd HH:mm"
        return displayFormatter.string(from: date)
    }

    private func formatTimestamp(_ timestamp: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd HH:mm"
        return formatter.string(from: timestamp)
    }
}

// MARK: - SavedSearchCard
struct SavedSearchCard: View {
    let savedSearch: SavedSearch
    let onUse: () -> Void

    @State private var isHovered = false

    var body: some View {
        Button(action: onUse) {
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    if savedSearch.isPinned {
                        Image(systemName: "pin.fill")
                            .font(.system(size: 10))
                            .foregroundColor(.fmOrange)
                    }

                    Text(savedSearch.name)
                        .font(.system(size: 13, weight: .medium))
                        .foregroundColor(.fmText)
                        .lineLimit(1)

                    Spacer()

                    Image(systemName: "arrow.right")
                        .font(.system(size: 10))
                        .foregroundColor(.fmText3)
                }

                if !savedSearch.description.isEmpty {
                    Text(savedSearch.description)
                        .font(.system(size: 11))
                        .foregroundColor(.fmText2)
                        .lineLimit(2)
                }

                HStack(spacing: 8) {
                    if !savedSearch.query.isEmpty {
                        HStack(spacing: 3) {
                            Image(systemName: "magnifyingglass")
                                .font(.system(size: 9))
                            Text(savedSearch.query)
                                .font(.system(size: 10))
                                .lineLimit(1)
                        }
                        .foregroundColor(.fmText3)
                    }

                    if savedSearch.lastUsed != nil {
                        HStack(spacing: 3) {
                            Image(systemName: "clock")
                                .font(.system(size: 9))
                            Text("使用 \(savedSearch.useCount) 次")
                                .font(.system(size: 10))
                        }
                        .foregroundColor(.fmText3)
                    }
                }
            }
            .padding(12)
            .background(isHovered ? Color.fmBg : Color.white)
            .cornerRadius(6)
            .overlay(
                RoundedRectangle(cornerRadius: 6)
                    .stroke(isHovered ? Color.fmBlue : Color.fmBorder, lineWidth: 1)
            )
        }
        .buttonStyle(PlainButtonStyle())
        .onHover { hovering in
            isHovered = hovering
        }
    }
}

// MARK: - SearchHistoryCard
struct SearchHistoryCard: View {
    let history: SearchHistory
    let onUse: () -> Void

    @State private var isHovered = false

    var body: some View {
        Button(action: onUse) {
            VStack(alignment: .leading, spacing: 6) {
                HStack {
                    Text(history.query)
                        .font(.system(size: 13, weight: .medium))
                        .foregroundColor(.fmText)
                        .lineLimit(1)

                    Spacer()

                    Image(systemName: "arrow.right")
                        .font(.system(size: 10))
                        .foregroundColor(.fmText3)
                }

                HStack(spacing: 8) {
                    HStack(spacing: 3) {
                        Image(systemName: "clock")
                            .font(.system(size: 9))
                        Text(formatTimestamp(history.timestamp))
                            .font(.system(size: 10))
                    }
                    .foregroundColor(.fmText3)

                    HStack(spacing: 3) {
                        Image(systemName: "doc.text")
                            .font(.system(size: 9))
                        Text("\(history.resultCount) 个结果")
                            .font(.system(size: 10))
                    }
                    .foregroundColor(.fmText3)
                }
            }
            .padding(10)
            .background(isHovered ? Color.fmBg : Color.white)
            .cornerRadius(6)
            .overlay(
                RoundedRectangle(cornerRadius: 6)
                    .stroke(isHovered ? Color.fmBlue : Color.fmBorder, lineWidth: 1)
            )
        }
        .buttonStyle(PlainButtonStyle())
        .onHover { hovering in
            isHovered = hovering
        }
    }

    private func formatTimestamp(_ timestamp: String) -> String {
        let formatter = ISO8601DateFormatter()
        guard let date = formatter.date(from: timestamp) else { return timestamp }

        let displayFormatter = DateFormatter()
        displayFormatter.dateFormat = "MM-dd HH:mm"
        return displayFormatter.string(from: date)
    }
}

// MARK: - SearchResultDetailSheet
struct SearchResultDetailSheet: View {
    let result: SearchResult
    @Environment(\.presentationMode) var presentationMode

    var body: some View {
        VStack(spacing: 0) {
            // Header
            HStack(spacing: 16) {
                // Type icon
                ZStack {
                    Circle()
                        .fill(typeColor.opacity(0.15))
                        .frame(width: 64, height: 64)

                    Image(systemName: typeIcon)
                        .font(.system(size: 28))
                        .foregroundColor(typeColor)
                }

                VStack(alignment: .leading, spacing: 6) {
                    Text(result.title)
                        .font(.system(size: 20, weight: .semibold))
                        .foregroundColor(.fmText)

                    HStack(spacing: 8) {
                        Text(result.type)
                            .font(.system(size: 11))
                            .foregroundColor(.white)
                            .padding(.horizontal, 8)
                            .padding(.vertical, 4)
                            .background(typeColor)
                            .cornerRadius(4)

                        if let projectName = result.projectName {
                            HStack(spacing: 3) {
                                Image(systemName: "folder.fill")
                                    .font(.system(size: 9))
                                Text(projectName)
                                    .font(.system(size: 11))
                            }
                            .foregroundColor(.fmText2)
                            .padding(.horizontal, 8)
                            .padding(.vertical, 4)
                            .background(Color.fmBg2)
                            .cornerRadius(4)
                        }

                        // Score badge
                        HStack(spacing: 4) {
                            Image(systemName: "star.fill")
                                .font(.system(size: 9))
                            Text(String(format: "%.1f", result.score))
                                .font(.system(size: 11, weight: .semibold))
                        }
                        .foregroundColor(scoreColor)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(scoreColor.opacity(0.1))
                        .cornerRadius(4)
                    }
                }

                Spacer()

                Button(action: { presentationMode.wrappedValue.dismiss() }) {
                    Image(systemName: "xmark.circle.fill")
                        .font(.system(size: 24))
                        .foregroundColor(.fmText3)
                }
                .buttonStyle(PlainButtonStyle())
            }
            .padding(24)
            .background(Color.fmBg2)

            Divider()

            // Content
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    // Snippet section
                    DetailSection(title: "搜索匹配", icon: "magnifyingglass") {
                        Text(result.snippet)
                            .font(.system(size: 13))
                            .foregroundColor(.fmText)
                            .lineSpacing(6)
                    }

                    Divider()

                    // Full content section
                    if !result.content.isEmpty {
                        DetailSection(title: "完整内容", icon: "doc.text") {
                            Text(result.content)
                                .font(.system(size: 13))
                                .foregroundColor(.fmText2)
                                .lineSpacing(6)
                        }

                        Divider()
                    }

                    // Tags section
                    if !result.tags.isEmpty {
                        DetailSection(title: "标签", icon: "tag") {
                            FlowLayout(spacing: 8) {
                                ForEach(result.tags, id: \.self) { tag in
                                    Text(tag)
                                        .font(.system(size: 11))
                                        .foregroundColor(.fmText2)
                                        .padding(.horizontal, 10)
                                        .padding(.vertical, 5)
                                        .background(Color.fmBg2)
                                        .cornerRadius(12)
                                }
                            }
                        }

                        Divider()
                    }

                    // Highlights section
                    if !result.highlights.isEmpty {
                        DetailSection(title: "匹配关键词", icon: "highlighter") {
                            FlowLayout(spacing: 8) {
                                ForEach(result.highlights, id: \.self) { highlight in
                                    Text(highlight)
                                        .font(.system(size: 12, weight: .medium))
                                        .foregroundColor(.fmBlue)
                                        .padding(.horizontal, 10)
                                        .padding(.vertical, 5)
                                        .background(Color.fmBlue.opacity(0.1))
                                        .cornerRadius(12)
                                }
                            }
                        }

                        Divider()
                    }

                    // Technical info section
                    DetailSection(title: "技术信息", icon: "info.circle") {
                        VStack(spacing: 8) {
                            InfoRow(label: "来源", value: result.source)
                            InfoRow(label: "时间", value: formatFullTimestamp(result.timestamp))

                            if let fileType = result.fileType {
                                InfoRow(label: "文件类型", value: fileType.uppercased())
                            }

                            InfoRow(label: "相关性得分", value: String(format: "%.2f", result.score))

                            // Metadata
                            ForEach(result.metadata.sorted(by: { $0.key < $1.key }), id: \.key) { key, value in
                                InfoRow(label: key, value: value)
                            }
                        }
                    }
                }
                .padding(24)
            }

            Divider()

            // Footer
            HStack {
                Text("FieldMind 高级搜索 v1.0")
                    .font(.system(size: 11))
                    .foregroundColor(.fmText3)

                Spacer()

                Button(action: { /* Open in source */ }) {
                    HStack(spacing: 6) {
                        Image(systemName: "arrow.up.forward.square")
                        Text("在\(result.source)中打开")
                            .font(.system(size: 13))
                    }
                    .foregroundColor(.fmBlue)
                    .padding(.horizontal, 12)
                    .padding(.vertical, 6)
                    .background(Color.fmBlue.opacity(0.1))
                    .cornerRadius(6)
                }
                .buttonStyle(PlainButtonStyle())
            }
            .padding(.horizontal, 24)
            .padding(.vertical, 12)
            .background(Color.fmBg2)
        }
        .frame(width: 900, height: 700)
        .background(Color.fmBg)
    }

    private var typeIcon: String {
        switch result.type {
        case "文件": return "doc.text.fill"
        case "对话": return "message.fill"
        case "引用": return "quote.bubble.fill"
        case "照片": return "photo.fill"
        case "表格": return "tablecells.fill"
        case "SOP": return "list.bullet.clipboard.fill"
        case "报告": return "doc.richtext.fill"
        default: return "doc.fill"
        }
    }

    private var typeColor: Color {
        switch result.type {
        case "文件": return .fmBlue
        case "对话": return .fmGreen
        case "引用": return .fmPurple
        case "照片": return .fmOrange
        case "表格": return .fmDocTable
        case "SOP": return .fmDocSOP
        case "报告": return .fmDocReport
        default: return .fmText2
        }
    }

    private var scoreColor: Color {
        if result.score >= 90 {
            return .fmSuccess
        } else if result.score >= 75 {
            return .fmBlue
        } else if result.score >= 60 {
            return .fmOrange
        } else {
            return .fmText3
        }
    }

    private func formatFullTimestamp(_ timestamp: String) -> String {
        let formatter = ISO8601DateFormatter()
        guard let date = formatter.date(from: timestamp) else { return timestamp }

        let displayFormatter = DateFormatter()
        displayFormatter.dateFormat = "yyyy-MM-dd HH:mm:ss"
        return displayFormatter.string(from: date)
    }

    private func formatFullTimestamp(_ timestamp: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd HH:mm:ss"
        return formatter.string(from: timestamp)
    }
}

// DetailSection - moved to QualityMonitorPageComponents.swift (shared component)

// MARK: - SaveSearchSheet
struct SaveSearchSheet: View {
    @Binding var searchName: String
    @Binding var searchDescription: String
    let onSave: () -> Void
    @Environment(\.presentationMode) var presentationMode

    var body: some View {
        VStack(spacing: 20) {
            Text("保存搜索")
                .font(.system(size: 18, weight: .semibold))
                .foregroundColor(.fmText)

            VStack(alignment: .leading, spacing: 8) {
                Text("搜索名称")
                    .font(.system(size: 13, weight: .medium))
                    .foregroundColor(.fmText)

                TextField("为这个搜索起个名字...", text: $searchName)
                    .textFieldStyle(PlainTextFieldStyle())
                    .font(.system(size: 14))
                    .padding(10)
                    .background(Color.fmBg2)
                    .cornerRadius(6)
                    .overlay(
                        RoundedRectangle(cornerRadius: 6)
                            .stroke(Color.fmBorder, lineWidth: 1)
                    )
            }

            VStack(alignment: .leading, spacing: 8) {
                Text("描述（可选）")
                    .font(.system(size: 13, weight: .medium))
                    .foregroundColor(.fmText)

                TextField("描述这个搜索的用途...", text: $searchDescription)
                    .textFieldStyle(PlainTextFieldStyle())
                    .font(.system(size: 14))
                    .padding(10)
                    .background(Color.fmBg2)
                    .cornerRadius(6)
                    .overlay(
                        RoundedRectangle(cornerRadius: 6)
                            .stroke(Color.fmBorder, lineWidth: 1)
                    )
            }

            HStack(spacing: 12) {
                Button("取消") {
                    presentationMode.wrappedValue.dismiss()
                }
                .foregroundColor(.fmText2)
                .padding(.horizontal, 20)
                .padding(.vertical, 8)
                .background(Color.fmBg2)
                .cornerRadius(6)

                Button("保存") {
                    onSave()
                    presentationMode.wrappedValue.dismiss()
                }
                .foregroundColor(.white)
                .padding(.horizontal, 20)
                .padding(.vertical, 8)
                .background(searchName.isEmpty ? Color.fmText3 : Color.fmBlue)
                .cornerRadius(6)
                .disabled(searchName.isEmpty)
            }
        }
        .padding(24)
        .frame(width: 400)
        .background(Color.fmBg)
    }
}
