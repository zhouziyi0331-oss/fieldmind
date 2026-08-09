import Foundation
import Combine

/// WebSocket 服务 - 实时接收后端通知
class WebSocketService: ObservableObject {
    static let shared = WebSocketService()

    @Published var isConnected = false
    @Published var lastMessage: WebSocketMessage?

    private var webSocketTask: URLSessionWebSocketTask?
    private var currentProjectId: Int?
    private var reconnectTimer: Timer?

    struct WebSocketMessage: Codable {
        let type: String
        let documentId: Int?
        let status: String?
        let details: [String: AnyCodable]?
        let stats: DashboardStatsResponse?
        let timestamp: String?

        enum CodingKeys: String, CodingKey {
            case type
            case documentId = "document_id"
            case status
            case details
            case stats
            case timestamp
        }
    }

    // MARK: - 连接管理

    func connect(projectId: Int) {
        // 如果已经连接到同一个项目，不重复连接
        if isConnected && currentProjectId == projectId {
            return
        }

        // 断开旧连接
        disconnect()

        currentProjectId = projectId

        let urlString = "ws://localhost:8000/ws/\(projectId)"
        guard let url = URL(string: urlString) else {
            print("❌ WebSocket URL 无效: \(urlString)")
            return
        }

        print("🔌 正在连接 WebSocket: \(urlString)")

        webSocketTask = URLSession.shared.webSocketTask(with: url)
        webSocketTask?.resume()

        isConnected = true

        // 开始接收消息
        receiveMessage()

        // 发送 ping 保持连接
        startPingTimer()
    }

    func disconnect() {
        webSocketTask?.cancel(with: .goingAway, reason: nil)
        webSocketTask = nil
        isConnected = false
        currentProjectId = nil
        reconnectTimer?.invalidate()
        reconnectTimer = nil

        print("🔌 WebSocket 已断开")
    }

    // MARK: - 消息接收

    private func receiveMessage() {
        webSocketTask?.receive { [weak self] result in
            guard let self = self else { return }

            switch result {
            case .success(let message):
                self.handleMessage(message)
                // 继续监听下一条消息
                self.receiveMessage()

            case .failure(let error):
                print("❌ WebSocket 接收消息失败: \(error)")
                self.isConnected = false

                // 尝试重连
                self.scheduleReconnect()
            }
        }
    }

    private func handleMessage(_ message: URLSessionWebSocketTask.Message) {
        switch message {
        case .string(let text):
            print("📩 收到 WebSocket 消息: \(text)")

            // 解析 JSON
            if let data = text.data(using: .utf8) {
                do {
                    let decoder = JSONDecoder()
                    let wsMessage = try decoder.decode(WebSocketMessage.self, from: data)

                    DispatchQueue.main.async {
                        self.lastMessage = wsMessage
                        self.processMessage(wsMessage)
                    }
                } catch {
                    print("❌ 解析 WebSocket 消息失败: \(error)")
                }
            }

        case .data(let data):
            print("📩 收到 WebSocket 二进制消息: \(data.count) bytes")

        @unknown default:
            break
        }
    }

    private func processMessage(_ message: WebSocketMessage) {
        print("⚡ 处理 WebSocket 消息: type=\(message.type)")

        switch message.type {
        case "connected":
            print("✅ WebSocket 连接成功")

        case "document_status":
            // 文档状态变化
            if let docId = message.documentId, let status = message.status {
                print("📄 文档 \(docId) 状态更新: \(status)")

                // 通知 ProjectDataManager 刷新文档列表
                DispatchQueue.main.async {
                    ProjectDataManager.shared.refreshDocuments()

                    // 如果处理完成，刷新所有数据
                    if status == "completed" {
                        ProjectDataManager.shared.refreshAllData()
                    }
                }
            }

        case "project_stats":
            // 项目统计更新
            if let stats = message.stats {
                print("📊 项目统计更新")

                DispatchQueue.main.async {
                    ProjectDataManager.shared.dashboardStats = stats
                }
            }

        default:
            print("⚠️ 未知的消息类型: \(message.type)")
        }
    }

    // MARK: - 心跳保持

    private func startPingTimer() {
        reconnectTimer?.invalidate()
        reconnectTimer = Timer.scheduledTimer(withTimeInterval: 30, repeats: true) { [weak self] _ in
            self?.sendPing()
        }
    }

    private func sendPing() {
        webSocketTask?.sendPing { error in
            if let error = error {
                print("❌ WebSocket ping 失败: \(error)")
            }
        }
    }

    // MARK: - 重连机制

    private func scheduleReconnect() {
        guard let projectId = currentProjectId else { return }

        print("🔄 将在 5 秒后重连...")

        DispatchQueue.main.asyncAfter(deadline: .now() + 5) { [weak self] in
            self?.connect(projectId: projectId)
        }
    }
}

// MARK: - AnyCodable 辅助类型

struct AnyCodable: Codable {
    let value: Any

    init(_ value: Any) {
        self.value = value
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()

        if let intValue = try? container.decode(Int.self) {
            value = intValue
        } else if let doubleValue = try? container.decode(Double.self) {
            value = doubleValue
        } else if let stringValue = try? container.decode(String.self) {
            value = stringValue
        } else if let boolValue = try? container.decode(Bool.self) {
            value = boolValue
        } else if container.decodeNil() {
            value = NSNull()
        } else {
            throw DecodingError.dataCorruptedError(in: container, debugDescription: "Cannot decode value")
        }
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()

        if let intValue = value as? Int {
            try container.encode(intValue)
        } else if let doubleValue = value as? Double {
            try container.encode(doubleValue)
        } else if let stringValue = value as? String {
            try container.encode(stringValue)
        } else if let boolValue = value as? Bool {
            try container.encode(boolValue)
        } else if value is NSNull {
            try container.encodeNil()
        }
    }
}
