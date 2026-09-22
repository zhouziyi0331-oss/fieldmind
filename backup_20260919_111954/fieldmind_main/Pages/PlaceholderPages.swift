import SwiftUI

// 临时占位页面，后续逐个实现

// 通用占位符视图
struct PlaceholderView: View {
    let title: String
    let icon: String

    var body: some View {
        VStack(spacing: 16) {
            ZStack {
                Circle()
                    .fill(Color.fmA1.opacity(0.12))
                    .frame(width: 80, height: 80)

                Image(systemName: icon)
                    .font(.system(size: 36))
                    .foregroundColor(.fmA1.opacity(0.5))
            }

            VStack(spacing: 6) {
                Text(title)
                    .font(.system(size: 15, weight: .bold))
                    .foregroundColor(.fmText)

                Text("开发中...")
                    .font(.system(size: 11))
                    .foregroundColor(.fmText3)
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

// UploadPage - moved to dedicated file
// FileManagerPage - moved to dedicated file
// PhotosPage - moved to dedicated file
// TablesPage - moved to dedicated file
// ConversationsPage - moved to dedicated file
// CitationsPage - moved to dedicated file
// VeinPage - moved to dedicated file
// ChroniclePage - moved to dedicated file
// TimelinePage - moved to dedicated file
// GraphExplorerPage - moved to dedicated file
// ReportPage - moved to dedicated file
// Report3Page - moved to dedicated file
// BusiPage - moved to dedicated file
// SOPPage - moved to dedicated file
// SOPAnalysisPage - moved to dedicated file
// WorkflowPage - moved to dedicated file
// SkillPage - moved to dedicated file
// AgentMemoryPage - moved to dedicated file

// AdvancedSearchPage - moved to dedicated file

// QualityMonitorPage - moved to dedicated file

// ModelPage - moved to dedicated file

// SettingsPage - moved to dedicated file

// ProjectDetailPage - moved to dedicated file
