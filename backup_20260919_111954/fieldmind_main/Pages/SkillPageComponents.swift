import SwiftUI

// MARK: - SkillCard

struct SkillCard: View {
    let skill: Skill
    @State private var isHovered = false

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            // Header with Icon and Badges
            HStack(alignment: .top, spacing: 12) {
                // Icon
                ZStack {
                    Circle()
                        .fill(categoryColor.opacity(0.1))
                        .frame(width: 56, height: 56)

                    Image(systemName: skill.icon)
                        .font(.system(size: 24))
                        .foregroundColor(categoryColor)
                }

                VStack(alignment: .leading, spacing: 6) {
                    // Name and Badges
                    HStack(spacing: 8) {
                        Text(skill.name)
                            .font(.system(size: 16, weight: .semibold))
                            .foregroundColor(Color.fmText)
                            .lineLimit(1)

                        if skill.isOfficial {
                            Image(systemName: "checkmark.seal.fill")
                                .font(.system(size: 14))
                                .foregroundColor(.blue)
                        }

                        if skill.isPremium {
                            Text("付费")
                                .font(.system(size: 11, weight: .medium))
                                .foregroundColor(.orange)
                                .padding(.horizontal, 6)
                                .padding(.vertical, 2)
                                .background(Color.orange.opacity(0.1))
                                .cornerRadius(4)
                        }

                        if skill.isInstalled {
                            Text("已安装")
                                .font(.system(size: 11, weight: .medium))
                                .foregroundColor(.green)
                                .padding(.horizontal, 6)
                                .padding(.vertical, 2)
                                .background(Color.green.opacity(0.1))
                                .cornerRadius(4)
                        }
                    }

                    // Category
                    Text(skill.category)
                        .font(.system(size: 12))
                        .foregroundColor(Color.fmText3)
                }

                Spacer()

                // Rating
                HStack(spacing: 4) {
                    Image(systemName: "star.fill")
                        .font(.system(size: 12))
                        .foregroundColor(.orange)
                    Text(String(format: "%.1f", skill.rating))
                        .font(.system(size: 13, weight: .medium))
                        .foregroundColor(Color.fmText)
                }
            }
            .padding(16)

            Divider()

            // Description
            Text(skill.description)
                .font(.system(size: 14))
                .foregroundColor(Color.fmText2)
                .lineLimit(2)
                .padding(.horizontal, 16)
                .padding(.vertical, 12)

            // Tags
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 8) {
                    ForEach(skill.tags, id: \.self) { tag in
                        Text(tag)
                            .font(.system(size: 12))
                            .foregroundColor(Color.fmText3)
                            .padding(.horizontal, 10)
                            .padding(.vertical, 4)
                            .background(Color(hex: "F5F5F5"))
                            .cornerRadius(12)
                    }
                }
                .padding(.horizontal, 16)
            }
            .padding(.bottom, 12)

            Divider()

            // Footer - Stats and Author
            HStack(spacing: 16) {
                // Download Count
                HStack(spacing: 4) {
                    Image(systemName: "arrow.down.circle")
                        .font(.system(size: 12))
                        .foregroundColor(Color.fmText3)
                    Text("\(formatNumber(skill.downloadCount))")
                        .font(.system(size: 12))
                        .foregroundColor(Color.fmText3)
                }

                // Review Count
                HStack(spacing: 4) {
                    Image(systemName: "text.bubble")
                        .font(.system(size: 12))
                        .foregroundColor(Color.fmText3)
                    Text("\(skill.reviewCount)")
                        .font(.system(size: 12))
                        .foregroundColor(Color.fmText3)
                }

                Spacer()

                // Author
                Text(skill.author)
                    .font(.system(size: 12))
                    .foregroundColor(Color.fmText3)
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 12)
        }
        .background(Color.white)
        .cornerRadius(12)
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(isHovered ? Color.blue.opacity(0.3) : Color.fmBorder, lineWidth: 1)
        )
        .shadow(color: isHovered ? Color.black.opacity(0.1) : Color.clear, radius: 8, x: 0, y: 4)
        .scaleEffect(isHovered ? 1.02 : 1.0)
        .animation(.easeInOut(duration: 0.2), value: isHovered)
        .onHover { hovering in
            isHovered = hovering
        }
    }

    private var categoryColor: Color {
        switch skill.category {
        case "数据处理": return .blue
        case "AI分析": return .purple
        case "可视化": return .green
        case "报告生成": return .orange
        case "工具集成": return .pink
        default: return .gray
        }
    }

    private func formatNumber(_ number: Int) -> String {
        if number >= 10000 {
            return String(format: "%.1fw", Double(number) / 10000.0)
        }
        return "\(number)"
    }
}

// MARK: - SkillDetailSheet

struct SkillDetailSheet: View {
    let skill: Skill
    @Environment(\.dismiss) var dismiss

    var body: some View {
        VStack(spacing: 0) {
            // Header
            HStack(spacing: 16) {
                // Icon
                ZStack {
                    Circle()
                        .fill(categoryColor.opacity(0.1))
                        .frame(width: 80, height: 80)

                    Image(systemName: skill.icon)
                        .font(.system(size: 36))
                        .foregroundColor(categoryColor)
                }

                VStack(alignment: .leading, spacing: 8) {
                    // Name and Badges
                    HStack(spacing: 10) {
                        Text(skill.name)
                            .font(.system(size: 24, weight: .semibold))
                            .foregroundColor(Color.fmText)

                        if skill.isOfficial {
                            Image(systemName: "checkmark.seal.fill")
                                .font(.system(size: 18))
                                .foregroundColor(.blue)
                        }

                        if skill.isPremium {
                            Text("付费")
                                .font(.system(size: 12, weight: .medium))
                                .foregroundColor(.orange)
                                .padding(.horizontal, 8)
                                .padding(.vertical, 4)
                                .background(Color.orange.opacity(0.1))
                                .cornerRadius(6)
                        }

                        if skill.isInstalled {
                            Text("已安装")
                                .font(.system(size: 12, weight: .medium))
                                .foregroundColor(.green)
                                .padding(.horizontal, 8)
                                .padding(.vertical, 4)
                                .background(Color.green.opacity(0.1))
                                .cornerRadius(6)
                        }
                    }

                    // Category
                    Text(skill.category)
                        .font(.system(size: 14))
                        .foregroundColor(categoryColor)
                        .padding(.horizontal, 10)
                        .padding(.vertical, 4)
                        .background(categoryColor.opacity(0.1))
                        .cornerRadius(12)

                    // Stats
                    HStack(spacing: 20) {
                        HStack(spacing: 4) {
                            Image(systemName: "star.fill")
                                .font(.system(size: 14))
                                .foregroundColor(.orange)
                            Text(String(format: "%.1f", skill.rating))
                                .font(.system(size: 14, weight: .medium))
                                .foregroundColor(Color.fmText)
                            Text("(\(skill.reviewCount) 评价)")
                                .font(.system(size: 13))
                                .foregroundColor(Color.fmText3)
                        }

                        HStack(spacing: 4) {
                            Image(systemName: "arrow.down.circle")
                                .font(.system(size: 14))
                                .foregroundColor(Color.fmText3)
                            Text("\(formatNumber(skill.downloadCount)) 次下载")
                                .font(.system(size: 13))
                                .foregroundColor(Color.fmText3)
                        }
                    }
                }

                Spacer()

                Button(action: { dismiss() }) {
                    Image(systemName: "xmark.circle.fill")
                        .font(.system(size: 24))
                        .foregroundColor(Color.fmText3)
                }
                .buttonStyle(PlainButtonStyle())
            }
            .padding(24)
            .background(Color(hex: "FAFAFA"))

            Divider()

            // Content
            ScrollView {
                VStack(alignment: .leading, spacing: 24) {
                    // Description Section
                    SkillSection(icon: "doc.text", title: "技能说明") {
                        Text(skill.detailedDescription)
                            .font(.system(size: 14))
                            .foregroundColor(Color.fmText2)
                            .lineSpacing(6)
                    }

                    // Features Section
                    SkillSection(icon: "star.circle", title: "核心功能") {
                        VStack(alignment: .leading, spacing: 10) {
                            ForEach(skill.features, id: \.self) { feature in
                                HStack(alignment: .top, spacing: 8) {
                                    Text("•")
                                        .font(.system(size: 14))
                                        .foregroundColor(categoryColor)
                                    Text(feature)
                                        .font(.system(size: 14))
                                        .foregroundColor(Color.fmText2)
                                }
                            }
                        }
                    }

                    // Usage Examples Section
                    SkillSection(icon: "lightbulb", title: "使用场景") {
                        VStack(alignment: .leading, spacing: 10) {
                            ForEach(skill.usageExamples, id: \.self) { example in
                                HStack(alignment: .top, spacing: 8) {
                                    Text("•")
                                        .font(.system(size: 14))
                                        .foregroundColor(categoryColor)
                                    Text(example)
                                        .font(.system(size: 14))
                                        .foregroundColor(Color.fmText2)
                                }
                            }
                        }
                    }

                    // Requirements Section
                    SkillSection(icon: "info.circle", title: "系统要求") {
                        VStack(alignment: .leading, spacing: 10) {
                            ForEach(skill.requirements, id: \.self) { requirement in
                                HStack(alignment: .top, spacing: 8) {
                                    Text("•")
                                        .font(.system(size: 14))
                                        .foregroundColor(.blue)
                                    Text(requirement)
                                        .font(.system(size: 14))
                                        .foregroundColor(Color.fmText2)
                                }
                            }
                        }
                    }

                    // Dependencies Section
                    if !skill.dependencies.isEmpty {
                        SkillSection(icon: "link", title: "依赖项") {
                            VStack(alignment: .leading, spacing: 10) {
                                ForEach(skill.dependencies, id: \.self) { dependency in
                                    HStack(alignment: .top, spacing: 8) {
                                        Text("•")
                                            .font(.system(size: 14))
                                            .foregroundColor(.orange)
                                        Text(dependency)
                                            .font(.system(size: 14))
                                            .foregroundColor(Color.fmText2)
                                    }
                                }
                            }
                        }
                    }

                    // Technical Info Section
                    SkillSection(icon: "gearshape.2", title: "技术信息") {
                        VStack(alignment: .leading, spacing: 12) {
                            InfoRow(label: "版本", value: skill.version)
                            InfoRow(label: "文件大小", value: skill.fileSize)
                            InfoRow(label: "兼容性", value: skill.compatibility)
                            InfoRow(label: "作者", value: skill.author)
                            InfoRow(label: "最后更新", value: skill.lastUpdated)
                        }
                    }

                    // Changelog Section
                    SkillSection(icon: "clock.arrow.circlepath", title: "更新日志") {
                        Text(skill.changelog)
                            .font(.system(size: 14))
                            .foregroundColor(Color.fmText2)
                            .lineSpacing(6)
                    }

                    // Tags Section
                    SkillSection(icon: "tag", title: "标签") {
                        FlowLayout(spacing: 8) {
                            ForEach(skill.tags, id: \.self) { tag in
                                Text(tag)
                                    .font(.system(size: 13))
                                    .foregroundColor(Color.fmText2)
                                    .padding(.horizontal, 12)
                                    .padding(.vertical, 6)
                                    .background(Color(hex: "F5F5F5"))
                                    .cornerRadius(16)
                            }
                        }
                    }
                }
                .padding(24)
            }

            Divider()

            // Footer Actions
            HStack(spacing: 12) {
                if skill.isInstalled {
                    Button(action: {}) {
                        HStack(spacing: 8) {
                            Image(systemName: "trash")
                                .font(.system(size: 14))
                            Text("卸载")
                                .font(.system(size: 14, weight: .medium))
                        }
                        .foregroundColor(.red)
                        .padding(.horizontal, 20)
                        .padding(.vertical, 10)
                        .background(Color.red.opacity(0.1))
                        .cornerRadius(8)
                    }
                    .buttonStyle(PlainButtonStyle())

                    Button(action: {}) {
                        HStack(spacing: 8) {
                            Image(systemName: "arrow.clockwise")
                                .font(.system(size: 14))
                            Text("检查更新")
                                .font(.system(size: 14, weight: .medium))
                        }
                        .foregroundColor(Color.fmText)
                        .padding(.horizontal, 20)
                        .padding(.vertical, 10)
                        .background(Color(hex: "F5F5F5"))
                        .cornerRadius(8)
                    }
                    .buttonStyle(PlainButtonStyle())
                } else {
                    Button(action: {}) {
                        HStack(spacing: 8) {
                            Image(systemName: "arrow.down.circle.fill")
                                .font(.system(size: 14))
                            Text(skill.isPremium ? "购买并安装" : "立即安装")
                                .font(.system(size: 14, weight: .medium))
                        }
                        .foregroundColor(.white)
                        .padding(.horizontal, 24)
                        .padding(.vertical, 10)
                        .background(Color.blue)
                        .cornerRadius(8)
                    }
                    .buttonStyle(PlainButtonStyle())
                }

                Button(action: {}) {
                    HStack(spacing: 8) {
                        Image(systemName: "square.and.arrow.up")
                            .font(.system(size: 14))
                        Text("分享")
                            .font(.system(size: 14, weight: .medium))
                    }
                    .foregroundColor(Color.fmText)
                    .padding(.horizontal, 20)
                    .padding(.vertical, 10)
                    .background(Color(hex: "F5F5F5"))
                    .cornerRadius(8)
                }
                .buttonStyle(PlainButtonStyle())

                Spacer()

                Text("v\(skill.version)")
                    .font(.system(size: 13))
                    .foregroundColor(Color.fmText3)
            }
            .padding(20)
            .background(Color(hex: "FAFAFA"))
        }
        .frame(width: 900, height: 700)
    }

    private var categoryColor: Color {
        switch skill.category {
        case "数据处理": return .blue
        case "AI分析": return .purple
        case "可视化": return .green
        case "报告生成": return .orange
        case "工具集成": return .pink
        default: return .gray
        }
    }

    private func formatNumber(_ number: Int) -> String {
        if number >= 10000 {
            return String(format: "%.1fw", Double(number) / 10000.0)
        }
        return "\(number)"
    }
}

// MARK: - SkillSection

struct SkillSection<Content: View>: View {
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
                    .font(.system(size: 16))
                    .foregroundColor(.blue)

                Text(title)
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundColor(Color.fmText)
            }

            content
        }
    }
}
