import SwiftUI

// MARK: - Model Card

struct ModelCard: View {
    let model: AIModel
    let onTap: () -> Void
    @State private var isHovered = false

    var body: some View {
        Button(action: onTap) {
            VStack(alignment: .leading, spacing: 0) {
                // Header
                HStack(spacing: 12) {
                    // Icon
                    ZStack {
                        RoundedRectangle(cornerRadius: 12)
                            .fill(Color(hex: model.color).opacity(0.12))
                            .frame(width: 56, height: 56)

                        Image(systemName: model.icon)
                            .font(.system(size: 24))
                            .foregroundColor(Color(hex: model.color))
                    }

                    VStack(alignment: .leading, spacing: 4) {
                        HStack(spacing: 8) {
                            Text(model.name)
                                .font(.system(size: 15, weight: .semibold))
                                .foregroundColor(Color.fmText)

                            if model.isActive {
                                HStack(spacing: 4) {
                                    Circle()
                                        .fill(Color.green)
                                        .frame(width: 6, height: 6)
                                    Text("使用中")
                                        .font(.system(size: 10, weight: .medium))
                                        .foregroundColor(.green)
                                }
                                .padding(.horizontal, 6)
                                .padding(.vertical, 3)
                                .background(Color.green.opacity(0.1))
                                .cornerRadius(4)
                            }
                        }

                        Text(model.provider)
                            .font(.system(size: 12))
                            .foregroundColor(Color.fmText3)
                    }

                    Spacer()

                    // Status Badge
                    if model.isConfigured {
                        Image(systemName: "checkmark.circle.fill")
                            .font(.system(size: 18))
                            .foregroundColor(.green)
                    } else {
                        Image(systemName: "exclamationmark.circle")
                            .font(.system(size: 18))
                            .foregroundColor(.orange)
                    }
                }
                .padding(16)

                Divider()

                // Description
                Text(model.description)
                    .font(.system(size: 13))
                    .foregroundColor(Color.fmText2)
                    .lineLimit(2)
                    .padding(.horizontal, 16)
                    .padding(.top, 12)

                // Capabilities
                HStack(spacing: 6) {
                    ForEach(model.capabilities, id: \.self) { capability in
                        HStack(spacing: 4) {
                            Image(systemName: capabilityIcon(capability))
                                .font(.system(size: 9))
                            Text(capabilityLabel(capability))
                                .font(.system(size: 11))
                        }
                        .foregroundColor(Color.fmText3)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(Color(hex: "F5F5F5"))
                        .cornerRadius(4)
                    }
                }
                .padding(.horizontal, 16)
                .padding(.top, 8)

                // Stats
                HStack(spacing: 16) {
                    ModelStatItem(
                        icon: "text.alignleft",
                        label: "上下文",
                        value: formatContextWindow(model.contextWindow)
                    )

                    Divider()
                        .frame(height: 24)

                    ModelStatItem(
                        icon: "speedometer",
                        label: "延迟",
                        value: model.performance.totalCalls > 0 ? String(format: "%.1fs", model.performance.avgLatency) : "-"
                    )

                    Divider()
                        .frame(height: 24)

                    ModelStatItem(
                        icon: "checkmark.circle",
                        label: "成功率",
                        value: model.performance.totalCalls > 0 ? String(format: "%.1f%%", model.performance.successRate) : "-"
                    )
                }
                .padding(.horizontal, 16)
                .padding(.vertical, 12)

                Divider()

                // Footer
                HStack {
                    HStack(spacing: 6) {
                        Image(systemName: "dollarsign.circle")
                            .font(.system(size: 11))
                            .foregroundColor(Color.fmText3)
                        Text("输入: $\(String(format: "%.4f", model.pricing.inputPrice))")
                            .font(.system(size: 11))
                            .foregroundColor(Color.fmText3)
                        Text("输出: $\(String(format: "%.4f", model.pricing.outputPrice))")
                            .font(.system(size: 11))
                            .foregroundColor(Color.fmText3)
                        Text("/ \(model.pricing.unit)")
                            .font(.system(size: 11))
                            .foregroundColor(Color.fmText3)
                    }

                    Spacer()

                    Image(systemName: "chevron.right")
                        .font(.system(size: 12))
                        .foregroundColor(Color.fmText3)
                }
                .padding(.horizontal, 16)
                .padding(.vertical, 12)
            }
            .background(isHovered ? Color(hex: "FAFAFA") : Color.white)
            .cornerRadius(12)
            .overlay(
                RoundedRectangle(cornerRadius: 12)
                    .stroke(isHovered ? Color.blue : Color.fmBorder, lineWidth: 1)
            )
        }
        .buttonStyle(PlainButtonStyle())
        .onHover { hovering in
            isHovered = hovering
        }
    }

    private func capabilityIcon(_ capability: String) -> String {
        switch capability {
        case "chat": return "bubble.left.and.bubble.right"
        case "embedding": return "function"
        case "vision": return "eye"
        case "function_calling": return "gearshape"
        default: return "circle"
        }
    }

    private func capabilityLabel(_ capability: String) -> String {
        switch capability {
        case "chat": return "对话"
        case "embedding": return "嵌入"
        case "vision": return "视觉"
        case "function_calling": return "函数调用"
        default: return capability
        }
    }

    private func formatContextWindow(_ tokens: Int) -> String {
        if tokens >= 1000 {
            return "\(tokens / 1000)K"
        }
        return "\(tokens)"
    }
}

// MARK: - Model Stat Item

struct ModelStatItem: View {
    let icon: String
    let label: String
    let value: String

    var body: some View {
        VStack(spacing: 4) {
            HStack(spacing: 4) {
                Image(systemName: icon)
                    .font(.system(size: 10))
                    .foregroundColor(Color.fmText3)
                Text(label)
                    .font(.system(size: 11))
                    .foregroundColor(Color.fmText3)
            }
            Text(value)
                .font(.system(size: 13, weight: .medium))
                .foregroundColor(Color.fmText)
        }
        .frame(maxWidth: .infinity)
    }
}

// MARK: - Config Card

struct ConfigCard: View {
    let config: ModelConfig
    let onTap: () -> Void
    @State private var isHovered = false

    var body: some View {
        Button(action: onTap) {
            HStack(spacing: 16) {
                // Icon
                ZStack {
                    RoundedRectangle(cornerRadius: 10)
                        .fill(Color.blue.opacity(0.12))
                        .frame(width: 48, height: 48)

                    Image(systemName: useCaseIcon(config.useCase))
                        .font(.system(size: 20))
                        .foregroundColor(.blue)
                }

                // Content
                VStack(alignment: .leading, spacing: 6) {
                    HStack(spacing: 8) {
                        Text(config.name)
                            .font(.system(size: 14, weight: .semibold))
                            .foregroundColor(Color.fmText)

                        Text(useCaseLabel(config.useCase))
                            .font(.system(size: 11))
                            .foregroundColor(.blue)
                            .padding(.horizontal, 8)
                            .padding(.vertical, 3)
                            .background(Color.blue.opacity(0.1))
                            .cornerRadius(4)
                    }

                    HStack(spacing: 12) {
                        HStack(spacing: 4) {
                            Image(systemName: "thermometer")
                                .font(.system(size: 10))
                            Text("Temperature: \(String(format: "%.1f", config.temperature))")
                                .font(.system(size: 11))
                        }
                        .foregroundColor(Color.fmText3)

                        HStack(spacing: 4) {
                            Image(systemName: "text.alignleft")
                                .font(.system(size: 10))
                            Text("Max: \(config.maxTokens)")
                                .font(.system(size: 11))
                        }
                        .foregroundColor(Color.fmText3)

                        HStack(spacing: 4) {
                            Image(systemName: "clock")
                                .font(.system(size: 10))
                            Text(formatTimestamp(config.lastModified))
                                .font(.system(size: 11))
                        }
                        .foregroundColor(Color.fmText3)
                    }
                }

                Spacer()

                Image(systemName: "chevron.right")
                    .font(.system(size: 12))
                    .foregroundColor(Color.fmText3)
            }
            .padding(16)
            .background(isHovered ? Color(hex: "FAFAFA") : Color.white)
            .cornerRadius(12)
            .overlay(
                RoundedRectangle(cornerRadius: 12)
                    .stroke(isHovered ? Color.blue : Color.fmBorder, lineWidth: 1)
            )
        }
        .buttonStyle(PlainButtonStyle())
        .onHover { hovering in
            isHovered = hovering
        }
    }

    private func useCaseIcon(_ useCase: String) -> String {
        switch useCase {
        case "chat": return "bubble.left.and.bubble.right"
        case "keyword": return "tag"
        case "summary": return "doc.text"
        case "analysis": return "chart.bar.doc.horizontal"
        default: return "slider.horizontal.3"
        }
    }

    private func useCaseLabel(_ useCase: String) -> String {
        switch useCase {
        case "chat": return "对话"
        case "keyword": return "关键词"
        case "summary": return "摘要"
        case "analysis": return "分析"
        default: return useCase
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

// MARK: - Usage Summary Card

struct UsageSummaryCard: View {
    let title: String
    let value: String
    let subtitle: String
    let icon: String
    let color: Color

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                ZStack {
                    Circle()
                        .fill(color.opacity(0.12))
                        .frame(width: 40, height: 40)

                    Image(systemName: icon)
                        .font(.system(size: 18))
                        .foregroundColor(color)
                }

                Spacer()
            }

            VStack(alignment: .leading, spacing: 4) {
                Text(value)
                    .font(.system(size: 24, weight: .bold))
                    .foregroundColor(Color.fmText)

                Text(title)
                    .font(.system(size: 13))
                    .foregroundColor(Color.fmText2)

                Text(subtitle)
                    .font(.system(size: 11))
                    .foregroundColor(Color.fmText3)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(20)
        .background(Color.white)
        .cornerRadius(12)
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(Color.fmBorder, lineWidth: 1)
        )
    }
}

// MARK: - Model Detail Sheet

struct ModelDetailSheet: View {
    let model: AIModel
    let onClose: () -> Void

    var body: some View {
        VStack(spacing: 0) {
            // Header
            HStack(spacing: 12) {
                ZStack {
                    RoundedRectangle(cornerRadius: 12)
                        .fill(Color(hex: model.color).opacity(0.12))
                        .frame(width: 48, height: 48)

                    Image(systemName: model.icon)
                        .font(.system(size: 20))
                        .foregroundColor(Color(hex: model.color))
                }

                VStack(alignment: .leading, spacing: 2) {
                    Text(model.name)
                        .font(.system(size: 17, weight: .semibold))
                        .foregroundColor(Color.fmText)

                    Text(model.provider)
                        .font(.system(size: 13))
                        .foregroundColor(Color.fmText3)
                }

                Spacer()

                Button(action: onClose) {
                    Image(systemName: "xmark")
                        .font(.system(size: 14))
                        .foregroundColor(Color.fmText3)
                        .frame(width: 28, height: 28)
                        .background(Color(hex: "F5F5F5"))
                        .cornerRadius(6)
                }
                .buttonStyle(PlainButtonStyle())
            }
            .padding(20)
            .background(Color(hex: "FAFAFA"))

            Divider()

            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    // Model Info Section
                    DetailSection(title: "基本信息", icon: "info.circle") {
                        VStack(spacing: 12) {
                            InfoRow(label: "模型名称", value: model.name)
                            InfoRow(label: "提供商", value: model.provider)
                            InfoRow(label: "模型 ID", value: model.modelId)
                            InfoRow(label: "状态", value: model.isActive ? "使用中" : (model.isConfigured ? "已配置" : "未配置"))
                        }
                    }

                    // Description Section
                    DetailSection(title: "模型描述", icon: "doc.text") {
                        Text(model.description)
                            .font(.system(size: 13))
                            .foregroundColor(Color.fmText2)
                            .lineSpacing(4)
                    }

                    // Capabilities Section
                    DetailSection(title: "支持能力", icon: "star") {
                        HStack(spacing: 8) {
                            ForEach(model.capabilities, id: \.self) { capability in
                                HStack(spacing: 6) {
                                    Image(systemName: capabilityIcon(capability))
                                        .font(.system(size: 11))
                                    Text(capabilityLabel(capability))
                                        .font(.system(size: 12))
                                }
                                .foregroundColor(.blue)
                                .padding(.horizontal, 12)
                                .padding(.vertical, 6)
                                .background(Color.blue.opacity(0.1))
                                .cornerRadius(6)
                            }
                        }
                    }

                    // Technical Specs Section
                    DetailSection(title: "技术参数", icon: "cpu") {
                        VStack(spacing: 12) {
                            InfoRow(label: "上下文窗口", value: formatContextWindow(model.contextWindow))
                            InfoRow(label: "最大输出", value: "\(model.maxOutput) tokens")
                        }
                    }

                    // Pricing Section
                    DetailSection(title: "定价信息", icon: "dollarsign.circle") {
                        VStack(spacing: 12) {
                            InfoRow(label: "输入价格", value: "$\(String(format: "%.4f", model.pricing.inputPrice)) / \(model.pricing.unit)")
                            InfoRow(label: "输出价格", value: "$\(String(format: "%.4f", model.pricing.outputPrice)) / \(model.pricing.unit)")
                        }
                    }

                    // Performance Section
                    if model.performance.totalCalls > 0 {
                        DetailSection(title: "性能指标", icon: "chart.bar") {
                            VStack(spacing: 12) {
                                InfoRow(label: "平均延迟", value: String(format: "%.2f 秒", model.performance.avgLatency))
                                InfoRow(label: "成功率", value: String(format: "%.1f%%", model.performance.successRate))
                                InfoRow(label: "总调用次数", value: formatNumber(model.performance.totalCalls))
                                InfoRow(label: "总 Tokens", value: formatNumber(model.performance.totalTokens))
                            }
                        }
                    }
                }
                .padding(20)
            }

            Divider()

            // Footer
            HStack {
                Text("FieldMind v1.0")
                    .font(.system(size: 11))
                    .foregroundColor(Color.fmText3)

                Spacer()

                if !model.isConfigured {
                    Button(action: {}) {
                        Text("配置")
                            .font(.system(size: 13, weight: .medium))
                            .foregroundColor(Color.fmText2)
                            .padding(.horizontal, 16)
                            .padding(.vertical, 8)
                            .background(Color(hex: "F5F5F5"))
                            .cornerRadius(6)
                    }
                    .buttonStyle(PlainButtonStyle())
                }

                Button(action: {}) {
                    Text(model.isActive ? "当前使用" : "切换到此模型")
                        .font(.system(size: 13, weight: .medium))
                        .foregroundColor(.white)
                        .padding(.horizontal, 16)
                        .padding(.vertical, 8)
                        .background(model.isActive ? Color.gray : Color.blue)
                        .cornerRadius(6)
                }
                .buttonStyle(PlainButtonStyle())
                .disabled(model.isActive || !model.isConfigured)
            }
            .padding(20)
            .background(Color(hex: "FAFAFA"))
        }
        .frame(width: 600, height: 600)
    }

    private func capabilityIcon(_ capability: String) -> String {
        switch capability {
        case "chat": return "bubble.left.and.bubble.right"
        case "embedding": return "function"
        case "vision": return "eye"
        case "function_calling": return "gearshape"
        default: return "circle"
        }
    }

    private func capabilityLabel(_ capability: String) -> String {
        switch capability {
        case "chat": return "对话"
        case "embedding": return "嵌入"
        case "vision": return "视觉"
        case "function_calling": return "函数调用"
        default: return capability
        }
    }

    private func formatContextWindow(_ tokens: Int) -> String {
        if tokens >= 1000 {
            return "\(tokens / 1000),000 tokens"
        }
        return "\(tokens) tokens"
    }

    private func formatNumber(_ number: Int) -> String {
        let formatter = NumberFormatter()
        formatter.numberStyle = .decimal
        formatter.groupingSeparator = ","
        return formatter.string(from: NSNumber(value: number)) ?? "\(number)"
    }
}

// MARK: - Config Detail Sheet

struct ConfigDetailSheet: View {
    let config: ModelConfig
    let onClose: () -> Void

    var body: some View {
        VStack(spacing: 0) {
            // Header
            HStack(spacing: 12) {
                ZStack {
                    RoundedRectangle(cornerRadius: 12)
                        .fill(Color.blue.opacity(0.12))
                        .frame(width: 48, height: 48)

                    Image(systemName: useCaseIcon(config.useCase))
                        .font(.system(size: 20))
                        .foregroundColor(.blue)
                }

                VStack(alignment: .leading, spacing: 2) {
                    Text("配置详情")
                        .font(.system(size: 17, weight: .semibold))
                        .foregroundColor(Color.fmText)

                    Text(config.name)
                        .font(.system(size: 13))
                        .foregroundColor(Color.fmText3)
                }

                Spacer()

                Button(action: onClose) {
                    Image(systemName: "xmark")
                        .font(.system(size: 14))
                        .foregroundColor(Color.fmText3)
                        .frame(width: 28, height: 28)
                        .background(Color(hex: "F5F5F5"))
                        .cornerRadius(6)
                }
                .buttonStyle(PlainButtonStyle())
            }
            .padding(20)
            .background(Color(hex: "FAFAFA"))

            Divider()

            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    // Basic Info Section
                    DetailSection(title: "基本信息", icon: "info.circle") {
                        VStack(spacing: 12) {
                            InfoRow(label: "配置名称", value: config.name)
                            InfoRow(label: "用途", value: useCaseLabel(config.useCase))
                            InfoRow(label: "最后修改", value: formatFullTimestamp(config.lastModified))
                        }
                    }

                    // Parameters Section
                    DetailSection(title: "模型参数", icon: "slider.horizontal.3") {
                        VStack(spacing: 12) {
                            InfoRow(label: "Temperature", value: String(format: "%.2f", config.temperature))
                            InfoRow(label: "Max Tokens", value: "\(config.maxTokens)")
                            InfoRow(label: "Top P", value: String(format: "%.2f", config.topP))
                            InfoRow(label: "Frequency Penalty", value: String(format: "%.2f", config.frequencyPenalty))
                            InfoRow(label: "Presence Penalty", value: String(format: "%.2f", config.presencePenalty))
                        }
                    }

                    // System Prompt Section
                    if let prompt = config.systemPrompt, !prompt.isEmpty {
                        DetailSection(title: "系统提示词", icon: "text.bubble") {
                            Text(prompt)
                                .font(.system(size: 13))
                                .foregroundColor(Color.fmText2)
                                .padding(12)
                                .frame(maxWidth: .infinity, alignment: .leading)
                                .background(Color(hex: "F5F5F5"))
                                .cornerRadius(8)
                        }
                    }
                }
                .padding(20)
            }

            Divider()

            // Footer
            HStack {
                Text("FieldMind v1.0")
                    .font(.system(size: 11))
                    .foregroundColor(Color.fmText3)

                Spacer()

                Button(action: {}) {
                    Text("编辑")
                        .font(.system(size: 13, weight: .medium))
                        .foregroundColor(Color.fmText2)
                        .padding(.horizontal, 16)
                        .padding(.vertical, 8)
                        .background(Color(hex: "F5F5F5"))
                        .cornerRadius(6)
                }
                .buttonStyle(PlainButtonStyle())

                Button(action: {}) {
                    Text("应用配置")
                        .font(.system(size: 13, weight: .medium))
                        .foregroundColor(.white)
                        .padding(.horizontal, 16)
                        .padding(.vertical, 8)
                        .background(Color.blue)
                        .cornerRadius(6)
                }
                .buttonStyle(PlainButtonStyle())
            }
            .padding(20)
            .background(Color(hex: "FAFAFA"))
        }
        .frame(width: 550, height: 550)
    }

    private func useCaseIcon(_ useCase: String) -> String {
        switch useCase {
        case "chat": return "bubble.left.and.bubble.right"
        case "keyword": return "tag"
        case "summary": return "doc.text"
        case "analysis": return "chart.bar.doc.horizontal"
        default: return "slider.horizontal.3"
        }
    }

    private func useCaseLabel(_ useCase: String) -> String {
        switch useCase {
        case "chat": return "AI 对话"
        case "keyword": return "关键词提取"
        case "summary": return "文本摘要"
        case "analysis": return "深度分析"
        default: return useCase
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

// MARK: - Add Model Sheet

struct AddModelSheet: View {
    let onClose: () -> Void

    var body: some View {
        VStack(spacing: 0) {
            // Header
            HStack {
                Text("添加模型")
                    .font(.system(size: 17, weight: .semibold))
                    .foregroundColor(Color.fmText)

                Spacer()

                Button(action: onClose) {
                    Image(systemName: "xmark")
                        .font(.system(size: 14))
                        .foregroundColor(Color.fmText3)
                        .frame(width: 28, height: 28)
                        .background(Color(hex: "F5F5F5"))
                        .cornerRadius(6)
                }
                .buttonStyle(PlainButtonStyle())
            }
            .padding(20)
            .background(Color(hex: "FAFAFA"))

            Divider()

            VStack(spacing: 16) {
                Image(systemName: "brain")
                    .font(.system(size: 64))
                    .foregroundColor(Color.fmText3.opacity(0.3))

                Text("添加模型功能")
                    .font(.system(size: 16, weight: .medium))
                    .foregroundColor(Color.fmText)

                Text("此功能将允许您添加自定义模型配置")
                    .font(.system(size: 13))
                    .foregroundColor(Color.fmText3)
                    .multilineTextAlignment(.center)
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)

            Divider()

            HStack {
                Spacer()

                Button(action: onClose) {
                    Text("关闭")
                        .font(.system(size: 13, weight: .medium))
                        .foregroundColor(.white)
                        .padding(.horizontal, 20)
                        .padding(.vertical, 8)
                        .background(Color.blue)
                        .cornerRadius(6)
                }
                .buttonStyle(PlainButtonStyle())
            }
            .padding(20)
            .background(Color(hex: "FAFAFA"))
        }
        .frame(width: 500, height: 400)
    }
}
