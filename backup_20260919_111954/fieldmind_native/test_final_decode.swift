import Foundation

// 模拟后端返回的真实数据
let tableStatsResponse = """
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

func decodePayload<T: Decodable>(_ data: Data, as type: T.Type) throws -> T {
    let decoder = JSONDecoder()
    decoder.keyDecodingStrategy = .convertFromSnakeCase
    
    do {
        // 尝试直接解码
        let result = try decoder.decode(T.self, from: data)
        print("✅ 直接解码成功")
        return result
    } catch {
        print("⚠️  直接解码失败，尝试提取data字段")

        guard let jsonString = String(data: data, encoding: .utf8) else {
            throw error
        }

        // 检查是否是包装响应
        guard (jsonString.contains("\"success\":true") || jsonString.contains("\"success\": true")),
              let dataStart = jsonString.range(of: "\"data\":")?.upperBound else {
            throw error
        }

        let remaining = jsonString[dataStart...]
        var index = remaining.startIndex

        // 跳过空格
        while index < remaining.endIndex && remaining[index].isWhitespace {
            index = remaining.index(after: index)
        }

        guard index < remaining.endIndex else { throw error }

        let firstChar = remaining[index]
        guard firstChar == "{" || firstChar == "[" else { throw error }

        let openChar = firstChar
        let closeChar: Character = (firstChar == "{") ? "}" : "]"

        // 提取完整的JSON
        var depth = 0
        var inString = false
        var escaped = false
        var endIndex = index

        for char in remaining[index...] {
            if escaped {
                escaped = false
            } else if char == "\\" {
                escaped = true
            } else if char == "\"" {
                inString.toggle()
            } else if !inString {
                if char == openChar {
                    depth += 1
                } else if char == closeChar {
                    depth -= 1
                    if depth == 0 {
                        endIndex = remaining.index(after: endIndex)
                        break
                    }
                }
            }
            endIndex = remaining.index(after: endIndex)
        }

        let dataJSONString = String(remaining[index..<endIndex])
        print("📦 提取的data字段: \(dataJSONString)")
        
        guard let dataJSON = dataJSONString.data(using: .utf8) else { throw error }

        let result = try decoder.decode(T.self, from: dataJSON)
        print("✅ 从data字段解码成功")
        return result
    }
}

// 执行测试
guard let data = tableStatsResponse.data(using: .utf8) else {
    print("❌ 无法转换为Data")
    exit(1)
}

do {
    let result = try decodePayload(data, as: TableStatistics.self)
    print("✅ 最终结果: totalTables=\(result.totalTables), totalRows=\(result.totalRows)")
} catch {
    print("❌ 解码失败: \(error)")
}
