import Foundation

// 模拟后端返回的三种响应格式
let photoResponse = """
{
  "success": true,
  "data": {
    "photos": [{
      "id": "35",
      "file_size": 16222,
      "project_id": 1
    }],
    "total": 1,
    "page": 1,
    "page_size": 10
  }
}
"""

let tableResponse = """
{
  "tables": [{
    "id": 37,
    "project_id": 1,
    "file_size": 10636,
    "row_count": 2,
    "column_count": 10,
    "filename": "test.xlsx",
    "format": "Excel",
    "columns": [],
    "tags": [],
    "description": null,
    "uploaded_at": "2026-08-27T04:33:02.341831",
    "updated_at": "2026-08-27T04:33:02.341831"
  }],
  "total": 1
}
"""

// 测试解码
struct PhotoData: Codable {
    let id: String
    let fileSize: Int
    let projectId: Int
    
    enum CodingKeys: String, CodingKey {
        case id
        case fileSize = "file_size"
        case projectId = "project_id"
    }
}

struct PhotoListResponse: Codable {
    let photos: [PhotoData]
    let total: Int
    let page: Int
    let pageSize: Int
    
    enum CodingKeys: String, CodingKey {
        case photos, total, page
        case pageSize = "page_size"
    }
}

struct TableData: Codable {
    let id: Int
    let projectId: Int
    let fileSize: Int
    
    enum CodingKeys: String, CodingKey {
        case id
        case projectId = "project_id"
        case fileSize = "file_size"
    }
}

struct TablesResponse: Codable {
    let tables: [TableData]
    let total: Int
}

let decoder = JSONDecoder()
decoder.keyDecodingStrategy = .convertFromSnakeCase

// 测试照片API（带success包装）
print("测试照片API:")
if let photoData = photoResponse.data(using: .utf8) {
    do {
        // 先解析为通用JSON
        let json = try JSONSerialization.jsonObject(with: photoData) as! [String: Any]
        if let dataDict = json["data"] as? [String: Any] {
            let dataJSON = try JSONSerialization.data(withJSONObject: dataDict)
            let result = try decoder.decode(PhotoListResponse.self, from: dataJSON)
            print("✅ 照片API解码成功: \(result.photos.count) 张照片")
        }
    } catch {
        print("❌ 照片API解码失败: \(error)")
    }
}

// 测试表格API（无包装）
print("\n测试表格API:")
if let tableData = tableResponse.data(using: .utf8) {
    do {
        let result = try decoder.decode(TablesResponse.self, from: tableData)
        print("✅ 表格API解码成功: \(result.tables.count) 个表格")
    } catch {
        print("❌ 表格API解码失败: \(error)")
    }
}
