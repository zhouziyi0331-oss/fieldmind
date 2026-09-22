import SwiftUI
import Foundation

// MARK: - Backend Process Manager
@MainActor
final class BackendProcessManager: ObservableObject {
    static let shared = BackendProcessManager()

    @Published var isRunning = false
    @Published var statusMessage = "未运行"

    private var process: Process?
    private let backendPath = "/Users/alwan/FieldMind/backend"

    private init() {}

    func start() async {
        guard !isRunning else { return }

        let process = Process()
        process.currentDirectoryPath = backendPath
        process.executableURL = URL(fileURLWithPath: "/usr/bin/python3")
        process.arguments = ["-m", "uvicorn", "src.main:app", "--host", "127.0.0.1", "--port", "8013"]

        do {
            try process.run()
            self.process = process
            isRunning = true
            statusMessage = "运行中"
            DebugLogger.shared.log("后端启动成功", type: .success, category: "backend")
        } catch {
            DebugLogger.shared.log("后端启动失败", type: .error, details: error.localizedDescription, category: "backend")
            statusMessage = "启动失败"
        }
    }

    func stop() {
        process?.terminate()
        process = nil
        isRunning = false
        statusMessage = "已停止"
        DebugLogger.shared.log("后端已停止", type: .info, category: "backend")
    }

    func ensureRunning() {
        if !isRunning {
            Task { await start() }
        }
    }
}

@main
struct FieldMindApp: App {
    @StateObject private var appState = AppState()
    @NSApplicationDelegateAdaptor(AppDelegate.self) var appDelegate

    var body: some Scene {
        WindowGroup {
            WebViewMainView()
                .environmentObject(appState)
                .frame(minWidth: 1200, minHeight: 800)
        }
        .windowStyle(.hiddenTitleBar)
        .windowToolbarStyle(.unified)
        .commands {
            // 开发者工具
            CommandGroup(after: .help) {
                Button("重新加载") {
                    WebViewManager.shared.reload()
                }
                .keyboardShortcut("r", modifiers: [.command])
            }
        }
    }
}

// MARK: - App Delegate
class AppDelegate: NSObject, NSApplicationDelegate {
    private var backendManager = BackendProcessManager.shared

    func applicationDidFinishLaunching(_ notification: Notification) {
        DebugLogger.shared.log("应用启动", type: .success, category: "lifecycle")

        // 启动后端
        Task {
            await backendManager.start()
        }
    }

    func applicationWillTerminate(_ notification: Notification) {
        DebugLogger.shared.log("应用即将退出", type: .info, category: "lifecycle")
        backendManager.stop()
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool {
        return true
    }
}
