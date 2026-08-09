import SwiftUI
import Combine

// MARK: - Toast Manager

class ToastManager: ObservableObject {
    static let shared = ToastManager()

    @Published var currentToast: ToastMessage?

    private init() {}

    func show(message: String, type: ToastType = .info, duration: TimeInterval = 3.0) {
        DispatchQueue.main.async {
            self.currentToast = ToastMessage(message: message, type: type)

            DispatchQueue.main.asyncAfter(deadline: .now() + duration) {
                self.currentToast = nil
            }
        }
    }

    func success(_ message: String) {
        show(message: message, type: .success)
    }

    func error(_ message: String) {
        show(message: message, type: .error)
    }

    func info(_ message: String) {
        show(message: message, type: .info)
    }

    func warning(_ message: String) {
        show(message: message, type: .warning)
    }
}

// MARK: - Toast Message

struct ToastMessage: Identifiable, Equatable {
    let id = UUID()
    let message: String
    let type: ToastType

    static func == (lhs: ToastMessage, rhs: ToastMessage) -> Bool {
        lhs.id == rhs.id
    }
}

enum ToastType {
    case success
    case error
    case info
    case warning

    var icon: String {
        switch self {
        case .success: return "checkmark.circle.fill"
        case .error: return "xmark.circle.fill"
        case .info: return "info.circle.fill"
        case .warning: return "exclamationmark.triangle.fill"
        }
    }

    var color: Color {
        switch self {
        case .success: return Color(hex: "48bb78")
        case .error: return Color(hex: "f56565")
        case .info: return Color(hex: "667eea")
        case .warning: return Color(hex: "ed8936")
        }
    }
}

// MARK: - Toast View

struct ToastView: View {
    let message: ToastMessage

    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: message.type.icon)
                .font(.system(size: 16, weight: .semibold))
                .foregroundColor(.white)

            Text(message.message)
                .font(.system(size: 13, weight: .medium))
                .foregroundColor(.white)
                .lineLimit(2)
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 12)
        .background(message.type.color)
        .cornerRadius(8)
        .shadow(color: Color.black.opacity(0.2), radius: 8, x: 0, y: 4)
    }
}

// MARK: - Toast Modifier

struct ToastModifier: ViewModifier {
    @ObservedObject var toastManager = ToastManager.shared

    func body(content: Content) -> some View {
        ZStack {
            content

            if let toast = toastManager.currentToast {
                VStack {
                    Spacer()

                    ToastView(message: toast)
                        .transition(.move(edge: .bottom).combined(with: .opacity))
                        .animation(.spring(response: 0.3, dampingFraction: 0.7), value: toastManager.currentToast)

                    Spacer()
                        .frame(height: 40)
                }
                .zIndex(999)
            }
        }
    }
}

extension View {
    func withToast() -> some View {
        modifier(ToastModifier())
    }
}
