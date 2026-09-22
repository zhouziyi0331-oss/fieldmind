import Foundation
import SwiftUI

/// PhotoViewModel - 照片管理状态管理
@MainActor
class PhotoViewModel: ObservableObject {
    @Published var photos: [PhotoService.PhotoResponse] = []
    @Published var stats: PhotoService.PhotoStatsResponse?

    @Published var isLoadingPhotos = false
    @Published var isLoadingStats = false
    @Published var errorMessage: String?
    @Published var successMessage: String?

    // Filters
    @Published var searchText: String = ""
    @Published var selectedDateFilter: String = "all"  // all/today/week/month/year
    @Published var selectedSort: String = "最新优先"

    private let service = PhotoService.shared

    // MARK: - API Methods

    /// 加载照片列表
    func loadPhotos(projectId: Int, page: Int = 1, pageSize: Int = 100) async {
        isLoadingPhotos = true
        errorMessage = nil

        do {
            let sortBy: String
            let sortOrder: String

            switch selectedSort {
            case "最新优先":
                sortBy = "uploaded_at"
                sortOrder = "desc"
            case "最旧优先":
                sortBy = "uploaded_at"
                sortOrder = "asc"
            case "名称 A-Z":
                sortBy = "filename"
                sortOrder = "asc"
            case "大小降序":
                sortBy = "size"
                sortOrder = "desc"
            default:
                sortBy = "uploaded_at"
                sortOrder = "desc"
            }

            let response = try await service.getPhotos(
                projectId: projectId,
                search: searchText.isEmpty ? nil : searchText,
                dateFilter: selectedDateFilter,
                sortBy: sortBy,
                sortOrder: sortOrder,
                page: page,
                pageSize: pageSize
            )

            photos = response.photos
            isLoadingPhotos = false
        } catch {
            errorMessage = "加载照片失败: \(error.localizedDescription)"
            isLoadingPhotos = false
        }
    }

    /// 加载统计数据
    func loadStats(projectId: Int) async {
        isLoadingStats = true

        do {
            stats = try await service.getStats(projectId: projectId)
            isLoadingStats = false
        } catch {
            print("⚠️ 加载统计失败: \(error)")
            isLoadingStats = false
        }
    }

    /// 加载所有数据
    func loadAllData(projectId: Int) async {
        await loadPhotos(projectId: projectId)
        await loadStats(projectId: projectId)
    }

    /// 删除照片
    func deletePhoto(photoId: String, projectId: Int) async -> Bool {
        do {
            try await service.deletePhoto(photoId: photoId)
            photos.removeAll { $0.id == photoId }
            successMessage = "照片已删除"

            // 重新加载统计
            await loadStats(projectId: projectId)
            return true
        } catch {
            errorMessage = "删除照片失败: \(error.localizedDescription)"
            return false
        }
    }

    func uploadPhotos(projectId: Int, fileURLs: [URL]) async -> Bool {
        isLoadingPhotos = true
        errorMessage = nil
        successMessage = nil
        var allSuccess = true

        for fileURL in fileURLs {
            do {
                _ = try await service.uploadPhoto(projectId: projectId, fileURL: fileURL)
            } catch {
                allSuccess = false
                errorMessage = "上传照片失败: \(error.localizedDescription)"
                DebugLogger.shared.log("照片上传失败", type: .error, details: "文件=\(fileURL.path)\n错误=\(error.localizedDescription)", category: "upload.photo")
            }
        }

        await loadAllData(projectId: projectId)
        if allSuccess {
            successMessage = "已上传 \(fileURLs.count) 张照片"
        }
        isLoadingPhotos = false
        return allSuccess
    }

    /// 批量删除照片
    func batchDeletePhotos(photoIds: [String], projectId: Int) async -> Bool {
        var allSuccess = true
        for id in photoIds {
            let success = await deletePhoto(photoId: id, projectId: projectId)
            if !success {
                allSuccess = false
            }
        }
        if allSuccess {
            successMessage = "已删除 \(photoIds.count) 张照片"
        }
        return allSuccess
    }

    // MARK: - Helper Methods

    /// 过滤照片（客户端额外过滤）
    func filteredPhotos() -> [PhotoService.PhotoResponse] {
        return photos
    }

    /// 按日期分组
    func photosByDate() -> [String: [PhotoService.PhotoResponse]] {
        let dateFormatter = DateFormatter()
        dateFormatter.dateFormat = "yyyy-MM-dd"

        return Dictionary(grouping: photos) { photo in
            if let date = photo.takenAt {
                return dateFormatter.string(from: date)
            }
            return "未知日期"
        }
    }

    /// 按位置分组
    func photosByLocation() -> [String: [PhotoService.PhotoResponse]] {
        Dictionary(grouping: photos) { photo in
            photo.location ?? "未知位置"
        }
    }

    /// 按设备分组
    func photosByDevice() -> [String: [PhotoService.PhotoResponse]] {
        Dictionary(grouping: photos) { photo in
            photo.device ?? "未知设备"
        }
    }

    /// 格式化文件大小
    func formatFileSize(_ bytes: Int64) -> String {
        let formatter = ByteCountFormatter()
        formatter.allowedUnits = [.useKB, .useMB, .useGB]
        formatter.countStyle = .file
        return formatter.string(fromByteCount: bytes)
    }

    /// 格式化日期
    func formatDate(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd HH:mm"
        return formatter.string(from: date)
    }

    /// 计算照片网格列数
    func calculateColumns(for width: CGFloat) -> Int {
        let minColumnWidth: CGFloat = 200
        return max(2, Int(width / minColumnWidth))
    }

    /// 清除消息
    func clearMessages() {
        errorMessage = nil
        successMessage = nil
    }
}
