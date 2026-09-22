import SwiftUI

// MARK: - 交互组件使用示例
// 本文件展示如何在页面中使用Toast、Modal、Tooltip、Loading和Transition组件

// MARK: - Toast使用示例
struct ToastExamples {
    @MainActor
    static func showSuccess() {
        ToastManager.shared.success("操作成功")
    }

    @MainActor
    static func showError() {
        ToastManager.shared.error("操作失败，请重试")
    }

    @MainActor
    static func showWarning() {
        ToastManager.shared.warning("请注意检查输入内容")
    }

    @MainActor
    static func showInfo() {
        ToastManager.shared.info("这是一条提示信息")
    }
}

// MARK: - Modal使用示例
struct ModalExamples {
    // 显示确认对话框
    @MainActor
    static func showConfirmAlert(onConfirm: @escaping () -> Void) {
        ModalManager.shared.showAlert(AlertConfig(
            title: "确认操作",
            message: "确定要执行此操作吗？此操作无法撤销。",
            primaryButtonText: "确定",
            secondaryButtonText: "取消",
            primaryAction: onConfirm,
            isDestructive: false
        ))
    }

    // 显示删除确认对话框
    @MainActor
    static func showDeleteAlert(itemName: String, onConfirm: @escaping () -> Void) {
        ModalManager.shared.showAlert(AlertConfig(
            title: "确认删除",
            message: "确定要删除「\(itemName)」吗？此操作无法撤销。",
            primaryButtonText: "删除",
            secondaryButtonText: "取消",
            primaryAction: onConfirm,
            isDestructive: true
        ))
    }

    // 显示表单模态框
    @MainActor
    static func showFormModal() {
        ModalManager.shared.showForm(title: "编辑信息") {
            VStack(alignment: .leading, spacing: 16) {
                VStack(alignment: .leading, spacing: 8) {
                    Text("名称")
                        .font(.system(size: 13))
                        .foregroundColor(Color.fmText2)

                    TextField("请输入名称", text: .constant(""))
                        .textFieldStyle(.plain)
                        .padding(10)
                        .background(Color.fmBg)
                        .cornerRadius(6)
                }

                VStack(alignment: .leading, spacing: 8) {
                    Text("描述")
                        .font(.system(size: 13))
                        .foregroundColor(Color.fmText2)

                    TextEditor(text: .constant(""))
                        .frame(height: 100)
                        .padding(10)
                        .background(Color.fmBg)
                        .cornerRadius(6)
                }

                HStack {
                    Spacer()

                    Button(action: {
                        ModalManager.shared.dismiss()
                    }) {
                        Text("取消")
                            .font(.system(size: 14))
                            .foregroundColor(Color.fmText2)
                            .padding(.horizontal, 20)
                            .padding(.vertical, 8)
                            .background(Color.fmBg)
                            .cornerRadius(6)
                    }
                    .buttonStyle(.plain)

                    Button(action: {
                        ModalManager.shared.dismiss()
                        ToastManager.shared.success("保存成功")
                    }) {
                        Text("保存")
                            .font(.system(size: 14))
                            .foregroundColor(.white)
                            .padding(.horizontal, 20)
                            .padding(.vertical, 8)
                            .background(Color(hex: "1890FF"))
                            .cornerRadius(6)
                    }
                    .buttonStyle(.plain)
                }
            }
        }
    }

    // 显示抽屉
    @MainActor
    static func showDrawer() {
        ModalManager.shared.showDrawer(title: "详细信息", width: 480) {
            VStack(alignment: .leading, spacing: 20) {
                ForEach(0..<5) { index in
                    VStack(alignment: .leading, spacing: 8) {
                        Text("项目 \(index + 1)")
                            .font(.system(size: 14, weight: .medium))
                            .foregroundColor(Color.fmText)

                        Text("这是项目的详细描述信息")
                            .font(.system(size: 13))
                            .foregroundColor(Color.fmText2)
                    }
                    .padding(16)
                    .background(Color.fmBg)
                    .cornerRadius(8)
                }
            }
        }
    }
}

// MARK: - Loading使用示例
struct LoadingExamples {
    // 显示加载中
    @MainActor
    static func showLoading(message: String = "加载中") {
        LoadingManager.shared.show(message: message)
    }

    // 隐藏加载中
    @MainActor
    static func hideLoading() {
        LoadingManager.shared.hide()
    }

    // 模拟异步操作
    @MainActor
    static func simulateAsyncOperation() {
        LoadingManager.shared.show(message: "正在处理")

        DispatchQueue.main.asyncAfter(deadline: .now() + 2.0) {
            LoadingManager.shared.hide()
            ToastManager.shared.success("处理完成")
        }
    }
}

// MARK: - 按钮交互增强示例
struct EnhancedButton: View {
    let title: String
    let icon: String?
    let isPrimary: Bool
    let isDestructive: Bool
    let action: () -> Void

    @State private var isHovered: Bool = false
    @State private var isPressed: Bool = false

    init(
        title: String,
        icon: String? = nil,
        isPrimary: Bool = false,
        isDestructive: Bool = false,
        action: @escaping () -> Void
    ) {
        self.title = title
        self.icon = icon
        self.isPrimary = isPrimary
        self.isDestructive = isDestructive
        self.action = action
    }

    var body: some View {
        Button(action: action) {
            HStack(spacing: 6) {
                if let icon = icon {
                    Image(systemName: icon)
                        .font(.system(size: 14))
                }

                Text(title)
                    .font(.system(size: 14, weight: isPrimary ? .medium : .regular))
            }
            .foregroundColor(foregroundColor)
            .padding(.horizontal, 16)
            .padding(.vertical, 8)
            .background(backgroundColor)
            .cornerRadius(6)
            .overlay(
                RoundedRectangle(cornerRadius: 6)
                    .stroke(borderColor, lineWidth: 1)
            )
        }
        .buttonStyle(.plain)
        .scaleEffect(isPressed ? 0.97 : (isHovered ? 1.02 : 1.0))
        .animation(.easeOut(duration: 0.15), value: isHovered)
        .animation(.easeOut(duration: 0.1), value: isPressed)
        .onHover { hovering in
            isHovered = hovering
        }
        .pressAction {
            isPressed = true
        } onRelease: {
            isPressed = false
        }
    }

    private var foregroundColor: Color {
        if isPrimary {
            return .white
        } else if isDestructive {
            return Color(hex: "FF4D4F")
        } else {
            return Color.fmText
        }
    }

    private var backgroundColor: Color {
        if isPrimary {
            return isHovered ? Color(hex: "40A9FF") : Color(hex: "1890FF")
        } else if isDestructive {
            return isHovered ? Color(hex: "FF4D4F").opacity(0.1) : Color.white
        } else {
            return isHovered ? Color.fmBg : Color.white
        }
    }

    private var borderColor: Color {
        if isPrimary {
            return Color.clear
        } else if isDestructive {
            return Color(hex: "FF4D4F")
        } else {
            return Color.fmBorder
        }
    }
}

// MARK: - Press Action Modifier
extension View {
    func pressAction(onPress: @escaping () -> Void, onRelease: @escaping () -> Void) -> some View {
        modifier(PressActions(onPress: onPress, onRelease: onRelease))
    }
}

struct PressActions: ViewModifier {
    var onPress: () -> Void
    var onRelease: () -> Void

    @State private var isPressed: Bool = false

    func body(content: Content) -> some View {
        content
            .simultaneousGesture(
                DragGesture(minimumDistance: 0)
                    .onChanged { _ in
                        if !isPressed {
                            isPressed = true
                            onPress()
                        }
                    }
                    .onEnded { _ in
                        isPressed = false
                        onRelease()
                    }
            )
    }
}

// MARK: - 卡片悬停效果示例
struct EnhancedCard<Content: View>: View {
    let content: Content
    @State private var isHovered: Bool = false

    init(@ViewBuilder content: () -> Content) {
        self.content = content()
    }

    var body: some View {
        content
            .background(Color.white)
            .cornerRadius(12)
            .overlay(
                RoundedRectangle(cornerRadius: 12)
                    .stroke(isHovered ? Color(hex: "1890FF") : Color.fmBorder, lineWidth: 1)
            )
            .shadow(
                color: Color.black.opacity(isHovered ? 0.08 : 0),
                radius: isHovered ? 12 : 0,
                x: 0,
                y: isHovered ? 4 : 0
            )
            .scaleEffect(isHovered ? 1.01 : 1.0)
            .animation(.easeOut(duration: 0.2), value: isHovered)
            .onHover { hovering in
                isHovered = hovering
            }
    }
}

// MARK: - 输入框交互增强
struct EnhancedTextField: View {
    let placeholder: String
    @Binding var text: String
    let isRequired: Bool
    let errorMessage: String?

    @State private var isFocused: Bool = false

    init(
        placeholder: String,
        text: Binding<String>,
        isRequired: Bool = false,
        errorMessage: String? = nil
    ) {
        self.placeholder = placeholder
        self._text = text
        self.isRequired = isRequired
        self.errorMessage = errorMessage
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            TextField(placeholder, text: $text)
                .textFieldStyle(.plain)
                .padding(10)
                .background(isFocused ? Color.white : Color.fmBg)
                .cornerRadius(6)
                .overlay(
                    RoundedRectangle(cornerRadius: 6)
                        .stroke(borderColor, lineWidth: 1)
                )
                .animation(.easeOut(duration: 0.2), value: isFocused)

            if let errorMessage = errorMessage {
                HStack(spacing: 4) {
                    Image(systemName: "exclamationmark.circle.fill")
                        .font(.system(size: 12))
                    Text(errorMessage)
                        .font(.system(size: 12))
                }
                .foregroundColor(Color(hex: "FF4D4F"))
            }
        }
    }

    private var borderColor: Color {
        if errorMessage != nil {
            return Color(hex: "FF4D4F")
        } else if isFocused {
            return Color(hex: "1890FF")
        } else {
            return Color.fmBorder
        }
    }
}
