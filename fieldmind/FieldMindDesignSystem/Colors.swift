"""
FieldMind 设计系统 - Succulents 配色方案
多肉植物主题配色
"""
import SwiftUI

extension Color {
    // MARK: - Succulents 主色调
    static let fmPrimary = Color(hex: "27768A")           // 深青绿
    static let fmPrimaryLight = Color(hex: "589DA4")      // 中青绿
    static let fmPrimaryLighter = Color(hex: "A8CCD3")    // 浅青绿

    // MARK: - Succulents 次色调
    static let fmSecondary = Color(hex: "748D44")         // 橄榄绿
    static let fmSecondaryLight = Color(hex: "85A156")    // 浅橄榄绿

    // MARK: - 强调色
    static let fmAccent = Color(hex: "F0F5E2")            // 奶油色

    // MARK: - 语义色
    static let fmSuccess = Color(hex: "85A156")           // 成功 - 浅橄榄绿
    static let fmWarning = Color(hex: "F8B042")           // 警告 - 橙黄色
    static let fmError = Color(hex: "EC6A52")             // 错误 - 珊瑚红
    static let fmInfo = Color(hex: "589DA4")              // 信息 - 中青绿

    // MARK: - 中性色（灰度色阶）
    static let fmGray50 = Color(hex: "F9FAFB")
    static let fmGray100 = Color(hex: "F3F4F6")
    static let fmGray200 = Color(hex: "E5E7EB")
    static let fmGray300 = Color(hex: "D1D5DB")
    static let fmGray400 = Color(hex: "9CA3AF")
    static let fmGray500 = Color(hex: "6B7280")
    static let fmGray600 = Color(hex: "4B5563")
    static let fmGray700 = Color(hex: "374151")
    static let fmGray800 = Color(hex: "1F2937")
    static let fmGray900 = Color(hex: "111827")

    // MARK: - 背景色
    static let fmBgPrimary = Color.white
    static let fmBgSecondary = Color.fmGray50
    static let fmBgTertiary = Color.fmGray100
    static let fmBgElevated = Color.white

    // MARK: - 文本色
    static let fmTextPrimary = Color.fmGray900
    static let fmTextSecondary = Color.fmGray600
    static let fmTextTertiary = Color.fmGray400
    static let fmTextInverse = Color.white

    // MARK: - 边框色
    static let fmBorder = Color.fmGray200
    static let fmBorderLight = Color.fmGray200
    static let fmBorderHover = Color.fmGray300

    // MARK: - 渐变色
    static let fmGradientPrimary = LinearGradient(
        colors: [Color.fmPrimary, Color.fmPrimaryLight],
        startPoint: .leading,
        endPoint: .trailing
    )

    static let fmGradientSecondary = LinearGradient(
        colors: [Color.fmSecondary, Color.fmSecondaryLight],
        startPoint: .leading,
        endPoint: .trailing
    )

    static let fmGradientWarning = LinearGradient(
        colors: [Color.fmWarning, Color(hex: "FFB84D")],
        startPoint: .leading,
        endPoint: .trailing
    )

    // MARK: - 辅助方法
    init(hex: String) {
        let scanner = Scanner(string: hex)
        var rgbValue: UInt64 = 0
        scanner.scanHexInt64(&rgbValue)

        let r = Double((rgbValue & 0xFF0000) >> 16) / 255.0
        let g = Double((rgbValue & 0x00FF00) >> 8) / 255.0
        let b = Double(rgbValue & 0x0000FF) / 255.0

        self.init(red: r, green: g, blue: b)
    }
}

// MARK: - 阴影样式
extension View {
    func fmCardShadow() -> some View {
        self.shadow(color: Color.black.opacity(0.05), radius: 4, x: 0, y: 2)
    }

    func fmElevatedShadow() -> some View {
        self.shadow(color: Color.black.opacity(0.1), radius: 8, x: 0, y: 4)
    }
}
