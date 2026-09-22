import SwiftUI

struct KeywordPage: View {
    let projectId: Int
    @StateObject private var viewModel = KeywordSearchViewModel()
    @State private var searchText = ""
    @State private var sortBy: SortOption = .count
    @State private var viewMode: ViewMode = .grid

    enum SortOption: String, CaseIterable {
        case count = "使用频率"
        case name = "名称"
    }

    enum ViewMode {
        case grid, list
    }

    var sortedKeywords: [KeywordSearchService.KeywordInfo] {
        var result = viewModel.topKeywords

        // Search filter
        if !searchText.isEmpty {
            result = result.filter { keyword in
                keyword.keyword.localizedCaseInsensitiveContains(searchText)
            }
        }

        // Sort
        switch sortBy {
        case .count:
            result.sort { $0.count > $1.count }
        case .name:
            result.sort { $0.keyword < $1.keyword }
        }

        return result
    }

    var body: some View {
        VStack(spacing: 0) {
            headerView
            Divider()

            if viewModel.isLoadingKeywords {
                loadingView
            } else if viewModel.topKeywords.isEmpty {
                emptyStateView
            } else {
                contentView
            }
        }
        .task {
            await viewModel.loadTopKeywords(projectId: projectId, limit: 100)
        }
    }

    // MARK: - Header
    private var headerView: some View {
        HStack(spacing: 12) {
            // Search
            HStack(spacing: 8) {
                Image(systemName: "magnifyingglass")
                    .font(.system(size: 13))
                    .foregroundStyle(Color.fmN5)
                TextField("搜索关键词...", text: $searchText)
                    .font(.system(size: 13))
                    .textFieldStyle(.plain)
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
            .background(Color.fmN1.opacity(0.5))
            .clipShape(RoundedRectangle(cornerRadius: 8))
            .frame(width: 280)

            Text("共 \(viewModel.topKeywords.count) 个关键词")
                .font(.system(size: 13))
                .foregroundStyle(Color.fmN6)

            Spacer()

            // View mode toggle
            HStack(spacing: 4) {
                Button {
                    viewMode = .grid
                } label: {
                    Image(systemName: "square.grid.2x2")
                        .font(.system(size: 13))
                        .foregroundStyle(viewMode == .grid ? Color.fmA2 : Color.fmN5)
                        .frame(width: 32, height: 28)
                        .background(viewMode == .grid ? Color.fmA2.opacity(0.12) : Color.clear)
                        .clipShape(RoundedRectangle(cornerRadius: 6))
                }
                .buttonStyle(.plain)

                Button {
                    viewMode = .list
                } label: {
                    Image(systemName: "list.bullet")
                        .font(.system(size: 13))
                        .foregroundStyle(viewMode == .list ? Color.fmA2 : Color.fmN5)
                        .frame(width: 32, height: 28)
                        .background(viewMode == .list ? Color.fmA2.opacity(0.12) : Color.clear)
                        .clipShape(RoundedRectangle(cornerRadius: 6))
                }
                .buttonStyle(.plain)
            }
            .padding(4)
            .background(Color.fmN1.opacity(0.5))
            .clipShape(RoundedRectangle(cornerRadius: 8))

            // Sort selector
            Menu {
                ForEach(SortOption.allCases, id: \.self) { option in
                    Button {
                        sortBy = option
                    } label: {
                        HStack {
                            Text(option.rawValue)
                            if sortBy == option {
                                Image(systemName: "checkmark")
                            }
                        }
                    }
                }
            } label: {
                HStack(spacing: 6) {
                    Text("排序: \(sortBy.rawValue)")
                        .font(.system(size: 13))
                    Image(systemName: "chevron.down")
                        .font(.system(size: 10))
                }
                .foregroundStyle(Color.fmN9)
                .padding(.horizontal, 12)
                .padding(.vertical, 8)
                .background(Color.fmN1.opacity(0.5))
                .clipShape(RoundedRectangle(cornerRadius: 8))
            }
            .buttonStyle(.plain)
        }
        .padding(.horizontal, 24)
        .padding(.vertical, 16)
    }

    // MARK: - Content View
    private var contentView: some View {
        ScrollView {
            if viewMode == .grid {
                LazyVGrid(columns: [
                    GridItem(.flexible(), spacing: 16),
                    GridItem(.flexible(), spacing: 16),
                    GridItem(.flexible(), spacing: 16),
                    GridItem(.flexible(), spacing: 16)
                ], spacing: 16) {
                    ForEach(sortedKeywords) { keyword in
                        KeywordCard(keyword: keyword)
                    }
                }
                .padding(24)
            } else {
                LazyVStack(spacing: 8) {
                    ForEach(sortedKeywords) { keyword in
                        KeywordListRow(keyword: keyword)
                    }
                }
                .padding(24)
            }
        }
    }

    // MARK: - Loading View
    private var loadingView: some View {
        VStack(spacing: 16) {
            ProgressView()
                .scaleEffect(1.2)
            Text("加载中...")
                .font(.system(size: 14))
                .foregroundColor(Color.fmText3)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    // MARK: - Empty State
    private var emptyStateView: some View {
        VStack(spacing: 20) {
            Image(systemName: "tag")
                .font(.system(size: 56))
                .foregroundColor(Color.fmText3.opacity(0.5))

            VStack(spacing: 8) {
                Text("暂无关键词")
                    .font(.system(size: 18, weight: .semibold))
                    .foregroundColor(Color.fmText)

                Text("上传材料后自动提取关键词")
                    .font(.system(size: 14))
                    .foregroundColor(Color.fmText3)
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

// MARK: - Keyword Card
struct KeywordCard: View {
    let keyword: KeywordSearchService.KeywordInfo

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text(keyword.keyword)
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundColor(Color.fmText)
                    .lineLimit(1)

                Spacer()

                Circle()
                    .fill(sizeColor)
                    .frame(width: 8, height: 8)
            }

            Divider()

            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text("\(keyword.count)")
                        .font(.system(size: 20, weight: .bold))
                        .foregroundColor(Color.fmA1)
                    Text("出现次数")
                        .font(.system(size: 11))
                        .foregroundColor(Color.fmText3)
                }

                Spacer()

                Image(systemName: "chevron.right")
                    .font(.system(size: 12))
                    .foregroundColor(Color.fmN5)
            }
        }
        .padding(16)
        .background(Color.fmBg2)
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }

    private var sizeColor: Color {
        if keyword.count > 50 {
            return Color.fmA1
        } else if keyword.count > 20 {
            return Color.fmA2
        } else if keyword.count > 10 {
            return Color.fmA5
        } else {
            return Color.fmN5
        }
    }
}

// MARK: - Keyword List Row
struct KeywordListRow: View {
    let keyword: KeywordSearchService.KeywordInfo

    var body: some View {
        HStack(spacing: 16) {
            Circle()
                .fill(sizeColor)
                .frame(width: 10, height: 10)

            Text(keyword.keyword)
                .font(.system(size: 14, weight: .medium))
                .foregroundColor(Color.fmText)

            Spacer()

            HStack(spacing: 12) {
                HStack(spacing: 6) {
                    Image(systemName: "number")
                        .font(.system(size: 11))
                        .foregroundColor(Color.fmText3)
                    Text("\(keyword.count) 次")
                        .font(.system(size: 13))
                        .foregroundColor(Color.fmText2)
                }

                Image(systemName: "chevron.right")
                    .font(.system(size: 12))
                    .foregroundColor(Color.fmN5)
            }
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 12)
        .background(Color.fmBg2)
        .clipShape(RoundedRectangle(cornerRadius: 8))
    }

    private var sizeColor: Color {
        if keyword.count > 50 {
            return Color.fmA1
        } else if keyword.count > 20 {
            return Color.fmA2
        } else if keyword.count > 10 {
            return Color.fmA5
        } else {
            return Color.fmN5
        }
    }
}
