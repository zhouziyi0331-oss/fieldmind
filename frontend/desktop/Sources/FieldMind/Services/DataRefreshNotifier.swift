import Foundation
import Combine

/// 数据刷新通知器 - 用于在文档处理完成后通知所有视图更新
class DataRefreshNotifier: ObservableObject {
    static let shared = DataRefreshNotifier()

    @Published var shouldRefreshDashboard = false
    @Published var shouldRefreshDocuments = false
    @Published var shouldRefreshContexts = false
    @Published var shouldRefreshTimeline = false
    @Published var shouldRefreshGraph = false
    @Published var shouldRefreshReports = false

    private init() {}

    /// 当文档处理完成时调用此方法，触发所有相关视图刷新
    func notifyDocumentProcessed() {
        DispatchQueue.main.async {
            self.shouldRefreshDashboard = true
            self.shouldRefreshDocuments = true
            self.shouldRefreshContexts = true
            self.shouldRefreshTimeline = true
            self.shouldRefreshGraph = true

            // 延迟重置刷新标志
            DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {
                self.resetRefreshFlags()
            }
        }
    }

    /// 重置所有刷新标志
    func resetRefreshFlags() {
        shouldRefreshDashboard = false
        shouldRefreshDocuments = false
        shouldRefreshContexts = false
        shouldRefreshTimeline = false
        shouldRefreshGraph = false
        shouldRefreshReports = false
    }

    /// 触发特定视图刷新
    func refreshView(_ view: RefreshableView) {
        DispatchQueue.main.async {
            switch view {
            case .dashboard:
                self.shouldRefreshDashboard = true
            case .documents:
                self.shouldRefreshDocuments = true
            case .contexts:
                self.shouldRefreshContexts = true
            case .timeline:
                self.shouldRefreshTimeline = true
            case .graph:
                self.shouldRefreshGraph = true
            case .reports:
                self.shouldRefreshReports = true
            }
        }
    }
}

enum RefreshableView {
    case dashboard
    case documents
    case contexts
    case timeline
    case graph
    case reports
}
