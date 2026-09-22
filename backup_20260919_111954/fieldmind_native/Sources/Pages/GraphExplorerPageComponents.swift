import SwiftUI

// MARK: - Graph Legend Item
struct GraphLegendItem: View {
    let color: String
    let icon: String
    let label: String
    let count: Int

    var body: some View {
        HStack(spacing: 10) {
            ZStack {
                Circle()
                    .fill(Color(hex: color))
                    .frame(width: 24, height: 24)

                Image(systemName: icon)
                    .font(.system(size: 10))
                    .foregroundColor(.white)
            }

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

// MARK: - Graph Relationship Legend Item
struct GraphRelationshipLegendItem: View {
    let label: String
    let count: Int

    var body: some View {
        HStack(spacing: 10) {
            Image(systemName: "arrow.right")
                .font(.system(size: 10))
                .foregroundColor(Color.fmText3)
                .frame(width: 24)

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

// MARK: - Graph Stat Row
struct GraphStatRow: View {
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
