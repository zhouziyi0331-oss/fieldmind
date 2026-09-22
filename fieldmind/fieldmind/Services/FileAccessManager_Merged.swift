//
//  FileAccessManager_Merged.swift
//  FieldMind
//
//  深度整合 - 合并自主版本和 Native 版本
//  Generated: Sat Sep 19 11:21:00 CST 2026
//

import AppKit
import Combine
import Foundation

// ========================================
// 主实现（来自主项目）
// ========================================


@MainActor

final class FileAccessManager: ObservableObject {
    static let shared = FileAccessManager()

    private let bookmarksKey = "fieldmind_authorized_folder_bookmarks"

    @Published private(set) var authorizedFolders: [URL] = []

    private init() {
        reloadAuthorizedFolders()
    }

    var authorizationSummary: String {
        if authorizedFolders.isEmpty {
            return "尚未授权任何文件夹"
        }
        return authorizedFolders.map { $0.lastPathComponent }.joined(separator: "、")
    }

    func authorizeCommonFolder(defaultDirectory: URL? = nil) -> Bool {
        let panel = NSOpenPanel()
        panel.title = "授权文件夹访问"
        panel.message = "请选择要让 FieldMind 反复访问的文件夹。"
        panel.canChooseFiles = false
        panel.canChooseDirectories = true
        panel.allowsMultipleSelection = true
        panel.canCreateDirectories = false
        panel.allowedContentTypes = [.folder]
        panel.directoryURL = defaultDirectory

        guard panel.runModal() == .OK else {
            return false
        }

        var didSave = false
        for url in panel.urls {
            didSave = saveAuthorizedFolder(url) || didSave
        }
        return didSave
    }

    func authorizeDownloadsFolder() -> Bool {
        authorizeCommonFolder(defaultDirectory: FileManager.default.urls(for: .downloadsDirectory, in: .userDomainMask).first)
    }

    func authorizeDesktopFolder() -> Bool {
        authorizeCommonFolder(defaultDirectory: FileManager.default.urls(for: .desktopDirectory, in: .userDomainMask).first)
    }

    func authorizeDocumentsFolder() -> Bool {
        authorizeCommonFolder(defaultDirectory: FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first)
    }

    func refresh() {
        reloadAuthorizedFolders()
    }

    private func saveAuthorizedFolder(_ url: URL) -> Bool {
        guard url.isFileURL else { return false }

        do {
            let bookmark = try url.bookmarkData(
                options: [.withSecurityScope],
                includingResourceValuesForKeys: nil,
                relativeTo: nil
            )
            var stored = storedBookmarks()
            stored.removeAll { $0.url == url.standardizedFileURL.path }
            stored.append((url.standardizedFileURL.path, bookmark))
            UserDefaults.standard.set(stored.map { $0.bookmark }, forKey: bookmarksKey)
            reloadAuthorizedFolders()
            return true
        } catch {
            DebugLogger.shared.log(
                "保存文件夹授权失败",
                type: .warning,
                details: "文件夹=\(url.path)\n错误=\(error.localizedDescription)",
                category: "permissions"
            )
            return false
        }
    }

    private func storedBookmarks() -> [(url: String, bookmark: Data)] {
        guard let bookmarks = UserDefaults.standard.array(forKey: bookmarksKey) as? [Data] else {
            return []
        }
        return bookmarks.compactMap { data in
            resolveBookmarkData(data).map { ($0.path, data) }
        }
    }

    private func reloadAuthorizedFolders() {
        guard let bookmarks = UserDefaults.standard.array(forKey: bookmarksKey) as? [Data] else {
            authorizedFolders = []
            return
        }

        var folders: [URL] = []
        var validBookmarks: [Data] = []

        for bookmark in bookmarks {
            guard let url = resolveBookmarkData(bookmark) else {
                continue
            }
            folders.append(url)
            validBookmarks.append(bookmark)
        }

        if validBookmarks.count != bookmarks.count {
            UserDefaults.standard.set(validBookmarks, forKey: bookmarksKey)
        }

        authorizedFolders = folders
    }

    private func resolveBookmarkData(_ bookmark: Data) -> URL? {
        var isStale = false
        do {
            let url = try URL(
                resolvingBookmarkData: bookmark,
                options: [.withSecurityScope],
                relativeTo: nil,
                bookmarkDataIsStale: &isStale
            )
            if isStale {
                DebugLogger.shared.log(
                    "文件夹授权书签已变旧，当前仍可读取",
                    type: .warning,
                    details: url.path,
                    category: "permissions"
                )
            }
            return url
        } catch {
            return nil
        }
    }
}

// ========================================
// Native 版本的扩展功能
// ========================================
// TODO: 手动审查并整合以下功能

/*

@MainActor

final class FileAccessManager: ObservableObject {
    static let shared = FileAccessManager()

    private let bookmarksKey = "fieldmind_authorized_folder_bookmarks"

    @Published private(set) var authorizedFolders: [URL] = []

    private init() {
        reloadAuthorizedFolders()
    }

    var authorizationSummary: String {
        if authorizedFolders.isEmpty {
            return "尚未授权任何文件夹"
        }
        return authorizedFolders.map { $0.lastPathComponent }.joined(separator: "、")
    }

    func authorizeCommonFolder(defaultDirectory: URL? = nil) -> Bool {
        let panel = NSOpenPanel()
        panel.title = "授权文件夹访问"
        panel.message = "请选择要让 FieldMind 反复访问的文件夹。"
        panel.canChooseFiles = false
        panel.canChooseDirectories = true
        panel.allowsMultipleSelection = true
        panel.canCreateDirectories = false
        panel.allowedContentTypes = [.folder]
        panel.directoryURL = defaultDirectory

        guard panel.runModal() == .OK else {
            return false
        }

        var didSave = false
        for url in panel.urls {
            didSave = saveAuthorizedFolder(url) || didSave
        }
        return didSave
    }

    func authorizeDownloadsFolder() -> Bool {
        authorizeCommonFolder(defaultDirectory: FileManager.default.urls(for: .downloadsDirectory, in: .userDomainMask).first)
    }

    func authorizeDesktopFolder() -> Bool {
        authorizeCommonFolder(defaultDirectory: FileManager.default.urls(for: .desktopDirectory, in: .userDomainMask).first)
    }

    func authorizeDocumentsFolder() -> Bool {
        authorizeCommonFolder(defaultDirectory: FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first)
    }

    func refresh() {
        reloadAuthorizedFolders()
    }

    private func saveAuthorizedFolder(_ url: URL) -> Bool {
        guard url.isFileURL else { return false }

        do {
            let bookmark = try url.bookmarkData(
                options: [.withSecurityScope],
                includingResourceValuesForKeys: nil,
                relativeTo: nil
            )
            var stored = storedBookmarks()
            stored.removeAll { $0.url == url.standardizedFileURL.path }
            stored.append((url.standardizedFileURL.path, bookmark))
            UserDefaults.standard.set(stored.map { $0.bookmark }, forKey: bookmarksKey)
            reloadAuthorizedFolders()
            return true
        } catch {
            DebugLogger.shared.log(
                "保存文件夹授权失败",
                type: .warning,
                details: "文件夹=\(url.path)\n错误=\(error.localizedDescription)",
                category: "permissions"
            )
            return false
        }
    }

    private func storedBookmarks() -> [(url: String, bookmark: Data)] {
        guard let bookmarks = UserDefaults.standard.array(forKey: bookmarksKey) as? [Data] else {
            return []
        }
        return bookmarks.compactMap { data in
            resolveBookmarkData(data).map { ($0.path, data) }
        }
    }

    private func reloadAuthorizedFolders() {
        guard let bookmarks = UserDefaults.standard.array(forKey: bookmarksKey) as? [Data] else {
            authorizedFolders = []
            return
        }

        var folders: [URL] = []
        var validBookmarks: [Data] = []

        for bookmark in bookmarks {
            guard let url = resolveBookmarkData(bookmark) else {
                continue
            }
            folders.append(url)
            validBookmarks.append(bookmark)
        }

        if validBookmarks.count != bookmarks.count {
            UserDefaults.standard.set(validBookmarks, forKey: bookmarksKey)
        }

        authorizedFolders = folders
    }

    private func resolveBookmarkData(_ bookmark: Data) -> URL? {
        var isStale = false
        do {
            let url = try URL(
                resolvingBookmarkData: bookmark,
                options: [.withSecurityScope],
                relativeTo: nil,
                bookmarkDataIsStale: &isStale
            )
            if isStale {
                DebugLogger.shared.log(
                    "文件夹授权书签已变旧，当前仍可读取",
                    type: .warning,
                    details: url.path,
                    category: "permissions"
                )
            }
            return url
        } catch {
            return nil
        }
    }
}
*/

