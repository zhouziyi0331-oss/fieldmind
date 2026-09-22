import SwiftUI

// FieldMind 按钮样式 - 完全复刻 HTML 版本

struct FMButtonStyle: ButtonStyle {
    enum Style {
        case primary    // 主要按钮
        case secondary  // 次要按钮 (alias for outline)
        case outline    // 轮廓按钮
        case ghost      // 幽灵按钮
    }

    let style: Style
    let size: Size

    enum Size {
        case small
        case medium
        case large
    }

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(fontForSize())
            .padding(.horizontal, horizontalPadding())
            .padding(.vertical, verticalPadding())
            .background(backgroundColor(isPressed: configuration.isPressed))
            .foregroundColor(foregroundColor(isPressed: configuration.isPressed))
            .cornerRadius(FMRadius.md)
            .overlay(
                RoundedRectangle(cornerRadius: FMRadius.md)
                    .stroke(borderColor(isPressed: configuration.isPressed), lineWidth: 1)
            )
            .scaleEffect(configuration.isPressed ? 0.98 : 1.0)
            .animation(FMAnimation.fast, value: configuration.isPressed)
    }

    private func fontForSize() -> Font {
        switch size {
        case .small: return FMFont.small
        case .medium: return FMFont.body
        case .large: return FMFont.bodyBold
        }
    }

    private func horizontalPadding() -> CGFloat {
        switch size {
        case .small: return 10
        case .medium: return 14
        case .large: return 18
        }
    }

    private func verticalPadding() -> CGFloat {
        switch size {
        case .small: return 5
        case .medium: return 7
        case .large: return 10
        }
    }

    private func backgroundColor(isPressed: Bool) -> Color {
        switch style {
        case .primary:
            return isPressed ? Color.fmA1.opacity(0.9) : Color.fmA1
        case .secondary, .outline:
            return isPressed ? Color.fmA1Dim2 : Color.fmA1Dim
        case .ghost:
            return isPressed ? Color.fmBg2 : Color.clear
        }
    }

    private func foregroundColor(isPressed: Bool) -> Color {
        switch style {
        case .primary:
            return .white
        case .secondary, .outline, .ghost:
            return .fmA1
        }
    }

    private func borderColor(isPressed: Bool) -> Color {
        switch style {
        case .primary:
            return Color.clear
        case .secondary, .outline:
            return isPressed ? Color.fmBorder3 : Color.fmBorder2
        case .ghost:
            return Color.clear
        }
    }
}

// 按钮便捷扩展
extension Button {
    func fmPrimary(size: FMButtonStyle.Size = .medium) -> some View {
        self.buttonStyle(FMButtonStyle(style: .primary, size: size))
    }

    func fmSecondary(size: FMButtonStyle.Size = .medium) -> some View {
        self.buttonStyle(FMButtonStyle(style: .secondary, size: size))
    }

    func fmOutline(size: FMButtonStyle.Size = .medium) -> some View {
        self.buttonStyle(FMButtonStyle(style: .outline, size: size))
    }

    func fmGhost(size: FMButtonStyle.Size = .medium) -> some View {
        self.buttonStyle(FMButtonStyle(style: .ghost, size: size))
    }
}
