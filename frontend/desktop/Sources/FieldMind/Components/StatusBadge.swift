import SwiftUI

struct StatusBadge: View {
    let status: DocumentStatus
    
    var body: some View {
        Text(statusText)
            .font(.system(size: 11, weight: .medium))
            .foregroundColor(.white)
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(backgroundColor)
            .cornerRadius(4)
    }
    
    private var statusText: String {
        switch status {
        case .pending: return "待处理"
        case .processing: return "处理中"
        case .completed: return "已完成"
        case .failed: return "失败"
        }
    }
    
    private var backgroundColor: Color {
        switch status {
        case .pending: return Color.gray
        case .processing: return Color.blue
        case .completed: return Color.green
        case .failed: return Color.red
        }
    }
}
