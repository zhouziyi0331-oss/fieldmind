import SwiftUI

struct BusiPage: View {
    let projectId: Int
    @StateObject private var viewModel = BusinessAnalysisViewModel()
    @State private var showExistingDetails = true
    @State private var showSuggestedDetails = true

    var body: some View {
        VStack(spacing: 0) {
            headerView
            Divider()

            if let errorMessage = viewModel.errorMessage {
                errorStateView(errorMessage)
            } else if let successMessage = viewModel.successMessage {
                successBanner(successMessage)
            }

            if viewModel.isAnalyzing {
                analyzingView
            } else if !viewModel.hasResults {
                emptyStateView
            } else if let result = viewModel.analysisResult {
                contentView(result)
            }
        }
    }

    private var headerView: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text("业态分析")
                    .font(.system(size: 24, weight: .semibold))
                    .foregroundColor(Color.fmText)

                Text("分析现有业态并建议新业态发展方向")
                    .font(.system(size: 14))
                    .foregroundColor(Color.fmText3)
            }

            Spacer()

            Button(action: {
                Task {
                    await viewModel.analyzeBusinessFormats(projectId: projectId)
                }
            }) {
                HStack(spacing: 6) {
                    if viewModel.isAnalyzing {
                        ProgressView()
                            .scaleEffect(0.7)
                            .frame(width: 14, height: 14)
                    } else {
                        Image(systemName: "chart.bar.doc.horizontal.fill")
                            .font(.system(size: 14))
                    }
                    Text(viewModel.isAnalyzing ? "分析中..." : viewModel.hasResults ? "重新分析" : "开始分析")
                        .font(.system(size: 14, weight: .medium))
                }
                .foregroundColor(.white)
                .padding(.horizontal, 16)
                .padding(.vertical, 8)
                .background(Color.blue)
                .cornerRadius(8)
            }
            .buttonStyle(PlainButtonStyle())
            .disabled(viewModel.isAnalyzing)
        }
        .padding(.horizontal, 24)
        .padding(.vertical, 20)
        .background(Color.fmBg)
    }

    private func errorStateView(_ message: String) -> some View {
        HStack(spacing: 12) {
            Image(systemName: "exclamationmark.triangle.fill")
                .font(.system(size: 16))
                .foregroundColor(.orange)

            Text(message)
                .font(.system(size: 14))
                .foregroundColor(Color.fmText)

            Spacer()

            Button(action: {
                viewModel.errorMessage = nil
            }) {
                Image(systemName: "xmark.circle.fill")
                    .font(.system(size: 16))
                    .foregroundColor(Color.fmText3)
            }
            .buttonStyle(PlainButtonStyle())
        }
        .padding(16)
        .background(Color.orange.opacity(0.1))
    }

    private func successBanner(_ message: String) -> some View {
        HStack(spacing: 12) {
            Image(systemName: "checkmark.circle.fill")
                .font(.system(size: 16))
                .foregroundColor(.green)

            Text(message)
                .font(.system(size: 14))
                .foregroundColor(Color.fmText)

            Spacer()

            Button(action: {
                viewModel.successMessage = nil
            }) {
                Image(systemName: "xmark.circle.fill")
                    .font(.system(size: 16))
                    .foregroundColor(Color.fmText3)
            }
            .buttonStyle(PlainButtonStyle())
        }
        .padding(16)
        .background(Color.green.opacity(0.1))
    }

    private var analyzingView: some View {
        VStack(spacing: 16) {
            ProgressView()
                .scaleEffect(1.2)

            Text("正在分析业态数据...")
                .font(.system(size: 14))
                .foregroundColor(Color.fmText3)

            Text("这可能需要几秒钟时间")
                .font(.system(size: 12))
                .foregroundColor(Color.fmText3)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color.fmBg)
    }

    private var emptyStateView: some View {
        VStack(spacing: 16) {
            Image(systemName: "chart.bar.doc.horizontal")
                .font(.system(size: 64))
                .foregroundColor(Color.fmText3.opacity(0.3))

            Text("业态分析")
                .font(.system(size: 16, weight: .medium))
                .foregroundColor(Color.fmText)

            Text("点击\"开始分析\"按钮，AI将分析项目中的现有业态并建议新的发展方向")
                .font(.system(size: 14))
                .foregroundColor(Color.fmText3)
                .multilineTextAlignment(.center)
                .frame(maxWidth: 400)

            Button(action: {
                Task {
                    await viewModel.analyzeBusinessFormats(projectId: projectId)
                }
            }) {
                HStack(spacing: 6) {
                    Image(systemName: "chart.bar.doc.horizontal.fill")
                        .font(.system(size: 14))
                    Text("开始分析")
                        .font(.system(size: 14, weight: .medium))
                }
                .foregroundColor(.white)
                .padding(.horizontal, 20)
                .padding(.vertical, 10)
                .background(Color.blue)
                .cornerRadius(8)
            }
            .buttonStyle(PlainButtonStyle())
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color.fmBg)
    }

    private func contentView(_ result: BusinessAnalysisResponse) -> some View {
        ScrollView {
            VStack(spacing: 20) {
                // Existing Formats
                if !result.existingFormats.isEmpty {
                    existingFormatsSection(result.existingFormats)
                }

                // Suggested Formats
                if !result.suggestedFormats.isEmpty {
                    suggestedFormatsSection(result.suggestedFormats)
                }

                // Synergy Analysis
                if !result.synergyAnalysis.isEmpty {
                    synergySection(result.synergyAnalysis)
                }

                // Recommendations
                if !result.recommendations.isEmpty {
                    recommendationsSection(result.recommendations)
                }
            }
            .padding(24)
        }
        .background(Color.fmBg)
    }

    private func existingFormatsSection(_ formats: [ExistingFormat]) -> some View {
        VStack(alignment: .leading, spacing: 16) {
            Button(action: { showExistingDetails.toggle() }) {
                HStack {
                    Text("现有业态")
                        .font(.system(size: 18, weight: .semibold))
                        .foregroundColor(Color.fmText)

                    Text("\(formats.count)")
                        .font(.system(size: 14, weight: .medium))
                        .foregroundColor(.white)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 2)
                        .background(Color.blue)
                        .cornerRadius(10)

                    Spacer()

                    Image(systemName: showExistingDetails ? "chevron.up" : "chevron.down")
                        .font(.system(size: 12))
                        .foregroundColor(Color.fmText3)
                }
            }
            .buttonStyle(PlainButtonStyle())

            if showExistingDetails {
                VStack(spacing: 12) {
                    ForEach(formats) { format in
                        ExistingFormatCard(format: format)
                    }
                }
            }
        }
        .padding(20)
        .background(Color.white)
        .cornerRadius(12)
        .shadow(color: Color.black.opacity(0.05), radius: 8, x: 0, y: 2)
    }

    private func suggestedFormatsSection(_ formats: [SuggestedFormat]) -> some View {
        VStack(alignment: .leading, spacing: 16) {
            Button(action: { showSuggestedDetails.toggle() }) {
                HStack {
                    Text("建议新业态")
                        .font(.system(size: 18, weight: .semibold))
                        .foregroundColor(Color.fmText)

                    Text("\(formats.count)")
                        .font(.system(size: 14, weight: .medium))
                        .foregroundColor(.white)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 2)
                        .background(Color.green)
                        .cornerRadius(10)

                    Spacer()

                    Image(systemName: showSuggestedDetails ? "chevron.up" : "chevron.down")
                        .font(.system(size: 12))
                        .foregroundColor(Color.fmText3)
                }
            }
            .buttonStyle(PlainButtonStyle())

            if showSuggestedDetails {
                VStack(spacing: 12) {
                    ForEach(formats) { format in
                        SuggestedFormatCard(format: format)
                    }
                }
            }
        }
        .padding(20)
        .background(Color.white)
        .cornerRadius(12)
        .shadow(color: Color.black.opacity(0.05), radius: 8, x: 0, y: 2)
    }

    private func synergySection(_ synergy: String) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(spacing: 8) {
                Image(systemName: "link.circle.fill")
                    .font(.system(size: 18))
                    .foregroundColor(.purple)

                Text("业态协同效应")
                    .font(.system(size: 18, weight: .semibold))
                    .foregroundColor(Color.fmText)
            }

            Text(synergy)
                .font(.system(size: 14))
                .foregroundColor(Color.fmText2)
                .lineSpacing(6)
        }
        .padding(20)
        .background(Color.white)
        .cornerRadius(12)
        .shadow(color: Color.black.opacity(0.05), radius: 8, x: 0, y: 2)
    }

    private func recommendationsSection(_ recommendations: [String]) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(spacing: 8) {
                Image(systemName: "lightbulb.fill")
                    .font(.system(size: 18))
                    .foregroundColor(.orange)

                Text("发展建议")
                    .font(.system(size: 18, weight: .semibold))
                    .foregroundColor(Color.fmText)
            }

            VStack(alignment: .leading, spacing: 10) {
                ForEach(Array(recommendations.enumerated()), id: \.offset) { index, recommendation in
                    HStack(alignment: .top, spacing: 12) {
                        Text("\(index + 1)")
                            .font(.system(size: 12, weight: .bold))
                            .foregroundColor(.white)
                            .frame(width: 20, height: 20)
                            .background(Color.orange)
                            .cornerRadius(10)

                        Text(recommendation)
                            .font(.system(size: 14))
                            .foregroundColor(Color.fmText2)
                            .lineSpacing(4)
                    }
                }
            }
        }
        .padding(20)
        .background(Color.white)
        .cornerRadius(12)
        .shadow(color: Color.black.opacity(0.05), radius: 8, x: 0, y: 2)
    }
}

struct ExistingFormatCard: View {
    let format: ExistingFormat

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Text(format.name)
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundColor(Color.fmText)

                Spacer()

                statusBadge(format.status)
                scaleBadge(format.scale)
            }

            Text(format.description)
                .font(.system(size: 14))
                .foregroundColor(Color.fmText2)
                .lineSpacing(4)
        }
        .padding(16)
        .background(Color.fmBg2)
        .cornerRadius(8)
    }

    private func statusBadge(_ status: String) -> some View {
        Text(status)
            .font(.system(size: 12, weight: .medium))
            .foregroundColor(statusColor(status))
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(statusColor(status).opacity(0.1))
            .cornerRadius(4)
    }

    private func scaleBadge(_ scale: String) -> some View {
        Text(scale)
            .font(.system(size: 12, weight: .medium))
            .foregroundColor(Color.fmText3)
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(Color.fmBg)
            .cornerRadius(4)
    }

    private func statusColor(_ status: String) -> Color {
        switch status {
        case "运营中": return .green
        case "筹备中": return .orange
        case "规划中": return .blue
        default: return .gray
        }
    }
}

struct SuggestedFormatCard: View {
    let format: SuggestedFormat

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text(format.name)
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundColor(Color.fmText)

                Spacer()

                feasibilityBadge(format.feasibilityScore)
            }

            Text(format.reason)
                .font(.system(size: 14))
                .foregroundColor(Color.fmText2)
                .lineSpacing(4)

            HStack(spacing: 16) {
                VStack(alignment: .leading, spacing: 4) {
                    Text("投资预估")
                        .font(.system(size: 12))
                        .foregroundColor(Color.fmText3)
                    Text(format.investment)
                        .font(.system(size: 14, weight: .medium))
                        .foregroundColor(Color.fmText)
                }

                Divider()
                    .frame(height: 30)

                VStack(alignment: .leading, spacing: 4) {
                    Text("收益潜力")
                        .font(.system(size: 12))
                        .foregroundColor(Color.fmText3)
                    Text(format.revenuePotential)
                        .font(.system(size: 14, weight: .medium))
                        .foregroundColor(Color.fmText)
                }
            }

            if !format.evidence.isEmpty {
                VStack(alignment: .leading, spacing: 6) {
                    Text("数据支撑")
                        .font(.system(size: 13, weight: .medium))
                        .foregroundColor(Color.fmText)

                    ForEach(Array(format.evidence.enumerated()), id: \.offset) { _, evidence in
                        HStack(alignment: .top, spacing: 6) {
                            Text("•")
                                .foregroundColor(Color.fmText3)
                            Text(evidence)
                                .font(.system(size: 13))
                                .foregroundColor(Color.fmText2)
                        }
                    }
                }
                .padding(12)
                .background(Color.blue.opacity(0.05))
                .cornerRadius(6)
            }

            if !format.riskPoints.isEmpty {
                VStack(alignment: .leading, spacing: 6) {
                    Text("风险点")
                        .font(.system(size: 13, weight: .medium))
                        .foregroundColor(.orange)

                    ForEach(Array(format.riskPoints.enumerated()), id: \.offset) { _, risk in
                        HStack(alignment: .top, spacing: 6) {
                            Text("⚠")
                                .foregroundColor(.orange)
                            Text(risk)
                                .font(.system(size: 13))
                                .foregroundColor(Color.fmText2)
                        }
                    }
                }
                .padding(12)
                .background(Color.orange.opacity(0.05))
                .cornerRadius(6)
            }

            if !format.requiredConditions.isEmpty {
                VStack(alignment: .leading, spacing: 6) {
                    Text("所需条件")
                        .font(.system(size: 13, weight: .medium))
                        .foregroundColor(Color.fmText)

                    ForEach(Array(format.requiredConditions.enumerated()), id: \.offset) { _, condition in
                        HStack(alignment: .top, spacing: 6) {
                            Text("✓")
                                .foregroundColor(.green)
                            Text(condition)
                                .font(.system(size: 13))
                                .foregroundColor(Color.fmText2)
                        }
                    }
                }
            }

            if !format.implementationSteps.isEmpty {
                VStack(alignment: .leading, spacing: 6) {
                    Text("实施步骤")
                        .font(.system(size: 13, weight: .medium))
                        .foregroundColor(Color.fmText)

                    ForEach(Array(format.implementationSteps.enumerated()), id: \.offset) { index, step in
                        HStack(alignment: .top, spacing: 8) {
                            Text("\(index + 1)")
                                .font(.system(size: 11, weight: .bold))
                                .foregroundColor(.white)
                                .frame(width: 18, height: 18)
                                .background(Color.blue)
                                .cornerRadius(9)

                            Text(step)
                                .font(.system(size: 13))
                                .foregroundColor(Color.fmText2)
                        }
                    }
                }
            }
        }
        .padding(16)
        .background(Color.fmBg2)
        .cornerRadius(8)
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .stroke(feasibilityColor(format.feasibilityScore).opacity(0.3), lineWidth: 2)
        )
    }

    private func feasibilityBadge(_ score: Int) -> some View {
        HStack(spacing: 4) {
            Text("\(score)")
                .font(.system(size: 16, weight: .bold))
                .foregroundColor(feasibilityColor(score))

            Text("分")
                .font(.system(size: 12))
                .foregroundColor(feasibilityColor(score))
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 6)
        .background(feasibilityColor(score).opacity(0.1))
        .cornerRadius(6)
    }

    private func feasibilityColor(_ score: Int) -> Color {
        switch score {
        case 80...100: return .green
        case 60..<80: return .blue
        case 40..<60: return .orange
        default: return .red
        }
    }
}

