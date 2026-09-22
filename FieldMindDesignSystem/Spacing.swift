"""
FieldMind 设计系统 - 间距定义
参考 chakra-ui 的间距系统
"""
import SwiftUI

struct Spacing {
    // MARK: - 基础间距（8pt 网格系统）
    static let xs: CGFloat = 4      // 0.5 单位
    static let sm: CGFloat = 8      // 1 单位
    static let md: CGFloat = 16     // 2 单位
    static let lg: CGFloat = 24     // 3 单位
    static let xl: CGFloat = 32     // 4 单位
    static let xxl: CGFloat = 48    // 6 单位
    static let xxxl: CGFloat = 64   // 8 单位

    // MARK: - 组件专用间距
    static let cardPadding: CGFloat = 16
    static let sectionSpacing: CGFloat = 24
    static let itemSpacing: CGFloat = 12
    static let iconSize: CGFloat = 20
    static let buttonHeight: CGFloat = 40

    // MARK: - 布局间距
    static let sidebarWidthCollapsed: CGFloat = 60
    static let sidebarWidthExpanded: CGFloat = 240
    static let topBarHeight: CGFloat = 60
    static let minContentWidth: CGFloat = 600
}

// MARK: - View Extension
extension View {
    func fmPadding(_ size: CGFloat = Spacing.md) -> some View {
        self.padding(size)
    }

    func fmSpacing(_ size: CGFloat = Spacing.md) -> some View {
        self.padding(.vertical, size / 2)
    }
}
