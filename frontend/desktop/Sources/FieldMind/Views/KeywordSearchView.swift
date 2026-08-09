import SwiftUI

struct KeywordSearchView: View {
    @StateObject private var viewModel = KeywordSearchViewModel()
    @State private var searchText = ""
    @State private var showVideoPlayer = false
    @State private var showAudioPlayer = false
    @State private var selectedVideoURL: URL?
    @State private var selectedAudioURL: URL?
    @State private var selectedTimestamp: Double?
    @State private var showExportMenu = false

    var body: some View {
        VStack(spacing: 0) {
            // 搜索栏
            searchBar

            Divider()

            // 内容区域
            if viewModel.isSearching {
                loadingView
            } else if let results = viewModel.searchResults {
                resultsView(results: results)
            } else {
                emptyStateView
            }
        }
        .navigationTitle("关键词检索")
        .alert("错误", isPresented: $viewModel.showError) {
            Button("确定", role: .cancel) { }
        } message: {
            Text(viewModel.errorMessage)
        }
        .sheet(isPresented: $showVideoPlayer) {
            if let url = selectedVideoURL {
                VideoPlayerView(videoURL: url, startTime: selectedTimestamp)
            }
        }
        .sheet(isPresented: $showAudioPlayer) {
            if let url = selectedAudioURL {
                AudioPlayerView(audioURL: url, startTime: selectedTimestamp)
            }
        }
    }

    // MARK: - 搜索栏

    private var searchBar: some View {
        HStack(spacing: 12) {
            // 搜索框
            HStack {
                Image(systemName: "magnifyingglass")
                    .foregroundColor(.gray)

                TextField("输入关键词搜索（如：布依族、民俗）", text: $searchText)
                    .textFieldStyle(.plain)
                    .onSubmit {
                        performSearch()
                    }

                if !searchText.isEmpty {
                    Button(action: {
                        searchText = ""
                    }) {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundColor(.gray)
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(8)
            .background(Color(NSColor.controlBackgroundColor))
            .cornerRadius(8)

            // 搜索按钮
            Button(action: performSearch) {
                Label("搜索", systemImage: "arrow.right.circle.fill")
            }
            .disabled(searchText.isEmpty || viewModel.isSearching)
            .buttonStyle(.borderedProminent)
        }
        .padding()
    }

    // MARK: - 加载视图

    private var loadingView: some View {
        VStack(spacing: 16) {
            ProgressView()
                .scaleEffect(1.5)
            Text("正在搜索中...")
                .foregroundColor(.secondary)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    // MARK: - 空状态视图

    private var emptyStateView: some View {
        VStack(spacing: 20) {
            Image(systemName: "magnifyingglass")
                .font(.system(size: 60))
                .foregroundColor(.gray)

            Text("智能关键词检索")
                .font(.title2)
                .fontWeight(.semibold)

            Text("输入关键词，在所有材料中搜索\n自动定位视频/音频的精确时间点")
                .multilineTextAlignment(.center)
                .foregroundColor(.secondary)

            VStack(alignment: .leading, spacing: 8) {
                Text("功能特点：").font(.headline)
                FeatureRow(icon: "video.fill", text: "视频时间点定位（如 00:03:25）")
                FeatureRow(icon: "waveform", text: "音频时间戳定位")
                FeatureRow(icon: "doc.text", text: "文档段落定位")
                FeatureRow(icon: "clock", text: "时间线可视化")
            }
            .padding()
            .background(Color(NSColor.controlBackgroundColor))
            .cornerRadius(12)
        }
        .padding(40)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    // MARK: - 搜索结果视图

    private func resultsView(results: KeywordSearchResponse) -> some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                // 统计信息
                statsHeader(results: results)

                // 相关关键词
                if !results.relatedKeywords.isEmpty {
                    relatedKeywordsSection(keywords: results.relatedKeywords)
                }

                // 视频时间戳
                if !results.videoTimestamps.isEmpty {
                    videoTimestampsSection(timestamps: results.videoTimestamps)
                }

                // 音频时间戳
                if !results.audioTimestamps.isEmpty {
                    audioTimestampsSection(timestamps: results.audioTimestamps)
                }

                // 文档匹配
                if !results.documents.isEmpty {
                    documentMatchesSection(documents: results.documents)
                }
            }
            .padding()
        }
    }

    // MARK: - 统计信息头部

    private func statsHeader(results: KeywordSearchResponse) -> some View {
        HStack {
            VStack(alignment: .leading, spacing: 8) {
                Text("关键词：\(results.keyword)")
                    .font(.title2)
                    .fontWeight(.bold)

                Text("找到 \(results.totalMentions) 处提及")
                    .foregroundColor(.secondary)
            }

            Spacer()

            // 导出按钮
            Menu {
                Button("导出为 HTML") {
                    exportReport(format: .html)
                }
                Button("导出为 Markdown") {
                    exportReport(format: .markdown)
                }
                Button("导出为文本") {
                    exportReport(format: .text)
                }
            } label: {
                Label("导出", systemImage: "square.and.arrow.up")
            }
        }
        .padding()
        .background(Color.blue.opacity(0.1))
        .cornerRadius(12)
    }

    // MARK: - 相关关键词

    private func relatedKeywordsSection(keywords: [String]) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("相关关键词")
                .font(.headline)

            FlowLayout(spacing: 8) {
                ForEach(keywords, id: \.self) { keyword in
                    Button(action: {
                        searchText = keyword
                        performSearch()
                    }) {
                        Text(keyword)
                            .padding(.horizontal, 12)
                            .padding(.vertical, 6)
                            .background(Color.blue.opacity(0.1))
                            .cornerRadius(16)
                    }
                    .buttonStyle(.plain)
                }
            }
        }
        .padding()
        .background(Color(NSColor.controlBackgroundColor))
        .cornerRadius(12)
    }

    // MARK: - 视频时间戳

    private func videoTimestampsSection(timestamps: [VideoTimestamp]) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("视频中的提及 (\(timestamps.count))")
                .font(.headline)

            ForEach(timestamps) { timestamp in
                VideoTimestampRow(timestamp: timestamp, onPlay: playVideo)
            }
        }
    }

    // MARK: - 音频时间戳

    private func audioTimestampsSection(timestamps: [AudioTimestamp]) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("音频中的提及 (\(timestamps.count))")
                .font(.headline)

            ForEach(timestamps) { timestamp in
                AudioTimestampRow(timestamp: timestamp, onPlay: playAudio)
            }
        }
    }

    // MARK: - 文档匹配

    private func documentMatchesSection(documents: [DocumentMatch]) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("文档中的提及 (\(documents.count))")
                .font(.headline)

            ForEach(documents) { doc in
                DocumentMatchRow(document: doc)
            }
        }
    }

    // MARK: - 执行搜索

    private func performSearch() {
        guard !searchText.isEmpty else { return }

        Task {
            await viewModel.searchKeyword(searchText)
        }
    }

    // MARK: - 播放视频

    private func playVideo(timestamp: VideoTimestamp) {
        // TODO: 构建实际的视频 URL
        // 这里需要从后端获取视频文件的实际路径
        let videoPath = "file:///path/to/videos/\(timestamp.filename)"
        if let url = URL(string: videoPath) {
            selectedVideoURL = url
            selectedTimestamp = timestamp.timestampSeconds
            showVideoPlayer = true
        }
    }

    // MARK: - 播放音频

    private func playAudio(timestamp: AudioTimestamp) {
        // TODO: 构建实际的音频 URL
        let audioPath = "file:///path/to/audios/\(timestamp.filename)"
        if let url = URL(string: audioPath) {
            selectedAudioURL = url
            selectedTimestamp = timestamp.timestampSeconds
            showAudioPlayer = true
        }
    }

    // MARK: - 导出报告

    private func exportReport(format: ExportFormat) {
        guard let results = viewModel.searchResults else { return }

        if let fileURL = ReportExporter.shared.exportKeywordSearchReport(results, format: format) {
            ReportExporter.shared.openFile(fileURL)
        }
    }
}

// MARK: - 子视图组件

struct FeatureRow: View {
    let icon: String
    let text: String

    var body: some View {
        HStack {
            Image(systemName: icon)
                .foregroundColor(.blue)
                .frame(width: 24)
            Text(text)
                .foregroundColor(.secondary)
        }
    }
}

struct VideoTimestampRow: View {
    let timestamp: VideoTimestamp
    var onPlay: ((VideoTimestamp) -> Void)?

    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            Image(systemName: "play.circle.fill")
                .font(.title)
                .foregroundColor(.blue)

            VStack(alignment: .leading, spacing: 4) {
                Text(timestamp.filename)
                    .font(.subheadline)
                    .fontWeight(.medium)

                HStack {
                    Image(systemName: "clock")
                        .font(.caption)
                    Text(timestamp.timestamp)
                        .font(.caption)
                        .fontWeight(.semibold)
                }
                .foregroundColor(.blue)

                Text(timestamp.context)
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .lineLimit(2)
            }

            Spacer()

            Button("跳转") {
                onPlay?(timestamp)
            }
            .buttonStyle(.bordered)
        }
        .padding()
        .background(Color(NSColor.controlBackgroundColor))
        .cornerRadius(8)
    }
}

struct AudioTimestampRow: View {
    let timestamp: AudioTimestamp
    var onPlay: ((AudioTimestamp) -> Void)?

    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            Image(systemName: "waveform.circle.fill")
                .font(.title)
                .foregroundColor(.purple)

            VStack(alignment: .leading, spacing: 4) {
                Text(timestamp.filename)
                    .font(.subheadline)
                    .fontWeight(.medium)

                HStack {
                    Image(systemName: "clock")
                        .font(.caption)
                    Text(timestamp.timestamp)
                        .font(.caption)
                        .fontWeight(.semibold)
                }
                .foregroundColor(.purple)

                Text(timestamp.context)
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .lineLimit(2)
            }

            Spacer()

            Button("播放") {
                onPlay?(timestamp)
            }
            .buttonStyle(.bordered)
        }
        .padding()
        .background(Color(NSColor.controlBackgroundColor))
        .cornerRadius(8)
    }
}

struct DocumentMatchRow: View {
    let document: DocumentMatch

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: "doc.text.fill")
                    .foregroundColor(.green)
                Text(document.filename)
                    .font(.subheadline)
                    .fontWeight(.medium)
                Spacer()
                Text("\(document.matches.count) 处匹配")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }

            ForEach(document.matches.indices, id: \.self) { index in
                let match = document.matches[index]
                HStack(alignment: .top, spacing: 8) {
                    if let paragraph = match.paragraph {
                        Text("第\(paragraph)段")
                            .font(.caption2)
                            .padding(.horizontal, 6)
                            .padding(.vertical, 2)
                            .background(Color.green.opacity(0.2))
                            .cornerRadius(4)
                    }

                    Text(match.context)
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
        }
        .padding()
        .background(Color(NSColor.controlBackgroundColor))
        .cornerRadius(8)
    }
}

