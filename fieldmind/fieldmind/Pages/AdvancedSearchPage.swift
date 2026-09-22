import SwiftUI

struct AdvancedSearchPage: View {
    let projectId: Int
    @StateObject private var viewModel = KeywordSearchViewModel()
    @State private var searchQuery = ""
    @State private var selectedTab = "all"  // all, videos, audios, documents
    @State private var showTopKeywords = false
    @State private var showFilterPanel = true

    var body: some View {
        VStack(spacing: 0) {
            // Header
            headerView

            Divider()

            HStack(spacing: 0) {
                // Left sidebar (filters or top keywords)
                if showFilterPanel {
                    filterSidebar
                        .frame(width: 280)

                    Divider()
                }

                // Main content
                VStack(spacing: 0) {
                    // Search bar
                    searchBarView

                    Divider()

                    // Messages
                    if let error = viewModel.errorMessage {
                        HStack {
                            Image(systemName: "exclamationmark.triangle.fill")
                                .foregroundColor(.red)
                            Text(error)
                                .font(.system(size: 13))
                                .foregroundColor(.fmText)
                            Spacer()
                            Button("关闭") {
                                viewModel.errorMessage = nil
                            }
                            .font(.system(size: 12))
                            .foregroundColor(.fmBlue)
                        }
                        .padding(12)
                        .background(Color.red.opacity(0.1))
                        .cornerRadius(8)
                        .padding(16)
                    }

                    if let success = viewModel.successMessage {
                        HStack {
                            Image(systemName: "checkmark.circle.fill")
                                .foregroundColor(.green)
                            Text(success)
                                .font(.system(size: 13))
                                .foregroundColor(.fmText)
                            Spacer()
                            Button("关闭") {
                                viewModel.successMessage = nil
                            }
                            .font(.system(size: 12))
                            .foregroundColor(.fmBlue)
                        }
                        .padding(12)
                        .background(Color.green.opacity(0.1))
                        .cornerRadius(8)
                        .padding(16)
                    }

                    // Results area
                    if viewModel.isSearching {
                        searchingView
                    } else if !viewModel.hasSearched {
                        emptyStateView
                    } else if !viewModel.hasResults {
                        noResultsView
                    } else {
                        resultsView
                    }
                }
            }
        }
        .background(Color.fmBg)
        .task {
            await viewModel.loadTopKeywords(projectId: projectId, limit: 50)
        }
    }

    private var headerView: some View {
        HStack(spacing: 16) {
            // Title
            HStack(spacing: 8) {
                Image(systemName: "magnifyingglass.circle.fill")
                    .font(.system(size: 20))
                    .foregroundColor(.fmBlue)
                Text("关键词智能检索")
                    .font(.system(size: 18, weight: .semibold))
                    .foregroundColor(.fmText)
            }

            Spacer()

            // View toggles
            HStack(spacing: 12) {
                Button(action: { showFilterPanel.toggle() }) {
                    HStack(spacing: 6) {
                        Image(systemName: showFilterPanel ? "sidebar.left" : "sidebar.left")
                        Text(showFilterPanel ? "隐藏侧栏" : "显示侧栏")
                            .font(.system(size: 13))
                    }
                    .foregroundColor(showFilterPanel ? .fmBlue : .fmText2)
                    .padding(.horizontal, 12)
                    .padding(.vertical, 6)
                    .background(showFilterPanel ? Color.fmBlue.opacity(0.1) : Color.clear)
                    .cornerRadius(6)
                }
                .buttonStyle(PlainButtonStyle())

                Button(action: { showTopKeywords.toggle() }) {
                    HStack(spacing: 6) {
                        Image(systemName: "chart.bar.fill")
                        Text("热门关键词")
                            .font(.system(size: 13))
                    }
                    .foregroundColor(showTopKeywords ? .fmBlue : .fmText2)
                    .padding(.horizontal, 12)
                    .padding(.vertical, 6)
                    .background(showTopKeywords ? Color.fmBlue.opacity(0.1) : Color.clear)
                    .cornerRadius(6)
                }
                .buttonStyle(PlainButtonStyle())
            }
        }
        .padding(16)
        .background(Color.white)
    }

    private var searchBarView: some View {
        HStack(spacing: 12) {
            // Search input
            HStack(spacing: 8) {
                Image(systemName: "magnifyingglass")
                    .foregroundColor(.fmText2)
                TextField("输入关键词搜索（如：布依族、传统工艺、非遗传承人）", text: $searchQuery)
                    .textFieldStyle(PlainTextFieldStyle())
                    .font(.system(size: 14))
                    .onSubmit {
                        Task {
                            await viewModel.searchKeyword(projectId: projectId, keyword: searchQuery)
                        }
                    }

                if !searchQuery.isEmpty {
                    Button(action: {
                        searchQuery = ""
                        viewModel.clearSearch()
                    }) {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundColor(.fmText2)
                    }
                    .buttonStyle(PlainButtonStyle())
                }
            }
            .padding(10)
            .background(Color.fmBg)
            .cornerRadius(8)

            // Search button
            Button(action: {
                Task {
                    await viewModel.searchKeyword(projectId: projectId, keyword: searchQuery)
                }
            }) {
                HStack(spacing: 6) {
                    Image(systemName: "magnifyingglass")
                    Text("搜索")
                }
                .font(.system(size: 13, weight: .medium))
                .foregroundColor(.white)
                .padding(.horizontal, 20)
                .padding(.vertical, 10)
                .background(searchQuery.isEmpty ? Color.gray : Color.fmBlue)
                .cornerRadius(8)
            }
            .buttonStyle(PlainButtonStyle())
            .disabled(searchQuery.isEmpty || viewModel.isSearching)
        }
        .padding(16)
        .background(Color.white)
    }

    private var filterSidebar: some View {
        VStack(spacing: 0) {
            if showTopKeywords {
                topKeywordsView
            } else {
                searchFiltersView
            }
        }
        .background(Color.white)
    }

    private var searchFiltersView: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("搜索范围")
                .font(.system(size: 14, weight: .semibold))
                .foregroundColor(.fmText)

            VStack(alignment: .leading, spacing: 12) {
                Toggle(isOn: $viewModel.includeDocuments) {
                    HStack(spacing: 8) {
                        Image(systemName: "doc.text.fill")
                            .foregroundColor(.fmBlue)
                        Text("文档")
                            .font(.system(size: 13))
                    }
                }
                .toggleStyle(SwitchToggleStyle(tint: .fmBlue))

                Toggle(isOn: $viewModel.includeVideos) {
                    HStack(spacing: 8) {
                        Image(systemName: "video.fill")
                            .foregroundColor(.fmPurple)
                        Text("视频（含时间点）")
                            .font(.system(size: 13))
                    }
                }
                .toggleStyle(SwitchToggleStyle(tint: .fmBlue))

                Toggle(isOn: $viewModel.includeAudios) {
                    HStack(spacing: 8) {
                        Image(systemName: "waveform")
                            .foregroundColor(.fmGreen)
                        Text("音频（含时间点）")
                            .font(.system(size: 13))
                    }
                }
                .toggleStyle(SwitchToggleStyle(tint: .fmBlue))
            }

            Divider()
                .padding(.vertical, 8)

            // Statistics
            if viewModel.hasResults {
                VStack(alignment: .leading, spacing: 12) {
                    Text("搜索统计")
                        .font(.system(size: 14, weight: .semibold))
                        .foregroundColor(.fmText)

                    statsRow(icon: "text.bubble.fill", label: "总提及次数", value: "\(viewModel.totalResults)")
                    statsRow(icon: "doc.text.fill", label: "文档", value: "\(viewModel.documentCount)")
                    statsRow(icon: "video.fill", label: "视频", value: "\(viewModel.videoCount)")
                    statsRow(icon: "waveform", label: "音频", value: "\(viewModel.audioCount)")
                }
            }

            Spacer()
        }
        .padding(16)
    }

    private func statsRow(icon: String, label: String, value: String) -> some View {
        HStack(spacing: 8) {
            Image(systemName: icon)
                .font(.system(size: 12))
                .foregroundColor(.fmText2)
                .frame(width: 16)
            Text(label)
                .font(.system(size: 12))
                .foregroundColor(.fmText2)
            Spacer()
            Text(value)
                .font(.system(size: 12, weight: .medium))
                .foregroundColor(.fmText)
        }
    }

    private var topKeywordsView: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 12) {
                Text("热门关键词 Top 50")
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundColor(.fmText)
                    .padding(.bottom, 4)

                if viewModel.isLoadingKeywords {
                    ProgressView()
                        .frame(maxWidth: .infinity, alignment: .center)
                        .padding()
                } else if viewModel.topKeywords.isEmpty {
                    Text("暂无热门关键词")
                        .font(.system(size: 12))
                        .foregroundColor(.fmText2)
                        .frame(maxWidth: .infinity, alignment: .center)
                        .padding()
                } else {
                    ForEach(viewModel.topKeywords) { keyword in
                        Button(action: {
                            searchQuery = keyword.keyword
                            Task {
                                await viewModel.searchKeyword(projectId: projectId, keyword: keyword.keyword)
                            }
                        }) {
                            HStack(spacing: 8) {
                                Text(keyword.keyword)
                                    .font(.system(size: 13))
                                    .foregroundColor(.fmText)
                                Spacer()
                                Text("\(keyword.count)")
                                    .font(.system(size: 11))
                                    .foregroundColor(.fmText2)
                                    .padding(.horizontal, 6)
                                    .padding(.vertical, 2)
                                    .background(Color.fmBlue.opacity(0.1))
                                    .cornerRadius(4)
                            }
                            .padding(.horizontal, 12)
                            .padding(.vertical, 8)
                            .background(Color.fmBg)
                            .cornerRadius(6)
                        }
                        .buttonStyle(PlainButtonStyle())
                    }
                }
            }
            .padding(16)
        }
    }

    private var searchingView: some View {
        VStack(spacing: 16) {
            ProgressView()
                .scaleEffect(1.2)
            Text("正在搜索...")
                .font(.system(size: 14))
                .foregroundColor(.fmText2)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    private var emptyStateView: some View {
        VStack(spacing: 20) {
            Image(systemName: "magnifyingglass")
                .font(.system(size: 60))
                .foregroundColor(.fmText2.opacity(0.3))

            VStack(spacing: 8) {
                Text("开始智能检索")
                    .font(.system(size: 16, weight: .medium))
                    .foregroundColor(.fmText)
                Text("输入关键词，在所有项目材料中精确搜索\n视频和音频将返回精确时间点")
                    .font(.system(size: 13))
                    .foregroundColor(.fmText2)
                    .multilineTextAlignment(.center)
            }

            if !viewModel.topKeywords.isEmpty {
                VStack(alignment: .leading, spacing: 8) {
                    Text("推荐关键词：")
                        .font(.system(size: 12))
                        .foregroundColor(.fmText2)

                    FlowLayout(spacing: 8) {
                        ForEach(viewModel.topKeywords.prefix(10)) { keyword in
                            Button(action: {
                                searchQuery = keyword.keyword
                                Task {
                                    await viewModel.searchKeyword(projectId: projectId, keyword: keyword.keyword)
                                }
                            }) {
                                Text(keyword.keyword)
                                    .font(.system(size: 12))
                                    .foregroundColor(.fmBlue)
                                    .padding(.horizontal, 10)
                                    .padding(.vertical, 6)
                                    .background(Color.fmBlue.opacity(0.1))
                                    .cornerRadius(12)
                            }
                            .buttonStyle(PlainButtonStyle())
                        }
                    }
                }
                .padding(.horizontal, 40)
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .padding(40)
    }

    private var noResultsView: some View {
        VStack(spacing: 20) {
            Image(systemName: "magnifyingglass")
                .font(.system(size: 60))
                .foregroundColor(.fmText2.opacity(0.3))

            VStack(spacing: 8) {
                Text("未找到相关结果")
                    .font(.system(size: 16, weight: .medium))
                    .foregroundColor(.fmText)
                Text("关键词 \"\(searchQuery)\" 在项目材料中未找到匹配")
                    .font(.system(size: 13))
                    .foregroundColor(.fmText2)
                    .multilineTextAlignment(.center)
            }

            Button(action: {
                searchQuery = ""
                viewModel.clearSearch()
            }) {
                Text("重新搜索")
                    .font(.system(size: 13))
                    .foregroundColor(.fmBlue)
                    .padding(.horizontal, 16)
                    .padding(.vertical, 8)
                    .background(Color.fmBlue.opacity(0.1))
                    .cornerRadius(6)
            }
            .buttonStyle(PlainButtonStyle())
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .padding(40)
    }

    private var resultsView: some View {
        ScrollView {
            VStack(spacing: 0) {
                // Tab selector
                HStack(spacing: 0) {
                    tabButton(id: "all", label: "全部", count: viewModel.totalResults)
                    tabButton(id: "documents", label: "文档", count: viewModel.documentCount)
                    tabButton(id: "videos", label: "视频", count: viewModel.videoCount)
                    tabButton(id: "audios", label: "音频", count: viewModel.audioCount)
                    Spacer()
                }
                .padding(.horizontal, 16)
                .padding(.top, 16)

                Divider()
                    .padding(.horizontal, 16)
                    .padding(.top, 12)

                // Results content
                VStack(alignment: .leading, spacing: 16) {
                    if let results = viewModel.searchResults {
                        // Related keywords
                        if !results.relatedKeywords.isEmpty {
                            relatedKeywordsSection(keywords: results.relatedKeywords)
                        }

                        // Documents
                        if (selectedTab == "all" || selectedTab == "documents") && !results.documents.isEmpty {
                            documentResultsSection(documents: results.documents)
                        }

                        // Videos
                        if (selectedTab == "all" || selectedTab == "videos") && !results.videoTimestamps.isEmpty {
                            videoResultsSection(timestamps: results.videoTimestamps)
                        }

                        // Audios
                        if (selectedTab == "all" || selectedTab == "audios") && !results.audioTimestamps.isEmpty {
                            audioResultsSection(timestamps: results.audioTimestamps)
                        }
                    }
                }
                .padding(16)
            }
        }
    }

    private func tabButton(id: String, label: String, count: Int) -> some View {
        Button(action: { selectedTab = id }) {
            VStack(spacing: 4) {
                HStack(spacing: 6) {
                    Text(label)
                        .font(.system(size: 13, weight: selectedTab == id ? .medium : .regular))
                    Text("\(count)")
                        .font(.system(size: 11))
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(selectedTab == id ? Color.fmBlue.opacity(0.2) : Color.fmText2.opacity(0.1))
                        .cornerRadius(4)
                }
                .foregroundColor(selectedTab == id ? .fmBlue : .fmText2)
                .padding(.horizontal, 12)
                .padding(.vertical, 8)

                Rectangle()
                    .fill(selectedTab == id ? Color.fmBlue : Color.clear)
                    .frame(height: 2)
            }
        }
        .buttonStyle(PlainButtonStyle())
    }

    private func relatedKeywordsSection(keywords: [String]) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(spacing: 8) {
                Image(systemName: "link")
                    .foregroundColor(.fmBlue)
                Text("相关关键词")
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundColor(.fmText)
            }

            FlowLayout(spacing: 8) {
                ForEach(keywords, id: \.self) { keyword in
                    Button(action: {
                        searchQuery = keyword
                        Task {
                            await viewModel.searchKeyword(projectId: projectId, keyword: keyword)
                        }
                    }) {
                        Text(keyword)
                            .font(.system(size: 12))
                            .foregroundColor(.fmBlue)
                            .padding(.horizontal, 10)
                            .padding(.vertical, 6)
                            .background(Color.fmBlue.opacity(0.1))
                            .cornerRadius(12)
                    }
                    .buttonStyle(PlainButtonStyle())
                }
            }
        }
        .padding(16)
        .background(Color.white)
        .cornerRadius(8)
    }

    private func documentResultsSection(documents: [KeywordSearchService.DocumentMatch]) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(spacing: 8) {
                Image(systemName: "doc.text.fill")
                    .foregroundColor(.fmBlue)
                Text("文档匹配 (\(documents.count))")
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundColor(.fmText)
            }

            VStack(spacing: 8) {
                ForEach(documents) { doc in
                    DocumentMatchCard(document: doc, keyword: searchQuery)
                }
            }
        }
        .padding(16)
        .background(Color.white)
        .cornerRadius(8)
    }

    private func videoResultsSection(timestamps: [KeywordSearchService.VideoTimestamp]) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(spacing: 8) {
                Image(systemName: "video.fill")
                    .foregroundColor(.fmPurple)
                Text("视频时间点 (\(timestamps.count))")
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundColor(.fmText)
            }

            VStack(spacing: 8) {
                ForEach(timestamps) { timestamp in
                    VideoTimestampCard(timestamp: timestamp, keyword: searchQuery)
                }
            }
        }
        .padding(16)
        .background(Color.white)
        .cornerRadius(8)
    }

    private func audioResultsSection(timestamps: [KeywordSearchService.AudioTimestamp]) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(spacing: 8) {
                Image(systemName: "waveform")
                    .foregroundColor(.fmGreen)
                Text("音频时间点 (\(timestamps.count))")
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundColor(.fmText)
            }

            VStack(spacing: 8) {
                ForEach(timestamps) { timestamp in
                    AudioTimestampCard(timestamp: timestamp, keyword: searchQuery)
                }
            }
        }
        .padding(16)
        .background(Color.white)
        .cornerRadius(8)
    }
}

// MARK: - Supporting Views

struct DocumentMatchCard: View {
    let document: KeywordSearchService.DocumentMatch
    let keyword: String

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(spacing: 8) {
                Image(systemName: "doc.text.fill")
                    .foregroundColor(.fmBlue)
                Text(document.filename)
                    .font(.system(size: 13, weight: .medium))
                    .foregroundColor(.fmText)
                Spacer()
                Text("\(document.matches.count) 处匹配")
                    .font(.system(size: 11))
                    .foregroundColor(.fmText2)
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(Color.fmBlue.opacity(0.1))
                    .cornerRadius(4)
            }

            ForEach(document.matches.indices, id: \.self) { index in
                if let context = document.matches[index]["context"] {
                    Text(highlightKeyword(in: context, keyword: keyword))
                        .font(.system(size: 12))
                        .foregroundColor(.fmText2)
                        .padding(8)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .background(Color.fmBg)
                        .cornerRadius(4)
                }
            }
        }
        .padding(12)
        .background(Color.fmBg.opacity(0.5))
        .cornerRadius(6)
    }

    private func highlightKeyword(in text: String, keyword: String) -> AttributedString {
        var attributedString = AttributedString(text)
        if let range = attributedString.range(of: keyword, options: .caseInsensitive) {
            attributedString[range].foregroundColor = .fmBlue
            attributedString[range].font = .system(size: 12, weight: .semibold)
        }
        return attributedString
    }
}

struct VideoTimestampCard: View {
    let timestamp: KeywordSearchService.VideoTimestamp
    let keyword: String

    var body: some View {
        HStack(spacing: 12) {
            VStack(alignment: .leading, spacing: 4) {
                HStack(spacing: 8) {
                    Image(systemName: "video.fill")
                        .foregroundColor(.fmPurple)
                    Text(timestamp.filename)
                        .font(.system(size: 13, weight: .medium))
                        .foregroundColor(.fmText)
                }

                HStack(spacing: 6) {
                    Image(systemName: "clock.fill")
                        .font(.system(size: 11))
                        .foregroundColor(.fmBlue)
                    Text(timestamp.timestamp)
                        .font(.system(size: 12, weight: .semibold))
                        .foregroundColor(.fmBlue)
                    Text("(\(Int(timestamp.timestampSeconds))秒)")
                        .font(.system(size: 11))
                        .foregroundColor(.fmText2)
                }

                Text(timestamp.context)
                    .font(.system(size: 12))
                    .foregroundColor(.fmText2)
                    .lineLimit(2)
            }

            Spacer()
        }
        .padding(12)
        .background(Color.fmBg.opacity(0.5))
        .cornerRadius(6)
    }
}

struct AudioTimestampCard: View {
    let timestamp: KeywordSearchService.AudioTimestamp
    let keyword: String

    var body: some View {
        HStack(spacing: 12) {
            VStack(alignment: .leading, spacing: 4) {
                HStack(spacing: 8) {
                    Image(systemName: "waveform")
                        .foregroundColor(.fmGreen)
                    Text(timestamp.filename)
                        .font(.system(size: 13, weight: .medium))
                        .foregroundColor(.fmText)
                }

                HStack(spacing: 6) {
                    Image(systemName: "clock.fill")
                        .font(.system(size: 11))
                        .foregroundColor(.fmBlue)
                    Text(timestamp.timestamp)
                        .font(.system(size: 12, weight: .semibold))
                        .foregroundColor(.fmBlue)
                    Text("(\(Int(timestamp.timestampSeconds))秒)")
                        .font(.system(size: 11))
                        .foregroundColor(.fmText2)
                }

                Text(timestamp.context)
                    .font(.system(size: 12))
                    .foregroundColor(.fmText2)
                    .lineLimit(2)
            }

            Spacer()
        }
        .padding(12)
        .background(Color.fmBg.opacity(0.5))
        .cornerRadius(6)
    }
}
