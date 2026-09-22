//
//  fieldmindApp.swift
//  fieldmind
//
//  Created by alwan on 2026/9/11.
//

import SwiftUI

@main
struct fieldmindApp: App {
    @StateObject private var backendService = BackendService.shared

    init() {
        // 应用启动时自动启动后端
        BackendService.shared.startBackend()
    }

    var body: some Scene {
        WindowGroup {
            MainNavigationView()
                .environmentObject(backendService)
                .onAppear {
                    backendService.checkBackendHealth()
                }
        }
        .commands {
            // 添加菜单命令
            CommandGroup(after: .appInfo) {
                Button("检查后端状态") {
                    backendService.checkBackendHealth()
                }
                Divider()
                Button(backendService.isRunning ? "停止后端" : "启动后端") {
                    if backendService.isRunning {
                        backendService.stopBackend()
                    } else {
                        backendService.startBackend()
                    }
                }
            }
        }
    }
}
