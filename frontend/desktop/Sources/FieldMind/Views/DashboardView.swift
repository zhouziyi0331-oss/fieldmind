import SwiftUI

struct DashboardView: View {
    @EnvironmentObject var appState: AppState
    @ObservedObject private var dataManager = ProjectDataManager.shared
    @State private var isExporting = false

    var body: some View {
        VStack(spacing: 0) {
            // 工具栏
            HStack {
                Text("数据看板")
                    .font(.system(size: 16, weight: .bold))
                    .foregroundColor(Color.fieldMindText)

                Spacer()

                Button(action: exportDashboard) {
                    HStack(spacing: 4) {
                        if isExporting {
                            ProgressView()
                                .scaleEffect(0.7)
                        } else {
                            Image(systemName: "square.and.arrow.up")
                        }
                        Text("导出报告")
                    }
                }
                .buttonStyle(.bordered)
                .disabled(dataManager.dashboardStats == nil || isExporting)
            }
            .padding()
            .background(Color(NSColor.controlBackgroundColor))

            Divider()

            // 内容区域
            if appState.currentProject == nil {
                EmptyStateView(icon: "folder.badge.questionmark", message: "请先选择一个项目")
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else if dataManager.isLoadingDashboard {
                ProgressView("加载数据中...")
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else if let stats = dataManager.dashboardStats {
                ScrollView {
                    VStack(spacing: 24) {
                        // 统计卡片
                        StatsCardsView(stats: stats)

                        // 最近文档
                        RecentDocumentsView(documents: stats.recentDocuments ?? [])
                    }
                    .padding(24)
                }
            } else {
                EmptyStateView(icon: "chart.bar", message: "暂无数据")
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            }
        }
        .background(Color.fieldMindBackground)
    }

    private func exportDashboard() {
        guard let stats = dataManager.dashboardStats else { return }

        isExporting = true

        Task {
            do {
                var exportText = "# 项目数据看板报告\n\n"
                exportText += "项目名称: \(appState.currentProject?.name ?? "未知")\n"
                exportText += "导出时间: \(Date().formatted(date: .long, time: .shortened))\n\n"

                exportText += "## 统计概览\n\n"
                exportText += "- 文档总数: \(stats.documentCount)\n"
                exportText += "- 知识脉络: \(stats.contextCount)\n"
                exportText += "- 关键词数量: \(stats.keywordCount)\n"
                exportText += "- 对话次数: \(stats.chatCount)\n\n"

                if let recentDocs = stats.recentDocuments, !recentDocs.isEmpty {
                    exportText += "## 最近文档\n\n"
                    for doc in recentDocs {
                        exportText += "- \(doc.filename) (\(formatDate(doc.uploadedAt)))\n"
                    }
                    exportText += "\n"
                }

                let exportData = Data(exportText.utf8)

                await MainActor.run {
                    let savePanel = NSSavePanel()
                    savePanel.allowedContentTypes = [.plainText]
                    savePanel.nameFieldStringValue = "数据看板_\(Date().timeIntervalSince1970).txt"

                    savePanel.begin { response in
                        if response == .OK, let url = savePanel.url {
                            do {
                                try exportData.write(to: url)
                                ToastManager.shared.success("看板导出成功")
                            } catch {
                                ToastManager.shared.error("导出失败")
                            }
                        }
                        self.isExporting = false
                    }
                }
            } catch {
                await MainActor.run {
                    ToastManager.shared.error("导出失败")
                    isExporting = false
                }
            }
        }
    }

    private func formatDate(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd HH:mm"
        return formatter.string(from: date)
    }
}

struct StatsCardsView: View {
    let stats: DashboardStatsResponse

    var body: some View {
        LazyVGrid(columns: [
            GridItem(.flexible()),
            GridItem(.flexible()),
            GridItem(.flexible()),
            GridItem(.flexible())
        ], spacing: 16) {
            StatCard(
                icon: "doc.fill",
                title: "文档总数",
                value: "\(stats.documentCount)",
                color: Color(hex: "48bb78")
            )

            StatCard(
                icon: "network",
                title: "知识脉络",
                value: "\(stats.contextCount)",
                color: Color(hex: "3182ce")
            )

            StatCard(
                icon: "key.fill",
                title: "关键词",
                value: "\(stats.keywordCount)",
                color: Color(hex: "ed8936")
            )

            StatCard(
                icon: "message.fill",
                title: "对话次数",
                value: "\(stats.chatCount)",
                color: Color(hex: "9f7aea")
            )
        }
    }
}

struct StatCard: View {
    let icon: String
    let title: String
    let value: String
    let color: Color

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: icon)
                    .font(.system(size: 20))
                    .foregroundColor(color)

                Spacer()
            }

            Text(value)
                .font(.system(size: 28, weight: .bold))
                .foregroundColor(Color.fieldMindText)

            Text(title)
                .font(.system(size: 13))
                .foregroundColor(.gray)
        }
        .padding(20)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color.white)
        .cornerRadius(12)
        .shadow(color: Color.black.opacity(0.05), radius: 4, x: 0, y: 2)
    }
}

struct RecentDocumentsView: View {
    let documents: [Document]

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("最近文档")
                .font(.system(size: 16, weight: .bold))
                .foregroundColor(Color.fieldMindText)

            if documents.isEmpty {
                Text("暂无文档")
                    .font(.system(size: 13))
                    .foregroundColor(.gray)
                    .frame(maxWidth: .infinity, alignment: .center)
                    .padding(32)
            } else {
                VStack(spacing: 8) {
                    ForEach(documents.prefix(5)) { document in
                        RecentDocumentRow(document: document)
                    }
                }
            }
        }
        .padding(20)
        .background(Color.white)
        .cornerRadius(12)
        .shadow(color: Color.black.opacity(0.05), radius: 4, x: 0, y: 2)
    }
}

struct RecentDocumentRow: View {
    let document: Document
    @EnvironmentObject var appState: AppState
    @State private var showingDetail = false

    var body: some View {
        Button(action: {
            showingDetail = true
        }) {
            HStack(spacing: 12) {
                Image(systemName: "doc.fill")
                    .font(.system(size: 14))
                    .foregroundColor(Color(hex: "48bb78"))

                VStack(alignment: .leading, spacing: 2) {
                    Text(document.filename)
                        .font(.system(size: 13, weight: .medium))
                        .foregroundColor(Color.fieldMindText)

                    Text(formatDate(document.uploadedAt))
                        .font(.system(size: 11))
                        .foregroundColor(.gray)
                }

                Spacer()

                StatusBadge(status: document.status)
            }
            .padding(12)
            .background(Color.fieldMindBackground)
            .cornerRadius(6)
        }
        .buttonStyle(.plain)
        .sheet(isPresented: $showingDetail) {
            DocumentDetailView(document: document)
        }
    }

    private func formatDate(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd HH:mm"
        return formatter.string(from: date)
    }
}
