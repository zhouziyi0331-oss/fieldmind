import Foundation
import SwiftUI

@MainActor
class ReportViewModel: ObservableObject {
    @Published var reports: [GeneratedReport] = []
    @Published var isGenerating = false
    @Published var errorMessage: String?
    @Published var successMessage: String?

    private let service = ReportService.shared

    // MARK: - Generated Report Model

    struct GeneratedReport: Identifiable {
        let id = UUID()
        let level: Int
        let content: String
        let documentsUsed: Int
        let generationMethod: String
        let generatedAt: Date
        let message: String?

        var levelName: String {
            switch level {
            case 1: return "一度报告"
            case 2: return "二度报告"
            case 3: return "三度报告"
            default: return "报告"
            }
        }

        var levelDescription: String {
            switch level {
            case 1: return "基于材料的直接分析"
            case 2: return "费孝通框架分析"
            case 3: return "综合多维度分析"
            default: return ""
            }
        }
    }

    // MARK: - Methods

    func generateReport(projectId: Int, documentIds: [Int]?, reportLevel: Int) async {
        isGenerating = true
        errorMessage = nil
        successMessage = nil

        do {
            let response = try await service.generateReport(
                projectId: projectId,
                documentIds: documentIds,
                reportLevel: reportLevel
            )

            if response.success {
                let report = GeneratedReport(
                    level: response.reportLevel,
                    content: response.reportContent,
                    documentsUsed: response.documentsUsed,
                    generationMethod: response.generationMethod,
                    generatedAt: Date(),
                    message: response.message
                )
                reports.insert(report, at: 0)
                successMessage = "报告生成成功"
            } else {
                errorMessage = response.message ?? "报告生成失败"
            }
        } catch {
            errorMessage = "生成报告失败: \(error.localizedDescription)"
        }

        isGenerating = false
    }

    func clearReports() {
        reports.removeAll()
        errorMessage = nil
        successMessage = nil
    }

    func deleteReport(id: UUID) {
        reports.removeAll { $0.id == id }
    }
}
