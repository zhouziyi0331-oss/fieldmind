import SwiftUI

// MARK: - Toast Item (使用AppState.swift中已定义的ToastType)
struct ToastItem: Identifiable, Equatable {
    let id: String
    let type: ToastType
    let message: String
    let duration: Double

    init(id: String = UUID().uuidString, type: ToastType, message: String, duration: Double = 3.0) {
        self.id = id
        self.type = type
        self.message = message
        self.duration = duration
    }
}

// MARK: - Toast Manager
@MainActor
class ToastManager: ObservableObject {
    static let shared = ToastManager()

    @Published var currentToast: ToastItem?

    private init() {}

    func show(_ type: ToastType, message: String, duration: Double = 3.0) {
        currentToast = ToastItem(type: type, message: message, duration: duration)

        DispatchQueue.main.asyncAfter(deadline: .now() + duration) { [weak self] in
            if self?.currentToast?.id == self?.currentToast?.id {
                self?.dismiss()
            }
        }
    }

    func success(_ message: String, duration: Double = 3.0) {
        show(.success, message: message, duration: duration)
    }

    func error(_ message: String, duration: Double = 3.0) {
        show(.error, message: message, duration: duration)
    }

    func warning(_ message: String, duration: Double = 3.0) {
        show(.warning, message: message, duration: duration)
    }

    func info(_ message: String, duration: Double = 3.0) {
        show(.info, message: message, duration: duration)
    }

    func dismiss() {
        withAnimation(.easeOut(duration: 0.2)) {
            currentToast = nil
        }
    }
}

// MARK: - Toast Container
struct ToastContainer: ViewModifier {
    @ObservedObject var manager: ToastManager

    func body(content: Content) -> some View {
        ZStack {
            content

            if let toast = manager.currentToast {
                VStack {
                    HStack {
                        Image(systemName: toast.type == .success ? "checkmark.circle.fill" :
                                         toast.type == .error ? "xmark.circle.fill" :
                                         toast.type == .warning ? "exclamationmark.triangle.fill" :
                                         "info.circle.fill")
                        Text(toast.message)
                        Spacer()
                        Button(action: { manager.dismiss() }) {
                            Image(systemName: "xmark")
                                .font(.system(size: 10))
                        }
                        .buttonStyle(.plain)
                    }
                    .padding()
                    .background(Color.blue.opacity(0.9))
                    .cornerRadius(8)
                    .shadow(radius: 4)
                    .padding(.horizontal)
                    .padding(.top, 20)
                    .transition(.move(edge: .top).combined(with: .opacity))

                    Spacer()
                }
                .zIndex(1000)
            }
        }
        .animation(.spring(response: 0.3, dampingFraction: 0.7), value: manager.currentToast?.id)
    }
}

extension View {
    @MainActor
    func toast(manager: ToastManager = ToastManager.shared) -> some View {
        self.modifier(ToastContainer(manager: manager))
    }
}
