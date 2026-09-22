import SwiftUI

// MARK: - TimelinePage
struct TimelinePage: View {
    let projectId: Int

    @StateObject private var viewModel = TimelineViewModel()

    @State private var searchText = ""
    @State private var selectedCategory: String?
    @State private var selectedTimeRange = "全部时间"
    @State private var viewMode = "horizontal"  // "horizontal" or "vertical"
    @State private var showLegend = true
    @State private var zoomLevel: CGFloat = 1.0  // 0.5 to 2.0
    @State private var selectedEventId: String?
    @State private var showBuildSheet = false

    let categories = ["全部类型", "event", "milestone", "meeting", "research", "policy", "custom"]
    let timeRanges = ["全部时间", "近1年", "近3年", "近5年", "10年以上"]

    var filteredEvents: [TimelineEventResponse] {
        var filtered = viewModel.events

        // Apply search filter
        if !searchText.isEmpty {
            filtered = filtered.filter { event in
                event.title.localizedCaseInsensitiveContains(searchText) ||
                (event.description?.localizedCaseInsensitiveContains(searchText) ?? false)
            }
        }

        // Apply category filter
        if let category = selectedCategory, category != "全部类型" {
            filtered = filtered.filter { $0.category == category }
        }

        return filtered
    }

    var body: some View {
        VStack(spacing: 0) {
            // Top toolbar
            topToolbar

            Divider()

            // Main content
            if viewModel.isLoadingEvents {
                VStack(spacing: 16) {
                    ProgressView()
                    Text("加载时间线数据...")
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
            } else if filteredEvents.isEmpty {
                VStack(spacing: 16) {
                    Image(systemName: "clock")
                        .font(.system(size: 48))
                        .foregroundColor(Color.fmText3)
                    Text("暂无时间线数据")
                        .font(.system(size: 15))
                        .foregroundColor(Color.fmText2)
                    Button("构建时间线") {
                        showBuildSheet = true
                    }
                    .fmPrimary()
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                if viewMode == "horizontal" {
                    horizontalTimelineView
                } else {
                    verticalTimelineView
                }
            }
        }
        .background(Color.white)
        .task {
            await viewModel.loadAllData(projectId: projectId)
        }
        .sheet(isPresented: $showBuildSheet) {
            BuildTimelineSheet(
                projectId: projectId,
                onBuild: { documentIds, forceRebuild in
                    Task {
                        await viewModel.buildTimeline(
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

                TextField("搜索时间轴事件...", text: $searchText)
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

            // Category filter
            Menu {
                ForEach(categories, id: \.self) { category in
                    Button(action: {
                        selectedCategory = category == "全部类型" ? nil : category
                    }) {
                        HStack {
                            Text(categoryLabel(category))
                            if (selectedCategory ?? "全部类型") == category {
                                Spacer()
                                Image(systemName: "checkmark")
                            }
                        }
                    }
                }
            } label: {
                HStack(spacing: 6) {
                    Image(systemName: "tag")
                        .font(.system(size: 13))
                    Text(categoryLabel(selectedCategory ?? "全部类型"))
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

            // Build timeline button
            Button(action: { showBuildSheet = true }) {
                HStack(spacing: 6) {
                    Image(systemName: "hammer")
                        .font(.system(size: 13))
                    Text("构建时间线")
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

            // Time range filter
            Menu {
                ForEach(timeRanges, id: \.self) { range in
                    Button(action: { selectedTimeRange = range }) {
                        HStack {
                            Text(range)
                            if selectedTimeRange == range {
                                Spacer()
                                Image(systemName: "checkmark")
                            }
                        }
                    }
                }
            } label: {
                HStack(spacing: 6) {
                    Image(systemName: "clock")
                        .font(.system(size: 13))
                    Text(selectedTimeRange)
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

            // View mode toggle
            HStack(spacing: 0) {
                Button(action: { viewMode = "horizontal" }) {
                    Image(systemName: "arrow.left.and.right")
                        .font(.system(size: 13))
                        .foregroundColor(viewMode == "horizontal" ? Color.white : Color.fmText2)
                        .frame(width: 32, height: 28)
                        .background(viewMode == "horizontal" ? Color.blue : Color.clear)
                }
                .buttonStyle(PlainButtonStyle())

                Rectangle()
                    .fill(Color.fmBorder)
                    .frame(width: 1)

                Button(action: { viewMode = "vertical" }) {
                    Image(systemName: "arrow.up.and.down")
                        .font(.system(size: 13))
                        .foregroundColor(viewMode == "vertical" ? Color.white : Color.fmText2)
                        .frame(width: 32, height: 28)
                        .background(viewMode == "vertical" ? Color.blue : Color.clear)
                }
                .buttonStyle(PlainButtonStyle())
            }
            .overlay(
                RoundedRectangle(cornerRadius: 6)
                    .stroke(Color.fmBorder, lineWidth: 1)
            )

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
            Button(action: { print("Export timeline") }) {
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

    // MARK: - Horizontal Timeline View
    private var horizontalTimelineView: some View {
        HStack(spacing: 0) {
            ScrollView(.horizontal, showsIndicators: true) {
                ScrollView(.vertical, showsIndicators: true) {
                    HStack(alignment: .top, spacing: 0) {
                        ForEach(groupEventsByYear(), id: \.year) { yearGroup in
                            HorizontalYearColumn(
                                year: yearGroup.year,
                                events: yearGroup.events,
                                zoomLevel: zoomLevel,
                                onSelectEvent: { eventId in selectedEventId = eventId }
                            )
                        }
                    }
                    .padding(40)
                }
            }
            .background(Color.fmBg.opacity(0.3))

            if showLegend {
                legendPanel
            }
        }
    }

    // MARK: - Vertical Timeline View
    private var verticalTimelineView: some View {
        HStack(spacing: 0) {
            ScrollView {
                VStack(spacing: 0) {
                    ForEach(groupEventsByYear(), id: \.year) { yearGroup in
                        VerticalYearSection(
                            year: yearGroup.year,
                            events: yearGroup.events,
                            zoomLevel: zoomLevel,
                            onSelectEvent: { eventId in selectedEventId = eventId }
                        )
                    }
                }
                .padding(40)
            }
            .background(Color.fmBg.opacity(0.3))

            if showLegend {
                legendPanel
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

            // Type legend
            VStack(alignment: .leading, spacing: 12) {
                Text("事件类型")
                    .font(.system(size: 13, weight: .medium))
                    .foregroundColor(Color.fmText2)

                ForEach(getLegendData(), id: \.type) { item in
                    TimelineLegendItem(
                        color: item.color,
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

                TimelineStatRow(label: "总事件数", value: "\(filteredEvents.count)")
                TimelineStatRow(label: "时间跨度", value: "\(calculateTimeSpan())年")
                TimelineStatRow(label: "类别数", value: "\(Set(filteredEvents.compactMap { $0.category }).count)")
                TimelineStatRow(label: "平均每年", value: String(format: "%.1f", averageEventsPerYear()))
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
    private func groupEventsByYear() -> [TimelineYearGroup] {
        let grouped = viewModel.eventsByYear()
        return grouped.map { TimelineYearGroup(year: $0.key, events: $0.value) }
            .sorted { $0.year > $1.year }
    }

    private func getLegendData() -> [(type: String, color: String, count: Int)] {
        let allTypes = ["event", "milestone", "meeting", "research", "policy", "custom"]
        return allTypes.map { type in
            let count = filteredEvents.filter { $0.category == type }.count
            let color = eventCategoryColor(type)
            return (type: categoryLabel(type), color: color, count: count)
        }
    }

    private func calculateTimeSpan() -> Int {
        guard let dateRange = viewModel.stats?.dateRange else { return 0 }
        let start = dateRange.start
        let end = dateRange.end

        // Extract years from date strings
        if let startYear = Int(start.prefix(4)), let endYear = Int(end.prefix(4)) {
            return endYear - startYear + 1
        }
        return 0
    }

    private func averageEventsPerYear() -> Double {
        let span = calculateTimeSpan()
        guard span > 0 else { return 0 }
        return Double(filteredEvents.count) / Double(span)
    }

    private func categoryLabel(_ category: String) -> String {
        switch category {
        case "event": return "事件"
        case "milestone": return "里程碑"
        case "meeting": return "会议"
        case "research": return "调研"
        case "policy": return "政策"
        case "custom": return "自定义"
        default: return category
        }
    }

    private func eventCategoryColor(_ category: String) -> String {
        switch category {
        case "event": return "3B82F6"      // Blue
        case "milestone": return "10B981"  // Green
        case "meeting": return "F59E0B"    // Orange
        case "research": return "8B5CF6"   // Purple
        case "policy": return "EC4899"     // Pink
        case "custom": return "14B8A6"     // Teal
        default: return "64748B"           // Gray
        }
    }
}

// MARK: - Timeline Year Group Helper
struct TimelineYearGroup {
    let year: Int
    let events: [TimelineEventResponse]
}

// MARK: - Horizontal Year Column
struct HorizontalYearColumn: View {
    let year: Int
    let events: [TimelineEventResponse]
    let zoomLevel: CGFloat
    let onSelectEvent: (String) -> Void

    private var sortedEvents: [TimelineEventResponse] {
        events.sorted { $0.date > $1.date }
    }

    private var columnWidth: CGFloat {
        200 * zoomLevel
    }

    var body: some View {
        VStack(spacing: 0) {
            // Year header
            VStack(spacing: 8) {
                Text("\(year)")
                    .font(.system(size: 20 * zoomLevel, weight: .bold))
                    .foregroundColor(Color.fmText)

                Text("\(events.count)个事件")
                    .font(.system(size: 11 * zoomLevel))
                    .foregroundColor(Color.fmText3)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(Color.fmBg)
                    .cornerRadius(10)
            }
            .frame(width: columnWidth)
            .padding(.vertical, 16)
            .background(Color.white)
            .cornerRadius(8)
            .overlay(
                RoundedRectangle(cornerRadius: 8)
                    .stroke(Color.fmBorder, lineWidth: 1)
            )

            // Timeline axis line
            Rectangle()
                .fill(Color.fmBorder)
                .frame(width: 2, height: 20 * zoomLevel)

            // Events
            VStack(spacing: 30 * zoomLevel) {
                ForEach(Array(sortedEvents.enumerated()), id: \.element.id) { index, event in
                    HorizontalTimelineEventCard(
                        event: event,
                        zoomLevel: zoomLevel,
                        isLeft: index % 2 == 0,
                        onTap: { onSelectEvent(event.id) }
                    )
                }
            }
        }
    }
}

// MARK: - Horizontal Timeline Event Card
struct HorizontalTimelineEventCard: View {
    let event: TimelineEventResponse
    let zoomLevel: CGFloat
    let isLeft: Bool
    let onTap: () -> Void

    private var cardWidth: CGFloat {
        180 * zoomLevel
    }

    var body: some View {
        VStack(spacing: 0) {
            // Connecting line
            Rectangle()
                .fill(Color.fmBorder)
                .frame(width: 2, height: 20 * zoomLevel)

            // Node dot
            Circle()
                .fill(Color(hex: eventCategoryColor(event.category ?? "event")))
                .frame(width: 12 * zoomLevel, height: 12 * zoomLevel)
                .overlay(
                    Circle()
                        .stroke(Color.white, lineWidth: 2 * zoomLevel)
                )

            // Branch line
            Rectangle()
                .fill(Color.fmBorder)
                .frame(width: 2, height: 15 * zoomLevel)

            // Card
            VStack(alignment: .leading, spacing: 8 * zoomLevel) {
                // Category badge
                Text(categoryLabel(event.category ?? "event"))
                    .font(.system(size: 10 * zoomLevel, weight: .medium))
                    .foregroundColor(Color(hex: eventCategoryColor(event.category ?? "event")))
                    .padding(.horizontal, 8 * zoomLevel)
                    .padding(.vertical, 3 * zoomLevel)
                    .background(Color(hex: eventCategoryColor(event.category ?? "event")).opacity(0.1))
                    .cornerRadius(10)

                // Title
                Text(event.title)
                    .font(.system(size: 13 * zoomLevel, weight: .semibold))
                    .foregroundColor(Color.fmText)
                    .lineLimit(2)

                // Date
                HStack(spacing: 4) {
                    Image(systemName: "calendar")
                        .font(.system(size: 10 * zoomLevel))
                    Text(formatDate(event.date))
                        .font(.system(size: 11 * zoomLevel))
                }
                .foregroundColor(Color.fmText3)

                // Description
                if let description = event.description {
                    Text(description)
                        .font(.system(size: 11 * zoomLevel))
                        .foregroundColor(Color.fmText2)
                        .lineLimit(3)
                }
            }
            .padding(12 * zoomLevel)
            .frame(width: cardWidth)
            .background(Color.white)
            .cornerRadius(8)
            .overlay(
                RoundedRectangle(cornerRadius: 8)
                    .stroke(Color.fmBorder, lineWidth: 1)
            )
            .shadow(color: Color.black.opacity(0.05), radius: 4, x: 0, y: 2)
            .onTapGesture(perform: onTap)
        }
    }

    private func categoryLabel(_ category: String) -> String {
        switch category {
        case "event": return "事件"
        case "milestone": return "里程碑"
        case "meeting": return "会议"
        case "research": return "调研"
        case "policy": return "政策"
        case "custom": return "自定义"
        default: return category
        }
    }

    private func eventCategoryColor(_ category: String) -> String {
        switch category {
        case "event": return "3B82F6"
        case "milestone": return "10B981"
        case "meeting": return "F59E0B"
        case "research": return "8B5CF6"
        case "policy": return "EC4899"
        case "custom": return "14B8A6"
        default: return "64748B"
        }
    }

    private func formatDate(_ dateString: String) -> String {
        // Simple date formatting - just show first 10 chars (YYYY-MM-DD)
        String(dateString.prefix(10))
    }
}

// MARK: - Vertical Year Section
struct VerticalYearSection: View {
    let year: Int
    let events: [TimelineEventResponse]
    let zoomLevel: CGFloat
    let onSelectEvent: (String) -> Void

    private var sortedEvents: [TimelineEventResponse] {
        events.sorted { $0.date > $1.date }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            // Year header
            HStack(spacing: 12) {
                Text("\(year)年")
                    .font(.system(size: 24 * zoomLevel, weight: .bold))
                    .foregroundColor(Color.fmText)

                Text("\(events.count)个事件")
                    .font(.system(size: 12 * zoomLevel))
                    .foregroundColor(Color.fmText3)
                    .padding(.horizontal, 10)
                    .padding(.vertical, 4)
                    .background(Color.fmBg)
                    .cornerRadius(12)

                Rectangle()
                    .fill(Color.fmBorder)
                    .frame(height: 1)
            }
            .padding(.bottom, 20 * zoomLevel)

            // Timeline events
            ForEach(Array(sortedEvents.enumerated()), id: \.element.id) { index, event in
                VerticalTimelineEventRow(
                    event: event,
                    zoomLevel: zoomLevel,
                    isLast: index == sortedEvents.count - 1,
                    onTap: { onSelectEvent(event.id) }
                )
            }
        }
        .padding(.bottom, 40 * zoomLevel)
    }
}

// MARK: - Vertical Timeline Event Row
struct VerticalTimelineEventRow: View {
    let event: TimelineEventResponse
    let zoomLevel: CGFloat
    let isLast: Bool
    let onTap: () -> Void

    var body: some View {
        HStack(alignment: .top, spacing: 0) {
            // Timeline column
            VStack(spacing: 0) {
                Circle()
                    .fill(Color(hex: eventCategoryColor(event.category ?? "event")))
                    .frame(width: 12 * zoomLevel, height: 12 * zoomLevel)
                    .overlay(
                        Circle()
                            .stroke(Color.white, lineWidth: 2 * zoomLevel)
                    )

                if !isLast {
                    Rectangle()
                        .fill(Color.fmBorder)
                        .frame(width: 2)
                        .frame(minHeight: 120 * zoomLevel)
                }
            }
            .padding(.top, 4)
            .frame(width: 40 * zoomLevel)

            // Content card
            VStack(alignment: .leading, spacing: 10 * zoomLevel) {
                // Category badge and date
                HStack {
                    Text(categoryLabel(event.category ?? "event"))
                        .font(.system(size: 11 * zoomLevel, weight: .medium))
                        .foregroundColor(Color(hex: eventCategoryColor(event.category ?? "event")))
                        .padding(.horizontal, 8 * zoomLevel)
                        .padding(.vertical, 3 * zoomLevel)
                        .background(Color(hex: eventCategoryColor(event.category ?? "event")).opacity(0.1))
                        .cornerRadius(10)

                    Spacer()

                    HStack(spacing: 4) {
                        Image(systemName: "calendar")
                            .font(.system(size: 11 * zoomLevel))
                        Text(formatDate(event.date))
                            .font(.system(size: 12 * zoomLevel))
                    }
                    .foregroundColor(Color.fmText3)
                }

                // Title
                Text(event.title)
                    .font(.system(size: 15 * zoomLevel, weight: .semibold))
                    .foregroundColor(Color.fmText)

                // Description
                if let description = event.description {
                    Text(description)
                        .font(.system(size: 13 * zoomLevel))
                        .foregroundColor(Color.fmText2)
                        .lineLimit(3)
                }

                // Tags
                if let tags = event.tags, !tags.isEmpty {
                    FlowLayout(spacing: 6 * zoomLevel) {
                        ForEach(tags.prefix(5), id: \.self) { tag in
                            Text(tag)
                                .font(.system(size: 11 * zoomLevel))
                                .foregroundColor(Color.fmText3)
                                .padding(.horizontal, 8 * zoomLevel)
                                .padding(.vertical, 3 * zoomLevel)
                                .background(Color.fmBg)
                                .cornerRadius(10)
                        }
                    }
                }
            }
            .padding(16 * zoomLevel)
            .background(Color.white)
            .cornerRadius(8)
            .overlay(
                RoundedRectangle(cornerRadius: 8)
                    .stroke(Color.fmBorder, lineWidth: 1)
            )
            .shadow(color: Color.black.opacity(0.05), radius: 4, x: 0, y: 2)
            .onTapGesture(perform: onTap)
        }
        .padding(.bottom, isLast ? 0 : 20 * zoomLevel)
    }

    private func categoryLabel(_ category: String) -> String {
        switch category {
        case "event": return "事件"
        case "milestone": return "里程碑"
        case "meeting": return "会议"
        case "research": return "调研"
        case "policy": return "政策"
        case "custom": return "自定义"
        default: return category
        }
    }

    private func eventCategoryColor(_ category: String) -> String {
        switch category {
        case "event": return "3B82F6"
        case "milestone": return "10B981"
        case "meeting": return "F59E0B"
        case "research": return "8B5CF6"
        case "policy": return "EC4899"
        case "custom": return "14B8A6"
        default: return "64748B"
        }
    }

    private func formatDate(_ dateString: String) -> String {
        String(dateString.prefix(10))
    }
}

// MARK: - Build Timeline Sheet
struct BuildTimelineSheet: View {
    let projectId: Int
    let onBuild: ([Int]?, Bool) -> Void

    @State private var forceRebuild = false
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        VStack(spacing: 24) {
            // Header
            HStack {
                Text("构建时间线")
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

            // Options
            VStack(alignment: .leading, spacing: 16) {
                Toggle(isOn: $forceRebuild) {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("强制重建")
                            .font(.system(size: 14, weight: .medium))
                            .foregroundColor(Color.fmText)
                        Text("删除现有数据并重新提取所有事件")
                            .font(.system(size: 12))
                            .foregroundColor(Color.fmText3)
                    }
                }
            }

            Spacer()

            // Actions
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
        .frame(width: 400, height: 280)
    }
}
