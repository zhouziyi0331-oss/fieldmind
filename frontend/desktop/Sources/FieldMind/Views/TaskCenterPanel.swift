import SwiftUI

/// 任务中心面板 - 显示所有后台任务
struct TaskCenterPanel: View {
    @ObservedObject private var taskManager = TaskManager.shared
    @State private var selectedTab: Tab = .active

    enum Tab: String, CaseIterable {
        case active = "进行中"
        case completed = "已完成"
    }

    var body: some View {
        VStack(spacing: 0) {
            // 标题栏
            HStack {
                Text("任务中心")
                    .font(.system(size: 14, weight: .bold))
                    .foregroundColor(Color.fieldMindText)

                Spacer()

                if selectedTab == .completed && !taskManager.completedTasks.isEmpty {
                    Button("清空") {
                        taskManager.clearCompletedTasks()
                    }
                    .font(.system(size: 11))
                    .foregroundColor(.blue)
                }
            }
            .padding()
            .background(Color.white)
            .overlay(
                Rectangle()
                    .fill(Color.gray.opacity(0.1))
                    .frame(height: 1),
                alignment: .bottom
            )

            // Tab切换
            Picker("", selection: $selectedTab) {
                ForEach(Tab.allCases, id: \.self) { tab in
                    Text(tab.rawValue).tag(tab)
                }
            }
            .pickerStyle(.segmented)
            .padding(.horizontal, 12)
            .padding(.vertical, 8)

            // 任务列表
            ScrollView {
                LazyVStack(spacing: 8) {
                    let tasks = selectedTab == .active ? taskManager.activeTasks : taskManager.completedTasks

                    if tasks.isEmpty {
                        VStack(spacing: 8) {
                            Image(systemName: selectedTab == .active ? "checkmark.circle" : "clock")
                                .font(.system(size: 32))
                                .foregroundColor(.gray.opacity(0.5))
                            Text(selectedTab == .active ? "暂无进行中的任务" : "暂无历史任务")
                                .font(.system(size: 12))
                                .foregroundColor(.gray)
                        }
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 40)
                    } else {
                        ForEach(tasks) { task in
                            TaskRow(task: task)
                        }
                    }
                }
                .padding(12)
            }
        }
        .frame(width: 360, height: 480)
        .background(Color.fieldMindBackground)
        .cornerRadius(8)
        .shadow(color: Color.black.opacity(0.15), radius: 10, x: 0, y: 4)
    }
}

struct TaskRow: View {
    let task: TaskManager.BackgroundTask

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            // 标题和状态
            HStack {
                Text(task.title)
                    .font(.system(size: 12, weight: .medium))
                    .foregroundColor(Color.fieldMindText)
                    .lineLimit(1)

                Spacer()

                HStack(spacing: 4) {
                    Circle()
                        .fill(task.statusColor)
                        .frame(width: 6, height: 6)

                    Text(task.statusText)
                        .font(.system(size: 10))
                        .foregroundColor(task.statusColor)
                }
            }

            // 进度条（仅运行中任务）
            if case .running = task.status {
                ProgressView(value: task.progress, total: 1.0)
                    .tint(Color.fieldMindPrimary)
                    .scaleEffect(x: 1, y: 0.5)

                Text("\(Int(task.progress * 100))%")
                    .font(.system(size: 10))
                    .foregroundColor(.gray)
            }

            // 时间信息
            HStack(spacing: 12) {
                Label(formatTime(task.createdAt), systemImage: "clock")
                    .font(.system(size: 10))
                    .foregroundColor(.gray)

                if let completedAt = task.completedAt {
                    Label(formatDuration(from: task.createdAt, to: completedAt), systemImage: "hourglass")
                        .font(.system(size: 10))
                        .foregroundColor(.gray)
                }
            }
        }
        .padding(12)
        .background(Color.white)
        .cornerRadius(6)
    }

    private func formatTime(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.timeStyle = .short
        return formatter.string(from: date)
    }

    private func formatDuration(from start: Date, to end: Date) -> String {
        let duration = end.timeIntervalSince(start)
        if duration < 60 {
            return "\(Int(duration))秒"
        } else {
            return "\(Int(duration / 60))分钟"
        }
    }
}

// MARK: - 任务中心按钮（侧边栏底部）
struct TaskCenterButton: View {
    @ObservedObject private var taskManager = TaskManager.shared
    @State private var showPanel = false

    var body: some View {
        Button(action: { showPanel.toggle() }) {
            HStack(spacing: 8) {
                Image(systemName: "list.bullet.circle.fill")
                    .font(.system(size: 14))

                Text("任务中心")
                    .font(.system(size: 12, weight: .medium))

                Spacer()

                // Badge显示活动任务数
                if !taskManager.activeTasks.isEmpty {
                    Text("\(taskManager.activeTasks.count)")
                        .font(.system(size: 10, weight: .bold))
                        .foregroundColor(.white)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(Color.red)
                        .cornerRadius(8)
                }
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 10)
            .foregroundColor(.white)
            .contentShape(Rectangle())
        }
        .buttonStyle(PlainButtonStyle())
        .popover(isPresented: $showPanel, arrowEdge: .trailing) {
            TaskCenterPanel()
        }
    }
}
