import AppKit
import Foundation

enum UploadFileSelectionHelper {
    static func collectUploadableFiles(from urls: [URL]) -> [URL] {
        var files: [URL] = []
        var seen = Set<String>()

        for url in urls {
            for file in uploadableFiles(at: url) {
                let stableFile = makeStableUploadCopy(file)
                let key = stableFile.standardizedFileURL.path
                if seen.insert(key).inserted {
                    files.append(stableFile)
                }
            }
        }

        return files
    }

    static func makeStableUploadCopy(_ url: URL) -> URL {
        guard url.isFileURL else { return url }

        let scoped = url.startAccessingSecurityScopedResource()
        defer {
            if scoped {
                url.stopAccessingSecurityScopedResource()
            }
        }

        let destination = FileManager.default.temporaryDirectory
            .appendingPathComponent("fieldmind-drop-\(UUID().uuidString)")
            .appendingPathExtension(url.pathExtension)

        do {
            try FileManager.default.copyItem(at: url, to: destination)
            return destination
        } catch {
            DebugLogger.shared.log(
                "拖拽文件复制失败，继续尝试原文件",
                type: .warning,
                details: "文件=\(url.lastPathComponent)\n错误=\(error.localizedDescription)",
                category: "upload.drop"
            )
            return url
        }
    }

    static func uploadableFiles(at url: URL) -> [URL] {
        guard url.isFileURL else { return [] }

        let scoped = url.startAccessingSecurityScopedResource()
        defer {
            if scoped {
                url.stopAccessingSecurityScopedResource()
            }
        }

        let values = try? url.resourceValues(forKeys: [.isDirectoryKey, .isRegularFileKey, .isHiddenKey])
        if values?.isHidden == true {
            return []
        }

        if values?.isDirectory == true {
            let options: FileManager.DirectoryEnumerationOptions = [.skipsHiddenFiles, .skipsPackageDescendants]
            guard let enumerator = FileManager.default.enumerator(
                at: url,
                includingPropertiesForKeys: [.isRegularFileKey, .isHiddenKey],
                options: options
            ) else {
                return []
            }

            return enumerator.compactMap { item in
                guard let fileURL = item as? URL else { return nil }
                let values = try? fileURL.resourceValues(forKeys: [.isRegularFileKey, .isHiddenKey])
                guard values?.isRegularFile == true, values?.isHidden != true else { return nil }
                return isSupportedUploadFile(fileURL) ? fileURL : nil
            }
        }

        if values?.isRegularFile == true || !url.hasDirectoryPath {
            return isSupportedUploadFile(url) ? [url] : []
        }

        return []
    }

    static func isSupportedUploadFile(_ url: URL) -> Bool {
        let supportedExtensions: Set<String> = [
            "pdf", "doc", "docx", "ppt", "pptx",
            "xls", "xlsx", "csv",
            "txt", "md", "html", "htm", "json", "xml",
            "mp3", "wav", "m4a", "aac", "flac",
            "mp4", "mov", "m4v", "avi",
            "jpg", "jpeg", "png", "gif", "heic", "heif", "webp", "tif", "tiff"
        ]
        return supportedExtensions.contains(url.pathExtension.lowercased())
    }
}
