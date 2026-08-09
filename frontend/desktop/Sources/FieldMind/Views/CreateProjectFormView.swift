import SwiftUI

struct CreateProjectFormView: View {
    @Environment(\.dismiss) var dismiss
    @EnvironmentObject var appState: AppState

    @State private var name: String = ""
    @State private var description: String = ""
    @State private var isCreating = false
    @State private var errorMessage: String?

    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("项目信息")) {
                    TextField("项目名称", text: $name)
                        .textFieldStyle(.roundedBorder)

                    TextEditor(text: $description)
                        .frame(height: 100)
                        .overlay(
                            RoundedRectangle(cornerRadius: 4)
                                .stroke(Color.gray.opacity(0.2), lineWidth: 1)
                        )
                        .overlay(
                            Group {
                                if description.isEmpty {
                                    Text("项目描述（可选）")
                                        .foregroundColor(.gray)
                                        .padding(.horizontal, 4)
                                        .padding(.vertical, 8)
                                        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
                                }
                            }
                        )
                }

                if let error = errorMessage {
                    Section {
                        Text(error)
                            .foregroundColor(.red)
                            .font(.system(size: 12))
                    }
                }
            }
            .navigationTitle("创建新项目")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("取消") {
                        dismiss()
                    }
                }

                ToolbarItem(placement: .confirmationAction) {
                    Button("创建") {
                        createProject()
                    }
                    .disabled(name.isEmpty || isCreating)
                }
            }
        }
        .frame(width: 500, height: 300)
    }

    private func createProject() {
        guard !name.isEmpty else {
            errorMessage = "项目名称不能为空"
            return
        }

        isCreating = true
        errorMessage = nil

        Task {
            do {
                let project = try await appState.createProject(
                    name: name,
                    description: description.isEmpty ? nil : description
                )

                await MainActor.run {
                    ToastManager.shared.success("项目创建成功")
                    dismiss()
                }
            } catch {
                await MainActor.run {
                    errorMessage = "创建失败: \(error.localizedDescription)"
                    isCreating = false
                }
            }
        }
    }
}
