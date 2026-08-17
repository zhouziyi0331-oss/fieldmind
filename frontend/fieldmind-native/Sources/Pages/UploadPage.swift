import SwiftUI
import UniformTypeIdentifiers

struct UploadPage: View {
    @EnvironmentObject var appState: AppState
    @StateObject private var viewModel = DocumentViewModel()
    @State private var isDragging = false
    @State private var searchText = ""
    @State private var selectedStatus: FileStatus? = nil
    @State private var selectedType: String? = nil
    @State private var sortBy: FileSortOption = .uploadTime
    @State private var showingFileDetail: DocumentStatusResponse? = nil

    // AI 处理设置
    @State private var autoProcess = true
    @State private var autoKeyword = true
    @State private var autoSummary = false

    var body: some View {
        ScrollView {
            VStack(spacing: 24) {
                // 页面标题
                HStack {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("材料上传")
                            .font(.system(size: 24, weight: .bold))
                        Text("支持文档、音频、视频等多种格式的智能处理")
                            .font(.system(size: 13))
                            .foregroundStyle(Color.fmN6)
                    }
                    Spacer()
                    HStack(spacing: 12) {
                        Text("\(viewModel.documents.count) 个文件")
                            .font(.system(size: 13))
                            .foregroundStyle(Color.fmN6)
                        Text("•")
                            .foregroundStyle(Color.fmN3)
                        Text(totalSizeString)
                            .font(.system(size: 13))
                            .foregroundStyle(Color.fmN6)
                    }
                }
                .padding(.horizontal, 24)
                .padding(.top, 24)

                // 错误提示
                if let errorMessage = viewModel.errorMessage {
                    HStack {
                        Image(systemName: "exclamationmark.triangle.fill")
                            .foregroundStyle(Color.fmRed)
                        Text(errorMessage)
                            .font(.system(size: 13))
                            .foregroundStyle(Color.fmRed)
                        Spacer()
                        Button("关闭") {
                            viewModel.errorMessage = nil
                        }
                        .font(.system(size: 12, weight: .medium))
                        .foregroundStyle(Color.fmRed)
                    }
                    .padding(12)
                    .background(Color.fmRed.opacity(0.1))
                    .clipShape(RoundedRectangle(cornerRadius: 8))
                    .padding(.horizontal, 24)
                }

                // 上传区域
                uploadArea
                    .padding(.horizontal, 24)

                // AI 处理设置
                aiSettingsCard
                    .padding(.horizontal, 24)

                // 筛选和搜索栏
                HStack(spacing: 12) {
                    // 搜索框
                    HStack(spacing: 8) {
                        Image(systemName: "magnifyingglass")
                            .foregroundStyle(Color.fmN5)
                            .font(.system(size: 13))
                        TextField("搜索文件名...", text: $searchText)
                            .textFieldStyle(.plain)
                            .font(.system(size: 13))
                    }
                    .padding(.horizontal, 12)
                    .padding(.vertical, 8)
                    .background(Color.fmN1)
                    .clipShape(RoundedRectangle(cornerRadius: 8))
                    .frame(maxWidth: 300)

                    Spacer()

                    // 状态筛选
                    Menu {
                        Button("全部状态") { selectedStatus = nil }
                        Divider()
                        Button("已完成") { selectedStatus = .completed }
                        Button("处理中") { selectedStatus = .processing }
                        Button("失败") { selectedStatus = .failed }
                        Button("待处理") { selectedStatus = .pending }
                    } label: {
                        HStack(spacing: 6) {
                            Text(selectedStatus?.displayName ?? "全部状态")
                                .font(.system(size: 13))
                            Image(systemName: "chevron.down")
                                .font(.system(size: 10))
                        }
                        .foregroundStyle(Color.fmText)
                        .padding(.horizontal, 12)
                        .padding(.vertical, 8)
                        .background(Color.fmN1)
                        .clipShape(RoundedRectangle(cornerRadius: 8))
                    }

                    // 类型筛选
                    Menu {
                        Button("全部类型") { selectedType = nil }
                        Divider()
                        ForEach(availableTypes, id: \.self) { type in
                            Button(type) { selectedType = type }
                        }
                    } label: {
                        HStack(spacing: 6) {
                            Text(selectedType ?? "全部类型")
                                .font(.system(size: 13))
                            Image(systemName: "chevron.down")
                                .font(.system(size: 10))
                        }
                        .foregroundStyle(Color.fmText)
                        .padding(.horizontal, 12)
                        .padding(.vertical, 8)
                        .background(Color.fmN1)
                        .clipShape(RoundedRectangle(cornerRadius: 8))
                    }

                    // 排序
                    Menu {
                        Button("上传时间") { sortBy = .uploadTime }
                        Button("文件名称") { sortBy = .name }
                        Button("文件大小") { sortBy = .size }
                        Button("处理状态") { sortBy = .status }
                    } label: {
                        HStack(spacing: 6) {
                            Image(systemName: "arrow.up.arrow.down")
                                .font(.system(size: 11))
                            Text(sortBy.displayName)
                                .font(.system(size: 13))
                        }
                        .foregroundStyle(Color.fmText)
                        .padding(.horizontal, 12)
                        .padding(.vertical, 8)
                        .background(Color.fmN1)
                        .clipShape(RoundedRectangle(cornerRadius: 8))
                    }
                }
                .padding(.horizontal, 24)

                // 文件列表
                if filteredFiles.isEmpty {
                    emptyState
                        .padding(.top, 60)
                } else {
                    fileList
                        .padding(.horizontal, 24)
                }

                Spacer(minLength: 24)
            }
        }
        .background(Color.fmBg)
        .sheet(item: $showingFileDetail) { file in
            FileDetailSheet(file: file, onDelete: {
                Task {
                    if let projectId = appState.currentProject?.id, let id = Int(projectId) {
                        await viewModel.deleteDocument(documentId: file.id, projectId: id)
                    }
                    showingFileDetail = nil
                }
            })
        }
        .task {
            viewModel.setAppState(appState)
            if let projectId = appState.currentProject?.id, let id = Int(projectId) {
                await viewModel.loadDocuments(projectId: id)
            }
        }
        .onDisappear {
            viewModel.stopStatusPolling()
        }
    }

    // MARK: - 上传区域
    private var uploadArea: some View {
        VStack(spacing: 16) {
            ZStack {
                // 背景
                RoundedRectangle(cornerRadius: 16)
                    .fill(isDragging ? Color.fmA1.opacity(0.05) : Color.white)
                    .overlay(
                        RoundedRectangle(cornerRadius: 16)
                            .strokeBorder(
                                isDragging ? Color.fmA1 : Color.fmN2,
                                style: StrokeStyle(lineWidth: 2, dash: [8, 4])
                            )
                    )
                    .shadow(color: Color.black.opacity(0.04), radius: 8, y: 2)

                // 内容
                VStack(spacing: 16) {
                    Image(systemName: isDragging ? "arrow.down.doc.fill" : "arrow.up.doc")
                        .font(.system(size: 48))
                        .foregroundStyle(isDragging ? Color.fmA1 : Color.fmN4)

                    if viewModel.isUploading {
                        VStack(spacing: 8) {
                            Text("上传中...")
                                .font(.system(size: 16, weight: .semibold))
                                .foregroundStyle(Color.fmText)
                            ProgressView(value: viewModel.uploadProgress)
                                .progressViewStyle(.linear)
                                .frame(width: 200)
                            Text("\(Int(viewModel.uploadProgress * 100))%")
                                .font(.system(size: 13))
                                .foregroundStyle(Color.fmN6)
                                .monospacedDigit()
                        }
                    } else {
                        VStack(spacing: 8) {
                            Text(isDragging ? "松开以上传文件" : "点击或拖拽上传文件")
                                .font(.system(size: 16, weight: .semibold))
                                .foregroundStyle(Color.fmText)

                            Text("支持 PDF, DOCX, PPTX, XLSX, TXT, MD, HTML, CSV, JSON, XML, MP3, MP4, WAV 等格式")
                                .font(.system(size: 12))
                                .foregroundStyle(Color.fmN6)
                                .multilineTextAlignment(.center)
                        }
                    }
                }
                .padding(48)
            }
            .frame(height: 240)
            .onDrop(of: [.fileURL], isTargeted: $isDragging) { providers in
                handleDrop(providers: providers)
                return true
            }
            .onTapGesture {
                if !viewModel.isUploading {
                    openFilePicker()
                }
            }
        }
    }

    // MARK: - 文件列表
    private var fileList: some View {
        VStack(spacing: 0) {
            // 表头
            HStack(spacing: 16) {
                Text("文件名称")
                    .frame(width: 280, alignment: .leading)
                Text("类型")
                    .frame(width: 80, alignment: .leading)
                Text("大小")
                    .frame(width: 100, alignment: .leading)
                Text("状态")
                    .frame(width: 100, alignment: .leading)
                Text("字数")
                    .frame(width: 100, alignment: .leading)
                Text("上传时间")
                    .frame(width: 140, alignment: .leading)
                Text("操作")
                    .frame(width: 100, alignment: .leading)
            }
            .font(.system(size: 11, weight: .medium))
            .foregroundStyle(Color.fmN6)
            .padding(.horizontal, 16)
            .padding(.vertical, 12)
            .background(Color.fmN1)

            Divider()

            // 文件行
            ScrollView {
                LazyVStack(spacing: 0) {
                    ForEach(filteredFiles) { file in
                        FileRow(file: file, onViewDetail: {
                            showingFileDetail = file
                        })
                        Divider()
                    }
                }
            }
            .background(Color.white)
        }
        .clipShape(RoundedRectangle(cornerRadius: 12))
        .shadow(color: Color.black.opacity(0.04), radius: 8, y: 2)
    }

    // MARK: - 空状态
    private var emptyState: some View {
        VStack(spacing: 16) {
            Image(systemName: "doc.badge.plus")
                .font(.system(size: 64))
                .foregroundStyle(Color.fmN3)
            Text("还没有上传的文件")
                .font(.system(size: 16, weight: .medium))
                .foregroundStyle(Color.fmN6)
            Text("点击或拖拽文件到上方区域开始上传")
                .font(.system(size: 13))
                .foregroundStyle(Color.fmN5)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 60)
    }

    // MARK: - 计算属性
    private var filteredFiles: [DocumentStatusResponse] {
        var result = viewModel.documents

        // 搜索过滤
        if !searchText.isEmpty {
            result = result.filter { $0.filename.localizedCaseInsensitiveContains(searchText) }
        }

        // 状态过滤
        if let status = selectedStatus {
            result = result.filter {
                FileStatus(rawValue: $0.status) == status
            }
        }

        // 类型过滤
        if let type = selectedType {
            result = result.filter { $0.fileType.uppercased() == type }
        }

        // 排序
        switch sortBy {
        case .uploadTime:
            result.sort {
                guard let date1 = parseISO8601($0.createdAt),
                      let date2 = parseISO8601($1.createdAt) else {
                    return false
                }
                return date1 > date2
            }
        case .name:
            result.sort { $0.filename < $1.filename }
        case .size:
            result.sort { ($0.wordCount ?? 0) > ($1.wordCount ?? 0) }
        case .status:
            result.sort { $0.status < $1.status }
        }

        return result
    }

    private var availableTypes: [String] {
        Array(Set(viewModel.documents.map { $0.fileType.uppercased() })).sorted()
    }

    private var totalSizeString: String {
        // 由于API不返回总大小，显示文档数量
        return "\(viewModel.documents.count) 文档"
    }

    // MARK: - 辅助方法
    private func handleDrop(providers: [NSItemProvider]) {
        guard let projectId = appState.currentProject?.id, let id = Int(projectId) else { return }

        for provider in providers {
            _ = provider.loadObject(ofClass: URL.self) { url, error in
                guard let url = url else { return }
                Task { @MainActor in
                    await viewModel.uploadFile(projectId: id, fileURL: url)
                }
            }
        }
    }

    private func openFilePicker() {
        guard let projectId = appState.currentProject?.id, let id = Int(projectId) else { return }

        let panel = NSOpenPanel()
        panel.allowsMultipleSelection = true
        panel.canChooseDirectories = false
        panel.allowedContentTypes = [
            .pdf, .text, .html, .xml, .json,
            .plainText, .spreadsheet, .presentation,
            .audio, .movie, .mpeg4Movie
        ]

        if panel.runModal() == .OK {
            for url in panel.urls {
                Task {
                    await viewModel.uploadFile(projectId: id, fileURL: url)
                }
            }
        }
    }

    private func parseISO8601(_ dateString: String?) -> Date? {
        guard let dateString = dateString else { return nil }
        let formatter = ISO8601DateFormatter()
        return formatter.date(from: dateString)
    }

    private func formatFileSize(_ bytes: Int64) -> String {
        let kb = Double(bytes) / 1024
        if kb < 1024 {
            return String(format: "%.1f KB", kb)
        }
        let mb = kb / 1024
        if mb < 1024 {
            return String(format: "%.1f MB", mb)
        }
        let gb = mb / 1024
        return String(format: "%.2f GB", gb)
    }

    // MARK: - AI 设置卡片
    private var aiSettingsCard: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                Image(systemName: "sparkles")
                    .foregroundStyle(Color.fmA1)
                    .font(.system(size: 14))
                Text("AI 智能处理")
                    .font(.system(size: 15, weight: .semibold))
                    .foregroundStyle(Color.fmText)
                Spacer()
            }

            VStack(spacing: 12) {
                Toggle(isOn: $autoProcess) {
                    HStack(spacing: 8) {
                        Image(systemName: "wand.and.stars")
                            .font(.system(size: 13))
                            .foregroundStyle(Color.fmA1)
                            .frame(width: 20)
                        VStack(alignment: .leading, spacing: 2) {
                            Text("自动处理文档")
                                .font(.system(size: 13, weight: .medium))
                                .foregroundStyle(Color.fmText)
                            Text("上传后立即开始分析和向量化")
                                .font(.system(size: 11))
                                .foregroundStyle(Color.fmN6)
                        }
                    }
                }
                .toggleStyle(.switch)

                Toggle(isOn: $autoKeyword) {
                    HStack(spacing: 8) {
                        Image(systemName: "tag.fill")
                            .font(.system(size: 13))
                            .foregroundStyle(Color.fmA2)
                            .frame(width: 20)
                        VStack(alignment: .leading, spacing: 2) {
                            Text("自动提取关键词")
                                .font(.system(size: 13, weight: .medium))
                                .foregroundStyle(Color.fmText)
                            Text("智能识别文档中的关键概念")
                                .font(.system(size: 11))
                                .foregroundStyle(Color.fmN6)
                        }
                    }
                }
                .toggleStyle(.switch)

                Toggle(isOn: $autoSummary) {
                    HStack(spacing: 8) {
                        Image(systemName: "doc.text.fill")
                            .font(.system(size: 13))
                            .foregroundStyle(Color.fmBlue)
                            .frame(width: 20)
                        VStack(alignment: .leading, spacing: 2) {
                            Text("自动生成摘要")
                                .font(.system(size: 13, weight: .medium))
                                .foregroundStyle(Color.fmText)
                            Text("为每个文档生成简洁摘要")
                                .font(.system(size: 11))
                                .foregroundStyle(Color.fmN6)
                        }
                    }
                }
                .toggleStyle(.switch)
            }
        }
        .padding(16)
        .background(Color.fmSurface)
        .clipShape(RoundedRectangle(cornerRadius: 12))
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(Color.fmN2, lineWidth: 1)
        )
    }
}

// MARK: - 文件行组件
struct FileRow: View {
    let file: DocumentStatusResponse
    let onViewDetail: () -> Void

    var body: some View {
        HStack(spacing: 16) {
            // 文件名
            HStack(spacing: 8) {
                fileIcon
                Text(file.filename)
                    .font(.system(size: 13))
                    .foregroundStyle(Color.fmText)
                    .lineLimit(1)
            }
            .frame(width: 280, alignment: .leading)

            // 类型
            Text(file.fileType.uppercased())
                .font(.system(size: 11, weight: .medium))
                .foregroundStyle(Color.white)
                .padding(.horizontal, 8)
                .padding(.vertical, 4)
                .background(typeColor(file.fileType))
                .clipShape(RoundedRectangle(cornerRadius: 4))
                .frame(width: 80, alignment: .leading)

            // 大小（显示为字数）
            Text(file.wordCount != nil ? "\(file.wordCount!) 字" : "-")
                .font(.system(size: 13))
                .foregroundStyle(Color.fmN6)
                .monospacedDigit()
                .frame(width: 100, alignment: .leading)

            // 状态
            HStack(spacing: 4) {
                Circle()
                    .fill(statusColor(file.status))
                    .frame(width: 6, height: 6)
                Text(statusDisplayName(file.status))
                    .font(.system(size: 12))
                    .foregroundStyle(statusColor(file.status))
            }
            .frame(width: 100, alignment: .leading)

            // 分块数
            Text(file.chunkCount > 0 ? "\(file.chunkCount)" : "-")
                .font(.system(size: 13))
                .foregroundStyle(Color.fmN6)
                .monospacedDigit()
                .frame(width: 100, alignment: .leading)

            // 上传时间
            Text(file.createdAt != nil ? timeAgo(from: file.createdAt!) : "-")
                .font(.system(size: 12))
                .foregroundStyle(Color.fmN6)
                .frame(width: 140, alignment: .leading)

            // 操作
            Button(action: onViewDetail) {
                Text("查看详情")
                    .font(.system(size: 12, weight: .medium))
                    .foregroundStyle(Color.fmA1)
            }
            .buttonStyle(.plain)
            .frame(width: 100, alignment: .leading)
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 12)
        .background(Color.white)
        .contentShape(Rectangle())
    }

    private var fileIcon: some View {
        ZStack {
            RoundedRectangle(cornerRadius: 6)
                .fill(typeColor(file.fileType).opacity(0.1))
                .frame(width: 32, height: 32)
            Image(systemName: fileIconName(file.fileType))
                .font(.system(size: 14))
                .foregroundStyle(typeColor(file.fileType))
        }
    }

    private func fileIconName(_ type: String) -> String {
        switch type.lowercased() {
        case "pdf": return "doc.fill"
        case "doc", "docx": return "doc.text.fill"
        case "xls", "xlsx": return "tablecells"
        case "ppt", "pptx": return "person.crop.rectangle"
        case "mp3", "wav", "audio": return "waveform"
        case "mp4", "mov", "video": return "video.fill"
        case "jpg", "png", "jpeg": return "photo.fill"
        case "txt", "md", "markdown": return "doc.plaintext"
        case "html": return "chevron.left.forwardslash.chevron.right"
        case "json": return "curlybraces"
        case "xml": return "chevron.left.forwardslash.chevron.right"
        default: return "doc"
        }
    }

    private func typeColor(_ type: String) -> Color {
        switch type.lowercased() {
        case "pdf": return Color(hex: "E03E3E")
        case "doc", "docx": return Color(hex: "2B5797")
        case "xls", "xlsx": return Color(hex: "1F7244")
        case "ppt", "pptx": return Color(hex: "D04524")
        case "mp3", "wav", "audio": return Color(hex: "9B59B6")
        case "mp4", "mov", "video": return Color(hex: "E74C3C")
        case "jpg", "png", "jpeg": return Color(hex: "3498DB")
        case "txt", "md", "markdown": return Color(hex: "95A5A6")
        case "html", "xml": return Color(hex: "E67E22")
        case "json": return Color(hex: "F39C12")
        default: return Color.fmN5
        }
    }

    private func statusColor(_ status: String) -> Color {
        switch status {
        case "completed": return Color.fmGreen
        case "processing": return Color.fmBlue
        case "failed": return Color.fmRed
        case "pending": return Color.fmYellow
        default: return Color.fmN5
        }
    }

    private func statusDisplayName(_ status: String) -> String {
        switch status {
        case "completed": return "已完成"
        case "processing": return "处理中"
        case "failed": return "失败"
        case "pending": return "待处理"
        default: return status
        }
    }

    private func timeAgo(from dateString: String) -> String {
        let formatter = ISO8601DateFormatter()
        guard let date = formatter.date(from: dateString) else {
            return dateString
        }

        let interval = Date().timeIntervalSince(date)
        let hours = Int(interval / 3600)
        let days = hours / 24

        if hours < 1 {
            return "刚刚"
        } else if hours < 24 {
            return "\(hours)小时前"
        } else if days < 30 {
            return "\(days)天前"
        } else {
            let formatter = DateFormatter()
            formatter.dateFormat = "yyyy-MM-dd"
            return formatter.string(from: date)
        }
    }
}

// MARK: - 文件详情弹窗
struct FileDetailSheet: View {
    let file: DocumentStatusResponse
    let onDelete: () -> Void
    @Environment(\.dismiss) var dismiss

    var body: some View {
        VStack(spacing: 0) {
            // 标题栏
            HStack {
                Text("文件详情")
                    .font(.system(size: 18, weight: .semibold))
                Spacer()
                Button(action: { dismiss() }) {
                    Image(systemName: "xmark")
                        .font(.system(size: 14, weight: .medium))
                        .foregroundStyle(Color.fmN6)
                }
                .buttonStyle(.plain)
            }
            .padding(20)
            .background(Color.white)

            Divider()

            // 内容
            ScrollView {
                VStack(alignment: .leading, spacing: 24) {
                    // 基本信息
                    infoSection(title: "基本信息") {
                        infoRow(label: "文件名", value: file.filename)
                        infoRow(label: "文件类型", value: file.fileType.uppercased())
                        infoRow(label: "上传时间", value: formatDate(file.createdAt))
                        infoRow(label: "处理状态", value: statusDisplayName(file.status), valueColor: statusColor(file.status))

                        if let errorMessage = file.errorMessage {
                            infoRow(label: "错误信息", value: errorMessage, valueColor: Color.fmRed)
                        }
                    }

                    // 处理结果
                    if file.status == "completed" {
                        infoSection(title: "处理结果") {
                            infoRow(label: "字数统计", value: file.wordCount != nil ? "\(file.wordCount!) 字" : "-")
                            infoRow(label: "分块数量", value: "\(file.chunkCount) 个")
                            infoRow(label: "向量化", value: file.vectorized ? "已完成" : "未完成")
                            infoRow(label: "技能分析", value: file.skillsCompleted ? "已完成" : "未完成")
                        }
                    }

                    // 操作按钮
                    HStack(spacing: 12) {
                        Button(action: {
                            onDelete()
                        }) {
                            Text("删除文件")
                                .font(.system(size: 13, weight: .medium))
                                .foregroundStyle(Color.fmRed)
                                .padding(.horizontal, 16)
                                .padding(.vertical, 8)
                                .background(Color.fmRed.opacity(0.1))
                                .clipShape(RoundedRectangle(cornerRadius: 6))
                        }
                        .buttonStyle(.plain)
                    }
                }
                .padding(20)
            }
            .background(Color.fmBg)
        }
        .frame(width: 600, height: 500)
    }

    private func infoSection<Content: View>(title: String, @ViewBuilder content: () -> Content) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(title)
                .font(.system(size: 14, weight: .semibold))
                .foregroundStyle(Color.fmText)
            VStack(spacing: 8) {
                content()
            }
            .padding(16)
            .background(Color.white)
            .clipShape(RoundedRectangle(cornerRadius: 8))
        }
    }

    private func infoRow(label: String, value: String, valueColor: Color = Color.fmText) -> some View {
        HStack {
            Text(label)
                .font(.system(size: 13))
                .foregroundStyle(Color.fmN6)
                .frame(width: 100, alignment: .leading)
            Text(value)
                .font(.system(size: 13, weight: .medium))
                .foregroundStyle(valueColor)
            Spacer()
        }
    }

    private func formatDate(_ dateString: String?) -> String {
        guard let dateString = dateString else { return "-" }
        let formatter = ISO8601DateFormatter()
        guard let date = formatter.date(from: dateString) else {
            return dateString
        }

        let displayFormatter = DateFormatter()
        displayFormatter.dateFormat = "yyyy-MM-dd HH:mm:ss"
        return displayFormatter.string(from: date)
    }

    private func statusColor(_ status: String) -> Color {
        switch status {
        case "completed": return Color.fmGreen
        case "processing": return Color.fmBlue
        case "failed": return Color.fmRed
        case "pending": return Color.fmYellow
        default: return Color.fmN5
        }
    }

    private func statusDisplayName(_ status: String) -> String {
        switch status {
        case "completed": return "已完成"
        case "processing": return "处理中"
        case "failed": return "失败"
        case "pending": return "待处理"
        default: return status
        }
    }
}

// MARK: - 支持类型
enum FileSortOption: String, CaseIterable {
    case uploadTime = "upload_time"
    case name = "name"
    case size = "size"
    case status = "status"

    var displayName: String {
        switch self {
        case .uploadTime: return "上传时间"
        case .name: return "文件名称"
        case .size: return "文件大小"
        case .status: return "处理状态"
        }
    }
}
