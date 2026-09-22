import Foundation

// 测试后端返回的实际数据
let tableStatsJSON = """
{
    "success": true,
    "data": {
        "total_tables": 6,
        "total_rows": 112,
        "total_size": 82304,
        "format_counts": {
            "Excel": 5,
            "CSV": 1
        }
    }
}
"""

struct TableStatistics: Codable {
    let totalTables: Int
    let totalRows: Int
    let totalSize: Int
    let formatCounts: [String: Int]
    
    enum CodingKeys: String, CodingKey {
        case totalTables = "total_tables"
        case totalRows = "total_rows"
        case totalSize = "total_size"
        case formatCounts = "format_counts"
    }
}

let decoder = JSONDecoder()
decoder.keyDecodingStrategy = .convertFromSnakeCase

guard let data = tableStatsJSON.data(using: .utf8) else {
    print("❌ 无法转换为Data")
    exit(1)
}

// 测试1：直接解码（会失败，因为有success包装）
print("测试1：直接解码")
do {
    let result = try decoder.decode(TableStatistics.self, from: data)
    print("✅ 成功: \(result)")
} catch {
    print("❌ 失败（预期）: \(error)")
}

// 测试2：手动提取data字段
print("\n测试2：手动提取data字段")
do {
    let json = try JSONSerialization.jsonObject(with: data) as! [String: Any]
    if let dataDict = json["data"] as? [String: Any] {
        let dataJSON = try JSONSerialization.data(withJSONObject: dataDict)
        let result = try decoder.decode(TableStatistics.self, from: dataJSON)
        print("✅ 成功: \(result)")
    }
} catch {
    print("❌ 失败: \(error)")
}

// 测试3：字符串提取（我的当前方法）
print("\n测试3：字符串提取")
if let jsonString = String(data: data, encoding: .utf8),
   let dataRange = jsonString.range(of: "\"data\":"),
   jsonString.contains("\"success\":true") {
    
    let afterData = jsonString[dataRange.upperBound...]
    var startIndex = afterData.startIndex
    while startIndex < afterData.endIndex && afterData[startIndex].isWhitespace {
        startIndex = afterData.index(after: startIndex)
    }
    
    if startIndex < afterData.endIndex {
        var dataContent = ""
        var braceCount = 0
        var inString = false
        var escaped = false
        
        for char in afterData[startIndex...] {
            dataContent.append(char)
            
            if escaped {
                escaped = false
                continue
            }
            
            if char == "\\" {
                escaped = true
                continue
            }
            
            if char == "\"" {
                inString.toggle()
                continue
            }
            
            if !inString {
                if char == "{" { braceCount += 1 }
                if char == "}" { 
                    braceCount -= 1
                    if braceCount == 0 {
                        break
                    }
                }
            }
        }
        
        print("提取的JSON: \(dataContent)")
        
        if let extractedData = dataContent.data(using: .utf8) {
            do {
                let result = try decoder.decode(TableStatistics.self, from: extractedData)
                print("✅ 成功: \(result)")
            } catch {
                print("❌ 失败: \(error)")
            }
        }
    }
}
