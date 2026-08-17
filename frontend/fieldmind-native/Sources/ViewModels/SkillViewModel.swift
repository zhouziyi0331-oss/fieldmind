import Foundation
import SwiftUI

@MainActor
class SkillViewModel: ObservableObject {
    @Published var availableSkills: [SkillService.SkillInfo] = []
    @Published var enabledSkills: Set<String> = []
    @Published var isLoading = false
    @Published var isSaving = false
    @Published var errorMessage: String?
    @Published var successMessage: String?

    func loadSkills(projectId: Int) async {
        isLoading = true
        errorMessage = nil

        do {
            let config = try await SkillService.shared.getSkillConfig(projectId: projectId)
            availableSkills = config.availableSkills
            enabledSkills = Set(config.enabledSkills)
        } catch {
            errorMessage = "加载技能配置失败: \(error.localizedDescription)"
        }

        isLoading = false
    }

    func toggleSkill(_ skillId: String) {
        if enabledSkills.contains(skillId) {
            enabledSkills.remove(skillId)
        } else {
            enabledSkills.insert(skillId)
        }
    }

    func saveConfig(projectId: Int) async {
        isSaving = true
        errorMessage = nil
        successMessage = nil

        do {
            let config = try await SkillService.shared.updateSkillConfig(
                projectId: projectId,
                enabledSkills: Array(enabledSkills)
            )
            enabledSkills = Set(config.enabledSkills)
            successMessage = "配置保存成功"
        } catch {
            errorMessage = "保存配置失败: \(error.localizedDescription)"
        }

        isSaving = false
    }

    func isSkillEnabled(_ skillId: String) -> Bool {
        enabledSkills.contains(skillId)
    }

    var enabledCount: Int {
        enabledSkills.count
    }

    var totalCount: Int {
        availableSkills.count
    }
}
