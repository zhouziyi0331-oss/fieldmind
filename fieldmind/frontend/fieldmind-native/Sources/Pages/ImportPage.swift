import SwiftUI
import UniformTypeIdentifiers

struct ImportPage: View {
    @EnvironmentObject var appState: AppState
    @State private var isDragging = false
    @State private var selectedFiles: [URL] = []
    @State private var autoTranscribe = true
    @State private var autoKeyword = true
    @State private var autoTimecode = true
    @State private var autoSummary = false
    @State private var autoLinkKeywords = false

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            // 页头
            sectionHeader

            // 两栏布局
            HStack(alignment: .top, spacing: 14) {
                // 左侧：上传区 + AI设置
                VStack(spacing: 14) {
                    uploadZone
                    aiSettingsCard
                }
                .frame(maxWidth: .infinity)

                // 右侧：统计和最近上传
                VStack(spacing: 14) {
                    statsCard
                    recentUploadsCard
                }
                .frame(width: 360)
            }
        }
    }

    // MARK: - Section Header
    private var sectionHeader: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack(spacing: 7) {
                Circle()
                    .fill(Color.fmA1)
                    .frame(width: 6, height: 6)
                    .shadow(color: Color.fmA1, radius: 4)

                Text("材料导入")
                    .font(.system(size: 14, weight: .heavy))
                    .foregroundColor(.fmText)
                    .tracking(-0.01)
            }

            Text("支持音频、视频、文字笔记、表格，AI 自动转录与关键词提炼")
                .font(.system(size: 10))
                .foregroundColor(.fmText3)
                .tracking(0.02)
        }
        .padding(.bottom, 16)
    }

    // MARK: - Upload Zone
    private var uploadZone: some View {
        VStack(spacing: 16) {
            // 上传图标
            ZStack {
                Circle()
                    .fill(isDragging ? Color.fmA1.opacity(0.2) : Color.fmA1.opacity(0.12))
                    .frame(width: 64, height: 64)

                Image(systemName: "arrow.down.doc.fill")
                    .font(.system(size: 28, weight: .medium))
                    .foregroundColor(isDragging ? .fmA1 : .fmA1.opacity(0.7))
            }

            VStack(spacing: 6) {
                Text(isDragging ? "松开以上传文件" : "拖拽文件到这里上传")
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundColor(.fmText)

                Text("支持拖拽或点击选择文件")
                    .font(.system(size: 12))
                    .foregroundColor(.fmText3)
            }

            // 支持的文件类型
            HStack(spacing: 6) {
                ForEach(["MP3", "MP4", "WAV", "MD", "XLSX", "PDF"], id: \.self) { type in
                    Text(type)
                        .font(.system(size: 9, weight: .bold))
                        .foregroundColor(.fmA1)
                        .padding(EdgeInsets(top: 3, leading: 8, bottom: 3, trailing: 8))
                        .background(Color.fmA1Dim)
                        .cornerRadius(10)
                }
            }

            // 上传进度（如果正在上传）
            if appState.isUploading {
                VStack(spacing: 8) {
                    HStack {
                        Text("正在处理...")
                            .font(.system(size: 11, weight: .semibold))
                            .foregroundColor(.fmText2)

                        Spacer()

                        Text("\(Int(appState.uploadProgress * 100))%")
                            .font(.system(size: 10, weight: .bold))
                            .foregroundColor(.fmA1)
                            .monospacedDigit()
                    }

                    GeometryReader { geometry in
                        ZStack(alignment: .leading) {
                            RoundedRectangle(cornerRadius: 4)
                                .fill(Color.fmSurface2)
                                .frame(height: 8)

                            RoundedRectangle(cornerRadius: 4)
                                .fill(Color.fmA1)
                                .frame(width: geometry.size.width * appState.uploadProgress, height: 8)
                        }
                    }
                    .frame(height: 8)

                    Text(appState.uploadingFileName)
                        .font(.system(size: 10))
                        .foregroundColor(.fmText3)
                        .lineLimit(1)
                }
                .padding(.top, 8)
            }
        }
        .frame(maxWidth: .infinity)
        .padding(EdgeInsets(top: 40, leading: 32, bottom: 40, trailing: 32))
        .background(
            RoundedRectangle(cornerRadius: FMRadius.lg)
                .fill(isDragging ? Color.fmA1Dim : Color.fmSurface)
                .overlay(
                    RoundedRectangle(cornerRadius: FMRadius.lg)
                        .stroke(
                            isDragging ? Color.fmA1 : Color.fmBorder2,
                            style: StrokeStyle(lineWidth: 2, dash: [8, 4])
                        )
                )
        )
        .shadow(color: Color.fmA1.opacity(0.07), radius: 6, x: 0, y: 2)
        .onDrop(of: [.fileURL], isTargeted: $isDragging) { providers in
            handleDrop(providers: providers)
            return true
        }
        .onTapGesture {
            selectFiles()
        }
    }

    // MARK: - AI Settings Card
    private var aiSettingsCard: some View {
        FMCard {
            VStack(spacing: 0) {
                HStack {
                    Text("AI 处理设置")
                        .font(.system(size: 13, weight: .bold))
                        .foregroundColor(.fmText)

                    Spacer()
                }
                .padding(EdgeInsets(top: 16, leading: 16, bottom: 12, trailing: 16))

                VStack(spacing: 9) {
                    SettingToggle(isOn: $autoTranscribe, label: "自动语音转录")
                    SettingToggle(isOn: $autoKeyword, label: "关键词自动提炼")
                    SettingToggle(isOn: $autoTimecode, label: "时间码精确定位")
                    SettingToggle(isOn: $autoSummary, label: "自动生成摘要")
                    SettingToggle(isOn: $autoLinkKeywords, label: "关联已有关键词")
                }
                .padding(EdgeInsets(top: 0, leading: 16, bottom: 16, trailing: 16))
            }
        }
    }

    // MARK: - Stats Card
    private var statsCard: some View {
        FMCard {
            VStack(spacing: 0) {
                HStack {
                    Text("快速统计")
                        .font(.system(size: 13, weight: .bold))
                        .foregroundColor(.fmText)

                    Spacer()
                }
                .padding(EdgeInsets(top: 16, leading: 16, bottom: 12, trailing: 16))

                VStack(spacing: 8) {
                    QuickStat(label: "本月上传", value: "47", color: .fmA1)
                    QuickStat(label: "本周处理", value: "8", color: .fmA2)
                    QuickStat(label: "待处理", value: "1", color: .fmText3)
                    QuickStat(label: "已完成", value: "46", color: .fmA2)
                }
                .padding(EdgeInsets(top: 0, leading: 16, bottom: 16, trailing: 16))
            }
        }
    }

    // MARK: - Recent Uploads Card
    private var recentUploadsCard: some View {
        FMCard {
            VStack(spacing: 0) {
                HStack {
                    Text("最近上传")
                        .font(.system(size: 13, weight: .bold))
                        .foregroundColor(.fmText)

                    Spacer()

                    Button(action: {
                        appState.navigateTo(.fileManager)
                    }) {
                        Text("查看全部")
                            .font(.system(size: 9))
                            .foregroundColor(.fmText3)
                    }
                    .buttonStyle(FMButtonStyle(style: .ghost, size: .small))
                }
                .padding(EdgeInsets(top: 16, leading: 16, bottom: 12, trailing: 16))

                VStack(spacing: 0) {
                    ForEach(appState.materials.prefix(5)) { material in
                        RecentUploadRow(material: material)
                            .padding(EdgeInsets(top: 8, leading: 12, bottom: 8, trailing: 12))
                    }
                }
            }
        }
    }

    // MARK: - File Handling
    private func handleDrop(providers: [NSItemProvider]) {
        Task { @MainActor in
            isDragging = false
            var urls: [URL] = []
            for provider in providers {
                if let url = await loadDroppedURL(from: provider) {
                    urls.append(url)
                }
            }
            let files = UploadFileSelectionHelper.collectUploadableFiles(from: urls)
            guard !files.isEmpty else {
                appState.showToast(message: "未能读取拖入的文件", type: .error)
                return
            }
            for file in files {
                uploadFile(url: file)
            }
        }
    }

    private nonisolated func loadDroppedURL(from provider: NSItemProvider) async -> URL? {
        guard provider.canLoadObject(ofClass: URL.self) else { return nil }
        return await withCheckedContinuation { continuation in
            _ = provider.loadObject(ofClass: URL.self) { object, _ in
                continuation.resume(returning: object)
            }
        }
    }

    private func selectFiles() {
        let panel = NSOpenPanel()
        panel.allowsMultipleSelection = true
        panel.canChooseDirectories = true
        panel.allowedContentTypes = [
            .mp3, .mpeg4Audio, .wav,
            .plainText, .pdf,
            UTType(filenameExtension: "xlsx")!,
            UTType(filenameExtension: "md")!
        ]

        if panel.runModal() == .OK {
            let files = UploadFileSelectionHelper.collectUploadableFiles(from: panel.urls)
            for url in files {
                uploadFile(url: url)
            }
        }
    }

    private func uploadFile(url: URL) {
        guard let projectId = appState.currentProject?.id else {
            appState.showToast(message: "请先选择项目", type: .error)
            return
        }

        appState.isUploading = true
        appState.uploadProgress = 0.0
        appState.uploadingFileName = url.lastPathComponent

        Task {
            do {
                // 上传文档
                let response = try await DocumentService.shared.uploadDocument(
                    projectId: projectId,
                    fileURL: url,
                    autoProcess: true
                )

                await MainActor.run {
                    appState.uploadProgress = 1.0
                    appState.isUploading = false
                    appState.showToast(message: "文件上传成功：\(url.lastPathComponent)", type: .success)

                    // 创建Material对象并添加到列表
                    let newMaterial = Material(
                        id: String(response.id),
                        name: response.filename,
                        type: mapFileType(response.fileType),
                        size: formatFileSize(response.fileSize),
                        duration: nil,
                        keywordCount: 0,
                        status: mapStatus(response.status),
                        uploadedAt: Date()
                    )
                    appState.materials.insert(newMaterial, at: 0)
                }
            } catch {
                await MainActor.run {
                    appState.isUploading = false
                    appState.showToast(message: "上传失败：\(error.localizedDescription)", type: .error)
                }
            }
        }
    }

    private func mapFileType(_ type: String) -> MaterialType {
        switch type.lowercased() {
        case "audio", "mp3", "wav", "m4a":
            return .audio
        case "video", "mp4", "mov", "avi":
            return .video
        case "spreadsheet", "xlsx", "xls", "csv":
            return .spreadsheet
        case "image", "jpg", "jpeg", "png", "gif":
            return .image
        default:
            return .document
        }
    }

    private func mapStatus(_ status: String) -> Material.MaterialStatus {
        switch status.lowercased() {
        case "pending":
            return .pending
        case "processing":
            return .processing
        case "completed":
            return .completed
        case "failed":
            return .failed
        default:
            return .pending
        }
    }

    private func formatFileSize(_ bytes: Int64) -> String {
        let formatter = ByteCountFormatter()
        formatter.allowedUnits = [.useKB, .useMB, .useGB]
        formatter.countStyle = .file
        return formatter.string(fromByteCount: bytes)
    }
}

// MARK: - Setting Toggle
struct SettingToggle: View {
    @Binding var isOn: Bool
    let label: String

    var body: some View {
        Toggle(isOn: $isOn) {
            Text(label)
                .font(.system(size: 11))
                .foregroundColor(.fmText2)
        }
        .toggleStyle(.checkbox)
        .tint(.fmA1)
    }
}

// MARK: - Quick Stat
struct QuickStat: View {
    let label: String
    let value: String
    let color: Color

    var body: some View {
        HStack {
            Text(label)
                .font(.system(size: 11, weight: .medium))
                .foregroundColor(.fmText2)

            Spacer()

            Text(value)
                .font(.system(size: 16, weight: .heavy))
                .foregroundColor(color)
                .monospacedDigit()
        }
        .padding(EdgeInsets(top: 8, leading: 12, bottom: 8, trailing: 12))
        .background(Color.fmSurface2)
        .cornerRadius(6)
    }
}

// MARK: - Recent Upload Row
struct RecentUploadRow: View {
    let material: Material

    var body: some View {
        HStack(spacing: 10) {
            ZStack {
                RoundedRectangle(cornerRadius: 6)
                    .fill(iconBackgroundColor)
                    .frame(width: 32, height: 32)

                Image(systemName: material.type.icon)
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(iconColor)
            }

            VStack(alignment: .leading, spacing: 2) {
                Text(material.name)
                    .font(.system(size: 10, weight: .medium))
                    .foregroundColor(.fmText)
                    .lineLimit(1)

                Text(timeAgo)
                    .font(.system(size: 9))
                    .foregroundColor(.fmText4)
            }

            Spacer()

            Text((material.status ?? .pending).displayName)
                .font(.system(size: 12))
                .foregroundColor(statusColor(material.status ?? .pending))
                .padding(.horizontal, 8)
                .padding(.vertical, 4)
                .background(statusColor(material.status ?? .pending).opacity(0.1))
                .cornerRadius(4)
        }
    }

    private func statusColor(_ status: Material.MaterialStatus) -> Color {
        switch status {
        case .completed: return .green
        case .processing: return .blue
        case .pending: return .orange
        case .failed: return .red
        }
    }

    private var iconBackgroundColor: Color {
        switch material.type {
        case .text: return Color.fmBg2
        case .audio: return Color.fmA1Dim2
        case .video: return Color.fmA2Dim2
        case .document: return Color.fmA5Dim2
        case .spreadsheet: return Color.fmA3Dim2
        case .image: return Color.fmA1Dim2
        }
    }

    private var iconColor: Color {
        switch material.type {
        case .text: return .fmText2
        case .audio: return .fmA1
        case .video: return .fmA2
        case .document: return .fmA5
        case .spreadsheet: return .fmA3
        case .image: return .fmA1
        }
    }

    private var timeAgo: String {
        let interval = Date().timeIntervalSince(material.uploadedAt)
        let hours = Int(interval / 3600)
        let days = Int(interval / 86400)

        if days > 0 {
            return "\(days) 天前"
        } else if hours > 0 {
            return "\(hours) 小时前"
        } else {
            return "刚刚"
        }
    }
}
