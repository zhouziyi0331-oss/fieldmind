//
//  BackendService.swift
//  FieldMind
//
//  后端服务管理 - 自动启动/停止 Python 后端
//

import Foundation
import Combine

class BackendService: ObservableObject {
    static let shared = BackendService()

    @Published var isRunning = false
    @Published var backendURL = "http://127.0.0.1:8000"

    private var backendProcess: Process?
    private var cancellables = Set<AnyCancellable>()

    private init() {
        checkBackendHealth()
    }

    /// 启动后端服务
    func startBackend() {
        guard !isRunning else { return }

        let backendPath = getBackendPath()
        guard FileManager.default.fileExists(atPath: backendPath) else {
            print("❌ Backend not found at: \(backendPath)")
            return
        }

        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/bin/zsh")

        let command = """
        cd \(backendPath) && \
        source venv/bin/activate && \
        python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
        """

        process.arguments = ["-c", command]

        let pipe = Pipe()
        process.standardOutput = pipe
        process.standardError = pipe

        do {
            try process.run()
            backendProcess = process

            // 等待后端启动
            DispatchQueue.main.asyncAfter(deadline: .now() + 3) { [weak self] in
                self?.checkBackendHealth()
            }

            print("✅ Backend starting...")
        } catch {
            print("❌ Failed to start backend: \(error)")
        }
    }

    /// 停止后端服务
    func stopBackend() {
        backendProcess?.terminate()
        backendProcess = nil
        isRunning = false
        print("🛑 Backend stopped")
    }

    /// 检查后端健康状态
    func checkBackendHealth() {
        guard let url = URL(string: "\(backendURL)/health") else { return }

        URLSession.shared.dataTask(with: url) { [weak self] data, response, error in
            DispatchQueue.main.async {
                if let httpResponse = response as? HTTPURLResponse,
                   httpResponse.statusCode == 200 {
                    self?.isRunning = true
                    print("✅ Backend is healthy")
                } else {
                    self?.isRunning = false
                    // 尝试自动启动
                    self?.startBackend()
                }
            }
        }.resume()
    }

    /// 获取后端路径
    private func getBackendPath() -> String {
        // 1. 尝试从 app bundle 内部获取
        if let bundlePath = Bundle.main.resourcePath {
            let internalBackend = "\(bundlePath)/backend"
            if FileManager.default.fileExists(atPath: internalBackend) {
                return internalBackend
            }
        }

        // 2. 使用开发环境路径
        let homeDir = FileManager.default.homeDirectoryForCurrentUser.path
        return "\(homeDir)/FieldMind/backend"
    }

    deinit {
        stopBackend()
    }
}
