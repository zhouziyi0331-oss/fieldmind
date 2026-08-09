import SwiftUI

struct GraphView: View {
    @EnvironmentObject var appState: AppState
    @ObservedObject private var dataManager = ProjectDataManager.shared
    @State private var selectedNode: GraphNode?
    @State private var showAddNodeSheet = false
    @State private var isExporting = false
    @State private var isBuilding = false
    @State private var layoutMode: LayoutMode = .network

    enum LayoutMode: String, CaseIterable {
        case network = "网络图"
        case tree = "树形图"
        case timeline = "时间轴"
    }

    var body: some View {
        VStack(spacing: 0) {
            // 工具栏
            HStack {
                Text("知识关系图谱")
                    .font(.system(size: 18, weight: .semibold))

                Spacer()

                // 布局切换器
                Picker("布局", selection: $layoutMode) {
                    ForEach(LayoutMode.allCases, id: \.self) { mode in
                        Text(mode.rawValue).tag(mode)
                    }
                }
                .pickerStyle(.segmented)
                .frame(width: 240)

                if let stats = dataManager.graphStatistics {
                    HStack(spacing: 20) {
                        HStack(spacing: 6) {
                            Image(systemName: "circle.fill")
                                .font(.system(size: 8))
                                .foregroundColor(Color(hex: "667eea"))
                            Text("\(stats.nodeCount) 节点")
                                .font(.system(size: 13))
                        }

                        HStack(spacing: 6) {
                            Image(systemName: "arrow.right")
                                .font(.system(size: 10))
                            Text("\(stats.edgeCount) 关系")
                                .font(.system(size: 13))
                        }
                    }
                    .foregroundColor(.secondary)
                    .padding(.leading, 12)
                }

                Button(action: { showAddNodeSheet = true }) {
                    HStack(spacing: 4) {
                        Image(systemName: "plus.circle")
                        Text("添加节点")
                    }
                }
                .buttonStyle(.bordered)
                .disabled(appState.currentProject == nil)

                Button(action: exportGraph) {
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
                .disabled(dataManager.graph == nil || isExporting)

                Button(action: buildGraph) {
                    HStack {
                        if isBuilding {
                            ProgressView()
                                .scaleEffect(0.7)
                        } else {
                            Image(systemName: "network")
                        }
                        Text("构建图谱")
                    }
                }
                .buttonStyle(.borderedProminent)
                .tint(Color(hex: "9f7aea"))
                .disabled(appState.currentProject == nil || isBuilding)
            }
            .padding()
            .background(Color(NSColor.controlBackgroundColor))

            Divider()

            // 图谱内容
            if appState.currentProject == nil {
                EmptyStateView(icon: "folder.badge.questionmark", message: "请先选择一个项目")
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else if dataManager.isLoadingGraph {
                ProgressView("加载中...")
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else if let graph = dataManager.graph, !graph.nodes.isEmpty {
                HSplitView {
                    // 图谱可视化 - 根据layoutMode显示不同布局
                    Group {
                        switch layoutMode {
                        case .network:
                            GraphCanvasView(graph: graph, selectedNode: $selectedNode)
                        case .tree:
                            TreeLayoutView(graph: graph, selectedNode: $selectedNode)
                        case .timeline:
                            TimelineLayoutView(graph: graph, selectedNode: $selectedNode)
                        }
                    }
                    .frame(minWidth: 400)

                    // 节点详情
                    if let node = selectedNode {
                        NodeDetailView(node: node, graph: graph)
                            .frame(minWidth: 300, idealWidth: 350, maxWidth: 400)
                    } else {
                        EmptyStateView(icon: "arrow.left", message: "点击节点查看详情")
                            .frame(minWidth: 300)
                    }
                }
            } else {
                EmptyStateView(icon: "point.3.connected.trianglepath.dotted", message: "暂无图谱数据，点击构建图谱")
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            }
        }
        .sheet(isPresented: $showAddNodeSheet) {
            AddNodeSheet(isPresented: $showAddNodeSheet, onNodeAdded: {
                dataManager.loadGraphData()
            })
        }
    }

    private func buildGraph() {
        guard let projectId = appState.currentProject?.id else { return }

        isBuilding = true

        Task {
            do {
                let builtGraph = try await APIService.shared.buildGraph(projectId: projectId, documentIds: nil)
                await MainActor.run {
                    dataManager.graph = builtGraph
                    dataManager.graphStatistics = builtGraph.statistics
                    isBuilding = false
                    ToastManager.shared.success("图谱构建完成")
                }
            } catch {
                print("❌ 构建图谱失败: \(error)")
                await MainActor.run {
                    isBuilding = false
                    ToastManager.shared.error("构建图谱失败")
                }
            }
        }
    }

    private func exportGraph() {
        guard let graph = dataManager.graph else { return }

        isExporting = true

        Task {
            do {
                // 创建JSON数据
                var exportData: [String: Any] = [
                    "nodes": graph.nodes.map { node in
                        [
                            "id": node.id,
                            "label": node.label,
                            "type": node.type,
                            "properties": node.properties ?? [:]
                        ]
                    },
                    "edges": graph.edges.map { edge in
                        [
                            "id": edge.id,
                            "source": edge.source,
                            "target": edge.target,
                            "relation": edge.relation
                        ]
                    }
                ]

                if let stats = graph.statistics {
                    exportData["statistics"] = [
                        "nodeCount": stats.nodeCount,
                        "edgeCount": stats.edgeCount,
                        "density": stats.density,
                        "avgDegree": stats.avgDegree
                    ]
                }

                let jsonData = try JSONSerialization.data(withJSONObject: exportData, options: .prettyPrinted)

                await MainActor.run {
                    // 显示保存对话框
                    let savePanel = NSSavePanel()
                    savePanel.allowedContentTypes = [.json]
                    savePanel.nameFieldStringValue = "知识图谱_\(Date().formatted(date: .numeric, time: .omitted)).json"
                    savePanel.message = "选择保存位置"

                    savePanel.begin { response in
                        if response == .OK, let url = savePanel.url {
                            do {
                                try jsonData.write(to: url)
                                print("✅ 图谱导出成功: \(url.path)")
                                ToastManager.shared.success("图谱导出成功")
                            } catch {
                                print("❌ 导出失败: \(error)")
                                ToastManager.shared.error("导出失败")
                            }
                        }
                        self.isExporting = false
                    }
                }
            } catch {
                print("❌ 导出数据准备失败: \(error)")
                await MainActor.run {
                    self.isExporting = false
                    ToastManager.shared.error("导出数据准备失败")
                }
            }
        }
    }
}

// MARK: - Network Layout (网络图)

struct GraphCanvasView: View {
    let graph: KnowledgeGraph
    @Binding var selectedNode: GraphNode?
    @State private var offset: CGSize = .zero
    @State private var scale: CGFloat = 1.0

    var body: some View {
        GeometryReader { geometry in
            ZStack {
                // 背景
                Color(NSColor.windowBackgroundColor)

                // 边
                ForEach(graph.edges) { edge in
                    if let source = graph.nodes.first(where: { $0.id == edge.source }),
                       let target = graph.nodes.first(where: { $0.id == edge.target }),
                       let sx = source.x, let sy = source.y,
                       let tx = target.x, let ty = target.y {

                        Path { path in
                            let startPoint = CGPoint(
                                x: geometry.size.width / 2 + CGFloat(sx) * scale + offset.width,
                                y: geometry.size.height / 2 + CGFloat(sy) * scale + offset.height
                            )
                            let endPoint = CGPoint(
                                x: geometry.size.width / 2 + CGFloat(tx) * scale + offset.width,
                                y: geometry.size.height / 2 + CGFloat(ty) * scale + offset.height
                            )
                            path.move(to: startPoint)
                            path.addLine(to: endPoint)
                        }
                        .stroke(Color.secondary.opacity(0.3), lineWidth: 1)
                    }
                }

                // 节点
                ForEach(graph.nodes) { node in
                    if let x = node.x, let y = node.y {
                        NodeView(node: node, isSelected: selectedNode?.id == node.id)
                            .position(
                                x: geometry.size.width / 2 + CGFloat(x) * scale + offset.width,
                                y: geometry.size.height / 2 + CGFloat(y) * scale + offset.height
                            )
                            .onTapGesture {
                                selectedNode = node
                            }
                    }
                }
            }
        }
        .gesture(
            DragGesture()
                .onChanged { value in
                    offset = value.translation
                }
        )
    }
}

// MARK: - Tree Layout (树形图)

struct TreeLayoutView: View {
    let graph: KnowledgeGraph
    @Binding var selectedNode: GraphNode?
    @State private var offset: CGSize = .zero

    var body: some View {
        ScrollView([.horizontal, .vertical]) {
            ZStack {
                Color(NSColor.windowBackgroundColor)

                // 简化的树形布局 - 垂直排列
                VStack(spacing: 60) {
                    ForEach(Array(groupNodesByLevel().enumerated()), id: \.offset) { levelIndex, levelNodes in
                        HStack(spacing: 40) {
                            ForEach(levelNodes) { node in
                                NodeView(node: node, isSelected: selectedNode?.id == node.id)
                                    .onTapGesture {
                                        selectedNode = node
                                    }
                            }
                        }
                    }
                }
                .padding(40)
            }
        }
    }

    private func groupNodesByLevel() -> [[GraphNode]] {
        // 简单分层：根据节点的出度和入度
        var levels: [[GraphNode]] = []
        var processedNodes = Set<String>()
        var currentLevel: [GraphNode] = []

        // 找到根节点（没有入边的节点）
        let nodesWithIncoming = Set(graph.edges.map { $0.target })
        let rootNodes = graph.nodes.filter { !nodesWithIncoming.contains($0.id) }

        if !rootNodes.isEmpty {
            currentLevel = rootNodes
        } else if !graph.nodes.isEmpty {
            currentLevel = [graph.nodes[0]]
        }

        while !currentLevel.isEmpty {
            levels.append(currentLevel)
            processedNodes.formUnion(currentLevel.map { $0.id })

            // 找到下一层节点
            var nextLevel: [GraphNode] = []
            for node in currentLevel {
                let outgoingEdges = graph.edges.filter { $0.source == node.id }
                for edge in outgoingEdges {
                    if !processedNodes.contains(edge.target),
                       let targetNode = graph.nodes.first(where: { $0.id == edge.target }) {
                        nextLevel.append(targetNode)
                    }
                }
            }
            currentLevel = Array(Set(nextLevel))
        }

        // 添加未处理的节点
        let unprocessed = graph.nodes.filter { !processedNodes.contains($0.id) }
        if !unprocessed.isEmpty {
            levels.append(unprocessed)
        }

        return levels
    }
}

// MARK: - Timeline Layout (时间轴布局)

struct TimelineLayoutView: View {
    let graph: KnowledgeGraph
    @Binding var selectedNode: GraphNode?

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 0) {
                ForEach(timelineGroups(), id: \.period) { group in
                    TimelinePeriodView(
                        period: group.period,
                        nodes: group.nodes,
                        selectedNode: $selectedNode
                    )
                }
            }
            .padding(24)
        }
        .background(Color(NSColor.windowBackgroundColor))
    }

    private func timelineGroups() -> [TimelineGroup] {
        var groups: [String: [GraphNode]] = [:]

        for node in graph.nodes {
            // 尝试从属性中提取时间信息
            var period = "未知时期"
            if let properties = node.properties {
                if let year = properties["year"] {
                    period = "\(year)年"
                } else if let date = properties["date"] {
                    period = date
                } else if let time = properties["time"] {
                    period = time
                }
            }

            if groups[period] == nil {
                groups[period] = []
            }
            groups[period]?.append(node)
        }

        return groups.map { TimelineGroup(period: $0.key, nodes: $0.value) }
            .sorted { $0.period < $1.period }
    }
}

struct TimelineGroup: Identifiable {
    let id = UUID()
    let period: String
    let nodes: [GraphNode]
}

struct TimelinePeriodView: View {
    let period: String
    let nodes: [GraphNode]
    @Binding var selectedNode: GraphNode?
    @State private var isExpanded = true

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            // 时期标题
            Button(action: { isExpanded.toggle() }) {
                HStack {
                    Image(systemName: isExpanded ? "chevron.down" : "chevron.right")
                        .font(.system(size: 12))

                    Text(period)
                        .font(.system(size: 16, weight: .semibold))

                    Text("(\(nodes.count))")
                        .font(.system(size: 14))
                        .foregroundColor(.secondary)

                    Spacer()
                }
                .padding(.vertical, 12)
                .contentShape(Rectangle())
            }
            .buttonStyle(.plain)

            if isExpanded {
                // 时间线
                VStack(alignment: .leading, spacing: 16) {
                    ForEach(nodes) { node in
                        HStack(spacing: 16) {
                            // 时间线标记
                            VStack(spacing: 0) {
                                Circle()
                                    .fill(nodeColor(node.type))
                                    .frame(width: 12, height: 12)

                                if node.id != nodes.last?.id {
                                    Rectangle()
                                        .fill(Color.secondary.opacity(0.3))
                                        .frame(width: 2, height: 40)
                                }
                            }

                            // 节点信息
                            Button(action: { selectedNode = node }) {
                                VStack(alignment: .leading, spacing: 4) {
                                    Text(node.label)
                                        .font(.system(size: 14, weight: .medium))

                                    Text(node.type)
                                        .font(.system(size: 12))
                                        .foregroundColor(.secondary)
                                }
                                .padding(12)
                                .frame(maxWidth: .infinity, alignment: .leading)
                                .background(
                                    selectedNode?.id == node.id
                                        ? Color(hex: "667eea").opacity(0.1)
                                        : Color(NSColor.controlBackgroundColor)
                                )
                                .cornerRadius(8)
                                .overlay(
                                    RoundedRectangle(cornerRadius: 8)
                                        .stroke(
                                            selectedNode?.id == node.id
                                                ? Color(hex: "667eea")
                                                : Color.clear,
                                            lineWidth: 2
                                        )
                                )
                            }
                            .buttonStyle(.plain)
                        }
                    }
                }
                .padding(.leading, 20)
                .padding(.bottom, 24)
            }

            Divider()
        }
    }

    private func nodeColor(_ type: String) -> Color {
        switch type.lowercased() {
        case "person": return Color(hex: "667eea")
        case "place": return Color(hex: "48bb78")
        case "event": return Color(hex: "ed8936")
        case "concept": return Color(hex: "9f7aea")
        default: return .secondary
        }
    }
}

// MARK: - Node View

struct NodeView: View {
    let node: GraphNode
    let isSelected: Bool

    var body: some View {
        VStack(spacing: 4) {
            Circle()
                .fill(nodeColor(node.type))
                .frame(width: isSelected ? 20 : 16, height: isSelected ? 20 : 16)
                .overlay(
                    Circle()
                        .stroke(Color.white, lineWidth: isSelected ? 3 : 2)
                )

            Text(node.label)
                .font(.system(size: 11))
                .foregroundColor(.primary)
                .lineLimit(1)
                .frame(maxWidth: 80)
        }
    }

    private func nodeColor(_ type: String) -> Color {
        switch type.lowercased() {
        case "person": return Color(hex: "667eea")
        case "place": return Color(hex: "48bb78")
        case "event": return Color(hex: "ed8936")
        case "concept": return Color(hex: "9f7aea")
        default: return .secondary
        }
    }
}

// MARK: - Node Detail View

struct NodeDetailView: View {
    let node: GraphNode
    let graph: KnowledgeGraph

    var connectedEdges: [GraphEdge] {
        graph.edges.filter { $0.source == node.id || $0.target == node.id }
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 24) {
                // 节点基本信息
                VStack(alignment: .leading, spacing: 12) {
                    HStack {
                        Circle()
                            .fill(nodeColor(node.type))
                            .frame(width: 16, height: 16)

                        Text(node.label)
                            .font(.system(size: 20, weight: .bold))
                    }

                    Text(node.type)
                        .font(.system(size: 14))
                        .padding(.horizontal, 12)
                        .padding(.vertical, 6)
                        .background(Color.secondary.opacity(0.1))
                        .cornerRadius(6)
                }

                // 属性
                if let properties = node.properties, !properties.isEmpty {
                    VStack(alignment: .leading, spacing: 12) {
                        Text("属性")
                            .font(.system(size: 16, weight: .semibold))

                        VStack(spacing: 8) {
                            ForEach(Array(properties.keys.sorted()), id: \.self) { key in
                                HStack(alignment: .top) {
                                    Text(key)
                                        .font(.system(size: 13, weight: .medium))
                                        .foregroundColor(.secondary)
                                        .frame(width: 80, alignment: .leading)

                                    Text(properties[key] ?? "")
                                        .font(.system(size: 13))
                                        .frame(maxWidth: .infinity, alignment: .leading)
                                }
                                .padding(10)
                                .background(Color(NSColor.controlBackgroundColor))
                                .cornerRadius(6)
                            }
                        }
                    }
                }

                // 关系
                if !connectedEdges.isEmpty {
                    VStack(alignment: .leading, spacing: 12) {
                        Text("关系 (\(connectedEdges.count))")
                            .font(.system(size: 16, weight: .semibold))

                        VStack(spacing: 8) {
                            ForEach(connectedEdges) { edge in
                                RelationshipRow(edge: edge, currentNodeId: node.id, graph: graph)
                            }
                        }
                    }
                }
            }
            .padding(20)
        }
        .background(Color(NSColor.windowBackgroundColor))
    }

    private func nodeColor(_ type: String) -> Color {
        switch type.lowercased() {
        case "person": return Color(hex: "667eea")
        case "place": return Color(hex: "48bb78")
        case "event": return Color(hex: "ed8936")
        case "concept": return Color(hex: "9f7aea")
        default: return .secondary
        }
    }
}

struct RelationshipRow: View {
    let edge: GraphEdge
    let currentNodeId: String
    let graph: KnowledgeGraph

    var otherNode: GraphNode? {
        let otherId = edge.source == currentNodeId ? edge.target : edge.source
        return graph.nodes.first { $0.id == otherId }
    }

    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: "arrow.right")
                .font(.system(size: 12))
                .foregroundColor(.secondary)

            VStack(alignment: .leading, spacing: 4) {
                Text(edge.relation)
                    .font(.system(size: 13, weight: .medium))

                if let other = otherNode {
                    Text(other.label)
                        .font(.system(size: 12))
                        .foregroundColor(.secondary)
                }
            }

            Spacer()
        }
        .padding(10)
        .background(Color(NSColor.controlBackgroundColor))
        .cornerRadius(6)
    }
}

// MARK: - Add Node Sheet

struct AddNodeSheet: View {
    @EnvironmentObject var appState: AppState
    @Binding var isPresented: Bool
    let onNodeAdded: () -> Void

    @State private var label: String = ""
    @State private var type: String = "concept"
    @State private var description: String = ""
    @State private var isCreating: Bool = false

    let nodeTypes = ["person", "place", "event", "concept", "organization"]

    var body: some View {
        VStack(spacing: 0) {
            // 标题栏
            HStack {
                Text("添加节点")
                    .font(.system(size: 18, weight: .semibold))

                Spacer()

                Button(action: { isPresented = false }) {
                    Image(systemName: "xmark.circle.fill")
                        .foregroundColor(.secondary)
                        .font(.system(size: 20))
                }
                .buttonStyle(.plain)
            }
            .padding()
            .background(Color(NSColor.controlBackgroundColor))

            Divider()

            // 表单内容
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    // 节点名称
                    VStack(alignment: .leading, spacing: 8) {
                        Text("节点名称")
                            .font(.system(size: 14, weight: .medium))

                        TextField("输入节点名称", text: $label)
                            .textFieldStyle(.roundedBorder)
                    }

                    // 节点类型
                    VStack(alignment: .leading, spacing: 8) {
                        Text("节点类型")
                            .font(.system(size: 14, weight: .medium))

                        Picker("", selection: $type) {
                            ForEach(nodeTypes, id: \.self) { nodeType in
                                Text(localizedNodeType(nodeType)).tag(nodeType)
                            }
                        }
                        .pickerStyle(.segmented)
                    }

                    // 描述
                    VStack(alignment: .leading, spacing: 8) {
                        Text("描述 (可选)")
                            .font(.system(size: 14, weight: .medium))

                        TextEditor(text: $description)
                            .frame(height: 100)
                            .font(.system(size: 13))
                            .padding(4)
                            .background(Color(NSColor.textBackgroundColor))
                            .cornerRadius(6)
                            .overlay(
                                RoundedRectangle(cornerRadius: 6)
                                    .stroke(Color.secondary.opacity(0.2), lineWidth: 1)
                            )
                    }
                }
                .padding(20)
            }

            Divider()

            // 按钮栏
            HStack {
                Spacer()

                Button("取消") {
                    isPresented = false
                }
                .buttonStyle(.bordered)

                Button(action: createNode) {
                    HStack {
                        if isCreating {
                            ProgressView()
                                .scaleEffect(0.7)
                        }
                        Text("创建")
                    }
                }
                .buttonStyle(.borderedProminent)
                .tint(Color(hex: "9f7aea"))
                .disabled(label.isEmpty || isCreating)
            }
            .padding()
            .background(Color(NSColor.controlBackgroundColor))
        }
        .frame(width: 500, height: 450)
    }

    private func localizedNodeType(_ type: String) -> String {
        switch type {
        case "person": return "人物"
        case "place": return "地点"
        case "event": return "事件"
        case "concept": return "概念"
        case "organization": return "组织"
        default: return type
        }
    }

    private func createNode() {
        guard !label.isEmpty else { return }

        isCreating = true

        Task {
            do {
                var properties: [String: Any] = [
                    "label": label
                ]
                if !description.isEmpty {
                    properties["description"] = description
                }

                _ = try await APIService.shared.createEntity(
                    type: type,
                    properties: properties
                )

                await MainActor.run {
                    print("✅ 节点创建成功")
                    ToastManager.shared.success("节点创建成功")
                    isPresented = false
                    onNodeAdded()
                }
            } catch {
                print("❌ 创建节点失败: \(error)")
                ToastManager.shared.error("创建节点失败")
                await MainActor.run {
                    isCreating = false
                }
            }
        }
    }
}
