import Foundation

/// FileManagerService - 文件管理服务（虚拟文件夹支持）
class FileManagerService {
    static let shared = FileManagerService()
    private let apiClient = APIClient.shared

    private init() {}

    // MARK: - Response Models

    struct FileNodeResponse: Codable, Identifiable {
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
            case modifiedAt = "modified_at"
        }
    }

    struct FileTreeResponse: Codable {
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
    }

    struct FolderContentsResponse: Codable {
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
        let targetPath: String

        enum CodingKeys: String, CodingKey {
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
        let request = MoveFileRequest(targetPath: targetPath)
        let endpoint = APIEndpoint.custom("/files/\(fileId)/move")
        return try await apiClient.request(endpoint, method: .put, body: request)
    }

    /// 删除文件夹
    func deleteFolder(projectId: Int, folderPath: String) async throws -> DeleteFolderResponse {
        let endpoint = APIEndpoint.custom("/folders")
            .with(queryItem: "project_id", value: "\(projectId)")
            .with(queryItem: "folder_path", value: folderPath)
        return try await apiClient.request(endpoint, method: .delete)
    }

    struct CreateFolderResponse: Codable {
        let status: String
        let folderPath: String
        let message: String

        enum CodingKeys: String, CodingKey {
            case status, message
            case folderPath = "folder_path"
        }
    }

    struct MoveFileResponse: Codable {
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

    struct DeleteFolderResponse: Codable {
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
