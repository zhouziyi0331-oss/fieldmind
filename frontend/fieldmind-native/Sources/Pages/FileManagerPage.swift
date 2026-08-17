import SwiftUI

/// FileManagerPage - 文件管理页面（带文件夹架构）
struct FileManagerPage: View {
    let projectId: Int

    @StateObject private var viewModel = FileManagerViewModel()
    @State private var showCreateFolderSheet = false
    @State private var showMoveFileSheet = false
    @State private var newFolderName = ""
    @State private var selectedFileToMove: FileManagerService.FileNodeResponse?
    @State private var moveTargetPath = ""
    @State private var showDeleteAlert = false
    @State private var itemToDelete: FileManagerService.FileNodeResponse?

    var body: some View {
        VStack(spacing: 0) {
            // 顶部工具栏
            toolbarView

            Divider()

            // 面包屑导航
            breadcrumbView

            Divider()

            // 主内容区域
            if viewModel.isLoadingTree {
                loadingView
            } else if let error = viewModel.errorMessage {
                errorView(error)
            } else {
                contentView
            }
        }
        .alert("删除确认", isPresented: $showDeleteAlert) {
            Button("取消", role: .cancel) {}
            Button("删除", role: .destructive) {
                if let item = itemToDelete {
                    Task {
                        if item.isFolder {
                            _ = await viewModel.deleteFolder(projectId: projectId, folderPath: item.path)
                        }
                    }
                }
            }
        } message: {
            Text(itemToDelete?.isFolder == true ? "确定要删除此文件夹及其所有内容吗？" : "确定要删除此文件吗？")
        }
        .sheet(isPresented: $showCreateFolderSheet) {
            CreateFolderSheet(
                isPresented: $showCreateFolderSheet,
                folderName: $newFolderName,
                currentPath: viewModel.currentPath,
                onCreate: {
                    Task {
                        let fullPath = viewModel.currentPath.isEmpty ? newFolderName : "\(viewModel.currentPath)/\(newFolderName)"
                        let success = await viewModel.createFolder(projectId: projectId, folderPath: fullPath)
                        if success {
                            showCreateFolderSheet = false
                            newFolderName = ""
                        }
                    }
                }
            )
        }
        .sheet(isPresented: $showMoveFileSheet) {
            if let file = selectedFileToMove {
                MoveFileSheet(
                    isPresented: $showMoveFileSheet,
                    file: file,
                    targetPath: $moveTargetPath,
                    onMove: {
                        Task {
                            let success = await viewModel.moveFile(fileId: file.id, targetPath: moveTargetPath, projectId: projectId)
                            if success {
                                showMoveFileSheet = false
                                moveTargetPath = ""
                                selectedFileToMove = nil
                            }
                        }
                    }
                )
            }
        }
        .task {
            await viewModel.loadFileTree(projectId: projectId)
        }
    }

    // MARK: - Toolbar

    private var toolbarView: some View {
        HStack(spacing: 16) {
            // 搜索框
            HStack(spacing: 8) {
                Image(systemName: "magnifyingglass")
                    .foregroundColor(Color(hex: "64748B"))
                TextField("搜索文件...", text: $viewModel.searchText)
                    .textFieldStyle(PlainTextFieldStyle())
                if !viewModel.searchText.isEmpty {
                    Button(action: { viewModel.searchText = "" }) {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundColor(Color(hex: "94A3B8"))
                    }
                }
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
            .background(Color(hex: "F1F5F9"))
            .cornerRadius(8)
            .frame(maxWidth: 400)

            Spacer()

            // 视图模式切换
            HStack(spacing: 4) {
                viewModeButton(mode: .tree, icon: "list.bullet.indent")
                viewModeButton(mode: .list, icon: "list.bullet")
                viewModeButton(mode: .grid, icon: "square.grid.2x2")
            }
            .padding(4)
            .background(Color(hex: "F1F5F9"))
            .cornerRadius(8)

            // 排序
            Menu {
                Button(action: { viewModel.sortBy = .name }) {
                    Label("名称", systemImage: viewModel.sortBy == .name ? "checkmark" : "")
                }
                Button(action: { viewModel.sortBy = .date }) {
                    Label("修改日期", systemImage: viewModel.sortBy == .date ? "checkmark" : "")
                }
                Button(action: { viewModel.sortBy = .size }) {
                    Label("大小", systemImage: viewModel.sortBy == .size ? "checkmark" : "")
                }
                Button(action: { viewModel.sortBy = .type }) {
                    Label("类型", systemImage: viewModel.sortBy == .type ? "checkmark" : "")
                }
            } label: {
                HStack(spacing: 6) {
                    Image(systemName: "arrow.up.arrow.down")
                    Text("排序")
                }
                .padding(.horizontal, 12)
                .padding(.vertical, 8)
                .background(Color(hex: "F1F5F9"))
                .cornerRadius(8)
            }

            // 新建文件夹
            Button(action: { showCreateFolderSheet = true }) {
                HStack(spacing: 6) {
                    Image(systemName: "folder.badge.plus")
                    Text("新建文件夹")
                }
                .padding(.horizontal, 12)
                .padding(.vertical, 8)
                .background(Color(hex: "3B82F6"))
                .foregroundColor(.white)
                .cornerRadius(8)
            }
        }
        .padding(16)
    }

    private func viewModeButton(mode: FileManagerViewModel.ViewMode, icon: String) -> some View {
        Button(action: { viewModel.viewMode = mode }) {
            Image(systemName: icon)
                .foregroundColor(viewModel.viewMode == mode ? Color(hex: "3B82F6") : Color(hex: "64748B"))
                .padding(8)
                .background(viewModel.viewMode == mode ? Color(hex: "DBEAFE") : Color.clear)
                .cornerRadius(6)
        }
    }

    // MARK: - Breadcrumb

    private var breadcrumbView: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 8) {
                ForEach(Array(viewModel.getBreadcrumbs().enumerated()), id: \.offset) { index, crumb in
                    Button(action: {
                        if index == 0 {
                            viewModel.currentPath = ""
                            if let root = viewModel.fileTree?.root {
                                viewModel.currentItems = root.children
                            }
                        } else {
                            let parts = viewModel.getBreadcrumbs().dropFirst().prefix(index)
                            let newPath = parts.joined(separator: "/")
                            Task {
                                await viewModel.loadFolderContents(projectId: projectId, folderPath: newPath)
                            }
                        }
                    }) {
                        HStack(spacing: 4) {
                            if index == 0 {
                                Image(systemName: "house.fill")
                            }
                            Text(crumb)
                                .fontWeight(index == viewModel.getBreadcrumbs().count - 1 ? .semibold : .regular)
                        }
                        .foregroundColor(index == viewModel.getBreadcrumbs().count - 1 ? Color(hex: "1E293B") : Color(hex: "64748B"))
                    }

                    if index < viewModel.getBreadcrumbs().count - 1 {
                        Image(systemName: "chevron.right")
                            .foregroundColor(Color(hex: "CBD5E1"))
                            .font(.system(size: 12))
                    }
                }
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 12)
        }
    }

    // MARK: - Content Views

    private var contentView: some View {
        Group {
            switch viewModel.viewMode {
            case .tree:
                treeView
            case .list:
                listView
            case .grid:
                gridView
            }
        }
    }

    private var treeView: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 0) {
                if let root = viewModel.fileTree?.root {
                    ForEach(root.children) { item in
                        FileTreeRow(
                            item: item,
                            level: 0,
                            viewModel: viewModel,
                            onSelect: { selectedItem in
                                if selectedItem.isFolder {
                                    Task {
                                        await viewModel.loadFolderContents(projectId: projectId, folderPath: selectedItem.path)
                                    }
                                }
                            },
                            onMove: { file in
                                selectedFileToMove = file
                                showMoveFileSheet = true
                            },
                            onDelete: { item in
                                itemToDelete = item
                                showDeleteAlert = true
                            }
                        )
                    }
                }
            }
            .padding(16)
        }
    }

    private var listView: some View {
        ScrollView {
            VStack(spacing: 8) {
                ForEach(viewModel.filteredAndSortedItems()) { item in
                    FileListRow(
                        item: item,
                        viewModel: viewModel,
                        onSelect: {
                            if item.isFolder {
                                Task {
                                    await viewModel.loadFolderContents(projectId: projectId, folderPath: item.path)
                                }
                            }
                        },
                        onMove: {
                            selectedFileToMove = item
                            showMoveFileSheet = true
                        },
                        onDelete: {
                            itemToDelete = item
                            showDeleteAlert = true
                        }
                    )
                }
            }
            .padding(16)
        }
    }

    private var gridView: some View {
        GeometryReader { geometry in
            ScrollView {
                let columns = max(2, Int(geometry.size.width / 180))
                let gridItems = Array(repeating: GridItem(.flexible(), spacing: 12), count: columns)

                LazyVGrid(columns: gridItems, spacing: 12) {
                    ForEach(viewModel.filteredAndSortedItems()) { item in
                        FileGridCard(
                            item: item,
                            viewModel: viewModel,
                            onSelect: {
                                if item.isFolder {
                                    Task {
                                        await viewModel.loadFolderContents(projectId: projectId, folderPath: item.path)
                                    }
                                }
                            },
                            onMove: {
                                selectedFileToMove = item
                                showMoveFileSheet = true
                            },
                            onDelete: {
                                itemToDelete = item
                                showDeleteAlert = true
                            }
                        )
                    }
                }
                .padding(16)
            }
        }
    }

    // MARK: - Loading & Error

    private var loadingView: some View {
        VStack(spacing: 16) {
            ProgressView()
                .scaleEffect(1.2)
            Text("加载文件树...")
                .foregroundColor(Color(hex: "64748B"))
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    private func errorView(_ message: String) -> some View {
        VStack(spacing: 16) {
            Image(systemName: "exclamationmark.triangle.fill")
                .font(.system(size: 48))
                .foregroundColor(Color(hex: "EF4444"))

            Text(message)
                .foregroundColor(Color(hex: "64748B"))
                .multilineTextAlignment(.center)

            Button(action: {
                Task {
                    await viewModel.loadFileTree(projectId: projectId)
                }
            }) {
                Text("重试")
                    .padding(.horizontal, 20)
                    .padding(.vertical, 10)
                    .background(Color(hex: "3B82F6"))
                    .foregroundColor(.white)
                    .cornerRadius(8)
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .padding(32)
    }
}

// MARK: - Supporting Components

/// 树形视图行
struct FileTreeRow: View {
    let item: FileManagerService.FileNodeResponse
    let level: Int
    let viewModel: FileManagerViewModel
    let onSelect: (FileManagerService.FileNodeResponse) -> Void
    let onMove: (FileManagerService.FileNodeResponse) -> Void
    let onDelete: (FileManagerService.FileNodeResponse) -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            HStack(spacing: 8) {
                // 缩进
                if level > 0 {
                    Spacer()
                        .frame(width: CGFloat(level * 20))
                }

                // 展开/折叠按钮
                if item.isFolder {
                    Button(action: {
                        viewModel.toggleFolder(item.id)
                    }) {
                        Image(systemName: viewModel.isFolderExpanded(item.id) ? "chevron.down" : "chevron.right")
                            .foregroundColor(Color(hex: "64748B"))
                            .font(.system(size: 12))
                    }
                }

                // 图标
                Image(systemName: viewModel.getFileIcon(item))
                    .foregroundColor(Color(hex: viewModel.getFileIconColor(item)))

                // 名称
                Text(item.name)
                    .foregroundColor(Color(hex: "1E293B"))

                Spacer()

                // 元信息
                if !item.isFolder {
                    Text(viewModel.formatFileSize(item.size))
                        .font(.system(size: 12))
                        .foregroundColor(Color(hex: "94A3B8"))
                }

                // 操作菜单
                Menu {
                    if !item.isFolder {
                        Button(action: { onMove(item) }) {
                            Label("移动", systemImage: "arrow.right")
                        }
                    }
                    Button(role: .destructive, action: { onDelete(item) }) {
                        Label("删除", systemImage: "trash")
                    }
                } label: {
                    Image(systemName: "ellipsis")
                        .foregroundColor(Color(hex: "94A3B8"))
                        .padding(8)
                }
            }
            .padding(.vertical, 8)
            .padding(.horizontal, 12)
            .background(Color.clear)
            .contentShape(Rectangle())
            .onTapGesture {
                if item.isFolder {
                    viewModel.toggleFolder(item.id)
                }
                onSelect(item)
            }

            // 子项
            if item.isFolder && viewModel.isFolderExpanded(item.id) {
                ForEach(item.children) { child in
                    FileTreeRow(
                        item: child,
                        level: level + 1,
                        viewModel: viewModel,
                        onSelect: onSelect,
                        onMove: onMove,
                        onDelete: onDelete
                    )
                }
            }
        }
    }
}

/// 列表视图行
struct FileListRow: View {
    let item: FileManagerService.FileNodeResponse
    let viewModel: FileManagerViewModel
    let onSelect: () -> Void
    let onMove: () -> Void
    let onDelete: () -> Void

    var body: some View {
        HStack(spacing: 12) {
            // 图标
            Image(systemName: viewModel.getFileIcon(item))
                .foregroundColor(Color(hex: viewModel.getFileIconColor(item)))
                .font(.system(size: 24))
                .frame(width: 40, height: 40)
                .background(Color(hex: viewModel.getFileIconColor(item)).opacity(0.1))
                .cornerRadius(8)

            // 信息
            VStack(alignment: .leading, spacing: 4) {
                Text(item.name)
                    .font(.system(size: 15, weight: .medium))
                    .foregroundColor(Color(hex: "1E293B"))

                HStack(spacing: 12) {
                    if !item.isFolder {
                        Text(viewModel.formatFileSize(item.size))
                            .font(.system(size: 13))
                            .foregroundColor(Color(hex: "94A3B8"))
                    }
                    Text(viewModel.formatDate(item.modifiedAt))
                        .font(.system(size: 13))
                        .foregroundColor(Color(hex: "94A3B8"))
                }
            }

            Spacer()

            // 操作菜单
            Menu {
                if !item.isFolder {
                    Button(action: onMove) {
                        Label("移动", systemImage: "arrow.right")
                    }
                }
                Button(role: .destructive, action: onDelete) {
                    Label("删除", systemImage: "trash")
                }
            } label: {
                Image(systemName: "ellipsis")
                    .foregroundColor(Color(hex: "94A3B8"))
                    .padding(8)
            }
        }
        .padding(12)
        .background(Color.white)
        .cornerRadius(8)
        .shadow(color: Color.black.opacity(0.05), radius: 2, x: 0, y: 1)
        .onTapGesture(perform: onSelect)
    }
}

/// 网格视图卡片
struct FileGridCard: View {
    let item: FileManagerService.FileNodeResponse
    let viewModel: FileManagerViewModel
    let onSelect: () -> Void
    let onMove: () -> Void
    let onDelete: () -> Void

    var body: some View {
        VStack(spacing: 12) {
            // 图标
            Image(systemName: viewModel.getFileIcon(item))
                .foregroundColor(Color(hex: viewModel.getFileIconColor(item)))
                .font(.system(size: 48))
                .frame(height: 80)

            // 名称
            Text(item.name)
                .font(.system(size: 14, weight: .medium))
                .foregroundColor(Color(hex: "1E293B"))
                .lineLimit(2)
                .multilineTextAlignment(.center)

            // 元信息
            if !item.isFolder {
                Text(viewModel.formatFileSize(item.size))
                    .font(.system(size: 12))
                    .foregroundColor(Color(hex: "94A3B8"))
            }

            // 操作菜单
            Menu {
                if !item.isFolder {
                    Button(action: onMove) {
                        Label("移动", systemImage: "arrow.right")
                    }
                }
                Button(role: .destructive, action: onDelete) {
                    Label("删除", systemImage: "trash")
                }
            } label: {
                Image(systemName: "ellipsis.circle")
                    .foregroundColor(Color(hex: "94A3B8"))
            }
        }
        .padding(16)
        .frame(maxWidth: .infinity)
        .background(Color.white)
        .cornerRadius(12)
        .shadow(color: Color.black.opacity(0.05), radius: 4, x: 0, y: 2)
        .onTapGesture(perform: onSelect)
    }
}

/// 创建文件夹弹窗
struct CreateFolderSheet: View {
    @Binding var isPresented: Bool
    @Binding var folderName: String
    let currentPath: String
    let onCreate: () -> Void

    var body: some View {
        VStack(spacing: 20) {
            // 标题
            HStack {
                Text("新建文件夹")
                    .font(.system(size: 18, weight: .semibold))
                Spacer()
                Button(action: { isPresented = false }) {
                    Image(systemName: "xmark.circle.fill")
                        .foregroundColor(Color(hex: "94A3B8"))
                }
            }

            // 当前路径
            if !currentPath.isEmpty {
                HStack {
                    Text("位置:")
                        .foregroundColor(Color(hex: "64748B"))
                    Text(currentPath)
                        .foregroundColor(Color(hex: "3B82F6"))
                    Spacer()
                }
                .font(.system(size: 14))
            }

            // 输入框
            VStack(alignment: .leading, spacing: 8) {
                Text("文件夹名称")
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(Color(hex: "1E293B"))

                TextField("请输入文件夹名称", text: $folderName)
                    .textFieldStyle(PlainTextFieldStyle())
                    .padding(12)
                    .background(Color(hex: "F1F5F9"))
                    .cornerRadius(8)
            }

            // 按钮
            HStack(spacing: 12) {
                Button(action: { isPresented = false }) {
                    Text("取消")
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 12)
                        .background(Color(hex: "F1F5F9"))
                        .foregroundColor(Color(hex: "64748B"))
                        .cornerRadius(8)
                }

                Button(action: onCreate) {
                    Text("创建")
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 12)
                        .background(folderName.isEmpty ? Color(hex: "CBD5E1") : Color(hex: "3B82F6"))
                        .foregroundColor(.white)
                        .cornerRadius(8)
                }
                .disabled(folderName.isEmpty)
            }
        }
        .padding(24)
        .frame(width: 400)
    }
}

/// 移动文件弹窗
struct MoveFileSheet: View {
    @Binding var isPresented: Bool
    let file: FileManagerService.FileNodeResponse
    @Binding var targetPath: String
    let onMove: () -> Void

    var body: some View {
        VStack(spacing: 20) {
            // 标题
            HStack {
                Text("移动文件")
                    .font(.system(size: 18, weight: .semibold))
                Spacer()
                Button(action: { isPresented = false }) {
                    Image(systemName: "xmark.circle.fill")
                        .foregroundColor(Color(hex: "94A3B8"))
                }
            }

            // 文件信息
            HStack(spacing: 12) {
                Image(systemName: "doc.fill")
                    .foregroundColor(Color(hex: "3B82F6"))
                    .font(.system(size: 24))

                VStack(alignment: .leading, spacing: 4) {
                    Text(file.name)
                        .font(.system(size: 15, weight: .medium))
                    Text("当前位置: \(file.path.isEmpty ? "根目录" : file.path)")
                        .font(.system(size: 13))
                        .foregroundColor(Color(hex: "64748B"))
                }
                Spacer()
            }
            .padding(12)
            .background(Color(hex: "F1F5F9"))
            .cornerRadius(8)

            // 目标路径输入
            VStack(alignment: .leading, spacing: 8) {
                Text("目标文件夹路径")
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(Color(hex: "1E293B"))

                TextField("例如: documents/reports", text: $targetPath)
                    .textFieldStyle(PlainTextFieldStyle())
                    .padding(12)
                    .background(Color(hex: "F1F5F9"))
                    .cornerRadius(8)

                Text("留空表示移动到根目录")
                    .font(.system(size: 12))
                    .foregroundColor(Color(hex: "94A3B8"))
            }

            // 按钮
            HStack(spacing: 12) {
                Button(action: { isPresented = false }) {
                    Text("取消")
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 12)
                        .background(Color(hex: "F1F5F9"))
                        .foregroundColor(Color(hex: "64748B"))
                        .cornerRadius(8)
                }

                Button(action: onMove) {
                    Text("移动")
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 12)
                        .background(Color(hex: "3B82F6"))
                        .foregroundColor(.white)
                        .cornerRadius(8)
                }
            }
        }
        .padding(24)
        .frame(width: 450)
    }
}
