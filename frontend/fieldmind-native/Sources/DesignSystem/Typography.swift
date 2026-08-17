import SwiftUI

// FieldMind 设计系统 - 字体排版

extension Font {
    // 标题字体
    static let fmH1 = Font.system(size: 28, weight: .bold)
    static let fmH2 = Font.system(size: 24, weight: .bold)
    static let fmH3 = Font.system(size: 20, weight: .semibold)
    static let fmH4 = Font.system(size: 18, weight: .semibold)
    static let fmH5 = Font.system(size: 16, weight: .semibold)
    static let fmH6 = Font.system(size: 14, weight: .semibold)

    // 正文字体
    static let fmBodyLarge = Font.system(size: 16, weight: .regular)
    static let fmBody = Font.system(size: 14, weight: .regular)
    static let fmBodySmall = Font.system(size: 13, weight: .regular)
    static let fmCaption = Font.system(size: 12, weight: .regular)
    static let fmCaptionSmall = Font.system(size: 11, weight: .regular)

    // 强调字体
    static let fmBodyMedium = Font.system(size: 14, weight: .medium)
    static let fmBodySemibold = Font.system(size: 14, weight: .semibold)

    // 按钮字体
    static let fmButton = Font.system(size: 14, weight: .medium)
    static let fmButtonSmall = Font.system(size: 13, weight: .medium)

    // 输入框字体
    static let fmInput = Font.system(size: 14, weight: .regular)

    // 标签字体
    static let fmLabel = Font.system(size: 13, weight: .medium)
    static let fmLabelSmall = Font.system(size: 12, weight: .medium)
}

// 字体大小常量（用于需要CGFloat的场景）
struct FontSize {
    static let h1: CGFloat = 28
    static let h2: CGFloat = 24
    static let h3: CGFloat = 20
    static let h4: CGFloat = 18
    static let h5: CGFloat = 16
    static let h6: CGFloat = 14

    static let bodyLarge: CGFloat = 16
    static let body: CGFloat = 14
    static let bodySmall: CGFloat = 13
    static let caption: CGFloat = 12
    static let captionSmall: CGFloat = 11
}
