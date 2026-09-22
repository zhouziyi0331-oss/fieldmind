"""
文档列表视图
参考 streamlabs 的列表设计 + metabase 的筛选器
"""
import SwiftUI

// MARK: - ViewModel
class DocumentListViewModel: ObservableObject {
    @Published var documents: [Document] = []
    @Published var searchText: String = ""
    @Published var selectedType: DocumentType?
    @Published var sortBy: SortOption = .dateDesc
    @Published var viewMode: ViewMode = .card
    @Published var isLoading: Bool = false

    var filteredDocuments: [Document] {
        var result = documents

        // 搜索过滤
        if !searchText.isEmpty {
            result = result.filter { doc in
                doc.name.localizedCaseInsensitiveContains(searchText) ||
                (doc.tags?.contains { $0.localizedCaseInsensitiveContains(searchText) } ?? false)
            }
        }

        // 类型过滤
        if let type = selectedType {
            result = result.filter { $0.type == type }
        }

        // 排序
        switch sortBy {
        case .dateDesc:
            result.sort { $0.uploadedAt > $1.uploadedAt }
        case .dateAsc:
            result.sort { $0.uploadedAt < $1.uploadedAt }
        case .nameAsc:
            result.sort { $0.name < $1.name }
        case .sizeDesc:
            result.sort { $0.fileSize > $1.fileSize }
        }

        return result
    }

    func loadDocuments(projectId: Int) {
        isLoading = true

        // TODO: 调用 API
        // GET /api/v1/documents/projects/{project_id}/documents/

        // 模拟数据
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) {
            self.documents = Self.mockDocuments
            self.isLoading = false
        }
    }

    static let mockDocuments: [Document] = [
        Document(name: "田野笔记001.pdf", type: .pdf, fileSize: 2048000, status: .completed, uploadedAt: Date()),
        Document(name: "访谈记录.docx", type: .word, fileSize: 1024000, status: .processing, uploadedAt: Date().addingTimeInterval(-3600)),
        Document(name: "照片集.jpg", type: .image, fileSize: 5120000, status: .completed, uploadedAt: Date().addingTimeInterval(-7200)),
        Document(name: "调查问卷.xlsx", type: .excel, fileSize: 512000, status: .completed, uploadedAt: Date().addingTimeInterval(-10800)),
        Document(name: "录音文件.mp3", type: .audio, fileSize: 10240000, status: .failed, uploadedAt: Date().addingTimeInterval(-14400)),
    ]
}

// MARK: - 数据模型
struct Document: Identifiable {
    let id = UUID()
    let name: String
    let type: DocumentType
    let fileSize: Int
    let status: DocumentStatus
    let uploadedAt: Date
    let tags: [String]?

    init(name: String, type: DocumentType, fileSize: Int, status: DocumentStatus, uploadedAt: Date, tags: [String]? = nil) {
        self.name = name
        self.type = type
        self.fileSize = fileSize
        self.status = status
        self.uploadedAt = uploadedAt
        self.tags = tags
    }

    var fileSizeFormatted: String {
        let formatter = ByteCountFormatter()
        formatter.countStyle = .file
        return formatter.string(fromByteCount: Int64(fileSize))
    }

    var typeIcon: String {
        type.icon
    }
}

enum DocumentType: String, CaseIterable {
    case pdf = "PDF"
    case word = "Word"
    case excel = "Excel"
    case image = "图片"
    case audio = "音频"
    case video = "视频"
    case text = "文本"

    var icon: String {
        switch self {
        case .pdf: return "doc.text.fill"
        case .word: return "doc.richtext"
        case .excel: return "tablecells"
        case .image: return "photo"
        case .audio: return "waveform"
        case .video: return "video"
        case .text: return "doc.plaintext"
        }
    }
}

enum DocumentStatus: String {
    case pending = "等待中"
    case processing = "处理中"
    case completed = "已完成"
    case failed = "失败"
}

enum SortOption: String, CaseIterable {
    case dateDesc = "最新优先"
    case dateAsc = "最早优先"
    case nameAsc = "名称升序"
    case sizeDesc = "大小降序"
}

enum ViewMode {
    case card, list
}

// MARK: - 主视图
struct DocumentListView: View {
    @StateObject var viewModel = DocumentListViewModel()
    let projectId: Int

    var body: some View {
        VStack(spacing: 0) {
            // 筛选栏
            DocumentFilterBar(
                searchText: $viewModel.searchText,
                selectedType: $viewModel.selectedType,
                sortBy: $viewModel.sortBy,
                viewMode: $viewModel.viewMode
            )
            .padding(Spacing.md)
            .background(Color.fmBgPrimary)

            Divider()

            // 文档列表
            ScrollView {
                if viewModel.isLoading {
                    ProgressView()
                        .padding(Spacing.xxl)
                } else if viewModel.filteredDocuments.isEmpty {
                    EmptyStateView(
                        icon: "doc.text.magnifyingglass",
                        title: "未找到文档",
                        message: "尝试调整筛选条件"
                    )
                    .padding(Spacing.xxl)
                } else {
                    if viewModel.viewMode == .card {
                        DocumentCardGrid(documents: viewModel.filteredDocuments)
                    } else {
                        DocumentListRows(documents: viewModel.filteredDocuments)
                    }
                }
            }
            .background(Color.fmBgSecondary)

            // 底部分页
            HStack {
                Text("共 \(viewModel.filteredDocuments.count) 个文档")
                    .font(Typography.caption)
                    .foregroundColor(.fmTextSecondary)

                Spacer()

                HStack(spacing: Spacing.sm) {
                    Button("上一页") {}
                        .buttonStyle(.bordered)
                        .disabled(true)

                    Text("1 / 1")
                        .font(Typography.caption)

                    Button("下一页") {}
                        .buttonStyle(.bordered)
                        .disabled(true)
                }
            }
            .padding(Spacing.md)
            .background(Color.fmBgPrimary)
        }
        .onAppear {
            viewModel.loadDocuments(projectId: projectId)
        }
    }
}

// MARK: - 筛选栏
struct DocumentFilterBar: View {
    @Binding var searchText: String
    @Binding var selectedType: DocumentType?
    @Binding var sortBy: SortOption
    @Binding var viewMode: ViewMode

    var body: some View {
        HStack(spacing: Spacing.md) {
            // 搜索框
            FMSearchField(text: $searchText, placeholder: "搜索文档...")
                .frame(maxWidth: 300)

            // 类型筛选
            Menu {
                Button("全部类型") {
                    selectedType = nil
                }
                Divider()
                ForEach(DocumentType.allCases, id: \.self) { type in
                    Button(type.rawValue) {
                        selectedType = type
                    }
                }
            } label: {
                HStack {
                    Image(systemName: "line.3.horizontal.decrease.circle")
                    Text(selectedType?.rawValue ?? "筛选")
                }
            }
            .buttonStyle(.bordered)

            // 排序
            Menu {
                ForEach(SortOption.allCases, id: \.self) { option in
                    Button(option.rawValue) {
                        sortBy = option
                    }
                }
            } label: {
                HStack {
                    Image(systemName: "arrow.up.arrow.down")
                    Text(sortBy.rawValue)
                }
            }
            .buttonStyle(.bordered)

            Spacer()

            // 视图切换
            Picker("", selection: $viewMode) {
                Image(systemName: "square.grid.2x2").tag(ViewMode.card)
                Image(systemName: "list.bullet").tag(ViewMode.list)
            }
            .pickerStyle(.segmented)
            .frame(width: 100)

            // 上传按钮
            Button {
                // TODO: 打开上传界面
            } label: {
                HStack {
                    Image(systemName: "plus")
                    Text("上传")
                }
            }
            .buttonStyle(.borderedProminent)
        }
    }
}

// MARK: - 卡片网格
struct DocumentCardGrid: View {
    let documents: [Document]

    let columns = [
        GridItem(.flexible()),
        GridItem(.flexible()),
        GridItem(.flexible()),
        GridItem(.flexible())
    ]

    var body: some View {
        LazyVGrid(columns: columns, spacing: Spacing.lg) {
            ForEach(documents) { doc in
                DocumentCard(document: doc)
            }
        }
        .padding(Spacing.lg)
    }
}

// MARK: - 文档卡片
struct DocumentCard: View {
    let document: Document
    @State private var isHovered = false

    var body: some View {
        Button {
            // TODO: 打开文档详情
        } label: {
            VStack(alignment: .leading, spacing: Spacing.sm) {
                // 缩略图
                ZStack {
                    Rectangle()
                        .fill(Color.fmGray100)
                        .aspectRatio(1.4, contentMode: .fit)

                    Image(systemName: document.typeIcon)
                        .font(.system(size: 48))
                        .foregroundColor(.fmGray400)
                }
                .cornerRadius(8)

                // 信息
                VStack(alignment: .leading, spacing: 4) {
                    Text(document.name)
                        .font(Typography.body)
                        .foregroundColor(.fmTextPrimary)
                        .lineLimit(2)

                    HStack {
                        Text(document.type.rawValue)
                        Text("·")
                        Text(document.fileSizeFormatted)
                    }
                    .font(Typography.caption)
                    .foregroundColor(.fmTextSecondary)

                    FMStatusBadge(status: document.status.rawValue)
                }
                .padding(.horizontal, 8)
                .padding(.bottom, 8)
            }
        }
        .buttonStyle(.plain)
        .background(Color.fmBgPrimary)
        .cornerRadius(12)
        .shadow(color: .black.opacity(isHovered ? 0.1 : 0.05), radius: isHovered ? 12 : 8, y: 2)
        .scaleEffect(isHovered ? 1.02 : 1.0)
        .animation(.spring(response: 0.3), value: isHovered)
        .onHover { hovering in
            isHovered = hovering
        }
    }
}

// MARK: - 列表行
struct DocumentListRows: View {
    let documents: [Document]

    var body: some View {
        VStack(spacing: 0) {
            ForEach(documents) { doc in
                DocumentListRow(document: doc)
                Divider()
            }
        }
        .background(Color.fmBgPrimary)
        .cornerRadius(12)
        .padding(Spacing.lg)
    }
}

struct DocumentListRow: View {
    let document: Document

    var body: some View {
        HStack(spacing: Spacing.md) {
            Image(systemName: document.typeIcon)
                .font(.title2)
                .foregroundColor(.fmAccent)
                .frame(width: 40)

            VStack(alignment: .leading, spacing: 4) {
                Text(document.name)
                    .font(Typography.body)
                    .foregroundColor(.fmTextPrimary)

                Text(document.uploadedAt, style: .relative)
                    .font(Typography.caption)
                    .foregroundColor(.fmTextSecondary)
            }

            Spacer()

            Text(document.fileSizeFormatted)
                .font(Typography.caption)
                .foregroundColor(.fmTextSecondary)
                .frame(width: 80, alignment: .trailing)

            FMStatusBadge(status: document.status.rawValue)
                .frame(width: 80)

            Button {} label: {
                Image(systemName: "ellipsis")
            }
            .buttonStyle(.plain)
        }
        .padding(.vertical, Spacing.sm)
        .padding(.horizontal, Spacing.md)
    }
}

// MARK: - 空状态
struct EmptyStateView: View {
    let icon: String
    let title: String
    let message: String

    var body: some View {
        VStack(spacing: Spacing.lg) {
            Image(systemName: icon)
                .font(.system(size: 64))
                .foregroundColor(.fmGray400)

            Text(title)
                .font(Typography.h3)
                .foregroundColor(.fmTextPrimary)

            Text(message)
                .font(Typography.body)
                .foregroundColor(.fmTextSecondary)
        }
    }
}

// MARK: - 预览
struct DocumentListView_Previews: PreviewProvider {
    static var previews: some View {
        DocumentListView(projectId: 1)
    }
}
