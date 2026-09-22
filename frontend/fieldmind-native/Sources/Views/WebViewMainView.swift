import SwiftUI
import WebKit
import UserNotifications

/// 使用 WebKit 加载 React 前端的新主视图
struct WebViewMainView: View {
    @EnvironmentObject var appState: AppState
    @StateObject private var webViewManager = WebViewManager.shared
    @State private var isLoading = true
    @State private var loadError: String?

    var body: some View {
        ZStack {
            // WebView 容器
            WebViewContainer(
                manager: webViewManager,
                isLoading: $isLoading,
                loadError: $loadError
            )
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .opacity(isLoading ? 0 : 1)
            .animation(.easeInOut(duration: 0.3), value: isLoading)

            // 加载指示器
            if isLoading {
                VStack(spacing: 20) {
                    ProgressView()
                        .scaleEffect(1.5)
                    Text("正在加载 FieldMind...")
                        .font(.system(size: 16, weight: .medium))
                        .foregroundColor(.secondary)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
                .background(Color(NSColor.windowBackgroundColor))
            }

            // 错误提示
            if let error = loadError {
                VStack(spacing: 20) {
                    Image(systemName: "exclamationmark.triangle")
                        .font(.system(size: 48))
                        .foregroundColor(.red)

                    Text("加载失败")
                        .font(.system(size: 20, weight: .bold))

                    Text(error)
                        .font(.system(size: 14))
                        .foregroundColor(.secondary)
                        .multilineTextAlignment(.center)
                        .padding(.horizontal, 40)

                    HStack(spacing: 12) {
                        Button("重试") {
                            loadError = nil
                            isLoading = true
                            webViewManager.reload()
                        }
                        .buttonStyle(.borderedProminent)

                        Button("打开开发者工具") {
                            webViewManager.openDevTools()
                        }
                        .buttonStyle(.bordered)
                    }
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
                .background(Color(NSColor.windowBackgroundColor))
            }
        }
        .onAppear {
            // 确保后端运行
            BackendProcessManager.shared.ensureRunning()

            // 清除缓存
            webViewManager.clearCache()

            // 延迟加载前端
            DispatchQueue.main.asyncAfter(deadline: .now() + 2.5) {
                webViewManager.loadFrontend()
            }
        }
    }
}

/// WebView 容器
struct WebViewContainer: NSViewRepresentable {
    let manager: WebViewManager
    @Binding var isLoading: Bool
    @Binding var loadError: String?

    func makeNSView(context: Context) -> WKWebView {
        let webView = manager.webView
        webView.navigationDelegate = context.coordinator
        return webView
    }

    func updateNSView(_ nsView: WKWebView, context: Context) {
        // 更新逻辑
    }

    func makeCoordinator() -> Coordinator {
        Coordinator(self)
    }

    class Coordinator: NSObject, WKNavigationDelegate {
        var parent: WebViewContainer

        init(_ parent: WebViewContainer) {
            self.parent = parent
        }

        func webView(_ webView: WKWebView, didStartProvisionalNavigation navigation: WKNavigation!) {
            DispatchQueue.main.async {
                self.parent.isLoading = true
                self.parent.loadError = nil
            }
        }

        func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
            DispatchQueue.main.async {
                self.parent.isLoading = false
                self.parent.loadError = nil
            }
            DebugLogger.shared.log("前端加载成功", type: .success, category: "webview")
        }

        func webView(_ webView: WKWebView, didFail navigation: WKNavigation!, withError error: Error) {
            DispatchQueue.main.async {
                self.parent.isLoading = false
                self.parent.loadError = "导航失败: \(error.localizedDescription)"
            }
            DebugLogger.shared.log("前端加载失败", type: .error, details: error.localizedDescription, category: "webview")
        }

        func webView(_ webView: WKWebView, didFailProvisionalNavigation navigation: WKNavigation!, withError error: Error) {
            DispatchQueue.main.async {
                self.parent.isLoading = false
                self.parent.loadError = "加载失败: \(error.localizedDescription)"
            }
            DebugLogger.shared.log("前端初始加载失败", type: .error, details: error.localizedDescription, category: "webview")
        }

        // 处理 JavaScript 警告和确认
        func webView(_ webView: WKWebView, runJavaScriptAlertPanelWithMessage message: String,
                     initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping () -> Void) {
            let alert = NSAlert()
            alert.messageText = "FieldMind"
            alert.informativeText = message
            alert.alertStyle = .informational
            alert.addButton(withTitle: "确定")
            alert.runModal()
            completionHandler()
        }

        func webView(_ webView: WKWebView, runJavaScriptConfirmPanelWithMessage message: String,
                     initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping (Bool) -> Void) {
            let alert = NSAlert()
            alert.messageText = "FieldMind"
            alert.informativeText = message
            alert.alertStyle = .warning
            alert.addButton(withTitle: "确定")
            alert.addButton(withTitle: "取消")
            let response = alert.runModal()
            completionHandler(response == .alertFirstButtonReturn)
        }
    }
}

/// WebView 管理器 - 单例
@MainActor
class WebViewManager: ObservableObject {
    static let shared = WebViewManager()

    @Published var webView: WKWebView
    private var devToolsWindow: NSWindow?

    private init() {
        // 配置 WebView
        let configuration = WKWebViewConfiguration()
        let contentController = WKUserContentController()

        // 注入 JavaScript 桥接
        let bridgeScript = """
        window.FieldMindNative = {
            platform: 'macos',
            version: '3.0',

            // 通知 Native 应用
            notify: function(message) {
                window.webkit.messageHandlers.nativeNotify.postMessage(message);
            },

            // 请求原生功能
            requestNativeAction: function(action, params) {
                window.webkit.messageHandlers.nativeAction.postMessage({
                    action: action,
                    params: params
                });
            },

            // 获取系统信息
            getSystemInfo: function() {
                const apiURL = window.localStorage.getItem('fieldmind_api_url') || 'http://127.0.0.1:8013';
                return {
                    platform: 'macos',
                    version: '3.0',
                    apiBaseURL: apiURL
                };
            }
        };

        // 拦截 console.log 发送到 Native
        (function() {
            const originalLog = console.log;
            const originalError = console.error;
            const originalWarn = console.warn;

            console.log = function(...args) {
                originalLog.apply(console, args);
                window.webkit.messageHandlers.consoleLog.postMessage({
                    level: 'log',
                    message: args.map(String).join(' ')
                });
            };

            console.error = function(...args) {
                originalError.apply(console, args);
                window.webkit.messageHandlers.consoleLog.postMessage({
                    level: 'error',
                    message: args.map(String).join(' ')
                });
            };

            console.warn = function(...args) {
                originalWarn.apply(console, args);
                window.webkit.messageHandlers.consoleLog.postMessage({
                    level: 'warn',
                    message: args.map(String).join(' ')
                });
            };
        })();
        """

        let userScript = WKUserScript(
            source: bridgeScript,
            injectionTime: .atDocumentStart,
            forMainFrameOnly: false
        )
        contentController.addUserScript(userScript)

        configuration.userContentController = contentController
        configuration.preferences.setValue(true, forKey: "developerExtrasEnabled")

        // 启用本地存储
        configuration.websiteDataStore = .default()

        self.webView = WKWebView(frame: .zero, configuration: configuration)
        self.webView.allowsBackForwardNavigationGestures = true

        // 添加消息处理器
        contentController.add(MessageHandler(), name: "nativeNotify")
        contentController.add(MessageHandler(), name: "nativeAction")
        contentController.add(ConsoleLogHandler(), name: "consoleLog")
    }

    /// 加载前端
    func loadFrontend() {
        let frontendURL: String

        // 🔥 临时强制使用开发服务器进行调试
        let useDev = true

        // 检查是否使用开发服务器
        if useDev || ProcessInfo.processInfo.environment["FIELDMIND_DEV"] == "true" {
            frontendURL = "http://localhost:3000"
            DebugLogger.shared.log("使用开发服务器", type: .info, details: frontendURL, category: "webview")

            if let url = URL(string: frontendURL) {
                webView.load(URLRequest(url: url))
                return
            }
        } else {
            // 使用打包的前端 - 从应用 Bundle 加载
            if let bundlePath = Bundle.main.resourcePath {
                let distPath = "\(bundlePath)/frontend"
                let indexPath = "\(distPath)/index.html"

                if FileManager.default.fileExists(atPath: indexPath) {
                    if let url = URL(string: "file://\(indexPath)") {
                        // 使用 loadFileURL 并授予目录访问权限
                        let baseURL = URL(fileURLWithPath: distPath, isDirectory: true)
                        webView.loadFileURL(url, allowingReadAccessTo: baseURL)
                        DebugLogger.shared.log("使用 Bundle 前端", type: .info, details: indexPath, category: "webview")
                        return
                    }
                }
            }

            // 回退到开发路径
            let distPath = "/Users/alwan/FieldMind/frontend/dist"
            let indexPath = "\(distPath)/index.html"

            if FileManager.default.fileExists(atPath: indexPath) {
                if let url = URL(string: "file://\(indexPath)") {
                    let baseURL = URL(fileURLWithPath: distPath, isDirectory: true)
                    webView.loadFileURL(url, allowingReadAccessTo: baseURL)
                    DebugLogger.shared.log("使用打包前端", type: .info, details: indexPath, category: "webview")
                }
            } else {
                DebugLogger.shared.log("前端文件不存在", type: .error, details: indexPath, category: "webview")
            }
        }
    }

    /// 清除缓存
    func clearCache() {
        let dataStore = WKWebsiteDataStore.default()
        let dataTypes = WKWebsiteDataStore.allWebsiteDataTypes()

        dataStore.fetchDataRecords(ofTypes: dataTypes) { records in
            dataStore.removeData(ofTypes: dataTypes, for: records) {
                DebugLogger.shared.log("WebView 缓存已清除", type: .info, category: "webview")
            }
        }
    }

    /// 重新加载
    func reload() {
        webView.reload()
    }

    /// 打开开发者工具
    func openDevTools() {
        // macOS WebKit 开发者工具需要右键菜单
        let alert = NSAlert()
        alert.messageText = "开发者工具"
        alert.informativeText = "请在 WebView 中右键点击，选择 '检查元素' 来打开开发者工具。\n\n提示：需要在偏好设置中启用 '在菜单栏中显示开发菜单'。"
        alert.alertStyle = .informational
        alert.addButton(withTitle: "确定")
        alert.runModal()
    }

    /// 执行 JavaScript
    func evaluateJavaScript(_ script: String, completion: ((Result<Any, Error>) -> Void)? = nil) {
        webView.evaluateJavaScript(script) { result, error in
            if let error = error {
                completion?(.failure(error))
            } else if let result = result {
                completion?(.success(result))
            }
        }
    }

    /// 注入认证 Token
    func injectAuthToken(_ token: String) {
        let script = """
        localStorage.setItem('token', '\(token)');
        window.dispatchEvent(new Event('storage'));
        """
        evaluateJavaScript(script)
    }

    /// 导航到指定页面
    func navigateTo(path: String) {
        let script = """
        if (window.location.pathname !== '\(path)') {
            window.history.pushState(null, '', '\(path)');
            window.dispatchEvent(new PopStateEvent('popstate'));
        }
        """
        evaluateJavaScript(script)
    }
}

/// 消息处理器
class MessageHandler: NSObject, WKScriptMessageHandler {
    func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {
        DebugLogger.shared.log(
            "收到前端消息",
            type: .info,
            details: "name: \(message.name)\nbody: \(message.body)",
            category: "webview.bridge"
        )

        if message.name == "nativeNotify" {
            if let text = message.body as? String {
                ToastManager.shared.show(.info, message: text)
            }
        } else if message.name == "nativeAction" {
            if let dict = message.body as? [String: Any],
               let action = dict["action"] as? String {
                handleNativeAction(action, params: dict["params"])
            }
        }
    }

    private func handleNativeAction(_ action: String, params: Any?) {
        DebugLogger.shared.log(
            "处理原生操作",
            type: .info,
            details: "action: \(action)\nparams: \(String(describing: params))",
            category: "webview.action"
        )

        switch action {
        case "selectFile":
            // 打开文件选择器
            selectFile()
        case "openExternal":
            // 打开外部链接
            if let urlString = params as? String, let url = URL(string: urlString) {
                NSWorkspace.shared.open(url)
            }
        case "showNotification":
            // 显示系统通知
            if let message = params as? String {
                showNotification(message)
            }
        default:
            break
        }
    }

    private func selectFile() {
        let panel = NSOpenPanel()
        panel.allowsMultipleSelection = true
        panel.canChooseDirectories = false
        panel.canChooseFiles = true

        panel.begin { response in
            if response == .OK {
                let paths = panel.urls.map { $0.path }
                let script = """
                window.dispatchEvent(new CustomEvent('nativeFileSelected', {
                    detail: { files: \(paths) }
                }));
                """
                WebViewManager.shared.evaluateJavaScript(script)
            }
        }
    }

    private func showNotification(_ message: String) {
        let center = UNUserNotificationCenter.current()

        // 请求通知权限
        center.requestAuthorization(options: [.alert, .sound]) { granted, error in
            guard granted else { return }

            let content = UNMutableNotificationContent()
            content.title = "FieldMind"
            content.body = message
            content.sound = .default

            let request = UNNotificationRequest(
                identifier: UUID().uuidString,
                content: content,
                trigger: nil
            )

            center.add(request) { error in
                if let error = error {
                    print("通知发送失败: \(error)")
                }
            }
        }
    }
}

/// Console Log 处理器
class ConsoleLogHandler: NSObject, WKScriptMessageHandler {
    func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {
        if let dict = message.body as? [String: String],
           let level = dict["level"],
           let text = dict["message"] {
            let logType: LogType = {
                switch level {
                case "error": return .error
                case "warn": return .warning
                default: return .info
                }
            }()

            DebugLogger.shared.log(
                "前端Console",
                type: logType,
                details: text,
                category: "webview.console"
            )
        }
    }
}
