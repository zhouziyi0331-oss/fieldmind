import SwiftUI

// MARK: - InfoRow Component
struct InfoRow: View {
    let label: String
    let value: String

    var body: some View {
        HStack(alignment: .top, spacing: 8) {
            Text(label + ":")
                .font(.system(size: 12))
                .foregroundColor(.fmText3)
                .frame(width: 60, alignment: .leading)

            Text(value)
                .font(.system(size: 12))
                .foregroundColor(.fmText)
                .frame(maxWidth: .infinity, alignment: .leading)
        }
    }
}
