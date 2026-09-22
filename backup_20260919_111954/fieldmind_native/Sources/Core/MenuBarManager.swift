import SwiftUI
import AppKit

class MenuBarManager: NSObject, ObservableObject {
    static let shared = MenuBarManager()

    private var statusItem: NSStatusItem?
    private var popover: NSPopover?
    private var didSetup = false
    @Published var isMenuBarMode = false

    override private init() {
        super.init()
    }

    func setupMenuBar(appState: AppState) {
        guard !didSetup else { return }
        didSetup = true

        // 创建状态栏项
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)

        if let button = statusItem?.button {
            // 设置图标
            if let image = NSImage(systemSymbolName: "brain.head.profile", accessibilityDescription: "FieldMind") {
                image.size = NSSize(width: 18, height: 18)
                button.image = image
            }
            button.action = #selector(togglePopover)
            button.target = self
        }

        // 创建弹出窗口
        let popover = NSPopover()
        popover.contentSize = NSSize(width: 400, height: 600)
        popover.behavior = .transient
        popover.contentViewController = NSHostingController(
            rootView: MenuBarPopoverView()
                .environmentObject(appState)
        )
        self.popover = popover
    }

    @objc func togglePopover() {
        guard let button = statusItem?.button else { return }

        if let popover = popover {
            if popover.isShown {
                popover.performClose(nil)
            } else {
                popover.show(relativeTo: button.bounds, of: button, preferredEdge: .minY)
                popover.contentViewController?.view.window?.makeKey()
            }
        }
    }

    func showMainWindow() {
        // 激活应用并显示主窗口
        NSApp.activate(ignoringOtherApps: true)

        // 如果主窗口不存在，创建一个
        if NSApp.windows.filter({ $0.isVisible && $0.level == .normal }).isEmpty {
            // 发送通知让应用创建新窗口
            NotificationCenter.default.post(name: .showMainWindow, object: nil)
        } else {
            // 显示现有窗口
            NSApp.windows.first(where: { $0.level == .normal })?.makeKeyAndOrderFront(nil)
        }

        // 关闭弹出窗口
        popover?.performClose(nil)
    }

    func navigateTo(_ page: PageType) {
        showMainWindow()
        NotificationCenter.default.post(name: .navigateFromMenuBar, object: page.rawValue)
    }
}

extension Notification.Name {
    static let showMainWindow = Notification.Name("showMainWindow")
    static let navigateFromMenuBar = Notification.Name("navigateFromMenuBar")
}
