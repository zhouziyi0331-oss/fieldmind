"""
文档上传视图
拖拽上传 + 批量处理 + 进度追踪
"""
import SwiftUI
import UniformTypeIdentifiers

// MARK: - ViewModel
class DocumentUploadViewModel: ObservableObject {
    @Published var uploadQueue: [UploadFile] = []
    @Published var isDragging: Bool = false

    func handleDrop(providers: [NSItemProvider]) {
        for provider in providers {
            provider.loadFileRepresentation(forTypeIdentifier: UTType.item.identifier) { url, error in
                guard let url = url else { return }

                DispatchQueue.main.async {
                    let file = UploadFile(
                        name: url.lastPathComponent,
                        url: url,
                        fileSize: self.getFileSize(url: url),
                        status: .pending
                    )
                    self.uploadQueue.append(file)
                }
            }
        }
    }

    func selectFiles() {
        let panel = NSOpenPanel()
        panel.allowsMultipleSelection = true
        panel.canChooseDirectories = false
        panel.canChooseFiles = true

        if panel.runModal() == .OK {
            for url in panel.urls {
                let file = UploadFile(
                    name: url.lastPathComponent,
                    url: url,
                    fileSize: getFileSize(url: url),
                    status: .pending
                )
                uploadQueue.append(file)
            }
        }
    }

    func startUpload() {
        for i in uploadQueue.indices where uploadQueue[i].status == .pending {
            uploadQueue[i].status = .uploading
            uploadFile(at: i)
        }
    }

    private func uploadFile(at index: Int) {
        guard index < uploadQueue.count else { return }

        let file = uploadQueue[index]

        Task {
            do {
                // 使用真实的 DocumentService 上传
                _ = try await DocumentService.shared.uploadDocument(
                    projectId: 1, // TODO: 从实际项目中获取
                    fileURL: file.url,
                    autoProcess: true,
                    progressHandler: { progress in
                        // 实时更新真实上传进度
                        DispatchQueue.main.async {
                            if index < self.uploadQueue.count {
                                self.uploadQueue[index].progress = progress

                                if progress >= 1.0 {
                                    self.uploadQueue[index].status = .completed
                                }
                            }
                        }
                    }
                )
            } catch {
                DispatchQueue.main.async {
                    if index < self.uploadQueue.count {
                        self.uploadQueue[index].status = .failed
                    }
                }
                DebugLogger.shared.log("上传文件失败: \(file.name)", type: .error, details: error.localizedDescription)
            }
        }
    }

    func cancelUpload(file: UploadFile) {
        uploadQueue.removeAll { $0.id == file.id }
    }

    func clearCompleted() {
        uploadQueue.removeAll { $0.status == .completed }
    }

    func pauseAll() {
        for i in uploadQueue.indices where uploadQueue[i].status == .uploading {
            uploadQueue[i].status = .paused
        }
    }

    func resumeAll() {
        for i in uploadQueue.indices where uploadQueue[i].status == .paused {
            uploadQueue[i].status = .uploading
            uploadFile(at: i)
        }
    }

    private func getFileSize(url: URL) -> Int {
        do {
            let attributes = try FileManager.default.attributesOfItem(atPath: url.path)
            return attributes[.size] as? Int ?? 0
        } catch {
            return 0
        }
    }
}

// MARK: - 数据模型
struct UploadFile: Identifiable {
    let id = UUID()
    let name: String
    let url: URL
    let fileSize: Int
    var status: UploadStatus
    var progress: Double = 0.0

    var icon: String {
        let ext = url.pathExtension.lowercased()
        switch ext {
        case "pdf": return "doc.text.fill"
        case "doc", "docx": return "doc.richtext"
        case "xls", "xlsx": return "tablecells"
        case "jpg", "jpeg", "png": return "photo"
        case "mp3", "wav": return "waveform"
        case "mp4", "mov": return "video"
        default: return "doc"
        }
    }

    var fileSizeFormatted: String {
        let formatter = ByteCountFormatter()
        formatter.countStyle = .file
        return formatter.string(fromByteCount: Int64(fileSize))
    }
}

enum UploadStatus {
    case pending, uploading, paused, completed, failed

    var description: String {
        switch self {
        case .pending: return "等待中"
        case .uploading: return "上传中"
        case .paused: return "已暂停"
        case .completed: return "已完成"
        case .failed: return "失败"
        }
    }
}

// MARK: - 主视图
struct DocumentUploadView: View {
    @StateObject var viewModel = DocumentUploadViewModel()
    @Environment(\.dismiss) var dismiss

    var body: some View {
        VStack(spacing: 0) {
            // 顶部栏
            HStack {
                Text("文档上传")
                    .font(Typography.h3)

                Spacer()

                Button {
                    dismiss()
                } label: {
                    Image(systemName: "xmark")
                }
                .buttonStyle(.plain)
            }
            .padding(Spacing.lg)
            .background(Color.fmBgPrimary)

            Divider()

            ScrollView {
                VStack(spacing: Spacing.xl) {
                    // 拖拽上传区域
                    DropZoneView(
                        isDragging: $viewModel.isDragging,
                        onDrop: viewModel.handleDrop,
                        onSelectFiles: viewModel.selectFiles
                    )
                    .padding(Spacing.xl)

                    // 上传队列
                    if !viewModel.uploadQueue.isEmpty {
                        VStack(spacing: 0) {
                            HStack {
                                Text("上传队列 (\(viewModel.uploadQueue.count) 个文件)")
                                    .font(Typography.h4)

                                Spacer()

                                Button("清空已完成") {
                                    viewModel.clearCompleted()
                                }
                                .buttonStyle(.bordered)
                                .font(Typography.caption)
                            }
                            .padding(.horizontal, Spacing.lg)
                            .padding(.bottom, Spacing.md)

                            VStack(spacing: Spacing.sm) {
                                ForEach(viewModel.uploadQueue) { file in
                                    UploadQueueItem(
                                        file: file,
                                        onCancel: {
                                            viewModel.cancelUpload(file: file)
                                        }
                                    )
                                }
                            }
                            .padding(.horizontal, Spacing.lg)
                        }
                    }
                }
            }
            .background(Color.fmBgSecondary)

            // 底部操作栏
            if !viewModel.uploadQueue.isEmpty {
                Divider()

                HStack(spacing: Spacing.md) {
                    Button("暂停全部") {
                        viewModel.pauseAll()
                    }
                    .buttonStyle(.bordered)

                    Button("继续全部") {
                        viewModel.resumeAll()
                    }
                    .buttonStyle(.bordered)

                    Button("清空队列") {
                        viewModel.uploadQueue.removeAll()
                    }
                    .buttonStyle(.bordered)

                    Spacer()

                    Button("开始上传") {
                        viewModel.startUpload()
                    }
                    .buttonStyle(.borderedProminent)
                }
                .padding(Spacing.lg)
                .background(Color.fmBgPrimary)
            }
        }
        .frame(width: 700, height: 600)
    }
}

// MARK: - 拖拽区域
struct DropZoneView: View {
    @Binding var isDragging: Bool
    let onDrop: ([NSItemProvider]) -> Void
    let onSelectFiles: () -> Void

    var body: some View {
        VStack(spacing: Spacing.lg) {
            Image(systemName: "arrow.down.doc")
                .font(.system(size: 48))
                .foregroundColor(isDragging ? .fmAccent : .fmTextSecondary)

            Text("将文件拖拽到此处")
                .font(Typography.h4)
                .foregroundColor(.fmTextPrimary)

            Text("或")
                .font(Typography.body)
                .foregroundColor(.fmTextSecondary)

            HStack(spacing: Spacing.md) {
                Button("选择文件") {
                    onSelectFiles()
                }
                .buttonStyle(.bordered)

                Button("选择文件夹") {
                    // TODO: 实现文件夹选择
                }
                .buttonStyle(.bordered)
            }

            VStack(spacing: 4) {
                Text("支持格式: PDF, Word, Excel, TXT, Markdown, 图片, 音视频")
                    .font(Typography.caption)
                    .foregroundColor(.fmTextSecondary)

                Text("最大单文件: 50MB")
                    .font(Typography.caption)
                    .foregroundColor(.fmTextSecondary)
            }
        }
        .frame(maxWidth: .infinity, minHeight: 300)
        .background(
            RoundedRectangle(cornerRadius: 12)
                .strokeBorder(
                    style: StrokeStyle(lineWidth: 2, dash: [8])
                )
                .foregroundColor(isDragging ? .fmAccent : .fmBorder)
        )
        .background(
            isDragging ? Color.fmAccent.opacity(0.05) : Color.clear
        )
        .onDrop(of: [.fileURL], isTargeted: $isDragging) { providers in
            onDrop(providers)
            return true
        }
    }
}

// MARK: - 上传队列项
struct UploadQueueItem: View {
    let file: UploadFile
    let onCancel: () -> Void

    var body: some View {
        HStack(spacing: Spacing.md) {
            Image(systemName: file.icon)
                .font(.title2)
                .foregroundColor(.fmAccent)
                .frame(width: 40)

            VStack(alignment: .leading, spacing: 6) {
                Text(file.name)
                    .font(Typography.body)
                    .foregroundColor(.fmTextPrimary)
                    .lineLimit(1)

                if file.status == .uploading {
                    ProgressView(value: file.progress)
                        .progressViewStyle(.linear)
                        .tint(.fmAccent)

                    HStack {
                        Text("\(Int(file.progress * 100))%")
                            .font(Typography.caption)
                            .foregroundColor(.fmTextSecondary)

                        Spacer()

                        Text(file.fileSizeFormatted)
                            .font(Typography.caption)
                            .foregroundColor(.fmTextSecondary)
                    }
                } else {
                    HStack {
                        Text(file.status.description)
                            .font(Typography.caption)
                            .foregroundColor(.fmTextSecondary)

                        Spacer()

                        Text(file.fileSizeFormatted)
                            .font(Typography.caption)
                            .foregroundColor(.fmTextSecondary)
                    }
                }
            }

            Button {
                onCancel()
            } label: {
                Image(systemName: "xmark.circle.fill")
                    .foregroundColor(.fmTextSecondary)
            }
            .buttonStyle(.plain)
        }
        .padding(Spacing.md)
        .background(Color.fmBgPrimary)
        .cornerRadius(8)
    }
}

// MARK: - 预览
struct DocumentUploadView_Previews: PreviewProvider {
    static var previews: some View {
        DocumentUploadView()
    }
}
