import SwiftUI

struct SOPPage: View {
    let projectId: Int
    @StateObject private var viewModel = SOPViewModel()
    @State private var searchText = ""
    @State private var selectedCategory = "全部分类"
    @State private var selectedStatus = "全部状态"
    @State private var sortBy = "lastModified"
    @State private var viewMode = "list"
    @State private var showCreateSheet = false

    let categories = ["全部分类", "调研方法", "口述史", "建筑测绘", "数字化", "影像记录", "知识管理"]
    let statuses = ["全部状态", "草稿", "审核中", "已发布", "已归档"]

    var filteredSOPs: [SOPService.SOP] {
        viewModel.filterSOPs(
            searchText: searchText,
            category: selectedCategory,
            status: selectedStatus,
            sortBy: sortBy
        )
    }

    var body: some View {
        VStack(spacing: 0) {
            headerView
            Divider()
            filterBar
            Divider()

            if viewModel.isLoading {
                loadingView
            } else if !viewModel.hasSOPs {
                emptyStateView
            } else {
                contentView
            }
        }
        .sheet(isPresented: $showCreateSheet) {
            createSOPSheet
        }
        .task {
            await loadData()
        }
    }

    // MARK: - Header
    private var headerView: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text("SOP 管理")
                    .font(.system(size: 24, weight: .semibold))
                    .foregroundColor(Color.fmText)

                if let stats = viewModel.statistics {
                    Text("共 \(stats.totalSOPs) 个SOP · \(stats.publishedSOPs) 已发布 · 平均成功率 \(Int(stats.avgSuccessRate * 100))%")
                        .font(.system(size: 12))
                        .foregroundColor(Color.fmText3)
                }
            }

            Spacer()

            Button(action: { showCreateSheet = true }) {
                HStack(spacing: 6) {
                    Image(systemName: "plus")
                        .font(.system(size: 13))
                    Text("新建 SOP")
                        .font(.system(size: 13))
                }
                .foregroundColor(.white)
                .padding(.horizontal, 16)
                .padding(.vertical, 8)
                .background(Color.fmA1)
                .cornerRadius(6)
            }
            .buttonStyle(PlainButtonStyle())
        }
        .padding(20)
    }

    // MARK: - Filter Bar
    private var filterBar: some View {
        HStack(spacing: 12) {
            HStack(spacing: 8) {
                Image(systemName: "magnifyingglass")
                    .foregroundColor(Color.fmText3)
                    .font(.system(size: 14))

                TextField("搜索 SOP 标题、作者、标签...", text: $searchText)
                    .textFieldStyle(PlainTextFieldStyle())
                    .font(.system(size: 13))
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
            .background(Color.fmN1.opacity(0.5))
            .cornerRadius(6)
            .frame(width: 300)

            Menu {
                ForEach(categories, id: \.self) { category in
                    Button(category) {
                        selectedCategory = category
                    }
                }
            } label: {
                HStack(spacing: 6) {
                    Text(selectedCategory)
                        .font(.system(size: 13))
                        .foregroundColor(Color.fmText2)
                    Image(systemName: "chevron.down")
                        .font(.system(size: 10))
                        .foregroundColor(Color.fmText3)
                }
                .padding(.horizontal, 12)
                .padding(.vertical, 8)
                .background(Color.fmN1.opacity(0.5))
                .cornerRadius(6)
            }

            Menu {
                ForEach(statuses, id: \.self) { status in
                    Button(status) {
                        selectedStatus = status
                    }
                }
            } label: {
                HStack(spacing: 6) {
                    Text(selectedStatus)
                        .font(.system(size: 13))
                        .foregroundColor(Color.fmText2)
                    Image(systemName: "chevron.down")
                        .font(.system(size: 10))
                        .foregroundColor(Color.fmText3)
                }
                .padding(.horizontal, 12)
                .padding(.vertical, 8)
                .background(Color.fmN1.opacity(0.5))
                .cornerRadius(6)
            }

            Menu {
                Button("最后修改") { sortBy = "lastModified" }
                Button("使用次数") { sortBy = "usedCount" }
                Button("标题") { sortBy = "title" }
            } label: {
                HStack(spacing: 6) {
                    Text("排序")
                        .font(.system(size: 13))
                        .foregroundColor(Color.fmText2)
                    Image(systemName: "chevron.down")
                        .font(.system(size: 10))
                        .foregroundColor(Color.fmText3)
                }
                .padding(.horizontal, 12)
                .padding(.vertical, 8)
                .background(Color.fmN1.opacity(0.5))
                .cornerRadius(6)
            }

            Spacer()

            HStack(spacing: 4) {
                Button {
                    viewMode = "list"
                } label: {
                    Image(systemName: "list.bullet")
                        .font(.system(size: 13))
                        .foregroundColor(viewMode == "list" ? Color.fmA1 : Color.fmText3)
                        .frame(width: 32, height: 28)
                        .background(viewMode == "list" ? Color.fmA1.opacity(0.1) : Color.clear)
                        .cornerRadius(6)
                }
                .buttonStyle(PlainButtonStyle())

                Button {
                    viewMode = "grid"
                } label: {
                    Image(systemName: "square.grid.2x2")
                        .font(.system(size: 13))
                        .foregroundColor(viewMode == "grid" ? Color.fmA1 : Color.fmText3)
                        .frame(width: 32, height: 28)
                        .background(viewMode == "grid" ? Color.fmA1.opacity(0.1) : Color.clear)
                        .cornerRadius(6)
                }
                .buttonStyle(PlainButtonStyle())
            }
        }
        .padding(.horizontal, 20)
        .padding(.vertical, 12)
    }

    // MARK: - Content View
    private var contentView: some View {
        ScrollView {
            if viewMode == "list" {
                listView
            } else {
                gridView
            }
        }
    }

    private var listView: some View {
        LazyVStack(spacing: 8) {
            ForEach(filteredSOPs) { sop in
                SOPListRow(sop: sop)
            }
        }
        .padding(20)
    }

    private var gridView: some View {
        LazyVGrid(columns: [
            GridItem(.flexible(), spacing: 16),
            GridItem(.flexible(), spacing: 16)
        ], spacing: 16) {
            ForEach(filteredSOPs) { sop in
                SOPGridCard(sop: sop)
            }
        }
        .padding(20)
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
            Image(systemName: "doc.text.magnifyingglass")
                .font(.system(size: 56))
                .foregroundColor(Color.fmText3.opacity(0.5))

            VStack(spacing: 8) {
                Text("暂无 SOP")
                    .font(.system(size: 18, weight: .semibold))
                    .foregroundColor(Color.fmText)

                Text("创建第一个标准操作流程")
                    .font(.system(size: 14))
                    .foregroundColor(Color.fmText3)
            }

            Button(action: { showCreateSheet = true }) {
                HStack(spacing: 6) {
                    Image(systemName: "plus.circle.fill")
                        .font(.system(size: 14))
                    Text("新建 SOP")
                        .font(.system(size: 14, weight: .medium))
                }
                .foregroundColor(.white)
                .padding(.horizontal, 20)
                .padding(.vertical, 10)
                .background(Color.fmA1)
                .cornerRadius(8)
            }
            .buttonStyle(PlainButtonStyle())
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    // MARK: - Create Sheet
    private var createSOPSheet: some View {
        VStack(spacing: 20) {
            Text("新建 SOP")
                .font(.system(size: 18, weight: .semibold))

            Text("功能开发中")
                .font(.system(size: 14))
                .foregroundColor(Color.fmText3)

            Button("关闭") {
                showCreateSheet = false
            }
            .buttonStyle(FMButtonStyle(style: .secondary, size: .medium))
        }
        .frame(width: 400, height: 300)
        .padding(30)
    }

    // MARK: - Load Data
    private func loadData() async {
        await viewModel.loadSOPs(
            projectId: projectId,
            category: selectedCategory == "全部分类" ? nil : selectedCategory,
            status: selectedStatus == "全部状态" ? nil : selectedStatus,
            search: searchText.isEmpty ? nil : searchText
        )
    }
}
