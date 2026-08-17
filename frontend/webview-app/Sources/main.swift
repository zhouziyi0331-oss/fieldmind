import Cocoa
import WebKit

class DragDropView: WKWebView {
    override func draggingEntered(_ sender: NSDraggingInfo) -> NSDragOperation {
        return .copy
    }

    override func performDragOperation(_ sender: NSDraggingInfo) -> Bool {
        let pasteboard = sender.draggingPasteboard
        guard let fileURLs = pasteboard.readObjects(forClasses: [NSURL.self], options: nil) as? [URL] else {
            return false
        }

        // 将文件转换为 base64 并传递给 JavaScript
        uploadFiles(fileURLs)
        return true
    }

    func uploadFiles(_ fileURLs: [URL]) {
        var filesData: [[String: Any]] = []

        for url in fileURLs {
            guard let data = try? Data(contentsOf: url) else { continue }
            let base64 = data.base64EncodedString()
            let fileName = url.lastPathComponent
            let mimeType = mimeTypeForPath(path: url.path)

            filesData.append([
                "name": fileName,
                "data": base64,
                "type": mimeType
            ])
        }

        // 将文件数据序列化为 JSON
        guard let jsonData = try? JSONSerialization.data(withJSONObject: filesData, options: []),
              let jsonString = String(data: jsonData, encoding: .utf8) else {
            return
        }

        let script = """
        (function() {
            const filesData = \(jsonString);
            const files = filesData.map(fd => {
                const byteCharacters = atob(fd.data);
                const byteNumbers = new Array(byteCharacters.length);
                for (let i = 0; i < byteCharacters.length; i++) {
                    byteNumbers[i] = byteCharacters.charCodeAt(i);
                }
                const byteArray = new Uint8Array(byteNumbers);
                const blob = new Blob([byteArray], {type: fd.type});
                return new File([blob], fd.name, {type: fd.type});
            });

            console.log('准备上传文件:', files.map(f => f.name));
            if (window.realUpload) {
                window.realUpload(files);
            } else {
                console.error('realUpload 函数不存在');
            }
        })();
        """

        self.evaluateJavaScript(script, completionHandler: { result, error in
            if let error = error {
                print("JavaScript 执行错误:", error)
            }
        })
    }

    func mimeTypeForPath(path: String) -> String {
        let url = URL(fileURLWithPath: path)
        let ext = url.pathExtension.lowercased()

        switch ext {
        case "mp3": return "audio/mpeg"
        case "wav": return "audio/wav"
        case "m4a": return "audio/mp4"
        case "mp4": return "video/mp4"
        case "pdf": return "application/pdf"
        case "txt", "md": return "text/plain"
        case "xlsx": return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        case "xls": return "application/vnd.ms-excel"
        case "doc": return "application/msword"
        case "docx": return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        default: return "application/octet-stream"
        }
    }

    override func draggingExited(_ sender: NSDraggingInfo?) {
        // 可选：通知 HTML 拖拽已退出
    }
}

class AppDelegate: NSObject, NSApplicationDelegate, WKNavigationDelegate, WKScriptMessageHandler {
    var window: NSWindow!
    var webView: DragDropView!

    func applicationDidFinishLaunching(_ notification: Notification) {
        // 创建窗口
        window = NSWindow(
            contentRect: NSRect(x: 0, y: 0, width: 1200, height: 800),
            styleMask: [.titled, .closable, .miniaturizable, .resizable],
            backing: .buffered,
            defer: false
        )
        window.center()
        window.title = "FieldMind"
        window.makeKeyAndOrderFront(nil)

        // 配置 WebView
        let configuration = WKWebViewConfiguration()
        configuration.preferences.setValue(true, forKey: "allowFileAccessFromFileURLs")
        configuration.setValue(true, forKey: "allowUniversalAccessFromFileURLs")

        // 添加消息处理器用于文件选择
        configuration.userContentController.add(self, name: "fileHandler")

        webView = DragDropView(frame: window.contentView!.bounds, configuration: configuration)
        webView.autoresizingMask = [.width, .height]
        webView.allowsMagnification = true
        webView.navigationDelegate = self

        // 注册拖放类型
        webView.registerForDraggedTypes([.fileURL])

        window.contentView?.addSubview(webView)

        // 加载 HTML 文件
        let htmlPath = "/Users/alwan/FieldMind/FieldMind.app/Contents/Resources/index.html"
        let htmlURL = URL(fileURLWithPath: htmlPath)
        webView.loadFileURL(htmlURL, allowingReadAccessTo: htmlURL.deletingLastPathComponent())
    }

    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        // 页面加载完成后的简单日志
        print("HTML 页面加载完成")
    }

    func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {
        if message.name == "fileHandler" && message.body as? String == "select" {
            selectFiles()
        }
    }

    func selectFiles() {
        let panel = NSOpenPanel()
        panel.allowsMultipleSelection = true
        panel.canChooseDirectories = false
        panel.canChooseFiles = true
        panel.allowedContentTypes = [.audio, .movie, .pdf, .plainText, .data]

        panel.begin { response in
            if response == .OK {
                self.webView.uploadFiles(panel.urls)
            }
        }
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool {
        return true
    }
}

// 主程序入口
let app = NSApplication.shared
let delegate = AppDelegate()
app.delegate = delegate
app.setActivationPolicy(.regular)
app.activate(ignoringOtherApps: true)
app.run()
