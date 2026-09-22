"""
FieldMind 组件库 - 折叠面板（Accordion）
参考 chakra-ui Accordion 和 streamlabs 折叠设计
"""
import SwiftUI

// MARK: - Accordion Item 数据模型
struct FMAccordionItem: Identifiable {
    let id = UUID()
    let title: String
    let content: AnyView
    let icon: String?

    init<Content: View>(
        title: String,
        icon: String? = nil,
        @ViewBuilder content: () -> Content
    ) {
        self.title = title
        self.icon = icon
        self.content = AnyView(content())
    }
}

// MARK: - Accordion 组件
struct FMAccordion: View {
    let items: [FMAccordionItem]
    @State private var expandedItems: Set<UUID> = []
    let allowMultiple: Bool

    init(
        items: [FMAccordionItem],
        allowMultiple: Bool = true
    ) {
        self.items = items
        self.allowMultiple = allowMultiple
    }

    var body: some View {
        VStack(spacing: 0) {
            ForEach(items) { item in
                FMAccordionItemView(
                    item: item,
                    isExpanded: expandedItems.contains(item.id),
                    onToggle: {
                        toggleItem(item.id)
                    }
                )
            }
        }
    }

    private func toggleItem(_ id: UUID) {
        withAnimation(.spring(response: 0.3)) {
            if expandedItems.contains(id) {
                expandedItems.remove(id)
            } else {
                if !allowMultiple {
                    expandedItems.removeAll()
                }
                expandedItems.insert(id)
            }
        }
    }
}

// MARK: - Accordion Item View
struct FMAccordionItemView: View {
    let item: FMAccordionItem
    let isExpanded: Bool
    let onToggle: () -> Void

    var body: some View {
        VStack(spacing: 0) {
            // 头部
            Button(action: onToggle) {
                HStack(spacing: Spacing.sm) {
                    if let icon = item.icon {
                        Image(systemName: icon)
                            .foregroundColor(.fmAccent)
                            .frame(width: 20)
                    }

                    Text(item.title)
                        .font(Typography.bodyBold)
                        .foregroundColor(.fmTextPrimary)

                    Spacer()

                    Image(systemName: "chevron.right")
                        .font(.caption)
                        .foregroundColor(.fmTextSecondary)
                        .rotationEffect(.degrees(isExpanded ? 90 : 0))
                }
                .padding(Spacing.md)
                .background(Color.fmBgSecondary)
            }
            .buttonStyle(.plain)

            // 内容区域
            if isExpanded {
                item.content
                    .padding(Spacing.md)
                    .background(Color.fmBgPrimary)
                    .transition(.opacity.combined(with: .move(edge: .top)))
            }

            Divider()
        }
    }
}

// MARK: - 预览
struct FMAccordion_Previews: PreviewProvider {
    static var previews: some View {
        FMAccordion(
            items: [
                FMAccordionItem(title: "项目信息", icon: "info.circle") {
                    VStack(alignment: .leading, spacing: Spacing.sm) {
                        Text("名称：田野调查项目")
                        Text("创建时间：2026-09-09")
                        Text("文档数：156")
                    }
                },
                FMAccordionItem(title: "统计数据", icon: "chart.bar") {
                    Text("这里是统计数据内容")
                },
                FMAccordionItem(title: "设置", icon: "gear") {
                    Text("这里是设置内容")
                }
            ],
            allowMultiple: false
        )
        .padding()
    }
}
