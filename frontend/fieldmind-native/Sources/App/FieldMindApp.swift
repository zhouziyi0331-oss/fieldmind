import SwiftUI

@main
struct FieldMindApp: App {
    @StateObject private var appState = AppState()
    @StateObject private var toastManager = ToastManager.shared
    @StateObject private var modalManager = ModalManager.shared
    @StateObject private var loadingManager = LoadingManager.shared

    var body: some Scene {
        WindowGroup {
            MainView()
                .environmentObject(appState)
                .frame(minWidth: 1200, minHeight: 800)
                .toast(manager: toastManager)
                .modal(manager: modalManager)
                .loading(manager: loadingManager)
        }
        .windowStyle(.hiddenTitleBar)
        .commands {
            CommandGroup(replacing: .newItem) {}
        }
    }
}
