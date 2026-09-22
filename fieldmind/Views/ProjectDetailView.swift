"""
项目详情视图
项目信息 + 文档树 + Tab 切换
"""
import SwiftUI

// MARK: - ViewModel
class ProjectDetailViewModel: ObservableObject {
    @Published var project: Project?
    @Published var documents: [DocumentNode] = []
    @Published var selectedTab: Int = 0
    @Published var isLoading: Bool = false

    func loadProject(projectId: Int) {
        isLoading = true

        // TODO: 调用 API
        // GET /api/v1/projects/{project_id}

        // 模拟数据
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) {
            self.project = Project(
                id: projectId,
                name: "某村文化传承调查",
                description: "针对某村的文化传承与产业发展进行的田野调查项目",
                documentCount: 156,
                nodeCount: 2340,
                tags: ["乡村振兴", "非遗", "文化传承"],
                createdAt: Date()
            )

            self.documents = [
                DocumentNode(name: "田野笔记", type: .folder, children: [
                    DocumentNode(name: "2026年9月.pdf", type: .file),
                    DocumentNode(name: "2026年8月.pdf", type: .file)
                ]),
                DocumentNode(name: "访谈记录", type: .folder, children: [
                    DocumentNode(name: "村民访谈.docx", type: .file),
                    DocumentNode(name: "工匠访谈.docx", type: .file)
                ]),
                DocumentNode(name: "影像资料", type: .folder, children: [
                    DocumentNode(name: "照片集", type: .folder, children: [
                        DocumentNode(name: "IMG_001.jpg", type: .file),
                        DocumentNode(name: "IMG_002.jpg", type: .file)
                    ]),
                    DocumentNode(name: "视频.mp4", type: .file)
                ])
            ]

            self.isLoading = false
        }
    }
}

// MARK: - 数据模型
struct Project {
    let id: Int
    let name: String
    let description: String
    let documentCount: Int
    let nodeCount: Int
    let tags: [String]
    let createdAt: Date
}

struct DocumentNode: Identifiable {
    let id = UUID()
    let name: String
    let type: NodeType
    var children: [DocumentNode]?
    var isExpanded: Bool = false

    enum NodeType {
        case folder, file
    }
}

// MARK: - 主视图
struct ProjectDetailView: View {
    @StateObject var viewModel = ProjectDetailViewModel()
    @Environment(\.dismiss) var dismiss
    let projectId: Int

    var body: some View {
        HSplitView {
            // 左侧：文档树
            DocumentTreeSidebar(documents: viewModel.documents)
                .frame(minWidth: 200, idealWidth: 250, maxWidth: 350)

            // 右侧：详情内容
            VStack(spacing: 0) {
                // 顶部栏
                HStack {
                    Button {
                        dismiss()
                    } label: {
                        Image(systemName: "chevron.left")
                        Text("返回")
                    }
                    .buttonStyle(.plain)

                    Spacer()

                    Button("编辑") {}
                        .buttonStyle(.bordered)

                    Button("删除") {}
                        .buttonStyle(.bordered)
                }
                .padding(Spacing.lg)
                .background(Color.fmBgPrimary)

                Divider()

                if viewModel.isLoading {
                    ProgressView()
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else if let project = viewModel.project {
                    ScrollView {
                        VStack(spacing: Spacing.xl) {
                            // 项目信息卡片
                            ProjectInfoCard(project: project)
                                .padding(Spacing.lg)

                            // Tab 切换
                            VStack(spacing: 0) {
                                // Tab 头部
                                HStack(spacing: 0) {
                                    TabButton(title: "文档", isSelected: viewModel.selectedTab == 0) {
                                        viewModel.selectedTab = 0
                                    }
                                    TabButton(title: "知识网络", isSelected: viewModel.selectedTab == 1) {
                                        viewModel.selectedTab = 1
                                    }
                                    TabButton(title: "业态分析", isSelected: viewModel.selectedTab == 2) {
                                        viewModel.selectedTab = 2
                                    }
                                    TabButton(title: "设置", isSelected: viewModel.selectedTab == 3) {
                                        viewModel.selectedTab = 3
                                    }
                                    Spacer()
                                }
                                .background(Color.fmBgPrimary)

                                Divider()

                                // Tab 内容
                                TabContentView(selectedTab: viewModel.selectedTab, projectId: projectId)
                                    .padding(Spacing.lg)
                            }
                        }
                    }
                    .background(Color.fmBgSecondary)
                }
            }
        }
        .onAppear {
            viewModel.loadProject(projectId: projectId)
        }
    }
}

// MARK: - 项目信息卡片
struct ProjectInfoCard: View {
    let project: Project

    var body: some View {
        FMCard {
            VStack(alignment: .leading, spacing: Spacing.lg) {
                HStack(alignment: .top) {
                    VStack(alignment: .leading, spacing: Spacing.sm) {
                        Text(project.name)
                            .font(Typography.h2)
                            .fontWeight(.bold)

                        if !project.description.isEmpty {
                            Text(project.description)
                                .font(Typography.body)
                                .foregroundColor(.fmTextSecondary)
                        }
                    }

                    Spacer()

                    // 标签
                    HStack {
                        ForEach(project.tags, id: \.self) { tag in
                            Text(tag)
                                .font(Typography.caption)
                                .padding(.horizontal, 8)
                                .padding(.vertical, 4)
                                .background(Color.fmAccent.opacity(0.1))
                                .foregroundColor(.fmAccent)
                                .cornerRadius(4)
                        }
                    }
                }

                Divider()

                HStack(spacing: Spacing.xxl) {
                    InfoItem(label: "创建时间", value: project.createdAt.formatted(date: .long, time: .omitted))
                    InfoItem(label: "文档数", value: "\(project.documentCount)")
                    InfoItem(label: "知识节点", value: "\(project.nodeCount)")
                }
            }
        }
    }
}

struct InfoItem: View {
    let label: String
    let value: String

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(label)
                .font(Typography.caption)
                .foregroundColor(.fmTextSecondary)
            Text(value)
                .font(Typography.bodyBold)
                .foregroundColor(.fmTextPrimary)
        }
    }
}

// MARK: - 文档树侧边栏
struct DocumentTreeSidebar: View {
    let documents: [DocumentNode]

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            Text("文档树")
                .font(Typography.h4)
                .padding(Spacing.md)

            Divider()

            List {
                ForEach(documents) { node in
                    DocumentTreeNode(node: node)
                }
            }
            .listStyle(.sidebar)
        }
        .background(Color.fmBgPrimary)
    }
}

struct DocumentTreeNode: View {
    let node: DocumentNode
    @State private var isExpanded: Bool = false

    var body: some View {
        if node.type == .folder {
            DisclosureGroup(
                isExpanded: $isExpanded,
                content: {
                    if let children = node.children {
                        ForEach(children) { child in
                            DocumentTreeNode(node: child)
                        }
                    }
                },
                label: {
                    Label(node.name, systemImage: "folder.fill")
                        .foregroundColor(.fmTextPrimary)
                }
            )
        } else {
            Label(node.name, systemImage: "doc.text")
                .foregroundColor(.fmTextSecondary)
        }
    }
}

// MARK: - Tab 按钮
struct TabButton: View {
    let title: String
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Text(title)
                .font(Typography.body)
                .fontWeight(isSelected ? .semibold : .regular)
                .foregroundColor(isSelected ? .fmAccent : .fmTextSecondary)
                .padding(.horizontal, Spacing.lg)
                .padding(.vertical, Spacing.md)
                .background(
                    isSelected ? Color.fmAccent.opacity(0.1) : Color.clear
                )
        }
        .buttonStyle(.plain)
    }
}

// MARK: - Tab 内容视图
struct TabContentView: View {
    let selectedTab: Int
    let projectId: Int

    var body: some View {
        Group {
            switch selectedTab {
            case 0:
                DocumentsTabView(projectId: projectId)
            case 1:
                KnowledgeNetworkTabView(projectId: projectId)
            case 2:
                BusinessAnalysisTabView(projectId: projectId)
            case 3:
                ProjectSettingsTabView(projectId: projectId)
            default:
                EmptyView()
            }
        }
    }
}

// MARK: - Tab 内容占位符
struct DocumentsTabView: View {
    let projectId: Int

    var body: some View {
        VStack {
            Text("文档列表内容")
                .font(Typography.h3)
            Text("这里将显示项目的所有文档")
                .font(Typography.body)
                .foregroundColor(.fmTextSecondary)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

struct KnowledgeNetworkTabView: View {
    let projectId: Int

    var body: some View {
        VStack {
            Text("知识网络")
                .font(Typography.h3)
            Text("这里将显示知识图谱可视化")
                .font(Typography.body)
                .foregroundColor(.fmTextSecondary)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

struct BusinessAnalysisTabView: View {
    let projectId: Int

    var body: some View {
        VStack {
            Text("业态分析")
                .font(Typography.h3)
            Text("这里将显示业态评估结果")
                .font(Typography.body)
                .foregroundColor(.fmTextSecondary)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

struct ProjectSettingsTabView: View {
    let projectId: Int

    var body: some View {
        VStack(alignment: .leading, spacing: Spacing.lg) {
            Text("项目设置")
                .font(Typography.h3)

            FMCard {
                VStack(alignment: .leading, spacing: Spacing.md) {
                    Text("基本信息")
                        .font(Typography.h4)

                    // 设置项
                    HStack {
                        Text("项目名称")
                        Spacer()
                        TextField("", text: .constant("某村文化传承调查"))
                            .textFieldStyle(.roundedBorder)
                            .frame(width: 300)
                    }

                    HStack {
                        Text("项目描述")
                        Spacer()
                        TextEditor(text: .constant("项目描述内容"))
                            .frame(width: 300, height: 100)
                            .cornerRadius(4)
                    }
                }
            }

            Spacer()
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}

// MARK: - 预览
struct ProjectDetailView_Previews: PreviewProvider {
    static var previews: some View {
        ProjectDetailView(projectId: 1)
            .frame(width: 1200, height: 800)
    }
}
