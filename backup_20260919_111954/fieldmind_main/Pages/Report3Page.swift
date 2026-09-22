import SwiftUI

struct Report3Page: View {
    let projectId: Int
    @StateObject private var viewModel = ProposalViewModel()
    @State private var showGenerateSheet = false

    var body: some View {
        VStack(spacing: 0) {
            headerView
            Divider()

            if let errorMessage = viewModel.errorMessage {
                errorBanner(errorMessage)
            }

            if let successMessage = viewModel.successMessage {
                successBanner(successMessage)
            }

            if viewModel.isGenerating {
                generatingView
            } else if !viewModel.hasProposal {
                emptyStateView
            } else if let proposal = viewModel.generatedProposal {
                proposalContentView(proposal)
            }
        }
        .sheet(isPresented: $showGenerateSheet) {
            generateOptionsSheet
        }
        .task {
            await viewModel.loadTemplates(projectId: projectId)
        }
    }

    private var headerView: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text("提案生成")
                    .font(.system(size: 24, weight: .semibold))
                    .foregroundColor(Color.fmText)

                Text("根据项目分析自动生成汇报提案")
                    .font(.system(size: 14))
                    .foregroundColor(Color.fmText3)
            }

            Spacer()

            if viewModel.hasProposal {
                HStack(spacing: 12) {
                    Button(action: {
                        viewModel.clearProposal()
                    }) {
                        HStack(spacing: 6) {
                            Image(systemName: "trash")
                                .font(.system(size: 14))
                            Text("清除")
                                .font(.system(size: 14, weight: .medium))
                        }
                        .foregroundColor(.red)
                        .padding(.horizontal, 16)
                        .padding(.vertical, 8)
                        .background(Color.red.opacity(0.1))
                        .cornerRadius(8)
                    }
                    .buttonStyle(PlainButtonStyle())

                    Button(action: {
                        showGenerateSheet = true
                    }) {
                        HStack(spacing: 6) {
                            Image(systemName: "arrow.clockwise")
                                .font(.system(size: 14))
                            Text("重新生成")
                                .font(.system(size: 14, weight: .medium))
                        }
                        .foregroundColor(.white)
                        .padding(.horizontal, 16)
                        .padding(.vertical, 8)
                        .background(Color.blue)
                        .cornerRadius(8)
                    }
                    .buttonStyle(PlainButtonStyle())
                }
            } else {
                Button(action: {
                    showGenerateSheet = true
                }) {
                    HStack(spacing: 6) {
                        Image(systemName: "doc.text.fill")
                            .font(.system(size: 14))
                        Text("生成提案")
                            .font(.system(size: 14, weight: .medium))
                    }
                    .foregroundColor(.white)
                    .padding(.horizontal, 16)
                    .padding(.vertical, 8)
                    .background(Color.blue)
                    .cornerRadius(8)
                }
                .buttonStyle(PlainButtonStyle())
            }
        }
        .padding(.horizontal, 24)
        .padding(.vertical, 20)
        .background(Color.fmBg)
    }

    private func errorBanner(_ message: String) -> some View {
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

    private var generatingView: some View {
        VStack(spacing: 16) {
            ProgressView()
                .scaleEffect(1.2)

            Text("正在生成提案...")
                .font(.system(size: 14))
                .foregroundColor(Color.fmText3)

            Text("AI正在分析项目数据并组织提案内容")
                .font(.system(size: 12))
                .foregroundColor(Color.fmText3)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color.fmBg)
    }

    private var emptyStateView: some View {
        VStack(spacing: 16) {
            Image(systemName: "doc.text")
                .font(.system(size: 64))
                .foregroundColor(Color.fmText3.opacity(0.3))

            Text("提案生成")
                .font(.system(size: 16, weight: .medium))
                .foregroundColor(Color.fmText)

            Text("根据项目的分析结果，自动生成可用于汇报的提案文档")
                .font(.system(size: 14))
                .foregroundColor(Color.fmText3)
                .multilineTextAlignment(.center)
                .frame(maxWidth: 400)

            Button(action: {
                showGenerateSheet = true
            }) {
                HStack(spacing: 6) {
                    Image(systemName: "doc.text.fill")
                        .font(.system(size: 14))
                    Text("生成提案")
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

    private func proposalContentView(_ proposal: ProposalService.ProposalData) -> some View {
        ScrollView {
            VStack(spacing: 24) {
                // Header
                VStack(alignment: .leading, spacing: 12) {
                    Text(proposal.title)
                        .font(.system(size: 28, weight: .bold))
                        .foregroundColor(Color.fmText)

                    HStack(spacing: 16) {
                        HStack(spacing: 6) {
                            Image(systemName: "doc.text")
                                .font(.system(size: 13))
                            Text(proposalTypeName(proposal.proposalType))
                                .font(.system(size: 13))
                        }
                        .foregroundColor(Color.fmText3)

                        HStack(spacing: 6) {
                            Image(systemName: "calendar")
                                .font(.system(size: 13))
                            Text(proposal.generatedAt)
                                .font(.system(size: 13))
                        }
                        .foregroundColor(Color.fmText3)
                    }
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(24)
                .background(Color.white)
                .cornerRadius(12)
                .shadow(color: Color.black.opacity(0.05), radius: 8, x: 0, y: 2)

                // Sections
                ForEach(Array(proposal.sections.enumerated()), id: \.offset) { index, section in
                    VStack(alignment: .leading, spacing: 12) {
                        HStack(spacing: 8) {
                            Text("\(index + 1)")
                                .font(.system(size: 14, weight: .bold))
                                .foregroundColor(.white)
                                .frame(width: 28, height: 28)
                                .background(Color.blue)
                                .cornerRadius(14)

                            Text(section.title)
                                .font(.system(size: 18, weight: .semibold))
                                .foregroundColor(Color.fmText)
                        }

                        Text(section.content)
                            .font(.system(size: 14))
                            .foregroundColor(Color.fmText2)
                            .lineSpacing(6)
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(20)
                    .background(Color.white)
                    .cornerRadius(12)
                    .shadow(color: Color.black.opacity(0.05), radius: 8, x: 0, y: 2)
                }
            }
            .padding(24)
        }
        .background(Color.fmBg)
    }

    private var generateOptionsSheet: some View {
        VStack(spacing: 24) {
            HStack {
                Text("生成提案")
                    .font(.system(size: 20, weight: .semibold))
                    .foregroundColor(Color.fmText)

                Spacer()

                Button(action: {
                    showGenerateSheet = false
                }) {
                    Image(systemName: "xmark.circle.fill")
                        .font(.system(size: 20))
                        .foregroundColor(Color.fmText3)
                }
                .buttonStyle(PlainButtonStyle())
            }

            Divider()

            VStack(alignment: .leading, spacing: 16) {
                Text("提案类型")
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(Color.fmText)

                ForEach(viewModel.templates) { template in
                    Button(action: {
                        viewModel.selectedTemplateId = template.id
                    }) {
                        HStack(spacing: 12) {
                            ZStack {
                                Circle()
                                    .stroke(viewModel.selectedTemplateId == template.id ? Color.blue : Color.fmBorder, lineWidth: 2)
                                    .frame(width: 20, height: 20)

                                if viewModel.selectedTemplateId == template.id {
                                    Circle()
                                        .fill(Color.blue)
                                        .frame(width: 12, height: 12)
                                }
                            }

                            VStack(alignment: .leading, spacing: 4) {
                                Text(template.name)
                                    .font(.system(size: 14, weight: .medium))
                                    .foregroundColor(Color.fmText)

                                Text(template.description)
                                    .font(.system(size: 12))
                                    .foregroundColor(Color.fmText3)
                            }

                            Spacer()
                        }
                        .padding(12)
                        .background(viewModel.selectedTemplateId == template.id ? Color.blue.opacity(0.05) : Color.fmBg2)
                        .cornerRadius(8)
                    }
                    .buttonStyle(PlainButtonStyle())
                }
            }

            VStack(alignment: .leading, spacing: 12) {
                Text("包含内容")
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(Color.fmText)

                Toggle("预算框架", isOn: $viewModel.includeBudget)
                    .toggleStyle(SwitchToggleStyle())

                Toggle("风险评估", isOn: $viewModel.includeRisk)
                    .toggleStyle(SwitchToggleStyle())
            }

            Spacer()

            HStack(spacing: 12) {
                Button(action: {
                    showGenerateSheet = false
                }) {
                    Text("取消")
                        .font(.system(size: 14, weight: .medium))
                        .foregroundColor(Color.fmText)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 10)
                        .background(Color.fmBg2)
                        .cornerRadius(8)
                }
                .buttonStyle(PlainButtonStyle())

                Button(action: {
                    showGenerateSheet = false
                    Task {
                        await viewModel.generateProposal(projectId: projectId)
                    }
                }) {
                    Text("生成")
                        .font(.system(size: 14, weight: .medium))
                        .foregroundColor(.white)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 10)
                        .background(Color.blue)
                        .cornerRadius(8)
                }
                .buttonStyle(PlainButtonStyle())
            }
        }
        .padding(24)
        .frame(width: 500, height: 600)
    }

    private func proposalTypeName(_ type: String) -> String {
        switch type {
        case "government": return "政府汇报型"
        case "academic": return "学术汇报型"
        case "business": return "商业计划型"
        default: return type
        }
    }
}
