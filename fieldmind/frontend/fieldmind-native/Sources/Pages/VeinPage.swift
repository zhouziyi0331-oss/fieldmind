import SwiftUI

struct VeinPage: View {
    let projectId: Int
    @StateObject private var viewModel = VeinViewModel()
    @State private var searchText = ""
    @State private var selectedDepth = "全部"
    @State private var selectedView = "tree"
    @State private var showingLegend = true

    let depths = ["1", "2", "3", "全部"]
    let viewModes = [
        ("tree", "树状图", "arrow.triangle.branch"),
        ("list", "列表视图", "list.bullet"),
        ("network", "网络图", "circle.hexagongrid")
    ]

    var body: some View {
        VStack(spacing: 0) {
            headerView
            Divider()

            if let errorMessage = viewModel.errorMessage {
                errorBanner(errorMessage)
            }

            if viewModel.isLoading {
                loadingView
            } else if !viewModel.hasContexts {
                emptyStateView
            } else {
                contentViewBody
            }
        }
        .task {
            await viewModel.loadContexts(projectId: projectId)
        }
    }

    // MARK: - Header

    private var headerView: some View {
        HStack(spacing: 12) {
            // Search
            HStack(spacing: 8) {
                Image(systemName: "magnifyingglass")
                    .font(.system(size: 13))
                    .foregroundColor(Color(hex: "94A3B8"))

                TextField("搜索知识节点...", text: $searchText)
                    .textFieldStyle(PlainTextFieldStyle())
                    .font(.system(size: 13))

                if !searchText.isEmpty {
                    Button(action: { searchText = "" }) {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundColor(Color(hex: "94A3B8"))
                            .font(.system(size: 12))
                    }
                    .buttonStyle(PlainButtonStyle())
                }
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
            .background(Color(hex: "F8FAFC"))
            .cornerRadius(8)
            .frame(width: 280)

            // View mode selector
            HStack(spacing: 8) {
                ForEach(viewModes, id: \.0) { mode in
                    Button(action: { selectedView = mode.0 }) {
                        HStack(spacing: 6) {
                            Image(systemName: mode.2)
                                .font(.system(size: 12))
                            Text(mode.1)
                                .font(.system(size: 13))
                        }
                        .foregroundColor(selectedView == mode.0 ? Color(hex: "3B82F6") : Color(hex: "64748B"))
                        .padding(.horizontal, 12)
                        .padding(.vertical, 7)
                        .background(selectedView == mode.0 ? Color(hex: "EFF6FF") : Color.white)
                        .cornerRadius(6)
                        .overlay(
                            RoundedRectangle(cornerRadius: 6)
                                .stroke(selectedView == mode.0 ? Color(hex: "3B82F6") : Color(hex: "E2E8F0"), lineWidth: 1)
                        )
                    }
                    .buttonStyle(PlainButtonStyle())
                }
            }

            // Depth filter
            Menu {
                ForEach(depths, id: \.self) { depth in
                    Button(action: {
                        selectedDepth = depth
                        Task {
                            let level = depth == "全部" ? nil : Int(depth)
                            await viewModel.loadContexts(projectId: projectId, level: level)
                        }
                    }) {
                        HStack {
                            Text("Level \(depth)")
                            if selectedDepth == depth {
                                Image(systemName: "checkmark")
                            }
                        }
                    }
                }
            } label: {
                HStack(spacing: 6) {
                    Image(systemName: "list.number")
                        .font(.system(size: 12))
                    Text("深度: \(selectedDepth)")
                        .font(.system(size: 13))
                    Image(systemName: "chevron.down")
                        .font(.system(size: 10))
                }
                .foregroundColor(Color(hex: "475569"))
                .padding(.horizontal, 12)
                .padding(.vertical, 7)
                .background(Color.white)
                .cornerRadius(6)
                .overlay(
                    RoundedRectangle(cornerRadius: 6)
                        .stroke(Color(hex: "E2E8F0"), lineWidth: 1)
                )
            }

            Spacer()

            // Legend toggle
            Button(action: { showingLegend.toggle() }) {
                HStack(spacing: 6) {
                    Image(systemName: showingLegend ? "eye.fill" : "eye.slash")
                        .font(.system(size: 12))
                    Text("图例")
                        .font(.system(size: 13))
                }
                .foregroundColor(Color(hex: "475569"))
                .padding(.horizontal, 12)
                .padding(.vertical, 7)
                .background(Color.white)
                .cornerRadius(6)
                .overlay(
                    RoundedRectangle(cornerRadius: 6)
                        .stroke(Color(hex: "E2E8F0"), lineWidth: 1)
                )
            }
            .buttonStyle(PlainButtonStyle())
        }
        .padding(.horizontal, 24)
        .padding(.vertical, 12)
        .background(Color.fmBg)
    }

    // MARK: - Content Views

    private var contentViewBody: some View {
        HStack(spacing: 0) {
            // Main content area
            ScrollView {
                if selectedView == "list" {
                    listViewBody
                } else if selectedView == "tree" {
                    treeViewBody
                } else {
                    networkPlaceholderView
                }
            }
            .frame(maxWidth: .infinity)

            // Legend sidebar
            if showingLegend {
                Divider()
                legendView
                    .frame(width: 280)
            }
        }
    }

    // MARK: - List View

    private var listViewBody: some View {
        VStack(spacing: 16) {
            let filteredContexts = viewModel.filterContexts(searchText: searchText)
            let groupedByLevel = Dictionary(grouping: filteredContexts, by: { $0.level })
            let sortedLevels = groupedByLevel.keys.sorted()

            ForEach(sortedLevels, id: \.self) { level in
                levelSection(level: level, contexts: groupedByLevel[level] ?? [])
            }
        }
        .padding(24)
    }

    private func levelSection(level: Int, contexts: [VeinService.ProjectContext]) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(spacing: 8) {
                Circle()
                    .fill(levelColor(level))
                    .frame(width: 12, height: 12)

                Text("Level \(level)")
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundColor(.fmText)

                Text("\(contexts.count)个节点")
                    .font(.system(size: 13))
                    .foregroundColor(.fmText3)

                Spacer()
            }

            VStack(spacing: 8) {
                ForEach(contexts, id: \.id) { context in
                    contextCard(context)
                }
            }
        }
    }

    private func contextCard(_ context: VeinService.ProjectContext) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack(spacing: 10) {
                Circle()
                    .fill(levelColor(context.level))
                    .frame(width: 8, height: 8)

                Text(context.name)
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(.fmText)

                Spacer()

                if context.parentId != nil {
                    Image(systemName: "arrow.turn.down.right")
                        .font(.system(size: 10))
                        .foregroundColor(.fmText3)
                }
            }

            if let description = context.description, !description.isEmpty {
                Text(description)
                    .font(.system(size: 13))
                    .foregroundColor(.fmText2)
                    .lineLimit(2)
            }

            if !context.keywords.isEmpty {
                HStack(spacing: 6) {
                    ForEach(context.keywords.prefix(6), id: \.self) { keyword in
                        Text(keyword)
                            .font(.system(size: 11))
                            .foregroundColor(Color(hex: "3B82F6"))
                            .padding(.horizontal, 8)
                            .padding(.vertical, 4)
                            .background(Color(hex: "EFF6FF"))
                            .cornerRadius(4)
                    }

                    if context.keywords.count > 6 {
                        Text("+\(context.keywords.count - 6)")
                            .font(.system(size: 11))
                            .foregroundColor(.fmText3)
                    }
                }
            }

            HStack(spacing: 12) {
                HStack(spacing: 4) {
                    Image(systemName: "doc")
                        .font(.system(size: 11))
                    Text("\(context.documentIds.count)个文档")
                        .font(.system(size: 12))
                }
                .foregroundColor(.fmText3)

                HStack(spacing: 4) {
                    Image(systemName: "calendar")
                        .font(.system(size: 11))
                    Text(formatDate(context.createdAt))
                        .font(.system(size: 12))
                }
                .foregroundColor(.fmText3)
            }
        }
        .padding(14)
        .background(Color.white)
        .cornerRadius(10)
        .overlay(
            RoundedRectangle(cornerRadius: 10)
                .stroke(Color(hex: "E2E8F0"), lineWidth: 1)
        )
    }

    // MARK: - Tree View

    private var treeViewBody: some View {
        VStack(alignment: .leading, spacing: 20) {
            let filteredContexts = viewModel.filterContexts(searchText: searchText)
            let rootContexts = filteredContexts.filter { $0.parentId == nil }

            ForEach(rootContexts, id: \.id) { context in
                treeNode(context: context, allContexts: filteredContexts, indentLevel: 0)
            }
        }
        .padding(24)
    }

    private func treeNode(context: VeinService.ProjectContext, allContexts: [VeinService.ProjectContext], indentLevel: Int) -> AnyView {
        AnyView(
            VStack(alignment: .leading, spacing: 12) {
            HStack(spacing: 12) {
                // Indent lines
                if indentLevel > 0 {
                    ForEach(0..<indentLevel, id: \.self) { _ in
                        Rectangle()
                            .fill(Color(hex: "E2E8F0"))
                            .frame(width: 2)
                    }
                    .frame(width: CGFloat(indentLevel) * 20)
                }

                // Node card
                HStack(spacing: 10) {
                    Circle()
                        .fill(levelColor(context.level))
                        .frame(width: 10, height: 10)

                    VStack(alignment: .leading, spacing: 4) {
                        Text(context.name)
                            .font(.system(size: 14, weight: .medium))
                            .foregroundColor(.fmText)

                        if !context.keywords.isEmpty {
                            HStack(spacing: 4) {
                                ForEach(context.keywords.prefix(3), id: \.self) { keyword in
                                    Text(keyword)
                                        .font(.system(size: 10))
                                        .foregroundColor(Color(hex: "3B82F6"))
                                        .padding(.horizontal, 6)
                                        .padding(.vertical, 3)
                                        .background(Color(hex: "EFF6FF"))
                                        .cornerRadius(3)
                                }
                            }
                        }
                    }

                    Spacer()

                    Text("\(context.documentIds.count)")
                        .font(.system(size: 12, weight: .medium))
                        .foregroundColor(.fmText3)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(Color.fmBg2)
                        .cornerRadius(4)
                }
                .padding(.horizontal, 12)
                .padding(.vertical, 10)
                .background(Color.white)
                .cornerRadius(8)
                .overlay(
                    RoundedRectangle(cornerRadius: 8)
                        .stroke(levelColor(context.level).opacity(0.3), lineWidth: 2)
                )
            }

            // Children nodes
            let children = allContexts.filter { $0.parentId == context.id }
            ForEach(children, id: \.id) { child in
                treeNode(context: child, allContexts: allContexts, indentLevel: indentLevel + 1)
            }
        }
        )
    }

    // MARK: - Network Placeholder

    private var networkPlaceholderView: some View {
        VStack(spacing: 16) {
            Image(systemName: "circle.hexagongrid")
                .font(.system(size: 48))
                .foregroundColor(.fmText3)

            Text("网络图视图")
                .font(.system(size: 16, weight: .medium))
                .foregroundColor(.fmText2)

            Text("该视图需要图形渲染引擎支持")
                .font(.system(size: 13))
                .foregroundColor(.fmText3)

            Button(action: { selectedView = "tree" }) {
                Text("切换到树状图")
                    .font(.system(size: 14))
                    .foregroundColor(.white)
                    .padding(.horizontal, 20)
                    .padding(.vertical, 10)
                    .background(Color.blue)
                    .cornerRadius(8)
            }
            .buttonStyle(.plain)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .padding(40)
    }

    // MARK: - Legend View

    private var legendView: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("图例")
                .font(.system(size: 15, weight: .semibold))
                .foregroundColor(.fmText)

            Divider()

            VStack(alignment: .leading, spacing: 12) {
                Text("节点层级")
                    .font(.system(size: 13, weight: .medium))
                    .foregroundColor(.fmText2)

                ForEach([1, 2, 3, 4], id: \.self) { level in
                    HStack(spacing: 8) {
                        Circle()
                            .fill(levelColor(level))
                            .frame(width: 10, height: 10)

                        Text("Level \(level)")
                            .font(.system(size: 12))
                            .foregroundColor(.fmText3)
                    }
                }
            }

            Divider()

            VStack(alignment: .leading, spacing: 12) {
                Text("统计信息")
                    .font(.system(size: 13, weight: .medium))
                    .foregroundColor(.fmText2)

                statisticRow(label: "总节点数", value: "\(viewModel.contexts.count)")
                statisticRow(label: "当前显示", value: "\(viewModel.filterContexts(searchText: searchText).count)")

                let byLevel = viewModel.contextsByLevel()
                ForEach(byLevel.keys.sorted(), id: \.self) { level in
                    statisticRow(label: "Level \(level)", value: "\(byLevel[level]?.count ?? 0)")
                }
            }

            Spacer()
        }
        .padding(16)
        .background(Color.fmBg)
    }

    private func statisticRow(label: String, value: String) -> some View {
        HStack {
            Text(label)
                .font(.system(size: 12))
                .foregroundColor(.fmText3)
            Spacer()
            Text(value)
                .font(.system(size: 12, weight: .medium))
                .foregroundColor(.fmText)
        }
    }

    // MARK: - Empty State

    private var emptyStateView: some View {
        VStack(spacing: 16) {
            Image(systemName: "network.slash")
                .font(.system(size: 48))
                .foregroundColor(.fmText3)

            Text("暂无知识脉络")
                .font(.system(size: 16, weight: .medium))
                .foregroundColor(.fmText2)

            Text("该项目还没有创建任何知识脉络节点")
                .font(.system(size: 13))
                .foregroundColor(.fmText3)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color.fmBg)
    }

    private var loadingView: some View {
        VStack(spacing: 16) {
            ProgressView()
                .scaleEffect(1.2)

            Text("加载知识脉络...")
                .font(.system(size: 14))
                .foregroundColor(.fmText3)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color.fmBg)
    }

    private func errorBanner(_ message: String) -> some View {
        HStack(spacing: 12) {
            Image(systemName: "exclamationmark.triangle.fill")
                .foregroundColor(.red)
            Text(message)
                .font(.system(size: 13))
                .foregroundColor(.fmText)
            Spacer()
            Button(action: {
                Task {
                    await viewModel.loadContexts(projectId: projectId)
                }
            }) {
                Text("重试")
                    .font(.system(size: 13, weight: .medium))
                    .foregroundColor(.white)
                    .padding(.horizontal, 12)
                    .padding(.vertical, 6)
                    .background(Color.blue)
                    .cornerRadius(6)
            }
            .buttonStyle(.plain)
        }
        .padding(12)
        .background(Color.red.opacity(0.1))
        .cornerRadius(8)
        .padding(.horizontal, 24)
        .padding(.vertical, 12)
    }

    // MARK: - Helper Functions

    private func levelColor(_ level: Int) -> Color {
        switch level {
        case 1: return Color(hex: "3B82F6")
        case 2: return Color(hex: "10B981")
        case 3: return Color(hex: "F59E0B")
        case 4: return Color(hex: "8B5CF6")
        default: return Color(hex: "6B7280")
        }
    }

    private func formatDate(_ dateString: String) -> String {
        let formatter = ISO8601DateFormatter()
        if let date = formatter.date(from: dateString) {
            let displayFormatter = DateFormatter()
            displayFormatter.dateFormat = "MM-dd"
            return displayFormatter.string(from: date)
        }
        return dateString.prefix(10).description
    }
}
