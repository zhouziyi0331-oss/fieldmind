import SwiftUI

// FieldMind 设计系统 - 间距和尺寸

// 间距
struct Spacing {
    static let xs: CGFloat = 4
    static let sm: CGFloat = 8
    static let md: CGFloat = 12
    static let lg: CGFloat = 16
    static let xl: CGFloat = 20
    static let xxl: CGFloat = 24
    static let xxxl: CGFloat = 32
    static let huge: CGFloat = 40
}

// 圆角
struct CornerRadius {
    static let xs: CGFloat = 4
    static let sm: CGFloat = 6
    static let md: CGFloat = 8
    static let lg: CGFloat = 10
    static let xl: CGFloat = 12
    static let xxl: CGFloat = 16
    static let round: CGFloat = 999  // 完全圆形
}

// 边框宽度
struct BorderWidth {
    static let thin: CGFloat = 1
    static let medium: CGFloat = 2
    static let thick: CGFloat = 3
}

// 阴影
struct Shadow {
    static let sm: CGFloat = 2
    static let md: CGFloat = 4
    static let lg: CGFloat = 8
    static let xl: CGFloat = 12
    static let xxl: CGFloat = 16
}

// 常用尺寸
struct Size {
    // 侧边栏
    static let sidebarWidth: CGFloat = 240
    static let sidebarCollapsedWidth: CGFloat = 60

    // 按钮高度
    static let buttonHeight: CGFloat = 36
    static let buttonHeightSmall: CGFloat = 32
    static let buttonHeightLarge: CGFloat = 40

    // 输入框高度
    static let inputHeight: CGFloat = 36
    static let inputHeightSmall: CGFloat = 32
    static let inputHeightLarge: CGFloat = 40

    // 图标尺寸
    static let iconXS: CGFloat = 12
    static let iconSM: CGFloat = 14
    static let iconMD: CGFloat = 16
    static let iconLG: CGFloat = 20
    static let iconXL: CGFloat = 24
    static let iconXXL: CGFloat = 32

    // 卡片最小宽度
    static let cardMinWidth: CGFloat = 280
    static let cardMaxWidth: CGFloat = 400

    // 内容宽度
    static let contentMaxWidth: CGFloat = 1400
}

// EdgeInsets 辅助方法
extension EdgeInsets {
    static func all(_ value: CGFloat) -> EdgeInsets {
        EdgeInsets(top: value, leading: value, bottom: value, trailing: value)
    }

    static func horizontal(_ value: CGFloat) -> EdgeInsets {
        EdgeInsets(top: 0, leading: value, bottom: 0, trailing: value)
    }

    static func vertical(_ value: CGFloat) -> EdgeInsets {
        EdgeInsets(top: value, leading: 0, bottom: value, trailing: 0)
    }

    static func symmetric(horizontal: CGFloat = 0, vertical: CGFloat = 0) -> EdgeInsets {
        EdgeInsets(top: vertical, leading: horizontal, bottom: vertical, trailing: horizontal)
    }
}
