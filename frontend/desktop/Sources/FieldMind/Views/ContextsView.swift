import SwiftUI

struct ContextsView: View {
    @EnvironmentObject var appState: AppState
    @ObservedObject private var dataManager = ProjectDataManager.shared
    @State private var selectedContext: Context?
    @State private var showRelationshipGraph = false

    var body: some View {
        HSplitView {
            // 左侧：知识脉络树
            VStack(spacing: 0) {
                HStack {
                    Text("知识脉络树")
                        .font(.system(size: 16, weight: .semibold))
                    Spacer()

                    Button(action: { showRelationshipGraph.toggle() }) {
                        HStack(spacing: 4) {
                            Image(systemName: showRelationshipGraph ? "list.bullet" : "point.3.connected.trianglepath.dotted")
                            Text(showRelationshipGraph ? "列表视图" : "关系图")
                        }
                        .font(.system(size: 13))
                    }
                    .buttonStyle(.bordered)

                    Button(action: refreshContexts) {
                        Image(systemName: "arrow.clockwise")
                    }
                    .buttonStyle(.plain)
                    .disabled(dataManager.isLoadingContexts)
                }
                .padding()
                .background(Color(NSColor.controlBackgroundColor))

                Divider()

                if dataManager.isLoadingContexts {
                    ProgressView()
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else if dataManager.contexts.isEmpty {
                    EmptyStateView(icon: "network", message: "暂无知识脉络")
                } else {
                    if showRelationshipGraph {
                        // 关系图视图
                        ContextRelationshipGraphView(
                            contexts: dataManager.contexts,
                            selectedContext: $selectedContext
                        )
                    } else {
                        // 树形列表视图
                        ScrollView {
                            LazyVStack(spacing: 4) {
                                ForEach(dataManager.contexts.filter { $0.level == 1 }) { context in
                                    ContextTreeNode(context: context, selectedContext: $selectedContext)
                                }
                            }
                            .padding(12)
                        }
                    }
                }
            }
            .frame(minWidth: 300, idealWidth: 350)

            // 右侧：脉络详情
            VStack(spacing: 0) {
                if let context = selectedContext {
                    ContextDetailView(context: context)
                } else {
                    EmptyStateView(icon: "arrow.left", message: "从左侧选择一个知识脉络")
                }
            }
        }
    }

    private func refreshContexts() {
        guard let projectId = appState.currentProject?.id else { return }
        dataManager.loadContexts(projectId: projectId)
    }
}

// MARK: - Relationship Graph View

struct ContextRelationshipGraphView: View {
    let contexts: [Context]
    @Binding var selectedContext: Context?
    @State private var offset: CGSize = .zero
    @State private var scale: CGFloat = 1.0

    var body: some View {
        GeometryReader { geometry in
            ZStack {
                Color(NSColor.windowBackgroundColor)

                // 绘制连接线
                ForEach(contexts) { context in
                    if let children = context.children {
                        ForEach(children) { child in
                            let parentPos = nodePosition(for: context, in: geometry)
                            let childPos = nodePosition(for: child, in: geometry)

                            Path { path in
                                path.move(to: parentPos)
                                path.addLine(to: childPos)
                            }
                            .stroke(Color.secondary.opacity(0.3), lineWidth: 2)
                        }
                    }
                }

                // 绘制节点
                ForEach(Array(contexts.enumerated()), id: \.element.id) { index, context in
                    ContextNodeView(
                        context: context,
                        isSelected: selectedContext?.id == context.id
                    )
                    .position(nodePosition(for: context, in: geometry))
                    .onTapGesture {
                        selectedContext = context
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

    private func nodePosition(for context: Context, in geometry: GeometryProxy) -> CGPoint {
        let centerX = geometry.size.width / 2
        let centerY = geometry.size.height / 2

        // 根据层级和索引计算位置
        let level = CGFloat(context.level)
        let radius = level * 80

        // 获取同层级的所有节点
        let sameLevelContexts = contexts.filter { $0.level == context.level }
        guard let index = sameLevelContexts.firstIndex(where: { $0.id == context.id }) else {
            return CGPoint(x: centerX, y: centerY)
        }

        let count = CGFloat(sameLevelContexts.count)
        let angle = (2 * .pi / count) * CGFloat(index)

        let x = centerX + radius * cos(angle) + offset.width
        let y = centerY + radius * sin(angle) + offset.height

        return CGPoint(x: x, y: y)
    }
}

struct ContextNodeView: View {
    let context: Context
    let isSelected: Bool

    var body: some View {
        VStack(spacing: 6) {
            Circle()
                .fill(levelColor(context.level))
                .frame(width: isSelected ? 50 : 40, height: isSelected ? 50 : 40)
                .overlay(
                    Circle()
                        .stroke(Color.white, lineWidth: isSelected ? 4 : 2)
                )
                .overlay(
                    Text("L\(context.level)")
                        .font(.system(size: isSelected ? 14 : 12, weight: .bold))
                        .foregroundColor(.white)
                )

            Text(context.name)
                .font(.system(size: isSelected ? 13 : 11))
                .lineLimit(2)
                .multilineTextAlignment(.center)
                .frame(width: 100)
        }
    }

    private func levelColor(_ level: Int) -> Color {
        switch level {
        case 1: return Color(hex: "667eea")
        case 2: return Color(hex: "48bb78")
        case 3: return Color(hex: "ed8936")
        default: return .secondary
        }
    }
}

// MARK: - Tree Node View

struct ContextTreeNode: View {
    let context: Context
    @Binding var selectedContext: Context?
    @State private var isExpanded = false

    var body: some View {
        VStack(spacing: 2) {
            Button(action: {
                selectedContext = context
                if context.children?.isEmpty == false {
                    withAnimation {
                        isExpanded.toggle()
                    }
                }
            }) {
                HStack(spacing: 8) {
                    if let children = context.children, !children.isEmpty {
                        Image(systemName: isExpanded ? "chevron.down" : "chevron.right")
                            .font(.system(size: 12))
                    } else {
                        Spacer().frame(width: 12)
                    }

                    Image(systemName: "circle.fill")
                        .font(.system(size: 8))
                        .foregroundColor(levelColor(context.level))

                    Text(context.name)
                        .font(.system(size: 14))
                        .lineLimit(1)

                    Spacer()

                    Text("Lv.\(context.level)")
                        .font(.system(size: 11))
                        .foregroundColor(.secondary)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(Color.secondary.opacity(0.1))
                        .cornerRadius(4)
                }
                .padding(.horizontal, 12)
                .padding(.vertical, 8)
                .background(
                    selectedContext?.id == context.id ?
                    Color(hex: "667eea").opacity(0.15) : Color.clear
                )
                .cornerRadius(6)
            }
            .buttonStyle(.plain)

            if isExpanded, let children = context.children {
                VStack(spacing: 2) {
                    ForEach(children) { child in
                        ContextTreeNode(context: child, selectedContext: $selectedContext)
                            .padding(.leading, 20)
                    }
                }
                .transition(.opacity.combined(with: .move(edge: .top)))
            }
        }
    }

    private func levelColor(_ level: Int) -> Color {
        switch level {
        case 1: return Color(hex: "667eea")
        case 2: return Color(hex: "48bb78")
        case 3: return Color(hex: "ed8936")
        default: return .secondary
        }
    }
}

// MARK: - Detail View

struct ContextDetailView: View {
    let context: Context

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 24) {
                // 标题和层级
                VStack(alignment: .leading, spacing: 12) {
                    HStack {
                        Text(context.name)
                            .font(.system(size: 24, weight: .bold))

                        Spacer()

                        Text("第 \(context.level) 层")
                            .font(.system(size: 14))
                            .padding(.horizontal, 12)
                            .padding(.vertical, 6)
                            .background(Color(hex: "667eea").opacity(0.15))
                            .foregroundColor(Color(hex: "667eea"))
                            .cornerRadius(8)
                    }

                    if let description = context.description {
                        Text(description)
                            .font(.system(size: 15))
                            .foregroundColor(.secondary)
                    }
                }

                // 关键词
                VStack(alignment: .leading, spacing: 12) {
                    Text("关键词")
                        .font(.system(size: 16, weight: .semibold))

                    FlowLayout(spacing: 8) {
                        ForEach(context.keywords, id: \.self) { keyword in
                            Text(keyword)
                                .font(.system(size: 13))
                                .padding(.horizontal, 12)
                                .padding(.vertical, 6)
                                .background(Color.secondary.opacity(0.1))
                                .cornerRadius(6)
                        }
                    }
                }
                .padding()
                .background(Color(NSColor.controlBackgroundColor))
                .cornerRadius(12)

                // 相关报告
                if let reports = context.relatedReports, !reports.isEmpty {
                    VStack(alignment: .leading, spacing: 12) {
                        Text("相关报告")
                            .font(.system(size: 16, weight: .semibold))

                        VStack(spacing: 8) {
                            ForEach(reports) { report in
                                ReportRow(report: report)
                            }
                        }
                    }
                    .padding()
                    .background(Color(NSColor.controlBackgroundColor))
                    .cornerRadius(12)
                }

                // 子节点
                if let children = context.children, !children.isEmpty {
                    VStack(alignment: .leading, spacing: 12) {
                        Text("子脉络 (\(children.count))")
                            .font(.system(size: 16, weight: .semibold))

                        VStack(spacing: 8) {
                            ForEach(children) { child in
                                HStack {
                                    Image(systemName: "circle.fill")
                                        .font(.system(size: 8))
                                        .foregroundColor(levelColor(child.level))

                                    Text(child.name)
                                        .font(.system(size: 14))

                                    Spacer()

                                    Text("Lv.\(child.level)")
                                        .font(.system(size: 11))
                                        .foregroundColor(.secondary)
                                }
                                .padding(12)
                                .background(Color(NSColor.controlBackgroundColor))
                                .cornerRadius(8)
                            }
                        }
                    }
                }
            }
            .padding(24)
        }
    }

    private func levelColor(_ level: Int) -> Color {
        switch level {
        case 1: return Color(hex: "667eea")
        case 2: return Color(hex: "48bb78")
        case 3: return Color(hex: "ed8936")
        default: return .secondary
        }
    }
}

struct ReportRow: View {
    let report: ContextReport

    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: "doc.text.fill")
                .font(.system(size: 16))
                .foregroundColor(tierColor(report.tier))

            VStack(alignment: .leading, spacing: 4) {
                Text(report.title)
                    .font(.system(size: 14, weight: .medium))

                Text("第 \(report.tier) 层报告")
                    .font(.system(size: 12))
                    .foregroundColor(.secondary)
            }

            Spacer()

            Image(systemName: "chevron.right")
                .font(.system(size: 12))
                .foregroundColor(.secondary)
        }
        .padding(12)
        .background(Color(NSColor.windowBackgroundColor))
        .cornerRadius(8)
    }

    private func tierColor(_ tier: Int) -> Color {
        switch tier {
        case 1: return Color(hex: "667eea")
        case 2: return Color(hex: "48bb78")
        case 3: return Color(hex: "ed8936")
        default: return .secondary
        }
    }
}
