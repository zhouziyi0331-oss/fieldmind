import SwiftUI
import Charts

struct ModelPage: View {
    @StateObject private var viewModel = ModelConfigViewModel()
    @State private var searchText = ""
    @State private var selectedProvider = "全部"
    @State private var showConfiguredOnly = false
    @State private var selectedTab = "models"  // "models", "configs", "usage"

    let providers = ["全部", "OpenAI", "Anthropic", "Google", "Local"]

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            headerView
            Divider()

            if let errorMessage = viewModel.errorMessage {
                errorBanner(errorMessage)
            } else if let successMessage = viewModel.successMessage {
                successBanner(successMessage)
            }

            // Tab Bar
            HStack(spacing: 0) {
                ModelTabButton(title: "模型列表", icon: "brain", isSelected: selectedTab == "models") {
                    selectedTab = "models"
                }
                ModelTabButton(title: "参数配置", icon: "slider.horizontal.3", isSelected: selectedTab == "configs") {
                    selectedTab = "configs"
                }
                ModelTabButton(title: "使用统计", icon: "chart.bar.fill", isSelected: selectedTab == "usage") {
                    selectedTab = "usage"
                }
                Spacer()
            }
            .padding(.horizontal, 24)
            .padding(.top, 12)
            .background(Color.fmBg)

            Divider()

            // Content
            if selectedTab == "models" {
                modelsTabView
            } else if selectedTab == "configs" {
                configsTabView
            } else {
                usageTabView
            }
        }
        .task {
            await loadInitialData()
        }
    }

    // MARK: - Header

    private var headerView: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text("AI 模型管理")
                    .font(.system(size: 24, weight: .semibold))
                    .foregroundColor(Color.fmText)

                if let activeModel = viewModel.activeModel {
                    Text("当前活跃: \(activeModel.name)")
                        .font(.system(size: 14))
                        .foregroundColor(Color.fmText3)
                }
            }

            Spacer()

            if viewModel.isLoadingModels || viewModel.isLoadingConfigs || viewModel.isLoadingUsage {
                ProgressView()
                    .scaleEffect(0.8)
            }
        }
        .padding(.horizontal, 24)
        .padding(.vertical, 20)
        .background(Color.fmBg)
    }

    // MARK: - Models Tab

    private var modelsTabView: some View {
        VStack(spacing: 0) {
            // Filter bar
            HStack(spacing: 12) {
                // Search
                HStack(spacing: 8) {
                    Image(systemName: "magnifyingglass")
                        .foregroundColor(Color.fmText3)
                        .font(.system(size: 14))
                    TextField("搜索模型名称...", text: $searchText)
                        .textFieldStyle(PlainTextFieldStyle())
                        .font(.system(size: 14))
                }
                .padding(.horizontal, 12)
                .padding(.vertical, 8)
                .background(Color.white)
                .cornerRadius(6)
                .frame(width: 300)

                // Provider filter
                Menu {
                    ForEach(providers, id: \.self) { provider in
                        Button(provider) {
                            selectedProvider = provider
                            Task {
                                await viewModel.loadModels(
                                    provider: provider == "全部" ? nil : provider,
                                    configuredOnly: showConfiguredOnly
                                )
                            }
                        }
                    }
                } label: {
                    HStack(spacing: 6) {
                        Text(selectedProvider)
                            .font(.system(size: 14))
                        Image(systemName: "chevron.down")
                            .font(.system(size: 12))
                    }
                    .foregroundColor(Color.fmText2)
                    .padding(.horizontal, 12)
                    .padding(.vertical, 8)
                    .background(Color.white)
                    .cornerRadius(6)
                }
                .menuStyle(BorderlessButtonMenuStyle())

                // Configured only toggle
                Toggle("仅显示已配置", isOn: $showConfiguredOnly)
                    .font(.system(size: 14))
                    .onChange(of: showConfiguredOnly) { oldValue, newValue in
                        Task {
                            await viewModel.loadModels(
                                provider: selectedProvider == "全部" ? nil : selectedProvider,
                                configuredOnly: showConfiguredOnly
                            )
                        }
                    }

                Spacer()
            }
            .padding(.horizontal, 24)
            .padding(.vertical, 16)
            .background(Color.fmBg)

            Divider()

            // Model list
            if viewModel.isLoadingModels {
                loadingView
            } else if !viewModel.hasModels {
                emptyStateView(icon: "brain", message: "暂无模型数据")
            } else {
                ScrollView {
                    LazyVStack(spacing: 12) {
                        let filtered = viewModel.filterModels(searchText: searchText, provider: selectedProvider)
                        ForEach(filtered) { model in
                            // Use custom card inline since types don't match
                            HStack(spacing: 16) {
                                Image(systemName: providerIcon(model.provider))
                                    .font(.system(size: 24))
                                    .foregroundColor(Color.blue)
                                    .frame(width: 56, height: 56)
                                    .background(Color.blue.opacity(0.1))
                                    .cornerRadius(12)

                                VStack(alignment: .leading, spacing: 6) {
                                    HStack(spacing: 8) {
                                        Text(model.name)
                                            .font(.system(size: 16, weight: .semibold))
                                            .foregroundColor(Color.fmText)

                                        if model.isActive {
                                            Text("活跃")
                                                .font(.system(size: 11, weight: .medium))
                                                .foregroundColor(.white)
                                                .padding(.horizontal, 8)
                                                .padding(.vertical, 3)
                                                .background(Color.green)
                                                .cornerRadius(4)
                                        }

                                        if model.isConfigured {
                                            Image(systemName: "checkmark.circle.fill")
                                                .font(.system(size: 14))
                                                .foregroundColor(Color.green)
                                        }
                                    }

                                    Text(model.description)
                                        .font(.system(size: 13))
                                        .foregroundColor(Color.fmText2)
                                        .lineLimit(2)
                                }

                                Spacer()

                                Button("配置") {}
                                    .buttonStyle(.bordered)
                            }
                            .padding(16)
                            .background(Color.white)
                            .cornerRadius(12)
                            .overlay(RoundedRectangle(cornerRadius: 12).stroke(Color.fmBorder, lineWidth: 1))
                        }
                    }
                    .padding(24)
                }
                .background(Color.fmBg)
            }
        }
    }

    // MARK: - Configs Tab

    private var configsTabView: some View {
        VStack {
            if viewModel.isLoadingConfigs {
                loadingView
            } else if !viewModel.hasConfigs {
                emptyStateView(icon: "slider.horizontal.3", message: "暂无配置数据")
            } else {
                ScrollView {
                    LazyVStack(spacing: 12) {
                        ForEach(viewModel.configs) { config in
                            // Use custom card inline since types don't match
                            VStack(alignment: .leading, spacing: 12) {
                                HStack {
                                    Text(config.name)
                                        .font(.system(size: 15, weight: .semibold))
                                        .foregroundColor(Color.fmText)

                                    if config.isDefault {
                                        Text("默认")
                                            .font(.system(size: 11, weight: .medium))
                                            .foregroundColor(.white)
                                            .padding(.horizontal, 8)
                                            .padding(.vertical, 3)
                                            .background(Color.blue)
                                            .cornerRadius(4)
                                    }

                                    Spacer()
                                }

                                HStack(spacing: 20) {
                                    VStack(alignment: .leading, spacing: 4) {
                                        Text("Temperature")
                                            .font(.system(size: 11))
                                            .foregroundColor(Color.fmText3)
                                        Text(String(format: "%.2f", config.temperature))
                                            .font(.system(size: 14, weight: .medium))
                                            .foregroundColor(Color.fmText)
                                    }

                                    VStack(alignment: .leading, spacing: 4) {
                                        Text("Top P")
                                            .font(.system(size: 11))
                                            .foregroundColor(Color.fmText3)
                                        Text(String(format: "%.2f", config.topP))
                                            .font(.system(size: 14, weight: .medium))
                                            .foregroundColor(Color.fmText)
                                    }

                                    VStack(alignment: .leading, spacing: 4) {
                                        Text("Max Tokens")
                                            .font(.system(size: 11))
                                            .foregroundColor(Color.fmText3)
                                        Text("\(config.maxTokens)")
                                            .font(.system(size: 14, weight: .medium))
                                            .foregroundColor(Color.fmText)
                                    }
                                }
                            }
                            .padding(16)
                            .background(Color.white)
                            .cornerRadius(12)
                            .overlay(RoundedRectangle(cornerRadius: 12).stroke(Color.fmBorder, lineWidth: 1))
                        }
                    }
                    .padding(24)
                }
                .background(Color.fmBg)
            }
        }
    }

    // MARK: - Usage Tab

    private var usageTabView: some View {
        VStack(spacing: 0) {
            // Stats cards
            if viewModel.hasUsageStats {
                HStack(spacing: 16) {
                    statCard(
                        title: "总调用次数",
                        value: "\(viewModel.totalCalls)",
                        icon: "arrow.triangle.2.circlepath",
                        color: "3B82F6"
                    )

                    statCard(
                        title: "总花费",
                        value: String(format: "$%.2f", viewModel.totalCost),
                        icon: "dollarsign.circle.fill",
                        color: "10B981"
                    )

                    statCard(
                        title: "平均成本",
                        value: viewModel.totalCalls > 0 ? String(format: "$%.4f", viewModel.totalCost / Double(viewModel.totalCalls)) : "$0",
                        icon: "chart.line.uptrend.xyaxis",
                        color: "8B5CF6"
                    )
                }
                .padding(24)
                .background(Color.fmBg)
            }

            Divider()

            // Usage list
            if viewModel.isLoadingUsage {
                loadingView
            } else if !viewModel.hasUsageStats {
                emptyStateView(icon: "chart.bar.fill", message: "暂无使用统计")
            } else {
                ScrollView {
                    LazyVStack(spacing: 12) {
                        ForEach(viewModel.usageStats) { usage in
                            // Inline usage card
                            HStack(spacing: 16) {
                                VStack(alignment: .leading, spacing: 6) {
                                    Text(formatDate(usage.date))
                                        .font(.system(size: 14, weight: .medium))
                                        .foregroundColor(Color.fmText)

                                    HStack(spacing: 12) {
                                        Label("\(usage.callCount) 次调用", systemImage: "arrow.triangle.2.circlepath")
                                            .font(.system(size: 12))
                                            .foregroundColor(Color.fmText3)

                                        Label("\(usage.totalTokens) tokens", systemImage: "doc.text")
                                            .font(.system(size: 12))
                                            .foregroundColor(Color.fmText3)
                                    }
                                }

                                Spacer()

                                VStack(alignment: .trailing, spacing: 4) {
                                    Text(String(format: "$%.2f", usage.cost))
                                        .font(.system(size: 18, weight: .semibold))
                                        .foregroundColor(Color.fmText)

                                    Text(String(format: "%.0fms 平均", usage.avgLatency))
                                        .font(.system(size: 11))
                                        .foregroundColor(Color.fmText3)
                                }
                            }
                            .padding(16)
                            .background(Color.white)
                            .cornerRadius(12)
                            .overlay(RoundedRectangle(cornerRadius: 12).stroke(Color.fmBorder, lineWidth: 1))
                        }
                    }
                    .padding(24)
                }
                .background(Color.fmBg)
            }
        }
    }

    // MARK: - Helper Views

    private func statCard(title: String, value: String, icon: String, color: String) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: icon)
                    .font(.system(size: 20))
                    .foregroundColor(Color(hex: color))
                    .frame(width: 40, height: 40)
                    .background(Color(hex: color).opacity(0.1))
                    .cornerRadius(8)

                Spacer()
            }

            Text(value)
                .font(.system(size: 24, weight: .bold))
                .foregroundColor(Color.fmText)

            Text(title)
                .font(.system(size: 13))
                .foregroundColor(Color.fmText2)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(20)
        .background(Color.white)
        .cornerRadius(12)
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(Color.fmBorder, lineWidth: 1)
        )
    }

    private var loadingView: some View {
        VStack(spacing: 16) {
            ProgressView()
                .scaleEffect(1.2)
            Text("加载中...")
                .font(.system(size: 14))
                .foregroundColor(Color.fmText3)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color.fmBg)
    }

    private func emptyStateView(icon: String, message: String) -> some View {
        VStack(spacing: 16) {
            Image(systemName: icon)
                .font(.system(size: 48))
                .foregroundColor(Color.fmText3)

            Text(message)
                .font(.system(size: 16, weight: .medium))
                .foregroundColor(Color.fmText2)

            Button(action: {
                Task {
                    await loadInitialData()
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

    private func successBanner(_ message: String) -> some View {
        HStack(spacing: 12) {
            Image(systemName: "checkmark.circle.fill")
                .font(.system(size: 16))
                .foregroundColor(.green)

            Text(message)
                .font(.system(size: 14))
                .foregroundColor(Color.fmText)

            Spacer()

            Button(action: {
                viewModel.successMessage = nil
            }) {
                Image(systemName: "xmark.circle.fill")
                    .font(.system(size: 16))
                    .foregroundColor(Color.fmText3)
            }
            .buttonStyle(PlainButtonStyle())
        }
        .padding(16)
        .background(Color.green.opacity(0.1))
    }

    // MARK: - Data Loading

    private func loadInitialData() async {
        await viewModel.loadModels(provider: nil, configuredOnly: false)
        await viewModel.loadConfigs()
        await viewModel.loadUsageStats()
    }

    private func providerIcon(_ provider: String) -> String {
        switch provider.lowercased() {
        case "openai": return "brain.head.profile"
        case "anthropic": return "sparkles"
        case "google": return "globe"
        case "local": return "server.rack"
        default: return "cpu"
        }
    }

    private func formatDate(_ dateString: String) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd"
        if let date = formatter.date(from: dateString) {
            formatter.dateFormat = "M月d日"
            return formatter.string(from: date)
        }
        return dateString
    }
}


// MARK: - Usage Card

struct UsageCard: View {
    let usage: ModelConfigService.ModelUsage

    var body: some View {
        HStack(spacing: 16) {
            VStack(alignment: .leading, spacing: 6) {
                Text(formatDate(usage.date))
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(Color.fmText)

                HStack(spacing: 12) {
                    Label("\(usage.callCount) 次调用", systemImage: "arrow.triangle.2.circlepath")
                        .font(.system(size: 12))
                        .foregroundColor(Color.fmText3)

                    Label("\(usage.totalTokens) tokens", systemImage: "doc.text")
                        .font(.system(size: 12))
                        .foregroundColor(Color.fmText3)
                }
            }

            Spacer()

            VStack(alignment: .trailing, spacing: 4) {
                Text(String(format: "$%.2f", usage.cost))
                    .font(.system(size: 18, weight: .semibold))
                    .foregroundColor(Color.fmText)

                Text(String(format: "%.0fms 平均", usage.avgLatency))
                    .font(.system(size: 11))
                    .foregroundColor(Color.fmText3)
            }
        }
        .padding(16)
        .background(Color.white)
        .cornerRadius(12)
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(Color.fmBorder, lineWidth: 1)
        )
    }

    private func formatDate(_ dateString: String) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd"
        if let date = formatter.date(from: dateString) {
            formatter.dateFormat = "M月d日"
            return formatter.string(from: date)
        }
        return dateString
    }
}

// MARK: - Tab Button

struct ModelTabButton: View {
    let title: String
    let icon: String
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: 6) {
                Image(systemName: icon)
                    .font(.system(size: 14))
                Text(title)
                    .font(.system(size: 14, weight: isSelected ? .semibold : .regular))
            }
            .foregroundColor(isSelected ? Color.blue : Color.fmText2)
            .padding(.horizontal, 16)
            .padding(.vertical, 10)
            .background(isSelected ? Color.blue.opacity(0.1) : Color.clear)
            .cornerRadius(8)
        }
        .buttonStyle(PlainButtonStyle())
    }
}
