import SwiftUI

// MARK: - Timeline Legend Item
struct TimelineLegendItem: View {
    let color: String
    let label: String
    let count: Int

    var body: some View {
        HStack(spacing: 8) {
            Circle()
                .fill(Color(hex: color))
                .frame(width: 10, height: 10)

            Text(label)
                .font(.system(size: 12))
                .foregroundColor(Color.fmText2)

            Spacer()

            Text("\(count)")
                .font(.system(size: 12, weight: .medium))
                .foregroundColor(Color.fmText)
        }
    }
}

// MARK: - Timeline Stat Row
struct TimelineStatRow: View {
    let label: String
    let value: String

    var body: some View {
        HStack {
            Text(label)
                .font(.system(size: 12))
                .foregroundColor(Color.fmText3)

            Spacer()

            Text(value)
                .font(.system(size: 12, weight: .medium))
                .foregroundColor(Color.fmText)
        }
    }
}
