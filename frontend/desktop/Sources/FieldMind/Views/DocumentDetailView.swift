import SwiftUI

struct DocumentDetailView: View {
    let document: Document
    @Environment(\.dismiss) var dismiss
    @ObservedObject private var dataManager = ProjectDataManager.shared
    @State private var showingDeleteAlert = false

    var body: some View {
        NavigationView {
            ScrollView {
                VStack(alignment: .leading, spacing: 24) {
                    // 基本信息
                    VStack(alignment: .leading, spacing: 16) {
                        Text("基本信息")
                            .font(.system(size: 18, weight: .bold))

                        InfoRow(label: "文件名", value: document.filename)
                        InfoRow(label: "文件类型", value: document.fileType)
                        InfoRow(label: "文件大小", value: formatFileSize(document.fileSize ?? 0))
                        InfoRow(label: "上传时间", value: formatDate(document.uploadedAt))
                        InfoRow(label: "状态", value: document.status.rawValue)

                        if let wordCount = document.wordCount {
                            InfoRow(label: "字数", value: "\(wordCount) 字")
                        }
                    }
                    .padding()
                    .background(Color(NSColor.controlBackgroundColor))
                    .cornerRadius(8)

                    // 文档内容预览
                    if let content = document.content, !content.isEmpty {
                        VStack(alignment: .leading, spacing: 12) {
                            Text("内容预览")
                                .font(.system(size: 18, weight: .bold))

                            Text(content.prefix(500))
                                .font(.system(size: 13))
                                .foregroundColor(.gray)
                                .padding()
                                .frame(maxWidth: .infinity, alignment: .leading)
                                .background(Color(NSColor.controlBackgroundColor))
                                .cornerRadius(8)

                            if content.count > 500 {
                                Text("... (还有 \(content.count - 500) 个字符)")
                                    .font(.system(size: 12))
                                    .foregroundColor(.gray)
                            }
                        }
                    }

                    // 转写文本（如果有）
                    if document.metadata?.summary != nil {
                        VStack(alignment: .leading, spacing: 12) {
                            Text("转写文本")
                                .font(.system(size: 18, weight: .bold))

                            Button(action: loadTranscript) {
                                HStack {
                                    Image(systemName: "doc.text")
                                    Text("查看完整转写文本")
                                }
                                .padding()
                                .frame(maxWidth: .infinity)
                                .background(Color.blue)
                                .foregroundColor(.white)
                                .cornerRadius(8)
                            }
                        }
                    }

                    // 关键词（如果有）
                    if let tags = document.metadata?.tags, !tags.isEmpty {
                        VStack(alignment: .leading, spacing: 12) {
                            Text("关键词")
                                .font(.system(size: 18, weight: .bold))

                            FlowLayout(spacing: 8) {
                                ForEach(tags.prefix(20), id: \.self) { tag in
                                    Text(tag)
                                        .font(.system(size: 12))
                                        .padding(.horizontal, 12)
                                        .padding(.vertical, 6)
                                        .background(Color.blue.opacity(0.1))
                                        .foregroundColor(.blue)
                                        .cornerRadius(12)
                                }
                            }
                        }
                    }

                    // 操作按钮
                    HStack(spacing: 12) {
                        Button(action: reprocess) {
                            HStack {
                                Image(systemName: "arrow.clockwise")
                                Text("重新处理")
                            }
                            .padding()
                            .frame(maxWidth: .infinity)
                            .background(Color.blue)
                            .foregroundColor(.white)
                            .cornerRadius(8)
                        }

                        Button(action: { showingDeleteAlert = true }) {
                            HStack {
                                Image(systemName: "trash")
                                Text("删除")
                            }
                            .padding()
                            .frame(maxWidth: .infinity)
                            .background(Color.red)
                            .foregroundColor(.white)
                            .cornerRadius(8)
                        }
                    }
                }
                .padding()
            }
            .navigationTitle("文档详情")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("关闭") {
                        dismiss()
                    }
                }
            }
            .alert("确认删除", isPresented: $showingDeleteAlert) {
                Button("取消", role: .cancel) { }
                Button("删除", role: .destructive) {
                    deleteDocument()
                }
            } message: {
                Text("确定要删除这个文档吗？此操作不可撤销。")
            }
        }
    }

    private func loadTranscript() {
        // TODO: 加载并显示完整转写文本
        ToastManager.shared.info("转写文本查看功能开发中")
    }

    private func reprocess() {
        Task {
            do {
                try await dataManager.processDocument(id: document.id)
                ToastManager.shared.success("已提交重新处理")
            } catch {
                ToastManager.shared.error("重新处理失败: \(error.localizedDescription)")
            }
        }
    }

    private func deleteDocument() {
        Task {
            do {
                try await dataManager.deleteDocument(id: document.id)
                ToastManager.shared.success("文档已删除")
                dismiss()
            } catch {
                ToastManager.shared.error("删除失败: \(error.localizedDescription)")
            }
        }
    }

    private func formatFileSize(_ bytes: Int) -> String {
        let formatter = ByteCountFormatter()
        formatter.allowedUnits = [.useKB, .useMB, .useGB]
        formatter.countStyle = .file
        return formatter.string(fromByteCount: Int64(bytes))
    }

    private func formatDate(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        formatter.timeStyle = .short
        return formatter.string(from: date)
    }
}

struct InfoRow: View {
    let label: String
    let value: String

    var body: some View {
        HStack {
            Text(label)
                .font(.system(size: 13))
                .foregroundColor(.gray)
                .frame(width: 80, alignment: .leading)

            Text(value)
                .font(.system(size: 13, weight: .medium))
                .foregroundColor(Color.fieldMindText)

            Spacer()
        }
    }
}

