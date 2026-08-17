import SwiftUI

// FieldMind 设计系统 - 颜色
// 完全复刻 HTML 版本的颜色方案

extension Color {
    // 主色调
    static let fmPrimary = Color(hex: "178AB7")  // 主蓝色 (alias for fmA1)
    static let fmA1 = Color(hex: "178AB7")  // 主蓝色
    static let fmA2 = Color(hex: "9FAC24")  // 次绿色
    static let fmA3 = Color(hex: "D9BC92")  // 辅助色
    static let fmA4 = Color(hex: "45481D")  // 深色
    static let fmA5 = Color(hex: "6FA7B6")  // 浅蓝色

    // 背景色
    static let fmBg = Color(hex: "F7F9FB")
    static let fmBg2 = Color(hex: "EEF1F5")

    // 表面色
    static let fmSurface = Color(hex: "FFFFFF")
    static let fmSurface2 = Color(hex: "F4F6F8")
    static let fmSurface3 = Color(hex: "E8EDF2")

    // 侧边栏
    static let fmSbBg = Color(hex: "178AB7")
    static let fmSbBg2 = Color(hex: "1278A0")
    static let fmSbText = Color.white
    static let fmSbText2 = Color.white.opacity(0.88)
    static let fmSbText3 = Color.white.opacity(0.52)
    static let fmSbBorder = Color.white.opacity(0.14)
    static let fmSbActiveBg = Color.white.opacity(0.18)
    static let fmSbActiveBorder = Color.white.opacity(0.38)
    static let fmSbHover = Color.white.opacity(0.1)

    // 边框
    static let fmBorder = Color(hex: "178AB7").opacity(0.1)
    static let fmBorder2 = Color(hex: "178AB7").opacity(0.22)
    static let fmBorder3 = Color(hex: "178AB7").opacity(0.42)

    // 文字
    static let fmText = Color(hex: "2A2D0F")
    static let fmText2 = Color(hex: "45481D")
    static let fmText3 = Color(hex: "5A6A7A")
    static let fmText4 = Color(hex: "8A9AAA")

    // 淡化色
    static let fmA1Dim = Color(hex: "178AB7").opacity(0.07)
    static let fmA1Dim2 = Color(hex: "178AB7").opacity(0.14)
    static let fmA1Glow = Color(hex: "178AB7").opacity(0.28)
    static let fmA2Dim = Color(hex: "9FAC24").opacity(0.08)
    static let fmA2Dim2 = Color(hex: "9FAC24").opacity(0.16)
    static let fmA2Glow = Color(hex: "9FAC24").opacity(0.26)
    static let fmA3Dim = Color(hex: "D9BC92").opacity(0.15)
    static let fmA3Dim2 = Color(hex: "D9BC92").opacity(0.28)
    static let fmA5Dim = Color(hex: "6FA7B6").opacity(0.09)
    static let fmA5Dim2 = Color(hex: "6FA7B6").opacity(0.17)

    // 错误色
    static let fmRed = Color(hex: "C0392B")
    static let fmRedDim = Color(hex: "C0392B").opacity(0.1)

    // 中性色 - Neutral colors
    static let fmN1 = Color(hex: "E8EDF2")   // 浅灰
    static let fmN2 = Color(hex: "D4DBE2")   // 中浅灰
    static let fmN3 = Color(hex: "B8C2CC")   // 中灰
    static let fmN4 = Color(hex: "9CAAB8")   // 中深灰
    static let fmN5 = Color(hex: "8A9AAA")   // 深灰
    static let fmN6 = Color(hex: "5A6A7A")   // 更深灰
    static let fmN7 = Color(hex: "45481D")   // 接近黑
    static let fmN8 = Color(hex: "2A2D0F")   // 深黑
    static let fmN9 = Color(hex: "1A1D0A")   // 最深黑

    // 语义色 - Semantic colors
    static let fmBlue = Color(hex: "178AB7")     // 蓝色 (同 fmA1)
    static let fmGreen = Color(hex: "27AE60")    // 绿色
    static let fmOrange = Color(hex: "E67E22")   // 橙色
    static let fmPurple = Color(hex: "9B59B6")   // 紫色
    static let fmYellow = Color(hex: "F39C12")   // 黄色
    static let fmPink = Color(hex: "E91E63")     // 粉色

    // 状态色 - Status colors
    static let fmSuccess = Color(hex: "27AE60")   // 成功 (同 fmGreen)
    static let fmWarning = Color(hex: "F39C12")   // 警告 (同 fmYellow)
    static let fmError = Color(hex: "C0392B")     // 错误 (同 fmRed)
    static let fmInfo = Color(hex: "178AB7")      // 信息 (同 fmBlue)

    // 数据可视化色板 - Data visualization colors
    static let fmChart1 = Color(hex: "178AB7")    // 蓝色
    static let fmChart2 = Color(hex: "27AE60")    // 绿色
    static let fmChart3 = Color(hex: "E67E22")    // 橙色
    static let fmChart4 = Color(hex: "9B59B6")    // 紫色
    static let fmChart5 = Color(hex: "C0392B")    // 红色
    static let fmChart6 = Color(hex: "E91E63")    // 粉色

    // 文档类型色 - Document type colors
    static let fmDocTable = Color(hex: "E67E22")  // 表格 - 橙色
    static let fmDocSOP = Color(hex: "3498DB")    // SOP - 浅蓝色
    static let fmDocReport = Color(hex: "E74C3C") // 报告 - 红橙色

    // 辅助浅色背景 - Light backgrounds for selection/hover
    static let fmBlueBg = Color(hex: "EFF6FF")    // 蓝色浅背景
    static let fmGreenBg = Color(hex: "F0FDF4")   // 绿色浅背景
    static let fmOrangeBg = Color(hex: "FFF7ED")  // 橙色浅背景
    static let fmRedBg = Color(hex: "FEF2F2")     // 红色浅背景

    // Hex 初始化器
    init(hex: String) {
        let hex = hex.trimmingCharacters(in: CharacterSet.alphanumerics.inverted)
        var int: UInt64 = 0
        Scanner(string: hex).scanHexInt64(&int)
        let a, r, g, b: UInt64
        switch hex.count {
        case 3: // RGB (12-bit)
            (a, r, g, b) = (255, (int >> 8) * 17, (int >> 4 & 0xF) * 17, (int & 0xF) * 17)
        case 6: // RGB (24-bit)
            (a, r, g, b) = (255, int >> 16, int >> 8 & 0xFF, int & 0xFF)
        case 8: // ARGB (32-bit)
            (a, r, g, b) = (int >> 24, int >> 16 & 0xFF, int >> 8 & 0xFF, int & 0xFF)
        default:
            (a, r, g, b) = (1, 1, 1, 0)
        }

        self.init(
            .sRGB,
            red: Double(r) / 255,
            green: Double(g) / 255,
            blue:  Double(b) / 255,
            opacity: Double(a) / 255
        )
    }
}
