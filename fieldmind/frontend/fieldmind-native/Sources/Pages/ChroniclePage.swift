import SwiftUI

struct ChroniclePage: View {
    let projectId: Int
    @StateObject private var viewModel = ChronicleViewModel()
    @State private var searchText = ""
    @State private var selectedCategory = "全部分类"
    @State private var selectedTimeRange = "全部时间"
    @State private var viewMode = "timeline"  // "timeline" or "cards"
    @State private var showLegend = true

    let categories = ["全部分类", "文化活动", "调研记录", "政策变化", "技艺传承", "经济变迁", "环境变化"]
    let timeRanges = ["全部时间", "近一年", "近三年", "近五年", "近十年"]

    var body: some View {
        VStack(spacing: 0) {
            toolbar
            Divider()

            if let errorMessage = viewModel.errorMessage {
                errorBanner(errorMessage)
            }

            if viewMode == "timeline" {
                timelineView
            } else {
                cardsView
            }
        }
        .background(Color.fmBg)
        .task {
            await viewModel.loadAllData(projectId: projectId)
        }
    }

    // MARK: - Toolbar

    private var toolbar: some View {
        HStack(spacing: 16) {
            // Search
            HStack(spacing: 8) {
                Image(systemName: "magnifyingglass")
                    .foregroundColor(Color.fmText3)
                    .font(.system(size: 14))

                TextField("搜索事件...", text: $searchText)
                    .textFieldStyle(PlainTextFieldStyle())
                    .font(.system(size: 13))

                if !searchText.isEmpty {
                    Button(action: { searchText = "" }) {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundColor(Color.fmText3)
                            .font(.system(size: 12))
                    }
                    .buttonStyle(PlainButtonStyle())
                }
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 6)
            .background(Color.white)
            .cornerRadius(6)
            .frame(width: 280)

            // Category Filter
            Menu {
                ForEach(categories, id: \.self) { category in
                    Button(action: {
                        selectedCategory = category
                        Task {
                            await viewModel.applyFilters(
                                projectId: projectId,
                                searchText: nil,
                                startDate: nil,
                                endDate: nil,
                                category: category == "全部分类" ? nil : category
                            )
                        }
                    }) {
                        HStack {
                            Text(category)
                            if selectedCategory == category {
                                Image(systemName: "checkmark")
                            }
                        }
                    }
                }
            } label: {
                HStack(spacing: 6) {
                    Image(systemName: "tag")
                        .font(.system(size: 12))
                    Text(selectedCategory)
                        .font(.system(size: 13))
                    Image(systemName: "chevron.down")
                        .font(.system(size: 10))
                }
                .foregroundColor(Color.fmText2)
                .padding(.horizontal, 12)
                .padding(.vertical, 6)
                .background(Color.white)
                .cornerRadius(6)
            }
            .menuStyle(BorderlessButtonMenuStyle())

            // Time Range Filter
            Menu {
                ForEach(timeRanges, id: \.self) { range in
                    Button(action: {
                        selectedTimeRange = range
                    }) {
                        HStack {
                            Text(range)
                            if selectedTimeRange == range {
                                Image(systemName: "checkmark")
                            }
                        }
                    }
                }
            } label: {
                HStack(spacing: 6) {
                    Image(systemName: "calendar")
                        .font(.system(size: 12))
                    Text(selectedTimeRange)
                        .font(.system(size: 13))
                    Image(systemName: "chevron.down")
                        .font(.system(size: 10))
                }
                .foregroundColor(Color.fmText2)
                .padding(.horizontal, 12)
                .padding(.vertical, 6)
                .background(Color.white)
                .cornerRadius(6)
            }
            .menuStyle(BorderlessButtonMenuStyle())

            Spacer()

            // View mode toggle
            HStack(spacing: 0) {
                Button(action: { viewMode = "timeline" }) {
                    Image(systemName: "timeline.selection")
                        .font(.system(size: 14))
                        .foregroundColor(viewMode == "timeline" ? .white : Color.fmText3)
                        .frame(width: 32, height: 28)
                        .background(viewMode == "timeline" ? Color.blue : Color.clear)
                }
                .buttonStyle(PlainButtonStyle())

                Button(action: { viewMode = "cards" }) {
                    Image(systemName: "square.grid.2x2")
                        .font(.system(size: 14))
                        .foregroundColor(viewMode == "cards" ? .white : Color.fmText3)
                        .frame(width: 32, height: 28)
                        .background(viewMode == "cards" ? Color.blue : Color.clear)
                }
                .buttonStyle(PlainButtonStyle())
            }
            .background(Color.white)
            .cornerRadius(6)
            .overlay(
                RoundedRectangle(cornerRadius: 6)
                    .stroke(Color.fmBorder, lineWidth: 1)
            )

            // Legend toggle
            Button(action: { showLegend.toggle() }) {
                HStack(spacing: 6) {
                    Image(systemName: showLegend ? "sidebar.right" : "sidebar.left")
                        .font(.system(size: 14))
                    Text("图例")
                        .font(.system(size: 13))
                }
                .foregroundColor(Color.fmText2)
                .padding(.horizontal, 12)
                .padding(.vertical, 6)
                .background(Color.white)
                .cornerRadius(6)
            }
            .buttonStyle(PlainButtonStyle())

            if viewModel.isLoadingEvents {
                ProgressView()
                    .scaleEffect(0.8)
            }
        }
        .padding(.horizontal, 20)
        .padding(.vertical, 16)
        .background(Color.white)
    }

    // MARK: - Timeline View

    private var timelineView: some View {
        HStack(spacing: 0) {
            if viewModel.isLoadingEvents {
                loadingView
            } else if viewModel.filteredEvents().isEmpty {
                emptyStateView
            } else {
                ScrollView {
                    LazyVStack(alignment: .leading, spacing: 24) {
                        let groupedByYear = viewModel.eventsByYear()
                        let years = groupedByYear.keys.sorted(by: >)

                        ForEach(years, id: \.self) { year in
                            yearSection(year: year, events: groupedByYear[year] ?? [])
                        }
                    }
                    .padding(24)
                }
                .background(Color.fmBg)
            }

            if showLegend {
                Divider()
                legendView
            }
        }
    }

    private func yearSection(year: Int, events: [TimelineEventResponse]) -> some View {
        VStack(alignment: .leading, spacing: 16) {
            // Year header
            HStack {
                Text("\(year)")
                    .font(.system(size: 20, weight: .bold))
                    .foregroundColor(Color.fmText)

                Text("\(events.count) 个事件")
                    .font(.system(size: 13))
                    .foregroundColor(Color.fmText3)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 3)
                    .background(Color.fmBg2)
                    .cornerRadius(4)
            }

            // Events
            ForEach(Array(events.enumerated()), id: \.element.id) { index, event in
                HStack(alignment: .top, spacing: 16) {
                    // Timeline line
                    VStack(spacing: 0) {
                        if index > 0 {
                            Rectangle()
                                .fill(Color.fmBorder)
                                .frame(width: 2, height: 20)
                        }

                        Circle()
                            .fill(categoryColor(event.category ?? "其他"))
                            .frame(width: 12, height: 12)

                        if index < events.count - 1 {
                            Rectangle()
                                .fill(Color.fmBorder)
                                .frame(width: 2)
                        }
                    }

                    // Event card
                    ChronicleEventCard(event: event)
                        .frame(maxWidth: .infinity)
                }
            }
        }
    }

    // MARK: - Cards View

    private var cardsView: some View {
        HStack(spacing: 0) {
            if viewModel.isLoadingEvents {
                loadingView
            } else if viewModel.filteredEvents().isEmpty {
                emptyStateView
            } else {
                ScrollView {
                    LazyVGrid(columns: [
                        GridItem(.flexible(), spacing: 16),
                        GridItem(.flexible(), spacing: 16),
                        GridItem(.flexible(), spacing: 16)
                    ], spacing: 16) {
                        ForEach(viewModel.filteredEvents(), id: \.id) { event in
                            ChronicleEventCard(event: event)
                        }
                    }
                    .padding(24)
                }
                .background(Color.fmBg)
            }

            if showLegend {
                Divider()
                legendView
            }
        }
    }

    // MARK: - Legend View

    private var legendView: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("类别图例")
                .font(.system(size: 14, weight: .semibold))
                .foregroundColor(Color.fmText)

            VStack(alignment: .leading, spacing: 12) {
                ForEach(categories.dropFirst(), id: \.self) { category in
                    HStack(spacing: 10) {
                        Circle()
                            .fill(categoryColor(category))
                            .frame(width: 12, height: 12)

                        Text(category)
                            .font(.system(size: 13))
                            .foregroundColor(Color.fmText2)

                        Spacer()

                        if let stats = viewModel.stats {
                            Text("\(stats.categories[category] ?? 0)")
                                .font(.system(size: 12))
                                .foregroundColor(Color.fmText3)
                                .padding(.horizontal, 8)
                                .padding(.vertical, 3)
                                .background(Color.fmBg2)
                                .cornerRadius(4)
                        }
                    }
                }
            }

            Divider()
                .padding(.vertical, 8)

            if let stats = viewModel.stats {
                VStack(alignment: .leading, spacing: 12) {
                    Text("统计概览")
                        .font(.system(size: 14, weight: .semibold))
                        .foregroundColor(Color.fmText)

                    statItem(label: "总事件数", value: "\(stats.totalEvents)")

                    if let dateRange = stats.dateRange {
                        statItem(label: "时间跨度", value: "\(formatShortDate(dateRange.start)) - \(formatShortDate(dateRange.end))")
                    }
                }
            }
        }
        .padding(20)
        .frame(width: 280)
        .background(Color.white)
    }

    private func statItem(label: String, value: String) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(label)
                .font(.system(size: 11))
                .foregroundColor(Color.fmText3)

            Text(value)
                .font(.system(size: 13, weight: .medium))
                .foregroundColor(Color.fmText)
        }
    }

    // MARK: - Helper Views

    private var loadingView: some View {
        VStack(spacing: 16) {
            ProgressView()
                .scaleEffect(1.2)
            Text("加载事件数据...")
                .font(.system(size: 14))
                .foregroundColor(Color.fmText3)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color.fmBg)
    }

    private var emptyStateView: some View {
        VStack(spacing: 16) {
            Image(systemName: "calendar.badge.clock")
                .font(.system(size: 48))
                .foregroundColor(Color.fmText3)

            Text("暂无事件数据")
                .font(.system(size: 16, weight: .medium))
                .foregroundColor(Color.fmText2)

            Text("开始记录项目事件以建立时间线")
                .font(.system(size: 14))
                .foregroundColor(Color.fmText3)

            Button(action: {
                Task {
                    await viewModel.loadAllData(projectId: projectId)
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

    // MARK: - Helpers

    private func categoryColor(_ category: String) -> Color {
        switch category {
        case "文化活动": return Color(hex: "3B82F6")
        case "调研记录": return Color(hex: "10B981")
        case "政策变化": return Color(hex: "F59E0B")
        case "技艺传承": return Color(hex: "8B5CF6")
        case "经济变迁": return Color(hex: "EF4444")
        case "环境变化": return Color(hex: "06B6D4")
        default: return Color(hex: "94A3B8")
        }
    }

    private func formatShortDate(_ dateString: String) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd"
        if let date = formatter.date(from: dateString) {
            formatter.dateFormat = "yyyy/M/d"
            return formatter.string(from: date)
        }
        return dateString
    }
}

// MARK: - Chronicle Event Card

struct ChronicleEventCard: View {
    let event: TimelineEventResponse

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Date and category
            HStack {
                Text(formatDate(event.date))
                    .font(.system(size: 12, weight: .medium))
                    .foregroundColor(Color.fmText2)

                if let category = event.category {
                    Text(category)
                        .font(.system(size: 11))
                        .foregroundColor(categoryColor(category))
                        .padding(.horizontal, 6)
                        .padding(.vertical, 3)
                        .background(categoryColor(category).opacity(0.1))
                        .cornerRadius(4)
                }

                Spacer()

                if let confidence = event.confidence {
                    HStack(spacing: 4) {
                        Image(systemName: "chart.bar.fill")
                            .font(.system(size: 10))
                        Text(String(format: "%.0f%%", confidence * 100))
                            .font(.system(size: 11))
                    }
                    .foregroundColor(Color.fmText3)
                }
            }

            // Title
            Text(event.title)
                .font(.system(size: 14, weight: .semibold))
                .foregroundColor(Color.fmText)
                .lineLimit(2)

            // Description
            if let description = event.description {
                Text(description)
                    .font(.system(size: 12))
                    .foregroundColor(Color.fmText2)
                    .lineLimit(3)
            }

            // Tags
            if let tags = event.tags, !tags.isEmpty {
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 6) {
                        ForEach(tags.prefix(5), id: \.self) { tag in
                            Text(tag)
                                .font(.system(size: 10))
                                .foregroundColor(Color.fmText3)
                                .padding(.horizontal, 6)
                                .padding(.vertical, 3)
                                .background(Color.fmBg2)
                                .cornerRadius(3)
                        }
                    }
                }
            }

            // Footer
            if let documentIds = event.documentIds, !documentIds.isEmpty {
                HStack(spacing: 4) {
                    Image(systemName: "doc.text")
                        .font(.system(size: 10))
                    Text("\(documentIds.count) 个相关文档")
                        .font(.system(size: 11))
                }
                .foregroundColor(Color.fmText3)
            }
        }
        .padding(16)
        .background(Color.white)
        .cornerRadius(10)
        .overlay(
            RoundedRectangle(cornerRadius: 10)
                .stroke(Color.fmBorder, lineWidth: 1)
        )
    }

    private func formatDate(_ dateString: String) -> String {
        let formatter = ISO8601DateFormatter()
        if let date = formatter.date(from: dateString) {
            let displayFormatter = DateFormatter()
            displayFormatter.dateFormat = "yyyy年M月d日"
            return displayFormatter.string(from: date)
        }

        // Fallback for simple format
        let simpleFormatter = DateFormatter()
        simpleFormatter.dateFormat = "yyyy-MM-dd"
        if let date = simpleFormatter.date(from: dateString) {
            simpleFormatter.dateFormat = "yyyy年M月d日"
            return simpleFormatter.string(from: date)
        }

        return dateString
    }

    private func categoryColor(_ category: String) -> Color {
        switch category {
        case "文化活动": return Color(hex: "3B82F6")
        case "调研记录": return Color(hex: "10B981")
        case "政策变化": return Color(hex: "F59E0B")
        case "技艺传承": return Color(hex: "8B5CF6")
        case "经济变迁": return Color(hex: "EF4444")
        case "环境变化": return Color(hex: "06B6D4")
        default: return Color(hex: "94A3B8")
        }
    }
}
