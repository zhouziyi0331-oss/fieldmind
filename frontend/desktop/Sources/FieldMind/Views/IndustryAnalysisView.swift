import SwiftUI

struct IndustryAnalysisView: View {
    @State private var analyses: [IndustryAnalysis] = []
    @State private var selectedAnalysis: IndustryAnalysis?
    @State private var showNewAnalysisForm = false
    @State private var isLoading = false

    var body: some View {
        HStack(spacing: 0) {
            // 左侧：分析列表
            analysisListSidebar
                .frame(width: 280)

            // 右侧：新建表单或分析详情
            if let analysis = selectedAnalysis {
                analysisDetailView(analysis: analysis)
            } else {
                if showNewAnalysisForm {
                    newAnalysisFormView
                } else {
                    emptyStateView
                }
            }
        }
        .background(Color.fieldMindBackground)
        .onAppear {
            loadAnalyses()
        }
    }

    // MARK: - 左侧分析列表
    private var analysisListSidebar: some View {
        VStack(spacing: 0) {
            // 标题和新建按钮
            HStack(spacing: 12) {
                Text("业态分析")
                    .font(.system(size: 14, weight: .bold))
                    .foregroundColor(Color.fieldMindText)

                Spacer()

                Button {
                    selectedAnalysis = nil
                    showNewAnalysisForm = true
                } label: {
                    Image(systemName: "plus.circle.fill")
                        .font(.system(size: 18))
                        .foregroundColor(Color.fieldMindPrimary)
                }
                .buttonStyle(PlainButtonStyle())
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 14)
            .background(Color.white)
            .overlay(
                Rectangle()
                    .fill(Color.gray.opacity(0.1))
                    .frame(height: 1),
                alignment: .bottom
            )

            // 分析列表
            if isLoading {
                Spacer()
                ProgressView()
                    .scaleEffect(0.8)
                Spacer()
            } else if analyses.isEmpty {
                Spacer()
                VStack(spacing: 8) {
                    Image(systemName: "chart.line.uptrend.xyaxis")
                        .font(.system(size: 32))
                        .foregroundColor(Color.fieldMindText.opacity(0.3))
                    Text("暂无分析")
                        .font(.system(size: 12))
                        .foregroundColor(Color.fieldMindText.opacity(0.5))
                }
                Spacer()
            } else {
                ScrollView(showsIndicators: false) {
                    VStack(spacing: 8) {
                        ForEach(analyses) { analysis in
                            analysisListItem(analysis: analysis)
                        }
                    }
                    .padding(12)
                }
            }
        }
        .background(Color.white)
        .overlay(
            Rectangle()
                .fill(Color.gray.opacity(0.1))
                .frame(width: 1),
            alignment: .trailing
        )
    }

    private func analysisListItem(analysis: IndustryAnalysis) -> some View {
        Button {
            selectedAnalysis = analysis
            showNewAnalysisForm = false
        } label: {
            VStack(alignment: .leading, spacing: 8) {
                HStack(spacing: 8) {
                    Text(analysis.industryType)
                        .font(.system(size: 10, weight: .medium))
                        .foregroundColor(.white)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(Color.fieldMindSuccess)
                        .cornerRadius(4)

                    Spacer()

                    Text(analysis.status)
                        .font(.system(size: 10))
                        .foregroundColor(analysis.statusColor)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(analysis.statusColor.opacity(0.1))
                        .cornerRadius(4)
                }

                Text(analysis.title)
                    .font(.system(size: 13, weight: .medium))
                    .foregroundColor(Color.fieldMindText)
                    .lineLimit(2)
                    .multilineTextAlignment(.leading)

                HStack(spacing: 12) {
                    Label(analysis.createdAt, systemImage: "clock")
                        .font(.system(size: 10))
                        .foregroundColor(Color.fieldMindText.opacity(0.6))

                    if let region = analysis.region {
                        Label(region, systemImage: "mappin")
                            .font(.system(size: 10))
                            .foregroundColor(Color.fieldMindText.opacity(0.6))
                    }
                }
            }
            .padding(12)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(
                selectedAnalysis?.id == analysis.id ?
                Color.fieldMindPrimary.opacity(0.08) : Color.fieldMindBackground
            )
            .cornerRadius(7)
            .overlay(
                RoundedRectangle(cornerRadius: 7)
                    .stroke(
                        selectedAnalysis?.id == analysis.id ?
                        Color.fieldMindPrimary.opacity(0.3) : Color.clear,
                        lineWidth: 1
                    )
            )
        }
        .buttonStyle(PlainButtonStyle())
    }

    // MARK: - 新建分析表单
    private var newAnalysisFormView: some View {
        NewIndustryAnalysisFormView(
            onCancel: {
                showNewAnalysisForm = false
            },
            onSubmit: { config in
                createAnalysis(config: config)
            }
        )
    }

    // MARK: - 分析详情视图
    private func analysisDetailView(analysis: IndustryAnalysis) -> some View {
        IndustryAnalysisDetailView(
            analysis: analysis,
            onClose: {
                selectedAnalysis = nil
            },
            onDelete: {
                deleteAnalysis(analysis: analysis)
            }
        )
    }

    // MARK: - 空状态视图
    private var emptyStateView: some View {
        VStack(spacing: 20) {
            Image(systemName: "chart.line.uptrend.xyaxis")
                .font(.system(size: 64))
                .foregroundColor(Color.fieldMindText.opacity(0.2))

            Text("选择分析查看详情")
                .font(.system(size: 14))
                .foregroundColor(Color.fieldMindText.opacity(0.6))

            Text("或点击左上角 + 创建新的业态分析")
                .font(.system(size: 12))
                .foregroundColor(Color.fieldMindText.opacity(0.4))
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color.fieldMindBackground)
    }

    // MARK: - 数据加载
    private func loadAnalyses() {
        isLoading = true
        Task {
            do {
                let response = try await APIService.shared.getIndustryCategories()

                await MainActor.run {
                    // 将业态类别转换为分析列表
                    analyses = response.categories.map { category in
                        IndustryAnalysis(
                            id: category.categoryId,
                            title: "\(category.name)产业分析",
                            industryType: category.name,
                            region: nil,
                            status: "已完成",
                            createdAt: formatDate(Date()),
                            marketSize: nil,
                            growthRate: nil,
                            competitionLevel: nil,
                            opportunities: nil,
                            threats: nil
                        )
                    }
                    isLoading = false
                }
            } catch {
                print("Error loading industry categories: \(error)")
                await MainActor.run {
                    // 失败时使用最小fallback数据
                    loadAnalysesFallback()
                    isLoading = false
                }
            }
        }
    }

    private func loadAnalysesFallback() {
        // 最小fallback数据 - 仅在API完全失败时使用
        analyses = [
            IndustryAnalysis(
                id: "fallback-1",
                title: "传统农业产业分析",
                industryType: "传统农业",
                region: nil,
                status: "等待数据",
                createdAt: formatDate(Date()),
                marketSize: nil,
                growthRate: nil,
                competitionLevel: nil,
                opportunities: nil,
                threats: nil
            )
        ]
    }

    private func formatDate(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd"
        return formatter.string(from: date)
    }

    private func createAnalysis(config: IndustryAnalysisConfig) {
        // TODO: 调用后端API /api/v1/industry/
        print("Creating analysis with config: \(config)")
        showNewAnalysisForm = false
    }

    private func deleteAnalysis(analysis: IndustryAnalysis) {
        // TODO: 调用后端API DELETE /api/v1/industry/{id}
        analyses.removeAll { $0.id == analysis.id }
        selectedAnalysis = nil
    }
}

// MARK: - 数据模型
struct IndustryAnalysis: Identifiable {
    let id: String
    let title: String
    let industryType: String
    let region: String?
    let status: String // 分析中, 已完成, 失败
    let createdAt: String
    let marketSize: String?
    let growthRate: String?
    let competitionLevel: String?
    let opportunities: [String]?
    let threats: [String]?

    // 从API加载的详细数据
    var detailData: IndustryDetailResponse?
    var isDetailLoaded: Bool = false

    var statusColor: Color {
        switch status {
        case "已完成": return Color.fieldMindSuccess
        case "分析中": return Color.fieldMindPrimary
        case "失败": return Color.fieldMindDanger
        default: return Color.fieldMindText.opacity(0.6)
        }
    }
}

// MARK: - 新建分析表单
struct NewIndustryAnalysisFormView: View {
    let onCancel: () -> Void
    let onSubmit: (IndustryAnalysisConfig) -> Void

    @State private var industryType = "文化旅游"
    @State private var region = ""
    @State private var targetMarket = ""
    @State private var analysisDimensions: [String] = ["市场规模", "竞争格局", "发展趋势"]
    @State private var includeCompetitors = true
    @State private var includePolicies = true

    let availableIndustryTypes = [
        "文化旅游", "特色农业", "手工艺品", "民宿经济", "文创产业", "生态农业"
    ]

    let availableDimensions = [
        "市场规模", "竞争格局", "发展趋势", "机会识别",
        "政策环境", "技术趋势", "消费者洞察"
    ]

    var body: some View {
        ScrollView(showsIndicators: false) {
            VStack(alignment: .leading, spacing: 24) {
                // 标题
                HStack {
                    Text("新建业态分析")
                        .font(.system(size: 16, weight: .bold))
                        .foregroundColor(Color.fieldMindText)

                    Spacer()

                    Button("取消") {
                        onCancel()
                    }
                    .font(.system(size: 12))
                    .foregroundColor(Color.fieldMindText.opacity(0.6))
                }

                // 行业类型选择
                VStack(alignment: .leading, spacing: 12) {
                    Text("行业类型")
                        .font(.system(size: 12, weight: .semibold))
                        .foregroundColor(Color.fieldMindText)

                    FlowLayout(spacing: 8) {
                        ForEach(availableIndustryTypes, id: \.self) { type in
                            industryTypeChip(type: type)
                        }
                    }
                }

                Divider()

                // 地区设置
                VStack(alignment: .leading, spacing: 12) {
                    Text("目标地区")
                        .font(.system(size: 12, weight: .semibold))
                        .foregroundColor(Color.fieldMindText)

                    TextField("例如：贵州、云南、四川", text: $region)
                        .textFieldStyle(CustomTextFieldStyle())
                }

                // 目标市场
                VStack(alignment: .leading, spacing: 12) {
                    Text("目标市场")
                        .font(.system(size: 12, weight: .semibold))
                        .foregroundColor(Color.fieldMindText)

                    TextField("例如：都市中产、文化爱好者", text: $targetMarket)
                        .textFieldStyle(CustomTextFieldStyle())
                }

                Divider()

                // 分析维度
                VStack(alignment: .leading, spacing: 12) {
                    Text("分析维度")
                        .font(.system(size: 12, weight: .semibold))
                        .foregroundColor(Color.fieldMindText)

                    Text("选择需要分析的维度")
                        .font(.system(size: 11))
                        .foregroundColor(Color.fieldMindText.opacity(0.6))

                    FlowLayout(spacing: 8) {
                        ForEach(availableDimensions, id: \.self) { dimension in
                            dimensionChip(dimension: dimension)
                        }
                    }
                }

                Divider()

                // 附加选项
                VStack(alignment: .leading, spacing: 12) {
                    Text("附加选项")
                        .font(.system(size: 12, weight: .semibold))
                        .foregroundColor(Color.fieldMindText)

                    Toggle("包含竞品分析", isOn: $includeCompetitors)
                        .font(.system(size: 12))
                        .toggleStyle(SwitchToggleStyle(tint: Color.fieldMindPrimary))

                    Toggle("包含政策解读", isOn: $includePolicies)
                        .font(.system(size: 12))
                        .toggleStyle(SwitchToggleStyle(tint: Color.fieldMindPrimary))
                }

                // 生成按钮
                Button {
                    let config = IndustryAnalysisConfig(
                        industryType: industryType,
                        region: region,
                        targetMarket: targetMarket,
                        dimensions: analysisDimensions,
                        includeCompetitors: includeCompetitors,
                        includePolicies: includePolicies
                    )
                    onSubmit(config)
                } label: {
                    HStack(spacing: 8) {
                        Image(systemName: "chart.line.uptrend.xyaxis")
                            .font(.system(size: 12))
                        Text("开始分析")
                            .font(.system(size: 13, weight: .medium))
                    }
                    .foregroundColor(.white)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 12)
                    .background(Color.fieldMindPrimary)
                    .cornerRadius(7)
                }
                .buttonStyle(PlainButtonStyle())
            }
            .padding(24)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color.fieldMindBackground)
    }

    private func industryTypeChip(type: String) -> some View {
        Button {
            industryType = type
        } label: {
            Text(type)
                .font(.system(size: 11))
                .foregroundColor(
                    industryType == type ?
                    .white : Color.fieldMindText
                )
                .padding(.horizontal, 12)
                .padding(.vertical, 6)
                .background(
                    industryType == type ?
                    Color.fieldMindSuccess : Color.white
                )
                .cornerRadius(5)
                .overlay(
                    RoundedRectangle(cornerRadius: 5)
                        .stroke(
                            industryType == type ?
                            Color.clear : Color.gray.opacity(0.2),
                            lineWidth: 1
                        )
                )
        }
        .buttonStyle(PlainButtonStyle())
    }

    private func dimensionChip(dimension: String) -> some View {
        Button {
            if analysisDimensions.contains(dimension) {
                analysisDimensions.removeAll { $0 == dimension }
            } else {
                analysisDimensions.append(dimension)
            }
        } label: {
            HStack(spacing: 6) {
                if analysisDimensions.contains(dimension) {
                    Image(systemName: "checkmark")
                        .font(.system(size: 9))
                }
                Text(dimension)
                    .font(.system(size: 11))
            }
            .foregroundColor(
                analysisDimensions.contains(dimension) ?
                .white : Color.fieldMindText
            )
            .padding(.horizontal, 12)
            .padding(.vertical, 6)
            .background(
                analysisDimensions.contains(dimension) ?
                Color.fieldMindPrimary : Color.white
            )
            .cornerRadius(5)
            .overlay(
                RoundedRectangle(cornerRadius: 5)
                    .stroke(
                        analysisDimensions.contains(dimension) ?
                        Color.clear : Color.gray.opacity(0.2),
                        lineWidth: 1
                    )
            )
        }
        .buttonStyle(PlainButtonStyle())
    }
}

// MARK: - 分析详情视图
struct IndustryAnalysisDetailView: View {
    let analysis: IndustryAnalysis
    let onClose: () -> Void
    let onDelete: () -> Void

    @State private var detailData: IndustryDetailResponse?
    @State private var isLoadingDetail = false

    var body: some View {
        ScrollView(showsIndicators: false) {
            VStack(alignment: .leading, spacing: 24) {
                // 顶部操作栏
                HStack {
                    Button {
                        onClose()
                    } label: {
                        HStack(spacing: 6) {
                            Image(systemName: "chevron.left")
                                .font(.system(size: 11))
                            Text("返回列表")
                                .font(.system(size: 12))
                        }
                        .foregroundColor(Color.fieldMindText.opacity(0.6))
                    }
                    .buttonStyle(PlainButtonStyle())

                    Spacer()

                    HStack(spacing: 12) {
                        Button {
                            // 导出
                        } label: {
                            HStack(spacing: 6) {
                                Image(systemName: "square.and.arrow.down")
                                    .font(.system(size: 11))
                                Text("导出")
                                    .font(.system(size: 12))
                            }
                            .foregroundColor(.white)
                            .padding(.horizontal, 12)
                            .padding(.vertical, 7)
                            .background(Color.fieldMindPrimary)
                            .cornerRadius(6)
                        }
                        .buttonStyle(PlainButtonStyle())

                        Menu {
                            Button("删除分析") {
                                onDelete()
                            }
                        } label: {
                            Image(systemName: "ellipsis")
                                .font(.system(size: 14))
                                .foregroundColor(Color.fieldMindText.opacity(0.6))
                                .frame(width: 32, height: 32)
                                .background(Color.fieldMindBackground)
                                .cornerRadius(6)
                        }
                        .menuStyle(BorderlessButtonMenuStyle())
                    }
                }

                // 分析标题卡片
                VStack(alignment: .leading, spacing: 16) {
                    HStack(spacing: 10) {
                        Text(analysis.industryType)
                            .font(.system(size: 11, weight: .medium))
                            .foregroundColor(.white)
                            .padding(.horizontal, 10)
                            .padding(.vertical, 5)
                            .background(Color.fieldMindSuccess)
                            .cornerRadius(5)

                        Text(analysis.status)
                            .font(.system(size: 11))
                            .foregroundColor(analysis.statusColor)
                            .padding(.horizontal, 10)
                            .padding(.vertical, 5)
                            .background(analysis.statusColor.opacity(0.1))
                            .cornerRadius(5)
                    }

                    Text(analysis.title)
                        .font(.system(size: 18, weight: .bold))
                        .foregroundColor(Color.fieldMindText)

                    HStack(spacing: 20) {
                        Label(analysis.createdAt, systemImage: "calendar")
                            .font(.system(size: 11))
                            .foregroundColor(Color.fieldMindText.opacity(0.6))

                        if let region = analysis.region {
                            Label(region, systemImage: "mappin")
                                .font(.system(size: 11))
                                .foregroundColor(Color.fieldMindText.opacity(0.6))
                        }
                    }
                }
                .padding(20)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(Color.white)
                .cornerRadius(10)

                // 动态加载的详细内容
                if isLoadingDetail {
                    VStack {
                        ProgressView()
                            .scaleEffect(0.8)
                        Text("加载详细数据中...")
                            .font(.system(size: 12))
                            .foregroundColor(Color.fieldMindText.opacity(0.6))
                    }
                    .frame(maxWidth: .infinity)
                    .padding(40)
                } else if let detail = detailData {
                    // 概览
                    VStack(alignment: .leading, spacing: 16) {
                        Text("概览")
                            .font(.system(size: 14, weight: .bold))
                            .foregroundColor(Color.fieldMindText)

                        Text(detail.overview.summary)
                            .font(.system(size: 12))
                            .foregroundColor(Color.fieldMindText.opacity(0.8))
                            .lineSpacing(4)

                        HStack(spacing: 8) {
                            Image(systemName: "doc.text")
                                .font(.system(size: 11))
                                .foregroundColor(Color.fieldMindPrimary)
                            Text("分析了 \(detail.overview.documentCount) 份文档")
                                .font(.system(size: 11))
                                .foregroundColor(Color.fieldMindText.opacity(0.6))
                        }

                        if !detail.overview.keyFindings.isEmpty {
                            VStack(alignment: .leading, spacing: 8) {
                                Text("关键发现")
                                    .font(.system(size: 12, weight: .semibold))
                                    .foregroundColor(Color.fieldMindText)

                                ForEach(detail.overview.keyFindings, id: \.self) { finding in
                                    HStack(alignment: .top, spacing: 8) {
                                        Circle()
                                            .fill(Color.fieldMindPrimary)
                                            .frame(width: 5, height: 5)
                                            .padding(.top, 5)

                                        Text(finding)
                                            .font(.system(size: 11))
                                            .foregroundColor(Color.fieldMindText.opacity(0.7))
                                    }
                                }
                            }
                        }
                    }
                    .padding(20)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .background(Color.white)
                    .cornerRadius(10)

                    // 详细分析
                    VStack(alignment: .leading, spacing: 16) {
                        Text("详细分析")
                            .font(.system(size: 14, weight: .bold))
                            .foregroundColor(Color.fieldMindText)

                        Text(detail.detailedAnalysis.currentStatus)
                            .font(.system(size: 12))
                            .foregroundColor(Color.fieldMindText.opacity(0.8))
                            .lineSpacing(4)

                        // 趋势、挑战、机遇
                        VStack(alignment: .leading, spacing: 16) {
                            // 趋势
                            if !detail.detailedAnalysis.trends.isEmpty {
                                VStack(alignment: .leading, spacing: 10) {
                                    HStack(spacing: 8) {
                                        Image(systemName: "chart.line.uptrend.xyaxis")
                                            .font(.system(size: 13))
                                            .foregroundColor(Color.fieldMindPrimary)
                                        Text("发展趋势")
                                            .font(.system(size: 12, weight: .semibold))
                                            .foregroundColor(Color.fieldMindText)
                                    }

                                    ForEach(detail.detailedAnalysis.trends, id: \.self) { trend in
                                        HStack(alignment: .top, spacing: 8) {
                                            Text("•")
                                                .foregroundColor(Color.fieldMindPrimary)
                                            Text(trend)
                                                .font(.system(size: 11))
                                                .foregroundColor(Color.fieldMindText.opacity(0.7))
                                        }
                                    }
                                }
                            }

                            // 挑战
                            if !detail.detailedAnalysis.challenges.isEmpty {
                                VStack(alignment: .leading, spacing: 10) {
                                    HStack(spacing: 8) {
                                        Image(systemName: "exclamationmark.triangle")
                                            .font(.system(size: 13))
                                            .foregroundColor(Color(hex: "ED8936"))
                                        Text("面临挑战")
                                            .font(.system(size: 12, weight: .semibold))
                                            .foregroundColor(Color.fieldMindText)
                                    }

                                    ForEach(detail.detailedAnalysis.challenges, id: \.self) { challenge in
                                        HStack(alignment: .top, spacing: 8) {
                                            Text("•")
                                                .foregroundColor(Color(hex: "ED8936"))
                                            Text(challenge)
                                                .font(.system(size: 11))
                                                .foregroundColor(Color.fieldMindText.opacity(0.7))
                                        }
                                    }
                                }
                            }

                            // 机遇
                            if !detail.detailedAnalysis.opportunities.isEmpty {
                                VStack(alignment: .leading, spacing: 10) {
                                    HStack(spacing: 8) {
                                        Image(systemName: "arrow.up.circle")
                                            .font(.system(size: 13))
                                            .foregroundColor(Color.fieldMindSuccess)
                                        Text("发展机遇")
                                            .font(.system(size: 12, weight: .semibold))
                                            .foregroundColor(Color.fieldMindText)
                                    }

                                    ForEach(detail.detailedAnalysis.opportunities, id: \.self) { opportunity in
                                        HStack(alignment: .top, spacing: 8) {
                                            Text("•")
                                                .foregroundColor(Color.fieldMindSuccess)
                                            Text(opportunity)
                                                .font(.system(size: 11))
                                                .foregroundColor(Color.fieldMindText.opacity(0.7))
                                        }
                                    }
                                }
                            }
                        }
                    }
                    .padding(20)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .background(Color.white)
                    .cornerRadius(10)

                    // 相关实体
                    if !detail.relatedEntities.isEmpty {
                        VStack(alignment: .leading, spacing: 16) {
                            Text("相关实体")
                                .font(.system(size: 14, weight: .bold))
                                .foregroundColor(Color.fieldMindText)

                            LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible()), GridItem(.flexible())], spacing: 12) {
                                ForEach(detail.relatedEntities, id: \.name) { entity in
                                    HStack {
                                        VStack(alignment: .leading, spacing: 4) {
                                            Text(entity.name)
                                                .font(.system(size: 11, weight: .medium))
                                                .foregroundColor(Color.fieldMindText)
                                            Text("\(entity.type) · \(entity.count)次")
                                                .font(.system(size: 10))
                                                .foregroundColor(Color.fieldMindText.opacity(0.5))
                                        }
                                        Spacer()
                                    }
                                    .padding(10)
                                    .background(Color.fieldMindBackground)
                                    .cornerRadius(6)
                                }
                            }
                        }
                        .padding(20)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .background(Color.white)
                        .cornerRadius(10)
                    }

                    // 相关文档
                    if !detail.documents.isEmpty && detail.documents.first?.id != "none" {
                        VStack(alignment: .leading, spacing: 16) {
                            Text("相关文档")
                                .font(.system(size: 14, weight: .bold))
                                .foregroundColor(Color.fieldMindText)

                            VStack(spacing: 8) {
                                ForEach(detail.documents, id: \.id) { doc in
                                    HStack {
                                        Image(systemName: "doc.text")
                                            .font(.system(size: 12))
                                            .foregroundColor(Color.fieldMindPrimary)

                                        Text(doc.title)
                                            .font(.system(size: 11))
                                            .foregroundColor(Color.fieldMindText)

                                        Spacer()

                                        Text(String(format: "%.0f%%", doc.relevanceScore * 100))
                                            .font(.system(size: 10))
                                            .foregroundColor(Color.fieldMindText.opacity(0.5))
                                    }
                                    .padding(10)
                                    .background(Color.fieldMindBackground)
                                    .cornerRadius(6)
                                }
                            }
                        }
                        .padding(20)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .background(Color.white)
                        .cornerRadius(10)
                    }
                } else {
                    VStack(spacing: 12) {
                        Image(systemName: "doc.text.magnifyingglass")
                            .font(.system(size: 40))
                            .foregroundColor(Color.fieldMindText.opacity(0.3))
                        Text("暂无详细数据")
                            .font(.system(size: 13))
                            .foregroundColor(Color.fieldMindText.opacity(0.6))
                    }
                    .frame(maxWidth: .infinity)
                    .padding(40)
                }
            }
            .padding(24)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color.fieldMindBackground)
        .onAppear {
            loadDetailData()
        }
    }

    private func loadDetailData() {
        isLoadingDetail = true
        Task {
            do {
                let detail = try await APIService.shared.getIndustryDetails(category: analysis.id)
                await MainActor.run {
                    detailData = detail
                    isLoadingDetail = false
                }
            } catch {
                print("Error loading industry details: \(error)")
                await MainActor.run {
                    isLoadingDetail = false
                }
            }
        }
    }
}

// MARK: - 配置模型
struct IndustryAnalysisConfig {
    let industryType: String
    let region: String
    let targetMarket: String
    let dimensions: [String]
    let includeCompetitors: Bool
    let includePolicies: Bool
}
