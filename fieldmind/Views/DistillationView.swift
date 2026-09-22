//
//  DistillationView.swift
//  FieldMind - 知识蒸馏主界面
//
//  完整的第二大脑蒸馏系统界面
//

import SwiftUI
import UniformTypeIdentifiers

// MARK: - 主蒸馏视图

struct DistillationView: View {
    @StateObject private var viewModel = DistillationViewModel()
    @State private var selectedTab = 0

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                // 顶部标签切换
                segmentedControl
                    .padding(.horizontal, 24)
                    .padding(.top, 24)

                // 内容区域
                TabView(selection: $selectedTab) {
                    // 创建新蒸馏
                    CreateDistillationView(viewModel: viewModel)
                        .tag(0)

                    // 作业列表
                    JobListView(viewModel: viewModel)
                        .tag(1)

                    // 统计面板
                    StatsView(viewModel: viewModel)
                        .tag(2)
                }
                .tabViewStyle(.page(indexDisplayMode: .never))
            }
            .background(Color.fmBgSecondary)
            .navigationTitle("知识蒸馏")
            .onAppear {
                viewModel.loadJobs()
                viewModel.loadStats()
            }
        }
    }

    // MARK: - 分段控制器
    private var segmentedControl: some View {
        HStack(spacing: 0) {
            ForEach(["创建蒸馏", "作业列表", "统计数据"].enumerated().map { $0 }, id: \.offset) { index, title in
                Button(action: { withAnimation { selectedTab = index } }) {
                    Text(title)
                        .font(.system(size: 14, weight: selectedTab == index ? .semibold : .regular))
                        .foregroundColor(selectedTab == index ? .white : .fmTextSecondary)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 10)
                        .background(
                            selectedTab == index ? Color.fmPrimary : Color.clear
                        )
                        .cornerRadius(8)
                }
                .buttonStyle(PlainButtonStyle())
            }
        }
        .padding(4)
        .background(Color.white)
        .cornerRadius(10)
        .shadow(color: Color.black.opacity(0.05), radius: 4, x: 0, y: 2)
    }
}

// MARK: - ViewModel

class DistillationViewModel: ObservableObject {
    @Published var jobs: [DistillationJob] = []
    @Published var stats: DistillationStats?
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published var currentJob: DistillationJob?

    private let service = DistillationService.shared
    private var cancellables = Set<AnyCancellable>()

    // MARK: - 加载作业列表
    func loadJobs() {
        isLoading = true
        service.listJobs(limit: 100)
            .sink(
                receiveCompletion: { [weak self] completion in
                    self?.isLoading = false
                    if case .failure(let error) = completion {
                        self?.errorMessage = "加载失败: \(error.localizedDescription)"
                    }
                },
                receiveValue: { [weak self] jobs in
                    self?.jobs = jobs
                }
            )
            .store(in: &cancellables)
    }

    // MARK: - 加载统计数据
    func loadStats() {
        service.getStats()
            .sink(
                receiveCompletion: { _ in },
                receiveValue: { [weak self] stats in
                    self?.stats = stats
                }
            )
            .store(in: &cancellables)
    }

    // MARK: - 上传文件蒸馏
    func uploadFile(url: URL, sourceKind: SourceKind, title: String, author: String) {
        isLoading = true
        errorMessage = nil

        service.uploadAndDistill(fileURL: url, sourceKind: sourceKind, title: title, author: author.isEmpty ? nil : author)
            .sink(
                receiveCompletion: { [weak self] completion in
                    self?.isLoading = false
                    if case .failure(let error) = completion {
                        self?.errorMessage = "上传失败: \(error.localizedDescription)"
                    }
                },
                receiveValue: { [weak self] job in
                    self?.currentJob = job
                    self?.startPolling(jobId: job.id)
                    self?.loadJobs()
                }
            )
            .store(in: &cancellables)
    }

    // MARK: - URL 蒸馏
    func distillURL(url: String, sourceKind: SourceKind, title: String, author: String) {
        isLoading = true
        errorMessage = nil

        service.distillFromURL(url: url, sourceKind: sourceKind, title: title, author: author.isEmpty ? nil : author)
            .sink(
                receiveCompletion: { [weak self] completion in
                    self?.isLoading = false
                    if case .failure(let error) = completion {
                        self?.errorMessage = "创建失败: \(error.localizedDescription)"
                    }
                },
                receiveValue: { [weak self] job in
                    self?.currentJob = job
                    self?.startPolling(jobId: job.id)
                    self?.loadJobs()
                }
            )
            .store(in: &cancellables)
    }

    // MARK: - 轮询作业状态
    private func startPolling(jobId: String) {
        service.pollJobUntilComplete(jobId: jobId, interval: 3.0)
            .sink(
                receiveCompletion: { _ in },
                receiveValue: { [weak self] job in
                    self?.currentJob = job
                    if job.status == .completed || job.status == .failed {
                        self?.loadJobs()
                        self?.loadStats()
                    }
                }
            )
            .store(in: &cancellables)
    }

    // MARK: - 删除作业
    func deleteJob(jobId: String) {
        service.deleteJob(jobId: jobId)
            .sink(
                receiveCompletion: { _ in },
                receiveValue: { [weak self] _ in
                    self?.loadJobs()
                    self?.loadStats()
                }
            )
            .store(in: &cancellables)
    }
}

// MARK: - 创建蒸馏视图

struct CreateDistillationView: View {
    @ObservedObject var viewModel: DistillationViewModel
    @State private var inputMode = 0 // 0: 文件, 1: URL
    @State private var selectedFile: URL?
    @State private var urlString = ""
    @State private var title = ""
    @State private var author = ""
    @State private var sourceKind: SourceKind = .book
    @State private var showFilePicker = false

    var body: some View {
        ScrollView {
            VStack(spacing: 24) {
                // 输入模式选择
                inputModeSelector

                // 文件上传或 URL 输入
                if inputMode == 0 {
                    fileUploadSection
                } else {
                    urlInputSection
                }

                // 元数据输入
                metadataSection

                // 提交按钮
                submitButton

                // 当前作业进度
                if let job = viewModel.currentJob {
                    currentJobProgress(job: job)
                }

                // 错误信息
                if let error = viewModel.errorMessage {
                    errorView(message: error)
                }
            }
            .padding(24)
        }
    }

    // MARK: - 输入模式选择器
    private var inputModeSelector: some View {
        HStack(spacing: 0) {
            ForEach(["文件上传", "URL 链接"].enumerated().map { $0 }, id: \.offset) { index, title in
                Button(action: { withAnimation { inputMode = index } }) {
                    Text(title)
                        .font(.system(size: 14, weight: inputMode == index ? .semibold : .regular))
                        .foregroundColor(inputMode == index ? .white : .fmTextSecondary)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 10)
                        .background(inputMode == index ? Color.fmPrimary : Color.clear)
                        .cornerRadius(8)
                }
                .buttonStyle(PlainButtonStyle())
            }
        }
        .padding(4)
        .background(Color.white)
        .cornerRadius(10)
        .shadow(color: Color.black.opacity(0.05), radius: 4, x: 0, y: 2)
    }

    // MARK: - 文件上传区域
    private var fileUploadSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("选择文件")
                .font(.system(size: 16, weight: .semibold))
                .foregroundColor(.fmTextPrimary)

            Button(action: { showFilePicker = true }) {
                HStack {
                    Image(systemName: "doc.badge.plus")
                        .font(.system(size: 20))
                    VStack(alignment: .leading, spacing: 4) {
                        Text(selectedFile?.lastPathComponent ?? "点击选择文件")
                            .font(.system(size: 14, weight: .medium))
                        Text("支持: PDF, EPUB, DOCX, TXT, Markdown")
                            .font(.system(size: 12))
                            .foregroundColor(.fmTextSecondary)
                    }
                    Spacer()
                }
                .padding(16)
                .background(Color.white)
                .cornerRadius(8)
                .overlay(
                    RoundedRectangle(cornerRadius: 8)
                        .stroke(Color.fmBorder, lineWidth: 1, style: StrokeStyle(lineWidth: 1, dash: [5, 5]))
                )
            }
            .buttonStyle(PlainButtonStyle())
            .fileImporter(
                isPresented: $showFilePicker,
                allowedContentTypes: [.pdf, .epub, .text, .plainText, .data],
                allowsMultipleSelection: false
            ) { result in
                if case .success(let urls) = result, let url = urls.first {
                    selectedFile = url
                    if title.isEmpty {
                        title = url.deletingPathExtension().lastPathComponent
                    }
                }
            }
        }
    }

    // MARK: - URL 输入区域
    private var urlInputSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("输入 URL")
                .font(.system(size: 16, weight: .semibold))
                .foregroundColor(.fmTextPrimary)

            TextField("https://example.com/article", text: $urlString)
                .textFieldStyle(PlainTextFieldStyle())
                .padding(12)
                .background(Color.white)
                .cornerRadius(8)
                .overlay(
                    RoundedRectangle(cornerRadius: 8)
                        .stroke(Color.fmBorder, lineWidth: 1)
                )

            Text("支持网页、Bilibili、YouTube 等")
                .font(.system(size: 12))
                .foregroundColor(.fmTextSecondary)
        }
    }

    // MARK: - 元数据输入
    private var metadataSection: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("元数据")
                .font(.system(size: 16, weight: .semibold))
                .foregroundColor(.fmTextPrimary)

            // 标题
            VStack(alignment: .leading, spacing: 8) {
                Text("标题 *")
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(.fmTextPrimary)
                TextField("输入书籍或文章标题", text: $title)
                    .textFieldStyle(PlainTextFieldStyle())
                    .padding(12)
                    .background(Color.white)
                    .cornerRadius(8)
                    .overlay(
                        RoundedRectangle(cornerRadius: 8)
                            .stroke(Color.fmBorder, lineWidth: 1)
                    )
            }

            // 作者
            VStack(alignment: .leading, spacing: 8) {
                Text("作者")
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(.fmTextPrimary)
                TextField("输入作者姓名（可选）", text: $author)
                    .textFieldStyle(PlainTextFieldStyle())
                    .padding(12)
                    .background(Color.white)
                    .cornerRadius(8)
                    .overlay(
                        RoundedRectangle(cornerRadius: 8)
                            .stroke(Color.fmBorder, lineWidth: 1)
                    )
            }

            // 源类型
            VStack(alignment: .leading, spacing: 8) {
                Text("类型")
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(.fmTextPrimary)

                HStack(spacing: 12) {
                    ForEach([SourceKind.book, .article, .paper, .video, .audio], id: \.self) { kind in
                        Button(action: { sourceKind = kind }) {
                            Text(kind.displayName)
                                .font(.system(size: 13, weight: sourceKind == kind ? .semibold : .regular))
                                .foregroundColor(sourceKind == kind ? .white : .fmTextSecondary)
                                .padding(.horizontal, 16)
                                .padding(.vertical, 8)
                                .background(sourceKind == kind ? Color.fmPrimary : Color.white)
                                .cornerRadius(6)
                                .overlay(
                                    RoundedRectangle(cornerRadius: 6)
                                        .stroke(Color.fmBorder, lineWidth: sourceKind == kind ? 0 : 1)
                                )
                        }
                        .buttonStyle(PlainButtonStyle())
                    }
                }
            }
        }
    }

    // MARK: - 提交按钮
    private var submitButton: some View {
        Button(action: handleSubmit) {
            HStack(spacing: 8) {
                if viewModel.isLoading {
                    ProgressView()
                        .scaleEffect(0.8)
                } else {
                    Image(systemName: "wand.and.stars")
                        .font(.system(size: 16))
                }
                Text(viewModel.isLoading ? "蒸馏中..." : "开始蒸馏")
                    .font(.system(size: 16, weight: .semibold))
            }
            .foregroundColor(.white)
            .frame(maxWidth: .infinity)
            .padding(.vertical, 14)
            .background(canSubmit ? Color.fmPrimary : Color.fmTextTertiary)
            .cornerRadius(10)
            .shadow(color: Color.fmPrimary.opacity(canSubmit ? 0.3 : 0), radius: 8, x: 0, y: 4)
        }
        .buttonStyle(PlainButtonStyle())
        .disabled(!canSubmit)
    }

    // MARK: - 当前作业进度
    private func currentJobProgress(job: DistillationJob) -> some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                Image(systemName: "hourglass")
                    .foregroundColor(.fmPrimary)
                Text("蒸馏进行中")
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundColor(.fmTextPrimary)
                Spacer()
                Text(job.status.displayName)
                    .font(.system(size: 13))
                    .foregroundColor(.fmTextSecondary)
            }

            ProgressView(value: job.status.progress)
                .tint(Color.fmPrimary)

            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text(job.title)
                        .font(.system(size: 14, weight: .medium))
                        .foregroundColor(.fmTextPrimary)
                    if let author = job.author {
                        Text(author)
                            .font(.system(size: 12))
                            .foregroundColor(.fmTextSecondary)
                    }
                }
                Spacer()
                Text("\(Int(job.status.progress * 100))%")
                    .font(.system(size: 20, weight: .bold))
                    .foregroundColor(.fmPrimary)
            }
        }
        .padding(20)
        .background(Color.white)
        .cornerRadius(12)
        .shadow(color: Color.black.opacity(0.05), radius: 4, x: 0, y: 2)
    }

    // MARK: - 错误视图
    private func errorView(message: String) -> some View {
        HStack(spacing: 12) {
            Image(systemName: "exclamationmark.triangle.fill")
                .foregroundColor(.fmError)
            Text(message)
                .font(.system(size: 14))
                .foregroundColor(.fmTextPrimary)
            Spacer()
        }
        .padding(16)
        .background(Color.fmError.opacity(0.1))
        .cornerRadius(8)
    }

    // MARK: - 辅助方法
    private var canSubmit: Bool {
        !title.isEmpty &&
        !viewModel.isLoading &&
        (inputMode == 0 ? selectedFile != nil : !urlString.isEmpty)
    }

    private func handleSubmit() {
        if inputMode == 0, let file = selectedFile {
            viewModel.uploadFile(url: file, sourceKind: sourceKind, title: title, author: author)
        } else {
            viewModel.distillURL(url: urlString, sourceKind: sourceKind, title: title, author: author)
        }
    }
}

// MARK: - 作业列表视图

struct JobListView: View {
    @ObservedObject var viewModel: DistillationViewModel
    @State private var selectedJob: DistillationJob?

    var body: some View {
        ScrollView {
            LazyVStack(spacing: 12) {
                ForEach(viewModel.jobs) { job in
                    JobCard(job: job, onTap: {
                        selectedJob = job
                    }, onDelete: {
                        viewModel.deleteJob(jobId: job.id)
                    })
                }
            }
            .padding(24)
        }
        .sheet(item: $selectedJob) { job in
            JobDetailView(job: job)
        }
    }
}

// MARK: - 作业卡片

struct JobCard: View {
    let job: DistillationJob
    let onTap: () -> Void
    let onDelete: () -> Void

    var body: some View {
        Button(action: onTap) {
            HStack(spacing: 16) {
                // 状态图标
                ZStack {
                    Circle()
                        .fill(statusColor.opacity(0.1))
                        .frame(width: 48, height: 48)
                    Image(systemName: statusIcon)
                        .font(.system(size: 20))
                        .foregroundColor(statusColor)
                }

                // 内容
                VStack(alignment: .leading, spacing: 6) {
                    Text(job.title)
                        .font(.system(size: 15, weight: .semibold))
                        .foregroundColor(.fmTextPrimary)
                        .lineLimit(1)

                    if let author = job.author {
                        Text(author)
                            .font(.system(size: 13))
                            .foregroundColor(.fmTextSecondary)
                    }

                    HStack(spacing: 8) {
                        Text(job.status.displayName)
                            .font(.system(size: 12))
                            .foregroundColor(statusColor)

                        Text("•")
                            .foregroundColor(.fmTextTertiary)

                        Text(job.sourceKind.displayName)
                            .font(.system(size: 12))
                            .foregroundColor(.fmTextTertiary)
                    }
                }

                Spacer()

                // 删除按钮
                Button(action: onDelete) {
                    Image(systemName: "trash")
                        .font(.system(size: 14))
                        .foregroundColor(.fmError)
                        .padding(8)
                }
                .buttonStyle(PlainButtonStyle())
            }
            .padding(16)
            .background(Color.white)
            .cornerRadius(10)
            .shadow(color: Color.black.opacity(0.05), radius: 4, x: 0, y: 2)
        }
        .buttonStyle(PlainButtonStyle())
    }

    private var statusColor: Color {
        switch job.status {
        case .completed: return .fmSuccess
        case .failed: return .fmError
        case .pending: return .fmTextTertiary
        default: return .fmPrimary
        }
    }

    private var statusIcon: String {
        switch job.status {
        case .completed: return "checkmark.circle.fill"
        case .failed: return "xmark.circle.fill"
        case .pending: return "clock.fill"
        default: return "arrow.triangle.2.circlepath"
        }
    }
}

// MARK: - 作业详情视图

struct JobDetailView: View {
    let job: DistillationJob
    @State private var knowledge: [KnowledgeUnit] = []
    @State private var methods: [MethodUnit] = []
    @State private var selectedTab = 0
    @Environment(\.dismiss) var dismiss

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                // 顶部信息
                jobHeader
                    .padding(24)
                    .background(Color.white)

                Divider()

                // 标签切换
                HStack(spacing: 0) {
                    ForEach(["知识单元", "方法单元"].enumerated().map { $0 }, id: \.offset) { index, title in
                        Button(action: { withAnimation { selectedTab = index } }) {
                            VStack(spacing: 8) {
                                Text(title)
                                    .font(.system(size: 14, weight: selectedTab == index ? .semibold : .regular))
                                    .foregroundColor(selectedTab == index ? .fmPrimary : .fmTextSecondary)

                                Rectangle()
                                    .fill(selectedTab == index ? Color.fmPrimary : Color.clear)
                                    .frame(height: 2)
                            }
                            .frame(maxWidth: .infinity)
                        }
                        .buttonStyle(PlainButtonStyle())
                    }
                }
                .padding(.horizontal, 24)
                .background(Color.white)

                // 内容
                TabView(selection: $selectedTab) {
                    KnowledgeListView(knowledge: knowledge)
                        .tag(0)
                    MethodListView(methods: methods)
                        .tag(1)
                }
                .tabViewStyle(.page(indexDisplayMode: .never))
            }
            .navigationTitle("作业详情")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("关闭") { dismiss() }
                }
            }
            .onAppear {
                loadDetails()
            }
        }
    }

    private var jobHeader: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(job.title)
                .font(.system(size: 20, weight: .bold))
                .foregroundColor(.fmTextPrimary)

            if let author = job.author {
                Text("作者: \(author)")
                    .font(.system(size: 14))
                    .foregroundColor(.fmTextSecondary)
            }

            HStack(spacing: 16) {
                Label(job.sourceKind.displayName, systemImage: "doc.text")
                Label(job.status.displayName, systemImage: "circle.fill")
                    .foregroundColor(statusColor)
            }
            .font(.system(size: 13))
            .foregroundColor(.fmTextSecondary)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    private var statusColor: Color {
        switch job.status {
        case .completed: return .fmSuccess
        case .failed: return .fmError
        default: return .fmPrimary
        }
    }

    private func loadDetails() {
        let service = DistillationService.shared

        service.getKnowledge(jobId: job.id)
            .sink(receiveCompletion: { _ in }, receiveValue: { self.knowledge = $0 })
            .store(in: &cancellables)

        service.getMethods(jobId: job.id)
            .sink(receiveCompletion: { _ in }, receiveValue: { self.methods = $0 })
            .store(in: &cancellables)
    }

    @State private var cancellables = Set<AnyCancellable>()
}

// MARK: - 知识列表

struct KnowledgeListView: View {
    let knowledge: [KnowledgeUnit]

    var body: some View {
        ScrollView {
            LazyVStack(spacing: 12) {
                ForEach(knowledge) { item in
                    KnowledgeCard(knowledge: item)
                }
            }
            .padding(24)
        }
        .background(Color.fmBgSecondary)
    }
}

struct KnowledgeCard: View {
    let knowledge: KnowledgeUnit

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text(knowledge.knowledgeType.uppercased())
                    .font(.system(size: 11, weight: .bold))
                    .foregroundColor(.fmPrimary)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(Color.fmPrimary.opacity(0.1))
                    .cornerRadius(4)

                Spacer()

                if let confidence = knowledge.confidence {
                    Text("\(Int(confidence * 100))%")
                        .font(.system(size: 12, weight: .medium))
                        .foregroundColor(.fmTextSecondary)
                }
            }

            Text(knowledge.content)
                .font(.system(size: 14))
                .foregroundColor(.fmTextPrimary)

            if let evidence = knowledge.evidence {
                Text("证据: \(evidence)")
                    .font(.system(size: 12))
                    .foregroundColor(.fmTextSecondary)
                    .padding(8)
                    .background(Color.fmBgSecondary)
                    .cornerRadius(6)
            }
        }
        .padding(16)
        .background(Color.white)
        .cornerRadius(10)
        .shadow(color: Color.black.opacity(0.05), radius: 4, x: 0, y: 2)
    }
}

// MARK: - 方法列表

struct MethodListView: View {
    let methods: [MethodUnit]

    var body: some View {
        ScrollView {
            LazyVStack(spacing: 12) {
                ForEach(methods) { item in
                    MethodCard(method: item)
                }
            }
            .padding(24)
        }
        .background(Color.fmBgSecondary)
    }
}

struct MethodCard: View {
    let method: MethodUnit
    @State private var isExpanded = false

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // 方法名称
            HStack {
                Text(method.methodName)
                    .font(.system(size: 16, weight: .bold))
                    .foregroundColor(.fmTextPrimary)

                Spacer()

                Button(action: { withAnimation { isExpanded.toggle() } }) {
                    Image(systemName: isExpanded ? "chevron.up" : "chevron.down")
                        .font(.system(size: 14))
                        .foregroundColor(.fmTextSecondary)
                }
                .buttonStyle(PlainButtonStyle())
            }

            // Reading (始终显示)
            SectionView(title: "R: 原文引用", content: method.reading, color: .fmPrimary)

            if isExpanded {
                // Interpretation
                SectionView(title: "I: 解释", content: method.interpretation, color: .fmSecondary)

                // Application Past
                if let app1 = method.applicationPast {
                    SectionView(title: "A1: 过去应用", content: app1, color: .fmWarning)
                }

                // Application Future
                if let app2 = method.applicationFuture {
                    SectionView(title: "A2: 未来触发", content: app2, color: .fmInfo)
                }

                // Execution
                if let exec = method.execution {
                    SectionView(title: "E: 执行步骤", content: exec, color: .fmSuccess)
                }

                // Boundary
                if let boundary = method.boundary {
                    SectionView(title: "B: 边界条件", content: boundary, color: .fmError)
                }

                // 测试通过率
                if let tests = method.testCasesPassed {
                    HStack {
                        Image(systemName: "checkmark.seal.fill")
                            .foregroundColor(.fmSuccess)
                        Text("通过 \(tests) 个测试用例")
                            .font(.system(size: 13))
                            .foregroundColor(.fmTextSecondary)
                    }
                }
            }
        }
        .padding(16)
        .background(Color.white)
        .cornerRadius(10)
        .shadow(color: Color.black.opacity(0.05), radius: 4, x: 0, y: 2)
    }
}

struct SectionView: View {
    let title: String
    let content: String
    let color: Color

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(title)
                .font(.system(size: 12, weight: .bold))
                .foregroundColor(color)

            Text(content)
                .font(.system(size: 13))
                .foregroundColor(.fmTextPrimary)
                .padding(10)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(color.opacity(0.05))
                .cornerRadius(6)
        }
    }
}

// MARK: - 统计视图

struct StatsView: View {
    @ObservedObject var viewModel: DistillationViewModel

    var body: some View {
        ScrollView {
            VStack(spacing: 16) {
                if let stats = viewModel.stats {
                    LazyVGrid(
                        columns: Array(repeating: GridItem(.flexible(), spacing: 16), count: 2),
                        spacing: 16
                    ) {
                        StatsCard(title: "总作业", value: "\(stats.totalJobs)", icon: "folder.fill", color: .fmPrimary)
                        StatsCard(title: "已完成", value: "\(stats.completedJobs)", icon: "checkmark.circle.fill", color: .fmSuccess)
                        StatsCard(title: "进行中", value: "\(stats.pendingJobs)", icon: "hourglass", color: .fmWarning)
                        StatsCard(title: "失败", value: "\(stats.failedJobs)", icon: "xmark.circle.fill", color: .fmError)
                        StatsCard(title: "知识单元", value: "\(stats.totalKnowledge)", icon: "lightbulb.fill", color: .fmSecondary)
                        StatsCard(title: "方法单元", value: "\(stats.totalMethods)", icon: "wand.and.stars", color: .fmInfo)
                    }
                }
            }
            .padding(24)
        }
    }
}

struct StatsCard: View {
    let title: String
    let value: String
    let icon: String
    let color: Color

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                ZStack {
                    RoundedRectangle(cornerRadius: 10)
                        .fill(color.opacity(0.1))
                        .frame(width: 40, height: 40)
                    Image(systemName: icon)
                        .font(.system(size: 18))
                        .foregroundColor(color)
                }
                Spacer()
            }

            Text(value)
                .font(.system(size: 28, weight: .bold))
                .foregroundColor(.fmTextPrimary)

            Text(title)
                .font(.system(size: 14))
                .foregroundColor(.fmTextSecondary)
        }
        .padding(20)
        .background(Color.white)
        .cornerRadius(12)
        .shadow(color: Color.black.opacity(0.05), radius: 4, x: 0, y: 2)
    }
}

// MARK: - 扩展

extension SourceKind {
    var displayName: String {
        switch self {
        case .book: return "书籍"
        case .article: return "文章"
        case .paper: return "论文"
        case .video: return "视频"
        case .audio: return "音频"
        }
    }
}

// MARK: - Preview

#Preview {
    DistillationView()
}
