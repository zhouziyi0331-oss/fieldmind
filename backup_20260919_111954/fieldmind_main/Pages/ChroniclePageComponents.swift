import SwiftUI

// MARK: - Event Card
struct EventCard: View {
    let event: ChronicleEvent

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Header
            HStack {
                HStack(spacing: 4) {
                    Circle()
                        .fill(categoryColor(event.category))
                        .frame(width: 6, height: 6)
                    Text(event.category)
                        .font(.system(size: 11))
                        .foregroundColor(Color.fmText2)
                }
                .padding(.horizontal, 8)
                .padding(.vertical, 4)
                .background(categoryColor(event.category).opacity(0.1))
                .cornerRadius(4)

                Spacer()

                Text(event.date)
                    .font(.system(size: 11))
                    .foregroundColor(Color.fmText3)
            }

            // Title
            Text(event.title)
                .font(.system(size: 14, weight: .semibold))
                .foregroundColor(Color.fmText)
                .lineLimit(2)

            // Description
            Text(event.description)
                .font(.system(size: 12))
                .foregroundColor(Color.fmText2)
                .lineLimit(3)

            // Tags
            if !event.tags.isEmpty {
                FlowLayout(spacing: 6) {
                    ForEach(event.tags.prefix(3), id: \.self) { tag in
                        Text(tag)
                            .font(.system(size: 10))
                            .foregroundColor(Color.fmText3)
                            .padding(.horizontal, 6)
                            .padding(.vertical, 3)
                            .background(Color.fmBg)
                            .cornerRadius(3)
                    }
                }
            }

            Divider()

            // Footer
            HStack(spacing: 12) {
                if !event.participants.isEmpty {
                    HStack(spacing: 4) {
                        Image(systemName: "person.2")
                            .font(.system(size: 10))
                        Text("\(event.participants.count)")
                            .font(.system(size: 10))
                    }
                }

                if !event.materials.isEmpty {
                    HStack(spacing: 4) {
                        Image(systemName: "doc.text")
                            .font(.system(size: 10))
                        Text("\(event.materials.count)")
                            .font(.system(size: 10))
                    }
                }

                Spacer()

                if event.importance > 0 {
                    HStack(spacing: 2) {
                        ForEach(0..<event.importance, id: \.self) { _ in
                            Image(systemName: "star.fill")
                                .font(.system(size: 9))
                                .foregroundColor(.fmYellow)
                        }
                    }
                }
            }
            .foregroundColor(Color.fmText3)
            .font(.system(size: 10))

            // Project
            Text(event.project)
                .font(.system(size: 10))
                .foregroundColor(Color.fmText3)
        }
        .padding(14)
        .background(Color.white)
        .cornerRadius(8)
        .shadow(color: Color.black.opacity(0.04), radius: 2, x: 0, y: 1)
        .shadow(color: Color.black.opacity(0.06), radius: 8, x: 0, y: 4)
    }

    private func categoryColor(_ category: String) -> Color {
        switch category {
        case "文化活动": return Color(hex: "3B82F6")
        case "调研记录": return Color(hex: "10B981")
        case "政策变化": return .fmYellow
        case "技艺传承": return Color(hex: "8B5CF6")
        case "经济变迁": return .fmPink
        case "环境变化": return Color(hex: "14B8A6")
        default: return Color(hex: "64748B")
        }
    }
}

// MARK: - Legend Item
struct ChronicleLegendItem: View {
    let color: Color
    let label: String
    let count: Int

    var body: some View {
        HStack(spacing: 8) {
            Circle()
                .fill(color)
                .frame(width: 8, height: 8)

            Text(label)
                .font(.system(size: 12))
                .foregroundColor(Color.fmText2)

            Spacer()

            Text("\(count)")
                .font(.system(size: 12, weight: .medium))
                .foregroundColor(Color.fmText3)
        }
    }
}

// MARK: - Stat Row
struct ChronicleStatRow: View {
    let label: String
    let value: String

    var body: some View {
        HStack {
            Text(label)
                .font(.system(size: 12))
                .foregroundColor(Color.fmText3)

            Spacer()

            Text(value)
                .font(.system(size: 12, weight: .medium))
                .foregroundColor(Color.fmText)
        }
    }
}

// MARK: - Event Detail Sheet
struct EventDetailSheet: View {
    let event: ChronicleEvent
    let onDismiss: () -> Void

    var body: some View {
        VStack(spacing: 0) {
            // Header
            HStack {
                Text("事件详情")
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundColor(Color.fmText)

                Spacer()

                Button(action: onDismiss) {
                    Image(systemName: "xmark")
                        .font(.system(size: 14))
                        .foregroundColor(Color.fmText3)
                        .frame(width: 28, height: 28)
                        .background(Color.fmBg)
                        .cornerRadius(6)
                }
                .buttonStyle(PlainButtonStyle())
            }
            .padding(20)

            Divider()

            // Content
            ScrollView {
                VStack(alignment: .leading, spacing: 24) {
                    // Basic Info
                    VStack(alignment: .leading, spacing: 12) {
                        HStack {
                            HStack(spacing: 4) {
                                Circle()
                                    .fill(categoryColor(event.category))
                                    .frame(width: 6, height: 6)
                                Text(event.category)
                                    .font(.system(size: 12))
                                    .foregroundColor(Color.fmText2)
                            }
                            .padding(.horizontal, 10)
                            .padding(.vertical, 5)
                            .background(categoryColor(event.category).opacity(0.1))
                            .cornerRadius(5)

                            Text(event.date)
                                .font(.system(size: 12))
                                .foregroundColor(Color.fmText3)
                        }

                        Text(event.title)
                            .font(.system(size: 20, weight: .semibold))
                            .foregroundColor(Color.fmText)

                        Text(event.description)
                            .font(.system(size: 14))
                            .foregroundColor(Color.fmText2)
                            .lineSpacing(4)
                    }

                    Divider()

                    // Project
                    EventDetailSection(title: "所属项目") {
                        Text(event.project)
                            .font(.system(size: 13))
                            .foregroundColor(Color.fmText2)
                            .padding(12)
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .background(Color.fmBg)
                            .cornerRadius(6)
                    }

                    // Location
                    if let location = event.location {
                        EventDetailSection(title: "地点") {
                            HStack(spacing: 8) {
                                Image(systemName: "mappin.circle")
                                    .foregroundColor(Color.fmText3)
                                Text(location)
                                    .font(.system(size: 13))
                                    .foregroundColor(Color.fmText2)
                            }
                            .padding(12)
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .background(Color.fmBg)
                            .cornerRadius(6)
                        }
                    }

                    // Participants
                    if !event.participants.isEmpty {
                        EventDetailSection(title: "参与人员") {
                            FlowLayout(spacing: 8) {
                                ForEach(event.participants, id: \.self) { participant in
                                    HStack(spacing: 6) {
                                        Image(systemName: "person.circle")
                                            .font(.system(size: 12))
                                        Text(participant)
                                            .font(.system(size: 12))
                                    }
                                    .foregroundColor(Color.fmText2)
                                    .padding(.horizontal, 10)
                                    .padding(.vertical, 6)
                                    .background(Color.fmBg)
                                    .cornerRadius(6)
                                }
                            }
                        }
                    }

                    // Materials
                    if !event.materials.isEmpty {
                        EventDetailSection(title: "相关材料") {
                            VStack(spacing: 8) {
                                ForEach(event.materials, id: \.self) { material in
                                    HStack(spacing: 8) {
                                        Image(systemName: "doc.text")
                                            .font(.system(size: 12))
                                            .foregroundColor(Color.fmText3)

                                        Text(material)
                                            .font(.system(size: 13))
                                            .foregroundColor(Color.fmText2)

                                        Spacer()

                                        Image(systemName: "chevron.right")
                                            .font(.system(size: 11))
                                            .foregroundColor(Color.fmText3)
                                    }
                                    .padding(12)
                                    .background(Color.fmBg)
                                    .cornerRadius(6)
                                }
                            }
                        }
                    }

                    // Tags
                    if !event.tags.isEmpty {
                        EventDetailSection(title: "标签") {
                            FlowLayout(spacing: 8) {
                                ForEach(event.tags, id: \.self) { tag in
                                    Text(tag)
                                        .font(.system(size: 12))
                                        .foregroundColor(Color.fmText2)
                                        .padding(.horizontal, 10)
                                        .padding(.vertical, 6)
                                        .background(Color.fmBg)
                                        .cornerRadius(6)
                                }
                            }
                        }
                    }

                    // Importance
                    if event.importance > 0 {
                        EventDetailSection(title: "重要程度") {
                            HStack(spacing: 4) {
                                ForEach(0..<5, id: \.self) { index in
                                    Image(systemName: index < event.importance ? "star.fill" : "star")
                                        .font(.system(size: 16))
                                        .foregroundColor(.fmYellow)
                                }
                            }
                            .padding(12)
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .background(Color.fmBg)
                            .cornerRadius(6)
                        }
                    }
                }
                .padding(20)
            }
        }
        .frame(width: 600, height: 700)
        .background(Color.white)
    }

    private func categoryColor(_ category: String) -> Color {
        switch category {
        case "文化活动": return Color(hex: "3B82F6")
        case "调研记录": return Color(hex: "10B981")
        case "政策变化": return .fmYellow
        case "技艺传承": return Color(hex: "8B5CF6")
        case "经济变迁": return .fmPink
        case "环境变化": return Color(hex: "14B8A6")
        default: return Color(hex: "64748B")
        }
    }
}

// MARK: - Detail Section
struct EventDetailSection<Content: View>: View {
    let title: String
    let content: Content

    init(title: String, @ViewBuilder content: () -> Content) {
        self.title = title
        self.content = content()
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text(title)
                .font(.system(size: 13, weight: .semibold))
                .foregroundColor(Color.fmText3)

            content
        }
    }
}
