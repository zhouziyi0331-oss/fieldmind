import SwiftUI
import UniformTypeIdentifiers

struct DocumentsView: View {
    @EnvironmentObject var appState: AppState
    @ObservedObject private var dataManager = ProjectDataManager.shared
    @State private var selectedFilter: DocumentFilter = .all
    @State private var isDragging = false
    @State private var uploadingFiles: [String: UploadProgress] = [:]

    enum DocumentFilter: String, CaseIterable {
        case all = "全部"
        case pending = "待处理"
        case processing = "处理中"
        case completed = "已完成"
        case failed = "失败"
    }

    struct UploadProgress {
        var isUploading: Bool
        var fileName: String
    }

    var filteredDocuments: [Document] {
        let docs = dataManager.documents
        switch selectedFilter {
        case .all: return docs
        case .pending: return docs.filter { $0.status == .pending }
        case .processing: return docs.filter { $0.status == .processing }
        case .completed: return docs.filter { $0.status == .completed }
        case .failed: return docs.filter { $0.status == .failed }
        }
    }

    var body: some View {
        VStack(spacing: 0) {
            // 工具栏
            HStack {
                // 过滤器
                Picker("", selection: $selectedFilter) {
                    ForEach(DocumentFilter.allCases, id: \.self) { filter in
                        Text(filter.rawValue).tag(filter)
                    }
                }
                .pickerStyle(.segmented)
                .frame(width: 400)

                Spacer()

                Button(action: selectFilesToUpload) {
                    Label("导入材料", systemImage: "arrow.up.doc")
                }
                .buttonStyle(.borderedProminent)
                .tint(Color(hex: "48bb78"))
                .disabled(appState.currentProject == nil)
            }
            .padding()
            .background(Color(NSColor.controlBackgroundColor))

            Divider()

            // 上传进度显示
            if !uploadingFiles.isEmpty {
                VStack(alignment: .leading, spacing: 8) {
                    ForEach(Array(uploadingFiles.keys), id: \.self) { key in
                        if let progress = uploadingFiles[key] {
                            HStack {
                                ProgressView()
                                    .scaleEffect(0.7)
                                Text("正在上传: \(progress.fileName)")
                                    .font(.system(size: 12))
                            }
                            .padding(.horizontal, 24)
                        }
                    }
                }
                .padding(.vertical, 12)
                .background(Color.blue.opacity(0.1))
            }

            // 拖拽区域提示
            if isDragging {
                VStack {
                    Image(systemName: "arrow.down.doc.fill")
                        .font(.system(size: 48))
                        .foregroundColor(Color(hex: "48bb78"))
                    Text("释放以上传文件")
                        .font(.system(size: 16, weight: .medium))
                        .foregroundColor(.gray)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
                .background(Color(hex: "48bb78").opacity(0.1))
            } else {
                // 文档列表
                if appState.currentProject == nil {
                    EmptyStateView(icon: "folder.badge.questionmark", message: "请先选择一个项目")
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else if dataManager.isLoadingDocuments {
                    ProgressView("加载文档中...")
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else if filteredDocuments.isEmpty {
                    VStack(spacing: 16) {
                        Image(systemName: "doc.badge.plus")
                            .font(.system(size: 48))
                            .foregroundColor(.gray)
                        Text("暂无文档")
                            .font(.system(size: 16, weight: .medium))
                            .foregroundColor(.gray)
                        Text("拖拽文件到此处或点击\"导入材料\"按钮")
                            .font(.system(size: 12))
                            .foregroundColor(.gray.opacity(0.8))
                    }
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else {
                    ScrollView {
                        LazyVStack(spacing: 12) {
                            ForEach(filteredDocuments) { document in
                                DocumentRow(
                                    document: document,
                                    onDelete: {
                                        deleteDocument(document)
                                    }
                                )
                            }
                        }
                        .padding(24)
                    }
                }
            }
        }
        .onDrop(of: [.fileURL], isTargeted: $isDragging) { providers in
            handleDrop(providers: providers)
            return true
        }
        .onChange(of: appState.currentProject?.id) { newProjectId in
            // 项目切换时，重新加载数据
            if let projectId = newProjectId {
                dataManager.loadDocuments(projectId: projectId)
            }
        }
    }

    // MARK: - 文件上传

    private func selectFilesToUpload() {
        let panel = NSOpenPanel()
        panel.allowsMultipleSelection = true
        panel.canChooseDirectories = false
        panel.canChooseFiles = true
        panel.allowedContentTypes = [
            .pdf, .plainText, .rtf,
            .audio, .movie, .mpeg4Movie,  // 添加音频和视频支持
            UTType(filenameExtension: "mp3") ?? .audio,
            UTType(filenameExtension: "mp4") ?? .movie,
            UTType(filenameExtension: "wav") ?? .audio,
            UTType(filenameExtension: "m4a") ?? .audio,
            UTType(filenameExtension: "doc") ?? .data,
            UTType(filenameExtension: "docx") ?? .data,
            UTType(filenameExtension: "txt") ?? .plainText,
            UTType(filenameExtension: "md") ?? .plainText,
            UTType(filenameExtension: "xlsx") ?? .data,
            UTType(filenameExtension: "xls") ?? .data
        ]

        panel.begin { response in
            if response == .OK {
                for url in panel.urls {
                    uploadDocument(fileURL: url)
                }
            }
        }
    }

    private func handleDrop(providers: [NSItemProvider]) {
        for provider in providers {
            provider.loadItem(forTypeIdentifier: UTType.fileURL.identifier, options: nil) { item, error in
                if let data = item as? Data,
                   let url = URL(dataRepresentation: data, relativeTo: nil) {
                    DispatchQueue.main.async {
                        uploadDocument(fileURL: url)
                    }
                }
            }
        }
    }

    private func uploadDocument(fileURL: URL) {
        guard let projectId = appState.currentProject?.id else {
            ToastManager.shared.error("请先选择项目")
            return
        }

        let fileName = fileURL.lastPathComponent
        let key = UUID().uuidString
        uploadingFiles[key] = UploadProgress(isUploading: true, fileName: fileName)

        // 创建任务并添加到任务中心
        let taskId = UUID().uuidString
        let task = TaskManager.BackgroundTask(
            id: taskId,
            type: .documentUpload(filename: fileName),
            projectId: projectId,
            status: .running,
            progress: 0.0,
            title: "上传文档: \(fileName)",
            createdAt: Date()
        )
        TaskManager.shared.addTask(task)

        Task {
            do {
                // 更新上传进度
                TaskManager.shared.updateTask(id: taskId, status: .running, progress: 0.3)

                let response = try await dataManager.uploadDocument(projectId: projectId, fileURL: fileURL)

                // 更新处理进度
                TaskManager.shared.updateTask(id: taskId, status: .running, progress: 0.7)

                // 等待处理完成
                try await Task.sleep(nanoseconds: 1_000_000_000)

                await MainActor.run {
                    uploadingFiles.removeValue(forKey: key)
                    TaskManager.shared.updateTask(id: taskId, status: .completed, progress: 1.0)
                    ToastManager.shared.success("文档上传并处理完成")
                }
            } catch {
                await MainActor.run {
                    uploadingFiles.removeValue(forKey: key)
                    TaskManager.shared.updateTask(id: taskId, status: .failed(error.localizedDescription))
                    ToastManager.shared.error("上传失败: \(error.localizedDescription)")
                }
            }
        }
    }

    private func deleteDocument(_ document: Document) {
        Task {
            do {
                try await dataManager.deleteDocument(id: document.id)
                ToastManager.shared.success("文档已删除")
            } catch {
                ToastManager.shared.error("删除失败: \(error.localizedDescription)")
            }
        }
    }
}

struct DocumentRow: View {
    let document: Document
    let onDelete: () -> Void

    var body: some View {
        HStack(spacing: 16) {
            // 文件图标
            Image(systemName: fileIcon(for: document.filename))
                .font(.system(size: 32))
                .foregroundColor(fileColor(for: document.filename))
                .frame(width: 48)

            // 文件信息
            VStack(alignment: .leading, spacing: 4) {
                Text(document.filename)
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(Color.fieldMindText)

                HStack(spacing: 12) {
                    Text(formatFileSize(document.fileSize ?? 0))
                        .font(.system(size: 11))
                        .foregroundColor(.gray)

                    Text(formatDate(document.uploadedAt))
                        .font(.system(size: 11))
                        .foregroundColor(.gray)
                }
            }

            Spacer()

            // 状态标签
            StatusBadge(status: document.status)

            // 操作按钮
            Button(action: onDelete) {
                Image(systemName: "trash")
                    .font(.system(size: 12))
                    .foregroundColor(.red)
            }
            .buttonStyle(.plain)
            .help("删除文档")
        }
        .padding(16)
        .background(Color.white)
        .cornerRadius(8)
        .shadow(color: Color.black.opacity(0.05), radius: 2, x: 0, y: 1)
    }

    private func fileIcon(for filename: String) -> String {
        let ext = (filename as NSString).pathExtension.lowercased()
        switch ext {
        case "pdf": return "doc.fill"
        case "doc", "docx": return "doc.text.fill"
        case "txt": return "doc.plaintext.fill"
        default: return "doc.fill"
        }
    }

    private func fileColor(for filename: String) -> Color {
        let ext = (filename as NSString).pathExtension.lowercased()
        switch ext {
        case "pdf": return .red
        case "doc", "docx": return .blue
        case "txt": return .gray
        default: return Color(hex: "48bb78")
        }
    }

    private func formatFileSize(_ bytes: Int) -> String {
        let formatter = ByteCountFormatter()
        formatter.countStyle = .file
        return formatter.string(fromByteCount: Int64(bytes))
    }

    private func formatDate(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd HH:mm"
        return formatter.string(from: date)
    }
}

