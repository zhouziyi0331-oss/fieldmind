import SwiftUI

struct DebugWindow: View {
    @ObservedObject var logger = DebugLogger.shared
    @State private var isExpanded = true
    @State private var windowPosition: CGPoint = CGPoint(x: 300, y: 100)
    @State private var dragOffset: CGSize = .zero

    var body: some View {
        VStack(spacing: 0) {
            // 标题栏 - 可拖动
            HStack {
                Image(systemName: "ant.circle.fill")
                    .foregroundColor(.orange)
                Text("调试日志")
                    .font(.system(size: 12, weight: .semibold))

                Spacer()

                Button(action: { logger.clearLogs() }) {
                    Image(systemName: "trash")
                        .font(.system(size: 11))
                }
                .buttonStyle(PlainButtonStyle())
                .foregroundColor(.gray)

                Button(action: { isExpanded.toggle() }) {
                    Image(systemName: isExpanded ? "chevron.down" : "chevron.right")
                        .font(.system(size: 11))
                }
                .buttonStyle(PlainButtonStyle())
                .foregroundColor(.gray)
            }
            .padding(8)
            .background(Color(NSColor.windowBackgroundColor))
            .contentShape(Rectangle())
            .gesture(
                DragGesture()
                    .onChanged { value in
                        dragOffset = value.translation
                    }
                    .onEnded { value in
                        windowPosition.x += value.translation.width
                        windowPosition.y += value.translation.height
                        dragOffset = .zero
                    }
            )

            if isExpanded {
                Divider()

                ScrollViewReader { proxy in
                    ScrollView {
                        LazyVStack(alignment: .leading, spacing: 4) {
                            ForEach(logger.logs) { log in
                                LogEntryView(log: log)
                                    .id(log.id)
                            }
                        }
                        .padding(8)
                    }
                    .frame(height: 250)
                    .onChange(of: logger.logs.count) { _ in
                        if let lastLog = logger.logs.last {
                            withAnimation {
                                proxy.scrollTo(lastLog.id, anchor: .bottom)
                            }
                        }
                    }
                }
            }
        }
        .frame(width: 450)
        .background(Color(NSColor.windowBackgroundColor))
        .cornerRadius(8)
        .shadow(color: Color.black.opacity(0.3), radius: 10, x: 0, y: 5)
        .offset(dragOffset)
        .position(windowPosition)
    }
}

struct LogEntryView: View {
    let log: DebugLog
    @State private var isExpanded = false

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack(spacing: 6) {
                // 时间戳
                Text(log.timestamp, style: .time)
                    .font(.system(size: 9, design: .monospaced))
                    .foregroundColor(.gray)

                // 类型图标
                Image(systemName: log.type.icon)
                    .font(.system(size: 9))
                    .foregroundColor(log.type.color)

                // 消息
                Text(log.message)
                    .font(.system(size: 10))
                    .lineLimit(isExpanded ? nil : 1)

                Spacer()

                if log.details != nil {
                    Button(action: { isExpanded.toggle() }) {
                        Image(systemName: isExpanded ? "chevron.up" : "chevron.down")
                            .font(.system(size: 8))
                    }
                    .buttonStyle(PlainButtonStyle())
                    .foregroundColor(.gray)
                }
            }

            if isExpanded, let details = log.details {
                Text(details)
                    .font(.system(size: 9, design: .monospaced))
                    .foregroundColor(.secondary)
                    .padding(6)
                    .background(Color.black.opacity(0.05))
                    .cornerRadius(4)
            }
        }
        .padding(.vertical, 2)
    }
}

// MARK: - Debug Logger

class DebugLogger: ObservableObject {
    static let shared = DebugLogger()

    @Published var logs: [DebugLog] = []

    private init() {}

    func log(_ message: String, type: LogType = .info, details: String? = nil) {
        DispatchQueue.main.async {
            let log = DebugLog(message: message, type: type, details: details)
            self.logs.append(log)

            // 保持最多100条日志
            if self.logs.count > 100 {
                self.logs.removeFirst()
            }
        }
    }

    func clearLogs() {
        logs.removeAll()
    }
}

// MARK: - Models

struct DebugLog: Identifiable {
    let id = UUID()
    let timestamp = Date()
    let message: String
    let type: LogType
    let details: String?
}

enum LogType {
    case info
    case success
    case warning
    case error
    case api

    var icon: String {
        switch self {
        case .info: return "info.circle.fill"
        case .success: return "checkmark.circle.fill"
        case .warning: return "exclamationmark.triangle.fill"
        case .error: return "xmark.circle.fill"
        case .api: return "network"
        }
    }

    var color: Color {
        switch self {
        case .info: return .blue
        case .success: return .green
        case .warning: return .orange
        case .error: return .red
        case .api: return .purple
        }
    }
}
