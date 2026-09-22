//
//  DocumentViewModel_Merged.swift
//  FieldMind
//
//  深度整合 - 合并自主版本和 Native 版本
//  Generated: Sat Sep 19 11:21:01 CST 2026
//

import Foundation
import SwiftUI

// ========================================
// 主实现（来自主项目）
// ========================================


@MainActor
class DocumentViewModel: ObservableObject {
    @Published var documents: [DocumentStatusResponse] = []
    @Published var isLoadingDocuments = false
    @Published var isUploading = false
    @Published var uploadProgress: Double = 0
    @Published var errorMessage: String?

    private let service = DocumentService.shared
    private var statusPollingTask: Task<Void, Never>?
    private var appState: AppState?

    func setAppState(_ appState: AppState) {
        self.appState = appState
    }

    /// 加载项目的所有文档
    func loadDocuments(projectId: Int) async {
        guard projectId > 0 else {
            DebugLogger.shared.log("⚠️ 无效的项目ID，跳过加载文档", type: .warning)
            return
        }

        isLoadingDocuments = true
        errorMessage = nil

        do {
            let statusList = try await service.getDocumentsStatus(projectId: projectId)
            self.documents = statusList
            DebugLogger.shared.log("✅ 加载了 \(statusList.count) 个文档", type: .success)
        } catch {
            self.errorMessage = "加载文档失败: \(error.localizedDescription)"
            DebugLogger.shared.log("❌ 加载文档失败: \(error.localizedDescription)", type: .error)
        }

        isLoadingDocuments = false
    }

    /// 上传文件
    func uploadFile(projectId: Int, fileURL: URL, autoProcess: Bool = true) async {
        isUploading = true
        uploadProgress = 0
        errorMessage = nil

        do {
            // 模拟上传进度
            let progressTask = Task {
                for i in 1...9 {
                    try? await Task.sleep(nanoseconds: 100_000_000) // 0.1秒
                    await MainActor.run {
                        self.uploadProgress = Double(i) / 10.0
                    }
                }
            }

            let response = try await service.uploadDocument(
                projectId: projectId,
                fileURL: fileURL,
                autoProcess: autoProcess
            )

            progressTask.cancel()
            uploadProgress = 1.0

            // 将新上传的文档添加到列表
            let newDoc = DocumentStatusResponse(
                id: response.id,
                filename: response.filename,
                status: response.status,
                chunkCount: 0,
                vectorized: false,
                skillsCompleted: false,
                createdAt: ISO8601DateFormatter().string(from: Date()),
                wordCount: nil,
                fileType: response.fileType,
                errorMessage: nil
            )
            if !documents.contains(where: { $0.id == newDoc.id }) {
                documents.insert(newDoc, at: 0)
            }
            // 文件已经真实落入 project_documents 和磁盘，立即通知文件管理器刷新；
            // 后续处理完成状态仍由轮询继续更新。
            appState?.notifyDocumentUpdated()

            // 以服务端主表为准，避免去重、重试或状态转换后本地临时记录失真。
            if let statusList = try? await service.getDocumentsStatus(projectId: projectId) {
                documents = statusList
            }

            // 开始轮询状态
            startStatusPolling(projectId: projectId)

        } catch {
            self.errorMessage = "上传失败: \(error.localizedDescription)"
        }

        isUploading = false
        uploadProgress = 0
    }

    /// 批量上传统一排队，避免多个任务同时覆盖同一个上传状态。
    func uploadFiles(projectId: Int, fileURLs: [URL], autoProcess: Bool = true) async {
        for fileURL in fileURLs {
            if Task.isCancelled { break }
            await uploadFile(projectId: projectId, fileURL: fileURL, autoProcess: autoProcess)
        }
    }

    /// 删除文档
    func deleteDocument(documentId: Int, projectId: Int) async {
        do {
            try await service.deleteDocument(documentId: documentId)
            documents.removeAll { $0.id == documentId }
        } catch {
            self.errorMessage = "删除失败: \(error.localizedDescription)"
        }
    }

    /// 开始轮询文档处理状态
    func startStatusPolling(projectId: Int) {
        // 取消之前的轮询任务
        statusPollingTask?.cancel()

        statusPollingTask = Task {
            while !Task.isCancelled {
                // 检查是否还有处理中的文档
                let hasProcessing = documents.contains { doc in
                    doc.status == "pending" || doc.status == "processing"
                }

                if !hasProcessing {
                    break
                }

                // 等待3秒
                try? await Task.sleep(nanoseconds: 3_000_000_000)

                if Task.isCancelled {
                    break
                }

                // 刷新状态
                do {
                    let statusList = try await service.getDocumentsStatus(projectId: projectId)

                    // 检查是否有文档状态从processing变为completed
                    let oldProcessingIds = Set(documents.filter {
                        $0.status == "pending" || $0.status == "processing"
                    }.map { $0.id })
                    let newCompletedIds = Set(statusList.filter { $0.status == "completed" }.map { $0.id })
                    let justCompleted = oldProcessingIds.intersection(newCompletedIds)

                    await MainActor.run {
                        self.documents = statusList

                        // 文件树和概览都需要在状态变化后刷新。
                        if !justCompleted.isEmpty {
                            DebugLogger.shared.log("✅ \(justCompleted.count) 个文档处理完成，触发全局数据刷新", type: .success)
                        }
                        appState?.notifyDocumentUpdated()
                    }
                } catch {
                    // 轮询错误静默处理
                    break
                }
            }
        }
    }

    /// 停止轮询
    func stopStatusPolling() {
        statusPollingTask?.cancel()
        statusPollingTask = nil
    }

    deinit {
        statusPollingTask?.cancel()
    }
}

// ========================================
// Native 版本的扩展功能
// ========================================
// TODO: 手动审查并整合以下功能

/*

@MainActor
class DocumentViewModel: ObservableObject {
    @Published var documents: [DocumentStatusResponse] = []
    @Published var isLoadingDocuments = false
    @Published var isUploading = false
    @Published var uploadProgress: Double = 0
    @Published var errorMessage: String?

    private let service = DocumentService.shared
    private var statusPollingTask: Task<Void, Never>?
    private var appState: AppState?

    func setAppState(_ appState: AppState) {
        self.appState = appState
    }

    /// 加载项目的所有文档
    func loadDocuments(projectId: Int) async {
        guard projectId > 0 else {
            DebugLogger.shared.log("⚠️ 无效的项目ID，跳过加载文档", type: .warning)
            return
        }

        isLoadingDocuments = true
        errorMessage = nil

        do {
            let statusList = try await service.getDocumentsStatus(projectId: projectId)
            self.documents = statusList
            DebugLogger.shared.log("✅ 加载了 \(statusList.count) 个文档", type: .success)
        } catch {
            self.errorMessage = "加载文档失败: \(error.localizedDescription)"
            DebugLogger.shared.log("❌ 加载文档失败: \(error.localizedDescription)", type: .error)
        }

        isLoadingDocuments = false
    }

    /// 上传文件
    func uploadFile(projectId: Int, fileURL: URL, autoProcess: Bool = true) async {
        isUploading = true
        uploadProgress = 0
        errorMessage = nil

        do {
            // 模拟上传进度
            let progressTask = Task {
                for i in 1...9 {
                    try? await Task.sleep(nanoseconds: 100_000_000) // 0.1秒
                    await MainActor.run {
                        self.uploadProgress = Double(i) / 10.0
                    }
                }
            }

            let response = try await service.uploadDocument(
                projectId: projectId,
                fileURL: fileURL,
                autoProcess: autoProcess
            )

            progressTask.cancel()
            uploadProgress = 1.0

            // 将新上传的文档添加到列表
            let newDoc = DocumentStatusResponse(
                id: response.id,
                filename: response.filename,
                status: response.status,
                chunkCount: 0,
                vectorized: false,
                skillsCompleted: false,
                createdAt: ISO8601DateFormatter().string(from: Date()),
                wordCount: nil,
                fileType: response.fileType,
                errorMessage: nil
            )
            if !documents.contains(where: { $0.id == newDoc.id }) {
                documents.insert(newDoc, at: 0)
            }
            // 文件已经真实落入 project_documents 和磁盘，立即通知文件管理器刷新；
            // 后续处理完成状态仍由轮询继续更新。
            appState?.notifyDocumentUpdated()

            // 以服务端主表为准，避免去重、重试或状态转换后本地临时记录失真。
            if let statusList = try? await service.getDocumentsStatus(projectId: projectId) {
                documents = statusList
            }

            // 开始轮询状态
            startStatusPolling(projectId: projectId)

        } catch {
            self.errorMessage = "上传失败: \(error.localizedDescription)"
        }

        isUploading = false
        uploadProgress = 0
    }

    /// 批量上传统一排队，避免多个任务同时覆盖同一个上传状态。
    func uploadFiles(projectId: Int, fileURLs: [URL], autoProcess: Bool = true) async {
        for fileURL in fileURLs {
            if Task.isCancelled { break }
            await uploadFile(projectId: projectId, fileURL: fileURL, autoProcess: autoProcess)
        }
    }

    /// 删除文档
    func deleteDocument(documentId: Int, projectId: Int) async {
        do {
            try await service.deleteDocument(documentId: documentId)
            documents.removeAll { $0.id == documentId }
        } catch {
            self.errorMessage = "删除失败: \(error.localizedDescription)"
        }
    }

    /// 开始轮询文档处理状态
    func startStatusPolling(projectId: Int) {
        // 取消之前的轮询任务
        statusPollingTask?.cancel()

        statusPollingTask = Task {
            while !Task.isCancelled {
                // 检查是否还有处理中的文档
                let hasProcessing = documents.contains { doc in
                    doc.status == "pending" || doc.status == "processing"
                }

                if !hasProcessing {
                    break
                }

                // 等待3秒
                try? await Task.sleep(nanoseconds: 3_000_000_000)

                if Task.isCancelled {
                    break
                }

                // 刷新状态
                do {
                    let statusList = try await service.getDocumentsStatus(projectId: projectId)

                    // 检查是否有文档状态从processing变为completed
                    let oldProcessingIds = Set(documents.filter {
                        $0.status == "pending" || $0.status == "processing"
                    }.map { $0.id })
                    let newCompletedIds = Set(statusList.filter { $0.status == "completed" }.map { $0.id })
                    let justCompleted = oldProcessingIds.intersection(newCompletedIds)

                    await MainActor.run {
                        self.documents = statusList

                        // 文件树和概览都需要在状态变化后刷新。
                        if !justCompleted.isEmpty {
                            DebugLogger.shared.log("✅ \(justCompleted.count) 个文档处理完成，触发全局数据刷新", type: .success)
                        }
                        appState?.notifyDocumentUpdated()
                    }
                } catch {
                    // 轮询错误静默处理
                    break
                }
            }
        }
    }

    /// 停止轮询
    func stopStatusPolling() {
        statusPollingTask?.cancel()
        statusPollingTask = nil
    }

    deinit {
        statusPollingTask?.cancel()
    }
}
*/

