import SwiftUI

struct LoginView: View {
    @EnvironmentObject var appState: AppState
    @State private var username = ""
    @State private var password = ""
    @State private var isLoading = false
    @State private var errorMessage: String?

    var body: some View {
        ZStack {
            // 渐变背景
            LinearGradient(
                colors: [Color(hex: "667eea"), Color(hex: "764ba2")],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            .ignoresSafeArea()

            VStack(spacing: 30) {
                // Logo 和标题
                VStack(spacing: 15) {
                    Image(systemName: "brain.head.profile")
                        .font(.system(size: 80))
                        .foregroundColor(.white)

                    Text("FieldMind")
                        .font(.system(size: 42, weight: .bold))
                        .foregroundColor(.white)

                    Text("田野调查智能分析平台")
                        .font(.system(size: 18))
                        .foregroundColor(.white.opacity(0.9))
                }
                .padding(.bottom, 40)

                // 登录表单
                VStack(spacing: 20) {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("用户名")
                            .font(.system(size: 14, weight: .medium))
                            .foregroundColor(.white.opacity(0.8))

                        TextField("", text: $username)
                            .textFieldStyle(CustomTextFieldStyle())
                            .disableAutocorrection(true)
                    }

                    VStack(alignment: .leading, spacing: 8) {
                        Text("密码")
                            .font(.system(size: 14, weight: .medium))
                            .foregroundColor(.white.opacity(0.8))

                        SecureField("", text: $password)
                            .textFieldStyle(CustomTextFieldStyle())
                    }

                    if let error = errorMessage {
                        Text(error)
                            .font(.system(size: 13))
                            .foregroundColor(.red.opacity(0.9))
                            .padding(.horizontal, 10)
                    }

                    Button(action: handleLogin) {
                        HStack {
                            if isLoading {
                                ProgressView()
                                    .progressViewStyle(CircularProgressViewStyle(tint: .white))
                                    .scaleEffect(0.8)
                            } else {
                                Text("登录")
                                    .font(.system(size: 16, weight: .semibold))
                            }
                        }
                        .frame(maxWidth: .infinity)
                        .frame(height: 50)
                        .background(Color.white)
                        .foregroundColor(Color(hex: "667eea"))
                        .cornerRadius(12)
                    }
                    .disabled(isLoading || username.isEmpty || password.isEmpty)
                    .opacity((isLoading || username.isEmpty || password.isEmpty) ? 0.6 : 1.0)

                    // Demo 提示
                    VStack(spacing: 8) {
                        Text("演示账号")
                            .font(.system(size: 12, weight: .medium))
                            .foregroundColor(.white.opacity(0.7))

                        HStack(spacing: 20) {
                            Text("用户名: demo")
                            Text("密码: demo123")
                        }
                        .font(.system(size: 11, design: .monospaced))
                        .foregroundColor(.white.opacity(0.6))
                    }
                    .padding(.top, 10)

                    // 演示模式按钮
                    Button(action: enterDemoMode) {
                        Text("演示模式（跳过登录）")
                            .font(.system(size: 14, weight: .medium))
                            .foregroundColor(.white)
                            .underline()
                    }
                    .buttonStyle(PlainButtonStyle())
                    .padding(.top, 5)
                }
                .padding(40)
                .background(Color.white.opacity(0.15))
                .cornerRadius(20)
                .frame(width: 400)
            }
        }
        .onSubmit(handleLogin)
    }

    private func handleLogin() {
        guard !username.isEmpty, !password.isEmpty else { return }

        isLoading = true
        errorMessage = nil

        Task {
            do {
                let response = try await APIService.shared.login(username: username, password: password)
                await MainActor.run {
                    appState.login(user: response.user, token: response.accessToken)
                    isLoading = false
                }
            } catch {
                await MainActor.run {
                    errorMessage = "登录失败: \(error.localizedDescription)"
                    isLoading = false
                }
            }
        }
    }

    private func enterDemoMode() {
        // 创建演示用户
        let demoUser = User(
            id: 999,
            username: "演示用户",
            email: "demo@fieldmind.local",
            role: "researcher",
            createdAt: Date()
        )

        // 使用演示token登录
        appState.login(user: demoUser, token: "demo-token")
    }
}
