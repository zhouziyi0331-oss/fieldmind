import SwiftUI

// MARK: - Report List Row
struct ReportListRow: View {
    let report: Report
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(alignment: .top, spacing: 16) {
                // Status indicator
                Circle()
                    .fill(statusColor(report.status))
                    .frame(width: 8, height: 8)
                    .padding(.top, 6)

                VStack(alignment: .leading, spacing: 8) {
                    // Title and type
                    HStack(alignment: .top, spacing: 8) {
                        Text(report.title)
                            .font(.system(size: 15, weight: .medium))
                            .foregroundColor(Color.fmText)
                            .lineLimit(2)

                        Spacer()

                        Text(report.type.rawValue)
                            .font(.system(size: 12))
                            .foregroundColor(Color.fmText2)
                            .padding(.horizontal, 8)
                            .padding(.vertical, 3)
                            .background(Color.fmBg)
                            .cornerRadius(4)
                    }

                    // Summary
                    Text(report.summary)
                        .font(.system(size: 13))
                        .foregroundColor(Color.fmText2)
                        .lineLimit(2)

                    // Tags
                    FlowLayout(spacing: 6) {
                        ForEach(report.tags, id: \.self) { tag in
                            Text(tag)
                                .font(.system(size: 11))
                                .foregroundColor(Color.fmText3)
                                .padding(.horizontal, 6)
                                .padding(.vertical, 2)
                                .background(Color.fmBg)
                                .cornerRadius(3)
                        }
                    }

                    // Meta info
                    HStack(spacing: 16) {
                        HStack(spacing: 4) {
                            Image(systemName: "person.circle")
                                .font(.system(size: 12))
                            Text(report.author)
                                .font(.system(size: 12))
                        }
                        .foregroundColor(Color.fmText3)

                        HStack(spacing: 4) {
                            Image(systemName: "calendar")
                                .font(.system(size: 12))
                            Text(report.date)
                                .font(.system(size: 12))
                        }
                        .foregroundColor(Color.fmText3)

                        HStack(spacing: 4) {
                            Image(systemName: "doc.text")
                                .font(.system(size: 12))
                            Text("\(report.stats.wordCount)字")
                                .font(.system(size: 12))
                        }
                        .foregroundColor(Color.fmText3)

                        HStack(spacing: 4) {
                            Image(systemName: "eye")
                                .font(.system(size: 12))
                            Text("\(report.stats.viewCount)")
                                .font(.system(size: 12))
                        }
                        .foregroundColor(Color.fmText3)

                        HStack(spacing: 4) {
                            Image(systemName: "square.and.arrow.down")
                                .font(.system(size: 12))
                            Text("\(report.stats.exportCount)")
                                .font(.system(size: 12))
                        }
                        .foregroundColor(Color.fmText3)

                        Spacer()

                        Text(report.status)
                            .font(.system(size: 12, weight: .medium))
                            .foregroundColor(statusColor(report.status))
                    }
                }
            }
            .padding(.horizontal, 20)
            .padding(.vertical, 16)
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

// MARK: - Report Grid Card
struct ReportGridCard: View {
    let report: Report
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            VStack(alignment: .leading, spacing: 12) {
                // Header with status
                HStack {
                    Text(report.type.rawValue)
                        .font(.system(size: 11))
                        .foregroundColor(Color.fmText3)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(Color.fmBg)
                        .cornerRadius(3)

                    Spacer()

                    Circle()
                        .fill(statusColor(report.status))
                        .frame(width: 6, height: 6)
                }

                // Title
                Text(report.title)
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(Color.fmText)
                    .lineLimit(2)
                    .frame(height: 40, alignment: .top)

                // Summary
                Text(report.summary)
                    .font(.system(size: 12))
                    .foregroundColor(Color.fmText2)
                    .lineLimit(3)
                    .frame(height: 51, alignment: .top)

                // Tags
                FlowLayout(spacing: 4) {
                    ForEach(report.tags.prefix(3), id: \.self) { tag in
                        Text(tag)
                            .font(.system(size: 10))
                            .foregroundColor(Color.fmText3)
                            .padding(.horizontal, 5)
                            .padding(.vertical, 2)
                            .background(Color.fmBg)
                            .cornerRadius(3)
                    }
                }
                .frame(height: 20, alignment: .top)

                Divider()

                // Footer stats
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

                    Text(report.date)
                        .font(.system(size: 11))
                }
                .foregroundColor(Color.fmText3)
            }
            .padding(14)
            .background(Color.white)
            .cornerRadius(8)
            .overlay(
                RoundedRectangle(cornerRadius: 8)
                    .stroke(Color.fmBorder, lineWidth: 1)
            )
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

// MARK: - Report Detail Sheet
struct ReportDetailSheet: View {
    let report: Report
    @Environment(\.dismiss) var dismiss

    var body: some View {
        VStack(spacing: 0) {
            // Header
            HStack {
                VStack(alignment: .leading, spacing: 8) {
                    Text(report.title)
                        .font(.system(size: 18, weight: .semibold))
                        .foregroundColor(Color.fmText)

                    HStack(spacing: 16) {
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

                        Circle()
                            .fill(statusColor(report.status))
                            .frame(width: 6, height: 6)
                        Text(report.status)
                            .font(.system(size: 13, weight: .medium))
                            .foregroundColor(statusColor(report.status))
                    }
                    .foregroundColor(Color.fmText2)
                }

                Spacer()

                // Action buttons
                HStack(spacing: 8) {
                    Button(action: {}) {
                        HStack(spacing: 4) {
                            Image(systemName: "square.and.arrow.up")
                            Text("导出")
                        }
                        .font(.system(size: 13))
                        .foregroundColor(Color.fmText2)
                        .padding(.horizontal, 12)
                        .padding(.vertical, 6)
                        .background(Color.fmBg)
                        .cornerRadius(6)
                    }
                    .buttonStyle(.plain)

                    Button(action: {}) {
                        HStack(spacing: 4) {
                            Image(systemName: "square.and.pencil")
                            Text("编辑")
                        }
                        .font(.system(size: 13))
                        .foregroundColor(.white)
                        .padding(.horizontal, 12)
                        .padding(.vertical, 6)
                        .background(Color.blue)
                        .cornerRadius(6)
                    }
                    .buttonStyle(.plain)

                    Button(action: { dismiss() }) {
                        Image(systemName: "xmark.circle.fill")
                            .font(.system(size: 20))
                            .foregroundColor(Color.fmText3)
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(20)
            .background(Color.white)
            .overlay(
                Rectangle()
                    .frame(height: 1)
                    .foregroundColor(Color.fmBorder),
                alignment: .bottom
            )

            ScrollView {
                VStack(alignment: .leading, spacing: 24) {
                    // Summary section
                    ReportDetailSection(title: "摘要", icon: "doc.text") {
                        Text(report.summary)
                            .font(.system(size: 14))
                            .foregroundColor(Color.fmText)
                            .lineSpacing(4)
                    }

                    // Stats section
                    ReportDetailSection(title: "统计信息", icon: "chart.bar") {
                        VStack(spacing: 12) {
                            ReportStatRow(label: "字数", value: "\(report.stats.wordCount) 字")
                            ReportStatRow(label: "浏览量", value: "\(report.stats.viewCount) 次")
                            ReportStatRow(label: "导出次数", value: "\(report.stats.exportCount) 次")
                            ReportStatRow(label: "最后修改", value: report.stats.lastModified)
                        }
                    }

                    // Tags section
                    ReportDetailSection(title: "标签", icon: "tag") {
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

                    // Sections content
                    ReportDetailSection(title: "报告内容", icon: "list.bullet.rectangle") {
                        VStack(alignment: .leading, spacing: 20) {
                            ForEach(report.sections ?? []) { section in
                                VStack(alignment: .leading, spacing: 8) {
                                    Text(section.title)
                                        .font(.system(size: 14, weight: .semibold))
                                        .foregroundColor(Color.fmText)

                                    Text(section.content)
                                        .font(.system(size: 13))
                                        .foregroundColor(Color.fmText2)
                                        .lineSpacing(4)
                                }
                            }
                        }
                    }

                    // Attachments section
                    if !(report.attachments ?? []).isEmpty {
                        ReportDetailSection(title: "附件", icon: "paperclip") {
                            VStack(spacing: 8) {
                                ForEach(report.attachments ?? []) { attachment in
                                    ReportAttachmentRow(attachment: attachment)
                                }
                            }
                        }
                    }
                }
                .padding(20)
            }
        }
        .frame(width: 900, height: 700)
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

// MARK: - Report Detail Section
struct ReportDetailSection<Content: View>: View {
    let title: String
    let icon: String
    let content: Content

    init(title: String, icon: String, @ViewBuilder content: () -> Content) {
        self.title = title
        self.icon = icon
        self.content = content()
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(spacing: 6) {
                Image(systemName: icon)
                    .font(.system(size: 14))
                Text(title)
                    .font(.system(size: 14, weight: .semibold))
            }
            .foregroundColor(Color.fmText)

            content
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color.fmBg.opacity(0.5))
        .cornerRadius(8)
    }
}

// MARK: - Report Stat Row
struct ReportStatRow: View {
    let label: String
    let value: String

    var body: some View {
        HStack {
            Text(label)
                .font(.system(size: 13))
                .foregroundColor(Color.fmText2)
            Spacer()
            Text(value)
                .font(.system(size: 13, weight: .medium))
                .foregroundColor(Color.fmText)
        }
    }
}

// MARK: - Report Attachment Row
struct ReportAttachmentRow: View {
    let attachment: Report.ReportAttachment

    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: attachmentIcon(attachment.type))
                .font(.system(size: 16))
                .foregroundColor(attachmentColor(attachment.type))
                .frame(width: 32, height: 32)
                .background(attachmentColor(attachment.type).opacity(0.1))
                .cornerRadius(6)

            VStack(alignment: .leading, spacing: 2) {
                Text(attachment.name)
                    .font(.system(size: 13))
                    .foregroundColor(Color.fmText)
                    .lineLimit(1)

                Text("\(attachment.type) • \(attachment.size)")
                    .font(.system(size: 11))
                    .foregroundColor(Color.fmText3)
            }

            Spacer()

            Button(action: {}) {
                Image(systemName: "arrow.down.circle")
                    .font(.system(size: 18))
                    .foregroundColor(Color.blue)
            }
            .buttonStyle(.plain)
        }
        .padding(10)
        .background(Color.white)
        .cornerRadius(6)
        .overlay(
            RoundedRectangle(cornerRadius: 6)
                .stroke(Color.fmBorder, lineWidth: 1)
        )
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
