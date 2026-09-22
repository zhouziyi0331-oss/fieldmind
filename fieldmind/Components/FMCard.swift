"""
FieldMind 组件库 - 卡片组件
参考 chakra-ui Card 设计
"""
import SwiftUI

struct FMCard<Content: View>: View {
    let content: Content
    var padding: CGFloat = Spacing.md
    var hasShadow: Bool = true
    var isHoverable: Bool = false

    @State private var isHovered = false

    init(
        padding: CGFloat = Spacing.md,
        hasShadow: Bool = true,
        isHoverable: Bool = false,
        @ViewBuilder content: () -> Content
    ) {
        self.padding = padding
        self.hasShadow = hasShadow
        self.isHoverable = isHoverable
        self.content = content()
    }

    var body: some View {
        content
            .padding(padding)
            .background(Color.fmBgPrimary)
            .cornerRadius(12)
            .shadow(
                color: hasShadow ? Color.black.opacity(0.05) : .clear,
                radius: isHovered ? 12 : 8,
                y: isHovered ? 4 : 2
            )
            .overlay(
                RoundedRectangle(cornerRadius: 12)
                    .stroke(Color.fmBorder, lineWidth: 1)
            )
            .scaleEffect(isHovered ? 1.02 : 1.0)
            .animation(.spring(response: 0.3), value: isHovered)
            .onHover { hovering in
                if isHoverable {
                    isHovered = hovering
                }
            }
    }
}

// MARK: - 统计卡片（Dashboard 用）
struct FMStatCard: View {
    let title: String
    let value: String
    let trend: Double?
    let icon: String?

    var body: some View {
        FMCard(isHoverable: true) {
            VStack(alignment: .leading, spacing: Spacing.sm) {
                HStack {
                    Text(title)
                        .font(Typography.caption)
                        .foregroundColor(.fmTextSecondary)

                    Spacer()

                    if let icon = icon {
                        Image(systemName: icon)
                            .foregroundColor(.fmAccent)
                    }
                }

                Text(value)
                    .font(Typography.h2)
                    .fontWeight(.bold)
                    .foregroundColor(.fmTextPrimary)

                if let trend = trend {
                    HStack(spacing: 4) {
                        Image(systemName: trend >= 0 ? "arrow.up.right" : "arrow.down.right")
                            .font(.caption)
                        Text("\(abs(trend), specifier: "%.1f")%")
                            .font(Typography.small)
                    }
                    .foregroundColor(trend >= 0 ? .fmSuccess : .fmError)
                }
            }
        }
    }
}

// MARK: - 预览
struct FMCard_Previews: PreviewProvider {
    static var previews: some View {
        VStack(spacing: Spacing.lg) {
            FMCard {
                VStack(alignment: .leading, spacing: Spacing.sm) {
                    Text("标题").font(Typography.h3)
                    Text("内容区域").font(Typography.body)
                }
            }

            FMStatCard(
                title: "项目总数",
                value: "12",
                trend: 15.5,
                icon: "folder.fill"
            )
            .frame(width: 200)
        }
        .padding()
    }
}
