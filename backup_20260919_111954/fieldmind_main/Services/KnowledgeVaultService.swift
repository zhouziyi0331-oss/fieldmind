//
//  KnowledgeVaultService.swift
//  FieldMind
//
//  知识库服务 - Obsidian 风格的笔记和知识管理
//

import Foundation
import Combine

/// 笔记模型
struct Note: Identifiable, Codable {
    let id: UUID
    var title: String
    var content: String
    var tags: [String]
    var createdAt: Date
    var updatedAt: Date
    var folderPath: String
    var linkedNotes: [UUID] // 双向链接

    init(title: String, content: String, folderPath: String = "/", tags: [String] = []) {
        self.id = UUID()
        self.title = title
        self.content = content
        self.folderPath = folderPath
        self.tags = tags
        self.createdAt = Date()
        self.updatedAt = Date()
        self.linkedNotes = []
    }
}

/// 知识图谱节点
struct GraphNode: Identifiable {
    let id: UUID
    let title: String
    let connections: Int
    let x: Double
    let y: Double
}

/// 知识库服务
class KnowledgeVaultService: ObservableObject {
    static let shared = KnowledgeVaultService()

    @Published var notes: [Note] = []
    @Published var folders: [String] = ["/"]
    @Published var graphNodes: [GraphNode] = []

    private let vaultPath: String
    private var cancellables = Set<AnyCancellable>()

    init() {
        let homeDir = FileManager.default.homeDirectoryForCurrentUser.path
        self.vaultPath = "\(homeDir)/FieldMind/vault"

        // 创建知识库目录
        try? FileManager.default.createDirectory(atPath: vaultPath, withIntermediateDirectories: true)

        loadNotes()
    }

    // MARK: - 笔记管理

    /// 创建新笔记
    func createNote(title: String, content: String, folderPath: String = "/", tags: [String] = []) -> Note {
        let note = Note(title: title, content: content, folderPath: folderPath, tags: tags)
        notes.append(note)
        saveNote(note)
        updateGraph()
        return note
    }

    /// 更新笔记
    func updateNote(_ note: Note) {
        if let index = notes.firstIndex(where: { $0.id == note.id }) {
            var updatedNote = note
            updatedNote.updatedAt = Date()
            notes[index] = updatedNote
            saveNote(updatedNote)
            updateGraph()
        }
    }

    /// 删除笔记
    func deleteNote(_ note: Note) {
        notes.removeAll { $0.id == note.id }
        deleteNoteFile(note)
        updateGraph()
    }

    /// 搜索笔记
    func searchNotes(query: String) -> [Note] {
        guard !query.isEmpty else { return notes }

        return notes.filter { note in
            note.title.localizedCaseInsensitiveContains(query) ||
            note.content.localizedCaseInsensitiveContains(query) ||
            note.tags.contains { $0.localizedCaseInsensitiveContains(query) }
        }
    }

    // MARK: - 双向链接

    /// 提取笔记中的链接 [[Note Title]]
    func extractLinks(from content: String) -> [String] {
        let pattern = "\\[\\[([^\\]]+)\\]\\]"
        guard let regex = try? NSRegularExpression(pattern: pattern) else { return [] }

        let matches = regex.matches(in: content, range: NSRange(content.startIndex..., in: content))
        return matches.compactMap { match in
            guard let range = Range(match.range(at: 1), in: content) else { return nil }
            return String(content[range])
        }
    }

    /// 更新笔记的双向链接
    func updateLinks(for note: Note) {
        let linkedTitles = extractLinks(from: note.content)

        var updatedNote = note
        updatedNote.linkedNotes = notes
            .filter { linkedTitles.contains($0.title) }
            .map { $0.id }

        updateNote(updatedNote)
    }

    /// 获取反向链接（哪些笔记链接到当前笔记）
    func getBacklinks(for note: Note) -> [Note] {
        return notes.filter { $0.linkedNotes.contains(note.id) }
    }

    // MARK: - 知识图谱

    /// 构建知识图谱
    func updateGraph() {
        var nodes: [GraphNode] = []
        let radius: Double = 300

        for (index, note) in notes.enumerated() {
            let angle = Double(index) * (2 * .pi / Double(notes.count))
            let x = cos(angle) * radius
            let y = sin(angle) * radius

            let node = GraphNode(
                id: note.id,
                title: note.title,
                connections: note.linkedNotes.count,
                x: x,
                y: y
            )
            nodes.append(node)
        }

        graphNodes = nodes
    }

    // MARK: - 文件系统操作

    /// 保存笔记到文件
    private func saveNote(_ note: Note) {
        let folderPath = vaultPath + note.folderPath
        try? FileManager.default.createDirectory(atPath: folderPath, withIntermediateDirectories: true)

        let filePath = "\(folderPath)/\(note.title).md"
        let markdown = generateMarkdown(for: note)

        try? markdown.write(toFile: filePath, atomically: true, encoding: .utf8)
    }

    /// 删除笔记文件
    private func deleteNoteFile(_ note: Note) {
        let filePath = "\(vaultPath)\(note.folderPath)/\(note.title).md"
        try? FileManager.default.removeItem(atPath: filePath)
    }

    /// 加载所有笔记
    private func loadNotes() {
        guard let enumerator = FileManager.default.enumerator(atPath: vaultPath) else { return }

        var loadedNotes: [Note] = []

        for case let file as String in enumerator where file.hasSuffix(".md") {
            let filePath = "\(vaultPath)/\(file)"
            if let content = try? String(contentsOfFile: filePath, encoding: .utf8),
               let note = parseMarkdown(content, filename: file) {
                loadedNotes.append(note)
            }
        }

        notes = loadedNotes
        updateGraph()
    }

    /// 生成 Markdown 格式
    private func generateMarkdown(for note: Note) -> String {
        var markdown = "---\n"
        markdown += "id: \(note.id.uuidString)\n"
        markdown += "created: \(ISO8601DateFormatter().string(from: note.createdAt))\n"
        markdown += "updated: \(ISO8601DateFormatter().string(from: note.updatedAt))\n"

        if !note.tags.isEmpty {
            markdown += "tags: [\(note.tags.map { "#\($0)" }.joined(separator: ", "))]\n"
        }

        markdown += "---\n\n"
        markdown += "# \(note.title)\n\n"
        markdown += note.content

        return markdown
    }

    /// 解析 Markdown 文件
    private func parseMarkdown(_ content: String, filename: String) -> Note? {
        let components = content.components(separatedBy: "---")
        guard components.count >= 3 else { return nil }

        let frontmatter = components[1]
        let body = components[2...].joined(separator: "---")

        // 解析 frontmatter
        var id = UUID()
        var createdAt = Date()
        var updatedAt = Date()
        var tags: [String] = []

        for line in frontmatter.components(separatedBy: "\n") {
            let parts = line.components(separatedBy: ": ")
            guard parts.count == 2 else { continue }

            let key = parts[0].trimmingCharacters(in: .whitespaces)
            let value = parts[1].trimmingCharacters(in: .whitespaces)

            switch key {
            case "id":
                id = UUID(uuidString: value) ?? UUID()
            case "created":
                createdAt = ISO8601DateFormatter().date(from: value) ?? Date()
            case "updated":
                updatedAt = ISO8601DateFormatter().date(from: value) ?? Date()
            case "tags":
                tags = value
                    .replacingOccurrences(of: "[", with: "")
                    .replacingOccurrences(of: "]", with: "")
                    .components(separatedBy: ", ")
                    .map { $0.replacingOccurrences(of: "#", with: "").trimmingCharacters(in: .whitespaces) }
            default:
                break
            }
        }

        let title = filename.replacingOccurrences(of: ".md", with: "")
        let noteContent = body.replacingOccurrences(of: "# \(title)\n\n", with: "").trimmingCharacters(in: .whitespacesAndNewlines)

        var note = Note(title: title, content: noteContent, folderPath: "/", tags: tags)
        note.id = id
        note.createdAt = createdAt
        note.updatedAt = updatedAt

        return note
    }

    // MARK: - 标签管理

    /// 获取所有标签
    func getAllTags() -> [String] {
        var allTags = Set<String>()
        for note in notes {
            allTags.formUnion(note.tags)
        }
        return Array(allTags).sorted()
    }

    /// 按标签筛选笔记
    func getNotes(withTag tag: String) -> [Note] {
        return notes.filter { $0.tags.contains(tag) }
    }
}
