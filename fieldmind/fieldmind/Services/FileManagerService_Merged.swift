//
//  FileManagerService_Merged.swift
//  FieldMind
//
//  深度整合 - 合并自主版本和 Native 版本
//  Generated: Sat Sep 19 11:21:00 CST 2026
//

import Foundation

// ========================================
// 主实现（来自主项目）
// ========================================


/// FileManagerService - 文件管理服务（虚拟文件夹支持）

class FileManagerService {
    static let shared = FileManagerService()
    private let apiClient = APIClient.shared

    private init() {}

    // MARK: - Response Models

    struct FileNodeResponse: Decodable, Identifiable {
        let id: String
        let name: String
        let isFolder: Bool
        let type: String
        let size: Int
        let modifiedAt: Date
        let path: String
        var children: [FileNodeResponse]

        enum CodingKeys: String, CodingKey {
            case id, name, type, size, path, children
            case isFolder = "is_folder"
            case isFolderCamel = "isFolder"
            case modifiedAt = "modified_at"
        }

        init(
            id: String,
            name: String,
            isFolder: Bool,
            type: String,
            size: Int,
            modifiedAt: Date,
            path: String,
            children: [FileNodeResponse] = []
        ) {
            self.id = id
            self.name = name
            self.isFolder = isFolder
            self.type = type
            self.size = size
            self.modifiedAt = modifiedAt
            self.path = path
            self.children = children
        }

        init(from decoder: Decoder) throws {
            let container = try decoder.container(keyedBy: CodingKeys.self)
            id = try container.decode(String.self, forKey: .id)
            name = try container.decode(String.self, forKey: .name)
            type = try container.decodeIfPresent(String.self, forKey: .type) ?? "unknown"
            // 新版后端使用 is_folder；兼容旧缓存/旧接口可能返回的 isFolder，
            // 最后按 type 推断，避免文件树因为一个可推断字段整体解码失败。
            if let folder = try container.decodeIfPresent(Bool.self, forKey: .isFolder) {
                isFolder = folder
            } else if let folder = try container.decodeIfPresent(Bool.self, forKey: .isFolderCamel) {
                isFolder = folder
            } else {
                isFolder = type.lowercased() == "folder" || type.lowercased() == "directory"
            }
            size = try container.decodeIfPresent(Int.self, forKey: .size) ?? 0
            modifiedAt = try container.decodeIfPresent(Date.self, forKey: .modifiedAt) ?? Date.distantPast
            path = try container.decodeIfPresent(String.self, forKey: .path) ?? ""
            children = try container.decodeIfPresent([FileNodeResponse].self, forKey: .children) ?? []
        }
    }

    struct FileTreeResponse: Decodable {
        let root: FileNodeResponse
        let totalFiles: Int
        let totalFolders: Int
        let totalSize: Int

        enum CodingKeys: String, CodingKey {
            case root
            case totalFiles = "total_files"
            case totalFolders = "total_folders"
            case totalSize = "total_size"
        }

        init(from decoder: Decoder) throws {
            let container = try decoder.container(keyedBy: CodingKeys.self)
            root = try container.decode(FileNodeResponse.self, forKey: .root)
            totalFiles = try container.decodeIfPresent(Int.self, forKey: .totalFiles) ?? root.countFiles()
            totalFolders = try container.decodeIfPresent(Int.self, forKey: .totalFolders) ?? root.countFolders()
            totalSize = try container.decodeIfPresent(Int.self, forKey: .totalSize) ?? root.sumFileSize()
        }
    }

    struct FolderContentsResponse: Decodable {
        let folderPath: String
        let items: [FileNodeResponse]
        let total: Int

        enum CodingKeys: String, CodingKey {
            case items, total
            case folderPath = "folder_path"
        }
    }

    struct CreateFolderRequest: Codable {
        let projectId: Int
        let folderPath: String

        enum CodingKeys: String, CodingKey {
            case projectId = "project_id"
            case folderPath = "folder_path"
        }
    }

    struct MoveFileRequest: Codable {
        let fileId: Int
        let targetPath: String

        enum CodingKeys: String, CodingKey {
            case fileId = "file_id"
            case targetPath = "target_path"
        }
    }

    // MARK: - API Methods

    /// 获取完整文件树
    func getFileTree(projectId: Int) async throws -> FileTreeResponse {
        let endpoint = APIEndpoint.custom("/file-tree/\(projectId)")
        return try await apiClient.request(endpoint, method: .get)
    }

    /// 获取文件夹内容（按需加载）
    func getFolderContents(projectId: Int, folderPath: String) async throws -> FolderContentsResponse {
        let endpoint = APIEndpoint.custom("/folder-contents")
            .with(queryItem: "project_id", value: "\(projectId)")
            .with(queryItem: "folder_path", value: folderPath)
        return try await apiClient.request(endpoint, method: .get)
    }

    /// 创建文件夹
    func createFolder(projectId: Int, folderPath: String) async throws -> CreateFolderResponse {
        let request = CreateFolderRequest(projectId: projectId, folderPath: folderPath)
        let endpoint = APIEndpoint.custom("/folders")
        return try await apiClient.request(endpoint, method: .post, body: request)
    }

    /// 移动文件
    func moveFile(fileId: String, targetPath: String) async throws -> MoveFileResponse {
        guard let numericFileId = Int(fileId) else {
            throw NetworkError.httpError(statusCode: 400, message: "无效的文件ID")
        }
        let request = MoveFileRequest(fileId: numericFileId, targetPath: targetPath)
        let endpoint = APIEndpoint.custom("/files/\(fileId)/move/")
        return try await apiClient.request(endpoint, method: .put, body: request)
    }

    /// 删除文件并同步删除主文档记录。
    func deleteFile(fileId: String) async throws {
        guard let numericFileId = Int(fileId) else {
            throw NetworkError.httpError(statusCode: 400, message: "无效的文件ID")
        }
        let _: EmptyResponse = try await apiClient.request(
            .custom("/files/\(numericFileId)"),
            method: .delete
        )
    }

    /// 删除文件夹
    func deleteFolder(projectId: Int, folderPath: String) async throws -> DeleteFolderResponse {
        let endpoint = APIEndpoint.custom("/folders")
            .with(queryItem: "project_id", value: "\(projectId)")
            .with(queryItem: "folder_path", value: folderPath)
        return try await apiClient.request(endpoint, method: .delete)
    }

    struct CreateFolderResponse: Decodable {
        let status: String
        let folderPath: String
        let message: String

        enum CodingKeys: String, CodingKey {
            case status, message
            case folderPath = "folder_path"
        }
    }

    struct MoveFileResponse: Decodable {
        let status: String
        let oldPath: String
        let newPath: String
        let message: String

        enum CodingKeys: String, CodingKey {
            case status, message
            case oldPath = "old_path"
            case newPath = "new_path"
        }
    }

    struct DeleteFolderResponse: Decodable {
        let status: String
        let folderPath: String
        let deletedFiles: Int
        let message: String

        enum CodingKeys: String, CodingKey {
            case status, message
            case folderPath = "folder_path"
            case deletedFiles = "deleted_files"
        }
    }
}

private extension FileManagerService.FileNodeResponse {
    func countFiles() -> Int {
        (isFolder ? 0 : 1) + children.reduce(0) { $0 + $1.countFiles() }
    }

    func countFolders() -> Int {
        (isFolder ? 1 : 0) + children.reduce(0) { $0 + $1.countFolders() }
    }

    func sumFileSize() -> Int {
        (isFolder ? 0 : size) + children.reduce(0) { $0 + $1.sumFileSize() }
    }
}

// ========================================
// Native 版本的扩展功能
// ========================================
// TODO: 手动审查并整合以下功能

/*

/// FileManagerService - 文件管理服务（虚拟文件夹支持）

class FileManagerService {
    static let shared = FileManagerService()
    private let apiClient = APIClient.shared

    private init() {}

    // MARK: - Response Models

    struct FileNodeResponse: Decodable, Identifiable {
        let id: String
        let name: String
        let isFolder: Bool
        let type: String
        let size: Int
        let modifiedAt: Date
        let path: String
        var children: [FileNodeResponse]

        enum CodingKeys: String, CodingKey {
            case id, name, type, size, path, children
            case isFolder = "is_folder"
            case isFolderCamel = "isFolder"
            case modifiedAt = "modified_at"
        }

        init(
            id: String,
            name: String,
            isFolder: Bool,
            type: String,
            size: Int,
            modifiedAt: Date,
            path: String,
            children: [FileNodeResponse] = []
        ) {
            self.id = id
            self.name = name
            self.isFolder = isFolder
            self.type = type
            self.size = size
            self.modifiedAt = modifiedAt
            self.path = path
            self.children = children
        }

        init(from decoder: Decoder) throws {
            let container = try decoder.container(keyedBy: CodingKeys.self)
            id = try container.decode(String.self, forKey: .id)
            name = try container.decode(String.self, forKey: .name)
            type = try container.decodeIfPresent(String.self, forKey: .type) ?? "unknown"
            // 新版后端使用 is_folder；兼容旧缓存/旧接口可能返回的 isFolder，
            // 最后按 type 推断，避免文件树因为一个可推断字段整体解码失败。
            if let folder = try container.decodeIfPresent(Bool.self, forKey: .isFolder) {
                isFolder = folder
            } else if let folder = try container.decodeIfPresent(Bool.self, forKey: .isFolderCamel) {
                isFolder = folder
            } else {
                isFolder = type.lowercased() == "folder" || type.lowercased() == "directory"
            }
            size = try container.decodeIfPresent(Int.self, forKey: .size) ?? 0
            modifiedAt = try container.decodeIfPresent(Date.self, forKey: .modifiedAt) ?? Date.distantPast
            path = try container.decodeIfPresent(String.self, forKey: .path) ?? ""
            children = try container.decodeIfPresent([FileNodeResponse].self, forKey: .children) ?? []
        }
    }

    struct FileTreeResponse: Decodable {
        let root: FileNodeResponse
        let totalFiles: Int
        let totalFolders: Int
        let totalSize: Int

        enum CodingKeys: String, CodingKey {
            case root
            case totalFiles = "total_files"
            case totalFolders = "total_folders"
            case totalSize = "total_size"
        }

        init(from decoder: Decoder) throws {
            let container = try decoder.container(keyedBy: CodingKeys.self)
            root = try container.decode(FileNodeResponse.self, forKey: .root)
            totalFiles = try container.decodeIfPresent(Int.self, forKey: .totalFiles) ?? root.countFiles()
            totalFolders = try container.decodeIfPresent(Int.self, forKey: .totalFolders) ?? root.countFolders()
            totalSize = try container.decodeIfPresent(Int.self, forKey: .totalSize) ?? root.sumFileSize()
        }
    }

    struct FolderContentsResponse: Decodable {
        let folderPath: String
        let items: [FileNodeResponse]
        let total: Int

        enum CodingKeys: String, CodingKey {
            case items, total
            case folderPath = "folder_path"
        }
    }

    struct CreateFolderRequest: Codable {
        let projectId: Int
        let folderPath: String

        enum CodingKeys: String, CodingKey {
            case projectId = "project_id"
            case folderPath = "folder_path"
        }
    }

    struct MoveFileRequest: Codable {
        let fileId: Int
        let targetPath: String

        enum CodingKeys: String, CodingKey {
            case fileId = "file_id"
            case targetPath = "target_path"
        }
    }

    // MARK: - API Methods

    /// 获取完整文件树
    func getFileTree(projectId: Int) async throws -> FileTreeResponse {
        let endpoint = APIEndpoint.custom("/file-tree/\(projectId)")
        return try await apiClient.request(endpoint, method: .get)
    }

    /// 获取文件夹内容（按需加载）
    func getFolderContents(projectId: Int, folderPath: String) async throws -> FolderContentsResponse {
        let endpoint = APIEndpoint.custom("/folder-contents")
            .with(queryItem: "project_id", value: "\(projectId)")
            .with(queryItem: "folder_path", value: folderPath)
        return try await apiClient.request(endpoint, method: .get)
    }

    /// 创建文件夹
    func createFolder(projectId: Int, folderPath: String) async throws -> CreateFolderResponse {
        let request = CreateFolderRequest(projectId: projectId, folderPath: folderPath)
        let endpoint = APIEndpoint.custom("/folders")
        return try await apiClient.request(endpoint, method: .post, body: request)
    }

    /// 移动文件
    func moveFile(fileId: String, targetPath: String) async throws -> MoveFileResponse {
        guard let numericFileId = Int(fileId) else {
            throw NetworkError.httpError(statusCode: 400, message: "无效的文件ID")
        }
        let request = MoveFileRequest(fileId: numericFileId, targetPath: targetPath)
        let endpoint = APIEndpoint.custom("/files/\(fileId)/move/")
        return try await apiClient.request(endpoint, method: .put, body: request)
    }

    /// 删除文件并同步删除主文档记录。
    func deleteFile(fileId: String) async throws {
        guard let numericFileId = Int(fileId) else {
            throw NetworkError.httpError(statusCode: 400, message: "无效的文件ID")
        }
        let _: EmptyResponse = try await apiClient.request(
            .custom("/files/\(numericFileId)"),
            method: .delete
        )
    }

    /// 删除文件夹
    func deleteFolder(projectId: Int, folderPath: String) async throws -> DeleteFolderResponse {
        let endpoint = APIEndpoint.custom("/folders")
            .with(queryItem: "project_id", value: "\(projectId)")
            .with(queryItem: "folder_path", value: folderPath)
        return try await apiClient.request(endpoint, method: .delete)
    }

    struct CreateFolderResponse: Decodable {
        let status: String
        let folderPath: String
        let message: String

        enum CodingKeys: String, CodingKey {
            case status, message
            case folderPath = "folder_path"
        }
    }

    struct MoveFileResponse: Decodable {
        let status: String
        let oldPath: String
        let newPath: String
        let message: String

        enum CodingKeys: String, CodingKey {
            case status, message
            case oldPath = "old_path"
            case newPath = "new_path"
        }
    }

    struct DeleteFolderResponse: Decodable {
        let status: String
        let folderPath: String
        let deletedFiles: Int
        let message: String

        enum CodingKeys: String, CodingKey {
            case status, message
            case folderPath = "folder_path"
            case deletedFiles = "deleted_files"
        }
    }
}

private extension FileManagerService.FileNodeResponse {
    func countFiles() -> Int {
        (isFolder ? 0 : 1) + children.reduce(0) { $0 + $1.countFiles() }
    }

    func countFolders() -> Int {
        (isFolder ? 1 : 0) + children.reduce(0) { $0 + $1.countFolders() }
    }

    func sumFileSize() -> Int {
        (isFolder ? 0 : size) + children.reduce(0) { $0 + $1.sumFileSize() }
    }
}
*/

