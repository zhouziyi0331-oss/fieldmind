//
//  ProposalViewModel_Merged.swift
//  FieldMind
//
//  深度整合 - 合并自主版本和 Native 版本
//  Generated: Sat Sep 19 11:21:01 CST 2026
//

import SwiftUI

// ========================================
// 主实现（来自主项目）
// ========================================


@MainActor
class ProposalViewModel: ObservableObject {
    @Published var templates: [ProposalService.ProposalTemplate] = []
    @Published var generatedProposal: ProposalService.ProposalData?
    @Published var isLoadingTemplates = false
    @Published var isGenerating = false
    @Published var errorMessage: String?
    @Published var successMessage: String?

    // Generation options
    @Published var selectedTemplateId = "government"
    @Published var includeBudget = true
    @Published var includeRisk = true

    func loadTemplates(projectId: Int) async {
        isLoadingTemplates = true
        errorMessage = nil

        do {
            let response = try await ProposalService.shared.getTemplates(projectId: projectId)
            templates = response.templates
        } catch {
            errorMessage = "加载模板失败: \(error.localizedDescription)"
        }

        isLoadingTemplates = false
    }

    func generateProposal(projectId: Int) async {
        isGenerating = true
        errorMessage = nil
        successMessage = nil

        do {
            let response = try await ProposalService.shared.generateProposal(
                projectId: projectId,
                proposalType: selectedTemplateId,
                includeBudget: includeBudget,
                includeRisk: includeRisk
            )
            generatedProposal = response.proposal
            successMessage = "提案生成成功"
        } catch {
            errorMessage = "生成提案失败: \(error.localizedDescription)"
        }

        isGenerating = false
    }

    func clearProposal() {
        generatedProposal = nil
        errorMessage = nil
        successMessage = nil
    }

    var hasProposal: Bool {
        generatedProposal != nil
    }
}

// ========================================
// Native 版本的扩展功能
// ========================================
// TODO: 手动审查并整合以下功能

/*

@MainActor
class ProposalViewModel: ObservableObject {
    @Published var templates: [ProposalService.ProposalTemplate] = []
    @Published var generatedProposal: ProposalService.ProposalData?
    @Published var isLoadingTemplates = false
    @Published var isGenerating = false
    @Published var errorMessage: String?
    @Published var successMessage: String?

    // Generation options
    @Published var selectedTemplateId = "government"
    @Published var includeBudget = true
    @Published var includeRisk = true

    func loadTemplates(projectId: Int) async {
        isLoadingTemplates = true
        errorMessage = nil

        do {
            let response = try await ProposalService.shared.getTemplates(projectId: projectId)
            templates = response.templates
        } catch {
            errorMessage = "加载模板失败: \(error.localizedDescription)"
        }

        isLoadingTemplates = false
    }

    func generateProposal(projectId: Int) async {
        isGenerating = true
        errorMessage = nil
        successMessage = nil

        do {
            let response = try await ProposalService.shared.generateProposal(
                projectId: projectId,
                proposalType: selectedTemplateId,
                includeBudget: includeBudget,
                includeRisk: includeRisk
            )
            generatedProposal = response.proposal
            successMessage = "提案生成成功"
        } catch {
            errorMessage = "生成提案失败: \(error.localizedDescription)"
        }

        isGenerating = false
    }

    func clearProposal() {
        generatedProposal = nil
        errorMessage = nil
        successMessage = nil
    }

    var hasProposal: Bool {
        generatedProposal != nil
    }
}
*/

