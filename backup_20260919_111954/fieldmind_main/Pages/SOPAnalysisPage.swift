import SwiftUI

struct SOPAnalysisPage: View {
    let projectId: Int
    @StateObject private var viewModel = SOPAnalysisViewModel()
    @State private var searchText = ""
    @State private var selectedCategory = "全部分类"
    @State private var selectedTimeRange = "最近90天"
    @State private var sortBy = "overallScore"

    let categories = ["全部分类", "调研方法", "口述史", "建筑测绘", "数字化", "影像记录", "知识管理"]
    let timeRanges = ["最近30天", "最近90天", "全部"]

    var body: some View {
        VStack(spacing: 0) {
            headerView
            Divider()

            if let errorMessage = viewModel.errorMessage {
                errorBanner(errorMessage)
            }

            filterBar

            if viewModel.isLoading {
                loadingView
            } else if !viewModel.hasAnalyses {
                emptyStateView
            } else {
                contentView
            }
        }
        .task {
            await loadData()
        }
    }

    // MARK: - Header

    private var headerView: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text("SOP 分析")
                    .font(.system(size: 24, weight: .semibold))
                    .foregroundColor(Color.fmText)

                if let summary = viewModel.summary {
                    Text("共 \(summary.totalSOPs) 个 SOP，平均评分 \(String(format: "%.1f", summary.avgScore))")
                        .font(.system(size: 14))
                        .foregroundColor(Color.fmText3)
                }
            }

            Spacer()

            Button(action: {}) {
                HStack(spacing: 6) {
                    Image(systemName: "arrow.down.doc")
                        .font(.system(size: 13))
                    Text("导出报告")
                        .font(.system(size: 14))
                }
                .foregroundColor(.white)
                .padding(.horizontal, 16)
                .padding(.vertical, 8)
                .background(Color.blue)
                .cornerRadius(6)
            }
            .buttonStyle(PlainButtonStyle())
        }
        .padding(.horizontal, 24)
        .padding(.vertical, 20)
        .background(Color.fmBg)
    }

    // MARK: - Filter Bar

    private var filterBar: some View {
        HStack(spacing: 12) {
            // Search
            HStack(spacing: 8) {
                Image(systemName: "magnifyingglass")
                    .foregroundColor(Color.fmText3)
                    .font(.system(size: 14))
                TextField("搜索 SOP 名称或分类", text: $searchText)
                    .textFieldStyle(PlainTextFieldStyle())
                    .font(.system(size: 14))
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
            .background(Color.white)
            .cornerRadius(6)
            .overlay(
                RoundedRectangle(cornerRadius: 6)
                    .stroke(Color.fmBorder, lineWidth: 1)
            )
            .frame(width: 300)

            // Category filter
            Menu {
                ForEach(categories, id: \.self) { category in
                    Button(category) {
                        selectedCategory = category
                        Task {
                            await viewModel.loadAnalyses(
                                projectId: projectId,
                                category: category == "全部分类" ? nil : category,
                                timeRange: selectedTimeRange == "全部" ? nil : selectedTimeRange
                            )
                        }
                    }
                }
            } label: {
                HStack(spacing: 6) {
                    Text(selectedCategory)
                        .font(.system(size: 14))
                        .foregroundColor(Color.fmText)
                    Image(systemName: "chevron.down")
                        .font(.system(size: 12))
                        .foregroundColor(Color.fmText3)
                }
                .padding(.horizontal, 12)
                .padding(.vertical, 8)
                .background(Color.white)
                .cornerRadius(6)
                .overlay(
                    RoundedRectangle(cornerRadius: 6)
                        .stroke(Color.fmBorder, lineWidth: 1)
                )
            }
            .menuStyle(BorderlessButtonMenuStyle())

            // Time range filter
            Menu {
                ForEach(timeRanges, id: \.self) { range in
                    Button(range) {
                        selectedTimeRange = range
                        Task {
                            await viewModel.loadAnalyses(
                                projectId: projectId,
                                category: selectedCategory == "全部分类" ? nil : selectedCategory,
                                timeRange: range == "全部" ? nil : range
                            )
                        }
                    }
                }
            } label: {
                HStack(spacing: 6) {
                    Text(selectedTimeRange)
                        .font(.system(size: 14))
                        .foregroundColor(Color.fmText)
                    Image(systemName: "chevron.down")
                        .font(.system(size: 12))
                        .foregroundColor(Color.fmText3)
                }
                .padding(.horizontal, 12)
                .padding(.vertical, 8)
                .background(Color.white)
                .cornerRadius(6)
                .overlay(
                    RoundedRectangle(cornerRadius: 6)
                        .stroke(Color.fmBorder, lineWidth: 1)
                )
            }
            .menuStyle(BorderlessButtonMenuStyle())

            // Sort menu
            Menu {
                Button("综合评分") { sortBy = "overallScore" }
                Button("使用次数") { sortBy = "totalUsage" }
                Button("成功率") { sortBy = "successRate" }
            } label: {
                HStack(spacing: 6) {
                    Image(systemName: "arrow.up.arrow.down")
                        .font(.system(size: 12))
                    Text("排序")
                        .font(.system(size: 14))
                }
                .foregroundColor(Color.fmText2)
                .padding(.horizontal, 12)
                .padding(.vertical, 8)
                .background(Color.white)
                .cornerRadius(6)
                .overlay(
                    RoundedRectangle(cornerRadius: 6)
                        .stroke(Color.fmBorder, lineWidth: 1)
                )
            }
            .menuStyle(BorderlessButtonMenuStyle())

            Spacer()

            if viewModel.isLoading {
                ProgressView()
                    .scaleEffect(0.8)
            }
        }
        .padding(.horizontal, 24)
        .padding(.vertical, 16)
        .background(Color(NSColor.controlBackgroundColor).opacity(0.3))
    }

    // MARK: - Content Views

    private var contentView: some View {
        ScrollView {
            LazyVStack(spacing: 16) {
                let filtered = viewModel.filterAnalyses(
                    searchText: searchText,
                    category: selectedCategory,
                    sortBy: sortBy
                )

                ForEach(filtered) { analysis in
                    SOPAnalysisCard(analysis: analysis)
                }
            }
            .padding(24)
        }
        .background(Color.fmBg)
    }

    private var loadingView: some View {
        VStack(spacing: 16) {
            ProgressView()
                .scaleEffect(1.2)
            Text("加载分析数据...")
                .font(.system(size: 14))
                .foregroundColor(Color.fmText3)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color.fmBg)
    }

    private var emptyStateView: some View {
        VStack(spacing: 16) {
            Image(systemName: "chart.bar.doc.horizontal")
                .font(.system(size: 48))
                .foregroundColor(Color.fmText3)

            Text("暂无分析数据")
                .font(.system(size: 16, weight: .medium))
                .foregroundColor(Color.fmText2)

            Text("开始分析 SOP 以查看详细统计")
                .font(.system(size: 14))
                .foregroundColor(Color.fmText3)

            Button(action: {
                Task {
                    await loadData()
                }
            }) {
                HStack(spacing: 6) {
                    Image(systemName: "arrow.clockwise")
                        .font(.system(size: 13))
                    Text("刷新数据")
                        .font(.system(size: 14))
                }
                .foregroundColor(.white)
                .padding(.horizontal, 16)
                .padding(.vertical, 8)
                .background(Color.blue)
                .cornerRadius(6)
            }
            .buttonStyle(PlainButtonStyle())
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color.fmBg)
    }

    private func errorBanner(_ message: String) -> some View {
        HStack(spacing: 12) {
            Image(systemName: "exclamationmark.triangle.fill")
                .font(.system(size: 16))
                .foregroundColor(.orange)

            Text(message)
                .font(.system(size: 14))
                .foregroundColor(Color.fmText)

            Spacer()

            Button(action: {
                viewModel.errorMessage = nil
            }) {
                Image(systemName: "xmark.circle.fill")
                    .font(.system(size: 16))
                    .foregroundColor(Color.fmText3)
            }
            .buttonStyle(PlainButtonStyle())
        }
        .padding(16)
        .background(Color.orange.opacity(0.1))
    }

    // MARK: - Data Loading

    private func loadData() async {
        await viewModel.loadAnalyses(
            projectId: projectId,
            category: selectedCategory == "全部分类" ? nil : selectedCategory,
            timeRange: selectedTimeRange == "全部" ? nil : selectedTimeRange
        )
        await viewModel.loadSummary(projectId: projectId)
    }
}

