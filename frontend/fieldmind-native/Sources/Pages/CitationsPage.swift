import SwiftUI

// MARK: - Citations Page (使用真实API)
struct CitationsPage_NEW: View {
    let projectId: Int
    @StateObject private var viewModel = CitationViewModel()
    @State private var selectedCitations: Set<Int> = []
    @State private var showingAddSheet = false
    @State private var showingExportSheet = false
    @State private var showingDetailSheet = false
    @State private var selectedCitationForDetail: CitationService.CitationResponse?

    let types = ["全部类型", "学术论文", "书籍", "报告", "网页", "其他"]
    let sortOptions = ["最新添加", "最早添加", "标题A-Z", "标题Z-A", "引用次数"]

    var body: some View {
        VStack(spacing: 0) {
            // Top toolbar
            toolbarView

            // Main content
            if viewModel.isLoadingCitations {
                loadingView
            } else if let error = viewModel.errorMessage {
                errorView(error)
            } else if viewModel.citations.isEmpty {
                emptyView
            } else {
                citationListView
            }

            // Batch action bar
            if !selectedCitations.isEmpty {
                batchActionBar
            }
        }
        .sheet(isPresented: $showingAddSheet) {
            addCitationSheet
        }
        .sheet(isPresented: $showingDetailSheet) {
            if let citation = selectedCitationForDetail {
                citationDetailSheet(citation: citation)
            }
        }
        .sheet(isPresented: $showingExportSheet) {
            exportSheet
        }
        .task {
            await viewModel.loadAllData(projectId: projectId)
        }
    }

    // MARK: - Toolbar
    private var toolbarView: some View {
        HStack(spacing: 12) {
            // Search
            HStack(spacing: 8) {
                Image(systemName: "magnifyingglass")
                    .font(.system(size: 13))
                    .foregroundColor(Color(hex: "94A3B8"))

                TextField("搜索引用...", text: $viewModel.searchText)
                    .textFieldStyle(PlainTextFieldStyle())
                    .font(.system(size: 13))
                    .onChange(of: viewModel.searchText) { _ in
                        Task {
                            try? await Task.sleep(nanoseconds: 500_000_000)  // 500ms debounce
                            await viewModel.loadCitations(projectId: projectId)
                        }
                    }
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
            .background(Color(hex: "F8FAFC"))
            .cornerRadius(8)
            .frame(width: 280)

            // Type filter
            Menu {
                ForEach(types, id: \.self) { type in
                    Button(action: {
                        viewModel.selectedType = type
                        Task {
                            await viewModel.loadCitations(projectId: projectId)
                        }
                    }) {
                        HStack {
                            Text(type)
                            if viewModel.selectedType == type {
                                Image(systemName: "checkmark")
                            }
                        }
                    }
                }
            } label: {
                HStack(spacing: 6) {
                    Image(systemName: "doc.text")
                        .font(.system(size: 12))
                    Text(viewModel.selectedType)
                        .font(.system(size: 13))
                    Image(systemName: "chevron.down")
                        .font(.system(size: 10))
                }
                .foregroundColor(Color(hex: "475569"))
                .padding(.horizontal, 12)
                .padding(.vertical, 8)
                .background(Color.white)
                .cornerRadius(8)
                .overlay(
                    RoundedRectangle(cornerRadius: 8)
                        .stroke(Color(hex: "E2E8F0"), lineWidth: 1)
                )
            }

            // Sort
            Menu {
                ForEach(sortOptions, id: \.self) { option in
                    Button(action: {
                        viewModel.selectedSort = option
                        Task {
                            await viewModel.loadCitations(projectId: projectId)
                        }
                    }) {
                        HStack {
                            Text(option)
                            if viewModel.selectedSort == option {
                                Image(systemName: "checkmark")
                            }
                        }
                    }
                }
            } label: {
                HStack(spacing: 6) {
                    Image(systemName: "arrow.up.arrow.down")
                        .font(.system(size: 12))
                    Text(viewModel.selectedSort)
                        .font(.system(size: 13))
                    Image(systemName: "chevron.down")
                        .font(.system(size: 10))
                }
                .foregroundColor(Color(hex: "475569"))
                .padding(.horizontal, 12)
                .padding(.vertical, 8)
                .background(Color.white)
                .cornerRadius(8)
                .overlay(
                    RoundedRectangle(cornerRadius: 8)
                        .stroke(Color(hex: "E2E8F0"), lineWidth: 1)
                )
            }

            Spacer()

            // Stats display
            if let stats = viewModel.stats {
                HStack(spacing: 16) {
                    StatBadge_Citation(label: "总计", value: "\(stats.totalCitations)", color: "3B82F6")
                    StatBadge_Citation(label: "本周新增", value: "\(stats.recentAdditions)", color: "10B981")
                }
            }

            // Add button
            Button(action: { showingAddSheet = true }) {
                HStack(spacing: 6) {
                    Image(systemName: "plus")
                        .font(.system(size: 12, weight: .medium))
                    Text("添加引用")
                        .font(.system(size: 13, weight: .medium))
                }
                .foregroundColor(.white)
                .padding(.horizontal, 16)
                .padding(.vertical, 8)
                .background(Color(hex: "3B82F6"))
                .cornerRadius(8)
            }
            .buttonStyle(PlainButtonStyle())

            // Export button
            Button(action: { showingExportSheet = true }) {
                Image(systemName: "square.and.arrow.up")
                    .font(.system(size: 14))
                    .foregroundColor(Color(hex: "475569"))
                    .padding(8)
                    .background(Color.white)
                    .cornerRadius(8)
                    .overlay(
                        RoundedRectangle(cornerRadius: 8)
                            .stroke(Color(hex: "E2E8F0"), lineWidth: 1)
                    )
            }
            .buttonStyle(PlainButtonStyle())
        }
        .padding(16)
        .background(Color(hex: "F8FAFC"))
    }

    // MARK: - Loading View
    private var loadingView: some View {
        VStack(spacing: 16) {
            ProgressView()
                .scaleEffect(1.5)
            Text("加载引用中...")
                .font(.system(size: 14))
                .foregroundColor(Color(hex: "64748B"))
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    // MARK: - Error View
    private func errorView(_ message: String) -> some View {
        VStack(spacing: 16) {
            Image(systemName: "exclamationmark.triangle")
                .font(.system(size: 48))
                .foregroundColor(Color(hex: "EF4444"))

            Text(message)
                .font(.system(size: 14))
                .foregroundColor(Color(hex: "64748B"))
                .multilineTextAlignment(.center)

            Button(action: {
                Task {
                    await viewModel.loadAllData(projectId: projectId)
                }
            }) {
                Text("重试")
                    .font(.system(size: 13, weight: .medium))
                    .foregroundColor(.white)
                    .padding(.horizontal, 20)
                    .padding(.vertical, 8)
                    .background(Color(hex: "3B82F6"))
                    .cornerRadius(8)
            }
            .buttonStyle(PlainButtonStyle())
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    // MARK: - Export Functions
    private func exportAsBibTeX(citations: [CitationService.CitationResponse]) {
        var bibtex = ""

        for citation in citations {
            // 如果有bibtex字段直接使用，否则生成
            if let existingBibtex = citation.bibtex, !existingBibtex.isEmpty {
                bibtex += existingBibtex + "\n\n"
            } else {
                let key = "citation\(citation.id)"
                let typeMap: [String: String] = [
                    "journal": "article",
                    "book": "book",
                    "conference": "inproceedings",
                    "thesis": "phdthesis",
                    "report": "techreport",
                    "webpage": "misc"
                ]
                let entryType = typeMap[citation.citationType.lowercased()] ?? "misc"

                bibtex += "@\(entryType){\(key),\n"
                bibtex += "  title = {\(citation.title)},\n"
                bibtex += "  author = {\(citation.authors.joined(separator: " and "))},\n"
                if let year = citation.year {
                    bibtex += "  year = {\(year)},\n"
                }
                if let publication = citation.publication {
                    bibtex += "  journal = {\(publication)},\n"
                }
                if let publisher = citation.publisher {
                    bibtex += "  publisher = {\(publisher)},\n"
                }
                if let doi = citation.doi {
                    bibtex += "  doi = {\(doi)},\n"
                }
                if let isbn = citation.isbn {
                    bibtex += "  isbn = {\(isbn)},\n"
                }
                if let url = citation.url {
                    bibtex += "  url = {\(url)},\n"
                }
                bibtex += "}\n\n"
            }
        }

        saveToFile(content: bibtex, filename: "citations.bib", fileType: "bib")
    }

    private func exportAsRIS(citations: [CitationService.CitationResponse]) {
        var ris = ""

        for citation in citations {
            let typeMap: [String: String] = [
                "journal": "JOUR",
                "book": "BOOK",
                "conference": "CONF",
                "thesis": "THES",
                "report": "RPRT",
                "webpage": "ELEC"
            ]
            let risType = typeMap[citation.citationType.lowercased()] ?? "GEN"

            ris += "TY  - \(risType)\n"
            ris += "TI  - \(citation.title)\n"

            for author in citation.authors {
                ris += "AU  - \(author)\n"
            }

            if let year = citation.year {
                ris += "PY  - \(year)\n"
            }
            if let publication = citation.publication {
                ris += "JO  - \(publication)\n"
            }
            if let publisher = citation.publisher {
                ris += "PB  - \(publisher)\n"
            }
            if let doi = citation.doi {
                ris += "DO  - \(doi)\n"
            }
            if let url = citation.url {
                ris += "UR  - \(url)\n"
            }
            if let abstract = citation.abstract {
                ris += "AB  - \(abstract)\n"
            }
            ris += "ER  - \n\n"
        }

        saveToFile(content: ris, filename: "citations.ris", fileType: "ris")
    }

    private func exportAsCSV(citations: [CitationService.CitationResponse]) {
        var csv = "ID,标题,作者,年份,出版物,出版社,DOI,类型,引用次数\n"

        for citation in citations {
            let id = "\(citation.id)"
            let title = escapeCSV(citation.title)
            let authors = escapeCSV(citation.authors.joined(separator: "; "))
            let year = citation.year ?? ""
            let publication = escapeCSV(citation.publication ?? "")
            let publisher = escapeCSV(citation.publisher ?? "")
            let doi = citation.doi ?? ""
            let type = citation.citationType
            let cited = "\(citation.citedCount)"

            csv += "\(id),\(title),\(authors),\(year),\(publication),\(publisher),\(doi),\(type),\(cited)\n"
        }

        saveToFile(content: csv, filename: "citations.csv", fileType: "csv")
    }

    private func escapeCSV(_ text: String) -> String {
        let escaped = text.replacingOccurrences(of: "\"", with: "\"\"")
        return "\"\(escaped)\""
    }

    private func saveToFile(content: String, filename: String, fileType: String) {
        let panel = NSSavePanel()
        panel.nameFieldStringValue = filename
        panel.allowedContentTypes = [.init(filenameExtension: fileType)!]
        panel.canCreateDirectories = true

        if panel.runModal() == .OK, let url = panel.url {
            do {
                try content.write(to: url, atomically: true, encoding: .utf8)
            } catch {
                print("导出失败: \(error)")
            }
        }
    }

    // MARK: - Empty View
    private var emptyView: some View {
        VStack(spacing: 20) {
            Image(systemName: "doc.text")
                .font(.system(size: 64))
                .foregroundColor(Color(hex: "CBD5E1"))

            VStack(spacing: 8) {
                Text("暂无引用")
                    .font(.system(size: 16, weight: .medium))
                    .foregroundColor(Color(hex: "1E293B"))

                Text("点击\"添加引用\"按钮开始添加文献引用")
                    .font(.system(size: 14))
                    .foregroundColor(Color(hex: "64748B"))
            }

            Button(action: { showingAddSheet = true }) {
                HStack(spacing: 6) {
                    Image(systemName: "plus")
                        .font(.system(size: 12, weight: .medium))
                    Text("添加引用")
                        .font(.system(size: 13, weight: .medium))
                }
                .foregroundColor(.white)
                .padding(.horizontal, 20)
                .padding(.vertical, 10)
                .background(Color(hex: "3B82F6"))
                .cornerRadius(8)
            }
            .buttonStyle(PlainButtonStyle())
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    // MARK: - Citation List
    private var citationListView: some View {
        ScrollView {
            LazyVStack(spacing: 12) {
                ForEach(viewModel.citations) { citation in
                    CitationCard(
                        citation: citation,
                        isSelected: selectedCitations.contains(citation.id),
                        onTap: {
                            selectedCitationForDetail = citation
                            showingDetailSheet = true
                        },
                        onToggleSelect: {
                            if selectedCitations.contains(citation.id) {
                                selectedCitations.remove(citation.id)
                            } else {
                                selectedCitations.insert(citation.id)
                            }
                        }
                    )
                }
            }
            .padding(16)
        }
    }

    // MARK: - Batch Action Bar
    private var batchActionBar: some View {
        HStack {
            Text("已选择 \(selectedCitations.count) 项")
                .font(.system(size: 14, weight: .medium))
                .foregroundColor(Color(hex: "1E293B"))

            Spacer()

            Button(action: {
                selectedCitations.removeAll()
            }) {
                Text("取消选择")
                    .font(.system(size: 13))
                    .foregroundColor(Color(hex: "64748B"))
            }
            .buttonStyle(PlainButtonStyle())

            Button(action: {
                Task {
                    let ids = Array(selectedCitations)
                    let success = await viewModel.batchDeleteCitations(citationIds: ids)
                    if success {
                        selectedCitations.removeAll()
                    }
                }
            }) {
                HStack(spacing: 6) {
                    Image(systemName: "trash")
                        .font(.system(size: 12))
                    Text("删除")
                        .font(.system(size: 13, weight: .medium))
                }
                .foregroundColor(.white)
                .padding(.horizontal, 16)
                .padding(.vertical, 8)
                .background(Color(hex: "EF4444"))
                .cornerRadius(8)
            }
            .buttonStyle(PlainButtonStyle())
        }
        .padding(16)
        .background(Color(hex: "FEF3C7"))
        .overlay(
            Rectangle()
                .fill(Color(hex: "F59E0B"))
                .frame(height: 2),
            alignment: .top
        )
    }

    // MARK: - Add Citation Sheet
    private var addCitationSheet: some View {
        AddCitationForm(projectId: projectId, onSave: { title, authors, year, publication, publisher, doi, url, abstract, notes, citationType, tags in
            Task {
                let success = await viewModel.createCitation(
                    title: title,
                    authors: authors,
                    year: year,
                    publication: publication,
                    publisher: publisher,
                    doi: doi,
                    url: url,
                    abstract: abstract,
                    notes: notes,
                    citationType: citationType,
                    tags: tags,
                    projectId: projectId
                )
                if success {
                    showingAddSheet = false
                }
            }
        }, onCancel: {
            showingAddSheet = false
        })
    }

    // MARK: - Citation Detail Sheet
    private func citationDetailSheet(citation: CitationService.CitationResponse) -> some View {
        CitationDetailView(
            citation: citation,
            onDelete: {
                Task {
                    let success = await viewModel.deleteCitation(citationId: citation.id)
                    if success {
                        showingDetailSheet = false
                    }
                }
            },
            onClose: {
                showingDetailSheet = false
            }
        )
    }

    // MARK: - Export Sheet
    private var exportSheet: some View {
        VStack(spacing: 20) {
            Text("导出引用")
                .font(.system(size: 18, weight: .semibold))
                .foregroundColor(Color(hex: "1E293B"))

            VStack(spacing: 12) {
                ExportOptionButton(icon: "doc.text", title: "BibTeX格式", subtitle: "适用于LaTeX文档") {
                    exportAsBibTeX(citations: selectedCitations.isEmpty ? viewModel.citations : selectedCitations.compactMap { id in viewModel.citations.first { $0.id == id } })
                    showingExportSheet = false
                }

                ExportOptionButton(icon: "doc.richtext", title: "RIS格式", subtitle: "适用于EndNote、Zotero等") {
                    exportAsRIS(citations: selectedCitations.isEmpty ? viewModel.citations : selectedCitations.compactMap { id in viewModel.citations.first { $0.id == id } })
                    showingExportSheet = false
                }

                ExportOptionButton(icon: "tablecells", title: "CSV格式", subtitle: "适用于Excel表格") {
                    exportAsCSV(citations: selectedCitations.isEmpty ? viewModel.citations : selectedCitations.compactMap { id in viewModel.citations.first { $0.id == id } })
                    showingExportSheet = false
                }
            }

            Button(action: {
                showingExportSheet = false
            }) {
                Text("取消")
                    .font(.system(size: 14))
                    .foregroundColor(Color(hex: "64748B"))
            }
            .buttonStyle(PlainButtonStyle())
        }
        .padding(24)
        .frame(width: 400)
    }
}

// MARK: - Supporting Components

struct CitationCard: View {
    let citation: CitationService.CitationResponse
    let isSelected: Bool
    let onTap: () -> Void
    let onToggleSelect: () -> Void

    var body: some View {
        HStack(spacing: 0) {
            // Selection checkbox
            Button(action: onToggleSelect) {
                Image(systemName: isSelected ? "checkmark.square.fill" : "square")
                    .font(.system(size: 18))
                    .foregroundColor(isSelected ? Color(hex: "3B82F6") : Color(hex: "CBD5E1"))
            }
            .buttonStyle(PlainButtonStyle())
            .padding(.trailing, 12)

            // Type icon
            VStack {
                Image(systemName: citationTypeIcon(citation.citationType))
                    .font(.system(size: 20))
                    .foregroundColor(Color(hex: citationTypeColor(citation.citationType)))
                    .frame(width: 40, height: 40)
                    .background(Color(hex: citationTypeColor(citation.citationType)).opacity(0.1))
                    .cornerRadius(8)
                Spacer()
            }
            .padding(.trailing, 12)

            // Content
            VStack(alignment: .leading, spacing: 8) {
                // Title
                Text(citation.title)
                    .font(.system(size: 15, weight: .semibold))
                    .foregroundColor(Color(hex: "1E293B"))
                    .lineLimit(2)

                // Authors and year
                HStack(spacing: 8) {
                    if !citation.authors.isEmpty {
                        Text(citation.authors.joined(separator: ", "))
                            .font(.system(size: 13))
                            .foregroundColor(Color(hex: "64748B"))
                            .lineLimit(1)
                    }
                    if let year = citation.year {
                        Text("(\(year))")
                            .font(.system(size: 13))
                            .foregroundColor(Color(hex: "64748B"))
                    }
                }

                // Publication
                if let publication = citation.publication, !publication.isEmpty {
                    Text(publication)
                        .font(.system(size: 12))
                        .foregroundColor(Color(hex: "94A3B8"))
                        .lineLimit(1)
                }

                // Tags
                if !citation.tags.isEmpty {
                    HStack(spacing: 6) {
                        ForEach(citation.tags.prefix(3), id: \.self) { tag in
                            Text(tag)
                                .font(.system(size: 11))
                                .foregroundColor(Color(hex: "64748B"))
                                .padding(.horizontal, 8)
                                .padding(.vertical, 4)
                                .background(Color(hex: "F1F5F9"))
                                .cornerRadius(4)
                        }
                        if citation.tags.count > 3 {
                            Text("+\(citation.tags.count - 3)")
                                .font(.system(size: 11))
                                .foregroundColor(Color(hex: "94A3B8"))
                        }
                    }
                }

                // Metadata row
                HStack(spacing: 16) {
                    if citation.citedCount > 0 {
                        HStack(spacing: 4) {
                            Image(systemName: "quote.bubble")
                                .font(.system(size: 11))
                            Text("引用 \(citation.citedCount)")
                                .font(.system(size: 12))
                        }
                        .foregroundColor(Color(hex: "64748B"))
                    }

                    Text(formatDate(citation.addedAt))
                        .font(.system(size: 12))
                        .foregroundColor(Color(hex: "94A3B8"))
                }
            }

            Spacer()

            // Action button
            Button(action: onTap) {
                Image(systemName: "chevron.right")
                    .font(.system(size: 14))
                    .foregroundColor(Color(hex: "CBD5E1"))
            }
            .buttonStyle(PlainButtonStyle())
        }
        .padding(16)
        .background(Color.white)
        .cornerRadius(12)
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(isSelected ? Color(hex: "3B82F6") : Color(hex: "E2E8F0"), lineWidth: isSelected ? 2 : 1)
        )
        .shadow(color: Color.black.opacity(0.04), radius: 2, x: 0, y: 1)
    }

    private func citationTypeIcon(_ type: String) -> String {
        switch type {
        case "学术论文": return "doc.text"
        case "书籍": return "book.closed"
        case "报告": return "doc.richtext"
        case "网页": return "globe"
        default: return "doc"
        }
    }

    private func citationTypeColor(_ type: String) -> String {
        switch type {
        case "学术论文": return "3B82F6"
        case "书籍": return "10B981"
        case "报告": return "F59E0B"
        case "网页": return "8B5CF6"
        default: return "6B7280"
        }
    }

    private func formatDate(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd"
        return formatter.string(from: date)
    }
}

struct StatBadge_Citation: View {
    let label: String
    let value: String
    let color: String

    var body: some View {
        HStack(spacing: 6) {
            Text(label)
                .font(.system(size: 12))
                .foregroundColor(Color(hex: "64748B"))
            Text(value)
                .font(.system(size: 14, weight: .semibold))
                .foregroundColor(Color(hex: color))
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 6)
        .background(Color.white)
        .cornerRadius(6)
        .overlay(
            RoundedRectangle(cornerRadius: 6)
                .stroke(Color(hex: "E2E8F0"), lineWidth: 1)
        )
    }
}

struct AddCitationForm: View {
    let projectId: Int
    let onSave: (String, [String], String?, String?, String?, String?, String?, String?, String?, String, [String]) -> Void
    let onCancel: () -> Void

    @State private var title = ""
    @State private var authorsText = ""
    @State private var year = ""
    @State private var publication = ""
    @State private var publisher = ""
    @State private var doi = ""
    @State private var url = ""
    @State private var abstract = ""
    @State private var notes = ""
    @State private var citationType = "学术论文"
    @State private var tagsText = ""

    let types = ["学术论文", "书籍", "报告", "网页", "其他"]

    var body: some View {
        VStack(spacing: 0) {
            // Header
            HStack {
                Text("添加引用")
                    .font(.system(size: 18, weight: .semibold))
                    .foregroundColor(Color(hex: "1E293B"))
                Spacer()
                Button(action: onCancel) {
                    Image(systemName: "xmark")
                        .font(.system(size: 14))
                        .foregroundColor(Color(hex: "64748B"))
                }
                .buttonStyle(PlainButtonStyle())
            }
            .padding(20)

            Divider()

            // Form
            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    FormField_Citation(label: "标题*", placeholder: "输入标题", text: $title)
                    FormField_Citation(label: "作者", placeholder: "多个作者用逗号分隔", text: $authorsText)

                    HStack(spacing: 12) {
                        FormField_Citation(label: "年份", placeholder: "2024", text: $year)

                        VStack(alignment: .leading, spacing: 6) {
                            Text("类型*")
                                .font(.system(size: 13, weight: .medium))
                                .foregroundColor(Color(hex: "475569"))

                            Menu {
                                ForEach(types, id: \.self) { type in
                                    Button(action: { citationType = type }) {
                                        Text(type)
                                    }
                                }
                            } label: {
                                HStack {
                                    Text(citationType)
                                        .font(.system(size: 14))
                                        .foregroundColor(Color(hex: "1E293B"))
                                    Spacer()
                                    Image(systemName: "chevron.down")
                                        .font(.system(size: 12))
                                        .foregroundColor(Color(hex: "94A3B8"))
                                }
                                .padding(10)
                                .background(Color.white)
                                .cornerRadius(8)
                                .overlay(
                                    RoundedRectangle(cornerRadius: 8)
                                        .stroke(Color(hex: "E2E8F0"), lineWidth: 1)
                                )
                            }
                        }
                    }

                    FormField_Citation(label: "出版物/期刊", placeholder: "期刊名称或会议名称", text: $publication)
                    FormField_Citation(label: "出版社", placeholder: "出版社名称", text: $publisher)
                    FormField_Citation(label: "DOI", placeholder: "10.1000/xyz123", text: $doi)
                    FormField_Citation(label: "URL", placeholder: "https://example.com", text: $url)
                    FormField_Citation(label: "摘要", placeholder: "输入摘要", text: $abstract, isMultiline: true)
                    FormField_Citation(label: "笔记", placeholder: "个人笔记", text: $notes, isMultiline: true)
                    FormField_Citation(label: "标签", placeholder: "多个标签用逗号分隔", text: $tagsText)
                }
                .padding(20)
            }

            Divider()

            // Footer
            HStack(spacing: 12) {
                Button(action: onCancel) {
                    Text("取消")
                        .font(.system(size: 14))
                        .foregroundColor(Color(hex: "64748B"))
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 10)
                        .background(Color(hex: "F1F5F9"))
                        .cornerRadius(8)
                }
                .buttonStyle(PlainButtonStyle())

                Button(action: {
                    let authors = authorsText.split(separator: ",").map { $0.trimmingCharacters(in: .whitespaces) }
                    let tags = tagsText.split(separator: ",").map { $0.trimmingCharacters(in: .whitespaces) }
                    onSave(
                        title,
                        authors,
                        year.isEmpty ? nil : year,
                        publication.isEmpty ? nil : publication,
                        publisher.isEmpty ? nil : publisher,
                        doi.isEmpty ? nil : doi,
                        url.isEmpty ? nil : url,
                        abstract.isEmpty ? nil : abstract,
                        notes.isEmpty ? nil : notes,
                        citationType,
                        tags
                    )
                }) {
                    Text("保存")
                        .font(.system(size: 14, weight: .medium))
                        .foregroundColor(.white)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 10)
                        .background(title.isEmpty ? Color(hex: "CBD5E1") : Color(hex: "3B82F6"))
                        .cornerRadius(8)
                }
                .buttonStyle(PlainButtonStyle())
                .disabled(title.isEmpty)
            }
            .padding(20)
        }
        .frame(width: 600, height: 700)
    }
}

struct FormField_Citation: View {
    let label: String
    let placeholder: String
    @Binding var text: String
    var isMultiline: Bool = false

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(label)
                .font(.system(size: 13, weight: .medium))
                .foregroundColor(Color(hex: "475569"))

            if isMultiline {
                TextEditor(text: $text)
                    .font(.system(size: 14))
                    .frame(height: 80)
                    .padding(8)
                    .background(Color.white)
                    .cornerRadius(8)
                    .overlay(
                        RoundedRectangle(cornerRadius: 8)
                            .stroke(Color(hex: "E2E8F0"), lineWidth: 1)
                    )
            } else {
                TextField(placeholder, text: $text)
                    .textFieldStyle(PlainTextFieldStyle())
                    .font(.system(size: 14))
                    .padding(10)
                    .background(Color.white)
                    .cornerRadius(8)
                    .overlay(
                        RoundedRectangle(cornerRadius: 8)
                            .stroke(Color(hex: "E2E8F0"), lineWidth: 1)
                    )
            }
        }
    }
}

struct CitationDetailView: View {
    let citation: CitationService.CitationResponse
    let onDelete: () -> Void
    let onClose: () -> Void

    var body: some View {
        VStack(spacing: 0) {
            // Header
            HStack {
                Text("引用详情")
                    .font(.system(size: 18, weight: .semibold))
                    .foregroundColor(Color(hex: "1E293B"))
                Spacer()
                Button(action: onClose) {
                    Image(systemName: "xmark")
                        .font(.system(size: 14))
                        .foregroundColor(Color(hex: "64748B"))
                }
                .buttonStyle(PlainButtonStyle())
            }
            .padding(20)

            Divider()

            // Content
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    // Title
                    VStack(alignment: .leading, spacing: 8) {
                        Text("标题")
                            .font(.system(size: 12, weight: .medium))
                            .foregroundColor(Color(hex: "64748B"))
                        Text(citation.title)
                            .font(.system(size: 16, weight: .semibold))
                            .foregroundColor(Color(hex: "1E293B"))
                    }

                    // Authors
                    if !citation.authors.isEmpty {
                        VStack(alignment: .leading, spacing: 8) {
                            Text("作者")
                                .font(.system(size: 12, weight: .medium))
                                .foregroundColor(Color(hex: "64748B"))
                            Text(citation.authors.joined(separator: ", "))
                                .font(.system(size: 14))
                                .foregroundColor(Color(hex: "1E293B"))
                        }
                    }

                    // Meta info
                    HStack(spacing: 20) {
                        if let year = citation.year {
                            DetailMetaItem(label: "年份", value: year)
                        }
                        DetailMetaItem(label: "类型", value: citation.citationType)
                    }

                    // Publication
                    if let publication = citation.publication {
                        VStack(alignment: .leading, spacing: 8) {
                            Text("出版物")
                                .font(.system(size: 12, weight: .medium))
                                .foregroundColor(Color(hex: "64748B"))
                            Text(publication)
                                .font(.system(size: 14))
                                .foregroundColor(Color(hex: "1E293B"))
                        }
                    }

                    // DOI
                    if let doi = citation.doi {
                        VStack(alignment: .leading, spacing: 8) {
                            Text("DOI")
                                .font(.system(size: 12, weight: .medium))
                                .foregroundColor(Color(hex: "64748B"))
                            Text(doi)
                                .font(.system(size: 14, design: .monospaced))
                                .foregroundColor(Color(hex: "3B82F6"))
                        }
                    }

                    // URL
                    if let url = citation.url {
                        VStack(alignment: .leading, spacing: 8) {
                            Text("链接")
                                .font(.system(size: 12, weight: .medium))
                                .foregroundColor(Color(hex: "64748B"))
                            Text(url)
                                .font(.system(size: 14))
                                .foregroundColor(Color(hex: "3B82F6"))
                                .lineLimit(1)
                        }
                    }

                    // Abstract
                    if let abstract = citation.abstract {
                        VStack(alignment: .leading, spacing: 8) {
                            Text("摘要")
                                .font(.system(size: 12, weight: .medium))
                                .foregroundColor(Color(hex: "64748B"))
                            Text(abstract)
                                .font(.system(size: 14))
                                .foregroundColor(Color(hex: "475569"))
                        }
                    }

                    // Notes
                    if let notes = citation.notes {
                        VStack(alignment: .leading, spacing: 8) {
                            Text("笔记")
                                .font(.system(size: 12, weight: .medium))
                                .foregroundColor(Color(hex: "64748B"))
                            Text(notes)
                                .font(.system(size: 14))
                                .foregroundColor(Color(hex: "475569"))
                        }
                    }

                    // Tags
                    if !citation.tags.isEmpty {
                        VStack(alignment: .leading, spacing: 8) {
                            Text("标签")
                                .font(.system(size: 12, weight: .medium))
                                .foregroundColor(Color(hex: "64748B"))
                            HStack(spacing: 8) {
                                ForEach(citation.tags, id: \.self) { tag in
                                    Text(tag)
                                        .font(.system(size: 12))
                                        .foregroundColor(Color(hex: "64748B"))
                                        .padding(.horizontal, 10)
                                        .padding(.vertical, 6)
                                        .background(Color(hex: "F1F5F9"))
                                        .cornerRadius(6)
                                }
                            }
                        }
                    }

                    // Stats
                    HStack(spacing: 20) {
                        DetailMetaItem(label: "引用次数", value: "\(citation.citedCount)")
                        DetailMetaItem(label: "添加时间", value: formatDate(citation.addedAt))
                    }
                }
                .padding(20)
            }

            Divider()

            // Footer
            HStack(spacing: 12) {
                Button(action: onDelete) {
                    HStack(spacing: 6) {
                        Image(systemName: "trash")
                            .font(.system(size: 12))
                        Text("删除")
                            .font(.system(size: 14))
                    }
                    .foregroundColor(Color(hex: "EF4444"))
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 10)
                    .background(Color(hex: "FEF2F2"))
                    .cornerRadius(8)
                }
                .buttonStyle(PlainButtonStyle())

                Button(action: onClose) {
                    Text("关闭")
                        .font(.system(size: 14, weight: .medium))
                        .foregroundColor(.white)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 10)
                        .background(Color(hex: "3B82F6"))
                        .cornerRadius(8)
                }
                .buttonStyle(PlainButtonStyle())
            }
            .padding(20)
        }
        .frame(width: 600, height: 700)
    }

    private func formatDate(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd HH:mm"
        return formatter.string(from: date)
    }
}

struct DetailMetaItem: View {
    let label: String
    let value: String

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(label)
                .font(.system(size: 11))
                .foregroundColor(Color(hex: "94A3B8"))
            Text(value)
                .font(.system(size: 13, weight: .medium))
                .foregroundColor(Color(hex: "1E293B"))
        }
    }
}

struct ExportOptionButton: View {
    let icon: String
    let title: String
    let subtitle: String
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: 12) {
                Image(systemName: icon)
                    .font(.system(size: 20))
                    .foregroundColor(Color(hex: "3B82F6"))
                    .frame(width: 40, height: 40)
                    .background(Color(hex: "EFF6FF"))
                    .cornerRadius(8)

                VStack(alignment: .leading, spacing: 4) {
                    Text(title)
                        .font(.system(size: 14, weight: .medium))
                        .foregroundColor(Color(hex: "1E293B"))
                    Text(subtitle)
                        .font(.system(size: 12))
                        .foregroundColor(Color(hex: "64748B"))
                }

                Spacer()

                Image(systemName: "chevron.right")
                    .font(.system(size: 12))
                    .foregroundColor(Color(hex: "CBD5E1"))
            }
            .padding(16)
            .background(Color.white)
            .cornerRadius(12)
            .overlay(
                RoundedRectangle(cornerRadius: 12)
                    .stroke(Color(hex: "E2E8F0"), lineWidth: 1)
            )
        }
        .buttonStyle(PlainButtonStyle())
    }
}
