import SwiftUI
import UniformTypeIdentifiers

struct AudioVideoView: View {
    @State private var tasks: [TranscriptionTask] = []
    @State private var selectedTask: TranscriptionTask?
    @State private var isDragging = false
    @State private var isUploading = false
    @State private var uploadProgress: Double = 0.0

    var body: some View {
        HStack(spacing: 0) {
            // 左侧：任务列表
            taskListSidebar
                .frame(width: 280)

            // 右侧：上传区域或任务详情
            if let task = selectedTask {
                taskDetailView(task: task)
            } else {
                uploadAreaView
            }
        }
        .background(Color.fieldMindBackground)
        .onAppear {
            loadTasks()
        }
    }

    // MARK: - 左侧任务列表
    private var taskListSidebar: some View {
        VStack(spacing: 0) {
            // 标题
            HStack {
                Text("转写任务")
                    .font(.system(size: 14, weight: .bold))
                    .foregroundColor(Color.fieldMindText)

                Spacer()

                Button {
                    selectedTask = nil
                } label: {
                    Image(systemName: "plus.circle.fill")
                        .font(.system(size: 18))
                        .foregroundColor(Color.fieldMindPrimary)
                }
                .buttonStyle(PlainButtonStyle())
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 14)
            .background(Color.white)
            .overlay(
                Rectangle()
                    .fill(Color.gray.opacity(0.1))
                    .frame(height: 1),
                alignment: .bottom
            )

            // 任务列表
            if tasks.isEmpty {
                Spacer()
                VStack(spacing: 8) {
                    Image(systemName: "waveform")
                        .font(.system(size: 32))
                        .foregroundColor(Color.fieldMindText.opacity(0.3))
                    Text("暂无转写任务")
                        .font(.system(size: 12))
                        .foregroundColor(Color.fieldMindText.opacity(0.5))
                }
                Spacer()
            } else {
                ScrollView(showsIndicators: false) {
                    VStack(spacing: 8) {
                        ForEach(tasks) { task in
                            taskListItem(task: task)
                        }
                    }
                    .padding(12)
                }
            }
        }
        .background(Color.white)
        .overlay(
            Rectangle()
                .fill(Color.gray.opacity(0.1))
                .frame(width: 1),
            alignment: .trailing
        )
    }

    private func taskListItem(task: TranscriptionTask) -> some View {
        Button {
            selectedTask = task
        } label: {
            VStack(alignment: .leading, spacing: 8) {
                HStack(spacing: 8) {
                    Image(systemName: task.fileType == .audio ? "waveform" : "video")
                        .font(.system(size: 12))
                        .foregroundColor(Color.fieldMindPrimary)

                    Text(task.fileName)
                        .font(.system(size: 12, weight: .medium))
                        .foregroundColor(Color.fieldMindText)
                        .lineLimit(1)

                    Spacer()

                    Text(task.status)
                        .font(.system(size: 10))
                        .foregroundColor(task.statusColor)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(task.statusColor.opacity(0.1))
                        .cornerRadius(4)
                }

                if task.status == "转写中" {
                    ProgressView(value: task.progress, total: 1.0)
                        .progressViewStyle(LinearProgressViewStyle(tint: Color.fieldMindPrimary))
                        .scaleEffect(x: 1, y: 0.5)
                }

                HStack(spacing: 12) {
                    if let duration = task.duration {
                        Label(duration, systemImage: "clock")
                            .font(.system(size: 10))
                            .foregroundColor(Color.fieldMindText.opacity(0.6))
                    }

                    if let wordCount = task.wordCount {
                        Label("\(wordCount)字", systemImage: "doc.text")
                            .font(.system(size: 10))
                            .foregroundColor(Color.fieldMindText.opacity(0.6))
                    }
                }
            }
            .padding(12)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(
                selectedTask?.id == task.id ?
                Color.fieldMindPrimary.opacity(0.08) : Color.fieldMindBackground
            )
            .cornerRadius(7)
            .overlay(
                RoundedRectangle(cornerRadius: 7)
                    .stroke(
                        selectedTask?.id == task.id ?
                        Color.fieldMindPrimary.opacity(0.3) : Color.clear,
                        lineWidth: 1
                    )
            )
        }
        .buttonStyle(PlainButtonStyle())
    }

    // MARK: - 上传区域
    private var uploadAreaView: some View {
        VStack(spacing: 24) {
            Spacer()

            // 拖拽上传区域
            VStack(spacing: 20) {
                Image(systemName: isDragging ? "arrow.down.circle.fill" : "waveform.circle.fill")
                    .font(.system(size: 64))
                    .foregroundColor(isDragging ? Color.fieldMindPrimary : Color.fieldMindText.opacity(0.3))

                VStack(spacing: 8) {
                    Text(isDragging ? "松开以上传文件" : "拖拽音视频文件到此处")
                        .font(.system(size: 14, weight: .medium))
                        .foregroundColor(Color.fieldMindText)

                    Text("支持 MP3, WAV, M4A, MP4, MOV, AVI 等格式")
                        .font(.system(size: 11))
                        .foregroundColor(Color.fieldMindText.opacity(0.6))
                }

                Button {
                    selectFile()
                } label: {
                    Text("或点击选择文件")
                        .font(.system(size: 12, weight: .medium))
                        .foregroundColor(.white)
                        .padding(.horizontal, 20)
                        .padding(.vertical, 10)
                        .background(Color.fieldMindPrimary)
                        .cornerRadius(6)
                }
                .buttonStyle(PlainButtonStyle())
            }
            .frame(maxWidth: 480, maxHeight: 320)
            .frame(maxWidth: .infinity)
            .background(
                RoundedRectangle(cornerRadius: 12)
                    .fill(isDragging ? Color.fieldMindPrimary.opacity(0.05) : Color.white)
                    .overlay(
                        RoundedRectangle(cornerRadius: 12)
                            .strokeBorder(
                                style: StrokeStyle(lineWidth: 2, dash: [8, 4])
                            )
                            .foregroundColor(
                                isDragging ? Color.fieldMindPrimary : Color.gray.opacity(0.3)
                            )
                    )
            )
            .onDrop(of: [.fileURL], isTargeted: $isDragging) { providers in
                return handleDrop(providers: providers)
            }

            // 上传进度
            if isUploading {
                VStack(spacing: 12) {
                    HStack(spacing: 12) {
                        ProgressView()
                            .scaleEffect(0.8)
                        Text("正在上传...")
                            .font(.system(size: 12))
                            .foregroundColor(Color.fieldMindText.opacity(0.7))
                    }

                    ProgressView(value: uploadProgress, total: 1.0)
                        .progressViewStyle(LinearProgressViewStyle(tint: Color.fieldMindPrimary))
                        .frame(maxWidth: 300)
                }
                .padding(16)
                .background(Color.white)
                .cornerRadius(8)
            }

            Spacer()
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .padding(24)
        .background(Color.fieldMindBackground)
    }

    // MARK: - 任务详情视图
    private func taskDetailView(task: TranscriptionTask) -> some View {
        ScrollView(showsIndicators: false) {
            VStack(alignment: .leading, spacing: 24) {
                // 顶部操作栏
                HStack {
                    Button {
                        selectedTask = nil
                    } label: {
                        HStack(spacing: 6) {
                            Image(systemName: "chevron.left")
                                .font(.system(size: 11))
                            Text("返回列表")
                                .font(.system(size: 12))
                        }
                        .foregroundColor(Color.fieldMindText.opacity(0.6))
                    }
                    .buttonStyle(PlainButtonStyle())

                    Spacer()

                    HStack(spacing: 12) {
                        if task.status == "已完成" {
                            Button {
                                exportTranscription(task: task)
                            } label: {
                                HStack(spacing: 6) {
                                    Image(systemName: "square.and.arrow.down")
                                        .font(.system(size: 11))
                                    Text("导出")
                                        .font(.system(size: 12))
                                }
                                .foregroundColor(.white)
                                .padding(.horizontal, 12)
                                .padding(.vertical, 7)
                                .background(Color.fieldMindPrimary)
                                .cornerRadius(6)
                            }
                            .buttonStyle(PlainButtonStyle())
                        }

                        Menu {
                            Button("删除任务") {
                                deleteTask(task: task)
                            }
                        } label: {
                            Image(systemName: "ellipsis")
                                .font(.system(size: 14))
                                .foregroundColor(Color.fieldMindText.opacity(0.6))
                                .frame(width: 32, height: 32)
                                .background(Color.fieldMindBackground)
                                .cornerRadius(6)
                        }
                        .menuStyle(BorderlessButtonMenuStyle())
                    }
                }

                // 文件信息卡片
                VStack(alignment: .leading, spacing: 16) {
                    HStack(spacing: 10) {
                        Image(systemName: task.fileType == .audio ? "waveform.circle.fill" : "video.circle.fill")
                            .font(.system(size: 20))
                            .foregroundColor(Color.fieldMindPrimary)

                        Text(task.fileName)
                            .font(.system(size: 16, weight: .semibold))
                            .foregroundColor(Color.fieldMindText)

                        Spacer()

                        Text(task.status)
                            .font(.system(size: 11))
                            .foregroundColor(task.statusColor)
                            .padding(.horizontal, 10)
                            .padding(.vertical, 5)
                            .background(task.statusColor.opacity(0.1))
                            .cornerRadius(5)
                    }

                    if task.status == "转写中" {
                        VStack(alignment: .leading, spacing: 8) {
                            HStack {
                                Text("转写进度")
                                    .font(.system(size: 11))
                                    .foregroundColor(Color.fieldMindText.opacity(0.6))
                                Spacer()
                                Text("\(Int(task.progress * 100))%")
                                    .font(.system(size: 11, weight: .medium))
                                    .foregroundColor(Color.fieldMindPrimary)
                            }
                            ProgressView(value: task.progress, total: 1.0)
                                .progressViewStyle(LinearProgressViewStyle(tint: Color.fieldMindPrimary))
                        }
                    }

                    HStack(spacing: 20) {
                        if let duration = task.duration {
                            VStack(alignment: .leading, spacing: 4) {
                                Text("时长")
                                    .font(.system(size: 10))
                                    .foregroundColor(Color.fieldMindText.opacity(0.6))
                                Text(duration)
                                    .font(.system(size: 12, weight: .medium))
                                    .foregroundColor(Color.fieldMindText)
                            }
                        }

                        if let wordCount = task.wordCount {
                            VStack(alignment: .leading, spacing: 4) {
                                Text("字数")
                                    .font(.system(size: 10))
                                    .foregroundColor(Color.fieldMindText.opacity(0.6))
                                Text("\(wordCount)")
                                    .font(.system(size: 12, weight: .medium))
                                    .foregroundColor(Color.fieldMindText)
                            }
                        }

                        VStack(alignment: .leading, spacing: 4) {
                            Text("上传时间")
                                .font(.system(size: 10))
                                .foregroundColor(Color.fieldMindText.opacity(0.6))
                            Text(task.uploadedAt)
                                .font(.system(size: 12, weight: .medium))
                                .foregroundColor(Color.fieldMindText)
                        }
                    }
                }
                .padding(20)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(Color.white)
                .cornerRadius(10)

                // 转写结果
                if task.status == "已完成", let transcription = task.transcription {
                    VStack(alignment: .leading, spacing: 14) {
                        HStack {
                            Text("转写结果")
                                .font(.system(size: 14, weight: .bold))
                                .foregroundColor(Color.fieldMindText)

                            Spacer()

                            Button {
                                // 编辑
                            } label: {
                                HStack(spacing: 6) {
                                    Image(systemName: "pencil")
                                        .font(.system(size: 10))
                                    Text("编辑")
                                        .font(.system(size: 11))
                                }
                                .foregroundColor(Color.fieldMindPrimary)
                                .padding(.horizontal, 10)
                                .padding(.vertical, 6)
                                .background(Color.fieldMindPrimary.opacity(0.1))
                                .cornerRadius(5)
                            }
                            .buttonStyle(PlainButtonStyle())
                        }

                        VStack(alignment: .leading, spacing: 12) {
                            ForEach(transcription.segments, id: \.timestamp) { segment in
                                transcriptionSegment(segment: segment)
                            }
                        }
                        .padding(16)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .background(Color.white)
                        .cornerRadius(7)
                    }
                }
            }
            .padding(24)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color.fieldMindBackground)
    }

    private func transcriptionSegment(segment: TranscriptionSegment) -> some View {
        HStack(alignment: .top, spacing: 12) {
            // 时间轴
            Text(segment.timestamp)
                .font(.system(size: 10, weight: .medium, design: .monospaced))
                .foregroundColor(Color.fieldMindPrimary)
                .frame(width: 60, alignment: .leading)

            // 说话人标注
            if let speaker = segment.speaker {
                Text(speaker)
                    .font(.system(size: 10, weight: .medium))
                    .foregroundColor(Color.fieldMindSuccess)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(Color.fieldMindSuccess.opacity(0.1))
                    .cornerRadius(4)
            }

            // 转写文本
            Text(segment.text)
                .font(.system(size: 12))
                .foregroundColor(Color.fieldMindText)
                .frame(maxWidth: .infinity, alignment: .leading)
        }
        .padding(.vertical, 8)
    }

    // MARK: - 文件处理
    private func selectFile() {
        let panel = NSOpenPanel()
        panel.allowsMultipleSelection = false
        panel.canChooseDirectories = false
        panel.allowedContentTypes = [
            .audio, .movie,
            UTType(filenameExtension: "mp3")!,
            UTType(filenameExtension: "wav")!,
            UTType(filenameExtension: "m4a")!,
            UTType(filenameExtension: "mp4")!,
            UTType(filenameExtension: "mov")!,
            UTType(filenameExtension: "avi")!
        ]

        if panel.runModal() == .OK, let url = panel.url {
            uploadFile(url: url)
        }
    }

    private func handleDrop(providers: [NSItemProvider]) -> Bool {
        guard let provider = providers.first else { return false }

        provider.loadItem(forTypeIdentifier: UTType.fileURL.identifier, options: nil) { item, error in
            guard let data = item as? Data,
                  let url = URL(dataRepresentation: data, relativeTo: nil) else {
                return
            }

            DispatchQueue.main.async {
                uploadFile(url: url)
            }
        }

        return true
    }

    private func uploadFile(url: URL) {
        isUploading = true
        uploadProgress = 0.0

        // TODO: 调用后端API /api/v1/audio/upload
        // 模拟上传进度
        Timer.scheduledTimer(withTimeInterval: 0.1, repeats: true) { timer in
            uploadProgress += 0.05
            if uploadProgress >= 1.0 {
                timer.invalidate()
                isUploading = false
                uploadProgress = 0.0

                // 添加新任务到列表
                let newTask = TranscriptionTask(
                    id: UUID().uuidString,
                    fileName: url.lastPathComponent,
                    fileType: url.pathExtension.contains("mp4") || url.pathExtension.contains("mov") ? .video : .audio,
                    status: "转写中",
                    progress: 0.3,
                    duration: "12:34",
                    wordCount: nil,
                    uploadedAt: "刚刚",
                    transcription: nil
                )
                tasks.insert(newTask, at: 0)
            }
        }
    }

    private func exportTranscription(task: TranscriptionTask) {
        // TODO: 导出转写结果
        print("Exporting transcription for: \(task.fileName)")
    }

    private func deleteTask(task: TranscriptionTask) {
        // TODO: 调用后端API DELETE /api/v1/audio/{id}
        tasks.removeAll { $0.id == task.id }
        selectedTask = nil
    }

    private func loadTasks() {
        // TODO: 调用后端API /api/v1/audio/tasks
        // 临时模拟数据
        tasks = [
            TranscriptionTask(
                id: "1",
                fileName: "田野调查访谈_村长.mp3",
                fileType: .audio,
                status: "已完成",
                progress: 1.0,
                duration: "45:23",
                wordCount: 8750,
                uploadedAt: "2024-03-20 14:30",
                transcription: Transcription(segments: [
                    TranscriptionSegment(
                        timestamp: "00:00:15",
                        speaker: "访谈者",
                        text: "您好，请问您在这个村子生活多久了？"
                    ),
                    TranscriptionSegment(
                        timestamp: "00:00:20",
                        speaker: "村长",
                        text: "我在这里生活了五十多年了，从小就在这里长大。"
                    ),
                    TranscriptionSegment(
                        timestamp: "00:00:28",
                        speaker: "访谈者",
                        text: "能和我们聊聊这个村子的历史吗？"
                    )
                ])
            ),
            TranscriptionTask(
                id: "2",
                fileName: "民族文化纪录片.mp4",
                fileType: .video,
                status: "转写中",
                progress: 0.65,
                duration: "1:23:15",
                wordCount: nil,
                uploadedAt: "2024-03-22 10:15",
                transcription: nil
            )
        ]
    }
}

// MARK: - 数据模型
struct TranscriptionTask: Identifiable {
    let id: String
    let fileName: String
    let fileType: FileType
    var status: String // 队列中, 转写中, 已完成, 失败
    var progress: Double
    let duration: String?
    let wordCount: Int?
    let uploadedAt: String
    let transcription: Transcription?

    enum FileType {
        case audio, video
    }

    var statusColor: Color {
        switch status {
        case "已完成": return Color.fieldMindSuccess
        case "转写中": return Color.fieldMindPrimary
        case "失败": return Color.fieldMindDanger
        default: return Color.fieldMindText.opacity(0.6)
        }
    }
}

struct Transcription {
    let segments: [TranscriptionSegment]
}

struct TranscriptionSegment {
    let timestamp: String
    let speaker: String?
    let text: String
}
