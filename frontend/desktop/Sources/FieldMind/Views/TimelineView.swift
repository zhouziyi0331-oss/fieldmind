import SwiftUI

struct TimelineView: View {
    @EnvironmentObject var appState: AppState
    @ObservedObject private var dataManager = ProjectDataManager.shared
    @State private var isGenerating = false
    @State private var isExporting = false

    var body: some View {
        VStack(spacing: 0) {
            // 工具栏
            HStack {
                Text("村落编年史")
                    .font(.system(size: 18, weight: .semibold))

                Spacer()

                Button(action: exportTimeline) {
                    HStack(spacing: 4) {
                        if isExporting {
                            ProgressView()
                                .scaleEffect(0.7)
                        } else {
                            Image(systemName: "square.and.arrow.up")
                        }
                        Text("导出")
                    }
                }
                .buttonStyle(.bordered)
                .disabled(dataManager.timeline == nil || isExporting)

                Button(action: generateTimeline) {
                    HStack {
                        if isGenerating {
                            ProgressView()
                                .scaleEffect(0.7)
                        } else {
                            Image(systemName: "sparkles")
                        }
                        Text("生成编年史")
                    }
                }
                .buttonStyle(.borderedProminent)
                .tint(Color(hex: "ed8936"))
                .disabled(appState.currentProject == nil || isGenerating)
            }
            .padding()
            .background(Color(NSColor.controlBackgroundColor))

            Divider()

            // 时间线内容
            if appState.currentProject == nil {
                EmptyStateView(icon: "folder.badge.questionmark", message: "请先选择一个项目")
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else if dataManager.isLoadingTimeline {
                ProgressView("加载中...")
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else if let timeline = dataManager.timeline, !timeline.years.isEmpty {
                ScrollView {
                    VStack(spacing: 32) {
                        ForEach(timeline.years.sorted(by: { $0.year > $1.year })) { yearData in
                            TimelineYearSection(yearData: yearData)
                        }
                    }
                    .padding(24)
                }
            } else {
                EmptyStateView(icon: "clock", message: "暂无编年史数据，点击生成编年史")
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            }
        }
    }

    private func generateTimeline() {
        guard let projectId = appState.currentProject?.id else { return }

        isGenerating = true

        Task {
            do {
                let generatedTimeline = try await APIService.shared.generateTimeline(projectId: projectId, documentIds: nil)
                await MainActor.run {
                    dataManager.timeline = generatedTimeline
                    isGenerating = false
                    ToastManager.shared.success("编年史生成完成")
                }
            } catch {
                print("❌ 生成编年史失败: \(error)")
                await MainActor.run {
                    isGenerating = false
                    ToastManager.shared.error("生成编年史失败")
                }
            }
        }
    }

    private func exportTimeline() {
        guard let timeline = dataManager.timeline else { return }

        isExporting = true

        Task {
            // 创建导出数据
            var exportText = "# 村落编年史\n\n"
            exportText += "导出时间: \(Date().formatted(date: .long, time: .shortened))\n\n"
            exportText += "---\n\n"

            for yearData in timeline.years.sorted(by: { $0.year > $1.year }) {
                exportText += "## \(yearData.year) 年\n\n"

                for event in yearData.events {
                    exportText += "### \(event.title)\n"
                    if let date = event.date {
                        exportText += "**日期**: \(date)\n\n"
                    }
                    exportText += "\(event.content)\n\n"
                    exportText += "---\n\n"
                }
            }

            let exportData = Data(exportText.utf8)

            await MainActor.run {
                // 显示保存对话框
                let savePanel = NSSavePanel()
                savePanel.allowedContentTypes = [.plainText]
                savePanel.nameFieldStringValue = "编年史_\(Date().formatted(date: .numeric, time: .omitted)).md"
                savePanel.message = "选择保存位置"

                savePanel.begin { response in
                    if response == .OK, let url = savePanel.url {
                        do {
                            try exportData.write(to: url)
                            print("✅ 编年史导出成功: \(url.path)")
                            ToastManager.shared.success("编年史导出成功")
                        } catch {
                            print("❌ 导出失败: \(error)")
                            ToastManager.shared.error("导出失败")
                        }
                    }
                    self.isExporting = false
                }
            }
        }
    }
}

struct TimelineYearSection: View {
    let yearData: TimelineYear
    @State private var isExpanded = true

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            // 年份标题 - 可点击展开/折叠
            Button(action: { withAnimation { isExpanded.toggle() } }) {
                HStack(alignment: .center, spacing: 16) {
                    // 展开/折叠图标
                    Image(systemName: isExpanded ? "chevron.down.circle.fill" : "chevron.right.circle.fill")
                        .font(.system(size: 24))
                        .foregroundColor(Color(hex: "ed8936"))

                    // 年份
                    VStack(alignment: .leading, spacing: 4) {
                        Text("\(yearData.year) 年")
                            .font(.system(size: 28, weight: .bold))
                            .foregroundColor(Color(hex: "ed8936"))

                        Text("\(yearData.events.count) 个事件")
                            .font(.system(size: 13))
                            .foregroundColor(.secondary)
                    }

                    Spacer()
                }
                .padding(.vertical, 12)
                .contentShape(Rectangle())
            }
            .buttonStyle(.plain)

            // 事件列表 - 可展开/折叠
            if isExpanded {
                HStack(alignment: .top, spacing: 24) {
                    // 时间线
                    VStack(spacing: 0) {
                        Circle()
                            .fill(Color(hex: "ed8936"))
                            .frame(width: 12, height: 12)
                            .padding(.top, 16)

                        Rectangle()
                            .fill(Color(hex: "ed8936").opacity(0.3))
                            .frame(width: 2)
                    }
                    .padding(.leading, 20)

                    // 事件列表
                    VStack(alignment: .leading, spacing: 16) {
                        ForEach(yearData.events) { event in
                            TimelineEventCard(event: event)
                        }
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(.top, 8)
                }
                .transition(.opacity.combined(with: .move(edge: .top)))
                .padding(.bottom, 16)
            }

            Divider()
        }
    }
}

struct TimelineEventCard: View {
    let event: TimelineEvent

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text(event.title)
                    .font(.system(size: 16, weight: .semibold))

                Spacer()

                if let date = event.date {
                    Text(date)
                        .font(.system(size: 12))
                        .foregroundColor(.secondary)
                }
            }

            Text(event.content)
                .font(.system(size: 14))
                .foregroundColor(.primary)
                .fixedSize(horizontal: false, vertical: true)
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color(NSColor.controlBackgroundColor))
        .cornerRadius(10)
        .shadow(color: Color.black.opacity(0.05), radius: 2, x: 0, y: 1)
    }
}
