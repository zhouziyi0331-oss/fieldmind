import SwiftUI

// FieldMind 卡片组件 - 完全复刻 HTML 版本

struct FMCard<Content: View>: View {
    let content: Content

    init(@ViewBuilder content: () -> Content) {
        self.content = content()
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            content
        }
        .background(Color.fmSurface)
        .cornerRadius(FMRadius.lg)
        .shadow(color: Color.fmA1.opacity(0.07), radius: 6, x: 0, y: 2)
    }
}

// 卡片头部
struct FMCardHeader<Leading: View, Trailing: View>: View {
    let leading: Leading
    let trailing: Trailing

    init(
        @ViewBuilder leading: () -> Leading,
        @ViewBuilder trailing: () -> Trailing = { EmptyView() }
    ) {
        self.leading = leading()
        self.trailing = trailing()
    }

    var body: some View {
        HStack {
            leading
            Spacer()
            trailing
        }
        .padding(.horizontal, FMSpacing.lg)
        .padding(.vertical, FMSpacing.md)
        .background(Color.fmSurface)
    }
}

// 卡片标题
struct FMCardTitle: View {
    let text: String
    let icon: String?

    init(_ text: String, icon: String? = nil) {
        self.text = text
        self.icon = icon
    }

    var body: some View {
        HStack(spacing: FMSpacing.sm) {
            if let icon = icon {
                ZStack {
                    Circle()
                        .fill(Color.fmA1Dim)
                        .frame(width: 28, height: 28)
                    Image(systemName: icon)
                        .font(.system(size: 13))
                        .foregroundColor(.fmA1)
                }
            }
            Text(text)
                .font(FMFont.bodyBold)
                .foregroundColor(.fmText)
        }
    }
}

// 卡片内容
struct FMCardBody<Content: View>: View {
    let content: Content

    init(@ViewBuilder content: () -> Content) {
        self.content = content()
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            content
        }
        .padding(FMSpacing.lg)
    }
}
