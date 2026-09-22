"""
FieldMind 组件库 - 搜索框
参考 chakra-ui Input 设计
"""
import SwiftUI

struct FMSearchField: View {
    @Binding var text: String
    let placeholder: String
    var onSubmit: (() -> Void)?

    var body: some View {
        HStack(spacing: Spacing.sm) {
            Image(systemName: "magnifyingglass")
                .foregroundColor(.fmTextSecondary)
                .font(.body)

            TextField(placeholder, text: $text)
                .textFieldStyle(.plain)
                .font(Typography.body)
                .onSubmit {
                    onSubmit?()
                }

            if !text.isEmpty {
                Button(action: { text = "" }) {
                    Image(systemName: "xmark.circle.fill")
                        .foregroundColor(.fmTextSecondary)
                }
                .buttonStyle(.plain)
            }
        }
        .padding(Spacing.sm)
        .background(Color.fmBgSecondary)
        .cornerRadius(8)
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .stroke(Color.fmBorder, lineWidth: 1)
        )
    }
}

// MARK: - 状态徽章
struct FMStatusBadge: View {
    let status: String
    let color: Color

    init(status: String) {
        self.status = status
        switch status {
        case "completed", "已完成":
            self.color = .fmSuccess
        case "processing", "处理中":
            self.color = .fmInfo
        case "pending", "等待中":
            self.color = .fmWarning
        case "failed", "失败":
            self.color = .fmError
        default:
            self.color = .fmTextSecondary
        }
    }

    var body: some View {
        Text(status)
            .font(Typography.small)
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(color.opacity(0.1))
            .foregroundColor(color)
            .cornerRadius(4)
    }
}
