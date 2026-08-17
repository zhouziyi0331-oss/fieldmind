import Foundation
import SwiftUI

/// FileManagerViewModel - 文件管理状态管理
@MainActor
class FileManagerViewModel: ObservableObject {
    @Published var fileTree: FileManagerService.FileTreeResponse?
    @Published var currentPath: String = ""
    @Published var currentItems: [FileManagerService.FileNodeResponse] = []
    @Published var selectedFiles: Set<String> = []
    @Published var expandedFolders: Set<String> = ["root"]

    @Published var isLoadingTree = false
    @Published var isLoadingFolder = false
    @Published var errorMessage: String?
    @Published var successMessage: String?

    // UI State
    @Published var searchText: String = ""
    @Published var viewMode: ViewMode = .tree
    @Published var sortBy: SortOption = .name

    enum ViewMode {
        case tree, list, grid
    }

    enum SortOption {
        case name, date, size, type
    }

    private let service = FileManagerService.shared

    // MARK: - API Methods

    /// 加载完整文件树
    func loadFileTree(projectId: Int) async {
        isLoadingTree = true
        errorMessage = nil

        do {
            fileTree = try await service.getFileTree(projectId: projectId)
            if let root = fileTree?.root {
                currentItems = root.children
            }
            isLoadingTree = false
        } catch {
            errorMessage = "加载文件树失败: \(error.localizedDescription)"
            isLoadingTree = false
        }
    }

    /// 加载文件夹内容（按需加载）
    func loadFolderContents(projectId: Int, folderPath: String) async {
        isLoadingFolder = true

        do {
            let response = try await service.getFolderContents(projectId: projectId, folderPath: folderPath)
            currentPath = folderPath
            currentItems = response.items
            isLoadingFolder = false
        } catch {
            errorMessage = "加载文件夹失败: \(error.localizedDescription)"
            isLoadingFolder = false
        }
    }

    /// 创建文件夹
    func createFolder(projectId: Int, folderPath: String) async -> Bool {
        do {
            let response = try await service.createFolder(projectId: projectId, folderPath: folderPath)
            successMessage = response.message

            // 重新加载文件树
            await loadFileTree(projectId: projectId)
            return true
        } catch {
            errorMessage = "创建文件夹失败: \(error.localizedDescription)"
            return false
        }
    }

    /// 移动文件
    func moveFile(fileId: String, targetPath: String, projectId: Int) async -> Bool {
        do {
            let response = try await service.moveFile(fileId: fileId, targetPath: targetPath)
            successMessage = response.message

            // 重新加载文件树
            await loadFileTree(projectId: projectId)
            return true
        } catch {
            errorMessage = "移动文件失败: \(error.localizedDescription)"
            return false
        }
    }

    /// 删除文件夹
    func deleteFolder(projectId: Int, folderPath: String) async -> Bool {
        do {
            let response = try await service.deleteFolder(projectId: projectId, folderPath: folderPath)
            successMessage = response.message

            // 重新加载文件树
            await loadFileTree(projectId: projectId)
            return true
        } catch {
            errorMessage = "删除文件夹失败: \(error.localizedDescription)"
            return false
        }
    }

    // MARK: - Helper Methods

    /// 切换文件夹展开/折叠
    func toggleFolder(_ folderId: String) {
        if expandedFolders.contains(folderId) {
            expandedFolders.remove(folderId)
        } else {
            expandedFolders.insert(folderId)
        }
    }

    /// 检查文件夹是否展开
    func isFolderExpanded(_ folderId: String) -> Bool {
        expandedFolders.contains(folderId)
    }

    /// 过滤和排序当前项
    func filteredAndSortedItems() -> [FileManagerService.FileNodeResponse] {
        var items = currentItems

        // 搜索过滤
        if !searchText.isEmpty {
            items = items.filter { $0.name.localizedCaseInsensitiveContains(searchText) }
        }

        // 排序
        items.sort { item1, item2 in
            // 文件夹优先
            if item1.isFolder && !item2.isFolder {
                return true
            }
            if !item1.isFolder && item2.isFolder {
                return false
            }

            // 按选定字段排序
            switch sortBy {
            case .name:
                return item1.name.localizedCaseInsensitiveCompare(item2.name) == .orderedAscending
            case .date:
                return item1.modifiedAt > item2.modifiedAt
            case .size:
                return item1.size > item2.size
            case .type:
                return item1.type.localizedCaseInsensitiveCompare(item2.type) == .orderedAscending
            }
        }

        return items
    }

    /// 格式化文件大小
    func formatFileSize(_ bytes: Int) -> String {
        let formatter = ByteCountFormatter()
        formatter.allowedUnits = [.useKB, .useMB, .useGB]
        formatter.countStyle = .file
        return formatter.string(fromByteCount: Int64(bytes))
    }

    /// 格式化日期
    func formatDate(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd HH:mm"
        return formatter.string(from: date)
    }

    /// 获取文件图标
    func getFileIcon(_ item: FileManagerService.FileNodeResponse) -> String {
        if item.isFolder {
            return "folder.fill"
        }
        switch item.type.lowercased() {
        case "pdf": return "doc.fill"
        case "doc", "docx": return "doc.text.fill"
        case "xls", "xlsx", "csv": return "tablecells"
        case "ppt", "pptx": return "person.crop.rectangle"
        case "mp3", "wav", "audio": return "waveform"
        case "mp4", "mov", "video": return "video.fill"
        case "jpg", "png", "jpeg", "image": return "photo.fill"
        case "txt", "md": return "doc.plaintext"
        case "html": return "chevron.left.forwardslash.chevron.right"
        case "json": return "curlybraces"
        case "zip", "rar": return "archivebox.fill"
        default: return "doc"
        }
    }

    /// 获取文件图标颜色
    func getFileIconColor(_ item: FileManagerService.FileNodeResponse) -> String {
        if item.isFolder {
            return "F59E0B"
        }
        switch item.type.lowercased() {
        case "pdf": return "EF4444"
        case "doc", "docx": return "3B82F6"
        case "xls", "xlsx", "csv": return "10B981"
        case "ppt", "pptx": return "F97316"
        case "mp3", "wav", "audio": return "8B5CF6"
        case "mp4", "mov", "video": return "EC4899"
        case "jpg", "png", "jpeg", "image": return "06B6D4"
        case "txt", "md": return "64748B"
        case "html": return "F59E0B"
        case "json": return "84CC16"
        case "zip", "rar": return "6366F1"
        default: return "64748B"
        }
    }

    /// 获取面包屑导航路径
    func getBreadcrumbs() -> [String] {
        if currentPath.isEmpty {
            return ["我的文件"]
        }
        let parts = currentPath.split(separator: "/").map(String.init)
        return ["我的文件"] + parts
    }

    /// 清除消息
    func clearMessages() {
        errorMessage = nil
        successMessage = nil
    }
}
