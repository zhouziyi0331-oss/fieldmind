"""
资产库视图 - 严格遵循设计标准
参考: Donezo Dashboard + Succulents 配色
"""
import SwiftUI

// MARK: - Assets View Model
class AssetsViewModel: ObservableObject {
    @Published var assets: [AssetItem] = [
        AssetItem(
            name: "数据分析模板",
            description: "可复用的数据分析工作流模板，包含完整的数据处理步骤",
            type: "模板",
            category: "分析",
            color: Color.fmPrimary,
            downloads: 342,
            size: "2.4 MB",
            updated: "2天前",
            tags: ["数据分析", "可视化", "报告"]
        ),
        AssetItem(
            name: "机器学习模型 v3.2",
            description: "预训练的文本分类模型，准确率达92%",
            type: "模型",
            category: "AI",
            color: Color.fmSecondary,
            downloads: 156,
            size: "45.8 MB",
            updated: "1周前",
            tags: ["ML", "NLP", "分类"]
        ),
        AssetItem(
            name: "客户行为数据集",
            description: "精选的客户行为分析训练数据集",
            type: "数据集",
            category: "数据",
            color: Color.fmWarning,
            downloads: 89,
            size: "128.5 MB",
            updated: "3天前",
            tags: ["数据", "客户", "行为"]
        ),
        AssetItem(
            name: "可视化组件库",
            description: "常用的数据可视化图表组件集合",
            type: "组件",
            category: "UI",
            color: Color.fmInfo,
            downloads: 234,
            size: "8.2 MB",
            updated: "5天前",
            tags: ["可视化", "图表", "组件"]
        ),
        AssetItem(
            name: "API集成脚本",
            description: "与第三方服务API集成的脚本集合",
            type: "脚本",
            category: "工具",
            color: Color(hex: "9FAC24"),
            downloads: 178,
            size: "1.2 MB",
            updated: "1天前",
            tags: ["API", "集成", "自动化"]
        ),
        AssetItem(
            name: "报告模板集",
            description: "专业的商业报告模板，包含多种样式",
            type: "模板",
            category: "文档",
            color: Color(hex: "6FA7B6"),
            downloads: 267,
            size: "15.6 MB",
            updated: "4天前",
            tags: ["报告", "模板", "文档"]
        )
    ]
}

// MARK: - Main Assets View
struct StandardAssetsView: View {
    @StateObject private var viewModel = AssetsViewModel()
    @State private var searchText = ""
    @State private var selectedCategory = "全部"

    var body: some View {
        ScrollView {
            VStack(spacing: 24) {
                // 页面标题区域
                headerSection
                    .padding(.horizontal, 24)

                // 搜索和过滤栏
                searchFilterSection
                    .padding(.horizontal, 24)

                // 资产卡片网格（3列）
                assetsGridSection
                    .padding(.horizontal, 24)

                Spacer()
            }
            .padding(.vertical, 24)
        }
        .background(Color.fmBgSecondary)
    }

    // MARK: - Header Section
    private var headerSection: some View {
        HStack(alignment: .top) {
            VStack(alignment: .leading, spacing: 4) {
                Text("资产库")
                    .font(.system(size: 32, weight: .bold))
                    .foregroundColor(.fmTextPrimary)

                Text("管理可复用的知识资产")
                    .font(.system(size: 16, weight: .regular))
                    .foregroundColor(.fmTextSecondary)
            }

            Spacer()

            Button(action: {}) {
                HStack(spacing: 6) {
                    Image(systemName: "arrow.up.doc")
                        .font(.system(size: 14))
                    Text("上传资产")
                        .font(.system(size: 14, weight: .medium))
                }
                .foregroundColor(.white)
                .padding(.horizontal, 16)
                .padding(.vertical, 10)
                .background(Color.fmPrimary)
                .cornerRadius(8)
            }
            .buttonStyle(ScaleButtonStyle())
        }
    }

    // MARK: - Search and Filter Section
    private var searchFilterSection: some View {
        HStack(spacing: 12) {
            HStack(spacing: 8) {
                Image(systemName: "magnifyingglass")
                    .font(.system(size: 14))
                    .foregroundColor(.fmTextTertiary)

                TextField("搜索资产...", text: $searchText)
                    .font(.system(size: 14))
                    .textFieldStyle(.plain)
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 10)
            .background(Color.white)
            .cornerRadius(8)
            .overlay(
                RoundedRectangle(cornerRadius: 8)
                    .stroke(Color.fmBorder, lineWidth: 1)
            )

            Menu {
                Button("全部") { selectedCategory = "全部" }
                Button("模板") { selectedCategory = "模板" }
                Button("模型") { selectedCategory = "模型" }
                Button("数据集") { selectedCategory = "数据集" }
                Button("组件") { selectedCategory = "组件" }
                Button("脚本") { selectedCategory = "脚本" }
            } label: {
                HStack(spacing: 6) {
                    Text(selectedCategory)
                        .font(.system(size: 14, weight: .medium))
                    Image(systemName: "chevron.down")
                        .font(.system(size: 12))
                }
                .foregroundColor(.fmTextPrimary)
                .padding(.horizontal, 16)
                .padding(.vertical, 10)
                .background(Color.white)
                .cornerRadius(8)
                .overlay(
                    RoundedRectangle(cornerRadius: 8)
                        .stroke(Color.fmBorder, lineWidth: 1)
                )
            }

            Menu {
                Button("最受欢迎") {}
                Button("最新上传") {}
                Button("下载最多") {}
            } label: {
                HStack(spacing: 6) {
                    Text("排序")
                        .font(.system(size: 14, weight: .medium))
                    Image(systemName: "chevron.down")
                        .font(.system(size: 12))
                }
                .foregroundColor(.fmTextPrimary)
                .padding(.horizontal, 16)
                .padding(.vertical, 10)
                .background(Color.white)
                .cornerRadius(8)
                .overlay(
                    RoundedRectangle(cornerRadius: 8)
                        .stroke(Color.fmBorder, lineWidth: 1)
                )
            }
        }
    }

    // MARK: - Assets Grid Section
    private var assetsGridSection: some View {
        LazyVGrid(
            columns: Array(repeating: GridItem(.flexible(), spacing: 16), count: 3),
            spacing: 16
        ) {
            ForEach(viewModel.assets) { asset in
                AssetCard(asset: asset)
            }
        }
    }
}

// MARK: - Asset Card Component
struct AssetCard: View {
    let asset: AssetItem
    @State private var isHovered = false

    var body: some View {
        VStack(spacing: 0) {
            // 顶部预览区域
            ZStack {
                Rectangle()
                    .fill(asset.color.opacity(0.1))
                    .frame(height: 160)

                Image(systemName: assetIcon)
                    .font(.system(size: 48))
                    .foregroundColor(asset.color)
            }

            // 内容区域
            VStack(alignment: .leading, spacing: 12) {
                // 标题和类型徽章
                HStack(alignment: .top) {
                    Text(asset.name)
                        .font(.system(size: 16, weight: .semibold))
                        .foregroundColor(.fmTextPrimary)
                        .lineLimit(1)

                    Spacer()

                    Text(asset.type)
                        .font(.system(size: 11, weight: .medium))
                        .foregroundColor(.fmInfo)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 3)
                        .background(Color.fmInfo.opacity(0.1))
                        .cornerRadius(10)
                }

                // 描述
                Text(asset.description)
                    .font(.system(size: 13))
                    .foregroundColor(.fmTextSecondary)
                    .lineLimit(2)
                    .frame(height: 36, alignment: .top)

                // 标签
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 6) {
                        ForEach(asset.tags, id: \.self) { tag in
                            Text(tag)
                                .font(.system(size: 11))
                                .foregroundColor(.fmTextSecondary)
                                .padding(.horizontal, 8)
                                .padding(.vertical, 4)
                                .background(Color.fmBgSecondary)
                                .cornerRadius(6)
                        }
                    }
                }

                Divider()

                // 底部信息
                HStack {
                    HStack(spacing: 4) {
                        Image(systemName: "arrow.down.circle.fill")
                            .font(.system(size: 12))
                            .foregroundColor(.fmTextTertiary)
                        Text("\(asset.downloads)")
                            .font(.system(size: 12))
                            .foregroundColor(.fmTextSecondary)
                    }

                    Spacer()

                    HStack(spacing: 4) {
                        Image(systemName: "doc.fill")
                            .font(.system(size: 11))
                            .foregroundColor(.fmTextTertiary)
                        Text(asset.size)
                            .font(.system(size: 11))
                            .foregroundColor(.fmTextTertiary)
                    }

                    Text("·")
                        .foregroundColor(.fmTextTertiary)

                    Text(asset.updated)
                        .font(.system(size: 11))
                        .foregroundColor(.fmTextTertiary)
                }
            }
            .padding(16)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color.white)
        .cornerRadius(12)
        .shadow(
            color: Color.black.opacity(isHovered ? 0.1 : 0.05),
            radius: isHovered ? 8 : 4,
            x: 0,
            y: isHovered ? 4 : 2
        )
        .offset(y: isHovered ? -2 : 0)
        .animation(.easeInOut(duration: 0.2), value: isHovered)
        .onHover { hovering in
            isHovered = hovering
        }
        .onTapGesture {
            // 导航到资产详情
        }
    }

    private var assetIcon: String {
        switch asset.type {
        case "模板": return "doc.text.fill"
        case "模型": return "cpu.fill"
        case "数据集": return "cylinder.fill"
        case "组件": return "square.stack.3d.up.fill"
        case "脚本": return "terminal.fill"
        default: return "cube.fill"
        }
    }
}

// MARK: - Data Models
struct AssetItem: Identifiable {
    let id = UUID()
    let name: String
    let description: String
    let type: String
    let category: String
    let color: Color
    let downloads: Int
    let size: String
    let updated: String
    let tags: [String]
}

// MARK: - Preview
#Preview {
    StandardAssetsView()
}
