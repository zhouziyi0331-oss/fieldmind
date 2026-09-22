import SwiftUI

// FieldMind 设计系统 - 阴影
struct FMShadow {
    // 标准阴影: 0 2px 12px rgba(23,138,183,.07)
    static let standard = Shadow(
        color: Color(hex: "178AB7").opacity(0.07),
        radius: 6,
        x: 0,
        y: 2
    )

    // 大阴影: 0 6px 28px rgba(23,138,183,.12)
    static let large = Shadow(
        color: Color(hex: "178AB7").opacity(0.12),
        radius: 14,
        x: 0,
        y: 6
    )

    struct Shadow {
        let color: Color
        let radius: CGFloat
        let x: CGFloat
        let y: CGFloat
    }
}

// FieldMind 设计系统 - 字体
struct FMFont {
    // 基础字体: Inter Tight
    static let body = Font.custom("Inter Tight", size: 13)
    static let bodyBold = Font.custom("Inter Tight", size: 13).weight(.semibold)

    static let small = Font.custom("Inter Tight", size: 11)
    static let smallBold = Font.custom("Inter Tight", size: 11).weight(.semibold)

    static let caption = Font.custom("Inter Tight", size: 9)

    static let title = Font.custom("Inter Tight", size: 15).weight(.bold)
    static let heading = Font.custom("Inter Tight", size: 17).weight(.bold)

    // 代码字体: JetBrains Mono
    static let mono = Font.custom("JetBrains Mono", size: 12)
}

// FieldMind 设计系统 - 间距
struct FMSpacing {
    static let xs: CGFloat = 4
    static let sm: CGFloat = 8
    static let md: CGFloat = 12
    static let lg: CGFloat = 16
    static let xl: CGFloat = 24
    static let xxl: CGFloat = 32
}

// FieldMind 设计系统 - 圆角
struct FMRadius {
    static let sm: CGFloat = 4
    static let md: CGFloat = 8
    static let lg: CGFloat = 12
    static let full: CGFloat = 999
}

// FieldMind 设计系统 - 动画
struct FMAnimation {
    static let fast = Animation.easeInOut(duration: 0.2)
    static let normal = Animation.easeInOut(duration: 0.3)
    static let slow = Animation.easeInOut(duration: 0.5)
}
