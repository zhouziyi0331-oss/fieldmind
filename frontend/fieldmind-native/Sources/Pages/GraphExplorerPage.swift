import SwiftUI

// MARK: - GraphExplorerPage
struct GraphExplorerPage: View {
    let projectId: Int

    @StateObject private var viewModel = KnowledgeGraphViewModel()

    @State private var searchText = ""
    @State private var selectedNodeType: String?
    @State private var layoutMode = "force"  // "force", "hierarchical", "circular"
    @State private var showLabels = true
    @State private var showLegend = true
    @State private var zoomLevel: CGFloat = 1.0  // 0.5 to 2.0
    @State private var selectedNodeId: Int?
    @State private var hoveredNodeId: Int?
    @State private var centerOffset: CGSize = .zero
    @State private var isDragging = false
    @State private var showBuildSheet = false

    let nodeTypes = ["全部类型", "person", "location", "organization", "event", "concept", "artifact", "custom"]

    var graphNodes: [KnowledgeGraphService.GraphNode] {
        viewModel.graphData?.nodes ?? []
    }

    var graphEdges: [KnowledgeGraphService.GraphEdge] {
        viewModel.graphData?.edges ?? []
    }

    var filteredNodes: [KnowledgeGraphService.GraphNode] {
        guard let selectedType = selectedNodeType, selectedType != "全部类型" else {
            return graphNodes
        }
        return graphNodes.filter { $0.group == selectedType }
    }

    var filteredEdges: [KnowledgeGraphService.GraphEdge] {
        let nodeIds = Set(filteredNodes.map { $0.id })
        return graphEdges.filter { nodeIds.contains($0.from) && nodeIds.contains($0.to) }
    }

    var body: some View {
        VStack(spacing: 0) {
            // Top toolbar
            topToolbar

            Divider()

            // Main content
            if viewModel.isLoadingEntities || viewModel.isLoadingGraph {
                VStack(spacing: 16) {
                    ProgressView()
                    Text("加载知识图谱...")
                        .font(.system(size: 14))
                        .foregroundColor(Color.fmText3)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else if let error = viewModel.errorMessage {
                VStack(spacing: 16) {
                    Image(systemName: "exclamationmark.triangle")
                        .font(.system(size: 48))
                        .foregroundColor(Color.fmRed)
                    Text(error)
                        .font(.system(size: 14))
                        .foregroundColor(Color.fmText2)
                    Button("重试") {
                        Task {
                            await viewModel.loadAllData(projectId: projectId)
                        }
                    }
                    .fmPrimary()
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else if graphNodes.isEmpty {
                VStack(spacing: 16) {
                    Image(systemName: "circle.hexagongrid")
                        .font(.system(size: 48))
                        .foregroundColor(Color.fmText3)
                    Text("暂无图谱数据")
                        .font(.system(size: 15))
                        .foregroundColor(Color.fmText2)
                    Button("构建知识图谱") {
                        showBuildSheet = true
                    }
                    .fmPrimary()
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                HStack(spacing: 0) {
                    graphCanvas

                    if showLegend {
                        legendPanel
                    }
                }
            }
        }
        .background(Color.white)
        .task {
            await viewModel.loadAllData(projectId: projectId)
        }
        .sheet(isPresented: $showBuildSheet) {
            BuildKnowledgeGraphSheet(
                projectId: projectId,
                onBuild: { documentIds, forceRebuild in
                    Task {
                        await viewModel.buildKnowledgeGraph(
                            projectId: projectId,
                            documentIds: documentIds,
                            forceRebuild: forceRebuild
                        )
                        showBuildSheet = false
                    }
                }
            )
        }
    }

    // MARK: - Top Toolbar
    private var topToolbar: some View {
        HStack(spacing: 16) {
            // Search
            HStack(spacing: 8) {
                Image(systemName: "magnifyingglass")
                    .foregroundColor(Color.fmText3)
                    .font(.system(size: 14))

                TextField("搜索节点...", text: $searchText)
                    .textFieldStyle(PlainTextFieldStyle())
                    .font(.system(size: 14))

                if !searchText.isEmpty {
                    Button(action: { searchText = "" }) {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundColor(Color.fmText3)
                            .font(.system(size: 14))
                    }
                    .buttonStyle(PlainButtonStyle())
                }
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
            .background(Color.fmBg)
            .cornerRadius(8)
            .frame(width: 280)

            // Node type filter
            Menu {
                ForEach(nodeTypes, id: \.self) { type in
                    Button(action: {
                        selectedNodeType = type == "全部类型" ? nil : type
                    }) {
                        HStack {
                            Text(nodeTypeLabel(type))
                            if (selectedNodeType ?? "全部类型") == type {
                                Spacer()
                                Image(systemName: "checkmark")
                            }
                        }
                    }
                }
            } label: {
                HStack(spacing: 6) {
                    Image(systemName: "circle.hexagongrid")
                        .font(.system(size: 13))
                    Text(nodeTypeLabel(selectedNodeType ?? "全部类型"))
                        .font(.system(size: 13))
                    Image(systemName: "chevron.down")
                        .font(.system(size: 10))
                }
                .foregroundColor(Color.fmText2)
                .padding(.horizontal, 12)
                .padding(.vertical, 7)
                .background(Color.fmBg)
                .cornerRadius(6)
            }
            .menuStyle(BorderlessButtonMenuStyle())

            // Build graph button
            Button(action: { showBuildSheet = true }) {
                HStack(spacing: 6) {
                    Image(systemName: "hammer")
                        .font(.system(size: 13))
                    Text("构建图谱")
                        .font(.system(size: 13))
                }
                .foregroundColor(Color.fmText)
                .padding(.horizontal, 12)
                .padding(.vertical, 7)
                .background(Color.fmBg)
                .cornerRadius(6)
            }
            .buttonStyle(PlainButtonStyle())
            .disabled(viewModel.isBuilding)

            // Layout mode
            Menu {
                Button(action: { layoutMode = "force" }) {
                    HStack {
                        Text("力导向布局")
                        if layoutMode == "force" {
                            Spacer()
                            Image(systemName: "checkmark")
                        }
                    }
                }
                Button(action: { layoutMode = "hierarchical" }) {
                    HStack {
                        Text("层级布局")
                        if layoutMode == "hierarchical" {
                            Spacer()
                            Image(systemName: "checkmark")
                        }
                    }
                }
                Button(action: { layoutMode = "circular" }) {
                    HStack {
                        Text("环形布局")
                        if layoutMode == "circular" {
                            Spacer()
                            Image(systemName: "checkmark")
                        }
                    }
                }
            } label: {
                HStack(spacing: 6) {
                    Image(systemName: "circle.grid.cross")
                        .font(.system(size: 13))
                    Text(layoutModeLabel())
                        .font(.system(size: 13))
                    Image(systemName: "chevron.down")
                        .font(.system(size: 10))
                }
                .foregroundColor(Color.fmText2)
                .padding(.horizontal, 12)
                .padding(.vertical, 7)
                .background(Color.fmBg)
                .cornerRadius(6)
            }
            .menuStyle(BorderlessButtonMenuStyle())

            Spacer()

            // Zoom controls
            HStack(spacing: 8) {
                Button(action: { zoomLevel = max(0.5, zoomLevel - 0.1) }) {
                    Image(systemName: "minus.magnifyingglass")
                        .font(.system(size: 13))
                }
                .buttonStyle(PlainButtonStyle())
                .foregroundColor(Color.fmText2)

                Text("\(Int(zoomLevel * 100))%")
                    .font(.system(size: 12))
                    .foregroundColor(Color.fmText3)
                    .frame(width: 45)

                Button(action: { zoomLevel = min(2.0, zoomLevel + 0.1) }) {
                    Image(systemName: "plus.magnifyingglass")
                        .font(.system(size: 13))
                }
                .buttonStyle(PlainButtonStyle())
                .foregroundColor(Color.fmText2)
            }
            .padding(.horizontal, 10)
            .padding(.vertical, 6)
            .background(Color.fmBg)
            .cornerRadius(6)

            // Reset view
            Button(action: {
                zoomLevel = 1.0
                centerOffset = .zero
            }) {
                HStack(spacing: 6) {
                    Image(systemName: "arrow.counterclockwise")
                        .font(.system(size: 13))
                    Text("重置")
                        .font(.system(size: 13))
                }
                .foregroundColor(Color.fmText2)
                .padding(.horizontal, 12)
                .padding(.vertical, 7)
                .background(Color.fmBg)
                .cornerRadius(6)
            }
            .buttonStyle(PlainButtonStyle())

            // Labels toggle
            Button(action: { showLabels.toggle() }) {
                HStack(spacing: 6) {
                    Image(systemName: showLabels ? "textformat" : "textformat.alt")
                        .font(.system(size: 13))
                    Text("标签")
                        .font(.system(size: 13))
                }
                .foregroundColor(showLabels ? Color.blue : Color.fmText2)
                .padding(.horizontal, 12)
                .padding(.vertical, 7)
                .background(showLabels ? Color.blue.opacity(0.1) : Color.fmBg)
                .cornerRadius(6)
                .overlay(
                    RoundedRectangle(cornerRadius: 6)
                        .stroke(showLabels ? Color.blue : Color.fmBorder, lineWidth: 1)
                )
            }
            .buttonStyle(PlainButtonStyle())

            // Legend toggle
            Button(action: { showLegend.toggle() }) {
                HStack(spacing: 6) {
                    Image(systemName: showLegend ? "chart.bar.fill" : "chart.bar")
                        .font(.system(size: 13))
                    Text("图例")
                        .font(.system(size: 13))
                }
                .foregroundColor(showLegend ? Color.blue : Color.fmText2)
                .padding(.horizontal, 12)
                .padding(.vertical, 7)
                .background(showLegend ? Color.blue.opacity(0.1) : Color.fmBg)
                .cornerRadius(6)
                .overlay(
                    RoundedRectangle(cornerRadius: 6)
                        .stroke(showLegend ? Color.blue : Color.fmBorder, lineWidth: 1)
                )
            }
            .buttonStyle(PlainButtonStyle())

            // Export button
            Button(action: { print("Export graph") }) {
                HStack(spacing: 6) {
                    Image(systemName: "square.and.arrow.up")
                        .font(.system(size: 13))
                    Text("导出")
                        .font(.system(size: 13))
                }
                .foregroundColor(Color.fmText)
                .padding(.horizontal, 12)
                .padding(.vertical, 7)
                .background(Color.fmBg)
                .cornerRadius(6)
            }
            .buttonStyle(PlainButtonStyle())
        }
        .padding(.horizontal, 20)
        .padding(.vertical, 12)
        .background(Color.white)
    }

    // MARK: - Graph Canvas
    private var graphCanvas: some View {
        GeometryReader { geometry in
            ZStack {
                // Background
                Color.fmBg.opacity(0.3)

                // Graph content
                ZStack {
                    // Edges
                    ForEach(filteredEdges) { edge in
                        if let sourceNode = filteredNodes.first(where: { $0.id == edge.from }),
                           let targetNode = filteredNodes.first(where: { $0.id == edge.to }) {
                            Path { path in
                                let sourcePos = getNodePosition(sourceNode, in: geometry.size)
                                let targetPos = getNodePosition(targetNode, in: geometry.size)
                                path.move(to: sourcePos)
                                path.addLine(to: targetPos)
                            }
                            .stroke(Color.gray.opacity(0.3), lineWidth: 1.5 / zoomLevel)
                        }
                    }

                    // Nodes
                    ForEach(filteredNodes) { node in
                        let position = getNodePosition(node, in: geometry.size)
                        ZStack {
                            Circle()
                                .fill(Color(hex: node.color ?? "64748B"))
                                .frame(width: 24, height: 24)
                                .overlay(
                                    Circle()
                                        .stroke(selectedNodeId == node.id ? Color.blue : Color.clear, lineWidth: 3)
                                )

                            if showLabels {
                                Text(node.label)
                                    .font(.system(size: 11))
                                    .foregroundColor(Color.fmText)
                                    .padding(.horizontal, 6)
                                    .padding(.vertical, 3)
                                    .background(Color.white.opacity(0.9))
                                    .cornerRadius(4)
                                    .offset(y: 20)
                            }
                        }
                        .position(position)
                        .onTapGesture {
                            selectedNodeId = node.id
                        }
                        .onHover { hovering in
                            hoveredNodeId = hovering ? node.id : nil
                        }
                    }
                }
                .scaleEffect(zoomLevel)
                .offset(centerOffset)
                .gesture(
                    DragGesture()
                        .onChanged { value in
                            isDragging = true
                            centerOffset = value.translation
                        }
                        .onEnded { _ in
                            isDragging = false
                        }
                )

                // Empty state
                if filteredNodes.isEmpty {
                    VStack(spacing: 16) {
                        Image(systemName: "circle.hexagongrid")
                            .font(.system(size: 48))
                            .foregroundColor(Color.fmText3)

                        Text("暂无图谱数据")
                            .font(.system(size: 15))
                            .foregroundColor(Color.fmText2)

                        Text("尝试调整筛选条件")
                            .font(.system(size: 13))
                            .foregroundColor(Color.fmText3)
                    }
                }

                // Stats overlay
                VStack {
                    Spacer()
                    HStack {
                        HStack(spacing: 8) {
                            Image(systemName: "circle.fill")
                                .font(.system(size: 8))
                                .foregroundColor(Color.blue)
                            Text("\(filteredNodes.count) 节点")
                                .font(.system(size: 12))

                            Image(systemName: "arrow.right")
                                .font(.system(size: 8))
                                .foregroundColor(Color.fmText3)
                            Text("\(filteredEdges.count) 关系")
                                .font(.system(size: 12))
                        }
                        .foregroundColor(Color.fmText2)
                        .padding(.horizontal, 12)
                        .padding(.vertical, 8)
                        .background(Color.white.opacity(0.95))
                        .cornerRadius(8)
                        .shadow(color: Color.black.opacity(0.1), radius: 4, x: 0, y: 2)

                        Spacer()
                    }
                    .padding(20)
                }
            }
        }
    }

    // MARK: - Legend Panel
    private var legendPanel: some View {
        VStack(alignment: .leading, spacing: 20) {
            // Title
            HStack {
                Text("图例")
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundColor(Color.fmText)

                Spacer()

                Button(action: { showLegend = false }) {
                    Image(systemName: "xmark")
                        .font(.system(size: 12))
                        .foregroundColor(Color.fmText3)
                }
                .buttonStyle(PlainButtonStyle())
            }

            Divider()

            // Node types
            VStack(alignment: .leading, spacing: 12) {
                Text("节点类型")
                    .font(.system(size: 13, weight: .medium))
                    .foregroundColor(Color.fmText2)

                ForEach(getNodeTypeLegend(), id: \.type) { item in
                    GraphLegendItem(
                        color: item.color,
                        icon: item.icon,
                        label: item.type,
                        count: item.count
                    )
                }
            }

            Divider()

            // Relationship types
            VStack(alignment: .leading, spacing: 12) {
                Text("关系类型")
                    .font(.system(size: 13, weight: .medium))
                    .foregroundColor(Color.fmText2)

                ForEach(getRelationshipLegend(), id: \.type) { item in
                    GraphRelationshipLegendItem(
                        label: item.type,
                        count: item.count
                    )
                }
            }

            Divider()

            // Statistics
            VStack(alignment: .leading, spacing: 10) {
                Text("统计信息")
                    .font(.system(size: 13, weight: .medium))
                    .foregroundColor(Color.fmText2)

                GraphStatRow(label: "节点总数", value: "\(filteredNodes.count)")
                GraphStatRow(label: "关系总数", value: "\(filteredEdges.count)")
                GraphStatRow(label: "平均连接", value: String(format: "%.1f", averageConnections()))
                GraphStatRow(label: "布局模式", value: layoutModeLabel())
            }

            Spacer()
        }
        .padding(20)
        .frame(width: 260)
        .background(Color.white)
        .overlay(
            Rectangle()
                .fill(Color.fmBorder)
                .frame(width: 1),
            alignment: .leading
        )
    }

    // MARK: - Helper Functions
    private func nodeTypeLabel(_ type: String) -> String {
        switch type {
        case "全部类型": return "全部类型"
        case "person": return "人物"
        case "location": return "地点"
        case "organization": return "组织"
        case "event": return "事件"
        case "concept": return "概念"
        case "artifact": return "物品"
        case "custom": return "自定义"
        default: return type
        }
    }

    private func getNodePosition(_ node: KnowledgeGraphService.GraphNode, in size: CGSize) -> CGPoint {
        switch layoutMode {
        case "force":
            return forceDirectedPosition(node, in: size)
        case "hierarchical":
            return hierarchicalPosition(node, in: size)
        case "circular":
            return circularPosition(node, in: size)
        default:
            return forceDirectedPosition(node, in: size)
        }
    }

    private func forceDirectedPosition(_ node: KnowledgeGraphService.GraphNode, in size: CGSize) -> CGPoint {
        // Simplified force-directed layout simulation
        let index = filteredNodes.firstIndex(where: { $0.id == node.id }) ?? 0
        let count = filteredNodes.count
        let angle = (Double(index) / Double(count)) * 2 * .pi
        let radius = min(size.width, size.height) * 0.3

        return CGPoint(
            x: size.width / 2 + CGFloat(cos(angle)) * radius,
            y: size.height / 2 + CGFloat(sin(angle)) * radius
        )
    }

    private func hierarchicalPosition(_ node: KnowledgeGraphService.GraphNode, in size: CGSize) -> CGPoint {
        let index = filteredNodes.firstIndex(where: { $0.id == node.id }) ?? 0
        let count = filteredNodes.count
        let columns = 5
        let row = index / columns
        let col = index % columns

        let horizontalSpacing = size.width * 0.8 / CGFloat(columns)
        let verticalSpacing = size.height * 0.8 / CGFloat((count + columns - 1) / columns)

        return CGPoint(
            x: size.width * 0.1 + CGFloat(col) * horizontalSpacing,
            y: size.height * 0.1 + CGFloat(row) * verticalSpacing
        )
    }

    private func circularPosition(_ node: KnowledgeGraphService.GraphNode, in size: CGSize) -> CGPoint {
        let index = filteredNodes.firstIndex(where: { $0.id == node.id }) ?? 0
        let count = filteredNodes.count
        let angle = (Double(index) / Double(count)) * 2 * .pi
        let radius = min(size.width, size.height) * 0.35

        return CGPoint(
            x: size.width / 2 + CGFloat(cos(angle)) * radius,
            y: size.height / 2 + CGFloat(sin(angle)) * radius
        )
    }

    private func layoutModeLabel() -> String {
        switch layoutMode {
        case "force": return "力导向"
        case "hierarchical": return "层级"
        case "circular": return "环形"
        default: return "力导向"
        }
    }

    private func getNodeTypeLegend() -> [(type: String, color: String, icon: String, count: Int)] {
        let typeGroups = Dictionary(grouping: filteredNodes) { $0.group }
        return typeGroups.map { (group, nodes) in
            let type = nodeTypeLabel(group)
            let color = nodes.first?.color ?? "64748B"
            let icon = "circle.fill"
            return (type: type, color: color, icon: icon, count: nodes.count)
        }.sorted { $0.count > $1.count }
    }

    private func getRelationshipLegend() -> [(type: String, count: Int)] {
        let labelCounts = Dictionary(grouping: filteredEdges) { $0.label ?? "未知" }
            .mapValues { $0.count }
        return labelCounts.map { (type: $0.key, count: $0.value) }
            .sorted { $0.count > $1.count }
    }

    private func averageConnections() -> Double {
        guard !filteredNodes.isEmpty else { return 0 }
        return Double(filteredEdges.count * 2) / Double(filteredNodes.count)
    }
}

// MARK: - Build Knowledge Graph Sheet
struct BuildKnowledgeGraphSheet: View {
    let projectId: Int
    let onBuild: ([Int]?, Bool) -> Void

    @State private var forceRebuild = false
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        VStack(spacing: 24) {
            HStack {
                Text("构建知识图谱")
                    .font(.system(size: 18, weight: .semibold))
                    .foregroundColor(Color.fmText)

                Spacer()

                Button(action: { dismiss() }) {
                    Image(systemName: "xmark")
                        .font(.system(size: 14))
                        .foregroundColor(Color.fmText3)
                }
                .buttonStyle(PlainButtonStyle())
            }

            Divider()

            VStack(alignment: .leading, spacing: 16) {
                Toggle(isOn: $forceRebuild) {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("强制重建")
                            .font(.system(size: 14, weight: .medium))
                            .foregroundColor(Color.fmText)
                        Text("删除现有图谱数据并重新提取所有实体和关系")
                            .font(.system(size: 12))
                            .foregroundColor(Color.fmText3)
                    }
                }
                .toggleStyle(SwitchToggleStyle())

                Text("提示：构建过程可能需要几分钟时间，请耐心等待")
                    .font(.system(size: 12))
                    .foregroundColor(Color.fmText3)
                    .padding(.top, 8)
            }

            Spacer()

            HStack(spacing: 12) {
                Button("取消") {
                    dismiss()
                }
                .fmSecondary()

                Button("开始构建") {
                    onBuild(nil, forceRebuild)
                }
                .fmPrimary()
            }
        }
        .padding(24)
        .frame(width: 480, height: 280)
        .background(Color.white)
    }
}
