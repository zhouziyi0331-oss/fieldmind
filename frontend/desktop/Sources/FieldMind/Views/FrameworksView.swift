import SwiftUI

struct FrameworksView: View {
    @State private var selectedFrameworkType: FrameworkType = .feixiaotong
    @State private var selectedFramework: AnalysisFramework?

    var frameworks: [AnalysisFramework] {
        switch selectedFrameworkType {
        case .feixiaotong:
            return FeiXiaotongFramework.all
        case .sop:
            return SOPFramework.all
        case .custom:
            return []
        }
    }

    var body: some View {
        VStack(spacing: 0) {
            // 工具栏
            HStack {
                Text("二度分析框架")
                    .font(.system(size: 18, weight: .semibold))

                Spacer()

                Picker("", selection: $selectedFrameworkType) {
                    Text("费孝通理论").tag(FrameworkType.feixiaotong)
                    Text("SOP 框架").tag(FrameworkType.sop)
                    Text("自定义框架").tag(FrameworkType.custom)
                }
                .pickerStyle(.segmented)
                .frame(width: 350)
            }
            .padding()
            .background(Color(NSColor.controlBackgroundColor))

            Divider()

            // 框架内容
            HSplitView {
                // 左侧：框架列表
                VStack(spacing: 0) {
                    HStack {
                        Text("框架列表")
                            .font(.system(size: 16, weight: .semibold))
                        Spacer()
                    }
                    .padding()
                    .background(Color(NSColor.controlBackgroundColor))

                    Divider()

                    if frameworks.isEmpty {
                        EmptyStateView(icon: "list.bullet.clipboard", message: "暂无自定义框架")
                    } else {
                        ScrollView {
                            LazyVStack(spacing: 8) {
                                ForEach(frameworks) { framework in
                                    FrameworkRow(framework: framework, isSelected: selectedFramework?.id == framework.id)
                                        .onTapGesture {
                                            selectedFramework = framework
                                        }
                                }
                            }
                            .padding(12)
                        }
                    }
                }
                .frame(minWidth: 280, idealWidth: 320)

                // 右侧：框架详情
                if let framework = selectedFramework {
                    FrameworkDetailView(framework: framework)
                } else {
                    EmptyStateView(icon: "arrow.left", message: "从左侧选择一个分析框架")
                }
            }
        }
        .onAppear {
            if !frameworks.isEmpty {
                selectedFramework = frameworks[0]
            }
        }
        .onChange(of: selectedFrameworkType) { _, _ in
            selectedFramework = frameworks.isEmpty ? nil : frameworks[0]
        }
    }
}

struct FrameworkRow: View {
    let framework: AnalysisFramework
    let isSelected: Bool

    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: "list.bullet.clipboard.fill")
                .font(.system(size: 18))
                .foregroundColor(frameworkColor(framework.type))

            VStack(alignment: .leading, spacing: 4) {
                Text(framework.name)
                    .font(.system(size: 15, weight: .medium))
                    .lineLimit(1)

                Text(framework.description)
                    .font(.system(size: 12))
                    .foregroundColor(.secondary)
                    .lineLimit(1)
            }

            Spacer()
        }
        .padding(12)
        .background(isSelected ? frameworkColor(framework.type).opacity(0.15) : Color.clear)
        .cornerRadius(8)
    }

    private func frameworkColor(_ type: FrameworkType) -> Color {
        switch type {
        case .feixiaotong: return Color(hex: "667eea")
        case .sop: return Color(hex: "48bb78")
        case .custom: return Color(hex: "ed8936")
        }
    }
}

struct FrameworkDetailView: View {
    let framework: AnalysisFramework

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 24) {
                // 框架标题
                VStack(alignment: .leading, spacing: 12) {
                    HStack {
                        Image(systemName: "list.bullet.clipboard.fill")
                            .font(.system(size: 32))
                            .foregroundColor(frameworkColor(framework.type))

                        Spacer()

                        Text(frameworkTypeText(framework.type))
                            .font(.system(size: 13))
                            .padding(.horizontal, 12)
                            .padding(.vertical, 6)
                            .background(frameworkColor(framework.type).opacity(0.15))
                            .foregroundColor(frameworkColor(framework.type))
                            .cornerRadius(8)
                    }

                    Text(framework.name)
                        .font(.system(size: 24, weight: .bold))

                    Text(framework.description)
                        .font(.system(size: 15))
                        .foregroundColor(.secondary)
                }

                // 框架组成部分
                VStack(alignment: .leading, spacing: 16) {
                    Text("分析维度")
                        .font(.system(size: 18, weight: .semibold))

                    ForEach(framework.components) { component in
                        ComponentCard(component: component, frameworkType: framework.type)
                    }
                }

                // 使用说明
                VStack(alignment: .leading, spacing: 12) {
                    Text("使用方法")
                        .font(.system(size: 18, weight: .semibold))

                    VStack(alignment: .leading, spacing: 8) {
                        InstructionRow(
                            number: 1,
                            text: "在智能对话页面创建新会话"
                        )
                        InstructionRow(
                            number: 2,
                            text: "选择此分析框架作为对话的分析视角"
                        )
                        InstructionRow(
                            number: 3,
                            text: "根据框架的引导问题进行对话和分析"
                        )
                        InstructionRow(
                            number: 4,
                            text: "系统将基于框架结构生成分析报告"
                        )
                    }
                    .padding()
                    .background(Color(NSColor.controlBackgroundColor))
                    .cornerRadius(10)
                }
            }
            .padding(24)
        }
    }

    private func frameworkColor(_ type: FrameworkType) -> Color {
        switch type {
        case .feixiaotong: return Color(hex: "667eea")
        case .sop: return Color(hex: "48bb78")
        case .custom: return Color(hex: "ed8936")
        }
    }

    private func frameworkTypeText(_ type: FrameworkType) -> String {
        switch type {
        case .feixiaotong: return "费孝通理论"
        case .sop: return "SOP 框架"
        case .custom: return "自定义"
        }
    }
}

struct ComponentCard: View {
    let component: FrameworkComponent
    let frameworkType: FrameworkType

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Circle()
                    .fill(frameworkColor(frameworkType))
                    .frame(width: 8, height: 8)

                Text(component.name)
                    .font(.system(size: 16, weight: .semibold))
            }

            Text(component.description)
                .font(.system(size: 14))
                .foregroundColor(.secondary)

            if !component.questions.isEmpty {
                VStack(alignment: .leading, spacing: 8) {
                    Text("引导问题:")
                        .font(.system(size: 13, weight: .medium))

                    ForEach(Array(component.questions.enumerated()), id: \.offset) { index, question in
                        HStack(alignment: .top, spacing: 8) {
                            Text("\(index + 1).")
                                .font(.system(size: 12))
                                .foregroundColor(.secondary)

                            Text(question)
                                .font(.system(size: 13))
                                .fixedSize(horizontal: false, vertical: true)
                        }
                    }
                }
                .padding(12)
                .background(Color(NSColor.windowBackgroundColor))
                .cornerRadius(8)
            }
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color(NSColor.controlBackgroundColor))
        .cornerRadius(10)
    }

    private func frameworkColor(_ type: FrameworkType) -> Color {
        switch type {
        case .feixiaotong: return Color(hex: "667eea")
        case .sop: return Color(hex: "48bb78")
        case .custom: return Color(hex: "ed8936")
        }
    }
}

struct InstructionRow: View {
    let number: Int
    let text: String

    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            Text("\(number)")
                .font(.system(size: 14, weight: .bold))
                .foregroundColor(.white)
                .frame(width: 28, height: 28)
                .background(Color(hex: "667eea"))
                .clipShape(Circle())

            Text(text)
                .font(.system(size: 14))
                .fixedSize(horizontal: false, vertical: true)

            Spacer()
        }
    }
}
