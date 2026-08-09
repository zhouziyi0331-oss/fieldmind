import SwiftUI

struct CrawlerView: View {
    @EnvironmentObject var appState: AppState
    @State private var sourceURL = ""
    @State private var crawlerType = "新闻动态"
    @State private var depth = 1
    @State private var includeImages = true
    @State private var includeLinks = true
    @State private var tasks: [CrawlerTask] = []
    @State private var isRunning = false
    @State private var selectedTask: CrawlerTask?

    let crawlerTypes = ["新闻动态", "政府文件", "研究报告", "社交媒体", "论坛讨论"]

    var body: some View {
        HStack(spacing: 0) {
            // 左侧任务列表
            VStack(spacing: 0) {
                // 列表头部
                HStack {
                    Text("爬取任务")
                        .font(.system(size: 12, weight: .bold))
                        .foregroundColor(Color.fieldMindText)

                    Spacer()

                    Button {
                        // 刷新任务列表
                        loadTasks()
                    } label: {
                        Image(systemName: "arrow.clockwise")
                            .font(.system(size: 11))
                            .foregroundColor(Color.fieldMindPrimary)
                    }
                    .buttonStyle(PlainButtonStyle())
                }
                .padding(.horizontal, 16)
                .padding(.vertical, 12)
                .background(Color.white)
                .overlay(
                    Rectangle()
                        .fill(Color.gray.opacity(0.1))
                        .frame(height: 1),
                    alignment: .bottom
                )

                // 任务列表
                if tasks.isEmpty {
                    VStack(spacing: 12) {
                        Image(systemName: "tray")
                            .font(.system(size: 32))
                            .foregroundColor(Color.fieldMindText.opacity(0.3))
                        Text("暂无爬取任务")
                            .font(.system(size: 11))
                            .foregroundColor(Color.fieldMindText.opacity(0.5))
                    }
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                    .background(Color.fieldMindBackground)
                } else {
                    ScrollView(showsIndicators: false) {
                        VStack(spacing: 8) {
                            ForEach(tasks) { task in
                                CrawlerTaskRow(
                                    task: task,
                                    isSelected: selectedTask?.id == task.id
                                )
                                .onTapGesture {
                                    selectedTask = task
                                }
                            }
                        }
                        .padding(12)
                    }
                    .background(Color.fieldMindBackground)
                }
            }
            .frame(width: 280)

            Rectangle()
                .fill(Color.gray.opacity(0.15))
                .frame(width: 1)

            // 右侧配置区域
            ScrollView(showsIndicators: false) {
                VStack(alignment: .leading, spacing: 24) {
                    if let task = selectedTask {
                        // 任务详情
                        taskDetailView(task)
                    } else {
                        // 新建任务表单
                        newTaskForm
                    }
                }
                .padding(24)
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .background(Color.fieldMindBackground)
        }
        .onAppear(perform: loadTasks)
    }

    // MARK: - 新建任务表单
    private var newTaskForm: some View {
        VStack(alignment: .leading, spacing: 20) {
            Text("新建爬取任务")
                .font(.system(size: 14, weight: .bold))
                .foregroundColor(Color.fieldMindText)

            VStack(alignment: .leading, spacing: 16) {
                // 目标URL
                FormField(label: "目标URL", isRequired: true) {
                    TextField("输入网站地址，如：https://example.com", text: $sourceURL)
                        .textFieldStyle(CustomTextFieldStyle())
                }

                // 爬取类型
                FormField(label: "爬取类型", isRequired: true) {
                    HStack(spacing: 8) {
                        ForEach(crawlerTypes, id: \.self) { type in
                            Button {
                                crawlerType = type
                            } label: {
                                Text(type)
                                    .font(.system(size: 11, weight: .medium))
                                    .foregroundColor(crawlerType == type ? .white : Color.fieldMindText)
                                    .padding(.horizontal, 12)
                                    .padding(.vertical, 6)
                                    .background(crawlerType == type ? Color.fieldMindPrimary : Color.white)
                                    .cornerRadius(6)
                                    .overlay(
                                        RoundedRectangle(cornerRadius: 6)
                                            .stroke(crawlerType == type ? Color.clear : Color.fieldMindText.opacity(0.2), lineWidth: 1)
                                    )
                            }
                            .buttonStyle(PlainButtonStyle())
                        }
                    }
                }

                // 爬取深度
                FormField(label: "爬取深度", isRequired: false) {
                    HStack(spacing: 12) {
                        Slider(value: Binding(
                            get: { Double(depth) },
                            set: { depth = Int($0) }
                        ), in: 1...5, step: 1)
                        .frame(maxWidth: 200)

                        Text("\(depth) 层")
                            .font(.system(size: 12, weight: .medium))
                            .foregroundColor(Color.fieldMindText)
                            .frame(width: 40)
                    }
                }

                // 选项
                VStack(alignment: .leading, spacing: 8) {
                    Text("爬取选项")
                        .font(.system(size: 12, weight: .medium))
                        .foregroundColor(Color.fieldMindText)

                    Toggle(isOn: $includeImages) {
                        Text("包含图片")
                            .font(.system(size: 12))
                            .foregroundColor(Color.fieldMindText)
                    }
                    .toggleStyle(.checkbox)

                    Toggle(isOn: $includeLinks) {
                        Text("跟随链接")
                            .font(.system(size: 12))
                            .foregroundColor(Color.fieldMindText)
                    }
                    .toggleStyle(.checkbox)
                }
            }
            .padding(14)
            .background(Color.white)
            .cornerRadius(10)

            // 启动按钮
            Button {
                startCrawler()
            } label: {
                HStack(spacing: 6) {
                    if isRunning {
                        ProgressView()
                            .scaleEffect(0.7)
                            .frame(width: 12, height: 12)
                    }
                    Text(isRunning ? "爬取中..." : "开始爬取")
                        .font(.system(size: 12, weight: .medium))
                }
                .foregroundColor(.white)
                .frame(maxWidth: .infinity)
                .padding(.vertical, 10)
                .background(sourceURL.isEmpty || isRunning ? Color.gray.opacity(0.3) : Color.fieldMindPrimary)
                .cornerRadius(6)
            }
            .buttonStyle(PlainButtonStyle())
            .disabled(sourceURL.isEmpty || isRunning)

            // 说明文字
            VStack(alignment: .leading, spacing: 8) {
                HStack(spacing: 6) {
                    Image(systemName: "info.circle.fill")
                        .font(.system(size: 12))
                        .foregroundColor(Color.fieldMindAuxiliary)
                    Text("爬取说明")
                        .font(.system(size: 11, weight: .bold))
                        .foregroundColor(Color.fieldMindText)
                }

                Text("• 爬取深度表示从起始页面开始，向下跟随链接的层数\n• 包含图片会下载页面中的所有图片资源\n• 跟随链接会自动爬取同域名下的相关页面\n• 爬取完成后，内容将自动保存到当前项目")
                    .font(.system(size: 11))
                    .foregroundColor(Color.fieldMindText.opacity(0.6))
                    .lineSpacing(2)
            }
            .padding(12)
            .background(Color.fieldMindAuxiliary.opacity(0.1))
            .cornerRadius(7)
        }
    }

    // MARK: - 任务详情
    private func taskDetailView(_ task: CrawlerTask) -> some View {
        VStack(alignment: .leading, spacing: 20) {
            HStack {
                Text("任务详情")
                    .font(.system(size: 14, weight: .bold))
                    .foregroundColor(Color.fieldMindText)

                Spacer()

                Button {
                    selectedTask = nil
                } label: {
                    Image(systemName: "xmark")
                        .font(.system(size: 11))
                        .foregroundColor(Color.fieldMindText.opacity(0.6))
                }
                .buttonStyle(PlainButtonStyle())
            }

            // 任务状态卡片
            VStack(alignment: .leading, spacing: 12) {
                HStack {
                    CrawlerStatusBadge(status: task.status)
                    Spacer()
                    Text(formatDate(task.createdAt))
                        .font(.system(size: 10))
                        .foregroundColor(Color.fieldMindText.opacity(0.5))
                }

                VStack(alignment: .leading, spacing: 8) {
                    Text(task.sourceURL)
                        .font(.system(size: 12, weight: .medium))
                        .foregroundColor(Color.fieldMindText)

                    Text(task.type)
                        .font(.system(size: 11))
                        .foregroundColor(Color.fieldMindText.opacity(0.6))
                }

                // 进度条
                if task.status == "运行中" {
                    VStack(alignment: .leading, spacing: 6) {
                        HStack {
                            Text("进度")
                                .font(.system(size: 11))
                                .foregroundColor(Color.fieldMindText.opacity(0.6))
                            Spacer()
                            Text("\(task.progress)%")
                                .font(.system(size: 11, weight: .bold))
                                .foregroundColor(Color.fieldMindPrimary)
                        }

                        GeometryReader { geometry in
                            ZStack(alignment: .leading) {
                                Rectangle()
                                    .fill(Color.gray.opacity(0.15))
                                    .frame(height: 6)
                                    .cornerRadius(3)

                                Rectangle()
                                    .fill(Color.fieldMindPrimary)
                                    .frame(width: geometry.size.width * CGFloat(task.progress) / 100.0, height: 6)
                                    .cornerRadius(3)
                            }
                        }
                        .frame(height: 6)
                    }
                }

                // 统计信息
                HStack(spacing: 20) {
                    StatItem(label: "已爬取", value: "\(task.pagesCollected)")
                    StatItem(label: "文件数", value: "\(task.filesDownloaded)")
                    if task.errorCount > 0 {
                        StatItem(label: "错误", value: "\(task.errorCount)", isError: true)
                    }
                }
            }
            .padding(14)
            .background(Color.white)
            .cornerRadius(10)

            // 操作按钮
            HStack(spacing: 12) {
                if task.status == "运行中" {
                    Button {
                        pauseTask(task)
                    } label: {
                        HStack(spacing: 6) {
                            Image(systemName: "pause.fill")
                                .font(.system(size: 10))
                            Text("暂停")
                                .font(.system(size: 12, weight: .medium))
                        }
                        .foregroundColor(Color.fieldMindText)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 10)
                        .background(Color.white)
                        .cornerRadius(6)
                        .overlay(
                            RoundedRectangle(cornerRadius: 6)
                                .stroke(Color.fieldMindText.opacity(0.2), lineWidth: 1)
                        )
                    }
                    .buttonStyle(PlainButtonStyle())
                } else if task.status == "已暂停" {
                    Button {
                        resumeTask(task)
                    } label: {
                        HStack(spacing: 6) {
                            Image(systemName: "play.fill")
                                .font(.system(size: 10))
                            Text("继续")
                                .font(.system(size: 12, weight: .medium))
                        }
                        .foregroundColor(.white)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 10)
                        .background(Color.fieldMindPrimary)
                        .cornerRadius(6)
                    }
                    .buttonStyle(PlainButtonStyle())
                }

                Button {
                    deleteTask(task)
                } label: {
                    HStack(spacing: 6) {
                        Image(systemName: "trash")
                            .font(.system(size: 10))
                        Text("删除")
                            .font(.system(size: 12, weight: .medium))
                    }
                    .foregroundColor(Color.fieldMindDanger)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 10)
                    .background(Color.white)
                    .cornerRadius(6)
                    .overlay(
                        RoundedRectangle(cornerRadius: 6)
                            .stroke(Color.fieldMindDanger.opacity(0.3), lineWidth: 1)
                    )
                }
                .buttonStyle(PlainButtonStyle())
            }

            // 爬取日志
            if !task.logs.isEmpty {
                VStack(alignment: .leading, spacing: 12) {
                    Text("爬取日志")
                        .font(.system(size: 12, weight: .bold))
                        .foregroundColor(Color.fieldMindText)

                    ScrollView {
                        VStack(alignment: .leading, spacing: 4) {
                            ForEach(task.logs, id: \.self) { log in
                                Text(log)
                                    .font(.system(size: 10, design: .monospaced))
                                    .foregroundColor(Color.fieldMindText.opacity(0.7))
                            }
                        }
                        .padding(10)
                    }
                    .frame(maxHeight: 200)
                    .background(Color.fieldMindText.opacity(0.05))
                    .cornerRadius(6)
                }
                .padding(14)
                .background(Color.white)
                .cornerRadius(10)
            }
        }
    }

    // MARK: - Helper Functions
    private func loadTasks() {
        // TODO: 从API加载任务
        tasks = [
            CrawlerTask(
                sourceURL: "https://example.com/news",
                type: "新闻动态",
                status: "运行中",
                progress: 45,
                pagesCollected: 23,
                filesDownloaded: 156,
                errorCount: 2,
                logs: ["[2024-01-15 10:30] 开始爬取", "[2024-01-15 10:31] 已爬取 10 页"]
            )
        ]
    }

    private func startCrawler() {
        isRunning = true

        Task {
            do {
                // TODO: 调用API启动爬虫
                try await Task.sleep(nanoseconds: 2_000_000_000)

                await MainActor.run {
                    isRunning = false
                    sourceURL = ""
                    loadTasks()
                }
            } catch {
                await MainActor.run {
                    isRunning = false
                }
            }
        }
    }

    private func pauseTask(_ task: CrawlerTask) {
        // TODO: 调用API暂停任务
    }

    private func resumeTask(_ task: CrawlerTask) {
        // TODO: 调用API继续任务
    }

    private func deleteTask(_ task: CrawlerTask) {
        // TODO: 调用API删除任务
        tasks.removeAll { $0.id == task.id }
        selectedTask = nil
    }

    private func formatDate(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd HH:mm"
        return formatter.string(from: date)
    }
}

// MARK: - Supporting Views
struct CrawlerTaskRow: View {
    let task: CrawlerTask
    let isSelected: Bool

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                CrawlerStatusBadge(status: task.status)
                Spacer()
                Text(task.type)
                    .font(.system(size: 9, weight: .medium))
                    .foregroundColor(Color.fieldMindText.opacity(0.5))
                    .padding(.horizontal, 6)
                    .padding(.vertical, 3)
                    .background(Color.fieldMindNeutral.opacity(0.2))
                    .cornerRadius(4)
            }

            Text(task.sourceURL)
                .font(.system(size: 11, weight: .medium))
                .foregroundColor(Color.fieldMindText)
                .lineLimit(2)

            HStack(spacing: 12) {
                HStack(spacing: 4) {
                    Image(systemName: "doc.fill")
                        .font(.system(size: 9))
                    Text("\(task.pagesCollected)")
                        .font(.system(size: 10))
                }
                .foregroundColor(Color.fieldMindText.opacity(0.5))

                HStack(spacing: 4) {
                    Image(systemName: "arrow.down.circle.fill")
                        .font(.system(size: 9))
                    Text("\(task.filesDownloaded)")
                        .font(.system(size: 10))
                }
                .foregroundColor(Color.fieldMindText.opacity(0.5))
            }
        }
        .padding(10)
        .background(isSelected ? Color.fieldMindPrimary.opacity(0.1) : Color.white)
        .cornerRadius(7)
        .overlay(
            RoundedRectangle(cornerRadius: 7)
                .stroke(isSelected ? Color.fieldMindPrimary.opacity(0.3) : Color.clear, lineWidth: 1)
        )
    }
}

struct CrawlerStatusBadge: View {
    let status: String

    var body: some View {
        Text(status)
            .font(.system(size: 10, weight: .bold))
            .foregroundColor(.white)
            .padding(.horizontal, 8)
            .padding(.vertical, 3)
            .background(statusColor)
            .cornerRadius(4)
    }

    private var statusColor: Color {
        switch status {
        case "运行中": return Color.fieldMindPrimary
        case "已完成": return Color.fieldMindSuccess
        case "已暂停": return Color.fieldMindNeutral
        case "失败": return Color.fieldMindDanger
        default: return Color.gray
        }
    }
}

struct StatItem: View {
    let label: String
    let value: String
    var isError: Bool = false

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(label)
                .font(.system(size: 10))
                .foregroundColor(Color.fieldMindText.opacity(0.5))
            Text(value)
                .font(.system(size: 14, weight: .bold))
                .foregroundColor(isError ? Color.fieldMindDanger : Color.fieldMindText)
        }
    }
}

// MARK: - Models
struct CrawlerTask: Identifiable {
    let id = UUID()
    let sourceURL: String
    let type: String
    var status: String
    var progress: Int = 0
    var pagesCollected: Int = 0
    var filesDownloaded: Int = 0
    var errorCount: Int = 0
    var logs: [String] = []
    let createdAt: Date = Date()
}
