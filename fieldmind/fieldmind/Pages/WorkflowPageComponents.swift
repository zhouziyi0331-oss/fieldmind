import SwiftUI

// MARK: - Workflow Card
struct WorkflowCard: View {
    let workflow: WorkflowTemplate

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            // Header
            HStack(spacing: 12) {
                // Icon
                Image(systemName: workflow.icon)
                    .font(.system(size: 32))
                    .foregroundColor(.blue)
                    .frame(width: 56, height: 56)
                    .background(Color.blue.opacity(0.1))
                    .cornerRadius(8)

                VStack(alignment: .leading, spacing: 6) {
                    HStack(spacing: 8) {
                        Text(workflow.name)
                            .font(.system(size: 15, weight: .semibold))
                            .foregroundColor(Color.fmText)
                            .lineLimit(1)

                        if workflow.isFavorite {
                            Image(systemName: "star.fill")
                                .font(.system(size: 11))
                                .foregroundColor(.orange)
                        }
                    }

                    HStack(spacing: 8) {
                        Text(workflow.category)
                            .font(.system(size: 12))
                            .foregroundColor(.blue)
                            .padding(.horizontal, 8)
                            .padding(.vertical, 3)
                            .background(Color.blue.opacity(0.1))
                            .cornerRadius(4)

                        ComplexityBadge(complexity: workflow.complexity)
                    }
                }

                Spacer()
            }
            .padding(16)

            Divider()

            // Description
            Text(workflow.description)
                .font(.system(size: 13))
                .foregroundColor(Color.fmText2)
                .lineLimit(2)
                .padding(.horizontal, 16)
                .padding(.vertical, 12)

            // Tags
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 8) {
                    ForEach(workflow.tags, id: \.self) { tag in
                        Text(tag)
                            .font(.system(size: 12))
                            .foregroundColor(Color.fmText3)
                            .padding(.horizontal, 8)
                            .padding(.vertical, 4)
                            .background(Color.fmBg)
                            .cornerRadius(4)
                    }
                }
                .padding(.horizontal, 16)
            }
            .padding(.bottom, 12)

            Divider()

            // Metrics
            HStack(spacing: 24) {
                WorkflowMetricItem(icon: "arrow.triangle.2.circlepath", label: "使用", value: "\(workflow.usageCount)次")
                WorkflowMetricItem(icon: "star.fill", label: "评分", value: String(format: "%.1f", workflow.rating))
                WorkflowMetricItem(icon: "clock", label: "用时", value: workflow.estimatedTime)
            }
            .padding(16)

            Divider()

            // Footer
            HStack {
                HStack(spacing: 6) {
                    Image(systemName: "person.circle")
                        .font(.system(size: 12))
                        .foregroundColor(Color.fmText3)
                    Text(workflow.createdBy)
                        .font(.system(size: 12))
                        .foregroundColor(Color.fmText3)
                }

                Spacer()

                Text("更新于 \(workflow.lastModified)")
                    .font(.system(size: 12))
                    .foregroundColor(Color.fmText3)
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 12)
        }
        .background(Color.white)
        .cornerRadius(8)
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .stroke(Color.fmBorder, lineWidth: 1)
        )
        .shadow(color: Color.black.opacity(0.03), radius: 2, x: 0, y: 1)
    }
}

// MARK: - Complexity Badge
struct ComplexityBadge: View {
    let complexity: String

    var color: Color {
        switch complexity {
        case "简单": return .green
        case "中等": return .orange
        case "复杂": return .red
        default: return .gray
        }
    }

    var body: some View {
        Text(complexity)
            .font(.system(size: 12))
            .foregroundColor(color)
            .padding(.horizontal, 8)
            .padding(.vertical, 3)
            .background(color.opacity(0.1))
            .cornerRadius(4)
    }
}

// MARK: - Workflow Metric Item
struct WorkflowMetricItem: View {
    let icon: String
    let label: String
    let value: String

    var body: some View {
        HStack(spacing: 6) {
            Image(systemName: icon)
                .font(.system(size: 12))
                .foregroundColor(Color.fmText3)
            VStack(alignment: .leading, spacing: 2) {
                Text(label)
                    .font(.system(size: 11))
                    .foregroundColor(Color.fmText3)
                Text(value)
                    .font(.system(size: 13, weight: .medium))
                    .foregroundColor(Color.fmText)
            }
        }
    }
}

// MARK: - Workflow Detail Sheet
struct WorkflowDetailSheet: View {
    let workflow: WorkflowTemplate
    @Environment(\.dismiss) var dismiss

    var body: some View {
        VStack(spacing: 0) {
            // Header
            HStack {
                HStack(spacing: 12) {
                    Image(systemName: workflow.icon)
                        .font(.system(size: 28))
                        .foregroundColor(.blue)
                        .frame(width: 48, height: 48)
                        .background(Color.blue.opacity(0.1))
                        .cornerRadius(8)

                    VStack(alignment: .leading, spacing: 4) {
                        HStack(spacing: 8) {
                            Text(workflow.name)
                                .font(.system(size: 18, weight: .semibold))
                                .foregroundColor(Color.fmText)

                            if workflow.isFavorite {
                                Image(systemName: "star.fill")
                                    .font(.system(size: 13))
                                    .foregroundColor(.orange)
                            }
                        }

                        HStack(spacing: 8) {
                            Text(workflow.category)
                                .font(.system(size: 12))
                                .foregroundColor(.blue)
                                .padding(.horizontal, 8)
                                .padding(.vertical, 3)
                                .background(Color.blue.opacity(0.1))
                                .cornerRadius(4)

                            ComplexityBadge(complexity: workflow.complexity)

                            Text("·")
                                .foregroundColor(Color.fmText3)

                            HStack(spacing: 4) {
                                Image(systemName: "star.fill")
                                    .font(.system(size: 11))
                                    .foregroundColor(.orange)
                                Text(String(format: "%.1f", workflow.rating))
                                    .font(.system(size: 12))
                                    .foregroundColor(Color.fmText2)
                            }

                            Text("·")
                                .foregroundColor(Color.fmText3)

                            Text("\(workflow.usageCount)次使用")
                                .font(.system(size: 12))
                                .foregroundColor(Color.fmText2)
                        }
                    }
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
            .padding(20)
            .background(Color.white)

            Divider()

            // Content
            ScrollView {
                VStack(alignment: .leading, spacing: 24) {
                    // Description
                    WorkflowSection(icon: "doc.text", title: "工作流说明") {
                        Text(workflow.description)
                            .font(.system(size: 14))
                            .foregroundColor(Color.fmText)
                            .lineSpacing(4)
                    }

                    // Components
                    WorkflowSection(icon: "list.number", title: "流程步骤") {
                        VStack(spacing: 12) {
                            ForEach(workflow.components) { component in
                                WorkflowComponentCard(component: component)
                            }
                        }
                    }

                    // Input Requirements
                    WorkflowSection(icon: "arrow.down.circle", title: "输入要求") {
                        VStack(alignment: .leading, spacing: 8) {
                            ForEach(workflow.inputRequirements, id: \.self) { requirement in
                                HStack(spacing: 8) {
                                    Circle()
                                        .fill(Color.blue)
                                        .frame(width: 6, height: 6)
                                    Text(requirement)
                                        .font(.system(size: 14))
                                        .foregroundColor(Color.fmText)
                                }
                            }
                        }
                    }

                    // Output Description
                    WorkflowSection(icon: "arrow.up.circle", title: "输出内容") {
                        Text(workflow.outputDescription)
                            .font(.system(size: 14))
                            .foregroundColor(Color.fmText)
                            .lineSpacing(4)
                    }

                    // Time & Complexity
                    WorkflowSection(icon: "info.circle", title: "其他信息") {
                        VStack(spacing: 12) {
                            InfoRow(label: "预计用时", value: workflow.estimatedTime)
                            InfoRow(label: "复杂度", value: workflow.complexity)
                            InfoRow(label: "创建者", value: workflow.createdBy)
                            InfoRow(label: "创建时间", value: workflow.createdAt)
                            InfoRow(label: "最近修改", value: workflow.lastModified)
                            InfoRow(label: "公开范围", value: workflow.isPublic ? "公开" : "私有")
                        }
                    }

                    // Tags
                    WorkflowSection(icon: "tag", title: "标签") {
                        FlowLayout(spacing: 8) {
                            ForEach(workflow.tags, id: \.self) { tag in
                                Text(tag)
                                    .font(.system(size: 13))
                                    .foregroundColor(Color.fmText2)
                                    .padding(.horizontal, 12)
                                    .padding(.vertical, 6)
                                    .background(Color.fmBg)
                                    .cornerRadius(6)
                            }
                        }
                    }
                }
                .padding(20)
            }

            Divider()

            // Footer buttons
            HStack(spacing: 12) {
                Button(action: {}) {
                    HStack(spacing: 6) {
                        Image(systemName: workflow.isFavorite ? "star.fill" : "star")
                            .font(.system(size: 13))
                        Text(workflow.isFavorite ? "取消收藏" : "收藏")
                            .font(.system(size: 14))
                    }
                    .foregroundColor(Color.fmText2)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 10)
                    .background(Color.white)
                    .cornerRadius(8)
                    .overlay(
                        RoundedRectangle(cornerRadius: 8)
                            .stroke(Color.fmBorder, lineWidth: 1)
                    )
                }
                .buttonStyle(PlainButtonStyle())

                Button(action: {}) {
                    HStack(spacing: 6) {
                        Image(systemName: "square.and.arrow.up")
                            .font(.system(size: 13))
                        Text("分享")
                            .font(.system(size: 14))
                    }
                    .foregroundColor(Color.fmText2)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 10)
                    .background(Color.white)
                    .cornerRadius(8)
                    .overlay(
                        RoundedRectangle(cornerRadius: 8)
                            .stroke(Color.fmBorder, lineWidth: 1)
                    )
                }
                .buttonStyle(PlainButtonStyle())

                Button(action: {}) {
                    HStack(spacing: 6) {
                        Image(systemName: "doc.on.doc")
                            .font(.system(size: 13))
                        Text("复制工作流")
                            .font(.system(size: 14))
                    }
                    .foregroundColor(Color.fmText2)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 10)
                    .background(Color.white)
                    .cornerRadius(8)
                    .overlay(
                        RoundedRectangle(cornerRadius: 8)
                            .stroke(Color.fmBorder, lineWidth: 1)
                    )
                }
                .buttonStyle(PlainButtonStyle())

                Button(action: {}) {
                    HStack(spacing: 6) {
                        Image(systemName: "play.fill")
                            .font(.system(size: 13))
                        Text("使用工作流")
                            .font(.system(size: 14, weight: .medium))
                    }
                    .foregroundColor(.white)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 10)
                    .background(Color.blue)
                    .cornerRadius(8)
                }
                .buttonStyle(PlainButtonStyle())
            }
            .padding(20)
            .background(Color.white)
        }
        .frame(width: 1000, height: 800)
        .background(Color(red: 0.98, green: 0.98, blue: 0.98))
    }
}

// MARK: - Workflow Section
struct WorkflowSection<Content: View>: View {
    let icon: String
    let title: String
    @ViewBuilder let content: Content

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(spacing: 8) {
                Image(systemName: icon)
                    .font(.system(size: 14))
                    .foregroundColor(.blue)
                Text(title)
                    .font(.system(size: 15, weight: .semibold))
                    .foregroundColor(Color.fmText)
            }

            content
        }
    }
}

// MARK: - Workflow Component Card
struct WorkflowComponentCard: View {
    let component: WorkflowTemplate.WorkflowComponent

    var typeColor: Color {
        switch component.type {
        case "数据导入": return .blue
        case "AI分析": return .purple
        case "可视化": return .green
        case "报告生成": return .orange
        default: return .gray
        }
    }

    var typeIcon: String {
        switch component.type {
        case "数据导入": return "arrow.down.doc"
        case "AI分析": return "brain"
        case "可视化": return "chart.bar"
        case "报告生成": return "doc.text"
        default: return "gearshape"
        }
    }

    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            // Step number
            ZStack {
                Circle()
                    .fill(typeColor.opacity(0.1))
                    .frame(width: 32, height: 32)
                Text("\(component.stepNumber)")
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundColor(typeColor)
            }

            VStack(alignment: .leading, spacing: 8) {
                HStack(spacing: 8) {
                    Text(component.name)
                        .font(.system(size: 14, weight: .medium))
                        .foregroundColor(Color.fmText)

                    HStack(spacing: 4) {
                        Image(systemName: typeIcon)
                            .font(.system(size: 10))
                        Text(component.type)
                            .font(.system(size: 11))
                    }
                    .foregroundColor(typeColor)
                    .padding(.horizontal, 6)
                    .padding(.vertical, 3)
                    .background(typeColor.opacity(0.1))
                    .cornerRadius(4)
                }

                Text(component.description)
                    .font(.system(size: 13))
                    .foregroundColor(Color.fmText2)
                    .lineSpacing(3)

                HStack(spacing: 16) {
                    HStack(spacing: 4) {
                        Image(systemName: "gearshape")
                            .font(.system(size: 11))
                            .foregroundColor(Color.fmText3)
                        Text(component.configuration)
                            .font(.system(size: 12))
                            .foregroundColor(Color.fmText3)
                    }

                    HStack(spacing: 4) {
                        Image(systemName: "clock")
                            .font(.system(size: 11))
                            .foregroundColor(Color.fmText3)
                        Text(component.estimatedDuration)
                            .font(.system(size: 12))
                            .foregroundColor(Color.fmText3)
                    }
                }
            }

            Spacer()
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
