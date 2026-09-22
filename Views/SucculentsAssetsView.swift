"""
资产库页面 - Succulents 设计系统
"""
import SwiftUI

struct SucculentsAssetsView: View {
    @StateObject private var viewModel = AssetsViewModel()

    var body: some View {
        ScrollView {
            VStack(spacing: 24) {
                // Header
                HStack {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("资产库")
                            .font(.system(size: 32, weight: .bold))
                            .foregroundColor(.fmTextPrimary)

                        Text("管理可复用的知识资产")
                            .font(.system(size: 16))
                            .foregroundColor(.fmTextSecondary)
                    }

                    Spacer()

                    Button(action: {}) {
                        HStack(spacing: 6) {
                            Image(systemName: "arrow.up.doc")
                            Text("上传资产")
                        }
                        .font(.system(size: 14, weight: .medium))
                        .foregroundColor(.white)
                        .padding(.horizontal, 16)
                        .padding(.vertical, 10)
                        .background(Color.fmPrimary)
                        .cornerRadius(8)
                    }
                    .buttonStyle(.plain)
                }
                .padding(.horizontal, 24)

                // Assets Grid
                LazyVGrid(columns: Array(repeating: GridItem(.flexible(), spacing: 16), count: 3), spacing: 16) {
                    ForEach(viewModel.assets) { asset in
                        AssetCardView(asset: asset)
                    }
                }
                .padding(.horizontal, 24)
            }
            .padding(.vertical, 24)
        }
        .background(Color.fmBgSecondary)
    }
}

struct AssetCardView: View {
    let asset: AssetItem

    var body: some View {
        VStack(spacing: 0) {
            // Asset Preview
            ZStack {
                Rectangle()
                    .fill(asset.color.opacity(0.15))
                    .frame(height: 160)

                Image(systemName: "cube.fill")
                    .font(.system(size: 48))
                    .foregroundColor(asset.color)
            }

            VStack(alignment: .leading, spacing: 12) {
                Text(asset.name)
                    .font(.system(size: 18, weight: .semibold))
                    .foregroundColor(.fmTextPrimary)

                Text(asset.description)
                    .font(.system(size: 14))
                    .foregroundColor(.fmTextSecondary)
                    .lineLimit(2)

                HStack {
                    Text(asset.type)
                        .font(.system(size: 12))
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(Color.fmInfo.opacity(0.1))
                        .foregroundColor(.fmInfo)
                        .cornerRadius(12)

                    Spacer()

                    HStack(spacing: 4) {
                        Image(systemName: "arrow.down.circle")
                            .font(.system(size: 12))
                        Text("\(asset.downloads)")
                            .font(.system(size: 12))
                    }
                    .foregroundColor(.fmTextTertiary)
                }
            }
            .padding(16)
        }
        .background(Color.fmBgElevated)
        .cornerRadius(12)
        .fmCardShadow()
    }
}

class AssetsViewModel: ObservableObject {
    @Published var assets: [AssetItem] = [
        AssetItem(name: "分析模板", description: "数据分析模板", type: "模板", downloads: 342, color: Color.fmPrimary),
        AssetItem(name: "ML模型 v3", description: "机器学习模型", type: "模型", downloads: 156, color: Color.fmSecondary),
        AssetItem(name: "训练数据集", description: "精选数据集", type: "数据集", downloads: 89, color: Color.fmWarning)
    ]
}

struct AssetItem: Identifiable {
    let id = UUID()
    let name: String
    let description: String
    let type: String
    let downloads: Int
    let color: Color
}

#Preview {
    SucculentsAssetsView()
}
