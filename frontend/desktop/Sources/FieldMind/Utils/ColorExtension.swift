import SwiftUI

extension Color {
    // 主色系统
    static let fieldMindPrimary = Color(hex: "178AB7")      // --a1 主蓝
    static let fieldMindSuccess = Color(hex: "9FAC24")      // --a2 黄绿
    static let fieldMindNeutral = Color(hex: "D9BC92")      // --a3 沙色
    static let fieldMindText = Color(hex: "45481D")         // --a4 深橄榄
    static let fieldMindAuxiliary = Color(hex: "6FA7B6")    // --a5 浅蓝
    static let fieldMindBackground = Color(hex: "F7F9FB")   // --bg 背景
    static let fieldMindDanger = Color(hex: "C0392B")       // 危险/删除

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
            (a, r, g, b) = (255, 0, 0, 0)
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
