import SwiftUI
import Combine

/// 任务管理器 - 管理后台任务和进度追踪
class TaskManager: ObservableObject {
    static let shared = TaskManager()

    @Published var activeTasks: [BackgroundTask] = []
    @Published var completedTasks: [BackgroundTask] = []

    private init() {}

    /// 后台任务模型
    struct BackgroundTask: Identifiable {
        let id: String
        let type: TaskType
        let projectId: Int
        var status: TaskStatus
        var progress: Double
        let title: String
        let createdAt: Date
        var completedAt: Date?
        var errorMessage: String?

        enum TaskType: Equatable {
            case documentUpload(filename: String)
            case documentProcessing(documentId: Int)
            case keywordSearch(keyword: String)
            case creativeAnalysis(keywords: [String])
            case businessAnalysis
            case reportGeneration(reportTitle: String)
        }

        enum TaskStatus: Equatable {
            case pending
            case running
            case completed
            case failed(String)
        }

        var statusText: String {
            switch status {
            case .pending: return "等待中"
            case .running: return "处理中"
            case .completed: return "已完成"
            case .failed(let error): return "失败: \(error)"
            }
        }

        var statusColor: Color {
            switch status {
            case .pending: return .orange
            case .running: return .blue
            case .completed: return .green
            case .failed: return .red
            }
        }
    }

    // MARK: - 任务管理

    /// 添加新任务
    func addTask(_ task: BackgroundTask) {
        DispatchQueue.main.async {
            self.activeTasks.append(task)
            // 发送通知
            NotificationCenter.default.post(name: .taskAdded, object: task)
        }
    }

    /// 更新任务状态
    func updateTask(id: String, status: BackgroundTask.TaskStatus, progress: Double? = nil) {
        DispatchQueue.main.async {
            if let index = self.activeTasks.firstIndex(where: { $0.id == id }) {
                self.activeTasks[index].status = status
                if let progress = progress {
                    self.activeTasks[index].progress = progress
                }

                // 如果任务完成或失败，移到完成列表
                if case .completed = status {
                    var task = self.activeTasks[index]
                    task.completedAt = Date()
                    self.activeTasks.remove(at: index)
                    self.completedTasks.insert(task, at: 0)

                    // 发送完成通知
                    NotificationCenter.default.post(name: .taskCompleted, object: task)
                    ToastManager.shared.success(task.title + " 已完成")
                } else if case .failed(let error) = status {
                    var task = self.activeTasks[index]
                    task.completedAt = Date()
                    task.errorMessage = error
                    self.activeTasks.remove(at: index)
                    self.completedTasks.insert(task, at: 0)

                    // 发送失败通知
                    NotificationCenter.default.post(name: .taskFailed, object: task)
                    ToastManager.shared.error(task.title + " 失败")
                }
            }
        }
    }

    /// 取消任务
    func cancelTask(id: String) {
        DispatchQueue.main.async {
            if let index = self.activeTasks.firstIndex(where: { $0.id == id }) {
                var task = self.activeTasks[index]
                task.status = .failed("用户取消")
                task.completedAt = Date()
                self.activeTasks.remove(at: index)
                self.completedTasks.insert(task, at: 0)
            }
        }
    }

    /// 清空已完成任务
    func clearCompletedTasks() {
        DispatchQueue.main.async {
            self.completedTasks.removeAll()
        }
    }

    /// 获取项目的活动任务数量
    func activeTaskCount(for projectId: Int) -> Int {
        activeTasks.filter { $0.projectId == projectId }.count
    }
}

// MARK: - Notification Names
extension Notification.Name {
    static let taskAdded = Notification.Name("taskAdded")
    static let taskCompleted = Notification.Name("taskCompleted")
    static let taskFailed = Notification.Name("taskFailed")
}
