import SwiftUI
import UniformTypeIdentifiers

// MARK: - Photos Page (使用真实API + EXIF支持)
struct PhotosPage: View {
    let projectId: Int
    @EnvironmentObject var appState: AppState
    @StateObject private var viewModel = PhotoViewModel()
    @State private var selectedPhotos: Set<String> = []
    @State private var viewMode: ViewMode = .grid
    @State private var showUploadSheet = false
    @State private var selectedPhoto: PhotoService.PhotoResponse?

    enum ViewMode {
        case grid, masonry
    }

    let dateFilters = ["all", "today", "week", "month", "year"]
    let dateFilterLabels = ["全部", "今天", "本周", "本月", "今年"]
    let sortOptions = ["最新优先", "最旧优先", "名称 A-Z", "大小降序"]

    var body: some View {
        VStack(spacing: 0) {
            // Toolbar
            ScrollView(.horizontal, showsIndicators: true) {
                toolbarView
                    .frame(minWidth: 780, alignment: .leading)
            }

            // Main content
            if viewModel.isLoadingPhotos {
                loadingView
            } else if let error = viewModel.errorMessage {
                errorView(error)
            } else if viewModel.photos.isEmpty {
                emptyView
            } else {
                photoGridView
            }

            // Batch action bar
            if !selectedPhotos.isEmpty {
                batchActionBar
            }
        }
        .sheet(item: $selectedPhoto) { photo in
            photoDetailSheet(photo: photo)
        }
        .task {
            await viewModel.loadAllData(projectId: projectId)
        }
        .onChange(of: projectId) { _, newProjectId in
            selectedPhotos.removeAll()
            Task {
                await viewModel.loadAllData(projectId: newProjectId)
            }
        }
        .onChange(of: appState.lastDocumentUpdate) { oldValue, newValue in
            Task {
                await viewModel.loadAllData(projectId: projectId)
            }
        }
    }

    // MARK: - Toolbar
    private var toolbarView: some View {
        HStack(spacing: 12) {
            // Search
            HStack(spacing: 6) {
                Image(systemName: "magnifyingglass")
                    .font(.system(size: 11))
                    .foregroundColor(Color(hex: "94A3B8"))
                TextField("搜索照片...", text: $viewModel.searchText)
                    .textFieldStyle(PlainTextFieldStyle())
                    .font(.system(size: 13))
                    .onChange(of: viewModel.searchText) { oldValue, newValue in
                        Task {
                            try? await Task.sleep(nanoseconds: 500_000_000)
                            await viewModel.loadPhotos(projectId: projectId)
                        }
                    }
            }
            .padding(.horizontal, 10)
            .padding(.vertical, 6)
            .background(Color(hex: "F8FAFC"))
            .cornerRadius(6)
            .frame(width: 240)

            // Date filter
            Menu {
                ForEach(Array(zip(dateFilters, dateFilterLabels)), id: \.0) { filter, label in
                    Button(action: {
                        viewModel.selectedDateFilter = filter
                        Task {
                            await viewModel.loadPhotos(projectId: projectId)
                        }
                    }) {
                        HStack {
                            Text(label)
                            if viewModel.selectedDateFilter == filter {
                                Image(systemName: "checkmark")
                            }
                        }
                    }
                }
            } label: {
                HStack(spacing: 4) {
                    Image(systemName: "calendar")
                        .font(.system(size: 11))
                    Text(dateFilterLabels[dateFilters.firstIndex(of: viewModel.selectedDateFilter) ?? 0])
                        .font(.system(size: 12))
                }
                .foregroundColor(Color(hex: "475569"))
                .padding(.horizontal, 10)
                .padding(.vertical, 6)
                .background(Color(hex: "F8FAFC"))
                .cornerRadius(6)
            }
            .buttonStyle(PlainButtonStyle())

            // Sort
            Menu {
                ForEach(sortOptions, id: \.self) { option in
                    Button(action: {
                        viewModel.selectedSort = option
                        Task {
                            await viewModel.loadPhotos(projectId: projectId)
                        }
                    }) {
                        HStack {
                            Text(option)
                            if viewModel.selectedSort == option {
                                Image(systemName: "checkmark")
                            }
                        }
                    }
                }
            } label: {
                HStack(spacing: 4) {
                    Image(systemName: "arrow.up.arrow.down")
                        .font(.system(size: 11))
                    Text(viewModel.selectedSort)
                        .font(.system(size: 12))
                }
                .foregroundColor(Color(hex: "475569"))
                .padding(.horizontal, 10)
                .padding(.vertical, 6)
                .background(Color(hex: "F8FAFC"))
                .cornerRadius(6)
            }
            .buttonStyle(PlainButtonStyle())

            Spacer()

            // Stats
            if let stats = viewModel.stats {
                HStack(spacing: 12) {
                    StatBadge_Photo(label: "总计", value: "\(stats.totalPhotos)", color: "3B82F6")
                    StatBadge_Photo(label: "容量", value: viewModel.formatFileSize(Int64(stats.totalSize)), color: "10B981")
                }
            }

            // View mode toggle
            HStack(spacing: 0) {
                Button(action: { viewMode = .grid }) {
                    Image(systemName: "square.grid.2x2")
                        .font(.system(size: 12))
                        .foregroundColor(viewMode == .grid ? Color(hex: "3B82F6") : Color(hex: "94A3B8"))
                        .frame(width: 32, height: 28)
                        .background(viewMode == .grid ? Color(hex: "EFF6FF") : Color.clear)
                }
                .buttonStyle(PlainButtonStyle())

                Button(action: { viewMode = .masonry }) {
                    Image(systemName: "square.grid.3x1.below.line.grid.1x2")
                        .font(.system(size: 12))
                        .foregroundColor(viewMode == .masonry ? Color(hex: "3B82F6") : Color(hex: "94A3B8"))
                        .frame(width: 32, height: 28)
                        .background(viewMode == .masonry ? Color(hex: "EFF6FF") : Color.clear)
                }
                .buttonStyle(PlainButtonStyle())
            }
            .overlay(
                RoundedRectangle(cornerRadius: 6)
                    .stroke(Color(hex: "E2E8F0"), lineWidth: 1)
            )

            // Upload button
            Button(action: openPhotoPicker) {
                HStack(spacing: 6) {
                    Image(systemName: "plus")
                        .font(.system(size: 12, weight: .medium))
                    Text("上传照片")
                        .font(.system(size: 13, weight: .medium))
                }
                .foregroundColor(.white)
                .padding(.horizontal, 16)
                .padding(.vertical, 8)
                .background(Color(hex: "3B82F6"))
                .cornerRadius(8)
            }
            .buttonStyle(PlainButtonStyle())
        }
        .padding(16)
        .background(Color(hex: "F8FAFC"))
    }

    // MARK: - Loading/Error/Empty Views
    private var loadingView: some View {
        VStack(spacing: 16) {
            ProgressView()
                .scaleEffect(1.5)
            Text("加载照片中...")
                .font(.system(size: 14))
                .foregroundColor(Color(hex: "64748B"))
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    private func errorView(_ message: String) -> some View {
        VStack(spacing: 16) {
            Image(systemName: "exclamationmark.triangle")
                .font(.system(size: 48))
                .foregroundColor(Color(hex: "EF4444"))
            Text(message)
                .font(.system(size: 14))
                .foregroundColor(Color(hex: "64748B"))
            Button(action: {
                Task {
                    await viewModel.loadAllData(projectId: projectId)
                }
            }) {
                Text("重试")
                    .font(.system(size: 13, weight: .medium))
                    .foregroundColor(.white)
                    .padding(.horizontal, 20)
                    .padding(.vertical, 8)
                    .background(Color(hex: "3B82F6"))
                    .cornerRadius(8)
            }
            .buttonStyle(PlainButtonStyle())
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    private var emptyView: some View {
        VStack(spacing: 20) {
            Image(systemName: "photo")
                .font(.system(size: 64))
                .foregroundColor(Color(hex: "CBD5E1"))
            VStack(spacing: 8) {
                Text("暂无照片")
                    .font(.system(size: 16, weight: .medium))
                    .foregroundColor(Color(hex: "1E293B"))
                Text("点击\"上传照片\"按钮开始上传")
                    .font(.system(size: 14))
                    .foregroundColor(Color(hex: "64748B"))
            }
            Button(action: openPhotoPicker) {
                HStack(spacing: 6) {
                    Image(systemName: "plus")
                    Text("上传照片")
                }
                .foregroundColor(.white)
                .padding(.horizontal, 20)
                .padding(.vertical, 10)
                .background(Color(hex: "3B82F6"))
                .cornerRadius(8)
            }
            .buttonStyle(PlainButtonStyle())
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    // MARK: - Photo Grid
    private var photoGridView: some View {
        GeometryReader { geometry in
            ScrollView {
                let columns = viewModel.calculateColumns(for: geometry.size.width - 32)
                let gridItems = Array(repeating: GridItem(.flexible(), spacing: 12), count: columns)

                LazyVGrid(columns: gridItems, spacing: 12) {
                    ForEach(viewModel.photos) { photo in
                        PhotoCard(
                            photo: photo,
                            isSelected: selectedPhotos.contains(photo.id),
                            onTap: {
                                selectedPhoto = photo
                            },
                            onToggleSelect: {
                                if selectedPhotos.contains(photo.id) {
                                    selectedPhotos.remove(photo.id)
                                } else {
                                    selectedPhotos.insert(photo.id)
                                }
                            }
                        )
                    }
                }
                .padding(16)
            }
        }
    }

    // MARK: - Batch Action Bar
    private var batchActionBar: some View {
        HStack {
            Text("已选择 \(selectedPhotos.count) 张")
                .font(.system(size: 14, weight: .medium))
                .foregroundColor(Color(hex: "1E293B"))
            Spacer()
            Button(action: {
                selectedPhotos.removeAll()
            }) {
                Text("取消选择")
                    .font(.system(size: 13))
                    .foregroundColor(Color(hex: "64748B"))
            }
            .buttonStyle(PlainButtonStyle())

            Button(action: {
                Task {
                    let ids = Array(selectedPhotos)
                    let success = await viewModel.batchDeletePhotos(photoIds: ids, projectId: projectId)
                    if success {
                        selectedPhotos.removeAll()
                    }
                }
            }) {
                HStack(spacing: 6) {
                    Image(systemName: "trash")
                        .font(.system(size: 12))
                    Text("删除")
                        .font(.system(size: 13, weight: .medium))
                }
                .foregroundColor(.white)
                .padding(.horizontal, 16)
                .padding(.vertical, 8)
                .background(Color(hex: "EF4444"))
                .cornerRadius(8)
            }
            .buttonStyle(PlainButtonStyle())
        }
        .padding(16)
        .background(Color(hex: "FEF3C7"))
        .overlay(
            Rectangle()
                .fill(Color(hex: "F59E0B"))
                .frame(height: 2),
            alignment: .top
        )
    }

    // MARK: - Photo Detail Sheet
    private func photoDetailSheet(photo: PhotoService.PhotoResponse) -> some View {
        PhotoDetailView_NEW(
            photo: photo,
            onDelete: {
                Task {
                    let success = await viewModel.deletePhoto(photoId: photo.id, projectId: projectId)
                    if success {
                        selectedPhoto = nil
                    }
                }
            },
            onClose: {
                selectedPhoto = nil
            }
        )
    }

    private func openPhotoPicker() {
        let panel = NSOpenPanel()
        panel.allowsMultipleSelection = true
        panel.canChooseDirectories = true
        panel.allowedContentTypes = [
            .image,
            UTType(filenameExtension: "jpg"),
            UTType(filenameExtension: "jpeg"),
            UTType(filenameExtension: "png"),
            UTType(filenameExtension: "heic"),
            UTType(filenameExtension: "webp"),
            UTType(filenameExtension: "tiff")
        ].compactMap { $0 }

        if panel.runModal() == .OK {
            let files = UploadFileSelectionHelper.collectUploadableFiles(from: panel.urls).filter {
                ["jpg", "jpeg", "png", "heic", "heif", "webp", "tif", "tiff", "gif", "bmp"].contains($0.pathExtension.lowercased())
            }
            guard !files.isEmpty else {
                appState.showToast(message: "没有找到可上传的照片", type: .warning)
                return
            }
            Task {
                let ok = await viewModel.uploadPhotos(projectId: projectId, fileURLs: files)
                if ok {
                    appState.notifyDocumentUpdated()
                    appState.showToast(message: "照片已上传并进入文件管理", type: .success)
                }
            }
        }
    }
}

// MARK: - Supporting Components

struct PhotoCard: View {
    let photo: PhotoService.PhotoResponse
    let isSelected: Bool
    let onTap: () -> Void
    let onToggleSelect: () -> Void

    var body: some View {
        VStack(spacing: 0) {
            // Image placeholder (实际应该加载真实图片)
            ZStack {
                Rectangle()
                    .fill(Color(hex: "F1F5F9"))
                    .aspectRatio(CGFloat(photo.width) / CGFloat(photo.height), contentMode: .fit)

                // Placeholder icon
                Image(systemName: "photo")
                    .font(.system(size: 32))
                    .foregroundColor(Color(hex: "CBD5E1"))

                // Selection overlay
                if isSelected {
                    Rectangle()
                        .fill(Color(hex: "3B82F6").opacity(0.3))
                }

                // Selection checkbox
                VStack {
                    HStack {
                        Spacer()
                        Button(action: onToggleSelect) {
                            Image(systemName: isSelected ? "checkmark.circle.fill" : "circle")
                                .font(.system(size: 20))
                                .foregroundColor(isSelected ? Color(hex: "3B82F6") : .white)
                                .shadow(radius: 2)
                        }
                        .buttonStyle(PlainButtonStyle())
                        .padding(8)
                    }
                    Spacer()
                }
            }
            .cornerRadius(8)

            // Info
            VStack(alignment: .leading, spacing: 4) {
                Text(photo.filename)
                    .font(.system(size: 12, weight: .medium))
                    .foregroundColor(Color(hex: "1E293B"))
                    .lineLimit(1)

                HStack(spacing: 8) {
                    Text("\(photo.width) × \(photo.height)")
                        .font(.system(size: 11))
                        .foregroundColor(Color(hex: "64748B"))

                    if let device = photo.device {
                        Text("·")
                            .foregroundColor(Color(hex: "CBD5E1"))
                        Text(device)
                            .font(.system(size: 11))
                            .foregroundColor(Color(hex: "64748B"))
                            .lineLimit(1)
                    }
                }

                if let location = photo.location {
                    HStack(spacing: 4) {
                        Image(systemName: "location.fill")
                            .font(.system(size: 9))
                        Text(location)
                            .font(.system(size: 11))
                    }
                    .foregroundColor(Color(hex: "8B5CF6"))
                }
            }
            .padding(8)
        }
        .background(Color.white)
        .cornerRadius(12)
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(isSelected ? Color(hex: "3B82F6") : Color(hex: "E2E8F0"), lineWidth: isSelected ? 2 : 1)
        )
        .onTapGesture(count: 2) {
            onTap()
        }
    }
}

struct StatBadge_Photo: View {
    let label: String
    let value: String
    let color: String

    var body: some View {
        HStack(spacing: 6) {
            Text(label)
                .font(.system(size: 12))
                .foregroundColor(Color(hex: "64748B"))
            Text(value)
                .font(.system(size: 14, weight: .semibold))
                .foregroundColor(Color(hex: color))
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 6)
        .background(Color.white)
        .cornerRadius(6)
        .overlay(
            RoundedRectangle(cornerRadius: 6)
                .stroke(Color(hex: "E2E8F0"), lineWidth: 1)
        )
    }
}

struct PhotoDetailView_NEW: View {
    let photo: PhotoService.PhotoResponse
    let onDelete: () -> Void
    let onClose: () -> Void

    var body: some View {
        VStack(spacing: 0) {
            // Header
            HStack {
                Text("照片详情")
                    .font(.system(size: 18, weight: .semibold))
                    .foregroundColor(Color(hex: "1E293B"))
                Spacer()
                Button(action: onClose) {
                    Image(systemName: "xmark")
                        .font(.system(size: 14))
                        .foregroundColor(Color(hex: "64748B"))
                }
                .buttonStyle(PlainButtonStyle())
            }
            .padding(20)

            Divider()

            // Content
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    // Image preview
                    Rectangle()
                        .fill(Color(hex: "F1F5F9"))
                        .aspectRatio(CGFloat(photo.width) / CGFloat(photo.height), contentMode: .fit)
                        .overlay(
                            Image(systemName: "photo")
                                .font(.system(size: 64))
                                .foregroundColor(Color(hex: "CBD5E1"))
                        )
                        .cornerRadius(12)

                    // Filename
                    DetailRow_Photo(label: "文件名", value: photo.filename)

                    // Dimensions
                    DetailRow_Photo(label: "尺寸", value: "\(photo.width) × \(photo.height)")

                    // Format
                    DetailRow_Photo(label: "格式", value: photo.format)

                    // File size
                    DetailRow_Photo(label: "大小", value: ByteCountFormatter.string(fromByteCount: photo.fileSize, countStyle: .file))

                    // Taken at
                    if let takenAt = photo.takenAt {
                        DetailRow_Photo(label: "拍摄时间", value: formatDate(takenAt))
                    }

                    // Location
                    if let location = photo.location {
                        DetailRow_Photo(label: "位置", value: location)
                    }

                    // Device
                    if let device = photo.device {
                        DetailRow_Photo(label: "设备", value: device)
                    }

                    // Tags
                    if !photo.tags.isEmpty {
                        VStack(alignment: .leading, spacing: 8) {
                            Text("标签")
                                .font(.system(size: 12, weight: .medium))
                                .foregroundColor(Color(hex: "64748B"))
                            HStack(spacing: 8) {
                                ForEach(photo.tags, id: \.self) { tag in
                                    Text(tag)
                                        .font(.system(size: 12))
                                        .foregroundColor(Color(hex: "64748B"))
                                        .padding(.horizontal, 10)
                                        .padding(.vertical, 6)
                                        .background(Color(hex: "F1F5F9"))
                                        .cornerRadius(6)
                                }
                            }
                        }
                    }

                    // Upload time
                    DetailRow_Photo(label: "上传时间", value: formatDate(photo.uploadedAt))
                }
                .padding(20)
            }

            Divider()

            // Footer
            HStack(spacing: 12) {
                Button(action: onDelete) {
                    HStack(spacing: 6) {
                        Image(systemName: "trash")
                            .font(.system(size: 12))
                        Text("删除")
                            .font(.system(size: 14))
                    }
                    .foregroundColor(Color(hex: "EF4444"))
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 10)
                    .background(Color(hex: "FEF2F2"))
                    .cornerRadius(8)
                }
                .buttonStyle(PlainButtonStyle())

                Button(action: onClose) {
                    Text("关闭")
                        .font(.system(size: 14, weight: .medium))
                        .foregroundColor(.white)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 10)
                        .background(Color(hex: "3B82F6"))
                        .cornerRadius(8)
                }
                .buttonStyle(PlainButtonStyle())
            }
            .padding(20)
        }
        .frame(width: 600, height: 700)
    }

    private func formatDate(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd HH:mm:ss"
        return formatter.string(from: date)
    }
}

struct DetailRow_Photo: View {
    let label: String
    let value: String

    var body: some View {
        HStack {
            Text(label)
                .font(.system(size: 13, weight: .medium))
                .foregroundColor(Color(hex: "64748B"))
                .frame(width: 80, alignment: .leading)
            Text(value)
                .font(.system(size: 14))
                .foregroundColor(Color(hex: "1E293B"))
            Spacer()
        }
    }
}
