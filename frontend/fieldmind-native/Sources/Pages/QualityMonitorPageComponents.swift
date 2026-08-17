import SwiftUI

// MARK: - Quality Metric Card
struct QualityMetricCard: View {
    let metric: QualityMetric
    let isSelected: Bool
    let onTap: () -> Void

    var body: some View {
        Button(action: onTap) {
            VStack(alignment: .leading, spacing: 10) {
                HStack {
                    Image(systemName: metric.icon)
                        .font(.system(size: 18))
                        .foregroundColor(statusColor)
                        .frame(width: 32, height: 32)
                        .background(statusColor.opacity(0.1))
                        .cornerRadius(8)

                    Spacer()

                    // 变化指示
                    HStack(spacing: 2) {
                        Image(systemName: metric.change >= 0 ? "arrow.up" : "arrow.down")
                            .font(.system(size: 9, weight: .bold))
                        Text(String(format: "%.1f%%", abs(metric.change)))
                            .font(.system(size: 10, weight: .medium))
                    }
                    .foregroundColor(metric.change >= 0 ? .fmGreen : .fmOrange)
                    .padding(.horizontal, 6)
                    .padding(.vertical, 3)
                    .background((metric.change >= 0 ? Color.fmGreen : Color.fmOrange).opacity(0.1))
                    .cornerRadius(10)
                }

                VStack(alignment: .leading, spacing: 4) {
                    Text(metric.name)
                        .font(.system(size: 12, weight: .medium))
                        .foregroundColor(.fmText)
                        .lineLimit(1)

                    HStack(alignment: .firstTextBaseline, spacing: 2) {
                        Text(String(format: "%.1f", metric.value))
                            .font(.system(size: 24, weight: .bold))
                            .foregroundColor(statusColor)

                        Text("/ 100")
                            .font(.system(size: 11))
                            .foregroundColor(.fmText3)
                    }

                    // 进度条
                    GeometryReader { geometry in
                        ZStack(alignment: .leading) {
                            RoundedRectangle(cornerRadius: 2)
                                .fill(Color.fmBorder)
                                .frame(height: 4)

                            RoundedRectangle(cornerRadius: 2)
                                .fill(statusColor)
                                .frame(width: geometry.size.width * CGFloat(metric.value / 100.0), height: 4)
                        }
                    }
                    .frame(height: 4)

                    Text(metric.description)
                        .font(.system(size: 10))
                        .foregroundColor(.fmText3)
                        .lineLimit(2)
                        .fixedSize(horizontal: false, vertical: true)
                }
            }
            .padding(14)
            .background(isSelected ? Color.white : Color.white)
            .cornerRadius(10)
            .overlay(
                RoundedRectangle(cornerRadius: 10)
                    .stroke(isSelected ? statusColor : Color.fmBorder, lineWidth: isSelected ? 2 : 1)
            )
            .shadow(color: isSelected ? statusColor.opacity(0.2) : Color.black.opacity(0.02), radius: isSelected ? 8 : 2, x: 0, y: isSelected ? 4 : 1)
        }
        .buttonStyle(PlainButtonStyle())
    }

    private var statusColor: Color {
        switch metric.status {
        case "excellent": return .fmGreen
        case "good": return .fmBlue
        case "warning": return .fmOrange
        case "critical": return Color(hex: "E74C3C")
        default: return .gray
        }
    }
}

// MARK: - Quality Issue Card
struct QualityIssueCard: View {
    let issue: QualityIssue
    let onTap: () -> Void

    @State private var isHovered = false

    var body: some View {
        Button(action: onTap) {
            HStack(spacing: 12) {
                // 左侧：类型图标
                ZStack {
                    Circle()
                        .fill(typeColor.opacity(0.1))
                        .frame(width: 44, height: 44)

                    Image(systemName: typeIcon)
                        .font(.system(size: 18))
                        .foregroundColor(typeColor)
                }

                // 中间：内容
                VStack(alignment: .leading, spacing: 6) {
                    HStack(spacing: 8) {
                        Text(issue.title)
                            .font(.system(size: 13, weight: .medium))
                            .foregroundColor(.fmText)
                            .lineLimit(1)

                        Spacer()

                        // 严重性标签
                        Text(severityLabel)
                            .font(.system(size: 10, weight: .medium))
                            .foregroundColor(.white)
                            .padding(.horizontal, 6)
                            .padding(.vertical, 2)
                            .background(severityColor)
                            .cornerRadius(4)

                        // 状态标签
                        Text(statusLabel)
                            .font(.system(size: 10, weight: .medium))
                            .foregroundColor(statusColor)
                            .padding(.horizontal, 6)
                            .padding(.vertical, 2)
                            .background(statusColor.opacity(0.1))
                            .cornerRadius(4)
                    }

                    Text(issue.description)
                        .font(.system(size: 11))
                        .foregroundColor(.fmText2)
                        .lineLimit(2)

                    HStack(spacing: 12) {
                        if let projectName = issue.projectName {
                            HStack(spacing: 4) {
                                Image(systemName: "folder")
                                    .font(.system(size: 9))
                                Text(projectName)
                                    .font(.system(size: 10))
                            }
                            .foregroundColor(.fmText3)
                        }

                        HStack(spacing: 4) {
                            Image(systemName: "exclamationmark.circle")
                                .font(.system(size: 9))
                            Text("\(issue.affectedItems) 项受影响")
                                .font(.system(size: 10))
                        }
                        .foregroundColor(.fmText3)

                        HStack(spacing: 4) {
                            Image(systemName: "clock")
                                .font(.system(size: 9))
                            Text(formatTimestamp(issue.timestamp))
                                .font(.system(size: 10))
                        }
                        .foregroundColor(.fmText3)

                        Spacer()

                        Image(systemName: "chevron.right")
                            .font(.system(size: 10))
                            .foregroundColor(.fmText3)
                    }
                }
            }
            .padding(12)
            .background(isHovered ? Color.fmBg : Color.white)
            .cornerRadius(8)
            .overlay(
                RoundedRectangle(cornerRadius: 8)
                    .stroke(isHovered ? typeColor.opacity(0.3) : Color.fmBorder, lineWidth: 1)
            )
        }
        .buttonStyle(PlainButtonStyle())
        .onHover { hovering in
            withAnimation(.easeInOut(duration: 0.15)) {
                isHovered = hovering
            }
        }
    }

    private var typeIcon: String {
        switch issue.type {
        case "error": return "xmark.circle.fill"
        case "warning": return "exclamationmark.triangle.fill"
        case "info": return "info.circle.fill"
        default: return "questionmark.circle.fill"
        }
    }

    private var typeColor: Color {
        switch issue.type {
        case "error": return Color(hex: "E74C3C")
        case "warning": return .fmOrange
        case "info": return .fmBlue
        default: return .gray
        }
    }

    private var severityLabel: String {
        switch issue.severity {
        case "high": return "严重"
        case "medium": return "中等"
        case "low": return "轻微"
        default: return "未知"
        }
    }

    private var severityColor: Color {
        switch issue.severity {
        case "high": return Color(hex: "E74C3C")
        case "medium": return .fmOrange
        case "low": return Color(hex: "95A5A6")
        default: return .gray
        }
    }

    private var statusLabel: String {
        switch issue.status {
        case "new": return "新问题"
        case "reviewing": return "审核中"
        case "fixing": return "修复中"
        case "resolved": return "已解决"
        default: return "未知"
        }
    }

    private var statusColor: Color {
        switch issue.status {
        case "new": return .fmOrange
        case "reviewing": return .fmBlue
        case "fixing": return .fmPurple
        case "resolved": return .fmGreen
        default: return .gray
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

// MARK: - Quality Check Task Card
struct QualityCheckTaskCard: View {
    let task: QualityCheckTask
    let onTap: () -> Void

    @State private var isHovered = false

    var body: some View {
        Button(action: onTap) {
            HStack(spacing: 12) {
                // 左侧：类别图标
                Image(systemName: categoryIcon)
                    .font(.system(size: 16))
                    .foregroundColor(.fmBlue)
                    .frame(width: 36, height: 36)
                    .background(Color.fmBlue.opacity(0.1))
                    .cornerRadius(8)

                // 中间：内容
                VStack(alignment: .leading, spacing: 6) {
                    HStack(spacing: 8) {
                        Text(task.name)
                            .font(.system(size: 13, weight: .medium))
                            .foregroundColor(.fmText)

                        // 频率标签
                        Text(frequencyLabel)
                            .font(.system(size: 10))
                            .foregroundColor(.fmText3)
                            .padding(.horizontal, 6)
                            .padding(.vertical, 2)
                            .background(Color.fmBg)
                            .cornerRadius(4)

                        Spacer()

                        // 状态指示
                        if task.status == "running" {
                            HStack(spacing: 4) {
                                ProgressView()
                                    .scaleEffect(0.6)
                                    .frame(width: 12, height: 12)
                                Text("运行中")
                                    .font(.system(size: 10))
                            }
                            .foregroundColor(.fmBlue)
                        } else if task.status == "completed" {
                            HStack(spacing: 4) {
                                Image(systemName: "checkmark.circle.fill")
                                    .font(.system(size: 10))
                                Text("已完成")
                                    .font(.system(size: 10))
                            }
                            .foregroundColor(.fmGreen)
                        } else if task.status == "failed" {
                            HStack(spacing: 4) {
                                Image(systemName: "xmark.circle.fill")
                                    .font(.system(size: 10))
                                Text("失败")
                                    .font(.system(size: 10))
                            }
                            .foregroundColor(Color(hex: "E74C3C"))
                        }
                    }

                    Text(task.description)
                        .font(.system(size: 11))
                        .foregroundColor(.fmText2)
                        .lineLimit(1)

                    HStack(spacing: 12) {
                        if let lastRun = task.lastRun {
                            HStack(spacing: 4) {
                                Image(systemName: "clock.arrow.circlepath")
                                    .font(.system(size: 9))
                                Text("上次: \(formatTimestamp(lastRun))")
                                    .font(.system(size: 10))
                            }
                            .foregroundColor(.fmText3)
                        }

                        if task.issuesFound > 0 {
                            HStack(spacing: 4) {
                                Image(systemName: "exclamationmark.triangle")
                                    .font(.system(size: 9))
                                Text("\(task.issuesFound) 个问题")
                                    .font(.system(size: 10))
                            }
                            .foregroundColor(.fmOrange)
                        }

                        if let duration = task.duration {
                            HStack(spacing: 4) {
                                Image(systemName: "timer")
                                    .font(.system(size: 9))
                                Text(duration)
                                    .font(.system(size: 10))
                            }
                            .foregroundColor(.fmText3)
                        }

                        Spacer()
                    }
                }

                // 右侧：操作按钮
                if task.frequency == "manual" || task.status == "idle" {
                    Button(action: { /* 运行任务 */ }) {
                        Image(systemName: "play.circle.fill")
                            .font(.system(size: 20))
                            .foregroundColor(.fmBlue)
                    }
                    .buttonStyle(PlainButtonStyle())
                }
            }
            .padding(12)
            .background(isHovered ? Color.fmBg : Color.white)
            .cornerRadius(8)
            .overlay(
                RoundedRectangle(cornerRadius: 8)
                    .stroke(isHovered ? Color.fmBlue.opacity(0.3) : Color.fmBorder, lineWidth: 1)
            )
        }
        .buttonStyle(PlainButtonStyle())
        .onHover { hovering in
            withAnimation(.easeInOut(duration: 0.15)) {
                isHovered = hovering
            }
        }
    }

    private var categoryIcon: String {
        switch task.category {
        case "ai": return "cpu"
        case "data": return "doc.text"
        case "citation": return "quote.bubble"
        case "graph": return "circle.hexagongrid"
        case "annotation": return "tag"
        default: return "checklist"
        }
    }

    private var frequencyLabel: String {
        switch task.frequency {
        case "daily": return "每日"
        case "weekly": return "每周"
        case "manual": return "手动"
        default: return task.frequency
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

// MARK: - Issue Detail Sheet
struct IssueDetailSheet: View {
    let issue: QualityIssue
    let onClose: () -> Void

    var body: some View {
        VStack(spacing: 0) {
            // 标题栏
            HStack {
                Image(systemName: typeIcon)
                    .font(.system(size: 20))
                    .foregroundColor(typeColor)

                Text("问题详情")
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundColor(.fmText)

                Spacer()

                Button(action: onClose) {
                    Image(systemName: "xmark")
                        .font(.system(size: 12))
                        .foregroundColor(.fmText3)
                        .frame(width: 24, height: 24)
                        .background(Color.fmBg)
                        .cornerRadius(12)
                }
                .buttonStyle(PlainButtonStyle())
            }
            .padding(20)
            .background(Color.fmBg2)

            Divider()

            // 内容区
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    // 基本信息
                    DetailSection(title: "基本信息", icon: "info.circle") {
                        VStack(alignment: .leading, spacing: 12) {
                            InfoRow(label: "标题", value: issue.title)
                            InfoRow(label: "类型", value: typeLabel)
                            InfoRow(label: "类别", value: categoryLabel)
                            InfoRow(label: "严重性", value: severityLabel)
                            InfoRow(label: "状态", value: statusLabel)
                            InfoRow(label: "发现时间", value: formatFullTimestamp(issue.timestamp))
                            if let projectName = issue.projectName {
                                InfoRow(label: "所属项目", value: projectName)
                            }
                            InfoRow(label: "受影响项", value: "\(issue.affectedItems) 项")
                        }
                    }

                    // 问题描述
                    DetailSection(title: "问题描述", icon: "doc.text") {
                        Text(issue.description)
                            .font(.system(size: 12))
                            .foregroundColor(.fmText2)
                            .lineSpacing(4)
                    }

                    // 建议操作
                    DetailSection(title: "建议操作", icon: "lightbulb") {
                        Text(issue.suggestedAction)
                            .font(.system(size: 12))
                            .foregroundColor(.fmText2)
                            .lineSpacing(4)
                    }

                    Spacer()
                }
                .padding(20)
            }

            Divider()

            // 底部操作栏
            HStack(spacing: 12) {
                Text("v1.0")
                    .font(.system(size: 10))
                    .foregroundColor(.fmText3)

                Spacer()

                Button(action: { /* 忽略 */ }) {
                    Text("忽略")
                        .font(.system(size: 12))
                        .foregroundColor(.fmText2)
                        .padding(.horizontal, 16)
                        .padding(.vertical, 8)
                        .background(Color.fmBg)
                        .cornerRadius(6)
                }
                .buttonStyle(PlainButtonStyle())

                Button(action: { /* 前往修复 */ }) {
                    Text("前往修复")
                        .font(.system(size: 12))
                        .foregroundColor(.white)
                        .padding(.horizontal, 16)
                        .padding(.vertical, 8)
                        .background(Color.fmBlue)
                        .cornerRadius(6)
                }
                .buttonStyle(PlainButtonStyle())
            }
            .padding(16)
            .background(Color.fmBg2)
        }
        .frame(width: 600, height: 500)
    }

    private var typeIcon: String {
        switch issue.type {
        case "error": return "xmark.circle.fill"
        case "warning": return "exclamationmark.triangle.fill"
        case "info": return "info.circle.fill"
        default: return "questionmark.circle.fill"
        }
    }

    private var typeColor: Color {
        switch issue.type {
        case "error": return Color(hex: "E74C3C")
        case "warning": return .fmOrange
        case "info": return .fmBlue
        default: return .gray
        }
    }

    private var typeLabel: String {
        switch issue.type {
        case "error": return "错误"
        case "warning": return "警告"
        case "info": return "信息"
        default: return "未知"
        }
    }

    private var categoryLabel: String {
        switch issue.category {
        case "ai": return "AI处理"
        case "data": return "数据质量"
        case "citation": return "引用"
        case "graph": return "知识图谱"
        case "annotation": return "标注"
        default: return "其他"
        }
    }

    private var severityLabel: String {
        switch issue.severity {
        case "high": return "严重"
        case "medium": return "中等"
        case "low": return "轻微"
        default: return "未知"
        }
    }

    private var statusLabel: String {
        switch issue.status {
        case "new": return "新问题"
        case "reviewing": return "审核中"
        case "fixing": return "修复中"
        case "resolved": return "已解决"
        default: return "未知"
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

// MARK: - Task Detail Sheet
struct TaskDetailSheet: View {
    let task: QualityCheckTask
    let onClose: () -> Void

    var body: some View {
        VStack(spacing: 0) {
            // 标题栏
            HStack {
                Image(systemName: categoryIcon)
                    .font(.system(size: 20))
                    .foregroundColor(.fmBlue)

                Text("任务详情")
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundColor(.fmText)

                Spacer()

                Button(action: onClose) {
                    Image(systemName: "xmark")
                        .font(.system(size: 12))
                        .foregroundColor(.fmText3)
                        .frame(width: 24, height: 24)
                        .background(Color.fmBg)
                        .cornerRadius(12)
                }
                .buttonStyle(PlainButtonStyle())
            }
            .padding(20)
            .background(Color.fmBg2)

            Divider()

            // 内容区
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    // 基本信息
                    DetailSection(title: "基本信息", icon: "info.circle") {
                        VStack(alignment: .leading, spacing: 12) {
                            InfoRow(label: "任务名称", value: task.name)
                            InfoRow(label: "类别", value: categoryLabel)
                            InfoRow(label: "执行频率", value: frequencyLabel)
                            InfoRow(label: "状态", value: statusLabel)
                        }
                    }

                    // 任务描述
                    DetailSection(title: "任务描述", icon: "doc.text") {
                        Text(task.description)
                            .font(.system(size: 12))
                            .foregroundColor(.fmText2)
                            .lineSpacing(4)
                    }

                    // 执行记录
                    DetailSection(title: "执行记录", icon: "clock.arrow.circlepath") {
                        VStack(alignment: .leading, spacing: 12) {
                            if let lastRun = task.lastRun {
                                InfoRow(label: "上次运行", value: formatFullTimestamp(lastRun))
                            }
                            if let nextRun = task.nextRun {
                                InfoRow(label: "下次运行", value: formatFullTimestamp(nextRun))
                            }
                            if let duration = task.duration {
                                InfoRow(label: "执行时长", value: duration)
                            }
                            InfoRow(label: "发现问题", value: "\(task.issuesFound) 个")
                        }
                    }

                    Spacer()
                }
                .padding(20)
            }

            Divider()

            // 底部操作栏
            HStack(spacing: 12) {
                Text("v1.0")
                    .font(.system(size: 10))
                    .foregroundColor(.fmText3)

                Spacer()

                Button(action: { /* 配置 */ }) {
                    Text("配置")
                        .font(.system(size: 12))
                        .foregroundColor(.fmText2)
                        .padding(.horizontal, 16)
                        .padding(.vertical, 8)
                        .background(Color.fmBg)
                        .cornerRadius(6)
                }
                .buttonStyle(PlainButtonStyle())

                Button(action: { /* 立即运行 */ }) {
                    Text("立即运行")
                        .font(.system(size: 12))
                        .foregroundColor(.white)
                        .padding(.horizontal, 16)
                        .padding(.vertical, 8)
                        .background(Color.fmBlue)
                        .cornerRadius(6)
                }
                .buttonStyle(PlainButtonStyle())
            }
            .padding(16)
            .background(Color.fmBg2)
        }
        .frame(width: 500, height: 450)
    }

    private var categoryIcon: String {
        switch task.category {
        case "ai": return "cpu"
        case "data": return "doc.text"
        case "citation": return "quote.bubble"
        case "graph": return "circle.hexagongrid"
        case "annotation": return "tag"
        default: return "checklist"
        }
    }

    private var categoryLabel: String {
        switch task.category {
        case "ai": return "AI处理"
        case "data": return "数据质量"
        case "citation": return "引用"
        case "graph": return "知识图谱"
        case "annotation": return "标注"
        default: return "其他"
        }
    }

    private var frequencyLabel: String {
        switch task.frequency {
        case "daily": return "每日执行"
        case "weekly": return "每周执行"
        case "manual": return "手动执行"
        default: return task.frequency
        }
    }

    private var statusLabel: String {
        switch task.status {
        case "idle": return "待运行"
        case "running": return "运行中"
        case "completed": return "已完成"
        case "failed": return "失败"
        default: return "未知"
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

// MARK: - Detail Section (Reusable)
struct DetailSection<Content: View>: View {
    let title: String
    let icon: String
    let content: Content

    init(title: String, icon: String, @ViewBuilder content: () -> Content) {
        self.title = title
        self.icon = icon
        self.content = content()
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack(spacing: 6) {
                Image(systemName: icon)
                    .font(.system(size: 12))
                    .foregroundColor(.fmBlue)

                Text(title)
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundColor(.fmText)
            }

            content
                .padding(12)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(Color.fmBg)
                .cornerRadius(8)
        }
    }
}

// Use InfoRow from PhotosPage (already exists, no redeclaration needed)
