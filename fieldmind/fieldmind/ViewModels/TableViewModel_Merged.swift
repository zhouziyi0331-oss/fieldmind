//
//  TableViewModel_Merged.swift
//  FieldMind
//
//  深度整合 - 合并自主版本和 Native 版本
//  Generated: Sat Sep 19 11:21:01 CST 2026
//

import Foundation

// ========================================
// 主实现（来自主项目）
// ========================================


@MainActor
class TableViewModel: ObservableObject {
    @Published var tables: [TableService.TableData] = []
    @Published var statistics: TableService.TableStatistics?
    @Published var selectedTable: TableService.TableData?
    @Published var isLoading = false
    @Published var isLoadingStats = false
    @Published var isUploading = false
    @Published var errorMessage: String?
    @Published var successMessage: String?

    func loadTables(projectId: Int, format: String? = nil) async {
        isLoading = true
        errorMessage = nil

        do {
            let response = try await TableService.shared.listTables(projectId: projectId, format: format)
            tables = response.tables
        } catch {
            errorMessage = "加载表格列表失败: \(error.localizedDescription)"
        }

        isLoading = false
    }

    func loadTableDetail(projectId: Int, tableId: Int) async {
        errorMessage = nil

        do {
            selectedTable = try await TableService.shared.getTable(projectId: projectId, tableId: tableId)
        } catch {
            errorMessage = "加载表格详情失败: \(error.localizedDescription)"
        }
    }

    func loadStatistics(projectId: Int) async {
        isLoadingStats = true
        errorMessage = nil

        do {
            statistics = try await TableService.shared.getStatistics(projectId: projectId)
        } catch {
            errorMessage = "加载统计信息失败: \(error.localizedDescription)"
        }

        isLoadingStats = false
    }

    func deleteTable(projectId: Int, tableId: Int) async {
        errorMessage = nil
        successMessage = nil

        do {
            try await TableService.shared.deleteTable(projectId: projectId, tableId: tableId)
            tables.removeAll { $0.id == tableId }
            successMessage = "表格删除成功"
        } catch {
            errorMessage = "删除表格失败: \(error.localizedDescription)"
        }
    }

    func uploadTable(projectId: Int, filename: String, format: String, data: Data, tags: [String]?, description: String?) async {
        isUploading = true
        errorMessage = nil
        successMessage = nil

        do {
            let newTable = try await TableService.shared.uploadTable(
                projectId: projectId,
                filename: filename,
                format: format,
                data: data,
                tags: tags,
                description: description
            )
            tables.insert(newTable, at: 0)
            successMessage = "表格上传成功"
        } catch {
            errorMessage = "上传表格失败: \(error.localizedDescription)"
        }

        isUploading = false
    }

    func uploadTables(projectId: Int, fileURLs: [URL]) async -> Bool {
        isUploading = true
        errorMessage = nil
        successMessage = nil
        var uploaded: [TableService.TableData] = []
        var allSuccess = true

        for fileURL in fileURLs {
            let scoped = fileURL.startAccessingSecurityScopedResource()
            defer {
                if scoped {
                    fileURL.stopAccessingSecurityScopedResource()
                }
            }

            do {
                let data = try Data(contentsOf: fileURL)
                let ext = fileURL.pathExtension.lowercased()
                let format = ext == "csv" ? "CSV" : "Excel"
                let table = try await TableService.shared.uploadTable(
                    projectId: projectId,
                    filename: fileURL.lastPathComponent,
                    format: format,
                    data: data,
                    tags: nil,
                    description: nil
                )
                uploaded.append(table)
            } catch {
                allSuccess = false
                errorMessage = "上传表格失败: \(error.localizedDescription)"
                DebugLogger.shared.log("表格上传失败", type: .error, details: "文件=\(fileURL.path)\n错误=\(error.localizedDescription)", category: "upload.table")
            }
        }

        if !uploaded.isEmpty {
            await loadTables(projectId: projectId)
            await loadStatistics(projectId: projectId)
            successMessage = "已上传 \(uploaded.count) 个表格"
        }

        isUploading = false
        return allSuccess
    }

    func filterTables(searchText: String, format: String, sortBy: String) -> [TableService.TableData] {
        var filtered = tables

        // Filter by search text
        if !searchText.isEmpty {
            filtered = filtered.filter { table in
                table.filename.localizedCaseInsensitiveContains(searchText) ||
                table.tags.contains { $0.localizedCaseInsensitiveContains(searchText) }
            }
        }

        // Filter by format
        if format != "全部类型" {
            filtered = filtered.filter { $0.format == format }
        }

        // Sort
        filtered.sort { first, second in
            switch sortBy {
            case "最新上传":
                return first.uploadedAt > second.uploadedAt
            case "最早上传":
                return first.uploadedAt < second.uploadedAt
            case "名称":
                return first.filename < second.filename
            case "大小":
                return first.fileSize > second.fileSize
            case "行数":
                return first.rowCount > second.rowCount
            default:
                return first.uploadedAt > second.uploadedAt
            }
        }

        return filtered
    }

    func formatFileSize(_ bytes: Int) -> String {
        let formatter = ByteCountFormatter()
        formatter.allowedUnits = [.useKB, .useMB, .useGB]
        formatter.countStyle = .file
        return formatter.string(fromByteCount: Int64(bytes))
    }

    var hasTables: Bool {
        !tables.isEmpty
    }

    var hasStatistics: Bool {
        statistics != nil
    }

    var totalTableCount: Int {
        statistics?.totalTables ?? tables.count
    }

    var totalRowCount: Int {
        statistics?.totalRows ?? tables.reduce(0) { $0 + $1.rowCount }
    }
}

// ========================================
// Native 版本的扩展功能
// ========================================
// TODO: 手动审查并整合以下功能

/*

@MainActor
class TableViewModel: ObservableObject {
    @Published var tables: [TableService.TableData] = []
    @Published var statistics: TableService.TableStatistics?
    @Published var selectedTable: TableService.TableData?
    @Published var isLoading = false
    @Published var isLoadingStats = false
    @Published var isUploading = false
    @Published var errorMessage: String?
    @Published var successMessage: String?

    func loadTables(projectId: Int, format: String? = nil) async {
        isLoading = true
        errorMessage = nil

        do {
            let response = try await TableService.shared.listTables(projectId: projectId, format: format)
            tables = response.tables
        } catch {
            errorMessage = "加载表格列表失败: \(error.localizedDescription)"
        }

        isLoading = false
    }

    func loadTableDetail(projectId: Int, tableId: Int) async {
        errorMessage = nil

        do {
            selectedTable = try await TableService.shared.getTable(projectId: projectId, tableId: tableId)
        } catch {
            errorMessage = "加载表格详情失败: \(error.localizedDescription)"
        }
    }

    func loadStatistics(projectId: Int) async {
        isLoadingStats = true
        errorMessage = nil

        do {
            statistics = try await TableService.shared.getStatistics(projectId: projectId)
        } catch {
            errorMessage = "加载统计信息失败: \(error.localizedDescription)"
        }

        isLoadingStats = false
    }

    func deleteTable(projectId: Int, tableId: Int) async {
        errorMessage = nil
        successMessage = nil

        do {
            try await TableService.shared.deleteTable(projectId: projectId, tableId: tableId)
            tables.removeAll { $0.id == tableId }
            successMessage = "表格删除成功"
        } catch {
            errorMessage = "删除表格失败: \(error.localizedDescription)"
        }
    }

    func uploadTable(projectId: Int, filename: String, format: String, data: Data, tags: [String]?, description: String?) async {
        isUploading = true
        errorMessage = nil
        successMessage = nil

        do {
            let newTable = try await TableService.shared.uploadTable(
                projectId: projectId,
                filename: filename,
                format: format,
                data: data,
                tags: tags,
                description: description
            )
            tables.insert(newTable, at: 0)
            successMessage = "表格上传成功"
        } catch {
            errorMessage = "上传表格失败: \(error.localizedDescription)"
        }

        isUploading = false
    }

    func uploadTables(projectId: Int, fileURLs: [URL]) async -> Bool {
        isUploading = true
        errorMessage = nil
        successMessage = nil
        var uploaded: [TableService.TableData] = []
        var allSuccess = true

        for fileURL in fileURLs {
            let scoped = fileURL.startAccessingSecurityScopedResource()
            defer {
                if scoped {
                    fileURL.stopAccessingSecurityScopedResource()
                }
            }

            do {
                let data = try Data(contentsOf: fileURL)
                let ext = fileURL.pathExtension.lowercased()
                let format = ext == "csv" ? "CSV" : "Excel"
                let table = try await TableService.shared.uploadTable(
                    projectId: projectId,
                    filename: fileURL.lastPathComponent,
                    format: format,
                    data: data,
                    tags: nil,
                    description: nil
                )
                uploaded.append(table)
            } catch {
                allSuccess = false
                errorMessage = "上传表格失败: \(error.localizedDescription)"
                DebugLogger.shared.log("表格上传失败", type: .error, details: "文件=\(fileURL.path)\n错误=\(error.localizedDescription)", category: "upload.table")
            }
        }

        if !uploaded.isEmpty {
            await loadTables(projectId: projectId)
            await loadStatistics(projectId: projectId)
            successMessage = "已上传 \(uploaded.count) 个表格"
        }

        isUploading = false
        return allSuccess
    }

    func filterTables(searchText: String, format: String, sortBy: String) -> [TableService.TableData] {
        var filtered = tables

        // Filter by search text
        if !searchText.isEmpty {
            filtered = filtered.filter { table in
                table.filename.localizedCaseInsensitiveContains(searchText) ||
                table.tags.contains { $0.localizedCaseInsensitiveContains(searchText) }
            }
        }

        // Filter by format
        if format != "全部类型" {
            filtered = filtered.filter { $0.format == format }
        }

        // Sort
        filtered.sort { first, second in
            switch sortBy {
            case "最新上传":
                return first.uploadedAt > second.uploadedAt
            case "最早上传":
                return first.uploadedAt < second.uploadedAt
            case "名称":
                return first.filename < second.filename
            case "大小":
                return first.fileSize > second.fileSize
            case "行数":
                return first.rowCount > second.rowCount
            default:
                return first.uploadedAt > second.uploadedAt
            }
        }

        return filtered
    }

    func formatFileSize(_ bytes: Int) -> String {
        let formatter = ByteCountFormatter()
        formatter.allowedUnits = [.useKB, .useMB, .useGB]
        formatter.countStyle = .file
        return formatter.string(fromByteCount: Int64(bytes))
    }

    var hasTables: Bool {
        !tables.isEmpty
    }

    var hasStatistics: Bool {
        statistics != nil
    }

    var totalTableCount: Int {
        statistics?.totalTables ?? tables.count
    }

    var totalRowCount: Int {
        statistics?.totalRows ?? tables.reduce(0) { $0 + $1.rowCount }
    }
}
*/

