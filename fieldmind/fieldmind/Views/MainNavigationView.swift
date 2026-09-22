//
//  MainNavigationView.swift
//  FieldMind
//
//  统一的主导航界面
//

import SwiftUI

enum NavigationItem: String, CaseIterable, Identifiable {
    case dashboard = "仪表盘"
    case vault = "知识库"
    case distillation = "知识蒸馏"
    case projects = "项目"
    case workflows = "工作流"
    case documents = "文档"
    case assets = "资产"
    case chat = "对话"
    case settings = "设置"

    var id: String { rawValue }

    var icon: String {
        switch self {
        case .dashboard: return "square.grid.2x2"
        case .vault: return "book.closed"
        case .distillation: return "wand.and.stars"
        case .projects: return "folder"
        case .workflows: return "arrow.triangle.branch"
        case .documents: return "doc.text"
        case .assets: return "photo.on.rectangle.angled"
        case .chat: return "message"
        case .settings: return "gearshape"
        }
    }

    var color: Color {
        switch self {
        case .dashboard: return .blue
        case .vault: return .orange
        case .distillation: return .purple
        case .projects: return .green
        case .workflows: return .indigo
        case .documents: return .cyan
        case .assets: return .pink
        case .chat: return .mint
        case .settings: return .gray
        }
    }
}

struct MainNavigationView: View {
    @State private var selectedItem: NavigationItem = .dashboard
    @EnvironmentObject var backendService: BackendService

    var body: some View {
        NavigationSplitView {
            // 侧边栏
            List(NavigationItem.allCases, selection: $selectedItem) { item in
                NavigationLink(value: item) {
                    Label {
                        Text(item.rawValue)
                    } icon: {
                        Image(systemName: item.icon)
                            .foregroundColor(item.color)
                    }
                }
            }
            .navigationTitle("FieldMind")
            .navigationSplitViewColumnWidth(min: 200, ideal: 220, max: 300)
            .toolbar {
                ToolbarItem(placement: .status) {
                    HStack(spacing: 4) {
                        Circle()
                            .fill(backendService.isRunning ? Color.green : Color.red)
                            .frame(width: 8, height: 8)
                        Text(backendService.isRunning ? "后端运行中" : "后端未启动")
                            .font(.caption2)
                            .foregroundColor(.secondary)
                    }
                }
            }
        } detail: {
            // 主内容区
            Group {
                switch selectedItem {
                case .dashboard:
                    DashboardView()
                case .vault:
                    KnowledgeVaultView()
                case .distillation:
                    DistillationView()
                case .projects:
                    ProjectsView()
                case .workflows:
                    WorkflowsView()
                case .documents:
                    DocumentsView()
                case .assets:
                    AssetsView()
                case .chat:
                    ChatView()
                case .settings:
                    SettingsView()
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
        }
    }
}

// MARK: - 仪表盘

struct DashboardView: View {
    @EnvironmentObject var backendService: BackendService
    @StateObject private var vaultService = KnowledgeVaultService.shared
    @StateObject private var distillationService = DistillationService.shared

    var body: some View {
        ScrollView {
            VStack(spacing: 20) {
                // 欢迎卡片
                WelcomeCard()

                // 统计卡片
                HStack(spacing: 20) {
                    StatCard(
                        title: "笔记总数",
                        value: "\(vaultService.notes.count)",
                        icon: "book.closed",
                        color: .orange
                    )

                    StatCard(
                        title: "蒸馏任务",
                        value: "-",
                        icon: "wand.and.stars",
                        color: .purple
                    )

                    StatCard(
                        title: "项目数",
                        value: "-",
                        icon: "folder",
                        color: .green
                    )
                }

                // 快速操作
                QuickActionsCard()

                // 最近活动
                RecentActivityCard(vaultService: vaultService)
            }
            .padding()
        }
        .navigationTitle("仪表盘")
    }
}

struct WelcomeCard: View {
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text("欢迎回来！")
                        .font(.title)
                        .bold()
                    Text("继续你的工作")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }
                Spacer()
                Image(systemName: "sparkles")
                    .font(.system(size: 40))
                    .foregroundColor(.blue)
            }
        }
        .frame(maxWidth: .infinity)
        .padding()
        .background(
            LinearGradient(
                colors: [.blue.opacity(0.1), .purple.opacity(0.1)],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
        )
        .cornerRadius(12)
    }
}

struct StatCard: View {
    let title: String
    let value: String
    let icon: String
    let color: Color

    var body: some View {
        VStack(spacing: 12) {
            Image(systemName: icon)
                .font(.system(size: 30))
                .foregroundColor(color)

            Text(value)
                .font(.title)
                .bold()

            Text(title)
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .frame(maxWidth: .infinity)
        .padding()
        .background(color.opacity(0.1))
        .cornerRadius(12)
    }
}

struct QuickActionsCard: View {
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("快速操作")
                .font(.headline)

            HStack(spacing: 12) {
                QuickActionButton(title: "新建笔记", icon: "plus.circle", color: .orange)
                QuickActionButton(title: "开始蒸馏", icon: "wand.and.stars", color: .purple)
                QuickActionButton(title: "新建项目", icon: "folder.badge.plus", color: .green)
                QuickActionButton(title: "AI 对话", icon: "message", color: .mint)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding()
        .background(Color.secondary.opacity(0.05))
        .cornerRadius(12)
    }
}

struct QuickActionButton: View {
    let title: String
    let icon: String
    let color: Color

    var body: some View {
        VStack(spacing: 8) {
            Image(systemName: icon)
                .font(.title2)
                .foregroundColor(color)
            Text(title)
                .font(.caption)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity)
        .padding()
        .background(color.opacity(0.1))
        .cornerRadius(8)
    }
}

struct RecentActivityCard: View {
    @ObservedObject var vaultService: KnowledgeVaultService

    var recentNotes: [Note] {
        vaultService.notes
            .sorted { $0.updatedAt > $1.updatedAt }
            .prefix(5)
            .map { $0 }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("最近活动")
                .font(.headline)

            if recentNotes.isEmpty {
                Text("暂无活动")
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .padding()
            } else {
                ForEach(recentNotes) { note in
                    HStack {
                        Image(systemName: "doc.text")
                            .foregroundColor(.blue)

                        VStack(alignment: .leading, spacing: 2) {
                            Text(note.title)
                                .font(.subheadline)
                            Text(note.updatedAt, style: .relative)
                                .font(.caption2)
                                .foregroundColor(.secondary)
                        }

                        Spacer()
                    }
                    .padding(.vertical, 4)
                    Divider()
                }
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding()
        .background(Color.secondary.opacity(0.05))
        .cornerRadius(12)
    }
}

// MARK: - 占位符视图

struct ProjectsView: View {
    var body: some View {
        VStack {
            Image(systemName: "folder")
                .font(.system(size: 60))
                .foregroundColor(.secondary)
            Text("项目管理")
                .font(.title2)
            Text("即将推出")
                .foregroundColor(.secondary)
        }
        .navigationTitle("项目")
    }
}

struct WorkflowsView: View {
    var body: some View {
        VStack {
            Image(systemName: "arrow.triangle.branch")
                .font(.system(size: 60))
                .foregroundColor(.secondary)
            Text("工作流管理")
                .font(.title2)
            Text("即将推出")
                .foregroundColor(.secondary)
        }
        .navigationTitle("工作流")
    }
}

struct DocumentsView: View {
    var body: some View {
        VStack {
            Image(systemName: "doc.text")
                .font(.system(size: 60))
                .foregroundColor(.secondary)
            Text("文档管理")
                .font(.title2)
            Text("即将推出")
                .foregroundColor(.secondary)
        }
        .navigationTitle("文档")
    }
}

struct AssetsView: View {
    var body: some View {
        VStack {
            Image(systemName: "photo.on.rectangle.angled")
                .font(.system(size: 60))
                .foregroundColor(.secondary)
            Text("资产管理")
                .font(.title2)
            Text("即将推出")
                .foregroundColor(.secondary)
        }
        .navigationTitle("资产")
    }
}

struct ChatView: View {
    var body: some View {
        VStack {
            Image(systemName: "message")
                .font(.system(size: 60))
                .foregroundColor(.secondary)
            Text("AI 对话")
                .font(.title2)
            Text("即将推出")
                .foregroundColor(.secondary)
        }
        .navigationTitle("对话")
    }
}

struct SettingsView: View {
    @EnvironmentObject var backendService: BackendService

    var body: some View {
        Form {
            Section("后端服务") {
                HStack {
                    Text("状态")
                    Spacer()
                    Circle()
                        .fill(backendService.isRunning ? Color.green : Color.red)
                        .frame(width: 12, height: 12)
                    Text(backendService.isRunning ? "运行中" : "未启动")
                        .foregroundColor(.secondary)
                }

                TextField("后端地址", text: .constant(backendService.backendURL))
                    .disabled(true)

                HStack {
                    Button(backendService.isRunning ? "停止后端" : "启动后端") {
                        if backendService.isRunning {
                            backendService.stopBackend()
                        } else {
                            backendService.startBackend()
                        }
                    }

                    Button("检查状态") {
                        backendService.checkBackendHealth()
                    }
                }
            }

            Section("关于") {
                HStack {
                    Text("版本")
                    Spacer()
                    Text("1.0.0")
                        .foregroundColor(.secondary)
                }

                HStack {
                    Text("构建号")
                    Spacer()
                    Text("2026.09.19")
                        .foregroundColor(.secondary)
                }
            }
        }
        .formStyle(.grouped)
        .navigationTitle("设置")
    }
}

#Preview {
    MainNavigationView()
        .environmentObject(BackendService.shared)
}
