import SwiftUI

/// 独立的系统诊断窗口内容。窗口本身由 FieldMindApp 的 Window scene 管理。
struct DebugWindow: View {
    @ObservedObject private var logger = DebugLogger.shared
    @StateObject private var viewModel = DiagnosticViewModel()
    @State private var selectedLogID: UUID?
    @State private var filter = "全部"
    @State private var keyword = ""
    @State private var autoRefresh = false
    @State private var refreshTask: Task<Void, Never>?

    private let filters = ["全部", "错误", "警告", "请求", "后端", "前端"]

    private var visibleLogs: [DebugLog] {
        logger.logs.filter { log in
            let levelMatch: Bool
            switch filter {
            case "错误": levelMatch = log.type == .error
            case "警告": levelMatch = log.type == .warning
            case "请求": levelMatch = log.type == .api
            case "后端": levelMatch = log.source == "backend"
            case "前端": levelMatch = log.source != "backend"
            default: levelMatch = true
            }
            let text = "\(log.message) \(log.details ?? "") \(log.source)".lowercased()
            return levelMatch && (keyword.isEmpty || text.contains(keyword.lowercased()))
        }
    }

    private var selectedLog: DebugLog? {
        guard let selectedLogID else { return visibleLogs.last }
        return logger.logs.first(where: { $0.id == selectedLogID })
    }

    var body: some View {
        VStack(spacing: 0) {
            header
            Divider()
            controls
            Divider()
            HStack(spacing: 0) {
                logList
                    .frame(minWidth: 560, maxWidth: .infinity, maxHeight: .infinity)
                Divider()
                detailPanel
                    .frame(maxHeight: .infinity)
                    .frame(width: 360)
            }
        }
        .background(Color(NSColor.windowBackgroundColor))
        .frame(minWidth: 980, minHeight: 620)
        .task { await refresh() }
        .onChange(of: autoRefresh) { _, enabled in
            enabled ? startAutoRefresh() : stopAutoRefresh()
        }
        .onDisappear { stopAutoRefresh() }
    }

    private var header: some View {
        HStack(spacing: 10) {
            Image(systemName: "stethoscope")
                .foregroundColor(.orange)
                .font(.system(size: 18, weight: .semibold))
            VStack(alignment: .leading, spacing: 2) {
                Text("系统检验").font(.system(size: 16, weight: .semibold))
                Text(viewModel.connectionText)
                    .font(.system(size: 11))
                    .foregroundColor(viewModel.connectionColor)
            }
            Spacer()
            if let lastRefresh = viewModel.lastRefresh {
                Text("最近刷新 \(lastRefresh.formatted(date: .omitted, time: .standard))")
                    .font(.system(size: 11, design: .monospaced))
                    .foregroundColor(.secondary)
            }
            Button { Task { await refresh() } } label: {
                Label("刷新", systemImage: "arrow.clockwise")
            }
            .keyboardShortcut("r", modifiers: [.command])
            .disabled(viewModel.isRefreshing)
            Button {
                logger.clearLogs()
                selectedLogID = nil
            } label: {
                Image(systemName: "trash")
            }
            .help("清空本地诊断记录")
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 12)
    }

    private var controls: some View {
        HStack(spacing: 10) {
            Picker("过滤", selection: $filter) {
                ForEach(filters, id: \.self) { Text($0).tag($0) }
            }
            .frame(width: 100)
            TextField("搜索错误、接口、文件名或请求 ID", text: $keyword)
                .textFieldStyle(.roundedBorder)
            Toggle("自动刷新", isOn: $autoRefresh)
                .toggleStyle(.checkbox)
            Text("\(visibleLogs.count) 条 / 本地 \(logger.logs.count) 条")
                .font(.system(size: 11, design: .monospaced))
                .foregroundColor(.secondary)
        }
        .padding(10)
    }

    private var logList: some View {
        List(selection: $selectedLogID) {
            ForEach(visibleLogs) { log in
                DiagnosticRow(log: log)
                    .tag(log.id)
                    .contextMenu {
                        Button("复制完整详情") {
                            NSPasteboard.general.clearContents()
                            NSPasteboard.general.setString(log.fullText, forType: .string)
                        }
                    }
            }
        }
        .listStyle(.inset)
        .overlay {
            if viewModel.isRefreshing && visibleLogs.isEmpty {
                ProgressView("正在读取前后端真实日志…")
            } else if visibleLogs.isEmpty {
                ContentUnavailableView("暂无匹配日志", systemImage: "checkmark.circle", description: Text("刷新后会同时读取前端和后端日志"))
            }
        }
    }

    private var detailPanel: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 12) {
                if let log = selectedLog {
                    Text("错误详情").font(.system(size: 15, weight: .semibold))
                    detailRow("时间", log.timestamp.formatted(date: .complete, time: .standard))
                    detailRow("级别", log.type.title)
                    detailRow("来源", log.source)
                    detailRow("分类", log.category)
                    if let statusCode = log.statusCode { detailRow("状态码", "\(statusCode)") }
                    if let requestURL = log.requestURL { detailRow("请求地址", requestURL) }
                    if let requestID = log.requestID { detailRow("请求 ID", requestID) }
                    Text("消息").font(.system(size: 12, weight: .semibold))
                    Text(log.message).textSelection(.enabled).font(.system(size: 12))
                    if let details = log.details, !details.isEmpty {
                        Text("后端详情 / 原始响应").font(.system(size: 12, weight: .semibold))
                        Text(details)
                            .textSelection(.enabled)
                            .font(.system(size: 11, design: .monospaced))
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .padding(8)
                            .background(Color.black.opacity(0.06))
                            .cornerRadius(6)
                    }
                    Text("去重键: \(log.dedupeKey)\n重复次数: \(log.occurrenceCount)")
                        .font(.system(size: 10, design: .monospaced))
                        .foregroundColor(.secondary)
                } else {
                    Text("选择一条日志查看完整详情").foregroundColor(.secondary)
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(16)
        }
        .background(Color(NSColor.controlBackgroundColor))
    }

    private func detailRow(_ title: String, _ value: String) -> some View {
        VStack(alignment: .leading, spacing: 3) {
            Text(title).font(.system(size: 10, weight: .semibold)).foregroundColor(.secondary)
            Text(value).font(.system(size: 11, design: .monospaced)).textSelection(.enabled)
        }
    }

    private func refresh() async {
        await viewModel.refresh(logger: logger)
        if selectedLogID == nil { selectedLogID = visibleLogs.last?.id }
    }

    private func startAutoRefresh() {
        stopAutoRefresh()
        refreshTask = Task {
            while !Task.isCancelled {
                try? await Task.sleep(for: .seconds(5))
                if !Task.isCancelled { await refresh() }
            }
        }
    }

    private func stopAutoRefresh() {
        refreshTask?.cancel()
        refreshTask = nil
    }
}

struct DiagnosticRow: View {
    let log: DebugLog

    var body: some View {
        HStack(alignment: .top, spacing: 8) {
            Image(systemName: log.type.icon).foregroundColor(log.type.color).frame(width: 18)
            VStack(alignment: .leading, spacing: 3) {
                HStack(spacing: 6) {
                    Text(log.timestamp.formatted(date: .omitted, time: .standard))
                    Text(log.source)
                    if log.occurrenceCount > 1 { Text("×\(log.occurrenceCount)").foregroundColor(.orange) }
                    Spacer()
                }
                .font(.system(size: 10, design: .monospaced))
                .foregroundColor(.secondary)
                Text(log.message).font(.system(size: 12)).lineLimit(2)
            }
        }
        .padding(.vertical, 3)
    }
}

final class DiagnosticViewModel: ObservableObject {
    @Published var isRefreshing = false
    @Published var lastRefresh: Date?
    @Published var backendAvailable = false
    @Published var backendLogFile: String?

    var connectionText: String { backendAvailable ? "后端已连接，显示真实日志" : "后端不可用，显示本地日志和真实连接错误" }
    var connectionColor: Color { backendAvailable ? .green : .orange }

    @MainActor
    func refresh(logger: DebugLogger) async {
        isRefreshing = true
        defer { isRefreshing = false; lastRefresh = Date() }
        do {
            let health = try await MonitoringService.shared.getHealth()
            backendAvailable = true
            logger.log("后端健康检查: \(health.status)", type: health.status == "healthy" ? .success : .warning, details: "API=\(health.components.api), database=\(health.components.database), disk=\(health.components.disk)", source: "backend", category: "health")
        } catch {
            backendAvailable = false
            logger.log("后端健康检查失败", type: .error, details: error.localizedDescription, source: "backend", category: "health", requestURL: MonitoringService.shared.lastRequestURL)
        }
        do {
            let response = try await MonitoringService.shared.getRecentLogs(lines: 200)
            backendLogFile = response.logFile
            logger.mergeBackend(events: response.events, rawLines: response.lines)
        } catch {
            logger.log("读取后端日志失败", type: .error, details: error.localizedDescription, source: "backend", category: "monitoring", requestURL: MonitoringService.shared.lastRequestURL)
        }
    }
}


final class DebugLogger: ObservableObject {
    static let shared = DebugLogger()
    @Published private(set) var logs: [DebugLog] = []
    private let maxLogs = 300
    private init() {}

    func log(_ message: String, type: LogType = .info, details: String? = nil, source: String = "frontend", category: String = "system", requestURL: String? = nil, statusCode: Int? = nil, requestID: String? = nil) {
        Task { @MainActor in
            self.appendDeduplicated(DebugLog(message: message, type: type, details: details, source: source, category: category, requestURL: requestURL, statusCode: statusCode, requestID: requestID))
        }
    }

    @MainActor
    func mergeBackend(events: [MonitoringService.RemoteLogEvent], rawLines: [String]) {
        if events.isEmpty {
            rawLines.forEach { appendDeduplicated(DebugLog(message: $0, type: .info, details: $0, source: "backend", category: "raw")) }
        } else {
            events.forEach { appendDeduplicated(DebugLog(remote: $0)) }
        }
    }

    @MainActor func clearLogs() { logs.removeAll() }

    @MainActor
    private func appendDeduplicated(_ event: DebugLog) {
        if let index = logs.lastIndex(where: { $0.dedupeKey == event.dedupeKey }) {
            let previous = logs[index]
            if Date().timeIntervalSince(previous.timestamp) < 60 {
                var updated = previous
                updated.timestamp = event.timestamp
                updated.occurrenceCount += 1
                logs[index] = updated
                return
            }
        }
        logs.append(event)
        if logs.count > maxLogs { logs.removeFirst(logs.count - maxLogs) }
    }
}

struct DebugLog: Identifiable {
    let id = UUID()
    var timestamp: Date
    let message: String
    let type: LogType
    let details: String?
    let source: String
    let category: String
    let requestURL: String?
    let statusCode: Int?
    let requestID: String?
    let dedupeKey: String
    var occurrenceCount = 1

    init(timestamp: Date = Date(), message: String, type: LogType = .info, details: String? = nil, source: String = "frontend", category: String = "system", requestURL: String? = nil, statusCode: Int? = nil, requestID: String? = nil) {
        self.timestamp = timestamp
        self.message = message
        self.type = type
        self.details = details
        self.source = source
        self.category = category
        self.requestURL = requestURL
        self.statusCode = statusCode
        self.requestID = requestID
        self.dedupeKey = [source, category, message, requestURL ?? "", "\(statusCode ?? 0)"].joined(separator: "|")
    }

    init(remote: MonitoringService.RemoteLogEvent) {
        self.init(timestamp: remote.timestamp ?? Date(), message: remote.message, type: LogType(remote.level), details: remote.details, source: remote.source, category: remote.category, requestURL: remote.requestURL, statusCode: remote.statusCode, requestID: remote.requestID)
    }

    var fullText: String {
        var text = "[\(timestamp)] [\(type.title)] [\(source)/\(category)] \(message)"
        if let requestURL { text += "\n请求地址: \(requestURL)" }
        if let statusCode { text += "\n状态码: \(statusCode)" }
        if let requestID { text += "\n请求 ID: \(requestID)" }
        if let details { text += "\n详情:\n\(details)" }
        return text
    }
}

enum LogType: Equatable {
    case info, success, warning, error, api

    init(_ level: String) {
        switch level.uppercased() {
        case "ERROR", "CRITICAL": self = .error
        case "WARNING", "WARN": self = .warning
        case "SUCCESS": self = .success
        default: self = .info
        }
    }

    var title: String {
        switch self { case .info: return "信息"; case .success: return "成功"; case .warning: return "警告"; case .error: return "错误"; case .api: return "请求" }
    }
    var icon: String {
        switch self { case .info: return "info.circle.fill"; case .success: return "checkmark.circle.fill"; case .warning: return "exclamationmark.triangle.fill"; case .error: return "xmark.circle.fill"; case .api: return "network" }
    }
    var color: Color {
        switch self { case .info: return .blue; case .success: return .green; case .warning: return .orange; case .error: return .red; case .api: return .purple }
    }
}
