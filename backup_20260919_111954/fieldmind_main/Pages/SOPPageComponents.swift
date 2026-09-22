import SwiftUI

// MARK: - List Row
struct SOPListRow: View {
    let sop: SOPService.SOP

    var body: some View {
        HStack(alignment: .top, spacing: 16) {
            // Icon
            ZStack {
                RoundedRectangle(cornerRadius: 8)
                    .fill(Color.blue.opacity(0.1))
                    .frame(width: 48, height: 48)

                Image(systemName: "doc.text")
                    .font(.system(size: 20))
                    .foregroundColor(.blue)
            }

            // Content
            VStack(alignment: .leading, spacing: 8) {
                // Title and version
                HStack(alignment: .top, spacing: 12) {
                    Text(sop.title)
                        .font(.system(size: 15, weight: .medium))
                        .foregroundColor(Color.fmText)

                    Text(sop.version)
                        .font(.system(size: 12))
                        .foregroundColor(Color.fmText3)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(Color.fmBg)
                        .cornerRadius(4)

                    Spacer()

                    // Status badge
                    Text(sop.status)
                        .font(.system(size: 12))
                        .foregroundColor(statusColor(sop.status))
                        .padding(.horizontal, 8)
                        .padding(.vertical, 3)
                        .background(statusColor(sop.status).opacity(0.1))
                        .cornerRadius(4)
                }

                // Description
                Text(sop.description)
                    .font(.system(size: 13))
                    .foregroundColor(Color.fmText2)
                    .lineLimit(2)

                // Tags
                FlowLayout(spacing: 8) {
                    ForEach(sop.tags, id: \.self) { tag in
                        Text(tag)
                            .font(.system(size: 12))
                            .foregroundColor(Color.fmText3)
                            .padding(.horizontal, 8)
                            .padding(.vertical, 3)
                            .background(Color.fmBg)
                            .cornerRadius(4)
                    }
                }

                // Meta info
                HStack(spacing: 16) {
                    Label {
                        Text(sop.author)
                            .font(.system(size: 12))
                            .foregroundColor(Color.fmText3)
                    } icon: {
                        Image(systemName: "person")
                            .font(.system(size: 11))
                            .foregroundColor(Color.fmText3)
                    }

                    Label {
                        Text("\(sop.steps.count) 个步骤")
                            .font(.system(size: 12))
                            .foregroundColor(Color.fmText3)
                    } icon: {
                        Image(systemName: "list.number")
                            .font(.system(size: 11))
                            .foregroundColor(Color.fmText3)
                    }

                    Label {
                        Text("使用 \(sop.usedCount) 次")
                            .font(.system(size: 12))
                            .foregroundColor(Color.fmText3)
                    } icon: {
                        Image(systemName: "arrow.clockwise")
                            .font(.system(size: 11))
                            .foregroundColor(Color.fmText3)
                    }

                    Label {
                        Text("成功率 \(Int(sop.successRate * 100))%")
                            .font(.system(size: 12))
                            .foregroundColor(Color.fmText3)
                    } icon: {
                        Image(systemName: "checkmark.circle")
                            .font(.system(size: 11))
                            .foregroundColor(Color.fmText3)
                    }

                    Spacer()

                    Text("更新于 \(sop.lastModified)")
                        .font(.system(size: 12))
                        .foregroundColor(Color.fmText3)
                }
            }
        }
        .padding(20)
    }

    private func statusColor(_ status: String) -> Color {
        switch status {
        case "草稿": return .gray
        case "审核中": return .orange
        case "已发布": return .green
        case "已归档": return .purple
        default: return .gray
        }
    }
}

// MARK: - Grid Card
struct SOPGridCard: View {
    let sop: SOPService.SOP

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Header
            HStack {
                ZStack {
                    RoundedRectangle(cornerRadius: 6)
                        .fill(Color.blue.opacity(0.1))
                        .frame(width: 40, height: 40)

                    Image(systemName: "doc.text")
                        .font(.system(size: 18))
                        .foregroundColor(.blue)
                }

                Spacer()

                Text(sop.status)
                    .font(.system(size: 11))
                    .foregroundColor(statusColor(sop.status))
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(statusColor(sop.status).opacity(0.1))
                    .cornerRadius(4)
            }

            // Title and version
            HStack(alignment: .top, spacing: 8) {
                Text(sop.title)
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(Color.fmText)
                    .lineLimit(2)
                    .fixedSize(horizontal: false, vertical: true)

                Spacer()

                Text(sop.version)
                    .font(.system(size: 11))
                    .foregroundColor(Color.fmText3)
                    .padding(.horizontal, 5)
                    .padding(.vertical, 2)
                    .background(Color.fmBg)
                    .cornerRadius(3)
            }

            // Category
            Text(sop.category)
                .font(.system(size: 12))
                .foregroundColor(Color.fmText2)

            // Description
            Text(sop.description)
                .font(.system(size: 12))
                .foregroundColor(Color.fmText3)
                .lineLimit(3)
                .frame(height: 48)

            Divider()

            // Stats
            HStack(spacing: 12) {
                VStack(alignment: .leading, spacing: 2) {
                    Text("\(sop.steps.count)")
                        .font(.system(size: 16, weight: .semibold))
                        .foregroundColor(Color.fmText)
                    Text("步骤")
                        .font(.system(size: 11))
                        .foregroundColor(Color.fmText3)
                }

                Divider()
                    .frame(height: 30)

                VStack(alignment: .leading, spacing: 2) {
                    Text("\(sop.usedCount)")
                        .font(.system(size: 16, weight: .semibold))
                        .foregroundColor(Color.fmText)
                    Text("使用")
                        .font(.system(size: 11))
                        .foregroundColor(Color.fmText3)
                }

                Divider()
                    .frame(height: 30)

                VStack(alignment: .leading, spacing: 2) {
                    Text("\(Int(sop.successRate * 100))%")
                        .font(.system(size: 16, weight: .semibold))
                        .foregroundColor(Color.fmText)
                    Text("成功率")
                        .font(.system(size: 11))
                        .foregroundColor(Color.fmText3)
                }

                Spacer()
            }

            // Author and date
            HStack {
                Text(sop.author)
                    .font(.system(size: 11))
                    .foregroundColor(Color.fmText3)

                Spacer()

                Text(sop.lastModified)
                    .font(.system(size: 11))
                    .foregroundColor(Color.fmText3)
            }
        }
        .padding(16)
        .background(Color.white)
        .cornerRadius(8)
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .stroke(Color.fmBorder, lineWidth: 1)
        )
    }

    private func statusColor(_ status: String) -> Color {
        switch status {
        case "草稿": return .gray
        case "审核中": return .orange
        case "已发布": return .green
        case "已归档": return .purple
        default: return .gray
        }
    }
}

// MARK: - Detail Sheet
struct SOPDetailSheet: View {
    let sop: SOPService.SOP
    @Environment(\.dismiss) var dismiss
    @State private var expandedSteps: Set<String> = []

    var body: some View {
        VStack(spacing: 0) {
            // Header
            HStack {
                VStack(alignment: .leading, spacing: 8) {
                    HStack(spacing: 12) {
                        Text(sop.title)
                            .font(.system(size: 20, weight: .semibold))
                            .foregroundColor(Color.fmText)

                        Text(sop.version)
                            .font(.system(size: 13))
                            .foregroundColor(Color.fmText3)
                            .padding(.horizontal, 8)
                            .padding(.vertical, 3)
                            .background(Color.fmBg)
                            .cornerRadius(4)

                        Text(sop.status)
                            .font(.system(size: 13))
                            .foregroundColor(statusColor(sop.status))
                            .padding(.horizontal, 8)
                            .padding(.vertical, 3)
                            .background(statusColor(sop.status).opacity(0.1))
                            .cornerRadius(4)
                    }

                    HStack(spacing: 16) {
                        Label(sop.category, systemImage: "folder")
                        Label(sop.author, systemImage: "person")
                        Label("更新于 \(sop.lastModified)", systemImage: "clock")
                    }
                    .font(.system(size: 13))
                    .foregroundColor(Color.fmText3)
                }

                Spacer()

                Button(action: { dismiss() }) {
                    Image(systemName: "xmark")
                        .font(.system(size: 14))
                        .foregroundColor(Color.fmText3)
                        .frame(width: 28, height: 28)
                        .background(Color.fmBg)
                        .cornerRadius(6)
                }
                .buttonStyle(PlainButtonStyle())
            }
            .padding(24)

            Divider()

            ScrollView {
                VStack(alignment: .leading, spacing: 24) {
                    // Description
                    SOPDetailSection(title: "流程说明", icon: "doc.text") {
                        Text(sop.description)
                            .font(.system(size: 14))
                            .foregroundColor(Color.fmText2)
                            .lineSpacing(4)
                    }

                    // Tags
                    SOPDetailSection(title: "标签", icon: "tag") {
                        FlowLayout(spacing: 8) {
                            ForEach(sop.tags, id: \.self) { tag in
                                Text(tag)
                                    .font(.system(size: 13))
                                    .foregroundColor(Color.fmText2)
                                    .padding(.horizontal, 10)
                                    .padding(.vertical, 5)
                                    .background(Color.fmBg)
                                    .cornerRadius(6)
                            }
                        }
                    }

                    // Usage stats
                    SOPDetailSection(title: "使用统计", icon: "chart.bar") {
                        HStack(spacing: 24) {
                            SOPStatCard(
                                label: "使用次数",
                                value: "\(sop.usedCount)",
                                icon: "arrow.clockwise",
                                color: .blue
                            )

                            SOPStatCard(
                                label: "成功率",
                                value: "\(Int(sop.successRate * 100))%",
                                icon: "checkmark.circle",
                                color: .green
                            )
                        }
                    }

                    // Steps
                    SOPDetailSection(title: "操作步骤", icon: "list.number") {
                        VStack(spacing: 12) {
                            ForEach(sop.steps) { step in
                                SOPStepCard(
                                    step: step,
                                    isExpanded: expandedSteps.contains("\(step.id)"),
                                    onToggle: {
                                        if expandedSteps.contains("\(step.id)") {
                                            expandedSteps.remove("\(step.id)")
                                        } else {
                                            expandedSteps.insert("\(step.id)")
                                        }
                                    }
                                )
                            }
                        }
                    }
                }
                .padding(24)
            }

            Divider()

            // Footer actions
            HStack(spacing: 12) {
                Button(action: {}) {
                    HStack(spacing: 6) {
                        Image(systemName: "square.and.arrow.up")
                            .font(.system(size: 13))
                        Text("导出")
                            .font(.system(size: 13))
                    }
                    .foregroundColor(Color.fmText2)
                    .padding(.horizontal, 16)
                    .padding(.vertical, 8)
                    .background(Color.fmBg)
                    .cornerRadius(6)
                }
                .buttonStyle(PlainButtonStyle())

                Button(action: {}) {
                    HStack(spacing: 6) {
                        Image(systemName: "square.and.pencil")
                            .font(.system(size: 13))
                        Text("编辑")
                            .font(.system(size: 13))
                    }
                    .foregroundColor(Color.fmText2)
                    .padding(.horizontal, 16)
                    .padding(.vertical, 8)
                    .background(Color.fmBg)
                    .cornerRadius(6)
                }
                .buttonStyle(PlainButtonStyle())

                Spacer()

                Button(action: {}) {
                    HStack(spacing: 6) {
                        Image(systemName: "play.fill")
                            .font(.system(size: 13))
                        Text("使用此 SOP")
                            .font(.system(size: 13))
                    }
                    .foregroundColor(.white)
                    .padding(.horizontal, 20)
                    .padding(.vertical, 8)
                    .background(Color.blue)
                    .cornerRadius(6)
                }
                .buttonStyle(PlainButtonStyle())
            }
            .padding(20)
        }
        .frame(width: 900, height: 700)
    }

    private func statusColor(_ status: String) -> Color {
        switch status {
        case "草稿": return .gray
        case "审核中": return .orange
        case "已发布": return .green
        case "已归档": return .purple
        default: return .gray
        }
    }
}

// MARK: - Detail Section
struct SOPDetailSection<Content: View>: View {
    let title: String
    let icon: String
    @ViewBuilder let content: Content

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Label {
                Text(title)
                    .font(.system(size: 15, weight: .semibold))
                    .foregroundColor(Color.fmText)
            } icon: {
                Image(systemName: icon)
                    .font(.system(size: 14))
                    .foregroundColor(Color.fmText2)
            }

            content
        }
    }
}

// MARK: - Stat Card
struct SOPStatCard: View {
    let label: String
    let value: String
    let icon: String
    let color: Color

    var body: some View {
        HStack(spacing: 12) {
            ZStack {
                RoundedRectangle(cornerRadius: 8)
                    .fill(color.opacity(0.1))
                    .frame(width: 44, height: 44)

                Image(systemName: icon)
                    .font(.system(size: 18))
                    .foregroundColor(color)
            }

            VStack(alignment: .leading, spacing: 2) {
                Text(label)
                    .font(.system(size: 12))
                    .foregroundColor(Color.fmText3)

                Text(value)
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundColor(Color.fmText)
            }

            Spacer()
        }
        .padding(12)
        .background(Color.fmBg)
        .cornerRadius(8)
    }
}

// MARK: - Step Card
struct SOPStepCard: View {
    let step: SOPService.SOPStep
    let isExpanded: Bool
    let onToggle: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            // Header
            Button(action: onToggle) {
                HStack(spacing: 12) {
                    // Step number
                    ZStack {
                        Circle()
                            .fill(Color.blue.opacity(0.1))
                            .frame(width: 32, height: 32)

                        Text("\(step.stepNumber)")
                            .font(.system(size: 14, weight: .semibold))
                            .foregroundColor(.blue)
                    }

                    VStack(alignment: .leading, spacing: 4) {
                        Text(step.title)
                            .font(.system(size: 14, weight: .medium))
                            .foregroundColor(Color.fmText)

                        if let estimatedTime = step.estimatedTime {
                            Label("\(estimatedTime) 分钟", systemImage: "clock")
                                .font(.system(size: 12))
                                .foregroundColor(Color.fmText3)
                        }
                    }

                    Spacer()

                    if step.required {
                        Text("必需")
                            .font(.system(size: 11))
                            .foregroundColor(.red)
                            .padding(.horizontal, 6)
                            .padding(.vertical, 2)
                            .background(Color.red.opacity(0.1))
                            .cornerRadius(4)
                    }

                    Image(systemName: isExpanded ? "chevron.up" : "chevron.down")
                        .font(.system(size: 12))
                        .foregroundColor(Color.fmText3)
                }
                .padding(16)
                .contentShape(Rectangle())
            }
            .buttonStyle(PlainButtonStyle())

            // Expanded content
            if isExpanded {
                VStack(alignment: .leading, spacing: 16) {
                    Divider()

                    // Description
                    VStack(alignment: .leading, spacing: 6) {
                        Text("操作说明")
                            .font(.system(size: 12, weight: .medium))
                            .foregroundColor(Color.fmText2)

                        Text(step.description)
                            .font(.system(size: 13))
                            .foregroundColor(Color.fmText2)
                            .lineSpacing(3)
                    }
                }
                .padding(.horizontal, 16)
                .padding(.bottom, 16)
            }
        }
        .background(Color.white)
        .cornerRadius(8)
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .stroke(Color.fmBorder, lineWidth: 1)
        )
    }
}
