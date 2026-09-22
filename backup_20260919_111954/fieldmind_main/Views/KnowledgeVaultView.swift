//
//  KnowledgeVaultView.swift
//  FieldMind
//
//  知识库界面 - Obsidian 风格的笔记管理
//

import SwiftUI

struct KnowledgeVaultView: View {
    @StateObject private var vaultService = KnowledgeVaultService.shared
    @State private var selectedNote: Note?
    @State private var searchQuery = ""
    @State private var showingNewNote = false
    @State private var selectedView = 0 // 0: List, 1: Graph, 2: Tags

    var filteredNotes: [Note] {
        vaultService.searchNotes(query: searchQuery)
    }

    var body: some View {
        NavigationSplitView {
            // 侧边栏
            VStack(spacing: 0) {
                // 搜索栏
                SearchBar(text: $searchQuery)
                    .padding(.horizontal)
                    .padding(.vertical, 8)

                // 视图切换
                Picker("", selection: $selectedView) {
                    Label("笔记", systemImage: "doc.text").tag(0)
                    Label("图谱", systemImage: "circle.hexagonpath").tag(1)
                    Label("标签", systemImage: "tag").tag(2)
                }
                .pickerStyle(.segmented)
                .padding(.horizontal)
                .padding(.bottom, 8)

                Divider()

                // 内容区域
                Group {
                    switch selectedView {
                    case 0:
                        NoteListView(notes: filteredNotes, selectedNote: $selectedNote)
                    case 1:
                        GraphView(nodes: vaultService.graphNodes)
                    case 2:
                        TagsView(tags: vaultService.getAllTags(), vaultService: vaultService)
                    default:
                        EmptyView()
                    }
                }
            }
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Button {
                        showingNewNote = true
                    } label: {
                        Label("新建笔记", systemImage: "plus")
                    }
                }
            }
        } detail: {
            // 详情区域
            if let note = selectedNote {
                NoteEditorView(note: note, vaultService: vaultService)
            } else {
                VStack(spacing: 20) {
                    Image(systemName: "note.text")
                        .font(.system(size: 60))
                        .foregroundColor(.secondary)
                    Text("选择或创建一个笔记")
                        .font(.title2)
                        .foregroundColor(.secondary)
                }
            }
        }
        .sheet(isPresented: $showingNewNote) {
            NewNoteSheet(vaultService: vaultService, selectedNote: $selectedNote)
        }
    }
}

// MARK: - 笔记列表视图

struct NoteListView: View {
    let notes: [Note]
    @Binding var selectedNote: Note?

    var body: some View {
        List(notes, selection: $selectedNote) { note in
            NoteRowView(note: note)
                .tag(note)
        }
        .listStyle(.sidebar)
    }
}

struct NoteRowView: View {
    let note: Note

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(note.title)
                .font(.headline)

            Text(note.content)
                .font(.caption)
                .foregroundColor(.secondary)
                .lineLimit(2)

            if !note.tags.isEmpty {
                HStack(spacing: 4) {
                    ForEach(note.tags, id: \.self) { tag in
                        Text("#\(tag)")
                            .font(.caption2)
                            .foregroundColor(.blue)
                    }
                }
            }

            Text(note.updatedAt, style: .relative)
                .font(.caption2)
                .foregroundColor(.secondary)
        }
        .padding(.vertical, 4)
    }
}

// MARK: - 笔记编辑器

struct NoteEditorView: View {
    let note: Note
    let vaultService: KnowledgeVaultService

    @State private var title: String
    @State private var content: String
    @State private var tags: String

    init(note: Note, vaultService: KnowledgeVaultService) {
        self.note = note
        self.vaultService = vaultService
        _title = State(initialValue: note.title)
        _content = State(initialValue: note.content)
        _tags = State(initialValue: note.tags.joined(separator: ", "))
    }

    var body: some View {
        VStack(spacing: 0) {
            // 标题栏
            VStack(spacing: 8) {
                TextField("笔记标题", text: $title)
                    .font(.title)
                    .textFieldStyle(.plain)

                TextField("标签（用逗号分隔）", text: $tags)
                    .font(.caption)
                    .textFieldStyle(.plain)
            }
            .padding()

            Divider()

            // Markdown 编辑器
            HSplitView {
                // 编辑区
                TextEditor(text: $content)
                    .font(.system(.body, design: .monospaced))
                    .padding()

                // 预览区
                ScrollView {
                    MarkdownPreview(content: content)
                        .padding()
                }
            }

            Divider()

            // 反向链接
            if !vaultService.getBacklinks(for: note).isEmpty {
                VStack(alignment: .leading, spacing: 8) {
                    Text("反向链接")
                        .font(.headline)
                        .padding(.horizontal)

                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 8) {
                            ForEach(vaultService.getBacklinks(for: note)) { backlink in
                                Text(backlink.title)
                                    .font(.caption)
                                    .padding(.horizontal, 12)
                                    .padding(.vertical, 6)
                                    .background(Color.blue.opacity(0.1))
                                    .cornerRadius(8)
                            }
                        }
                        .padding(.horizontal)
                    }
                }
                .padding(.vertical, 8)
            }
        }
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Button("保存") {
                    saveNote()
                }
                .keyboardShortcut("s", modifiers: .command)
            }
        }
        .onDisappear {
            saveNote()
        }
    }

    private func saveNote() {
        var updatedNote = note
        updatedNote.title = title
        updatedNote.content = content
        updatedNote.tags = tags.components(separatedBy: ",").map { $0.trimmingCharacters(in: .whitespaces) }.filter { !$0.isEmpty }

        vaultService.updateNote(updatedNote)
        vaultService.updateLinks(for: updatedNote)
    }
}

// MARK: - Markdown 预览

struct MarkdownPreview: View {
    let content: String

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            ForEach(parseMarkdown(), id: \.self) { line in
                if line.hasPrefix("# ") {
                    Text(line.dropFirst(2))
                        .font(.title)
                        .bold()
                } else if line.hasPrefix("## ") {
                    Text(line.dropFirst(3))
                        .font(.title2)
                        .bold()
                } else if line.hasPrefix("### ") {
                    Text(line.dropFirst(4))
                        .font(.title3)
                        .bold()
                } else if line.hasPrefix("- ") {
                    HStack(alignment: .top) {
                        Text("•")
                        Text(line.dropFirst(2))
                    }
                } else if line.contains("[[") && line.contains("]]") {
                    renderLinks(line)
                } else {
                    Text(line)
                }
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    private func parseMarkdown() -> [String] {
        content.components(separatedBy: "\n").filter { !$0.isEmpty }
    }

    private func renderLinks(_ line: String) -> some View {
        let pattern = "\\[\\[([^\\]]+)\\]\\]"
        guard let regex = try? NSRegularExpression(pattern: pattern) else {
            return AnyView(Text(line))
        }

        let matches = regex.matches(in: line, range: NSRange(line.startIndex..., in: line))

        var result: [AnyView] = []
        var lastEnd = line.startIndex

        for match in matches {
            if let range = Range(match.range, in: line),
               let linkRange = Range(match.range(at: 1), in: line) {
                // 添加链接前的文本
                if lastEnd < range.lowerBound {
                    result.append(AnyView(Text(String(line[lastEnd..<range.lowerBound]))))
                }

                // 添加链接
                let linkText = String(line[linkRange])
                result.append(AnyView(
                    Text(linkText)
                        .foregroundColor(.blue)
                        .underline()
                ))

                lastEnd = range.upperBound
            }
        }

        // 添加剩余文本
        if lastEnd < line.endIndex {
            result.append(AnyView(Text(String(line[lastEnd...]))))
        }

        return AnyView(
            HStack(spacing: 0) {
                ForEach(0..<result.count, id: \.self) { index in
                    result[index]
                }
            }
        )
    }
}

// MARK: - 知识图谱视图

struct GraphView: View {
    let nodes: [GraphNode]

    var body: some View {
        GeometryReader { geometry in
            ZStack {
                // 连接线（简化版）
                ForEach(nodes) { node in
                    ForEach(nodes) { otherNode in
                        if node.id != otherNode.id {
                            Path { path in
                                let start = CGPoint(
                                    x: geometry.size.width / 2 + node.x,
                                    y: geometry.size.height / 2 + node.y
                                )
                                let end = CGPoint(
                                    x: geometry.size.width / 2 + otherNode.x,
                                    y: geometry.size.height / 2 + otherNode.y
                                )
                                path.move(to: start)
                                path.addLine(to: end)
                            }
                            .stroke(Color.gray.opacity(0.2), lineWidth: 1)
                        }
                    }
                }

                // 节点
                ForEach(nodes) { node in
                    VStack {
                        Circle()
                            .fill(Color.blue)
                            .frame(width: 40, height: 40)

                        Text(node.title)
                            .font(.caption)
                            .lineLimit(1)
                    }
                    .position(
                        x: geometry.size.width / 2 + node.x,
                        y: geometry.size.height / 2 + node.y
                    )
                }
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

// MARK: - 标签视图

struct TagsView: View {
    let tags: [String]
    let vaultService: KnowledgeVaultService
    @State private var selectedTag: String?

    var body: some View {
        List(tags, id: \.self, selection: $selectedTag) { tag in
            HStack {
                Text("#\(tag)")
                    .font(.headline)

                Spacer()

                Text("\(vaultService.getNotes(withTag: tag).count)")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
    }
}

// MARK: - 新建笔记弹窗

struct NewNoteSheet: View {
    let vaultService: KnowledgeVaultService
    @Binding var selectedNote: Note?
    @Environment(\.dismiss) var dismiss

    @State private var title = ""
    @State private var content = ""
    @State private var tags = ""

    var body: some View {
        NavigationStack {
            Form {
                TextField("标题", text: $title)
                TextField("标签（用逗号分隔）", text: $tags)
                TextEditor(text: $content)
                    .frame(height: 200)
            }
            .navigationTitle("新建笔记")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("取消") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("创建") {
                        let tagArray = tags.components(separatedBy: ",").map { $0.trimmingCharacters(in: .whitespaces) }.filter { !$0.isEmpty }
                        let newNote = vaultService.createNote(title: title, content: content, tags: tagArray)
                        selectedNote = newNote
                        dismiss()
                    }
                    .disabled(title.isEmpty)
                }
            }
        }
        .frame(width: 500, height: 400)
    }
}

// MARK: - 搜索栏

struct SearchBar: View {
    @Binding var text: String

    var body: some View {
        HStack {
            Image(systemName: "magnifyingglass")
                .foregroundColor(.secondary)

            TextField("搜索笔记...", text: $text)
                .textFieldStyle(.plain)

            if !text.isEmpty {
                Button {
                    text = ""
                } label: {
                    Image(systemName: "xmark.circle.fill")
                        .foregroundColor(.secondary)
                }
                .buttonStyle(.plain)
            }
        }
        .padding(8)
        .background(Color.secondary.opacity(0.1))
        .cornerRadius(8)
    }
}

#Preview {
    KnowledgeVaultView()
}
