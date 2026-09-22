import SwiftUI
import Charts

struct QualityMonitorPage: View {
    let projectId: Int
    @StateObject private var viewModel = MonitoringViewModel()
    @State private var selectedTab = "overview"  // overview, metrics, logs
    @State private var autoRefresh = false
    @State private var refreshTimer: Timer?

    var body: some View {
        VStack(spacing: 0) {
            // Header
            headerView

            Divider()

            // Tab selector
            tabSelector

            Divider()

            // Messages
            if let error = viewModel.errorMessage {
                HStack {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .foregroundColor(.red)
                    Text(error)
                        .font(.system(size: 13))
                        .foregroundColor(.fmText)
                    Spacer()
                    Button("关闭") {
                        viewModel.errorMessage = nil
                    }
                    .font(.system(size: 12))
                    .foregroundColor(.fmBlue)
                }
                .padding(12)
                .background(Color.red.opacity(0.1))
                .cornerRadius(8)
                .padding(16)
            }

            // Content
            ScrollView {
                VStack(spacing: 20) {
                    switch selectedTab {
                    case "overview":
                        overviewSection
                    case "metrics":
                        metricsSection
                    case "logs":
                        logsSection
                    default:
                        EmptyView()
                    }
                }
                .padding(24)
            }
        }
        .background(Color.fmBg)
        .task {
            await viewModel.refreshAll()
        }
        .onDisappear {
            stopAutoRefresh()
        }
    }

    private var headerView: some View {
        HStack(spacing: 16) {
            HStack(spacing: 8) {
                Image(systemName: "chart.line.uptrend.xyaxis")
                    .font(.system(size: 20))
                    .foregroundColor(.fmBlue)
                Text("质量监控")
                    .font(.system(size: 18, weight: .semibold))
                    .foregroundColor(.fmText)
            }

            Spacer()

            HStack(spacing: 12) {
                // Auto refresh toggle
                Toggle(isOn: $autoRefresh) {
                    HStack(spacing: 6) {
                        Image(systemName: autoRefresh ? "arrow.clockwise.circle.fill" : "arrow.clockwise.circle")
                        Text("自动刷新")
                            .font(.system(size: 13))
                    }
                }
                .toggleStyle(SwitchToggleStyle(tint: .fmBlue))
                .onChange(of: autoRefresh) { _, newValue in
                    if newValue {
                        startAutoRefresh()
                    } else {
                        stopAutoRefresh()
                    }
                }

                Button(action: {
                    Task {
                        await viewModel.refreshAll()
                    }
                }) {
                    HStack(spacing: 6) {
                        Image(systemName: "arrow.clockwise")
                        Text("刷新")
                    }
                    .font(.system(size: 13, weight: .medium))
                    .foregroundColor(.white)
                    .padding(.horizontal, 16)
                    .padding(.vertical, 8)
                    .background(Color.fmBlue)
                    .cornerRadius(6)
                }
                .buttonStyle(PlainButtonStyle())
            }
        }
        .padding(16)
        .background(Color.white)
    }

    private var tabSelector: some View {
        HStack(spacing: 0) {
            tabButton(id: "overview", label: "系统概览", icon: "chart.bar.fill")
            tabButton(id: "metrics", label: "性能指标", icon: "speedometer")
            tabButton(id: "logs", label: "系统日志", icon: "doc.text.fill")
            Spacer()
        }
        .padding(.horizontal, 16)
        .padding(.top, 12)
        .background(Color.white)
    }

    private func tabButton(id: String, label: String, icon: String) -> some View {
        Button(action: { selectedTab = id }) {
            VStack(spacing: 4) {
                HStack(spacing: 6) {
                    Image(systemName: icon)
                        .font(.system(size: 12))
                    Text(label)
                        .font(.system(size: 13, weight: selectedTab == id ? .medium : .regular))
                }
                .foregroundColor(selectedTab == id ? .fmBlue : .fmText2)
                .padding(.horizontal, 12)
                .padding(.vertical, 8)

                Rectangle()
                    .fill(selectedTab == id ? Color.fmBlue : Color.clear)
                    .frame(height: 2)
            }
        }
        .buttonStyle(PlainButtonStyle())
    }

    private var overviewSection: some View {
        VStack(spacing: 16) {
            // Health status cards
            HStack(spacing: 16) {
                healthCard(
                    title: "系统状态",
                    value: viewModel.systemStatus.uppercased(),
                    color: viewModel.statusColor,
                    icon: "heart.fill"
                )

                if let health = viewModel.health {
                    healthCard(
                        title: "API",
                        value: health.components.api.uppercased(),
                        color: health.components.api == "healthy" ? .green : .red,
                        icon: "network"
                    )

                    healthCard(
                        title: "数据库",
                        value: health.components.database == "healthy" ? "HEALTHY" : "UNHEALTHY",
                        color: health.components.database == "healthy" ? .green : .red,
                        icon: "cylinder.fill"
                    )

                    healthCard(
                        title: "磁盘",
                        value: health.components.disk.uppercased(),
                        color: health.components.disk == "healthy" ? .green : .red,
                        icon: "externaldrive.fill"
                    )
                }
            }

            // Resource usage
            if let metrics = viewModel.metrics {
                VStack(alignment: .leading, spacing: 16) {
                    Text("资源使用情况")
                        .font(.system(size: 16, weight: .semibold))
                        .foregroundColor(.fmText)

                    HStack(spacing: 16) {
                        resourceCard(
                            title: "CPU",
                            value: metrics.system.cpuPercent,
                            unit: "%",
                            color: usageColor(metrics.system.cpuPercent),
                            icon: "cpu"
                        )

                        resourceCard(
                            title: "内存",
                            value: metrics.system.memoryPercent,
                            unit: "%",
                            color: usageColor(metrics.system.memoryPercent),
                            icon: "memorychip"
                        )

                        resourceCard(
                            title: "磁盘",
                            value: metrics.system.diskPercent,
                            unit: "%",
                            color: usageColor(metrics.system.diskPercent),
                            icon: "internaldrive"
                        )
                    }

                    // Detailed metrics
                    metricsDetailView(metrics: metrics)
                }
                .padding(16)
                .background(Color.white)
                .cornerRadius(8)
            }
        }
    }

    private var metricsSection: some View {
        VStack(alignment: .leading, spacing: 16) {
            if let metrics = viewModel.metrics {
                // System metrics
                VStack(alignment: .leading, spacing: 12) {
                    Text("系统资源")
                        .font(.system(size: 16, weight: .semibold))
                        .foregroundColor(.fmText)

                    metricRow(label: "CPU 使用率", value: "\(String(format: "%.2f", metrics.system.cpuPercent))%")
                    metricRow(label: "内存使用率", value: "\(String(format: "%.2f", metrics.system.memoryPercent))%")
                    metricRow(label: "可用内存", value: "\(String(format: "%.2f", metrics.system.memoryAvailableGb)) GB")
                    metricRow(label: "磁盘使用率", value: "\(String(format: "%.2f", metrics.system.diskPercent))%")
                    metricRow(label: "剩余磁盘空间", value: "\(String(format: "%.2f", metrics.system.diskFreeGb)) GB")
                }
                .padding(16)
                .background(Color.white)
                .cornerRadius(8)

                // Process metrics
                VStack(alignment: .leading, spacing: 12) {
                    Text("进程信息")
                        .font(.system(size: 16, weight: .semibold))
                        .foregroundColor(.fmText)

                    metricRow(label: "进程 ID", value: "\(metrics.process.pid)")
                    metricRow(label: "进程内存", value: "\(String(format: "%.2f", metrics.process.memoryMb)) MB")
                    metricRow(label: "线程数", value: "\(metrics.process.numThreads)")
                }
                .padding(16)
                .background(Color.white)
                .cornerRadius(8)

                // Timestamp
                Text("更新时间: \(formatTimestamp(metrics.timestamp))")
                    .font(.system(size: 12))
                    .foregroundColor(.fmText2)
                    .frame(maxWidth: .infinity, alignment: .center)
            } else {
                Text("加载中...")
                    .font(.system(size: 14))
                    .foregroundColor(.fmText2)
                    .frame(maxWidth: .infinity, alignment: .center)
                    .padding(40)
            }
        }
    }

    private var logsSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("系统日志")
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundColor(.fmText)

                Spacer()

                Text("\(viewModel.logs.count) 行")
                    .font(.system(size: 12))
                    .foregroundColor(.fmText2)
            }

            if viewModel.isLoadingLogs {
                ProgressView()
                    .frame(maxWidth: .infinity, alignment: .center)
                    .padding(40)
            } else if viewModel.logs.isEmpty {
                Text("暂无日志")
                    .font(.system(size: 14))
                    .foregroundColor(.fmText2)
                    .frame(maxWidth: .infinity, alignment: .center)
                    .padding(40)
            } else {
                ScrollView {
                    VStack(alignment: .leading, spacing: 4) {
                        ForEach(Array(viewModel.logs.enumerated()), id: \.offset) { index, line in
                            HStack(alignment: .top, spacing: 8) {
                                Text("\(index + 1)")
                                    .font(.system(size: 11, design: .monospaced))
                                    .foregroundColor(.fmText3)
                                    .frame(width: 40, alignment: .trailing)

                                Text(line)
                                    .font(.system(size: 11, design: .monospaced))
                                    .foregroundColor(.fmText)
                                    .textSelection(.enabled)
                            }
                            .padding(.vertical, 2)
                        }
                    }
                    .padding(12)
                }
                .frame(height: 400)
                .background(Color.black.opacity(0.05))
                .cornerRadius(8)
            }
        }
        .padding(16)
        .background(Color.white)
        .cornerRadius(8)
    }

    private func healthCard(title: String, value: String, color: Color, icon: String) -> some View {
        VStack(spacing: 12) {
            Image(systemName: icon)
                .font(.system(size: 24))
                .foregroundColor(color)

            VStack(spacing: 4) {
                Text(value)
                    .font(.system(size: 16, weight: .bold))
                    .foregroundColor(color)

                Text(title)
                    .font(.system(size: 12))
                    .foregroundColor(.fmText2)
            }
        }
        .frame(maxWidth: .infinity)
        .padding(16)
        .background(Color.white)
        .cornerRadius(8)
    }

    private func resourceCard(title: String, value: Double, unit: String, color: Color, icon: String) -> some View {
        VStack(spacing: 12) {
            HStack(spacing: 6) {
                Image(systemName: icon)
                    .font(.system(size: 14))
                    .foregroundColor(color)
                Text(title)
                    .font(.system(size: 13, weight: .medium))
                    .foregroundColor(.fmText)
            }

            HStack(alignment: .firstTextBaseline, spacing: 2) {
                Text(String(format: "%.1f", value))
                    .font(.system(size: 24, weight: .bold))
                    .foregroundColor(color)
                Text(unit)
                    .font(.system(size: 12))
                    .foregroundColor(.fmText2)
            }

            // Progress bar
            GeometryReader { geometry in
                ZStack(alignment: .leading) {
                    Rectangle()
                        .fill(Color.gray.opacity(0.2))
                        .frame(height: 4)

                    Rectangle()
                        .fill(color)
                        .frame(width: geometry.size.width * (value / 100.0), height: 4)
                }
                .cornerRadius(2)
            }
            .frame(height: 4)
        }
        .frame(maxWidth: .infinity)
        .padding(16)
        .background(Color.white)
        .cornerRadius(8)
    }

    private func metricsDetailView(metrics: MonitoringService.MetricsResponse) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("详细信息")
                .font(.system(size: 14, weight: .semibold))
                .foregroundColor(.fmText)

            Grid(alignment: .leading, horizontalSpacing: 16, verticalSpacing: 8) {
                GridRow {
                    Text("可用内存:")
                        .font(.system(size: 12))
                        .foregroundColor(.fmText2)
                    Text("\(String(format: "%.2f", metrics.system.memoryAvailableGb)) GB")
                        .font(.system(size: 12, weight: .medium))
                        .foregroundColor(.fmText)
                }

                GridRow {
                    Text("剩余磁盘:")
                        .font(.system(size: 12))
                        .foregroundColor(.fmText2)
                    Text("\(String(format: "%.2f", metrics.system.diskFreeGb)) GB")
                        .font(.system(size: 12, weight: .medium))
                        .foregroundColor(.fmText)
                }

                GridRow {
                    Text("进程内存:")
                        .font(.system(size: 12))
                        .foregroundColor(.fmText2)
                    Text("\(String(format: "%.2f", metrics.process.memoryMb)) MB")
                        .font(.system(size: 12, weight: .medium))
                        .foregroundColor(.fmText)
                }

                GridRow {
                    Text("进程线程:")
                        .font(.system(size: 12))
                        .foregroundColor(.fmText2)
                    Text("\(metrics.process.numThreads)")
                        .font(.system(size: 12, weight: .medium))
                        .foregroundColor(.fmText)
                }
            }
        }
    }

    private func metricRow(label: String, value: String) -> some View {
        HStack {
            Text(label)
                .font(.system(size: 13))
                .foregroundColor(.fmText2)
            Spacer()
            Text(value)
                .font(.system(size: 13, weight: .medium))
                .foregroundColor(.fmText)
        }
        .padding(.vertical, 4)
    }

    private func usageColor(_ value: Double) -> Color {
        if value < 60 {
            return .green
        } else if value < 80 {
            return .orange
        } else {
            return .red
        }
    }

    private func formatTimestamp(_ timestamp: String) -> String {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]

        if let date = formatter.date(from: timestamp) {
            let displayFormatter = DateFormatter()
            displayFormatter.dateFormat = "yyyy-MM-dd HH:mm:ss"
            return displayFormatter.string(from: date)
        }
        return timestamp
    }

    private func startAutoRefresh() {
        refreshTimer = Timer.scheduledTimer(withTimeInterval: 5.0, repeats: true) { _ in
            Task {
                await viewModel.refreshAll()
            }
        }
    }

    private func stopAutoRefresh() {
        refreshTimer?.invalidate()
        refreshTimer = nil
    }
}
