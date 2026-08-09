import SwiftUI

/// 文档处理状态指示器 - 显示5个阶段
struct DocumentProcessingStages: View {
    let documentId: Int
    @State private var status: ProcessingStatus?
    @State private var isLoading = true

    struct ProcessingStatus: Codable {
        let document_id: Int
        let status: String
        let progress: Int
        let stages: Stages
        let error: String?

        struct Stages: Codable {
            let extract: StageInfo
            let clean: StageInfo
            let chunk: StageInfo
            let vectorize: StageInfo
            let index: StageInfo

            struct StageInfo: Codable {
                let completed: Bool
                let count: Int?
            }
        }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("处理进度")
                .font(.system(size: 12, weight: .medium))
                .foregroundColor(.gray)

            if isLoading {
                ProgressView()
                    .scaleEffect(0.7)
            } else if let status = status {
                HStack(spacing: 6) {
                    StageIndicator(
                        name: "提取",
                        icon: "doc.text",
                        completed: status.stages.extract.completed,
                        isActive: status.status == "processing" && !status.stages.extract.completed
                    )

                    StageIndicator(
                        name: "清洗",
                        icon: "sparkles",
                        completed: status.stages.clean.completed,
                        isActive: status.status == "processing" && status.stages.extract.completed && !status.stages.clean.completed
                    )

                    StageIndicator(
                        name: "切分",
                        icon: "scissors",
                        completed: status.stages.chunk.completed,
                        isActive: status.status == "processing" && status.stages.clean.completed && !status.stages.chunk.completed
                    )

                    StageIndicator(
                        name: "向量化",
                        icon: "waveform",
                        completed: status.stages.vectorize.completed,
                        isActive: status.status == "processing" && status.stages.chunk.completed && !status.stages.vectorize.completed
                    )

                    StageIndicator(
                        name: "入库",
                        icon: "tray.and.arrow.down",
                        completed: status.stages.index.completed,
                        isActive: status.status == "processing" && status.stages.vectorize.completed && !status.stages.index.completed
                    )
                }

                // 显示chunks数量
                if let chunkCount = status.stages.chunk.count, chunkCount > 0 {
                    Text("已切分为 \(chunkCount) 个语义块")
                        .font(.system(size: 10))
                        .foregroundColor(.gray)
                }
            }
        }
        .onAppear {
            loadStatus()
        }
    }

    private func loadStatus() {
        Task {
            do {
                let url = URL(string: "http://localhost:8000/api/document-processing/documents/\(documentId)/status")!
                let (data, _) = try await URLSession.shared.data(from: url)
                let decodedStatus = try JSONDecoder().decode(ProcessingStatus.self, from: data)

                await MainActor.run {
                    self.status = decodedStatus
                    self.isLoading = false
                }
            } catch {
                await MainActor.run {
                    self.isLoading = false
                }
            }
        }
    }
}

struct StageIndicator: View {
    let name: String
    let icon: String
    let completed: Bool
    let isActive: Bool

    var body: some View {
        VStack(spacing: 3) {
            ZStack {
                Circle()
                    .fill(backgroundColor)
                    .frame(width: 28, height: 28)

                if completed {
                    Image(systemName: "checkmark")
                        .font(.system(size: 12, weight: .bold))
                        .foregroundColor(.white)
                } else if isActive {
                    ProgressView()
                        .scaleEffect(0.6)
                        .tint(.white)
                } else {
                    Image(systemName: icon)
                        .font(.system(size: 11))
                        .foregroundColor(iconColor)
                }
            }

            Text(name)
                .font(.system(size: 9))
                .foregroundColor(textColor)
        }
    }

    private var backgroundColor: Color {
        if completed {
            return Color.green
        } else if isActive {
            return Color.blue
        } else {
            return Color.gray.opacity(0.2)
        }
    }

    private var iconColor: Color {
        completed ? .green : (isActive ? .blue : .gray)
    }

    private var textColor: Color {
        completed ? .green : (isActive ? .blue : .gray)
    }
}
