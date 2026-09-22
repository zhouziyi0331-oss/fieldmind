"""
FieldMind 设计系统 - 字体定义
参考 chakra-ui 的字体系统
"""
import SwiftUI

struct Typography {
    // MARK: - 标题字体
    static let h1 = Font.system(size: 32, weight: .bold)
    static let h2 = Font.system(size: 24, weight: .semibold)
    static let h3 = Font.system(size: 20, weight: .semibold)
    static let h4 = Font.system(size: 18, weight: .semibold)
    static let h5 = Font.system(size: 16, weight: .semibold)

    // MARK: - 正文字体
    static let body = Font.system(size: 16, weight: .regular)
    static let bodyBold = Font.system(size: 16, weight: .semibold)
    static let bodyLarge = Font.system(size: 18, weight: .regular)

    // MARK: - 辅助字体
    static let caption = Font.system(size: 14, weight: .regular)
    static let captionBold = Font.system(size: 14, weight: .semibold)
    static let small = Font.system(size: 12, weight: .regular)
    static let tiny = Font.system(size: 10, weight: .regular)

    // MARK: - 等宽字体（代码）
    static let code = Font.system(size: 14, weight: .regular, design: .monospaced)
}

// MARK: - Text Extension
extension Text {
    func fmH1() -> Text {
        self.font(Typography.h1)
    }

    func fmH2() -> Text {
        self.font(Typography.h2)
    }

    func fmH3() -> Text {
        self.font(Typography.h3)
    }

    func fmBody() -> Text {
        self.font(Typography.body)
    }

    func fmCaption() -> Text {
        self.font(Typography.caption)
            .foregroundColor(.fmTextSecondary)
    }
}
