import SwiftUI

// MARK: - Progress Milestone

struct ProgressMilestone: View {
    let title: String
    let isDone: Bool

    var body: some View {
        HStack(spacing: 6) {
            Image(systemName: isDone ? "checkmark.circle.fill" : "circle")
                .font(.system(size: 14, weight: .medium))
                .foregroundColor(isDone ? Color(hex: "66BB6A") : .fmText3)

            Text(title)
                .font(.system(size: 12))
                .foregroundColor(isDone ? .fmText : .fmText3)
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 6)
        .background(isDone ? Color(hex: "66BB6A").opacity(0.1) : Color.white)
        .cornerRadius(6)
        .overlay(
            RoundedRectangle(cornerRadius: 6)
                .stroke(isDone ? Color(hex: "66BB6A") : Color.fmBorder, lineWidth: 1)
        )
    }
}

// MARK: - Activity Item

struct ActivityItem: View {
    let icon: String
    let color: String
    let title: String
    let subtitle: String
    let time: String

    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: icon)
                .font(.system(size: 16, weight: .medium))
                .foregroundColor(Color(hex: color))
                .frame(width: 40, height: 40)
                .background(Color(hex: color).opacity(0.1))
                .cornerRadius(8)

            VStack(alignment: .leading, spacing: 4) {
                Text(title)
                    .font(.system(size: 13, weight: .medium))
                    .foregroundColor(.fmText)

                Text(subtitle)
                    .font(.system(size: 12))
                    .foregroundColor(.fmText2)
            }

            Spacer()

            Text(time)
                .font(.system(size: 11))
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
}

// MARK: - Material Type Card

struct MaterialTypeCard: View {
    let type: String
    let count: Int
    let icon: String
    let color: String

    var body: some View {
        VStack(spacing: 12) {
            Image(systemName: icon)
                .font(.system(size: 24, weight: .semibold))
                .foregroundColor(Color(hex: color))
                .frame(width: 56, height: 56)
                .background(Color(hex: color).opacity(0.1))
                .cornerRadius(12)

            Text("\(count)")
                .font(.system(size: 24, weight: .bold))
                .foregroundColor(.fmText)

            Text(type)
                .font(.system(size: 13))
                .foregroundColor(.fmText2)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 20)
        .background(Color.white)
        .cornerRadius(12)
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(Color.fmBorder, lineWidth: 1)
        )
    }
}

// MARK: - Project Material Row

struct ProjectMaterialRow: View {
    let material: Material

    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: material.type.icon)
                .font(.system(size: 18, weight: .medium))
                .foregroundColor(Color(hex: materialColor))
                .frame(width: 44, height: 44)
                .background(Color(hex: materialColor).opacity(0.1))
                .cornerRadius(8)

            VStack(alignment: .leading, spacing: 4) {
                Text(material.name)
                    .font(.system(size: 13, weight: .medium))
                    .foregroundColor(.fmText)
                    .lineLimit(1)

                HStack(spacing: 8) {
                    Text(material.type.displayName)
                        .font(.system(size: 11))
                        .foregroundColor(.fmText3)

                    if let duration = material.duration {
                        Text("·")
                            .foregroundColor(.fmText3)
                        Text(duration)
                            .font(.system(size: 11))
                            .foregroundColor(.fmText3)
                    }

                    if let size = material.size {
                        Text("·")
                            .foregroundColor(.fmText3)
                        Text(size)
                            .font(.system(size: 11))
                            .foregroundColor(.fmText3)
                    }
                }
            }

            Spacer()

            // Status badge
            HStack(spacing: 4) {
                Circle()
                    .fill(Color(hex: statusColor))
                    .frame(width: 6, height: 6)

                Text(statusText)
                    .font(.system(size: 11, weight: .medium))
                    .foregroundColor(Color(hex: statusColor))
            }
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(Color(hex: statusColor).opacity(0.1))
            .cornerRadius(4)
        }
        .padding(12)
    }

    var materialColor: String {
        switch material.type {
        case .audio: return "42A5F5"
        case .video: return "66BB6A"
        case .document: return "FFA726"
        case .spreadsheet: return "AB47BC"
        case .image: return "EC407A"
        }
    }

    var statusColor: String {
        switch material.status {
        case .pending: return "FFA726"
        case .processing: return "42A5F5"
        case .completed: return "66BB6A"
        case .failed: return "EF5350"
        }
    }

    var statusText: String {
        switch material.status {
        case .pending: return "待处理"
        case .processing: return "处理中"
        case .completed: return "已完成"
        case .failed: return "失败"
        }
    }
}

// MARK: - Business Item

struct BusinessItem: View {
    let name: String
    let score: Double
    let trend: String

    var body: some View {
        HStack(spacing: 12) {
            VStack(alignment: .leading, spacing: 4) {
                Text(name)
                    .font(.system(size: 13, weight: .medium))
                    .foregroundColor(.fmText)

                HStack(spacing: 6) {
                    HStack(spacing: 2) {
                        ForEach(0..<Int(score), id: \.self) { _ in
                            Image(systemName: "star.fill")
                                .font(.system(size: 10))
                                .foregroundColor(Color(hex: "FFA726"))
                        }
                        if score - Double(Int(score)) >= 0.5 {
                            Image(systemName: "star.leadinghalf.filled")
                                .font(.system(size: 10))
                                .foregroundColor(Color(hex: "FFA726"))
                        }
                    }

                    Text(String(format: "%.1f", score))
                        .font(.system(size: 11, weight: .medium))
                        .foregroundColor(.fmText3)
                }
            }

            Spacer()

            // Trend indicator
            HStack(spacing: 4) {
                Image(systemName: trendIcon)
                    .font(.system(size: 11))
                    .foregroundColor(Color(hex: trendColor))

                Text(trendText)
                    .font(.system(size: 11, weight: .medium))
                    .foregroundColor(Color(hex: trendColor))
            }
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(Color(hex: trendColor).opacity(0.1))
            .cornerRadius(4)
        }
        .padding(12)
        .background(Color.white)
        .cornerRadius(8)
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .stroke(Color.fmBorder, lineWidth: 1)
        )
    }

    var trendIcon: String {
        switch trend {
        case "up": return "arrow.up.right"
        case "down": return "arrow.down.right"
        default: return "minus"
        }
    }

    var trendColor: String {
        switch trend {
        case "up": return "66BB6A"
        case "down": return "EF5350"
        default: return "9E9E9E"
        }
    }

    var trendText: String {
        switch trend {
        case "up": return "上升"
        case "down": return "下降"
        default: return "稳定"
        }
    }
}

// MARK: - SOP Step Item

struct SOPStepItem: View {
    let title: String
    let status: String
    let progress: Double

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(spacing: 12) {
                Image(systemName: statusIcon)
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(Color(hex: statusColor))
                    .frame(width: 32, height: 32)
                    .background(Color(hex: statusColor).opacity(0.1))
                    .cornerRadius(8)

                Text(title)
                    .font(.system(size: 13, weight: .medium))
                    .foregroundColor(.fmText)

                Spacer()

                Text(statusText)
                    .font(.system(size: 11, weight: .medium))
                    .foregroundColor(Color(hex: statusColor))
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(Color(hex: statusColor).opacity(0.1))
                    .cornerRadius(4)
            }

            // Progress bar
            if status == "active" || status == "completed" {
                GeometryReader { geometry in
                    ZStack(alignment: .leading) {
                        RoundedRectangle(cornerRadius: 4)
                            .fill(Color.fmBg2)
                            .frame(height: 6)

                        RoundedRectangle(cornerRadius: 4)
                            .fill(Color(hex: statusColor))
                            .frame(width: geometry.size.width * progress, height: 6)
                    }
                }
                .frame(height: 6)
                .padding(.leading, 44)
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

    var statusIcon: String {
        switch status {
        case "completed": return "checkmark.circle.fill"
        case "active": return "play.circle.fill"
        case "pending": return "circle"
        default: return "circle"
        }
    }

    var statusColor: String {
        switch status {
        case "completed": return "66BB6A"
        case "active": return "42A5F5"
        case "pending": return "BDBDBD"
        default: return "BDBDBD"
        }
    }

    var statusText: String {
        switch status {
        case "completed": return "已完成"
        case "active": return "进行中"
        case "pending": return "未开始"
        default: return "未开始"
        }
    }
}

// MARK: - Team Member Card

struct TeamMemberCard: View {
    let member: TeamMember

    @State private var isHovered = false

    var body: some View {
        HStack(spacing: 16) {
            Image(systemName: member.avatar)
                .font(.system(size: 24, weight: .medium))
                .foregroundColor(Color(hex: "007AFF"))
                .frame(width: 56, height: 56)
                .background(Color(hex: "007AFF").opacity(0.1))
                .cornerRadius(28)

            VStack(alignment: .leading, spacing: 4) {
                Text(member.name)
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundColor(.fmText)

                Text(member.role)
                    .font(.system(size: 12))
                    .foregroundColor(.fmText2)
            }

            Spacer()

            Button(action: {}) {
                Image(systemName: "envelope")
                    .font(.system(size: 14))
                    .foregroundColor(.fmText2)
                    .frame(width: 32, height: 32)
                    .background(Color.fmBg2)
                    .cornerRadius(8)
            }
            .buttonStyle(.plain)
        }
        .padding(16)
        .background(isHovered ? Color(hex: "FAFAFA") : Color.white)
        .cornerRadius(12)
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(isHovered ? Color(hex: "007AFF") : Color.fmBorder, lineWidth: 1)
        )
        .onHover { hovering in
            withAnimation(.easeInOut(duration: 0.2)) {
                isHovered = hovering
            }
        }
    }
}

// MARK: - Collaboration Stat Card

struct CollaborationStatCard: View {
    let title: String
    let value: String
    let icon: String
    let color: String

    var body: some View {
        VStack(spacing: 12) {
            Image(systemName: icon)
                .font(.system(size: 20, weight: .semibold))
                .foregroundColor(Color(hex: color))
                .frame(width: 48, height: 48)
                .background(Color(hex: color).opacity(0.1))
                .cornerRadius(10)

            Text(value)
                .font(.system(size: 24, weight: .bold))
                .foregroundColor(.fmText)

            Text(title)
                .font(.system(size: 12))
                .foregroundColor(.fmText2)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 20)
        .background(Color.white)
        .cornerRadius(12)
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(Color.fmBorder, lineWidth: 1)
        )
    }
}

// MARK: - Project Detail Flow Layout

struct ProjectDetailFlowLayout: Layout {
    var spacing: CGFloat = 8

    func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) -> CGSize {
        let result = FlowResult(
            in: proposal.replacingUnspecifiedDimensions().width,
            subviews: subviews,
            spacing: spacing
        )
        return result.size
    }

    func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) {
        let result = FlowResult(
            in: bounds.width,
            subviews: subviews,
            spacing: spacing
        )
        for (index, subview) in subviews.enumerated() {
            subview.place(at: CGPoint(x: bounds.minX + result.positions[index].x, y: bounds.minY + result.positions[index].y), proposal: .unspecified)
        }
    }

    struct FlowResult {
        var size: CGSize = .zero
        var positions: [CGPoint] = []

        init(in maxWidth: CGFloat, subviews: Subviews, spacing: CGFloat) {
            var x: CGFloat = 0
            var y: CGFloat = 0
            var lineHeight: CGFloat = 0

            for subview in subviews {
                let size = subview.sizeThatFits(.unspecified)

                if x + size.width > maxWidth && x > 0 {
                    x = 0
                    y += lineHeight + spacing
                    lineHeight = 0
                }

                positions.append(CGPoint(x: x, y: y))
                lineHeight = max(lineHeight, size.height)
                x += size.width + spacing
            }

            self.size = CGSize(width: maxWidth, height: y + lineHeight)
        }
    }
}
