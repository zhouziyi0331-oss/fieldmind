"""
上传页面 - Succulents 设计系统
"""
import SwiftUI

struct SucculentsUploadView: View {
    @State private var files: [UploadFile] = []

    var body: some View {
        ScrollView {
            VStack(spacing: 24) {
                // Header
                VStack(alignment: .leading, spacing: 4) {
                    Text("上传文档")
                        .font(.system(size: 32, weight: .bold))
                        .foregroundColor(.fmTextPrimary)

                    Text("添加文件到您的知识库")
                        .font(.system(size: 16))
                        .foregroundColor(.fmTextSecondary)
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.horizontal, 24)

                // Upload Area
                VStack(spacing: 16) {
                    ZStack {
                        RoundedRectangle(cornerRadius: 12)
                            .strokeBorder(style: StrokeStyle(lineWidth: 2, dash: [8]))
                            .foregroundColor(.fmBorder)

                        VStack(spacing: 12) {
                            Image(systemName: "arrow.up.doc")
                                .font(.system(size: 48))
                                .foregroundColor(.fmTextTertiary)

                            Text("拖放文件到此处或点击上传")
                                .font(.system(size: 18, weight: .medium))

                            Text("支持: PDF, DOC, DOCX, TXT, CSV, Excel")
                                .font(.system(size: 14))
                                .foregroundColor(.fmTextSecondary)
                        }
                        .padding(60)
                    }
                    .frame(height: 300)
                }
                .padding(.horizontal, 24)

                // Files List
                if !files.isEmpty {
                    VStack(alignment: .leading, spacing: 16) {
                        Text("文件 (\(files.count))")
                            .font(.system(size: 18, weight: .semibold))

                        ForEach(files) { file in
                            FileRow(file: file)
                        }
                    }
                    .padding(24)
                    .background(Color.fmBgElevated)
                    .cornerRadius(12)
                    .padding(.horizontal, 24)
                }
            }
            .padding(.vertical, 24)
        }
        .background(Color.fmBgSecondary)
    }
}

struct FileRow: View {
    let file: UploadFile

    var body: some View {
        HStack(spacing: 12) {
            ZStack {
                RoundedRectangle(cornerRadius: 8)
                    .fill(Color.fmPrimary.opacity(0.1))
                    .frame(width: 40, height: 40)

                Image(systemName: "doc.fill")
                    .foregroundColor(.fmPrimary)
            }

            VStack(alignment: .leading, spacing: 2) {
                Text(file.name)
                    .font(.system(size: 14, weight: .medium))
                Text(file.size)
                    .font(.system(size: 12))
                    .foregroundColor(.fmTextSecondary)
            }

            Spacer()

            Button(action: {}) {
                Image(systemName: "xmark")
                    .foregroundColor(.fmError)
            }
            .buttonStyle(.plain)
        }
        .padding(12)
        .background(Color.fmBgSecondary)
        .cornerRadius(8)
    }
}

struct UploadFile: Identifiable {
    let id = UUID()
    let name: String
    let size: String
}

#Preview {
    SucculentsUploadView()
}
