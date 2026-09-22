import SwiftUI

// MARK: - Report3 List Item
struct Report3ListItem: View {
    let report: Report
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            VStack(alignment: .leading, spacing: 8) {
                // Title
                Text(report.title)
                    .font(.system(size: 13, weight: .medium))
                    .foregroundColor(Color.fmText)
                    .lineLimit(2)
                    .multilineTextAlignment(.leading)

                // Meta info
                HStack(spacing: 8) {
                    HStack(spacing: 3) {
                        Image(systemName: "person.circle")
                            .font(.system(size: 10))
                        Text(report.author)
                            .font(.system(size: 11))
                            .lineLimit(1)
                    }

                    Text("•")
                        .font(.system(size: 10))

                    Text(report.date)
                        .font(.system(size: 11))
                }
                .foregroundColor(Color.fmText3)

                // Tags
                FlowLayout(spacing: 4) {
                    ForEach(report.tags.prefix(2), id: \.self) { tag in
                        Text(tag)
                            .font(.system(size: 10))
                            .foregroundColor(Color.fmText3)
                            .padding(.horizontal, 5)
                            .padding(.vertical, 2)
                            .background(Color.fmBg)
                            .cornerRadius(3)
                    }
                }

                // Stats
                HStack(spacing: 12) {
                    HStack(spacing: 3) {
                        Image(systemName: "eye")
                            .font(.system(size: 10))
                        Text("\(report.stats.viewCount)")
                            .font(.system(size: 11))
                    }

                    HStack(spacing: 3) {
                        Image(systemName: "doc.text")
                            .font(.system(size: 10))
                        Text("\(report.stats.wordCount / 1000)k")
                            .font(.system(size: 11))
                    }

                    Spacer()

                    Circle()
                        .fill(statusColor(report.status))
                        .frame(width: 6, height: 6)
                }
                .foregroundColor(Color.fmText3)
            }
            .padding(12)
            .background(isSelected ? Color.blue.opacity(0.08) : Color.clear)
            .overlay(
                Rectangle()
                    .frame(width: 3)
                    .foregroundColor(isSelected ? Color.blue : Color.clear),
                alignment: .leading
            )
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
    }

    private func statusColor(_ status: String) -> Color {
        switch status {
        case "已发布": return Color.green
        case "审核中": return Color.orange
        case "草稿": return Color.gray
        default: return Color.gray
        }
    }
}

// MARK: - Report3 Detail View
struct Report3DetailView: View {
    let report: Report
    @State private var selectedSectionId: String?

    var body: some View {
        HStack(spacing: 0) {
            // Main content
            ScrollView {
                VStack(alignment: .leading, spacing: 0) {
                    // Header
                    VStack(alignment: .leading, spacing: 16) {
                        // Type and status
                        HStack {
                            Text(report.type.rawValue)
                                .font(.system(size: 11))
                                .foregroundColor(Color.fmText3)
                                .padding(.horizontal, 8)
                                .padding(.vertical, 3)
                                .background(Color.fmBg)
                                .cornerRadius(4)

                            Spacer()

                            HStack(spacing: 6) {
                                Circle()
                                    .fill(statusColor(report.status))
                                    .frame(width: 6, height: 6)
                                Text(report.status)
                                    .font(.system(size: 12, weight: .medium))
                                    .foregroundColor(statusColor(report.status))
                            }
                        }

                        // Title
                        Text(report.title)
                            .font(.system(size: 22, weight: .bold))
                            .foregroundColor(Color.fmText)

                        // Meta info
                        HStack(spacing: 20) {
                            HStack(spacing: 6) {
                                Image(systemName: "person.circle.fill")
                                    .font(.system(size: 14))
                                Text(report.author)
                                    .font(.system(size: 13))
                            }

                            HStack(spacing: 6) {
                                Image(systemName: "calendar")
                                    .font(.system(size: 14))
                                Text(report.date)
                                    .font(.system(size: 13))
                            }

                            HStack(spacing: 6) {
                                Image(systemName: "folder")
                                    .font(.system(size: 14))
                                Text(report.project)
                                    .font(.system(size: 13))
                            }
                        }
                        .foregroundColor(Color.fmText2)

                        // Stats bar
                        HStack(spacing: 24) {
                            HStack(spacing: 6) {
                                Image(systemName: "doc.text")
                                    .font(.system(size: 13))
                                VStack(alignment: .leading, spacing: 2) {
                                    Text("\(report.stats.wordCount)")
                                        .font(.system(size: 14, weight: .semibold))
                                    Text("字数")
                                        .font(.system(size: 11))
                                        .foregroundColor(Color.fmText3)
                                }
                            }

                            HStack(spacing: 6) {
                                Image(systemName: "eye")
                                    .font(.system(size: 13))
                                VStack(alignment: .leading, spacing: 2) {
                                    Text("\(report.stats.viewCount)")
                                        .font(.system(size: 14, weight: .semibold))
                                    Text("浏览")
                                        .font(.system(size: 11))
                                        .foregroundColor(Color.fmText3)
                                }
                            }

                            HStack(spacing: 6) {
                                Image(systemName: "square.and.arrow.down")
                                    .font(.system(size: 13))
                                VStack(alignment: .leading, spacing: 2) {
                                    Text("\(report.stats.exportCount)")
                                        .font(.system(size: 14, weight: .semibold))
                                    Text("导出")
                                        .font(.system(size: 11))
                                        .foregroundColor(Color.fmText3)
                                }
                            }

                            Spacer()

                            // Action buttons
                            HStack(spacing: 8) {
                                Button(action: {}) {
                                    HStack(spacing: 4) {
                                        Image(systemName: "square.and.arrow.up")
                                        Text("导出")
                                    }
                                    .font(.system(size: 12))
                                    .foregroundColor(Color.fmText2)
                                    .padding(.horizontal, 10)
                                    .padding(.vertical, 6)
                                    .background(Color.fmBg)
                                    .cornerRadius(5)
                                }
                                .buttonStyle(.plain)

                                Button(action: {}) {
                                    HStack(spacing: 4) {
                                        Image(systemName: "square.and.pencil")
                                        Text("编辑")
                                    }
                                    .font(.system(size: 12))
                                    .foregroundColor(.white)
                                    .padding(.horizontal, 10)
                                    .padding(.vertical, 6)
                                    .background(Color.blue)
                                    .cornerRadius(5)
                                }
                                .buttonStyle(.plain)
                            }
                        }
                        .foregroundColor(Color.fmText)
                    }
                    .padding(24)
                    .background(Color.white)

                    Divider()

                    // Tags section
                    VStack(alignment: .leading, spacing: 12) {
                        HStack(spacing: 6) {
                            Image(systemName: "tag")
                                .font(.system(size: 13))
                            Text("标签")
                                .font(.system(size: 13, weight: .semibold))
                        }
                        .foregroundColor(Color.fmText2)

                        FlowLayout(spacing: 8) {
                            ForEach(report.tags, id: \.self) { tag in
                                Text(tag)
                                    .font(.system(size: 12))
                                    .foregroundColor(Color.fmText2)
                                    .padding(.horizontal, 10)
                                    .padding(.vertical, 5)
                                    .background(Color.fmBg)
                                    .cornerRadius(4)
                            }
                        }
                    }
                    .padding(24)
                    .background(Color.white)

                    Divider()

                    // Summary section
                    VStack(alignment: .leading, spacing: 12) {
                        HStack(spacing: 6) {
                            Image(systemName: "doc.plaintext")
                                .font(.system(size: 13))
                            Text("摘要")
                                .font(.system(size: 13, weight: .semibold))
                        }
                        .foregroundColor(Color.fmText2)

                        Text(report.summary)
                            .font(.system(size: 14))
                            .foregroundColor(Color.fmText)
                            .lineSpacing(6)
                    }
                    .padding(24)
                    .background(Color.white)

                    Divider()

                    // Sections content
                    VStack(alignment: .leading, spacing: 24) {
                        HStack(spacing: 6) {
                            Image(systemName: "list.bullet.rectangle")
                                .font(.system(size: 13))
                            Text("正文")
                                .font(.system(size: 13, weight: .semibold))
                        }
                        .foregroundColor(Color.fmText2)

                        ForEach(report.sections ?? []) { section in
                            Report3SectionContent(
                                section: section,
                                isSelected: selectedSectionId == section.id
                            ) {
                                selectedSectionId = section.id
                            }
                        }
                    }
                    .padding(24)
                    .background(Color.white)

                    Divider()

                    // Attachments section
                    if !(report.attachments ?? []).isEmpty {
                        VStack(alignment: .leading, spacing: 12) {
                            HStack(spacing: 6) {
                                Image(systemName: "paperclip")
                                    .font(.system(size: 13))
                                Text("附件 (\((report.attachments ?? []).count))")
                                    .font(.system(size: 13, weight: .semibold))
                            }
                            .foregroundColor(Color.fmText2)

                            VStack(spacing: 8) {
                                ForEach(report.attachments ?? []) { attachment in
                                    Report3AttachmentCard(attachment: attachment)
                                }
                            }
                        }
                        .padding(24)
                        .background(Color.white)
                    }
                }
            }

            // Right sidebar - Table of contents
            VStack(spacing: 0) {
                HStack {
                    Text("目录")
                        .font(.system(size: 13, weight: .semibold))
                        .foregroundColor(Color.fmText)
                    Spacer()
                }
                .padding(.horizontal, 16)
                .padding(.vertical, 12)
                .background(Color.fmBg.opacity(0.5))

                ScrollView {
                    VStack(alignment: .leading, spacing: 4) {
                        ForEach(report.sections ?? []) { section in
                            Report3TocItem(
                                section: section,
                                isSelected: selectedSectionId == section.id
                            ) {
                                selectedSectionId = section.id
                            }
                        }
                    }
                    .padding(12)
                }
            }
            .frame(width: 220)
            .background(Color.white)
            .overlay(
                Rectangle()
                    .frame(width: 1)
                    .foregroundColor(Color.fmBorder),
                alignment: .leading
            )
        }
        .onAppear {
            if selectedSectionId == nil && !(report.sections ?? []).isEmpty {
                selectedSectionId = report.sections?.first?.id
            }
        }
    }

    private func statusColor(_ status: String) -> Color {
        switch status {
        case "已发布": return Color.green
        case "审核中": return Color.orange
        case "草稿": return Color.gray
        default: return Color.gray
        }
    }
}

// MARK: - Report3 Section Content
struct Report3SectionContent: View {
    let section: Report.ReportSection
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            VStack(alignment: .leading, spacing: 8) {
                Text(section.title)
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundColor(Color.fmText)

                Text(section.content)
                    .font(.system(size: 14))
                    .foregroundColor(Color.fmText2)
                    .lineSpacing(6)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(16)
            .background(isSelected ? Color.blue.opacity(0.05) : Color.fmBg.opacity(0.3))
            .cornerRadius(8)
            .overlay(
                RoundedRectangle(cornerRadius: 8)
                    .stroke(isSelected ? Color.blue.opacity(0.3) : Color.clear, lineWidth: 2)
            )
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
    }
}

// MARK: - Report3 TOC Item
struct Report3TocItem: View {
    let section: Report.ReportSection
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: 8) {
                Circle()
                    .fill(isSelected ? Color.blue : Color.fmText3)
                    .frame(width: 4, height: 4)

                Text(section.title)
                    .font(.system(size: 12))
                    .foregroundColor(isSelected ? Color.blue : Color.fmText2)
                    .lineLimit(2)
                    .multilineTextAlignment(.leading)

                Spacer()
            }
            .padding(.horizontal, 8)
            .padding(.vertical, 6)
            .background(isSelected ? Color.blue.opacity(0.08) : Color.clear)
            .cornerRadius(4)
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
    }
}

// MARK: - Report3 Attachment Card
struct Report3AttachmentCard: View {
    let attachment: Report.ReportAttachment

    var body: some View {
        HStack(spacing: 12) {
            // Icon
            ZStack {
                RoundedRectangle(cornerRadius: 8)
                    .fill(attachmentColor(attachment.type).opacity(0.1))
                    .frame(width: 48, height: 48)

                Image(systemName: attachmentIcon(attachment.type))
                    .font(.system(size: 20))
                    .foregroundColor(attachmentColor(attachment.type))
            }

            // Info
            VStack(alignment: .leading, spacing: 4) {
                Text(attachment.name)
                    .font(.system(size: 13, weight: .medium))
                    .foregroundColor(Color.fmText)
                    .lineLimit(1)

                HStack(spacing: 8) {
                    Text(attachment.type)
                        .font(.system(size: 11))
                        .foregroundColor(Color.fmText3)

                    Text("•")
                        .font(.system(size: 10))
                        .foregroundColor(Color.fmText3)

                    Text(attachment.size)
                        .font(.system(size: 11))
                        .foregroundColor(Color.fmText3)
                }
            }

            Spacer()

            // Download button
            Button(action: {}) {
                Image(systemName: "arrow.down.circle.fill")
                    .font(.system(size: 24))
                    .foregroundColor(Color.blue)
            }
            .buttonStyle(.plain)
        }
        .padding(12)
        .background(Color.fmBg.opacity(0.5))
        .cornerRadius(8)
    }

    private func attachmentIcon(_ type: String) -> String {
        switch type {
        case "图片": return "photo"
        case "文档": return "doc.text"
        case "音频": return "waveform"
        case "视频": return "video"
        default: return "doc"
        }
    }

    private func attachmentColor(_ type: String) -> Color {
        switch type {
        case "图片": return Color.purple
        case "文档": return Color.blue
        case "音频": return Color.orange
        case "视频": return Color.green
        default: return Color.gray
        }
    }
}
