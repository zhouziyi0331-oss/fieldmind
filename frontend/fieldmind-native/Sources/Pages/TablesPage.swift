import SwiftUI

struct TablesPage: View {
    let projectId: Int
    @StateObject private var viewModel = TableViewModel()
    @State private var searchText = ""
    @State private var selectedType = "全部类型"
    @State private var sortBy = "最新上传"
    @State private var viewMode: ViewMode = .grid
    @State private var selectedTables: Set<Int> = []
    @State private var showUploadSheet = false
    @State private var selectedTable: TableService.TableData?

    enum ViewMode {
        case grid, list
    }

    let typeOptions = ["全部类型", "Excel", "CSV", "JSON", "Database Export"]
    let sortOptions = ["最新上传", "最早上传", "名称", "大小", "行数"]

    var body: some View {
        VStack(spacing: 0) {
            toolbar
            Divider()

            if let errorMessage = viewModel.errorMessage {
                errorBanner(errorMessage)
            } else if let successMessage = viewModel.successMessage {
                successBanner(successMessage)
            }

            if viewModel.isLoading {
                loadingView
            } else if !viewModel.hasTables {
                emptyStateView
            } else {
                contentView
            }
        }
        .background(Color.fmBg)
        .sheet(isPresented: $showUploadSheet) {
            UploadTableSheet(projectId: projectId, viewModel: viewModel)
        }
        .sheet(item: $selectedTable) { table in
            TableDetailSheet(table: table, projectId: projectId)
        }
        .task {
            await loadData()
        }
    }

    // MARK: - Toolbar

    private var toolbar: some View {
        HStack(spacing: 12) {
            // Search
            HStack(spacing: 8) {
                Image(systemName: "magnifyingglass")
                    .foregroundColor(Color(hex: "94A3B8"))
                    .font(.system(size: 14))
                TextField("搜索表格文件或标签...", text: $searchText)
                    .textFieldStyle(.plain)
                    .font(.system(size: 13))
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
            .background(Color(hex: "F8FAFC"))
            .cornerRadius(8)
            .frame(width: 280)

            // Type filter
            Menu {
                ForEach(typeOptions, id: \.self) { option in
                    Button(option) {
                        selectedType = option
                        Task {
                            await viewModel.loadTables(
                                projectId: projectId,
                                format: option == "全部类型" ? nil : option
                            )
                        }
                    }
                }
            } label: {
                HStack(spacing: 6) {
                    Image(systemName: "doc.fill")
                        .font(.system(size: 12))
                    Text(selectedType)
                        .font(.system(size: 13))
                    Image(systemName: "chevron.down")
                        .font(.system(size: 10))
                }
                .foregroundColor(Color(hex: "475569"))
                .padding(.horizontal, 12)
                .padding(.vertical, 8)
                .background(Color.white)
                .cornerRadius(8)
            }
            .menuStyle(BorderlessButtonMenuStyle())

            // Sort menu
            Menu {
                ForEach(sortOptions, id: \.self) { option in
                    Button(option) {
                        sortBy = option
                    }
                }
            } label: {
                HStack(spacing: 6) {
                    Image(systemName: "arrow.up.arrow.down")
                        .font(.system(size: 12))
                    Text(sortBy)
                        .font(.system(size: 13))
                    Image(systemName: "chevron.down")
                        .font(.system(size: 10))
                }
                .foregroundColor(Color(hex: "475569"))
                .padding(.horizontal, 12)
                .padding(.vertical, 8)
                .background(Color.white)
                .cornerRadius(8)
            }
            .menuStyle(BorderlessButtonMenuStyle())

            Spacer()

            // Stats
            if let stats = viewModel.statistics {
                HStack(spacing: 16) {
                    statBadge(label: "表格", value: "\(stats.totalTables)")
                    statBadge(label: "总行数", value: formatNumber(stats.totalRows))
                    statBadge(label: "总大小", value: viewModel.formatFileSize(stats.totalSize))
                }
            }

            // View mode toggle
            HStack(spacing: 0) {
                Button(action: { viewMode = .grid }) {
                    Image(systemName: "square.grid.2x2")
                        .font(.system(size: 14))
                        .foregroundColor(viewMode == .grid ? .white : Color.fmText3)
                        .frame(width: 32, height: 28)
                        .background(viewMode == .grid ? Color.blue : Color.clear)
                }
                .buttonStyle(PlainButtonStyle())

                Button(action: { viewMode = .list }) {
                    Image(systemName: "list.bullet")
                        .font(.system(size: 14))
                        .foregroundColor(viewMode == .list ? .white : Color.fmText3)
                        .frame(width: 32, height: 28)
                        .background(viewMode == .list ? Color.blue : Color.clear)
                }
                .buttonStyle(PlainButtonStyle())
            }
            .background(Color.white)
            .cornerRadius(6)
            .overlay(
                RoundedRectangle(cornerRadius: 6)
                    .stroke(Color.fmBorder, lineWidth: 1)
            )

            // Upload button
            Button(action: { showUploadSheet = true }) {
                HStack(spacing: 6) {
                    Image(systemName: "arrow.up.doc")
                        .font(.system(size: 13))
                    Text("上传表格")
                        .font(.system(size: 14))
                }
                .foregroundColor(.white)
                .padding(.horizontal, 16)
                .padding(.vertical, 8)
                .background(Color.blue)
                .cornerRadius(8)
            }
            .buttonStyle(PlainButtonStyle())
            .disabled(viewModel.isUploading)

            if viewModel.isLoading || viewModel.isUploading {
                ProgressView()
                    .scaleEffect(0.8)
            }
        }
        .padding(.horizontal, 20)
        .padding(.vertical, 16)
        .background(Color.white)
    }

    private func statBadge(label: String, value: String) -> some View {
        HStack(spacing: 6) {
            Text(label)
                .font(.system(size: 12))
                .foregroundColor(Color.fmText3)
            Text(value)
                .font(.system(size: 13, weight: .semibold))
                .foregroundColor(Color.fmText)
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 6)
        .background(Color.fmBg2)
        .cornerRadius(6)
    }

    // MARK: - Content Views

    private var contentView: some View {
        Group {
            if viewMode == .grid {
                gridView
            } else {
                listView
            }
        }
    }

    private var gridView: some View {
        ScrollView {
            LazyVGrid(columns: [
                GridItem(.flexible(), spacing: 16),
                GridItem(.flexible(), spacing: 16),
                GridItem(.flexible(), spacing: 16)
            ], spacing: 16) {
                let filtered = viewModel.filterTables(
                    searchText: searchText,
                    format: selectedType,
                    sortBy: sortBy
                )

                ForEach(filtered) { table in
                    TableGridCard(
                        table: table,
                        isSelected: selectedTables.contains(table.id),
                        onTap: { selectedTable = table },
                        onSelect: { toggleSelection(table.id) }
                    )
                }
            }
            .padding(24)
        }
        .background(Color.fmBg)
    }

    private var listView: some View {
        ScrollView {
            LazyVStack(spacing: 12) {
                let filtered = viewModel.filterTables(
                    searchText: searchText,
                    format: selectedType,
                    sortBy: sortBy
                )

                ForEach(filtered) { table in
                    TableListRow(
                        table: table,
                        isSelected: selectedTables.contains(table.id),
                        onTap: { selectedTable = table },
                        onSelect: { toggleSelection(table.id) },
                        onDelete: {
                            Task {
                                await viewModel.deleteTable(projectId: projectId, tableId: table.id)
                            }
                        }
                    )
                }
            }
            .padding(24)
        }
        .background(Color.fmBg)
    }

    private var loadingView: some View {
        VStack(spacing: 16) {
            ProgressView()
                .scaleEffect(1.2)
            Text("加载表格数据...")
                .font(.system(size: 14))
                .foregroundColor(Color.fmText3)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color.fmBg)
    }

    private var emptyStateView: some View {
        VStack(spacing: 16) {
            Image(systemName: "tablecells")
                .font(.system(size: 48))
                .foregroundColor(Color.fmText3)

            Text("暂无表格数据")
                .font(.system(size: 16, weight: .medium))
                .foregroundColor(Color.fmText2)

            Text("上传 Excel、CSV 或其他表格文件开始分析")
                .font(.system(size: 14))
                .foregroundColor(Color.fmText3)

            Button(action: { showUploadSheet = true }) {
                HStack(spacing: 6) {
                    Image(systemName: "arrow.up.doc")
                        .font(.system(size: 13))
                    Text("上传表格")
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

    // MARK: - Helpers

    private func toggleSelection(_ id: Int) {
        if selectedTables.contains(id) {
            selectedTables.remove(id)
        } else {
            selectedTables.insert(id)
        }
    }

    private func formatNumber(_ number: Int) -> String {
        let formatter = NumberFormatter()
        formatter.numberStyle = .decimal
        return formatter.string(from: NSNumber(value: number)) ?? "\(number)"
    }

    private func loadData() async {
        await viewModel.loadTables(projectId: projectId)
        await viewModel.loadStatistics(projectId: projectId)
    }
}

// MARK: - Table Grid Card

struct TableGridCard: View {
    let table: TableService.TableData
    let isSelected: Bool
    let onTap: () -> Void
    let onSelect: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Header with checkbox
            HStack {
                Button(action: onSelect) {
                    Image(systemName: isSelected ? "checkmark.circle.fill" : "circle")
                        .font(.system(size: 18))
                        .foregroundColor(isSelected ? .blue : Color.fmText3)
                }
                .buttonStyle(PlainButtonStyle())

                Spacer()

                formatBadge(table.format)
            }

            // File icon and name
            VStack(spacing: 8) {
                Image(systemName: formatIcon(table.format))
                    .font(.system(size: 32))
                    .foregroundColor(formatColor(table.format))

                Text(table.filename)
                    .font(.system(size: 13, weight: .medium))
                    .foregroundColor(Color.fmText)
                    .lineLimit(2)
                    .multilineTextAlignment(.center)
            }
            .frame(maxWidth: .infinity)

            Divider()

            // Stats
            VStack(spacing: 8) {
                HStack {
                    Image(systemName: "tablecells")
                        .font(.system(size: 11))
                        .foregroundColor(Color.fmText3)
                    Text("\(table.rowCount) 行 × \(table.columnCount) 列")
                        .font(.system(size: 11))
                        .foregroundColor(Color.fmText2)
                    Spacer()
                }

                HStack {
                    Image(systemName: "doc")
                        .font(.system(size: 11))
                        .foregroundColor(Color.fmText3)
                    Text(formatFileSize(table.fileSize))
                        .font(.system(size: 11))
                        .foregroundColor(Color.fmText2)
                    Spacer()
                }
            }

            // Tags
            if !table.tags.isEmpty {
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 6) {
                        ForEach(table.tags.prefix(3), id: \.self) { tag in
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
        }
        .padding(16)
        .background(Color.white)
        .cornerRadius(12)
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(isSelected ? Color.blue : Color.fmBorder, lineWidth: isSelected ? 2 : 1)
        )
        .onTapGesture(perform: onTap)
    }

    private func formatBadge(_ format: String) -> some View {
        Text(format.uppercased())
            .font(.system(size: 10, weight: .semibold))
            .foregroundColor(formatColor(format))
            .padding(.horizontal, 6)
            .padding(.vertical, 3)
            .background(formatColor(format).opacity(0.1))
            .cornerRadius(4)
    }

    private func formatIcon(_ format: String) -> String {
        switch format.lowercased() {
        case "excel": return "doc.richtext"
        case "csv": return "tablecells"
        case "json": return "curlybraces"
        default: return "doc"
        }
    }

    private func formatColor(_ format: String) -> Color {
        switch format.lowercased() {
        case "excel": return Color(hex: "10B981")
        case "csv": return Color(hex: "3B82F6")
        case "json": return Color(hex: "F59E0B")
        default: return Color(hex: "94A3B8")
        }
    }

    private func formatFileSize(_ bytes: Int) -> String {
        let formatter = ByteCountFormatter()
        formatter.allowedUnits = [.useKB, .useMB, .useGB]
        formatter.countStyle = .file
        return formatter.string(fromByteCount: Int64(bytes))
    }
}

// MARK: - Table List Row

struct TableListRow: View {
    let table: TableService.TableData
    let isSelected: Bool
    let onTap: () -> Void
    let onSelect: () -> Void
    let onDelete: () -> Void

    var body: some View {
        HStack(spacing: 16) {
            // Checkbox
            Button(action: onSelect) {
                Image(systemName: isSelected ? "checkmark.circle.fill" : "circle")
                    .font(.system(size: 18))
                    .foregroundColor(isSelected ? .blue : Color.fmText3)
            }
            .buttonStyle(PlainButtonStyle())

            // Icon
            Image(systemName: formatIcon(table.format))
                .font(.system(size: 24))
                .foregroundColor(formatColor(table.format))
                .frame(width: 40, height: 40)
                .background(formatColor(table.format).opacity(0.1))
                .cornerRadius(8)

            // File info
            VStack(alignment: .leading, spacing: 4) {
                Text(table.filename)
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(Color.fmText)

                HStack(spacing: 12) {
                    Label("\(table.rowCount) 行", systemImage: "tablecells")
                        .font(.system(size: 11))
                        .foregroundColor(Color.fmText3)

                    Label(formatFileSize(table.fileSize), systemImage: "doc")
                        .font(.system(size: 11))
                        .foregroundColor(Color.fmText3)

                    Label(formatDate(table.uploadedAt), systemImage: "clock")
                        .font(.system(size: 11))
                        .foregroundColor(Color.fmText3)
                }
            }

            Spacer()

            // Tags
            if !table.tags.isEmpty {
                HStack(spacing: 6) {
                    ForEach(table.tags.prefix(2), id: \.self) { tag in
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

            // Actions
            HStack(spacing: 8) {
                Button(action: onTap) {
                    Image(systemName: "eye")
                        .font(.system(size: 14))
                        .foregroundColor(Color.fmText2)
                        .frame(width: 32, height: 32)
                        .background(Color.fmBg2)
                        .cornerRadius(6)
                }
                .buttonStyle(PlainButtonStyle())

                Button(action: onDelete) {
                    Image(systemName: "trash")
                        .font(.system(size: 14))
                        .foregroundColor(Color(hex: "EF4444"))
                        .frame(width: 32, height: 32)
                        .background(Color(hex: "FEE2E2"))
                        .cornerRadius(6)
                }
                .buttonStyle(PlainButtonStyle())
            }
        }
        .padding(16)
        .background(Color.white)
        .cornerRadius(12)
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(isSelected ? Color.blue : Color.fmBorder, lineWidth: isSelected ? 2 : 1)
        )
    }

    private func formatIcon(_ format: String) -> String {
        switch format.lowercased() {
        case "excel": return "doc.richtext"
        case "csv": return "tablecells"
        case "json": return "curlybraces"
        default: return "doc"
        }
    }

    private func formatColor(_ format: String) -> Color {
        switch format.lowercased() {
        case "excel": return Color(hex: "10B981")
        case "csv": return Color(hex: "3B82F6")
        case "json": return Color(hex: "F59E0B")
        default: return Color(hex: "94A3B8")
        }
    }

    private func formatFileSize(_ bytes: Int) -> String {
        let formatter = ByteCountFormatter()
        formatter.allowedUnits = [.useKB, .useMB, .useGB]
        formatter.countStyle = .file
        return formatter.string(fromByteCount: Int64(bytes))
    }

    private func formatDate(_ dateString: String) -> String {
        let formatter = ISO8601DateFormatter()
        if let date = formatter.date(from: dateString) {
            let displayFormatter = DateFormatter()
            displayFormatter.dateFormat = "M/d"
            return displayFormatter.string(from: date)
        }
        return dateString
    }
}

// MARK: - Upload Table Sheet

struct UploadTableSheet: View {
    let projectId: Int
    @ObservedObject var viewModel: TableViewModel
    @Environment(\.dismiss) var dismiss

    var body: some View {
        VStack(spacing: 20) {
            Text("上传表格")
                .font(.system(size: 18, weight: .semibold))

            Text("上传功能暂未实现")
                .font(.system(size: 14))
                .foregroundColor(Color.fmText3)

            Button("关闭") {
                dismiss()
            }
            .padding(.horizontal, 20)
            .padding(.vertical, 10)
            .background(Color.blue)
            .foregroundColor(.white)
            .cornerRadius(8)
        }
        .padding(40)
        .frame(width: 400)
    }
}

// MARK: - Table Detail Sheet

struct TableDetailSheet: View {
    let table: TableService.TableData
    let projectId: Int
    @Environment(\.dismiss) var dismiss

    var body: some View {
        VStack(spacing: 20) {
            Text(table.filename)
                .font(.system(size: 18, weight: .semibold))

            Text("表格详情暂未实现")
                .font(.system(size: 14))
                .foregroundColor(Color.fmText3)

            Button("关闭") {
                dismiss()
            }
            .padding(.horizontal, 20)
            .padding(.vertical, 10)
            .background(Color.blue)
            .foregroundColor(.white)
            .cornerRadius(8)
        }
        .padding(40)
        .frame(width: 500, height: 400)
    }
}
