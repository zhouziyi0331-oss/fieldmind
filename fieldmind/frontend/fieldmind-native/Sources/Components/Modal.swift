import SwiftUI

// MARK: - Modal Type
enum ModalType {
    case alert
    case form
    case fullscreen
    case drawer
}

// MARK: - Alert Configuration
struct AlertConfig {
    let title: String
    let message: String
    let primaryButtonText: String
    let secondaryButtonText: String?
    let primaryAction: () -> Void
    let secondaryAction: (() -> Void)?
    let isDestructive: Bool

    init(
        title: String,
        message: String,
        primaryButtonText: String = "确定",
        secondaryButtonText: String? = "取消",
        primaryAction: @escaping () -> Void,
        secondaryAction: (() -> Void)? = nil,
        isDestructive: Bool = false
    ) {
        self.title = title
        self.message = message
        self.primaryButtonText = primaryButtonText
        self.secondaryButtonText = secondaryButtonText
        self.primaryAction = primaryAction
        self.secondaryAction = secondaryAction
        self.isDestructive = isDestructive
    }
}

// MARK: - Alert Modal View
struct AlertModal: View {
    let config: AlertConfig
    let onDismiss: () -> Void

    var body: some View {
        VStack(spacing: 0) {
            // Title
            Text(config.title)
                .font(.system(size: 16, weight: .semibold))
                .foregroundColor(Color.fmText)
                .padding(.top, 20)
                .padding(.horizontal, 20)

            // Message
            Text(config.message)
                .font(.system(size: 14))
                .foregroundColor(Color.fmText2)
                .multilineTextAlignment(.center)
                .padding(.top, 12)
                .padding(.horizontal, 20)
                .padding(.bottom, 24)

            Divider()

            // Buttons
            HStack(spacing: 0) {
                if let secondaryText = config.secondaryButtonText {
                    Button(action: {
                        config.secondaryAction?()
                        onDismiss()
                    }) {
                        Text(secondaryText)
                            .font(.system(size: 14))
                            .foregroundColor(Color.fmText2)
                            .frame(maxWidth: .infinity)
                            .frame(height: 44)
                    }
                    .buttonStyle(.plain)

                    Divider()
                }

                Button(action: {
                    config.primaryAction()
                    onDismiss()
                }) {
                    Text(config.primaryButtonText)
                        .font(.system(size: 14, weight: .medium))
                        .foregroundColor(config.isDestructive ? Color(hex: "FF4D4F") : Color(hex: "1890FF"))
                        .frame(maxWidth: .infinity)
                        .frame(height: 44)
                }
                .buttonStyle(.plain)
            }
        }
        .frame(width: 360)
        .background(Color.white)
        .cornerRadius(12)
        .shadow(color: Color.black.opacity(0.15), radius: 20, x: 0, y: 10)
    }
}

// MARK: - Form Modal View
struct FormModal<Content: View>: View {
    let title: String
    let content: Content
    let onDismiss: () -> Void

    init(title: String, onDismiss: @escaping () -> Void, @ViewBuilder content: () -> Content) {
        self.title = title
        self.onDismiss = onDismiss
        self.content = content()
    }

    var body: some View {
        VStack(spacing: 0) {
            // Header
            HStack {
                Text(title)
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundColor(Color.fmText)

                Spacer()

                Button(action: onDismiss) {
                    Image(systemName: "xmark")
                        .font(.system(size: 14))
                        .foregroundColor(Color.fmText3)
                        .frame(width: 28, height: 28)
                        .background(Color.fmBg)
                        .cornerRadius(6)
                }
                .buttonStyle(.plain)
            }
            .padding(20)

            Divider()

            // Content
            ScrollView {
                content
                    .padding(20)
            }
        }
        .frame(width: 560)
        .frame(maxHeight: 640)
        .background(Color.white)
        .cornerRadius(12)
        .shadow(color: Color.black.opacity(0.15), radius: 20, x: 0, y: 10)
    }
}

// MARK: - Fullscreen Modal View
struct FullscreenModal<Content: View>: View {
    let title: String
    let content: Content
    let onDismiss: () -> Void

    init(title: String, onDismiss: @escaping () -> Void, @ViewBuilder content: () -> Content) {
        self.title = title
        self.onDismiss = onDismiss
        self.content = content()
    }

    var body: some View {
        VStack(spacing: 0) {
            // Header
            HStack {
                Text(title)
                    .font(.system(size: 18, weight: .semibold))
                    .foregroundColor(Color.fmText)

                Spacer()

                Button(action: onDismiss) {
                    HStack(spacing: 6) {
                        Image(systemName: "xmark")
                            .font(.system(size: 12))
                        Text("关闭")
                            .font(.system(size: 14))
                    }
                    .foregroundColor(Color.fmText2)
                    .padding(.horizontal, 16)
                    .padding(.vertical, 8)
                    .background(Color.fmBg)
                    .cornerRadius(6)
                }
                .buttonStyle(.plain)
            }
            .padding(20)
            .background(Color.white)

            Divider()

            // Content
            content
        }
        .background(Color.fmBg)
    }
}

// MARK: - Drawer Modal View
struct DrawerModal<Content: View>: View {
    let title: String
    let content: Content
    let onDismiss: () -> Void
    let width: CGFloat

    init(
        title: String,
        width: CGFloat = 480,
        onDismiss: @escaping () -> Void,
        @ViewBuilder content: () -> Content
    ) {
        self.title = title
        self.width = width
        self.onDismiss = onDismiss
        self.content = content()
    }

    var body: some View {
        HStack(spacing: 0) {
            Spacer()

            VStack(spacing: 0) {
                // Header
                HStack {
                    Text(title)
                        .font(.system(size: 16, weight: .semibold))
                        .foregroundColor(Color.fmText)

                    Spacer()

                    Button(action: onDismiss) {
                        Image(systemName: "xmark")
                            .font(.system(size: 14))
                            .foregroundColor(Color.fmText3)
                            .frame(width: 28, height: 28)
                            .background(Color.fmBg)
                            .cornerRadius(6)
                    }
                    .buttonStyle(.plain)
                }
                .padding(20)

                Divider()

                // Content
                ScrollView {
                    content
                        .padding(20)
                }
            }
            .frame(width: width)
            .background(Color.white)
            .shadow(color: Color.black.opacity(0.2), radius: 30, x: -10, y: 0)
        }
    }
}

// MARK: - Modal Manager
@MainActor
class ModalManager: ObservableObject {
    static let shared = ModalManager()

    @Published var isPresented: Bool = false
    @Published var modalType: ModalType = .alert
    @Published var alertConfig: AlertConfig?
    @Published var formContent: AnyView?
    @Published var fullscreenContent: AnyView?
    @Published var drawerContent: AnyView?
    @Published var modalTitle: String = ""
    @Published var drawerWidth: CGFloat = 480

    private init() {}

    func showAlert(_ config: AlertConfig) {
        alertConfig = config
        modalType = .alert
        isPresented = true
    }

    func showForm<Content: View>(title: String, @ViewBuilder content: () -> Content) {
        modalTitle = title
        formContent = AnyView(content())
        modalType = .form
        isPresented = true
    }

    func showFullscreen<Content: View>(title: String, @ViewBuilder content: () -> Content) {
        modalTitle = title
        fullscreenContent = AnyView(content())
        modalType = .fullscreen
        isPresented = true
    }

    func showDrawer<Content: View>(title: String, width: CGFloat = 480, @ViewBuilder content: () -> Content) {
        modalTitle = title
        drawerWidth = width
        drawerContent = AnyView(content())
        modalType = .drawer
        isPresented = true
    }

    func dismiss() {
        withAnimation(.easeOut(duration: 0.2)) {
            isPresented = false
        }
    }
}

// MARK: - Modal Container
struct ModalContainer: ViewModifier {
    @ObservedObject var manager: ModalManager

    func body(content: Content) -> some View {
        ZStack {
            content

            if manager.isPresented {
                // Overlay
                Color.black.opacity(0.5)
                    .ignoresSafeArea()
                    .onTapGesture {
                        if manager.modalType != .fullscreen {
                            manager.dismiss()
                        }
                    }
                    .transition(.opacity)

                // Modal Content
                Group {
                    switch manager.modalType {
                    case .alert:
                        if let config = manager.alertConfig {
                            AlertModal(config: config, onDismiss: manager.dismiss)
                                .transition(.scale.combined(with: .opacity))
                        }

                    case .form:
                        if let formContent = manager.formContent {
                            FormModal(title: manager.modalTitle, onDismiss: manager.dismiss) {
                                formContent
                            }
                            .transition(.scale.combined(with: .opacity))
                        }

                    case .fullscreen:
                        if let fullscreenContent = manager.fullscreenContent {
                            FullscreenModal(title: manager.modalTitle, onDismiss: manager.dismiss) {
                                fullscreenContent
                            }
                            .transition(.opacity)
                        }

                    case .drawer:
                        if let drawerContent = manager.drawerContent {
                            DrawerModal(title: manager.modalTitle, width: manager.drawerWidth, onDismiss: manager.dismiss) {
                                drawerContent
                            }
                            .transition(.move(edge: .trailing))
                        }
                    }
                }
                .zIndex(1001)
            }
        }
        .animation(.spring(response: 0.3, dampingFraction: 0.7), value: manager.isPresented)
    }
}

extension View {
    @MainActor
    func modal(manager: ModalManager = ModalManager.shared) -> some View {
        self.modifier(ModalContainer(manager: manager))
    }
}
